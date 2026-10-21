"""Generate report and a five-minute script from the current measured receipts."""
import json
from pathlib import Path
import sys
from decimal import Decimal, ROUND_HALF_UP
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from app.catalog import TABULAR, IMAGE
NAMES={k:v[0] for k,v in {**TABULAR,**IMAGE}.items()}
pct=lambda x:str(Decimal(str(100*x)).quantize(Decimal('0.1'),rounding=ROUND_HALF_UP))+'%'
def main():
    saved={n:json.loads((ROOT/f'docs/evaluation/{n}.json').read_text())for n in ['synthetic_process','secom','images']}
    rr={n:x['result']for n,x in saved.items()};r=rr['synthetic_process'];w=r['winner'];b,t=r['baseline_test'],r['test'];v=w['validation'];split=r['split']
    assert split['target_ratios']=={'train':.6,'validation':.2,'test':.2},'Regenerate receipts with 6:2:2 first'
    mg=json.loads((ROOT/'docs/evaluation/model_management.json').read_text());m=mg['comparison']['same_model_retraining'];old,new=m['before'],m['after']
    c=next(x for x in mg['comparison']['products']if x['product']=='C');chosen=next(x for x in c['candidates']if x['strategy']==c['selected_strategy'])
    model=NAMES[w['model']];products='+'.join(w['products']);pos=t['positive_count'];normal=t['tn']+t['fp'];dt=t['tp']-b['tp'];dfp=t['fp']-b['fp']
    uci='https://archive.ics.uci.edu/dataset/179/secom';doi='https://doi.org/10.24432/C54305';sk='https://news.skhynix.com/en/the-past-present-and-future-of-data-science-organization-at-sk-hynix/'
    initial_conclusion='시연 목표 충족·회사 적용은 별도 검증'if r['gate']['passed']else'시연 목표 미달·추가 실험 필요'
    retrain_conclusion='Recall·정상 오판 시연 목표 충족. 회사 적용은 별도 검증'if new['recall']>=.9 and new['fpr']<=.15 else'시연 목표 초과·미달 항목은 추가 확인 필요'
    cway='C만 학습'if c['selected_strategy']=='separate'else'A+B+C+D 합쳐 학습'
    candidate=f'{model} · {products} 학습'
    five=[
      (15,'안녕하세요. G045 김용찬입니다. 반도체 검사 모델 실험 도우미를 만들었습니다. 데이터를 넣으면 모델 비교 계획을 제안하고, 엔지니어가 승인하면 실제 학습하는 Agent입니다.'),
      (20,'새 검사 데이터에 어떤 모델을 쓸지 결정하는 상황입니다. 데이터 선택, 계획 확인, 승인과 학습, 결과 확인까지 한 실험으로 이어집니다. 합성 센서 사례로 처음부터 결론까지 보여 드리겠습니다. 반복 실험을 돕는 기능이며 실제 작업 시간 절감은 아직 측정하지 않았습니다.'),
      (25,'오른쪽 제품 A부터D의 합성 센서1,280건을 선택합니다. 불량 정답은201건입니다. 비교 목표를 정한 뒤 비교 계획 제안받기를 누릅니다. A부터D는 가상 제품이고 가운데 UCI SECOM은 실제 공개 반도체 센서 자료입니다. 내 센서 CSV나 이미지 ZIP도 등록할 수 있습니다.'),
      (35,'Agent가 빈 값과 불량 비율을 확인하고 전처리 이유와 비교 계획을 제안합니다. SVM이나 KNN에는 단위를 맞추는 Scaling을, 불량 부족에는 학습 가중치나 복제를 비교합니다. 수업에서 배운6대2대2로 나눠 고정합니다. 교육 모델 열두 종류와 제품 조합을 최대 쉰두 조건까지 비교하고, 여기 승인 버튼을 눌러야 학습합니다. 검출률90퍼센트와 정상 오판15퍼센트는 회사 기준이 아닌 시연 목표입니다.'),
      (20,f'앞에서 승인한 실험의 결론입니다. {model}를 {products}로 학습한 후보가 선택됐습니다. 별도 Test에서 불량{pos}개 중{t["tp"]}개를 찾아 Recall{pct(t["recall"])}입니다. {initial_conclusion}라고 알려 줍니다. 후보 선정과 생산 적용은 다릅니다.'),
      (25,'불량을 놓치면 안 되므로 Recall을 우선합니다. 불량 열 개 중 아홉 개를 찾으면 Recall90퍼센트이고 놓친 한 개가 FN입니다. 정상인데 불량으로 판정한 것은 FP, 정상 오판입니다. 전부 불량이라고 해도 Recall은 높아지므로 정상 오판을 함께 봅니다. Precision과 F1은 보조 지표로 확인합니다.'),
      (35,f'같은 Test의 Before After입니다. 불량{pos}개 중 기본 모델은{b["tp"]}개, 후보는{t["tp"]}개를 찾았습니다. 정상 오판은{b["fp"]}개에서{t["fp"]}개로 바뀌었습니다. 불량 검출과 정상 오판을 함께 보고 판단해야 합니다. 후보 Recall{pct(t["recall"])}는 시연 목표90퍼센트에 못 미쳐 추가 실험이 필요합니다. 합성 결과이므로 현장 수율 증가로 해석하지 않습니다.'),
      (35,f'추가 상황입니다. 기존 모델이 있으면 같은 제품의 새 정답 데이터로 점검하고 재학습을 제안합니다. 승인 후 같은 {NAMES[m["model"]]}를 다시 학습한 합성 시연입니다. 새 배치의 같은 Test에서 불량 발견은{old["tp"]}개에서{new["tp"]}개, 정상 오판은{old["fp"]}개에서{new["fp"]}개가 됐습니다. Recall{pct(new["recall"])}, 정상 오판률{pct(new["fpr"])}입니다. 운영 모델은 자동 교체하지 않습니다.'),
      (20,f'제품 데이터를 합칠지 따로 학습할지도 비교합니다. C의 같은 Validation에서는 {cway}한 후보를 골랐습니다. 별도 Test의 Recall은{pct(chosen["test"]["recall"])}여서 {c["recommendation"]}입니다. 제품별 학습이 항상 좋다는 결론은 아닙니다.'),
      (25,f'공개 데이터 출처는 UCI Machine Learning Repository의 SECOM입니다. McCann과 Johnston이2008년에 공개했고 DOI와 원본 링크를 적었습니다. 제조사명은 원자료에 없습니다. 실제 공개 자료에서는 Test 불량{rr["secom"]["test"]["positive_count"]}개 중{rr["secom"]["test"]["tp"]}개를 찾았습니다. 합성 시연의 개선을 실제 공장 효과로 일반화하지 않습니다.'),
      (20,'이 앱은 계획의 이유를 제안하고 승인 후 실제 학습과 비교를 수행합니다. 역할별 Agent, RAG와 MCP를 연결했고 테스트30개를 통과했습니다. 작은 표본과 합성 데이터가 한계이며, 현장 데이터와 담당자 기준의 검증이 다음 단계입니다. 상세 기술과 지표는 부록에 넣었습니다. 감사합니다.')]
    slides=[]
    def add(context,title,body,table=None,sources=None,note=None,layout_id=None):
        item=dict(context=context,title=title,body=body,table=table,sources=sources or [],note=note or '')
        if len(slides)<11:item['note']=five[len(slides)][1]
        if layout_id:item['layout_id']=layout_id
        slides.append(item)
    add('프로젝트 소개','반도체 검사 모델\n실험 도우미',['데이터에 맞는 모델을 비교하고, 승인받아 학습하는 Agent','G045 김용찬 · SK AI Leader Academy · 과제 2'])
    add('사용자 · 검사 모델을 만드는 공정·장비 엔지니어','엔지니어 입력부터 실험 결론까지',['사용 상황: 새 검사 데이터에 어떤 모델을 사용할지 비교합니다.','같은 합성 센서 사례의 입력, 승인, 결과를 이어서 보여 줍니다.'],[['단계','엔지니어의 행동','Agent가 보여 주는 결과'],['1. 데이터 선택','제품 A–D 합성 센서 선택','1,280건·불량201건 점검'],['2. 계획 확인','비교 계획 제안받기','전처리 이유·12모델·최대52조건'],['3. 승인·학습','계획 승인·학습 시작','실제 학습·Validation 후보 선택'],['4. 실험 결론','같은 Test 결과 확인',f'{model} 후보·Recall{pct(t["recall"])}\n{initial_conclusion}']],sources=[sk,'app/workbench.py'])
    add('본 실험 1/3 · 정상/불량 정답이 있는 합성 센서','데이터 선택 후 비교 계획을 요청합니다',['선택: 제품 A–D 합성 센서 1,280건, 불량201건','엔지니어 행동: 비교 목표를 정하고 “비교 계획 제안받기” 클릭'],sources=[uci,'app/data.py'])
    add('본 실험 2/3 · 앞에서 선택한 같은 센서 데이터','계획의 이유를 확인하고 학습을 승인합니다',[f'분할: Train60%({split["train"]["rows"]}개)·Validation20%({split["validation"]["rows"]}개)·Test20%({split["test"]["rows"]}개)', '같은 생산 묶음(lot)을 분리하고 전처리·12모델·최대52조건 확인 후 승인'],sources=['app/data.py','app/catalog.py','docs/CURRICULUM_MODELS.md'])
    add('본 실험 3/3 · 승인한 비교 실험의 결과','후보는 골랐지만, 추가 실험이 필요합니다'if not r['gate']['passed']else'시연 목표를 만족한 비교 후보입니다',[f'후보: {candidate} / Test 불량{t["tp"]}/{pos}개 발견',f'결론: Recall{pct(t["recall"])}. {initial_conclusion}·자동 적용 없음'],sources=['docs/evaluation/synthetic_process.json'])
    add('판단 기준 · 불량을 Positive로 둡니다','불량 미검출을 줄이되, 정상 오판도 확인합니다',['Recall: 실제 불량 중 얼마나 찾아냈는가?','정상 오판률: 실제 정상 중 얼마나 불량으로 잘못 판정했는가?','Precision·F1도 보조 지표로 함께 확인합니다.'],[['설명용 예시','불량으로 판정','정상으로 판정'],['실제 불량10개','9개 발견 (TP)','1개 놓침 (FN)'],['실제 정상90개','3개 정상 오판 (FP)','87개 정상 통과 (TN)']],sources=['스칼라 12주차 데이터분석 Mini Project 박병선p PDF15쪽','사용자 제공 Recall·정상 오판 설명 스크린샷 두 장 참고. 금액 추정·폐기 단정은 사용하지 않음.'])
    add('실험 1 · 합성 센서의 같은 Test에서 비교',f'불량 {dt}개를 더 찾았지만 정상 오판도 늘었습니다'if dt>0 and dfp>0 else'불량 발견과 정상 오판의 변화를 비교했습니다',[f'후보: {candidate} / 기본: Logistic Regression',f'후보 Recall{pct(t["recall"])}·정상 오판률{pct(t["fpr"])}. {initial_conclusion}'],[[f'동일 Test · 불량{pos}개 / 정상{normal}개','기본 모델','고른 후보'],['불량 발견',f'{b["tp"]} / {pos}개',f'{t["tp"]} / {pos}개'],['놓친 불량',f'{b["fn"]}개',f'{t["fn"]}개'],['정상 오판',f'{b["fp"]} / {normal}개',f'{t["fp"]} / {normal}개']],sources=['docs/evaluation/synthetic_process.json'])
    add('추가 상황 · 같은 제품에 새 정답 데이터가 들어왔습니다','점검 후, 승인받아 같은 알고리즘을 재학습합니다',[f'새 합성 배치의 같은 Test: 불량 발견 {old["tp"]}/{old["positive_count"]}개에서 {new["tp"]}/{new["positive_count"]}개',f'정상 오판 {old["fp"]}개에서 {new["fp"]}개. {retrain_conclusion}'],sources=['docs/evaluation/model_management.json'])
    add('추가 기능 · 제품 데이터를 합칠지 나눌지 비교합니다','제품별로 합친 학습과 개별 학습을 비교합니다',[f'C 제품: 같은 Validation에서 “{cway}” 후보 선택',f'C의 별도 Test Recall{pct(chosen["test"]["recall"])}. {c["recommendation"]}'],sources=['docs/evaluation/model_management.json'])
    sc,im=rr['secom']['test'],rr['images']['test']
    add('데이터 출처 · 실측 결과와 합성 시연을 구분합니다','공개 반도체 공정 데이터: UCI SECOM',['McCann, M. & Johnston, A. (2008). SECOM [Dataset].','UCI Machine Learning Repository · DOI: 10.24432/C54305 · CC BY4.0','archive.ics.uci.edu/dataset/179/secom'],[['자료','입력과 정답','한계·최종 Test 결과'],['UCI SECOM 공개 원본','1,567건·센서590열\n합격/불합격 기록·불합격104건',f'제조사명·제품ID 제공 없음\n불량{sc["tp"]}/{sc["positive_count"]}개 발견·정상{sc["fp"]}/{sc["tn"]+sc["fp"]}개 오판'],['합성 센서 / 합성 이미지','가상 제품 A–D / 연습용 패턴',f'실제 생산 데이터·SEM 이미지 아님\n이미지 불량{im["tp"]}/{im["positive_count"]}개 발견']],sources=[uci,doi,'data/public/secom/secom.names','docs/evaluation/secom.json','docs/evaluation/images.json'])
    add('결론 · 지금 사용할 수 있는 기능과 남은 검증','실험 계획부터 결과 확인까지 연결했습니다',['구현: 데이터별 계획·이유, 승인 후 학습, 같은 Test 비교, 재학습·제품별 비교','확인: 실제 학습·모델 파일 저장, MCP 연결, 단위/API 테스트30개 통과','한계: 작은 불량 표본, 합성 데이터, 단일 분할, 반복 Validation 비교','추가 검증: 현장 데이터와 담당자 기준, 독립 기간 평가, 엔지니어 작업 시간 측정'],sources=['docs/evaluation/tests.txt',sk])
    integration_path=ROOT/'docs/evaluation/agent_integration.json';integ=json.loads(integration_path.read_text())
    states=' / '.join(x['role']+':'+x['status']for x in integ['agent_outputs'])
    add('부록 · Agent와 엔지니어의 역할','판단 근거를 제안하고, 승인 뒤 도구를 실행합니다',['LangGraph: 데이터 점검, 실험 계획, 결과 검토 역할 분리','RAG: 데이터·모델 근거를 검색해 실험 계획 설명에 연결','로컬 Qwen: 응답 검사 실패 시 규칙 설명 사용','엔지니어는 승인·적용 판단, 실험 엔진은 학습·지표 계산'],note='현재 RAG는 교육·공개 근거 요약문14개를 검색합니다. 새 모델을 외부에서 자동 발굴하는 기능은 확장 설계입니다. 실험 엔진이 수치를 계산하고 LLM은 허용 코드·출처 검사를 거칩니다. 실제 실행 상태: '+states+'. 이 검사는 자유 추론의 모든 사실성을 보장하지 않습니다.',sources=['docs/evaluation/agent_integration.json','app/planner.py','app/advisors.py'])
    labels={'synthetic_process':'합성 센서','secom':'UCI 공개 센서 SECOM','images':'합성 이미지'}
    metrics=[['선택 후보의 Test 결과','Recall','Precision','F1','정상 오판률']]+[[labels[n],*[pct(x['test'][k])for k in ['recall','precision','f1','fpr']]]for n,x in rr.items()]
    add('부록 · 상세 지표와 검증 방식','Validation으로 고르고, Test로 마지막 확인합니다',['Train은 학습, Validation은 후보·판정값 비교, Test는 마지막 확인',f'합성 센서 Train60%({split["train"]["rows"]}개) / Validation20%({split["validation"]["rows"]}개) / Test20%({split["test"]["rows"]}개)','같은 생산 묶음(lot)·날짜 경계를 보존합니다. 후보의 제품 범위에 따라 Train 실사용 수는 다릅니다.','F1은 보조 지표입니다. Test 점수를 보며 분할·후보를 조정하지 않습니다.'],metrics,note=f'수업 기준에 맞춰6대2대2를 사전에 고정했습니다. 합성 센서 전체 학습 풀은{split["train"]["rows"]}개이고 선택 후보는 그중{products}의{w["train_n"]}개를 학습했습니다. SECOM은 날짜 블록60/20/20을 나눠 실제 행 수는'+str([rr['secom']['split'][k]['rows']for k in ['train','validation','test']])+'개입니다. 원자료의 제조사명은 제공되지 않습니다. 반복 Validation 비교와 단일 seed의 한계가 있어 독립 기간 평가가 필요합니다. Recall=TP/(TP+FN), Precision=TP/(TP+FP), F1=2TP/(2TP+FP+FN), 정상 오판률=FP/(FP+TN)입니다.',sources=['app/data.py','docs/evaluation/summary.json','https://scikit-learn.org/stable/modules/cross_validation.html'])
    add('부록 · 확장 설계이며 혼합 비율 탐색은 미구현','앙상블 비율도 Validation에서 비교하는 확장',['현재: RF·부스팅 사용. 서로 다른 모델의 혼합 비율 탐색은 미구현','6:2:2 분할을 비교 전에 고정하고 “실험한 비율 중 가장 좋은 후보”로 설명'],[['확장 단계','Agent가 설명할 내용'],['1. 같은 입력·고정 분할','동일 입력·라벨의 모델1·모델2를 Train으로 학습'],['2. 승인받아 비율 비교','0:100,25:75,50:50,75:25,100:0 등 예시 실험안\n측정한 최적값 아님'],['3. Validation에서 선택','Recall 우선·정상 오판 함께 확인. 목표 미달이면 추가 실험'],['4. 고정된 Test로 확인','선택 비율을 고정해 단일 모델과 비교. 두 모델 운영 부담 확인']],note='가중치를 비교하는 확장 설계입니다. 현재 RF·부스팅 알고리즘은 실제 사용하지만 서로 다른 모델의 예측 확률을 섞는 비율 탐색은 미구현입니다. 사전 정의한 비율과 판정값을 Validation에서 고르고 고정된 Test에서 확인합니다. 모든 문제에 통용되는 전역 최적 비율이라는 주장을 하지 않습니다. 새 모델 발굴은 외부 검색으로 공식 문서·논문·모델 카드를 모으고 RAG로 적합성 근거를 찾은 뒤 별도 승인과 adapter 검증이 필요합니다.',sources=['docs/MODEL_DISCOVERY_DESIGN.md','https://scikit-learn.org/stable/modules/ensemble.html#voting-classifier'],layout_id=15)
    add('부록 · 기술 요소와 구현 위치','기술 요소가 반영된 위치',['상세 대응표: docs/ASSIGNMENT_CHECKLIST.md'],[['기술 요소','구현 위치','확인 상태'],['Multi-Agent','planner.py · advisors.py','데이터 점검·계획·결과 검토 역할'],['RAG','Knowledge · knowledge.json','계획 설명용 근거 검색·출처 연결'],['MCP','mcp_server.py','4도구·지식 resource 실제 연결'],['의존성 주입','Dependencies · Workbench','Store·Knowledge·Advisor 주입'],['모듈화','app/ 데이터·학습·관리 모듈','API·MCP가 공통 엔진 재사용'],['단위/API 테스트','tests/','26개 테스트 통과']],note='기술 요소와 구현 위치를 연결한 표입니다. 과제의 발표 흐름은 문제, 추가 기능, 같은 입력의 Before/After, 한계입니다. 본 발표1~11장과 기술·지표 부록12~15장에 반영했습니다. 점수는 기재하지 않습니다.',sources=['docs/ASSIGNMENT_CHECKLIST.md','docs/evaluation/tests.txt','docs/evaluation/mcp_check.json'],layout_id=14)
    # Presentation revision: teach the context first, then one real app workflow.
    previous_slides=slides
    import copy
    slides=[]
    def keep(index,layout):
        item=copy.deepcopy(previous_slides[index]);item['layout_id']=layout;slides.append(item);return item
    def newslide(context,title,body,layout,table=None,sources=None,note=''):
        item=dict(context=context,title=title,body=body,layout_id=layout,table=table,sources=sources or [],note=note);slides.append(item);return item
    keep(0,1)
    newslide('출발점 · 반도체 교육에서 배운 데이터와 모델','데이터 종류에 따라 쓰는 모델이 다릅니다',[
        '이번 구현: 검사 이미지와 숫자 센서의 정상·불량 분류',
        '자연어 로그 분석·시계열 예측은 향후 확장 범위'],20,table=[['데이터 종류','반도체 업무 활용 예시','교육자료의 모델 예시'],['검사 이미지','불량 이미지 분류\n단면 길이 분석','ResNet · VGGNet\nGAN · Autoencoder'],['자연어·로그','장비 불량 유형 분류\n공정 로그 분석','LSTM · GPT · BERT'],['시계열','수율 분석\n산포 분석','LSTM · ARIMA\nAutoencoder']],
        sources=['사용자 제공 반도체 교육 사진2 / 20261017_135247.jpg. 분류 화면의 내용을 사용자 요청에 따라 편집 가능한 표로 재구성.'])
    flow=keep(1,2);flow['title']='반복할 모델 실험을 Agent에게 맡깁니다';flow['body']=['사용 상황: 새 검사 데이터에 어떤 모델을 쓸지 비교합니다.','엔지니어는 계획을 검토하고, Agent는 승인받은 실험을 실행합니다.'];flow['table']=[['순서','엔지니어의 행동','Agent가 보여 주는 내용'],['1. 입력','검사 데이터 선택','데이터 상태와 비교 계획'],['2. 승인','모델·전처리 계획 확인 후 승인','실제 학습과 Validation 비교'],['3. 결론','기본 모델과 후보 결과 확인','불량 발견·정상 오판·추가 실험 판단']]
    keep(2,3)
    plan=keep(3,4);plan['body']=['학습60% · 검증20% · 마지막 확인20%로 고정','생산 묶음(lot)이 학습·평가에 섞이지 않도록 분리합니다.']
    result=keep(4,5);result['body']=['기본: Logistic Regression / 선택 후보: CatBoost · A+B+C 학습','Test 불량27/32개 발견. 목표 미달로 추가 실험 필요']
    sc,im=rr['secom']['test'],rr['images']['test'];sb,ib=rr['secom']['baseline_test'],rr['images']['baseline_test']
    newslide('같은 앱의 세 가지 데이터 · 각 데이터 안에서 같은 Test로 비교','데이터를 바꾸면 모델과 결론도 달라집니다',[
        '기본 / 후보 순으로 표시했습니다. 각 행의 Test는 서로 다릅니다.',
        'UCI SECOM: 공개 반도체 센서·합격/불합격 기록, McCann & Johnston(2008)'],21,[
        ['데이터','기본 모델 / 선택 후보','불량 발견\n기본 / 후보','정상 오판\n기본 / 후보','Agent의 결론'],
        ['합성 센서\n제품 A–D','Logistic / CatBoost\n후보 학습: A+B+C',f'{b["tp"]} / {t["tp"]}\n(불량{pos}개)',f'{b["fp"]} / {t["fp"]}\n(정상{normal}개)','Recall84.4%\n추가 실험 필요'],
        ['UCI SECOM\n공개 센서','Logistic / XGBoost\nXGBoost는 참고 결과',f'{sb["tp"]} / {sc["tp"]}\n(불량{sc["positive_count"]}개)',f'{sb["fp"]} / {sc["fp"]}\n(정상{sc["fp"]+sc["tn"]}개)','목표 충족 후보 없음\n데이터·계획 재검토'],
        ['합성 이미지','축소 ResNet /\nAutoencoder',f'{ib["tp"]} / {im["tp"]}\n(불량{im["positive_count"]}개)',f'{ib["fp"]} / {im["fp"]}\n(정상{im["fp"]+im["tn"]}개)','Recall93.3%\n불량 표본 보강 필요']
    ],sources=[uci,doi,'docs/evaluation/synthetic_process.json','docs/evaluation/secom.json','docs/evaluation/images.json'])
    newslide('판단 기준 · 불량을 Positive로 둡니다','Recall을 우선하되 정상 오판도 함께 봅니다',[
        '먼저 중요한 불량의 검출 목표와 정상 오판 허용 목표를 정합니다.',
        '현재90%·15%는 교육용 시연 목표입니다. 회사별 기준은 별도 합의합니다.'],22,[
        ['지표','쉽게 말하면','이번 프로젝트에서의 역할'],
        ['Recall','실제 불량 중 몇 개를 찾았나?','불량을 놓치지 않는 목표를 우선 확인'],
        ['정상 오판률','실제 정상 중 몇 개를 불량으로 잘못 봤나?','Recall만 높이는 후보를 걸러내는 목표'],
        ['Precision · F1','불량 판정의 정확성과 Recall의 균형','후보의 장단점을 함께 보는 보조 지표']
    ],sources=['https://ir.kla.com/news-events/press-releases/detail/121/kla-tencor-introduces-comprehensive-wafer-inspection-and','https://scikit-learn.org/stable/modules/generated/sklearn.metrics.f1_score.html'])
    discovery_path=ROOT/'docs/evaluation/model_discovery.json';dr=json.loads(discovery_path.read_text())if discovery_path.exists()else None
    newslide('추가 기능 · 엔지니어가 아직 비교하지 않은 모델 찾기','공식 문서에서 새 후보를 찾아 실험합니다',[
        '공식 모델 목록 검색 · RAG 근거 확인 · 계획 승인 · 실제 학습',
        '센서 ExtraTrees·GaussianNB 실험 후 CatBoost 유지. 새 후보 이력을 저장했습니다.'],23,
        sources=['app/discovery.py','docs/evaluation/model_discovery.json','https://scikit-learn.org/stable/api/index.html'])
    final=keep(10,11);final['title']='검사 모델을 비교하고 다음 실험을 판단합니다';final['body']=['사용: 데이터 선택, 계획 승인, 기본 모델과 후보 비교','추가: 새 모델 탐색 RAG, 재학습, 합친 학습·제품별 학습 비교','한계: 합성 데이터·작은 불량 표본·Test 재사용 탐색 비교','다음: 현장 데이터와 담당자 기준으로 독립 기간 검증']
    keep(7,8);keep(8,9);metric=keep(12,13);metric['body']=[s.replace('같은 생산 묶음(lot)','같은 생산 묶음(lot)')for s in metric['body']];keep(9,10)
    ext=keep(13,15);ext['context']='부록 · 앙상블 혼합 비율은 확장 설계이며 미구현';ext['note']=ext['note'].split('새 모델 발굴은')[0]+' 외부 모델 탐색은 공식 scikit-learn 목록과 두 개의 검토된 adapter 범위에서 실제 구현했습니다. 임의 웹 모델 자동 코드 생성은 지원하지 않습니다.'
    mapping=keep(14,14);mapping['table'][2]=['RAG','discovery.py · Knowledge','공식 외부 문서 검색·후보 제안·승인 후 학습'];mapping['table'][-1]=['단위/API 테스트','tests/','30개 테스트 통과'];mapping['note']='기술 요소와 구현 위치를 연결한 표입니다. 점수는 적지 않습니다. 본문1~10장, 질문용 부록11~16장입니다.'
    five=[
      (10,'안녕하세요. G045 김용찬입니다. 반도체 검사 데이터에 맞는 모델을 비교하고, 승인받아 학습하는 Agent를 만들었습니다.'),
      (25,'반도체 교육에서 배운 내용입니다. 검사 이미지, 장비 로그, 시간에 따라 쌓이는 데이터는 형태가 달라 쓰는 모델도 다릅니다. 이 프로젝트에서는 범위를 줄여 검사 이미지와 숫자 센서의 정상·불량 분류를 구현했습니다. 자연어 로그와 시계열 예측까지 모두 구현한 것은 아닙니다.'),
      (20,'엔지니어가 전처리와 여러 모델을 직접 반복 비교하는 상황을 생각했습니다. 데이터를 선택하면 Agent가 계획을 제안하고, 엔지니어가 승인하면 학습합니다. 결과에서는 기본 모델보다 무엇이 달라졌고 추가 실험이 필요한지 보여 줍니다.'),
      (20,'같은 사례로 끝까지 보겠습니다. 제품 A부터D의 합성 센서1,280건을 선택하고 비교 계획을 요청합니다. 불량 정답은201건이며 제품 이름은 가상입니다. 기존 완료 결과를 보는 버튼은 이전 실험을 불러오는 기능입니다.'),
      (30,'Agent가 결측과 불량 비율을 점검하고 전처리·모델 계획을 제안합니다. 필요한 모델에는 Scaling을 적용합니다. 학습, 검증, 마지막 확인 데이터는 수업 기준6대2대2로 고정했습니다. 생산 묶음인 lot이 학습과 평가에 섞이지 않게 나눕니다. 이 승인 버튼을 눌러야 실제 학습합니다.'),
      (30,'결과입니다. 기본 비교 모델은 Logistic Regression이고, 이번 실험에서 고른 후보는 A B C로 학습한 CatBoost입니다. 같은 Test에서 불량32개 중20개를 찾던 것이27개로 늘었지만 정상 오판도1개에서14개로 늘었습니다. 후보 Recall84.4퍼센트는 시연 목표에 못 미쳐 추가 실험이 필요합니다. 현장 적용 모델로 확정한 것은 아닙니다.'),
      (40,'다른 데이터도 같은 앱에서 확인할 수 있습니다. 합성 센서는 불량을 더 찾았지만 정상 오판이 늘었습니다. UCI SECOM은 실제 공개 반도체 센서와 합격·불합격 기록인데, 이번 조건에서는 목표를 만족한 모델이 없었습니다. 합성 이미지는 Autoencoder가 정상 오판을 줄였지만 불량 하나를 놓쳤고, 평가 불량이15개로 작았습니다. 데이터마다 Test가 다르므로 이 표를 모델의 종합 순위로 해석하지 않습니다.'),
      (30,'불량 유출을 막는 검사에서는 Recall을 우선하되, 전부 불량이라고 판정하는 모델을 고르면 안 됩니다. 그래서 정상 오판 목표도 함께 확인합니다. Precision은 불량이라고 본 것 중 진짜 불량의 비율이고, F1은 Precision과 Recall을 함께 보는 지표입니다. 어떤 지표가 무조건 최고라는 회사 공통 수치 대신, 담당자가 검사 목적에 맞는 목표를 정하도록 했습니다.'),
      (45,'엔지니어가 기존 모델을 알고 있다는 점을 고려해 새 모델 탐색도 추가했습니다. 공식 모델 목록과 문서를 가져오고 RAG로 근거를 검색해 ExtraTrees와 Gaussian Naive Bayes를 제안합니다. 엔지니어가 계획을 승인하면 기존 후보와 같은 조건으로 실제 학습하고 모델 목록에 결과를 남깁니다. 현재는 두 개의 검토된 센서 모델 연결을 지원합니다. 웹에서 임의 코드를 받아 실행하는 기능은 아닙니다. 기존 Test를 다시 쓴 탐색 결과이므로 현장 적용에는 독립 기간 검증이 필요합니다.'),
      (25,'핵심은 가장 좋아 보이는 모델 이름만 알려 주는 것이 아니라, 실제 실험을 수행하고 불량 발견과 정상 오판으로 다음 판단을 돕는 것입니다. 새 모델 탐색, 기존 모델 재학습, 제품별 학습 비교를 연결했습니다. 합성과 공개 자료로 확인한 교육용 결과이며 현장 검증이 필요합니다. 감사합니다.')]
    for i,(seconds,note)in enumerate(five):slides[i]['note']=note

    (ROOT/'docs/slide-content.json').write_text(json.dumps(slides,ensure_ascii=False,indent=2))
    script='G045 김용찬 / 과제2 / 반도체 검사 모델 실험 도우미\n2026-10-21 · 6:2:2 재실험 결과\n본 발표1~10장, 11~16장은 질문용 부록입니다.\n시간 계획275초(4분35초)+전환 여유25초=5분. 실제 발화 속도에 따라 연습하며 조정하세요.\n줌에서 슬라이드를 공유하고 실제 화면 캡처를 설명합니다. 새 학습을 기다릴 필요는 없습니다.\n\n'
    elapsed=0
    for i,x in enumerate(slides,1):
        if i<=10:elapsed+=five[i-1][0];cue=f'{five[i-1][0]}초 / 누적{elapsed//60}:{elapsed%60:02d}'
        else:cue='질문용 부록'
        script+=f'[{i}장 / {cue}] '+x['title'].replace('\n',' ')+'\n'+x['note']+'\n\n'
    script+='질문 대비\nQ. 왜6:2:2인가요?\nA. 수업 기준에 맞춘 사전 고정 분할입니다. 같은 생산 묶음(lot)을 섞지 않고 날짜 경계를 보존합니다. 비율을 Test 점수에 맞춰 바꾸지 않습니다. lot·날짜 단위 때문에 실제 행 비율은 약간 달라질 수 있습니다.\n\nQ. 후보를 골랐는데 적용은 왜 보류하나요?\nA. Validation 후보 선택과 별도 Test 확인, 실제 회사 적용 승인은 다른 단계입니다.\n\nQ. 정상 오판은 재검사나 폐기인가요?\nA. 정상을 불량으로 잘못 판정한 FP입니다. 후속 조치는 이 실험에서 가정하지 않습니다.\n\nQ. 외부 모델 검색과 앙상블 비율도 동작하나요?\nA. 외부 모델 검색은 공식 scikit-learn 목록과 두 adapter 범위에서 구현했습니다. 서로 다른 모델의 앙상블 혼합 비율 탐색은 확장 설계입니다.\n\n앱 켜기\nFinder에서 Semiconductor-AI-Agent 폴더를 열고 start.command를 더블클릭합니다. 열린 터미널 창을 열어 둔 채 Chrome에서 http://localhost:8700을 엽니다. localhost는 내 컴퓨터입니다. 재부팅하면 앱도 꺼지므로 다시 켭니다.\n'
    (ROOT/'docs/발표대본_G045.txt').write_text(script)
    report='# 반도체 검사 모델 실험 도우미\n\nG045 김용찬 · 과제2 · 2026-10-21\n\n6:2:2로 재실험한 현재 결과만 사용합니다.\n\n'
    for i,x in enumerate(slides,1):
        report+=f'## {i}. '+x['title'].replace('\n',' ')+'\n\n'+x['context']+'\n\n'+'\n\n'.join(x['body'])+'\n\n'
        if x['table']:report+='| '+' | '.join(x['table'][0])+' |\n|'+'---|'*len(x['table'][0])+'\n'+'\n'.join('| '+' | '.join(str(a).replace('\n',' / ')for a in row)+' |'for row in x['table'][1:])+'\n\n'
        report+=x['note']+'\n\n'
        if x['sources']: report+='출처: '+'; '.join(x['sources'])+'\n\n'
    report+='## 제품별 검증 상세\n\n|제품|합친 학습 Validation Recall/FPR|제품만 학습 Validation Recall/FPR|선택|Test 판단|\n|---|---|---|---|---|\n'
    for x in mg['comparison']['products']:
        a,z=[v['validation']for v in x['candidates']];report+=f'|{x["product"]}|{pct(a["recall"])}/{pct(a["fpr"])}|{pct(z["recall"])}/{pct(z["fpr"])}|{x["selected_strategy"]}|{x["recommendation"]}|\n'
    report+='\n새 데이터의 학습 범위 비교이며 과거 파일을 자동 병합하지 않습니다. 기존 모델·판정값을 고정해 새 학습 구간에서 점검하고 Test는 재학습 필요 판단에 사용하지 않습니다. 성능 저하 배치는 새 합성3,840행·480lot이며 실제 공정 변화 실측이 아닙니다.\n\n원본 SECOM 수치 센서는590열이고 UCI 메타데이터는591 features라고 표기합니다. pass=-1은 정상0, fail=1은 불량1로 변환했습니다. 제품ID·제조사명을 제공하지 않습니다. CC BY4.0, McCann & Johnston(2008), DOI10.24432/C54305입니다.\n\n교육 근거 검색 평가는14개 요약문과 고정13질의의 작은 자체 평가입니다. 새 외부 모델 검색의 품질 평가와 구분합니다. 검색 방식 간 결과는 agent_integration.json을 참조하며 일반 검색 성능 개선을 보장하지 않습니다. LLM 검사 실패는 규칙 설명으로 처리합니다. 운영 자동 배포, 수율·금액 이익, 공정조건 수율 예측, NLP·시계열·SEM 길이, 임의 외부 모델 코드 자동 생성과 혼합 비율 탐색은 검증된 실행 기능이 아닙니다. 공식 문서 기반 ExtraTrees·GaussianNB 발굴·실험은 구현했습니다. Docker/Kubernetes 예시는 실배포 미검증이며 기업 인증·권한·worker·모델 registry가 필요합니다.\n'
    (ROOT/'docs/REPORT.md').write_text(report)
    result_table='|자료|Test 불량 발견|정상 오판|Recall|Precision|F1|\n|---|---:|---:|---:|---:|---:|\n'
    for n,x in rr.items():q=x['test'];result_table+=f'|{labels[n]}|{q["tp"]}/{q["positive_count"]}|{q["fp"]}/{q["fp"]+q["tn"]}|{pct(q["recall"])}|{pct(q["precision"])}|{pct(q["f1"])}|\n'
    readme=f'''# 반도체 검사 모델 실험 도우미

G045 김용찬 · SK AI Leader Academy · 과제2

데이터를 점검해 전처리·모델·제품 학습 범위를 제안하고, 엔지니어 승인 후 실제 학습합니다. Recall을 우선 확인하고 Precision·F1·정상 오판도 설명합니다. 새 데이터로 같은 제품의 기존 모델을 점검하고 승인받아 재학습을 비교합니다.

[최종 제출 Slides](https://docs.google.com/presentation/d/1J2m_cpXyvb-5_Xabs2DsD3EnEV6B6GicF5OP2s5FohU/edit) · [5분 대본](docs/발표대본_G045.txt) · [보고서](docs/REPORT.md) · [교육 모델](docs/CURRICULUM_MODELS.md) · [요구사항 대응표](docs/ASSIGNMENT_CHECKLIST.md)

![같은 Test의 비교 결과](docs/assets/app-result.jpg)

## Mac에서 앱 켜기

1. Finder에서 Semiconductor-AI-Agent 폴더를 엽니다.
2. **start.command를 더블클릭**합니다.
3. 글자가 나오는 터미널 창을 열어 둔 채 **http://localhost:8700**을 엽니다.

localhost는 내 컴퓨터의 앱 주소입니다. 재부팅하면 앱도 꺼지므로 다시 켭니다. 터미널을 닫으면 앱이 종료됩니다. 터미널 명령은 `bash start.sh`입니다. Python3.11 이상이 필요하고 최초 실행에 의존성을 설치합니다. macOS XGBoost·LightGBM은 `brew install libomp`가 필요합니다.

start.command는 설치된 Ollama를 연결합니다. qwen3.5:2b·qwen3-embedding:0.6b가 있으면 로컬 LLM·임베딩을 사용할 수 있습니다. bash start.sh 기본은 규칙·TF-IDF이며 `SEMI_LLM_ENABLED=1 bash start.sh`로 LLM을 켭니다. 실제 모드는 /health와 화면에 표시합니다.

## 6:2:2로 다시 확인한 결과

합성 센서는 **Train768 / Validation256 / Test256개**입니다. 같은 생산 묶음(lot)은 구간을 넘지 않습니다. SECOM은 날짜 블록60/20/20이므로 행 수는 **{rr['secom']['split']['train']['rows']} / {rr['secom']['split']['validation']['rows']} / {rr['secom']['split']['test']['rows']}개**입니다. 비율을 점수에 맞춰 자동 조정하지 않습니다. 이전 분할의 이력은 보존하지만 현재 화면의 예시 결과는6:2:2 버전만 선택합니다.

{result_table}
최초 센서 후보 **{candidate}**: 불량{b['tp']}/{pos}개에서{t['tp']}/{pos}개 발견, 정상 오판{b['fp']}개에서{t['fp']}개. {initial_conclusion}. 선택 후보는 전체 Train768개 중 해당 제품의 **{w['train_n']}개**를 학습했습니다.

재학습은 새 합성 배치의 같은 Test에서 불량{old['tp']}/{old['positive_count']}개에서{new['tp']}/{new['positive_count']}개, 정상 오판{old['fp']}개에서{new['fp']}개. {retrain_conclusion}. 운영 모델은 자동 교체하지 않습니다.

90% Recall·15% 정상 오판·Test 불량20개는 시연 목표이며 회사 양산 기준이 아닙니다. 정상 오판은 FP이며 재검사·폐기를 의미하지 않습니다. 제조 수율과 금액 이득, 실제 작업 시간 절감은 측정하지 않았습니다.

## 데이터와 모델

A·B·C·D는 합성 데이터의 가상 제품명입니다. UCI SECOM은 반도체 공정 센서와 합격/불합격 기록1,567건·불합격104건입니다. 제조사명은 원자료에 제공하지 않으며 같은 이름의 경비회사와 연결할 근거는 확인하지 못했습니다. McCann & Johnston(2008), [UCI 원본]({uci}), [DOI10.24432/C54305]({doi}), CC BY4.0. 숫자 센서 원파일590열과 공식 메타데이터591 features 표기를 구분합니다.

센서12종: Logistic, Decision Tree, RF, GB, XGBoost, LightGBM, CatBoost, KNN, SVM, MLP, AdaBoost, HistGB. 전체 제품12종×불균형2조건을 비교한 뒤 상위2알고리즘의 제품 조합을 확장해 최대52조건입니다. 완전탐색이 아닙니다. 이미지3종은 축소 ResNet·VGGNet·Autoencoder를 처음부터 학습하며 실제 SEM 이미지가 아닙니다.

## Agent와 재현

LangGraph 점검·계획·결과 검토, 로컬 Qwen,교육 근거14개와 실시간 공식 외부 문서 검색 RAG,4 MCP 도구, Store·Knowledge·Advisor 의존성 주입, 모듈화를 구현했습니다. 30개 단위/API 테스트와 MCP 실제 연결 기록은 docs/evaluation에 있습니다. LLM 수치를 신뢰하지 않고 실험 엔진이 계산합니다. 실패하면 규칙 설명을 사용합니다. 원격 추적 기능은 제출의 완성 기능에서 제외했습니다.

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/evaluate.py
.venv/bin/python scripts/evaluate_management.py
.venv/bin/python scripts/evaluate_agents.py
.venv/bin/python scripts/check_mcp.py
.venv/bin/python scripts/build_report.py
```

평가 승인은 자동 테스트 actor이며 현장 승인 실적이 아닙니다. 계획·데이터·분할 hash와 seed45를 저장합니다. 전처리·가중치는 Train에서만 fit합니다. 반복 Validation 선택과 작은 표본이 한계입니다. 기업 클라우드는 인증·권한·학습 worker·중앙 모델 관리가 추가로 필요하고 배포 예시는 실배포 미검증입니다. 공식 외부 모델 검색·RAG 제안·승인 후 학습·후보 목록 갱신을 구현했습니다. 현재 센서 ExtraTrees·GaussianNB 연결을 지원하며 임의 코드 자동 생성과 혼합 비율 탐색은 확장 범위입니다. [구현 범위](docs/MODEL_DISCOVERY_DESIGN.md) 교육 원본 전체·제출 명단 엑셀·비밀 값은 공개 저장소에 넣지 않습니다. 사용자가 요청한 교육 사진의 데이터 유형 분류 내용을 표로 재구성했습니다.
'''
    (ROOT/'README.md').write_text(readme)
    demo=f'''# 발표와 앱 실행

본 발표는1~10장, 부록은11~16장입니다. TXT 대본은275초 계획이며 화면 전환 여유25초를 남겼습니다. 줌에서는 슬라이드의 실제 화면 캡처를 공유해 설명하고 새 학습을 기다릴 필요는 없습니다.

1. start.command를 더블클릭하고 터미널 창을 열어 둔 채 http://localhost:8700을 엽니다. 재부팅하면 다시 켭니다.
2. 제품 A–D 합성 센서를 선택하고 “비교 계획 제안받기”를 누릅니다.
3. Train768·Validation256·Test256, 전처리 이유와12모델·최대52조건을 확인합니다. 승인 전에는 학습하지 않습니다.
4. 승인 후 실제 학습합니다. 현재 완료 이력은6:2:2 버전만 화면에서 선택합니다.
5. 같은 Test에서 불량{b['tp']}개와{t['tp']}개, 정상 오판{b['fp']}개와{t['fp']}개를 비교합니다. 결론은 {initial_conclusion}입니다.
6. 추가 상황으로 새 합성 배치에서 기존 모델을 점검하고 승인 뒤 같은 알고리즘 재학습을 비교합니다. 불량{old['tp']}개와{new['tp']}개, 정상 오판{old['fp']}개와{new['fp']}개입니다.
7. C의 합친 학습/개별 학습을 같은 Validation에서 비교하고 Test로 확인합니다.
8. 공개 UCI SECOM의 출처와 부족한 성능, 합성 이미지의 작은 불량 표본을 설명합니다.

새 설치에는 완료 이력이 없어 먼저 계획을 승인해 학습해야 합니다. 학습 시간은 기기마다 다릅니다. 운영 모델을 자동 교체하지 않습니다. 원래 서버 창을 닫으면 앱도 종료됩니다.
'''
    (ROOT/'docs/DEMO.md').write_text(demo)
if __name__=='__main__':main()
