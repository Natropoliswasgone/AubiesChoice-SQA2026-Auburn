## Project Files Overview

This repository contains all scripts and outputs required for Tasks 1–4 of the CFR V&V project.

### Input File

* `CFR-117.130.md` – Original CFR section used as input for requirement extraction

---

### Scripts

* `generate_requirements_v2.py` – Parses the CFR markdown file into structured requirements (`requirements.json`)
* `generate_test_cases.py` – Generates test cases for selected atomic rules (`test_cases.json`)
* `verify.py` – Performs verification checks to ensure requirements are correctly structured
* `validate.py` – Validates that test cases correctly map to requirements
* `forensick.py` – Logs and detects issues such as missing requirements, skipped rules, or failures in validation

---

### Output Files

* `requirements.json` – Extracted and structured requirements from the CFR document
* `expected_structure.json` – Mapping of parent requirements to their child components
* `test_cases.json` – Generated test cases for selected atomic rules
* `forensick_log.jsonl` – Log file capturing validation and verification issues

---

### CI/CD Pipeline

* `vv_pipeline.yml` – GitHub Actions workflow that automates verification, validation, and forensick checks on each push

---

## Team Members

* Cindy Jiang
* Nathan Currier
* Pearson Keyton
* Reed Parish

