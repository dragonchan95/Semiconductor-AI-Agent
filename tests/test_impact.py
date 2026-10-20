import unittest
from pydantic import ValidationError
from app.impact import ImpactRequest, compare_impact


class ImpactTests(unittest.TestCase):
    def setUp(self):
        self.result = {'dataset': {'synthetic': True},
                       'baseline_test': {'recall': .6, 'fpr': .1},
                       'test': {'recall': .8, 'fpr': .2, 'n': 200, 'positive_count': 20}}
        self.costs = {'miss_cost': 100000, 'false_alarm_cost': 1000}

    def test_counts_and_loss_are_consistent(self):
        x = compare_impact(self.result, {}, self.costs)
        self.assertEqual(x['before']['detected_defects'], 60)
        self.assertEqual(x['after']['missed_defects'], 20)
        self.assertEqual(x['after']['normal_extra_checks'], 180)
        self.assertEqual(x['delta']['additional_detected'], 20)
        self.assertEqual(x['delta']['additional_normal_checks'], 90)
        self.assertEqual(x['delta']['assumed_loss_reduction'], 1910000)
        for m in [x['before'], x['after']]:
            self.assertEqual(m['detected_defects']+m['missed_defects'], 100)
            self.assertEqual(m['normal_extra_checks']+m['normal_pass'], 900)

    def test_inspection_alone_never_increases_good_fraction(self):
        x = compare_impact(self.result, {}, self.costs)
        self.assertFalse(x['repair_scenario_enabled'])
        self.assertEqual(x['before']['good_fraction_after_repair'], .9)
        self.assertEqual(x['after']['good_fraction_after_repair'], .9)
        self.assertEqual(x['delta']['good_fraction_change'], 0)

    def test_repair_applies_equally_to_baseline_and_selected(self):
        x = compare_impact(self.result, {'repair_success': .25}, self.costs)
        self.assertAlmostEqual(x['before']['good_fraction_after_repair'], .915)
        self.assertAlmostEqual(x['after']['good_fraction_after_repair'], .920)
        self.assertEqual(x['delta']['additional_recovered'], 5)
        self.assertAlmostEqual(x['delta']['good_fraction_change'], .005)

    def test_input_bounds_and_zero_defects(self):
        for args in [{'quantity': 0}, {'defect_rate': 1.1}, {'repair_success': -1}]:
            with self.assertRaises(ValidationError):
                ImpactRequest.model_validate(args)
        x = compare_impact(self.result, {'defect_rate': 0, 'repair_success': 1}, self.costs)
        self.assertEqual(x['delta']['additional_detected'], 0)
        self.assertEqual(x['after']['good_fraction_after_repair'], 1)
