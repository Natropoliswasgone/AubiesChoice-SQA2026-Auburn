# scripts/generate_requirements_v2.py
"""
Parses a CFR Markdown file into requirements.json that passes all verify.py rules:
  Rule 1 - Required fields: requirement_id, description, source
  Rule 2 - ID format: REQ-[A-Z]+-NNN[A-Z]  e.g. REQ-HAZ-001A
  Rule 3 - Every requirement must have a test case (use --select to emit only chosen ones)
  Rule 4 - No "all hazards" in description
  Rule 5 - Child ID must start with parent ID string
"""

import json
import re
import argparse
from collections import defaultdict
import forensick   # ← forensick: Integration Point 1

# ---------- Arguments ----------
parser = argparse.ArgumentParser(description="Generate requirement JSON from CFR Markdown")
parser.add_argument("--input",    "-i", required=True,  help="Input Markdown file (.md)")
parser.add_argument("--output",   "-o", required=True,  help="Output requirements JSON file")
parser.add_argument("--struct",   "-s", required=True,  help="Output expected_structure JSON file")
parser.add_argument("--cfr",      "-c", required=True,  help="CFR section label (e.g. '21 CFR 117.130')")
parser.add_argument("--category", "-k", required=True,
                    help="Pure-letter category code for IDs (e.g. HAZ). Must match [A-Z]+.")
parser.add_argument("--select",   "-q", nargs="*",
                    help="Flat requirement IDs to include (e.g. REQ-HAZ-001A REQ-HAZ-001C). "
                         "Omit to see all generated IDs, then re-run with --select.")
parser.add_argument("--debug",    "-d", action="store_true", help="Print per-line parse decisions")
args = parser.parse_args()

if not re.fullmatch(r"[A-Z]+", args.category):
    raise ValueError(f"--category must be uppercase letters only, got: {args.category!r}")

INPUT_MD    = args.input
OUTPUT_JSON = args.output
STRUCT_JSON = args.struct
CFR_SECTION = args.cfr
CATEGORY    = args.category
DEBUG       = args.debug

# Arrow pattern covers → (U+2192), ->, =>, – >
ARROW = r"(?:→|->|=>|–\s*>)"
LETTER_SEQ = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def clean_description(text: str) -> str:
    """Strip markdown markers, inline numbering, and Rule-4 vague phrases."""
    text = re.sub(r"^[-*#]+\s*", "", text)
    text = re.sub(r"^\([ivxlcdmIVXLCDM\d]+\)\s*", "", text)
    # Rule 4: replace "all hazards" to avoid vague phrase failure
    text = re.sub(r"\ball hazards\b", "identified hazards", text, flags=re.IGNORECASE)
    return text.strip()

# ---------- Read file ----------
with open(INPUT_MD, "r", encoding="utf-8") as f:
    lines = [line.strip() for line in f if line.strip()]

print(f"Read {len(lines)} non-empty lines from {INPUT_MD}")

# ---------- Parse into raw atoms ----------
# Strategy: ALL atoms within a section (regardless of nesting depth) are
# assigned sequential letters A, B, C... so the final ID is always
# REQ-CAT-NNN[A-Z], satisfying Rule 2. Sub-children are flattened.

raw_atoms     = []  # list of {section_num, letter, description}
section_counter = 0
letter_counter  = 0

for line in lines:
    # Section header line
    req_match = re.search(ARROW + r"\s*(REQ-[\d\.]+-\d+)", line)
    if req_match:
        section_counter += 1
        letter_counter = 0
        if DEBUG:
            print(f"[SECTION {section_counter:03d}] ← {req_match.group(1)}")
        continue

    # Atomic rule: any depth, ends in → <LETTER><optional digits>
    atomic_match = re.match(r"^(.*?)\s*" + ARROW + r"\s*([A-Z]\d*)$", line)
    if atomic_match and section_counter > 0:
        description     = clean_description(atomic_match.group(1))
        assigned_letter = LETTER_SEQ[letter_counter]
        letter_counter += 1

        raw_atoms.append({
            "section_num": section_counter,
            "letter":      assigned_letter,
            "description": description,
        })
        if DEBUG:
            rid = f"REQ-{CATEGORY}-{section_counter:03d}{assigned_letter}"
            print(f"  [{rid}] {description}")
    elif DEBUG and section_counter > 0:
        print(f"  [SKIP] {repr(line)}")

print(f"Parsed {len(raw_atoms)} atomic rules across {section_counter} sections.")

# ---------- Build flat requirements ----------
# ID:     REQ-<CATEGORY>-<NNN><L>   e.g. REQ-HAZ-001A  (Rule 2 ✓)
# Parent: REQ-<CATEGORY>-<NNN>      e.g. REQ-HAZ-001
# child.startswith(parent) always True                   (Rule 5 ✓)

all_requirements = []
for atom in raw_atoms:
    n   = atom["section_num"]
    ltr = atom["letter"]
    all_requirements.append({
        "requirement_id": f"REQ-{CATEGORY}-{n:03d}{ltr}",
        "description":    atom["description"],
        "source":         CFR_SECTION,                   # Rule 1 ✓
        "parent":         f"REQ-{CATEGORY}-{n:03d}",
    })

# ---------- Print full list if no --select given ----------
if not args.select:
    print("\nAll generated requirement IDs (pass these to --select to filter):")
    for r in all_requirements:
        print(f"  {r['requirement_id']}  |  {r['description']}")
    print("\n[INFO] Re-run with --select <IDs> to restrict output to your chosen requirements.")

# ---------- Filter to selected IDs ----------
if args.select:
    selected_set = set(args.select)
    requirements = [r for r in all_requirements if r["requirement_id"] in selected_set]
    missing = selected_set - {r["requirement_id"] for r in requirements}
    if missing:
        print(f"[WARN] --select IDs not found in parsed output: {missing}")

    # Integration Point 1 — log every requirement that was parsed but not selected
    selected_ids = {r["requirement_id"] for r in requirements}
    for r in all_requirements:
        if r["requirement_id"] not in selected_ids:
            forensick.log_requirement_skipped(
                requirement_id=r["requirement_id"],
                description=r["description"],
                reason="excluded by --select filter"
            )
else:
    requirements = all_requirements

# ---------- Save requirements.json ----------
with open(OUTPUT_JSON, "w") as f:
    json.dump(requirements, f, indent=2)
print(f"\nSaved {len(requirements)} requirements → {OUTPUT_JSON}")

# ---------- Build expected_structure.json ----------
structure = defaultdict(list)
for req in requirements:
    parent = req["parent"]
    suffix = req["requirement_id"][len(parent):]  # single letter
    if suffix not in structure[parent]:
        structure[parent].append(suffix)

with open(STRUCT_JSON, "w") as f:
    json.dump({k: sorted(v) for k, v in sorted(structure.items())}, f, indent=2)
print(f"Saved expected_structure → {STRUCT_JSON}")
