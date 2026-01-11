import unittest
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers.sig import SigParser

class TestSimpleSigs(unittest.TestCase):
    """Tests for sigs that should be parsable but were previously flagged as unparsable"""
    
    def setUp(self):
        self.parser = SigParser()

    def test_time_based_sigs(self):
        """Test sigs with specific times like 5:00 pm"""
        sigs = [
            "take 1 tablet by mouth every day at 5:00 pm",
            "take 1 tablet by mouth every day at 5pm",
            "take 1 tablet10 mg by mouth every day at 5 pm",
            "take 1 tablet20 mg by mouth every day at 5 pm",
        ]
        for sig in sigs:
            with self.subTest(sig=sig):
                result = self.parser.parse(sig)
                self.assertTrue(result['Is_Sig_Parsable'], f"Should be parsable: {sig}")
                self.assertEqual(result['max_dose_per_day'], 1.0)
                self.assertEqual(result['frequency'], 1)

    def test_one_time_per_day(self):
        """Test sigs with '1 time' phrasing"""
        sigs = [
            "take 1 tablet by mouth 1 time every day",
            "take 1 tablet by mouth 1 time a day",
            "take 1 tablet by mouth one time daily",
        ]
        for sig in sigs:
            with self.subTest(sig=sig):
                result = self.parser.parse(sig)
                self.assertTrue(result['Is_Sig_Parsable'], f"Should be parsable: {sig}")
                self.assertEqual(result['max_dose_per_day'], 1.0)

    def test_or_frequency_ranges(self):
        """Test sigs with 'once or twice' patterns"""
        sig = "take 1-2 tablets 10-20 mg once or twice a day"
        result = self.parser.parse(sig)
        self.assertTrue(result['Is_Sig_Parsable'])
        # max_dose_per_day should consider the upper bounds: 2 tablets × 2 times = 4
        self.assertEqual(result['max_dose_per_day'], 4.0)

    def test_after_meal_timing(self):
        """Test sigs with meal-based timing"""
        sigs = [
            "take 1 tablet 40 mg total by mouth after dinner",
            "take 1 tablet 5 mg total by mouth after lunch",
        ]
        for sig in sigs:
            with self.subTest(sig=sig):
                result = self.parser.parse(sig)
                self.assertTrue(result['Is_Sig_Parsable'], f"Should be parsable: {sig}")
                self.assertIsNotNone(result['dose'])

    def test_basic_daily_sigs(self):
        """Test basic daily dosing sigs"""
        sigs = [
            "take 1 tablet 5 mg total by mouth",
            "take 1 tablet 5 mg total by mouth every day at 5:00 pm",
            "take 1 tablet 50 mg total by mouth every day at 5:00 pm",
            "take 1 tablet 80 mg total by mouth every day at 5:00 pm",
        ]
        for sig in sigs:
            with self.subTest(sig=sig):
                result = self.parser.parse(sig)
                self.assertTrue(result['Is_Sig_Parsable'], f"Should be parsable: {sig}")

    def test_titration_sigs_unparsable(self):
        """Test that titration sigs are correctly marked as unparsable"""
        sigs = [
            "take 1 tablet by mouth daily for 3 days then 2 tablets daily",
            "take 1 tablet by mouth once daily for 7 days then 2 tablets once daily",
            "take 1/2 tablet daily x 1 week then increase to one tablet daily",
            "take 1/2 tablet twice daily increase to 1 tab twice a day",
        ]
        for sig in sigs:
            with self.subTest(sig=sig):
                result = self.parser.parse(sig)
                self.assertFalse(result['Is_Sig_Parsable'], 
                               f"Titration sig should be unparsable: {sig}")

    def test_multi_instruction_sigs(self):
        """Test sigs with multiple separate instructions"""
        sigs = [
            "take 1 tablet by mouth in the morning and then take 1 tablet by mouth in the evening with meals",
            "take 1 tablet by mouth on monday wednesdays and fridays",
        ]
        for sig in sigs:
            with self.subTest(sig=sig):
                result = self.parser.parse(sig)
                # These should be parsable
                self.assertTrue(result['Is_Sig_Parsable'], f"Should be parsable: {sig}")

    def test_mwf_sigs(self):
        """Test Monday-Wednesday-Friday dosing patterns"""
        sig = "take one 1 tablets by mouth once a day monday wednesday and friday"
        result = self.parser.parse(sig)
        self.assertTrue(result['Is_Sig_Parsable'])
        # Current logic defaults to daily (1.0) which is a safe over-estimate for labeling
        self.assertEqual(result['max_dose_per_day'], 1.0)

    def test_frequency_refinement_issues(self):
        """Test sigs where time-of-day creates refinement ambiguity"""
        sig = "take 1/2 tablet by mouth 1 time a day in the morning"
        result = self.parser.parse(sig)
        self.assertTrue(result['Is_Sig_Parsable'])
        self.assertEqual(result['max_dose_per_day'], 0.5)

    def test_each_week_refinement(self):
        """Test that 'each week' creates refinement ambiguity"""
        sig = "take one 1 tablets by mouth once a day monday wednesday and friday of each week"
        result = self.parser.parse(sig)
        # Now parsable with safe default
        self.assertTrue(result['Is_Sig_Parsable'])

if __name__ == '__main__':
    unittest.main()
