# 🧠 Advanced-Sig-Parser

> A modern, lightweight medication sig parser.

## Getting started

Input free text medication sigs, output discrete sig elements.
* Extract method, dose, strength, frequency, route, duration, indication, and additional info
* Calculate maximum daily dose (preferring explicit MDD in sig over maximum possible dose per day)

Medication "sigs" are the instructions you see on your prescription label - i.e. "take 1-2 tablets by mouth daily". 

### Installation

Clone repo.

```
git clone https://github.com/coderxio/Advanced-Sig-Parser.git
```

Create virtual environment within the `Advanced-Sig-Parser/` directory.

```
cd Advanced-Sig-Parser
python3 -m venv venv
```

### Running Advanced-Sig-Parser

Activate virtual environment.

```
source venv/bin/activate
```

### Parse single sig

Individual sig usage: 

```
python advanced_sig_parser.py take 1 tab by mouth daily
```

* Replace `take 1 tab by mouth daily` with your own sig.

Example:

```
$ python advanced_sig_parser.py take 1-2 tab po qid x7d prn pain
{
    "sig_text": "take 1-2 tab po qid x7d prn pain",
    "sig_readable": "take 1-2 tablets by mouth 4 times a day for 7 days as needed for pain",
    "max_dose_per_day": 8.0,
    "dose": 1,
    "frequency": 4,
    "dose_unit": "tablet",
    "strength_unit": null,
    "strength": null
}
```

In this example, "take 1-2 tab po qid x7d prn pain" is interepreted by Advanced-Sig-Parser as "take 1-2 tablets by mouth 4 times a day for 7 days as needed for pain".

* You can see each individual component that comprises that sig, as well as the start and end characters within the original sig.

### Parse CSV of sigs

Bulk sig usage:  

```
python advanced_sig_parser.py --b input.csv output.csv
```

* Use the `--b` flag for bulk parsing of sigs in CSV files.
* Replace input.csv with the name of your input file (needs to be in the /csv directory).
* Replace output.csv with the desired name of your output file (will be in the /csv/output directory).
* Separate input and output file names with a space.

Example:

```
$ python advanced_sig_parser.py --b input.csv output.csv
Progress: |██████████████████████████████████████████████████| 100.0% complete (n = 250)
Output written to output.csv.
```

![image](https://github.com/user-attachments/assets/fc5e5e21-0f80-4688-9e55-f631e1caf3cc)

## Parsed sig components

### Text

`sig_text`

A string containing the modified sig_text from the request, converted to lower case, extraneous characters removed, and duplicate spaces converted to single spaces.

`sig_readable`

A human-readable version of the parsed sig for quick and easy validation.

### Method

`method`

How the medication is administered (i.e. take, inject, inhale).

### Dose

`dose`

`dose_max`

`dose_unit`

How much medication patient is instructed to take based on dosage (i.e. 2 tablets, 30 units, 1-2 puffs).

Numbers represented as words in the sig will be converted to integers (i.e. “one” will be converted to 1).

### Strength

`strength`

`strength_max`

`strength_unit`

How much medication the patient is instructed to take based on strength (i.e. 500 mg, 15 mL, 17 g).

NOTE: Advanced-Sig-Parser intentionally does not parse multiple ingredient strengths (i.e. if 5/325 mg is in a sig, it will return null for strength).

### Route

`route`

Route of administration of the medication (i.e. by mouth, via inhalation, in left eye).

### Frequency

`frequency`

`frequency_max`

`period`

`period_max`

`period_unit`

`time_duration`

`time_duration_unit`

`day_of_week`

`time_of_day`

`when`

`offset`

`bounds`

`count`

`frequency_readable`

How often medication should be administered (i.e. every 4-6 hours, three times daily, once daily in the morning with meal).

Due to the complexity and variety of medication instructions, these elements are based off of an existing standard - FHIR Timing.

For convenience, a frequency_readable is generated to represent a human-readable representation of the sig frequency.

### Duration

`duration`

`duration_max`

`duration_unit`

How long the patient is instructed to take the medication (i.e. for 7 days, for 7-10 days, for 28 days).

NOTE: this is different from days’ supply, which represents how long a given supply of medication should last.

### Indication / PRN

`as_needed`

`indication`

Whether the medication should be taken “as needed” (i.e. PRN), and the specific reason the patient is taking the medication (i.e. for pain, for wheezing and shortness of breath, for insomnia).

NOTE: indication may be populated even if as_needed is false. There are chronic indications represented in sigs as well (i.e. for cholesterol, for high blood pressure, for diabetes).

### Maximum daily dose

`max_dose_per_day`

`max_numerator_value`

`max_numerator_unit`

`max_denominator_value`

`max_deniminator_unit`

Max numerator and denominator elements are extracted from text explicitly stated in the sig (i.e. if a prescriber writes mdd or nte). 

Max dose per day looks to both the maximum dose possible per the sig instructions and any explicit mdd or or nte directions, preferring the mdd or nte directions if present.

Examples:

* take 1 tab every 6 hours mdd 3/d -> max_dose_per_day should be 3, max numerator/denominator should have values
* take 1 tab every 6 hours -> max_dose_per_day should be 4, max numerator/denominator should not have values

### Additional info

`additional_info`

Extra instructions such as "take with food" - things that might be on auxillary labels on a prescription bottle.

## Architecture

The **Advanced-Sig-Parser** follows a robust, modular pipeline designed to break down complex medical instructions into structured data.

### 1. Normalization
The raw input string is pre-processed to standardize the text. This involves:
- converting to lower case
- removing extraneous characters
- normalizing number representations (e.g., "one" -> "1", "1/2" -> "0.5")

### 2. Tokenization & Matching
The normalized text is passed through a suite of strictly typed parsers located in the `parsers/` directory. Each parser focuses on a specific component of the sig:
- `parsers/dose.py`: Extracts dosage amounts (e.g., "1-2 tablets").
- `parsers/frequency.py`: Identifies timing patterns (e.g., "twice daily", "q4h", "every morning").
- `parsers/route.py`: Detects administration routes (e.g., "by mouth", "topically").
- `parsers/strength.py`, `parsers/duration.py`, etc. handle their respective domains.

These parsers operate independently to identify all potential matches within the text.

### 3. Inference & Logic
Once components are identified, the system applies logical inference to fill gaps:
- **Route Inference**: If a dosage form like "tablet" is found but no route is specified, "by mouth" is inferred.
- **Compound Sig Handling**: The parser detects complex instructions (e.g., "take 1 tablet in the morning and 2 at night") and intelligently merges them into a cohesive structured output.

### 4. Output Generation
The final step assembles the extracted and inferred data into:
- A structured JSON-like dictionary containing all individual fields (`dose`, `frequency`, `max_dose_per_day`, etc.).
- A `sig_readable` string that reconstructs the instruction into a clear, standardized human-readable format.

