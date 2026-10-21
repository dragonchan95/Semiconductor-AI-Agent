import json
from pathlib import Path
root = Path(__file__).resolve().parent.parent
p = root/'data/knowledge.json'
docs = json.loads(p.read_text(encoding='utf-8'))
more = [
 ('tree', '트리 계열과 Scaling', 'Decision Tree, Random Forest, Gradient Boosting, XGBoost, LightGBM, CatBoost는 숫자 특성의 순서에 따른 분기를 학습한다. 트리에는 단위 Scaling가 필수는 아니다. 이번 비교에서는 일관된 결측 처리를 위해 학습 중앙값으로 대체한다. SKALA Day1 PDF 51, 62~73쪽 확인.', 'scikit-learn Decision Trees', 'https://scikit-learn.org/stable/modules/tree.html'),
 ('distance', 'KNN·SVM과 센서 단위', 'KNN의 거리와 RBF SVM의 커널은 특성 스케일에 영향을 받는다. 학습 중앙값으로 결측을 대체한 뒤 학습 평균·분산으로 Scaling하고 같은 변환을 평가 표본에 적용한다. SKALA Day2 PDF 21~42쪽의 모델을 실제 분류기로 비교한다.', 'scikit-learn Preprocessing', 'https://scikit-learn.org/stable/modules/preprocessing.html'),
 ('ann', 'MLP 신경망과 데이터 부족', '다층 퍼셉트론 MLP는 숫자 센서의 비선형 관계를 학습한다. Scaling와 규제, 고정된 학습 반복 예산을 사용한다. 불량 복제는 train에만 적용하고 validation/test 라벨 분포는 바꾸지 않는다. SKALA Day3 PDF 7~22쪽 신경망 교육에서 후보를 선정했다.', 'scikit-learn Neural networks', 'https://scikit-learn.org/stable/modules/neural_networks_supervised.html'),
 ('modalities', '이미지·로그·시계열 입력의 구분', '반도체 교육 사진 20261017_135247은 이미지 ResNet/VGGNet/GAN/Autoencoder, 자연어 LSTM/GPT/BERT, 시계열 LSTM/ARIMA/Autoencoder를 소개한다. 이번 PoC는 센서 표의 이진 분류와 이미지 분류·이상 탐지만 실제 학습한다. 로그 텍스트와 시계열 예측 표적이 없을 때 해당 모델을 실행했다고 주장하지 않는다.', '제공 반도체 교육 사진의 모델 소개를 요약한 프로젝트 범위', None),
 ('retraining', '재학습과 제품 전용 후보', '새로운 라벨 배치에서 기존 모델의 Recall 저하와 FPR 증가를 점검한다. 변화 탐지는 재학습 제안 근거이며 원인 진단은 아니다. 엔지니어 승인 후 통합 모델과 제품별 모델을 같은 제품의 validation에서 비교하고 최종 test 기준으로 권고 또는 보류한다. 운영 배포는 자동 수행하지 않는다.', '프로젝트 모델 관리 정책', None),
]
known = {d['id'] for d in docs}
for id, title, text, source, url in more:
    if id not in known:
        docs.append(dict(id=id, title=title, text=text, source=source, url=url))
p.write_text(json.dumps(docs, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
