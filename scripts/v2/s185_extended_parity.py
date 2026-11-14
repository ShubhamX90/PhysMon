#!/usr/bin/env python3
"""G0 item 3 (plan of record, G0 "P0, narrowed" and P0.3a): extended Hugging Face versus TransformerLens parity at the hook
sites and trace lengths G5 will use. Protocol, thresholds and their reasons: docs/registry/v2/g0_extended_parity_protocol.md.

Two subcommands:

* `plan` (login node, CPU, tokenizer only) freezes the inputs for one model: N prompts (default 12), each a chat-templated
  user turn built exactly as the Stage 15 runner builds it (`reasoning_contract_v2.user_turn` + `generation.chat_prompt_ids`)
  followed by one of the SAME model's own sampled reasoning traces from its G2 calibration run. Traces are chosen only by
  length (quantiles 0.05..0.95 of the model's calibration length distribution), never by answer or correctness. Writes
  `data/v2/g0_extended_parity/<model_key>/{plan.json,inputs.jsonl}` (refuses to overwrite); these are committed before any
  GPU job, together with the thresholds below, which `plan.json` fingerprints.
* `run` (GPU job, from an immutable snapshot) verifies the model files against the manifest SHA-256, loads the model once in
  Hugging Face (study dtype bfloat16, default SDPA attention) and once as a TransformerLens HookedTransformer built from the
  same in-memory weights with every weight-processing option off, and compares, per prompt and per layer, the residual
  stream (resid_pre, resid_mid, resid_post), attention output, per-head z (the input of o_proj) and MLP output, and the
  final logits; two reference comparisons measure the noise floor (a second HF SDPA pass: determinism; an HF eager-attention
  pass: the bf16 implementation floor). Two interventions (a residual-stream addition and a per-head z addition) are applied
  identically in both backends to show that the hooks write the claimed tensor at the claimed positions and nowhere else.
  Writes `<output-dir>/<model_key>.json` (refuses to overwrite) with PASS/FAIL per site and overall.

Exit codes of `run`: 0 PASS, 1 FAIL (results written), 2 refusal (existing output, changed plan or thresholds),
3 no GPU, 8 no source commit, 11 model files differ from the manifest, 12 inputs do not re-tokenize identically.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import socket
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.benchmark import reasoning_contract_v2 as rc2  # noqa: E402
from physmon.models import generation as gen  # noqa: E402
from physmon.runtime.workqueue import sha256_file  # noqa: E402
from physmon.utils.paths import expand_model_path  # noqa: E402

SCHEMA = "g0_extended_parity/v1"
PLAN_DIR = "data/v2/g0_extended_parity"
CELLS = "data/v2/dataset/m0_pilot/cells.jsonl"
DATASET_V1 = "data/v2/dataset/v1/dataset.jsonl"
REGISTRY = "docs/model_registry.yml"
MANIFESTS = "docs/model_manifests"
CALIBRATION_RUNS = {"qwen_primary": "results/stage15/s15_cal_qwen25_7b/raw_records.jsonl",
                    "llama_primary": "results/stage15/s15_cal_llama31_8b/raw_records.jsonl"}
EXIT_PASS, EXIT_FAIL, EXIT_REFUSE, EXIT_NO_GPU, EXIT_NO_COMMIT, EXIT_MODEL, EXIT_INPUTS = 0, 1, 2, 3, 8, 11, 12

# --- pre-registered design (fingerprinted in plan.json; changing any of it after `plan` makes `run` refuse) ---------------

# Prompt selection: target trace lengths at these quantiles of the model's own calibration length distribution (all records
# with status OK, any completion status: T1 takes traces "regardless of its answer"). Short (q=0.05), median and long
# (q=0.95) cases are included by construction.
N_PROMPTS_DEFAULT = 12
QUANTILE_LO, QUANTILE_HI = 0.05, 0.95
M0_LENGTH_TOLERANCE = 0.15  # an M0 role-cell structure is used if one of its traces is within 15% of the target length
CELL_TYPE_CYCLE = ("no_cue", "N", "R", "D", "C", "K")

# Sites. TL hook name <-> HF tensor (captured with forward hooks on the HF modules, never via output_hidden_states, whose
# last entry is the final-normed state in transformers 5).
SITES = ("resid_pre", "resid_mid", "resid_post", "attn_out", "z", "mlp_out")
SITE_CLASS = {"resid_pre": "residual", "resid_mid": "residual", "resid_post": "residual",
              "attn_out": "component", "z": "component", "mlp_out": "component"}
TL_HOOK = {"resid_pre": "blocks.{li}.hook_resid_pre", "resid_mid": "blocks.{li}.hook_resid_mid",
           "resid_post": "blocks.{li}.hook_resid_post", "attn_out": "blocks.{li}.hook_attn_out",
           "z": "blocks.{li}.attn.hook_z", "mlp_out": "blocks.{li}.hook_mlp_out"}

# Thresholds. Each metric is an error (larger = worse). A metric passes if value <= allowance, or if value <= FLOOR_MULTIPLIER
# x (the same metric between two correct HF bf16 implementations, SDPA vs eager attention) AND value <= ceiling. The allowance
# is an absolute level at which no mechanism conclusion could change; the floor clause keeps a TL path that is no worse than
# HF's own kernel choice from failing; the ceiling is a hard bug detector no floor can excuse. Reasons: protocol doc.
FLOOR_MULTIPLIER = 3.0
THRESHOLDS: dict[str, dict[str, dict[str, float]]] = {
    "residual": {
        "one_minus_cos_min": {"allowance": 1e-3, "ceiling": 1e-2},   # cosine >= 0.999 at every position (>= 0.99 hard)
        "one_minus_cos_mean": {"allowance": 1e-4, "ceiling": 1e-3},  # mean cosine >= 0.9999 (>= 0.999 hard)
        "rel_l2": {"allowance": 2e-2, "ceiling": 5e-2},              # ||TL-HF|| / ||HF|| over the sequence, worst prompt
    },
    "component": {
        "one_minus_cos_min": {"allowance": 1e-2, "ceiling": 1e-1},   # small-norm outputs after cancellation: looser
        "one_minus_cos_mean": {"allowance": 1e-3, "ceiling": 1e-2},
        "rel_l2": {"allowance": 5e-2, "ceiling": 1.5e-1},
    },
    "logits": {
        "top1_disagreement": {"allowance": 1e-2, "ceiling": 3e-2},   # top-1 agreement >= 0.99 (>= 0.97 hard)
        "kl_mean": {"allowance": 1e-2, "ceiling": 5e-2},             # mean KL(HF||TL) <= 0.01 nats (<= 0.05 hard)
    },
    "intervention_effect": {
        "rel_err": {"allowance": 1e-1, "ceiling": 5e-1},             # ||dTL - dHF|| / ||dHF|| of the intervention effect
    },
}
# Interventions: applied identically in HF (module hooks) and TL (hook points). Direction fixed by a seed; scale from the HF
# clean pass. The window positions are the only ones the hook may change at its site.
INTERVENTIONS = {
    "resid_add": {"site": "resid_post", "layer": "n_layers // 2", "start": "n_prompt // 2", "width": 4,
                  "scale": "1.0 x median L2 norm of HF resid_post at that layer", "scale_factor": 1.0, "seed": 1851,
                  "downstream_site": "resid_post of that layer, read after the hook", "stands_for": "T3 intervention at a quantity's prompt tokens"},
    "head_z_add": {"site": "z", "layer": "n_layers // 2", "head": "n_heads // 2", "start": "n_prompt (first trace token)",
                   "width": 16, "scale": "20 x median L2 norm of HF z of that head", "scale_factor": 20.0, "seed": 1852,
                   "downstream_site": "attn_out of the same layer", "stands_for": "T1 head intervention at answer positions"},
}
EFFECT_EVAL_EXTRA = 64        # effect parity over positions [start, end + 64): where the effect is concentrated
INFORMATIVE_MIN_NATS = 1.0    # the HF effect must move some next-token log-probability by >= 1 nat, else UNINFORMATIVE
DIRECTION_MIN_COS = 0.99      # the change at the downstream site in the window must point where the perturbation predicts
LOGIT_LOCALITY_ABS_TOL = 5e-2  # logits before the window: <= max(2 x rerun noise, 0.05); a leak of a residual-norm push is >> 1
TL_OPTIONS = {
    "fold_ln": False,                    # keep RMSNorm weights separate: activations equal HF's, not a reparameterisation
    "center_writing_weights": False,     # centering changes resid_* by a per-position mean; HF has no such centering
    "center_unembed": False,             # centering W_U shifts logits by a per-position constant; keep HF logits
    "fold_value_biases": False,          # Qwen2 has v biases; folding moves them into b_O and changes hook_z
    "refactor_factored_attn_matrices": False,  # would rotate W_Q/W_K and W_V/W_O bases: hook_z/q/k would differ from HF
    "default_prepend_bos": False,        # inputs are token ids built here; the chat template already holds the BOS
    "n_devices": 1,
    "use_attn_result": False,            # per-head results not materialised (memory); z and attn_out are compared
}


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def design_fingerprint() -> str:
    payload = {"thresholds": THRESHOLDS, "floor_multiplier": FLOOR_MULTIPLIER, "interventions": INTERVENTIONS,
               "effect_eval_extra": EFFECT_EVAL_EXTRA, "informative_min_nats": INFORMATIVE_MIN_NATS,
               "direction_min_cos": DIRECTION_MIN_COS, "logit_locality_abs_tol": LOGIT_LOCALITY_ABS_TOL,
               "tl_options": TL_OPTIONS, "sites": SITES, "site_class": SITE_CLASS,
               "quantiles": [QUANTILE_LO, QUANTILE_HI], "m0_length_tolerance": M0_LENGTH_TOLERANCE,
               "cell_type_cycle": CELL_TYPE_CYCLE}
    return sha256_text(json.dumps(payload, sort_keys=True))


def resolve(path: str | Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else REPO_ROOT / candidate


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def registry_entry(model_key: str) -> dict[str, Any]:
    import yaml

    return yaml.safe_load((REPO_ROOT / REGISTRY).read_text(encoding="utf-8"))["models"][model_key]


def load_manifest(model_key: str, override: str | None) -> tuple[dict[str, Any], Path]:
    path = resolve(override) if override else REPO_ROOT / MANIFESTS / f"{model_key}.json"
    if not path.exists():
        raise SystemExit(f"no manifest for {model_key}: {path}")
    return json.loads(path.read_text(encoding="utf-8")), path


def verify_model_files(model_dir: Path, manifest: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    """Every manifest file present with the recorded size and SHA-256."""

    bad = []
    for entry in manifest["files"]:
        path = model_dir / entry["path"]
        if not path.exists() or path.stat().st_size != entry["size"] or sha256_file(path) != entry["sha256"]:
            bad.append(entry["path"])
    return not bad, {"n_files": len(manifest["files"]), "mismatched": bad}


# --- plan -------------------------------------------------------------------------------------------------------------------

def quantile(sorted_values: list[int], q: float) -> float:
    """Linear-interpolation quantile (numpy's default) of an ascending list."""

    if not sorted_values:
        raise ValueError("empty distribution")
    pos = q * (len(sorted_values) - 1)
    lo, hi = math.floor(pos), math.ceil(pos)
    return sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * (pos - lo)


def select_prompts(records: list[dict[str, Any]], cells: list[dict[str, Any]], n: int) -> tuple[list[dict[str, Any]], dict]:
    """Choose n (trace, prompt) pairs by trace length only. Returns the selections and the length targets.

    Targets are the quantiles linspace(0.05, 0.95, n) of the model's calibration lengths. Longest target first, each structure
    used once: an M0 structure (instance 0, the instance the role cells use) whose trace is within 15% of the target is
    preferred, and the prompt is one of that structure's role cells (cell type cycling no_cue, N, R, D, C, K: the trace is the
    model's own trace under the no-cue control prompt, as in T1 prefix type (ii)); otherwise the closest trace of any unused
    structure is taken with its own calibration prompt. Ties break on (structure_id, instance, sample_index)."""

    ok = [r for r in records if r.get("status") == "OK" and r.get("n_generated_tokens")]
    lengths = sorted(int(r["n_generated_tokens"]) for r in ok)
    qs = [QUANTILE_LO + (QUANTILE_HI - QUANTILE_LO) * i / (n - 1) for i in range(n)] if n > 1 else [0.5]
    targets = [(i, q, quantile(lengths, q)) for i, q in enumerate(qs)]
    cells_by_structure: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for c in cells:
        cells_by_structure.setdefault(c["structure_id"], {}).setdefault(c["cell_id"].split(":")[0], []).append(c)
    used: set[str] = set()
    chosen: dict[int, dict[str, Any]] = {}
    for i, q, target in sorted(targets, key=lambda t: -t[2]):
        def key(r: dict[str, Any], target: float = target) -> tuple:
            return (abs(int(r["n_generated_tokens"]) - target), r["structure_id"], r["instance"], r["sample_index"])

        m0 = [r for r in ok if r["structure_id"] in cells_by_structure and r["instance"] == 0 and r["structure_id"] not in used
              and abs(int(r["n_generated_tokens"]) - target) <= M0_LENGTH_TOLERANCE * target]
        if m0:
            rec = min(m0, key=key)
            types = cells_by_structure[rec["structure_id"]]
            cell_type = next(CELL_TYPE_CYCLE[(i + k) % len(CELL_TYPE_CYCLE)] for k in range(len(CELL_TYPE_CYCLE))
                             if CELL_TYPE_CYCLE[(i + k) % len(CELL_TYPE_CYCLE)] in types)
            cell = sorted(types[cell_type], key=lambda c: c["cell_id"])[0]
            chosen[i] = {"record": rec, "cell": cell, "prompt_source": "m0_role_cell"}
        else:
            rest = [r for r in ok if r["structure_id"] not in used]
            if not rest:
                raise ValueError("not enough distinct structures for the requested number of prompts")
            rec = min(rest, key=key)
            chosen[i] = {"record": rec, "cell": None, "prompt_source": "calibration_own_prompt"}
        used.add(rec["structure_id"])
        chosen[i].update({"quantile": q, "target_tokens": target})
    return [chosen[i] for i in range(n)], {"quantiles": qs, "targets": [t[2] for t in targets], "n_records": len(ok),
                                           "p50": quantile(lengths, 0.5), "p95": quantile(lengths, 0.95),
                                           "max": lengths[-1]}


def cmd_plan(args: argparse.Namespace) -> int:
    out_dir = resolve(args.plan_dir) / args.model_key
    if out_dir.exists() and any(out_dir.iterdir()):
        print(f"Refusing to overwrite an existing plan: {out_dir}", file=sys.stderr)
        return EXIT_REFUSE
    registry = registry_entry(args.model_key)
    manifest, manifest_path = load_manifest(args.model_key, args.manifest)
    model_dir = Path(args.model_path or expand_model_path(registry["path"]))
    records_path = resolve(args.records or CALIBRATION_RUNS[args.model_key])
    cells_path, dataset_path = resolve(args.cells), resolve(args.dataset)
    records, cells = read_jsonl(records_path), read_jsonl(cells_path)
    revisions = {r.get("model_commit") for r in records}
    if revisions != {manifest.get("revision")}:
        print(f"Refusing: calibration records come from model revisions {revisions}, manifest is {manifest.get('revision')}",
              file=sys.stderr)
        return EXIT_REFUSE
    dataset = {r["sample_id"]: r for r in read_jsonl(dataset_path)}
    selections, dist = select_prompts(records, cells, args.n_prompts)

    import transformers

    tokenizer = transformers.AutoTokenizer.from_pretrained(str(model_dir), local_files_only=True, trust_remote_code=False)
    rows = []
    for k, sel in enumerate(selections):
        rec = sel["record"]
        own = dataset[f"{rec['structure_id']}-i{rec['instance']}"]
        own_user = rc2.user_turn(own["problem"], own["answer_unit"])  # the calibration run stated the unit (state_unit)
        if sel["cell"] is not None:
            user = rc2.user_turn(sel["cell"]["prompt"], sel["cell"]["gold_unit"])
        else:
            user = own_user
        prompt_text, prompt_ids = gen.chat_prompt_ids(tokenizer, user, enable_thinking=None)
        trace = rec["generated_answer_raw"]
        trace_ids = list(tokenizer(trace, add_special_tokens=False).input_ids)
        ids = prompt_ids + trace_ids
        rows.append({
            "prompt_id": f"p{k:02d}", "quantile": round(sel["quantile"], 4), "target_tokens": sel["target_tokens"],
            "prompt_source": sel["prompt_source"], "structure_id": rec["structure_id"], "instance": rec["instance"],
            "cell_id": sel["cell"]["cell_id"] if sel["cell"] else "no_cue",
            "cell_job_id": sel["cell"]["job_id"] if sel["cell"] else None,
            "trace_job_id": rec["job_id"], "trace_sample_index": rec["sample_index"],
            "trace_completion_status": rec["completion_status"], "trace_n_generated_tokens": rec["n_generated_tokens"],
            "trace_finish_reason": rec.get("finish_reason"), "trace_under_identical_prompt": user == own_user,
            "user_text": user, "prompt_text_sha256": sha256_text(prompt_text), "trace_text": trace,
            "trace_text_sha256": sha256_text(trace), "n_prompt_tokens": len(prompt_ids), "n_trace_tokens": len(trace_ids),
            "n_tokens": len(ids), "token_ids": ids, "token_ids_sha256": sha256_text(json.dumps(ids)),
        })
    out_dir.mkdir(parents=True)
    inputs = out_dir / "inputs.jsonl"
    inputs.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    plan = {
        "schema": SCHEMA, "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "model_key": args.model_key,
        "model_name": registry["name"], "model_path": registry["path"], "model_revision": manifest.get("revision"),
        "manifest": str(manifest_path.relative_to(REPO_ROOT)) if manifest_path.is_relative_to(REPO_ROOT) else str(manifest_path),
        "manifest_sha256": sha256_file(manifest_path),
        "tokenizer_json_sha256": sha256_file(model_dir / "tokenizer.json") if (model_dir / "tokenizer.json").exists() else None,
        "chat_template_sha256": sha256_text(str(getattr(tokenizer, "chat_template", "") or "")),
        "sources": {str(p.relative_to(REPO_ROOT)) if p.is_relative_to(REPO_ROOT) else str(p): sha256_file(p)
                    for p in (records_path, cells_path, dataset_path)},
        "length_distribution": dist, "n_prompts": len(rows),
        "n_tokens": {"min": min(r["n_tokens"] for r in rows), "max": max(r["n_tokens"] for r in rows),
                     "median": sorted(r["n_tokens"] for r in rows)[len(rows) // 2]},
        "design_fingerprint": design_fingerprint(), "design": json.loads(json.dumps({
            "thresholds": THRESHOLDS, "floor_multiplier": FLOOR_MULTIPLIER, "interventions": INTERVENTIONS,
            "tl_options": TL_OPTIONS, "sites": SITES})),
        "inputs_sha256": sha256_file(inputs), "selection_rule": select_prompts.__doc__,
        "note": "inputs frozen before any GPU result; traces chosen by length only, never by answer or correctness",
    }
    (out_dir / "plan.json").write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"plan_dir": str(out_dir), "n_prompts": len(rows), "n_tokens": plan["n_tokens"],
                      "sources": [r["prompt_source"] for r in rows], "design_fingerprint": plan["design_fingerprint"]},
                     indent=2))
    return EXIT_PASS


