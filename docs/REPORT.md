# 반도체 검사 모델 관리 Agent 최종 보고서

G045 김용찬 / SK AI Leader Academy / 과제2 신규 프로젝트 / 2026-10-20

## 문제와 목표

반도체 공정 엔지니어가 불량을 더 찾는 모델을 고를 때 정상 제품의 추가검사 부담도 함께 판단해야 합니다. 데이터 분포가 바뀌면 재학습이 필요한지, 제품 데이터를 합칠지 전용 모델을 쓸지도 다시 비교해야 합니다. 이 프로젝트는 검색 근거와 수치 규칙으로 실험을 제안하고 엔지니어 승인 후 실제 학습을 실행하는 교육용 Agent입니다. 특정 회사 플랫폼 연동은 범위에 포함하지 않습니다.

## 구현과 사용 흐름

1. 공정 센서 CSV 또는 검사 이미지 ZIP을 등록하고 라벨·중복·결측·제품·lot·시각을 점검합니다.
2. 데이터 종류에 맞는 모델 후보와 전처리·학습 제품 범위·불균형 대책을 계획합니다.
3. 계획 hash와 데이터 버전을 확인하고 엔지니어가 승인해야 학습합니다. 반려·미승인·중복 실행을 차단합니다.
4. 학습, 임계값 조정, 후보 선택, 최종 평가를 분리합니다. 같은 입력의 기본·선택 절차를 비교합니다.
5. 불량 추가 발견량과 정상 추가검사를 가정 생산량으로 환산합니다.
6. 새 라벨 배치에서 성능 저하를 점검하고 재학습을 제안합니다. 승인 후 공통·제품별 후보를 생성하고 같은 제품의 평가에서 방식을 선택합니다.
7. 권고 또는 보류 사유, 실제 모델 파일·버전을 저장합니다. 운영 장비·recipe·모델을 자동 교체하지 않습니다.

![검사 효과 화면](assets/easy-result.png)

## 교육 자료에 맞춘 모델

[교육 자료와 모델 선택 근거](CURRICULUM_MODELS.md)에 PDF명과 페이지를 정리했습니다. 공정 후보는 Decision Tree·Random Forest·Gradient Boosting·XGBoost·LightGBM·CatBoost·KNN·SVM·MLP·Logistic·AdaBoost·Hist Gradient Boosting 12종이며 이미지 후보는 교육용 축소 ResNet·VGGNet 계열과 Autoencoder입니다. 입력 형식에 맞는 후보군 안에서 실제 결과로 선택합니다. NLP·시계열 모델 우월성을 검증한 기능은 없습니다.

## 데이터와 분할

