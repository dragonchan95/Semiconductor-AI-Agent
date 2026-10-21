"""Five-minute story: purpose, criteria, approved ensemble, evidence, lessons."""


def compose_content(load,names,pct,ranking):
    receipts={n:load(n) for n in ['synthetic_process','secom','images']}
    r=receipts['synthetic_process']['result']
    ranks=ranking(r['trials'],receipts['synthetic_process']['plan']['policy'])
    trace=load('langsmith_check');judge=load('llm_judge');windows=load('windows_check')
    er=load('weighted_ensemble')['result'];e=er['ensemble'];ev=e['selected']['validation']
    single=e['best_single']['validation'];eb=e['best_single_test'];et=er['test']
    content=[]
    def add(title,context,body,seconds=0,note='',table=None,image=None,kind=None,sources=None):
        content.append(dict(title=title,context=context,body=body,seconds=seconds,note=note,
                            table=table,image=image,kind=kind,sources=sources or []))

    add('반도체 검사 모델\n실험 도우미','01 · 무엇을 만드는 프로젝트인가요?',[
        '모델과 앙상블 비율을 비교하고, 선택 이유를 보여 주는 Agent',
        'SKALA 광주 2반 · G045 김용찬 · 2026.10.22'],15,
        '안녕하세요. 김용찬입니다. 검사 데이터를 넣으면 모델과 앙상블 비율을 비교하고, 왜 그 비율을 선택했는지 결과와 함께 보여 주는 Agent를 만들었습니다.',kind='cover')
    add('반복하던 모델·비율 비교를 한 흐름으로','02 · 사용자와 해결할 문제',[
        '사용자: 검사 데이터로 정상·불량 분류 모델을 만드는 엔지니어',
        '반복 업무: 데이터 확인 → 여러 모델 학습 → 혼합 비율 비교 → 근거 기록',
        'Agent가 근거와 계획을 제시하고, 엔지니어가 승인하면 실행',
        '센서 사례 하나로 입력부터 선택 결과까지 보여 드립니다.'],20,
        '대상은 검사 모델을 만드는 엔지니어입니다. 데이터가 바뀌면 어떤 모델을 쓰고 예측을 어떤 비율로 섞을지 비교해야 합니다. 이 반복 작업을 연결했습니다. 스칼라에서 배운 모델과 반도체 자료의 후보를 함께 넣었고, 센서 사례 하나로 설명하겠습니다.')
    add('불량을 놓치지 않되, 정상 오판도 제한합니다','03 · 결과를 읽기 위한 기준',[
        '불량 검출률(Recall): 실제 불량 중 찾아낸 비율',
        '정상 오판률: 정상을 불량으로 잘못 판정한 비율',
        '이번 목표: 불량 검출률90% 이상 · 정상 오판률15% 이하',
        '정상 오판 한도 준수 → Recall 최대 → 동률이면 F1',
        '90%·15%는 교육용 목표입니다. 현장에서는 담당자와 허용 범위를 정합니다.'],25,
        '불량을 놓치지 않는 것이 목적이라 검출률을 우선합니다. 다만 전부 불량으로 찍는 것을 막기 위해 정상 오판률을 십오 퍼센트 이하로 제한합니다. 그 안에서 검출률이 높고, 같으면 F1이 높은 비율을 고릅니다. F1은 불량 검출과 불량 판정의 정확성을 함께 보는 보조 지표입니다.',kind='criteria',
        sources=['app/ensemble.py','https://scikit-learn.org/stable/modules/model_evaluation.html'])
    add('① 검사 데이터를 선택합니다','04 · 실제 화면 | 이번 시연의 입력',[
        '합성 센서 1,280건 · 불량 201건 · 제품 A–D는 가상 이름',
        '센서 CSV와 검사 이미지 ZIP 등록도 지원합니다.',
        '오늘은 센서 예제로 모델과 혼합 비율을 비교합니다.'],20,
        '실제 앱 화면입니다. 제품 A부터 D의 합성 센서 천이백팔십 건을 선택합니다. 불량 정답은 이백한 건입니다. 직접 만든 예제로, 실제 공장 데이터는 아닙니다. 내 센서 CSV나 검사 이미지 ZIP을 등록하는 기능도 있습니다.',image='app-data.jpg',sources=['app/data.py'])
    add('② 모델 비교 후, 비율 탐색 계획을 승인합니다','05 · 실제 화면 | 비율 탐색도 승인 후 실행',[
        '결측·불균형 점검과\n전처리 이유 확인',
        '학습60% / 후보 선택20% / 마지막 확인20% · 같은 lot은 분리',
        '상위 3개 모델의 확률을 5% 간격으로 혼합 · 합계100%',
        '232개 비율 비교 · 엔지니어 승인 후 실행'],25,
        '먼저 여러 모델을 같은 조건으로 비교하고 상위 세 알고리즘을 고릅니다. 화면은 그 확률을 섞는 비율 탐색 계획입니다. 학습, 후보 선택, 마지막 확인 데이터를 육 대 이 대 이로 나누고 같은 생산 묶음은 섞지 않습니다. 비교 범위를 확인하고 승인하면 실행합니다.',image='app-ensemble-plan.jpg',sources=['app/ensemble.py','docs/evaluation/weighted_ensemble.json'])
    add('③ 선택 비율: CatBoost 90% + LightGBM 10%','06 · 실제 화면 | Validation에서 비율과 판정 기준 선택',[
        f'검출률 {pct(ev["recall"])} 유지 · F1 {single["f1"]:.3f} → {ev["f1"]:.3f}',
        '정상 오판 한도 준수 → Recall 최대 → 동률이면 F1',
        '상위 3개 모델 · 5% 간격과 균등 비율 · 232개 비교',
        '선택 범위 안의 최선입니다. Test로 비율을 고르지 않습니다.'],35,
        '후보 선택용 데이터인 Validation에서 비율과 판정 기준을 비교합니다. 다섯 퍼센트 간격과 균등 비율을 포함한 이백서른두 조합 중 CatBoost 구십, LightGBM 십 퍼센트가 선택됐습니다. 단일 모델과 검출률 백 퍼센트는 같지만 정상 오판이 스무 건에서 열아홉 건으로 줄고 F1도 개선됐습니다. 이 탐색 범위 안의 최선이라는 뜻입니다.',image='app-ensemble-validation.jpg',kind='ensemble_screen',sources=['docs/evaluation/weighted_ensemble.json','docs/evaluation/ensemble_browser.json'])
    add('④ 같은 검출률을 유지하며 정상 오판을 줄였습니다','07 · 실제 화면 | 같은 Test 256건: 불량32개 · 정상224개',[
        f'불량 발견 {eb["tp"]} → {et["tp"]}개',
        f'정상 오판 {eb["fp"]} → {et["fp"]}개',
        f'Test F1 {eb["f1"]:.3f} → {et["f1"]:.3f}',
        f'검출률 {pct(et["recall"])} · 시연 목표 충족\n새 독립 데이터 검증 필요'],35,
        '비율을 고른 뒤 같은 Test에서 확인했습니다. 단일 CatBoost와 선택 조합은 둘 다 불량 서른두 개 중 서른 개를 찾았습니다. 정상 오판은 스물한 개에서 열아홉 개로 줄고 F1도 영 점 칠이삼에서 칠사일로 높아졌습니다. 이번 시연 목표는 충족했지만, 기존 Test를 다시 확인한 추가 탐색이므로 새로운 독립 데이터 검증이 필요합니다.',image='app-ensemble-test.jpg',kind='result_screen',sources=['docs/evaluation/weighted_ensemble.json'])
    add('⑤ 공식 문서에서 비교 후보를 추가할 수 있습니다','08 · 실제 검색 기록의 UI 재현 | RAG = 관련 근거 검색',[
        '공식 문서 조회 → 근거 검색 → 후보와 제안 이유 제시',
        'ExtraTrees·GaussianNB 두 모델을 추가할 수 있습니다.',
        '근거 확인 → 계획 승인 → 기존 후보와 학습·비교'],25,
        '후보를 더 비교하고 싶으면 공식 문서를 검색합니다. 저장된 실제 검색 기록을 현재 화면에서 다시 보여 드립니다. 관련 근거와 제안 이유를 연결하는 것이 RAG입니다. 현재는 두 모델을 추가할 수 있고, 이 경우도 승인 후 비교합니다.',image='app-rag-proof.jpg',sources=['app/discovery.py','docs/evaluation/model_discovery.json'])
    add('역할을 나누고, 실행과 답변을 검증했습니다','09 · 구현 구조와 검증',[
        'LangGraph: 데이터 점검·근거 검색·계획 역할 연결',
        '로컬 Qwen: 설명 보조 / 실험 엔진: 실제 학습·비율·지표 계산'],35,
        'LangGraph로 점검, 검색, 계획 역할을 연결하고 로컬 Qwen이 설명을 돕습니다. MCP는 조회와 계획 도구를 제공하고, 실제 학습과 비율 비교는 실험 엔진이 계산합니다. LangSmith로 실행 경로를 확인했습니다. 또 설명이 실제 결과와 맞는지 LLM이 검사하게 했습니다. 직접 만든 예제 여덟 개 중 여섯 개는 맞혔지만, 오판도 있어 수치 검사는 코드로 유지합니다.',kind='architecture',sources=['app/planner.py','app/ensemble.py','docs/evaluation/langsmith_check.json','docs/evaluation/llm_judge.json','docs/evaluation/tests-windows.txt'])
    add('추천 비율과 함께, 선택 이유와 한계를 남깁니다','10 · 성과와 교훈',[
        '성과: 승인된 모델·앙상블 비율 비교와 선택 근거를 한 흐름으로 연결',
        '교훈: F1 하나보다 불량 미검출·정상 오판의 우선순위가 먼저입니다.',
        '한계: 합성 데이터·작은 불량 표본·반복 비교 → 현장 효과 미측정',
        '개선: 현장 기준 합의 → 새 독립 데이터 검증 → 작업시간 절감 측정'],20,
        '모델 이름뿐 아니라 혼합 비율과 선택 근거까지 보여 주는 흐름을 구현했습니다. F1 하나로 고르기보다 업무의 우선순위를 먼저 정해야 한다는 것을 배웠습니다. 합성 데이터와 작은 표본이 한계이며, 다음에는 현장 기준과 독립 데이터로 검증하겠습니다. 감사합니다.')

    full=[['모델 · 전체 제품 학습','불균형 설정','검출률','정상 오판률','F1']]+[
        [names[x['model']],x['balance'],pct(x['validation']['recall']),pct(x['validation']['fpr']),pct(x['validation']['f1'])] for x in ranks]
    add('비율을 섞기 전, 개별 모델 비교','부록 A · 초기 전체 제품 Validation 비교',[
        '전체 제품 Train의 24조건에서 알고리즘별 최선 불균형 설정을 표시합니다.',
        '앙상블은 같은 학습 범위의 CatBoost·HistGradientBoosting·LightGBM으로 비교했습니다.'],table=full,
        note='초기 전체 제품 비교표입니다. AdaBoost는 F1이 더 높지만 이번에는 검출률을 먼저 보는 규칙을 따랐습니다. 초기 제품 조합 탐색의 CatBoost A+B+C와 이번 전체 제품 앙상블은 별도의 실험입니다.',sources=['docs/evaluation/synthetic_process.json','docs/evaluation/weighted_ensemble.json'])
    other=[['데이터','기본 / 선택·참고 후보','불량 발견','정상 오판','판단']]
    for key,label in [('synthetic_process','합성 센서'),('secom','UCI SECOM'),('images','합성 이미지')]:
        q=receipts[key]['result'];a=q['baseline_test'];z=q['test']
        other.append([label,('축소 ResNet' if key=='images' else 'Logistic')+' / '+names[q['winner']['model']],
            f'{a["tp"]} → {z["tp"]} / {z["positive_count"]}',f'{a["fp"]} → {z["fp"]} / {z["tn"]+z["fp"]}',
            '목표 충족 후보 없음' if key=='secom' else '불량 표본 보강' if key=='images' else '추가 검증 필요'])
    add('공개 센서와 이미지에서도 실행했습니다','부록 B · 앙상블 추가 전의 별도 실험 기록',[
        '본문의 앙상블 결과와 별개입니다. 각 행 안에서만 같은 Test를 비교합니다.',
        'SECOM은 실제 공개 자료이며, 센서·이미지 예제는 합성 데이터입니다.'],table=other,
        note='SECOM은1,567건 중 불합격104건이며 제조사·제품ID는 제공되지 않습니다. 이미지 Test의 불량15건은 작은 표본입니다. 이 표는 이전 실험 기록이며 앙상블 적용 결과로 해석하지 않습니다.',sources=['docs/evaluation/summary.json'])
    add('왜 이 비율을 선택했나요?','부록 C · 앙상블 선택 근거와 범위',[
        'Train: 학습 / Validation: 비율·판정 기준 선택 / Test: 선택 후 확인',
        '동일 제품 A+B+C+D의 Train 768건으로 세 모델 학습 · 분할768/256/256',
        '합계100% 비율을 5% 간격으로 모두 비교 + 균등 비율 = 232개',
        '정상 오판률15% 이하에서 Recall 최대 → 동률 F1 → 단순한 조합',
        '이 후보·간격·Validation 범위의 최선이며, 새 독립 데이터 확인이 필요합니다.'],
        note='각 모델의 불량 확률을90대10으로 평균하고 Validation에서 정한 판정값 이상이면 불량으로 봅니다. 단일 모델과 균등 비율도 포함했습니다. 동률이면 적은 모델을 고르므로 단일 모델을 유지할 수도 있습니다. 모든 모델·모든 실수 비율의 전역 최적이라는 뜻은 아닙니다. 정확한 근거는 전체 비율 CSV로 확인할 수 있습니다.',sources=['app/ensemble.py','docs/evaluation/weighted_ensemble.json'])
    add('LLM-as-a-Judge: 설명이 맞는지 LLM이 검사합니다','부록 D · 실제 예시로 이해하기',[
        '검사용 기준: 이전 실험에서 불량27/32개 발견 · 목표90%에는 미달',
        '실제 결과와 설명 문장을 주고 “맞는 설명인가?”를 물었습니다.',
        '직접 만든 예제 8개 중 6개는 맞게 검사했고, 2개는 틀렸습니다.'],table=[
        ['검사할 설명','맞는 판단','LLM의 실제 답'],
        ['“불량27개를 찾았고 목표에는 미달했다”','맞는 설명','맞다 · 올바른 검사'],
        ['“실제 공장 수율 증가가 입증됐다”','근거 없는 설명','틀리다 · 올바른 검사'],
        ['“불량30개를 발견했다”','실제는27개 → 틀림','맞다 · 검사가 틀림']],
        note='LLM-as-a-Judge는 설명이 맞는지 LLM에게 검사시키는 기능입니다. 실제로27개를 찾았는데30개라고 설명하면 틀렸다고 알려줘야 합니다. 실제 결과와 문장을 함께 주고 검사했고, 직접 만든 예제8개 중6개는 맞게 판단했습니다. 하지만30개라는 오류는 놓쳤습니다. 그래서 보조 검사로 쓰고 중요한 숫자는 코드로 확인합니다. 이 예시는 앙상블 추가 전의 실험 기록을 기준으로 검사했습니다.',sources=['docs/evaluation/llm_judge.json','docs/EVALUATION.md'])
    assert len(content)==14 and sum(x['seconds'] for x in content)==255
    return content,receipts,trace
