"""Run a local LLM-as-a-Judge against measured facts and labelled challenge cases."""
import json
import os
from pathlib import Path
import sys
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
os.environ['LANGSMITH_TRACING']='false'
os.environ['LANGCHAIN_TRACING_V2']='false'
import app
from app.judge import LocalJudge

record=json.loads((ROOT/'docs/evaluation/windows_llm_synthetic.json').read_text(encoding='utf-8'))
r=record['result'];a=r['test'];b=r['baseline_test']
reference={'selected_model':'CatBoost','training_products':r['winner']['products'],
    'test_defects':a['positive_count'],'detected_defects':a['tp'],'missed_defects':a['fn'],
    'test_normals':a['tn']+a['fp'],'false_positives':a['fp'],'recall_percent':round(100*a['recall'],1),
    'baseline_detected_defects':b['tp'],'baseline_false_positives':b['fp'],
    'demo_recall_goal_percent':90,'demo_false_positive_limit_percent':15,
    'goal_scope':'Educational demo goals only. No common industry numerical standard was verified.',
    'production_approved':False,'manufacturing_yield_improvement_measured':False,
    'financial_benefit_measured':False,'data_scope':'synthetic sensor dataset'}
reference_ko=(f'선택 모델: CatBoost. 학습 제품: A+B+C. Test의 실제 불량 {a["positive_count"]}개 중 '
    f'발견 {a["tp"]}개, 놓침 {a["fn"]}개. 실제 정상 {a["tn"]+a["fp"]}개 중 정상 오판 {a["fp"]}개. '
    f'기본 모델 발견 {b["tp"]}개와 정상 오판 {b["fp"]}개에서 후보 발견 {a["tp"]}개와 정상 오판 {a["fp"]}개로 변화. '
    f'Recall {100*a["recall"]:.1f}%는 90%보다 낮아서 교육용 목표 미달. '
    '90%·15%는 이 실험의 교육용 목표이며 반도체 회사의 공통 기준이 아님. '
    '데이터는 합성이며 실제 공장 수율·금액 효과는 측정하지 않았음. 양산 적용 승인 없음.')
correct=f'선택 후보는 CatBoost이며 Test 불량 {a["positive_count"]}개 중 {a["tp"]}개를 찾았습니다. Recall은 {100*a["recall"]:.1f}%로 교육용 목표 90%에 못 미쳐 추가 검증이 필요합니다.'
cases=[
    ('correct_summary',correct,'pass'),
    ('correct_tradeoff',f'기본 모델보다 불량 발견은 {b["tp"]}개에서 {a["tp"]}개로 늘었지만 정상 오판도 {b["fp"]}개에서 {a["fp"]}개로 늘었습니다.','pass'),
    ('wrong_defect_count',f'선택 후보는 CatBoost이며 Test 불량 {a["positive_count"]}개 중 {a["tp"]+3}개를 찾았습니다.','fail'),
    ('wrong_false_positives','이번 후보의 정상 오판은 0개이며 정상 오판 없이 불량을 찾았습니다.','fail'),
    ('wrong_selected_model','이번 실험에서는 AdaBoost가 최종 선택 후보입니다.','fail'),
    ('unsupported_factory_effect','이번 실험으로 실제 반도체 공장의 제조 수율 증가가 입증되었습니다.','fail'),
    ('unsupported_industry_standard','Recall 90%는 모든 반도체 회사에 공통으로 적용되는 양산 승인 기준입니다.','fail'),
    ('wrong_goal_interpretation',f'후보 Recall {100*a["recall"]:.1f}%는 이번 교육용 목표 90%를 충족했습니다.','fail')]
if '--smoke' in sys.argv:cases=[cases[0],cases[2],cases[4]]
judge=LocalJudge();rows=[]
for ident,answer,expected in cases:
    # Gold labels and case identifiers are not sent to the LLM.
    output=judge.evaluate(reference_ko,answer)
    aligned=output.get('status')=='evaluated' and output.get('verdict')==expected
    rows.append({'case':ident,'answer':answer,'expected_verdict':expected,'judge':output,'label_match':aligned})
    print(ident,output.get('status'),output.get('verdict'),f'label_match={aligned}',flush=True)
evaluated=sum(x['judge']['status']=='evaluated' for x in rows)
false_accepts=sum(x['expected_verdict']=='fail' and x['judge'].get('verdict')=='pass' for x in rows)
false_rejects=sum(x['expected_verdict']=='pass' and x['judge'].get('verdict')=='fail' for x in rows)
class_rates=[sum(x['label_match'] for x in rows if x['expected_verdict']==label)/sum(x['expected_verdict']==label for x in rows)
             for label in ['pass','fail'] if any(x['expected_verdict']==label for x in rows)]
receipt={'verified_at':datetime.now(timezone.utc).isoformat(),'model':judge.model,'backend':'local Ollama',
    'reference_source':'docs/evaluation/windows_llm_synthetic.json','reference':reference,
    'case_count':len(rows),'evaluated_count':evaluated,'label_match_count':sum(x['label_match'] for x in rows),
    'label_match_rate':sum(x['label_match'] for x in rows)/len(rows),'gold_labels_sent_to_judge':False,
    'false_accepts':false_accepts,'false_rejects':false_rejects,'invalid_or_failed_responses':len(rows)-evaluated,
    'balanced_label_match_rate':sum(class_rates)/len(class_rates),
    'reference_text_sent_to_judge':reference_ko,'prompt_revision':'Korean facts + separate few-shot examples + binary support verdict',
    'cases':rows,'limitations':['Small hand-authored development set used to refine this prompt, not an independent real-world benchmark.',
        'Same model family used for assistant and evaluator; correlated errors remain possible.',
        'LLM judge decisions are advisory and do not replace deterministic metric/approval checks.']}
target='llm_judge_smoke.json' if '--smoke' in sys.argv else 'llm_judge.json'
(ROOT/'docs/evaluation'/target).write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in receipt.items() if k not in {'cases','reference'}},ensure_ascii=False,indent=2))
raise SystemExit(0 if evaluated==len(rows) else 1)
