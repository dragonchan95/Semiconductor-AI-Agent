"""Verify the local UI's result, ranking and next-action flow with Chrome."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent.parent
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    page=browser.new_page(viewport={'width':1440,'height':1000},device_scale_factor=1)
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://127.0.0.1:8700',wait_until='networkidle')
    page.locator('#load-result').wait_for(state='visible')
    page.wait_for_function("!document.querySelector('#load-result').disabled")
    page.locator('#load-result').click()
    page.locator('#next-discovery').wait_for(state='visible',timeout=30000)
    assert '12종' not in page.locator('#model-hint').inner_text()
    page.get_by_text('왜 이 모델인가요? 모델별 Validation 비교',exact=True).click()
    ranking=page.locator('#result > details').filter(has=page.get_by_text('왜 이 모델인가요? 모델별 Validation 비교',exact=True))
    assert ranking.get_by_text('AdaBoost',exact=True).count()==1
    page.locator('#next-discovery').click()
    assert page.locator('#discovery-features').evaluate('(el)=>el.open')
    assert page.locator('#next-review').count()==0
    assert not page.locator('#management-features').evaluate('(el)=>el.open')
    page.locator('#next-plan').click()
    assert page.locator('#proposal-form details').first.evaluate('(el)=>el.open')
    assert not errors,errors
    out=ROOT/'var/browser-check';out.mkdir(exist_ok=True)
    page.locator('#result-section').screenshot(path=str(out/'windows-result.png'))
    page.locator('#view-ensemble').click()
    page.locator('#ensemble-recommendation').wait_for(state='visible',timeout=30000)
    assert 'NaN' not in page.locator('#ensemble-recommendation').inner_text()
    assert '90.0%' in page.locator('.ensemble-weights').inner_text()
    page.locator('#back-to-models').click()
    page.locator('#ensemble-proposal').wait_for(state='visible',timeout=30000)
    page.locator('#view-grouping').click()
    page.locator('#grouping-summary').wait_for(state='visible',timeout=30000)
    assert 'A+B+C / D' in page.locator('#grouping-summary').inner_text()
    assert '적용 보류' in page.locator('#grouping-test').inner_text()
    page.locator('#back-to-models').click()
    page.locator('#grouping-proposal').wait_for(state='visible',timeout=30000)
    assert not errors,errors
    receipt={'browser':'Chrome headless','console_errors':errors,'result_loaded':True,
             'validation_ranking_visible':True,'next_discovery':True,'retraining_outside_main_flow':True,
             'change_goal':True,'main_wording_uses_generic_model_comparison':True,
             'saved_ensemble_loaded_and_returned_to_source':True,
             'saved_product_grouping_loaded_and_returned_to_source':True}
    (ROOT/'docs/evaluation/browser_check.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(receipt,ensure_ascii=False))
    browser.close()
