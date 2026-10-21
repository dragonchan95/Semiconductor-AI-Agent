"""Build the final deck, report and timed script from preserved measured receipts."""
import json
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / 'docs'
SLIDES_URL = 'https://docs.google.com/presentation/d/1J2m_cpXyvb-5_Xabs2DsD3EnEV6B6GicF5OP2s5FohU/edit'
REPO_URL = 'https://github.com/dragonchan95/Semiconductor-AI-Agent'
NAMES = {'logistic':'Logistic Regression','decision_tree':'Decision Tree',
         'random_forest':'Random Forest','gradient_boosting':'Gradient Boosting',
         'xgboost':'XGBoost','lightgbm':'LightGBM','catboost':'CatBoost','knn':'KNN',
         'svm':'SVM (RBF)','mlp':'MLP / ANN','adaboost':'AdaBoost',
         'hist_gradient':'HistGradientBoosting','extra_trees':'ExtraTrees',
         'gaussian_nb':'GaussianNB','resnet_small':'축소 ResNet','vgg_small':'축소 VGGNet',
         'autoencoder':'Autoencoder'}
TEAL='147D82'; INK='173A49'; MUTED='617681'; BG='F6F8FA'; LINE='D8E3E7'; PALE='E8F3F3'; ORANGE='FFF0DD'


def load(name):
    return json.loads((DOCS / 'evaluation' / f'{name}.json').read_text(encoding='utf-8'))


def pct(value):
    return str(Decimal(str(value * 100)).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)) + '%'


def ranking(trials, policy):
    def key(t):
        m=t['validation']
        return (m['recall']>=policy['min_recall'] and m['fpr']<=policy['max_fpr'],
                -max(0,policy['min_recall']-m['recall'])-max(0,m['fpr']-policy['max_fpr']),
                m['recall'],-m['fpr'],t['id'])
    complete=[t for t in trials if t['status']=='completed']
    count=max(len(t['products']) for t in complete)
    best={}
    for t in complete:
        if len(t['products'])==count and (t['model'] not in best or key(t)>key(best[t['model']])):
            best[t['model']]=t
    return sorted(best.values(),key=key,reverse=True)


def make_content():
    from presentation_content import compose_content
    return compose_content(load,NAMES,pct,ranking)


def color(value):
    return RGBColor.from_string(value)


def box(slide,x,y,w,h,fill,line=None,rounded=False):
    shape=slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE,
                                 Inches(x),Inches(y),Inches(w),Inches(h))
    shape.fill.solid();shape.fill.fore_color.rgb=color(fill)
    if line:shape.line.color.rgb=color(line)
    else:shape.line.fill.background()
    if rounded:
        shape.adjustments[0]=.08
    return shape


def text(slide,value,x,y,w,h,size=20,fill=INK,bold=False):
    shape=slide.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h))
    frame=shape.text_frame;frame.word_wrap=True
    frame.margin_left=frame.margin_right=Inches(.02)
    frame.margin_top=frame.margin_bottom=Inches(.02)
    for i,line in enumerate(str(value).split('\n')):
        p=frame.paragraphs[0] if i==0 else frame.add_paragraph()
        p.text=line;p.font.name='맑은 고딕';p.font.size=Pt(size);p.font.bold=bold;p.font.color.rgb=color(fill)
        p.space_after=Pt(8);p.line_spacing=1.14
    return shape


def add_table(slide,rows,y=3.05,height=3.25,font=17,widths=None):
    cols=len(rows[0]);shape=slide.shapes.add_table(len(rows),cols,Inches(.65),Inches(y),Inches(12.03),Inches(height))
    table=shape.table
    if widths:
        for i,v in enumerate(widths):table.columns[i].width=Inches(v)
    for i,row in enumerate(rows):
        for j,value in enumerate(row):
            cell=table.cell(i,j);cell.text=str(value);cell.margin_left=Inches(.13);cell.margin_right=Inches(.1)
            cell.margin_top=Inches(.07);cell.margin_bottom=Inches(.06);cell.vertical_anchor=MSO_ANCHOR.MIDDLE
            cell.fill.solid();cell.fill.fore_color.rgb=color(TEAL if i==0 else ('FFFFFF' if i%2 else PALE))
            for p in cell.text_frame.paragraphs:
                p.font.name='맑은 고딕';p.font.size=Pt(font);p.font.bold=i==0;p.font.color.rgb=color('FFFFFF' if i==0 else INK)
    return shape


