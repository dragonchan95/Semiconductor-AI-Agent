# 반도체 검사 모델 실험 도우미

G045 김용찬 · 과제2 · 2026-10-21

6:2:2로 재실험한 현재 결과만 사용합니다.

## 1. 반도체 검사 모델 실험 도우미

프로젝트 소개

데이터에 맞는 모델을 비교하고, 승인받아 학습하는 Agent

G045 김용찬 · SK AI Leader Academy · 과제 2

안녕하세요. G045 김용찬입니다. 반도체 검사 데이터에 맞는 모델을 비교하고, 승인받아 학습하는 Agent를 만들었습니다.

## 2. 데이터 종류에 따라 쓰는 모델이 다릅니다

출발점 · 반도체 교육에서 배운 데이터와 모델

이번 구현: 검사 이미지와 숫자 센서의 정상·불량 분류

자연어 로그 분석·시계열 예측은 향후 확장 범위

| 데이터 종류 | 반도체 업무 활용 예시 | 교육자료의 모델 예시 |
|---|---|---|
| 검사 이미지 | 불량 이미지 분류 / 단면 길이 분석 | ResNet · VGGNet / GAN · Autoencoder |
| 자연어·로그 | 장비 불량 유형 분류 / 공정 로그 분석 | LSTM · GPT · BERT |
| 시계열 | 수율 분석 / 산포 분석 | LSTM · ARIMA / Autoencoder |

반도체 교육에서 배운 내용입니다. 검사 이미지, 장비 로그, 시간에 따라 쌓이는 데이터는 형태가 달라 쓰는 모델도 다릅니다. 이 프로젝트에서는 범위를 줄여 검사 이미지와 숫자 센서의 정상·불량 분류를 구현했습니다. 자연어 로그와 시계열 예측까지 모두 구현한 것은 아닙니다.

출처: 사용자 제공 반도체 교육 사진2 / 20261017_135247.jpg. 분류 화면의 내용을 사용자 요청에 따라 편집 가능한 표로 재구성.

## 3. 반복할 모델 실험을 Agent에게 맡깁니다

사용자 · 검사 모델을 만드는 공정·장비 엔지니어

사용 상황: 새 검사 데이터에 어떤 모델을 쓸지 비교합니다.

엔지니어는 계획을 검토하고, Agent는 승인받은 실험을 실행합니다.

| 순서 | 엔지니어의 행동 | Agent가 보여 주는 내용 |
|---|---|---|
| 1. 입력 | 검사 데이터 선택 | 데이터 상태와 비교 계획 |
| 2. 승인 | 모델·전처리 계획 확인 후 승인 | 실제 학습과 Validation 비교 |
| 3. 결론 | 기본 모델과 후보 결과 확인 | 불량 발견·정상 오판·추가 실험 판단 |

엔지니어가 전처리와 여러 모델을 직접 반복 비교하는 상황을 생각했습니다. 데이터를 선택하면 Agent가 계획을 제안하고, 엔지니어가 승인하면 학습합니다. 결과에서는 기본 모델보다 무엇이 달라졌고 추가 실험이 필요한지 보여 줍니다.

출처: https://news.skhynix.com/en/the-past-present-and-future-of-data-science-organization-at-sk-hynix/; app/workbench.py

## 4. 데이터 선택 후 비교 계획을 요청합니다

본 실험 1/3 · 정상/불량 정답이 있는 합성 센서

선택: 제품 A–D 합성 센서 1,280건, 불량201건

엔지니어 행동: 비교 목표를 정하고 “비교 계획 제안받기” 클릭

같은 사례로 끝까지 보겠습니다. 제품 A부터D의 합성 센서1,280건을 선택하고 비교 계획을 요청합니다. 불량 정답은201건이며 제품 이름은 가상입니다. 기존 완료 결과를 보는 버튼은 이전 실험을 불러오는 기능입니다.

출처: https://archive.ics.uci.edu/dataset/179/secom; app/data.py

## 5. 계획의 이유를 확인하고 학습을 승인합니다

본 실험 2/3 · 앞에서 선택한 같은 센서 데이터

학습60% · 검증20% · 마지막 확인20%로 고정

생산 묶음(lot)이 학습·평가에 섞이지 않도록 분리합니다.

