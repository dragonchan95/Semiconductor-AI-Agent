# 반도체 불량 판정 모델 선택·재학습 Agent

G045 김용찬 · SK AI Leader Academy · 과제 2

**어떤 모델로 불량을 판정하고, 성능이 떨어지면 언제 다시 학습할까요?**

데이터를 점검해 전처리·모델·제품 학습 범위를 제안하고, 엔지니어 승인 후 실제 학습합니다. Recall을 우선 확인하고 Precision·F1과 정상 오판도 함께 설명합니다. 새 데이터에서는 같은 제품에 기존 모델과 판정값을 고정해 점검하고, 승인받아 같은 알고리즘을 재학습합니다.

[최종 제출 Google Slides](https://docs.google.com/presentation/d/1J2m_cpXyvb-5_Xabs2DsD3EnEV6B6GicF5OP2s5FohU/edit) · [발표 대본](docs/발표대본_G045.txt) · [상세 보고서](docs/REPORT.md) · [교육자료 근거](docs/CURRICULUM_MODELS.md) · [과제 요구사항 대응표](docs/ASSIGNMENT_CHECKLIST.md)

![실제 비교 화면](docs/assets/easy-result.png)

## 실행

macOS에서는 **start.command를 더블클릭**하거나 터미널에서 실행합니다.

```bash
bash start.sh
```

http://localhost:8700 에 접속합니다. 재부팅 뒤에는 서버도 다시 켜야 합니다. 실행 터미널을 닫으면 서버가 종료됩니다. Python3.11 이상, 최초 의존성 설치가 필요합니다. macOS XGBoost·LightGBM에는 OpenMP가 필요합니다. `brew install libomp`로 설치할 수 있습니다.

예제 데이터 → 완료된 결과 확인 → 새 비교 계획 → 승인 → 새 데이터 점검 순으로 사용합니다. 새 설치에는 완료 이력이 없어 먼저 계획을 승인해 학습해야 합니다. [시연 순서](docs/DEMO.md)

## 데이터와 모델

센서12종: Logistic Regression, Decision Tree, Random Forest, Gradient Boosting, XGBoost, LightGBM, CatBoost, KNN, SVM, MLP, AdaBoost, Hist Gradient Boosting. 먼저 전체 제품의12종×불균형2조건, 이후 상위 두 알고리즘의 제품 조합을 확장해 최대52조건을 비교합니다. 완전탐색이 아닙니다.

이미지: 자체 축소 ResNet·VGGNet·Autoencoder. 표준 사전학습 대형 모델의 성능 비교는 아닙니다. 입력 종류가 다른 NLP·시계열 모델은 별도 과제로 구분합니다.

제품 A·B·C·D는 **합성 데이터의 가상 제품명**입니다. 실제 공개 데이터인 **SECOM은 반도체 제조 센서·합격/불합격 기록**으로1,567건·센서590열·불량104건입니다. 실제 제품 A–D 정보가 없고 특정 회사의 현재 생산 데이터도 아닙니다. [UCI 공식 자료·CC BY4.0](https://archive.ics.uci.edu/dataset/179/secom)

## 같은 Test에서 확인한 결과

| 데이터 | Test 불량 발견 | 정상 오판 | Recall | Precision | F1 |
|---|---:|---:|---:|---:|---:|
| 합성 센서 | 19/25 | 8/167 | 76.0% | 70.4% | 73.1% |
| 공개 반도체 센서 SECOM | 6/15 | 73/249 | 40.0% | 7.6% | 12.8% |
| 합성 이미지 | 6/14 | 0/76 | 42.9% | 100.0% | 60.0% |

합성 센서의 기본 Logistic은 불량25개 중17개, 후보 CatBoost(A+B+C 학습)는19개를 발견했습니다. 정상167개 중 오판은1개→8개입니다. 후보의 Recall76%가 데모 목표90%에 못 미쳐 재검토합니다. Validation에서 골랐다는 뜻이며 회사 적용 승인이 아닙니다.

새 합성 배치의 동일 Test에서 기존 CatBoost와 같은 알고리즘 재학습을 비교하면 불량127개 중24개→117개를 발견했습니다. 정상449개 중 오판은70개→68개입니다. 재학습 Recall92.1%, 정상 오판15.1%로 데모 목표 중 정상 오판 목표를 넘습니다. 같은 제품별로 합쳐 학습/따로 학습한 방법도 비교하고 후보 파일·버전을 저장합니다. 운영 모델은 자동 교체하지 않습니다.

## 회사 기준과 데모 목표

**90% Recall·15% 정상 오판·Test 불량20개는 교육용 기본값이며 회사 양산 기준이 아닙니다.** 공개 회사 자료에서 모든 제품에 통용되는 수치 기준은 확인하지 못했습니다. 실제 도입에는 제품·공정·결함별 품질 요구와 담당자가 정한 독립 검증 기준이 필요합니다. [SK하이닉스 검사 AI 성능 감시·학습 사례](https://news.skhynix.com/en/the-past-present-and-future-of-data-science-organization-at-sk-hynix/)

정상 오판은 FP, 놓친 불량은 FN입니다. Recall=TP/(TP+FN), Precision=TP/(TP+FP), F1=2TP/(2TP+FP+FN), 정상 오판률=FP/(FP+TN). 정상 오판이 실제 재검사나 폐기를 뜻하지 않습니다. 제조 수율 향상은 측정하지 않았습니다.

## Agent와 검증

LangGraph의 데이터 점검·실험 계획·결과 검토 역할, 로컬 Qwen,14개 근거 요약문 검색 RAG, Store·Knowledge·Advisor 의존성 주입, API/MCP 공통 Workbench를 구현했습니다. MCP4도구를 실제 stdio로 확인했고26개 테스트를 통과했습니다. LLM은 허용된 코드·출처 연결을 검사하며 실패하면 규칙 설명을 사용합니다. 실제 통합 검증에서 품질·계획 역할은 통과, 결과 검토는 fallback이었습니다.

bash start.sh의 기본 실행은 규칙·TF-IDF 모드입니다. macOS start.command는 설치된 Ollama가 있으면 서버를 켜고 로컬 LLM을 연결합니다. Ollama에 qwen3.5:2b와 qwen3-embedding:0.6b가 있으면 Ollama를 켠 뒤 `SEMI_LLM_ENABLED=1 bash start.sh`로 로컬 LLM·임베딩을 사용합니다. 현재 모드는 화면의 Agent 세부 실행 상태와 /health에 표시합니다. 검색 고정13질문의 Hit@3는 TF-IDF/dense 모두100%, MRR@3 모두0.9615로 이번 작은 평가에서는 검색 품질 개선을 확인하지 못했습니다.

로컬 LLM·검색의 [실제 실행 기록](docs/evaluation/agent_integration.json)을 제공합니다.

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/check_mcp.py
.venv/bin/python scripts/evaluate.py
.venv/bin/python scripts/evaluate_management.py
.venv/bin/python scripts/build_report.py
```

승인자는 재현용 자동 테스트 actor이며 현장 승인 실적이 아닙니다. 계획·데이터·분할 hash와 seed를 저장합니다. 학습/Validation/Test를 분리하고 전처리·가중치는 학습에서만 fit합니다. 후보와 판정값을 같은 Validation에서 반복 비교하므로 선택 편향이 있고 독립 기간 검증이 필요합니다. 이미지와 SECOM의 불량 표본도 작습니다. requirements.lock.txt는 검증 환경입니다.

## 기업 클라우드 확장과 범위

Docker/Kubernetes 예시는 기업 클라우드 확장용이며 실배포 미검증입니다. production은 ENGINEER_TOKEN 필수이며 개인 SSO/RBAC·학습 queue·중앙 저장소·모델 registry가 추가로 필요합니다. 외부 모델 자동 검색·목록 갱신은 [확장 설계](docs/MODEL_DISCOVERY_DESIGN.md)입니다. 공정 조건별 수율 예측·SEM 길이·NLP·시계열 예측은 실행 기능이 아닙니다.

CSV는 label(정상0/불량1),product,lot_id 또는 timestamp와 숫자 센서 열, 이미지 ZIP은 manifest.csv와 상대 image_path가 필요합니다. 업로드30MB,압축 해제128MB,실험72조건,제품4종,20,000행 한도입니다. 교육 원본·사진·제출 명단 엑셀·비밀은 공개 저장소에 넣지 않습니다.
