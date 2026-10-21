"""Copy completed deliverables to the user's explicitly requested week folder."""
import json
from pathlib import Path
import shutil
from datetime import datetime

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
         (ROOT/'docs/발표대본_G045.txt','발표대본_G045.txt'),
         (ROOT/'docs/HANDOFF_WINDOWS.md','작업이어받기_G045.md')]
for source,name in mapping:
    assert source.is_file(),source
    destination=(WEEK/name).resolve()
    assert destination.parent==WEEK,destination
    shutil.copy2(source,destination)
receipt={'requested_folder':str(WEEK),'delivered':[name for _,name in mapping],
         'original_workbook_backup':str(backup),
         'google_slides_online_update':'pending Google Drive connection; original URL preserved'}
(staging/'delivery.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(receipt,ensure_ascii=False,indent=2))
