"""Reproducible offline evaluation. Approval actor is explicitly a test actor.
No factory devices, recipe changes, deployments or paid APIs are invoked.
"""
import json
import os
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ["LANGSMITH_TRACING"] = "false"
os.environ["LANGCHAIN_TRACING_V2"] = "false"

from app.workbench import Workbench


def main():
    wb = Workbench(ROOT / "var")
    datasets = [d for d in wb.ensure_examples() if d['name'] in {'제품 A–D 합성 공정','UCI SECOM 공개 공정','제품 A–D 합성 검사 이미지'}]
    receipts = []
    for dataset in reversed(datasets):
        if "--images-only" in sys.argv and dataset["modality"] != "image":
            continue
        if '--tabular-only' in sys.argv and dataset['modality'] == 'image':
            continue
        image = dataset["modality"] == "image"
        request = {"dataset_id": dataset["id"], "cohort_mode": "all" if image else "subsets",
                   "question": "불량 재현율, 전처리, 제품 학습 범위와 불균형 대책을 비교",
                   "epochs": 6}
        proposal = wb.propose(request)
        print(f"PROPOSED {dataset['name']}: {proposal['plan']['trial_budget']} trials", flush=True)
        run_id, result = wb.approve_and_run(proposal["id"], proposal["plan_hash"], "G045 자동 평가 시나리오(테스트 승인자)",
            lambda event: print(json.dumps(event, ensure_ascii=False), flush=True))
        target = ROOT / "docs/evaluation"
        target.mkdir(parents=True, exist_ok=True)
        name = "images" if image else "synthetic_process" if dataset["synthetic"] else "secom"
        (target / f"{name}.json").write_text(json.dumps({"run_id": run_id,
            "approval_actor": "자동 평가 시나리오의 테스트 승인자. 현장 엔지니어 승인 증빙이 아님.",
            "plan": proposal["plan"], "result": result}, ensure_ascii=False, indent=2))
        receipts.append({"dataset": name, "run_id": run_id, "trials": len(result["trials"]),
                         "winner": result["winner"]["model"], "baseline_recall": result["baseline_test"]["recall"],
                         "test_recall": result["test"]["recall"], "test_precision": result["test"]["precision"],
                         "test_fpr": result["test"]["fpr"],
                         "gate": result["gate"], "seconds": result["elapsed_seconds"]})
    if "--images-only" in sys.argv or '--tabular-only' in sys.argv:
        receipts = []
        for name in ["synthetic_process", "secom", "images"]:
            saved = json.loads((ROOT / f"docs/evaluation/{name}.json").read_text())
            result = saved["result"]
            receipts.append({"dataset": name, "run_id": saved["run_id"], "trials": len(result["trials"]),
                "winner": result["winner"]["model"], "baseline_recall": result["baseline_test"]["recall"],
                "test_recall": result["test"]["recall"], "test_precision": result["test"]["precision"],
                "test_fpr": result["test"]["fpr"],
                "gate": result["gate"], "seconds": result["elapsed_seconds"]})
    (ROOT / "docs/evaluation/summary.json").write_text(json.dumps({"python": platform.python_version(),
        "platform": platform.platform(), "datasets": receipts}, ensure_ascii=False, indent=2))
    print(json.dumps(receipts, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
