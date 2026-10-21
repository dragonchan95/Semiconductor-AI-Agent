"""Fit on train; tune threshold and choose candidate on Validation.
Only the selected candidate and declared baseline access the final test.
"""
import itertools
import json
import time
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import (RandomForestClassifier, HistGradientBoostingClassifier,
                              GradientBoostingClassifier, AdaBoostClassifier, ExtraTreesClassifier)
from sklearn.naive_bayes import GaussianNB
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.utils.class_weight import compute_sample_weight
from sklearn.feature_selection import VarianceThreshold
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from .config import MAX_TRIALS, SEED
from .data import load_frame, split_frame, META
from .metrics import choose_threshold, measure, operational_gate, meets_goals, selection_key
from .store import digest
from .catalog import pipeline_reason


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
        model = ExtraTreesClassifier(n_estimators=80, max_depth=9, min_samples_leaf=3, class_weight=balanced, n_jobs=1, random_state=SEED)
    elif name == "gaussian_nb":
        model = GaussianNB(var_smoothing=1e-8)
    elif name == "random_forest":
        model = RandomForestClassifier(n_estimators=80, max_depth=9, min_samples_leaf=3,
                                     class_weight=balanced, n_jobs=1, random_state=SEED)
    elif name == "hist_gradient":
        model = HistGradientBoostingClassifier(max_iter=70, max_leaf_nodes=9,
                     l2_regularization=2, class_weight=balanced, random_state=SEED)
    elif name == 'decision_tree':
        model = DecisionTreeClassifier(max_depth=6, min_samples_leaf=5, class_weight=balanced, random_state=SEED)
    elif name == 'gradient_boosting':
        model = GradientBoostingClassifier(n_estimators=70, max_depth=2, learning_rate=.06, random_state=SEED)
    elif name == 'adaboost':
        model = AdaBoostClassifier(n_estimators=60, learning_rate=.5, random_state=SEED)
    elif name == 'knn':
        model = KNeighborsClassifier(n_neighbors=7, weights='distance', n_jobs=1)
    elif name == 'svm':
        model = SVC(C=2, kernel='rbf', probability=True, class_weight=balanced, random_state=SEED)
    elif name == 'mlp':
        model = MLPClassifier(hidden_layer_sizes=(32, 16), max_iter=180, alpha=.01, random_state=SEED)
    elif name == 'xgboost':
        from xgboost import XGBClassifier
        model = XGBClassifier(n_estimators=70, max_depth=3, learning_rate=.06,
                              reg_lambda=2, n_jobs=1, random_state=SEED, eval_metric='logloss')
    elif name == 'lightgbm':
        from lightgbm import LGBMClassifier
        model = LGBMClassifier(n_estimators=70, num_leaves=9, learning_rate=.06,
                               reg_lambda=2, n_jobs=1, random_state=SEED, verbosity=-1)
    elif name == 'catboost':
        from catboost import CatBoostClassifier
        model = CatBoostClassifier(iterations=70, depth=4, learning_rate=.06,
                                    thread_count=1, random_seed=SEED, verbose=False, allow_writing_files=False)
    else:
        raise ValueError(f"지원하지 않는 모델: {name}")
    preprocessing = pipeline_reason(name, preprocessing, balance)['preprocessing']
    steps = [("impute", SimpleImputer(strategy="median", keep_empty_features=True)),
             ("variance", VarianceThreshold())]
    if preprocessing == "scaled":
        steps.append(("scale", StandardScaler()))
    elif preprocessing != "median":
        raise ValueError("지원하지 않는 전처리")
    return Pipeline(steps + [("classifier", model)])


def fit_estimator(name, prep, balance, x, y):
    """Every transform and imbalance treatment sees only the supplied train rows."""
    model = estimator(name, prep, balance)
    kwargs = {}
    if balance == 'weighted' and name in {'knn', 'mlp'}:
        rng = np.random.default_rng(SEED)
        groups = [np.flatnonzero(y == label) for label in [0, 1]]
        target = max(map(len, groups))
        idx = np.concatenate([np.concatenate([g, rng.choice(g, target-len(g), replace=True)]) for g in groups])
        x, y = x[idx], y[idx]
    elif balance == 'weighted' and name in {'gradient_boosting', 'adaboost', 'xgboost', 'lightgbm', 'catboost', 'gaussian_nb'}:
        kwargs['classifier__sample_weight'] = compute_sample_weight('balanced', y)
    return model.fit(x, y, **kwargs)


def rank_trials(rows, policy):
    complete = [r for r in rows if r['status'] == 'completed']
    feasible = [r for r in complete if meets_goals(r['validation'], policy)]
    return sorted(complete, key=lambda r:(*selection_key(r['validation'],policy),r['id']), reverse=True), feasible


