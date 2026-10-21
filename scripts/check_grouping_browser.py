"""Real UI plan/approval/execution, partition CSV and stored routing model evidence."""
import csv
import io
import json
from pathlib import Path
import httpx
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent.parent;BASE='http://127.0.0.1:8700'
source=json.loads((ROOT/'docs/evaluation/windows_llm_synthetic.json').read_text(encoding='utf-8'))['run_id']
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    page=browser.new_page(viewport={'width':1100,'height':1200},device_scale_factor=1)
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(BASE,wait_until='networkidle');page.wait_for_function('datasets.length>0')
    page.evaluate('(id)=>watch(id)',source)
    page.locator('#grouping-proposal').click();page.locator('#proposal-section').wait_for(state='visible')
    assert '15' in page.locator('#proposal-section').inner_text()
    page.locator('#engineer').fill('G045 제품그룹 UI 자동검증')
    page.locator('#proposal-section').screenshot(path=str(ROOT/'docs/assets/app-grouping-plan.jpg'),type='jpeg',quality=95)
    proposal_id=page.evaluate('proposal.id');plan_hash=page.evaluate('proposal.plan_hash')
    page.locator('#approve').click()
    page.locator('#grouping-summary').wait_for(state='visible',timeout=240000)
    page.locator('#grouping-validation').screenshot(path=str(ROOT/'docs/assets/app-grouping-validation.jpg'),type='jpeg',quality=95)
    page.locator('#grouping-test').screenshot(path=str(ROOT/'docs/assets/app-grouping-test.jpg'),type='jpeg',quality=95)
    record=page.evaluate('currentRun');g=record['result']['grouping']
    assert g['evaluated_partition_count']==15 and g['selection_uses_test'] is False
    assert 'NaN' not in page.locator('#result').inner_text() and not errors,errors
    plan=httpx.get(BASE+f'/api/proposals/{proposal_id}').json()['plan']
    duplicate=httpx.post(BASE+f'/api/proposals/{proposal_id}/decision',json={
        'accepted':True,'engineer':'duplicate test','plan_hash':plan_hash})
    assert duplicate.status_code==400
    exported=httpx.get(BASE+f'/api/runs/{record["id"]}/export.csv')
    rows=list(csv.DictReader(io.StringIO(exported.text)));assert len(rows)==15 and 'product_groups' in rows[0]
    receipt={'run_id':record['id'],'plan':plan,'result':record['result'],'scope':'Real local UI execution; automatic validation actor, not factory approval'}
    (ROOT/'docs/evaluation/product_partitions.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    check={'run_id':record['id'],'selected':g['selected']['name'],'partitions':15,'csv_rows':len(rows),
        'console_errors':errors,'duplicate_approval_blocked':True,'test_recall':record['result']['test']['recall']}
    (ROOT/'docs/evaluation/grouping_browser.json').write_text(json.dumps(check,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(check,ensure_ascii=False));browser.close()
