# CFR V&V Project

## Project Overview

This project implements a Verification & Validation (V&V) pipeline for regulatory requirements extracted from the Code of Federal Regulations (CFR). Specifically, it parses **CFR § 117.130**, extracts structured atomic requirements, generates test cases for those requirements, and runs automated verification and validation checks — all orchestrated through a CI/CD pipeline via GitHub Actions.

The goal is to ensure that regulatory text can be systematically decomposed, tested, and audited for correctness and completeness in a reproducible way.

---

## Project Structure

```
.
├── .github/                  # GitHub Actions workflow
├── Input CFR File/
│   ├── CFR-117.130.md         # Original CFR section (input)
│   ├── expected_structure.json
│   ├── output.json
│   ├── requirements.json
│   └── test_cases.json
├── Pictures/                 # Screenshots and supporting images
├── scripts/
│   ├── generate_requirements_v2.py
│   ├── generate_test_cases.py
│   ├── verify.py
│   ├── validate.py
│   └── forensick.py
├── venv/                     # Python virtual environment (not committed)
├── .gitignore
├── forensick_log.jsonl
├── GroupReport.pdf
└── README.md
```

---

## Output Files

| File | Description |
|---|---|
| `requirements.json` | Extracted and structured requirements from the CFR document |
| `expected_structure.json` | Mapping of parent requirements to their child components |
| `test_cases.json` | Generated test cases for selected atomic rules |
| `forensick_log.jsonl` | Log capturing validation and verification issues |

---

## Scripts

| Script | Description |
|---|---|
| `generate_requirements_v2.py` | Parses the CFR markdown file into structured requirements |
| `generate_test_cases.py` | Generates test cases for selected atomic rules |
| `verify.py` | Performs verification checks on requirement structure |
| `validate.py` | Validates that test cases correctly map to requirements |
| `forensick.py` | Detects and logs issues such as missing requirements or validation failures |

---

## CI/CD Pipeline

`vv_pipeline.yml` is a GitHub Actions workflow that automatically runs verification, validation, and forensick checks on every push to the repository.

---

## Reproducing Locally

### Prerequisites

- Python 3.8 or higher
- `pip` (comes with Python)
- Git

---

### macOS Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd <repo-folder>
   ```

2. **Create and activate a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the pipeline scripts in order**
   ```bash
   python3 scripts/generate_requirements_v2.py
   python3 scripts/generate_test_cases.py
   python3 scripts/verify.py
   python3 scripts/validate.py
   python3 scripts/forensick.py
   ```

5. **Deactivate the virtual environment when done**
   ```bash
   deactivate
   ```

---

### Windows Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd <repo-folder>
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```
   > If you get a permissions error, run PowerShell as Administrator and execute:
   > `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the pipeline scripts in order**
   ```bash
   python scripts\generate_requirements_v2.py
   python scripts\generate_test_cases.py
   python scripts\verify.py
   python scripts\validate.py
   python scripts\forensick.py
   ```

5. **Deactivate the virtual environment when done**
   ```bash
   deactivate
   ```

---

## Team Members

- Cindy Jiang
- Nathan Currier
- Pearson Keyton
- Reed Parish