Agent가 결측과 불량 비율을 점검하고 전처리·모델 계획을 제안합니다. 필요한 모델에는 Scaling을 적용합니다. 학습, 검증, 마지막 확인 데이터는 수업 기준6대2대2로 고정했습니다. 생산 묶음인 lot이 학습과 평가에 섞이지 않게 나눕니다. 이 승인 버튼을 눌러야 실제 학습합니다.

출처: app/data.py; app/catalog.py; docs/CURRICULUM_MODELS.md

## 6. 후보는 골랐지만, 추가 실험이 필요합니다

본 실험 3/3 · 승인한 비교 실험의 결과

기본: Logistic Regression / 선택 후보: CatBoost · A+B+C 학습

Test 불량27/32개 발견. 목표 미달로 추가 실험 필요

결과입니다. 기본 비교 모델은 Logistic Regression이고, 이번 실험에서 고른 후보는 A B C로 학습한 CatBoost입니다. 같은 Test에서 불량32개 중20개를 찾던 것이27개로 늘었지만 정상 오판도1개에서14개로 늘었습니다. 후보 Recall84.4퍼센트는 시연 목표에 못 미쳐 추가 실험이 필요합니다. 현장 적용 모델로 확정한 것은 아닙니다.

출처: docs/evaluation/synthetic_process.json

## 7. 데이터를 바꾸면 모델과 결론도 달라집니다

같은 앱의 세 가지 데이터 · 각 데이터 안에서 같은 Test로 비교

기본 / 후보 순으로 표시했습니다. 각 행의 Test는 서로 다릅니다.

UCI SECOM: 공개 반도체 센서·합격/불합격 기록, McCann & Johnston(2008)

| 데이터 | 기본 모델 / 선택 후보 | 불량 발견
기본 / 후보 | 정상 오판
기본 / 후보 | Agent의 결론 |
|---|---|---|---|---|
| 합성 센서 / 제품 A–D | Logistic / CatBoost / 후보 학습: A+B+C | 20 / 27 / (불량32개) | 1 / 14 / (정상224개) | Recall84.4% / 추가 실험 필요 |
| UCI SECOM / 공개 센서 | Logistic / XGBoost / XGBoost는 참고 결과 | 0 / 5 / (불량23개) | 17 / 87 / (정상357개) | 목표 충족 후보 없음 / 데이터·계획 재검토 |
| 합성 이미지 | 축소 ResNet / / Autoencoder | 15 / 14 / (불량15개) | 32 / 0 / (정상105개) | Recall93.3% / 불량 표본 보강 필요 |

다른 데이터도 같은 앱에서 확인할 수 있습니다. 합성 센서는 불량을 더 찾았지만 정상 오판이 늘었습니다. UCI SECOM은 실제 공개 반도체 센서와 합격·불합격 기록인데, 이번 조건에서는 목표를 만족한 모델이 없었습니다. 합성 이미지는 Autoencoder가 정상 오판을 줄였지만 불량 하나를 놓쳤고, 평가 불량이15개로 작았습니다. 데이터마다 Test가 다르므로 이 표를 모델의 종합 순위로 해석하지 않습니다.

출처: https://archive.ics.uci.edu/dataset/179/secom; https://doi.org/10.24432/C54305; docs/evaluation/synthetic_process.json; docs/evaluation/secom.json; docs/evaluation/images.json

## 8. Recall을 우선하되 정상 오판도 함께 봅니다

판단 기준 · 불량을 Positive로 둡니다

먼저 중요한 불량의 검출 목표와 정상 오판 허용 목표를 정합니다.

현재90%·15%는 교육용 시연 목표입니다. 회사별 기준은 별도 합의합니다.

| 지표 | 쉽게 말하면 | 이번 프로젝트에서의 역할 |
|---|---|---|
| Recall | 실제 불량 중 몇 개를 찾았나? | 불량을 놓치지 않는 목표를 우선 확인 |
| 정상 오판률 | 실제 정상 중 몇 개를 불량으로 잘못 봤나? | Recall만 높이는 후보를 걸러내는 목표 |
| Precision · F1 | 불량 판정의 정확성과 Recall의 균형 | 후보의 장단점을 함께 보는 보조 지표 |