# --- metrics (pure torch, testable on CPU) ----------------------------------------------------------------------------------

def _rows(x: Any, site: str) -> Any:
    """[1, pos, ...] -> 2-D rows in float32: (pos, d_model), or (pos * head, d_head) for z."""

    x = x[0] if x.dim() >= 3 else x
    return x.reshape(-1, x.shape[-1]).float()


def site_metrics(ref: Any, test: Any, site: str) -> dict[str, Any]:
    """Cosine per row (position, or position x head for z), relative L2 error and max abs error of test against ref."""

    import torch

    a, b = _rows(ref, site), _rows(test, site)
    if a.shape != b.shape:
        raise ValueError(f"{site}: shape {tuple(a.shape)} != {tuple(b.shape)}")
    na, nb = a.norm(dim=-1), b.norm(dim=-1)
    dot = (a * b).sum(-1)
    cos = dot / (na * nb).clamp_min(1e-30)
    cos = torch.where((na == 0) & (nb == 0), torch.ones_like(cos), cos)
    diff = b - a
    per_pos = ref.shape[-2] if site == "z" else 1  # rows per position
    worst = int(cos.argmin())
    sq_err, sq_ref = float((diff * diff).sum()), float((a * a).sum())
    return {"n": int(cos.numel()), "cos_min": float(cos.min()), "cos_sum": float(cos.double().sum()),
            "worst_position": worst // per_pos, "sq_err": sq_err, "sq_ref": sq_ref,
            "rel_l2": math.sqrt(sq_err / sq_ref) if sq_ref > 0 else (0.0 if sq_err == 0 else math.inf),
            "max_abs": float(diff.abs().max()) if diff.numel() else 0.0}


