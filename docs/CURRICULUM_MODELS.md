# 교육자료와 실제 모델

Agent의 설명용 언어 모델은 **5주차 실습의 Qwen2.5-1.5B-Instruct 계열**입니다. 현재 Windows는 같은 계열의 Q4_K_M 양자화 기본 모델을 Ollama로 실행합니다. 센서의 정상·불량을 분류하는 아래 후보 모델들과 역할이 다릅니다. 실습의 인사규정용 LoRA 가중치는 이번 반도체 Agent에 적용하지 않습니다.

RAG는 같은5주차의 `knowledge_asset_demo_faiss_bge_m3.ipynb`를 참고해 **BGE-M3 임베딩·정규화·FAISS IndexFlatIP·Qwen 문맥 주입**을 구현했습니다. 현재 Windows는 BGE-M3를 로컬 Ollama로 실행하며 수업의 SentenceTransformer 호출과 실행 도구가 다릅니다. [구현과 검증 범위](RAG.md)

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

## 입력 종류와 현재 실행 범위

| 입력 종류 | 후보 예 | 현재 범위 |
|---|---|---|
| 센서 표 | Tree·Forest·Boosting, KNN·SVM·MLP 등12종 | 실제 학습·Validation 비교·제품 그룹·앙상블·승인 재학습 |
| 검사 이미지 | 축소 ResNet·VGGNet·Autoencoder | 합성 이미지로 실제 학습 비교 |
| 이미지 추가 후보 | EfficientNet·GAN | 미구현·미실행 |
| 연속 시계열 | LSTM·ARIMA·Autoencoder | 전용 연속 입력·예측 목표·학습 연결 미준비 |
| 장비 로그 텍스트 | LSTM·BERT·GPT | 로그·정답·학습 연결 미준비 |

입력 종류에 따라 후보와 전처리를 정하고, 엔지니어 승인 후 비교하는 흐름입니다. 현재 센서와 이미지만 실제 실행을 지원합니다. Autoencoder의 현재 구현은 이미지 복원 오차이며 시계열 모델은 별도 구현이 필요합니다. LSTM은 시계열과 텍스트 양쪽에 적용할 수 있습니다. 설명용 Qwen 실행을 로그 BERT/GPT 분류의 실행 증거로 사용하지 않습니다.

이미지는 같은 Validation114건(불량19·정상95)에서 gray/contrast2조건 중 각 모델의 최선 결과를 비교했습니다. 세 모델 모두 contrast에서 Recall100%·F1 1.000·정상 오판0%였습니다. 단순 합성 패턴이며 센서 모델과 하나의 순위로 합치지 않습니다. 선택 Autoencoder는 Test에서14/15개를 검출했고 정상 오판은0/105개였지만 불량20개 최소 기준에 미달해 적용 판단을 보류했습니다. 32×32 교육용 축소 구조와6epochs이며 사전학습 원형 ResNet/VGG 전체를 재현한 실험이 아닙니다.

[실행 범위·데이터 출처 요약](evaluation/model_scope.json), [이미지 원본](evaluation/images.json). EfficientNet은 사용자 요청을 반영한 추가 후보이며 이번에 학습하지 않았습니다. [공식 EfficientNet 소개](https://pytorch.org/hub/nvidia_deeplearningexamples_efficientnet/), [LSTM 공식 문서](https://docs.pytorch.org/docs/stable/generated/torch.nn.modules.rnn.LSTM.html), [BERT 공식 문서](https://huggingface.co/docs/transformers/model_doc/bert). 교육 사진의 원본 화면·인물은 재배포하지 않고 모델명을 표로 재구성했습니다.
