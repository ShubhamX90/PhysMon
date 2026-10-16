#!/usr/bin/env python3
"""Stage 14.3: scoring-interface audit for the Stage 6 behavioural records (tokenizer only, CPU).

Reconstructs, for every committed Stage 6 prompt record, exactly what was scored: the raw prompt bytes,
the chat-templated prompt, the token ids used by behavioural scoring and generation
(`add_special_tokens=True`), the token ids used by activation extraction (`add_special_tokens=False`), the
answer-token span, and the boundary tokenization. It also tokenizes the frozen wrapper multiverse
(`physmon.benchmark.scoring_contract`) and tests whether the 0.5-nat legacy label is easier to cross for
longer answer sequences (v2 P1.4, p.17).

Only tokenizer files are read from the model store (read-only). No model weights are loaded, no GPU is used,
nothing is written outside the attempt directory. Manual teacher-forced scoring on representative cases needs a
model forward pass and is therefore NOT_EVALUATED here; the cases and their expected token spans are written
to `manual_scoring_cases.json` for a later approved GPU job.

Plan reference: B1.4 (p.7), P1.3-P1.4 (p.17), C04-C05 (p.33), card X03 (p.39), first sprint item 3 (p.48).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.benchmark import scoring_contract as sc  # noqa: E402
from physmon.governance import recompute as rc  # noqa: E402
from physmon.utils.paths import expand_model_path  # noqa: E402

OUT_ROOT = "results/stage14/s143_scoring_contract"
INPUTS = {
    "prompt_records": "results/stage6/behavioural_full_rerun/prompt_records.jsonl",
    "rendered_families": "results/stage6/generated_full_benchmark",
    "registry": "docs/model_registry.yml",
    "per_family": "results/stage6/analysis_d2/stage6_d1_per_family.csv",
}
MODEL_KEYS = {
    "Qwen/Qwen2.5-7B-Instruct": "qwen_primary",
    "meta-llama/Llama-3.1-8B-Instruct": "llama_primary",
}


def load_run_behavioural():
    spec = importlib.util.spec_from_file_location("rb", REPO_ROOT / "scripts/run_behavioural.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True,
                          check=False).stdout.strip()


def load_tokenizers() -> tuple[dict[str, Any], dict[str, Any]]:
    from transformers import AutoTokenizer

    registry = yaml.safe_load((REPO_ROOT / INPUTS["registry"]).read_text(encoding="utf-8"))["models"]
    tokenizers, provenance = {}, {}
    for model_name, key in MODEL_KEYS.items():
        path = Path(expand_model_path(registry[key]["path"]))
        tokenizers[model_name] = AutoTokenizer.from_pretrained(
            str(path), local_files_only=True, trust_remote_code=False
        )
        provenance[model_name] = {
            "registry_key": key,
            "path": str(path),
            "tokenizer.json_sha256": sha256_file(path / "tokenizer.json"),
            "tokenizer_config.json_sha256": sha256_file(path / "tokenizer_config.json"),
            "bos_token_id": tokenizers[model_name].bos_token_id,
        }
    return tokenizers, provenance


def read_records() -> list[dict]:
    path = REPO_ROOT / INPUTS["prompt_records"]
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def numeric_token_count(tokenizer, ids: list[int]) -> int:
    return sum(any(ch.isdigit() for ch in tokenizer.decode([i])) for i in ids)


def token_audit(records, tokenizers, rb, rendered) -> tuple[list[dict], dict[str, Any]]:
    rows = []
    for record in records:
        model = record["model_name"]
        tok = tokenizers[model]
        raw = record["prompt"]
        family = rendered[record["template_id"]]
        variant = next(v for v in family["variants"] if int(v["variant_id"]) == int(record["variant_id"]))
        formatted = rb.format_prompt_with_chat_template(raw, tok)
        behavioural = tok(formatted, add_special_tokens=True).input_ids
        native = tok(formatted, add_special_tokens=False).input_ids
        answer = str(record["correct_answer"])
        answer_ids = tok(answer, add_special_tokens=False).input_ids
        joint = tok(formatted + answer, add_special_tokens=True).input_ids
        bos = tok.bos_token_id
        generated = str(record.get("generated_text") or "").strip()
        stored = rc.as_float_or_none(record.get("logprob_correct_answer"))
        rows.append({
            "model": model,
            "template_id": record["template_id"],
            "variant_id": int(record["variant_id"]),
            "raw_prompt_equals_rendered_family": int(raw == variant["prompt"]),
            "correct_answer_equals_rendered_family": int(answer == family["correct_answer"]),
            "formatted_prompt_sha256": sha256_text(formatted),
            "formatted_ends_with_assistant_opener": int(formatted.rstrip(" ").endswith(("assistant\n", "\n\n"))),
            "n_prompt_tokens_behavioural": len(behavioural),
            "n_prompt_tokens_native": len(native),
            "leading_bos_behavioural": sc.leading_special_count(behavioural, bos),
            "leading_bos_native": sc.leading_special_count(native, bos),
            "behavioural_equals_extraction_ids": int(behavioural == native),
            "answer": answer,
            "n_answer_tokens": len(answer_ids),
            "n_numeric_answer_tokens": numeric_token_count(tok, answer_ids),
            "first_answer_token": tok.decode(answer_ids[:1]),
            "separate_equals_joint_tokenization": int(behavioural + answer_ids == joint),
            "generation_starts_with_Answer_prefix": int(generated.startswith("Answer:")),
            "stored_logprob": stored,
            "stored_logprob_per_answer_token": (stored / len(answer_ids)) if stored is not None else None,
        })
    return rows, {}


def wrapper_audit(records, tokenizers, rb) -> list[dict]:
    """Token counts per wrapper and tokenizer for each family (variant 0 prompt for the boundary check)."""

    seen = {}
    for record in records:
        if int(record["variant_id"]) == 0:
            seen[(record["model_name"], record["template_id"])] = record
    rows = []
    for (model, template_id), record in sorted(seen.items()):
        tok = tokenizers[model]
        value_text, unit = sc.split_answer(str(record["correct_answer"]))
        for wrapper_id in sc.WRAPPERS:
            target = sc.render_target(wrapper_id, value_text, unit)
            messages = [
                {"role": "system", "content": sc.instruction_for(wrapper_id)},
                {"role": "user", "content": record["prompt"]},
            ]
            formatted = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            prompt_ids = tok(formatted, add_special_tokens=True).input_ids
            target_ids = tok(target, add_special_tokens=False).input_ids
            joint = tok(formatted + target, add_special_tokens=True).input_ids
            rows.append({
                "model": model,
                "template_id": template_id,
                "wrapper_id": wrapper_id,
                "target": target,
                "n_target_tokens": len(target_ids),
                "n_numeric_target_tokens": numeric_token_count(tok, target_ids),
                "separate_equals_joint_tokenization": int(prompt_ids + target_ids == joint),
                "instruction_sha256": sha256_text(sc.instruction_for(wrapper_id)),
            })
    return rows


def label_table(records) -> dict[tuple[str, str], dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[int, float]] = {}
    for record in records:
        value = rc.as_float_or_none(record.get("logprob_correct_answer"))
        if value is not None:
            grouped.setdefault((record["model_name"], record["template_id"]), {})[int(record["variant_id"])] = value
    table = {}
    for key, values in grouped.items():
        if len(values) == 4:
            s0 = rc.legacy_slp_repo_clamped(values, 0)
            spread = max(values.values()) - min(values.values())
            table[key] = {"S0": s0, "range": spread, "y_b0": int(s0 >= 0.5), "range_label": int(spread >= 0.5),
                          "mean_logprob": float(np.mean(list(values.values())))}
    return table


def length_audit(token_rows, labels) -> tuple[list[dict], dict[str, Any]]:
    per_family: dict[tuple[str, str], dict[str, Any]] = {}
    for row in token_rows:
        key = (row["model"], row["template_id"])
        per_family.setdefault(key, {"n_answer_tokens": row["n_answer_tokens"],
                                    "n_numeric_answer_tokens": row["n_numeric_answer_tokens"]})
    rows, summary = [], {}
    for model in sorted({k[0] for k in per_family}):
        items = []
        for (m, template_id), info in sorted(per_family.items()):
            if m != model or (m, template_id) not in labels:
                continue
            item = {"model": m, "template_id": template_id, **info, **labels[(m, template_id)]}
            rows.append(item)
            items.append(item)
        n = [i["n_answer_tokens"] for i in items]
        order = sorted(items, key=lambda i: (i["n_answer_tokens"], i["template_id"]))
        tercile = {i["template_id"]: ("short", "medium", "long")[min(2, idx * 3 // len(order))]
                   for idx, i in enumerate(order)}
        by_tercile = {}
        for name in ("short", "medium", "long"):
            group = [i for i in items if tercile[i["template_id"]] == name]
            if not group:
                by_tercile[name] = {"n": 0, "answer_tokens_min_max": None,
                                    "legacy_positive_base0": 0, "range_positive": 0}
                continue
            by_tercile[name] = {
                "n": len(group),
                "answer_tokens_min_max": [min(g["n_answer_tokens"] for g in group),
                                          max(g["n_answer_tokens"] for g in group)],
                "legacy_positive_base0": sum(g["y_b0"] for g in group),
                "range_positive": sum(g["range_label"] for g in group),
            }
        summary[model] = {
            "n_families": len(items),
            "answer_tokens": {"min": min(n), "median": float(np.median(n)), "max": max(n)},
            "spearman_answer_tokens_vs_S0": rc.spearman(n, [i["S0"] for i in items]),
            "spearman_answer_tokens_vs_range": rc.spearman(n, [i["range"] for i in items]),
            "spearman_answer_tokens_vs_mean_logprob": rc.spearman(n, [i["mean_logprob"] for i in items]),
            "by_answer_token_tercile": by_tercile,
        }
    return rows, summary


def pick_manual_cases(records, tokenizers, rb, per_family_csv) -> list[dict]:
    by_template: dict[str, dict[str, Any]] = {}
    for record in records:
        if int(record["variant_id"]) == 0:
            by_template.setdefault(record["template_id"], {})[record["model_name"]] = record
    degraded = sorted(r["template_id"] for r in per_family_csv if r["notes"].startswith("qwen_degraded"))

    def wrong_for_qwen(template_id: str) -> bool:
        rec = by_template[template_id]["Qwen/Qwen2.5-7B-Instruct"]
        parsed = str(rec.get("parsed_answer_canonical") or "").split()
        number = rc.as_float_or_none(parsed[0]) if parsed else None
        target = rc.as_float_or_none(str(rec["correct_answer"]).split()[0])
        return number is None or target is None or abs(number - target) / max(abs(target), 1e-12) > 1e-3

    chosen = {
        "near_match_plan_example": "CM_B_UM_059",
        "frame_or_unit_rendering": next(t for t in sorted(by_template) if t.startswith("CM_C_")),
        "wrong_answer": next(t for t in sorted(by_template) if wrong_for_qwen(t)),
        "parse_failure_degraded": degraded[0],
        "smallest_magnitude_answer": min(
            by_template, key=lambda t: abs(float(str(next(iter(by_template[t].values()))["correct_answer"]).split()[0]))
        ),
        "scientific_notation_answer": next(
            t for t in sorted(by_template)
            if "e" in str(next(iter(by_template[t].values()))["correct_answer"]).split()[0].lower()
        ),
    }
    cases = []
    for label, template_id in chosen.items():
        for model, tok in tokenizers.items():
            record = by_template[template_id][model]
            formatted = rb.format_prompt_with_chat_template(record["prompt"], tok)
            n_prompt = len(tok(formatted, add_special_tokens=True).input_ids)
            answer = str(record["correct_answer"])
            n_answer = len(tok(answer, add_special_tokens=False).input_ids)
            cases.append({
                "case": label, "template_id": template_id, "model": model, "variants": [0, 1, 2, 3],
                "answer": answer, "formatted_prompt_sha256_variant0": sha256_text(formatted),
                "n_prompt_tokens_behavioural_variant0": n_prompt, "n_answer_tokens": n_answer,
                "expected_span_behavioural": sc.answer_span(n_prompt, n_answer),
                "status": "NOT_EVALUATED",
                "reason": "needs a model forward pass (GPU); not authorized or run in Stage 14.3",
            })
    return cases


def summarise(token_rows, wrapper_rows, length_summary) -> dict[str, Any]:
    models = sorted({r["model"] for r in token_rows})
    per_model: dict[str, Any] = {}
    for model in models:
        rows = [r for r in token_rows if r["model"] == model]
        n = len(rows)
        wr = [r for r in wrapper_rows if r["model"] == model]
        per_model[model] = {
            "n_records": n,
            "raw_prompt_equals_rendered_family": sum(r["raw_prompt_equals_rendered_family"] for r in rows),
            "correct_answer_equals_rendered_family": sum(r["correct_answer_equals_rendered_family"] for r in rows),
            "records_with_duplicate_leading_special_token_behavioural": sum(r["leading_bos_behavioural"] > 1 for r in rows),
            "records_with_duplicate_leading_special_token_native": sum(r["leading_bos_native"] > 1 for r in rows),
            "behavioural_ids_equal_extraction_ids": sum(r["behavioural_equals_extraction_ids"] for r in rows),
            "separate_equals_joint_tokenization": sum(r["separate_equals_joint_tokenization"] for r in rows),
            "generation_starts_with_Answer_prefix": sum(r["generation_starts_with_Answer_prefix"] for r in rows),
            "answer_tokens_scored_distribution": {
                str(k): int(v) for k, v in zip(*np.unique([r["n_answer_tokens"] for r in rows], return_counts=True))
            },
            "wrapper_target_tokens_mean": {
                w: float(np.mean([r["n_target_tokens"] for r in wr if r["wrapper_id"] == w]))
                for w in sc.WRAPPERS
            },
            "wrapper_separate_equals_joint": {
                w: [sum(r["separate_equals_joint_tokenization"] for r in wr if r["wrapper_id"] == w),
                    sum(1 for r in wr if r["wrapper_id"] == w)]
                for w in sc.WRAPPERS
            },
            "length_audit": length_summary.get(model),
        }
    checks = []

    def add(code, name, passed, evidence):
        checks.append({"code": code, "name": name, "result": "PASS" if passed else "FAIL", "evidence": evidence})

    total = sum(m["n_records"] for m in per_model.values())
    add("S1", "raw prompt bytes and reference answer equal the rendered family JSON",
        all(m["raw_prompt_equals_rendered_family"] == m["n_records"]
            and m["correct_answer_equals_rendered_family"] == m["n_records"] for m in per_model.values()),
        {k: [m["raw_prompt_equals_rendered_family"], m["n_records"]] for k, m in per_model.items()})
    add("S2", "chat template applied natively with the generation prompt",
        all(r["formatted_ends_with_assistant_opener"] for r in token_rows), f"{total} records")
    add("S3", "no duplicated special token at the start of the scored or generation prompt",
        all(m["records_with_duplicate_leading_special_token_behavioural"] == 0 for m in per_model.values()),
        {k: m["records_with_duplicate_leading_special_token_behavioural"] for k, m in per_model.items()})
    add("S4", "separate tokenization of prompt and answer equals joint tokenization (span is exact)",
        all(m["separate_equals_joint_tokenization"] == m["n_records"] for m in per_model.values()),
        {k: [m["separate_equals_joint_tokenization"], m["n_records"]] for k, m in per_model.items()})
    add("S5", "the scored string is the string the model is instructed to emit",
        False,
        {"scored_string": "the bare reference answer, for example '6.928 N*m'",
         "instructed_format": "Answer: [value] [unit]",
         "generations_starting_with_Answer_prefix": {k: [m["generation_starts_with_Answer_prefix"], m["n_records"]]
                                                      for k, m in per_model.items()}})
    add("S6", "behavioural scoring and activation extraction used identical prompt token ids",
        all(m["behavioural_ids_equal_extraction_ids"] == m["n_records"] for m in per_model.values()),
        {k: [m["behavioural_ids_equal_extraction_ids"], m["n_records"]] for k, m in per_model.items()})
    add("S7", "every wrapper's separate and joint tokenization agree for every family",
        all(a == b for m in per_model.values() for a, b in m["wrapper_separate_equals_joint"].values()),
        {k: {w: v for w, v in m["wrapper_separate_equals_joint"].items() if v[0] != v[1]}
         for k, m in per_model.items()})
    return {"per_model": per_model, "contract_checks": checks}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt-id", default=None)
    parser.add_argument("--out-root", default=OUT_ROOT)
    args = parser.parse_args()

    sha = git("rev-parse", "HEAD")
    day = git("log", "-1", "--format=%cd", "--date=format:%Y%m%d")
    attempt = args.attempt_id or f"attempt_{day}_{sha[:7]}"
    out_dir = (REPO_ROOT / args.out_root / attempt).resolve()
    if out_dir.exists() and any(out_dir.iterdir()):
        print(f"Refusing to reuse non-empty attempt directory: {out_dir}", file=sys.stderr)
        return 2

    import transformers

    rb = load_run_behavioural()
    tokenizers, provenance = load_tokenizers()
    records = read_records()
    rendered = {p.stem: json.loads(p.read_text(encoding="utf-8"))
                for p in (REPO_ROOT / INPUTS["rendered_families"]).glob("*.json") if p.stem != "assembly_summary"}
    token_rows, _ = token_audit(records, tokenizers, rb, rendered)
    wrapper_rows = wrapper_audit(records, tokenizers, rb)
    length_rows, length_summary = length_audit(token_rows, label_table(records))
    with (REPO_ROOT / INPUTS["per_family"]).open(newline="", encoding="utf-8") as handle:
        per_family_csv = list(csv.DictReader(handle))
    cases = pick_manual_cases(records, tokenizers, rb, per_family_csv)
    summary = summarise(token_rows, wrapper_rows, length_summary)

    out_dir.mkdir(parents=True, exist_ok=True)
    for name, rows in (("token_audit.csv", token_rows), ("wrapper_token_counts.csv", wrapper_rows),
                       ("family_length_audit.csv", length_rows)):
        with (out_dir / name).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
    (out_dir / "manual_scoring_cases.json").write_text(json.dumps(cases, indent=2) + "\n", encoding="utf-8")
    result = {
        "stage": "14.3",
        "evidence_class": "scoring-interface audit; tokenizer only; no model forward pass; not paper-eligible",
        "source_commit": sha,
        "git_status_short": git("status", "--short").splitlines(),
        "command": " ".join(sys.argv),
        "python": platform.python_version(),
        "transformers": transformers.__version__,
        "contract_version": sc.CONTRACT_VERSION,
        "contract_fingerprint": sc.contract_fingerprint(),
        "tokenizers": provenance,
        "inputs": {k: INPUTS[k] for k in INPUTS},
        "summary": summary,
        "manual_teacher_forced_scoring": "NOT_EVALUATED (needs a model forward pass; cases in manual_scoring_cases.json)",
    }
    (out_dir / "summary.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    shown = out_dir.relative_to(REPO_ROOT) if out_dir.is_relative_to(REPO_ROOT) else out_dir
    print(json.dumps({"attempt_dir": str(shown),
                      "contract_checks": [(c["code"], c["result"]) for c in summary["contract_checks"]]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