def logit_metrics(ref: Any, test: Any, chunk: int = 512) -> dict[str, Any]:
    """Top-1 agreement, KL(ref||test) per position (mean, max), max abs logit difference; ref is HF."""

    import torch

    ref, test = (ref[0] if ref.dim() == 3 else ref), (test[0] if test.dim() == 3 else test)
    n, agree, kl_sum, kl_max, max_abs, margin_dis = 0, 0, 0.0, 0.0, 0.0, 0.0
    for s in range(0, ref.shape[0], chunk):
        r, t = ref[s:s + chunk].float(), test[s:s + chunk].float()
        lr, lt = torch.log_softmax(r, -1), torch.log_softmax(t, -1)
        kl = (lr.exp() * (lr - lt)).sum(-1).clamp_min(0)
        same = r.argmax(-1) == t.argmax(-1)
        top2 = r.topk(2, dim=-1).values
        margin = top2[:, 0] - top2[:, 1]
        n += r.shape[0]
        agree += int(same.sum())
        kl_sum += float(kl.double().sum())
        kl_max = max(kl_max, float(kl.max()))
        max_abs = max(max_abs, float((r - t).abs().max()))
        if (~same).any():
            margin_dis = max(margin_dis, float(margin[~same].max()))
    return {"n": n, "n_agree": agree, "top1_agreement": agree / n if n else math.nan, "kl_sum": kl_sum,
            "kl_mean": kl_sum / n if n else math.nan, "kl_max": kl_max, "max_abs": max_abs,
            "max_hf_margin_at_disagreement": margin_dis}


