import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import joblib
import numpy as np
import pandas as pd

from app.advisors import LocalAdvisor
from app.data import generate_demo,split_frame
from app.grouping import partitions,route_metrics,choose_group_threshold,partition_key,propose_grouping
from app.metrics import measure
from app.workbench import Workbench


class GroupingTests(unittest.TestCase):
    policy={'min_recall':.9,'max_fpr':.15,'min_test_defects':20}

    def test_all_fifteen_partitions_cover_each_product_exactly_once(self):
        rows=partitions('ABCD');self.assertEqual(len(rows),15)
        self.assertEqual(len(partitions('ABC')),5)
        for groups in rows:self.assertEqual(sorted(p for g in groups for p in g),list('ABCD'))
        for wanted in [[list('ABCD')],[list('ABC'),['D']],[list('AB'),list('CD')],[[p] for p in 'ABCD']]:
            self.assertIn(wanted,rows)
        with self.assertRaises(ValueError):partitions('AAB')

    def test_route_counts_are_aggregated_not_averaged_percentages(self):
        y=[0,0,1,1];s=[.2,.8,.6,.3];t=[.3,.9,.5,.5]
        m=route_metrics(y,s,t)
        self.assertEqual([m[k] for k in ['tn','fp','fn','tp']],[2,0,1,1])
        self.assertIsNone(m['roc_auc']);self.assertIsNone(m['threshold'])

    def test_group_threshold_respects_each_product_false_alarm_limit(self):
        y=np.array([0,0,1,1,0,0,1,1]);s=np.array([.1,.7,.8,.9,.1,.2,.4,.5]);p=np.array(list('AAAABBBB'))
        threshold=choose_group_threshold(y,s,p,self.policy)
        for product in 'AB':self.assertLessEqual(measure(y[p==product],s[p==product],threshold)['fpr'],.15)

    def test_ties_prefer_fewer_models_and_test_cannot_change_rank(self):
        m={'recall':1.,'fpr':.1,'f1':.8};a={'validation':m,'per_product':{'A':m},'model_count':1,'name':'A'}
        b={**a,'model_count':2,'name':'B','test':{'recall':1.}}
        self.assertGreater(partition_key(a,self.policy),partition_key(b,self.policy))
        before=partition_key(b,self.policy);b['test']['recall']=0;self.assertEqual(before,partition_key(b,self.policy))

    def test_approved_routing_fits_each_group_once_and_roundtrips(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);wb=Workbench(root,advisor=LocalAdvisor(enabled=False))
            ds=wb.register(generate_demo(root/'data'),'grouping','synthetic',True)
            p=wb.propose({'dataset_id':ds['id'],'models':['logistic'],'cohort_mode':'all','balance':['none']})
            source,_=wb.approve_and_run(p['id'],p['plan_hash'],'unit test')
            gp=propose_grouping(wb,source)
            with self.assertRaises(ValueError):wb.store.claim_run(gp['id'])
            from app.grouping import fit_estimator as real_fit
            sizes=[]
            def fit(*args):sizes.append(len(args[-1]));return real_fit(*args)
            with patch('app.grouping.fit_estimator',side_effect=fit):
                ident,result=wb.approve_and_run(gp['id'],gp['plan_hash'],'unit test')
            self.assertEqual(len(sizes),15);self.assertTrue(all(n<=768 for n in sizes))
            g=result['grouping'];self.assertEqual(len(g['strategies']),15)
            self.assertEqual(len({r['validation_fingerprint'] for r in g['strategies']}),1)
            self.assertFalse(g['selection_uses_test'])
            self.assertLessEqual(len(g['tested_baselines']),3)
            routed=joblib.load(root/'runs'/ident/'product-routing.joblib')
            frame=pd.read_csv(ds['path']);parts,_=split_frame(frame)
            s,t,pred=routed.predict_frame(frame.iloc[parts['test']].reset_index(drop=True))
            self.assertEqual(route_metrics(frame.iloc[parts['test']].label.to_numpy(),s,t),result['test'])
            unknown=frame.iloc[:1].copy();unknown['product']='E'
            with self.assertRaises(ValueError):routed.predict_frame(unknown)
            with self.assertRaises(ValueError):wb.store.claim_run(gp['id'])
            # Refuse an unevaluable product instead of crashing after training.
            original_parts,metadata=split_frame(frame)
            incomplete={**original_parts,'test':original_parts['test'][frame.iloc[original_parts['test']]['product'].to_numpy()!='D']}
            with patch('app.grouping.split_frame',return_value=(incomplete,metadata)):
                with self.assertRaisesRegex(ValueError,'D Test'):
                    propose_grouping(wb,source)
