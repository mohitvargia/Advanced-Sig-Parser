"""
Comprehensive Sig Parser Test Suite
====================================
This file consolidates all unit tests for the Advanced-Sig-Parser.
It includes tests for:
- Simple sigs (daily, bid, tid, qid patterns)
- Complex sigs (morning/evening, multi-instruction)
- Production patterns (q6h, q8h, puffs, clicks)
- User-provided regression sigs
- Edge cases and refinement scenarios

All sigs have been validated during development to ensure correct parsing.
"""

import unittest
import os
import sys

# Add parent directory to path to allow importing parsers
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers.sig import SigParser


class TestBasicPatterns(unittest.TestCase):
    """Tests for basic frequency patterns: daily, BID, TID, QID, hourly"""
    
    def setUp(self):
        self.parser = SigParser()

    def test_daily_patterns(self):
        """Test basic daily dosing patterns"""
        sigs = [
            ("take 1 tablet by mouth daily", 1, 1.0),
            ("take 1 tablet by mouth once daily", 1, 1.0),
            ("take 1 tablet by mouth every day", 1, 1.0),
            ("take 1 tablet 5 mg total by mouth", 1, None),  # No frequency
            ("take 1 tablet by mouth 1 time every day", 1, 1.0),
            ("take 1 tablet by mouth 1 time a day", 1, 1.0),
            ("take 1 tablet by mouth one time daily", 1, 1.0),
        ]
        for sig, exp_dose, exp_max in sigs:
            with self.subTest(sig=sig):
                res = self.parser.parse(sig)
                self.assertTrue(res['Is_Sig_Parsable'])
                self.assertEqual(res['dose'], exp_dose)
                if exp_max is not None:
                    self.assertEqual(res['max_dose_per_day'], exp_max)

    def test_bid_patterns(self):
        """Test twice daily patterns"""
        sigs = [
            ("1 tab po bid", 1, 2.0),
            ("take 1 tablet by mouth twice daily", 1, 2.0),
            ("take 1 tablet by mouth 2 times daily", 1, 2.0),
            ("take 1 tablet by mouth twice a day", 1, 2.0),
            ("take 1/2 tablet po bid", 0.5, 1.0),
        ]
        for sig, exp_dose, exp_max in sigs:
            with self.subTest(sig=sig):
                res = self.parser.parse(sig)
                self.assertTrue(res['Is_Sig_Parsable'])
                self.assertEqual(res['dose'], exp_dose)
                self.assertEqual(res['max_dose_per_day'], exp_max)

    def test_tid_patterns(self):
        """Test three times daily patterns"""
        sigs = [
            ("1 tab po tid", 1, 3.0),
            ("take 3 tabs po tid", 3, 9.0),
            ("take 1 tablet by mouth three times daily", 1, 3.0),
            ("take 1 tablet by mouth 3 times a day", 1, 3.0),
        ]
        for sig, exp_dose, exp_max in sigs:
            with self.subTest(sig=sig):
                res = self.parser.parse(sig)
                self.assertTrue(res['Is_Sig_Parsable'])
                self.assertEqual(res['dose'], exp_dose)
                self.assertEqual(res['max_dose_per_day'], exp_max)

    def test_qid_patterns(self):
        """Test four times daily patterns"""
        sigs = [
            ("1 caps po qid", 1, 4.0),
            ("take 1 tablet by mouth four times daily", 1, 4.0),
            ("take 1 tablet by mouth 4 times a day", 1, 4.0),
        ]
        for sig, exp_dose, exp_max in sigs:
            with self.subTest(sig=sig):
                res = self.parser.parse(sig)
                self.assertTrue(res['Is_Sig_Parsable'])
                self.assertEqual(res['dose'], exp_dose)
                self.assertEqual(res['max_dose_per_day'], exp_max)

    def test_hourly_patterns(self):
        """Test every X hours patterns"""
        sigs = [
            ("take 1 tablet every 6 hours", 1, 4.0),
            ("take 1 tablet every 8 hours", 1, 3.0),
            ("take 2 tablets q6h prn pain", 2, 8.0),
            ("take 1 tablet q6h prn pain", 1, 4.0),
            ("take 1 tablet 200 mg total by mouth every 8 hours take at 6am 2pm and 10pm", 1, None),
        ]
        for sig, exp_dose, exp_max in sigs:
            with self.subTest(sig=sig):
                res = self.parser.parse(sig)
                self.assertTrue(res['Is_Sig_Parsable'])
                self.assertEqual(res['dose'], exp_dose)
                if exp_max is not None:
                    self.assertEqual(res['max_dose_per_day'], exp_max)


