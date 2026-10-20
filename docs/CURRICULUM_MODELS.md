# 교육 자료와 모델 선택 근거

SKALA 머신러닝 및 딥러닝 이해 Day1 76쪽, Day2 74쪽, Day3 76쪽을 OCR로 검색하고 모델 소개 페이지를 직접 확인했습니다. 두 참고 사진 폴더 693장을 검색하고 주요 모델 표를 확인했습니다. 원본 교육자료는 재배포하지 않습니다. 페이지는 PDF 기준입니다.

| 입력 | 실제 후보 | 전처리 | 자료 위치 | 비교 이유 |
|---|---|---|---|---|
| 숫자 센서 | Logistic Regression | scaled | Day3 PDF 68쪽 이진 확률 예시 | 선형 결정 경계를 비교하는 기준 모델 |
| 숫자 센서 | Decision Tree | median | Day1 PDF 33~55쪽 | 조건 분기로 센서의 비선형 관계를 비교 |
| 숫자 센서 | Random Forest | median | Day1 PDF 59, 62~64쪽 | 여러 트리의 평균으로 단일 트리의 변동을 줄이는 후보 |
| 숫자 센서 | Gradient Boosting | median | Day1 PDF 60~61쪽 | 앞선 트리의 오차를 순차 보완하는 후보 |
| 숫자 센서 | XGBoost | median | Day1 PDF 65~67, 71, 74~75쪽 | 규제를 적용한 트리 부스팅 후보 |
| 숫자 센서 | LightGBM | median | Day1 PDF 68~69, 72쪽 | 히스토그램 기반 트리 부스팅 후보 |
| 숫자 센서 | CatBoost | median | Day1 PDF 70, 73쪽 | 교육자료의 트리 부스팅 후보. 이번 입력은 숫자 센서이므로 범주형 이점은 검증하지 않음 |
| 숫자 센서 | KNN | scaled | Day2 PDF 21~31쪽 | 가까운 센서 패턴의 라벨로 비교 |
| 숫자 센서 | SVM (RBF) | scaled | Day2 PDF 32~42쪽 | 커널로 비선형 경계를 비교 |
| 숫자 센서 | MLP / ANN | scaled | Day3 PDF 7~22쪽 | 다층 신경망으로 센서 간 비선형 관계를 비교 |
| 숫자 센서 | AdaBoost | median | 반도체 발표 PDF 40~42쪽 | 틀린 표본에 더 집중하는 부스팅 후보 |
| 숫자 센서 | Hist Gradient Boosting | median | 반도체 발표 PDF 40쪽 | 히스토그램 기반 부스팅의 추가 비교 후보 |
| 검사 이미지 | ResNet 계열 축소 | gray / contrast, 32×32 | Day3 PDF 74쪽 / 반도체 커리큘럼 사진 20261017_135247 | 잔차 연결을 적용한 교육용 CNN |
| 검사 이미지 | VGGNet 계열 축소 | gray / contrast, 32×32 | Day3 PDF 74쪽 / 같은 커리큘럼 사진 | 작은 합성곱을 쌓은 교육용 CNN |
| 검사 이미지 | Autoencoder | gray / contrast, 32×32 | 반도체 커리큘럼 사진 20261017_135247, 135711 | 정상 이미지를 복원하고 복원 오차로 이상을 점수화 |

자료명: `2) 데이터분석 및 AIOps_4.머신러닝 및 딥러닝 이해_Day1,2,3_박병선p.pdf` 각각의 파일, `DRAM, NAND 특성, 반도체 업에서 활용되는 AI, ML 기술 발표자료 (2).pdf`.

`반도체 ai agent 참고 사진/20261017_144839.jpg`에는 NN·KNN·SVM·Tree 기반 고장 분류가 나옵니다. `참고 사진 2/20261017_135247.jpg`에는 이미지 ResNet·VGGNet·GAN·Autoencoder, 자연어 LSTM·GPT·BERT, 시계열 LSTM·ARIMA·Autoencoder가 나옵니다. 원 자료의 회귀·수명 예측 사례와 이번 불량 이진 분류를 구분합니다. 이 구현의 평가는 Recall·Precision·FPR·AP입니다.

기본 전처리는 학습 중앙값 결측 대체와 상수 특성 제거입니다. Logistic·KNN·SVM·MLP는 학습 평균·분산으로 표준화합니다. 트리는 크기 비교 분기이므로 기본적으로 표준화를 생략합니다. KNN·MLP의 weighted 정책은 train 안에서 소수 클래스 무작위 복제이며 나머지는 빈도 역수 가중치입니다. 평가 분포는 바꾸지 않습니다.

센서 비교는 먼저 전체 제품에서 12종×불균형 2정책을 비교하고 validation 상위 서로 다른 두 모델의 최선 조건을 제품 15조합으로 확장합니다. 최대52조건이며 전 모델×전 제품×전 처리의 완전탐색은 아닙니다. 반복 validation 사용의 선택 편향과 작은 표본을 한계로 명시합니다. 각 실험은 실제 모델명·학습 데이터·적용 전처리·이유·출처를 저장합니다.

이미지 모델은 자체 축소 구조를 scratch 학습합니다. 표준 ResNet50/VGG19 사전학습 비교가 아닙니다. GAN 생성 학습, LSTM·ARIMA 시계열 예측, BERT·GPT 장비 로그 모델 학습은 입력과 별도 평가 설계가 없어 미구현입니다. 로컬 Qwen은 Agent 판단용이며 장비 로그 분류 모델의 성능 실험이 아닙니다.

공식 구현 근거: [scikit-learn 전처리](https://scikit-learn.org/stable/modules/preprocessing.html), [트리](https://scikit-learn.org/stable/modules/tree.html), [신경망](https://scikit-learn.org/stable/modules/neural_networks_supervised.html), [XGBoost](https://xgboost.readthedocs.io/en/stable/), [LightGBM](https://lightgbm.readthedocs.io/en/stable/), [CatBoost](https://catboost.ai/docs/).
