"""Capture live UI evidence without approving or starting any training."""
import json
import sys
from pathlib import Path
import httpx
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'docs/assets'
BASE='http://127.0.0.1:8700'
before=httpx.get(BASE+'/api/runs').json()
receipt={'source':'live local Windows UI','training_started':False,'screens':{}}
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    page=browser.new_page(viewport={'width':1050,'height':1200},device_scale_factor=1)
    page.goto(BASE,wait_until='networkidle')
    page.wait_for_function("!document.querySelector('#load-result').disabled")
    page.locator('#load-result').click()
    page.locator('#next-discovery').wait_for(state='visible',timeout=30000)
    assert '27 / 32' in page.locator('#result').inner_text()
    page.add_style_tag(content='* { scroll-behavior: auto !important; }')
    page.evaluate('window.scrollTo(0,0)')
    page.wait_for_timeout(300)
    # Capture the complete result header, decision and comparison table.
    top=page.locator('#result-section > .section-title').bounding_box()
    end=page.locator('#result > .explanation').bounding_box()
    page.screenshot(path=str(OUT/'app-test-proof.jpg'),type='jpeg',quality=95,full_page=True,
        clip={'x':top['x'],'y':top['y'],'width':top['width'],'height':end['y']+end['height']-top['y']})
    ranking=page.locator('#result > details').filter(has=page.get_by_text('왜 이 모델인가요? 모델별 Validation 비교',exact=True))
    ranking.locator('summary').click()
    page.evaluate('window.scrollTo(0,0)')
    # Top four rows of the actual UI table; the full ranking is in the appendix.
    first=ranking.locator('summary').bounding_box()
    fourth=ranking.locator('tbody tr').nth(3).bounding_box()
    page.screenshot(path=str(OUT/'app-validation-proof.jpg'),type='jpeg',quality=95,full_page=True,
        clip={'x':first['x'],'y':first['y'],'width':first['width'],'height':fourth['y']+fourth['height']-first['y']+8})
    page.locator('#next-discovery').click()
    if '--saved-discovery' in sys.argv:
        # Replay the preserved real retrieval receipt through the current UI.
        # No labels, metrics or evidence text are invented or modified.
        saved=json.loads((ROOT/'docs/evaluation/model_discovery.json').read_text(encoding='utf-8'))['discovery']
        page.route('**/api/model-discovery/search',lambda route:route.fulfill(
            status=200,content_type='application/json',body=json.dumps(saved,ensure_ascii=False)))
        receipt['rag_capture_mode']='Current UI replay of preserved actual retrieval receipt; not a new live search'
        receipt['rag_source']='docs/evaluation/model_discovery.json'
        receipt['rag_original_created_at']=saved['created_at']
    page.locator('#search-models').click()
    page.locator('#discovery-proposal').wait_for(state='visible',timeout=180000)
    details=page.locator('#discovery-result > details')
    details.locator('summary').click()
    page.evaluate('window.scrollTo(0,0)')
    start=page.locator('#discovery-result').bounding_box()
    evidence=details.locator('p').first.bounding_box()
    page.screenshot(path=str(OUT/'app-rag-proof.jpg'),type='jpeg',quality=95,full_page=True,
        clip={'x':start['x'],'y':start['y'],'width':start['width'],'height':evidence['y']+evidence['height']-start['y']+10})
    receipt['run_id']=page.evaluate('currentRun.id')
    receipt['screens']={'app-test-proof.jpg':'Decision and same-Test baseline/candidate comparison',
        'app-validation-proof.jpg':'Actual UI ranking, first four rows; full ranking in appendix',
        'app-rag-proof.jpg':'Retrieved candidate models and first official document evidence; see rag_capture_mode'}
    browser.close()
after=httpx.get(BASE+'/api/runs').json()
assert {x['id'] for x in before}=={x['id'] for x in after},'Unexpected training run'
(ROOT/'docs/evaluation/presentation_screenshots.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(receipt,ensure_ascii=False))