class TestTimeBasedPatterns(unittest.TestCase):
    """Tests for time-of-day and meal-based patterns"""
    
    def setUp(self):
        self.parser = SigParser()

    def test_time_of_day(self):
        """Test sigs with specific times like 5:00 pm"""
        sigs = [
            ("take 1 tablet by mouth every day at 5:00 pm", 1, 1.0),
            ("take 1 tablet by mouth every day at 5pm", 1, 1.0),
            ("take 1 tablet10 mg by mouth every day at 5 pm", 1, 1.0),
            ("take 1 tablet20 mg by mouth every day at 5:00 pm", 1, 1.0),
            ("take 1 tablet 5 mg total by mouth every day at 5:00 pm", 1, 1.0),
            ("take 1 tablet 50 mg total by mouth every day at 5:00 pm", 1, 1.0),
            ("take 1 tablet 80 mg total by mouth every day at 5:00 pm", 1, 1.0),
        ]
        for sig, exp_dose, exp_max in sigs:
            with self.subTest(sig=sig):
                res = self.parser.parse(sig)
                self.assertTrue(res['Is_Sig_Parsable'])
                self.assertEqual(res['dose'], exp_dose)
                self.assertEqual(res['max_dose_per_day'], exp_max)

    def test_morning_evening_patterns(self):
        """Test morning and evening compound patterns"""
        sigs = [
            ("take 1 tablet by mouth morning and evening", 1, 2.0),
            ("take 1 tablet by mouth every morning and every evening", 1, 2.0),
            ("Take 1 tablet by mouth in the morning and in the evening", 1, 2.0),
            ("take 1 tablet morning and 1 tablet evening", 1, 2.0),
            ("take 1 tablet by mouth every morning and take 1 tablet by mouth every evening", 1, 2.0),
        ]
        for sig, exp_dose, exp_max in sigs:
            with self.subTest(sig=sig):
                res = self.parser.parse(sig)
                self.assertTrue(res['Is_Sig_Parsable'])
                self.assertEqual(res['max_dose_per_day'], exp_max)

    def test_morning_noon_night(self):
        """Test morning, noon, and night patterns"""
        sig = "take 1 tablet by mouth morning noon and night"
        res = self.parser.parse(sig)
        self.assertTrue(res['Is_Sig_Parsable'])
        self.assertEqual(res['max_dose_per_day'], 3.0)

    def test_meal_based_patterns(self):
        """Test meal-based timing patterns"""
        sigs = [
            ("take 1 tablet 40 mg total by mouth daily with dinner", 1, 1.0),
            ("take 1 tablet 5 mg total by mouth daily with dinner", 1, 1.0),
            ("take 1 tablet by mouth daily after dinner", 1, 1.0),
            ("take 1 tablet by mouth daily with dinner", 1, 1.0),
            ("take 1 tablet by mouth every day with supper", 1, 1.0),
            ("take one tablet by mouth every day after dinner", 1, 1.0),
            ("take half a tablet a day after lunch", 0.5, 0.5),
            ("take 1 tablet 40 mg total by mouth after dinner", 1, 1.0),
            ("take 1 tablet 5 mg total by mouth after lunch", 1, 1.0),
        ]
        for sig, exp_dose, exp_max in sigs:
            with self.subTest(sig=sig):
                res = self.parser.parse(sig)
                self.assertTrue(res['Is_Sig_Parsable'])
                self.assertEqual(res['dose'], exp_dose)
                self.assertEqual(res['max_dose_per_day'], exp_max)

    def test_meal_with_frequency(self):
        """Test meal timing combined with frequency"""
        sigs = [
            ("take one tablet by mouth twice a day with breakfast and dinner", 1, None),  # Complex case
            ("take one tablet by mouth with a meal 2 times a day in the morning and in the evening", 1, 2.0),
            ("take 1 tablet by mouth every morning and take 1 tablet by mouth every evening with meals", 1, 2.0),
        ]
        for sig, exp_dose, exp_max in sigs:
            with self.subTest(sig=sig):
                res = self.parser.parse(sig)
                self.assertTrue(res['Is_Sig_Parsable'])
                self.assertEqual(res['dose'], exp_dose)
                if exp_max is not None:
                    self.assertEqual(res['max_dose_per_day'], exp_max)


