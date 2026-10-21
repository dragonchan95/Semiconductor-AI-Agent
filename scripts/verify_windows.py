"""Capture a clean test receipt without PowerShell's native stderr formatting."""
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parent.parent
env={**os.environ,'LANGSMITH_TRACING':'false','LANGCHAIN_TRACING_V2':'false','SEMI_LLM_ENABLED':'0','SEMI_DENSE_ENABLED':'0','PYTHONUTF8':'1'}
result=subprocess.run([sys.executable,'-X','utf8','-m','unittest','discover','-s','tests','-v'],
                      cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8')
(ROOT/'docs/evaluation/tests-windows.txt').write_text(result.stdout,encoding='utf-8')
match=re.search(r'Ran (\d+) tests in ([\d.]+)s',result.stdout)
receipt={'verified_at':datetime.now(timezone.utc).isoformat(),'platform':platform.platform(),
         'python':platform.python_version(),'tests_passed':result.returncode==0,
         'test_count':int(match.group(1)) if match else None,
         'seconds':float(match.group(2)) if match else None,
         'scope':'Windows unit/API tests including approved ensemble, product partitions and FAISS retrieval/cache/fallback; real model and external-document integration receipts are separate.'}
(ROOT/'docs/evaluation/windows_check.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(receipt,ensure_ascii=False,indent=2))
if result.returncode:print(result.stdout)
raise SystemExit(result.returncode)
