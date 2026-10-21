"""Exercise plan -> real approval -> weight search -> visible evidence and CSV."""
import csv
import io
import json
from pathlib import Path
import httpx
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent.parent
BASE='http://127.0.0.1:8700'
source=json.loads((ROOT/'docs/evaluation/windows_llm_synthetic.json').read_text(encoding='utf-8'))['run_id']
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    page=browser.new_page(viewport={'width':1050,'height':1200},device_scale_factor=1)
    errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
    page.goto(BASE,wait_until='networkidle')
    page.wait_for_function('datasets.length>0')
    page.evaluate('(id)=>watch(id)',source)
    page.locator('#ensemble-proposal').click()
    page.locator('#proposal-section').wait_for(state='visible')
    assert '232' in page.locator('#proposal-section').inner_text()
    page.locator('#engineer').fill('G045 UI 자동검증 승인자')
    page.locator('#proposal-section').screenshot(path=str(ROOT/'docs/assets/app-ensemble-plan.jpg'),type='jpeg',quality=95)
    proposal_id=page.evaluate('proposal.id');plan_hash=page.evaluate('proposal.plan_hash')
    page.locator('#approve').click()
    page.locator('#ensemble-recommendation').wait_for(state='visible',timeout=180000)
    page.locator('#ensemble-recommendation').screenshot(path=str(ROOT/'docs/assets/app-ensemble-summary.jpg'),type='jpeg',quality=95)
    page.locator('#ensemble-validation').screenshot(path=str(ROOT/'docs/assets/app-ensemble-validation.jpg'),type='jpeg',quality=95)
    page.locator('#ensemble-test').screenshot(path=str(ROOT/'docs/assets/app-ensemble-test.jpg'),type='jpeg',quality=95)
    record=page.evaluate('currentRun')
    plan=httpx.get(BASE+f'/api/proposals/{proposal_id}').json()['plan']
    assert record['status']=='completed'
    e=record['result']['ensemble']
    assert e['selection_uses_test'] is False
    assert 'NaN' not in page.locator('#result').inner_text()
    assert abs(sum(m['weight'] for m in e['members'])-1)<1e-12
    response=httpx.post(BASE+f'/api/proposals/{proposal_id}/decision',json={
        'accepted':True,'engineer':'duplicate test','plan_hash':plan_hash})
    assert response.status_code==400
    exported=httpx.get(BASE+f'/api/runs/{record["id"]}/export.csv')
    rows=list(csv.DictReader(io.StringIO(exported.text)))
    assert len(rows)==e['weight_count'] and 'weights' in rows[0] and 'validation_f1' in rows[0]
    assert not errors,errors
    receipt={'run_id':record['id'],'plan':plan,'result':record['result'],
             'scope':'Real local Chrome UI plan and automatic validation actor approval; not factory approval'}
    (ROOT/'docs/evaluation/weighted_ensemble.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    check={'ui_plan_and_approval':True,'csv_weights':len(rows),'duplicate_approval_blocked':True,
           'console_errors':errors,'weights':e['weights_description'],'run_id':record['id']}
    (ROOT/'docs/evaluation/ensemble_browser.json').write_text(json.dumps(check,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(check,ensure_ascii=False))
    browser.close()