불량 유출을 막는 검사에서는 Recall을 우선하되, 전부 불량이라고 판정하는 모델을 고르면 안 됩니다. 그래서 정상 오판 목표도 함께 확인합니다. Precision은 불량이라고 본 것 중 진짜 불량의 비율이고, F1은 Precision과 Recall을 함께 보는 지표입니다. 어떤 지표가 무조건 최고라는 회사 공통 수치 대신, 담당자가 검사 목적에 맞는 목표를 정하도록 했습니다.

출처: https://ir.kla.com/news-events/press-releases/detail/121/kla-tencor-introduces-comprehensive-wafer-inspection-and; https://scikit-learn.org/stable/modules/generated/sklearn.metrics.f1_score.html

## 9. 공식 문서에서 새 후보를 찾아 실험합니다

추가 기능 · 엔지니어가 아직 비교하지 않은 모델 찾기

공식 모델 목록 검색 · RAG 근거 확인 · 계획 승인 · 실제 학습

센서 ExtraTrees·GaussianNB 실험 후 CatBoost 유지. 새 후보 이력을 저장했습니다.

엔지니어가 기존 모델을 알고 있다는 점을 고려해 새 모델 탐색도 추가했습니다. 공식 모델 목록과 문서를 가져오고 RAG로 근거를 검색해 ExtraTrees와 Gaussian Naive Bayes를 제안합니다. 엔지니어가 계획을 승인하면 기존 후보와 같은 조건으로 실제 학습하고 모델 목록에 결과를 남깁니다. 현재는 두 개의 검토된 센서 모델 연결을 지원합니다. 웹에서 임의 코드를 받아 실행하는 기능은 아닙니다. 기존 Test를 다시 쓴 탐색 결과이므로 현장 적용에는 독립 기간 검증이 필요합니다.

출처: app/discovery.py; docs/evaluation/model_discovery.json; https://scikit-learn.org/stable/api/index.html

## 10. 검사 모델을 비교하고 다음 실험을 판단합니다

결론 · 지금 사용할 수 있는 기능과 남은 검증

사용: 데이터 선택, 계획 승인, 기본 모델과 후보 비교

추가: 새 모델 탐색 RAG, 재학습, 합친 학습·제품별 학습 비교

한계: 합성 데이터·작은 불량 표본·Test 재사용 탐색 비교

다음: 현장 데이터와 담당자 기준으로 독립 기간 검증

핵심은 가장 좋아 보이는 모델 이름만 알려 주는 것이 아니라, 실제 실험을 수행하고 불량 발견과 정상 오판으로 다음 판단을 돕는 것입니다. 새 모델 탐색, 기존 모델 재학습, 제품별 학습 비교를 연결했습니다. 합성과 공개 자료로 확인한 교육용 결과이며 현장 검증이 필요합니다. 감사합니다.

출처: docs/evaluation/tests.txt; https://news.skhynix.com/en/the-past-present-and-future-of-data-science-organization-at-sk-hynix/

## 11. 점검 후, 승인받아 같은 알고리즘을 재학습합니다

추가 상황 · 같은 제품에 새 정답 데이터가 들어왔습니다

새 합성 배치의 같은 Test: 불량 발견 43/167개에서 153/167개

정상 오판 96개에서 79개. Recall·정상 오판 시연 목표 충족. 회사 적용은 별도 검증

추가 상황입니다. 기존 모델이 있으면 같은 제품의 새 정답 데이터로 점검하고 재학습을 제안합니다. 승인 후 같은 CatBoost를 다시 학습한 합성 시연입니다. 새 배치의 같은 Test에서 불량 발견은43개에서153개, 정상 오판은96개에서79개가 됐습니다. Recall91.6%, 정상 오판률13.1%입니다. 운영 모델은 자동 교체하지 않습니다.

출처: docs/evaluation/model_management.json

## 12. 제품별로 합친 학습과 개별 학습을 비교합니다

추가 기능 · 제품 데이터를 합칠지 나눌지 비교합니다

C 제품: 같은 Validation에서 “C만 학습” 후보 선택

C의 별도 Test Recall79.1%. 추가 데이터로 재확인 필요