UCI SECOM은1,567행·불량104개·숫자 센서590열입니다. pass=-1을 정상0,fail=1을 불량1로 변환했고 제품 ID가 없어 단일 SECOM 제품으로 유지했습니다. [공식 출처, CC BY4.0](https://archive.ics.uci.edu/dataset/179/secom)

합성 공정은1,280행·불량201개·160lot, 합성 이미지는576장·불량85개·96lot입니다. 실제 제조 측정값이 아닙니다. SECOM은 날짜별 시간 순4분할, 합성 자료는 lot별4분할이며 합성 분할은 시간 순서가 아닙니다.

| 데이터 | Train | Calibration | Validation | Test |
|---|---:|---:|---:|---:|
| 합성 공정 | 704 | 192 | 192 | 192 |
| 공개 SECOM | 769 | 231 | 303 | 264 |
| 합성 이미지 | 306 | 90 | 90 | 90 |

전처리는 train에서만 fit합니다. 유효0을 결측으로 제거하지 않습니다. 정확한 중복 행·이미지를 거부하며 근접 중복은 별도 검사 필요입니다. Calibration에서 임계값,validation에서 후보를 고르고 test는 마지막 비교·보류에만 씁니다. 같은 target·평가 행을 고정합니다. [누수 방지 원칙](https://scikit-learn.org/stable/common_pitfalls.html)

공정 기본 모델은 전체 제품 train의 unweighted Logistic Regression,median+scaling,threshold0.5입니다. 이미지 기본 모델은 계획의 첫 지도학습 후보이며 이번에는 gray ResNetSmall,threshold0.5입니다. After는 모델·전처리·학습 범위·임계값을 함께 선택한 전체 절차입니다. 개별 요소의 인과 효과로 해석하지 않습니다.

## 실제 Before/After

| 데이터 | 후보 수 | Before Recall | After Recall | After Precision | After FPR | 판단 |
|---|---:|---:|---:|---:|---:|---|
| 합성 공정 | 52 | 60.0% | 96.0% | 48.0% | 15.6% | 보류 |
| 공개 SECOM | 24 | 6.7% | 93.3% | 6.0% | 88.8% | 보류 |
| 합성 이미지 | 6 | 64.3% | 100.0% | 100.0% | 0.0% | 보류 |

| 데이터 | Test 전체/불량 | Before 미탐/오탐 | After 미탐/오탐 | Before/After AP | Recall Wilson95% | 시간 |
|---|---:|---:|---:|---:|---:|---:|
| 합성 공정 | 192 / 25 | 10 / 1 | 1 / 26 | 0.851 / 0.920 | 80.5%~99.3% | 22.03초 |
| 공개 SECOM | 264 / 15 | 14 / 11 | 1 / 221 | 0.077 / 0.076 | 70.2%~98.8% | 23.05초 |
| 합성 이미지 | 90 / 14 | 5 / 45 | 0 / 0 | 0.436 / 1.000 | 78.5%~100.0% | 4.38초 |

합성 공정 선택은 **SVM (RBF) / B+C+D / auto / none**입니다. 합성 공정은 최종 FPR15.6%로 허용15%를 초과해 보류합니다. 공개 SECOM은 calibration·validation 기준을 동시에 만족한 후보가 없어 탐색 후보만 보고하고 보류합니다. 이미지 contrast 세 구조는 validation 주요 지표가 동률이어서 사전 정의한 trial ID로 Autoencoder를 선택했습니다. 구조 우월성의 증거가 아닙니다.

AP는 sklearn non-interpolated Average Precision입니다. 단일 seed45·CPU·Python3.11.15,이미지6epoch 결과입니다. 합성의 높은 성능은 실제 현장 성능을 입증하지 않습니다. Wilson 구간도 분포 변화의 보장은 아닙니다. [AP 정의](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html), [PyTorch 재현성](https://docs.pytorch.org/docs/stable/notes/randomness.html)

## 검사량·비용·재작업 가정

제품1,000개 중 불량100개·정상900개와 검증 비율 유지라는 **가정**입니다. 기본 모델은 불량60.0개, 선택 모델은96.0개를 찾습니다. 불량36.0개를 더 찾는 대신 정상 추가검사는5.4개에서140.1개로134.7개 늘어납니다.

미검출1개10만원·정상 추가검사1개1천원 가정에서는 손실4,005,389원에서540,120원, 차이3,465,269원입니다. 재작업·설비·처리량·매출 효과를 제외하여 실제 영업이익으로 해석하지 않습니다.

두 모델의 검출 불량 중20%를 재작업으로 정상화한다는 별도 가정에서는 양품7.2개를 추가 회수합니다. **재작업 후 양품 비율**은91.2%에서91.9%, 차이0.72%p입니다. 실제 결함의 재작업 가능성과 제조 수율 향상은 검증하지 않았습니다.

FPR은 실제 정상 중 잘못 추가검사 대상으로 고른 비율입니다. 화면에서는 정상 제품 추가 검사 허용 비율로 표현합니다. 15%는 정상100개 중 최대15개라는 뜻입니다. Recall은 실제 불량 중 발견 비율이므로 분모가 다릅니다.

계산식: D=N×불량률,G=N−D,발견=D×Recall,정상추가검사=G×FPR,손실=미탐×가정단가+정상추가검사×가정단가,재작업후양품률=(G+발견×정상화비율)/N. [계산 원본](evaluation/presentation_cases.json),[구현](../app/impact.py)

## 재학습 판단과 공통·제품별 비교

독립 seed1045의 새 합성3,840행·480lot에서 불량 발생 규칙을 변경했습니다. 이전 데이터와 중복되는 센서 행을 거부하고 새 train 구간에서만 기존 모델을 점검합니다. 이전 test Recall96.0%에 비해 새 train 점검39.2%,FPR27.1%로 **재학습 필요**을 제안했습니다. 서로 다른 배치의 비교이며 Recall10%p하락 등의 개발 휴리스틱은 통계적 drift 검정이 아닙니다. 불량20개 미만은 판단 보류합니다.

공통1개와 제품별4개 계획 생성 시 학습하지 않는 것을 검증했습니다. 자동 검증용 테스트 승인자로 승인한 뒤 각4개,총20개 조건(Random Forest/Logistic,none/weighted)을 실제 학습했습니다. 현장 승인 실적이 아닙니다.

| 제품 | 공통 Recall / FPR | 전용 Recall / FPR | 선택 방식 | 최종 판단 |
|---|---:|---:|---|---|
| A | 95.1% / 14.3% | 87.8% / 10.9% | 공통 | 공통 모델 권고 |
| B | 92.9% / 16.3% | 92.9% / 21.7% | 공통 | 적용 보류 |
| C | 92.3% / 12.8% | 92.3% / 12.8% | 전용 | 제품 전용 모델 권고 |
| D | 100.0% / 12.9% | 91.7% / 14.3% | 공통 | 적용 보류 |

표는 **동일 제품의 같은 validation 행**을 평가한 수치입니다. 각 후보는 train에서 학습하고 calibration에서 정한 임계값을 고정합니다. calibration·validation 기준을 충족한 후보 중 Recall,AP 순으로 방식을 선택하고 동률이면 공통을 택합니다. 둘 다 부족하면 비용 최소 참고 후보를 표시하고 보류합니다. test는 순위에 사용하지 않고 최종 확인·보류에만 사용합니다. 내부 후보와 방식 선택이 같은 validation을 재사용하므로 낙관 편향 가능성이 있습니다. 독립 기간 반복 평가가 필요합니다.

새로 등록한 한 배치 안의 제품 데이터를 통합·분리합니다. 과거 배치 파일을 자동 병합하지 않습니다. 파일·버전·source run·제품·지표·검토 상태를 저장하며 자동 배포false입니다. [점검·실행·비교 원본](evaluation/model_management.json)

## 학습 제품 부분집합 비교

이 표는 기존 합성 공정의 같은 validation192개를 평가합니다. 전용 제품만 평가하는 위의 새 배치 전략 비교와 목적이 다릅니다.

| 학습 제품 | 후보 | Recall | Precision | FPR |
|---|---|---:|---:|---:|
| A | CatBoost / weighted | 91.2% | 66.0% | 10.1% |
| B | 기준 충족 후보 없음 | — | — | — |
| C | CatBoost / weighted | 97.1% | 63.5% | 12.0% |
| D | SVM (RBF) / none | 91.2% | 63.3% | 11.4% |
| A+B | SVM (RBF) / none | 91.2% | 66.0% | 10.1% |
| A+C | SVM (RBF) / none | 97.1% | 67.3% | 10.1% |
| A+D | SVM (RBF) / none | 88.2% | 76.9% | 5.7% |
| B+C | CatBoost / weighted | 94.1% | 58.2% | 14.6% |
| B+D | CatBoost / weighted | 88.2% | 60.0% | 12.7% |
| C+D | SVM (RBF) / none | 94.1% | 74.4% | 7.0% |
| A+B+C | CatBoost / weighted | 97.1% | 60.0% | 13.9% |
| A+B+D | SVM (RBF) / none | 97.1% | 67.3% | 10.1% |
| A+C+D | CatBoost / weighted | 97.1% | 61.1% | 13.3% |
| B+C+D | SVM (RBF) / none | 100.0% | 61.8% | 13.3% |
| A+B+C+D | SVM (RBF) / none | 97.1% | 68.8% | 9.5% |

## Agent 구조와 기술 평가

LangGraph의 검사·검색·실험 계획 그래프와 결과 검토 역할을 분리했습니다. DataQualityAgent·ExperimentPlannerAgent·ResultCriticAgent가 로컬 Qwen3.5:2b를 호출하여 관측 사실과 검색 문서에서 허용된 판단의 우선순위를 제안합니다. 모델 선택 수치·실험 예산·승인·최종 보류는 분석 엔진이 결정합니다. LLM의 코드·출처·주제 연결 검사를 통과하지 못하면 규칙 설명으로 대체하며 실패 상태를 숨기지 않습니다. 실제 통합 검증에서는 품질·계획 역할이 검사를 통과했고 결과 검토는 출처 검사 실패로 규칙 fallback을 사용했습니다. 자유 대화형 자율 Agent나 운영 자동 배포는 아닙니다.

13개 요약 근거 문서를 qwen3-embedding:0.6b로 임베딩하고 cosine 검색한 뒤 역할별 생성 입력에 연결합니다. TF-IDF는 비교 기준과 연결 장애 시 fallback으로 유지합니다. 같은 13개 고정 질문에서 검색 Hit@3는 둘 다100%, MRR@3는0.9103에서0.9615였습니다. 자체 정답표의 작은 평가로 일반 검색 개선을 보장하지 않습니다. dense는 로컬 모델 호출 때문에 더 느립니다. 실제 질의·응답 시간과 역할별 성공/거부 상태는 [통합 검증 JSON](evaluation/agent_integration.json)에 기록합니다. 유료 LLM API 비용은0원이며 로컬 연산·전력 비용은 측정하지 않았습니다.

MCP는 list_datasets,propose_experiment,get_experiment_result,explain_model_candidates와 지식 resource를 제공합니다. 실제 stdio handshake·tools/list·tools/call·resources/read 및 모델 설명 도구 호출을 검증했습니다. 승인·실행 도구는 노출하지 않습니다. DI로 Store·Knowledge·Advisor를 주입하고 API·MCP가 Workbench를 재사용합니다. SQLite에 hash·승인·이벤트·후보 이력을 저장하며 학습 worker는 단일 프로세스입니다.

LangSmith @traceable 계측과 실제 전송을 시도했지만, 기존 자격 증명으로 원격 API가403 Forbidden을 반환했습니다. 따라서 원격 추적 성공을 주장하지 않습니다. 로컬 실험·통합 검증 기록은 저장했고 유효한 프로젝트 권한으로 원격 추적 재검증이 필요합니다. 비밀 값은 저장소에 넣지 않았습니다.

| 평가항목 | 증빙 |
|---|---|
| 기능30 | 실제 공정·이미지 학습, 승인, 성능 저하 점검, 통합·전용 모델 생성·비교 |
| 기술30 | LangGraph 역할,검색 근거,DI,MCP,모듈화,단위/API 테스트 |
| 한계20 | 공개 SECOM 실패,검사 부담,작은 불량 표본,합성·비용 가정 명시 |
| 발표20 | 쉬운 건수 비교,승인 시연,발표 대본과 코드 설명 |
| Before/After bonus10 | 같은 입력·분할의 기본/선택 절차 실측 수치 |

26개 테스트를 통과했습니다. 분할·누수·지표·승인·인증·API·SSE·CSV,가정 계산,재학습 계획 시 실행 없음,승인 후 후보 버전,validation만으로 전략 선택을 확인했습니다. [테스트 로그](evaluation/tests.txt),[MCP 실측](evaluation/mcp_check.json)

## 외부 모델 발굴과 목록 갱신 (확장 설계)

외부 검색으로 새 모델을 찾고 모델 문서·과거 실험을 RAG로 참고한 뒤 적합성을 검토합니다. 엔지니어 승인 후 같은 분할에서 성능·검사 부담·자원 비용을 비교하고 검증 완료 후보 목록을 갱신하는 흐름입니다. [설계 문서](MODEL_DISCOVERY_DESIGN.md)에 상태와 승인·평가 조건을 정리했습니다. 현재 외부 모델 발굴·adapter 생성·자동 목록 갱신은 미구현입니다.

## 한계와 다음 단계

단일 seed·작은 불량 표본·반복 validation 비교의 한계가 있습니다. 기준Precision25%이상,FPR15%이하,test불량20개이상은 교육용 개발 정책이며 현장 승인 기준이 아닙니다. 실제 wafer·장비·기간·제품별 독립 검증과 비용·처리량 측정이 필요합니다.

이미지 모델은32×32·축소 구조·scratch6epoch입니다. GAN·자연어·시계열·SEM길이·공정 조건별 수율 예측은 미구현입니다. 조건별 수율 예측에는 lot별 투입/양품 수량과 시간·장비·공정 조건 이력이 필요합니다. pass/fail 확률을 제조 수율로 대체하지 않습니다.

기업용 클라우드 확장을 위한 Docker/Kubernetes 예시는 제공하지만 빌드·실배포는 미검증입니다. 현재 SQLite 단일 worker와 공유 토큰은 SSO/RBAC를 대체하지 않습니다. 실제 도입에는 개인 인증·권한,worker queue,object storage,model registry,중앙 감사·백업이 필요합니다.

교육 자료·아이디어 사진 원본은 공개 저장소에 올리지 않았습니다. 자료명·참고 페이지는 [교육 모델 근거](CURRICULUM_MODELS.md)에 남겼습니다. 공개 데이터는 [UCI SECOM](https://archive.ics.uci.edu/dataset/179/secom),원본 ZIP SHA256은eea568baf3c2229096d7d294cf0b096b5502bd96d92c0b80a65b84714059be8e입니다.

실행·재현은 [README](../README.md),시연은 [DEMO](DEMO.md),읽을 대본은 [TXT](발표대본_G045.txt),코드는 https://github.com/dragonchan95/Semiconductor-AI-Agent 입니다.
