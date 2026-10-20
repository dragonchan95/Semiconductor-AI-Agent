import importlib
import os
import tempfile
import time
import unittest
from unittest.mock import patch
from pathlib import Path

from fastapi.testclient import TestClient


class APITests(unittest.TestCase):
    def test_production_auth_does_not_block_health_or_ui(self):
        import app.api as module
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"APP_ENV": "production", "ENGINEER_TOKEN": "test-token-45"}):
                module = importlib.reload(module)
                module.STATE_DIR = Path(tmp)
                with TestClient(module.app) as client:
                    self.assertEqual(client.get("/health").status_code, 200)
                    self.assertEqual(client.get("/").status_code, 200)
                    self.assertEqual(client.get("/api/datasets").status_code, 401)
                    self.assertEqual(client.get("/api/datasets", headers={"X-Engineer-Token": "test-token-45"}).status_code, 200)
            importlib.reload(module)

    def test_proposal_rejection_and_single_approval_http(self):
        with tempfile.TemporaryDirectory() as tmp:
            import app.api as module
            module.STATE_DIR = Path(tmp)
            with TestClient(module.app) as client:
                self.assertEqual(client.get("/health").status_code, 200)
                dataset = client.post("/api/examples").json()
                ident = next(d["id"] for d in dataset if d["synthetic"] and d["modality"] == "tabular")
                payload = {"dataset_id": ident, "cohort_mode": "all", "models": ["logistic"], "balance": ["none"]}
                p = client.post("/api/proposals", json=payload).json()
                self.assertEqual(client.get("/api/runs").json(), [])
                denied = client.post(f"/api/proposals/{p['id']}/decision", json={
                    "accepted": True, "engineer": "test", "plan_hash": "0" * 64})
                self.assertEqual(denied.status_code, 400)
                rejected = client.post(f"/api/proposals/{p['id']}/decision", json={
                    "accepted": False, "engineer": "test", "plan_hash": p["plan_hash"]})
                self.assertIsNone(rejected.json()["run_id"])
                self.assertEqual(client.get("/api/runs").json(), [])
                p = client.post("/api/proposals", json=payload).json()
                decision = {"accepted": True, "engineer": "G045 HTTP 자동검증 승인자", "plan_hash": p["plan_hash"]}
                response = client.post(f"/api/proposals/{p['id']}/decision", json=decision)
                self.assertEqual(response.status_code, 200)
                run_id = response.json()["run_id"]
                self.assertEqual(client.post(f"/api/proposals/{p['id']}/decision", json=decision).status_code, 400)
                for _ in range(100):
                    record = client.get(f"/api/runs/{run_id}").json()
                    if record["status"] != "running":
                        break
                    time.sleep(.1)
                self.assertEqual(record["status"], "completed", record)
                stream = client.get(f"/api/runs/{run_id}/events")
                self.assertTrue(stream.text.endswith("data: [DONE]\n\n"))
                self.assertEqual(client.get(f"/api/runs/{run_id}/export.csv").status_code, 200)


if __name__ == "__main__":
    unittest.main()