제품 데이터를 합칠지 따로 학습할지도 비교합니다. C의 같은 Validation에서는 C만 학습한 후보를 골랐습니다. 별도 Test의 Recall은79.1%여서 추가 데이터로 재확인 필요입니다. 제품별 학습이 항상 좋다는 결론은 아닙니다.

출처: docs/evaluation/model_management.json

## 13. Validation으로 고르고, Test로 마지막 확인합니다

부록 · 상세 지표와 검증 방식

Train은 학습, Validation은 후보·판정값 비교, Test는 마지막 확인

합성 센서 Train60%(768개) / Validation20%(256개) / Test20%(256개)

같은 생산 묶음(lot)·날짜 경계를 보존합니다. 후보의 제품 범위에 따라 Train 실사용 수는 다릅니다.

F1은 보조 지표입니다. Test 점수를 보며 분할·후보를 조정하지 않습니다.

| 선택 후보의 Test 결과 | Recall | Precision | F1 | 정상 오판률 |
|---|---|---|---|---|
| 합성 센서 | 84.4% | 65.9% | 74.0% | 6.3% |
| UCI 공개 센서 SECOM | 21.7% | 5.4% | 8.7% | 24.4% |
| 합성 이미지 | 93.3% | 100.0% | 96.6% | 0.0% |

수업 기준에 맞춰6대2대2를 사전에 고정했습니다. 합성 센서 전체 학습 풀은768개이고 선택 후보는 그중A+B+C의544개를 학습했습니다. SECOM은 날짜 블록60/20/20을 나눠 실제 행 수는[820, 367, 380]개입니다. 원자료의 제조사명은 제공되지 않습니다. 반복 Validation 비교와 단일 seed의 한계가 있어 독립 기간 평가가 필요합니다. Recall=TP/(TP+FN), Precision=TP/(TP+FP), F1=2TP/(2TP+FP+FN), 정상 오판률=FP/(FP+TN)입니다.

출처: app/data.py; docs/evaluation/summary.json; https://scikit-learn.org/stable/modules/cross_validation.html

## 14. 공개 반도체 공정 데이터: UCI SECOM

데이터 출처 · 실측 결과와 합성 시연을 구분합니다

McCann, M. & Johnston, A. (2008). SECOM [Dataset].

UCI Machine Learning Repository · DOI: 10.24432/C54305 · CC BY4.0

archive.ics.uci.edu/dataset/179/secom

| 자료 | 입력과 정답 | 한계·최종 Test 결과 |
|---|---|---|
| UCI SECOM 공개 원본 | 1,567건·센서590열 / 합격/불합격 기록·불합격104건 | 제조사명·제품ID 제공 없음 / 불량5/23개 발견·정상87/357개 오판 |
| 합성 센서 / 합성 이미지 | 가상 제품 A–D / 연습용 패턴 | 실제 생산 데이터·SEM 이미지 아님 / 이미지 불량14/15개 발견 |

공개 데이터 출처는 UCI Machine Learning Repository의 SECOM입니다. McCann과 Johnston이2008년에 공개했고 DOI와 원본 링크를 적었습니다. 제조사명은 원자료에 없습니다. 실제 공개 자료에서는 Test 불량23개 중5개를 찾았습니다. 합성 시연의 개선을 실제 공장 효과로 일반화하지 않습니다.

출처: https://archive.ics.uci.edu/dataset/179/secom; https://doi.org/10.24432/C54305; data/public/secom/secom.names; docs/evaluation/secom.json; docs/evaluation/images.json

## 15. 앙상블 비율도 Validation에서 비교하는 확장

부록 · 앙상블 혼합 비율은 확장 설계이며 미구현

현재: RF·부스팅 사용. 서로 다른 모델의 혼합 비율 탐색은 미구현

6:2:2 분할을 비교 전에 고정하고 “실험한 비율 중 가장 좋은 후보”로 설명

| 확장 단계 | Agent가 설명할 내용 |
|---|---|
| 1. 같은 입력·고정 분할 | 동일 입력·라벨의 모델1·모델2를 Train으로 학습 |
| 2. 승인받아 비율 비교 | 0:100,25:75,50:50,75:25,100:0 등 예시 실험안 / 측정한 최적값 아님 |
| 3. Validation에서 선택 | Recall 우선·정상 오판 함께 확인. 목표 미달이면 추가 실험 |
| 4. 고정된 Test로 확인 | 선택 비율을 고정해 단일 모델과 비교. 두 모델 운영 부담 확인 |

