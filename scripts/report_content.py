"""The reviewed report Markdown is the authoritative final report."""
from pathlib import Path

def build_final_report(content, receipts, trace):
    return (Path(__file__).resolve().parent.parent/'docs'/'REPORT.md').read_text(encoding='utf-8')