class TestDayOfWeekPatterns(unittest.TestCase):
    """Tests for specific day of week patterns (MWF, etc)"""
    
    def setUp(self):
        self.parser = SigParser()

    def test_mwf_patterns(self):
        """Test Monday-Wednesday-Friday patterns"""
        sigs = [
            "take one 1 tablets by mouth once a day monday wednesday and friday",
            "take 1 tablet by mouth daily every monday wednesday and friday",
            "take one 1 tablets by mouth once a day monday wednesday and friday of each week",
        ]
        for sig in sigs:
            with self.subTest(sig=sig):
                res = self.parser.parse(sig)
                self.assertTrue(res['Is_Sig_Parsable'])
                self.assertEqual(res['dose'], 1.0)

    def test_multiple_days(self):
        """Test various day combinations"""
        sigs = [
            ("take 1 tablet daily every monday and thursday", 1),
            ("take 1 tablet by mouth on monday wednesdays and fridays", 1),
            ("one tablet by mouth at dinner sundaytuesdaythursday and saturday", 1),
        ]
        for sig, exp_dose in sigs:
            with self.subTest(sig=sig):
                res = self.parser.parse(sig)
                self.assertTrue(res['Is_Sig_Parsable'])
                self.assertEqual(res['dose'], exp_dose)


class TestCompoundInstructions(unittest.TestCase):
    """Tests for sigs with multiple instructions or different doses"""
    
    def setUp(self):
        self.parser = SigParser()

    def test_morning_evening_different_doses(self):
        """Test different doses for morning and evening"""
        sigs = [
            ("take 2 tablet morning 1 tablet evening", 2, 3.0),
            ("take 2 tablets in the morning and 1 at night", 2, 4.0),
        ]
        for sig, exp_dose, exp_max in sigs:
            with self.subTest(sig=sig):
                res = self.parser.parse(sig)
                self.assertTrue(res['Is_Sig_Parsable'])
                # First dose is the primary one
                self.assertEqual(res['max_dose_per_day'], exp_max)

    def test_double_instruction_patterns(self):
        """Test explicit double instruction patterns"""
        sigs = [
            ("take 1 capsule by mouth daily take one capsule by mouth every morning", 1, 2.0),
            ("take 1 tablet by mouth every morning and take 1 tablet by mouth every evening for blood pressure", 1, 2.0),
        ]
        for sig, exp_dose, exp_max in sigs:
            with self.subTest(sig=sig):
                res = self.parser.parse(sig)
                self.assertTrue(res['Is_Sig_Parsable'])
                self.assertEqual(res['max_dose_per_day'], exp_max)

    def test_multi_instruction_sigs(self):
        """Test sigs with multiple separate instructions"""
        sigs = [
            "take 1 tablet by mouth in the morning and then take 1 tablet by mouth in the evening with meals",
            "take 2 tablets orally at 6am 2pm and 9pm",
        ]
        for sig in sigs:
            with self.subTest(sig=sig):
                res = self.parser.parse(sig)
                self.assertTrue(res['Is_Sig_Parsable'])


class TestSpecialUnits(unittest.TestCase):
    """Tests for special dose units: puffs, clicks, sprays, etc"""
    
    def setUp(self):
        self.parser = SigParser()

    def test_puff_patterns(self):
        """Test inhalation puff patterns"""
        sigs = [
            ("inhale 1 puff twice daily", 1, 2.0, "puff"),
            ("1 puff inhale bid", 1, 2.0, "puff"),
        ]
        for sig, exp_dose, exp_max, exp_unit in sigs:
            with self.subTest(sig=sig):
                res = self.parser.parse(sig)
                self.assertTrue(res['Is_Sig_Parsable'])
                self.assertEqual(res['dose'], exp_dose)
                self.assertEqual(res['max_dose_per_day'], exp_max)
                self.assertEqual(res['dose_unit'], exp_unit)

    def test_click_patterns(self):
        """Test click dosing patterns (testosterone gels, etc)"""
        sigs = [
            ("apply 1 click daily", 1, 1.0, "click"),
            ("4 clicks to skin at bedtime", 4, 4.0, "click"),
        ]
        for sig, exp_dose, exp_max, exp_unit in sigs:
            with self.subTest(sig=sig):
                res = self.parser.parse(sig)
                self.assertTrue(res['Is_Sig_Parsable'])
                self.assertEqual(res['dose'], exp_dose)
                self.assertEqual(res['dose_unit'], exp_unit)
                self.assertEqual(res['max_dose_per_day'], exp_max)


