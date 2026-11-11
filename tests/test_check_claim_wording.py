"""G0 item (e): mechanical claim-wording check against the claim registry."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_claim_wording.py"
spec = importlib.util.spec_from_file_location("check_claim_wording_for_test", SCRIPT)
wording = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wording)


def _kinds(text: str) -> list[tuple[str, str]]:
    return [(hit["claim"], hit["kind"]) for hit in wording.scan_text(text)]


def test_flags_prohibited_causal_wording():
    text = "Removing the four heads at L16 cancels the sensitivity.\nThese heads are necessary for it."
    assert ("C08", "VIOLATION") in _kinds(text)
    assert sum(kind == "VIOLATION" for _, kind in _kinds(text)) == 2


def test_necessary_needs_a_component_context():
    assert _kinds("It is necessary to report the interval.") == []


def test_negated_mention_is_reported_but_not_a_violation():
    kinds = _kinds("We do not claim necessity of the heads, nor a complete circuit.")
    assert kinds and all(kind == "NEGATED_MENTION" for _, kind in kinds)


def test_other_registry_prohibitions():
    text = ("The monitor outperforms all baselines. Its signal is independent of correctness. "
            "The probe shows cross-model transfer. Both models share a shared mechanism. "
            "The renamed-donor controls establish specificity with 100% specificity.")
    claims = {claim for claim, kind in _kinds(text) if kind == "VIOLATION"}
    assert {"C02", "C03", "C07", "C09", "C10"} <= claims


def test_sentences_spanning_lines_keep_their_first_line_number():
    hits = wording.scan_text("Intro.\n\nThe knockout\ncancels the shortcut sensitivity.")
    assert hits and hits[0]["line"] == 3


def test_registry_and_rules_must_agree(tmp_path):
    registry = {"C08": wording.RULES["C08"]["prohibited"]}
    wording.check_rules_cover(registry)
    with pytest.raises(wording.RegistryMismatch):
        wording.check_rules_cover({"C08": "Do not claim anything about heads."})
    with pytest.raises(wording.RegistryMismatch):
        wording.check_rules_cover({"C99": "Do not claim magic."})


def test_json_and_markdown_registries_are_read_and_compared(tmp_path):
    payload = {"claims": [{"claim_id": "C01", "prohibited_wording": wording.RULES["C01"]["prohibited"]}]}
    (tmp_path / "m.json").write_text(json.dumps(payload), encoding="utf-8")
    (tmp_path / "m.md").write_text("### C01\n\n- Prohibited: " + wording.RULES["C01"]["prohibited"] + "\n",
                                   encoding="utf-8")
    assert wording.load_registry(tmp_path / "m.json", tmp_path / "m.md") == {
        "C01": wording.RULES["C01"]["prohibited"]}
    (tmp_path / "m.md").write_text("### C01\n\n- Prohibited: Something else.\n", encoding="utf-8")
    with pytest.raises(wording.RegistryMismatch):
        wording.load_registry(tmp_path / "m.json", tmp_path / "m.md")


def test_committed_registry_is_covered_by_the_rules():
    registry = wording.load_registry(wording.DEFAULT_REGISTRY_JSON, wording.DEFAULT_REGISTRY_MD)
    wording.check_rules_cover(registry)
    assert len(registry) == 10


def test_cli_exit_codes(tmp_path):
    clean = tmp_path / "clean.md"
    clean.write_text("The monitor carries information about later sensitivity.\n", encoding="utf-8")
    bad = tmp_path / "bad.md"
    bad.write_text("The head is necessary for the effect.\n", encoding="utf-8")
    report = tmp_path / "report.json"
    assert wording.main([str(clean)]) == 0
    assert wording.main([str(bad), "--json", str(report)]) == 1
    assert json.loads(report.read_text(encoding="utf-8"))["n_violations"] == 1
