# 과제 2 요구사항과 구현 위치

SKALA 광주 2반 · G045 김용찬 · 신규 프로젝트 · 2026-10-22 최종 점검·발표

기준 문서: `AI-Mini-Project_20261004_2.pdf`. 쪽은 PDF 기준입니다. 요구사항과 증빙을 연결한 표이며 점수 획득을 보장하는 자기평가가 아닙니다. PDF에 이 대응표 자체가 필수라고 명시된 문구는 확인하지 못했습니다.

| 요구사항 | 반영 위치 | 확인 상태 |
|---|---|---|
| 과제2: 신규 AI Agent, 주제 제약 없음. 코드·내용 설명 가능해야 함 (10쪽) | README, 발표1~10장, [교육자료/모델 근거](CURRICULUM_MODELS.md), [발표대본](발표대본_G045.txt) | 모델·전처리·승인·지표 공식과 한계 설명 포함 |
| 신규 주제 및 세부 기능 리스트 작성 (11~12쪽) | 원본 제출 엑셀 `2반!C11:D11`, README | G045 김용찬·과제2·세부 기능 반영 |
| UID·성함·Git 주소·공개 보고서 주소 등록 (3쪽) | 원본 제출 엑셀 `2반!A11:F11` | GitHub·기존 Google Slides URL 유지. 로그인 없는 공개 접근은 확인했으나 Slides 최신본은 미반영. 공용 Google Spread 직접 제출은 미수행 |
| 기능 구현 완성도 30점: 실제 동작 (13쪽) | [API](../app/api.py), [Workbench](../app/workbench.py), [실험 엔진](../app/experiments.py), [이미지 학습](../app/images.py), [모델 점검·재학습](../app/monitoring.py) | 센서12종·이미지3종 실제 학습, 승인 후 실행, 같은 알고리즘 재학습·후보 버전 저장. 현장 적용 실적은 아님 |
| Before/After 보너스10점: 같은 입력 실측 (13쪽) | 발표6~8장, [제품 그룹](evaluation/product_partitions.json), [앙상블](evaluation/weighted_ensemble.json), [최초 센서](evaluation/synthetic_process.json) | 각 실험에서 같은 Test 행·라벨 사용. 두 실험은 알고리즘 고정 그룹 비교와 제품ABCD 고정 비율 비교로 분리. 기존 시스템 대비 업무시간 개선 실적은 아님 |
| 한계·Trade-off20점 (13쪽) | 발표6~10·13장, [상세 보고서](REPORT.md) | 앙상블 후보·비율 간격 한정, 작은 불량 표본, 반복 Validation·Test 재사용, LLM 오판 |
| PPT·발표20점: 문제→기준→시연→기술→교훈 (13쪽) | 발표1~10장, [PDF](G045_Semiconductor_Agent.pdf), [TXT 대본](발표대본_G045.txt) | 1~3장 소개·문제·기준, 4~5장 입력·계획 승인, 6장 그룹 선택·Test 실패, 7장 별도 비율별 Validation, 8장 앙상블의 같은 Test, 9장 구조·검증, 10장 교훈. 11~14장은 질문용 부록이며12장 RAG 화면 |

## 기술 요소 30점의 세부 대응

