"""Actual candidate training with an explicitly labeled automatic test actor."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from app.workbench import Workbench
from app.monitoring import prepare_changed_demo, assess, product_plans, compare_strategies
from app.impact import compare_impact

wb=Workbench(ROOT/'var')
baseline=json.loads((ROOT/'docs/evaluation/synthetic_process.json').read_text(encoding='utf-8'))
dataset=prepare_changed_demo(wb)
review=assess(wb,baseline['run_id'],dataset['id'])
assert review['verdict']=='재학습 필요', review
before=len(wb.store.runs())
plans=product_plans(wb,review['id'])
assert len(wb.store.runs())==before, '계획만 만들 때 학습해서는 안 됩니다'
assert len(plans['proposals'])==5
receipts=[]
for p in plans['proposals']:
    run_id,result=wb.approve_and_run(p['id'],p['plan_hash'],'G045 자동 검증 시나리오(테스트 승인자)')
    assert Path(ROOT/'var'/result['model_version']['artifact']).exists()
    receipts.append({'run_id':run_id,'plan':p['plan'],'result':result})
comparison=compare_strategies(wb,[r['run_id'] for r in receipts])
receipt={'comparison':comparison,'approval_actor':'자동 검증용 테스트 승인자. 현장 승인 실적 아님.',
         'review':review,'training_started_during_planning':False,'runs':receipts,'versions':[v for v in wb.store.versions() if v['run_id'] in {r['run_id'] for r in receipts}]}
(ROOT/'docs/evaluation/model_management.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2), encoding='utf-8')
cases={}
for name in ['synthetic_process','secom','images']:
    d=json.loads((ROOT/f'docs/evaluation/{name}.json').read_text(encoding='utf-8'))
    cases[name]=compare_impact(d['result'],{'quantity':1000,'defect_rate':.10},d['plan']['policy'])
(ROOT/'docs/evaluation/presentation_cases.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2), encoding='utf-8')
print(json.dumps({'review':review['verdict'],'old_recall':review['previous_recall'],
                 'new_recall':review['current']['recall'],'recommendations':[{k:r[k] for k in ['product','selected_strategy','recommendation']} for r in comparison['products']],
                 'scenario':cases['synthetic_process']['delta']},ensure_ascii=False,indent=2))
