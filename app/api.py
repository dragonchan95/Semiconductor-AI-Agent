import asyncio
import csv
import io
import json
import os
import secrets
import uuid
import zipfile
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile, Request
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .config import MAX_UPLOAD_BYTES, ROOT, STATE_DIR
from .planner import ProposalRequest
from .workbench import Workbench
from .impact import ImpactRequest, compare_impact
from .monitoring import prepare_changed_demo, assess, product_plans, compare_strategies

TOKEN = os.environ.get("ENGINEER_TOKEN", "")
if os.environ.get("APP_ENV") == "production" and not TOKEN:
    raise RuntimeError("production에서는 ENGINEER_TOKEN이 필수입니다")


def authorize(request: Request, x_engineer_token: str = Header(default="")):
    if not request.url.path.startswith("/api"):
        return
    if TOKEN and not secrets.compare_digest(x_engineer_token, TOKEN):
        raise HTTPException(401, "엔지니어 토큰이 필요합니다")


@asynccontextmanager
async def lifespan(app):
    app.state.workbench = Workbench(STATE_DIR)
    app.state.executor = ThreadPoolExecutor(max_workers=1)
    # An interrupted process never auto-resumes an approved training job.
    for run in app.state.workbench.store.runs():
        if run["status"] == "running":
            app.state.workbench.store.finish_run(run["id"], {"error": "서버 재시작으로 중단. 새 제안과 승인이 필요합니다"}, True)
    yield
    app.state.executor.shutdown(wait=False, cancel_futures=True)


app = FastAPI(title="Semiconductor Experiment Copilot", version="1.0.0", lifespan=lifespan,
              dependencies=[Depends(authorize)] if TOKEN else [])
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


@app.exception_handler(ValueError)
async def invalid(_, exc):
    return JSONResponse({"detail": str(exc)}, status_code=400)


@app.exception_handler(KeyError)
async def missing(_, exc):
    return JSONResponse({"detail": str(exc)}, status_code=404)


@app.get("/")
def home():
    return FileResponse(ROOT / "static/index.html")


@app.get("/health")
def health():
    return {"status": "ok", "mode": "authenticated" if TOKEN else "local_demo",
            "cloud_connected": False, "external_llm_calls": False,
            "approval_required": True, "auto_deploy": False}


@app.get("/api/datasets")
def datasets():
    return [{k: v for k, v in d.items() if k != "path"} for d in app.state.workbench.store.datasets()]


@app.post("/api/examples", dependencies=[Depends(authorize)])
def examples():
    app.state.workbench.ensure_examples()
    return datasets()


