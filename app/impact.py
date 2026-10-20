"""Translate measured detection rates into an explicitly hypothetical workload.
Inspection does not change intrinsic product quality. Optional repair recovery
requires a separately supplied success fraction and is not first-pass yield.
"""
import math
from pydantic import BaseModel, Field


class ImpactRequest(BaseModel):
    quantity: int = Field(default=1000, ge=1, le=1000000)
    defect_rate: float = Field(default=.10, ge=0, le=1)
    repair_success: float | None = Field(default=None, ge=0, le=1)


def compare_impact(result, scenario, policy):
    req = scenario if isinstance(scenario, ImpactRequest) else ImpactRequest.model_validate(scenario)
    n, defects = req.quantity, req.quantity * req.defect_rate
    normals = n - defects
    recovered_fraction = req.repair_success or 0

    def calculate(metrics):
        recall, fpr = metrics['recall'], metrics['fpr']
        if not all(math.isfinite(v) and 0 <= v <= 1 for v in [recall, fpr]):
            raise ValueError('유효한 검출·오탐 비율이 필요합니다')
        caught, extra_check = defects * recall, normals * fpr
        missed = defects - caught
        recovered = caught * recovered_fraction
        return {'detected_defects': caught, 'missed_defects': missed,
                'normal_extra_checks': extra_check, 'normal_pass': normals-extra_check,
                'flagged_total': caught+extra_check,
                'assumed_loss': missed*policy['miss_cost']+extra_check*policy['false_alarm_cost'],
                'recovered_by_repair': recovered,
                'good_fraction_after_repair': (normals+recovered)/n,
                'recall': recall, 'normal_extra_check_rate': fpr}

    before, after = calculate(result['baseline_test']), calculate(result['test'])
    return {'scenario': req.model_dump(), 'expected_defects': defects, 'expected_normals': normals,
            'intrinsic_good_fraction': 1-req.defect_rate, 'before': before, 'after': after,
            'delta': {'additional_detected': after['detected_defects']-before['detected_defects'],
                      'additional_normal_checks': after['normal_extra_checks']-before['normal_extra_checks'],
                      'assumed_loss_reduction': before['assumed_loss']-after['assumed_loss'],
                      'additional_recovered': after['recovered_by_repair']-before['recovered_by_repair'],
                      'good_fraction_change': after['good_fraction_after_repair']-before['good_fraction_after_repair']},
            'cost_assumptions': {'missed_defect': policy['miss_cost'], 'normal_extra_check': policy['false_alarm_cost']},
            'repair_scenario_enabled': req.repair_success is not None,
            'measured_source': {'synthetic': result['dataset']['synthetic'],
                                'test_n': result['test']['n'], 'test_defects': result['test']['positive_count']},
            'interpretation': '검증 데이터의 검출률·오탐률이 유지된다고 가정한 기대 건수. 생산 실측이 아님.',
            'repair_note': '양쪽 모델의 검출 불량에 같은 재작업 정상화 비율 적용. 재작업 후 양품률 가정이며 최초 제조 수율 실측이 아님.',
            'economic_note': '미검출·정상 추가검사 손실 가정만 포함. 재작업비·설비·처리량·매출 효과는 제외.'}
