"""Build plain-language report and slide content from measured receipts."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
import sys
sys.path.insert(0,str(ROOT))
from app.catalog import TABULAR,IMAGE
NAMES={k:v[0] for k,v in {**TABULAR,**IMAGE}.items()}
pct=lambda x:f'{x*100:.1f}%'
def main():
    saved={n:json.loads((ROOT/f'docs/evaluation/{n}.json').read_text()) for n in ['synthetic_process','secom','images']}
    rr={n:x['result'] for n,x in saved.items()};r=rr['synthetic_process'];w=r['winner'];v=w['validation'];t=r['test'];b=r['baseline_test']
    mg=json.loads((ROOT/'docs/evaluation/model_management.json').read_text());m=mg['comparison']['same_model_retraining'];old,new=m['before'],m['after']
    sk='https://news.skhynix.com/en/the-past-present-and-future-of-data-science-organization-at-sk-hynix/'
    uci='https://archive.ics.uci.edu/dataset/179/secom'
    notes=[]
    slides=[]
    def add(context,title,body,table=None,note='',source=None):
        slides.append(dict(context=context,title=title,body=body,table=table,note=note.strip(),sources=source or []))
    add('프로젝트 소개','반도체 불량 판정 모델\n선택·재학습 Agent',['어떤 모델을 고르고, 언제 다시 학습할지 엔지니어에게 제안합니다.','G045 김용찬 · SK AI Leader Academy · 과제 2'],note='안녕하세요. G045 김용찬입니다. 반도체 불량 판정에 어떤 모델을 사용할지, 성능이 떨어지면 언제 다시 학습할지를 도와주는 Agent를 만들었습니다. 엔지니어가 계획을 확인하고 승인하면 실제 학습을 실행합니다.')
    add('현장 문제 · 모델을 만든 뒤에도 관리가 필요합니다','엔지니어가 결정해야 할 세 가지',['1  처음 쓸 모델: 데이터에 맞는 전처리와 모델은?','2  기존 제품: 새 데이터에서도 불량을 잘 잡는가?','3  여러 제품: 합쳐 학습할까, 제품마다 따로 학습할까?'],note='처음에는 여러 모델 중 하나를 골라야 합니다. 이후 공정이나 데이터가 바뀌면 기존 모델의 성능을 확인해야 하고, 제품 데이터를 합칠지도 결정해야 합니다. SK하이닉스의 공개 사례에서도 검사 AI의 성능 감시와 성능 저하 후 복구, 새로운 결함 학습이 운영 과제로 나옵니다. 이 프로젝트는 이 결정을 돕는 교육용 구현입니다.',source=[sk])
    add('평가 기준 · 불량을 Positive로 정의합니다','Recall이 우선, Precision·F1도 함께 확인',['Recall 90%: 실제 불량 10개 중 9개를 발견','Precision 75%: 잡힌 12개 중 진짜 불량 9개','F1 81.8%: Precision과 Recall을 함께 반영'],[['설명용 예시','불량으로 판정','정상으로 판정'],['실제 불량 10개','TP 9개 · 잘 잡음','FN 1개 · 놓침'],['실제 정상 90개','FP 3개 · 정상 오판','TN 87개 · 정상 통과']],note='여기서는 불량을 Positive로 정합니다. 중요한 오류는 실제 불량을 정상으로 놓치는 FN입니다. Recall은 실제 불량 중 얼마나 잡았는지입니다. 예를 들어 불량 열 개 중 아홉 개를 잡으면 90퍼센트입니다. 그런데 잡힌 열두 개 중 진짜 불량이 아홉 개라면 Precision은 75퍼센트입니다. F1은 두 지표를 함께 반영합니다. 전부 불량으로 판정하면 Recall만 높아질 수 있으므로 정상 오판도 확인합니다. F1만으로 순위를 정하지는 않습니다.',source=['스칼라 12주차 데이터분석 Mini Project 박병선p PDF 15쪽','https://scikit-learn.org/stable/modules/generated/sklearn.metrics.f1_score.html'])
    add('상황 1 · 정상/불량 정답이 있는 데이터를 받았습니다','데이터 종류에 맞춰 전처리와 모델을 제안',['센서 12종: Logistic·Tree·RF·GB·XGBoost·LightGBM·CatBoost·KNN·SVM·MLP·AdaBoost·HistGB','A·B·C·D는 합성 데이터의 가상 제품명입니다.'],[['입력','전처리와 이유','실제 비교 후보'],['숫자 공정 센서','결측 대체·상수 제거\n거리·신경망 모델은 Scaling','교육 기반 센서 모델 12종'],['검사 이미지','흑백 32×32·0~1 Scaling\n대비 보정도 비교','축소 ResNet·VGGNet\nAutoencoder']],note='입력은 두 종류입니다. 센서는 빈 값을 학습 데이터의 중앙값으로 채우고 상수 열을 제거합니다. KNN이나 SVM처럼 단위 차이에 민감한 모델에는 Scaling을 적용합니다. 트리는 기본 설정에서 Scaling을 생략합니다. 불량이 부족하면 학습 데이터 안에서만 가중치나 복제를 비교합니다. 모델은 스칼라 Day1, 2, 3과 반도체 교육자료에서 고른 센서 열두 종과 축소 이미지 세 종류입니다. 로그나 시계열 모델은 입력이 달라 이번 센서 모델과 무조건 경쟁시키지 않았습니다.',source=['SKALA 머신러닝 및 딥러닝 이해 Day1 PDF 51,59~75쪽 / Day2 21~42쪽 / Day3 7~22,68,74쪽','반도체 참고 사진 20261017_135247, 144839 / DRAM NAND 발표 PDF 40~42쪽','https://scikit-learn.org/stable/modules/preprocessing.html'])
    add('상황 1 · 학습을 실행하기 전입니다','계획을 승인받고 학습·검증·마지막 확인',['Agent 제안 → 엔지니어 승인 → 실제 학습 → 결과 설명','최대 52조건 비교: 모델 12종 비교 후 상위 2종의 제품 조합 확장'],[['데이터 구간','하는 일','이번 합성 센서 예시'],['학습 Train','모델·전처리 학습','896개'],['비교·검증 Validation','판정 경계값과 후보 선택','192개'],['마지막 확인 Test','고른 후보를 처음 보는 데이터로 확인','192개']],note='먼저 Agent가 데이터 문제와 비교 계획, 근거를 보여 줍니다. 승인하기 전에는 학습하지 않습니다. 데이터를 학습, Validation, Test 세 구간으로 나눕니다. Validation은 학습이 잘 됐는지 검증하고 후보와 판정 경계값을 비교하는 데 사용합니다. Test는 후보를 고르는 데 쓰지 않고 마지막 확인에 남겨 둡니다. 같은 lot이 다른 구간에 섞이지 않게 했습니다. 전체 제품에서 모든 모델을 먼저 비교하고 상위 두 알고리즘만 제품 조합을 확장하기 때문에 완전탐색은 아닙니다.',source=['app/data.py','app/experiments.py','https://scikit-learn.org/stable/modules/classification_threshold.html'])
    add('상황 1 · 합성 센서 데이터에서 후보를 골랐습니다','불량은 더 찾았지만, 목표에는 아직 못 미침',[f"후보: {NAMES[w['model']]} · 학습 제품 {'+'.join(w['products'])}",f"Validation에서는 불량 {v['tp']}/{v['positive_count']}개 발견 → Test에서는 {t['tp']}/{t['positive_count']}개 발견",'데모 목표 Recall 90%에 Test 76%가 못 미쳐 후보 재검토'],[['동일 Test 192개','기본 Logistic','고른 후보'],['실제 불량 25개 중 발견',f"{b['tp']}개 ({pct(b['recall'])})",f"{t['tp']}개 ({pct(t['recall'])})"],['놓친 불량',f"{b['fn']}개",f"{t['fn']}개"],['정상 167개 중 불량으로 오판',f"{b['fp']}개 ({pct(b['fpr'])})",f"{t['fp']}개 ({pct(t['fpr'])})"]],note=f"합성 센서의 실제 결과입니다. Validation으로 고른 후보는 {NAMES[w['model']]}이고 학습 제품은 {'+'.join(w['products'])}입니다. 같은 Test에서 기본 모델은 불량 25개 중 {b['tp']}개, 후보는 {t['tp']}개를 발견했습니다. 대신 정상 오판은 {b['fp']}개에서 {t['fp']}개로 늘었습니다. Validation에서는 불량 34개를 모두 찾았어도 다른 Test에서는 19개만 찾을 수 있습니다. 그래서 후보로 골랐다는 말과 적용을 승인한다는 말은 다릅니다. 여기서는 Recall 데모 목표 90퍼센트에 못 미쳐 재검토합니다. 90퍼센트와 정상 오판 15퍼센트는 회사 기준이 아닌 시연 기본값입니다.",source=['docs/evaluation/synthetic_process.json'])
    add('상황 2 · 같은 제품에 새 데이터가 들어왔습니다','기존 모델 점검 후, 승인받아 같은 알고리즘 재학습',['새 학습 구간에서 기존 모델·판정값을 고정해 제품별 점검 → 재학습 제안·승인','새 Test 576개에서 같은 알고리즘 비교: Recall 18.9% → 92.1%','정상 오판 15.1%는 데모 목표 15% 초과: 추가 확인 필요'],[['새 합성 Test · 불량 127 / 정상 449','기존 모델 그대로','같은 알고리즘 재학습'],['불량 발견',f"{old['tp']}개 ({pct(old['recall'])})",f"{new['tp']}개 ({pct(new['recall'])})"],['놓친 불량',f"{old['fn']}개",f"{new['fn']}개"],['정상 오판',f"{old['fp']}개 ({pct(old['fpr'])})",f"{new['fp']}개 ({pct(new['fpr'])})"]],note='이번에는 공정이 바뀌었다고 가정해 불량 발생 규칙을 바꾼 새 합성 데이터를 넣었습니다. 기존 모델과 판정값을 그대로 두고 같은 제품별로 점검합니다. 성능이 부족하면 재학습을 제안합니다. 승인 뒤 같은 CatBoost 알고리즘을 새 데이터로 다시 학습했습니다. 새 배치의 같은 Test에서 불량 발견은 24개에서 117개로 늘었고 놓친 불량은 103개에서 10개로 줄었습니다. 정상 오판은 70개에서 68개입니다. 다만 정상 오판률 15.1퍼센트가 시연 목표 15퍼센트를 조금 넘으므로 바로 적용한다고 말하지 않습니다. 기존 모델을 운영 중이라고 가정한 모의 검증이며 실제 공정 변화 실측이 아닙니다.',source=['docs/evaluation/model_management.json'])
    cr=next(x for x in mg['comparison']['products'] if x['product']=='C');a,z=[x['validation'] for x in cr['candidates']];chosen=next(x for x in cr['candidates'] if x['strategy']==cr['selected_strategy'])
    add('상황 3 · 제품 C의 학습 범위를 결정합니다','여러 제품을 합칠까, C만 따로 학습할까?',['같은 C 제품의 Validation 데이터로 비교합니다.','C만 학습한 후보가 데모 목표를 만족해 선택됐습니다.',f"그러나 C의 Test 검출률은 {pct(chosen['test']['recall'])} → 추가 데이터로 재확인"],[['C에서 비교한 학습 방식','불량 검출률','정상 오판률'],['A+B+C+D를 합쳐 학습',pct(a['recall']),pct(a['fpr'])],['C 제품만 따로 학습',pct(z['recall']),pct(z['fpr'])]],note='여기서 공통 권고나 전용 권고라는 말은 쓰지 않겠습니다. 새 데이터의 A B C D를 모두 합쳐 학습하는 방법과 C만 학습하는 방법을 비교한 것입니다. 같은 C의 Validation에서 C만 학습한 후보가 검출률 96.2퍼센트, 정상 오판률 13.8퍼센트로 데모 목표를 만족했습니다. 하지만 별도 Test의 검출률은 86.1퍼센트여서 다시 확인해야 합니다. 제품마다 결과가 다르므로 제품별 학습이 항상 좋다고 결론 내리지 않습니다. 새 배치 안의 학습 범위를 비교한 것이며 과거 데이터를 자동 병합하는 기능은 아닙니다.',source=['docs/evaluation/model_management.json'])
    sc,im=rr['secom'],rr['images']
    add('검증 · 합성 데이터만 잘 되는지 확인합니다','실제 공개 반도체 센서에서도 실패를 확인',['SECOM: UCI가 공개한 반도체 제조 공정 센서·합격/불합격 데이터','1,567건 · 센서 590열 · 불량 104건 · 실제 제품 A–D 정보 없음','검사 이미지는 별도의 합성 패턴이며 실제 SEM 이미지가 아닙니다.'],[['독립 Test 결과','불량 발견','정상 오판','해석'],['실제 공개 센서 SECOM',f"{sc['test']['tp']}/{sc['test']['positive_count']}개",f"{sc['test']['fp']}/{sc['test']['tn']+sc['test']['fp']}개",'데모 목표 미달'],['합성 이미지',f"{im['test']['tp']}/{im['test']['positive_count']}개",f"{im['test']['fp']}/{im['test']['tn']+im['test']['fp']}개",'검출률·표본 부족']],note='SECOM은 UCI가 공개한 반도체 공정 데이터셋의 이름입니다. 공정 센서와 합격 불합격 결과가 있고 2008년에 공개됐습니다. 실제 특정 회사의 현재 데이터라고 말할 수는 없습니다. 제품 A B C D 구분도 없어서 이 실험은 단일 제품으로 평가했습니다. 최종 Test에서 불량 15개 중 6개만 발견하고 정상 249개 중 73개를 오판했습니다. 합성 이미지도 불량 14개 중 6개를 발견했습니다. 정상 오판이 없어도 불량을 놓치면 좋은 모델이라고 할 수 없습니다. 실패도 그대로 기록하고 추천을 보류하는 것이 이 Agent의 역할입니다.',source=[uci,'docs/evaluation/secom.json','docs/evaluation/images.json'])
    add('시연 · 엔지니어가 보는 화면','계획의 이유와 판정 건수를 한 화면에서',['1  데이터 선택 → 완료된 결과 확인','2  새 실험 계획의 전처리·모델 근거 확인 → 승인','3  새 데이터로 점검 → 재학습 계획 승인'],note='화면에서는 먼저 연습용 센서 데이터를 고르고 완료된 결과를 보겠습니다. 불량 몇 개를 찾고 몇 개를 놓쳤는지부터 읽을 수 있습니다. 새 계획에서는 왜 Scaling이나 가중치를 쓰는지 확인하고 승인할 수 있습니다. 다음으로 새 데이터에서 기존 모델을 점검하고 재학습 계획을 받습니다. 로컬 주소는 localhost 8700입니다. 컴퓨터를 재부팅하면 프로젝트 폴더의 start.command를 실행해 서버를 켭니다.')
    add('구현 · Agent가 하는 일과 엔지니어의 역할','설명·계획은 Agent, 실행은 승인 뒤에',['데이터 점검 Agent → 근거 검색 → 실험 계획 Agent → 승인 → 학습 → 결과 검토 Agent','로컬 LLM: 허용된 판단 코드와 출처를 검사하고 실패하면 규칙 설명 사용','실험 엔진: 학습·지표 계산·파일 저장 · 운영 모델 자동 교체 없음'],[['평가항목','실제 구현·확인'],['Multi-Agent · RAG','LangGraph 역할 분리 · 요약 근거 14개 검색'],['MCP · 의존성 주입 · 모듈화','MCP 4도구 실제 연결 · 공통 Workbench 재사용'],['단위/API 테스트','26개 테스트 통과']],note='Agent 역할은 데이터 품질 점검, 계획 제안, 결과 검토로 나눴습니다. 근거 검색은 교육 내용을 요약한 문서와 공개 자료를 사용합니다. 로컬 Qwen을 실제 호출하고 허용한 판단과 검색 출처를 검사합니다. 품질 점검과 계획 역할은 통과했고 결과 검토 역할은 응답 검사에 실패해 규칙 설명을 사용했습니다. 수치는 LLM이 만들어내지 않고 실험 엔진이 계산합니다. MCP 네 도구와 의존성 주입, 모듈화, 테스트를 구현했습니다. ',source=['docs/evaluation/agent_integration.json','docs/evaluation/mcp_check.json','docs/evaluation/tests.txt'])
    add('결론 · 회사 도입과 미니프로젝트의 범위를 구분합니다','모델 선택과 재학습을 돕는 주제로 완성',['핵심: 불량을 놓치지 않도록 Recall 우선, Precision·F1·정상 오판 함께 확인','회사 기준: 공개 자료에서 공통 합격 수치를 확인하지 못함 → 제품·공정 담당자가 정의','현재 한계: 작은 불량 표본·합성 데이터·단일 분할·반복 Validation 비교','다음 단계: 독립 기간 검증·현장 데이터·인증/권한·중앙 모델 관리'],note='이 프로젝트의 주제는 수율 숫자를 바로 올리는 AI가 아니라 불량 판정 모델을 고르고 유지하는 엔지니어를 돕는 Agent입니다. Recall을 우선해 불량을 놓치는 일을 줄이고, Precision과 F1, 정상 오판도 함께 설명합니다. 회사 공통의 합격 수치는 공개 자료로 확인하지 못했습니다. 지금 설정은 시연 값이며 실제 도입에는 제품과 공정 담당자의 기준과 독립 기간 검증이 필요합니다. 현재 작은 표본과 합성 데이터, 반복 Validation 비교가 한계입니다. 기업용 클라우드 확장 구조는 제공하지만 실제 배포나 생산 적용을 검증한 것은 아닙니다. 감사합니다.',source=[sk,'https://research.skhynix.com/research-areas/semiconductor-Infrastructure-technology/advanced-metrology-inspection'])
    labels={'synthetic_process':'합성 센서','secom':'공개 반도체 센서 SECOM','images':'합성 이미지'}
    rows=[['Test 상세 · 선택 후보','Recall','Precision','F1','정상 오판률']]
    for n,x in rr.items(): rows.append([labels[n],*[pct(x['test'][k]) for k in ['recall','precision','f1','fpr']]])
    add('부록 · 지표와 비교 방식의 한계','상세 지표와 재현 조건',['순위: 데모 목표를 만족한 후보 중 Recall 우선, 동률이면 정상 오판이 적은 후보','F1은 보조 지표이며 순위 선정에 사용하지 않았습니다.','단일 seed 45 · 같은 lot 분리 · SECOM은 날짜 순서 분리','제품별 작은 표본·Validation 반복 사용으로 결과가 낙관적일 수 있습니다.'],rows,note='필요할 때 보여 줄 부록입니다. Recall은 TP 나누기 TP 더하기 FN, Precision은 TP 나누기 TP 더하기 FP입니다. F1은 2TP 나누기 2TP 더하기 FP 더하기 FN입니다. 정상 오판률은 FP 나누기 FP 더하기 TN입니다. 목표 충족 후보가 없으면 목표와의 차이가 작은 참고 후보만 표시하며 적용 추천이 아닙니다. 완전 동률의 결정 규칙은 trial ID이며 제품 학습 방식 완전 동률은 관리할 모델이 적은 합친 학습입니다. test는 순위 선택에 쓰지 않습니다. 결과는 데이터와 모델뿐 아니라 전처리, 학습 범위, 가중치, 판정 경계값을 포함한 절차 비교입니다.',source=['docs/evaluation/summary.json','app/metrics.py','app/monitoring.py'])
    add('부록 · 기술 요소와 구현 위치','기술 요소가 반영된 위치',['코드·실행 증빙의 자세한 연결: docs/ASSIGNMENT_CHECKLIST.md'],[['기술 요소','구현 위치','확인 상태'],['Multi-Agent','planner.py · advisors.py','점검·계획·결과 검토 역할'],['RAG','Knowledge · knowledge.json','근거 검색·출처 연결'],['MCP','mcp_server.py','4도구·지식 resource 실제 연결'],['의존성 주입','Dependencies · Workbench','Store·Knowledge·Advisor 주입'],['모듈화','app/ 데이터·학습·관리 모듈','API·MCP가 공통 엔진 재사용'],['단위/API 테스트','tests/','26개 테스트 통과']],note='기술 요소가 어디에 반영됐는지 연결한 부록입니다. Multi-Agent는 품질 점검과 계획, 결과 검토 역할입니다. RAG는 근거 요약문 검색과 출처 연결에 사용합니다. MCP는 네 도구와 지식 resource를 제공하고 실제 연결을 검증했습니다. 의존성 주입으로 Store와 Knowledge, Advisor를 바꿔 사용할 수 있습니다. 데이터와 학습, 모델 관리, 접속을 모듈로 나누고 스물여섯 개 테스트를 통과했습니다. 구현 위치와 실행 기록은 체크리스트 문서에 연결했습니다.',source=['docs/ASSIGNMENT_CHECKLIST.md','docs/evaluation/agent_integration.json','docs/evaluation/mcp_check.json','docs/evaluation/tests.txt'])
    (ROOT/'docs/slide-content.json').write_text(json.dumps(slides,ensure_ascii=False,indent=2))
    script='G045 김용찬 / 과제 2 / 반도체 불량 판정 모델 선택·재학습 Agent\n2026-10-21 수정본\n본 발표 1~12장 약 6분, 13~14장은 질문용 부록입니다.\n\n'
    for i,s in enumerate(slides,1): script+=f"[{i}장] {s['title'].replace(chr(10),' ')}\n{s['note']}\n\n"
    script+='질문 대비\nQ. 재학습이 왜 필요한가요?\nA. 같은 제품이라도 공정·장비·재료·데이터가 달라지면 기존 모델의 성능이 달라질 수 있습니다. 기존 모델과 판정값을 고정해 새 정답 데이터에서 점검하고, 부족할 때 승인받아 재학습을 비교합니다. 점검만으로 변화의 원인을 확정하지는 않습니다.\n\nQ. 왜 고른 모델을 바로 적용하지 않나요?\nA. Validation에서 고른 후보가 별도 Test나 회사 기준까지 만족한다는 보장은 없기 때문입니다. 후보 선정, 마지막 확인, 회사 적용 승인은 다른 단계입니다.\n\nQ. 15%는 회사 기준인가요?\nA. 아닙니다. 90% 검출률, 15% 정상 오판률, Test 불량20개는 시연용 기본값입니다. 회사 공통 수치를 공개 자료에서 확인하지 못했습니다. 제품·공정 담당자가 별도 기준을 정해야 합니다.\n\nQ. 기업 클라우드에서도 쓰나요?\nA. API·MCP·분석 엔진을 분리한 확장 예시는 있지만 실배포는 검증하지 않았습니다. 조직 인증과 권한, 데이터 연결, 학습 worker·모델 registry가 추가로 필요합니다.\n\nQ. 외부 모델을 검색해 스스로 목록을 갱신하나요?\nA. 현재는 확장 설계입니다. 실제 실행한 교육 모델 비교와 구분해 설명합니다.\n'
    script+='Q. 앙상블 비율도 비교하나요?\nA. RF·부스팅 자체는 앙상블이지만 서로 다른 모델의 예측을 섞는 가중치 탐색은 아직 미구현입니다. 확장 시 Validation에서 후보 비율을 비교하고 고정된 Test에서 단일 모델과 확인합니다. 최적은 실험한 후보 안의 최선이라는 뜻입니다.\n\nQ. 학습/Validation/Test는 꼭6:2:2인가요?\nA. 정해진 비율은 없습니다. 현재 합성 예시는7:1.5:1.5이며 같은 lot을 섞지 않습니다. SECOM은 날짜 블록 기준이라 행 비율은 달라집니다. Test를 고정하고 불량 표본 수와 시간·lot 경계를 먼저 확인합니다. 점수를 높이려고 분할을 반복해서 바꿨다고 설명하지 않습니다.\n'
    (ROOT/'docs/발표대본_G045.txt').write_text(script)
    results='| 데이터 | Test 불량 발견 | 정상 오판 | Recall | Precision | F1 |\n|---|---:|---:|---:|---:|---:|\n'
    for n,x in rr.items(): q=x['test'];results+=f"| {labels[n]} | {q['tp']}/{q['positive_count']} | {q['fp']}/{q['fp']+q['tn']} | {pct(q['recall'])} | {pct(q['precision'])} | {pct(q['f1'])} |\n"
    report='# 반도체 불량 판정 모델 선택·재학습 Agent\n\nG045 김용찬 · SK AI Leader Academy · 과제 2 · 2026-10-21\n\n'
    for i,s in enumerate(slides,1):
        report+=f"## {i}. {s['title'].replace(chr(10),' ')}\n\n상황: {s['context']}\n\n"+'\n\n'.join(s['body'])+'\n\n'
        if s['table']:report+='| '+' | '.join(s['table'][0])+' |\n|'+'---|'*len(s['table'][0])+'\n'+'\n'.join('| '+' | '.join(str(c).replace('\n',' / ') for c in row)+' |' for row in s['table'][1:])+'\n\n'
        report+=s['note']+'\n\n'
        if s['sources']:report+='출처: '+'; '.join(s['sources'])+'\n\n'
    report+='## 제품별 학습 방식 상세\n\n| 제품 | 합친 학습 Validation Recall / 정상 오판 | 개별 학습 Validation Recall / 정상 오판 | Validation 선택 | 마지막 확인 |\n|---|---|---|---|---|\n'
    for row in mg['comparison']['products']:
        x,y=[c['validation'] for c in row['candidates']];report+=f"| {row['product']} | {pct(x['recall'])} / {pct(x['fpr'])} | {pct(y['recall'])} / {pct(y['fpr'])} | {'합쳐 학습' if row['selected_strategy']=='shared' else '이 제품만 학습'} | {row['recommendation']} |\n"
    report+='\n제품별 Validation/Test는 같은 표본으로 고정했습니다. 과거 파일을 자동 병합하지 않습니다. 두 방식의 Validation이 모두 목표 미달이면 참고 후보만 표시합니다. Test가 좋아도 이 선택 실패를 지우지 않습니다. 새 제품의 초기 모델 개발과 같은 제품의 성능 저하 후 재학습을 구분합니다.\n\n'
    report+='## 재현과 기술 검증\n\n14개 근거 요약문을 검색하며 고정 13개 질의에서 TF-IDF와 dense 검색 Hit@3는 둘 다100%, MRR@3는 둘 다0.9615였습니다. 이 작은 자체 평가에서는 dense의 검색 품질 개선을 확인하지 못했습니다. 실제 입력·실행 상태는 evaluation/agent_integration.json에 있습니다. 문서 cache 변경과 성능 수치를 숨기지 않습니다. LLM 출력은 허용 코드·출처 연결 검사이며 자유 추론 사실성의 검증은 아닙니다.\n\nMCP stdio 실제 연결과 4도구·resource를 검증했습니다. DI는 Store·Knowledge·Advisor를 주입하며 API·MCP에서 Workbench를 재사용합니다. 26개 테스트는 승인 hash·단일 승인·미승인 실행 방지·분할·학습 전용 전처리·정확한 지표·API 인증·SSE·CSV·재학습 버전·Validation만으로 방식 선택을 확인합니다.\n\n기본 센서 모델은 전체 학습 제품의 Logistic Regression, 가중치 없음, 중앙값 대체·Scaling, 기본 판정값0.5입니다. 이미지 기본 모델은 첫 지도학습 후보(이번 ResNetSmall gray), 기본 판정값0.5입니다. After는 전처리·가중치·판정값·제품 범위를 포함한 절차 비교입니다.\n\nSECOM은 원본 pass=-1을 정상0, fail=1을 불량1로 변환했습니다. 다운로드 파일의 숫자 센서 열은590개이며 공식 웹 메타데이터의 feature count591 표기와 구분합니다. 제품 ID가 없으므로 단일 SECOM 집단입니다. 이름의 약어를 임의로 확장하지 않고 반도체 제조 센서·검사 결과 데이터로 설명합니다. CC BY4.0, McCann & Johnston(2008), DOI10.24432/C54305입니다.\n\n합성 센서는1,280행·불량201·160lot, 합성 이미지는576장·불량85·96lot입니다. 새 성능 저하 배치는3,840행·480lot, seed1045로 불량 규칙을 바꿨습니다. 최초 데이터와 센서 중복을 차단하고 새 학습 구간에서만 기존 모델을 점검합니다. Test는 점검·선택에 쓰지 않습니다. 기존 제품별 기준 표본이 작으므로 10%p 하락 규칙은 통계 검정이 아닌 탐색적 점검입니다.\n\n외부 모델 자동 검색·adapter 생성·후보 목록 갱신, 장비 로그 NLP·시계열 예측·SEM 길이·공정조건 수율 예측은 실행 기능이 아닙니다. 확장 설계는 MODEL_DISCOVERY_DESIGN.md에 있습니다. Docker/Kubernetes 예시는 실배포 미검증입니다. SSO/RBAC·학습 queue·중앙 저장소·model registry가 필요합니다.\n\n교육 원본·사진·제출용 명단 엑셀·비밀 값은 공개 저장소에 넣지 않습니다.\n'
    (ROOT/'docs/REPORT.md').write_text(report)
    cur='# 교육자료와 실제 모델\n\n모델 명칭·위치를 확인한 교육자료의 요약이며 원본 PDF·사진은 재배포하지 않습니다. PDF 기준 쪽입니다.\n\n| 실제 센서 후보 | 기본 전처리 | 사용 이유 | 자료 위치 |\n|---|---|---|---|\n'
    for k,(title,prep,why,src) in TABULAR.items():cur+=f'| {title} | {"결측 대체·상수 제거·Scaling" if prep=="scaled" else "결측 대체·상수 제거"} | {why} | {src} |\n'
    cur+='\n자료명: 9주차 `2) 데이터분석 및 AIOps_4.머신러닝 및 딥러닝 이해_Day1,2,3_박병선p.pdf` 각 파일. 반도체 `DRAM, NAND 특성, 반도체 업에서 활용되는 AI, ML 기술 발표자료 (2).pdf` 40~42쪽. 참고 사진 `20261017_144839.jpg`의 NN·KNN·SVM·Tree 고장 분류.\n\n검사 이미지: 자체 축소 ResNet·VGGNet·Autoencoder를 실제 학습합니다. 참고 사진2의 `20261017_135247.jpg`와 Day3 PDF74쪽. GAN 생성 학습·BERT/GPT 로그 분류·LSTM/ARIMA 시계열 예측은 미구현입니다.\n\n지표: 12주차 `데이터분석 및 AIOps_7.데이터분석 Mini Project_박병선p.pdf` 15쪽에 Accuracy·Precision·Recall·F1 Score가 함께 제시됩니다. 이 프로젝트는 불량을 Positive로 정의해 Recall을 우선 비교하고 Precision·F1·정상 오판률도 보고합니다. F1은 2TP/(2TP+FP+FN)입니다.\n\nScaling은 전처리의 넓은 표현이며 이번 StandardScaler는 학습 평균·분산으로 단위를 맞추는 방식입니다. 학습 표본에서만 fit하고 Validation/Test에는 같은 변환만 적용합니다. 불량 가중치·복제도 학습 구간 안에서만 적용합니다.\n'
    (ROOT/'docs/CURRICULUM_MODELS.md').write_text(cur)
    readme=f'''# 반도체 불량 판정 모델 선택·재학습 Agent

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

제품 A·B·C·D는 **합성 데이터의 가상 제품명**입니다. 실제 공개 데이터인 **SECOM은 반도체 제조 센서·합격/불합격 기록**으로1,567건·센서590열·불량104건입니다. 실제 제품 A–D 정보가 없고 특정 회사의 현재 생산 데이터도 아닙니다. [UCI 공식 자료·CC BY4.0]({uci})

## 같은 Test에서 확인한 결과

{results}
합성 센서의 기본 Logistic은 불량25개 중17개, 후보 CatBoost(A+B+C 학습)는19개를 발견했습니다. 정상167개 중 오판은1개→8개입니다. 후보의 Recall76%가 데모 목표90%에 못 미쳐 재검토합니다. Validation에서 골랐다는 뜻이며 회사 적용 승인이 아닙니다.

새 합성 배치의 동일 Test에서 기존 CatBoost와 같은 알고리즘 재학습을 비교하면 불량127개 중24개→117개를 발견했습니다. 정상449개 중 오판은70개→68개입니다. 재학습 Recall92.1%, 정상 오판15.1%로 데모 목표 중 정상 오판 목표를 넘습니다. 같은 제품별로 합쳐 학습/따로 학습한 방법도 비교하고 후보 파일·버전을 저장합니다. 운영 모델은 자동 교체하지 않습니다.

## 회사 기준과 데모 목표

**90% Recall·15% 정상 오판·Test 불량20개는 교육용 기본값이며 회사 양산 기준이 아닙니다.** 공개 회사 자료에서 모든 제품에 통용되는 수치 기준은 확인하지 못했습니다. 실제 도입에는 제품·공정·결함별 품질 요구와 담당자가 정한 독립 검증 기준이 필요합니다. [SK하이닉스 검사 AI 성능 감시·학습 사례]({sk})

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
'''
    (ROOT/'README.md').write_text(readme)
    (ROOT/'docs/DEMO.md').write_text('''# 발표 시연 순서

1. 프로젝트 폴더의 start.command 실행 후 http://localhost:8700 접속. 재부팅하면 다시 실행합니다.
2. 합성 제품 A–D 센서 선택 → 완료된 결과 보기. 같은 Test192개에서 불량17→19개 발견, 정상오판1→8개 확인.
3. Validation/Test 설명을 펼쳐 후보 선정과 마지막 확인이 다른 이유를 설명. 회사 적용 승인과 구분.
4. 비교 목표는 Recall 우선이며 90%·15%는 회사 기준이 아닌 데모 기본값임을 설명.
5. 새 비교 계획에서 전처리·후보 이유 확인. 승인 전 실행 이력이 늘지 않음을 설명하고 승인하면 실제 학습.
6. 기존 모델 그대로 점검 클릭. 같은 제품별 새 정답 데이터 성능을 확인. 새 Test는 이 점검에 사용하지 않음.
7. 같은 알고리즘 재학습 계획 받기 → 합친 학습1개+제품별4개 계획 확인 → 승인 뒤 실제 학습.
8. 새 배치 동일 Test에서 기존24/127개→재학습117/127개 발견 확인. 정상오판도 함께 보고 회사 적용 별도.
9. C의 합친 학습/따로 학습 Validation을 비교하고 Test에서 목표 미달일 수 있음을 설명.
10. 공개 SECOM은 실제 반도체 센서·검사 결과이며 실험 성능이 부족한 사례를 그대로 보여 줌.

Local LLM을 쓰려면 Ollama 서버와 qwen3.5:2b·qwen3-embedding:0.6b 모델 준비 후 SEMI_LLM_ENABLED=1 bash start.sh로 실행합니다. 기본은 규칙·TF-IDF이며 역할별 실행 상태를 숨기지 않습니다. 일반적인 계획은 최대52조건, 센서 수초~수십초이며 기기마다 다릅니다. 화면은 현재 버전의 실행 결과만 선택합니다.
''')
if __name__=='__main__':main()
