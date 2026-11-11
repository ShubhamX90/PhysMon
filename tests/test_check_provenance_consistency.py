"""G0 item (f): text about authorship and validation must agree with the provenance fields."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_provenance_consistency.py"
spec = importlib.util.spec_from_file_location("check_provenance_consistency_for_test", SCRIPT)
prov = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prov)


def _fixture(tmp_path: Path, *, created_by: str = "agent", pi_validated: bool = True,
             v2_validated: bool = False, admission: str = "UNREVIEWED") -> tuple[Path, Path]:
    templates = tmp_path / "templates" / "sub"
    templates.mkdir(parents=True)
    (templates / "T_001.yaml").write_text(
        f"created_by: {created_by}\nvalidation:\n  pi_validated: {str(pi_validated).lower()}\n"
        f"  v2_validated: {str(v2_validated).lower()}\n  verifier_certified: true\n", encoding="utf-8")
    dataset = tmp_path / "dataset.jsonl"
    dataset.write_text(json.dumps({"admission_category": admission, "level_judged_by": "author agent",
                                   "agent_verification": {"status": "accepted"}}) + "\n", encoding="utf-8")
    return tmp_path / "templates", dataset


def _statuses(text: str, facts) -> dict[str, str]:
    return {hit["kind"]: hit["status"] for hit in prov.scan_text(text, facts)}


def test_facts_are_read_from_nested_templates_and_dataset(tmp_path):
    facts = prov.collect_facts(*_fixture(tmp_path))
    assert facts["templates"]["n"] == 1 and facts["templates"]["created_by"] == {"agent": 1}
    assert facts["dataset"]["admission_category"] == {"UNREVIEWED": 1}
    assert facts["supports"]["HUMAN_AUTHORSHIP"] is False
    assert facts["supports"]["INDEPENDENT_VALIDATION"] is False


def test_claims_of_expert_and_independent_validation_conflict_with_agent_records(tmp_path):
    facts = prov.collect_facts(*_fixture(tmp_path))
    statuses = _statuses("All problems were validated by physicists. Families were independently validated "
                         "by two raters. The templates were written by hand.", facts)
    # "validated by two raters" is also a human-validation claim, which pi_validated leaves ambiguous.
    assert statuses == {"EXPERT_REVIEW": "CONFLICT", "INDEPENDENT_VALIDATION": "CONFLICT",
                        "HUMAN_AUTHORSHIP": "CONFLICT", "HUMAN_VALIDATION": "UNSUPPORTED_BY_FIELDS"}


def test_human_validation_with_pi_flag_is_only_unsupported_by_fields(tmp_path):
    facts = prov.collect_facts(*_fixture(tmp_path))
    assert _statuses("Each family was manually verified.", facts) == {"HUMAN_VALIDATION": "UNSUPPORTED_BY_FIELDS"}


def test_human_validation_conflicts_when_no_record_supports_it(tmp_path):
    facts = prov.collect_facts(*_fixture(tmp_path, pi_validated=False))
    assert _statuses("Each family was manually verified.", facts) == {"HUMAN_VALIDATION": "CONFLICT"}


def test_negated_statements_are_consistent(tmp_path):
    facts = prov.collect_facts(*_fixture(tmp_path))
    hits = prov.scan_text("No item was validated by physicists; agent checks replaced the expert review.", facts)
    assert hits and all(hit["status"] == "NEGATED_MENTION" for hit in hits)


def test_human_authorship_is_consistent_when_a_record_says_so(tmp_path):
    facts = prov.collect_facts(*_fixture(tmp_path, created_by="human"))
    assert _statuses("The templates were written by hand.", facts) == {"HUMAN_AUTHORSHIP": "CONSISTENT"}


def test_cli_exit_codes(tmp_path):
    templates, dataset = _fixture(tmp_path)
    good = tmp_path / "good.md"
    good.write_text("Items were checked by a blind solver agent.\n", encoding="utf-8")
    bad = tmp_path / "bad.md"
    bad.write_text("The benchmark was reviewed by experts.\n", encoding="utf-8")
    common = ["--templates", str(templates), "--dataset", str(dataset)]
    assert prov.main([str(good), *common]) == 0
    report = tmp_path / "r.json"
    assert prov.main([str(bad), *common, "--json", str(report)]) == 1
    assert json.loads(report.read_text(encoding="utf-8"))["status_counts"] == {"CONFLICT": 1}
    assert prov.main([str(good), "--templates", str(tmp_path / "none"), "--dataset", str(tmp_path / "none.jsonl")]) == 2


def test_planned_validation_is_not_a_claim_of_completed_validation(tmp_path):
    facts = prov.collect_facts(*_fixture(tmp_path))
    hits = prov.scan_text("Dual independent validation is specified, and a planned human validation will follow.", facts)
    assert hits and all(hit["status"] == "PLANNED_MENTION" for hit in hits)


def test_denying_model_authorship_conflicts_with_agent_created_records(tmp_path):
    facts = prov.collect_facts(*_fixture(tmp_path))
    text = "Language models could not write physics or determine ground truth."
    assert _statuses(text, facts) == {"MODEL_AUTHORSHIP_DENIED": "CONFLICT"}
    human = prov.collect_facts(*_fixture(tmp_path / "h", created_by="human"))
    # The dataset fixture still names an author agent, so the denial stays unsupported there too.
    assert _statuses(text, human) == {"MODEL_AUTHORSHIP_DENIED": "CONFLICT"}
