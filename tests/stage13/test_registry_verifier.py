import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ALLOWED_STATUSES = {
    "complete_authoritative",
    "corrected_authoritative",
    "complete_exploratory",
    "superseded",
    "partial_not_reportable",
    "failed",
    "pending",
    "diagnostic_only",
}


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_registry_uses_exact_status_vocabulary_and_unique_ids():
    rows = load_jsonl(ROOT / "docs/registry/experiment_registry.jsonl")
    ids = [row["experiment_id"] for row in rows]
    assert len(ids) == len(set(ids))
    assert {row["status"] for row in rows} <= ALLOWED_STATUSES


def test_registry_verification_v2_passes_but_does_not_mark_paper_eligible():
    result = json.loads(
        (ROOT / "results/stage13/wave0/registry_verification_v2.json").read_text(encoding="utf-8")
    )
    assert result["status"] == "PASS"
    assert result["n_errors"] == 0

    rows = load_jsonl(ROOT / "docs/registry/experiment_registry.jsonl")
    assert all(row["paper_eligibility"] is False for row in rows)
    assert any(row["provenance_status"] == "unresolved" for row in rows)


def test_supersession_chain_for_variable_renaming_is_explicit():
    rows = {row["experiment_id"]: row for row in load_jsonl(ROOT / "docs/registry/experiment_registry.jsonl")}
    corrected = rows["stage11_variable_renaming_probe_corrected"]
    original = rows["stage11_variable_renaming_probe_original"]
    assert corrected["status"] == "complete_exploratory"
    assert corrected["supersedes_experiment_id"] == original["experiment_id"]
    assert original["status"] == "superseded"


def test_authoritative_status_requires_complete_provenance():
    rows = load_jsonl(ROOT / "docs/registry/experiment_registry.jsonl")
    for row in rows:
        if row["status"] in {"complete_authoritative", "corrected_authoritative"}:
            assert row["provenance_status"] == "complete"


def test_claim_matrix_links_existing_experiment_ids():
    rows = {row["experiment_id"] for row in load_jsonl(ROOT / "docs/registry/experiment_registry.jsonl")}
    claims = json.loads((ROOT / "docs/registry/claim_evidence_matrix_v2.json").read_text(encoding="utf-8"))[
        "claims"
    ]
    for claim in claims:
        for experiment_id in claim["experiment_ids"]:
            assert experiment_id in rows
