"""Course-derived candidates. Rationale is factual metadata, never an LLM metric."""
TABULAR = {
    'logistic': ('Logistic Regression', 'scaled', '선형 결정 경계를 비교하는 기준 모델', 'Day3 PDF 68쪽 이진 확률 예시'),
    'decision_tree': ('Decision Tree', 'median', '조건 분기로 센서의 비선형 관계를 비교', 'Day1 PDF 33~55쪽'),
    'random_forest': ('Random Forest', 'median', '여러 트리의 평균으로 단일 트리의 변동을 줄이는 후보', 'Day1 PDF 59, 62~64쪽'),
    'gradient_boosting': ('Gradient Boosting', 'median', '앞선 트리의 오차를 순차 보완하는 후보', 'Day1 PDF 60~61쪽'),
    'xgboost': ('XGBoost', 'median', '규제를 적용한 트리 부스팅 후보', 'Day1 PDF 65~67, 71, 74~75쪽'),
    'lightgbm': ('LightGBM', 'median', '히스토그램 기반 트리 부스팅 후보', 'Day1 PDF 68~69, 72쪽'),
    'catboost': ('CatBoost', 'median', '교육자료의 트리 부스팅 후보. 이번 입력은 숫자 센서이므로 범주형 이점은 검증하지 않음', 'Day1 PDF 70, 73쪽'),
    'knn': ('KNN', 'scaled', '가까운 센서 패턴의 라벨로 비교', 'Day2 PDF 21~31쪽'),
    'svm': ('SVM (RBF)', 'scaled', '커널로 비선형 경계를 비교', 'Day2 PDF 32~42쪽'),
    'mlp': ('MLP / ANN', 'scaled', '다층 신경망으로 센서 간 비선형 관계를 비교', 'Day3 PDF 7~22쪽'),
    'adaboost': ('AdaBoost', 'median', '틀린 표본에 더 집중하는 부스팅 후보', '반도체 발표 PDF 40~42쪽'),
    'hist_gradient': ('Hist Gradient Boosting', 'median', '히스토그램 기반 부스팅의 추가 비교 후보', '반도체 발표 PDF 40쪽'),
}
EXTERNAL = {
    'extra_trees': ('ExtraTrees', 'median', '무작위 분할을 사용하는 여러 트리의 평균으로 센서의 비선형 관계를 비교합니다. 기존 Random Forest와 다른 분할 방식을 실험할 후보입니다.', 'https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.ExtraTreesClassifier.html', 'ExtraTreesClassifier'),
    'gaussian_nb': ('Gaussian Naive Bayes', 'scaled', '특성의 조건부 독립과 클래스별 정규분포를 가정하는 단순한 확률 분류 후보입니다. 센서 상관과 분포 가정이 맞지 않으면 성능이 낮을 수 있습니다.', 'https://scikit-learn.org/stable/modules/generated/sklearn.naive_bayes.GaussianNB.html', 'GaussianNB'),
}

IMAGE = {
    'resnet_small': ('ResNet 계열 축소', '잔차 연결을 적용한 교육용 CNN', 'Day3 PDF 74쪽 / 반도체 커리큘럼 사진 20261017_135247'),
    'vgg_small': ('VGGNet 계열 축소', '작은 합성곱을 쌓은 교육용 CNN', 'Day3 PDF 74쪽 / 같은 커리큘럼 사진'),
    'autoencoder': ('Autoencoder', '정상 이미지를 복원하고 복원 오차로 이상을 점수화', '반도체 커리큘럼 사진 20261017_135247, 135711'),
}


def pipeline_reason(model, prep='auto', balance='none'):
    if model in IMAGE:
        title, why, source = IMAGE[model]
        return {'model': model, 'title': title, 'input': '라벨이 있는 검사 이미지',
                'preprocessing': prep, 'preprocessing_reason': '흑백 32×32 및 0~1 정규화로 CPU 데모 연산량을 제한. contrast는 대비 보정 비교이며 작은 결함 정보 손실 가능',
                'model_reason': why, 'balance_method': '정상만 학습' if model == 'autoencoder' else '가중 손실' if balance == 'weighted' else '기본 손실',
                'source': source, 'limitation': '축소 구조를 scratch 학습. 표준 ResNet50/VGG19 사전학습 성능의 증거가 아님'}
    title, default, why, source = (TABULAR[model] if model in TABULAR else EXTERNAL[model][:4])
    prep = default if prep == 'auto' else prep
    reason = '센서 단위 차이가 거리·마진·가중치 학습에 영향을 주므로 학습 표본 기준 Scaling(StandardScaler)' if prep == 'scaled' else '트리 모델은 단위 차이의 영향이 작아 기본 설정에서 Scaling 없이 사용'
    if model == 'gaussian_nb':
        reason = '학습 구간의 평균·분산으로 수치 범위를 맞춰 비교. 클래스별 분포·특성 독립 가정의 적합성은 별도 확인'
    if model in {'knn', 'mlp'} and balance == 'weighted':
        method = '학습 표본 안에서만 불량 무작위 복제 (오버샘플링)'
    elif balance == 'weighted':
        method = '학습 클래스 빈도의 역수에 비례한 가중치'
    else:
        method = '원래 학습 클래스 비율 유지'
    return {'model': model, 'title': title, 'input': '숫자 센서와 정상/불량 라벨',
            'preprocessing': prep, 'preprocessing_reason': '결측은 학습 중앙값으로 대체하고 상수 특성을 제거. '+reason,
            'model_reason': why, 'balance_method': method, 'source': source,
            'limitation': '동일 분할의 validation 비교 결과로 선택. 다른 제품·공정에서의 우위를 보장하지 않음'}


def explain_plan(audit, plan):
    image = audit['modality'] == 'image'
    return {
        'data_summary': f"{'검사 이미지' if image else '숫자 공정 센서'} {audit['rows']:,}개, 불량 {audit['defects']:,}개 ({audit['defect_ratio']:.1%}), 결측 {audit['missing_ratio']:.1%}",
        'task': '정상/불량 이진 분류. 수율 회귀 또는 시간 예측 과제가 아님',
        'preprocessing_evidence': '이미지 크기·대비 후보를 비교합니다.' if image else f"숫자 특성 {audit['features']}개. 결측 대체·상수 제거·Scaling의 적합은 train에만 수행합니다.",
        'imbalance_reason': f"불량 {audit['defect_ratio']:.1%}. Recall, 정상 오판률(정상을 불량으로 판정), Precision을 함께 비교합니다. 복제·가중치는 train에만 적용합니다.",
        'candidates': [pipeline_reason(n, plan['preprocessing'][0], plan['balance'][-1]) for n in plan['models']],
        'excluded': [
            {'models': 'LSTM / ARIMA', 'reason': '연속 관측 주기와 예측 시점·목표가 있는 시계열 입력이 필요. 현재 행 단위 불량 분류와 직접 경쟁시키지 않음'},
            {'models': 'BERT / GPT', 'reason': '장비 로그 텍스트 및 분류 라벨이 필요. 현재 센서 CSV·이미지의 검사 모델로 학습하지 않음'},
            {'models': 'GAN', 'reason': '결함 생성의 진위·품질 평가와 별도 검증이 필요. 합성 불량 생성 학습은 이번 PoC 범위 밖'},
        ],
    }
