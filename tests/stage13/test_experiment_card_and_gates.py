import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_false_wave0_pass_is_superseded_by_v2_failure():
    gate = json.loads((ROOT / "results/stage13/wave0/wave0_gate_v2.json").read_text(encoding="utf-8"))
    assert gate["status"] == "FAIL"
    assert gate["paper_eligibility"] is False
    assert gate["permission_for_wave2"] is False
    assert gate["supersedes"] == "results/stage13/wave0/wave0_gate.json"


def test_wave0_gate_v3_fails_on_substantive_authority_not_file_existence():
    gate = json.loads((ROOT / "results/stage13/wave0/wave0_gate_v3.json").read_text(encoding="utf-8"))
    assert gate["status"] == "FAIL"
    assert gate["paper_eligibility"] is False
    assert gate["permission_for_wave2"] is False
    assert "authority_no_critical_unresolved" in gate["critical_failures"]
    assert any(check["check_id"] == "registry_v2_verification" and check["passed"] for check in gate["checks"])
    assert any(check["check_id"] == "canonical_tables_verify" and check["passed"] for check in gate["checks"])


def test_wave1a_software_materials_pass_but_human_pilot_pending():
    gate = json.loads(
        (ROOT / "results/stage13/benchmark_integrity/wave1a_gate_v2.json").read_text(
            encoding="utf-8"
        )
    )
    assert gate["status"] == "PASS"
    assert gate["human_pilot_status"] == "PENDING"
    assert gate["paper_eligibility"] is False
    assert gate["permission_for_wave2"] is False


def test_partition_freeze_requires_exact_ids_or_none_available():
    freeze = json.loads((ROOT / "docs/registry/partition_freeze_v2.json").read_text(encoding="utf-8"))
    assert freeze["internal_confirmatory_status"] == "none_available"
    assert freeze["family_classification_counts"]["discovery"] == 155
    assert freeze["family_classification_counts"]["internal_confirmatory"] == 0
