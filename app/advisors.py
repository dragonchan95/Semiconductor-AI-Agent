"""Bounded local LLM roles. Engine facts, approval and numeric metrics stay authoritative."""
import json
import os
import time

import httpx
from langsmith import traceable


class LocalAdvisor:
    def __init__(self, enabled=None, client=None):
        self.enabled = os.getenv('SEMI_LLM_ENABLED', '0') == '1' if enabled is None else enabled
        self.url = os.getenv('OLLAMA_URL', 'http://127.0.0.1:11434').rstrip('/')
        self.model = os.getenv('SEMI_LLM_MODEL', 'qwen3.5:2b')
        self.client = client or httpx.Client(timeout=45)

    @traceable(name='LocalLLMAgent', run_type='chain')
    def advise(self, role, facts, choices, evidence):
        """No raw rows/images, tool execution, free-form numbers or approval token reach the LLM."""
        if not self.enabled:
            return {'role': role, 'status': 'disabled', 'note': '로컬 LLM 미사용. 수치·계획은 규칙 엔진으로 생성'}
        start = time.perf_counter()
        ids = [d['id'] for d in evidence]
        source_map = {'split':'leakage', 'missing':'leakage', 'imbalance':'imbalance', 'products':'product',
                      'validation':'leakage', 'tradeoff':'profit', 'candidate':'approval', 'hold':'approval', 'sample':'imbalance',
                      'logistic':'ann', 'mlp':'ann', 'knn':'distance', 'svm':'distance'}
        if role == 'ExperimentPlannerAgent':
            source_map.update({c:'tree' for c in choices if c not in source_map})
        choices = {c:v for c,v in choices.items() if source_map.get(c) in ids}
        required = {c:source_map[c] for c in choices}
        schema = {'type': 'object', 'properties': {
            'priority_codes': {'type': 'array', 'items': {'type': 'string', 'enum': list(choices)}, 'minItems': 1, 'maxItems': min(3, len(choices))},
            'evidence_ids': {'type': 'array', 'items': {'type': 'string', 'enum': ids}, 'minItems': 1, 'maxItems': min(3, len(ids))}},
            'required': ['priority_codes', 'evidence_ids'], 'additionalProperties': False}
        if not choices or not ids:
            return {'role': role, 'status': 'fallback', 'note': '선택 가능한 근거 부족'}
        try:
            response = self.client.post(self.url+'/api/chat', json={
                'model': self.model, 'stream': False, 'think': False, 'format': schema,
                'options': {'temperature': 0, 'num_predict': 220, 'num_ctx': 4096},
                'messages': [{'role': 'system', 'content': 'You are '+role+'. Rank only the provided applicable codes using the measured facts and retrieved evidence. Cite only supplied evidence ids. Return JSON only. Never approve training, deploy, or invent a metric.'},
                             {'role': 'user', 'content': json.dumps({'facts': facts, 'applicable_choices': choices,
                                'required_evidence_for_each_code': required,
                                'retrieved_evidence': [{'id': d['id'], 'text': d['text']} for d in evidence]}, ensure_ascii=False)}]})
            response.raise_for_status()
            payload = response.json()
            output = json.loads(payload['message']['content'])
            codes, cited = output['priority_codes'], output['evidence_ids']
            if set(output) != {'priority_codes', 'evidence_ids'} or not codes or not cited:
                raise ValueError('응답 구조 또는 근거 누락')
            if not set(codes) <= set(choices) or not set(cited) <= set(ids):
                raise ValueError('허용되지 않은 판단 또는 출처')
            if not {required[c] for c in codes} <= set(cited):
                raise ValueError('선택한 판단을 뒷받침하는 출처 누락')
            if len(codes) > 4 or len(cited) > 3 or len(codes) != len(set(codes)):
                raise ValueError('역할별 출력 예산 초과')
            return {'role': role, 'status': 'verified', 'model': self.model,
                    'priority_codes': codes, 'recommendations': [choices[c] for c in codes],
                    'evidence_ids': cited, 'seconds': round(time.perf_counter()-start, 3),
                    'tokens': payload.get('eval_count'), 'numeric_claims': 'engine_only',
                    'validation_scope': '허용 코드·출처 존재·주제 연결 검사. 자유 추론의 사실성을 보증하는 평가 아님'}
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
            return {'role': role, 'status': 'fallback', 'note': 'LLM 응답을 검증할 수 없어 규칙 근거를 사용',
                    'error_type': type(exc).__name__, 'seconds': round(time.perf_counter()-start, 3)}


def quality_choices(audit):
    result = {'split': '같은 lot 또는 날짜가 학습·평가에 걸치지 않도록 분할을 확인'}
    if audit['missing_ratio'] > 0:
        result['missing'] = '관측한 센서 결측을 학습 중앙값으로 대체'
    if audit['defect_ratio'] < .2:
        result['imbalance'] = '불량이 적어 train 전용 불균형 대책과 Recall·Precision을 함께 비교'
    if len(audit['products']) > 1:
        result['products'] = '여러 제품의 공통·전용 학습 범위를 같은 평가 표본으로 비교'
    return result


def result_choices(result):
    choices = {'validation': '모델 선택에는 validation 결과를 사용. test 수치로 후보 순서를 바꾸지 않음',
               'tradeoff': '추가 불량 검출과 정상 제품 추가 검사 부담을 함께 검토'}
    choices['candidate' if result['gate']['passed'] else 'hold'] = (
        '기준 통과 후보를 엔지니어 검토 대상으로 제시. 운영 배포는 별도 절차' if result['gate']['passed'] else '현재 결과는 적용 보류. 기준 미달 원인을 먼저 검토')
    if result['test']['positive_count'] < 20:
        choices['sample'] = 'test 불량 표본이 적어 독립 검증 불량 데이터를 보강'
    return choices
