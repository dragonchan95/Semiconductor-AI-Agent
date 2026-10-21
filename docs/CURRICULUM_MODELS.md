# 교육자료와 실제 모델

모델 명칭·위치를 확인한 교육자료의 요약이며 원본 PDF·사진은 재배포하지 않습니다. PDF 기준 쪽입니다.

| 실제 센서 후보 | 기본 전처리 | 사용 이유 | 자료 위치 |
|---|---|---|---|
| Logistic Regression | 결측 대체·상수 제거·Scaling | 선형 결정 경계를 비교하는 기준 모델 | Day3 PDF 68쪽 이진 확률 예시 |
| Decision Tree | 결측 대체·상수 제거 | 조건 분기로 센서의 비선형 관계를 비교 | Day1 PDF 33~55쪽 |
| Random Forest | 결측 대체·상수 제거 | 여러 트리의 평균으로 단일 트리의 변동을 줄이는 후보 | Day1 PDF 59, 62~64쪽 |
| Gradient Boosting | 결측 대체·상수 제거 | 앞선 트리의 오차를 순차 보완하는 후보 | Day1 PDF 60~61쪽 |
| XGBoost | 결측 대체·상수 제거 | 규제를 적용한 트리 부스팅 후보 | Day1 PDF 65~67, 71, 74~75쪽 |
| LightGBM | 결측 대체·상수 제거 | 히스토그램 기반 트리 부스팅 후보 | Day1 PDF 68~69, 72쪽 |
| CatBoost | 결측 대체·상수 제거 | 교육자료의 트리 부스팅 후보. 이번 입력은 숫자 센서이므로 범주형 이점은 검증하지 않음 | Day1 PDF 70, 73쪽 |
| KNN | 결측 대체·상수 제거·Scaling | 가까운 센서 패턴의 라벨로 비교 | Day2 PDF 21~31쪽 |
| SVM (RBF) | 결측 대체·상수 제거·Scaling | 커널로 비선형 경계를 비교 | Day2 PDF 32~42쪽 |
| MLP / ANN | 결측 대체·상수 제거·Scaling | 다층 신경망으로 센서 간 비선형 관계를 비교 | Day3 PDF 7~22쪽 |
| AdaBoostClassifier | 결측 대체·상수 제거 | 교육자료의 회귀 사례와 같은 계열을 정상·불량 분류에 적용 | 반도체 발표 PDF 40~42쪽의 Adaboost Regression / Ada Boost |
| Hist Gradient Boosting | 결측 대체·상수 제거 | 히스토그램 기반 부스팅의 추가 비교 후보 | 반도체 발표 PDF 40쪽 |

자료명: 9주차 `2) 데이터분석 및 AIOps_4.머신러닝 및 딥러닝 이해_Day1,2,3_박병선p.pdf` 각 파일. 반도체 `DRAM, NAND 특성, 반도체 업에서 활용되는 AI, ML 기술 발표자료 (2).pdf` 40~42쪽. 참고 사진 `20261017_144839.jpg`의 NN·KNN·SVM·Tree 고장 분류.

2026-10-21 원본 페이지 재확인: 40쪽은 `Adaboost Regression`, 41~42쪽은 `ADA Boost / Ada Boost`가 MSE·R² 비교표에 등장합니다. 자료는 회귀 예제이고 이 프로젝트는 이진 분류용 `AdaBoostClassifier`로 적용했습니다. 교육자료의 과제·구조·수치를 그대로 재현한 것은 아닙니다. Hist Gradient Boosting도 40쪽의 회귀 비교를 참고해 분류용으로 적용했습니다. 새 모델 탐색 RAG가 추가한 후보는 이 두 모델이 아닌 ExtraTrees·GaussianNB입니다.

검사 이미지: 자체 축소 ResNet·VGGNet·Autoencoder를 실제 학습합니다. 참고 사진2의 `20261017_135247.jpg`와 Day3 PDF74쪽. GAN 생성 학습·BERT/GPT 로그 분류·LSTM/ARIMA 시계열 예측은 미구현입니다.

지표: 12주차 `데이터분석 및 AIOps_7.데이터분석 Mini Project_박병선p.pdf` 15쪽에 Accuracy·Precision·Recall·F1 Score가 함께 제시됩니다. 이 프로젝트는 불량을 Positive로 정의해 Recall을 우선 비교하고 Precision·F1·정상 오판률도 보고합니다. F1은 2TP/(2TP+FP+FN)입니다.

Scaling은 전처리의 넓은 표현이며 이번 StandardScaler는 학습 평균·분산으로 단위를 맞추는 방식입니다. 학습 표본에서만 fit하고 Validation/Test에는 같은 변환만 적용합니다. 불량 가중치·복제도 학습 구간 안에서만 적용합니다.
