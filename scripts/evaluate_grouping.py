"""Measure approved full product partition comparison without replacing prior receipts."""
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(ROOT))
os.environ['LANGSMITH_TRACING']='false';os.environ['LANGCHAIN_TRACING_V2']='false';os.environ['SEMI_LLM_ENABLED']='0'
from app.workbench import Workbench
from app.config import STATE_DIR
from app.grouping import propose_grouping

wb=Workbench(STATE_DIR)
source=json.loads((ROOT/'docs/evaluation/windows_llm_synthetic.json').read_text(encoding='utf-8'))['run_id']
p=propose_grouping(wb,source)
print('Product partitions:',len(p['plan']['grouping']['partitions']),flush=True)
run,result=wb.approve_and_run(p['id'],p['plan_hash'],'G045 제품 그룹 자동재현 검증 (현장 승인 아님)',lambda e:print(e,flush=True))
receipt={'run_id':run,'plan':p['plan'],'result':result,'scope':'Real Windows experiment; automated validation actor approval'}
(ROOT/'docs/evaluation/product_partitions.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
g=result['grouping']
print(json.dumps({'selected':g['selected'],'baselines':g['tested_baselines'],'gate':result['gate']},ensure_ascii=False,indent=2))
