import json
import os
from pathlib import Path
import httpx
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
from .catalog import TABULAR, IMAGE, EXTERNAL, explain_plan
from .advisors import quality_choices


class Policy(BaseModel):
    min_recall: float = Field(default=.90, ge=.01, le=1)
    max_fpr: float = Field(default=.15, ge=0, le=1)
    min_test_defects: int = Field(default=20, ge=3, le=10000)


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
    discovery_id: str | None = None
    discovery_source_run: str | None = None
    epochs: int = Field(default=4, ge=1, le=12)
    policy: Policy = Field(default_factory=Policy)


class Knowledge:
    def __init__(self, directory=None, dense=None, client=None):
        self.docs = json.loads((ROOT / "data/knowledge.json").read_text(encoding='utf-8'))
        self.vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(2, 4))
        self.matrix = self.vectorizer.fit_transform([d["title"] + " " + d["text"] for d in self.docs])
        self.dense = os.getenv('SEMI_LLM_ENABLED', '0') == '1' if dense is None else dense
        self.client = client or httpx.Client(timeout=45)
        self.cache = Path(directory) / 'knowledge-vectors.json' if directory else None
        self.model = os.getenv('SEMI_EMBED_MODEL', 'qwen3-embedding:0.6b')
        self.last_status = {'mode': 'tfidf', 'model': None}

    def embed(self, texts):
        r = self.client.post(os.getenv('OLLAMA_URL', 'http://127.0.0.1:11434')+'/api/embed',
                             json={'model': self.model, 'input': texts})
        r.raise_for_status()
        return np.asarray(r.json()['embeddings'], dtype=float)

    @traceable(name="knowledge.retrieve")
    def search(self, query, k=4):
        if self.dense:
            try:
                signature = digest({'docs': self.docs, 'model': self.model})
                cached = json.loads(self.cache.read_text(encoding='utf-8')) if self.cache and self.cache.exists() else {}
                if cached.get('signature') != signature:
                    vectors = self.embed([d['title']+' '+d['text'] for d in self.docs])
                    cached = {'signature': signature, 'vectors': vectors.tolist()}
                    if self.cache:
                        self.cache.parent.mkdir(parents=True, exist_ok=True)
                        self.cache.write_text(json.dumps(cached), encoding='utf-8')
                scores = cosine_similarity(self.embed([query]), np.asarray(cached['vectors']))[0]
                self.last_status = {'mode': 'dense', 'model': self.model, 'document_count': len(self.docs)}
            except (httpx.HTTPError, ValueError, KeyError):
                scores = cosine_similarity(self.vectorizer.transform([query]), self.matrix)[0]
                self.last_status = {'mode': 'tfidf_fallback', 'note': '임베딩 연결 실패'}
        else:
            scores = cosine_similarity(self.vectorizer.transform([query]), self.matrix)[0]
        return [{**self.docs[i], "score": round(float(scores[i]), 6)}
                for i in np.argsort(-scores)[:k] if scores[i] > 0]


@dataclass
class Dependencies:
    store: object
    knowledge: Knowledge
    advisor: object = None