def picture(slide,path,x,y,w,h):
    from PIL import Image
    iw,ih=Image.open(path).size
    scale=min(w/iw,h/ih);pw,ph=iw*scale,ih*scale
    box(slide,x-.08,y-.08,w+.16,h+.16,'FFFFFF',LINE,True)
    slide.shapes.add_picture(str(path),Inches(x+(w-pw)/2),Inches(y+(h-ph)/2),width=Inches(pw),height=Inches(ph))


def build_deck(content,trace):
    prs=Presentation();prs.slide_width=Inches(13.333333);prs.slide_height=Inches(7.5)
    for i,item in enumerate(content,1):
        slide=prs.slides.add_slide(prs.slide_layouts[6]);slide.background.fill.solid();slide.background.fill.fore_color.rgb=color(BG)
        box(slide,0,0,.16,7.5,TEAL)
        text(slide,item['context'],.65,.32,12,.3,12,TEAL,True)
        text(slide,item['title'],.65,.91,12,1.1,32 if '\n' not in item['title'] else 38,INK,True)
        box(slide,.65,6.91,12.03,.015,LINE)
        text(slide,'SKALA 광주 2반 · G045 김용찬',.65,7.02,8,.25,10,MUTED)
        text(slide,f'{i:02d} / {len(content):02d}'+('  부록' if i>10 else ''),11.1,7.02,1.6,.25,10,MUTED)
        slide.notes_slide.notes_text_frame.text=item['note']+'\n\n출처: '+'; '.join(item['sources'])
        if item['kind']=='cover':
            text(slide,item['body'][0],.72,2.75,11.5,.8,23,MUTED)
            text(slide,item['body'][1],.72,3.77,11.5,.5,20,INK)
            for j,(a,b) in enumerate([('01','데이터 점검'),('02','계획 승인'),('03','모델·비율 비교'),('04','선택 근거')]):
                x=.72+j*3.08;box(slide,x,5.15,2.78,1.05,PALE,rounded=True)
                text(slide,a,x+.2,5.27,.5,.32,14,TEAL,True);text(slide,b,x+.2,5.68,2.4,.4,19,INK,True)
        elif item['kind']=='criteria':
            for j,(label,definition) in enumerate([('불량 검출률 · Recall','불량 100개 중 몇 개를 찾았나요?'),('정상 오판률','정상 100개 중 몇 개를 잘못 잡았나요?')]):
                x=.72+j*6.08
                box(slide,x,2.15,5.82,1.43,PALE if j==0 else ORANGE,rounded=True)
                text(slide,label,x+.22,2.34,5.35,.45,25,TEAL if j==0 else INK,True)
                text(slide,definition,x+.22,2.97,5.35,.4,19,INK)
            text(slide,'시연 목표: 불량 검출률 90% 이상 · 정상 오판률 15% 이하',.8,3.99,11.7,.55,23,INK,True)
            text(slide,'정상 오판 한도 준수 → 검출률 최대 → 동률이면 F1',.8,4.89,11.7,.55,22,TEAL,True)
            text(slide,'F1: 불량 검출과 불량 판정의 정확성을 함께 보는 보조 지표',.8,5.58,11.7,.4,17,MUTED)
            text(slide,item['body'][-1],.8,6.12,11.7,.45,17,MUTED)
        elif item['kind']=='architecture':
            text(slide,'LangGraph 역할 연결 · 로컬 Qwen 설명 · MCP 조회·계획 도구',.68,2.1,12,.45,21,MUTED)
            text(slide,'RAG: 내부 근거·공식 문서 → BGE-M3 임베딩 → FAISS 검색 → Qwen에 근거 전달',.72,2.58,11.9,.25,13,TEAL)
            nodes=[('데이터 점검','행·결측·라벨'),('근거 검색','BGE-M3 · FAISS'),('실험 계획','모델·전처리·비교 범위'),('엔지니어 승인','확인 후 실행 허용')]
            for j,(a,b) in enumerate(nodes):
                x=.7+j*3.08;box(slide,x,2.92,2.77,1.12,PALE,rounded=True)
                text(slide,a,x+.15,3.08,2.48,.4,21,TEAL,True);text(slide,b,x+.15,3.59,2.5,.3,13,MUTED)
                if j<3:text(slide,'→',x+2.8,3.22,.28,.4,19,TEAL,True)
            box(slide,.7,4.36,11.95,.85,'FFFFFF',LINE,True)
            text(slide,'실험 엔진 학습·수치·순위 계산 → 결과 검토 역할이 근거 정리',.92,4.56,11.5,.45,22,INK,True)
            text(slide,'LangSmith: 실제 실행 추적 · API 재조회 확인',.8,5.56,11.7,.4,19,TEAL,True)
            text(slide,f'설명 검사(LLM-as-a-Judge): 6/8개 올바른 판단 · 코드 테스트 {load("windows_check")["test_count"]}개 통과',.8,6.16,11.7,.4,18,MUTED)
        elif item['kind']=='grouping_screen':
            picture(slide,DOCS/'assets'/item['image'],.8,2.2,11.72,3.82)
            text(slide,item['body'][1],.85,6.12,11.7,.42,19,INK,True)
            text(slide,'Validation에서는 좋았지만 Test에서는 목표 미달 · 기존 Test 재사용 탐색 · 새 독립 데이터 필요',.85,6.62,11.7,.24,12,MUTED)
        elif item['kind']=='ensemble_screen':
            picture(slide,DOCS/'assets'/item['image'],.8,2.2,11.72,3.82)
            text(slide,item['body'][0],.85,6.12,11.7,.4,20,TEAL,True)
            text(slide,'5% 간격과 균등 비율의 232개 비교 · 이 탐색 범위 안의 최선 · Test로 비율 선택하지 않음',.85,6.62,11.7,.24,12,MUTED)
        elif item['kind']=='validation_screen':
            picture(slide,DOCS/'assets'/item['image'],.78,2.15,8.02,4.2)
            for j,line in enumerate(['같은 조건에서 후보 비교','검출률·정상 오판 동시 확인','선택: CatBoost · A+B+C','Test는 마지막 확인에 사용']):
                text(slide,line,9.15,2.35+j*1.04,3.42,.85,21 if j==2 else 18,TEAL if j==2 else INK,j==2)
            text(slide,'실제 앱 비교표의 상단 4행 · 전체표는 부록 A',.88,6.65,11.8,.22,11,MUTED)
        elif item['kind']=='result_screen':
            for j,line in enumerate(item['body']):
                text(slide,line,.78,2.3+j*1.04,4.25,.87,24 if j<2 else 21,TEAL if j<2 else INK,True)
            picture(slide,DOCS/'assets'/item['image'],5.45,2.1,7.03,4.55)
        elif item['image']:
            for j,line in enumerate(item['body']):
                text(slide,line,.72,2.25+j*.96,4.95,.88,22 if j==0 else 19,INK if j==0 else MUTED,j==0)
            picture(slide,DOCS/'assets'/item['image'],6.0,2.05,6.4,4.55)
        elif item['kind']=='trace':
            for j,line in enumerate(item['body']):text(slide,line,.7,2.15+j*.62,12,.52,19,INK,j==2)
            box(slide,.72,4.93,11.9,1.42,'FFFFFF',LINE,True)
            text(slide,'experiment.propose → LangGraph → 점검 · 검색 · 계획',.97,5.1,11.3,.5,23,TEAL,True)
            if trace:text(slide,'API 재조회 성공 · child run '+str(len(trace['child_runs']))+'개 · '+trace['root_run_id'],.97,5.86,11.1,.3,13,MUTED)
            text(slide,'LLM은 근거와 설명을 보조하고, 모델 학습·지표 계산·후보 순위는 실험 엔진이 담당합니다.',.75,6.5,11.8,.3,12,MUTED)
        elif item['table']:
            body_size=18 if i!=11 else 15
            for j,line in enumerate(item['body']):text(slide,line,.7,2.02+j*.46,12,.44,body_size,MUTED)
            y=2.12+len(item['body'])*.46+.16
            height=6.64-y
            font=16 if i<=10 else 13
            if i==11:font=12
            if i==14:font=15
            widths=None
            if i==11:widths=[4.43,1.9,1.9,1.9,1.9]
            if i==12:widths=[1.0,3.9,3.9,3.23]
            if i==14:widths=[5.3,3.3,3.43]
            if i==15:widths=[5.7,3.13,3.2]
            add_table(slide,item['table'],y,height,font,widths)
        else:
            for j,line in enumerate(item['body']):
                y=2.16+j*.85;box(slide,.7,y,.055,.56,TEAL)
                text(slide,line,.95,y,11.6,.7,21 if i<=10 else 19,INK)
    prs.core_properties.title='반도체 검사 모델 실험 도우미'
    prs.core_properties.author='SKALA 광주 2반 · G045 김용찬'
    target=DOCS/'G045_Semiconductor_Agent.pptx';prs.save(target)
    return target


