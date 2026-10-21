import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

from .config import MAX_ROWS, ROOT, SEED
from .store import digest

META = {"label", "product", "lot_id", "timestamp", "image_path", "sample_id"}


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_frame(dataset):
    path = Path(dataset["path"])
    if file_hash(path) != dataset["sha256"]:
        raise ValueError("등록 후 데이터가 변경됐습니다. 다시 등록하고 승인해 주세요")
    df = pd.read_csv(path)
    if "product" in df:
        df["product"] = df["product"].astype(str)
    if dataset.get("image_digest"):
        actual = image_digest(df, path.parent)
        if actual != dataset["image_digest"]:
            raise ValueError("승인 후 이미지가 변경됐습니다")
    return df


def image_digest(df, root):
    root = Path(root).resolve()
    rows = []
    for name in df.image_path:
        p = (root / str(name)).resolve()
        if not p.is_relative_to(root):
            raise ValueError("이미지는 manifest 폴더 안에 있어야 합니다")
        rows.append([str(name), file_hash(p)])
    return digest(rows)


def audit_frame(df, modality="tabular"):
    if not 80 <= len(df) <= MAX_ROWS:
        raise ValueError(f"데이터는 80~{MAX_ROWS}행이어야 합니다")
    if "label" not in df or df.label.isna().any() or not set(df.label.unique()) <= {0, 1}:
        raise ValueError("label은 정상=0, 불량=1이며 누락될 수 없습니다")
    if df.label.nunique() != 2 or int(df.label.sum()) < 12:
        raise ValueError("정상과 불량이 모두 필요하고 불량 표본이 12개 이상이어야 합니다")
    if "product" not in df or df["product"].isna().any():
        raise ValueError("product 열이 필요합니다. 실제 제품 정보가 없으면 단일 집단으로 표시하세요")
    if len(df["product"].unique()) > 4:
        raise ValueError("이번 PoC는 최대 4개 제품을 비교합니다")
    if modality == "image":
        if "image_path" not in df:
            raise ValueError("이미지 manifest에는 image_path가 필요합니다")
        features = ["image_path"]
        missing = 0.0
    else:
        features = [c for c in df if c not in META]
        if not features or len(features) > 1000:
            raise ValueError("숫자 센서 특성 1~1000개가 필요합니다")
        numeric = df[features].apply(pd.to_numeric, errors="raise")
        if np.isinf(numeric.to_numpy(dtype=float)).any():
            raise ValueError("무한대 값은 허용하지 않습니다")
        if (numeric.notna().sum(axis=1) == 0).any():
            raise ValueError("모든 센서값이 누락된 행이 있습니다")
        missing = float(numeric.isna().mean().mean())
        if numeric.duplicated().any():
            raise ValueError("동일한 센서 행이 중복됩니다. lot 간 복제·누수를 먼저 정리하세요")
    counts = {str(k): int(v) for k, v in df.groupby("product").size().items()}
    warnings = []
    ratio = float(df.label.mean())
    if ratio < 0.2:
        warnings.append(f"불량 비율 {ratio:.1%}: 정확도만으로 선택하지 않고 가중치·임계값을 비교합니다")
    if missing:
        warnings.append(f"센서 결측 {missing:.1%}: 결측 대체·스케일러는 학습 파티션에서만 적합합니다")
    if "lot_id" not in df and "timestamp" not in df:
        raise ValueError("누수 방지를 위해 lot_id 또는 timestamp가 필요합니다")
    if "timestamp" in df and df.timestamp.isna().any():
        raise ValueError("timestamp에 누락된 시각이 있습니다")
    if "lot_id" in df and (df.lot_id.isna().any() or df.lot_id.nunique() < 16):
        raise ValueError("lot_id에는 누락이 없고 서로 다른 lot이 16개 이상이어야 합니다")
    return {"rows": len(df), "features": len(features), "defects": int(df.label.sum()),
            "defect_ratio": ratio, "missing_ratio": missing, "products": counts,
            "warnings": warnings, "feature_names": features, "modality": modality}


