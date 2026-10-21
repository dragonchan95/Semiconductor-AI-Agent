"""Small scratch-trained architecture experiments, not pretrained ResNet/VGG
benchmark claims. No image augmentation occurs outside training.
"""
import itertools
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from PIL import Image
from torch import nn

from .config import MAX_TRIALS, SEED
from .metrics import choose_threshold, measure, operational_gate, meets_goals, selection_key
from .store import digest


class ResidualBlock(nn.Module):
    def __init__(self, channels):
        super().__init__()
        self.layers = nn.Sequential(nn.Conv2d(channels, channels, 3, padding=1), nn.ReLU(),
                                    nn.Conv2d(channels, channels, 3, padding=1))

    def forward(self, x):
        return torch.relu(x + self.layers(x))


class ResNetSmall(nn.Module):
    def __init__(self):
        super().__init__()
        self.layers = nn.Sequential(nn.Conv2d(1, 8, 3, padding=1), nn.ReLU(), ResidualBlock(8),
            nn.MaxPool2d(2), nn.Conv2d(8, 16, 3, padding=1), nn.ReLU(), ResidualBlock(16),
            nn.AdaptiveAvgPool2d(1), nn.Flatten(), nn.Linear(16, 1))

    def forward(self, x):
        return self.layers(x).squeeze(1)


