#!/usr/bin/env python3
"""Stage 15 (G1): score a judge's reviews of the qualification bank under the frozen protocol
(`docs/validation/v2/llm_panel/qualification_protocol_v1.md`).

Input: a directory of review files `<item_id>_pass1.json` / `<item_id>_pass2.json` (one JSON object each) and the bank's
`key_RESTRICTED.json` and `pass2_packets.jsonl`. A missing or invalid review counts as a miss (defective) or a rejection
(valid). Output: a JSON report with Q1-Q4, the verdict QUALIFIED / NOT_QUALIFIED, and the diagnostics.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.governance.review import validate_review  # noqa: E402

Q1_MIN, Q3_MIN, Q2_MIN_LEGACY_VALID = 0.85, 0.85, 5
VOCABULARY = {"hidden_coupling", "missing_assumption", "relevant_variable_removed_from_equation",
              "failed_transformation_identity", "inconsistent_units", "invalid_parameter_domain",
              "insufficient_boundary_condition", "invalid_numerical_precision", "contradictory_distractor_statement",
              "rendering_not_minimal", "other"}


def flags(record: dict | None) -> list[str]:
    """The record's defect flags as plain terms (a list of strings; objects or other shapes yield nothing)."""

    raw = (record or {}).get("defect_flags", [])
    return [f for f in raw if isinstance(f, str)] if isinstance(raw, list) else []


def has_high_severity(record: dict | None) -> bool:
    severity = (record or {}).get("defect_severity") or {}
    return isinstance(severity, dict) and any(str(v).lower() == "high" for v in severity.values())


def load_reviews(directory: Path) -> tuple[dict[tuple[str, int], dict], dict[str, list[str]]]:
    reviews, errors = {}, defaultdict(list)
    for path in sorted(directory.glob("*_pass[12].json")):
        item_id, pass_part = path.stem.rsplit("_pass", 1)
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors[item_id].append(f"pass{pass_part}: unreadable JSON ({exc})")
            continue
        problems = validate_review(record)
        if record.get("item_id") != item_id or record.get("pass_number") != int(pass_part):
            problems.append("item_id or pass_number does not match the file name")
        if problems:
            errors[item_id].extend(f"pass{pass_part}: {p}" for p in problems)
            continue
        reviews[(item_id, int(pass_part))] = record
    return reviews, dict(errors)


