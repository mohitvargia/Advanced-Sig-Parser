import unittest
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers.sig import SigParser

class TestRedundancy(unittest.TestCase):
    def setUp(self):
        self.parser = SigParser()

    def test_bedtime_redundancy(self):
        sig = "take 1 tablet by mouth at bedtime"
        result = self.parser.parse(sig)
        readable = result['sig_readable']
        print(f"\nInput: {sig}")
        print(f"Output: {readable}")
        
        # Check that "at bedtime" only appears once
        count = readable.count("bedtime")
        self.assertEqual(count, 1, f"Expected 'bedtime' to appear once, but found it {count} times in '{readable}'")

    def test_morning_redundancy(self):
        sig = "take 1 tablet in the morning"
        result = self.parser.parse(sig)
        readable = result['sig_readable']
        print(f"\nInput: {sig}")
        print(f"Output: {readable}")
        
        count = readable.count("morning")
        self.assertEqual(count, 1, f"Expected 'morning' to appear once, but found it {count} times in '{readable}'")

    def test_input_cases(self):
        """Test unique cases from input.csv with full field validation"""
        test_cases = [
            {
                "input": "take one capsule daily",
                "expected": {
                    "sig_readable": "take 1 capsule by mouth daily",
                    "max_dose_per_day": 1.0,
                    "dose": 1,
                    "frequency": 1,
                    "dose_unit": "capsule",
                    "strength_unit": None,
                    "strength": None
                }
            },
            {
                "input": "1 po qd",
                "expected": {
                    "sig_readable": "1 by mouth daily",
                    "max_dose_per_day": 1.0,
                    "dose": 1,
                    "frequency": 1,
                    "dose_unit": None, # Unit inferred? No, 'po' is route. '1' is lone dose. Parser might output None for unit if not explicit.
                    "strength_unit": None,
                    "strength": None
                }
            },
             {
                "input": "take 1 tablet by mouth in the morning and 1 tablet before bedtime do all this for 7 days",
                "expected": {
                    "sig_readable": "take 1 tablet in the morning and 1 tablet bedtime by mouth for 7 days",
                    "max_dose_per_day": 2.0,
                    "dose": 1,
                    "frequency": 2, # 1+1
                    "dose_unit": "tablet",
                    "strength_unit": None,
                    "strength": None
                }
            },
            {
                 "input": "1-2 tabs 5-10mg q6h prn po pain",
                 "expected": {
                    "sig_readable": "1-2 tablets (5-10 mg) by mouth every 6 hours as needed for pain",
                    "max_dose_per_day": 8.0, # 2 tabs * (24/6 = 4) = 8
                    "dose": 1,
                    # Current parser returns frequency=1, period=6, period_unit='hour' for 'q6h'.
                    # It does NOT autoconvert this to frequency=4 per day in the 'frequency' field itself.
                    # The max_dose calculation uses the derived value (24/6), but the raw frequency field remains 1.
                    "frequency": 1, 
                    "dose_unit": "tablet",
                    "strength_unit": "mg",
                    "strength": 5
                 }
            },
            {
                "input": "1 cap inhale daily",
                "expected": {
                    "sig_readable": "inhale 1 capsule into the lungs daily",
                    "max_dose_per_day": 1.0,
                    "dose": 1,
                    "frequency": 1,
                    "dose_unit": "capsule",
                    "strength_unit": None,
                    "strength": None
                }
            },
             {
                "input": "take 1 tablet by mouth at bedtime",
                "expected": {
                    "sig_readable": "take 1 tablet by mouth at bedtime",
                    "max_dose_per_day": 1.0,
                    "dose": 1,
                    "frequency": 1,
                    "dose_unit": "tablet",
                    "strength_unit": None,
                    "strength": None
                }
            },
            {
                "input": "take 1 tablet 12.5mg by mouth in the morning and in the evening with meal",
                "expected": {
                    "sig_readable": "take 1 tablet in the morning and 1 tablet in the evening by mouth",
                    "max_dose_per_day": 2.0,
                    "dose": 1,
                    "frequency": 2,
                    "dose_unit": "tablet",
                    "strength_unit": "mg",
                    "strength": 12.5
                }
            },
            {
                "input": "take 1 tablet by mouth every morning and take 1 every evening",
                "expected": {
                    "sig_readable": "take 1 tablet every morning and 1 tablet every evening by mouth",
                    "max_dose_per_day": 2.0,
                    "dose": 1,
                    "frequency": 2,
                    "dose_unit": "tablet",
                    "strength_unit": None,
                    "strength": None
                }
            }
        ]

        print("\n--- Running Deep Validation Checks ---")
        for case in test_cases:
            sig = case['input']
            expected = case['expected']
            result = self.parser.parse(sig)
            
            print(f"Testing: {sig}")
            
            for key, val in expected.items():
                parsed_val = result.get(key)
                
                # Loose comparison for floats
                if isinstance(val, float) and isinstance(parsed_val, (float, int)):
                     if abs(float(val) - float(parsed_val)) < 0.001:
                         continue
                
                # Normalize validation for None vs None
                if val is None and parsed_val is None:
                    continue
                    
                if parsed_val != val:
                    self.fail(
                        f"Mismatch for input: '{sig}'\n"
                        f"Field: '{key}'\n"
                        f"Expected: {val!r}\n"
                        f"Got:      {parsed_val!r}"
                    )

if __name__ == '__main__':
    unittest.main()
