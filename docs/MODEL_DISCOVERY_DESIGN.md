# 새 모델 탐색 RAG와 후보 목록 갱신

현재 실제 동작: 공식 scikit-learn API 목록 조회, 기존 교육12종 밖의 ExtraTrees·GaussianNB 공식 본문 수집, 문서 chunk 검색(TF-IDF·cosine), 근거 연결 제안, 엔지니어 승인 후 기존 후보와 새 모델 학습·Validation 비교, 같은 Test 확인, 외부 후보 목록과 실험 이력 저장.

숙련 엔지니어가 아직 검토하지 않은 후보를 찾는 것이 주된 목적입니다. 기존 전처리·모델 설명은 그 제안을 검토하는 보조 정보로 남깁니다. 검색은 자료를 모으고 RAG는 수집한 본문에서 데이터 적합성 근거를 찾습니다. 로컬 LLM은 허용 모델 코드와 인용 근거를 검사하며 실패하면 근거 템플릿으로 설명합니다. RAG 추천은 성능 증거가 아니며 실제 학습으로 비교합니다.

## 실제 범위

공식 API 색인에서 모델 링크를 발견하고 두 개의 검토된 로컬 adapter에 연결합니다. 새 후보라는 말은 기존 교육 후보 목록에 없던 모델이라는 뜻이며 최신 연구 모델이라는 주장은 아닙니다. 새 이름의 adapter 코드를 자동 작성하거나 웹 설치 명령을 실행하지 않습니다. 임의 사이트 검색·이미지/NLP/시계열 새 모델 연결은 추가 구현이 필요합니다. 공식 문서 조회 실패 시 가짜 결과로 대체하지 않습니다.

원본 센서 행·제품명·사용자 질문을 공식 문서 서버에 보내지 않습니다. 외부 통신은 고정된 공식 HTTPS 경로 GET만 사용합니다. 문서 조회 시각·주소·hash·검색 근거와 승인 계획을 기록합니다. 운영 모델은 자동 교체하지 않습니다.

## 비교 방식과 실측

학습/Validation/Test 목표6:2:2와 같은 생산 묶음(lot) 경계를 보존합니다. 기준 실험에서 고른 제품 학습 범위를 그대로 사용하고 기존 알고리즘과 새 모델을 같은 조건에서 다시 학습합니다. Validation에서 후보·판정 경계값을 비교하며 F1·Precision도 보조로 확인합니다. 기존에 본 Test를 재사용한 탐색 비교이므로 독립적인 최종 검증을 새로 했다는 주장을 하지 않습니다. 현장 적용에는 별도 기간·제품 검증이 필요합니다.

실행 기록: [model_discovery.json](evaluation/model_discovery.json). 합성 센서 A+B+C 학습에서 ExtraTrees·GaussianNB를 비교했고 CatBoost가 유지됐습니다. 새 모델의 Validation 결과와 후보 상태를 목록에 저장합니다. 새로운 모델이 항상 우수하다는 가정은 두지 않습니다.

## 모델 간 앙상블 비율

RF·부스팅 자체를 사용하는 것에 더해, 서로 다른 모델의 예측 확률을 섞는 비율 탐색도 구현했습니다. 승인한 구성 모델과 비율을 Validation에서 비교하고 선택 후 같은 Test를 확인합니다. 정상 오판 한도 안에서 Recall 우선·동률 F1으로 고르며, 현재 예제는CatBoost90%와LightGBM10%입니다. [앙상블 방법·실측·한계](ENSEMBLE.md)를 참고합니다.

근거: [ExtraTrees 공식 문서](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.ExtraTreesClassifier.html), [GaussianNB 공식 문서](https://scikit-learn.org/stable/modules/generated/sklearn.naive_bayes.GaussianNB.html), [교차검증](https://scikit-learn.org/stable/modules/cross_validation.html).
