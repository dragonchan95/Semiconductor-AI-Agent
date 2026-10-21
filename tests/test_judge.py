import json
import unittest
import httpx

from app.judge import LocalJudge


class JudgeTests(unittest.TestCase):
    def client(self,payload):
        return httpx.Client(transport=httpx.MockTransport(lambda request:httpx.Response(
            200,json={'message':{'content':json.dumps(payload)},'eval_count':12})))

    def test_valid_judge_verdict_is_reported_as_model_evaluation(self):
        payload={'supported':False}
        result=LocalJudge(self.client(payload)).evaluate({'detected':27},'Detected 30.')
        self.assertEqual(result['status'],'evaluated')
        self.assertEqual(result['verdict'],'fail')

    def test_inconsistent_or_invented_verdict_is_not_success(self):
        for payload in [
            {'supported':'true'},
            {'supported':True,'unverified_claim':30},
            {'verdict':'invented'}]:
            result=LocalJudge(self.client(payload)).evaluate({'detected':27},'Detected 30.')
            self.assertEqual(result['status'],'error')

    def test_unavailable_llm_is_not_replaced_by_a_fake_judge(self):
        client=httpx.Client(transport=httpx.MockTransport(lambda request:httpx.Response(503)))
        result=LocalJudge(client).evaluate({'detected':27},'Detected 30.')
        self.assertEqual(result['status'],'error')
        self.assertNotIn('verdict',result)
