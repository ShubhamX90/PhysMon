#!/usr/bin/env python3
"""Stage 14.14: plan the numeral-presence control (dry run; tokenizers only; NOT authorized to run).

Stage 14.12 showed that no record scores the same candidate answer where the same numeral plays different roles. This plan
builds the missing control from the committed factor-cell manifest: for every feasible cell prompt it lists every numeral that
appears in the prompt as a candidate answer (written with the target unit in the answer-line wrapper, exactly as the numeral is
written in the prompt), tagged with its role (the cue numeral, or a relevant input of the problem), and for each of them a matched
absent control: a numeral of the same shape (same digit count and decimal places) that appears nowhere in the prompt and is not
within 1% of the gold answer. The log-probability of a present numeral minus that of its matched control, under the same prompt,
is the presence effect for that role; the cue-numeral effect can then be compared with the effect for relevant inputs.

The job manifest uses the format of `s147_pilot_plan.py`, so `s147_pilot_run.py` can score it: the candidate string is the job's
`gold_text` (the runner calls it "gold"), the real gold answer is kept in `true_gold_value`, and no decoy is defined. It does not
load a model, use a GPU or submit anything, and it states `authorized_to_run: false`.

Plan reference: protocol section 5 decision-table row 4; P4 (copying account); journal J14.12-002.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.benchmark import scoring_contract as sc  # noqa: E402
from physmon.benchmark.v2 import design as dg  # noqa: E402
from physmon.scoring import v2_scorer as vs  # noqa: E402

OUT_ROOT = "results/stage14/s154_numeral_presence_plan"
WRAPPER = "answer_line"
MODELS = ("qwen_primary", "llama_primary")
SEED = 42
NUMERAL = re.compile(r"(?<![\w.])\d+(?:\.\d+)?(?:[eE][-+]?\d+)?(?![\w])")


def _load_pilot_plan():
    spec = importlib.util.spec_from_file_location("s147_pilot_plan", REPO_ROOT / "scripts/v2/s147_pilot_plan.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


plan_mod = _load_pilot_plan()


def numerals_in(prompt: str) -> list[str]:
    """Distinct numerals of a prompt, in order of first appearance, as written."""

    seen: list[str] = []
    for text in NUMERAL.findall(prompt):
        if text not in seen:
            seen.append(text)
    return seen


def role_of(text: str, row: dict) -> str:
    cue = row.get("cue_numeric_value")
    if cue is not None and abs(float(text) - float(cue)) < 1e-9:
        return "cue_relevant_reference" if row["cell_id"] == "role_reversal" else "cue_" + str(row.get("cue_semantic_role"))
    return "relevant_input"


def control_for(text: str, present: set[float], gold: float, rng: random.Random) -> str | None:
    """A numeral of the same shape as `text` that is not in the prompt and not within 1% of the gold; None if none is found."""

    for _ in range(200):
        chars = []
        for position, ch in enumerate(text):
            if ch.isdigit():
                lowest = 1 if position == 0 and ch != "0" else 0  # keep a non-zero leading digit, keep "0.x" as "0.x"
                chars.append(str(rng.randint(lowest, 9)))
            else:
                chars.append(ch)
        candidate = "".join(chars)
        value = float(candidate)
        if candidate == text or any(abs(value - p) < 1e-9 for p in present):
            continue
        if gold != 0 and abs(value - gold) / abs(gold) <= 0.01:
            continue
        return candidate
    return None


def build_jobs(rows: list[dict], tokenizers: dict[str, Any], model_keys: tuple[str, ...]) -> list[dict[str, Any]]:
    system = sc.instruction_for(WRAPPER)
    jobs: list[dict[str, Any]] = []
    for key in model_keys:
        tok = tokenizers[key]
        for row in rows:
            if not row["feasible"]:
                continue
            unit = dg.display_unit(row["gold_unit"])
            texts = numerals_in(row["prompt"])
            present = {float(t) for t in texts}
            prompt = vs.build_chat_prompt(tok, system, row["prompt"])
            candidates: list[dict[str, Any]] = []
            for text in texts:
                candidates.append({"kind": "present", "text": text, "matched_to": None, "role": role_of(text, row)})
                rng = random.Random(f"{SEED}:{row['structure_id']}:{row['instance']}:{text}")
                control = control_for(text, present, float(row["gold_value"]), rng)
                candidates.append({"kind": "absent_control", "text": control, "matched_to": text, "role": "absent"})
            for cand in candidates:
                if cand["text"] is None:
                    continue
                target = sc.render_target(WRAPPER, cand["text"], unit)
                pair = vs.tokenize_pair(tok, prompt, target)
                jobs.append({
                    "job_id": f"{key}:{row['structure_id']}:{row['instance']}:{row['cell_id']}:cand:{cand['kind']}:{cand['text']}",
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
                    "candidate_role": cand["role"], "true_gold_value": row["gold_value"],
                    "candidate_note": "gold_text is the CANDIDATE string scored under this prompt; true_gold_value is the real answer",
                })
    return jobs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt-id", default=None)
    parser.add_argument("--out-root", default=OUT_ROOT)
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
    rows = plan_mod.read_manifest(set(args.structures) if args.structures else None)
    jobs = build_jobs(rows, tokenizers, model_keys)
    per_model = {}
    for key in model_keys:
        mine = [j for j in jobs if j["model_key"] == key]
        per_model[key] = {"n_jobs": len(mine), "by_kind": dict(Counter(j["candidate_kind"] for j in mine)),
                          "by_role": dict(sorted(Counter(j["candidate_role"] for j in mine).items())),
                          "tokenization_failures": sum(j["gold_tokenization_status"] != "OK" for j in mine),
                          "n_prompts": len({(j["structure_id"], j["instance"], j["cell_id"]) for j in mine}),
                          "gpu_time_estimate": "NOT ESTIMATED: score-only passes; measure on the stack"}
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "job_manifest.jsonl").write_text(
        "".join(json.dumps(j, sort_keys=True, ensure_ascii=False) + "\n" for j in jobs), encoding="utf-8")
    plan = {"stage": "14.14", "kind": "numeral-presence control plan (dry run)", "authorized_to_run": False,
            "source_commit": sha, "git_status_short": plan_mod.git("status", "--short").splitlines(),
            "command": " ".join(sys.argv), "transformers": transformers.__version__, "contract_version": sc.CONTRACT_VERSION,
            "contract_fingerprint": sc.contract_fingerprint(), "wrapper_id": WRAPPER, "seed": SEED,
            "candidate_policy": ("every numeral of each cell prompt, as written, with the target unit; one matched absent control per "
                                 "numeral (same shape, not in the prompt, not within 1% of the gold)"),
            "manifest": {"path": plan_mod.MANIFEST, "sha256": hashlib.sha256((REPO_ROOT / plan_mod.MANIFEST).read_bytes()).hexdigest()},
            "tokenizers": provenance, "per_model": per_model, "n_jobs": len(jobs),
            "data_role": "EXPLORATION", "evidence_class": "exploratory; not paper-eligible; not run"}
    (out_dir / "plan.json").write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    shown = out_dir.relative_to(REPO_ROOT) if out_dir.is_relative_to(REPO_ROOT) else out_dir
    print(json.dumps({"attempt_dir": str(shown), "n_jobs": len(jobs), "authorized_to_run": False, "per_model": per_model}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