def observed_logprobs(logits: Any, ids: list[int], chunk: int = 512) -> Any:
    """log p(token[t+1] | prefix up to t) for t = 0..T-2, float32 on the logits' device."""

    import torch

    lg = logits[0] if logits.dim() == 3 else logits
    target = torch.tensor(ids[1:], device=lg.device)
    out = []
    for s in range(0, lg.shape[0] - 1, chunk):
        e = min(s + chunk, lg.shape[0] - 1)
        out.append(torch.log_softmax(lg[s:e].float(), -1).gather(-1, target[s:e, None])[:, 0])
    return torch.cat(out)


def pool_sites(per_prompt: list[dict[str, Any]]) -> dict[str, Any]:
    """Pooled over prompts: min cosine (and where), mean cosine over all rows, worst-prompt relative L2, max abs."""

    worst = min(range(len(per_prompt)), key=lambda i: per_prompt[i]["cos_min"])
    n = sum(m["n"] for m in per_prompt)
    return {"cos_min": per_prompt[worst]["cos_min"], "cos_min_prompt": per_prompt[worst]["prompt_id"],
            "cos_min_position": per_prompt[worst]["worst_position"],
            "cos_mean": sum(m["cos_sum"] for m in per_prompt) / n if n else math.nan,
            "rel_l2": max(m["rel_l2"] for m in per_prompt),
            "rel_l2_prompt": max(per_prompt, key=lambda m: m["rel_l2"])["prompt_id"],
            "max_abs": max(m["max_abs"] for m in per_prompt), "n_rows": n, "n_prompts": len(per_prompt)}


def pool_logits(per_prompt: list[dict[str, Any]]) -> dict[str, Any]:
    n = sum(m["n"] for m in per_prompt)
    return {"top1_agreement": sum(m["n_agree"] for m in per_prompt) / n if n else math.nan,
            "kl_mean": sum(m["kl_sum"] for m in per_prompt) / n if n else math.nan,
            "kl_max": max(m["kl_max"] for m in per_prompt), "max_abs": max(m["max_abs"] for m in per_prompt),
            "max_hf_margin_at_disagreement": max(m["max_hf_margin_at_disagreement"] for m in per_prompt),
            "n_positions": n, "n_prompts": len(per_prompt)}


def site_errors(pooled: dict[str, Any]) -> dict[str, float]:
    return {"one_minus_cos_min": 1.0 - pooled["cos_min"], "one_minus_cos_mean": 1.0 - pooled["cos_mean"],
            "rel_l2": pooled["rel_l2"]}


def logit_errors(pooled: dict[str, Any]) -> dict[str, float]:
    return {"top1_disagreement": 1.0 - pooled["top1_agreement"], "kl_mean": pooled["kl_mean"]}


def judge_value(value: float, floor: float | None, allowance: float, ceiling: float,
                multiplier: float = FLOOR_MULTIPLIER) -> dict[str, Any]:
    """PASS if value <= allowance, or value <= multiplier x floor and value <= ceiling; NaN or inf fails."""

    out = {"value": value, "floor": floor, "allowance": allowance, "ceiling": ceiling, "multiplier": multiplier}
    if value is None or not math.isfinite(value):
        return {**out, "pass": False, "by": "not_finite"}
    if value <= allowance:
        return {**out, "pass": True, "by": "allowance"}
    if floor is not None and math.isfinite(floor) and value <= multiplier * floor and value <= ceiling:
        return {**out, "pass": True, "by": "noise_floor"}
    return {**out, "pass": False, "by": "exceeds"}


def judge(errors: dict[str, float], floor_errors: dict[str, float] | None, klass: str) -> dict[str, Any]:
    metrics = {name: judge_value(errors[name], (floor_errors or {}).get(name), lim["allowance"], lim["ceiling"])
               for name, lim in THRESHOLDS[klass].items()}
    return {"pass": all(m["pass"] for m in metrics.values()), "metrics": metrics}


# --- capture ----------------------------------------------------------------------------------------------------------------

def hf_layers(model: Any) -> Any:
    return model.model.layers


def _first(output: Any) -> Any:
    return output[0] if isinstance(output, tuple) else output


class HFRun:
    """One HF forward pass with capture hooks on decoder layers, self_attn, o_proj and mlp, and optional interventions."""

    def __init__(self, model: Any, layers: list[int] | None, sites: tuple[str, ...], n_heads: int,
                 extra_capture: dict[str, tuple[str, int]] | None = None,
                 resid_add: tuple[int, int, int, Any] | None = None, z_add: tuple[int, int, int, int, Any] | None = None):
        self.model, self.sites, self.n_heads = model, sites, n_heads
        n = len(hf_layers(model))
        self.layers = list(range(n)) if layers is None else layers
        self.extra = extra_capture or {}
        self.resid_add, self.z_add = resid_add, z_add
        self.store: dict[str, Any] = {}

    def __call__(self, ids: Any, output_hidden_states: bool = False) -> tuple[Any, dict[str, Any], Any]:
        import torch

        handles = []
        store = self.store
        layers = hf_layers(self.model)
        want = {(site, li) for site in self.sites for li in self.layers}
        want |= {(site, li) for site, li in self.extra.values()}
        try:
            for li, layer in enumerate(layers):
                if ("resid_pre", li) in want or ("resid_mid", li) in want:
                    def pre(module, args, kwargs, li=li):
                        store[f"resid_pre.{li}"] = (args[0] if args else kwargs["hidden_states"]).detach().clone()
                    handles.append(layer.register_forward_pre_hook(pre, with_kwargs=True))
                if ("z", li) in want or (self.z_add and self.z_add[0] == li):
                    def opre(module, args, li=li):
                        x = args[0]
                        if self.z_add and self.z_add[0] == li:
                            _, head, s, e, vec = self.z_add
                            d_head = x.shape[-1] // self.n_heads
                            x = x.clone()
                            x[0, s:e, head * d_head:(head + 1) * d_head] += vec.to(x.dtype)
                        if ("z", li) in want:
                            store[f"z.{li}"] = x.detach().reshape(x.shape[0], x.shape[1], self.n_heads, -1).clone()
                        return (x, *args[1:]) if self.z_add and self.z_add[0] == li else None
                    handles.append(layer.self_attn.o_proj.register_forward_pre_hook(opre))
                if ("attn_out", li) in want or ("resid_mid", li) in want:
                    def attn(module, args, output, li=li):
                        store[f"attn_out.{li}"] = _first(output).detach().clone()
                    handles.append(layer.self_attn.register_forward_hook(attn))
                if ("mlp_out", li) in want:
                    def mlp(module, args, output, li=li):
                        store[f"mlp_out.{li}"] = output.detach().clone()
                    handles.append(layer.mlp.register_forward_hook(mlp))
                if ("resid_post", li) in want or (self.resid_add and self.resid_add[0] == li):
                    def post(module, args, output, li=li):
                        out = _first(output)
                        if self.resid_add and self.resid_add[0] == li:
                            _, s, e, vec = self.resid_add
                            out = out.clone()
                            out[0, s:e] += vec.to(out.dtype)
                        if ("resid_post", li) in want:
                            store[f"resid_post.{li}"] = out.detach().clone()
                        if self.resid_add and self.resid_add[0] == li:
                            return (out, *output[1:]) if isinstance(output, tuple) else out
                        return None
                    handles.append(layer.register_forward_hook(post))
            with torch.inference_mode():
                result = self.model(input_ids=ids, use_cache=False, output_hidden_states=output_hidden_states)
        finally:
            for h in handles:
                h.remove()
        for li in self.layers:
            if "resid_mid" in self.sites:
                store[f"resid_mid.{li}"] = store[f"resid_pre.{li}"] + store[f"attn_out.{li}"]  # HF's own bf16 add
        keep = {f"{site}.{li}" for site, li in want}
        acts = {k: v for k, v in store.items() if k in keep}
        self.store = {}
        return result.logits, acts, getattr(result, "hidden_states", None)


