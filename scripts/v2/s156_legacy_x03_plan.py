#!/usr/bin/env python3
"""Stage 14.16: plan X03 on the legacy families (dry run; tokenizers only; NOT authorized to run).

Card X03 asks for a stratified 60 to 100 families drawn from the original families, paired wrapper variants, both primary
dense models. Stage 14.10 ran X03 on the ten v2 structures; this plans the legacy-family version, the one the card names.

Sampling rule, frozen before any score exists: from the 135 families of the Stage 14.4 cohort, 60 families stratified by cue type
and domain (every non-empty stratum gets at least one family, the rest are allocated in proportion by largest remainder), drawn
with a seeded generator. The sample and its seed are written to the plan.

A legacy family has four renderings and each rendering carries a cue; there is no no-cue prompt. So the design is a candidate
matrix inside each family: for every rendering v (the prompt) the plan lists the gold answer and, for each rendering u, the cue
numeral of u written as an answer with the target unit. The cue numeral of u is present in prompt u and normally absent from prompt
v (flagged when it also appears in v as a relevant input), so the same candidate string is scored where it is in the prompt and where
it is not. Families whose cue is not a number (frame renderings, colours, words) carry no candidate numeral: only the gold answer is listed.
Four wrappers of the Stage 14.3 contract are used: `answer_line`, `plain`, `boxed`, `json`.

The manifest uses the format of `s147_pilot_plan.py`, so `s147_pilot_run.py` can score it (the candidate is the job's `gold_text`; the
real answer is `true_gold_value`). Legacy conventions are kept: the unit string is the one stored with the family (for example
`m/s^2`), and the value text is as stored. It does not load a model, use a GPU or submit anything.

Plan reference: card X03 (v2 p.39), P1.3 and P1.4 (p.17), journal J14.10-001 (the deviation this closes).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.benchmark import scoring_contract as sc  # noqa: E402
from physmon.scoring import v2_scorer as vs  # noqa: E402

OUT_ROOT = "results/stage14/s156_legacy_x03_plan"
CLUSTERS = "results/stage14/s144_structure_overlap/attempt_20261016_d637b0e/clusters.csv"
WRAPPERS = ("answer_line", "plain", "boxed", "json")
MODELS = ("qwen_primary", "llama_primary")
N_FAMILIES = 60
SEED = 42
NUMERAL = re.compile(r"(?<![\w.])\d+(?:\.\d+)?(?:[eE][-+]?\d+)?(?![\w])")


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


plan_mod = _load("s147_pilot_plan", "scripts/v2/s147_pilot_plan.py")
s145 = _load("s145_validation_materials", "scripts/v2/s145_validation_materials.py")


def allocate(strata: dict[tuple[str, str], list[str]], total: int) -> dict[tuple[str, str], int]:
    """At least one per non-empty stratum, the rest in proportion by largest remainder; never more than the stratum holds."""

    keys = sorted(strata)
    if total < len(keys):
        raise ValueError("fewer families requested than strata")
    n_all = sum(len(strata[k]) for k in keys)
    counts = {k: 1 for k in keys}
    spare = total - len(keys)
    shares = {k: spare * len(strata[k]) / n_all for k in keys}
    for k in keys:
        counts[k] += int(shares[k])
    left = total - sum(counts.values())
    for k in sorted(keys, key=lambda key: (-(shares[key] - int(shares[key])), key)):
        if left <= 0:
            break
        counts[k] += 1
        left -= 1
    for k in keys:  # a stratum cannot give more families than it has; move the excess to the largest stratum with room
        if counts[k] > len(strata[k]):
            excess, counts[k] = counts[k] - len(strata[k]), len(strata[k])
            for other in sorted(keys, key=lambda key: -(len(strata[key]) - counts[key])):
                room = len(strata[other]) - counts[other]
                take = min(room, excess)
                counts[other] += take
                excess -= take
    return counts


def draw_sample(cohort: list[dict], total: int = N_FAMILIES, seed: int = SEED) -> list[str]:
    strata: dict[tuple[str, str], list[str]] = defaultdict(list)
    for row in cohort:
        strata[(row["cue_type"], row["domain"])].append(row["family"])
    counts = allocate({k: sorted(v) for k, v in strata.items()}, total)
    rng = random.Random(f"{seed}:legacy-x03")
    chosen: list[str] = []
    for key in sorted(strata):
        chosen += sorted(rng.sample(sorted(strata[key]), counts[key]))
    return sorted(chosen)


def parse_answer(text: str) -> tuple[str, str]:
    value, unit = text.split(" ", 1)
    float(value)
    return value, unit.strip()


def is_numeric(text: Any) -> bool:
    try:
        float(str(text))
    except ValueError:
        return False
    return True


def numerals(prompt: str) -> set[float]:
    return {float(t) for t in NUMERAL.findall(prompt)}


def family_jobs(family: dict, cluster: dict, wrapper: str, model_key: str, tok: Any) -> list[dict[str, Any]]:
    value_text, unit = parse_answer(str(family["correct_answer"]))
    variants = sorted(family["variants"], key=lambda v: int(v["variant_id"]))
    system = sc.instruction_for(wrapper)
    # A family either has a numeric cue in every rendering (a mass, a reading) or none (a colour, a word, a unit rendering):
    # only the first kind has candidate numerals; the rest list the gold answer only.
    has_candidates = all(is_numeric(v["cue_value"]) for v in variants)
    jobs: list[dict[str, Any]] = []
    for v in variants:
        prompt_text = str(v["prompt"])
        prompt = vs.build_chat_prompt(tok, system, prompt_text)
        present_numbers = numerals(prompt_text)
        candidates = [("gold", value_text, None)]
        if has_candidates:
            for u in variants:
                candidates.append(("cue_candidate", str(u["cue_value"]), int(u["variant_id"])))
        for kind, text, source_variant in candidates:
            target = sc.render_target(wrapper, text, unit)
            pair = vs.tokenize_pair(tok, prompt, target)
            own = source_variant is not None and source_variant == int(v["variant_id"])
            jobs.append({
                "job_id": f"{model_key}:{family['template_id']}:v{v['variant_id']}:{kind}"
                          + ("" if source_variant is None else f":c{source_variant}") + f":{wrapper}",
                "model_key": model_key, "wrapper_id": wrapper, "structure_id": family["template_id"],
                "structure_uuid": family["template_id"], "template_cluster_id": cluster["cluster_id"],
                "symbolic_program_hash": None, "instance": 0, "cell_id": f"variant{v['variant_id']}",
                "expected_effect": "legacy", "cue_semantic_role": family["cue_type"], "numeric_proximity": None,
                "unit_type": None, "digit_overlap": None, "cue_position": None, "isolation_condition": None,
                "cue_numeric_value": float(v["cue_value"]) if has_candidates else None, "cue_unit": None,
                "gold_value": float(value_text), "gold_unit": unit, "user_prompt": prompt_text,
                "user_prompt_sha256": hashlib.sha256(prompt_text.encode("utf-8")).hexdigest(),
                "formatted_prompt_sha256": pair.prompt_sha256, "gold_text": target, "decoy_text": None, "decoy_defined": False,
                "n_prompt_tokens": len(pair.prompt_ids), "n_gold_tokens": len(pair.target_ids), "n_decoy_tokens": None,
                "gold_tokenization_status": pair.status, "decoy_tokenization_status": "NOT_APPLICABLE",
                "leading_special_tokens": pair.n_leading_special,
                "candidate_kind": kind, "candidate_text": text, "candidate_source_variant": source_variant,
                "candidate_in_own_prompt": own if source_variant is not None else None,
                "candidate_numeral_in_prompt": (float(text) in present_numbers) if kind == "cue_candidate" else None,
                "prompt_variant": int(v["variant_id"]), "true_gold_value": float(value_text),
                "candidate_note": "gold_text is the CANDIDATE string scored under this prompt; true_gold_value is the real answer",
            })
    return jobs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt-id", default=None)
    parser.add_argument("--out-root", default=OUT_ROOT)
    parser.add_argument("--n-families", type=int, default=N_FAMILIES)
    parser.add_argument("--families", nargs="*", default=None, help="Use these family ids instead of the sample (tests).")
    parser.add_argument("--models", nargs="*", default=list(MODELS))
    parser.add_argument("--wrappers", nargs="*", default=list(WRAPPERS), choices=sorted(sc.WRAPPERS))
    args = parser.parse_args()

    sha = plan_mod.git("rev-parse", "HEAD")
    day = plan_mod.git("log", "-1", "--format=%cd", "--date=format:%Y%m%d")
    attempt = args.attempt_id or f"attempt_{day}_{sha[:7]}"
    out_dir = (REPO_ROOT / args.out_root / attempt).resolve()
    if out_dir.exists() and any(out_dir.iterdir()):
        print(f"Refusing to reuse non-empty attempt directory: {out_dir}", file=sys.stderr)
        return 2

    import transformers

    with (REPO_ROOT / CLUSTERS).open(newline="", encoding="utf-8") as handle:
        clusters = {r["family"]: r for r in csv.DictReader(handle)}
    cohort = [r for r in clusters.values() if r["in_135_cohort"] == "1"]
    sample = sorted(args.families) if args.families else draw_sample(cohort, args.n_families)
    families = s145.load_families()
    model_keys = tuple(args.models)
    tokenizers, provenance = plan_mod.load_tokenizers(model_keys)
    jobs: list[dict[str, Any]] = []
    for key in model_keys:
        for wrapper in args.wrappers:
            for fid in sample:
                jobs += family_jobs(families[fid], clusters[fid], wrapper, key, tokenizers[key])
    per_model = {}
    for key in model_keys:
        mine = [j for j in jobs if j["model_key"] == key]
        per_model[key] = {"n_jobs": len(mine), "by_kind": dict(Counter(j["candidate_kind"] for j in mine)),
                          "by_wrapper": dict(sorted(Counter(j["wrapper_id"] for j in mine).items())),
                          "tokenization_failures": sum(j["gold_tokenization_status"] != "OK" for j in mine),
                          "candidates_whose_numeral_is_also_in_a_foreign_prompt": sum(
                              1 for j in mine if j["candidate_kind"] == "cue_candidate" and not j["candidate_in_own_prompt"]
                              and j["candidate_numeral_in_prompt"]),
                          "gpu_time_estimate": "NOT ESTIMATED: score-only passes; measure on the stack"}
    strata = Counter((clusters[f]["cue_type"], clusters[f]["domain"]) for f in sample)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "job_manifest.jsonl").write_text("".join(json.dumps(j, sort_keys=True, ensure_ascii=False) + "\n" for j in jobs),
                                                encoding="utf-8")
    plan = {"stage": "14.16", "kind": "legacy-family X03 plan (dry run)", "authorized_to_run": False, "source_commit": sha,
            "git_status_short": plan_mod.git("status", "--short").splitlines(), "command": " ".join(sys.argv),
            "transformers": transformers.__version__, "contract_version": sc.CONTRACT_VERSION,
            "contract_fingerprint": sc.contract_fingerprint(), "wrapper_ids": list(args.wrappers), "seed": SEED,
            "sampling_rule": ("60 of the 135 cohort families, stratified by cue type and domain, at least one per non-empty stratum, "
                              "the rest by largest remainder, seeded draw; frozen before any score"),
            "sample": sample, "sample_strata": {f"{k[0]}|{k[1]}": v for k, v in sorted(strata.items())},
            "cohort": {"path": CLUSTERS, "sha256": hashlib.sha256((REPO_ROOT / CLUSTERS).read_bytes()).hexdigest(), "n": len(cohort)},
            "tokenizers": provenance, "per_model": per_model, "n_jobs": len(jobs), "data_role": "EXPLORATION",
            "evidence_class": "exploratory; not paper-eligible; not run"}
    (out_dir / "plan.json").write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    shown = out_dir.relative_to(REPO_ROOT) if out_dir.is_relative_to(REPO_ROOT) else out_dir
    print(json.dumps({"attempt_dir": str(shown), "n_jobs": len(jobs), "authorized_to_run": False, "n_families": len(sample),
                      "per_model": per_model, "sample_strata": plan["sample_strata"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
