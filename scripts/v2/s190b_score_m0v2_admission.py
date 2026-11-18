#!/usr/bin/env python3
"""G1: apply the dataset admission standard (sections 5.2-5.3 and 6.1) to the panel reviews of M0 v2.

Input: for each judge, one or more directories holding `<item_id>_pass1.json` / `<item_id>_pass2.json` (admission) and, for
naturalness, directories of JSON files holding a rating object or a list of them (`{"item_id","rating","reason"}`).
Per structure: ADMIT when every judge's pass-2 validity is `valid` and carries no `high` flag; REJECT when any judge's
pass 2 is `invalid`, `uncertain` or carries a `high` flag (every flag is listed with its reason); INCOMPLETE when evidence is
missing (a missing review is not a verdict). Per sentence (6.1 as amended 2026-11-15): any `artificial` rating means REWRITE, and so does a D sentence rated more than one level
worse than its R twin (natural > slightly_artificial > artificial). The restricted keys give
the structure of every item and the role of every sentence; they never go to a judge.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
ADMISSION_DIR = "docs/validation/v2/llm_panel/admission_m0v2"
VALIDITY = ("valid", "invalid", "uncertain")
RATINGS = ("natural", "slightly_artificial", "artificial")
RANK = {r: i for i, r in enumerate(RATINGS)}  # natural 0 > slightly_artificial 1 > artificial 2 (higher is worse)
MAX_D_GAP = 1  # admission 6.1 (amended 2026-11-15): a D sentence may be at most this many levels worse than its R twin


def twin_violation(d_rating: str | None, r_rating: str | None) -> bool:
    """True when a D sentence is rated worse than its R twin by more than one level (natural > slightly_artificial > artificial)."""

    if d_rating not in RANK or r_rating not in RANK:
        return False
    return RANK[d_rating] - RANK[r_rating] > MAX_D_GAP
EXPECTED_BLIND = {"R": "R", "D": "D", "N": "D", "C": "C", "K": "K"}  # K_out has no blind expectation in the vocabulary


def _read(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def load_admission_reviews(dirs: list[Path]) -> dict[tuple[str, int], dict[str, Any]]:
    reviews: dict[tuple[str, int], dict[str, Any]] = {}
    for d in dirs:
        for path in sorted(d.glob("*_pass[12].json")):
            item_id, number = path.stem.rsplit("_pass", 1)
            record = _read(path)
            reviews[(item_id, int(number))] = record if isinstance(record, dict) else {"_unreadable": True}
    return reviews


def load_ratings(dirs: list[Path]) -> dict[str, dict[str, Any]]:
    ratings: dict[str, dict[str, Any]] = {}
    for d in dirs:
        for path in sorted(d.glob("*.json")):
            data = _read(path)
            for record in data if isinstance(data, list) else [data]:
                if isinstance(record, dict) and isinstance(record.get("item_id"), str):
                    ratings[record["item_id"]] = record
    return ratings


def flag_list(review: dict[str, Any]) -> list[dict[str, str]]:
    raw = review.get("defect_flags")
    severity = review.get("defect_severity") if isinstance(review.get("defect_severity"), dict) else {}
    reasons = review.get("defect_reasons") if isinstance(review.get("defect_reasons"), dict) else {}
    out = []
    for f in raw if isinstance(raw, list) else []:
        if isinstance(f, str):
            out.append({"flag": f, "severity": str(severity.get(f, "unrated")).lower(), "reason": str(reasons.get(f, ""))})
    return out


GUARD_53B_FLAGS = ("rendering_not_minimal",)
SENTENCE_ID = re.compile(r"\bT[0-9A-F]{4}\b")


def guarded_53b(flag: dict[str, str], n_sentence_ids: set[str]) -> bool:
    """Amendment A1 (docs/registry/v2/g1/freeze/amendments.md, check 5.3b): a high `rendering_not_minimal` flag whose every named
    sentence is a numeral-free control (N) sentence is a judge error. A flag naming no sentence, or any non-N sentence, counts."""

    ids = set(SENTENCE_ID.findall(flag.get("reason", "")))
    return flag["flag"] in GUARD_53B_FLAGS and bool(ids) and ids <= n_sentence_ids


def judge_verdict(item_id: str, reviews: dict[tuple[str, int], dict[str, Any]],
                  n_sentence_ids: set[str] | None = None) -> dict[str, Any]:
    p2 = reviews.get((item_id, 2))
    if p2 is None:
        return {"status": "MISSING", "reasons": ["no pass-2 review"], "flags": [], "warnings": []}
    if p2.get("_unreadable") or p2.get("validity") not in VALIDITY:
        return {"status": "MALFORMED", "reasons": ["pass-2 review unreadable or without a valid `validity`"], "flags": [],
                "warnings": []}
    flags = flag_list(p2)
    reasons, warnings, guarded = [], [], []
    for f in flags:
        if f["severity"] == "high":
            if n_sentence_ids is not None and guarded_53b(f, n_sentence_ids):
                guarded.append(f"5.3b judge error (not counted): high flag {f['flag']}: {f['reason']}")
            else:
                reasons.append(f"high flag {f['flag']}: {f['reason']}")
        elif f["severity"] == "unrated":
            warnings.append(f"flag {f['flag']} has no severity")
    if p2["validity"] != "valid" and not (guarded and not reasons):
        reasons.insert(0, f"validity is {p2['validity']}")
    elif p2["validity"] != "valid":
        warnings.append(f"validity {p2['validity']} rests only on 5.3b-guarded flags; the other judge decides")
    warnings += guarded
    for field in ("equation_consistent", "units_consistent", "answer_correct", "precision_adequate"):
        if p2.get(field) is False and p2["validity"] == "valid":
            warnings.append(f"{field} is false although validity is valid")
    return {"status": "FAIL" if reasons else "PASS", "reasons": reasons, "flags": flags, "warnings": warnings,
            "validity": p2["validity"], "admission_category": p2.get("admission_category"),
            "precision_adequate": p2.get("precision_adequate")}


def blind_agreement(item_id: str, strata: dict[str, str], reviews: dict[tuple[str, int], dict[str, Any]]) -> dict[str, Any]:
    p1 = reviews.get((item_id, 1))
    if not p1 or not isinstance(p1.get("stratum_assignments"), dict):
        return {"checked": 0, "mismatches": [], "available": False}
    checked, mismatches = 0, []
    for sid, stratum in strata.items():
        expected = EXPECTED_BLIND.get(stratum)
        if expected is None:
            continue
        got = p1["stratum_assignments"].get(sid)
        got = got.get("stratum") if isinstance(got, dict) else None
        checked += 1
        if got != expected:
            mismatches.append({"sentence_id": sid, "authors_stratum": stratum, "judge_stratum": got})
    return {"checked": checked, "mismatches": mismatches, "available": True}


def score(key: dict[str, Any], nat_key: dict[str, Any], judges: dict[str, list[Path]],
          nat_judges: dict[str, list[Path]], min_judges: int = 2, title: str = "M0 v2 admission report",
          guard_53b: bool = False) -> dict[str, Any]:
    loaded = {j: load_admission_reviews(d) for j, d in judges.items()}
    rated = {j: load_ratings(d) for j, d in nat_judges.items()}
    structures: dict[str, Any] = {}
    for item_id in sorted(key):
        n_ids = ({sid for sid, s in key[item_id].get("sentence_strata", {}).items() if s == "N"} if guard_53b else None)
        verdicts = {j: judge_verdict(item_id, r, n_ids) for j, r in loaded.items()}
        statuses = [v["status"] for v in verdicts.values()]
        reasons = [f"{j}: {r}" for j, v in verdicts.items() for r in v["reasons"]]
        if "FAIL" in statuses:
            status = "REJECT"
        elif not verdicts or any(s != "PASS" for s in statuses) or len(verdicts) < min_judges:
            status = "INCOMPLETE"
            if len(verdicts) < min_judges:
                reasons.append(f"only {len(verdicts)} judge(s) given, {min_judges} required")
            reasons += [f"{j}: {v['status']}" for j, v in verdicts.items() if v["status"] in ("MISSING", "MALFORMED")]
        else:
            status = "ADMIT"
        medium = {j: sorted(f["flag"] for f in v["flags"] if f["severity"] == "medium") for j, v in verdicts.items()}
        notes = []
        if len({tuple(m) for m in medium.values()}) > 1:
            notes.append("judges disagree on medium flags (recorded, not a rejection): " + json.dumps(medium))
        for j, v in verdicts.items():
            high_precision = any(f["flag"] == "invalid_numerical_precision" and f["severity"] == "high" for f in v["flags"])
            claude_ok = any(w.startswith("claude") and verdicts[w].get("precision_adequate") is True for w in verdicts)
            if high_precision and claude_ok and not j.startswith("claude"):
                notes.append(f"5.3 rounding guard: {j} flags precision high while a Claude judge accepts it; the status "
                             "above is not changed, the standard's owner decides")
        structures[item_id] = {
            "structure_id": key[item_id].get("structure_id"), "status": status, "reasons": reasons, "notes": notes,
            "judges": {j: {k: v[k] for k in ("status", "validity", "admission_category", "flags", "warnings") if k in v}
                       for j, v in verdicts.items()},
            "blind_stratum_agreement": {j: blind_agreement(item_id, key[item_id].get("sentence_strata", {}), r)
                                        for j, r in loaded.items()}}
    sentences: dict[str, Any] = {}
    for nat_id in sorted(nat_key):
        by_judge = {}
        for j, r in rated.items():
            rec = r.get(nat_id)
            if rec is None:
                by_judge[j] = {"rating": None, "reason": "missing"}
            elif rec.get("rating") not in RATINGS:
                by_judge[j] = {"rating": None, "reason": "malformed rating"}
            else:
                by_judge[j] = {"rating": rec["rating"], "reason": str(rec.get("reason", ""))}
        ratings = [v["rating"] for v in by_judge.values()]
        if "artificial" in ratings:
            status = "REWRITE"
        elif not by_judge or None in ratings:
            status = "PENDING"
        else:
            status = "OK"
        sentences[nat_id] = {**{k: nat_key[nat_id][k] for k in ("structure_id", "label", "stratum")},
                             "status": status, "ratings": by_judge,
                             "slightly_artificial": "slightly_artificial" in ratings, "twin_gap": []}
    # amended 6.1: each D sentence no worse than its R twin (same structure, same pair) by more than one level, per rater
    by_label = {(v["structure_id"], v["label"]): nat_id for nat_id, v in sentences.items()}
    for nat_id, v in sentences.items():
        if v["stratum"] != "D":
            continue
        twin_label = nat_key[nat_id].get("twin_label") or "R" + v["label"][1:]
        twin_id = by_label.get((v["structure_id"], twin_label))
        if twin_id is None:
            continue
        for j, d in v["ratings"].items():
            r = sentences[twin_id]["ratings"].get(j, {})
            if twin_violation(d["rating"], r.get("rating")):
                v["twin_gap"].append({"rater": j, "d": d["rating"], "r_twin": r["rating"], "twin_label": twin_label})
            elif d["rating"] is not None and r.get("rating") is None and v["status"] == "OK":
                v["status"] = "PENDING"  # the R twin is not rated yet, so the comparison cannot be made
        if v["twin_gap"]:
            v["status"] = "REWRITE"
    for item_id, s in structures.items():
        mine = [v for v in sentences.values() if v["structure_id"] == s["structure_id"]]
        s["naturalness"] = {"sentences": len(mine), "rewrite": [v["label"] for v in mine if v["status"] == "REWRITE"],
                            "pending": sum(1 for v in mine if v["status"] == "PENDING"),
                            "slightly_artificial": [v["label"] for v in mine if v["slightly_artificial"]]}
        s["ready"] = (s["status"] == "ADMIT" and not s["naturalness"]["rewrite"] and not s["naturalness"]["pending"])
    counts: dict[str, int] = {}
    for s in structures.values():
        counts[s["status"]] = counts.get(s["status"], 0) + 1
    return {"standard": "docs/registry/v2/g1/dataset_admission_standard.md sections 5.2, 5.3, 6.1 (6.1 as amended 2026-11-15)",
            "title": title,
            "judges": sorted(judges), "naturalness_judges": sorted(nat_judges), "min_judges": min_judges,
            "structure_counts": counts, "structures": structures, "sentences": sentences}


def render_markdown(report: dict[str, Any]) -> str:
    lines = [f"# {report.get('title', 'M0 v2 admission report')}", "",
             "Applies admission standard 5.2-5.3 (physics, qualified LLM panel) and 6.1 (naturalness) to the panel's reviews.",
             f"Judges: {', '.join(report['judges']) or 'none'}. Naturalness raters: "
             f"{', '.join(report['naturalness_judges']) or 'none'}. Judges required per structure: {report['min_judges']}.",
             "", "A structure is ADMITTED only if every judge calls it valid with no high flag. Missing reviews make it "
             "INCOMPLETE (a missing review is not a verdict). A sentence rated artificial must be rewritten, and so must a D sentence "
             "rated more than one level worse than its R twin (natural > slightly_artificial > artificial; standard 6.1 as amended "
             "2026-11-15).", "",
             "Structures: " + ", ".join(f"{k} {v}" for k, v in sorted(report["structure_counts"].items())), ""]
    for item_id, s in report["structures"].items():
        lines += [f"## {item_id}: {s['status']}" + ("  (ready: admitted and natural)" if s["ready"] else ""), ""]
        for r in s["reasons"]:
            lines.append(f"- {r}")
        for j, v in s["judges"].items():
            lines.append(f"- {j}: pass-2 {v['status']}" + (f", validity {v['validity']}" if "validity" in v else "")
                         + (f", category {v['admission_category']}" if v.get("admission_category") else ""))
            for f in v["flags"]:
                lines.append(f"  - flag {f['flag']} ({f['severity']}): {f['reason']}")
            for w in v["warnings"]:
                lines.append(f"  - warning: {w}")
        for n in s["notes"]:
            lines.append(f"- note: {n}")
        for j, b in s["blind_stratum_agreement"].items():
            if b["available"] and b["mismatches"]:
                lines.append(f"- pass-1 stratum differences ({j}, information only): "
                             + ", ".join(f"{m['sentence_id']} authors {m['authors_stratum']} judge {m['judge_stratum']}"
                                         for m in b["mismatches"]))
        nat = s["naturalness"]
        lines.append(f"- naturalness: {nat['sentences']} sentences, rewrite {nat['rewrite'] or 'none'}, "
                     f"pending {nat['pending']}, slightly artificial {nat['slightly_artificial'] or 'none'}")
        for v in report["sentences"].values():
            if v["structure_id"] == s["structure_id"] and v["status"] == "REWRITE":
                for j, r in v["ratings"].items():
                    if r["rating"] == "artificial":
                        lines.append(f"  - REWRITE {v['label']} ({v['stratum']}): {j}: {r['reason']}")
                for g in v.get("twin_gap", []):
                    lines.append(f"  - REWRITE {v['label']} (D): {g['rater']}: rated {g['d']} while its R twin {g['twin_label']} is "
                                 f"{g['r_twin']} (more than one level worse)")
        lines.append("")
    return "\n".join(lines) + "\n"


def parse_judges(specs: list[str]) -> dict[str, list[Path]]:
    out: dict[str, list[Path]] = {}
    for spec in specs:
        label, _, dirs = spec.partition("=")
        out.setdefault(label, []).extend(Path(d) for d in dirs.split(",") if d)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--judge", action="append", default=[], metavar="LABEL=DIR[,DIR...]",
                        help="a judge's review directories (pass-1 and pass-2 files); repeat per judge")
    parser.add_argument("--naturalness", action="append", default=[], metavar="LABEL=DIR[,DIR...]",
                        help="a naturalness rater's rating directories; repeat per rater")
    parser.add_argument("--bank", default=ADMISSION_DIR)
    parser.add_argument("--out-dir", default=ADMISSION_DIR)
    parser.add_argument("--min-judges", type=int, default=2)
    parser.add_argument("--title", default="M0 v2 admission report")
    parser.add_argument("--guard-53b", action="store_true",
                        help="apply amendment A1 (check 5.3b): rendering_not_minimal flags on N sentences are judge errors")
    args = parser.parse_args(argv)
    bank = Path(args.bank) if Path(args.bank).is_absolute() else REPO_ROOT / args.bank
    out = Path(args.out_dir) if Path(args.out_dir).is_absolute() else REPO_ROOT / args.out_dir
    targets = [out / "admission_report.json", out / "admission_report.md"]
    if any(t.exists() for t in targets):
        print("Refusing to overwrite an existing admission report", file=sys.stderr)
        return 2
    key = json.loads((bank / "key_RESTRICTED.json").read_text(encoding="utf-8"))
    nat_key = json.loads((bank / "naturalness_key_RESTRICTED.json").read_text(encoding="utf-8"))
    report = score(key, nat_key, parse_judges(args.judge), parse_judges(args.naturalness), args.min_judges, args.title,
                   guard_53b=args.guard_53b)
    out.mkdir(parents=True, exist_ok=True)
    targets[0].write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    targets[1].write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["structure_counts"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
