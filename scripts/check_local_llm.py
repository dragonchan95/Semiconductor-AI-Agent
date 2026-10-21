"""Verify real Qwen responses for the three existing roles without model training."""
import json
import os
from pathlib import Path
import sys
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
os.environ['LANGSMITH_TRACING']='false'
os.environ['LANGCHAIN_TRACING_V2']='false'
import app
import httpx
from app.advisors import LocalAdvisor, result_choices
from app.config import STATE_DIR
from app.workbench import Workbench


class Recorder:
    def __init__(self):self.client=httpx.Client(timeout=150);self.responses=[]
    def post(self,*args,**kwargs):
        r=self.client.post(*args,**kwargs)
        self.responses.append({'status':r.status_code,'body':r.text})
        return r


recorder=Recorder()
wb=Workbench(STATE_DIR,advisor=LocalAdvisor(enabled=True,client=recorder))
ds=next(d for d in wb.ensure_examples() if d['synthetic'] and d['modality']=='tabular')
p=wb.propose({'dataset_id':ds['id'],'cohort_mode':'all',
    'question':'센서 결측과 불량 불균형을 점검하고 선형·트리 모델의 비교 계획과 근거를 설명해줘'})
saved=json.loads((ROOT/'docs/evaluation/windows_synthetic.json').read_text(encoding='utf-8'))['result']
critic=wb.advisor.advise('ResultCriticAgent',{'winner':saved['winner']['model'],
    'test':saved['test'],'gate':saved['gate']},result_choices(saved),p['evidence'])
outputs=p['agent_outputs']+[critic]
receipt={'verified_at':datetime.now(timezone.utc).isoformat(),'model':wb.advisor.model,
    'backend':'Ollama on localhost','course_reference':'Week 5 Qwen/Qwen2.5-1.5B-Instruct; Q4 quantized base without HR LoRA',
    'agent_outputs':outputs,'all_roles_verified':all(o['status']=='verified' for o in outputs),
    'retrieval':wb.knowledge.last_status,'training_started':False,
    'scope':'Real local inference and allowed code/source validation, not an LLM-as-a-Judge evaluation.'}
(ROOT/'var/local-llm-raw.json').write_text(json.dumps(recorder.responses,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'docs/evaluation/local_llm_check.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(receipt,ensure_ascii=False,indent=2))
raise SystemExit(0 if receipt['all_roles_verified'] else 1)