def tl_run(model: Any, ids: Any, layers: list[int] | None, sites: tuple[str, ...],
           extra_capture: dict[str, tuple[str, int]] | None = None, resid_add: tuple[int, int, int, Any] | None = None,
           z_add: tuple[int, int, int, int, Any] | None = None) -> tuple[Any, dict[str, Any]]:
    import torch

    n = model.cfg.n_layers
    layers = list(range(n)) if layers is None else layers
    want = {(site, li) for site in sites for li in layers} | set((extra_capture or {}).values())
    store: dict[str, Any] = {}
    hooks = []
    if resid_add:
        li, s, e, vec = resid_add

        def add_resid(x, hook):
            x = x.clone()
            x[0, s:e] += vec.to(x.dtype)
            return x
        hooks.append((TL_HOOK["resid_post"].format(li=li), add_resid))
    if z_add:
        li, head, s, e, vec = z_add

        def add_z(x, hook):
            x = x.clone()
            x[0, s:e, head] += vec.to(x.dtype)
            return x
        hooks.append((TL_HOOK["z"].format(li=li), add_z))
    for site, li in sorted(want):
        def cap(x, hook, key=f"{site}.{li}"):
            store[key] = x.detach().clone()
        hooks.append((TL_HOOK[site].format(li=li), cap))
    with torch.inference_mode():
        logits = model.run_with_hooks(ids, return_type="logits", fwd_hooks=hooks)
    return logits, store


def set_attn_implementation(model: Any, impl: str) -> None:
    if hasattr(model, "set_attn_implementation"):
        model.set_attn_implementation(impl)
    else:  # pragma: no cover - older transformers
        model.config._attn_implementation = impl


def build_tl(hf_model: Any, tokenizer: Any, model_dir: Path, dtype: Any, device: str, n_ctx: int) -> tuple[Any, dict]:
    """HookedTransformer from the in-memory HF weights, configured from the LOCAL config (no hub lookup). This mirrors
    HookedTransformer.from_pretrained_no_processing step by step; from_pretrained itself needs an official model name and,
    for Qwen2, fetches the config from the hub, which offline compute nodes cannot do."""

    from transformer_lens import HookedTransformer
    from transformer_lens import loading_from_pretrained as loading

    cfg = loading.get_pretrained_model_config(str(model_dir), hf_cfg=hf_model.config.to_dict(), fold_ln=TL_OPTIONS["fold_ln"],
                                              device=device, n_devices=TL_OPTIONS["n_devices"],
                                              default_prepend_bos=TL_OPTIONS["default_prepend_bos"], dtype=dtype, n_ctx=n_ctx)
    state_dict = loading.get_pretrained_state_dict(str(model_dir), cfg, hf_model, dtype=dtype)
    model = HookedTransformer(cfg, tokenizer, move_to_device=False)
    model.load_and_process_state_dict(state_dict, fold_ln=TL_OPTIONS["fold_ln"],
                                      center_writing_weights=TL_OPTIONS["center_writing_weights"],
                                      center_unembed=TL_OPTIONS["center_unembed"],
                                      fold_value_biases=TL_OPTIONS["fold_value_biases"],
                                      refactor_factored_attn_matrices=TL_OPTIONS["refactor_factored_attn_matrices"])
    model.move_model_modules_to_device()
    model.eval()
    del state_dict
    keys = ("model_name", "original_architecture", "n_layers", "d_model", "n_heads", "d_head", "n_key_value_heads", "d_mlp",
            "d_vocab", "n_ctx", "eps", "act_fn", "normalization_type", "positional_embedding_type", "rotary_base",
            "rotary_dim", "rotary_adjacent_pairs", "use_NTK_by_parts_rope", "NTK_by_parts_factor",
            "NTK_by_parts_low_freq_factor", "NTK_by_parts_high_freq_factor", "NTK_original_ctx_len", "gated_mlp",
            "final_rms", "use_attn_result", "use_split_qkv_input", "dtype")
    return model, {k: str(getattr(model.cfg, k, None)) if k == "dtype" else getattr(model.cfg, k, None) for k in keys}


def tl_head_direction(tl_model: Any, layer: int, head: int, vec: Any) -> Any:
    return vec.float() @ tl_model.blocks[layer].attn.W_O[head].float()


def hf_head_direction(hf_model: Any, layer: int, head: int, vec: Any, n_heads: int) -> Any:
    w = hf_layers(hf_model)[layer].self_attn.o_proj.weight
    d_head = w.shape[1] // n_heads
    return w[:, head * d_head:(head + 1) * d_head].float() @ vec.float()


def window_checks(clean: Any, intervened: Any, s: int, e: int, expected: Any, tolerance: float) -> dict[str, Any]:
    """The downstream site changes only inside [s, e), and inside it in the direction the perturbation predicts."""

    import torch

    diff = (intervened[0].float() - clean[0].float())
    outside = torch.cat([diff[:s], diff[e:]])
    out_max = float(outside.abs().max()) if outside.numel() else 0.0
    inside = diff[s:e]
    exp = expected.float().to(inside.device)
    cos = (inside @ exp) / (inside.norm(dim=-1) * exp.norm()).clamp_min(1e-30)
    return {"outside_max_abs": out_max, "tolerance": tolerance, "locality_pass": out_max <= tolerance,
            "inside_min_cos": float(cos.min()), "direction_pass": float(cos.min()) >= DIRECTION_MIN_COS,
            "inside_min_norm": float(inside.norm(dim=-1).min())}


def effect_parity(d_ref: Any, d_test: Any, d_floor: Any, s: int, e: int) -> dict[str, Any]:
    import torch

    stop = min(d_ref.shape[0], e + EFFECT_EVAL_EXTRA)
    a, b, f = d_ref[s:stop].double(), d_test[s:stop].double(), d_floor[s:stop].double()
    norm = float(a.norm())
    rel = float((b - a).norm()) / norm if norm > 0 else math.inf
    rel_floor = float((f - a).norm()) / norm if norm > 0 else math.inf
    corr = float(torch.corrcoef(torch.stack([a, b]))[0, 1]) if a.numel() > 1 else math.nan
    lim = THRESHOLDS["intervention_effect"]["rel_err"]
    informative = float(a.abs().max()) >= INFORMATIVE_MIN_NATS if a.numel() else False
    verdict = judge_value(rel, rel_floor, lim["allowance"], lim["ceiling"])
    return {"eval_range": [s, stop], "hf_max_abs_effect_nats": float(a.abs().max()) if a.numel() else 0.0,
            "informative": informative, "rel_err": rel, "rel_err_floor_eager": rel_floor, "corr": corr,
            "judgement": verdict, "pass": informative and verdict["pass"]}


