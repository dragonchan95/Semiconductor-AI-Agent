import json
import unittest
from pydantic import ValidationError
from app.impact import ImpactRequest, compare_impact

class CountIllustrationTests(unittest.TestCase):
    def setUp(self):
        self.result={'baseline_test':{'recall':.6,'fpr':.1},'test':{'recall':.8,'fpr':.2}}

    def test_counts_keep_separate_defect_and_normal_denominators(self):
        x=compare_impact(self.result,{})
        self.assertEqual(x['before']['detected_defects'],60)
        self.assertEqual(x['after']['normal_false_positives'],180)
        for m in [x['before'],x['after']]:
            self.assertAlmostEqual(m['detected_defects']+m['missed_defects'],100)
            self.assertAlmostEqual(m['normal_false_positives']+m['normal_correct'],900)

    def test_no_money_or_yield_claims(self):
        text=json.dumps(compare_impact(self.result,{}))
        for word in ['assumed_loss','cost','saving','good_fraction','repair']:
            self.assertNotIn(word,text)

    def test_reject_removed_repair_and_invalid_inputs(self):
        for args in [{'quantity':0},{'defect_rate':1.1},{'repair_success':.2}]:
            with self.assertRaises(ValidationError):
                ImpactRequest.model_validate(args)

    def test_zero_and_all_defects_preserve_counts(self):
        for rate in [0,1]:
            x=compare_impact(self.result,{'defect_rate':rate})
            self.assertAlmostEqual(sum(x['after'].values()),1000)
