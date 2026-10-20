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

[교육 자료와 모델 선택 근거](CURRICULUM_MODELS.md)에 PDF명과 페이지를 정리했습니다. 공정 후보는 Random Forest, Logistic Regression, Hist Gradient Boosting이며 이미지 후보는 교육용 축소 ResNet·VGGNet 계열과 Autoencoder입니다. 입력 형식에 맞는 후보군 안에서 실제 결과로 선택합니다. NLP·시계열 모델 우월성을 검증한 기능은 없습니다.

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
| 합성 공정 | 60 | 60.0% | 88.0% | 53.7% | 11.4% | 합성 내 검토 가능 |
| 공개 SECOM | 12 | 6.7% | 60.0% | 5.2% | 65.5% | 보류 |
| 합성 이미지 | 6 | 64.3% | 100.0% | 100.0% | 0.0% | 보류 |

| 데이터 | Test 전체/불량 | Before 미탐/오탐 | After 미탐/오탐 | Before/After AP | Recall Wilson95% | 시간 |
|---|---:|---:|---:|---:|---:|---:|
| 합성 공정 | 192 / 25 | 10 / 1 | 3 / 19 | 0.851 / 0.852 | 70.0%~95.8% | 25.54초 |
| 공개 SECOM | 264 / 15 | 14 / 11 | 6 / 163 | 0.077 / 0.069 | 35.7%~80.2% | 15.59초 |
| 합성 이미지 | 90 / 14 | 5 / 45 | 0 / 0 | 0.436 / 1.000 | 78.5%~100.0% | 4.22초 |

합성 공정 선택은 **Random Forest / B+C / scaled / none**입니다. 공개 SECOM은 calibration·validation 기준을 동시에 만족한 후보가 없어 탐색 후보만 보고하고 보류합니다. 이미지 contrast 세 구조는 validation 주요 지표가 동률이어서 사전 정의한 trial ID로 Autoencoder를 선택했습니다. 구조 우월성의 증거가 아닙니다.

