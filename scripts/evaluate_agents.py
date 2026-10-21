"""Real local LLM + embedding integration; optional LangSmith trace of public/synthetic summaries only."""
import json
import os
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ['SEMI_LLM_ENABLED'] = '1'
if '--langsmith-env' in sys.argv:
    from dotenv import dotenv_values
    cfg = dotenv_values(sys.argv[sys.argv.index('--langsmith-env')+1])
    os.environ['LANGSMITH_API_KEY'] = cfg.get('LANGSMITH_API_KEY') or cfg.get('LANGCHAIN_API_KEY', '')
    os.environ['LANGSMITH_ENDPOINT'] = cfg.get('LANGSMITH_ENDPOINT') or cfg.get('LANGCHAIN_ENDPOINT', 'https://api.smith.langchain.com')
    os.environ['LANGSMITH_PROJECT'] = cfg.get('LANGSMITH_PROJECT') or cfg.get('LANGCHAIN_PROJECT') or 'G045-Semiconductor-Agent'
    os.environ['LANGSMITH_TRACING'] = 'true'
    os.environ['LANGCHAIN_TRACING_V2'] = 'true'

from langsmith import Client, traceable
from app.planner import Knowledge
from app.advisors import LocalAdvisor, result_choices
from app.workbench import Workbench

QUERIES = [
 ('학습과 테스트에 같은 lot이 섞이면 어떻게 하나요?', ['leakage']),
 ('정상은 많고 불량이 적을 때 정확도를 믿어도 되나요?', ['imbalance']),
 ('A B 제품을 각각 훈련할지 합칠지 비교하려면?', ['product']),
 ('정상 이미지만으로 결함을 찾는 모델은?', ['image']),
 ('SECOM pass fail과 제품 구분은 어떻게 되어 있나요?', ['secom']),
 ('엔지니어 승인 없이 모델 학습을 실행해도 되나요?', ['approval']),
 ('불량 검출률이 오르면 수율과 영업이익도 확정되나요?', ['profit']),
 ('기업 클라우드에 배포할 때 필요한 연결은?', ['cloud']),
 ('의사결정나무와 랜덤포레스트도 센서 Scaling가 필요한가요?', ['tree']),
 ('센서 단위가 다를 때 KNN과 SVM의 전처리는?', ['distance']),
 ('다층 퍼셉트론 신경망에 센서를 입력할 때 주의점은?', ['ann']),
 ('로그 텍스트와 시계열에는 어떤 모델을 쓰나요?', ['modalities']),
 ('새 제품 데이터에서 성능이 하락하면 언제 재학습하나요?', ['retraining']),
]


@traceable(name='G045.public_synthetic_agent_workflow')
def integration():
    dense, before = Knowledge(ROOT/'var', dense=True), Knowledge(dense=False)
    retrieval = []
    for mode, knowledge in [('tfidf', before), ('dense', dense)]:
        rows = []
        for query, expected in QUERIES:
            start = time.perf_counter()
            docs = knowledge.search(query, 3)
            ids = [d['id'] for d in docs]
            rank = min([ids.index(d)+1 for d in expected if d in ids], default=0)
            rows.append({'query': query, 'expected': expected, 'actual': ids, 'hit_at_3': bool(rank),
                         'reciprocal_rank': 1/rank if rank else 0, 'seconds': time.perf_counter()-start,
                         'backend': knowledge.last_status['mode']})
        retrieval.append({'mode': mode, 'hit_at_3': sum(r['hit_at_3'] for r in rows)/len(rows),
                          'mrr_at_3': sum(r['reciprocal_rank'] for r in rows)/len(rows),
                          'mean_seconds': sum(r['seconds'] for r in rows)/len(rows), 'queries': rows})
    wb = Workbench(ROOT/'var', knowledge=dense, advisor=LocalAdvisor(enabled=True))
    ds = next(d for d in wb.store.datasets() if d['name']=='제품 A–D 합성 공정')
    start = time.perf_counter()
    p = wb.propose({'dataset_id': ds['id'], 'question':'센서 결측과 불량 부족에 맞는 전처리, 교육 모델과 제품 학습 범위를 근거로 비교해줘'})
    saved = json.loads((ROOT/'docs/evaluation/synthetic_process.json').read_text(encoding='utf-8'))
    critic = wb.advisor.advise('ResultCriticAgent', {'winner':saved['result']['winner']['model'],
        'test': saved['result']['test'], 'gate': saved['result']['gate']}, result_choices(saved['result']), p['evidence'])
    outputs = p['agent_outputs']+[critic]
    return {'retrieval':retrieval, 'agent_outputs':outputs, 'proposal_id':p['id'], 'plan_hash':p['plan_hash'],
            'approval_status':p['status'], 'training_started':False,
            'workflow_seconds':time.perf_counter()-start, 'all_roles_verified':all(a['status']=='verified' for a in outputs),
            'retrieval_model':dense.model, 'local_llm_model':wb.advisor.model,
            'evaluation_note':'고정 13개 프로젝트 질문의 자체 정답표. 일반 검색 성능·현장 정확도의 증거 아님. dense 첫 질의에는 문서 캐시 준비 시간이 포함될 수 있음'}


def main():
    run_id = uuid.uuid4()
    result = integration(langsmith_extra={'run_id':run_id})
    result['langsmith'] = {'verified':False}
    if os.getenv('LANGSMITH_API_KEY'):
        try:
            client = Client()
            client.flush()
            remote = client.read_run(run_id, load_child_runs=True)
            url = client.get_run_url(run=remote)
            result['langsmith'] = {'verified':True, 'run_id':str(run_id), 'project':os.getenv('LANGSMITH_PROJECT'),
                                   'url':url, 'child_run_count':len(remote.child_runs or []),
                                   'data_scope':'공개·합성 데이터 요약, 역할별 판단, 검색 평가. 교육 PDF·사진 원본 전송 없음'}
        except Exception as exc:
            result['langsmith'] = {'verified':False, 'error_type':type(exc).__name__}
    (ROOT/'docs/evaluation/agent_integration.json').write_text(json.dumps(result,ensure_ascii=False,indent=2), encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in {'retrieval','plan_hash'}},ensure_ascii=False,indent=2))


if __name__ == '__main__': main()
