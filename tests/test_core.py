import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from app.data import audit_frame, generate_demo, load_frame, split_frame, import_secom
from app.metrics import choose_threshold, measure, operational_gate
from app.planner import ProposalRequest
from app.store import Store, digest
from app.workbench import Workbench


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name)
        self.frame = pd.read_csv(generate_demo(self.path))

    def tearDown(self):
        self.tmp.cleanup()

    def test_lot_disjoint_and_all_rows(self):
        parts, summary = split_frame(self.frame)
        sets = [set(self.frame.iloc[idx].lot_id) for idx in parts.values()]
        for i in range(3):
            for j in range(i):
                self.assertFalse(sets[i] & sets[j])
        self.assertEqual(sum(map(len, parts.values())), len(self.frame))

    def test_chronological_date_split(self):
        frame = self.frame.drop(columns="lot_id").copy()
        parts, _ = split_frame(frame)
        previous = None
        for name in ["train", "validation", "test"]:
            times = pd.to_datetime(frame.iloc[parts[name]].timestamp)
            if previous is not None:
                self.assertGreater(times.min(), previous)
            previous = times.max()

    def test_no_random_row_split_when_group_unknown(self):
        with self.assertRaises(ValueError):
            audit_frame(self.frame.drop(columns=["lot_id", "timestamp"]))

    def test_preserve_valid_zeros(self):
        frame = self.frame.copy()
        frame.loc[:10, "sensor_0"] = 0
        self.assertEqual(audit_frame(frame)["rows"], len(frame))

    def test_public_secom_label_and_quoted_timestamp(self):
        frame = pd.read_csv(import_secom(self.path))
        self.assertEqual(len(frame), 1567)
        self.assertEqual(int(frame.label.sum()), 104)
        self.assertFalse(frame.timestamp.isna().any())
        self.assertGreater(frame.timestamp.nunique(), 16)
        parts, _ = split_frame(frame)
        self.assertGreater(frame.iloc[parts["test"]].timestamp.min(), frame.iloc[parts["train"]].timestamp.max())

    def test_duplicate_features_rejected(self):
        frame = pd.concat([self.frame, self.frame.iloc[:1]], ignore_index=True)
        with self.assertRaises(ValueError):
            audit_frame(frame)

    def test_metrics_manual_confusion(self):
        m = measure([0, 0, 1, 1], [.2, .8, .7, .1], .5,
                    {"miss_cost": 100, "false_alarm_cost": 10})
        self.assertEqual([m[k] for k in ["tn", "fp", "fn", "tp"]], [1, 1, 1, 1])
        self.assertEqual(m["recall"], .5)
        self.assertEqual(m["precision"], .5)
        self.assertEqual(m['f1'],.5)
        self.assertNotIn("assumed_cost_per_10000",m)

    def test_threshold_infeasibility_is_visible(self):
        _, feasible = choose_threshold([0, 1, 0, 1], [.5, .5, .5, .5], {
            "min_recall": .9, "max_fpr": .01, "miss_cost": 100, "false_alarm_cost": 10})
        self.assertFalse(feasible)

    def test_sparse_gate_never_auto_deploys(self):
        m = measure([0, 0, 1, 1], [.1, .2, .8, .9], .5,
                    {"miss_cost": 100, "false_alarm_cost": 1})
        gate = operational_gate(m, {"min_recall": .5, "max_fpr": .1})
        self.assertFalse(gate["passed"])
        self.assertFalse(gate["auto_deploy"])

    def test_approval_hash_reject_and_single_use(self):
        store = Store(self.path / "state")
        p = store.add_proposal({"dataset": "v1", "budget": 1}, {})
        with self.assertRaises(ValueError):
            store.claim_run(p["id"])
        with self.assertRaises(ValueError):
            store.decide(p["id"], "0" * 64, True, "test")
        store.decide(p["id"], p["plan_hash"], True, "test")
        store.claim_run(p["id"])
        with self.assertRaises(ValueError):
            store.claim_run(p["id"])
        with self.assertRaises(ValueError):
            store.decide(p["id"], p["plan_hash"], True, "test")

    def test_rejected_plan_cannot_run(self):
        store = Store(self.path / "state")
        p = store.add_proposal({"dataset": "v1"}, {})
        store.decide(p["id"], p["plan_hash"], False, "test")
        with self.assertRaises(ValueError):
            store.claim_run(p["id"])

    def test_propose_does_not_train_and_restart_keeps_approval(self):
        wb = Workbench(self.path / "state")
        ds = wb.register(self.path / "process_demo.csv", "demo", "test", True)
        p = wb.propose({"dataset_id": ds["id"]})
        self.assertEqual(p["status"], "awaiting_approval")
        self.assertEqual(wb.store.runs(), [])
        self.assertEqual(len(p["plan"]["cohorts"]), 15)
        self.assertEqual(p["plan"]["trial_budget"], 52)
        self.assertEqual(len(p['plan']['models']), 12)
        self.assertEqual(p['plan']['search_strategy'], 'model_then_cohort')
        self.assertEqual(Workbench(self.path / "state").store.proposal(p["id"])["plan_hash"], p["plan_hash"])

    def test_changed_data_invalidates_execution(self):
        wb = Workbench(self.path / "state")
        ds = wb.register(self.path / "process_demo.csv", "demo", "test", True)
        self.frame.iloc[0, self.frame.columns.get_loc("sensor_1")] += 10
        self.frame.to_csv(self.path / "process_demo.csv", index=False)
        with self.assertRaises(ValueError):
            load_frame(ds)

    def test_budget_and_unknown_product_guard(self):
        wb = Workbench(self.path / "state")
        ds = wb.register(self.path / "process_demo.csv", "demo", "test", True)
        for extra in [{"target_products": ["unknown"]},
                      {"models": ["logistic", "random_forest", "hist_gradient"], "preprocessing": ["median", "scaled"]}]:
            with self.assertRaises(ValueError):
                wb.propose({"dataset_id": ds["id"], **extra})


if __name__ == "__main__":
    unittest.main()
