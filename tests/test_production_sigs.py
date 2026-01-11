import unittest
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers.sig import SigParser

class TestProductionSigs(unittest.TestCase):
    def setUp(self):
        self.parser = SigParser()

    def test_inhale_puffs(self):
        sigs = [
            ("inhale 1 puff twice daily", 1, 2.0),
            ("1 puff inhale bid", 1, 2.0),
        ]
        for sig, exp_dose, exp_max in sigs:
            with self.subTest(sig=sig):
                res = self.parser.parse(sig)
                self.assertTrue(res['Is_Sig_Parsable'], f"Should be parsable: {sig}")
                self.assertEqual(res['dose'], exp_dose)
                self.assertEqual(res['max_dose_per_day'], exp_max)

    def test_every_x_hours(self):
        sigs = [
            ("take 1 tablet every 6 hours", 1, 4.0),
            ("take 1 tablet every 8 hours", 1, 3.0),
            ("take 2 tablets q6h prn pain", 2, 8.0),
        ]
        for sig, exp_dose, exp_max in sigs:
            with self.subTest(sig=sig):
                res = self.parser.parse(sig)
                self.assertTrue(res['Is_Sig_Parsable'], f"Should be parsable: {sig}")
                self.assertEqual(res['max_dose_per_day'], exp_max)

    def test_click_unit(self):
        sigs = [
            ("apply 1 click daily", 1, 1.0),
            ("4 clicks to skin at bedtime", 4, 4.0),
        ]
        for sig, exp_dose, exp_max in sigs:
            with self.subTest(sig=sig):
                res = self.parser.parse(sig)
                self.assertTrue(res['Is_Sig_Parsable'], f"Should be parsable: {sig}")
                self.assertEqual(res['dose'], exp_dose)
                self.assertEqual(res['dose_unit'], 'click')
                self.assertEqual(res['max_dose_per_day'], exp_max)

    def test_production_patterns(self):
        sigs = [
            ("1 tab po bid", 1, 2.0),
            ("1 tab po tid", 1, 3.0),
            ("1 caps po qid", 1, 4.0),
            ("take 1 tablet by mouth every morning and every evening", 1, 2.0),
            ("take 1 tablet q6h prn pain", 1, 4.0),
        ]
        for sig, exp_dose, exp_max in sigs:
            with self.subTest(sig=sig):
                res = self.parser.parse(sig)
                self.assertTrue(res['Is_Sig_Parsable'], f"Should be parsable: {sig}")
                self.assertEqual(res['max_dose_per_day'], exp_max)

if __name__ == '__main__':
    unittest.main()
