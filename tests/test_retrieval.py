import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import httpx

from app.planner import Knowledge
from app.retrieval import FaissRetriever


class RetrievalTests(unittest.TestCase):
    def client(self, calls):
        def serve(request):
            payload = json.loads(request.content)
            calls.append(payload['input'])
            # Different magnitudes expose accidental unnormalized inner product.
            vectors = [[1, 0] if 'alpha' in text else [100, 100] for text in payload['input']]
            return httpx.Response(200, json={'embeddings': vectors})
        return httpx.Client(transport=httpx.MockTransport(serve))

    def test_cosine_and_persistent_unicode_roundtrip(self):
        calls = []
        docs = [{'id': 'a', 'text': 'alpha'}, {'id': 'b', 'text': 'beta'}]
        with tempfile.TemporaryDirectory(prefix='반도체-') as folder:
            first = FaissRetriever(folder, self.client(calls), 'bge-m3')
            found = first.search(docs, 'alpha', 10)
            self.assertEqual([d['id'] for d in found], ['a', 'b'])
            self.assertAlmostEqual(found[0]['score'], 1)
            self.assertAlmostEqual(found[1]['score'], .707107, places=5)
            again = FaissRetriever(folder, self.client(calls), 'bge-m3')
            self.assertEqual(again.search(docs, 'alpha'), found)
            self.assertTrue(again.last_status['index_cache_hit'])
            self.assertEqual(calls, [['\nalpha', '\nbeta'], ['alpha'], ['alpha']])
            metadata = json.loads(next((Path(folder)/'rag').glob('*.json')).read_text(encoding='utf-8'))
            self.assertEqual(metadata['documents'], docs)

    def test_changed_text_rebuilds_and_corrupt_index_recovers(self):
        calls = []
        with tempfile.TemporaryDirectory() as folder:
            search = FaissRetriever(folder, self.client(calls), 'bge-m3')
            search.search([{'id': 'same', 'text': 'alpha'}], 'alpha')
            old_signature = search.last_status['index_signature']
            search.search([{'id': 'same', 'text': 'beta'}], 'alpha')
            self.assertNotEqual(search.last_status['index_signature'], old_signature)
            index = Path(folder)/'rag'/f'{search.last_status["index_signature"]}.faiss'
            index.write_bytes(b'broken')
            self.assertTrue(search.search([{'id': 'same', 'text': 'beta'}], 'alpha'))
            self.assertFalse(search.last_status['index_cache_hit'])

    def test_bad_embeddings_are_explicit_fallback(self):
        client = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, json={'embeddings': [[0, 0]]})))
        with patch.dict('os.environ', {'SEMI_RETRIEVER': 'bge_m3_faiss'}):
            knowledge = Knowledge(dense=True, client=client)
            self.assertTrue(knowledge.search('센서 결측'))
            self.assertEqual(knowledge.last_status['mode'], 'tfidf_fallback')
            self.assertTrue(knowledge.search_documents([{'id': 'x', 'text': 'sensor missing'}], 'sensor'))
            self.assertEqual(knowledge.last_status['mode'], 'tfidf_fallback')

    def test_external_documents_use_configured_vector_search(self):
        calls = []
        with patch.dict('os.environ', {'SEMI_RETRIEVER': 'bge_m3_faiss', 'SEMI_EMBED_MODEL': 'bge-m3'}):
            knowledge = Knowledge(dense=True, client=self.client(calls))
            found = knowledge.search_documents([{'id': 'official-a', 'text': 'alpha', 'url': 'https://example.org/source'}], 'alpha')
            self.assertEqual(found[0]['url'], 'https://example.org/source')
            self.assertEqual(knowledge.last_status['mode'], 'bge_m3_faiss')
            self.assertEqual(knowledge.last_status['index_type'], 'IndexFlatIP')


if __name__ == '__main__':
    unittest.main()
