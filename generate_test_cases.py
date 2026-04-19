# scripts/generate_test_cases.py
import json
import re
import argparse

# ---------- Arguments ----------
parser = argparse.ArgumentParser(
    description="Generate test_cases.json from requirements.json and expected_structure.json"
)
parser.add_argument("--requirements", "-r", required=True, help="Path to requirements.json")
parser.add_argument("--structure",    "-s", required=True, help="Path to expected_structure.json")
parser.add_argument("--output",       "-o", required=True, help="Path to output test_cases.json")
parser.add_argument(
    "--select", "-q", nargs="*",
    help="Explicit requirement IDs to include (space-separated). "
         "If omitted, all leaf nodes in expected_structure.json are used."
)
args = parser.parse_args()

# ---------- Load inputs ----------
with open(args.requirements, "r") as f:
    all_requirements: list[dict] = json.load(f)

with open(args.structure, "r") as f:
    structure: dict[str, list[str]] = json.load(f)

# Index requirements by ID for fast lookup
req_index: dict[str, dict] = {r["requirement_id"]: r for r in all_requirements}

# ---------- Resolve selected requirement IDs ----------
# A "leaf" in expected_structure is a child suffix whose full ID does NOT
# appear as a parent key in the structure — i.e. it has no further children.
all_parent_ids = set(structure.keys())

def expand_children(parent_id: str) -> list[str]:
    """Return the full requirement IDs of all children of parent_id."""
    children = []
    for suffix in structure.get(parent_id, []):
        child_id = f"{parent_id}{suffix}"
        children.append(child_id)
    return children

# Build full set of child IDs across the whole structure
all_child_ids: list[str] = []
for parent_id, suffixes in structure.items():
    for suffix in suffixes:
        child_id = f"{parent_id}{suffix}"
        all_child_ids.append(child_id)

# Leaf = child that is NOT itself a parent
leaf_ids = [cid for cid in all_child_ids if cid not in all_parent_ids]

if args.select:
    selected_ids = args.select
else:
    selected_ids = leaf_ids

print(f"Selected {len(selected_ids)} requirement IDs for test case generation.")

# ---------- Description generation ----------

# Map of common CFR imperative verbs → passive past participle
VERB_PASSIVE: dict[str, str] = {
    "conduct":    "conducted",
    "identify":   "identified",
    "evaluate":   "evaluated",
    "determine":  "determined",
    "assess":     "assessed",
    "consider":   "considered",
    "document":   "documented",
    "perform":    "performed",
    "review":     "reviewed",
    "establish":  "established",
    "implement":  "implemented",
    "verify":     "verified",
    "monitor":    "monitored",
    "analyze":    "analyzed",
    "analyse":    "analysed",
    "record":     "recorded",
    "maintain":   "maintained",
    "ensure":     "ensured",
    "include":    "included",
    "address":    "addressed",
    "occur":      "accounted for",
    "introduce":  "introduced",
}

# Words that signal a noun-phrase description (no leading verb)
NOUN_STARTERS = {
    "biological", "chemical", "physical", "environmental",
    "formulation", "facility", "raw", "transportation",
    "manufacturing", "packaging", "storage", "intended",
    "sanitation", "any", "hazard", "food", "ingredient",
    "pathogen", "factor", "practice", "procedure", "activity",
    "distribution", "labeling", "equipment", "condition",
    "material", "hygiene", "use",
}

def is_plural_noun(word: str) -> bool:
    """Rough plural check: ends in a known plural suffix or is a known plural word."""
    known_plurals = {
        "hazards", "pathogens", "materials", "ingredients", "procedures",
        "practices", "activities", "factors", "foods", "toxins", "controls",
        "reports", "methods", "pathogens", "hazards", "risks", "items",
    }
    w = word.rstrip(",.").lower()
    return w in known_plurals or (w.endswith("s") and not w.endswith("ss"))


def noun_verb(phrase_words: list[str]) -> str:
    """Return 'are' or 'is' based on whether the last content word looks plural."""
    for word in reversed(phrase_words):
        clean = word.rstrip(",.()")
        if clean:
            return "are" if is_plural_noun(clean) else "is"
    return "is"


def to_verify_description(raw: str) -> str:
    """
    Convert a short requirement description into a 'Verify that ...' test sentence.

    Handles three patterns:
      1. Imperative verb phrase  e.g. "Conduct hazard analysis"
         → "Verify that the hazard analysis is conducted."
      2. 'Must' / passive phrase e.g. "Hazard analysis must be written"
         → "Verify that the hazard analysis is documented in writing."
      3. Noun phrase             e.g. "Biological hazards"
         → "Verify that biological hazards are identified and evaluated."
    """
    text = raw.strip().rstrip(".")

    # ── Pattern 2: contains "must be" ──────────────────────────────────────
    must_match = re.match(r"^(.*?)\s+must\s+be\s+(.+)$", text, re.IGNORECASE)
    if must_match:
        subject = must_match.group(1).strip().lower()
        predicate = must_match.group(2).strip()
        return f"Verify that the {subject} is {predicate}."

    words = text.split()
    first_word = words[0].lower() if words else ""

    # ── Pattern 1: imperative verb ─────────────────────────────────────────
    if first_word in VERB_PASSIVE:
        past = VERB_PASSIVE[first_word]
        obj_words = words[1:]           # everything after the verb
        obj_phrase = " ".join(obj_words).strip().lower()

        # Edge case: verb with only an adverb remainder (e.g. "Occur naturally")
        # → treat whole phrase as a behaviour description
        if not obj_phrase or all(
            w.endswith("ly") for w in obj_phrase.split() if w
        ):
            return f"Verify that hazards that {text.lower()} are identified and documented."

        # Determine are/is based on the object noun
        verb_form = noun_verb(obj_words)

        # Add article if object has none
        first_obj = obj_words[0].lower() if obj_words else ""
        if first_obj and first_obj not in {"a", "an", "the", "all", "each", "any"}:
            obj_phrase = "the " + obj_phrase

        return f"Verify that {obj_phrase} {verb_form} {past}."

    # ── Pattern 3: noun phrase ─────────────────────────────────────────────
    noun_phrase = text.lower()
    verb_form = noun_verb(words)
    return f"Verify that {noun_phrase} {verb_form} identified and evaluated."


# ---------- Build test cases ----------
test_cases = []

for i, req_id in enumerate(selected_ids, start=1):
    req = req_index.get(req_id)
    if req is None:
        print(f"  [WARN] {req_id} not found in requirements.json — skipping.")
        continue

    tc_id = f"TC-{i:03d}"
    description = to_verify_description(req["description"])

    test_cases.append({
        "test_case_id":   tc_id,
        "requirement_id": req_id,
        "description":    description,
    })

# ---------- Save ----------
with open(args.output, "w") as f:
    json.dump(test_cases, f, indent=2)

print(f"Saved {len(test_cases)} test cases → {args.output}")