# --- run --------------------------------------------------------------------------------------------------------------------

def versions() -> dict[str, str | None]:
    import importlib.metadata as md

    out: dict[str, str | None] = {"python": platform.python_version()}
    for p in ("torch", "transformers", "transformer_lens", "tokenizers", "safetensors", "einops"):
        try:
            out[p] = md.version(p)
        except md.PackageNotFoundError:
            out[p] = None
    return out


def compare_prompt(row: dict[str, Any], hf: Any, tl: Any, n_heads: int, device: str, chunk: int) -> dict[str, Any]:
    """Every comparison for one prompt. Returns per-site metrics (tl, floor, rerun), logits and the intervention checks."""

    import torch

    ids_list = row["token_ids"]
    ids = torch.tensor([ids_list], device=device)
    n_layers = len(hf_layers(hf))
    layer, head = n_layers // 2, n_heads // 2
    n_prompt, T = row["n_prompt_tokens"], len(ids_list)
    out: dict[str, Any] = {"prompt_id": row["prompt_id"], "n_tokens": T, "n_prompt_tokens": n_prompt, "sites": {}}
    timings: dict[str, float] = {}

    def timed(name, fn):
        t0 = time.time()
        value = fn()
        if device.startswith("cuda"):
            torch.cuda.synchronize()
        timings[name] = round(time.time() - t0, 3)
        return value

    set_attn_implementation(hf, "sdpa")
    logits_a, acts_a, hidden = timed("hf_sdpa_a", lambda: HFRun(hf, None, SITES, n_heads)(ids, output_hidden_states=True))
    # HF's hidden_states[li] (li < n_layers) must be exactly the hooked resid_pre[li]; hidden_states[n_layers] is final-normed.
    hs_diff = max(float((hidden[li] - acts_a[f"resid_pre.{li}"]).abs().max()) for li in range(n_layers))
    hs_post_diff = max([float((hidden[li + 1] - acts_a[f"resid_post.{li}"]).abs().max()) for li in range(n_layers - 1)] or [0.0])
    out["hf_hidden_states_vs_hooks_max_abs"] = {"resid_pre": hs_diff, "resid_post_except_last": hs_post_diff}
    del hidden

    def compare_all(acts_ref: dict[str, Any], acts_x: dict[str, Any], label: str) -> None:
        for site in SITES:
            for li in range(n_layers):
                key = f"{site}.{li}"
                m = site_metrics(acts_ref[key], acts_x[key], site)
                out["sites"].setdefault(key, {})[label] = {**m, "prompt_id": row["prompt_id"]}

    logits_b, acts_b, _ = timed("hf_sdpa_b", lambda: HFRun(hf, None, SITES, n_heads)(ids))
    compare_all(acts_a, acts_b, "rerun")
    out["logits"] = {"rerun": logit_metrics(logits_a, logits_b, chunk)}
    rerun_site_max = {k: acts_b[k].sub(acts_a[k]).abs().max().item() for k in (f"resid_post.{layer}", f"attn_out.{layer}")}
    rerun_logit_max = out["logits"]["rerun"]["max_abs"]
    del acts_b, logits_b

    set_attn_implementation(hf, "eager")
    logits_e, acts_e, _ = timed("hf_eager", lambda: HFRun(hf, None, SITES, n_heads)(ids))
    compare_all(acts_a, acts_e, "floor")
    out["logits"]["floor"] = logit_metrics(logits_a, logits_e, chunk)
    del acts_e
    set_attn_implementation(hf, "sdpa")

    logits_t, acts_t = timed("tl_a", lambda: tl_run(tl, ids, None, SITES))
    compare_all(acts_a, acts_t, "tl")
    out["logits"]["tl"] = logit_metrics(logits_a, logits_t, chunk)
    tl_clean_sites = {k: acts_t[k] for k in (f"resid_post.{layer}", f"attn_out.{layer}")}
    del acts_t
    logits_t2, acts_t2 = timed("tl_b", lambda: tl_run(tl, ids, [], (), extra_capture={
        "r": ("resid_post", layer), "a": ("attn_out", layer)}))
    tl_rerun_site_max = {k: float((acts_t2[k].float() - tl_clean_sites[k].float()).abs().max()) for k in tl_clean_sites}
    tl_rerun_logit_max = float((logits_t2.float() - logits_t.float()).abs().max())
    out["tl_rerun_max_abs"] = {"logits": tl_rerun_logit_max, **tl_rerun_site_max}
    del logits_t2, acts_t2

    # Interventions (same perturbation in both backends; scale from the HF clean pass).
    lp_a, lp_e, lp_t = (observed_logprobs(x, ids_list, chunk) for x in (logits_a, logits_e, logits_t))
    del logits_e
    g = torch.Generator().manual_seed(INTERVENTIONS["resid_add"]["seed"])
    u = torch.randn(acts_a[f"resid_post.{layer}"].shape[-1], generator=g)
    u = u / u.norm()
    scale_r = float(acts_a[f"resid_post.{layer}"][0].float().norm(dim=-1).median()) * INTERVENTIONS["resid_add"]["scale_factor"]
    vec_r = (u * scale_r).to(device)
    s_r = n_prompt // 2
    e_r = min(s_r + INTERVENTIONS["resid_add"]["width"], T - 1)
    g = torch.Generator().manual_seed(INTERVENTIONS["head_z_add"]["seed"])
    uz = torch.randn(acts_a[f"z.{layer}"].shape[-1], generator=g)
    uz = uz / uz.norm()
    scale_z = float(acts_a[f"z.{layer}"][0, :, head].float().norm(dim=-1).median()) * INTERVENTIONS["head_z_add"]["scale_factor"]
    vec_z = (uz * scale_z).to(device)
    s_z = n_prompt
    e_z = min(s_z + INTERVENTIONS["head_z_add"]["width"], T - 1)
    if not (0 < s_r < e_r and 0 < s_z < e_z):
        raise ValueError(f"intervention windows empty for T={T}, n_prompt={n_prompt}")
    hf_clean_sites = {k: acts_a[k] for k in (f"resid_post.{layer}", f"attn_out.{layer}")}
    del acts_a
    specs = {
        "resid_add": {"hf": {"resid_add": (layer, s_r, e_r, vec_r)}, "tl": {"resid_add": (layer, s_r, e_r, vec_r)},
                      "window": (s_r, e_r), "site": f"resid_post.{layer}", "capture": ("resid_post", layer),
                      "expected_hf": vec_r, "expected_tl": vec_r, "scale": scale_r},
        "head_z_add": {"hf": {"z_add": (layer, head, s_z, e_z, vec_z)}, "tl": {"z_add": (layer, head, s_z, e_z, vec_z)},
                       "window": (s_z, e_z), "site": f"attn_out.{layer}", "capture": ("attn_out", layer),
                       "expected_hf": hf_head_direction(hf, layer, head, vec_z, n_heads),
                       "expected_tl": tl_head_direction(tl, layer, head, vec_z), "scale": scale_z},
    }
    out["interventions"] = {}
    for name, sp in specs.items():
        s, e = sp["window"]
        key = sp["site"]
        lg_h, ac_h, _ = timed(f"hf_{name}", lambda sp=sp: HFRun(hf, [], (), n_heads, extra_capture={"x": sp["capture"]},
                                                                  **sp["hf"])(ids))
        set_attn_implementation(hf, "eager")
        lg_he, _, _ = timed(f"hf_eager_{name}", lambda sp=sp: HFRun(hf, [], (), n_heads, **sp["hf"])(ids))
        set_attn_implementation(hf, "sdpa")
        lg_t, ac_t = timed(f"tl_{name}", lambda sp=sp: tl_run(tl, ids, [], (), extra_capture={"x": sp["capture"]}, **sp["tl"]))
        res: dict[str, Any] = {"layer": layer, "head": head if name == "head_z_add" else None, "window": [s, e],
                               "scale": sp["scale"], "downstream_site": key}
        res["hf_site"] = window_checks(hf_clean_sites[key], ac_h[key], s, e, sp["expected_hf"], 2 * rerun_site_max[key])
        res["tl_site"] = window_checks(tl_clean_sites[key], ac_t[key], s, e, sp["expected_tl"], 2 * tl_rerun_site_max[key])
        hf_before = float((lg_h[0, :s].float() - logits_a[0, :s].float()).abs().max())
        tl_before = float((lg_t[0, :s].float() - logits_t[0, :s].float()).abs().max())
        tol_h = max(2 * rerun_logit_max, LOGIT_LOCALITY_ABS_TOL)
        tol_t = max(2 * tl_rerun_logit_max, LOGIT_LOCALITY_ABS_TOL)
        res["hf_logits_before_window"] = {"max_abs": hf_before, "tolerance": tol_h, "pass": hf_before <= tol_h}
        res["tl_logits_before_window"] = {"max_abs": tl_before, "tolerance": tol_t, "pass": tl_before <= tol_t}
        d_h = observed_logprobs(lg_h, ids_list, chunk) - lp_a
        d_he = observed_logprobs(lg_he, ids_list, chunk) - lp_e
        d_t = observed_logprobs(lg_t, ids_list, chunk) - lp_t
        res["effect"] = effect_parity(d_h, d_t, d_he, s, e)
        res["pass"] = bool(res["hf_site"]["locality_pass"] and res["hf_site"]["direction_pass"]
                           and res["tl_site"]["locality_pass"] and res["tl_site"]["direction_pass"]
                           and res["hf_logits_before_window"]["pass"] and res["tl_logits_before_window"]["pass"]
                           and res["effect"]["pass"])
        out["interventions"][name] = res
        del lg_h, ac_h, lg_he, lg_t, ac_t
    out["timings_s"] = timings
    return out