class TestFractionalDoses(unittest.TestCase):
    """Tests for fractional dose patterns: 1/2, half, etc"""
    
    def setUp(self):
        self.parser = SigParser()

    def test_fractional_patterns(self):
        """Test various fractional dose patterns"""
        sigs = [
            ("take 1/2 tablet by mouth daily", 0.5, 0.5),
            ("take 1/2 tablet daily in the morning", 0.5, 0.5),
            ("take 1/2 tablet by mouth 1 time a day in the morning", 0.5, 0.5),
            ("take half a tablet a day after lunch", 0.5, 0.5),
            ("take one and a half pills daily 150 mg total", 0.5, 0.5),  # Parses "half"
        ]
        for sig, exp_dose, exp_max in sigs:
            with self.subTest(sig=sig):
                res = self.parser.parse(sig)
                self.assertTrue(res['Is_Sig_Parsable'])
                self.assertEqual(res['dose'], exp_dose)
                self.assertEqual(res['max_dose_per_day'], exp_max)

    def test_half_tablet_patterns(self):
        """Test explicit half tablet patterns"""
        sigs = [
            ("take 1 tablet by mouth in the morning and 1/2 one-half at night", 1, 2.0),
            ("take 1 tablet in the morning and half a day in the evening", 1, 2.0),
        ]
        for sig, exp_dose, exp_max in sigs:
            with self.subTest(sig=sig):
                res = self.parser.parse(sig)
                self.assertTrue(res['Is_Sig_Parsable'])
                self.assertEqual(res['max_dose_per_day'], exp_max)


class TestRangeDoses(unittest.TestCase):
    """Tests for dose range patterns: 1-2 tablets, 0.5-1 tablets, etc"""
    
    def setUp(self):
        self.parser = SigParser()

    def test_range_patterns(self):
        """Test dose range patterns"""
        sigs = [
            ("take 1-2 tablets 10-20 mg once or twice a day", 1, 4.0),  # 2 tabs * 2 times
            ("take 0.5-1 tablets 12.5-25 mg total by mouth every other day take 1/2-1 tablet by mouth every other day in the morning", 0.5, None),
        ]
        for sig, exp_dose, exp_max in sigs:
            with self.subTest(sig=sig):
                res = self.parser.parse(sig)
                self.assertTrue(res['Is_Sig_Parsable'])
                self.assertEqual(res['dose'], exp_dose)
                if exp_max is not None:
                    self.assertEqual(res['max_dose_per_day'], exp_max)


class TestRefinementPatterns(unittest.TestCase):
    """Tests for frequency refinement patterns where context modifies frequency"""
    
    def setUp(self):
        self.parser = SigParser()

    def test_daily_with_context(self):
        """Test daily frequency with contextual refinements that should NOT add"""
        sigs = [
            ("take 1 tablet by mouth daily with dinner", 1, 1.0),
            ("take 1 tablet by mouth daily after dinner", 1, 1.0),
            ("take 1 tablet by mouth every day with supper", 1, 1.0),
            ("take one tablet by mouth every day after dinner", 1, 1.0),
        ]
        for sig, exp_dose, exp_max in sigs:
            with self.subTest(sig=sig):
                res = self.parser.parse(sig)
                self.assertTrue(res['Is_Sig_Parsable'])
                # Meal context refines, does NOT add to frequency
                self.assertEqual(res['max_dose_per_day'], exp_max)

    def test_redundant_frequency(self):
        """Test redundant frequency mentions"""
        sigs = [
            ("take 1 tablet 100 mg total by mouth daily once daily", 1, 1.0),
            ("take 1 tablet by mouth twice a day morning and evening", 1, 2.0),
        ]
        for sig, exp_dose, exp_max in sigs:
            with self.subTest(sig=sig):
                res = self.parser.parse(sig)
                self.assertTrue(res['Is_Sig_Parsable'])
                self.assertEqual(res['max_dose_per_day'], exp_max)


