# 이 노트북에서 이어서 작업한 상태

작업본은 **15주차/Semiconductor-AI-Agent-main/continued-project**입니다.
같은 위치의 `Semiconductor-AI-Agent-main` 하위 폴더는 처음 받은 압축본입니다.
Git 이력이 있는 `continued-project`에서 이후 작업합니다.

## 완료

- GitHub 최신본 복구, Windows용 `start.cmd`·`start.ps1` 추가
- 명시적 UTF-8 읽기/쓰기와 SQLite 연결 종료 수정
- Windows 단위/API 테스트 30개 통과, MCP stdio 실제 연결 확인
- 합성 센서 52조건 Windows 재실행: 기존 Mac과 같은 CatBoost A+B+C 후보·Test 27/32·FP14
- LangSmith APAC 실제 계획 생성·하위 실행 API 재조회 성공
- 발표 본문 10장 + 질문용 부록 6장, 발화280초 + 전환20초의 5분 대본
- ‘여러 모델 비교’ 표현 사용, 스칼라 수업과 반도체 자료의 후보 출처 구분
- AdaBoost는 반도체 자료 40~42쪽의 회귀 예제를 참고해 분류용 AdaBoostClassifier 적용
- 엑셀 G045 행의 Google Slides·GitHub 링크 유지, 제출 안내 시트 추가

## 실행

`continued-project/start.cmd`를 더블클릭하고 http://localhost:8700을 엽니다.
상위 폴더의 `.venv`를 사용하며, 모델 파일·실행 이력은 `continued-project/var/`에 있습니다.
현재 Windows는 LLM 미사용·TF-IDF·규칙 설명 모드입니다.
LangSmith 설정은 Git에서 제외된 `.env`에 복원했습니다. 키를 출력하거나 커밋하지 않습니다.
기존 Mac LLM verified/fallback 기록은 `docs/evaluation/agent_integration.json`에 보존했습니다.

## 제출 확인 필요

기존 Google Slides는 아래 주소입니다. 이 노트북에서 온라인 원본을 수정한 것으로 간주하면 안 됩니다.
https://docs.google.com/presentation/d/1J2m_cpXyvb-5_Xabs2DsD3EnEV6B6GicF5OP2s5FohU/edit

로그인 없는 공개 열람은 PPTX export로 확인했습니다. 온라인의 16장은 이전 버전이며 이번 최신 내용은 미반영입니다.
Google Drive 연결 후 최신 PPTX 내용을 기존 Slides에 반영해야 합니다.
연결이 어려우면 Slides에서 파일 → 슬라이드 가져오기 → 업로드로 최신 PPTX의 전체 슬라이드를 가져온 뒤 기존 장을 정리합니다.
가져온 뒤 16장·발표자 노트·한글·표·이미지를 확인합니다.
원본 주소를 유지하므로 엑셀의 F11 링크를 바꿀 필요가 없습니다.

로컬 엑셀 수정과 지정된 공용 Google Spreadsheet 등록은 별개입니다.
제출 마감은 2026-10-22(목) 13:00, 발표 시작은13:10이며 개인 발표5분입니다.
