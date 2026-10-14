"""Smoke-test registry models the way PhysMon scripts actually use them.

Two phases, run separately so the CPU phase can run on the login node:

  cpu  Paths, manifest, safetensors headers, config vs registry, the real chat tokenizer
       and prompt formatting from scripts/run_behavioural.py, cue-token lookup, architecture
       instantiation on the meta device (no weights), and TransformerLens name support.
  gpu  Loads each model through physmon.models.loader.load_model exactly as the experiment
       scripts do, then checks greedy generation, answer parsing, reference-answer
       log-probability, hook points, and (TransformerLens models) activation extraction and
       Hugging Face versus TransformerLens logit parity.

Diagnostic only: results are infrastructure evidence, not scientific evidence. One JSON
file per model and phase is written to --output-dir, plus a summary. A failing check does
not stop the run; the exit code is non-zero if any check failed.
"""

from __future__ import annotations

import argparse
import gc
import importlib.util
import json
import math
import struct
import sys
import time
import traceback
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

DEFAULT_FAMILY = REPO_ROOT / "data" / "generated" / "CM_B_001.json"
CHAT_MARKERS = {"qwen": "<|im_start|>", "llama": "<|start_header_id|>", "mistral": "[INST]"}
SAFETENSORS_DTYPE_BYTES = {
    "F64": 8, "F32": 4, "BF16": 2, "F16": 2, "I64": 8, "I32": 4, "I16": 2, "I8": 1,
    "U8": 1, "F8_E4M3": 1, "F8_E5M2": 1, "BOOL": 1,
}


class Report:
    """Collect named checks for one model and phase."""

    def __init__(self, model_key: str, phase: str) -> None:
        self.model_key = model_key
        self.phase = phase
        self.checks: list[dict[str, Any]] = []
        self.facts: dict[str, Any] = {}

    def check(self, name: str, ok: bool, detail: Any = None, severity: str = "hard") -> bool:
        self.checks.append({"name": name, "ok": bool(ok), "severity": severity, "detail": detail})
        marker = "PASS" if ok else ("FAIL" if severity == "hard" else "WARN")
        print(f"  [{marker}] {name}: {detail}", flush=True)
        return bool(ok)

    def guarded(self, name: str, func: Any, severity: str = "hard") -> Any:
        """Run func; record an exception as a failed check instead of aborting."""

        try:
            return func()
        except Exception as error:  # noqa: BLE001 - smoke test must survive any failure
            detail = f"{type(error).__name__}: {str(error)[:300]}"
            self.check(name, False, detail, severity)
            self.facts.setdefault("tracebacks", {})[name] = traceback.format_exc()[-1500:]
            return None

    @property
    def passed(self) -> bool:
        return all(c["ok"] for c in self.checks if c["severity"] == "hard")


