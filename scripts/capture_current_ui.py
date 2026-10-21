"""Capture the current Windows UI after the requested model wording changes."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent.parent
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    page=browser.new_page(viewport={'width':900,'height':1100},device_scale_factor=1)
    page.goto('http://127.0.0.1:8700',wait_until='networkidle')
    page.wait_for_function("document.querySelectorAll('[data-dataset]').length > 0")
    page.locator('#data-section').screenshot(path=str(ROOT/'docs/assets/app-data.jpg'),type='jpeg',quality=94)
    page.locator('#proposal-form button[type=submit]').click()
    page.locator('#proposal-section').wait_for(state='visible',timeout=150000)
    assert '12종' not in page.locator('#proposal-section').inner_text()
    page.locator('#proposal-section').screenshot(path=str(ROOT/'docs/assets/app-plan.jpg'),type='jpeg',quality=94)
    browser.close()
print('Captured current data and approval screens. No training was started.')
