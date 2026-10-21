"""Measured counts. Goals are configurable demo goals, not factory standards."""
import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix, precision_score, recall_score, roc_auc_score


def measure(y, scores, threshold, policy=None):
    y = np.asarray(y, dtype=int)
    predicted = np.asarray(scores) >= threshold
    tn, fp, fn, tp = map(int, confusion_matrix(y, predicted, labels=[0, 1]).ravel())
    recall = float(recall_score(y, predicted, zero_division=0))
    precision = float(precision_score(y, predicted, zero_division=0))
    # Wilson interval describes sampling uncertainty only, not domain shift.
    n = tp + fn
    z = 1.96
    center = (recall + z*z/(2*n))/(1+z*z/n) if n else 0
    half = z*np.sqrt(recall*(1-recall)/n+z*z/(4*n*n))/(1+z*z/n) if n else 1
    return {"n": len(y), "positive_count": n, "tn": tn, "fp": fp, "fn": fn, "tp": tp,
            "accuracy": float(accuracy_score(y, predicted)), "recall": recall, "precision": precision,
            "f1": 2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0.0,
            "fpr": fp / (fp + tn) if fp+tn else 0,
            "roc_auc": float(roc_auc_score(y, scores)) if len(np.unique(y))==2 else None, "threshold": float(threshold),
            "recall_wilson95": [float(max(0, center - half)), float(min(1, center + half))]}


def meets_goals(m, policy):
    return m['recall'] >= policy['min_recall'] and m['fpr'] <= policy['max_fpr']


def selection_key(m, policy):
    # AP and money never decide. If no candidate meets both goals, display the
    # smallest total percentage-point shortfall only as an exploratory reference.
    shortfall=max(0,policy['min_recall']-m['recall'])+max(0,m['fpr']-policy['max_fpr'])
    return (meets_goals(m,policy),-shortfall,m['recall'],-m['fpr'])


def choose_threshold(y, scores, policy):
    scores = np.asarray(scores)
    thresholds = np.unique(np.r_[scores, np.nextafter(scores.max(), np.inf)])
    rows = [measure(y, scores, float(t), policy) for t in thresholds]
    best=max(rows,key=lambda m:selection_key(m,policy))
    return best['threshold'],meets_goals(best,policy)


def operational_gate(m, policy):
    reasons = []
    if m["recall"] < policy["min_recall"]:
        reasons.append(f"불량 검출률 {m['recall']:.1%}: 데모 목표 {policy['min_recall']:.0%} 미달")
    if m["fpr"] > policy["max_fpr"]:
        reasons.append(f"정상 오판률 {m['fpr']:.1%}: 데모 목표 {policy['max_fpr']:.0%} 초과")
    if m["positive_count"] < policy.get('min_test_defects',20):
        reasons.append("마지막 평가의 불량 표본 부족: 더 많은 데이터로 확인 필요")
    return {"passed": not reasons, "reasons": reasons,
            "action": "데모 목표 충족 · 현장 별도 검증 필요" if not reasons else "데모 목표 미충족 또는 표본 부족 · 후보 재검토",
            "criteria_scope": "교육용 비교 목표. 회사의 양산 승인 기준이 아님.",
            "auto_deploy": False}
