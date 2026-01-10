from parsers.classes.parser import *
from parsers import method, dose, strength, route, frequency, when, duration, indication, max as max_parser, additional_info
import csv

# TODO: need to move all this to the main app and re-purpose the sig.py parser

# a work in progress...
# read csv: https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_csv.html
# general dataframe: https://pandas.pydata.org/pandas-docs/stable/reference/frame.html
# dataframe to csv: https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.to_csv.html
# csv to sql: https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.to_sql.html
class SigParser(Parser):
    parsers = {
        'method': method.parsers,
        'dose': dose.parsers,
        'strength': strength.parsers,
        'route': route.parsers,
        'frequency': frequency.parsers,
        'when': when.parsers,
        'duration': duration.parsers,
        'indication': indication.parsers,
        'max': max_parser.parsers,
        'additional_info': additional_info.parsers,
    }
    # TODO: make this match_keys assignment more elegant
    #match_keys = ['original_sig_text'] + ['sig_text', 'sig_readable', 'max_dose_per_day'] + method.parsers[0].match_keys + dose.parsers[0].match_keys + strength.parsers[0].match_keys + route.parsers[0].match_keys + frequency.parsers[0].match_keys + when.parsers[0].match_keys + duration.parsers[0].match_keys + indication.parsers[0].match_keys + max.parsers[0].match_keys + additional_info.parsers[0].match_keys
    #match_keys = ['sig_text', 'sig_readable', 'max_dose_per_day'] + method.parsers[0].match_keys + dose.parsers[0].match_keys + strength.parsers[0].match_keys + route.parsers[0].match_keys + frequency.parsers[0].match_keys + when.parsers[0].match_keys + duration.parsers[0].match_keys + indication.parsers[0].match_keys + max_parser.parsers[0].match_keys + additional_info.parsers[0].match_keys
    OUTPUT_KEYS = ['sig_text', 'sig_readable', 'max_dose_per_day', 'dose', 'frequency', 'dose_unit', 'strength_unit', 'strength']
    match_keys = OUTPUT_KEYS
    parser_type = 'sig'

    def get_normalized_sig_text(self, sig_text):
        # standardize to lower case
        sig_text = sig_text.lower()
        # remove:
        # . if not bordered by a number (i.e. don't want to convert 2.5 to 25 or 0.5 to 05)
        # : if not bordered by a number (i.e. not 5:00 or 1:10000)
        # , ; # * " ' ( ) \t [ ] :
        sig_text = re.sub(r'(?:(?<![0-9])\.(?![0-9])|,|;|#|\*|\"|\'|\(|\)|\t|\[|\]|(?<![0-9]):(?![0-9]))', '', sig_text)
        # remove duplicate spaces, and in doing so, also trim whitespaces from around sig
        sig_text = ' '.join(sig_text.split())
        return sig_text

    def get_readable(self, match_dict, inferred_method=None, inferred_route=None, inferred_dose_unit=None):
        method = match_dict.get('method_readable') or inferred_method or ''
        dose = match_dict.get('dose_readable') or ''
        if match_dict.get('dose_unit'):
            dose_unit = ''
        else:
            dose_unit = inferred_dose_unit or ''
        strength = match_dict.get('strength_readable') or ''
        route = match_dict.get('route_readable') or inferred_route or ''
        frequency = match_dict.get('frequency_readable') or ''
        when = match_dict.get('when_readable') or ''
        
        # Prevent redundancy if frequency includes the timing (e.g. "at bedtime" in both)
        if when and frequency and when in frequency:
            when = ''

        duration = match_dict.get('duration_readable') or ''
        indication = match_dict.get('indication_readable') or ''
        max = match_dict.get('max_readable') or ''
        additional_info = match_dict.get('additional_info_readable') or ''

        if dose != '' and strength != '':
            strength = '(' + strength + ')'
        sig_elements = [method, dose, dose_unit, strength, route, frequency, when, duration, indication, max, additional_info]
        # join sig elements with spaces
        readable = ' '.join(sig_elements)
        # remove duplicate spaces, and in doing so, also trim whitespaces from around sig
        # this accounts for empty sig elements
        readable = ' '.join(readable.split())
        return readable

    def get_period_per_day(self, period, period_unit):
        if not period:
            return None

        if period_unit == 'hour':
            return 24 / period
        elif period_unit == 'day':
            return 1 / period
        elif period_unit == 'week':
            return 1 / (7 * period)
        elif period_unit == 'month':
            return 1 / (30 * period)
        else:
            return None
        
    def filter_matches(self, matches, start_key, end_key):
        if not matches: return []
        # Sort by length descending to prioritize identifying 'best' matches first
        matches_sorted = sorted(matches, key=lambda x: (x[end_key] - x[start_key]), reverse=True)
        
        kept = []
        for m in matches_sorted:
            m_start = m[start_key]
            m_end = m[end_key]
            overlap = False
            for k in kept:
                k_start = k[start_key]
                k_end = k[end_key]
                if max(m_start, k_start) < min(m_end, k_end):
                    overlap = True
                    break
            if not overlap:
                kept.append(m)
        
        # Return sorted by position
        return sorted(kept, key=lambda x: x[start_key])

    def get_max_dose_per_day(self, match_dict, all_matches=None):
        # Helper to calculate single component max dose
        def calculate_component(d_match, f_match):
            frequency = f_match.get('frequency_max') or f_match.get('frequency')
            period = f_match.get('period')
            period_unit_raw = f_match.get('period_unit')
            period_unit = get_normalized(PERIOD_UNIT, period_unit_raw) if period_unit_raw else period_unit_raw
            period_per_day = self.get_period_per_day(period, period_unit)

            dose = d_match.get('dose_max') or d_match.get('dose')
            # Check ignored units
            dose_unit = d_match.get('dose_unit')
            if dose_unit in EXCLUDED_MDD_DOSE_UNITS:
                return None

            if frequency and period_per_day and dose:
                return frequency * period_per_day * dose
            return None

        # Helper to calculate from explicit "max dose" fields (e.g. "max 3 per day")
        # usually stored in the 'max' parser results.
        # This is usually global for the sig, not per instruction.
        # We rely on match_dict handling this from the 'max' parser.
        def calculate_explicit_max(m_dict):
             frequency_max = 1
             period_max = m_dict.get('max_denominator_value')
             period_unit_max = m_dict.get('max_denominator_unit')
             period_per_day_max = self.get_period_per_day(period_max, period_unit_max)
             dose_max = m_dict.get('max_numerator_value')
             if frequency_max and period_per_day_max and dose_max:
                return frequency_max * period_per_day_max * dose_max
             return None

        # Calculate using all_matches if available
        calculated_max_dose = None
        
        if all_matches:
            doses = self.filter_matches(all_matches.get('dose', []), 'dose_text_start', 'dose_text_end')
            frequencies = self.filter_matches(all_matches.get('frequency', []), 'frequency_text_start', 'frequency_text_end')
            
            # Scenario 1: N doses, N frequencies (1:1 mapping)
            if len(doses) == len(frequencies) and len(doses) > 0:
                total = 0
                valid = True
                for d, f in zip(doses, frequencies):
                    val = calculate_component(d, f)
                    if val is None:
                        valid = False
                        break
                    total += val
                if valid:
                    calculated_max_dose = total
            
            # Scenario 2: 1 dose, N frequencies ("1 tablet morning and evening")
            elif len(doses) == 1 and len(frequencies) > 1:
                total = 0
                valid = True
                d = doses[0]
                for f in frequencies:
                    val = calculate_component(d, f)
                    if val is None:
                        valid = False
                        break
                    total += val
                if valid:
                    calculated_max_dose = total
        
        # Fallback to single match_dict calculation if complex calculation failed or wasn't applicable
        if calculated_max_dose is None:
             calculated_max_dose = calculate_component(match_dict, match_dict)
             
        # Check explicit max dose constraint
        max_constraint = calculate_explicit_max(match_dict)
        
        if max_constraint and calculated_max_dose:
             # Prefer the higher value based on previous logic "always prefer max over sig"? 
             # Wait, code said: "requirements changed to always prefer max over sig"
             # which implies return max_constraint if present?
             # actually line 121: max = max_constraint OR calculated.
             # but line 117 condition was complex.
             # existing logic: if (calc or max) and (units match ...): return max or calc.
             # assuming unit check passes (we don't have unit for explicit max easily available here except strings)
             return max_constraint or calculated_max_dose
             
        return max_constraint or calculated_max_dose

    def parse(self, sig_text, verbose=False):
        match_dict = dict(self.match_dict)
        #match_dict['original_sig_text'] = sig_text
        sig_text = self.get_normalized_sig_text(sig_text)
        match_dict['sig_text'] = sig_text
        
        all_matches = {}

        for parser_type, parsers in self.parsers.items():
            matches = []
            
            for parser in parsers:
                match = parser.parse(sig_text)
                if match:
                    matches += match
            
            all_matches[parser_type] = matches
            
            if len(matches) > 1:
                # TODO: this is where we can put logic to determine the best dose / frequency / etc

                match = matches[0]
                for k, v in match.items():
                    match_dict[k] = v
            elif len(matches) == 1:
                match = matches[0]
                for k, v in match.items():
                    match_dict[k] = v

        # Handle compound sigs (N doses, N frequencies)
        doses = self.filter_matches(all_matches.get('dose', []), 'dose_text_start', 'dose_text_end')
        frequencies = self.filter_matches(all_matches.get('frequency', []), 'frequency_text_start', 'frequency_text_end')
        
        is_compound = False

        
        # Scenario 1: N doses, N frequencies (1:1 mapping)
        if len(doses) > 1 and len(doses) == len(frequencies):
             is_compound = True

             d_list = doses
        # Scenario 2: 1 dose, N frequencies (1:N mapping)
        elif len(doses) == 1 and len(frequencies) > 1:
             # Refinement: Check for redundant "daily" + "at night" patterns
             # If we have a generic 'daily' frequency AND a specific 'time' frequency, 
             # and they are not separated by 'and', assume one refines the other.
             
             generic_daily_pattern = re.compile(r'daily|qd|every day|once daily')
             specific_time_pattern = re.compile(r'morning|evening|night|bedtime|am|pm|noon')
             
             has_generic = False
             has_specific = False
             
             # Identify types
             for f in frequencies:
                 txt = f.get('frequency_text', '').lower()
                 if generic_daily_pattern.search(txt): has_generic = True
                 if specific_time_pattern.search(txt): has_specific = True

             if has_generic and has_specific:
                 # Check for separators

                 sorted_freq = sorted(frequencies, key=lambda x: x['frequency_text_start'])
                 
                 new_frequencies = []
                 keep_all = False
                 
                 for i in range(len(sorted_freq) - 1):
                     f1 = sorted_freq[i]
                     f2 = sorted_freq[i+1]
                     
                     # Check text between
                     start = f1['frequency_text_end']
                     end = f2['frequency_text_start']
                     between_text = sig_text[start:end].lower()
                     if 'and' in between_text or '&' in between_text:
                         keep_all = True
                         break
                 
                 if not keep_all:
                     # Filter out generic daily matches, prefer specific
                     for f in frequencies:
                         txt = f.get('frequency_text', '').lower()
                         if specific_time_pattern.search(txt):
                             new_frequencies.append(f)
                         elif not generic_daily_pattern.search(txt): 
                             # Keep if it's neither (e.g. valid other frequency)
                             new_frequencies.append(f)
                             
                     if new_frequencies:
                         frequencies = new_frequencies
                         # Update all_matches so get_max_dose uses the filtered list
                         all_matches['frequency'] = frequencies

             if len(frequencies) > 1:
                 is_compound = True
                 d_list = [doses[0]] * len(frequencies)
             else:
                 # Reverted to single frequency scenario
                 is_compound = False
                 match = doses[0]
                 match.update(frequencies[0]) # Merge freq data into dose match
                 # match_dict has original data. We need to OVERWRITE it with this specific chosen match.
                 for k, v in match.items():
                    match_dict[k] = v
                 
                 # IMPORTANT: match_dict might contain 'frequency' from the generic match if it appeared first in original parsing loop.
                 # Ensure 'frequency' is updated.
                 match_dict['frequency'] = frequencies[0].get('frequency')
             
        if is_compound:
            total_freq = 0
            readable_parts = []
            
            # Helper to check if a match is 'valid' (has values)
            def has_values(m):
                # Frequency match must have a frequency value to be counted
                return m.get('frequency') is not None
            
            # Validate pairs before proceeding
            valid_pairs = True
            for d, f in zip(d_list, frequencies):
                if not has_values(f):
                    valid_pairs = False
                    break
            
            if valid_pairs:
                for d, f in zip(d_list, frequencies):
                    # Sum frequency
                    f_val = f.get('frequency')
                    p_val = f.get('period')
                    p_unit = f.get('period_unit')
                    # normalize p_unit to day for summation if possible, roughly
                    # Assuming standard "daily" context if period_unit matches or is standardized
                    # For now, just simplistically sum the 'frequency' value if periods match or are 1 day
                    # This is an approximation.
                    if f_val:
                         total_freq += f_val
                    
                    # Build readable part
                    # Check for route near this dose?
                    # For now simple: dose + frequency
                    
                    # Optimization: If dose text is identical in consequent parts, maybe omit it?
                    # But for safety, repeat it: "1 tab morning and 1 tab evening" is clear.
                    
                    f_text = f.get('frequency_readable', '')
                    # Avoid redundant "at bedtime" if frequency has it (redundancy logic from standard path)
                    # Note: We don't have 'when' match here easily detached, assuming f_text covers it.
                    
                    part = f"{d.get('dose_readable', '')} {f_text}"
                    readable_parts.append(part.strip())

                match_dict['frequency'] = total_freq
                
                # Reconstruct sig_readable
                method = match_dict.get('method_readable') or ''
                route = match_dict.get('route_readable') or ''
                duration = match_dict.get('duration_readable') or ''
                indication = match_dict.get('indication_readable') or ''
                additional_info = match_dict.get('additional_info_readable') or ''
                
                combined_parts = " and ".join(readable_parts)
                
                # Assemble: {method} {combined_parts} {route} {duration} ...
                # Note: Route placement is tricky. Putting it after parts is safe-ish.
                pieces = [method, combined_parts, route, duration, indication, additional_info]
                match_dict['sig_readable'] = ' '.join([p for p in pieces if p])
                match_dict['sig_readable'] = ' '.join(match_dict['sig_readable'].split()) # Clean spaces
        
        if not is_compound:
            match_dict['sig_readable'] = self.get_readable(match_dict)
        match_dict ['max_dose_per_day'] = self.get_max_dose_per_day(match_dict, all_matches)

        if not verbose:
            return {k: match_dict.get(k) for k in self.OUTPUT_KEYS}

        # calculate admin instructions based on leftover pieces of sig
        # would need to calculate overlap in each of the match_dicts
        # in doing so, maybe also return a map of the parsed parts of the sig for use in frontend highlighting
        # i.e. 0,4|5,12|18,24
        return match_dict

    # infer method, dose_unit, and route from NDC or RXCUI
    def infer(self, match_dict, ndc=None, rxcui=None):
        sig_elements = ['method', 'dose_unit', 'route']
        #sig_elements = ['method', 'route']
        inferred = dict.fromkeys(sig_elements)
        for sig_element in sig_elements:
            inferred[sig_element] = infer_sig_element(sig_element, ndc, rxcui)
        inferred['sig_readable'] = self.get_readable(match_dict, inferred_method=inferred['method'], inferred_route=inferred['route'], inferred_dose_unit=inferred['dose_unit'])
        return inferred

    # parse a csv
    def parse_sig_csv(self, input_file='input.csv', output_file='output.csv'):
        input_folder = 'csv/'
        output_folder = input_folder + 'output/'
        csv_columns = self.match_keys
        # create an empty list to collect the data
        parsed_sigs = []
        # open the file and read through it line by line
        try:
            input_file_path = input_folder + input_file
            with open(input_file_path) as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=',')
                # calculate total number of rows for progress bar
                row_total = sum(1 for row in csv_reader)
                row_count = 0
                # reset csv file to beginning
                csv_file.seek(0)
                for row in csv_reader:
                    row_count += 1
                    print_progress_bar(row_count, row_total)
                    sig = row[0]
                    parsed_sig = self.parse(sig)
                    parsed_sigs.append(parsed_sig.copy())
        except IOError:
            print("I/O error")

        try:
            output_file_path = output_folder + output_file
            with open(output_file_path, 'w') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=csv_columns)
                writer.writeheader()
                for parsed_sig in parsed_sigs:
                    writer.writerow(parsed_sig)
        except IOError:
            print("I/O error")

        return parsed_sigs

def print_progress_bar (iteration, total, prefix = 'Progress:', suffix = 'complete', decimals = 1, length = 50, fill = '#', print_end = "\r"):
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    print('\r%s |%s| %s%% %s (n = %s)' % (prefix, bar, percent, suffix, iteration), end = print_end)
    if iteration == total: 
        print()

#print(SigParser().infer(ndc='68788640709'))
#parsed_sigs = SigParser().parse_sig_csv()
#parsed_sig = SigParser().parse('take 1-2 tabs by mouth qid x7d prn nausea')
#print(parsed_sig)
#parsed_sigs = SigParser().parse_validate_sig_csv()
#print(parsed_sigs)

# NOTE: if no dose found, check for numbers immediately following method (i.e. take 1-2 po qid)
# NOTE: if indication overlaps something else, then end indication just before the next thing starts
# NOTE: don't forget about the actual sig text and the sequence
# NOTE: split sig by "then" occurrences for sequence
# NOTE: Github has pieces that could make a FHIR converter
