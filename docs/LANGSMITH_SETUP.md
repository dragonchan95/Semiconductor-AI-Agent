# LangSmith 연결 복원

`.env.example`을 `.env`로 복사하고 APAC 계정의 키를 로컬 파일에만 입력합니다.
`LANGSMITH_TRACING=true`, `LANGSMITH_ENDPOINT=https://apac.api.smith.langchain.com`을 설정합니다.
이 프로젝트는 앱 모듈을 가져오기 전에 `.env`를 읽습니다. 이미 지정한 환경변수가 우선합니다.

Windows에서는 `..\.venv\Scripts\python.exe scripts/check_langsmith.py`를 실행합니다.
새 비교 계획을 실제로 생성하고, 전송한 root/child run을 API로 다시 조회합니다.
검증 성공 시 `docs/evaluation/langsmith_check.json`에 키를 제외한 결과를 저장합니다.
LangSmith 추적과 Ollama LLM의 응답 성공은 별개입니다. `agent_outputs`로 verified/fallback/disabled를 확인합니다.
LLM-as-a-Judge는 현재 구현하지 않았습니다.

공식 설정 안내: https://docs.langchain.com/langsmith/trace-without-env-vars
