import json
import tempfile
import unittest

import httpx
import numpy as np
from app.advisors import LocalAdvisor
from app.catalog import TABULAR, pipeline_reason
from app.experiments import fit_estimator
from app.planner import Knowledge


class AdvisorTests(unittest.TestCase):
    def client(self, content):
        return httpx.Client(transport=httpx.MockTransport(lambda req: httpx.Response(200,
            json={'message': {'content': json.dumps(content)}, 'eval_count': 10})))

    def test_unknown_citation_or_metric_rejected(self):
        for output in [dict(priority_codes=['missing'], evidence_ids=['invented']),
                       dict(priority_codes=['deploy'], evidence_ids=['leakage']),
                       dict(priority_codes=['missing'], evidence_ids=['leakage'], recall=.99)]:
            result = LocalAdvisor(True, self.client(output)).advise('DataQualityAgent', {}, {'missing': '결측'}, [{'id':'leakage','text':'train only'}])
            self.assertEqual(result['status'], 'fallback')

    def test_grounded_role_output(self):
        output = dict(priority_codes=['missing'], evidence_ids=['leakage'])
        result = LocalAdvisor(True, self.client(output)).advise('DataQualityAgent', {}, {'missing':'결측'}, [{'id':'leakage','text':'train only'}])
        self.assertEqual(result['status'], 'verified')
        self.assertEqual(result['numeric_claims'], 'engine_only')

    def test_train_only_transform_and_model_support(self):
        rng = np.random.default_rng(45)
        x = rng.normal(size=(80, 4)); y = np.array([0]*60+[1]*20)
        x[:4, 1] = np.nan
        model = fit_estimator('knn', 'auto', 'weighted', x, y)
        original = fit_estimator('logistic', 'auto', 'none', x, y)
        self.assertAlmostEqual(original.named_steps['impute'].statistics_[1], np.nanmedian(x[:,1]))
        self.assertEqual(model.named_steps['classifier'].n_samples_fit_, 120)
        self.assertEqual(pipeline_reason('svm')['preprocessing'], 'scaled')
        self.assertEqual(pipeline_reason('random_forest')['preprocessing'], 'median')
        for name in TABULAR:
            self.assertTrue(pipeline_reason(name)['source'])

    def test_dense_connection_failure_is_explicit_fallback(self):
        client = httpx.Client(transport=httpx.MockTransport(lambda req: httpx.Response(503)))
        with tempfile.TemporaryDirectory() as d:
            k = Knowledge(d, True, client)
            self.assertTrue(k.search('센서 결측'))
            self.assertEqual(k.last_status['mode'], 'tfidf_fallback')


if __name__ == '__main__': unittest.main()
