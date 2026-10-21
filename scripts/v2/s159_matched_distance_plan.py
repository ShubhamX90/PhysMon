#!/usr/bin/env python3
"""Stage 14.17: plan the plausibility-matched numeral-presence control (dry run; tokenizers only; NOT authorized to run).

Stage 14.14 found that every numeral that appears in a prompt is more probable as an answer than a matched absent numeral, and
that a cue is boosted more than a relevant input. Its control was any same-shape numeral that is absent from the prompt and not
within 1% of the gold. Most cue numerals are chosen near the gold (0.1% to 0.8% away), so that control cannot tell a presence
effect from the plausibility of a number close to the gold answer.

This plan builds the missing control. For every numeral of every feasible cell prompt it lists the numeral itself (present) and up
to K matched controls: numerals of the same shape (same count of integer digits and decimals) that are absent from the prompt and
lie at about the same distance from the gold, d = |ln(v / gold)| within a factor F of the numeral's own distance, two above and two
below the gold where possible. A numeral within 0.1% of the gold, or whose gold is zero, has no matched control (it would be a
correct answer, not an equally plausible wrong one) and is NOT_EVALUATED. Everything is written with the target unit in the
answer-line wrapper, as in Stage 14.14, so the unit is not varied. Both structure batches are included.

The job manifest uses the format of `s154_numeral_presence_plan.py`, so `s158_score_only_run.py` can score it. It does not load a
model, use a GPU or submit anything, and it states `authorized_to_run: false`.

Plan reference: protocol section 5 decision-table row 4; P4 (copying account); journals J14.14-005 and J14.17.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import random
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.benchmark import scoring_contract as sc  # noqa: E402
from physmon.benchmark.v2 import design as dg  # noqa: E402
from physmon.scoring import v2_scorer as vs  # noqa: E402

OUT_ROOT = "results/stage14/s159_matched_distance_plan"
MANIFESTS = ("data/v2/structures/v1/factor_cell_manifest.jsonl", "data/v2/structures/v2/factor_cell_manifest.jsonl")
WRAPPER = "answer_line"
MODELS = ("qwen_primary", "llama_primary")
SEED = 42
K_PER_SIDE = 2
FACTOR = 2.0
RELAXED_FACTOR = 4.0
MIN_DISTANCE = 1e-3  # a numeral closer than this to the gold is a correct answer, not an equally plausible wrong one
SCAN_CAP = 400


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


presence = _load("s154_numeral_presence_plan", "scripts/v2/s154_numeral_presence_plan.py")
plan_mod = presence.plan_mod


def shape_of(text: str) -> tuple[int, int]:
    """(integer digits, decimals) of a plain decimal numeral."""

    whole, _, frac = text.partition(".")
    return len(whole), len(frac)


def log_distance(value: float, gold: float) -> float | None:
    """|ln(|value| / |gold|)|, or None when either is zero."""

    if value == 0 or gold == 0:
        return None
    return abs(math.log(abs(value) / abs(gold)))


def prefix_overlap(text: str, gold: float) -> int:
    """Count of leading significant digits shared by the numeral and the gold written to the numeral's own digit count."""

    digits = text.replace(".", "").lstrip("0")
    if not digits:
        return 0
    significant = len(digits)
    gold_digits = f"{abs(gold):.{max(significant - 1, 0)}e}".split("e")[0].replace(".", "")
    shared = 0
    for a, b in zip(digits, gold_digits, strict=False):
        if a != b:
            break
        shared += 1
    return shared


def _band(gold: float, distance: float, factor: float, sign: int) -> tuple[float, float]:
    lo, hi = sorted((abs(gold) * math.exp(sign * distance / factor), abs(gold) * math.exp(sign * distance * factor)))
    return lo, hi


