"""Durable, single-use engineer approval. Only immutable approved plans execute."""
import hashlib
import json
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":"), allow_nan=False).encode()).hexdigest()


class Store:
    def __init__(self, directory: Path):
        self.directory = directory
        directory.mkdir(parents=True, exist_ok=True)
        self.path = directory / "state.db"
        self.lock = threading.RLock()
        with self.connect() as c:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS discoveries(id TEXT PRIMARY KEY, payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS candidate_registry(model TEXT PRIMARY KEY, payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS datasets(id TEXT PRIMARY KEY, payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS proposals(id TEXT PRIMARY KEY, status TEXT NOT NULL,
              plan TEXT NOT NULL, hash TEXT NOT NULL, payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY, proposal_id TEXT UNIQUE,
              status TEXT NOT NULL, result TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT,
              at TEXT NOT NULL, entity TEXT NOT NULL, kind TEXT NOT NULL, payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS model_comparisons(id TEXT PRIMARY KEY, payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS model_reviews(id TEXT PRIMARY KEY, payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS model_versions(id TEXT PRIMARY KEY, run_id TEXT UNIQUE,
              product TEXT NOT NULL, payload TEXT NOT NULL);
            """)

    def connect(self):
        c = sqlite3.connect(self.path, timeout=30)
        c.row_factory = sqlite3.Row
        return c

    def event(self, entity, kind, payload):
        with self.connect() as c:
            c.execute("INSERT INTO events(at,entity,kind,payload) VALUES(?,?,?,?)",
                      (now(), entity, kind, json.dumps(payload, ensure_ascii=False)))

    def add_dataset(self, payload):
        ident = "ds-" + uuid.uuid4().hex[:12]
        payload = {**payload, "id": ident, "created_at": now()}
        with self.connect() as c:
            c.execute("INSERT INTO datasets VALUES(?,?)", (ident, json.dumps(payload, ensure_ascii=False)))
        return payload

    def datasets(self):
        with self.connect() as c:
            return [json.loads(r[0]) for r in c.execute("SELECT payload FROM datasets ORDER BY rowid DESC")]

    def dataset(self, ident):
        with self.connect() as c:
            row = c.execute("SELECT payload FROM datasets WHERE id=?", (ident,)).fetchone()
        if row is None:
            raise KeyError("데이터셋을 찾지 못했습니다")
        return json.loads(row[0])

    def proposal(self, ident):
        with self.connect() as c:
            row = c.execute("SELECT * FROM proposals WHERE id=?", (ident,)).fetchone()
        if row is None:
            raise KeyError("제안을 찾지 못했습니다")
        return {"id": row["id"], "status": row["status"], "plan": json.loads(row["plan"]),
                "plan_hash": row["hash"], **json.loads(row["payload"])}

    def add_proposal(self, plan, payload):
        ident = "proposal-" + uuid.uuid4().hex[:12]
        with self.connect() as c:
            c.execute("INSERT INTO proposals VALUES(?,?,?,?,?)", (
                ident, "awaiting_approval", json.dumps(plan, ensure_ascii=False), digest(plan),
                json.dumps({**payload, "created_at": now()}, ensure_ascii=False)))
        self.event(ident, "proposal_created", {"plan_hash": digest(plan)})
        return self.proposal(ident)

    def decide(self, ident, plan_hash, accepted, engineer):
        if not engineer.strip():
            raise ValueError("승인자 이름이 필요합니다")
        with self.lock, self.connect() as c:
            c.execute("BEGIN IMMEDIATE")
            row = c.execute("SELECT * FROM proposals WHERE id=?", (ident,)).fetchone()
            if row is None:
                raise KeyError("제안을 찾지 못했습니다")
            if row["status"] != "awaiting_approval":
                raise ValueError("이미 처리된 제안입니다. 중복 승인은 실행하지 않습니다")
            if plan_hash != row["hash"] or digest(json.loads(row["plan"])) != plan_hash:
                raise ValueError("검토한 계획과 승인 계획의 해시가 다릅니다")
            status = "approved" if accepted else "rejected"
            c.execute("UPDATE proposals SET status=? WHERE id=?", (status, ident))
            c.execute("INSERT INTO events(at,entity,kind,payload) VALUES(?,?,?,?)",
                      (now(), ident, status, json.dumps({"engineer": engineer, "plan_hash": plan_hash})))
        return self.proposal(ident)

    def claim_run(self, ident):
        with self.lock, self.connect() as c:
            c.execute("BEGIN IMMEDIATE")
            row = c.execute("SELECT * FROM proposals WHERE id=?", (ident,)).fetchone()
            if row is None or row["status"] != "approved":
                raise ValueError("승인된 계획만 실행할 수 있습니다")
            run_id = "run-" + uuid.uuid4().hex[:12]
            c.execute("UPDATE proposals SET status='running' WHERE id=?", (ident,))
            c.execute("INSERT INTO runs VALUES(?,?,?,?)", (run_id, ident, "running", "{}"))
        return run_id

    def finish_run(self, run_id, result, failed=False):
        status = "failed" if failed else "completed"
        with self.connect() as c:
            c.execute("UPDATE runs SET status=?,result=? WHERE id=?",
                      (status, json.dumps(result, ensure_ascii=False, allow_nan=False), run_id))
            c.execute("UPDATE proposals SET status=? WHERE id=(SELECT proposal_id FROM runs WHERE id=?)",
                      (status, run_id))
            if not failed and result.get('model_version'):
                v = result['model_version']
                c.execute('INSERT INTO model_versions VALUES(?,?,?,?)',
                          (v['id'], run_id, v['product'], json.dumps(v, ensure_ascii=False)))
        self.event(run_id, status, {"winner": result.get("winner_id")})

    def run(self, ident):
        with self.connect() as c:
            row = c.execute("SELECT * FROM runs WHERE id=?", (ident,)).fetchone()
        if row is None:
            raise KeyError("실행 결과를 찾지 못했습니다")
        return {"id": ident, "proposal_id": row["proposal_id"], "status": row["status"],
                "result": json.loads(row["result"])}

    def runs(self):
        with self.connect() as c:
            ids = [r[0] for r in c.execute("SELECT id FROM runs ORDER BY rowid DESC")]
        return [self.run(i) for i in ids]

    def audit_log(self, entity):
        with self.connect() as c:
            return [{**dict(r), "payload": json.loads(r["payload"])}
                    for r in c.execute("SELECT * FROM events WHERE entity=? ORDER BY id", (entity,))]

    def save_review(self, payload):
        record = {**payload, 'id': 'review-'+uuid.uuid4().hex[:12], 'created_at': now()}
        with self.connect() as c:
            c.execute('INSERT INTO model_reviews VALUES(?,?)', (record['id'], json.dumps(record, ensure_ascii=False)))
        return record

    def review(self, ident):
        with self.connect() as c:
            row = c.execute('SELECT payload FROM model_reviews WHERE id=?', (ident,)).fetchone()
        if row is None:
            raise KeyError('모델 점검 결과가 없습니다')
        return json.loads(row[0])

    def versions(self):
        with self.connect() as c:
            return [json.loads(r[0]) for r in c.execute('SELECT payload FROM model_versions ORDER BY rowid DESC')]


    def save_comparison(self, payload):
        record = {**payload, 'id':'comparison-'+uuid.uuid4().hex[:12], 'created_at':now()}
        with self.connect() as c:
            c.execute('INSERT INTO model_comparisons VALUES(?,?)',(record['id'],json.dumps(record,ensure_ascii=False)))
        return record

    def comparisons(self):
        with self.connect() as c:
            return [json.loads(r[0]) for r in c.execute('SELECT payload FROM model_comparisons ORDER BY rowid DESC')]

    def save_discovery(self, payload):
        with self.connect() as c:
            c.execute('INSERT INTO discoveries VALUES(?,?)',(payload['id'],json.dumps(payload,ensure_ascii=False)))
        self.event(payload['id'],'external_documents_retrieved',{'models':[m['model']for m in payload['models']]})
        return payload

    def discovery(self, ident):
        with self.connect() as c:
            row=c.execute('SELECT payload FROM discoveries WHERE id=?',(ident,)).fetchone()
        if row is None:raise KeyError('모델 탐색 기록이 없습니다')
        return json.loads(row[0])

    def update_candidate(self, payload):
        with self.lock,self.connect() as c:
            row=c.execute('SELECT payload FROM candidate_registry WHERE model=?',(payload['model'],)).fetchone()
            prior=json.loads(row[0])if row else {'experiments':[]}
            history=[x for x in prior['experiments']if x['run_id']!=payload['run_id']]+[payload]
            c.execute('INSERT OR REPLACE INTO candidate_registry VALUES(?,?)',(payload['model'],json.dumps({'model':payload['model'],'title':payload['title'],'experiments':history,'latest':payload},ensure_ascii=False)))

    def candidates(self):
        with self.connect() as c:return [json.loads(row[0])for row in c.execute('SELECT payload FROM candidate_registry ORDER BY model')]