가중치를 비교하는 확장 설계입니다. 현재 RF·부스팅 알고리즘은 실제 사용하지만 서로 다른 모델의 예측 확률을 섞는 비율 탐색은 미구현입니다. 사전 정의한 비율과 판정값을 Validation에서 고르고 고정된 Test에서 확인합니다. 모든 문제에 통용되는 전역 최적 비율이라는 주장을 하지 않습니다.  외부 모델 탐색은 공식 scikit-learn 목록과 두 개의 검토된 adapter 범위에서 실제 구현했습니다. 임의 웹 모델 자동 코드 생성은 지원하지 않습니다.

출처: docs/MODEL_DISCOVERY_DESIGN.md; https://scikit-learn.org/stable/modules/ensemble.html#voting-classifier

## 16. 기술 요소가 반영된 위치

부록 · 기술 요소와 구현 위치

상세 대응표: docs/ASSIGNMENT_CHECKLIST.md

| 기술 요소 | 구현 위치 | 확인 상태 |
|---|---|---|
| Multi-Agent | planner.py · advisors.py | 데이터 점검·계획·결과 검토 역할 |
| RAG | discovery.py · Knowledge | 공식 외부 문서 검색·후보 제안·승인 후 학습 |
| MCP | mcp_server.py | 4도구·지식 resource 실제 연결 |
| 의존성 주입 | Dependencies · Workbench | Store·Knowledge·Advisor 주입 |
| 모듈화 | app/ 데이터·학습·관리 모듈 | API·MCP가 공통 엔진 재사용 |
| 단위/API 테스트 | tests/ | 30개 테스트 통과 |

기술 요소와 구현 위치를 연결한 표입니다. 점수는 적지 않습니다. 본문1~10장, 질문용 부록11~16장입니다.

출처: docs/ASSIGNMENT_CHECKLIST.md; docs/evaluation/tests.txt; docs/evaluation/mcp_check.json

## 제품별 검증 상세

|제품|합친 학습 Validation Recall/FPR|제품만 학습 Validation Recall/FPR|선택|Test 판단|
|---|---|---|---|---|
|A|98.6%/14.8%|94.2%/14.2%|shared|여러 제품을 합쳐 학습한 후보|
|B|89.7%/13.2%|89.7%/14.9%|shared|추가 데이터로 재확인 필요|
|C|90.9%/14.3%|93.2%/14.3%|separate|추가 데이터로 재확인 필요|
|D|98.2%/8.3%|98.2%/13.9%|shared|추가 데이터로 재확인 필요|

새 데이터의 학습 범위 비교이며 과거 파일을 자동 병합하지 않습니다. 기존 모델·판정값을 고정해 새 학습 구간에서 점검하고 Test는 재학습 필요 판단에 사용하지 않습니다. 성능 저하 배치는 새 합성3,840행·480lot이며 실제 공정 변화 실측이 아닙니다.

원본 SECOM 수치 센서는590열이고 UCI 메타데이터는591 features라고 표기합니다. pass=-1은 정상0, fail=1은 불량1로 변환했습니다. 제품ID·제조사명을 제공하지 않습니다. CC BY4.0, McCann & Johnston(2008), DOI10.24432/C54305입니다.

교육 근거 검색 평가는14개 요약문과 고정13질의의 작은 자체 평가입니다. 새 외부 모델 검색의 품질 평가와 구분합니다. 검색 방식 간 결과는 agent_integration.json을 참조하며 일반 검색 성능 개선을 보장하지 않습니다. LLM 검사 실패는 규칙 설명으로 처리합니다. 운영 자동 배포, 수율·금액 이익, 공정조건 수율 예측, NLP·시계열·SEM 길이, 임의 외부 모델 코드 자동 생성과 혼합 비율 탐색은 검증된 실행 기능이 아닙니다. 공식 문서 기반 ExtraTrees·GaussianNB 발굴·실험은 구현했습니다. Docker/Kubernetes 예시는 실배포 미검증이며 기업 인증·권한·worker·모델 registry가 필요합니다.
