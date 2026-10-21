"""Actual local BGE-M3/FAISS retrieval and grounded Qwen role, no training."""
import json
import os
from pathlib import Path
import sys
import time
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from dotenv import load_dotenv
load_dotenv(ROOT/'.env')
os.environ.update(LANGSMITH_TRACING='false', LANGCHAIN_TRACING_V2='false',
                  SEMI_DENSE_ENABLED='1', SEMI_RETRIEVER='bge_m3_faiss', SEMI_EMBED_MODEL='bge-m3')
from app.planner import Knowledge
from app.workbench import Workbench
from app.advisors import LocalAdvisor
from app.discovery import discover


def main():
    knowledge = Knowledge(ROOT/'var', dense=True)
    # Reuse the earlier fixed questions without modifying the old Mac receipt.
    previous = json.loads((ROOT/'docs/evaluation/agent_integration.json').read_text(encoding='utf-8'))
    questions = previous['retrieval'][0]['queries']
    rows = []
    for case in questions:
        started = time.perf_counter()
        found = knowledge.search(case['query'], 3)
        status = dict(knowledge.last_status)
        assert status['mode'] == 'bge_m3_faiss', status
        ids = [d['id'] for d in found]
        rank = min([ids.index(i)+1 for i in case['expected'] if i in ids], default=0)
        rows.append({'query': case['query'], 'expected': case['expected'], 'actual': ids,
                     'hit_at_3': bool(rank), 'reciprocal_rank': 1/rank if rank else 0,
                     'seconds': round(time.perf_counter()-started, 3)})
        print('knowledge', len(rows), '/'+str(len(questions)), status['mode'], flush=True)
    wb = Workbench(ROOT/'var', knowledge=knowledge, advisor=LocalAdvisor(enabled=True))
    dataset = next(d for d in wb.store.datasets() if d['name'] == '제품 A–D 합성 공정')
    before = len(wb.store.runs())
    discovery = discover(wb, dataset['id'], '센서 결측과 불량 분류에 적용할 새로운 모델 후보와 문서 근거')
    assert discovery['retrieval_status']['mode'] == 'bge_m3_faiss', discovery['retrieval_status']
    assert discovery['agent']['status'] == 'verified', discovery['agent']
    assert len(wb.store.runs()) == before
    receipt = {'verified_at': datetime.now(timezone.utc).isoformat(), 'model': knowledge.model,
               'course_reference': '5주차/sllm-main-std/knowledge_asset_demo_faiss_bge_m3.ipynb',
               'course_pattern': 'normalized BGE-M3 embeddings + FAISS IndexFlatIP + retrieved context to Qwen',
               'runtime_difference': 'Course SentenceTransformer; this Windows laptop uses local Ollama BGE-M3 F16',
               'knowledge_index': status, 'query_count': len(rows),
               'hit_at_3': sum(r['hit_at_3'] for r in rows)/len(rows),
               'mrr_at_3': sum(r['reciprocal_rank'] for r in rows)/len(rows), 'queries': rows,
               'external_discovery': discovery, 'training_started': False,
               'scope': 'Small fixed development queries, not an independent benchmark. FAISS local vector index + JSON source metadata, not a server vector database.'}
    (ROOT/'docs/evaluation/vector_rag.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k not in {'queries', 'external_discovery'}}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
