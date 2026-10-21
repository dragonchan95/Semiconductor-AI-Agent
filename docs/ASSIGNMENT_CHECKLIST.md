# 과제 2 요구사항과 구현 위치

SKALA 광주 2반 · G045 김용찬 · 신규 프로젝트 · 2026-10-21 검증 / 10-22 발표

기준 문서: `AI-Mini-Project_20261004_2.pdf`. 쪽은 PDF 기준입니다. 요구사항과 증빙을 연결한 표이며 점수 획득을 보장하는 자기평가가 아닙니다. PDF에 이 대응표 자체가 필수라고 명시된 문구는 확인하지 못했습니다.

| 요구사항 | 반영 위치 | 확인 상태 |
|---|---|---|
| 과제2: 신규 AI Agent, 주제 제약 없음. 코드·내용 설명 가능해야 함 (10쪽) | README, 발표1~10장, [교육자료/모델 근거](CURRICULUM_MODELS.md), [발표대본](발표대본_G045.txt) | 모델·전처리·승인·지표 공식과 한계 설명 포함 |
| 신규 주제 및 세부 기능 리스트 작성 (11~12쪽) | 원본 제출 엑셀 `2반!C11:D11`, README | G045 김용찬·과제2·세부 기능 반영 |
| UID·성함·Git 주소·공개 보고서 주소 등록 (3쪽) | 원본 제출 엑셀 `2반!A11:F11` | GitHub·기존 Google Slides URL 유지. 로그인 없는 공개 접근은 확인했으나 Slides 최신본은 미반영. 공용 Google Spread 직접 제출은 미수행 |
| 기능 구현 완성도 30점: 실제 동작 (13쪽) | [API](../app/api.py), [Workbench](../app/workbench.py), [실험 엔진](../app/experiments.py), [이미지 학습](../app/images.py), [모델 점검·재학습](../app/monitoring.py) | 센서12종·이미지3종 실제 학습, 승인 후 실행, 같은 알고리즘 재학습·후보 버전 저장. 현장 적용 실적은 아님 |
| Before/After 보너스10점: 같은 입력 실측 (13쪽) | 발표7·11~12장, [최초 센서](evaluation/synthetic_process.json), [재학습](evaluation/model_management.json), [SECOM](evaluation/secom.json), [이미지](evaluation/images.json) | 각 비교에서 같은 Test 행·라벨 사용. 모델·전처리·판정값·학습 범위가 함께 바뀐 절차 비교이며 개별 기법의 인과 효과는 아님 |
| 한계·Trade-off20점 (13쪽) | 발표6~10·13장, [상세 보고서](REPORT.md) | Recall 증가와 정상 오판 증가, 작은 불량 표본, 합성·공개 데이터, 반복 Validation 비교, LLM fallback 표시 |
| PPT·발표20점: 문제→기준→시연→기술→교훈 (13쪽) | 발표1~10장, [PDF](G045_Semiconductor_Agent.pdf), [TXT 대본](발표대본_G045.txt) | 1~3장 소개·문제·지표 기준, 4~5장 입력·승인 화면, 6장 모델별 Validation 비교, 7장 같은 Test 결과, 8장 후보·문서 근거, 9장 구조·추적·평가, 10장 교훈·한계. 11~16장은 질문용 부록 |

## 기술 요소 30점의 세부 대응