def split_frame(df):
    """Train / Validation / Test. One lot never crosses a boundary. Timestamp-only uses
    date blocks, preventing equal-time records from crossing a boundary.
    """
    if "lot_id" in df:
        groups = df.lot_id.astype(str)
        remaining = np.arange(len(df))
        parts = {}
        for name, size in [("test", .20), ("validation", .20 / .80)]:
            a, b = next(GroupShuffleSplit(n_splits=1, test_size=size, random_state=SEED).split(
                remaining, groups=groups.iloc[remaining]))
            parts[name] = remaining[b]
            remaining = remaining[a]
        parts["train"] = remaining
        method = "lot_group_holdout"
    else:
        # ISO dates must not be interpreted with dayfirst=True (2026-01-13).
        iso = df.timestamp.astype(str).str.match(r"^\d{4}-\d{2}-\d{2}").all()
        times = pd.to_datetime(df.timestamp, format="ISO8601" if iso else "mixed",
                               dayfirst=not iso, errors="raise")
        blocks = sorted(times.dt.date.unique())
        if len(blocks) < 16:
            raise ValueError("시간 분할에는 서로 다른 날짜가 16일 이상 필요합니다")
        cut = [int(len(blocks) * x) for x in [.60, .80]]
        chunks = np.split(np.array(blocks, dtype=object), cut)
        parts = {name: np.flatnonzero(times.dt.date.isin(chunk).to_numpy())
                 for name, chunk in zip(["train", "validation", "test"], chunks)}
        method = "chronological_date_holdout"
    for name, idx in parts.items():
        labels = df.iloc[idx].label
        if labels.nunique() < 2 or int(labels.sum()) < 3:
            raise ValueError(f"{name}에 불량과 정상 표본이 충분하지 않습니다. 데이터 기간·lot을 보강하세요")
    summary = {name: {"rows": len(idx), "defects": int(df.iloc[idx].label.sum()),
                      "index_hash": digest(sorted(map(int, idx)))} for name, idx in parts.items()}
    summary["method"] = method
    summary["target_ratios"] = {"train": .60, "validation": .20, "test": .20}
    return parts, summary


def generate_demo(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    rows = []
    for lot in range(160):
        product = "ABCD"[lot % 4]
        offset = "ABCD".index(product)
        for j in range(8):
            x = rng.normal(0, 1, 8)
            # Synthetic process/domain shifts are deliberate demonstration data.
            signal = x[0] + .7 * x[1] + .45 * x[2] ** 2 + .18 * offset + rng.normal(0, .4)
            label = int(signal > 2.1)
            x[3] += offset * .8
            record = {"sample_id": f"demo-{lot}-{j}", "product": product,
                      "lot_id": f"lot-{lot:03d}", "timestamp": f"2026-01-{1+lot//8:02d}", "label": label}
            record.update({f"sensor_{i}": float(v) for i, v in enumerate(x)})
            if rng.random() < .15:
                record["sensor_6"] = None
            rows.append(record)
    path = directory / "process_demo.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def import_secom(directory):
    source = ROOT / "data/public/secom"
    if not (source / "secom.data").exists():
        raise ValueError("scripts/download_secom.py를 먼저 실행하세요")
    x = pd.read_csv(source / "secom.data", sep=r"\s+", header=None)
    x = x.copy()
    # The date and time form one quoted field in the official file.
    labels = pd.read_csv(source / "secom_labels.data", sep=r"\s+", header=None,
                         names=["outcome", "timestamp"])
    x.columns = [f"sensor_{i:03d}" for i in range(x.shape[1])]
    x["label"] = (labels.outcome == 1).astype(int)
    x["product"] = "SECOM"
    x["timestamp"] = pd.to_datetime(labels.timestamp, format="%d/%m/%Y %H:%M:%S").dt.strftime("%Y-%m-%dT%H:%M:%S")
    x["sample_id"] = [f"secom-{i}" for i in range(len(x))]
    path = Path(directory) / "secom.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    x.to_csv(path, index=False)
    return path
