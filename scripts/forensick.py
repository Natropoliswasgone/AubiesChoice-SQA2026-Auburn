"""
forensick.py — Forensic Audit Logger for CFR V&V Pipeline
==========================================================
Creates a tamper-evident, append-only JSONL audit trail with five
integration points used across generate_requirements_v2.py,
generate_test_cases.py, verify.py, and the CI workflow.

Integration Points
------------------
  1. REQUIREMENT_SKIPPED   – emitted when a parsed requirement is not
                             included in the final output (--select filter)
  2. REQUIREMENT_MISSING   – emitted when a required field or ID is absent
  3. TEST_COVERAGE_GAP     – emitted when a requirement has no test case
  4. ID_FORMAT_VIOLATION   – emitted when a requirement_id fails the regex
  5. CI_BUILD_RESULT       – emitted at pipeline exit with pass/fail + summary

Each event is a JSON object written to forensick_log.jsonl (one per line).
A human-readable summary is also printed to stdout for CI logs.
"""

import json
import hashlib
import os
import sys
import socket
from datetime import datetime, timezone
from pathlib import Path

LOG_FILE = Path("forensick_log.jsonl")

# ── Event type constants (the five integration points) ────────────────────────
REQUIREMENT_SKIPPED  = "REQUIREMENT_SKIPPED"
REQUIREMENT_MISSING  = "REQUIREMENT_MISSING"
TEST_COVERAGE_GAP    = "TEST_COVERAGE_GAP"
ID_FORMAT_VIOLATION  = "ID_FORMAT_VIOLATION"
CI_BUILD_RESULT      = "CI_BUILD_RESULT"


def _prev_hash() -> str:
    """Return SHA-256 of the last line in the log for chain integrity."""
    if not LOG_FILE.exists():
        return "0" * 64   # genesis block
    lines = LOG_FILE.read_text(encoding="utf-8").strip().splitlines()
    if not lines:
        return "0" * 64
    return hashlib.sha256(lines[-1].encode()).hexdigest()


def _write(event_type: str, payload: dict) -> dict:
    """Append one forensic event to the JSONL log and return the record."""
    record = {
        "timestamp":  datetime.now(timezone.utc).isoformat(),
        "event":      event_type,
        "host":       socket.gethostname(),
        "pid":        os.getpid(),
        "prev_hash":  _prev_hash(),
        **payload,
    }
    # Self-hash: sign the record (excluding hash field itself)
    record["hash"] = hashlib.sha256(
        json.dumps({k: v for k, v in record.items() if k != "hash"},
                   sort_keys=True).encode()
    ).hexdigest()

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    return record


def _fmt(label: str, msg: str) -> str:
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    return f"[forensick {ts}] {label:22s} {msg}"


# ── Integration Point 1: REQUIREMENT_SKIPPED ─────────────────────────────────
def log_requirement_skipped(requirement_id: str, description: str, reason: str = "--select filter"):
    """
    Called in generate_requirements_v2.py when a parsed requirement is
    intentionally excluded from the output by the --select argument.

    Provides an audit trail showing the requirement was seen but deliberately
    omitted — distinguishes intentional omission from parse failure.
    """
    rec = _write(REQUIREMENT_SKIPPED, {
        "requirement_id": requirement_id,
        "description":    description,
        "reason":         reason,
    })
    print(_fmt("SKIPPED", f"{requirement_id} | {reason}"))
    return rec


# ── Integration Point 2: REQUIREMENT_MISSING ─────────────────────────────────
def log_requirement_missing(context: str, missing_field: str, raw_entry: dict):
    """
    Called in verify.py (Rule 1) when a required field is absent from a
    requirement entry. Records the full raw entry so the analyst can
    reconstruct what was present without re-running the pipeline.
    """
    rec = _write(REQUIREMENT_MISSING, {
        "context":       context,
        "missing_field": missing_field,
        "raw_entry":     raw_entry,
    })
    print(_fmt("MISSING FIELD", f"'{missing_field}' absent in {context}"))
    return rec


# ── Integration Point 3: TEST_COVERAGE_GAP ───────────────────────────────────
def log_test_coverage_gap(requirement_id: str, description: str):
    """
    Called in verify.py (Rule 3) when a requirement has no corresponding
    test case. This is the most common compliance gap in CFR V&V pipelines;
    forensick captures every instance with enough context for a coverage report.
    """
    rec = _write(TEST_COVERAGE_GAP, {
        "requirement_id": requirement_id,
        "description":    description,
        "remedy":         "Add a test case referencing this requirement_id to test_cases.json",
    })
    print(_fmt("COVERAGE GAP", f"{requirement_id} has no test case"))
    return rec


# ── Integration Point 4: ID_FORMAT_VIOLATION ─────────────────────────────────
def log_id_format_violation(requirement_id: str, expected_pattern: str):
    """
    Called in verify.py (Rule 2) when a requirement_id does not match the
    expected regex. Logs both the offending ID and the pattern so the
    generate script can be corrected without guesswork.
    """
    rec = _write(ID_FORMAT_VIOLATION, {
        "requirement_id":   requirement_id,
        "expected_pattern": expected_pattern,
        "tip": "Re-run generate_requirements_v2.py with a pure-letter --category (e.g. HAZ)",
    })
    print(_fmt("ID VIOLATION", f"{requirement_id!r} does not match {expected_pattern}"))
    return rec


# ── Integration Point 5: CI_BUILD_RESULT ─────────────────────────────────────
def log_ci_build_result(passed: bool, failure_count: int, failures: list[str],
                        stage: str = "verify"):
    """
    Called at the end of verify.py (sys.exit) to record the overall pipeline
    outcome. The CI workflow uploads forensick_log.jsonl as an artifact so
    every build has a permanent, auditable record.
    """
    status = "PASS" if passed else "FAIL"
    rec = _write(CI_BUILD_RESULT, {
        "stage":         stage,
        "status":        status,
        "failure_count": failure_count,
        "failures":      failures,
        "log_file":      str(LOG_FILE.resolve()),
    })
    banner = "✅ PASS" if passed else f"❌ FAIL  ({failure_count} violation(s))"
    print(_fmt("CI BUILD", f"[{stage.upper()}] {banner}"))
    return rec


# ── Report helper (print log summary to stdout) ───────────────────────────────
def print_summary():
    """Print a grouped summary of all events in the current log."""
    if not LOG_FILE.exists():
        print("[forensick] No log file found.")
        return

    from collections import Counter
    events: list[dict] = []
    for line in LOG_FILE.read_text().splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            pass

    counts = Counter(e["event"] for e in events)
    print("\n── forensick audit summary ──────────────────────────────")
    for etype, n in sorted(counts.items()):
        print(f"  {etype:30s} {n:>4d} event(s)")
    print(f"  {'TOTAL':30s} {len(events):>4d}")
    print(f"  log → {LOG_FILE.resolve()}")
    print("─────────────────────────────────────────────────────────\n")


if __name__ == "__main__":
    print_summary()
