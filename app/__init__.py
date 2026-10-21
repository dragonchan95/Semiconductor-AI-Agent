"""Semiconductor Experiment Copilot."""
import os
from pathlib import Path

from dotenv import load_dotenv

# Load before importing modules with @traceable decorators. Process settings win.
load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=False)
if os.getenv("LANGSMITH_API_KEY"):
    os.environ.setdefault("LANGSMITH_ENDPOINT", "https://apac.api.smith.langchain.com")
    os.environ.setdefault("LANGSMITH_PROJECT", "Semiconductor-AI-Agent-G045")
