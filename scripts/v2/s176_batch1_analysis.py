#!/usr/bin/env python3
"""Stage 15 batch 1 analyses, rules fixed before any record exists (journal J15.1-004, J15.1-006).

`parity`      greedy vLLM versus the Hugging Face reference on the same problems. PASS requires all three:
              (i) graded-correctness agreement (declared view) on at least 85% of the problems both runs attempted;
              (ii) |accuracy(vLLM) - accuracy(HF)| at most 0.05; (iii) completion-status agreement on at least 85%.
              Exact text identity is reported but not required (bf16 kernels differ between engines). A FAIL means vLLM
              calibration results are not used until the difference is understood.
`calibration` per run: completion statuses, the three grading views, the semantic outcome O2, tokens and budget use;
              per structure (instances pooled), the selection share (samples 0-3) and the estimation share (samples 4-7,
              never the selection samples); band membership by the selection share in [0.30, 0.85] (planning band of the
              plan of record G2), with the estimation share reported beside it; accuracy by level and domain with a
              2,000-resample bootstrap over structures (seed 42). Records with completion status other than COMPLETE count
              as not correct for O1 and are never relabelled wrong.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

PARITY_MIN_AGREEMENT = 0.85
PARITY_MAX_ACC_DIFF = 0.05
BAND = (0.30, 0.85)
SELECTION = range(0, 4)
ESTIMATION = range(4, 8)


def load(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def key(r: dict[str, Any]) -> str:
    return f"{r['structure_id']}:{r['instance']}:{r['cell_id']}"


def correct(r: dict[str, Any], view: str = "grade_declared") -> bool:
    return r.get(view) == "correct"


def parity(a: list[dict[str, Any]], b: list[dict[str, Any]]) -> dict[str, Any]:
    ra, rb = {key(r): r for r in a}, {key(r): r for r in b}
    shared = sorted(set(ra) & set(rb))
    if not shared:
        return {"verdict": "NOT_EVALUATED", "reason": "no shared problems"}
    agree_correct = sum(correct(ra[k]) == correct(rb[k]) for k in shared) / len(shared)
    agree_status = sum(ra[k]["completion_status"] == rb[k]["completion_status"] for k in shared) / len(shared)
    acc_a = sum(correct(ra[k]) for k in shared) / len(shared)
    acc_b = sum(correct(rb[k]) for k in shared) / len(shared)
    identical = sum(ra[k]["generated_answer_raw"].strip() == rb[k]["generated_answer_raw"].strip() for k in shared) / len(shared)
    only_a = sum(correct(ra[k]) and not correct(rb[k]) for k in shared)
    only_b = sum(correct(rb[k]) and not correct(ra[k]) for k in shared)
    passed = (agree_correct >= PARITY_MIN_AGREEMENT and abs(acc_a - acc_b) <= PARITY_MAX_ACC_DIFF
              and agree_status >= PARITY_MIN_AGREEMENT)
    return {"verdict": "PASS" if passed else "FAIL", "n_shared": len(shared), "agreement_correctness": agree_correct,
            "agreement_status": agree_status, "accuracy_a": acc_a, "accuracy_b": acc_b, "identical_text": identical,
            "discordant_correct_only_a": only_a, "discordant_correct_only_b": only_b,
            "rule": {"min_agreement": PARITY_MIN_AGREEMENT, "max_accuracy_difference": PARITY_MAX_ACC_DIFF}}


def bootstrap(per_structure: dict[str, float], n: int = 2000, seed: int = 42) -> list[float] | None:
    values = list(per_structure.values())
    if len(values) < 2:
        return None
    rng = random.Random(seed)
    means = sorted(sum(rng.choice(values) for _ in values) / len(values) for _ in range(n))
    return [means[int(0.025 * n)], means[int(0.975 * n) - 1]]


def calibration(records: list[dict[str, Any]]) -> dict[str, Any]:
    status: dict[str, int] = defaultdict(int)
    views: dict[str, dict[str, int]] = {v: defaultdict(int) for v in ("grade_declared", "grade_convertible", "grade_rel1pct",
                                                                      "o2_semantic_correct")}
    by_structure: dict[str, dict[str, list[bool]]] = defaultdict(lambda: {"sel": [], "est": []})
    meta: dict[str, dict[str, Any]] = {}
    tokens = []
    for r in records:
        status[r["completion_status"]] += 1
        for v in views:
            views[v][str(r.get(v))] += 1
        tokens.append(int(r.get("n_generated_tokens") or 0))
        part = "sel" if r["sample_index"] in SELECTION else "est" if r["sample_index"] in ESTIMATION else None
        if part:
            by_structure[r["structure_id"]][part].append(correct(r))
        meta[r["structure_id"]] = {"level": r.get("level"), "domain": r.get("domain")}
    per = {}
    for sid, d in sorted(by_structure.items()):
        sel = sum(d["sel"]) / len(d["sel"]) if d["sel"] else None
        est = sum(d["est"]) / len(d["est"]) if d["est"] else None
        per[sid] = {"selection_share": sel, "estimation_share": est, "n_sel": len(d["sel"]), "n_est": len(d["est"]),
                    "in_band": sel is not None and BAND[0] <= sel <= BAND[1], **meta[sid]}
    in_band = sorted(s for s, v in per.items() if v["in_band"])
    est_all = {s: v["estimation_share"] for s, v in per.items() if v["estimation_share"] is not None}
    est_band = {s: per[s]["estimation_share"] for s in in_band if per[s]["estimation_share"] is not None}
    by_group: dict[str, Any] = {}
    for field in ("level", "domain"):
        groups: dict[str, dict[str, float]] = defaultdict(dict)
        for s, v in per.items():
            if v["estimation_share"] is not None:
                groups[str(v[field])][s] = v["estimation_share"]
        by_group[field] = {g: {"n_structures": len(m), "mean": sum(m.values()) / len(m), "ci95": bootstrap(m)}
                           for g, m in sorted(groups.items())}
    tokens.sort()
    return {"n_records": len(records), "completion_status": dict(status), "views": {k: dict(v) for k, v in views.items()},
            "tokens_median": tokens[len(tokens) // 2] if tokens else None,
            "tokens_p90": tokens[int(0.9 * len(tokens))] if tokens else None,
            "n_structures": len(per), "band": list(BAND), "n_in_band": len(in_band), "in_band": in_band,
            "estimation_mean_all": sum(est_all.values()) / len(est_all) if est_all else None,
            "estimation_ci95_all": bootstrap(est_all),
            "estimation_mean_in_band": sum(est_band.values()) / len(est_band) if est_band else None,
            "by_group": by_group, "per_structure": per,
            "note": "selection by samples 0-3; estimates from samples 4-7 only; EXPLORATION data (dataset v1)"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("parity")
    p.add_argument("--a", required=True, help="raw_records.jsonl of the first run (vLLM)")
    p.add_argument("--b", required=True, help="raw_records.jsonl of the reference run (HF)")
    p.add_argument("--out", required=True)
    c = sub.add_parser("calibration")
    c.add_argument("--records", required=True)
    c.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    out = Path(args.out)
    if out.exists():
        print(f"Refusing to overwrite {out}", file=sys.stderr)
        return 2
    result = parity(load(Path(args.a)), load(Path(args.b))) if args.command == "parity" else calibration(load(Path(args.records)))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in result if k not in ("per_structure", "by_group")}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
