"""Fit on train, choose threshold on calibration, select on validation.
Only the selected candidate and declared baseline access the final test.
"""
import itertools
import json
import time
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import ExtraTreesClassifier, HistGradientBoostingClassifier
from sklearn.feature_selection import VarianceThreshold
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from .config import MAX_TRIALS, SEED
from .data import load_frame, split_frame, META
from .metrics import choose_threshold, measure, operational_gate
from .store import digest


def cohorts(products, mode):
    products = sorted(products)
    if mode == "all":
        return [products]
    return [list(c) for n in range(1, len(products) + 1) for c in itertools.combinations(products, n)]


def estimator(name, preprocessing, balance):
    balanced = "balanced" if balance == "weighted" else None
    if name == "logistic":
        model = LogisticRegression(C=.2, max_iter=1500, class_weight=balanced, random_state=SEED)
    elif name == "extra_trees":
        model = ExtraTreesClassifier(n_estimators=80, max_depth=9, min_samples_leaf=3,
                                     class_weight=balanced, n_jobs=1, random_state=SEED)
    elif name == "hist_gradient":
        model = HistGradientBoostingClassifier(max_iter=70, max_leaf_nodes=9,
                     l2_regularization=2, class_weight=balanced, random_state=SEED)
    else:
        raise ValueError(f"지원하지 않는 모델: {name}")
    steps = [("impute", SimpleImputer(strategy="median", keep_empty_features=True)),
             ("variance", VarianceThreshold())]
    if preprocessing == "scaled":
        steps.append(("scale", StandardScaler()))
    elif preprocessing != "median":
        raise ValueError("지원하지 않는 전처리")
    return Pipeline(steps + [("classifier", model)])


def execute(dataset, plan, artifact_dir, on_event=lambda e: None):
    df = load_frame(dataset)
    parts, split_summary = split_frame(df)
    if digest(split_summary) != plan["split_hash"]:
        raise ValueError("승인한 데이터 분할과 실행 분할이 다릅니다")
    targets = plan["target_products"]
    evaluation = {name: idx[np.isin(df.iloc[idx]["product"].astype(str), targets)]
                  for name, idx in parts.items()}
    for name in ["calibration", "validation", "test"]:
        if len(evaluation[name]) == 0 or df.iloc[evaluation[name]].label.nunique() < 2:
            raise ValueError(f"{name} 대상 제품의 정상·불량 표본이 부족합니다")
    if dataset["modality"] == "image":
        from .images import run_images
        return run_images(dataset, df, parts, evaluation, plan, artifact_dir, on_event)
    features = [c for c in df if c not in META]
    x = df[features].to_numpy(dtype=float)
    y = df.label.to_numpy(dtype=int)
    policy = plan["policy"]
    configs = list(itertools.product(plan["cohorts"], plan["models"], plan["preprocessing"], plan["balance"]))
    if len(configs) > MAX_TRIALS:
        raise ValueError("승인한 실험 예산을 초과했습니다")
    rows, fitted, baseline = [], {}, None
    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    start_all = time.perf_counter()
    with threadpool_limits(limits=1):
        for i, (products, model_name, prep, balance) in enumerate(configs):
            idx = parts["train"][np.isin(df.iloc[parts["train"]]["product"].astype(str), products)]
            name = f"trial-{i+1:03d}"
            config = {"products": products, "model": model_name, "preprocessing": prep, "balance": balance}
            if len(idx) < 30 or y[idx].sum() < 4 or len(np.unique(y[idx])) < 2:
                rows.append({"id": name, **config, "status": "skipped", "reason": "학습 불량 표본 부족"})
                continue
            started = time.perf_counter()
            try:
                fitted_model = estimator(model_name, prep, balance).fit(x[idx], y[idx])
                cal = evaluation["calibration"]
                threshold, feasible = choose_threshold(y[cal], fitted_model.predict_proba(x[cal])[:, 1], policy)
                val = evaluation["validation"]
                scores = fitted_model.predict_proba(x[val])[:, 1]
                metrics = measure(y[val], scores, threshold, policy)
                row = {"id": name, **config, "status": "completed", "train_n": len(idx),
                       "train_defects": int(y[idx].sum()), "calibration_feasible": feasible,
                       "validation": metrics, "fit_seconds": time.perf_counter() - started,
                       "validation_fingerprint": digest(sorted(map(int, val)))}
                rows.append(row)
                fitted[name] = (fitted_model, threshold)
                on_event({"type": "TrialCompleted", "trial": name, "model": model_name,
                          "recall": metrics["recall"], "precision": metrics["precision"]})
            except (ValueError, FloatingPointError) as exc:
                rows.append({"id": name, **config, "status": "failed", "reason": str(exc)})
        complete = [r for r in rows if r["status"] == "completed"]
        if not complete:
            raise ValueError("실행 가능한 후보가 없습니다")
        feasible = [r for r in complete if r["calibration_feasible"] and
                    r["validation"]["precision"] >= policy["min_precision"] and
                    r["validation"]["fpr"] <= policy["max_fpr"]]
        pool = feasible or complete
        winner = max(pool, key=lambda r: (r["validation"]["recall"] if feasible else
                                         -r["validation"]["assumed_cost_per_10000"],
                                         r["validation"]["average_precision"], r["id"]))
        test = evaluation["test"]
        best_model, threshold = fitted[winner["id"]]
        test_metrics = measure(y[test], best_model.predict_proba(x[test])[:, 1], threshold, policy)
        # Fixed before-experiment baseline: all products, unweighted logistic,
        # median imputation + scaling, default threshold 0.5.
        baseline_model = estimator("logistic", "scaled", "none").fit(x[parts["train"]], y[parts["train"]])
        baseline = measure(y[test], baseline_model.predict_proba(x[test])[:, 1], .5, policy)
        joblib.dump(best_model, artifact_dir / "champion.joblib")
        prediction = [{"sample_index": int(index), "label": int(y[index]), "score": float(score)}
                      for index, score in zip(test, best_model.predict_proba(x[test])[:, 1])]
    result = {"dataset": {k: dataset[k] for k in ["id", "name", "source", "synthetic", "sha256"]},
              "split": split_summary, "trials": rows, "winner_id": winner["id"], "winner": winner,
              "test": test_metrics, "baseline_test": baseline,
              "test_fingerprint": digest(sorted(map(int, test))), "test_predictions": prediction,
              "selection_feasible": bool(feasible), "gate": operational_gate(test_metrics, policy),
              "elapsed_seconds": time.perf_counter() - start_all,
              "economic_note": "사용자 비용 가정에 따른 시나리오 계산. 실현 수율·영업이익 증가의 증거가 아닙니다.",
              "test_note": "최종 test는 선택에 사용하지 않음. baseline과 validation으로 선택한 후보만 평가.",
              "seed": SEED, "actual_llm_api_cost": 0}
    if not feasible:
        result["gate"] = {"passed": False, "reasons": ["calibration·validation 기준을 함께 만족한 후보 없음"],
                          "action": "배포 보류·학습 데이터와 기준 재검토", "auto_deploy": False}
    (artifact_dir / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return result
