"""Self-contained HTML and a readable PDF of the detailed five-section report."""
import base64
import json
from pathlib import Path
from urllib.parse import urljoin

from markdown_it import MarkdownIt
import pymupdf
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT/'docs'
BASE = 'https://github.com/dragonchan95/Semiconductor-AI-Agent/blob/main/docs/'

ARCHITECTURE = '''<div class="architecture">
  <div class="step">검사 데이터 선택 → 데이터 점검</div><div class="arrow">↓</div>
  <div class="step">RAG: BGE-M3 임베딩 → FAISS 근거 검색 → 로컬 Qwen 설명</div><div class="arrow">↓</div>
  <div class="step">실험 계획 확인 → 엔지니어 승인 → Train 학습·Validation 비교</div><div class="arrow">↓</div>
  <div class="branches"><div class="step">실험1: 알고리즘 고정<br>제품 담당 그룹15개 비교</div>
  <div class="step">실험2: 학습 제품ABCD 고정<br>예측 혼합 비율232개 비교</div></div><div class="arrow">↓</div>
  <div class="step">Validation에서 선택 고정 → 같은 Test 확인 → 결과·실패·보류 기록</div>
  <div class="arrow">↓</div><div class="step">새 정답 배치로 기존 모델 점검 → 승인 재학습 → 같은 Test 전후 비교 → 후보 저장</div><p>MCP: 조회·계획 도구 / Resource · LangSmith: 실행 추적 · LLM 설명 검사 + 코드 수치·승인 검사</p>
</div>'''


def main():
    parser = MarkdownIt('commonmark').enable('table')
    tokens = parser.parse((DOCS/'REPORT.md').read_text(encoding='utf-8'))
    original_fence = parser.renderer.rules['fence']

    def fence(items, index, options, env):
        return ARCHITECTURE if items[index].info.strip() == 'mermaid' else original_fence(items, index, options, env)

    parser.renderer.rules['fence'] = fence
    for token in tokens:
        for child in token.children or []:
            if child.type == 'image':
                path = DOCS/child.attrGet('src')
                mime = 'image/jpeg' if path.suffix == '.jpg' else 'image/png'
                child.attrSet('src', 'data:'+mime+';base64,'+base64.b64encode(path.read_bytes()).decode())
            elif child.type == 'link_open':
                child.attrSet('href', urljoin(BASE, child.attrGet('href')))
    body = parser.renderer.render(tokens, parser.options, {})
    css = '''
@page {size:A4; margin:16mm 13mm 17mm}
* {box-sizing:border-box}
body {max-width:190mm;margin:auto;color:#173a49;font-family:"Arial Unicode MS","Malgun Gothic",sans-serif;font-size:10pt;line-height:1.65;overflow-wrap:anywhere}
h1 {font-size:23pt;line-height:1.4;color:#173a49;border-bottom:3px solid #167d84;padding-bottom:12px}
h2 {font-size:15pt;color:#167d84;border-bottom:1px solid #c9dadd;margin:24px 0 12px;break-after:avoid}
h3 {font-size:12pt;margin-top:20px;break-after:avoid}
p {margin:9px 0} a {color:#136d91;text-decoration:none}
table {border-collapse:collapse;width:100%;margin:12px 0;font-size:8pt;line-height:1.55;table-layout:fixed}
th,td {border:1px solid #c9dadd;padding:7px;vertical-align:top}
th {background:#e7f1f2;color:#173a49} tr {break-inside:avoid} thead {display:table-header-group}
img {display:block;max-width:100%;max-height:112mm;object-fit:contain;margin:12px auto;break-inside:avoid}
ul,ol {padding-left:23px} li {margin:6px 0} pre {white-space:pre-wrap;font-size:8pt}
.purpose {padding:10px 14px;background:#edf5f6;border-left:4px solid #167d84;font-size:10pt}
.architecture {break-inside:avoid;margin:15px 0;text-align:center;font-size:9pt}
.step {background:#edf5f6;border:1px solid #a8c8ce;border-radius:6px;padding:10px}
.arrow {font-size:15pt;color:#167d84;line-height:1.5}
.branches {display:flex;gap:14px}.branches>.step {width:50%}
.architecture p {font-size:8pt}
@media screen {body{padding:24px;background:white}html{background:#e6edef}}
'''
    html = '<!doctype html><html lang="ko"><meta charset="utf-8"><title>G045 최종 보고서</title><style>'+css+'</style><body>'
    html += '<div class="purpose"><strong>상세 제출용 최종 보고서</strong><br>5분 발표는 별도의 발표 PPTX·PDF 본문1~12장을 사용합니다. 프로젝트와 실험 결과는 같습니다.</div>'
    html += body+'</body></html>'
    html_path = DOCS/'G045_Final_Report.html'
    pdf_path = DOCS/'G045_Final_Report.pdf'
    html_path.write_text(html, encoding='utf-8')
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel='chrome', headless=True)
        page = browser.new_page()
        page.goto(html_path.as_uri(), wait_until='load')
        page.evaluate('document.fonts.ready')
        assert page.locator('h2').count() == 5
        assert page.locator('img').evaluate_all('(images)=>images.every(i=>i.complete&&i.naturalWidth>0)')
        page.pdf(path=str(pdf_path), format='A4', print_background=True, display_header_footer=True,
                 header_template='<span></span>',
                 footer_template='<div style="width:100%;text-align:center;font-size:8px;color:#607d86">SKALA G045 · Final Report · <span class="pageNumber"></span> / <span class="totalPages"></span></div>')
        browser.close()
    document = pymupdf.open(pdf_path)
    all_text = ''.join(page.get_text() for page in document)
    assert all(word in all_text for word in ['1. 표지', '2. 문제', '3. 적용', '4. 구현', '5. 교훈', 'BGE-M3', 'FAISS'])
    assert '\ufffd' not in all_text
    receipt = {'artifact': 'docs/G045_Final_Report.pdf', 'html_self_contained': True,
               'pages': len(document), 'required_sections': 5, 'screens': 9,
               'architecture': 'Printable flow diagram equivalent to the report Mermaid branches',
               'purpose': 'Detailed submission report; separate from the five-minute slide deck',
               'no_replacement_characters': True}
    (DOCS/'evaluation/final_report_check.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == '__main__':
    main()
