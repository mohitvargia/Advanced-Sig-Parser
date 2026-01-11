import unittest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers.sig import SigParser

class TestBulkVerifiedSigs(unittest.TestCase):
    def setUp(self):
        self.parser = SigParser()

    def test_bulk_sigs(self):
        sigs = [
            ("take 1.5 pills daily 150 mg total", 1.5),
            ("take one tablet by mouth twice a day with breakfast and dinner", 2.0),
            ("take 0.5-1 tablets 12.5-25 mg total by mouth every other day take 1/2-1 tablet by mouth every other day in the morning", 1.0),
            ("take 1 tablet 40 mg total by mouth daily with dinner", 1.0),
            ("take 1 tablet 5 mg total by mouth daily with dinner", 1.0),
            ("take 1 tablet by mouth daily after dinner", 1.0),
            ("take 1 tablet by mouth daily with dinner", 1.0),
            ("take 1 tablet by mouth every day with supper", 1.0),
            ("take half a tablet a day after lunch", 0.5),
            ("take one tablet by mouth every day after dinner", 1.0),
            ("1/2- 1 tab q hs", 1.0),
            ("take 1/2 tablet by mouth 1 time a day in the morning for fluid/blood presure", 0.5),
            ("take 1/2 tablet by mouth 1 time a day in the morning", 0.5),
            ("take 2 pills in the am and 1 pill in the pm", 3.0),
            ("take 2 tablets by mouth in the am and 1 tablet by mouth in the evening", 3.0),
            ("take 1 tablet 40 mg total by mouth after dinner", 1.0),
            ("take 1 tablet 5 mg total by mouth after lunch", 1.0),
            ("take 1 tablet by mouth 1 time every day", 1.0),
            ("take 1 tablet by mouth 1 time a day", 1.0),
            ("take 1 tablet by mouth one time daily", 1.0),
            ("take 1-2 tablets 1.25-2.5 mg total by mouth daily as needed", 2.0),
            ("take 1-2 tablets 1.25-2.5 mg total by mouth every morning", 2.0),
            ("take 1-2 tablets 1.25-2.5 mg total by mouth three times a week", 0.8571428571428571),
            ("take 1-2 tablets 10-20 mg total by mouth 3 times daily as needed", 6.0),
            ("take 1-2 tablets 10-20 mg once or twice a day", 4.0),
            ("take 1 tablet 100 mg total by mouth daily once daily", 1.0),
            ("take 1 tablet by mouth every morning and 1 tablet every evening", 2.0),
            ("take 1 tablet by mouth every morning and take 1 tablet by mouth every evening", 2.0),
            ("take 1 tablet by mouth twice a day morning and evening", 2.0),
            ("take 1 tablet by mouth twice a day in the morning and in the evening", 2.0),
            ("take 1 tablet by mouth twice a day in the morning and in the evening", 2.0),
            ("take one 1 tablets by mouth at bedtime every other night", 0.5),
            ("take one tablet by mouth every morning and take one tablet by mouth every evening", 2.0),
            ("take one tablet by mouth every morning and take one tablet by mouth every evening - take with mea", 2.0),
            ("take one tablet by mouth every morning and take one tablet by mouth every evening take with meal", 2.0),
            ("take one tablet by mouth every morning and take one tablet by mouth every evening take with meal duplicate", 2.0),
            ("take one tablet by mouth every morning and take one tablet by mouth every evening with meal", 2.0),
            ("take one tablet by mouth every morning and take one tablet by mouth every evening with meals", 2.0),
            ("take one tablet by mouth every morning take one tablet by mouth every evening take with meal", 2.0),
            ("take one tablet by mouth twice a day morning and evening", 2.0),
            ("take one tablet by mouth twice a day in the morning and evening with meals", 2.0),
            ("take one tablet by mouth twice a day in the morning and evening", 2.0),
            ("take one tablet by mouth twice a day every morning and every evening", 2.0),
            ("take one tablet by mouth twice a day in the morning and in the evening with meal", 2.0),
            ("take one tablet by mouth every morning and 1 tablet every evening with meals", 2.0),
            ("take one tablet by mouth with a meal 2 times a day in the morning and in the evening", 2.0),
        ]
        for sig_text, expected_max in sigs:
            with self.subTest(sig=sig_text):
                 res = self.parser.parse(sig_text)
                 self.assertTrue(res['Is_Sig_Parsable'], f'Failed to parse: {sig_text}')
                 if expected_max is not None:
                      self.assertAlmostEqual(res['max_dose_per_day'], expected_max, places=2)

if __name__ == '__main__':
    unittest.main()