def _enumerate(lo: float, hi: float, decimals: int, rng: random.Random) -> list[str]:
    scale = 10 ** decimals
    first, last = math.ceil(lo * scale), math.floor(hi * scale)
    if last < first:
        return []
    count = last - first + 1
    picks = range(first, last + 1) if count <= SCAN_CAP else sorted(rng.sample(range(first, last + 1), SCAN_CAP))
    return [f"{m / scale:.{decimals}f}" for m in picks]


def matched_controls(text: str, present: set[float], gold: float, rng: random.Random) -> dict[str, Any]:
    """Up to 2 x K_PER_SIDE absent numerals of the same shape at about the numeral's own distance from the gold.

    Returns {"controls": [{text, side, distance, ratio, prefix_overlap}], "factor": F used, "reason": None | why none}.
    """

    value = float(text)
    own = log_distance(value, gold)
    if own is None:
        return {"controls": [], "factor": None, "reason": "numeral or gold is zero"}
    if own < MIN_DISTANCE:
        return {"controls": [], "factor": None, "reason": f"numeral within {MIN_DISTANCE:.0e} of the gold (a correct answer)"}
    whole, decimals = shape_of(text)
    for factor in (FACTOR, RELAXED_FACTOR):
        by_side: dict[int, list[dict[str, Any]]] = {1: [], -1: []}
        for sign in (1, -1):
            lo, hi = _band(gold, own, factor, sign)
            for cand in _enumerate(lo, hi, decimals, rng):
                number = float(cand)
                if cand == text or shape_of(cand)[0] != whole or any(abs(number - p) < 1e-9 for p in present):
                    continue
                if text[0] != "0" and cand[0] == "0":
                    continue
                d = log_distance(number, gold)
                if d is None or d < MIN_DISTANCE:
                    continue
                by_side[sign].append({"text": cand, "side": "above" if sign > 0 else "below", "distance": round(d, 6),
                                      "ratio": round(d / own, 4), "prefix_overlap": prefix_overlap(cand, gold),
                                      "_rank": abs(math.log(d / own)) + 0.05 * abs(prefix_overlap(cand, gold) - prefix_overlap(text, gold))})
        chosen: list[dict[str, Any]] = []
        for sign in (1, -1):
            pool = sorted(by_side[sign], key=lambda c: (c["_rank"], rng.random()))
            chosen += pool[:K_PER_SIDE]
        extra = sorted([c for s in (1, -1) for c in by_side[s] if c not in chosen], key=lambda c: (c["_rank"], rng.random()))
        while len(chosen) < 2 * K_PER_SIDE and extra:
            chosen.append(extra.pop(0))
        if len(chosen) >= 2 or factor == RELAXED_FACTOR:
            for c in chosen:
                c.pop("_rank", None)
            return {"controls": chosen, "factor": factor, "reason": None if chosen else "no numeral of this shape at this distance"}
    return {"controls": [], "factor": None, "reason": "unreachable"}


