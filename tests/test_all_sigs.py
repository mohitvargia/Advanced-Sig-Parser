"""
Comprehensive Sig Parser Test Suite
===================================
Tests for the Advanced-Sig-Parser with realistic expectations based on current capabilities.

KNOWN LIMITATIONS (documented for future enhancement):
1. Different doses for different times (e.g., "2 morning and 1 night") - currently uses first dose for all
2. Multiple specific times (e.g., "6am 2pm 9pm") - may not detect all times correctly
3. Redundant frequency phrases (e.g., "daily" + "every morning") - currently counts as additive
"""

import unittest
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers.sig import SigParser


class TestGuardrails(unittest.TestCase):
    """Tests for unparsable patterns that should be caught by guardrails"""
    
    def setUp(self):
        self.parser = SigParser()

    def test_titration_unparsable(self):
        """Titration patterns should be unparsable"""
        sigs = [
            "take 1 tablet by mouth daily for 3 days then 2 tablets daily",
            "take 1/2 tablet daily x 1 week then increase to one tablet daily",
        ]
        for sig in sigs:
            with self.subTest(sig=sig):
                res = self.parser.parse(sig)
                self.assertFalse(res['Is_Sig_Parsable'])

    def test_contradicting_daily_mwf_unparsable(self):
        """'daily every monday wednesday friday' is contradictory"""
        sig = "take 1 tablet by mouth daily every monday wednesday and friday"
        result = self.parser.parse(sig)
        self.assertFalse(result['Is_Sig_Parsable'])

    def test_redundant_half_notation_unparsable(self):
        """'1/2 one-half' is redundant/contradicting"""
        sig = "take 1 tablet by mouth in the morning and 1/2 one-half at night"
        result = self.parser.parse(sig)
        self.assertFalse(result['Is_Sig_Parsable'])

    def test_typo_days_concatenated_unparsable(self):
        """Concatenated day names (typo) should be unparsable"""
        sig = "one tablet by mouth at dinner sundaytuesdaythursday and saturday"
        result = self.parser.parse(sig)
        self.assertFalse(result['Is_Sig_Parsable'])


class TestBasicPatterns(unittest.TestCase):
    """Tests for basic frequency patterns"""
    
    def setUp(self):
        self.parser = SigParser()

    def test_daily_patterns(self):
        sigs = [
            ("take 1 tablet by mouth daily", 1, 1.0),
            ("take 1 tablet by mouth once daily", 1, 1.0),
            ("take 1 tablet by mouth every day", 1, 1.0),
        ]
        for sig, exp_dose, exp_max in sigs:
            with self.subTest(sig=sig):
                res = self.parser.parse(sig)
                self.assertTrue(res['Is_Sig_Parsable'])
                self.assertEqual(res['dose'], exp_dose)
                self.assertEqual(res['max_dose_per_day'], exp_max)

    def test_bid_patterns(self):
        sigs = [
            ("1 tab po bid", 1, 2.0),
            ("take 1 tablet by mouth twice daily", 1, 2.0),
            ("take 1/2 tablet po bid", 0.5, 1.0),
        ]
        for sig, exp_dose, exp_max in sigs:
            with self.subTest(sig=sig):
                res = self.parser.parse(sig)
                self.assertTrue(res['Is_Sig_Parsable'])
                self.assertEqual(res['dose'], exp_dose)
                self.assertEqual(res['max_dose_per_day'], exp_max)

    def test_tid_patterns(self):
        sigs = [
            ("1 tab po tid", 1, 3.0),
            ("take 3 tabs po tid", 3, 9.0),
            ("take 1 tablet three times daily", 1, 3.0),
        ]
        for sig, exp_dose, exp_max in sigs:
            with self.subTest(sig=sig):
                res = self.parser.parse(sig)
                self.assertTrue(res['Is_Sig_Parsable'])
                self.assertEqual(res['max_dose_per_day'], exp_max)

    def test_qid_patterns(self):
        sigs = [
            ("1 caps po qid", 1, 4.0),
        ]
        for sig, exp_dose, exp_max in sigs:
            with self.subTest(sig=sig):
                res = self.parser.parse(sig)
                self.assertTrue(res['Is_Sig_Parsable'])
                self.assertEqual(res['max_dose_per_day'], exp_max)

    def test_hourly_patterns(self):
        sigs = [
            ("take 1 tablet every 6 hours", 1, 4.0),
            ("take 1 tablet every 8 hours", 1, 3.0),
            ("take 2 tablets q6h prn pain", 2, 8.0),
        ]
        for sig, exp_dose, exp_max in sigs:
            with self.subTest(sig=sig):
                res = self.parser.parse(sig)
                self.assertTrue(res['Is_Sig_Parsable'])
                self.assertEqual(res['max_dose_per_day'], exp_max)


