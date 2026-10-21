import inspect
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import joblib
import numpy as np
import pandas as pd

from app.advisors import LocalAdvisor
from app.data import generate_demo, split_frame, META
from app.ensemble import (weight_grid, search_weights, choose_ensemble_threshold,
    ensemble_key, propose_ensemble, probability)
from app.metrics import measure
from app.workbench import Workbench


class EnsembleTests(unittest.TestCase):
    policy={'min_recall':.9,'max_fpr':.15,'min_test_defects':20}

    def test_grid_includes_all_simplex_vertices_and_equal_weight(self):
        rows=np.asarray(weight_grid(3,20))
        self.assertEqual(rows.shape,(232,3))
        np.testing.assert_allclose(rows.sum(axis=1),1)
        self.assertTrue((rows>=0).all())
        for v in np.eye(3):self.assertTrue(any(np.array_equal(v,row) for row in rows))
        self.assertTrue(any(np.allclose([1/3]*3,row) for row in rows))

    def test_complementary_predictions_can_outperform_both_single_models(self):
        result=search_weights([0,0,1,1],[[.9,.1,.8,.4],[.1,.9,.4,.8]],self.policy)
        self.assertEqual(result['winner']['validation']['recall'],1)
        self.assertEqual(result['winner']['validation']['fpr'],0)
        self.assertGreater(result['winner']['validation']['f1'],result['best_single']['validation']['f1'])
        self.assertEqual(result['winner']['active_models'],2)

    def test_equal_performance_keeps_a_single_model_instead_of_forcing_mixing(self):
        result=search_weights([0,0,1,1],[[.1,.2,.8,.9],[.9,.8,.2,.1]],self.policy)
        self.assertEqual(result['winner']['active_models'],1)
        self.assertEqual(result['winner']['weights'],[1,0])

    def test_false_alarm_limit_prevents_all_defective_shortcut(self):
        m=choose_ensemble_threshold([0,0,1,1],[.5]*4,self.policy)
        self.assertEqual(m['fpr'],0)
        self.assertEqual(m['recall'],0)

    def test_recall_has_priority_over_f1_within_false_alarm_limit(self):
        high_recall={'recall':1.,'fpr':.14,'f1':.65}
        high_f1={'recall':.9,'fpr':.02,'f1':.9}
        self.assertGreater(ensemble_key(high_recall,self.policy),ensemble_key(high_f1,self.policy))
        self.assertLess(ensemble_key({**high_recall,'fpr':.16},self.policy),ensemble_key(high_f1,self.policy))

    def test_threshold_matches_independent_enumeration_of_confusion_metrics(self):
        y=np.array([0,1,0,1,0,1]);scores=np.array([.1,.9,.4,.5,.8,.7])
        expected=max((measure(y,scores,t) for t in np.unique(np.r_[scores,np.nextafter(scores.max(),np.inf)])),
                     key=lambda m:(*ensemble_key(m,self.policy),m['threshold']))
        self.assertEqual(choose_ensemble_threshold(y,scores,self.policy),expected)

    def test_invalid_probabilities_or_dimensions_are_rejected(self):
        for scores in [[[.1,np.nan,.4,.9],[.1,.2,.4,.9]],[[.1,1.1,.4,.9],[.1,.2,.4,.9]],[[.1,.9]]]:
            with self.assertRaises(ValueError):search_weights([0,0,1,1],scores,self.policy)
        self.assertEqual(list(inspect.signature(search_weights).parameters),['y_validation','validation_scores','policy','units'])

    def test_positive_class_column_is_found_by_label(self):
        class ReverseModel:
            classes_=[1,0]
            def predict_proba(self,x):return np.array([[.7,.3],[.2,.8]])
        np.testing.assert_allclose(probability(ReverseModel(),None),[.7,.2])

    def test_approval_training_scope_artifact_and_test_only_after_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);wb=Workbench(root,advisor=LocalAdvisor(enabled=False))
            ds=wb.register(generate_demo(root/'data'),'ensemble test','synthetic',True)
            p=wb.propose({'dataset_id':ds['id'],'cohort_mode':'all','models':['logistic','decision_tree','random_forest'],'balance':['none']})
            source,_=wb.approve_and_run(p['id'],p['plan_hash'],'unit test')
            ep=propose_ensemble(wb,source)
            self.assertEqual(ep['plan']['ensemble']['weight_count'],232)
            with self.assertRaises(ValueError):wb.store.claim_run(ep['id'])
            with self.assertRaises(ValueError):wb.store.decide(ep['id'],'0'*64,True,'unit test')
            from app.ensemble import fit_estimator as real_fit
            sizes=[];events=[]
            def fit(*args):sizes.append(len(args[-1]));return real_fit(*args)
            with patch('app.ensemble.fit_estimator',side_effect=fit):
                run,result=wb.approve_and_run(ep['id'],ep['plan_hash'],'unit test',events.append)
            self.assertEqual(sizes,[768]*3)
            self.assertFalse(result['ensemble']['selection_uses_test'])
            self.assertEqual(result['test_fingerprint'],wb.store.run(source)['result']['test_fingerprint'])
            self.assertTrue(any(e['type']=='EnsembleWeightsSelected' for e in events))
            model=joblib.load(root/'runs'/run/'champion.joblib')
            df=pd.read_csv(ds['path']);parts,_=split_frame(df)
            x=df[[c for c in df if c not in META]].to_numpy(dtype=float)[parts['test']]
            np.testing.assert_allclose(model.predict_proba(x)[:,1],[p['score'] for p in result['test_predictions']])
            with self.assertRaises(ValueError):wb.store.claim_run(ep['id'])
            ep2=propose_ensemble(wb,source)
            changed=wb.store.run(source)['result'];changed['scope_note']='changed after approval'
            wb.store.finish_run(source,changed)
            with self.assertRaisesRegex(ValueError,'원본 실험'):
                wb.approve_and_run(ep2['id'],ep2['plan_hash'],'unit test')
