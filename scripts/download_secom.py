"""Official UCI data, CC BY 4.0. Fetch once; no runtime external data transfer."""
import hashlib
import json
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
URL = "https://archive.ics.uci.edu/static/public/179/secom.zip"


def prepare():
    target = ROOT / "data/public"
    target.mkdir(parents=True, exist_ok=True)
    archive = target / "secom.zip"
    if not archive.exists():
        urllib.request.urlretrieve(URL, archive)
    with zipfile.ZipFile(archive) as z:
        for name in ["secom.data", "secom_labels.data", "secom.names"]:
            (target / "secom").mkdir(exist_ok=True)
            (target / "secom" / name).write_bytes(z.read(name))
    receipt = {"source": URL, "license": "CC BY 4.0", "citation": "McCann, M. & Johnston, A. (2008). SECOM. UCI. doi:10.24432/C54305",
               "sha256": hashlib.sha256(archive.read_bytes()).hexdigest()}
    (target / "provenance.json").write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(receipt)


if __name__ == "__main__":
    prepare()