def load_run_behavioural() -> Any:
    spec = importlib.util.spec_from_file_location(
        "run_behavioural_for_smoke", REPO_ROOT / "scripts" / "run_behavioural.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_family(path: Path) -> dict[str, Any]:
    family = json.loads(path.read_text(encoding="utf-8"))
    return family


def safetensors_summary(model_dir: Path) -> dict[str, Any]:
    """Read every safetensors header (never the tensor data) and cross-check the index."""

    files = sorted(model_dir.glob("*.safetensors"))
    tensors: dict[str, str] = {}
    total_params = 0
    dtypes: dict[str, int] = {}
    for file in files:
        with file.open("rb") as handle:
            (header_len,) = struct.unpack("<Q", handle.read(8))
            header = json.loads(handle.read(header_len))
        header.pop("__metadata__", None)
        data_end = 0
        for name, info in header.items():
            numel = math.prod(info["shape"]) if info["shape"] else 1
            total_params += numel
            dtypes[info["dtype"]] = dtypes.get(info["dtype"], 0) + 1
            tensors[name] = file.name
            data_end = max(data_end, info["data_offsets"][1])
        expected = 8 + header_len + data_end
        if file.stat().st_size != expected:
            raise ValueError(f"{file.name}: size {file.stat().st_size} != header-implied {expected}")
    index_path = model_dir / "model.safetensors.index.json"
    missing_from_index = []
    if index_path.exists():
        weight_map = json.loads(index_path.read_text())["weight_map"]
        missing_from_index = sorted(set(weight_map) - set(tensors))
    return {
        "files": len(files),
        "tensors": len(tensors),
        "total_elements": total_params,
        "dtype_counts": dtypes,
        "index_entries_without_tensor": missing_from_index[:5],
        "index_missing_count": len(missing_from_index),
    }


def cpu_phase(model_key: str, family: dict[str, Any], rb: Any, out: Path) -> Report:
    import torch
    from transformers import AutoConfig, AutoModelForCausalLM

    from physmon.models.hooks import find_cue_token_index
    from physmon.models.loader import resolve_model_spec

    report = Report(model_key, "cpu")
    print(f"=== CPU checks: {model_key}", flush=True)
    spec = resolve_model_spec(model_key=model_key)
    model_dir = Path(spec.path)
    report.facts.update({"repo_id": spec.name, "path": spec.path, "backend": spec.hook_backend})

    report.check("model_dir_exists", model_dir.is_dir(), spec.path)
    manifest = REPO_ROOT / "docs" / "model_manifests" / f"{model_key}.json"
    manifest_data = json.loads(manifest.read_text()) if manifest.exists() else None
    report.check("manifest_present", manifest_data is not None, str(manifest.name))
    if manifest_data:
        on_disk = {
            f.relative_to(model_dir).as_posix()
            for f in model_dir.rglob("*")
            if f.is_file() and ".cache" not in f.relative_to(model_dir).parts
        }
        listed = {entry["path"] for entry in manifest_data["files"]}
        report.check(
            "files_match_manifest",
            listed <= on_disk,
            f"{len(listed)} manifest files, missing={sorted(listed - on_disk)[:3]}",
        )
        report.facts["revision"] = manifest_data["revision"]

    summary = report.guarded("safetensors_headers", lambda: safetensors_summary(model_dir))
    if summary is not None:
        report.facts["safetensors"] = summary
        report.check(
            "safetensors_consistent",
            summary["index_missing_count"] == 0 and summary["tensors"] > 0,
            f"{summary['files']} files, {summary['tensors']} tensors, dtypes={summary['dtype_counts']}",
        )

    config = report.guarded(
        "config_loads", lambda: AutoConfig.from_pretrained(spec.path, local_files_only=True)
    )
    if config is not None:
        text = config.get_text_config() if hasattr(config, "get_text_config") else config
        layers, hidden = getattr(text, "num_hidden_layers", None), getattr(text, "hidden_size", None)
        report.facts.update({"num_layers": layers, "hidden_size": hidden, "model_type": config.model_type})
        report.check("config_loads", True, f"{config.model_type}, layers={layers}, hidden={hidden}")
        for key, got in (("num_layers", layers), ("hidden_dim", hidden)):
            expected = getattr(spec, key)
            if expected is not None:
                report.check(f"registry_{key}_matches_config", expected == got, f"registry={expected} config={got}")

    tokenizer = report.guarded(
        "chat_tokenizer_loads", lambda: rb.load_chat_tokenizer(spec.path, spec.name)
    )
    variant = family["variants"][0]
    if tokenizer is not None:
        prompt = rb.format_prompt_with_chat_template(variant["prompt"], tokenizer)
        marker = CHAT_MARKERS.get(spec.family)
        report.check("chat_tokenizer_loads", True, f"vocab={len(tokenizer)} pad={tokenizer.pad_token!r}")
        report.check(
            "chat_template_markers",
            marker is None or marker in prompt,
            f"family={spec.family} marker={marker!r} prefix={prompt[:60]!r}",
        )
        ids = tokenizer(prompt, add_special_tokens=True).input_ids
        report.facts["prompt_tokens"] = len(ids)
        cue_index = report.guarded(
            "cue_token_lookup",
            lambda: find_cue_token_index(prompt, variant["cue_sentence"], tokenizer),
        )
        if cue_index is not None:
            report.check(
                "cue_token_lookup",
                0 <= cue_index < len(ids),
                f"index={cue_index} of {len(ids)}, token={tokenizer.decode(ids[cue_index])!r}",
            )

    def meta_instantiate() -> dict[str, Any]:
        with torch.device("meta"):
            model = AutoModelForCausalLM.from_config(config)
        params = sum(p.numel() for p in model.parameters())
        return {"class": type(model).__name__, "parameters": params}

    if config is not None:
        meta = report.guarded("architecture_instantiates_on_meta", meta_instantiate)
        if meta is not None:
            report.facts["meta_model"] = meta
            stored = (summary or {}).get("total_elements")
            detail = f"{meta['class']}, {meta['parameters']/1e9:.2f}B params"
            if stored:
                detail += f", stored elements {stored/1e9:.2f}B"
            report.check("architecture_instantiates_on_meta", True, detail)

    if spec.hook_backend == "transformer_lens" and config is not None:
        def tl_support() -> dict[str, Any]:
            from transformer_lens.loading_from_pretrained import (
                get_official_model_name,
                get_pretrained_model_config,
            )

            official = get_official_model_name(spec.name)
            tl_cfg = get_pretrained_model_config(official, hf_cfg=config.to_dict(), fold_ln=False)
            return {"official": official, "n_layers": tl_cfg.n_layers, "d_model": tl_cfg.d_model,
                    "n_heads": tl_cfg.n_heads}

        tl = report.guarded("transformer_lens_supports_model", tl_support)
        if tl is not None:
            report.facts["transformer_lens"] = tl
            report.check(
                "transformer_lens_supports_model",
                tl["n_layers"] == report.facts.get("num_layers") and tl["d_model"] == report.facts.get("hidden_size"),
                tl,
            )
    (out / f"{model_key}.cpu.json").write_text(
        json.dumps({"checks": report.checks, "facts": report.facts, "passed": report.passed}, indent=2, default=str)
    )
    return report


def gpu_phase(model_key: str, family: dict[str, Any], rb: Any, out: Path, device: str, max_new_tokens: int) -> Report:
    import torch

    from physmon.benchmark.parser import parse_answer
    from physmon.models.hooks import extract_targeted_activations, find_cue_token_index
    from physmon.models.loader import load_model, resolve_model_spec
    from physmon.models.logprob import compute_reference_answer_logprob

    report = Report(model_key, "gpu")
    print(f"=== GPU checks: {model_key}", flush=True)
    spec = resolve_model_spec(model_key=model_key)
    report.facts.update({"repo_id": spec.name, "backend": spec.hook_backend, "gpu": torch.cuda.get_device_name(0)})
    variant = family["variants"][0]

    started = time.time()
    # Mirrors scripts/extract_activations.py and run_causal_patching.py.
    device_map = "auto" if spec.hook_backend != "transformer_lens" else None
    bundle = report.guarded("load_model", lambda: load_model(model_key=model_key, device=device, device_map=device_map))
    if bundle is None:
        return _finish(report, out, "gpu")
    load_seconds = round(time.time() - started, 1)
    first_param = next(bundle.hf_model.parameters())
    report.facts.update({"load_seconds": load_seconds, "dtype": str(first_param.dtype), "param_device": str(first_param.device)})
    report.check("load_model", True, f"{load_seconds}s dtype={first_param.dtype} device={first_param.device} backend={bundle.backend}")

    tokenizer = bundle.tokenizer
    if tokenizer.pad_token is None and tokenizer.eos_token is not None:
        tokenizer.pad_token = tokenizer.eos_token
    prompt = rb.format_prompt_with_chat_template(variant["prompt"], tokenizer)

    completion = report.guarded("greedy_generation", lambda: rb.generate_completion(bundle, prompt, max_new_tokens))
    if completion is not None:
        report.check(
            "greedy_generation",
            isinstance(completion, str) and len(completion.strip()) > 0,
            f"{len(completion)} chars; head={completion[:90]!r}",
        )
        parsed = parse_answer(completion)
        report.facts["parsed_answer"] = parsed.answer
        report.check(
            "answer_parseable",
            parsed.answer is not None,
            f"parsed={parsed.answer!r} expected={variant['correct_answer']!r} (informational)",
            severity="soft",
        )

    logprob = report.guarded(
        "reference_answer_logprob",
        lambda: compute_reference_answer_logprob(bundle, prompt, variant["correct_answer"]),
    )
    if logprob is not None:
        report.facts["reference_logprob"] = logprob
        report.check("reference_answer_logprob", math.isfinite(logprob) and logprob < 0, f"{logprob:.3f}")

    n_layers = report.facts.get("num_layers") or bundle.hf_model.config.get_text_config().num_hidden_layers
    layer = min(16, n_layers - 1)

    def hook_points() -> dict[str, Any]:
        if bundle.hooked_model is not None:
            names = set(bundle.hooked_model.hook_dict)
            needed = [f"blocks.{layer}.hook_resid_post", f"blocks.{layer}.attn.hook_z"]
            return {"kind": "transformer_lens", "needed": needed, "present": [n in names for n in needed]}
        blocks = bundle.hf_model.model.layers  # HF fallback path used for DeepSeek causal scripts
        return {"kind": "hf_modules", "o_proj": hasattr(blocks[layer].self_attn, "o_proj"),
                "n_blocks": len(blocks), "present": [hasattr(blocks[layer].self_attn, "o_proj")]}

    points = report.guarded("hook_points_present", hook_points)
    if points is not None:
        report.check("hook_points_present", all(points["present"]), points)

    if bundle.hooked_model is not None:
        def activations() -> dict[str, Any]:
            ids = tokenizer(prompt, return_tensors="pt", add_special_tokens=True).input_ids
            cue_index = find_cue_token_index(prompt, variant["cue_sentence"], tokenizer)
            states = extract_targeted_activations(
                bundle.hooked_model, prompt, ids[0].tolist(), [cue_index], layers=[layer],
                sites=["resid_post_last_prompt", "resid_post_cue_token"], dtype="float16",
            )
            return {key: tuple(value.shape) for key, value in states.items()}

        shapes = report.guarded("activation_extraction", activations)
        if shapes is not None:
            hidden = report.facts.get("hidden_size") or bundle.hf_model.config.hidden_size
            report.check("activation_extraction", all(s == (hidden,) for s in shapes.values()), shapes)

        def parity() -> dict[str, Any]:
            ids = tokenizer(prompt, return_tensors="pt", add_special_tokens=True).input_ids.to(first_param.device)
            with torch.no_grad():
                hf_logits = bundle.hf_model(ids).logits[0, -1].float()
                tl_logits = bundle.hooked_model(ids)[0, -1].float()
            cosine = torch.nn.functional.cosine_similarity(hf_logits, tl_logits, dim=0).item()
            return {
                "top1_equal": int(hf_logits.argmax()) == int(tl_logits.argmax()),
                "cosine": round(cosine, 5),
                "max_abs_diff": round((hf_logits - tl_logits).abs().max().item(), 4),
            }

        parity_result = report.guarded("hf_vs_transformer_lens_parity", parity)
        if parity_result is not None:
            report.check(
                "hf_vs_transformer_lens_parity",
                parity_result["top1_equal"] and parity_result["cosine"] > 0.99,
                parity_result,
            )

    report.facts["peak_gpu_gb"] = round(torch.cuda.max_memory_allocated() / 1e9, 1)
    bundle = None  # release GPU memory before the next model
    gc.collect()
    torch.cuda.empty_cache()
    return _finish(report, out, "gpu")


def _finish(report: Report, out: Path, phase: str) -> Report:
    payload = {"checks": report.checks, "facts": report.facts, "passed": report.passed}
    (out / f"{report.model_key}.{phase}.json").write_text(json.dumps(payload, indent=2, default=str))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model-keys", nargs="+", required=True)
    parser.add_argument("--phase", choices=["cpu", "gpu"], required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--family", type=Path, default=DEFAULT_FAMILY)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--max-new-tokens", type=int, default=64)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    family = load_family(args.family)
    rb = load_run_behavioural()
    reports = []
    for key in args.model_keys:
        if args.phase == "cpu":
            reports.append(cpu_phase(key, family, rb, args.output_dir))
        else:
            reports.append(gpu_phase(key, family, rb, args.output_dir, args.device, args.max_new_tokens))
    summary = {r.model_key: {"passed": r.passed, "failed": [c["name"] for c in r.checks if not c["ok"] and c["severity"] == "hard"]} for r in reports}
    (args.output_dir / f"summary_{args.phase}.json").write_text(json.dumps(summary, indent=2))
    print("\nSUMMARY", json.dumps(summary, indent=2))
    return 0 if all(r.passed for r in reports) else 1


if __name__ == "__main__":
    sys.exit(main())
