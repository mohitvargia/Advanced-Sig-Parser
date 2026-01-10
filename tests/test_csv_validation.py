import unittest
import csv
import os
import sys

# Add parent directory to path to allow importing parsers
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers.sig import SigParser

class TestCsvValidation(unittest.TestCase):
    def setUp(self):
        self.parser = SigParser()
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.input_path = os.path.join(self.base_dir, 'csv', 'input.csv')
        self.output_path = os.path.join(self.base_dir, 'csv', 'output', 'output.csv')

    def normalize_value(self, value):
        """Normalize values for comparison (strings vs numbers, None vs empty string)"""
        if value is None:
            return ""
        if isinstance(value, (int, float)):
            # Handle .0 float cases that might appear as integers in string
            if isinstance(value, float) and value.is_integer():
                return str(int(value))
            return str(value)
        return str(value).strip()

    def test_validate_csv_output(self):
        """Validate that parsing input.csv produces the expected results in output.csv"""
        
        if not os.path.exists(self.input_path):
            self.skipTest(f"Input file not found: {self.input_path}")
        if not os.path.exists(self.output_path):
            self.skipTest(f"Output file not found: {self.output_path}")

        # Read expected output
        expected_results = []
        with open(self.output_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                expected_results.append(row)

        # Read input and validate
        with open(self.input_path, 'r', encoding='utf-8') as f:
            # Assuming input csv is headerless or we treat first line as data if it looks like a sig
            # Based on inspection, it looks headerless. 
            # We use csv.reader to handle quoted strings properly
            reader = csv.reader(f)
            input_rows = list(reader)

        print(f"\nValidating {len(input_rows)} records...")

        # Ensure we have enough expected results
        self.assertGreaterEqual(len(expected_results), len(input_rows), 
            "Output file has fewer rows than input file")

        errors = []

        for i, row in enumerate(input_rows):
            if not row: continue # Skip empty lines
            
            sig_input = row[0]
            expected = expected_results[i]
            
            # Parse
            parsed = self.parser.parse(sig_input)
            
            # Compare fields
            # expected keys are from output.csv, which matches OUTPUT_KEYS
            # parsed keys are also OUTPUT_KEYS
            
            # Check for SIG TEXT mismatch first (sanity check alignment)
            # The input.csv text might be slightly different normalized in output (e.g. lowercase)
            # But the 'sig_text' in output should generally come from input.
            
            for key in expected.keys():
                parsed_val = self.normalize_value(parsed.get(key))
                expected_val = self.normalize_value(expected.get(key))
                
                # Loose comparison for floats (e.g. 2.0 vs 2)
                if parsed_val != expected_val:
                    # Try comparing as floats if possible
                    try:
                        p_float = float(parsed_val)
                        e_float = float(expected_val)
                        if abs(p_float - e_float) < 0.001:
                            continue
                    except ValueError:
                        pass
                    
                    errors.append(
                        f"Row {i+1} mismatch for '{key}':\n"
                        f"  Input: {sig_input}\n"
                        f"  Expected: {expected_val!r}\n"
                        f"  Got:      {parsed_val!r}"
                    )
        
        if errors:
            self.fail(f"Found {len(errors)} validation errors:\n" + "\n".join(errors[:10]) + 
                      (f"\n...and {len(errors)-10} more." if len(errors) > 10 else ""))

if __name__ == '__main__':
    unittest.main()