class PlanState(TypedDict, total=False):
    request: dict
    dataset: dict
    audit: dict
    evidence: list[dict]
    split: dict
    plan: dict
    reasons: list[str]
    events: list[dict]
    explanation: dict
    agent_outputs: list[dict]


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
        evidence = deps.knowledge.search(query, 8)
        discovery_id=state['request'].get('discovery_id')
        if discovery_id:
            d=deps.store.discovery(discovery_id)
            if d['dataset_id']!=state['dataset']['id']or d['dataset_sha256']!=state['dataset']['sha256']:
                raise ValueError('탐색한 데이터와 현재 데이터가 다릅니다')
            evidence=evidence+d['evidence']
        qa = deps.advisor.advise('DataQualityAgent', state['audit'], quality_choices(state['audit']), evidence) if deps.advisor else {'role': 'DataQualityAgent', 'status': 'disabled'}
        return {"evidence": evidence, 'agent_outputs': [qa], "events": state["events"] + [{"type": "KnowledgeRetrieved", "count": len(evidence), **deps.knowledge.last_status}]}

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
        names = req.get('models') or list(IMAGE if image else TABULAR)
        allowed = set(IMAGE if image else TABULAR)
        if source_run and not image:
            source_model=deps.store.run(source_run)['result']['winner']['model']
            if source_model in EXTERNAL: allowed.add(source_model)
        if req.get('discovery_id') and not image:
            d=deps.store.discovery(req['discovery_id'])
            allowed.update(x['model']for x in d['models']if x['model']in EXTERNAL)
        if not names or not set(names) <= allowed or len(names) != len(set(names)):
            raise ValueError("모델 후보가 유효하지 않습니다")
        if image and not any(n != "autoencoder" for n in names):
            raise ValueError("비교 baseline을 위해 지도학습 이미지 모델이 하나 이상 필요합니다")
        prep = req.get("preprocessing") or ((["gray"] if req["cohort_mode"] == "subsets" else
                                             ["gray", "contrast"]) if image else ["auto"])
        balance = req.get("balance") or (["weighted"] if image else ["none", "weighted"])
        if not set(prep) <= ({"gray", "contrast"} if image else {"median", "scaled", "auto"}) or not prep:
            raise ValueError("전처리 후보가 유효하지 않습니다")
        if not set(balance) <= {"none", "weighted"} or not balance:
            raise ValueError("불균형 정책이 유효하지 않습니다")
        count = len(combinations) * len(names) * len(prep) * len(balance)
        staged = not image and req['cohort_mode'] == 'subsets' and not req.get('models')
        if staged:
            count = len(names) * len(prep) * len(balance) + min(2, len(names)) * (len(combinations)-1)
        if count > MAX_TRIALS:
            raise ValueError(f"후보 {count}개가 예산 {MAX_TRIALS}개를 넘습니다. 전체 제품 학습 또는 후보 수를 줄여 주세요")
        plan = {"dataset_id": state["dataset"]["id"], "dataset_sha256": state["dataset"]["sha256"],
                "image_digest": state["dataset"].get("image_digest"), "cohorts": combinations,
                "target_products": target, "models": names, "preprocessing": prep, "balance": balance,
                "epochs": req["epochs"], "policy": req["policy"], "trial_budget": count,
                "split_hash": digest(state["split"]), "seed": SEED,
                "selection": "Validation threshold and candidate selection; final Test once",
                "model_backend": "local_sklearn_or_pytorch", "auto_deploy": False,
                "management_source_run": source_run, "discovery_id": req.get("discovery_id"), "discovery_source_run": req.get("discovery_source_run")}
        if req.get('discovery_id'):
            source=deps.store.run(req.get('discovery_source_run'))
            if source['status']!='completed' or source['result']['dataset']['id']!=state['dataset']['id']:
                raise ValueError('외부 후보 비교의 기준 실험이 유효하지 않습니다')
            plan['discovery_incumbent']=source['result']['winner']['model']
            if plan['discovery_incumbent'] not in names:
                raise ValueError('새 모델 비교에는 기존 후보 알고리즘을 포함해야 합니다')
        plan['search_strategy'] = 'model_then_cohort' if staged else 'grid'
        reasons = list(quality["warnings"]) + [
            f"제품 학습 조합 {len(combinations)}개와 모델 {len(names)}개 등 최대 {count}개 실험입니다.",
            "모든 학습 조합은 동일한 대상 제품의 validation/test 표본으로 평가합니다.",
            "test는 모델 선택에 쓰지 않고 선택된 후보와 사전 정의 baseline만 마지막에 평가합니다.",
            "입력값은 교육용 비교 목표입니다. 회사 양산 기준은 현장 담당자가 별도 정의해야 합니다.",
            "승인은 이 계획의 로컬 학습 실행만 허용합니다. 장비·recipe 변경과 운영 배포는 수행하지 않습니다."]
        if image:
            reasons.append("ResNetSmall/VGGSmall은 자체 축소 구조를 scratch 학습합니다. 표준 사전학습 모델 비교가 아닙니다.")
            reasons.append("Autoencoder는 정상 학습 표본만 사용합니다. 라벨이 있는 Validation에서 판정 경계값을 선택합니다.")
        elif staged:
            reasons.append('전체 제품에서 모든 모델을 비교한 뒤 validation 상위 서로 다른 두 모델의 제품 학습 조합을 확장합니다. 완전탐색은 아니며 같은 validation의 반복 사용에 따른 선택 편향이 남습니다.')
        explanation = explain_plan(quality, plan)
        choices = {n: (IMAGE[n][1] if image else (TABULAR.get(n) or EXTERNAL[n])[2]) for n in names}
        advice = deps.advisor.advise('ExperimentPlannerAgent', {'audit': quality, 'budget': count,
                'strategy': plan['search_strategy']}, choices, state['evidence']) if deps.advisor else {'role': 'ExperimentPlannerAgent', 'status': 'disabled'}
        plan['llm_priorities'] = advice.get('priority_codes', [])
        return {"plan": plan, "reasons": reasons,
                "explanation": explanation,
                'agent_outputs': state['agent_outputs']+[advice],
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
