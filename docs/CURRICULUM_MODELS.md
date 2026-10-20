# 교육 자료와 모델 선택 근거

| 입력·목적 | 실제 후보 | 제공 자료의 위치 | 이번 구현의 적용 |
|---|---|---|---|
| 공정 센서 | Random Forest | 스칼라 `생성형AI 기반 모델개발 실습.pptx.pdf` PDF4쪽(인쇄3쪽), 반도체 발표자료 PDF41~42쪽 | 같은 모델 계열의 분류기로 정상/불량 학습 |
| 공정 센서 | Hist Gradient Boosting | 반도체 발표자료 PDF40쪽의 Hist Gradient Boost | 원자료의 연속 Response 회귀 소개를 이 과제에서는 정상/불량 분류로 적용 |
| 비교 기준 | Logistic Regression | 스칼라 머신러닝 및 딥러닝 Day3 PDF68쪽의 이진 확률 예시 | 사전 정의한 기준 모델과 선형 후보 |
| 검사 이미지 | ResNet·VGGNet 계열 | 스칼라 머신러닝 및 딥러닝 Day3 PDF74쪽 | residual block 및 VGG형 convolution의 자체 축소 구조를 scratch 학습 |
| 검사 이미지 | Autoencoder | 사용자가 제공한 반도체 이미지 이상탐지 아이디어 | 정상 이미지로 학습하는 교육용 이상 탐지 구현. 위 Day3 PDF의 특정 페이지에서 소개했음을 확인한 것은 아님 |

반도체 자료: `DRAM, NAND 특성, 반도체 업에서 활용되는 AI, ML 기술 발표자료 (2).pdf`.

원자료에는 회귀 성능 MSE/R²가 등장하지만 이 프로젝트 목표는 불량 이진 분류입니다. Recall·Precision·FPR·AP로 평가합니다. Random Forest가 항상 최고라고 가정하지 않고 동일 평가에서 비교합니다.

이미지 구현은 표준 ResNet18/VGG16 사전학습 모델이 아닙니다. 화면에 교육용 축소를 표시하고 원본 코드명 ResNetSmall/VGGSmall은 코드·상세 결과에 유지합니다. XGBoost·LightGBM·GAN·LSTM·ARIMA·BERT·GPT 전체 실험은 구현하지 않았습니다. 텍스트·시계열·공정 조건별 수율 예측은 실제 데이터 확보 후 확장합니다.

교육 PDF와 사진 원본은 공개 저장소에 재배포하지 않습니다.

구현 API: [RandomForestClassifier](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html), [HistGradientBoostingClassifier](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html).