@app.post("/api/datasets", dependencies=[Depends(authorize)])
async def upload(file: UploadFile = File(...)):
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "업로드는 30MB 이하여야 합니다")
    name = Path(file.filename or "upload").name
    directory = STATE_DIR / "uploads" / uuid.uuid4().hex
    directory.mkdir(parents=True)
    wb = app.state.workbench
    if name.lower().endswith(".csv"):
        path = directory / "data.csv"
        path.write_bytes(content)
        record = wb.register(path, name, "사용자 업로드, 사용 권한과 데이터 정의는 제공자가 확인", False)
    elif name.lower().endswith(".zip"):
        try:
            archive = zipfile.ZipFile(io.BytesIO(content))
        except zipfile.BadZipFile as exc:
            raise ValueError("유효한 ZIP 파일이 아닙니다") from exc
        if sum(f.file_size for f in archive.infolist()) > 128 * 1024 * 1024 or len(archive.infolist()) > 5000:
            raise ValueError("이미지 ZIP의 압축 해제 크기 또는 파일 수가 너무 큽니다")
        for item in archive.infolist():
            target = (directory / item.filename).resolve()
            if not target.is_relative_to(directory.resolve()) or (item.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError("ZIP 경로 또는 심볼릭 링크는 허용하지 않습니다")
            if not item.is_dir() and target.suffix.lower() not in {".csv", ".jpg", ".jpeg", ".png"}:
                raise ValueError("ZIP에는 manifest.csv와 검사 이미지 파일만 포함할 수 있습니다")
        archive.extractall(directory)
        path = directory / "manifest.csv"
        if not path.exists():
            raise ValueError("ZIP 최상위에 manifest.csv가 필요합니다")
        record = wb.register(path, name, "사용자 업로드 이미지, 공정 조건·장비별 현장 검증 필요", False, "image")
    else:
        raise ValueError("CSV 또는 manifest.csv를 포함한 이미지 ZIP을 업로드하세요")
    return {k: v for k, v in record.items() if k != "path"}


@app.post("/api/proposals", dependencies=[Depends(authorize)])
def propose(req: ProposalRequest):
    return app.state.workbench.propose(req)


@app.get("/api/proposals/{ident}")
def proposal(ident: str):
    return app.state.workbench.store.proposal(ident)


class Decision(BaseModel):
    accepted: bool
    engineer: str = Field(min_length=1, max_length=80)
    plan_hash: str = Field(min_length=64, max_length=64)


@app.post("/api/proposals/{ident}/decision", dependencies=[Depends(authorize)])
def decide(ident: str, req: Decision):
    wb = app.state.workbench
    proposal = wb.store.decide(ident, req.plan_hash, req.accepted, req.engineer)
    if not req.accepted:
        return {"proposal": proposal, "run_id": None}
    run_id = wb.store.claim_run(ident)
    def worker():
        try:
            wb.perform(ident, run_id, lambda event: wb.store.event(run_id, event["type"], event))
        except Exception:
            pass  # Failure is persisted and returned through run status.
    app.state.executor.submit(worker)
    return {"proposal": proposal, "run_id": run_id}


@app.get("/api/runs")
def runs():
    return app.state.workbench.store.runs()


@app.get("/api/runs/{ident}")
def run(ident: str):
    return app.state.workbench.store.run(ident)


@app.post('/api/runs/{ident}/impact')
def impact(ident: str, req: ImpactRequest):
    record = app.state.workbench.store.run(ident)
    if record['status'] != 'completed':
        raise ValueError('완료된 실험의 성능으로만 계산할 수 있습니다')
    plan = app.state.workbench.store.proposal(record['proposal_id'])['plan']
    return compare_impact(record['result'], req, plan['policy'])


class ModelReviewRequest(BaseModel):
    source_run: str
    dataset_id: str


@app.post('/api/model-management/example')
def management_example():
    d = prepare_changed_demo(app.state.workbench)
    return {k:v for k,v in d.items() if k != 'path'}


@app.post('/api/model-management/review')
def management_review(req: ModelReviewRequest):
    return assess(app.state.workbench,req.source_run,req.dataset_id)


@app.post('/api/model-management/reviews/{ident}/plans')
def management_plans(ident: str):
    return product_plans(app.state.workbench,ident)


@app.get('/api/model-versions')
def model_versions():
    return app.state.workbench.store.versions()


@app.get("/api/runs/{ident}/events")
async def events(ident: str):
    wb = app.state.workbench
    wb.store.run(ident)
    async def stream():
        seen = 0
        while True:
            entries = wb.store.audit_log(ident)
            for item in entries[seen:]:
                yield "data: " + json.dumps(item, ensure_ascii=False) + "\n\n"
            seen = len(entries)
            if wb.store.run(ident)["status"] in {"completed", "failed"}:
                yield "data: [DONE]\n\n"
                return
            await asyncio.sleep(.5)
    return StreamingResponse(stream(), media_type="text/event-stream")


@app.get("/api/runs/{ident}/export.csv")
def export_csv(ident: str):
    record = app.state.workbench.store.run(ident)
    if record["status"] != "completed":
        raise ValueError("완료된 실험만 내보낼 수 있습니다")
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["trial", "model", "train_products", "preprocessing", "balance", "validation_recall",
                     "validation_precision", "validation_AP", "fit_seconds", "status"])
    for row in record["result"]["trials"]:
        m = row.get("validation", {})
        writer.writerow([row["id"], row.get("model"), "+".join(row.get("products", [])),
                         row.get("preprocessing"), row.get("balance"), m.get("recall"),
                         m.get("precision"), m.get("average_precision"), row.get("fit_seconds"), row["status"]])
    return Response("\ufeff" + buf.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition": f'attachment; filename="{ident}.csv"'})


class StrategyRequest(BaseModel):
    run_ids: list[str] = Field(min_length=2,max_length=5)


@app.post('/api/model-comparisons')
def strategy_comparison(req: StrategyRequest):
    return compare_strategies(app.state.workbench,req.run_ids)


@app.get('/api/model-comparisons')
def strategy_history():
    return app.state.workbench.store.comparisons()