AP는 sklearn non-interpolated Average Precision입니다. 단일 seed45·CPU·Python3.11.15,이미지6epoch 결과입니다. 합성의 높은 성능은 실제 현장 성능을 입증하지 않습니다. Wilson 구간도 분포 변화의 보장은 아닙니다. [AP 정의](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html), [PyTorch 재현성](https://docs.pytorch.org/docs/stable/notes/randomness.html)

## 검사량·비용·재작업 가정

제품1,000개 중 불량100개·정상900개와 검증 비율 유지라는 **가정**입니다. 기본 모델은 불량60.0개, 선택 모델은88.0개를 찾습니다. 불량28.0개를 더 찾는 대신 정상 추가검사는5.4개에서102.4개로97.0개 늘어납니다.

미검출1개10만원·정상 추가검사1개1천원 가정에서는 손실4,005,389원에서1,302,395원, 차이2,702,994원입니다. 재작업·설비·처리량·매출 효과를 제외하여 실제 영업이익으로 해석하지 않습니다.

두 모델의 검출 불량 중20%를 재작업으로 정상화한다는 별도 가정에서는 양품5.6개를 추가 회수합니다. **재작업 후 양품 비율**은91.2%에서91.8%, 차이0.56%p입니다. 실제 결함의 재작업 가능성과 제조 수율 향상은 검증하지 않았습니다.

FPR은 실제 정상 중 잘못 추가검사 대상으로 고른 비율입니다. 화면에서는 정상 제품 추가 검사 허용 비율로 표현합니다. 15%는 정상100개 중 최대15개라는 뜻입니다. Recall은 실제 불량 중 발견 비율이므로 분모가 다릅니다.

계산식: D=N×불량률,G=N−D,발견=D×Recall,정상추가검사=G×FPR,손실=미탐×가정단가+정상추가검사×가정단가,재작업후양품률=(G+발견×정상화비율)/N. [계산 원본](evaluation/presentation_cases.json),[구현](../app/impact.py)

## 재학습 판단과 공통·제품별 비교

독립 seed1045의 새 합성3,840행·480lot에서 불량 발생 규칙을 변경했습니다. 이전 데이터와 중복되는 센서 행을 거부하고 새 train 구간에서만 기존 모델을 점검합니다. 이전 test Recall88.0%에 비해 새 train 점검37.1%,FPR23.9%로 **재학습 필요**을 제안했습니다. 서로 다른 배치의 비교이며 Recall10%p하락 등의 개발 휴리스틱은 통계적 drift 검정이 아닙니다. 불량20개 미만은 판단 보류합니다.

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
| A | Random Forest / none | 94.1% | 65.3% | 10.8% |
| B | Random Forest / none | 73.5% | 61.0% | 10.1% |
| C | Random Forest / none | 91.2% | 72.1% | 7.6% |
| D | Random Forest / weighted | 79.4% | 56.2% | 13.3% |
| A+B | Random Forest / none | 94.1% | 64.0% | 11.4% |
| A+C | Random Forest / none | 94.1% | 66.7% | 10.1% |
| A+D | Random Forest / none | 88.2% | 57.7% | 13.9% |
| B+C | Random Forest / none | 100.0% | 64.2% | 12.0% |
| B+D | Random Forest / weighted | 85.3% | 65.9% | 9.5% |
| C+D | Random Forest / weighted | 91.2% | 62.0% | 12.0% |
| A+B+C | Random Forest / none | 97.1% | 62.3% | 12.7% |
| A+B+D | Random Forest / weighted | 88.2% | 62.5% | 11.4% |
| A+C+D | Random Forest / weighted | 88.2% | 68.2% | 8.9% |
| B+C+D | Random Forest / none | 85.3% | 63.0% | 10.8% |
| A+B+C+D | Random Forest / none | 94.1% | 60.4% | 13.3% |

## Agent 구조와 기술 평가

LangGraph의 DataQualityAgent,KnowledgeAgent,ExperimentPlannerAgent는 결정적 Python 역할 노드입니다. 독립 LLM 추론 Multi-Agent는 구현하지 않았습니다. TF-IDF 문자2~4gram 검색으로8개 정책 문서의 근거를 계획에 결합합니다. 생성형 LLM 호출은0회이며 비용0원입니다. DI로 Store·Knowledge를 주입하고 API·MCP가 Workbench를 공유합니다.

MCP는 list_datasets,propose_experiment,get_experiment_result와 정책 resource만 제공합니다. 승인·실행 도구는 노출하지 않습니다. 실제 stdio handshake·tools/list·tools/call·resources/read를 확인했습니다. SQLite는 승인 상태·hash·감사 이력을 저장하고 단일 worker가 학습합니다. LangSmith @traceable 계측은 구현했으며 원격 업로드는 미검증입니다.

| 평가항목 | 증빙 |
|---|---|
| 기능30 | 실제 공정·이미지 학습, 승인, 성능 저하 점검, 통합·전용 모델 생성·비교 |
| 기술30 | LangGraph 역할,검색 근거,DI,MCP,모듈화,단위/API 테스트 |
| 한계20 | 공개 SECOM 실패,검사 부담,작은 불량 표본,합성·비용 가정 명시 |
| 발표20 | 쉬운 건수 비교,승인 시연,발표 대본과 코드 설명 |
| Before/After bonus10 | 같은 입력·분할의 기본/선택 절차 실측 수치 |

22개 테스트를 통과했습니다. 분할·누수·지표·승인·인증·API·SSE·CSV,가정 계산,재학습 계획 시 실행 없음,승인 후 후보 버전,validation만으로 전략 선택을 확인했습니다. [테스트 로그](evaluation/tests.txt),[MCP 실측](evaluation/mcp_check.json)

## 한계와 다음 단계

단일 seed·작은 불량 표본·반복 validation 비교의 한계가 있습니다. 기준Precision25%이상,FPR15%이하,test불량20개이상은 교육용 개발 정책이며 현장 승인 기준이 아닙니다. 실제 wafer·장비·기간·제품별 독립 검증과 비용·처리량 측정이 필요합니다.

이미지 모델은32×32·축소 구조·scratch6epoch입니다. GAN·자연어·시계열·SEM길이·공정 조건별 수율 예측은 미구현입니다. 조건별 수율 예측에는 lot별 투입/양품 수량과 시간·장비·공정 조건 이력이 필요합니다. pass/fail 확률을 제조 수율로 대체하지 않습니다.

기업용 클라우드 확장을 위한 Docker/Kubernetes 예시는 제공하지만 빌드·실배포는 미검증입니다. 현재 SQLite 단일 worker와 공유 토큰은 SSO/RBAC를 대체하지 않습니다. 실제 도입에는 개인 인증·권한,worker queue,object storage,model registry,중앙 감사·백업이 필요합니다.

교육 자료·아이디어 사진 원본은 공개 저장소에 올리지 않았습니다. 자료명·참고 페이지는 [교육 모델 근거](CURRICULUM_MODELS.md)에 남겼습니다. 공개 데이터는 [UCI SECOM](https://archive.ics.uci.edu/dataset/179/secom),원본 ZIP SHA256은eea568baf3c2229096d7d294cf0b096b5502bd96d92c0b80a65b84714059be8e입니다.

실행·재현은 [README](../README.md),시연은 [DEMO](DEMO.md),읽을 대본은 [TXT](발표대본_G045.txt),코드는 https://github.com/dragonchan95/Semiconductor-AI-Agent 입니다.
