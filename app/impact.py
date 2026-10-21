"""Optional count illustration. No financial assumptions or yield claims."""
import math
from pydantic import BaseModel, Field, ConfigDict

class ImpactRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    quantity: int = Field(default=1000,ge=1,le=1000000)
    defect_rate: float = Field(default=.10,ge=0,le=1)

def compare_impact(result, scenario, policy=None):
    req=scenario if isinstance(scenario,ImpactRequest) else ImpactRequest.model_validate(scenario)
    defects=req.quantity*req.defect_rate
    normals=req.quantity-defects
    def calculate(m):
        recall,fpr=m['recall'],m['fpr']
        if not all(math.isfinite(v) and 0<=v<=1 for v in [recall,fpr]):
            raise ValueError('유효한 검출·오판 비율이 필요합니다')
        return {'detected_defects':defects*recall,'missed_defects':defects*(1-recall),
            'normal_false_positives':normals*fpr,'normal_correct':normals*(1-fpr)}
    before,after=calculate(result['baseline_test']),calculate(result['test'])
    return {'scenario':req.model_dump(),'expected_defects':defects,'expected_normals':normals,
        'before':before,'after':after,
        'delta':{'additional_detected':after['detected_defects']-before['detected_defects'],
            'additional_normal_false_positives':after['normal_false_positives']-before['normal_false_positives']},
        'interpretation':'Test 비율이 유지된다고 가정한 건수 예시. 생산 실측이 아님. 정상 오판은 재검사·폐기를 뜻하지 않음.'}