class VGGSmall(nn.Module):
    def __init__(self):
        super().__init__()
        self.layers = nn.Sequential(nn.Conv2d(1, 8, 3, padding=1), nn.ReLU(),
            nn.Conv2d(8, 8, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(8, 16, 3, padding=1), nn.ReLU(), nn.Conv2d(16, 16, 3, padding=1),
            nn.ReLU(), nn.MaxPool2d(2), nn.Flatten(), nn.Linear(16 * 8 * 8, 1))

    def forward(self, x):
        return self.layers(x).squeeze(1)


class Autoencoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.layers = nn.Sequential(nn.Conv2d(1, 8, 3, stride=2, padding=1), nn.ReLU(),
            nn.Conv2d(8, 4, 3, stride=2, padding=1), nn.ReLU(),
            nn.ConvTranspose2d(4, 8, 4, stride=2, padding=1), nn.ReLU(),
            nn.ConvTranspose2d(8, 1, 4, stride=2, padding=1), nn.Sigmoid())

    def forward(self, x):
        return self.layers(x)


def load_images(df, root, preprocessing):
    images = []
    root = Path(root).resolve()
    hashes = set()
    import hashlib
    for item in df.image_path:
        path = (root / str(item)).resolve()
        if not path.is_relative_to(root) or path.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
            raise ValueError("허용된 이미지 경로가 아닙니다")
        with Image.open(path) as image:
            if image.width * image.height > 16_000_000:
                raise ValueError("이미지가 너무 큽니다")
            array = np.array(image.convert("L").resize((32, 32)), dtype=np.float32) / 255
        raw_hash = hashlib.sha256(array.tobytes()).hexdigest()
        if raw_hash in hashes:
            raise ValueError("중복 이미지가 있습니다. lot 분할 전 중복을 정리하세요")
        hashes.add(raw_hash)
        if preprocessing == "contrast":
            low, high = np.quantile(array, [.02, .98])
            array = np.clip((array - low) / max(float(high - low), .01), 0, 1)
        elif preprocessing != "gray":
            raise ValueError("이미지 전처리는 gray 또는 contrast입니다")
        images.append(array)
    return torch.from_numpy(np.stack(images).astype(np.float32)[:, None, :, :])


def generate_images(directory):
    directory = Path(directory)
    (directory / "images").mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    yy, xx = np.mgrid[:32, :32]
    records = []
    for lot in range(96):
        product = "ABCD"[lot % 4]
        k = "ABCD".index(product)
        for j in range(6):
            label = int(rng.random() < .16)
            base = .25 + k * .1 + .1 * np.sin(xx / (2.5 + k * .2))
            image = base + rng.normal(0, .025, (32, 32))
            if label:
                x, y = rng.integers(6, 24, size=2)
                image[y:y + 4, x:x + 8] += .45
            name = f"images/{lot:03d}-{j}.png"
            Image.fromarray((np.clip(image, 0, 1) * 255).astype(np.uint8)).save(directory / name)
            records.append({"sample_id": f"image-{lot}-{j}", "image_path": name,
                            "product": product, "lot_id": f"image-lot-{lot}", "label": label})
    path = directory / "manifest.csv"
    pd.DataFrame(records).to_csv(path, index=False)
    return path


def run_images(dataset, df, parts, evaluation, plan, artifact_dir, on_event):
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    root = Path(dataset["path"]).parent
    y = df.label.to_numpy(dtype=int)
    policy = plan["policy"]
    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    configs = list(itertools.product(plan["cohorts"], plan["models"], plan["preprocessing"], plan["balance"]))
    if len(configs) > MAX_TRIALS:
        raise ValueError("이미지 실험 예산 초과")
    tensors = {prep: load_images(df, root, prep) for prep in plan["preprocessing"]}
    rows, fitted = [], {}
    started_all = time.perf_counter()

    def predict(model, x, mode):
        model.eval()
        with torch.no_grad():
            output = model(x)
            score = (output - x).square().mean((1, 2, 3)) if mode == "autoencoder" else output.sigmoid()
        return score.numpy()

    for i, (products, model_name, prep, balance) in enumerate(configs):
        ident = f"trial-{i+1:03d}"
        torch.manual_seed(SEED)
        rng = np.random.default_rng(SEED)
        idx = parts["train"][np.isin(df.iloc[parts["train"]]["product"], products)]
        if len(idx) < 30 or int(y[idx].sum()) < 4:
            rows.append({"id": ident, "status": "skipped", "reason": "학습 표본 부족"})
            continue
        if model_name not in {"resnet_small", "vgg_small", "autoencoder"}:
            raise ValueError("지원하지 않는 이미지 모델")
        model = {"resnet_small": ResNetSmall, "vgg_small": VGGSmall, "autoencoder": Autoencoder}[model_name]()
        optimizer = torch.optim.Adam(model.parameters(), lr=.002)
        x = tensors[prep]
        weights = float((y[idx] == 0).sum() / max(1, y[idx].sum())) if balance == "weighted" else 1.0
        loss_fn = nn.BCEWithLogitsLoss(pos_weight=torch.tensor(weights))
        train_idx = idx[y[idx] == 0] if model_name == "autoencoder" else idx
        started = time.perf_counter()
        for epoch in range(plan["epochs"]):
            model.train()
            shuffled = rng.permutation(train_idx)
            for batch in np.array_split(shuffled, max(1, int(np.ceil(len(shuffled) / 32)))):
                optimizer.zero_grad()
                output = model(x[batch])
                loss = (output - x[batch]).square().mean() if model_name == "autoencoder" else loss_fn(
                    output, torch.tensor(y[batch], dtype=torch.float32))
                loss.backward()
                optimizer.step()
        cal = evaluation["validation"]
        threshold, feasible = choose_threshold(y[cal], predict(model, x[cal], model_name), policy)
        val = evaluation["validation"]
        metrics = measure(y[val], predict(model, x[val], model_name), threshold, policy)
        row = {"id": ident, "status": "completed", "model": model_name, "products": products,
               "preprocessing": prep, "balance": "normal_only" if model_name == "autoencoder" else balance,
               "train_n": len(train_idx), "train_defects": 0 if model_name == "autoencoder" else int(y[idx].sum()),
               "parameters": sum(p.numel() for p in model.parameters()), "epochs": plan["epochs"],
               "validation": metrics, "validation_feasible": feasible,
               "validation_fingerprint": digest(sorted(map(int, val))), "fit_seconds": time.perf_counter() - started}
        rows.append(row)
        fitted[ident] = (model, threshold, prep)
        on_event({"type": "TrialCompleted", "trial": ident, "model": model_name,
                  "recall": metrics["recall"], "precision": metrics["precision"]})
    complete = [r for r in rows if r["status"] == "completed"]
    if not complete:
        raise ValueError("이미지 후보 학습 불가")
    feasible = [r for r in complete if meets_goals(r['validation'],policy)]
    winner = max(complete,key=lambda r:(*selection_key(r['validation'],policy),r['id']))
    best, threshold, prep = fitted[winner["id"]]
    test = evaluation["test"]
    metrics = measure(y[test], predict(best, tensors[prep][test], winner["model"]), threshold, policy)
    # Declared image baseline: first approved ResNet candidate, fixed 0.5 threshold.
    first = next(r for r in complete if r["model"] != "autoencoder")
    baseline_model, _, baseline_prep = fitted[first["id"]]
    baseline = measure(y[test], predict(baseline_model, tensors[baseline_prep][test], first["model"]), .5, policy)
    torch.save(best.state_dict(), artifact_dir / "champion.pt")
    from .catalog import pipeline_reason
    result = {"dataset": {k: dataset[k] for k in ["id", "name", "source", "synthetic", "sha256"]},
              "winner_id": winner["id"], "winner": winner, "trials": rows, "test": metrics,
              "baseline_test": baseline, "selection_feasible": bool(feasible),
              "test_fingerprint": digest(sorted(map(int, test))), "gate": operational_gate(metrics, policy),
              "split": {name: {"rows": len(idx), "index_hash": digest(sorted(map(int, idx)))} for name, idx in parts.items()},
              "elapsed_seconds": time.perf_counter() - started_all, "seed": SEED,
              "architecture_note": "ResNetSmall/VGGSmall은 축소 자체 구조를 처음부터 학습. ResNet18/VGG16 사전학습 성능 비교가 아님.",
              "scope_note": "합성 이미지 데모. 실제 검사 이미지 성능으로 일반화할 수 없음.",
}
    result['explanation'] = {**pipeline_reason(winner['model'], winner['preprocessing'], winner['balance']),
        'selection_reason': '같은 Validation에서 데모 목표 충족 여부, 불량 검출률, 정상 오판률 순으로 비교. 완전 동률은 trial ID로 결정',
        'search_note': '같은 이미지 평가 표본에서 승인한 전처리·모델 후보를 비교. 단순한 합성 패턴 결과를 현장 성능으로 일반화하지 않음'}
    if not feasible:
        result["gate"] = {"passed": False, "reasons": ["Validation에서 두 데모 목표를 만족한 후보 없음"],
                          "action": "배포 보류·학습 데이터와 기준 재검토", "auto_deploy": False}
    (artifact_dir / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    return result