def aggregate(prompts: list[dict[str, Any]], n_layers: int) -> dict[str, Any]:
    ok = [p for p in prompts if "error" not in p]
    if not ok:  # zero evaluable prompts is a FAIL, never a measured parity
        return {"sites": {}, "logits": {}, "interventions": {}, "hf_hidden_states_vs_hooks_exact": None,
                "site_pass_counts": {}, "overall": "FAIL",
                "failures": ["no_evaluable_prompts", *[f"prompt_error.{p['prompt_id']}" for p in prompts]]}
    sites: dict[str, list[dict[str, Any]]] = {}
    for site in SITES:
        rows = []
        for li in range(n_layers):
            key = f"{site}.{li}"
            pooled = {label: pool_sites([p["sites"][key][label] for p in ok]) for label in ("tl", "floor", "rerun")}
            verdict = judge(site_errors(pooled["tl"]), site_errors(pooled["floor"]), SITE_CLASS[site])
            rows.append({"layer": li, **pooled, "judgement": verdict, "pass": verdict["pass"]})
        sites[site] = rows
    logits = {label: pool_logits([p["logits"][label] for p in ok]) for label in ("tl", "floor", "rerun")}
    logits["judgement"] = judge(logit_errors(logits["tl"]), logit_errors(logits["floor"]), "logits")
    logits["pass"] = logits["judgement"]["pass"]
    interventions = {name: {"pass": all(p["interventions"][name]["pass"] for p in ok),
                            "failed_prompts": [p["prompt_id"] for p in ok if not p["interventions"][name]["pass"]],
                            "uninformative_prompts": [p["prompt_id"] for p in ok
                                                      if not p["interventions"][name]["effect"]["informative"]]}
                     for name in INTERVENTIONS}
    hidden_ok = all(p["hf_hidden_states_vs_hooks_max_abs"]["resid_pre"] == 0.0 for p in ok)
    failures = [f"{site}.{r['layer']}" for site, rows in sites.items() for r in rows if not r["pass"]]
    failures += ["logits"] if not logits["pass"] else []
    failures += [f"intervention.{n}" for n, v in interventions.items() if not v["pass"]]
    failures += ["hf_hidden_states_vs_hooks"] if not hidden_ok else []
    failures += [f"prompt_error.{p['prompt_id']}" for p in prompts if "error" in p]
    failures += ["no_evaluable_prompts"] if not ok else []
    return {"sites": sites, "logits": logits, "interventions": interventions, "hf_hidden_states_vs_hooks_exact": hidden_ok,
            "site_pass_counts": {site: sum(r["pass"] for r in rows) for site, rows in sites.items()},
            "failures": failures, "overall": "PASS" if not failures else "FAIL"}


def compact_prompt(p: dict[str, Any]) -> dict[str, Any]:
    """Per-prompt record without the per-site arrays (those are pooled); keeps logits, interventions, timings."""

    return {k: v for k, v in p.items() if k != "sites"}


