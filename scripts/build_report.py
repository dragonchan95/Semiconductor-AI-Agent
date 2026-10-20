"""Build report and README from actual curriculum-aligned measured receipts."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
pct=lambda x:f'{100*x:.1f}%'
num=lambda x:f'{x:,.1f}'
NAMES={'logistic':'Logistic Regression','random_forest':'Random Forest','hist_gradient':'Hist Gradient Boosting',
       'resnet_small':'ResNet 계열(교육용 축소)','vgg_small':'VGGNet 계열(교육용 축소)','autoencoder':'Autoencoder'}

def main():
    saved={n:json.loads((ROOT/f'docs/evaluation/{n}.json').read_text()) for n in ['synthetic_process','secom','images']}
    results={n:d['result'] for n,d in saved.items()}
    mg=json.loads((ROOT/'docs/evaluation/model_management.json').read_text())
    impact=json.loads((ROOT/'docs/evaluation/presentation_cases.json').read_text())['synthetic_process']
    a,b,delta=impact['after'],impact['before'],impact['delta']
    labels={'synthetic_process':'합성 공정','secom':'공개 SECOM','images':'합성 이미지'}
    rows=['| 데이터 | 후보 수 | Before Recall | After Recall | After Precision | After FPR | 판단 |','|---|---:|---:|---:|---:|---:|---|']
    for n,r in results.items():rows.append(f"| {labels[n]} | {len(r['trials'])} | {pct(r['baseline_test']['recall'])} | {pct(r['test']['recall'])} | {pct(r['test']['precision'])} | {pct(r['test']['fpr'])} | {'합성 내 검토 가능' if r['gate']['passed'] else '보류'} |")
    main_table='\n'.join(rows)
    cr=['| 제품 | 공통 Recall / FPR | 전용 Recall / FPR | 선택 방식 | 최종 판단 |','|---|---:|---:|---|---|']
    for r in mg['comparison']['products']:
        x,y=[c['validation'] for c in r['candidates']]
        cr.append(f"| {r['product']} | {pct(x['recall'])} / {pct(x['fpr'])} | {pct(y['recall'])} / {pct(y['fpr'])} | {'공통' if r['selected_strategy']=='shared' else '전용'} | {r['recommendation']} |")
    comparison='\n'.join(cr)
    brief=f'''제품1,000개 중 불량100개·정상900개와 검증 비율 유지라는 **가정**입니다. 기본 모델은 불량{num(b['detected_defects'])}개, 선택 모델은{num(a['detected_defects'])}개를 찾습니다. 불량{num(delta['additional_detected'])}개를 더 찾는 대신 정상 추가검사는{num(b['normal_extra_checks'])}개에서{num(a['normal_extra_checks'])}개로{num(delta['additional_normal_checks'])}개 늘어납니다.

미검출1개10만원·정상 추가검사1개1천원 가정에서는 손실{b['assumed_loss']:,.0f}원에서{a['assumed_loss']:,.0f}원, 차이{delta['assumed_loss_reduction']:,.0f}원입니다. 재작업·설비·처리량·매출 효과를 제외하여 실제 영업이익으로 해석하지 않습니다.

두 모델의 검출 불량 중20%를 재작업으로 정상화한다는 별도 가정에서는 양품{num(delta['additional_recovered'])}개를 추가 회수합니다. **재작업 후 양품 비율**은{pct(b['good_fraction_after_repair'])}에서{pct(a['good_fraction_after_repair'])}, 차이{delta['good_fraction_change']*100:.2f}%p입니다. 실제 결함의 재작업 가능성과 제조 수율 향상은 검증하지 않았습니다.'''
    curriculum='''# 교육 자료와 모델 선택 근거

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
'''
    (ROOT/'docs/CURRICULUM_MODELS.md').write_text(curriculum)
    cohort_rows=[]
    rr=results['synthetic_process']
    for products in saved['synthetic_process']['plan']['cohorts']:
        candidates=[r for r in rr['trials'] if r['status']=='completed' and r['products']==products and r['calibration_feasible'] and r['validation']['precision']>=.25 and r['validation']['fpr']<=.15]
        if candidates:
            w=max(candidates,key=lambda r:(r['validation']['recall'],r['validation']['average_precision'],r['id']));v=w['validation']
            cohort_rows.append(f"| {'+'.join(products)} | {NAMES[w['model']]} / {w['balance']} | {pct(v['recall'])} | {pct(v['precision'])} | {pct(v['fpr'])} |")
        else:cohort_rows.append(f"| {'+'.join(products)} | 기준 충족 후보 없음 | — | — | — |")
    detail=[]
    for n,r in results.items():
        x,y=r['baseline_test'],r['test'];ci=y['recall_wilson95'];detail.append(f"| {labels[n]} | {y['n']} / {y['positive_count']} | {x['fn']} / {x['fp']} | {y['fn']} / {y['fp']} | {x['average_precision']:.3f} / {y['average_precision']:.3f} | {pct(ci[0])}~{pct(ci[1])} | {r['elapsed_seconds']:.2f}초 |")
    report=f'''# 반도체 검사 모델 관리 Agent 최종 보고서

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
'''
    for n,r in results.items():report+=f"| {labels[n]} | "+' | '.join(str(r['split'][k]['rows']) for k in ['train','calibration','validation','test'])+' |\n'
    report+='''
전처리는 train에서만 fit합니다. 유효0을 결측으로 제거하지 않습니다. 정확한 중복 행·이미지를 거부하며 근접 중복은 별도 검사 필요입니다. Calibration에서 임계값,validation에서 후보를 고르고 test는 마지막 비교·보류에만 씁니다. 같은 target·평가 행을 고정합니다. [누수 방지 원칙](https://scikit-learn.org/stable/common_pitfalls.html)

공정 기본 모델은 전체 제품 train의 unweighted Logistic Regression,median+scaling,threshold0.5입니다. 이미지 기본 모델은 계획의 첫 지도학습 후보이며 이번에는 gray ResNetSmall,threshold0.5입니다. After는 모델·전처리·학습 범위·임계값을 함께 선택한 전체 절차입니다. 개별 요소의 인과 효과로 해석하지 않습니다.

## 실제 Before/After

'''+main_table+'''

| 데이터 | Test 전체/불량 | Before 미탐/오탐 | After 미탐/오탐 | Before/After AP | Recall Wilson95% | 시간 |
|---|---:|---:|---:|---:|---:|---:|
'''+ '\n'.join(detail)+f'''

합성 공정 선택은 **{NAMES[rr['winner']['model']]} / {'+'.join(rr['winner']['products'])} / {rr['winner']['preprocessing']} / {rr['winner']['balance']}**입니다. 공개 SECOM은 calibration·validation 기준을 동시에 만족한 후보가 없어 탐색 후보만 보고하고 보류합니다. 이미지 contrast 세 구조는 validation 주요 지표가 동률이어서 사전 정의한 trial ID로 Autoencoder를 선택했습니다. 구조 우월성의 증거가 아닙니다.

AP는 sklearn non-interpolated Average Precision입니다. 단일 seed45·CPU·Python3.11.15,이미지6epoch 결과입니다. 합성의 높은 성능은 실제 현장 성능을 입증하지 않습니다. Wilson 구간도 분포 변화의 보장은 아닙니다. [AP 정의](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html), [PyTorch 재현성](https://docs.pytorch.org/docs/stable/notes/randomness.html)

## 검사량·비용·재작업 가정

{brief}

FPR은 실제 정상 중 잘못 추가검사 대상으로 고른 비율입니다. 화면에서는 정상 제품 추가 검사 허용 비율로 표현합니다. 15%는 정상100개 중 최대15개라는 뜻입니다. Recall은 실제 불량 중 발견 비율이므로 분모가 다릅니다.

계산식: D=N×불량률,G=N−D,발견=D×Recall,정상추가검사=G×FPR,손실=미탐×가정단가+정상추가검사×가정단가,재작업후양품률=(G+발견×정상화비율)/N. [계산 원본](evaluation/presentation_cases.json),[구현](../app/impact.py)

## 재학습 판단과 공통·제품별 비교

독립 seed1045의 새 합성3,840행·480lot에서 불량 발생 규칙을 변경했습니다. 이전 데이터와 중복되는 센서 행을 거부하고 새 train 구간에서만 기존 모델을 점검합니다. 이전 test Recall{pct(mg['review']['previous_recall'])}에 비해 새 train 점검{pct(mg['review']['current']['recall'])},FPR{pct(mg['review']['current']['fpr'])}로 **{mg['review']['verdict']}**을 제안했습니다. 서로 다른 배치의 비교이며 Recall10%p하락 등의 개발 휴리스틱은 통계적 drift 검정이 아닙니다. 불량20개 미만은 판단 보류합니다.

공통1개와 제품별4개 계획 생성 시 학습하지 않는 것을 검증했습니다. 자동 검증용 테스트 승인자로 승인한 뒤 각4개,총20개 조건(Random Forest/Logistic,none/weighted)을 실제 학습했습니다. 현장 승인 실적이 아닙니다.

{comparison}

표는 **동일 제품의 같은 validation 행**을 평가한 수치입니다. 각 후보는 train에서 학습하고 calibration에서 정한 임계값을 고정합니다. calibration·validation 기준을 충족한 후보 중 Recall,AP 순으로 방식을 선택하고 동률이면 공통을 택합니다. 둘 다 부족하면 비용 최소 참고 후보를 표시하고 보류합니다. test는 순위에 사용하지 않고 최종 확인·보류에만 사용합니다. 내부 후보와 방식 선택이 같은 validation을 재사용하므로 낙관 편향 가능성이 있습니다. 독립 기간 반복 평가가 필요합니다.

새로 등록한 한 배치 안의 제품 데이터를 통합·분리합니다. 과거 배치 파일을 자동 병합하지 않습니다. 파일·버전·source run·제품·지표·검토 상태를 저장하며 자동 배포false입니다. [점검·실행·비교 원본](evaluation/model_management.json)

## 학습 제품 부분집합 비교

이 표는 기존 합성 공정의 같은 validation192개를 평가합니다. 전용 제품만 평가하는 위의 새 배치 전략 비교와 목적이 다릅니다.

| 학습 제품 | 후보 | Recall | Precision | FPR |
|---|---|---:|---:|---:|
'''+ '\n'.join(cohort_rows)+'''

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
'''
    (ROOT/'docs/REPORT.md').write_text(report)
    readme=f'''# 반도체 검사 모델 관리 Agent

G045 김용찬 / SK AI Leader Academy / 과제2 신규 프로젝트

[최종 보고서 Google Slides](https://docs.google.com/presentation/d/1J2m_cpXyvb-5_Xabs2DsD3EnEV6B6GicF5OP2s5FohU/edit) / [상세 보고서](docs/REPORT.md) / [발표 대본 TXT](docs/발표대본_G045.txt)

불량 추가 발견과 정상 제품 추가검사 부담을 비교합니다. 새 데이터에서 재학습 필요를 판단하고,엔지니어 승인 후 공통·제품 전용 모델을 생성해 같은 제품의 평가에서 학습 방식을 권고하거나 보류합니다. 공개·합성 데이터의 교육용 PoC입니다.

![검사 효과 화면](docs/assets/easy-result.png)

## 시작하기

```bash
bash start.sh
```

http://localhost:8700 에서 연습용 공정 데이터와 완료된 예시 결과 바로 보기를 선택합니다. 새 설치에는 실행 이력이 없으므로 예제 데이터 준비 후 비교 계획을 생성하고 승인합니다. **계획 생성만으로 학습하지 않습니다.** 승인한 계획만 실행하고 반려·중복 실행은 차단합니다.

Python3.11 이상과 최초 의존성 설치가 필요합니다. SECOM 공식 ZIP은 저장소에 포함되어 SHA256으로 확인합니다. [시연 순서](docs/DEMO.md)

## 교육에서 다룬 모델

공정 후보: **Random Forest**,Logistic Regression,Hist Gradient Boosting. 이미지 후보: 교육용 축소 ResNet·VGGNet 계열,Autoencoder. [교육 자료명·페이지와 구현 구분](docs/CURRICULUM_MODELS.md)

Random Forest는 스칼라 실습과 반도체 자료 모두에서 확인했습니다. 이미지 축소 구조는 표준 ResNet18/VGG16 사전학습 비교가 아닙니다. NLP·시계열과 수율 예측은 향후 범위입니다.

## 구현한 기능

- 데이터 종류별 후보,전처리,제품 A/B/AB/ABC/ABCD 등 최대15개 학습 범위 비교
- train 전용 결측·분산·스케일 처리,불량 class weight,정상 전용 Autoencoder
- 근거 검색과 승인 계획·데이터 hash 고정,학습·평가·CSV 내보내기
- 검사 수량·불량률에 따른 추가 검출량과 검사 부담,손실·재작업 가정 계산
- 새 배치 성능 점검,승인 후 공통1개·제품별4개 후보의 실제 학습과 버전 저장
- 동일 제품 validation으로 공통/전용 방식 선택,test 기준 미달이면 보류

## 실제 측정 결과

{main_table}

공개 SECOM은 운영 성능 개선을 주장하지 않고 보류 사례로 보고합니다. 합성 이미지100%는 단순한 인공 패턴이며 현장 성능으로 일반화할 수 없습니다. 모델·전처리·임계값을 포함한 절차 비교로 개별 기법의 인과 효과는 아닙니다.

## 건수와 비용을 쉽게 읽기

{brief}

## 통합·제품별 재학습 비교

기존 모델의 이전 test Recall{pct(mg['review']['previous_recall'])}와 새 배치 train 점검{pct(mg['review']['current']['recall'])}를 비교해 재학습을 제안했습니다. 서로 다른 배치의 비교이며 통계적 drift 검정은 아닙니다.

{comparison}

표는 같은 제품의 같은 validation에서 비교합니다. test는 방식 선택에 쓰지 않고 최종 확인에만 사용합니다. 새 배치 안에서 통합·전용 학습을 비교하며 과거 파일을 자동 병합하지 않습니다. 운영 모델 자동 교체는 없습니다. [실제 점검·학습 기록](docs/evaluation/model_management.json)

## 검증과 재현

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/check_mcp.py
.venv/bin/python scripts/evaluate.py
.venv/bin/python scripts/evaluate_management.py
.venv/bin/python scripts/build_report.py
```

22개 테스트와 실제 MCP stdio 연결을 검증했습니다. 평가 스크립트의 승인자는 명시적인 자동 테스트 actor이며 현장 승인 실적이 아닙니다. 데이터·분할 hash,seed와환경은 JSON 및 requirements.lock.txt에 기록합니다. 기기·라이브러리 차이까지 완전한 재현을 보장하지 않습니다.

## Agent와 운영 범위

LangGraph의 데이터 검사·근거 검색·계획 역할은 결정적 Python 함수입니다. TF-IDF 검색 근거를 사용하고 독립 LLM 추론·생성형 응답은 구현하지 않았습니다. 외부 LLM 호출0회입니다. DI로 API와 MCP가 Workbench를 공유합니다. MCP는 조회·제안만 제공하고 승인·실행 도구를 노출하지 않습니다. LangSmith 계측은 구현했고 원격 추적은 미검증입니다.

Dockerfile과 deploy/kubernetes.yaml은 기업 클라우드 확장 예시이며 빌드·실배포는 검증하지 않았습니다. production에서는 ENGINEER_TOKEN을 설정해야 API를 사용할 수 있습니다. 현재 공유 토큰·SQLite·단일 worker는 개인별 SSO/RBAC·대규모 worker·중앙 감사 체계를 대체하지 않습니다.

## 데이터 형식과 출처

공정 CSV에는 label(정상0/불량1),product,lot_id 또는 timestamp와 숫자 센서 열을 넣습니다. 이미지 ZIP은 manifest.csv와 image_path의 상대 이미지 파일로 구성합니다. 이미지 manifest에도 label·product·lot_id 또는 timestamp가 필요합니다. 업로드30MB,압축 해제128MB,실험72조건,제품4개,행20,000개로 제한합니다.

[UCI SECOM](https://archive.ics.uci.edu/dataset/179/secom)은CC BY4.0입니다. 센서590열·표본1,567·불량104입니다. 교육 PDF·아이디어 사진과 제출용 명단 엑셀은 공개 저장소에 넣지 않았습니다.
'''
    (ROOT/'README.md').write_text(readme)
if __name__=='__main__':main()
