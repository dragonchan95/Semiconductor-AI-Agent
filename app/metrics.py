import numpy as np
from sklearn.metrics import (accuracy_score, average_precision_score, confusion_matrix,
                             precision_score, recall_score, roc_auc_score)


def measure(y, scores, threshold, costs):
    y = np.asarray(y, dtype=int)
    predicted = np.asarray(scores) >= threshold
    tn, fp, fn, tp = map(int, confusion_matrix(y, predicted, labels=[0, 1]).ravel())
    recall = float(recall_score(y, predicted, zero_division=0))
    precision = float(precision_score(y, predicted, zero_division=0))
    # Wilson interval describes sampling uncertainty only, not domain shift.
    n = tp + fn
    z = 1.96
    center = (recall + z * z / (2 * n)) / (1 + z * z / n)
    half = z * np.sqrt(recall * (1 - recall) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    unit_cost = (fn * costs["miss_cost"] + fp * costs["false_alarm_cost"]) / len(y)
    baseline_cost = float(y.mean()) * costs["miss_cost"]
    return {"n": len(y), "positive_count": n, "tn": tn, "fp": fp, "fn": fn, "tp": tp,
            "accuracy": float(accuracy_score(y, predicted)), "recall": recall, "precision": precision,
            "f2": (5 * precision * recall / (4 * precision + recall)) if precision + recall else 0.0,
            "fpr": fp / (fp + tn), "average_precision": float(average_precision_score(y, scores)),
            "roc_auc": float(roc_auc_score(y, scores)), "threshold": float(threshold),
            "recall_wilson95": [float(max(0, center - half)), float(min(1, center + half))],
            "assumed_cost_per_10000": float(unit_cost * 10000),
            "assumed_saving_vs_all_pass_per_10000": float((baseline_cost - unit_cost) * 10000)}


def choose_threshold(y, scores, policy):
    scores = np.asarray(scores)
    thresholds = np.unique(np.r_[scores, np.nextafter(scores.max(), np.inf)])
    rows = [measure(y, scores, float(t), policy) for t in thresholds]
    feasible = [m for m in rows if m["precision"] >= policy["min_precision"] and m["fpr"] <= policy["max_fpr"]]
    if feasible:
        best = max(feasible, key=lambda m: (m["recall"], -m["assumed_cost_per_10000"], m["precision"]))
        return best["threshold"], True
    # Expose infeasibility. Do not silently declare this threshold operational.
    best = min(rows, key=lambda m: m["assumed_cost_per_10000"])
    return best["threshold"], False


def operational_gate(m, policy):
    reasons = []
    if m["precision"] < policy["min_precision"]:
        reasons.append("정밀도 하한 미달")
    if m["fpr"] > policy["max_fpr"]:
        reasons.append("오탐률 상한 초과")
    if m["positive_count"] < 20:
        reasons.append("평가 불량 표본 20개 미만: 통계적 불확실성이 큼")
    if m["assumed_saving_vs_all_pass_per_10000"] <= 0:
        reasons.append("입력한 비용 가정에서 손실 절감 없음")
    return {"passed": not reasons, "reasons": reasons,
            "action": "엔지니어 파일럿 검토 가능" if not reasons else "배포 보류·표본 보강 및 재검토",
            "auto_deploy": False}