def score(reviews: dict[tuple[str, int], dict], key: dict[str, dict], packets2: dict[str, dict],
          split: str = "qualification") -> dict[str, Any]:
    items = {i: k for i, k in key.items() if k["split"] == split}
    per_type: dict[str, dict[str, int]] = defaultdict(lambda: {"n": 0, "detected": 0, "detected_exact_term": 0,
                                                               "flagged": 0, "pass1_detected": 0})
    valid = {"n": 0, "accepted": 0, "legacy_n": 0, "legacy_accepted": 0, "valid_but_high_severity_flag": 0}
    strata = {"n": 0, "agree": 0, "missing": 0}
    missing, unknown_terms, contested = [], defaultdict(list), {}
    for item_id, k in sorted(items.items()):
        r2 = reviews.get((item_id, 2))
        r1 = reviews.get((item_id, 1))
        if r2 is None:
            missing.append(item_id)
        for rec in (r1, r2):
            bad = sorted(set(flags(rec)) - VOCABULARY)
            if bad:
                unknown_terms[item_id].extend(bad)
        if k["expected_verdict"] == "valid":
            valid["n"] += 1
            ok = r2 is not None and r2["validity"] == "valid" and not has_high_severity(r2)  # plan: no high-severity defect
            valid["valid_but_high_severity_flag"] += r2 is not None and r2["validity"] == "valid" and has_high_severity(r2)
            valid["accepted"] += ok
            if k["source"] == "legacy_14.5":
                valid["legacy_n"] += 1
                valid["legacy_accepted"] += ok
            if k["source"] == "role_m0":  # blind stratum agreement over every certified sentence (omitted = disagree)
                given = (r1 or {}).get("stratum_assignments")
                given = given if isinstance(given, dict) else {}
                for c in packets2[item_id].get("authors_claims", []):
                    a = given.get(c["sentence_id"])
                    stratum = a.get("stratum") if isinstance(a, dict) else a
                    strata["n"] += 1
                    strata["missing"] += a is None
                    strata["agree"] += isinstance(stratum, str) and stratum.strip().upper() == c["stratum"]
            continue
        accepted = set(k.get("accepted_terms") or [k["defect_type"]])
        t = per_type[k["defect_type"]]
        t["n"] += 1
        hit = r2 is not None and r2["validity"] == "invalid" and bool(accepted & set(flags(r2)))
        if r2 is not None:
            t["detected"] += hit
            t["detected_exact_term"] += r2["validity"] == "invalid" and k["defect_type"] in flags(r2)
            t["flagged"] += r2["validity"] in ("invalid", "uncertain")
        if k["detectable_in"] == "pass1" and r1 is not None:
            t["pass1_detected"] += r1["validity"] == "invalid" and bool(accepted & set(flags(r1)))
        if k.get("contested"):
            contested[item_id] = {"reason": k["contested"], "detected": hit}
    n_def = sum(t["n"] for t in per_type.values())
    n_det = sum(t["detected"] for t in per_type.values())
    q1 = n_det / n_def if n_def else 0.0
    q3 = valid["accepted"] / valid["n"] if valid["n"] else 0.0
    zero_types = sorted(d for d, t in per_type.items() if t["detected"] == 0)
    checks = {"Q1_detected_for_declared_reason": {"value": q1, "detected": n_det, "n": n_def, "min": Q1_MIN,
                                                  "pass": q1 >= Q1_MIN},
              "Q2_legacy_valid_accepted": {"accepted": valid["legacy_accepted"], "n": valid["legacy_n"],
                                           "min": Q2_MIN_LEGACY_VALID,
                                           "pass": valid["legacy_accepted"] >= Q2_MIN_LEGACY_VALID or valid["legacy_n"] == 0},
              "Q3_all_valid_accepted": {"value": q3, "accepted": valid["accepted"], "n": valid["n"], "min": Q3_MIN,
                                        "pass": q3 >= Q3_MIN},
              "Q4_no_type_missed": {"missed_types": zero_types, "pass": not zero_types}}
    if split == "heldout":  # requalification thresholds of the protocol
        checks = {"H1_heldout_defects": {"detected": n_det, "n": n_def, "pass": n_det >= 5},
                  "H2_heldout_valid": {"accepted": valid["accepted"], "n": valid["n"], "pass": valid["accepted"] >= 3}}
    return {"split": split, "verdict": "QUALIFIED" if all(c["pass"] for c in checks.values()) else "NOT_QUALIFIED",
            "checks": checks, "per_type": {d: dict(t) for d, t in sorted(per_type.items())},
            "valid": valid, "blind_stratum_agreement": {**strata, "rate": strata["agree"] / strata["n"] if strata["n"] else None},
            "missing_pass2_reviews": missing, "contested_items": contested,
            "flags_outside_vocabulary": dict(unknown_terms)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--reviews", required=True)
    parser.add_argument("--bank", default="docs/validation/v2/llm_panel/bank_v3")
    parser.add_argument("--split", default="qualification", choices=("qualification", "heldout"))
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    bank = REPO_ROOT / args.bank if not Path(args.bank).is_absolute() else Path(args.bank)
    out = Path(args.out)
    if out.exists():
        print(f"Refusing to overwrite {out}", file=sys.stderr)
        return 2
    key = json.loads((bank / "key_RESTRICTED.json").read_text(encoding="utf-8"))
    packets2 = {json.loads(line)["item_id"]: json.loads(line)
                for line in (bank / "pass2_packets.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()}
    reviews, errors = load_reviews(Path(args.reviews))
    report = {**score(reviews, key, packets2, args.split), "review_errors": errors}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("verdict", "checks", "blind_stratum_agreement")}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
