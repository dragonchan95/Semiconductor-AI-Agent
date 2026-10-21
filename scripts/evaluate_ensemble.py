"""Approve and measure the new weighted ensemble on the preserved Windows example."""
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
os.environ['LANGSMITH_TRACING']='false'
os.environ['LANGCHAIN_TRACING_V2']='false'
os.environ['SEMI_LLM_ENABLED']='0'
from app.workbench import Workbench
from app.config import STATE_DIR
from app.ensemble import propose_ensemble

wb=Workbench(STATE_DIR)
source=json.loads((ROOT/'docs/evaluation/windows_llm_synthetic.json').read_text(encoding='utf-8'))['run_id']
p=propose_ensemble(wb,source)
print('Proposed:',p['plan']['ensemble']['weight_count'],'weights; source:',source,flush=True)
run_id,result=wb.approve_and_run(p['id'],p['plan_hash'],'G045 앙상블 기능 자동 재현 검증 (현장 승인 아님)',
    lambda e:print(e,flush=True))
receipt={'run_id':run_id,'plan':p['plan'],'result':result,'scope':'Measured Windows weighted soft voting; automated validation actor approval'}
(ROOT/'docs/evaluation/weighted_ensemble.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
e=result['ensemble']
print(json.dumps({'weights':e['weights_description'],'selected_validation':e['selected']['validation'],
    'single_validation':e['best_single']['validation'],'equal_validation':e['equal']['validation'],
    'test':result['test'],'single_test':e['best_single_test'],'reason':e['selection_reason']},ensure_ascii=False,indent=2))