| 기술 | 코드·실행 증빙 | 실제 상태와 한계 |
|---|---|---|
| Multi-Agent | [planner.py](../app/planner.py), [advisors.py](../app/advisors.py), [현재 로컬 Qwen 검증](evaluation/local_llm_check.json) | LangGraph 품질 점검·계획 역할과 결과 검토 역할. 현재 Windows의 Qwen2.5-1.5B에서 세 역할의 실제 응답·허용 코드·출처 연결 검사 통과. 제한된 역할 구조이며 자율 Supervisor는 미구현. 소규모 검증이 일반적 사실성·업무 성능을 보증하지 않음 |
| RAG | [retrieval.py](../app/retrieval.py), planner.Knowledge, [실제 검증](evaluation/vector_rag.json), [구현 설명](RAG.md) | 5주차 BGE-M3·FAISS 실습 응용. 현재 Windows는 내부 근거·공식 문서 의미 임베딩과FAISS IndexFlatIP·출처 JSON을 로컬 저장·검색하고 Qwen에 주입. 서버형 Vector DB는 아님. 실패 시TF-IDF 대체 상태 표시. 학습 연결은 검토된 ExtraTrees·GaussianNB adapter |
| MCP | [mcp_server.py](../mcp_server.py), [실제 연결 확인](evaluation/mcp_check.json) | stdio handshake·4도구·지식resource 실제 호출. 승인·실행 도구는 노출하지 않음 |
| 의존성 주입 (DI) | planner.Dependencies, workbench.Workbench.__init__, tests/test_advisors.py | Store·Knowledge·Advisor를 전달해 테스트 대체와 API/MCP 공통 엔진 재사용 |
| LangSmith | [실제 APAC 추적 검증](evaluation/langsmith_check.json), [설정 안내](LANGSMITH_SETUP.md) | Windows에서 실제 계획 생성·하위 실행을 전송하고 API 재조회 확인. 현재 로컬 Qwen 추론은 별도 검증 기록으로 확인하며 추적 성공과 LLM 응답 성공을 구분 |
| 모듈화 | app/data.py·catalog.py·metrics.py·experiments.py·images.py·monitoring.py·store.py·api.py | 데이터·모델·지표·학습·관리·저장·접속 역할 분리 |
| 단위/API 테스트 | [tests/](../tests), [Windows51개 통과 로그](evaluation/tests-windows.txt), [검증 환경](evaluation/windows_check.json) | 분할·지표·승인 hash·인증·SSE·CSV·재학습·앙상블 선택·15개 제품 그룹·저장 모델 재현·Judge 실패·벡터 정규화·캐시 변경·한글 경로·검색 실패 상태 검증 |
| 모델 간 앙상블 | [확률 혼합](../app/ensemble.py), [실측](evaluation/weighted_ensemble.json), [실제 UI](evaluation/ensemble_browser.json), [방법](ENSEMBLE.md) | 승인한 상위3개 모델과5% 간격+균등 비율232개를 Validation에서 비교. 정상 오판 한도 안에서 Recall 우선·동률 F1. CatBoost90%+LightGBM10%, 같은 Test 불량발견30/32동일·정상오판21→19·F1 .723→.741. 전역 최적 주장은 아님 |
| 학습 제품 범위 | [grouping.py](../app/grouping.py), [제품 범위 설명](PRODUCT_GROUPING.md), [실제15개 구성](evaluation/product_partitions.json), 발표2·5·6장 | 고정 CatBoost의 ABCD·ABC/D·AB/CD 등15개 담당 그룹 전수 비교. Validation 선택ABC/D는 Test Recall78.1%로 목표 미달·보류. 그룹과 앙상블 비율 공동 전역 최적화는 아님 |
| LLM-as-a-Judge | [로컬 평가자](../app/judge.py), [실제 평가 기록](evaluation/llm_judge.json), [초기 실패 기록](evaluation/llm_judge_initial.json) | 로컬 Qwen이 결과 설명과 실제 실험 근거를 대조해 판정. 사전 라벨을 모델에 보내지 않고 일치율을 측정. 프롬프트 보완에 사용한 작은 자체 개발 예제이며 독립 평가·일반 정확도 실적은 아님. 코드 검사를 대체하지 않음 |

| 미구현 기술 | 실제 범위 표시 | 서버형 Vector DB·자율 Supervisor는 미구현. 로컬FAISS 벡터 저장·검색은 구현. 혼합은 센서 이진 분류의 검토된2~3개 구성 모델에 한정 |

발표의 범위는 데이터 점검·승인된 모델 비교·선택 근거입니다. 재학습·운영 감시는 추가 구현으로 보존하되 5분 발표에서 제외합니다. 추상적인 ‘다음 실험을 자동 제안’ 대신 ‘공식 문서에서 비교 후보를 추가’로 실제 동작을 설명합니다.

평가항목의 기술을 언급했다는 사실만으로 충분한 구현으로 인정된다고 단정하지 않습니다. 실제 구현과 미확인·미구현 상태를 함께 제시했습니다. 실제 회사의 공통 Recall/FPR 합격 수치를 확인하지 못했으며 90%·15%·불량20개는 교육용 기본값입니다.

목표 Train/Validation/Test=6:2:2. 본문10장·질문용 부록4장, 발화 목표255초+전환20초+여유25초로 5분을 준비합니다. 실측 리허설 시간은 아닙니다. 현재 본문은 승인한 제품 그룹과 별도 앙상블 비율 선택을 설명합니다. [Windows 로컬 Qwen 포함 초기 실험](evaluation/windows_llm_synthetic.json)의TP27·FP14는 별도 과거 기록입니다. 현재 그룹 실험은TP25·FP14, 앙상블은TP30·FP19이며 섞지 않습니다. 13장은 선택 범위, 14장은 쉬운 Judge 예시입니다. 출처·중복 기술표는 슬라이드에서 제거하고 보고서에 보존합니다. AdaBoost는 반도체 자료의 회귀 사례를 분류용으로 적용했습니다.

최종 보고서는 교수 안내의 다섯 항목(소속, 문제·신규 구현, 적용 기술, 흐름도·화면·결과, 교훈) 순서로 구성했습니다. 문제는 프로젝트에서 설정한 엔지니어의 비교·기록 업무이며 특정 회사 기존 시스템의 결함을 조사했다고 주장하지 않습니다.
