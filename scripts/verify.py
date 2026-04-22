import json
import re
import sys
import forensick   # ← forensick integration

"""
Verification script for requirements and test cases.

Rules:
1. Required fields exist (requirement_id, description, source)
2. Requirement ID format: REQ-[CATEGORY]-[3 digits][letter], e.g., REQ-HAZ-001A
3. Each requirement must have at least one test case
4. No vague phrases like "all hazards" in description
5. Parent-child ID consistency (child must start with parent ID)
"""

with open("Input CFR File/requirements.json") as f:
    requirements = json.load(f)

with open("Input CFR File/test_cases.json") as f:
    test_cases = json.load(f)

test_ids = {t["requirement_id"] for t in test_cases}
failures = []

for r in requirements:
    rid = r.get("requirement_id", "")

    # Rule 1: Required fields
    # Integration Point 2 — REQUIREMENT_MISSING
    for field in ["requirement_id", "description", "source"]:
        if field not in r:
            msg = f"Missing field '{field}' in requirement: {r}"
            failures.append(msg)
            forensick.log_requirement_missing(
                context=rid or str(r),
                missing_field=field,
                raw_entry=r
            )

    # Rule 2: ID format
    # Integration Point 4 — ID_FORMAT_VIOLATION
    if rid and not re.match(r"REQ-[A-Z]+-\d{3}[A-Z]$", rid):
        msg = f"Invalid requirement_id format: {rid}"
        failures.append(msg)
        forensick.log_id_format_violation(
            requirement_id=rid,
            expected_pattern=r"REQ-[A-Z]+-\d{3}[A-Z]"
        )

    # Rule 3: Must have at least one test case
    # Integration Point 3 — TEST_COVERAGE_GAP
    if rid and rid not in test_ids:
        msg = f"No test case for requirement: {rid}"
        failures.append(msg)
        forensick.log_test_coverage_gap(
            requirement_id=rid,
            description=r.get("description", "(no description)")
        )

    # Rule 4: No vague phrase
    if "description" in r and "all hazards" in r["description"].lower():
        failures.append(f"Vague description in requirement: {rid}")

    # Rule 5: Parent-child consistency
    if "parent" in r and rid and not rid.startswith(r["parent"]):
        failures.append(f"Parent-child ID mismatch: {rid} (parent {r['parent']})")

# Integration Point 5 — CI_BUILD_RESULT (always fires, pass or fail)
passed = len(failures) == 0
forensick.log_ci_build_result(
    passed=passed,
    failure_count=len(failures),
    failures=failures,
    stage="verify"
)
forensick.print_summary()

if failures:
    print("Verification FAILED:")
    for f in failures:
        print("-", f)
    sys.exit(1)
else:
    print("Verification passed: all requirements meet structural rules.")
    sys.exit(0)
