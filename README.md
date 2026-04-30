# CFR V&V Project
**21 CFR Atomic Rules | SQA 2026 – Auburn University**

## Project Overview

This project implements a Verification & Validation (V&V) pipeline for regulatory requirements extracted from the Code of Federal Regulations (CFR). We parse **CFR § 117.130**, extract structured atomic requirements, generate test cases, and validate correctness using automated scripts and GitHub Actions.

The goal is to ensure that regulatory text can be systematically decomposed, tested, and audited for correctness and completeness in a reproducible way.

---

## Repository Structure

```
.
├── .github/
│   └── vv_pipeline.yml           # GitHub Actions CI/CD pipeline
├── Input CFR File/
│   ├── CFR-117.130.md            # Original CFR section (input)
│   ├── expected_structure.json
│   ├── output.json
│   ├── requirements.json
│   └── test_cases.json
├── Pictures/                     # Screenshots and supporting images
├── scripts/
│   ├── generate_requirements_v2.py
│   ├── generate_test_cases.py
│   ├── verify.py
│   ├── validate.py
│   └── forensick.py
├── venv/                         # Python virtual environment (not committed)
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

## Reproducing Locally

### Prerequisites

- Python 3.8 or higher
- `pip` (comes with Python)
- Git

---

### macOS Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/AubiesChoice/AubiesChoice-SQA2026-Auburn.git
   cd AubiesChoice-SQA2026-Auburn
   ```

2. **Create and activate a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install <package-name>
   ```
   > Check the imports at the top of each script in `scripts/` and install any third-party packages listed there.

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
   git clone https://github.com/AubiesChoice/AubiesChoice-SQA2026-Auburn.git
   cd AubiesChoice-SQA2026-Auburn
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
   pip install <package-name>
   ```
   > Check the imports at the top of each script in `scripts/` and install any third-party packages listed there.

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

## CI/CD Pipeline

`vv_pipeline.yml` is a GitHub Actions workflow that automatically runs verification, validation, and forensick checks on every push to the repository.

---

## Forensick Integration

Automated checks are implemented for:

- Missing requirements
- Skipped atomic rules
- Incomplete test cases
- CI build failures
- Invalid structure mappings

These checks run automatically via GitHub Actions on every push.

---

## LLM Testing (Individual Task)

Test cases were generated using:

- **Mistral**
- **Quantized Mistral**

Each model was evaluated based on:

- **Coverage** – Did it generate test cases for all requirements?
- **Correctness** – Does each test case match its requirement?
- **Completeness** – Are all required fields present?

---

## Team Members

- Cindy Jiang
- Nathan Currier
- Pearson Keyton
- Reed Parish
