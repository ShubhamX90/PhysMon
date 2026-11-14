"""CPU tests of the G0 extended-parity script (s185) on tiny random Llama (GQA) and Qwen2 models in float32: plan and run end to
end (HF versus TransformerLens must PASS), a deliberately perturbed TransformerLens weight must FAIL the affected sites and
leave the upstream ones passing, the threshold rule, and the refusals (existing output, changed design). No real checkpoint,
no GPU, nothing submitted."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

pytest.importorskip("transformer_lens")
torch = pytest.importorskip("torch")
transformers = pytest.importorskip("transformers")


def _load():
    spec = importlib.util.spec_from_file_location("s185", REPO_ROOT / "scripts/v2/s185_extended_parity.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


s185 = _load()
STRUCTURES = ("S01", "S02", "S03", "S04")


def _save_tiny(directory: Path, kind: str, tokenizer) -> None:
    torch.manual_seed(0)
    common = dict(vocab_size=len(tokenizer), hidden_size=32, intermediate_size=64, num_hidden_layers=2, num_attention_heads=4,
                  num_key_value_heads=2, max_position_embeddings=4096, initializer_range=0.5)
    if kind == "llama":
        model = transformers.LlamaForCausalLM(transformers.LlamaConfig(**common))
    else:
        model = transformers.Qwen2ForCausalLM(transformers.Qwen2Config(**common))
    model.save_pretrained(str(directory))
    tokenizer.save_pretrained(str(directory))


def _manifest(model_dir: Path, out: Path) -> Path:
    files = [{"path": p.name, "size": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
             for p in sorted(model_dir.iterdir()) if p.is_file()]
    out.write_text(json.dumps({"revision": "tiny-rev", "files": files}))
    return out


@pytest.fixture(scope="module")
def inputs(tmp_path_factory):
    """Synthetic calibration records, M0 cells and dataset rows (the real files' shapes, tiny traces)."""

    d = tmp_path_factory.mktemp("parity_inputs")
    words = "Step one: the force balance gives a = F / m, so we compute the value carefully and check units. "
    records, cells, dataset = [], [], []
    for si, sid in enumerate(STRUCTURES):
        dataset.append({"sample_id": f"{sid}-i0", "problem": f"A block of mass {si + 2} kg is pushed. What is a?",
                        "answer_unit": "m/s^2"})
        for k in range(3):
            n_words = 8 + 6 * si + 4 * k
            trace = (words * 10)[: 6 * n_words] + "\nFINAL: 1.5 m/s^2"
            records.append({"status": "OK", "structure_id": sid, "instance": 0, "sample_index": k,
                            "job_id": f"{sid}-i0:no_cue:s{k}", "n_generated_tokens": n_words + 5, "model_commit": "tiny-rev",
                            "completion_status": "COMPLETE", "finish_reason": "stop", "generated_answer_raw": trace})
        if sid != "S04":  # S04 is not an M0 structure: its trace keeps its own calibration prompt
            for cell_id in ("no_cue", "N:after_context", "R:z0:r0:after_context", "D:z0:d0:after_context"):
                cells.append({"structure_id": sid, "instance": 0, "cell_id": cell_id, "job_id": f"{sid}-i0:{cell_id}",
                              "prompt": f"A block of mass {si + 2} kg is pushed ({cell_id}). What is a?",
                              "gold_unit": "m/s^2"})
    for name, rows in (("records.jsonl", records), ("cells.jsonl", cells), ("dataset.jsonl", dataset)):
        (d / name).write_text("".join(json.dumps(r) + "\n" for r in rows))
    return d


@pytest.fixture(scope="module", params=["llama", "qwen"])
def planned(request, tmp_path_factory, inputs, tokenizer_for):
    kind = request.param
    # no "llama" in the path: TL keys its config on the path text and reads the local config.json only otherwise
    model_dir = tmp_path_factory.mktemp("tiny_gqa" if kind == "llama" else "tiny_qwen2")
    _save_tiny(model_dir, kind, tokenizer_for[kind])
    manifest = _manifest(model_dir, tmp_path_factory.mktemp("manifest") / "tiny.json")
    plan_dir = tmp_path_factory.mktemp("plans")
    key = "llama_primary" if kind == "llama" else "qwen_primary"
    rc = s185.main(["plan", "--model-key", key, "--plan-dir", str(plan_dir), "--n-prompts", "4",
                    "--cells", str(inputs / "cells.jsonl"), "--dataset", str(inputs / "dataset.jsonl"),
                    "--records", str(inputs / "records.jsonl"), "--model-path", str(model_dir), "--manifest", str(manifest)])
    assert rc == 0
    return {"kind": kind, "key": key, "model_dir": model_dir, "manifest": manifest, "plan_dir": plan_dir}


def _run(planned, out_dir, extra=()):
    return s185.main(["run", "--model-key", planned["key"], "--plan-dir", str(planned["plan_dir"]), "--output-dir", str(out_dir),
                      "--device", "cpu", "--dtype", "float32", "--model-path", str(planned["model_dir"]),
                      "--manifest", str(planned["manifest"]), *extra])


def test_plan_freezes_inputs_and_refuses_to_overwrite(planned, inputs):
    plan_dir = planned["plan_dir"] / planned["key"]
    plan = json.loads((plan_dir / "plan.json").read_text())
    rows = [json.loads(line) for line in (plan_dir / "inputs.jsonl").read_text().splitlines()]
    assert len(rows) == 4 and plan["n_prompts"] == 4 and plan["model_revision"] == "tiny-rev"
    assert plan["design_fingerprint"] == s185.design_fingerprint()
    assert len({r["structure_id"] for r in rows}) == 4  # one trace per structure
    assert {r["prompt_source"] for r in rows} <= {"m0_role_cell", "calibration_own_prompt"}
    assert any(r["prompt_source"] == "calibration_own_prompt" for r in rows if r["structure_id"] == "S04")
    for r in rows:
        assert r["n_tokens"] == r["n_prompt_tokens"] + r["n_trace_tokens"] == len(r["token_ids"])
        assert r["user_text"].startswith(s185.rc2.INSTRUCTION)
    lengths = [r["trace_n_generated_tokens"] for r in rows]
    assert lengths[-1] == max(lengths)  # the 0.95 target is served first, with the longest trace
    assert s185.main(["plan", "--model-key", planned["key"], "--plan-dir", str(planned["plan_dir"]), "--n-prompts", "4",
                      "--cells", str(inputs / "cells.jsonl"), "--dataset", str(inputs / "dataset.jsonl"),
                      "--records", str(inputs / "records.jsonl"), "--model-path", str(planned["model_dir"]),
                      "--manifest", str(planned["manifest"])]) == s185.EXIT_REFUSE


def test_hf_vs_tl_float32_passes_and_output_is_never_overwritten(planned, tmp_path, monkeypatch):
    monkeypatch.setenv("PHYSMON_SOURCE_COMMIT", "deadbeef")
    assert _run(planned, tmp_path) == s185.EXIT_PASS
    report = json.loads((tmp_path / f"{planned['key']}.json").read_text())
    assert report["overall"] == "PASS" and report["failures"] == []
    assert report["model_files"]["verified"] is True and report["source_commit"] == "deadbeef"
    assert report["n_prompts_evaluated"] == 4 and report["parity_valid_up_to_tokens"] > 0
    assert report["hf_hidden_states_vs_hooks_exact"] is True
    for site in s185.SITES:
        assert len(report["sites"][site]) == 2 and all(r["pass"] for r in report["sites"][site])
        assert report["sites"][site][0]["tl"]["cos_min"] > 0.9999
    assert report["logits"]["tl"]["top1_agreement"] == 1.0 and report["logits"]["tl"]["kl_mean"] < 1e-6
    for name in s185.INTERVENTIONS:
        assert report["interventions"][name]["pass"], report["interventions"][name]
        first = report["prompts"][0]["interventions"][name]
        assert first["hf_site"]["outside_max_abs"] == 0.0 and first["tl_site"]["outside_max_abs"] == 0.0
        assert first["effect"]["informative"] and first["effect"]["rel_err"] < 1e-3
    assert report["tl_options"]["fold_ln"] is False and report["tl_options"]["center_writing_weights"] is False
    assert _run(planned, tmp_path) == s185.EXIT_REFUSE  # never overwrites


def test_perturbed_tl_weight_fails_the_affected_sites(planned, tmp_path, monkeypatch):
    monkeypatch.setenv("PHYSMON_SOURCE_COMMIT", "deadbeef")
    original = s185.build_tl

    def perturbed(*args, **kwargs):
        model, cfg = original(*args, **kwargs)
        with torch.no_grad():
            model.blocks[1].mlp.W_out.mul_(1.3)  # layer-1 MLP output 30% too large
        return model, cfg

    monkeypatch.setattr(s185, "build_tl", perturbed)
    assert _run(planned, tmp_path, ("--skip-model-hash",)) == s185.EXIT_FAIL
    report = json.loads((tmp_path / f"{planned['key']}.json").read_text())
    by_site = {(site, r["layer"]): r["pass"] for site, rows in report["sites"].items() for r in rows}
    assert report["overall"] == "FAIL"
    assert not by_site[("mlp_out", 1)] and not by_site[("resid_post", 1)]
    assert all(by_site[(site, 0)] for site in s185.SITES)  # upstream of the defect: unchanged
    assert by_site[("resid_pre", 1)] and by_site[("attn_out", 1)] and by_site[("z", 1)]
    assert "mlp_out.1" in report["failures"] and report["model_files"]["verified"] is False


def test_run_refuses_a_changed_design(planned, tmp_path, monkeypatch):
    monkeypatch.setenv("PHYSMON_SOURCE_COMMIT", "deadbeef")
    monkeypatch.setitem(s185.THRESHOLDS["residual"]["rel_l2"], "allowance", 0.5)  # loosened after the plan was frozen
    assert _run(planned, tmp_path, ("--skip-model-hash",)) == s185.EXIT_REFUSE
    assert not (tmp_path / f"{planned['key']}.json").exists()


def test_run_refuses_without_source_commit(planned, tmp_path, monkeypatch):
    monkeypatch.delenv("PHYSMON_SOURCE_COMMIT", raising=False)
    assert _run(planned, tmp_path, ("--skip-model-hash",)) == s185.EXIT_NO_COMMIT


def test_threshold_rule():
    j = s185.judge_value
    assert j(0.001, None, 0.01, 0.05)["by"] == "allowance"
    assert j(0.02, 0.01, 0.01, 0.05)["by"] == "noise_floor"          # within 3x a 0.01 floor and under the ceiling
    assert not j(0.04, 0.01, 0.01, 0.05)["pass"]                    # more than 3x the floor
    assert not j(0.06, 0.05, 0.01, 0.05)["pass"]                    # within 3x floor but above the hard ceiling
    assert not j(math.nan, 0.01, 0.01, 0.05)["pass"] and not j(math.inf, None, 0.01, 0.05)["pass"]
    verdict = s185.judge({"one_minus_cos_min": 0.0, "one_minus_cos_mean": 0.0, "rel_l2": 0.2}, None, "residual")
    assert not verdict["pass"] and not verdict["metrics"]["rel_l2"]["pass"]


def test_metrics_on_known_tensors():
    a = torch.randn(1, 7, 8)
    m = s185.site_metrics(a, a.clone(), "resid_post")
    assert m["cos_min"] == pytest.approx(1.0) and m["rel_l2"] == 0.0 and m["max_abs"] == 0.0
    b = a.clone()
    b[0, 3] = -b[0, 3]
    m = s185.site_metrics(a, b, "resid_post")
    assert m["cos_min"] == pytest.approx(-1.0) and m["worst_position"] == 3
    z = torch.randn(1, 5, 4, 2)
    zb = z.clone()
    zb[0, 2, 1] *= -1
    assert s185.site_metrics(z, zb, "z")["worst_position"] == 2
    logits = torch.randn(1, 6, 11)
    lm = s185.logit_metrics(logits, logits.clone(), chunk=4)
    assert lm["top1_agreement"] == 1.0 and lm["kl_mean"] == pytest.approx(0.0, abs=1e-7)
    shifted = logits + 5.0  # a per-position constant shift leaves the distribution unchanged
    assert s185.logit_metrics(logits, shifted)["kl_mean"] == pytest.approx(0.0, abs=1e-6)


def test_selection_uses_length_only():
    recs = [{"status": "OK", "structure_id": f"S{i:02d}", "instance": 0, "sample_index": 0, "n_generated_tokens": 100 * (i + 1),
             "completion_status": "COMPLETE" if i % 2 else "UNPARSEABLE"} for i in range(10)]
    a, _ = s185.select_prompts(recs, [], 3)
    flipped = [{**r, "completion_status": "COMPLETE"} for r in recs]
    b, _ = s185.select_prompts(flipped, [], 3)
    assert [x["record"]["structure_id"] for x in a] == [x["record"]["structure_id"] for x in b]
    assert [x["record"]["n_generated_tokens"] for x in a] == sorted(x["record"]["n_generated_tokens"] for x in a)
