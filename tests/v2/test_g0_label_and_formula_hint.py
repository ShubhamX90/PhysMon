"""G0 items (a) and (b): label stability across instructions and the formula-hint record."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load(name: str):
    spec = importlib.util.spec_from_file_location(f"{name}_for_test", ROOT / "scripts" / "v2" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


stability = _load("g0a_label_stability")
formula = _load("g0b_formula_hint")


def test_compare_reports_spearman_agreement_and_chance():
    a = {"f1": 0.0, "f2": 0.6, "f3": 1.2, "f4": 0.1}
    b = {"f1": 0.7, "f2": 0.0, "f3": 1.0, "f4": 0.2}
    result = stability.compare(a, b, ["f1", "f2", "f3", "f4"])
    assert result["status"] == "EVALUATED" and result["n"] == 4
    assert result["label_agreement"] == 2 and result["positives_a"] == 2 and result["positives_b"] == 2
    assert result["chance_agreement"] == 0.5


def test_compare_with_too_few_families_is_not_evaluated():
    result = stability.compare({"f1": 1.0}, {"f1": 1.0}, ["f1", "f2"])
    assert result["status"] == "NOT_EVALUATED" and "spearman" not in result


def test_records_from_several_runs_are_not_silently_merged():
    rows = [{"model_name": "M", "template_id": "T", "variant_id": v, "logprob_correct_answer": -1.0}
            for v in (0, 1, 1)]
    values, note = stability.slp_from_records(rows, "M")
    assert values is None and "several records" in note


def test_committed_records_reproduce_c2b_and_extend_it_to_llama():
    report = stability.run(ROOT)
    qwen = report["models"]["qwen"]["pairs"]["stage4_repair__vs__stage6_panel__pilot"]
    assert (qwen["n"], qwen["spearman"], qwen["label_agreement"]) == (30, 0.043, 17)
    llama = report["models"]["llama"]["pairs"]["stage4_repair__vs__stage6_panel__pilot"]
    assert llama["status"] == "EVALUATED" and llama["n"] == 30
    control = report["models"]["qwen"]["pairs"]["stage6_d1__vs__stage6_panel__shared"]
    assert control["spearman"] == 1.0 and control["label_agreement"] == control["n"] == 40


def test_grading_rule_and_transitions():
    assert formula.split_answer("Answer: 12.0 Nm") == (12.0, "Nm")
    assert formula.is_correct("12.0 Nm", "12.0 N*m", 1e-3) is True
    assert formula.is_correct("10460 J", "41860 J", 1e-3) is False
    assert formula.is_correct("no number", "41860 J", 1e-3) is None
    assert formula.transition(False, True) == "becomes_correct"
    assert formula.transition(None, True) == "NOT_EVALUATED"


def test_committed_formula_hint_records():
    report = formula.run(ROOT)
    qwen = report["models"]["Qwen/Qwen2.5-7B-Instruct"]
    assert qwen["n_families_evaluated"] == 5 and qwen["label_fires_at_0.5"] == 5
    assert qwen["transition_counts"]["transition@0.001"]["stays_correct"] == 4
    assert qwen["transition_counts"]["transition@0.001"]["becomes_correct"] == 1
    assert qwen["transition_counts"]["transition@0.001"]["becomes_wrong"] == 0
    assert "meta-llama/Llama-3.1-8B-Instruct" in report["models_NOT_EVALUATED"]
