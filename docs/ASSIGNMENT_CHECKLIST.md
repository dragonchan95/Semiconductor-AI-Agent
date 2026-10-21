# 과제 2 요구사항과 구현 위치

G045 김용찬 · 신규 프로젝트 · 2026-10-21

기준 문서: `AI-Mini-Project_20261004_2.pdf`. 쪽은 PDF 기준입니다. 요구사항과 증빙을 연결한 표이며 점수 획득을 보장하는 자기평가가 아닙니다. PDF에 이 대응표 자체가 필수라고 명시된 문구는 확인하지 못했습니다.

| 요구사항 | 반영 위치 | 확인 상태 |
|---|---|---|
| 과제2: 신규 AI Agent, 주제 제약 없음. 코드·내용 설명 가능해야 함 (10쪽) | README, 발표1~11장, [교육자료/모델 근거](CURRICULUM_MODELS.md), [발표대본](발표대본_G045.txt) | 모델·전처리·승인·지표 공식과 한계 설명 포함 |
| 신규 주제 및 세부 기능 리스트 작성 (11~12쪽) | 원본 제출 엑셀 `2반!C11:D11`, README | G045 김용찬·과제2·세부 기능 반영 |
| UID·성함·Git 주소·공개 보고서 주소 등록 (3쪽) | 원본 제출 엑셀 `2반!A11:F11` | 엑셀에 GitHub·같은 공개 Google Slides URL 기입. 링크 전체 공유 상태 확인. 공용 Google Spread에 직접 제출하는 작업은 미수행 |
| 기능 구현 완성도 30점: 실제 동작 (13쪽) | [API](../app/api.py), [Workbench](../app/workbench.py), [실험 엔진](../app/experiments.py), [이미지 학습](../app/images.py), [모델 점검·재학습](../app/monitoring.py) | 센서12종·이미지3종 실제 학습, 승인 후 실행, 같은 알고리즘 재학습·후보 버전 저장. 현장 적용 실적은 아님 |
| Before/After 보너스10점: 같은 입력 실측 (13쪽) | 발표7~10장, [최초 센서](evaluation/synthetic_process.json), [재학습](evaluation/model_management.json), [SECOM](evaluation/secom.json), [이미지](evaluation/images.json) | 각 비교에서 같은 Test 행·라벨 사용. 모델·전처리·판정값·학습 범위가 함께 바뀐 절차 비교이며 개별 기법의 인과 효과는 아님 |
| 한계·Trade-off20점 (13쪽) | 발표6~11·13장, [상세 보고서](REPORT.md) | Recall 증가와 정상 오판 증가, 작은 불량 표본, 합성·공개 데이터, 반복 Validation 비교, LLM fallback 표시 |
| PPT·발표20점: 문제→기능→수치→한계 (13쪽) | 발표1~11장, [PDF](G045_Semiconductor_Agent.pdf), [TXT 대본](발표대본_G045.txt) | 1~2장 사용자·문제, 3~5장 실제 화면, 6~10장 지표·실측·후속 화면·출처, 11장 한계와 다음 검증, 12~15장 기술·상세 지표 부록 |

## 기술 요소 30점의 세부 대응

| 기술 | 코드·실행 증빙 | 실제 상태와 한계 |
|---|---|---|
| Multi-Agent | [planner.py](../app/planner.py), [advisors.py](../app/advisors.py), [통합 실행 기록](evaluation/agent_integration.json) | LangGraph의 품질 점검·계획 역할과 결과 검토 역할. 제한된 선택 코드·출처를 검사하는 로컬 LLM 구조. 품질·계획은 검증 통과, 결과 검토는 fallback. 자율 도구 실행·supervisor-of-supervisors 구현은 아님 |
| RAG | planner.Knowledge, [교육·공개 모델 근거](../data/knowledge.json), 통합 기록 | qwen 임베딩+cosine 검색, TF-IDF 비교·fallback. 고정13질의 Hit@3 양쪽100%, MRR@3 양쪽0.9615로 이번 평가에서 dense 품질 개선은 확인하지 못함. 외부 모델 발굴은 확장 설계 |
| MCP | [mcp_server.py](../mcp_server.py), [실제 연결 확인](evaluation/mcp_check.json) | stdio handshake·4도구·지식resource 실제 호출. 승인·실행 도구는 노출하지 않음 |
| 의존성 주입 (DI) | planner.Dependencies, workbench.Workbench.__init__, tests/test_advisors.py | Store·Knowledge·Advisor를 전달해 테스트 대체와 API/MCP 공통 엔진 재사용 |
| LangSmith | 이번 제출 범위에서 제외 | 완성 기능·발표 기술 목록에 포함하지 않음 |
| 모듈화 | app/data.py·catalog.py·metrics.py·experiments.py·images.py·monitoring.py·store.py·api.py | 데이터·모델·지표·학습·관리·저장·접속 역할 분리 |
| 단위/API 테스트 | [tests/](../tests), [26개 통과 로그](evaluation/tests.txt) | 분할·지표·승인 hash·미승인 실행 차단·인증·SSE·CSV·재학습 버전·Validation만으로 학습 방식 선택 검증 |

평가항목의 기술을 언급했다는 사실만으로 충분한 구현으로 인정된다고 단정하지 않습니다. 실제 구현과 미확인·미구현 상태를 함께 제시했습니다. 실제 회사의 공통 Recall/FPR 합격 수치를 확인하지 못했으며 90%·15%·불량20개는 교육용 기본값입니다.

2026-10-21 재검증: 목표 Train/Validation/Test=6:2:2. 같은 lot·날짜 경계를 보존하고 실제 센서·이미지·재학습 수치를 다시 계산했습니다. 현재 앱의 완료 이력은 이 분할 버전만 예시 결과로 표시합니다. 앙상블 혼합 비율 탐색은14장 확장 설계이며 실행 기능이 아닙니다. 기술 대응표는15장입니다. 대본만5분으로 줄이고 본문 슬라이드의 순서는 유지했습니다.