def build_jobs(rows: list[dict], tokenizers: dict[str, Any], model_keys: tuple[str, ...]) -> list[dict[str, Any]]:
    system = sc.instruction_for(WRAPPER)
    jobs: list[dict[str, Any]] = []
    for key in model_keys:
        tok = tokenizers[key]
        for row in rows:
            if not row["feasible"]:
                continue
            unit = dg.display_unit(row["gold_unit"])
            texts = presence.numerals_in(row["prompt"])
            present = {float(t) for t in texts}
            prompt = vs.build_chat_prompt(tok, system, row["prompt"])
            gold = float(row["gold_value"])
            candidates: list[dict[str, Any]] = []
            for text in texts:
                role = presence.role_of(text, row)
                candidates.append({"kind": "present", "text": text, "matched_to": None, "role": role, "meta": {}})
                rng = random.Random(f"{SEED}:matched:{row['structure_id']}:{row['instance']}:{text}")
                found = matched_controls(text, present, gold, rng)
                if not found["controls"]:
                    candidates.append({"kind": "no_matched_control", "text": None, "matched_to": text, "role": role,
                                       "meta": {"reason": found["reason"]}})
                for c in found["controls"]:
                    candidates.append({"kind": "matched_control", "text": c["text"], "matched_to": text, "role": "absent",
                                       "meta": {"control_side": c["side"], "control_distance": c["distance"],
                                                "control_distance_ratio": c["ratio"], "control_prefix_overlap": c["prefix_overlap"],
                                                "match_factor": found["factor"],
                                                "own_distance": round(log_distance(float(text), gold) or 0.0, 6),
                                                "own_prefix_overlap": prefix_overlap(text, gold)}})
            for cand in candidates:
                if cand["text"] is None:
                    continue
                target = sc.render_target(WRAPPER, cand["text"], unit)
                pair = vs.tokenize_pair(tok, prompt, target)
                jobs.append({
                    "job_id": f"{key}:{row['structure_id']}:{row['instance']}:{row['cell_id']}:cand:{cand['kind']}:{cand['matched_to'] or ''}:{cand['text']}",
                    "model_key": key, "wrapper_id": WRAPPER, "structure_id": row["structure_id"],
                    "structure_uuid": row["structure_uuid"], "template_cluster_id": row["template_cluster_id"],
                    "symbolic_program_hash": row["symbolic_program_hash"], "instance": row["instance"], "cell_id": row["cell_id"],
                    "expected_effect": row["expected_effect"], "cue_semantic_role": row.get("cue_semantic_role"),
                    "numeric_proximity": row.get("numeric_proximity"), "unit_type": row.get("unit_type"),
                    "digit_overlap": row.get("digit_overlap"), "cue_position": row.get("cue_position"),
                    "isolation_condition": row.get("isolation_condition"), "cue_numeric_value": row.get("cue_numeric_value"),
                    "cue_unit": row.get("cue_unit"), "gold_value": row["gold_value"], "gold_unit": row["gold_unit"],
                    "user_prompt": row["prompt"], "user_prompt_sha256": row["prompt_sha256"],
                    "formatted_prompt_sha256": pair.prompt_sha256, "gold_text": target, "decoy_text": None, "decoy_defined": False,
                    "n_prompt_tokens": len(pair.prompt_ids), "n_gold_tokens": len(pair.target_ids), "n_decoy_tokens": None,
                    "gold_tokenization_status": pair.status, "decoy_tokenization_status": "NOT_APPLICABLE",
                    "leading_special_tokens": pair.n_leading_special,
                    "candidate_kind": cand["kind"], "candidate_text": cand["text"], "candidate_matched_to": cand["matched_to"],
                    "candidate_role": cand["role"], "true_gold_value": row["gold_value"], **cand["meta"],
                    "candidate_note": "gold_text is the CANDIDATE string scored under this prompt; true_gold_value is the real answer",
                })
        # numerals with no matched control are kept as zero-job markers in the plan summary, not as jobs
    return jobs