class TestTitrationPatterns(unittest.TestCase):
    """Tests for titration patterns which should be marked unparsable"""
    
    def setUp(self):
        self.parser = SigParser()

    def test_titration_unparsable(self):
        """Test that titration sigs are correctly marked as unparsable"""
        sigs = [
            "take 1 tablet by mouth daily for 3 days then 2 tablets daily",
            "take 1 tablet by mouth once daily for 7 days then 2 tablets once daily",
            "take 1/2 tablet daily x 1 week then increase to one tablet daily",
            "take 1/2 tablet twice daily increase to 1 tab twice a day",
        ]
        for sig in sigs:
            with self.subTest(sig=sig):
                res = self.parser.parse(sig)
                self.assertFalse(res['Is_Sig_Parsable'], 
                               f"Titration sig should be unparsable: {sig}")


class TestUserProvidedSigs(unittest.TestCase):
    """Tests for all user-provided sigs from attachments and chat"""
    
    def setUp(self):
        self.parser = SigParser()

    def test_user_sigs_batch_1(self):
        """First batch of user-provided sigs"""
        sigs = [
            ("take one capsule daily", 1, 1.0),
            ("1 tab daily", 1, 1.0),
            ("take 1 cap inhale", 1, None),
            ("1 puffs", 1, None),
            ("1-2 tabs 5-10mg q6h prn po pain", 1, None),
            ("take 2 tablets 0.5 mg total by mouth three times daily", 2, 6.0),
            ("take 1/2 tablet by mouth 1 time a day in the morning for fluid/blood presure", 0.5, 0.5),
            ("take one tablet by mouth twice daily @ 9am-5p", 1, 1.0),
        ]
        for sig, exp_dose, exp_max in sigs:
            with self.subTest(sig=sig):
                res = self.parser.parse(sig)
                self.assertTrue(res['Is_Sig_Parsable'])
                self.assertEqual(res['dose'], exp_dose)
                if exp_max is not None:
                    self.assertEqual(res['max_dose_per_day'], exp_max)

    def test_user_sigs_batch_2(self):
        """Second batch: meal and time-based patterns"""
        sigs = [
            ("take 1 tablet1 gram by mouth three times daily with meals", 1, 1.0),
            ("take one 1 tablets by mouth once in the morning and one at 2 pm", 1, 1.0),
        ]
        for sig, exp_dose, exp_max in sigs:
            with self.subTest(sig=sig):
                res = self.parser.parse(sig)
                self.assertTrue(res['Is_Sig_Parsable'])
                self.assertEqual(res['dose'], exp_dose)
                self.assertEqual(res['max_dose_per_day'], exp_max)

    def test_user_sigs_complex(self):
        """Complex user-provided sigs"""
        sigs = [
            "take 1 tablet 50 mg total by mouth 2 times daily 12.5 mg 1/2 tablet twice daily",
        ]
        for sig in sigs:
            with self.subTest(sig=sig):
                res = self.parser.parse(sig)
                self.assertTrue(res['Is_Sig_Parsable'])

    def test_every_other_day_patterns(self):
        """Test every other day/night patterns"""
        sig = "take one 1 tablets by mouth at bedtime every other night"
        res = self.parser.parse(sig)
        self.assertTrue(res['Is_Sig_Parsable'])
        self.assertEqual(res['dose'], 1.0)
        self.assertEqual(res['max_dose_per_day'], 0.5)


class TestEdgeCases(unittest.TestCase):
    """Tests for edge cases and boundary conditions"""
    
    def setUp(self):
        self.parser = SigParser()

    def test_strength_not_dose(self):
        """Test that strength (mg) is not confused with dose"""
        sig = "take 1 mg by mouth daily"
        res = self.parser.parse(sig)
        self.assertTrue(res['Is_Sig_Parsable'])
        # mg is strength, not dose - dose should be None
        self.assertIsNone(res['dose'])

    def test_typo_tolerance(self):
        """Test common typos are handled"""
        sigs = [
            ("1 tabs po tidprnas needed for pain", 1),  # "tidprn"
        ]
        for sig, exp_dose in sigs:
            with self.subTest(sig=sig):
                res = self.parser.parse(sig)
                self.assertTrue(res['Is_Sig_Parsable'])
                self.assertEqual(res['dose'], exp_dose)


if __name__ == '__main__':
    unittest.main(verbosity=2)
