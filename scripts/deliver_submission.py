"""Copy completed deliverables to the user's explicitly requested week folder."""
import json
from pathlib import Path
import shutil
import re

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
상세 최종 보고서: G045_최종보고서.pdf
  - 같은 프로젝트를 교수 안내의5개 필수 항목 순서로 자세히 정리했습니다.
  - HTML은 인터넷 없이 화면·표를 읽는 사본, MD는 편집 가능한 본문입니다.
제출 명단: AI Agent Mini-Project-Semiconductor-AI-Agent.xlsx

최신 공개 보고서:
https://github.com/dragonchan95/Semiconductor-AI-Agent/blob/main/docs/REPORT.md
소스 코드:
https://github.com/dragonchan95/Semiconductor-AI-Agent

Google Slides 공개 주소는 엑셀에 유지했습니다. 온라인 원본은 예전16장으로 최신14장 미반영입니다.
Slides는 발표자료와 최종 보고서 어느 용도로도 제출할 수 있으며, 별도 보고서용으로 남겨둔 것이 아닙니다.
최신 PPTX를 기존 Slides에 가져온 뒤 기존 장을 정리해야 온라인도 최신본이 됩니다.
로컬 엑셀 갱신과 지정된 공용 Google Spreadsheet 등록은 별개입니다.
'''
(WEEK/'G045_제출자료_안내.txt').write_text(guide,encoding='utf-8')
receipt={'requested_folder':str(WEEK),'delivered':[name for _,name in mapping],
         'additional_documents':['G045_최종보고서.md','G045_제출자료_안내.txt'],
         'original_workbook_backup':str(backup),
         'google_slides_online_update':'pending Google Drive connection; original URL preserved'}
(staging/'delivery.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(receipt,ensure_ascii=False,indent=2))