def unmatched_numerals(rows: list[dict]) -> list[dict[str, Any]]:
    """Numerals that have no matched control, with the reason (model independent)."""

    out = []
    for row in rows:
        if not row["feasible"]:
            continue
        texts = presence.numerals_in(row["prompt"])
        present = {float(t) for t in texts}
        for text in texts:
            rng = random.Random(f"{SEED}:matched:{row['structure_id']}:{row['instance']}:{text}")
            found = matched_controls(text, present, float(row["gold_value"]), rng)
            if not found["controls"]:
                out.append({"structure_id": row["structure_id"], "instance": row["instance"], "cell_id": row["cell_id"],
                            "numeral": text, "role": presence.role_of(text, row), "reason": found["reason"]})
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt-id", default=None)
    parser.add_argument("--out-root", default=OUT_ROOT)
    parser.add_argument("--manifests", nargs="*", default=list(MANIFESTS))
    parser.add_argument("--structures", nargs="*", default=None, help="Restrict to these structure ids (tests).")
    parser.add_argument("--models", nargs="*", default=list(MODELS))
    args = parser.parse_args()

    sha = plan_mod.git("rev-parse", "HEAD")
    day = plan_mod.git("log", "-1", "--format=%cd", "--date=format:%Y%m%d")
    attempt = args.attempt_id or f"attempt_{day}_{sha[:7]}"
    out_dir = (REPO_ROOT / args.out_root / attempt).resolve()
    if out_dir.exists() and any(out_dir.iterdir()):
        print(f"Refusing to reuse non-empty attempt directory: {out_dir}", file=sys.stderr)
        return 2

    import transformers

    model_keys = tuple(args.models)
    tokenizers, provenance = plan_mod.load_tokenizers(model_keys)
    rows: list[dict] = []
    for manifest in args.manifests:
        rows += plan_mod.read_manifest(set(args.structures) if args.structures else None, manifest)
    jobs = build_jobs(rows, tokenizers, model_keys)
    unmatched = unmatched_numerals(rows)
    per_model = {}
    for key in model_keys:
        mine = [j for j in jobs if j["model_key"] == key]
        per_model[key] = {"n_jobs": len(mine), "by_kind": dict(Counter(j["candidate_kind"] for j in mine)),
                          "by_role": dict(sorted(Counter(j["candidate_role"] for j in mine if j["candidate_kind"] == "present").items())),
                          "tokenization_failures": sum(j["gold_tokenization_status"] != "OK" for j in mine),
                          "n_prompts": len({(j["structure_id"], j["instance"], j["cell_id"]) for j in mine}),
                          "relaxed_factor_controls": sum(j.get("match_factor") == RELAXED_FACTOR for j in mine),
                          "gpu_time_estimate": "NOT ESTIMATED: score-only passes; measure on the stack"}
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "job_manifest.jsonl").write_text(
        "".join(json.dumps(j, sort_keys=True, ensure_ascii=False) + "\n" for j in jobs), encoding="utf-8")
    (out_dir / "unmatched_numerals.json").write_text(json.dumps(
        {"n": len(unmatched), "by_reason": dict(Counter(u["reason"] for u in unmatched)),
         "by_role": dict(Counter(u["role"] for u in unmatched)), "items": unmatched}, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    plan = {"stage": "14.17", "kind": "plausibility-matched numeral-presence plan (dry run)", "authorized_to_run": False,
            "source_commit": sha, "git_status_short": plan_mod.git("status", "--short").splitlines(),
            "command": " ".join(sys.argv), "transformers": transformers.__version__, "contract_version": sc.CONTRACT_VERSION,
            "contract_fingerprint": sc.contract_fingerprint(), "wrapper_id": WRAPPER, "seed": SEED,
            "match_rule": {"shape": "same count of integer digits and decimals", "distance": "|ln(v / gold)| within a factor of the numeral's own",
                           "factor": FACTOR, "relaxed_factor": RELAXED_FACTOR, "per_side": K_PER_SIDE, "min_distance": MIN_DISTANCE,
                           "absent_from_prompt": True},
            "manifests": [{"path": m, "sha256": hashlib.sha256((REPO_ROOT / m).read_bytes()).hexdigest()} for m in args.manifests],
            "tokenizers": provenance, "per_model": per_model, "n_jobs": len(jobs), "n_unmatched_numerals_per_model": len(unmatched),
            "data_role": "EXPLORATION", "evidence_class": "exploratory; not paper-eligible; not run"}
    (out_dir / "plan.json").write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    shown = out_dir.relative_to(REPO_ROOT) if out_dir.is_relative_to(REPO_ROOT) else out_dir
    print(json.dumps({"attempt_dir": str(shown), "n_jobs": len(jobs), "authorized_to_run": False, "per_model": per_model,
                      "unmatched_numerals_per_model": len(unmatched), "unmatched_by_reason": dict(Counter(u["reason"] for u in unmatched))},
                     indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
