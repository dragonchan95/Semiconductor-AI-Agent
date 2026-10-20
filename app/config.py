import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = Path(os.environ.get("STATE_DIR", ROOT / "var"))
STATE_DIR.mkdir(parents=True, exist_ok=True)
MAX_TRIALS = 72
MAX_ROWS = 20000
MAX_UPLOAD_BYTES = 30 * 1024 * 1024
SEED = 45
