"""Stage the requested workbook; leave every other student's cells unchanged."""
from pathlib import Path
import json
from copy import copy
from openpyxl import load_workbook
from openpyxl.comments import Comment
from openpyxl.styles import Font, PatternFill, Alignment

ROOT=Path(__file__).resolve().parent.parent
WEEK=ROOT.parent.parent
SOURCE=WEEK/'AI Agent Mini-Project-Semiconductor-AI-Agent.xlsx'
TARGET=ROOT/'docs/submission'/SOURCE.name
TARGET.parent.mkdir(parents=True,exist_ok=True)
wb=load_workbook(SOURCE)
assert wb['2반']['A11'].value=='G045' and wb['2반']['B11'].value=='김용찬'
before={(s.title,c.coordinate):c.value for s in wb for row in s for c in row if c.value is not None}
ws=wb['2반']
ws['C11']=2
ws['D11']='\n'.join([
    '반도체 검사 모델 실험 도우미 (신규 AI Agent · 과제 2)',
    '- 데이터 점검 → 근거 검색 → 계획 승인 → 모델 비교 → 선택 근거·지표',
    '- 스칼라 수업·반도체 자료를 참고한 후보 모델 비교',
    '- 6:2:2 사전 고정·같은 lot/날짜 분리·Validation 후보 선택',
    '- Recall 우선·정상 오판·Precision·F1 함께 비교',
    '- 공식 문서 탐색 RAG·ExtraTrees/GaussianNB 승인 비교·목록 갱신',
    '- 재학습·기존 모델 점검은 추가 구현으로 보존, 발표 범위에서 제외',
    '- LangGraph·MCP 4도구/Resource·DI·모듈화·33개 단위/API 테스트',
    '- LangSmith APAC 실제 계획·하위 실행 API 재조회 확인',
    '- Windows 실행 복구·5분 발표 10장 + 질문용 부록 6장',
    '- 수업과 같은 Qwen2.5-1.5B 계열 로컬 연결·역할별 응답 검증 기록',
    '- 로컬 LLM-as-a-Judge로 설명 정합성 평가·초기 실패 기록 보존',
    '- 양산 효과·자동 배포는 검증 범위 밖'])
repo='https://github.com/dragonchan95/Semiconductor-AI-Agent'
report=repo+'/blob/main/docs/REPORT.md'
slides='https://docs.google.com/presentation/d/1J2m_cpXyvb-5_Xabs2DsD3EnEV6B6GicF5OP2s5FohU/edit'
ws['E11']=repo
ws['F11']=slides
for addr in ['E11','F11']:
    ws[addr].hyperlink=ws[addr].value
    font=copy(ws[addr].font);font.color='0563C1';font.underline='single';ws[addr].font=font
ws['F11'].comment=Comment('요청한 기존 Google Slides 주소를 유지합니다. 로그인 없는 공개 열람은 확인했습니다. 최신 PPTX 내용의 온라인 원본 반영은 Google Drive 연결 후 진행해야 합니다. 최신 로컬 내용의 보고서: '+report,'G045')
name='G045 제출 안내'
if name in wb.sheetnames:
    info=wb[name]
else:info=wb.create_sheet(name)
rows=[['항목','내용'],['소속','SKALA 광주 2반 · G045 김용찬 · 과제 2'],
      ['최종 보고서 Google Slides URL',slides],['소스 코드 URL',repo],['최신 보고서 사본',report],
      ['최신 발표 PPTX',repo+'/blob/main/docs/G045_Semiconductor_Agent.pptx'],
      ['최신 발표 PDF',repo+'/blob/main/docs/G045_Semiconductor_Agent.pdf'],
      ['5분 대본',repo+'/blob/main/docs/발표대본_G045.txt'],
      ['온라인 Slides 상태','로그인 없는 공개 열람 확인. 최신 내용은 아직 미반영이며 Google Drive 연결 후 갱신 필요.'],
      ['제출 일정','2026-10-22(목) 13:00 마감 / 13:10 발표 시작 / 개인 5분'],
      ['제출 절차','이 파일은 로컬 명단입니다. 지정된 공용 Google Spreadsheet 등록 여부는 별도 확인 필요.'],
      ['LangSmith','APAC에서 실제 계획 생성·하위 실행 API 재조회 성공. 키는 로컬 .env에만 저장.'],
      ['실행 모드','Windows: 로컬 Qwen2.5-1.5B 양자화 모델 + TF-IDF 검색. 역할별 검증 기록을 별도 보관.'],
      ['발표 구성','본문 10장 280초 + 전환 20초 / 질문용 부록 6장']]
for i,row in enumerate(rows,1):
    for j,value in enumerate(row,1):
        cell=info.cell(i,j,value);cell.alignment=Alignment(vertical='top',wrap_text=True)
        cell.font=Font(name='맑은 고딕',size=11,color='173A49',bold=i==1)
        if value.startswith('https://'):cell.hyperlink=value;cell.font=Font(name='맑은 고딕',size=11,color='0563C1',underline='single')
        if i==1:cell.fill=PatternFill('solid',fgColor='DDEFEF')
    info.row_dimensions[i].height=38 if i>1 else 25
info.column_dimensions['A'].width=26;info.column_dimensions['B'].width=105
info.freeze_panes='B2'
wb.save(TARGET)
after=load_workbook(TARGET)
changed=[]
for key,value in before.items():
    sheet,coordinate=key
    if after[sheet][coordinate].value!=value:changed.append(key)
assert all(sheet==name or (sheet,coordinate) in {('2반',x) for x in ['C11','D11','E11','F11']} for sheet,coordinate in changed),changed
print(json.dumps({'staged_workbook':str(TARGET),'changed_existing_cells':changed,'added_sheet':name},ensure_ascii=False))
