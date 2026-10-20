import tempfile
import unittest
from pathlib import Path

from app.data import generate_demo
from app.monitoring import assess, prepare_changed_demo, product_plans, select_strategy
from app.workbench import Workbench


class MonitoringTests(unittest.TestCase):
    def test_review_plans_need_approval_and_save_candidate_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            wb = Workbench(root/'state')
            ds = wb.register(generate_demo(root), 'baseline', 'synthetic test', True)
            p = wb.propose({'dataset_id':ds['id'], 'cohort_mode':'all',
                            'models':['random_forest'], 'balance':['none']})
            run_id, _ = wb.approve_and_run(p['id'], p['plan_hash'], 'automated test actor')
            with self.assertRaisesRegex(ValueError, '중복'):
                assess(wb, run_id, ds['id'])
            new = prepare_changed_demo(wb)
            review = assess(wb, run_id, new['id'])
            self.assertEqual(review['verdict'], '재학습 필요')
            n = len(wb.store.runs())
            plans = product_plans(wb, review['id'])['proposals']
            self.assertEqual(len(plans), 5)
            self.assertEqual(len(wb.store.runs()), n)
            self.assertEqual(wb.store.versions(), [])
            for plan in plans:
                self.assertEqual(plan['status'], 'awaiting_approval')
                self.assertEqual(plan['plan']['cohorts'], [plan['plan']['target_products']])
            p = plans[1]
            with self.assertRaises(ValueError):
                wb.store.claim_run(p['id'])
            trained, result = wb.approve_and_run(p['id'], p['plan_hash'], 'automated test actor')
            versions = wb.store.versions()
            self.assertEqual(len(versions), 1)
            self.assertEqual(versions[0]['run_id'], trained)
            self.assertFalse(versions[0]['auto_deployed'])
            self.assertTrue((wb.directory/result['model_version']['artifact']).is_file())

    def test_strategy_selection_uses_validation_and_can_abstain(self):
        policy={'min_precision':.25,'max_fpr':.15}
        a={'strategy':'shared','selection_feasible':True,'validation':{'recall':.8,'precision':.5,'fpr':.1,'average_precision':.7,'assumed_cost_per_10000':100},'test':{'recall':0}}
        b={'strategy':'separate','selection_feasible':True,'validation':{'recall':.9,'precision':.4,'fpr':.1,'average_precision':.7,'assumed_cost_per_10000':90},'test':{'recall':1}}
        self.assertEqual(select_strategy([a,b],policy),('separate',True))
        a['test'],b['test']=b['test'],a['test']
        self.assertEqual(select_strategy([a,b],policy),('separate',True))
        b['validation']['fpr']=.5
        self.assertEqual(select_strategy([a,b],policy),('shared',True))
        a['validation']['fpr']=.5
        self.assertEqual(select_strategy([a,b],policy),('separate',False))
