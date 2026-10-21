"""Course-style BGE-M3 embeddings + a persistent, local FAISS vector store.

Embeddings run on the local Ollama service. FAISS stores normalized vectors;
JSON stores the ordered source documents. No remote vector DB is involved.
"""
import json
import os
from pathlib import Path
import threading
import uuid

import httpx
import numpy as np

from .store import digest


class FaissRetriever:
    def __init__(self, directory=None, client=None, model=None):
        self.directory = Path(directory) / 'rag' if directory else None
        self.client = client or httpx.Client(timeout=120)
        self.model = model or os.getenv('SEMI_EMBED_MODEL', 'bge-m3')
        self.url = os.getenv('OLLAMA_URL', 'http://127.0.0.1:11434').rstrip('/')
        self._lock = threading.RLock()
        self.last_status = {}

    def embed(self, texts):
        response = self.client.post(self.url + '/api/embed', json={
            'model': self.model, 'input': texts, 'truncate': False,
            # Release the embedding model before loading Qwen on an 8GB laptop.
            'keep_alive': 0})
        response.raise_for_status()
        vectors = np.ascontiguousarray(response.json()['embeddings'], dtype='float32')
        if (vectors.ndim != 2 or vectors.shape[0] != len(texts) or
                vectors.shape[1] == 0 or not np.isfinite(vectors).all() or
                np.any(np.linalg.norm(vectors, axis=1) == 0)):
            raise ValueError('Invalid embedding vectors')
        return vectors

    def search(self, docs, query, k=4):
        import faiss
        if not docs or k <= 0:
            return []
        # A content address prevents stale vectors being attached to changed text.
        signature = digest({'model': self.model, 'docs': docs, 'metric': 'normalized-IP-v1'})
        index_file = self.directory / f'{signature}.faiss' if self.directory else None
        metadata_file = self.directory / f'{signature}.json' if self.directory else None
        with self._lock:
            index = None
            cache_hit = False
            if index_file and index_file.exists() and metadata_file.exists():
                try:
                    metadata = json.loads(metadata_file.read_text(encoding='utf-8'))
                    if metadata['signature'] == signature and metadata['documents'] == docs:
                        index = faiss.deserialize_index(np.frombuffer(index_file.read_bytes(), dtype='uint8'))
                        if index.ntotal != len(docs) or index.d != metadata['dimension']:
                            index = None
                        else:
                            cache_hit = True
                except (OSError, ValueError, KeyError, RuntimeError):
                    index = None
            if index is None:
                # Small batches limit peak embedding memory on CPU.
                batches = [self.embed([d.get('title', '') + '\n' + d['text']
                                      for d in docs[i:i+4]]) for i in range(0, len(docs), 4)]
                vectors = np.ascontiguousarray(np.concatenate(batches), dtype='float32')
                faiss.normalize_L2(vectors)
                index = faiss.IndexFlatIP(vectors.shape[1])
                index.add(vectors)
                if index_file:
                    self.directory.mkdir(parents=True, exist_ok=True)
                    # Python byte I/O also handles Korean Windows paths.
                    token = uuid.uuid4().hex
                    temporary = index_file.with_suffix('.' + token + '.tmp')
                    temporary.write_bytes(faiss.serialize_index(index).tobytes())
                    temporary.replace(index_file)
                    metadata = {'signature': signature, 'model': self.model,
                                'dimension': index.d, 'documents': docs}
                    temporary = metadata_file.with_suffix('.' + token + '.tmp')
                    temporary.write_text(json.dumps(metadata, ensure_ascii=False), encoding='utf-8')
                    temporary.replace(metadata_file)
            query_vector = self.embed([query])
            if query_vector.shape[1] != index.d:
                raise ValueError('Query/document embedding dimensions differ')
            faiss.normalize_L2(query_vector)
            scores, ids = index.search(query_vector, min(k, len(docs)))
            self.last_status = {'mode': 'bge_m3_faiss', 'model': self.model,
                                'embedding_provider': 'local_ollama', 'dimension': index.d,
                                'document_count': index.ntotal, 'index_type': 'IndexFlatIP',
                                'metric': 'cosine (normalized inner product)',
                                'index_signature': signature, 'persistent': index_file is not None,
                                'index_cache_hit': cache_hit}
            return [{**docs[int(i)], 'score': round(float(score), 6)}
                    for score, i in zip(scores[0], ids[0]) if i >= 0 and score > 0]
