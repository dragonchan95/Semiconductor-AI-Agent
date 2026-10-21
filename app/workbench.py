"""Reusable experiment engine for a local API, notebook or enterprise cloud."""
import json
from pathlib import Path

import pandas as pd
from langsmith import traceable

from .data import (audit_frame, file_hash, generate_demo, import_secom,
                   image_digest, load_frame)
from .experiments import execute
from .planner import Dependencies, Knowledge, ProposalRequest, build_planner
from .store import Store
from .advisors import LocalAdvisor, result_choices


class Workbench:
    def __init__(self, directory, knowledge=None, advisor=None, store=None):
        self.directory = Path(directory)
        self.store = store or Store(self.directory)
        self.knowledge = knowledge or Knowledge(self.directory)
        self.advisor = advisor or LocalAdvisor()
        self.planner = build_planner(Dependencies(self.store, self.knowledge, self.advisor))

    def register(self, path, name, source, synthetic=False, modality="tabular"):
        path = Path(path).resolve()
        frame = pd.read_csv(path)
        audit = audit_frame(frame, modality)
        payload = {"name": name, "path": str(path), "source": source, "synthetic": synthetic,
                   "sha256": file_hash(path), "modality": modality, "audit": audit}
        if modality == "image":
            from .images import load_images
            load_images(frame, path.parent, "gray")
            payload["image_digest"] = image_digest(frame, path.parent)
        return self.store.add_dataset(payload)

    def ensure_examples(self):
        known = {d["name"] for d in self.store.datasets()}
        if "제품 A–D 합성 공정" not in known:
            path = generate_demo(self.directory / "examples/process")
            self.register(path, "제품 A–D 합성 공정", "자체 생성 합성 데이터, 실제 반도체 측정값 아님", True)
        if "UCI SECOM 공개 공정" not in known:
            path = import_secom(self.directory / "examples")
            self.register(path, "UCI SECOM 공개 공정", "https://archive.ics.uci.edu/dataset/179/secom", False)
        if "제품 A–D 합성 검사 이미지" not in known:
            from .images import generate_images
            path = generate_images(self.directory / "examples/image")
            self.register(path, "제품 A–D 합성 검사 이미지", "자체 생성 결함 패턴 데모, 실제 SEM/wafer 이미지 아님", True, "image")
        return self.store.datasets()

    @traceable(name="experiment.propose")
    def propose(self, request):
        if not isinstance(request, ProposalRequest):
            request = ProposalRequest.model_validate(request)
        state = self.planner.invoke({"request": request.model_dump()})
        return self.store.add_proposal(state["plan"], {
            "audit": state["audit"], "explanation": state.get("explanation"), "agent_outputs": state.get("agent_outputs", []), "split": state["split"], "evidence": state["evidence"],
            "reasons": state["reasons"], "events": state["events"], "question": request.question,
            "dataset_name": state["dataset"]["name"], "synthetic": state["dataset"]["synthetic"]})

    @traceable(name="experiment.execute_approved")
    def perform(self, proposal_id, run_id, on_event=lambda e: None):
        proposal = self.store.proposal(proposal_id)
        run = self.store.run(run_id)
        if proposal["status"] != "running" or run["proposal_id"] != proposal_id:
            raise ValueError("승인된 실행 토큰이 아닙니다")
        dataset = self.store.dataset(proposal["plan"]["dataset_id"])
        if dataset["sha256"] != proposal["plan"]["dataset_sha256"] or dataset.get("image_digest") != proposal["plan"].get("image_digest"):
            raise ValueError("승인한 데이터 버전과 등록 데이터 버전이 다릅니다")
        try:
            if proposal['plan'].get('ensemble'):
                from .ensemble import execute_ensemble
                result = execute_ensemble(self,dataset,proposal['plan'],self.directory/'runs'/run_id,on_event)
            else:
                result = execute(dataset, proposal["plan"], self.directory / "runs" / run_id, on_event)
            result['agent_review'] = self.advisor.advise('ResultCriticAgent', {
                'winner': result['winner']['model'], 'validation': result['winner']['validation'],
                'test': result['test'], 'gate': result['gate']}, result_choices(result), proposal['evidence'])
            if proposal['plan'].get('management_source_run'):
                products = result['winner']['products']
                result['model_version'] = {'id': 'model-'+run_id, 'product': '+'.join(products),
                    'run_id': run_id, 'source_run': proposal['plan']['management_source_run'],
                    'artifact': f'runs/{run_id}/champion.joblib', 'model': result['winner']['model'],
                    'status': '후보 검토 가능' if result['gate']['passed'] else '후보 검토 보류',
                    'test_recall': result['test']['recall'], 'test_fpr': result['test']['fpr'],
                    'auto_deployed': False}
            from .discovery import register_results
            register_results(self, proposal, run_id, result)
            self.store.finish_run(run_id, result)
            on_event({"type": "RunCompleted", "run_id": run_id})
            return result
        except Exception as exc:
            self.store.finish_run(run_id, {"error": str(exc)}, failed=True)
            on_event({"type": "RunFailed", "run_id": run_id, "error": str(exc)})
            raise

    def approve_and_run(self, proposal_id, plan_hash, engineer, on_event=lambda e: None):
        """Notebook entry point. Call only after an engineer reviewed the proposal."""
        self.store.decide(proposal_id, plan_hash, True, engineer)
        run_id = self.store.claim_run(proposal_id)
        return run_id, self.perform(proposal_id, run_id, on_event)
