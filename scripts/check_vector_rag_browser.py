"""Render a preserved real BGE/FAISS retrieval through the current UI.

The search response is replayed; this browser run does not claim a fresh fetch.
The real official fetch and Qwen call are in verify_vector_rag.py's receipt.
"""
import json
from pathlib import Path
import sys
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
record = json.loads((ROOT/'docs/evaluation/vector_rag.json').read_text(encoding='utf-8'))
discovery = record['external_discovery']
live = '--live' in sys.argv
source = json.loads((ROOT/'docs/evaluation/windows_llm_synthetic.json').read_text(encoding='utf-8'))['run_id']
with sync_playwright() as p:
    browser = p.chromium.launch(channel='chrome', headless=True)
    page = browser.new_page(viewport={'width': 1250, 'height': 1400})
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    if not live:
        page.route('**/api/model-discovery/search', lambda route: route.fulfill(
            status=200, content_type='application/json', body=json.dumps(discovery, ensure_ascii=False)))
    page.goto('http://127.0.0.1:8700', wait_until='networkidle')
    page.wait_for_function('datasets.length>0')
    page.evaluate('(id)=>watch(id)', source)
    page.locator('#next-discovery').click()
    page.locator('#search-models').click()
    page.locator('#discovery-proposal').wait_for(state='visible', timeout=180000 if live else 30000)
    if live:
        discovery = page.evaluate('discoveryState')
        assert discovery['retrieval_status']['mode'] == 'bge_m3_faiss'
    assert 'BGE-M3 임베딩 + FAISS 의미 검색' in page.locator('#discovery-result').inner_text()
    assert discovery['agent']['status'] == 'verified'
    page.locator('#discovery-result details').evaluate('(el)=>el.open=true')
    if not live:
        page.locator('#discovery-result').evaluate("el=>el.insertAdjacentHTML('afterbegin','<p><strong>저장된 실제 BGE-M3·FAISS 검색 기록 · 현재 UI 재현</strong></p>')")
    capture = ROOT/'var/browser-check/rag-live.jpg' if live else ROOT/'docs/assets/app-rag-proof.jpg'
    page.locator('#discovery-result').screenshot(path=str(capture), type='jpeg', quality=95)
    assert not errors, errors
    receipt = {'source': 'Live local API and Chrome UI: official GET + BGE-M3/FAISS + Qwen' if live else 'Current UI replay of actual local BGE-M3/FAISS + official GET + Qwen receipt',
               'fresh_browser_search': live, 'actual_retrieval_source': 'live local API' if live else 'docs/evaluation/vector_rag.json',
               'original_created_at': discovery['created_at'], 'discovery_id': discovery['id'],
               'retrieval_mode_visible': True, 'llm_status': discovery['agent']['status'], 'console_errors': errors}
    name = 'vector_rag_browser_live.json' if live else 'vector_rag_browser.json'
    (ROOT/'docs/evaluation'/name).write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
    if not live:
        existing = json.loads((ROOT/'docs/evaluation/presentation_screenshots.json').read_text(encoding='utf-8'))
        existing.update(rag_capture_mode=receipt['source'], rag_source=receipt['actual_retrieval_source'],
                        rag_original_created_at=discovery['created_at'])
        (ROOT/'docs/evaluation/presentation_screenshots.json').write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(receipt, ensure_ascii=False))
    browser.close()