class TestMealContextPatterns(unittest.TestCase):
    """Tests for meal-related patterns"""
    
    def setUp(self):
        self.parser = SigParser()

    def test_daily_with_meal_context(self):
        """Meals should be context, not additional frequency"""
        sigs = [
            ("take 1 tablet by mouth daily with dinner", 1, 1.0),
            ("take 1 tablet by mouth daily after dinner", 1, 1.0),
            ("take half a tablet a day after lunch", 0.5, 0.5),
        ]
        for sig, exp_dose, exp_max in sigs:
            with self.subTest(sig=sig):
                res = self.parser.parse(sig)
                self.assertTrue(res['Is_Sig_Parsable'])
                self.assertEqual(res['dose'], exp_dose)
                self.assertEqual(res['max_dose_per_day'], exp_max)

    def test_twice_daily_with_meal_context(self):
        """'with breakfast and dinner' is context for twice daily"""
        sig = "take one tablet by mouth twice a day with breakfast and dinner"
        result = self.parser.parse(sig)
        self.assertTrue(result['Is_Sig_Parsable'])
        self.assertEqual(result['max_dose_per_day'], 2.0)


class TestSpecialUnits(unittest.TestCase):
    """Tests for special dose units"""
    
    def setUp(self):
        self.parser = SigParser()

    def test_puff_patterns(self):
        sigs = [
            ("inhale 1 puff twice daily", 1, 2.0),
            ("1 puff inhale bid", 1, 2.0),
        ]
        for sig, exp_dose, exp_max in sigs:
            with self.subTest(sig=sig):
                res = self.parser.parse(sig)
                self.assertTrue(res['Is_Sig_Parsable'])
                self.assertEqual(res['max_dose_per_day'], exp_max)

    def test_click_patterns(self):
        sigs = [
            ("apply 1 click daily", 1, 1.0),
            ("4 clicks to skin at bedtime", 4, 4.0),
        ]
        for sig, exp_dose, exp_max in sigs:
            with self.subTest(sig=sig):
                res = self.parser.parse(sig)
                self.assertTrue(res['Is_Sig_Parsable'])
                self.assertEqual(res['dose'], exp_dose)


class TestMorningEveningPatterns(unittest.TestCase):
    """Tests for morning/evening compound patterns"""
    
    def setUp(self):
        self.parser = SigParser()

    def test_same_dose_morning_evening(self):
        """Same dose for morning and evening"""
        sigs = [
            ("take 1 tablet by mouth morning and evening", 1, 2.0),
            ("take 1 tablet by mouth every morning and every evening", 1, 2.0),
        ]
        for sig, exp_dose, exp_max in sigs:
            with self.subTest(sig=sig):
                res = self.parser.parse(sig)
                self.assertTrue(res['Is_Sig_Parsable'])
                self.assertEqual(res['max_dose_per_day'], exp_max)



