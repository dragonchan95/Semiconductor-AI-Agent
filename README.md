# 반도체 검사 모델 실험 도우미

G045 김용찬 · SK AI Leader Academy · 과제2

데이터를 점검해 전처리·모델·제품 학습 범위를 제안하고, 엔지니어 승인 후 실제 학습합니다. Recall을 우선 확인하고 Precision·F1·정상 오판도 설명합니다. 새 데이터로 같은 제품의 기존 모델을 점검하고 승인받아 재학습을 비교합니다.

[최종 제출 Slides](https://docs.google.com/presentation/d/1J2m_cpXyvb-5_Xabs2DsD3EnEV6B6GicF5OP2s5FohU/edit) · [5분 대본](docs/발표대본_G045.txt) · [보고서](docs/REPORT.md) · [교육 모델](docs/CURRICULUM_MODELS.md) · [요구사항 대응표](docs/ASSIGNMENT_CHECKLIST.md)

![같은 Test의 비교 결과](docs/assets/app-result.jpg)

## Mac에서 앱 켜기

1. Finder에서 Semiconductor-AI-Agent 폴더를 엽니다.
2. **start.command를 더블클릭**합니다.
3. 글자가 나오는 터미널 창을 열어 둔 채 **http://localhost:8700**을 엽니다.

localhost는 내 컴퓨터의 앱 주소입니다. 재부팅하면 앱도 꺼지므로 다시 켭니다. 터미널을 닫으면 앱이 종료됩니다. 터미널 명령은 `bash start.sh`입니다. Python3.11 이상이 필요하고 최초 실행에 의존성을 설치합니다. macOS XGBoost·LightGBM은 `brew install libomp`가 필요합니다.

start.command는 설치된 Ollama를 연결합니다. qwen3.5:2b·qwen3-embedding:0.6b가 있으면 로컬 LLM·임베딩을 사용할 수 있습니다. bash start.sh 기본은 규칙·TF-IDF이며 `SEMI_LLM_ENABLED=1 bash start.sh`로 LLM을 켭니다. 실제 모드는 /health와 화면에 표시합니다.

## 6:2:2로 다시 확인한 결과

합성 센서는 **Train768 / Validation256 / Test256개**입니다. 같은 생산 묶음(lot)은 구간을 넘지 않습니다. SECOM은 날짜 블록60/20/20이므로 행 수는 **820 / 367 / 380개**입니다. 비율을 점수에 맞춰 자동 조정하지 않습니다. 이전 분할의 이력은 보존하지만 현재 화면의 예시 결과는6:2:2 버전만 선택합니다.

|자료|Test 불량 발견|정상 오판|Recall|Precision|F1|
|---|---:|---:|---:|---:|---:|
|합성 센서|27/32|14/224|84.4%|65.9%|74.0%|
|UCI 공개 센서 SECOM|5/23|87/357|21.7%|5.4%|8.7%|
|합성 이미지|14/15|0/105|93.3%|100.0%|96.6%|

최초 센서 후보 **CatBoost · A+B+C 학습**: 불량20/32개에서27/32개 발견, 정상 오판1개에서14개. 시연 목표 미달·추가 실험 필요. 선택 후보는 전체 Train768개 중 해당 제품의 **544개**를 학습했습니다.

재학습은 새 합성 배치의 같은 Test에서 불량43/167개에서153/167개, 정상 오판96개에서79개. Recall·정상 오판 시연 목표 충족. 회사 적용은 별도 검증. 운영 모델은 자동 교체하지 않습니다.

90% Recall·15% 정상 오판·Test 불량20개는 시연 목표이며 회사 양산 기준이 아닙니다. 정상 오판은 FP이며 재검사·폐기를 의미하지 않습니다. 제조 수율과 금액 이득, 실제 작업 시간 절감은 측정하지 않았습니다.

## 데이터와 모델

A·B·C·D는 합성 데이터의 가상 제품명입니다. UCI SECOM은 반도체 공정 센서와 합격/불합격 기록1,567건·불합격104건입니다. 제조사명은 원자료에 제공하지 않으며 같은 이름의 경비회사와 연결할 근거는 확인하지 못했습니다. McCann & Johnston(2008), [UCI 원본](https://archive.ics.uci.edu/dataset/179/secom), [DOI10.24432/C54305](https://doi.org/10.24432/C54305), CC BY4.0. 숫자 센서 원파일590열과 공식 메타데이터591 features 표기를 구분합니다.

센서12종: Logistic, Decision Tree, RF, GB, XGBoost, LightGBM, CatBoost, KNN, SVM, MLP, AdaBoost, HistGB. 전체 제품12종×불균형2조건을 비교한 뒤 상위2알고리즘의 제품 조합을 확장해 최대52조건입니다. 완전탐색이 아닙니다. 이미지3종은 축소 ResNet·VGGNet·Autoencoder를 처음부터 학습하며 실제 SEM 이미지가 아닙니다.

## Agent와 재현

LangGraph 점검·계획·결과 검토, 로컬 Qwen,교육 근거14개와 실시간 공식 외부 문서 검색 RAG,4 MCP 도구, Store·Knowledge·Advisor 의존성 주입, 모듈화를 구현했습니다. 30개 단위/API 테스트와 MCP 실제 연결 기록은 docs/evaluation에 있습니다. LLM 수치를 신뢰하지 않고 실험 엔진이 계산합니다. 실패하면 규칙 설명을 사용합니다. 원격 추적 기능은 제출의 완성 기능에서 제외했습니다.

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/evaluate.py
.venv/bin/python scripts/evaluate_management.py
.venv/bin/python scripts/evaluate_agents.py
.venv/bin/python scripts/check_mcp.py
.venv/bin/python scripts/build_report.py
```

평가 승인은 자동 테스트 actor이며 현장 승인 실적이 아닙니다. 계획·데이터·분할 hash와 seed45를 저장합니다. 전처리·가중치는 Train에서만 fit합니다. 반복 Validation 선택과 작은 표본이 한계입니다. 기업 클라우드는 인증·권한·학습 worker·중앙 모델 관리가 추가로 필요하고 배포 예시는 실배포 미검증입니다. 공식 외부 모델 검색·RAG 제안·승인 후 학습·후보 목록 갱신을 구현했습니다. 현재 센서 ExtraTrees·GaussianNB 연결을 지원하며 임의 코드 자동 생성과 혼합 비율 탐색은 확장 범위입니다. [구현 범위](docs/MODEL_DISCOVERY_DESIGN.md) 교육 원본 전체·제출 명단 엑셀·비밀 값은 공개 저장소에 넣지 않습니다. 사용자가 요청한 교육 사진의 데이터 유형 분류 내용을 표로 재구성했습니다.
