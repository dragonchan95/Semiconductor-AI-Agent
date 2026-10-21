"""Replay a synthetic experiment locally without replacing the original Mac receipt."""
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
os.environ['LANGSMITH_TRACING']='false'
os.environ['LANGCHAIN_TRACING_V2']='false'
os.environ['SEMI_LLM_ENABLED']='0'
from app.config import STATE_DIR
from app.workbench import Workbench

wb=Workbench(STATE_DIR)
ds=next(d for d in wb.ensure_examples() if d['synthetic'] and d['modality']=='tabular')
p=wb.propose({'dataset_id':ds['id'],'cohort_mode':'subsets','epochs':6})
print('Approved replay by automated validation actor: '+str(p['plan']['trial_budget'])+' trials',flush=True)
run_id,result=wb.approve_and_run(p['id'],p['plan_hash'],'G045 Windows 자동 재현 검증 (실제 현장 승인 아님)',
    lambda e:print(e.get('type'),e.get('trial',''),flush=True))
receipt={'run_id':run_id,'plan':p['plan'],'result':result,
         'scope':'New Windows replay. Original Mac receipts remain unchanged.'}
(ROOT/'docs/evaluation/windows_synthetic.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'run_id':run_id,'winner':result['winner']['model'],'test':result['test']},ensure_ascii=False),flush=True)