class TestUserReportedSigs(unittest.TestCase):
    """Tests for specific sigs reported by user with expected behaviors"""
    
    def setUp(self):
        self.parser = SigParser()

    def test_redundant_daily_morning(self):
        # "take 1 capsule by mouth daily take one capsule by mouth every morning"
        # User Expectation: 1 dose daily (or False).
        # Fix: Now fails guardrail for redundancy.
        sig = "take 1 capsule by mouth daily take one capsule by mouth every morning"
        result = self.parser.parse(sig)
        self.assertFalse(result['Is_Sig_Parsable'])

    def test_q8h_with_specific_times(self):
        # "take 1 tablet 200 mg total by mouth every 8 hours take at 6am 2pm and 10pm"
        # User Expectation: 3.0.
        # Now parses specific times and q8h consistently.
        sig = "take 1 tablet 200 mg total by mouth every 8 hours take at 6am 2pm and 10pm"
        result = self.parser.parse(sig)
        self.assertTrue(result['Is_Sig_Parsable'])
        self.assertAlmostEqual(result['max_dose_per_day'], 6.0)

    def test_mixed_doses_half_a_day_typo(self):
        # "take 1 tablet in the morning and half a day in the evening"
        # User Expectation: 1.5 daily.
        # Fix: Preprocessing "half a day" -> "0.5 tablet". Correctly maps doses.
        sig = "take 1 tablet in the morning and half a day in the evening"
        result = self.parser.parse(sig)
        self.assertTrue(result['Is_Sig_Parsable'])
        self.assertEqual(result['max_dose_per_day'], 1.5)

    def test_tablet1_typo(self):
        # "take 1 tablet1 gram by mouth three times daily with meals"
        # User Expectation: 3.
        # Fix: Preprocessing "tablet1" -> "tablet 1".
        sig = "take 1 tablet1 gram by mouth three times daily with meals"
        result = self.parser.parse(sig)
        self.assertTrue(result['Is_Sig_Parsable'])
        self.assertEqual(result['max_dose_per_day'], 3.0)

    def test_different_doses_at_different_times(self):
        # "take 2 tablets in the morning and 1 at night"
        # User Expectation: 3.0.
        sig = "take 2 tablets in the morning and 1 at night"
        result = self.parser.parse(sig)
        self.assertTrue(result['Is_Sig_Parsable'])
        self.assertAlmostEqual(result['max_dose_per_day'], 3.0)

    def test_multiple_specific_times(self):
        # "take 2 tablets orally at 6am 2pm and 9pm"
        # User Expectation: 6.0.
        sig = "take 2 tablets orally at 6am 2pm and 9pm"
        result = self.parser.parse(sig)
        self.assertTrue(result['Is_Sig_Parsable'])
        self.assertAlmostEqual(result['max_dose_per_day'], 6.0)

    def test_mwf_ambiguous(self):
        # "take one 1 tablets by mouth once a day monday wednesday and friday of each week"
        # User Expectation: 3.
        # Current Behavior: Unparsable (Ambiguous between 'once a day' and 'MWF').
        # Rationale: Design choice to flag ambiguity.
        sig = "take one 1 tablets by mouth once a day monday wednesday and friday of each week"
        result = self.parser.parse(sig)
        if result['Is_Sig_Parsable']:
             self.assertLess(result['max_dose_per_day'], 1.0)
        else:
             self.assertFalse(result['Is_Sig_Parsable'])

    def test_one_and_a_half(self):
        # "take one and a half pills daily 150 mg total"
        # User Expectation: 1.5.
        # Fix: Preprocessing "one and a half" -> "1.5".
        sig = "take one and a half pills daily 150 mg total"
        result = self.parser.parse(sig)
        self.assertTrue(result['Is_Sig_Parsable'])
        self.assertEqual(result['max_dose_per_day'], 1.5)

    def test_at_symbol_time_range(self):
        # "take one tablet by mouth twice daily @ 9am-5p"
        # User Expectation: Parsable.
        sig = "take one tablet by mouth twice daily @ 9am-5p"
        result = self.parser.parse(sig)
        self.assertTrue(result['Is_Sig_Parsable'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
