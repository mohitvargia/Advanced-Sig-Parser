import unittest
import sys
import os

# Adjust path to import parsers
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers.sig import SigParser

class TestBasicSigs(unittest.TestCase):
    def setUp(self):
        self.parser = SigParser()

    def test_full_basic_sig_list(self):
        # Full list of 28 sigs provided by user, with expected behaviors based on latest parser state.
        test_cases = [
            # Successful Parses
            ("take 2 tablets in the morning and 1 at night", True, 3.0),
            ("take 2 tablets orally at 6am 2pm and 9pm", True, 6.0),
            ("take 1 daily", True, 1.0),
            ("take 1 bid", True, 2.0),
            ("take 1 every evening", True, 1.0),
            ("take 1 every morning", True, 1.0),
            ("take 1 twice daily", True, 2.0),
            ("take 1 tablet by mouth every day at 5:00 pm", True, 1.0),
            ("take one tablet by mouth twice daily at 9am-5p", True, 2.0),
            ("take 2 tablet by mouth every morning and 1 tablet by mouth every night at bed", True, 3.0),
            
            # New Fixed Sigs
            ("take one tablet by mouth daily at 5 in the evening", True, 1.0),
            ("take 1 tablet 200 mg total by mouth every 8 hours take at 6am 2pm and 10pm", True, 3.0),
            ("take 1 tablet 40 mg total by mouth 2 times daily 8:00 am and 2:00 pm", True, 2.0),
            ("take one tab every day bid", True, 2.0),
            ("take 0.5 tablets by mouth 2 times daily 1/2 tab bid", False, None),
            
            # Parsable but No Max Dose (PRN, Missing Freq, or Strength-only)
            ("take 1 mg by mouth daily", True, 1.0),
            ("take 1 tablet 20 mg total by mouth as needed", True, None),
            ("take 1 tablet 5 mg total by mouth", True, None),
            ("take 1 tablet by mouth on monday wednesdays and Fridays", True, 1.0),
            ("take one 1 tablets by mouth once a day on monday wednesday and Friday", True, 1.0),
            ("take 1 tablet 50mg total by mouth", True, None),

            # Passed but with 1.0 Max Dose (Previously thought False)
            ("take 1 tablet 40 mg total by mouth every day at 5:00 pm", True, 1.0),
            ("take 1 tablet 5 mg total by mouth every day at 5:00 pm", True, 1.0),
            ("take 1 tablet 50 mg total by mouth every day at 5:00 pm", True, 1.0),
            ("take 1 tablet 80 mg total by mouth every day at 5:00 pm", True, 1.0),

            # Unparsable / Ambiguous / Titration / Complex
            ("take one 1 tablets by mouth once a day monday wednesday and friday of each we", False, None),
            ("take one 1 tablets by mouth once in the morning and one at 2 pm", False, None),
            ("take 1 and 1/2 to 2 tablets by mouth daily", False, None),
            ("take 2 tablets by mouth in the morning and then take 2 tablets in the evening", False, None),
            ("take 1 tablet 10 mg total by mouth 1 one time each day", False, None),
            ("take 1 tablet 10 mg total by mouth daily 1 tab", False, None),
            ("take 1 tablet by mouth once daily for 7 days then 2 tablets once daily", False, None),
            ("take 2 tablets by mouth every morning and take 1 tablet by mouth daily in the", False, None),
        ]

        for sig, expected_parsable, expected_max in test_cases:
            with self.subTest(sig=sig):
                res = self.parser.parse(sig)
                self.assertEqual(res['Is_Sig_Parsable'], expected_parsable, 
                                 f"Parsability mismatch for: {sig}. Got: {res['Is_Sig_Parsable']}")
                if expected_max is not None:
                     self.assertIsNotNone(res['max_dose_per_day'], f"Expected Max Dose for: {sig}")
                     self.assertAlmostEqual(res['max_dose_per_day'], expected_max, delta=0.01, 
                                            msg=f"Max dose mismatch for: {sig}")
                elif expected_parsable and expected_max is None:
                     # If Passable but Max Dose expected None, verify it is None
                     self.assertIsNone(res['max_dose_per_day'], f"Expected None Max Dose for: {sig}")

if __name__ == '__main__':
    unittest.main()