def cmd_run(args: argparse.Namespace) -> int:
    started = time.time()
    out_path = resolve(args.output_dir) / f"{args.model_key}.json"
    if out_path.exists():
        print(f"Refusing to overwrite: {out_path}", file=sys.stderr)
        return EXIT_REFUSE
    source_commit = os.environ.get("PHYSMON_SOURCE_COMMIT", "")
    if not source_commit:
        print("Refusing: PHYSMON_SOURCE_COMMIT is not set (run from a snapshot of a pushed commit).", file=sys.stderr)
        return EXIT_NO_COMMIT
    plan_dir = resolve(args.plan_dir) / args.model_key
    plan = json.loads((plan_dir / "plan.json").read_text(encoding="utf-8"))
    if plan["design_fingerprint"] != design_fingerprint():
        print("Refusing: thresholds or design changed since the plan was frozen "
              f"({plan['design_fingerprint']} != {design_fingerprint()})", file=sys.stderr)
        return EXIT_REFUSE
    if sha256_file(plan_dir / "inputs.jsonl") != plan["inputs_sha256"]:
        print("Refusing: inputs.jsonl does not match plan.json", file=sys.stderr)
        return EXIT_REFUSE
    rows = read_jsonl(plan_dir / "inputs.jsonl")
    if args.max_prompts:
        rows = rows[: args.max_prompts]

    import torch

    if args.device.startswith("cuda") and not torch.cuda.is_available():
        print("Refusing: a CUDA device was requested but none is available.", file=sys.stderr)
        return EXIT_NO_GPU
    registry = registry_entry(args.model_key)
    manifest, manifest_path = load_manifest(args.model_key, args.manifest)
    if sha256_file(manifest_path) != plan["manifest_sha256"]:
        print("Refusing: the manifest changed since the plan was frozen", file=sys.stderr)
        return EXIT_REFUSE
    model_dir = Path(args.model_path or expand_model_path(registry["path"]))
    header: dict[str, Any] = {"event": "start", "model_key": args.model_key, "model_dir": str(model_dir),
                              "host": socket.gethostname(), "slurm_job_id": os.environ.get("SLURM_JOB_ID", ""),
                              "source_commit": source_commit, "versions": versions()}
    print(json.dumps(header), flush=True)
    if args.skip_model_hash:
        files_report: dict[str, Any] = {"verified": False, "reason": "--skip-model-hash (tests only)"}
    else:
        t0 = time.time()
        ok, files_report = verify_model_files(model_dir, manifest)
        files_report["seconds"] = round(time.time() - t0, 1)
        print(json.dumps({"event": "model_hash", "ok": ok, **files_report}), flush=True)
        if not ok:
            print(f"Refusing: model files differ from the manifest: {files_report['mismatched'][:5]}", file=sys.stderr)
            return EXIT_MODEL
        files_report["verified"] = True

    import transformers

    dtype = getattr(torch, args.dtype)
    tokenizer = transformers.AutoTokenizer.from_pretrained(str(model_dir), local_files_only=True, trust_remote_code=False)
    for row in rows:  # inputs must re-tokenize to exactly the frozen ids (tokenizer or template drift fails closed)
        _, prompt_ids = gen.chat_prompt_ids(tokenizer, row["user_text"], enable_thinking=None)
        ids = prompt_ids + list(tokenizer(row["trace_text"], add_special_tokens=False).input_ids)
        if ids != row["token_ids"]:
            print(f"Refusing: {row['prompt_id']} does not re-tokenize to the frozen ids", file=sys.stderr)
            return EXIT_INPUTS
    t0 = time.time()
    hf = transformers.AutoModelForCausalLM.from_pretrained(str(model_dir), local_files_only=True, trust_remote_code=False,
                                                           dtype=dtype)
    hf.to(args.device)
    hf.eval()
    hf_load_s = round(time.time() - t0, 1)
    attn_default = getattr(hf.config, "_attn_implementation", None)
    n_ctx = max(2048, max(r["n_tokens"] for r in rows))
    t0 = time.time()
    tl, tl_cfg = build_tl(hf, tokenizer, model_dir, dtype, args.device, n_ctx)
    tl_load_s = round(time.time() - t0, 1)
    n_heads = hf.config.num_attention_heads
    n_layers = len(hf_layers(hf))
    print(json.dumps({"event": "loaded", "hf_load_s": hf_load_s, "tl_load_s": tl_load_s, "attn_default": attn_default,
                      "tl_cfg": tl_cfg}, default=str), flush=True)

    prompts = []
    for row in rows:
        t0 = time.time()
        try:
            result = compare_prompt(row, hf, tl, n_heads, args.device, args.chunk)
        except Exception as exc:  # recorded, never dropped: the run then FAILS
            result = {"prompt_id": row["prompt_id"], "n_tokens": row["n_tokens"], "error": repr(exc)[:1000]}
            if args.device.startswith("cuda"):
                torch.cuda.empty_cache()
        result["seconds"] = round(time.time() - t0, 1)
        for k in ("structure_id", "cell_id", "prompt_source", "trace_job_id", "trace_completion_status", "quantile",
                  "token_ids_sha256", "n_trace_tokens"):
            result[k] = row[k]
        prompts.append(result)
        brief = {"event": "prompt_done", "prompt_id": row["prompt_id"], "n_tokens": row["n_tokens"],
                 "seconds": result["seconds"], "error": result.get("error")}
        if "logits" in result:
            brief["top1_tl"] = result["logits"]["tl"]["top1_agreement"]
            brief["kl_tl"] = result["logits"]["tl"]["kl_mean"]
        print(json.dumps(brief), flush=True)

    summary = aggregate(prompts, n_layers)
    evaluated = [p for p in prompts if "error" not in p]
    report = {
        "schema": SCHEMA, "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "model_key": args.model_key,
        "model_name": registry["name"], "model_revision": manifest.get("revision"), "model_dir": str(model_dir),
        "manifest_sha256": sha256_file(manifest_path), "model_files": files_report, "source_commit": source_commit,
        "slurm_job_id": os.environ.get("SLURM_JOB_ID", ""), "partition": os.environ.get("SLURM_JOB_PARTITION", ""),
        "authorization_ref": os.environ.get("AUTHORIZATION_REF", ""), "host": socket.gethostname(), "device": args.device,
        "gpu_name": torch.cuda.get_device_name(0) if args.device.startswith("cuda") else "cpu", "dtype": args.dtype,
        "versions": versions(), "hf_attn_implementation": {"default": attn_default, "study": "sdpa", "floor": "eager"},
        "torch_flags": {"matmul_allow_tf32": torch.backends.cuda.matmul.allow_tf32,
                        "bf16_reduced_precision_reduction": torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction},
        "tl_options": TL_OPTIONS, "tl_cfg": tl_cfg, "tl_n_ctx": n_ctx, "plan_sha256": sha256_file(plan_dir / "plan.json"),
        "inputs_sha256": plan["inputs_sha256"], "design_fingerprint": design_fingerprint(), "thresholds": THRESHOLDS,
        "floor_multiplier": FLOOR_MULTIPLIER, "interventions_spec": INTERVENTIONS,
        "n_prompts_planned": len(rows), "n_prompts_evaluated": len(evaluated),
        "parity_valid_up_to_tokens": max((p["n_tokens"] for p in evaluated), default=0),
        "load_seconds": {"hf": hf_load_s, "tl": tl_load_s},
        "peak_gpu_gb": round(torch.cuda.max_memory_allocated() / 1e9, 1) if args.device.startswith("cuda") else None,
        **summary, "prompts": [compact_prompt(p) for p in prompts], "elapsed_s": round(time.time() - started, 1),
        "note": "infrastructure evidence (G0 item 3), not scientific evidence; a FAIL bars mechanism work on this model and "
                "backend, behaviour may proceed",
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("x", encoding="utf-8") as handle:  # exclusive create: never overwrite
        handle.write(json.dumps(report, indent=1, sort_keys=True, default=str) + "\n")
    print(json.dumps({"event": "done", "overall": report["overall"], "failures": report["failures"][:20],
                      "n_failures": len(report["failures"]), "output": str(out_path), "elapsed_s": report["elapsed_s"]}),
          flush=True)
    return EXIT_PASS if report["overall"] == "PASS" else EXIT_FAIL


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("plan")
    p.add_argument("--model-key", required=True, choices=sorted(CALIBRATION_RUNS))
    p.add_argument("--plan-dir", default=PLAN_DIR)
    p.add_argument("--n-prompts", type=int, default=N_PROMPTS_DEFAULT)
    p.add_argument("--cells", default=CELLS)
    p.add_argument("--dataset", default=DATASET_V1)
    p.add_argument("--records", default=None, help="override the calibration records (tests only)")
    p.add_argument("--model-path", default=None, help="override the registry path (tests only)")
    p.add_argument("--manifest", default=None, help="override the manifest path (tests only)")
    r = sub.add_parser("run")
    r.add_argument("--model-key", required=True, choices=sorted(CALIBRATION_RUNS))
    r.add_argument("--plan-dir", default=PLAN_DIR)
    r.add_argument("--output-dir", required=True)
    r.add_argument("--device", default="cuda")
    r.add_argument("--dtype", default="bfloat16", help="the study dtype; float32 only for CPU tests")
    r.add_argument("--chunk", type=int, default=512, help="positions per chunk for log-softmax/KL")
    r.add_argument("--max-prompts", type=int, default=None, help="tests only")
    r.add_argument("--model-path", default=None, help="override the registry path (tests only)")
    r.add_argument("--manifest", default=None, help="override the manifest path (tests only)")
    r.add_argument("--skip-model-hash", action="store_true", help="tests only")
    args = parser.parse_args(argv)
    return {"plan": cmd_plan, "run": cmd_run}[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
