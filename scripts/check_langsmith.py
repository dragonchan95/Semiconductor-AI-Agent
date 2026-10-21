"""Create a real proposal trace and confirm its child runs by API readback."""
import json
import os
from pathlib import Path
import sys
import time
from uuid import uuid4

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import app  # Loads the local .env before importing traced modules.
from langsmith import Client, tracing_context
from app.config import STATE_DIR
from app.workbench import Workbench


def main():
    if not os.getenv('LANGSMITH_API_KEY'):
        raise SystemExit('Set LANGSMITH_API_KEY in the local .env first. No key was printed.')
    client = Client()
    project = os.getenv('LANGSMITH_PROJECT', 'Semiconductor-AI-Agent-G045')
    wb = Workbench(STATE_DIR)
    wb.ensure_examples()
    dataset = next(d for d in wb.store.datasets() if d['synthetic'] and d['modality'] == 'tabular')
    run_id = uuid4()
    with tracing_context(enabled=True, client=client, project_name=project):
        proposal = wb.propose({'dataset_id': dataset['id'], 'cohort_mode': 'all',
                               'models': ['logistic'], 'balance': ['none']},
                              langsmith_extra={'run_id': run_id})
    client.flush()
    root = None
    for _ in range(12):
        try:
            root = client.read_run(run_id, load_child_runs=True)
            if root.end_time and root.child_runs:
                break
        except Exception:
            pass
        time.sleep(2)
    if root is None or not root.child_runs:
        raise SystemExit('Trace readback failed. Check APAC endpoint, key and read permissions.')
    def flatten(run):
        return [{'name': run.name, 'error': bool(run.error)}] + [
            item for child in (run.child_runs or []) for item in flatten(child)]
    receipt = {'verified_at': root.start_time.isoformat(), 'endpoint': client.api_url,
               'project': project, 'root_run_id': str(run_id), 'root_name': root.name,
               'readback_verified': True, 'child_runs': flatten(root)[1:],
               'llm_enabled': wb.advisor.enabled, 'agent_outputs': proposal.get('agent_outputs', []),
               'scope': 'Actual proposal and child runs; no training, deployment or LLM-as-a-Judge claim.'}
    target = ROOT / 'docs/evaluation/langsmith_check.json'
    target.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
