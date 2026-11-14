#!/usr/bin/env python3
"""Stage 15 (G1): score a judge's reviews of the qualification bank under the frozen protocol
(`docs/validation/v2/llm_panel/qualification_protocol_v1.md`; `--split requal` follows `qualification_protocol_v2.md`, and
`--split requal --protocol v3` follows `qualification_protocol_v3.md`, bank v5 and judge prompt v3).

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
RETARGETED = ("missing_assumption", "insufficient_boundary_condition", "contradictory_distractor_statement",
              "invalid_numerical_precision")
FALSE_CLAIM_TYPES = ("rendering_not_minimal", "failed_transformation_identity")  # protocol v3, R5


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
          split: str = "qualification", protocol: str = "v2") -> dict[str, Any]:
    if protocol not in ("v2", "v3") or (protocol == "v3" and split != "requal"):
        raise ValueError(f"protocol {protocol!r} with split {split!r} is not defined (v3 scores only the requal split)")
    items = {i: k for i, k in key.items() if k["split"] == split}
    hits: dict[str, bool] = {}
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
            role_valid = k["source"] == "role_m0" or (protocol == "v3" and k["source"].startswith("role_m0"))
            if role_valid:  # blind stratum agreement over every certified sentence (omitted = disagree)
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
        hits[item_id] = hit
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
    if split == "requal":  # qualification_protocol_v2.md (bank v4, judge prompt v2)
        retargeted = ("missing_assumption", "insufficient_boundary_condition", "contradictory_distractor_statement",
                      "invalid_numerical_precision")
        r1 = n_det / n_def if n_def else 0.0
        checks = {"R1_detected_for_declared_reason": {"value": r1, "detected": n_det, "n": n_def, "min": 0.85,
                                                      "pass": r1 >= 0.85},
                  "R2_valid_accepted": {"value": q3, "accepted": valid["accepted"], "n": valid["n"], "min": 0.85,
                                        "pass": q3 >= 0.85},
                  "R3_failed_types_recovered": {
                      "per_type": {t: per_type[t]["detected"] for t in retargeted if t in per_type},
                      "pass": all(per_type[t]["detected"] >= 2 for t in retargeted if t in per_type)
                      and all(t in per_type for t in retargeted)},
                  "R4_no_type_with_3_or_more_items_missed": {
                      "missed_types": sorted(d for d, t in per_type.items() if t["n"] >= 3 and t["detected"] == 0),
                      "pass": not any(t["n"] >= 3 and t["detected"] == 0 for t in per_type.values())}}
    if protocol == "v3":  # qualification_protocol_v3.md (bank v5, judge prompt v3)
        checks = requal_v3_checks(items, per_type, valid, hits)
    if split == "heldout":  # requalification thresholds of the protocol
        checks = {"H1_heldout_defects": {"detected": n_det, "n": n_def, "pass": n_det >= 5},
                  "H2_heldout_valid": {"accepted": valid["accepted"], "n": valid["n"], "pass": valid["accepted"] >= 3}}
    extra = {"protocol": protocol} if protocol != "v2" else {}  # v2 reports stay byte-identical
    return {"split": split, **extra,
            "verdict": "QUALIFIED" if all(c["pass"] for c in checks.values()) else "NOT_QUALIFIED",
            "checks": checks, "per_type": {d: dict(t) for d, t in sorted(per_type.items())},
            "valid": valid, "blind_stratum_agreement": {**strata, "rate": strata["agree"] / strata["n"] if strata["n"] else None},
            "missing_pass2_reviews": missing, "contested_items": contested,
            "flags_outside_vocabulary": dict(unknown_terms)}


def requal_v3_checks(items: dict[str, dict], per_type: dict, valid: dict, hits: dict[str, bool]) -> dict[str, Any]:
    """R1-R5 of qualification_protocol_v3.md. R5: the role-format plants whose defect is a false authors' claim about the
    rendering or the shown relation (rendering_not_minimal, failed_transformation_identity) are detected in all but one
    (at least 2 of 3; all but one of 4 or more)."""

    n_def = sum(t["n"] for t in per_type.values())
    n_det = sum(t["detected"] for t in per_type.values())
    r1 = n_det / n_def if n_def else 0.0
    r2 = valid["accepted"] / valid["n"] if valid["n"] else 0.0
    false_claims = sorted(i for i, k in items.items() if k["expected_verdict"] == "invalid"
                          and k["source"].startswith("role_") and k["defect_type"] in FALSE_CLAIM_TYPES)
    n5, d5 = len(false_claims), sum(hits.get(i, False) for i in false_claims)
    need5 = n5 - 1 if n5 >= 3 else n5
    return {"R1_detected_for_declared_reason": {"value": r1, "detected": n_det, "n": n_def, "min": 0.85,
                                                "pass": r1 >= 0.85},
            "R2_valid_accepted": {"value": r2, "accepted": valid["accepted"], "n": valid["n"], "min": 0.85,
                                  "pass": r2 >= 0.85},
            "R3_retargeted_types_detected": {
                "per_type": {t: {"detected": per_type[t]["detected"], "n": per_type[t]["n"]}
                             for t in RETARGETED if t in per_type},
                "min_detected": 2,
                "pass": all(t in per_type and per_type[t]["detected"] >= 2 for t in RETARGETED)},
            "R4_no_type_with_3_or_more_items_missed": {
                "missed_types": sorted(d for d, t in per_type.items() if t["n"] >= 3 and t["detected"] == 0),
                "pass": not any(t["n"] >= 3 and t["detected"] == 0 for t in per_type.values())},
            "R5_false_claim_role_plants_detected": {
                "items": {i: hits.get(i, False) for i in false_claims}, "detected": d5, "n": n5, "min_detected": need5,
                "pass": n5 >= 3 and d5 >= need5}}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--reviews", required=True)
    parser.add_argument("--bank", default="docs/validation/v2/llm_panel/bank_v3")
    parser.add_argument("--split", default="qualification", choices=("qualification", "heldout", "requal"))
    parser.add_argument("--protocol", default="v2", choices=("v2", "v3"),
                        help="v3: qualification_protocol_v3.md (R1-R5; requal split only)")
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    if args.protocol == "v3" and args.split != "requal":
        parser.error("--protocol v3 scores only --split requal")
    bank = REPO_ROOT / args.bank if not Path(args.bank).is_absolute() else Path(args.bank)
    out = Path(args.out)
    if out.exists():
        print(f"Refusing to overwrite {out}", file=sys.stderr)
        return 2
    key = json.loads((bank / "key_RESTRICTED.json").read_text(encoding="utf-8"))
    packets2 = {json.loads(line)["item_id"]: json.loads(line)
                for line in (bank / "pass2_packets.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()}
    reviews, errors = load_reviews(Path(args.reviews))
    report = {**score(reviews, key, packets2, args.split, args.protocol), "review_errors": errors}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("verdict", "checks", "blind_stratum_agreement")}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
