# LangSmith 연결 복원

`.env.example`을 `.env`로 복사하고 APAC 계정의 키를 로컬 파일에만 입력합니다.
`LANGSMITH_TRACING=true`, `LANGSMITH_ENDPOINT=https://apac.api.smith.langchain.com`을 설정합니다.
이 프로젝트는 앱 모듈을 가져오기 전에 `.env`를 읽습니다. 이미 지정한 환경변수가 우선합니다.

Windows에서는 `..\.venv\Scripts\python.exe scripts/check_langsmith.py`를 실행합니다.
새 비교 계획을 실제로 생성하고, 전송한 root/child run을 API로 다시 조회합니다.
검증 성공 시 `docs/evaluation/langsmith_check.json`에 키를 제외한 결과를 저장합니다.
LangSmith 추적과 Ollama LLM의 응답 성공은 별개입니다. `agent_outputs`로 verified/fallback/disabled를 확인합니다.
LLM-as-a-Judge는 `scripts/evaluate_judge.py`에서 로컬 Qwen을 별도 평가자로 호출합니다.
이 평가는 기본적으로 외부 추적을 끄고 실행하며 `docs/evaluation/llm_judge.json`에 결과를 기록합니다.
모델 추론, LangSmith 추적, LLM 평가의 목적과 검증 기록을 구분합니다.

현재 Windows는 수업과 같은 Qwen2.5-1.5B 계열을 로컬 Ollama로 실행합니다.
`docs/evaluation/local_llm_check.json`은 실제 세 역할의 응답·허용 코드·출처 연결 검사입니다.
Qwen은 로컬 추론이고 LangSmith는 외부 추적 서비스이므로, 로컬 모델 사용만으로 전체 시스템이 오프라인인 것은 아닙니다.
현재 추적 검증에는 공개·합성 데이터 요약만 사용했습니다. 외부 추적을 끄려면 `LANGSMITH_TRACING=false`를 설정합니다.

공식 설정 안내: https://docs.langchain.com/langsmith/trace-without-env-vars
