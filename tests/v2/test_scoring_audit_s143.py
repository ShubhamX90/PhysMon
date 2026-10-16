"""Tests for the Stage 14.3 scoring-interface audit.

Pure-function tests are hermetic. The end-to-end test reads tokenizer files from the model store and is
skipped when they are absent (for example after another scratch wipe); it never loads model weights.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))


def _load():
    spec = importlib.util.spec_from_file_location(
        "s143_scoring_audit", REPO_ROOT / "scripts/v2/s143_scoring_audit.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


s143 = _load()


def _tokenizers_available() -> bool:
    from physmon.utils.paths import model_root

    return all((model_root() / name / "tokenizer.json").exists()
               for name in ("Qwen2.5-7B-Instruct", "Llama-3.1-8B-Instruct"))


def _token_row(model, template, n_tokens, **extra):
    row = {"model": model, "template_id": template, "n_answer_tokens": n_tokens,
           "n_numeric_answer_tokens": max(0, n_tokens - 2)}
    row.update(extra)
    return row


def test_length_audit_reports_rank_association_and_terciles():
    model = s143.MODEL_KEYS and "Qwen/Qwen2.5-7B-Instruct"
    token_rows = [_token_row(model, f"F{i}", 2 + i) for i in range(9)]
    labels = {(model, f"F{i}"): {"S0": float(i), "range": float(i) + 1.0, "y_b0": int(i >= 4),
                                 "range_label": 1, "mean_logprob": -10.0 - 2 * i} for i in range(9)}
    rows, summary = s143.length_audit(token_rows, labels)
    assert len(rows) == 9
    result = summary[model]
    assert result["n_families"] == 9
    assert result["spearman_answer_tokens_vs_S0"] == pytest.approx(1.0)
    assert result["spearman_answer_tokens_vs_mean_logprob"] == pytest.approx(-1.0)
    assert [result["by_answer_token_tercile"][k]["n"] for k in ("short", "medium", "long")] == [3, 3, 3]


def test_length_audit_skips_families_without_a_complete_label_row():
    model = "Qwen/Qwen2.5-7B-Instruct"
    token_rows = [_token_row(model, "A", 3), _token_row(model, "B", 4), _token_row(model, "C", 5)]
    labels = {(model, "A"): {"S0": 1.0, "range": 2.0, "y_b0": 1, "range_label": 1, "mean_logprob": -5.0},
              (model, "B"): {"S0": 0.0, "range": 0.1, "y_b0": 0, "range_label": 0, "mean_logprob": -6.0},
              (model, "C"): {"S0": 2.0, "range": 3.0, "y_b0": 1, "range_label": 1, "mean_logprob": -7.0}}
    del labels[(model, "B")]  # a family with a missing log-probability has no row; it must not become 0
    rows, summary = s143.length_audit(token_rows, labels)
    assert {r["template_id"] for r in rows} == {"A", "C"}
    assert summary[model]["n_families"] == 2


def test_main_refuses_to_reuse_a_non_empty_attempt_directory(tmp_path, monkeypatch):
    attempt = tmp_path / "attempt_x"
    attempt.mkdir()
    (attempt / "keep.txt").write_text("existing evidence", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["s143", "--out-root", str(tmp_path), "--attempt-id", "attempt_x"])
    assert s143.main() == 2
    assert (attempt / "keep.txt").read_text(encoding="utf-8") == "existing evidence"


@pytest.mark.skipif(not _tokenizers_available(), reason="model-store tokenizers not present")
def test_end_to_end_audit_finds_the_known_scoring_interface_facts(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["s143", "--out-root", str(tmp_path), "--attempt-id", "t1"])
    assert s143.main() == 0
    result = json.loads((tmp_path / "t1" / "summary.json").read_text(encoding="utf-8"))
    checks = {c["code"]: c for c in result["summary"]["contract_checks"]}
    qwen, llama = (result["summary"]["per_model"][m]
                   for m in ("Qwen/Qwen2.5-7B-Instruct", "meta-llama/Llama-3.1-8B-Instruct"))
    # Facts that hold for the committed Stage 6 records and the restored tokenizers.
    assert checks["S1"]["result"] == "PASS" and checks["S2"]["result"] == "PASS"
    assert checks["S4"]["result"] == "PASS" and checks["S7"]["result"] == "PASS"
    assert checks["S3"]["result"] == "FAIL" and checks["S6"]["result"] == "FAIL"
    assert checks["S5"]["result"] == "FAIL"
    assert qwen["records_with_duplicate_leading_special_token_behavioural"] == 0
    assert llama["records_with_duplicate_leading_special_token_behavioural"] == llama["n_records"] == 560
    assert qwen["behavioural_ids_equal_extraction_ids"] == qwen["n_records"]
    assert llama["behavioural_ids_equal_extraction_ids"] == 0
    assert result["manual_teacher_forced_scoring"].startswith("NOT_EVALUATED")
    cases = json.loads((tmp_path / "t1" / "manual_scoring_cases.json").read_text(encoding="utf-8"))
    assert cases and all(case["status"] == "NOT_EVALUATED" for case in cases)
    plan_case = next(c for c in cases if c["case"] == "near_match_plan_example"
                     and c["model"].startswith("Qwen"))
    assert plan_case["n_prompt_tokens_behavioural_variant0"] == 128 and plan_case["n_answer_tokens"] == 7
    token_rows = (tmp_path / "t1" / "token_audit.csv").read_text(encoding="utf-8").splitlines()
    assert len(token_rows) == 1 + 1120
