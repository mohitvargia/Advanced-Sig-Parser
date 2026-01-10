# Advanced-Sig-Parser Project Analysis

## Overview
Advanced-Sig-Parser is a Python-based medication "sig" (instructions) parser. It takes free-text medication instructions (e.g., "take 1 tablet by mouth daily") and converts them into structured data elements (method, dose, route, frequency, etc.).

## Project Structure
The project is structured as a modular application:
- **Root**: Contains the entry point `advanced_sig_parser.py`, `README.md`, and data folders.
- **`parsers/`**: Contains the core logic.
  - **`sig.py`**: The main orchestrator traversing all specific parsers.
  - **Component Parsers**: Specialized modules for each sig component: `dose.py`, `frequency.py`, `method.py`, `route.py`, etc.
  - **`classes/parser.py`**: Defines the base `Parser` class which handles regex pattern matching and normalization.
  - **`services/`**: helper services and data.
    - `normalize.py`: Likely contains extensive regex constants and normalization dictionaries (40KB file).
    - `infer.py`: Logic to infer missing details using NDC/RxCUI codes.
    - CSV files: various mapping tables for normalizations.

## Logic Flow
1. **Input**: A raw string (sig).
2. **Normalization**: The sig string is cleaned (lowercase, punctuation removal).
3. **Parsing**: 
   - The `SigParser` iterates through a list of component parsers.
   - Each component parser (e.g., `DoseParser`, `FrequencyParser`) defines a regex `pattern`.
   - `re.finditer` identifies matches.
   - Matches are "normalized" into structured dictionaries (e.g., converting "once" to `frequency=1`).
4. **Aggregation**: Matches are collected into a single result dictionary.
5. **Output**: A JSON object or CSV row.

## Key Observations
- **Regex-Heavy**: The project relies heavily on Regular Expressions for Natural Language Processing. This is efficient for structured inputs but can be brittle for highly irregular text.
- **Modular Design**: The `Parser` base class allows easy addition of new patterns.
- **Inference Capability**: It attempts to infer missing data (like route or method) if an NDC or RxCUI is provided, utilizing CSV mappings in `services/`.
- **Missing Tests**: There is no dedicated `tests/` directory, suggesting a lack of unit testing, which is critical for a parser project to ensure regression safety.
- **Dependencies**: No `requirements.txt` is present. It appears to rely mostly on the Python standard library (`re`, `json`, `csv`, `sys`), which makes it lightweight.

## Functional Analysis (Static)
- **`dose.py`**: Handles complex cases like ranges ("1-2 tabs") and unit normalization ("teaspoon" -> 5mL).
- **`frequency.py`**: Maps standard medical abbreviations (`qd`, `bid`, `tid`) and natural language ("every 4 hours") to FHIR-like timing structures. It handles gaps (e.g., "daily" vs "every day").
- **Entry Point**: `advanced_sig_parser.py` provides a CLI interface for single string parsing (`python advanced_sig_parser.py ...`) or bulk CSV processing (`--b`).

## Conclusion
The codebase is a focused, lightweight tool for parsing medical instructions. Its strength lies in its modularity and specific focus on medical terminology cleanup. However, it lacks testing infrastructure and formal dependency management.