| 기술 | 코드·실행 증빙 | 실제 상태와 한계 |
|---|---|---|
| Multi-Agent | [planner.py](../app/planner.py), [advisors.py](../app/advisors.py), [현재 로컬 Qwen 검증](evaluation/local_llm_check.json) | LangGraph 품질 점검·계획 역할과 결과 검토 역할. 현재 Windows의 Qwen2.5-1.5B에서 세 역할의 실제 응답·허용 코드·출처 연결 검사 통과. 제한된 역할 구조이며 자율 Supervisor는 미구현. 소규모 검증이 일반적 사실성·업무 성능을 보증하지 않음 |
| RAG | planner.Knowledge, [교육·공개 모델 근거](../data/knowledge.json), 통합 기록 | 현재 Windows는 TF-IDF 검색+로컬 Qwen 설명. 기존 Mac에서 Qwen 임베딩+cosine과 TF-IDF를 비교한 고정13질의 평가는 Hit@3 양쪽100%, MRR@3 양쪽0.9615였으며 일반 품질 우위는 확인하지 못함. 별도 Vector DB는 미도입. 외부 후보 추가는 공식 문서 검색·근거 연결·승인 학습·목록 기록 구현. 센서 ExtraTrees·GaussianNB adapter 지원 |
| MCP | [mcp_server.py](../mcp_server.py), [실제 연결 확인](evaluation/mcp_check.json) | stdio handshake·4도구·지식resource 실제 호출. 승인·실행 도구는 노출하지 않음 |
| 의존성 주입 (DI) | planner.Dependencies, workbench.Workbench.__init__, tests/test_advisors.py | Store·Knowledge·Advisor를 전달해 테스트 대체와 API/MCP 공통 엔진 재사용 |
| LangSmith | [실제 APAC 추적 검증](evaluation/langsmith_check.json), [설정 안내](LANGSMITH_SETUP.md) | Windows에서 실제 계획 생성·하위 실행을 전송하고 API 재조회 확인. 현재 로컬 Qwen 추론은 별도 검증 기록으로 확인하며 추적 성공과 LLM 응답 성공을 구분 |
| 모듈화 | app/data.py·catalog.py·metrics.py·experiments.py·images.py·monitoring.py·store.py·api.py | 데이터·모델·지표·학습·관리·저장·접속 역할 분리 |
| 단위/API 테스트 | [tests/](../tests), [Windows 33개 통과 로그](evaluation/tests-windows.txt), [검증 환경](evaluation/windows_check.json) | 분할·지표·승인 hash·미승인 실행 차단·인증·SSE·CSV·재학습 버전·Validation만으로 학습 방식 선택과 Judge 실패 상태 검증. Windows DB 연결 미종료 문제 수정 |
| LLM-as-a-Judge | [로컬 평가자](../app/judge.py), [실제 평가 기록](evaluation/llm_judge.json), [초기 실패 기록](evaluation/llm_judge_initial.json) | 로컬 Qwen이 결과 설명과 실제 실험 근거를 대조해 판정. 사전 라벨을 모델에 보내지 않고 일치율을 측정. 프롬프트 보완에 사용한 작은 자체 개발 예제이며 독립 평가·일반 정확도 실적은 아님. 코드 검사를 대체하지 않음 |

| 미구현 기술 | 실제 범위 표시 | 별도 Vector DB·자율 Supervisor·앙상블 혼합 가중치 탐색은 미구현 |

발표의 범위는 데이터 점검·승인된 모델 비교·선택 근거입니다. 재학습·운영 감시는 추가 구현으로 보존하되 5분 발표에서 제외합니다. 추상적인 ‘다음 실험을 자동 제안’ 대신 ‘공식 문서에서 비교 후보를 추가’로 실제 동작을 설명합니다.

평가항목의 기술을 언급했다는 사실만으로 충분한 구현으로 인정된다고 단정하지 않습니다. 실제 구현과 미확인·미구현 상태를 함께 제시했습니다. 실제 회사의 공통 Recall/FPR 합격 수치를 확인하지 못했으며 90%·15%·불량20개는 교육용 기본값입니다.

목표 Train/Validation/Test=6:2:2. 본문10장·질문용 부록6장, 발화 목표255초+전환20초+여유25초로 5분을 준비합니다. 실측 리허설 시간은 아닙니다. [Windows 로컬 Qwen 포함 전체 학습](evaluation/windows_llm_synthetic.json)에서 실제 세 역할 응답과 같은 Test 결과(TP27·FP14)를 재현했습니다. 기존 Test를 재사용한 외부 후보 탐색은 독립 검증이 필요합니다. 14장은 기술 대응표, 15장은 Judge 오판 사례, 16장은 출처입니다. 본문은 ‘여러 모델 비교’로 소개하고 각 후보의 수업·반도체 자료 출처를 구분합니다. AdaBoost는 반도체 자료의 회귀 사례를 분류용으로 적용했습니다.
