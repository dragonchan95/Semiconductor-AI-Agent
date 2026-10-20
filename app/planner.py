import json
from dataclasses import dataclass
from typing import TypedDict

import numpy as np
from langgraph.graph import StateGraph, END
from langsmith import traceable
from pydantic import BaseModel, Field
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .config import MAX_TRIALS, ROOT, SEED
from .data import audit_frame, load_frame, split_frame
from .experiments import cohorts
from .store import digest


class Policy(BaseModel):
    min_precision: float = Field(default=.25, ge=.01, le=1)
    max_fpr: float = Field(default=.15, ge=0, le=1)
    miss_cost: float = Field(default=100000, gt=0, le=1e10)
    false_alarm_cost: float = Field(default=1000, ge=0, le=1e10)


class ProposalRequest(BaseModel):
    dataset_id: str
    question: str = Field(default="불량 재현율과 제품별 학습 조합, 불균형 대책을 비교해줘", max_length=3000)
    cohort_mode: str = Field(default="subsets", pattern="^(all|subsets)$")
    target_products: list[str] | None = None
    training_products: list[str] | None = None
    management_source_run: str | None = None
    models: list[str] | None = None
    preprocessing: list[str] | None = None
    balance: list[str] | None = None
    epochs: int = Field(default=4, ge=1, le=12)
    policy: Policy = Field(default_factory=Policy)


class Knowledge:
    def __init__(self):
        self.docs = json.loads((ROOT / "data/knowledge.json").read_text())
        self.vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(2, 4))
        self.matrix = self.vectorizer.fit_transform([d["title"] + " " + d["text"] for d in self.docs])

    @traceable(name="knowledge.retrieve")
    def search(self, query, k=4):
        scores = cosine_similarity(self.vectorizer.transform([query]), self.matrix)[0]
        return [{**self.docs[i], "score": round(float(scores[i]), 6)}
                for i in np.argsort(-scores)[:k] if scores[i] > 0]


@dataclass
class Dependencies:
    store: object
    knowledge: Knowledge


class PlanState(TypedDict, total=False):
    request: dict
    dataset: dict
    audit: dict
    evidence: list[dict]
    split: dict
    plan: dict
    reasons: list[str]
    events: list[dict]


def build_planner(deps):
    @traceable(name="DataQualityAgent")
    def audit(state):
        dataset = deps.store.dataset(state["request"]["dataset_id"])
        frame = load_frame(dataset)
        quality = audit_frame(frame, dataset["modality"])
        _, split = split_frame(frame)
        return {"dataset": dataset, "audit": quality, "split": split,
                "events": [{"type": "DataAudited", "rows": quality["rows"]}]}

    @traceable(name="KnowledgeAgent")
    def retrieve(state):
        query = state["request"]["question"] + " 불균형 누수 방지 제품별 승인 " + state["dataset"]["modality"]
        evidence = deps.knowledge.search(query)
        return {"evidence": evidence, "events": state["events"] + [{"type": "KnowledgeRetrieved", "count": len(evidence)}]}

    @traceable(name="ExperimentPlannerAgent")
    def plan(state):
        req, quality = state["request"], state["audit"]
        image = state["dataset"]["modality"] == "image"
        products = sorted(quality["products"])
        target = req.get("target_products") or products
        if not set(target) <= set(products) or not target:
            raise ValueError("평가 대상 제품이 데이터에 없습니다")
        training = req.get('training_products') or products
        if not training or not set(training) <= set(products):
            raise ValueError('학습 제품이 데이터에 없습니다')
        combinations = cohorts(training, req["cohort_mode"])
        source_run = req.get('management_source_run')
        if source_run and deps.store.run(source_run)['status'] != 'completed':
            raise ValueError('모델 관리의 기준 실행이 완료되지 않았습니다')
        names = req.get("models") or (["resnet_small", "vgg_small", "autoencoder"] if image else
                                     (["logistic", "random_forest"] if len(products) > 2 else
                                      ["logistic", "random_forest", "hist_gradient"]))
        allowed = {"resnet_small", "vgg_small", "autoencoder"} if image else {"logistic", "random_forest", "hist_gradient"}
        if not names or not set(names) <= allowed or len(names) != len(set(names)):
            raise ValueError("모델 후보가 유효하지 않습니다")
        if image and not any(n != "autoencoder" for n in names):
            raise ValueError("비교 baseline을 위해 지도학습 이미지 모델이 하나 이상 필요합니다")
        prep = req.get("preprocessing") or ((["gray"] if req["cohort_mode"] == "subsets" else
                                             ["gray", "contrast"]) if image else ["scaled"])
        balance = req.get("balance") or (["weighted"] if image else ["none", "weighted"])
        if not set(prep) <= ({"gray", "contrast"} if image else {"median", "scaled"}) or not prep:
            raise ValueError("전처리 후보가 유효하지 않습니다")
        if not set(balance) <= {"none", "weighted"} or not balance:
            raise ValueError("불균형 정책이 유효하지 않습니다")
        count = len(combinations) * len(names) * len(prep) * len(balance)
        if count > MAX_TRIALS:
            raise ValueError(f"후보 {count}개가 예산 {MAX_TRIALS}개를 넘습니다. 전체 제품 학습 또는 후보 수를 줄여 주세요")
        plan = {"dataset_id": state["dataset"]["id"], "dataset_sha256": state["dataset"]["sha256"],
                "image_digest": state["dataset"].get("image_digest"), "cohorts": combinations,
                "target_products": target, "models": names, "preprocessing": prep, "balance": balance,
                "epochs": req["epochs"], "policy": req["policy"], "trial_budget": count,
                "split_hash": digest(state["split"]), "seed": SEED,
                "selection": "calibration threshold; validation selection; final test once",
                "model_backend": "local_sklearn_or_pytorch", "auto_deploy": False,
                "management_source_run": source_run}
        reasons = list(quality["warnings"]) + [
            f"제품 학습 조합 {len(combinations)}개와 모델 {len(names)}개 등 최대 {count}개 실험입니다.",
            "모든 학습 조합은 동일한 대상 제품의 validation/test 표본으로 평가합니다.",
            "test는 모델 선택에 쓰지 않고 선택된 후보와 사전 정의 baseline만 마지막에 평가합니다.",
            "비용은 입력한 미탐·오탐 가정에 따른 분류 손실입니다. 수율·영업이익 향상을 확정하지 않습니다.",
            "승인은 이 계획의 로컬 학습 실행만 허용합니다. 장비·recipe 변경과 운영 배포는 수행하지 않습니다."]
        if image:
            reasons.append("ResNetSmall/VGGSmall은 자체 축소 구조를 scratch 학습합니다. 표준 사전학습 모델 비교가 아닙니다.")
            reasons.append("Autoencoder는 정상 학습 표본만 사용합니다. 라벨이 있는 calibration에서 threshold를 선택합니다.")
        return {"plan": plan, "reasons": reasons,
                "events": state["events"] + [{"type": "PlanProposed", "trial_count": count}]}

    graph = StateGraph(PlanState)
    graph.add_node("data_quality", audit)
    graph.add_node("knowledge", retrieve)
    graph.add_node("experiment_plan", plan)
    graph.set_entry_point("data_quality")
    graph.add_edge("data_quality", "knowledge")
    graph.add_edge("knowledge", "experiment_plan")
    graph.add_edge("experiment_plan", END)
    return graph.compile()
