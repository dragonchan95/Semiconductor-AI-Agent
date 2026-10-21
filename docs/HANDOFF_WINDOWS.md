# 이 노트북에서 이어서 작업한 상태

작업본은 **15주차/Semiconductor-AI-Agent-main/continued-project**입니다.
같은 위치의 `Semiconductor-AI-Agent-main` 하위 폴더는 처음 받은 압축본입니다.
Git 이력이 있는 `continued-project`에서 이후 작업합니다.

## 완료

- GitHub 최신본 복구, Windows용 `start.cmd`·`start.ps1` 추가
- 명시적 UTF-8 읽기/쓰기와 SQLite 연결 종료 수정
- Windows 단위/API 테스트51개 통과, MCP stdio 실제 연결 확인
- 합성 센서 52조건 Windows 재실행: 기존 Mac과 같은 CatBoost A+B+C 후보·Test 27/32·FP14
- LangSmith APAC 실제 계획 생성·하위 실행 API 재조회 성공
- 발표 본문 10장 + 질문용 부록 4장, 발화 목표255초 + 전환20초 + 여유25초의 5분 대본
- 서로 다른 모델의 확률을 섞는 비율 탐색 구현. 정상 오판 한도 안에서 Recall 우선·동률 F1. 예제CatBoost90%+LightGBM10% 선택
- 232개 비율·판정 기준을 Validation에서 비교하고 동일 Test에서 단일 모델과 비교. 불량발견30/32동일·정상오판21→19·F1 .723→.741
- 고정 알고리즘으로 ABCD·ABC/D·AB/CD 등15개 담당 그룹 구성 자동 비교. Validation 선택ABC/D는 Test Recall78.1%로 적용 보류. 6장에서 실제 실패도 설명
- 지표→입력→승인→제품 그룹→별도 앙상블 비교 순서로 실제 화면5장 배치. RAG 공식 문서 근거는 부록12장. 두 실험은 공동 전역 최적화가 아님
- 최종 보고서는 교수 안내의5개 필수 항목 순서로 재구성. 기존 시스템 조사 대신 프로젝트에서 설정한 엔지니어의 비교·기록 업무를 문제로 제시
- ‘여러 모델 비교’ 표현 사용, 스칼라 수업과 반도체 자료의 후보 출처 구분
- 발표는 모델 비교·선택 근거에 집중하고 재학습·운영 감시·3σ는 발표에서 제외
- 5주차 모델이 Qwen2.5-1.5B-Instruct임을 확인하고 같은 계열의 Q4 모델로 로컬 추론 복원
- 데이터 점검·계획 설명·결과 검토 세 역할의 실제 Qwen 응답·허용 코드·출처 연결 검사 통과
- 5주차 BGE-M3·FAISS 실습을 응용한 내부 근거·외부 공식 문서 의미 검색. FAISS 벡터와 출처 JSON을 로컬 저장. 실제 검증은 docs/evaluation/vector_rag.json
- 로컬 LLM-as-a-Judge 추가: 자체 개발 예제 8개 중 6개에서 사전 라벨과 판정 일치. 잘못된 발견 수와 목표 충족 설명은 오판했으며 초기 실패도 보존
- AdaBoost는 반도체 자료 40~42쪽의 회귀 예제를 참고해 분류용 AdaBoostClassifier 적용
- 엑셀 G045 행의 Google Slides·GitHub 링크 유지, 제출 안내 시트 추가

## 실행

`continued-project/start.cmd`를 더블클릭하고 http://localhost:8700을 엽니다.
상위 폴더의 `.venv`를 사용하며, 모델 파일·실행 이력은 `continued-project/var/`에 있습니다.
현재 Windows는 로컬 Qwen2.5-1.5B 양자화 모델 + BGE-M3 임베딩·FAISS 검색입니다. 임베딩 모델과 문서 인덱스는var/에 저장하며 검색 실패 시TF-IDF 대체 상태를 표시합니다. 서버형 Vector DB는 아닙니다.
실행 파일은 프로젝트 안의 CPU용 Ollama도 숨김 창으로 시작합니다. 유료 추론 API는 사용하지 않습니다.
원래 5주차 폴더에는 인사규정 학습용 LoRA 추가 가중치만 있었고 기본 모델은 실습 폴더에 포함되지 않았습니다.
기본 모델은 원래 실습 코드가 Hugging Face 캐시에서 불러오는 방식입니다. 이번에는 같은 모델 계열을 Ollama 양자화 버전으로 복원했습니다.
5주차의 인사규정 LoRA는 보존하며 반도체 Agent에는 적용하지 않았습니다.
실제 검증: `docs/evaluation/local_llm_check.json`. 응답 검사 실패 시 규칙 설명으로 대체합니다.
LangSmith 설정은 Git에서 제외된 `.env`에 복원했습니다. 키를 출력하거나 커밋하지 않습니다.
로컬 Qwen 추론과 외부 LangSmith 추적은 별개입니다. LangSmith는 공개·합성 자료의 실행 요약으로 검증했습니다.
기존 Mac LLM verified/fallback 기록은 `docs/evaluation/agent_integration.json`에 보존했습니다.

## 제출 확인 필요

기존 Google Slides는 아래 주소입니다. 이 노트북에서 온라인 원본을 수정한 것으로 간주하면 안 됩니다.
https://docs.google.com/presentation/d/1J2m_cpXyvb-5_Xabs2DsD3EnEV6B6GicF5OP2s5FohU/edit

로그인 없는 공개 열람은 PPTX export로 확인했습니다. 온라인의 16장은 이전 버전이며 이번 최신 내용은 미반영입니다.
Google Drive 연결 후 최신 PPTX 내용을 기존 Slides에 반영해야 합니다.
교수님께 제출할 링크는 상세 최종 보고서여야 합니다. 15주차의 `G045_최종보고서.pptx`는 상세 보고서8쪽을 모두 담은 Google Slides 업로드용 파일입니다.
보고서 PPTX를 Google Drive에 업로드하고 Google Slides로 열어 저장합니다. A4 세로8장·한글·표·이미지를 확인합니다. 새 문서 주소를 쓰면 엑셀2반!F11도 새 보고서 주소로 바꿉니다.
페이지 이미지를 사용해 보고서 레이아웃을 보존했으며 추출한 텍스트는 노트에 있습니다. 본문 수정은REPORT.md에서 하고 재생성합니다.
별도 `G045_최종발표.pptx`는14장 요약본이며 발표 때1~10장만 사용합니다. 교수님께 제출할 상세 보고서용 PPTX와 구분합니다.

로컬 엑셀 수정과 지정된 공용 Google Spreadsheet 등록은 별개입니다.
제출 마감은 2026-10-22(목) 13:00, 발표 시작은13:10이며 개인 발표5분입니다.
