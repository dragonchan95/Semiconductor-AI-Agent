import tempfile
import unittest
from pathlib import Path
import httpx
from app.discovery import discover, propose_discovery, INDEX, fetch
from app.catalog import EXTERNAL
from app.data import generate_demo
from app.workbench import Workbench
from app.advisors import LocalAdvisor
from app.planner import Knowledge
from app.experiments import fit_estimator
import numpy as np


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.wb=Workbench(self.root,knowledge=Knowledge(dense=False),advisor=LocalAdvisor(enabled=False))
        self.dataset=self.wb.register(generate_demo(self.root/'input'),'synthetic','synthetic',True)
        self.urls=[]
        def serve(req):
            self.urls.append(str(req.url))
            if str(req.url)==INDEX:
                return httpx.Response(200,text=''.join('<a href="'+v[3]+'">'+v[4]+'</a>' for v in EXTERNAL.values()))
            meta=next(v for v in EXTERNAL.values()if v[3]==str(req.url))
            return httpx.Response(200,text='<article><h1>'+meta[4]+'</h1><p>Classifier for binary numerical tabular data. Random trees or Gaussian distribution and conditional independence.</p><h2>Parameters:</h2></article>')
        self.client=httpx.Client(transport=httpx.MockTransport(serve))
    def tearDown(self):self.temp.cleanup()
    def test_live_documents_retrieved_without_dataset_transmission(self):
        d=discover(self.wb,self.dataset['id'],'private product abc',self.client)
        self.assertEqual({x['model']for x in d['models']},set(EXTERNAL))
        self.assertTrue(all(e['document_hash']and e['text']for e in d['evidence']))
        self.assertTrue(all('private'not in u and 'abc'not in u for u in self.urls))
        self.assertEqual(self.wb.store.runs(),[])
        self.assertEqual(self.wb.store.candidates(),[])
    def test_failed_network_never_invents_candidates(self):
        client=httpx.Client(transport=httpx.MockTransport(lambda req:httpx.Response(503)))
        with self.assertRaises(ValueError):discover(self.wb,self.dataset['id'],'',client)
        with self.assertRaises(ValueError):fetch('https://untrusted.example/code',self.client)
    def test_external_adapters_train_and_predict(self):
        x=np.array([[0,1],[1,2],[2,0],[3,2],[4,3],[5,1]],float);y=np.array([0,0,1,0,1,1])
        for code in EXTERNAL:
            for balance in ['none','weighted']:
                model=fit_estimator(code,'auto',balance,x,y)
                self.assertEqual(model.predict_proba(x).shape,(6,2))
    def test_discovery_requires_evidence_and_engineer_approval(self):
        # Ordinary requests cannot train external adapters without a discovery record.
        with self.assertRaises(ValueError):self.wb.propose({'dataset_id':self.dataset['id'],'models':['extra_trees'],'cohort_mode':'all'})
        base=self.wb.propose({'dataset_id':self.dataset['id'],'models':['logistic'],'cohort_mode':'all','balance':['none']})
        run,result=self.wb.approve_and_run(base['id'],base['plan_hash'],'test actor')
        d=discover(self.wb,self.dataset['id'],'',self.client)
        p=propose_discovery(self.wb,d['id'],run)
        self.assertEqual(p['status'],'awaiting_approval')
        self.assertEqual(self.wb.store.candidates(),[])
        with self.assertRaises(ValueError):self.wb.store.claim_run(p['id'])
        new_run,new=self.wb.approve_and_run(p['id'],p['plan_hash'],'test actor')
        self.assertEqual(new['test_fingerprint'],result['test_fingerprint'])
        self.assertEqual({x['model']for x in self.wb.store.candidates()},set(EXTERNAL))
        self.assertTrue(all(not x['latest']['production_deployed']for x in self.wb.store.candidates()))
        self.assertEqual(new['discovery_comparison']['reference_model'],'logistic')
        with self.assertRaises(ValueError):self.wb.approve_and_run(p['id'],p['plan_hash'],'test actor')

if __name__=='__main__':unittest.main()