def execute(dataset, plan, artifact_dir, on_event=lambda e: None):
    df = load_frame(dataset)
    parts, split_summary = split_frame(df)
    if digest(split_summary) != plan["split_hash"]:
        raise ValueError("승인한 데이터 분할과 실행 분할이 다릅니다")
    targets = plan["target_products"]
    evaluation = {name: idx[np.isin(df.iloc[idx]["product"].astype(str), targets)]
                  for name, idx in parts.items()}
    for name in ["validation", "test"]:
        if len(evaluation[name]) == 0 or df.iloc[evaluation[name]].label.nunique() < 2:
            raise ValueError(f"{name} 대상 제품의 정상·불량 표본이 부족합니다")
    if dataset["modality"] == "image":
        from .images import run_images
        result = run_images(dataset, df, parts, evaluation, plan, artifact_dir, on_event)
        result["split"] = split_summary
        (Path(artifact_dir) / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
        return result
    features = [c for c in df if c not in META]
    x = df[features].to_numpy(dtype=float)
    y = df.label.to_numpy(dtype=int)
    policy = plan["policy"]
    staged = plan.get('search_strategy') == 'model_then_cohort'
    initial_products = sorted({p for group in plan['cohorts'] for p in group})
    configs = list(itertools.product([initial_products] if staged else plan['cohorts'],
                                    plan["models"], plan["preprocessing"], plan["balance"]))
    if len(configs) > MAX_TRIALS:
        raise ValueError("승인한 실험 예산을 초과했습니다")
    rows, fitted, baseline = [], {}, None
    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    start_all = time.perf_counter()
    with threadpool_limits(limits=1):
        stage_one_count = len(configs)
        for i, (products, model_name, prep, balance) in enumerate(configs):
            idx = parts["train"][np.isin(df.iloc[parts["train"]]["product"].astype(str), products)]
            name = f"trial-{i+1:03d}"
            config = {"products": products, "model": model_name, "preprocessing": prep, "balance": balance}
            if len(idx) < 30 or y[idx].sum() < 4 or len(np.unique(y[idx])) < 2:
                rows.append({"id": name, **config, "status": "skipped", "reason": "학습 불량 표본 부족"})
                continue
            started = time.perf_counter()
            try:
                fitted_model = fit_estimator(model_name, prep, balance, x[idx], y[idx])
                cal = evaluation["validation"]
                threshold, feasible = choose_threshold(y[cal], fitted_model.predict_proba(x[cal])[:, 1], policy)
                val = evaluation["validation"]
                scores = fitted_model.predict_proba(x[val])[:, 1]
                metrics = measure(y[val], scores, threshold, policy)
                row = {"id": name, **config, "status": "completed", "train_n": len(idx),
                       "train_defects": int(y[idx].sum()), "validation_feasible": feasible,
                       "explanation": pipeline_reason(model_name, prep, balance),
                       "stage": 'model_comparison' if not staged or i < stage_one_count else 'cohort_comparison',
                       "validation": metrics, "fit_seconds": time.perf_counter() - started,
                       "validation_fingerprint": digest(sorted(map(int, val)))}
                rows.append(row)
                fitted[name] = (fitted_model, threshold)
                on_event({"type": "TrialCompleted", "trial": name, "model": model_name,
                          "recall": metrics["recall"], "precision": metrics["precision"]})
            except (ValueError, FloatingPointError) as exc:
                rows.append({"id": name, **config, "status": "failed", "reason": str(exc)})
            if staged and i + 1 == stage_one_count:
                ranked, _ = rank_trials(rows, policy)
                finalists = []
                for row in ranked:
                    if row['model'] not in [r['model'] for r in finalists]:
                        finalists.append(row)
                    if len(finalists) == 2:
                        break
                for row in finalists:
                    for group in plan['cohorts']:
                        if group != configs[0][0]:
                            configs.append((group, row['model'], row['preprocessing'], row['balance']))
                if len(configs) > plan['trial_budget'] or len(configs) > MAX_TRIALS:
                    raise ValueError('승인한 단계별 탐색 예산 초과')
        complete = [r for r in rows if r["status"] == "completed"]
        if not complete:
            raise ValueError("실행 가능한 후보가 없습니다")
        ranked, feasible = rank_trials(rows, policy)
        winner = ranked[0]
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
              "scope_note": "불량 판정 성능 비교이며 제조 수율 개선 실측이 아닙니다.",
              "test_note": "최종 test는 선택에 사용하지 않음. baseline과 validation으로 선택한 후보만 평가.",
              "seed": SEED}
    if plan.get('discovery_incumbent'):
        reference_rows=[row for row in complete if row['model']==plan['discovery_incumbent']]
        reference=max(reference_rows,key=lambda row:(*selection_key(row['validation'],policy),row['id']))
        reference_model,reference_threshold=fitted[reference['id']]
        result['discovery_comparison']={'reference_model':reference['model'],'reference_validation':reference['validation'],
            'reference_test':measure(y[test],reference_model.predict_proba(x[test])[:,1],reference_threshold,policy),
            'reference_products':reference['products'],'note':'기존 알고리즘과 새 후보를 같은 학습 제품·같은 분할로 비교. 기존 Test 재사용 탐색 결과'}
    result['explanation'] = {
        **winner['explanation'],
        'selection_reason': f"같은 Validation에서 데모 목표를 만족한 {len(feasible)}개 후보 중 불량 검출률이 높고 정상 오판률이 낮은 순서로 선택" if feasible else '두 데모 목표를 만족한 후보 없음. 목표와의 차이가 가장 작은 참고 후보이며 적용 추천이 아님',
        'evaluated_models': sorted({r['model'] for r in complete}),
        'search_note': '전체 제품으로 모든 모델·불균형 정책 비교 후 validation 상위 서로 다른 두 모델의 최선 정책을 제품 조합으로 확장. 완전탐색이 아니며 같은 validation의 반복 사용에 따른 선택 편향 가능' if staged else '승인한 후보들의 같은 분할 비교',
    }
    if not feasible:
        result["gate"] = {"passed": False, "reasons": ["Validation에서 불량 검출률·정상 오판률 데모 목표를 만족한 후보 없음"],
                          "action": "후보 재검토 · 데이터와 비교 목표 확인", "auto_deploy": False}
    (artifact_dir / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    return result
