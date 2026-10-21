"""Copy completed deliverables to the user's explicitly requested week folder."""
import json
from pathlib import Path
import shutil
import re
import zipfile

ROOT=Path(__file__).resolve().parent.parent
WEEK=ROOT.parent.parent.resolve()
assert WEEK.name=='15주차',WEEK
staging=ROOT/'docs/submission'
workbook='AI Agent Mini-Project-Semiconductor-AI-Agent.xlsx'
original=WEEK/workbook
backup=staging/'AI Agent Mini-Project-Semiconductor-AI-Agent.before-windows.xlsx'
if not backup.exists():shutil.copy2(original,backup)
mapping=[(staging/workbook,workbook),
         (ROOT/'docs/G045_Semiconductor_Agent.pptx','G045_최종발표.pptx'),
         (ROOT/'docs/G045_Semiconductor_Agent.pdf','G045_최종발표.pdf'),
         (ROOT/'docs/G045_Final_Report.pdf','G045_최종보고서.pdf'),
         (ROOT/'docs/G045_Final_Report.pptx','G045_최종보고서.pptx'),
         (ROOT/'docs/G045_Final_Report.html','G045_최종보고서.html'),
         (ROOT/'docs/발표대본_G045.txt','발표대본_G045.txt'),
         (ROOT/'docs/HANDOFF_WINDOWS.md','작업이어받기_G045.md')]
for source,name in mapping:
    assert source.is_file(),source
    destination=(WEEK/name).resolve()
    assert destination.parent==WEEK,destination
    shutil.copy2(source,destination)
report=(ROOT/'docs/REPORT.md').read_text(encoding='utf-8')
prefix=ROOT.relative_to(WEEK).as_posix()+'/docs/'
def local_link(match):
    target=match.group(2)
    if not target.startswith(('https://','http://','#','mailto:')):target=prefix+target
    return match.group(1)+target+match.group(3)
(WEEK/'G045_최종보고서.md').write_text(re.sub(r'(!?\[[^\]]+\]\()([^\n)]+)(\))',local_link,report),encoding='utf-8')
guide='''SKALA 광주2반 G045 김용찬 · 제출자료 안내

발표할 때: G045_최종발표.pptx 또는 G045_최종발표.pdf
  - 본문1~10장만 발표, 11~14장은 질문용 부록입니다.
발표 연습: 발표대본_G045.txt
교수님께 제출할 Google Slides에 올릴 파일: G045_최종보고서.pptx
  - 상세 보고서8쪽을 모두 담은 제출용입니다. 발표자료와 구분합니다.
  - A4 세로 문서이므로 Google Drive에 업로드한 뒤 Google Slides로 열어 새 문서로 저장하는 방식을 권장합니다.
  - 각 쪽은 고해상도 이미지이며 전체 텍스트는 노트에 보존했습니다. 본문 수정은 MD에서 하고 재생성합니다.
상세 최종 보고서 PDF: G045_최종보고서.pdf
  - 같은 프로젝트를 교수 안내의5개 필수 항목 순서로 자세히 정리했습니다.
  - HTML은 인터넷 없이 화면·표를 읽는 사본, MD는 편집 가능한 본문입니다.
제출 명단: AI Agent Mini-Project-Semiconductor-AI-Agent.xlsx

최신 공개 보고서:
https://github.com/dragonchan95/Semiconductor-AI-Agent/blob/main/docs/REPORT.md
소스 코드:
https://github.com/dragonchan95/Semiconductor-AI-Agent

현재 엑셀의 Google Slides 주소는 예전16장입니다. 제출용 최종 보고서8장으로 온라인 갱신이 필요합니다.
G045_최종보고서.pptx를 Google Slides로 열어 공유하고, 새 주소를 쓰면 엑셀2반!F11에도 새 보고서 주소를 입력합니다.
공유는 링크가 있는 모든 사용자에게 뷰어 권한을 주고 로그인하지 않은 창에서 열리는지 확인합니다.
G045_최종발표.pptx는5분 발표할 때 별도로 띄우는 요약본입니다.
로컬 엑셀 갱신과 지정된 공용 Google Spreadsheet 등록은 별개입니다.
'''
(WEEK/'G045_제출자료_안내.txt').write_text(guide,encoding='utf-8')
mail_files=['G045_최종보고서.pptx','G045_최종보고서.pdf','G045_최종발표.pptx',
            '발표대본_G045.txt',workbook,'G045_제출자료_안내.txt']
with zipfile.ZipFile(WEEK/'G045_메일첨부.zip','w',compression=zipfile.ZIP_DEFLATED) as bundle:
    for name in mail_files:bundle.write(WEEK/name,arcname=name)
receipt={'requested_folder':str(WEEK),'delivered':[name for _,name in mapping],
         'additional_documents':['G045_최종보고서.md','G045_제출자료_안내.txt','G045_메일첨부.zip'],
         'original_workbook_backup':str(backup),
         'google_slides_online_update':'pending Google Drive connection; original URL preserved'}
(staging/'delivery.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(receipt,ensure_ascii=False,indent=2))