def write_documents(content,receipts,trace):
    (DOCS/'slide-content.json').write_text(json.dumps(content,ensure_ascii=False,indent=2),encoding='utf-8')
    script='SKALA 광주 2반 · G045 김용찬 / 과제 2\n반도체 검사 모델 실험 도우미\n'
    script+='2026-10-22 발표 · 본문 10장 + 질문용 부록 4장\n발화 목표 255초 + 화면 전환 20초 = 4분35초 / 5분까지 여유25초\n계획 시간이며 실제 리허설 측정값은 아닙니다. 부록은 읽지 않습니다.\n\n'
    elapsed=0
    for i,item in enumerate(content,1):
        elapsed+=item['seconds']
        timing=f"{item['seconds']}초 / 누적 {elapsed//60}:{elapsed%60:02d}" if i<=10 else '질문용 부록'
        script+=f"[{i}장 / {timing}] "+item['title'].replace('\n',' ')+'\n'+item['note']+'\n\n'
    from report_content import build_final_report
    report=build_final_report(content,receipts,trace)
    script+='''질문 대비
Q. AdaBoost는 어디서 나온 모델인가요?
A. 15주차 반도체 발표자료 40~42쪽의 Adaboost Regression / Ada Boost 회귀 사례를 참고해 분류용 AdaBoostClassifier로 적용했습니다. 새 모델 탐색 RAG가 추가한 모델은 ExtraTrees와 GaussianNB입니다.

Q. 왜 F1이 더 높은 AdaBoost를 선택하지 않았나요?
A. 이번 실험은 사전에 정한 Recall 목표와 정상 오판 한도 충족을 먼저 보고, Recall 우선·동률이면 정상 오판이 낮은 후보를 골랐습니다. 다른 업무 목표라면 선택 규칙도 바뀔 수 있습니다.

Q. 6:2:2가 항상 최적인가요?
A. 수업 기준으로 정한 사전 고정 조건입니다. 모든 데이터에서 최적이라는 뜻은 아닙니다. 같은 lot·날짜 경계를 보존하고 Test를 보고 비율을 고르지 않습니다.

Q. 서로 다른 모델의 예측을 섞는 앙상블도 구현했나요?
A. 네. 각 모델의 불량 확률을 비율대로 곱해 더합니다. 단일 모델과 균등 비율도 포함해 비교했습니다. 현재 예제에서는 CatBoost90%와LightGBM10%가 선택됐습니다. Random Forest·부스팅 내부의 앙상블을 쓰는 것에서 한 단계 더 나아가, 서로 다른 모델 사이의 비율도 비교한 것입니다.

Q. 제품별로 따로 학습하는 것이 당연히 좋지 않나요?
A. 꼭 그렇지는 않습니다. 제품별로 나누면 특성은 맞추기 쉽지만 학습 데이터와 불량 표본도 줄어듭니다. 별도 합성 실험에서는 A는 전체 제품을 합친 모델이, C는 전용 모델이 Validation에서 더 높은 검출률을 보였습니다. 같은 제품의 같은 평가 행으로 비교해야 합니다.

Q. ABC용 모델과D용 모델로 나누는 것도 자동으로 비교하나요?
A. 네. 네 제품을 중복·누락 없이 나누는15개 구성을 모두 비교합니다. 같은 알고리즘과 설정을 고정하고 각 그룹의 모델을 Train으로 학습하며, 같은 Validation에서 구성을 고릅니다. 이번에는 ABC와D가 선택됐지만 Test에서는 목표 미달이라 적용을 보류했습니다. 앙상블 비율까지 동시에 최적화한 실험은 아닙니다.

Q. 왜 F1이 가장 높은 비율을 고르지 않나요?
A. 이번 목적은 불량을 놓치는 일을 줄이는 것입니다. 정상 오판률 한도 안에서 Recall을 먼저 높이고, Recall이 같을 때 F1으로 고릅니다. F1·Precision·오판률을 모두 함께 보여 줍니다. 실제 현장 기준은 업무 비용에 맞춰 정해야 합니다.

Q. 90대10이 정말 최적인가요?
A. 승인한 세 모델과5% 간격의 비율, Validation 데이터 안에서 정한 기준으로 가장 좋았습니다. 모든 모델과 모든 연속 비율에서의 최적이라는 뜻은 아닙니다. 선택 후 Test를 확인했지만 기존 Test의 추가 탐색이므로 새 독립 기간 검증이 필요합니다.

Q. 자동화와 Agent는 어떤 차이가 있나요?
A. 현재는 역할을 나눈 제한된 Agent 구조입니다. 근거를 검색해 설명하고 계획을 제안한 뒤 승인받은 도구로 모델을 비교합니다. 실제 수치·후보 순위·승인은 실험 엔진이 책임집니다. 자율 Supervisor나 무제한 모델 발굴을 구현했다고 주장하지 않습니다.

Q. LangSmith와 로컬 Qwen은 어떤 차이인가요?
A. Qwen은 노트북에서 설명용 응답을 만들고, LangSmith는 별도로 실행 경로를 기록합니다. Qwen을 로컬에서 돌려도 LangSmith 추적을 켜면 설정한 실행 기록은 외부로 전송됩니다. 지금은 공개·합성 데이터로 검증했습니다.

Q. 재학습이나 운영 감시도 발표하나요?
A. 추가 구현으로 보존했지만 이번 5분 발표는 데이터 점검·모델 비교·선택 근거에 집중합니다.

Q. LLM-as-a-Judge도 구현했나요?
A. 네. 실제 결과와 설명 문장을 LLM에 함께 주고 맞는 설명인지 검사했습니다. 직접 만든 예제8개 중6개는 맞게 검사했습니다. 예를 들어27개를 찾았는데30개라고 설명한 오류를 놓치기도 했습니다. 그래서 중요한 숫자는 코드로도 검사합니다.

Q. 결과 검토 Agent가 이미 Judge 아닌가요?
A. 결과 검토 Agent는 실험 결과를 설명하는 역할입니다. Judge는 그 설명이 실제 결과와 맞는지 다시 검사하는 역할입니다. 현재 평가에서는 실제 결과를 바탕으로 직접 만든 설명 예제들을 검사했습니다.

Windows 앱 실행: continued-project 폴더의 start.cmd를 더블클릭하고 http://localhost:8700을 엽니다.
새 환경은 예제 데이터 준비 → 계획 제안 → 승인·학습 순서입니다. 발표는 기록된 화면을 설명하므로 새 학습을 기다릴 필요가 없습니다.
'''
    (DOCS/'REPORT.md').write_text(report,encoding='utf-8')
    (DOCS/'발표대본_G045.txt').write_text(script,encoding='utf-8')
    r=receipts['synthetic_process']['result'];b=r['baseline_test'];t=r['test']
    ensemble=load('weighted_ensemble')['result'];e=ensemble['ensemble'];eb=ensemble['baseline_test'];et=ensemble['test']
    readme=f'''# 반도체 검사 모델 실험 도우미

**SKALA 광주 2반 · G045 김용찬 · 신규 AI Agent 과제 2**

검사 데이터를 점검하고 승인받아 **학습할 제품 묶음**과 **예측 확률의 혼합 비율**을 각각 비교한 뒤, 선택 근거와 검증 결과를 보여 줍니다.

[최종 보고서](docs/REPORT.md) · [발표 PPTX](docs/G045_Semiconductor_Agent.pptx) · [발표 PDF](docs/G045_Semiconductor_Agent.pdf) · [5분 대본](docs/발표대본_G045.txt) · [과제 대응표](docs/ASSIGNMENT_CHECKLIST.md)

발표자료는5분 요약본, 최종 보고서는 같은 프로젝트의 상세 제출 문서입니다. [상세 보고서 PDF](docs/G045_Final_Report.pdf)와 인터넷 없이 읽는 [HTML 사본](docs/G045_Final_Report.html)도 제공합니다. 15주차 폴더에는 발표자료·보고서·대본·제출 엑셀을 함께 모았습니다.

기존 [Google Slides]({SLIDES_URL}) 주소를 보존했습니다. 이번 수정의 원본은 이 저장소의 보고서와 PPTX입니다. Slides의 온라인 갱신 상태는 별도로 확인해야 합니다.

## 하나의 사용 흐름

데이터 선택 → 점검·근거 검색 → 승인·모델 학습 → 그룹 또는 앙상블 비교 계획 승인 → Validation 선택 → 같은 Test 확인

![앙상블 비율의 Validation 비교](docs/assets/app-ensemble-validation.jpg)

현재 합성 센서 예제의 선택 비율은 **CatBoost90% + LightGBM10%**입니다(HistGradientBoosting0%).
정상 오판률 한도 안에서 **Recall 최대 → 동률이면 F1** 순서로 고릅니다. F1만 최대로 고르는 방식이 아닙니다.
세 모델의 합계100% 비율을5% 간격으로 모두 비교하고 균등 비율도 추가해 **232개 비율**과 각 판정 기준을 Validation에서 비교했습니다.
단일 모델도 포함하며 동률이면 적은 모델을 택합니다. 항상 혼합을 강제하지 않습니다.
이 후보·간격·데이터 안의 최선이며 전체 모델의 전역 최적이나 양산 최적을 뜻하지 않습니다.
[실제 승인·실행 기록](docs/evaluation/weighted_ensemble.json) · [브라우저·CSV 검증](docs/evaluation/ensemble_browser.json) · [비교 방법](docs/ENSEMBLE.md)

학습할 제품 범위도 비교합니다. **ABCD 하나 / ABC와D / AB와CD / 각각4개**를 포함해 네 제품의 담당 그룹15개 구성을 모두 비교합니다. 알고리즘을 고정한 실제 실험에서ABC와D가 Validation에서 선택됐지만 Test Recall78.1%로 목표 미달이라 적용을 보류했습니다. 제품별 전용이 항상 우수하다고 가정하지 않으며 앙상블 비율 실험과 별도로 조건을 통제합니다. [그룹 비교 방법·실측](docs/PRODUCT_GROUPING.md) · [실제15개 구성](docs/evaluation/product_partitions.json)

## Windows에서 실행

`start.cmd`를 더블클릭하고 **http://localhost:8700**을 엽니다. 실행 창은 열어 둡니다.
새 설치는 PowerShell에서 `./start.ps1`로 Python 환경과 의존성을 준비합니다. Python 3.11 이상이 필요합니다.
이 작업 폴더에서는 상위 폴더의 `.venv`도 인식합니다. 처음에는 **예제 데이터 준비**를 누릅니다.
새 환경에는 과거 모델 파일과 DB가 없으므로 계획 승인 후 학습해야 새 실행 이력이 생깁니다.
저장된 실측 결과는 `docs/evaluation/`에서 확인할 수 있습니다.

macOS/Linux에서는 `bash start.sh`를 실행합니다. macOS의 XGBoost·LightGBM은 OpenMP 설치가 필요할 수 있습니다.

## 현재 모드와 LangSmith

`.env.example`을 참고해 로컬 `.env`를 설정합니다. 키는 Git에서 제외합니다.
APAC LangSmith에서 **실제 계획 생성과 하위 실행 기록의 API 재조회**를 확인했습니다.
[추적 증빙](docs/evaluation/langsmith_check.json) · [설정 안내](docs/LANGSMITH_SETUP.md)

현재 Windows에는 수업과 같은 Qwen2.5-1.5B-Instruct 계열의 양자화 모델을 로컬 Ollama로 연결했습니다.
실제 역할별 응답 검증은 [기록](docs/evaluation/local_llm_check.json)을 기준으로 확인합니다.
5주차 실습을 참고해 **BGE-M3 임베딩 + FAISS 로컬 벡터 저장·검색**을 내부 근거와 외부 모델 문서에 연결했습니다.
`SEMI_LLM_ENABLED=1`, `SEMI_LLM_MODEL=qwen2.5:1.5b`, `SEMI_DENSE_ENABLED=1`, `SEMI_EMBED_MODEL=bge-m3`이 현재 설정입니다.
[실제 검색·Qwen 근거 연결 검증](docs/evaluation/vector_rag.json) · [설정·구현 범위](docs/RAG.md)
첫 준비는 `scripts/setup_local_qwen.py`, 이후 Windows 실행 파일은 로컬 Ollama도 함께 시작합니다.
기존 Mac의 LLM 검증 기록은 [agent_integration.json](docs/evaluation/agent_integration.json)에 보존합니다.
LangSmith 연결과 LLM 응답 성공은 별개이며 UI에 verified/fallback/disabled 상태를 표시합니다.

## 고정한 조건과 결과

6:2:2를 사전에 고정했습니다. 합성 센서는 Train768 / Validation256 / Test256이며 같은 lot을 섞지 않습니다.
SECOM은 날짜 블록60/20/20이라 실제 행 수는 820 / 367 / 380입니다.
여러 모델과 불균형 설정을 비교한 뒤 상위 후보의 제품 조합을 확장합니다. 최대52조건이며 완전탐색이 아닙니다.
후보는 Validation에서 고르고 Test로 순위를 바꾸지 않습니다.

|같은 합성 센서 Test|최선 단일 CatBoost|선택 비율90:10|
|---|---:|---:|
|불량 발견|{eb['tp']}/32|{et['tp']}/32|
|정상 오판|{eb['fp']}/224|{et['fp']}/224|
|Recall|{pct(eb['recall'])}|{pct(et['recall'])}|
|F1|{eb['f1']:.3f}|{et['f1']:.3f}|

이번 조합은 교육용 목표를 충족했습니다. 양산 승인이나 현장 성능 보장은 아닙니다.
비율 선택에는 Test를 쓰지 않았지만, 이전 프로젝트에서 이미 확인한 Test의 추가 탐색이므로 새 독립 기간 데이터가 필요합니다.
초기 개별 모델·제품 조합 비교의20→27개 발견 결과는 별도 [기존 기록](docs/evaluation/synthetic_process.json)에 보존합니다.
측정은 기존 Mac 실험 기록을 보존하며 Windows의 재검증은 별도 증빙으로 구분합니다.

## 구현 범위

LangGraph 역할 분리, 교육 근거14개 검색과 공식 문서 기반 새 모델 탐색, MCP4도구·Resource,
의존성 주입, 승인 hash, 실제 모델 학습·파일 저장, 서로 다른 모델의 확률 혼합 비율 탐색, 모델 점검·재학습, 제품별 학습 비교를 구현했습니다.
외부 모델 탐색은 **ExtraTrees·GaussianNB의 검토된 adapter**를 지원합니다.
현재 RAG는 BGE-M3 의미 임베딩과 FAISS IndexFlatIP·출처 JSON 저장을 사용합니다. 별도 서버형 Vector DB는 아니며, 검색 실패 시 TF-IDF 대체 상태를 표시합니다.
로컬 LLM-as-a-Judge는 [평가 기록](docs/evaluation/llm_judge.json)에 있습니다. 작은 자체 개발 예제에 대한 결과이며 독립 평가가 아닙니다. 초기 실패도 보존합니다.
자율 Supervisor·임의 코드 생성은 미구현입니다. 확률 혼합은 현재 센서 분류 모델2~3개의 승인된 격자 탐색 범위입니다.

운영 모델은 자동 교체하지 않습니다. 회사 공통 Recall 수치, 양산 수율·금액 이득·작업시간 절감은 검증하지 않았습니다.
작은 불량 표본·반복 Validation과 추가 탐색의 Test 재사용이 한계이며 독립 기간 검증이 필요합니다.
교육 원본·제출 명단 엑셀·비밀 값은 공개 저장소에 넣지 않습니다.

## 검증과 재현

```powershell
$env:LANGSMITH_TRACING='false'
..\\.venv\\Scripts\\python.exe -X utf8 -m unittest discover -s tests -v
..\\.venv\\Scripts\\python.exe -X utf8 scripts/check_mcp.py
..\\.venv\\Scripts\\python.exe -X utf8 scripts/check_langsmith.py
..\\.venv\\Scripts\\python.exe -X utf8 scripts/build_report.py
```

독립 설치에서는 `..\\.venv` 대신 `.venv`를 사용합니다. 발표 생성 패키지는 `requirements-presentation.txt`에 있습니다.
Windows에서는 SQLite 연결을 transaction 종료 후 명시적으로 닫아 DB 파일 잠금 문제를 수정했습니다.
SECOM: McCann & Johnston(2008), [UCI 원본](https://archive.ics.uci.edu/dataset/179/secom), DOI10.24432/C54305, CC BY4.0.
센서 원파일590열과 UCI 메타데이터591 features 표기를 구분합니다. 제조사·제품ID는 원자료에 제공되지 않습니다.
'''
    (ROOT/'README.md').write_text(readme,encoding='utf-8')


def main():
    content,receipts,trace=make_content()
    target=build_deck(content,trace)
    write_documents(content,receipts,trace)
    print(json.dumps({'pptx':str(target),'slides':len(content),'main_slides':10,
                      'planned_speech_seconds':sum(s['seconds'] for s in content)},ensure_ascii=False))


if __name__=='__main__':
    main()
