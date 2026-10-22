"""Semiconductor Experiment Copilot."""
import os
from pathlib import Path

# Set before numpy/sklearn/FAISS/PyTorch load their OpenMP runtimes.
# Apple Silicon wheels can bundle different libomp builds; keep this small
# local demo single-threaded instead of bypassing duplicate-runtime checks.
for _name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS",
              "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_name, "1")

from dotenv import load_dotenv

# Load before importing modules with @traceable decorators. Process settings win.
load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=False)
if os.getenv("LANGSMITH_API_KEY"):
    os.environ.setdefault("LANGSMITH_ENDPOINT", "https://apac.api.smith.langchain.com")
    os.environ.setdefault("LANGSMITH_PROJECT", "Semiconductor-AI-Agent-G045")
