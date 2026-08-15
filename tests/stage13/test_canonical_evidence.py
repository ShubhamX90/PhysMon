import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_canonical_manifest_has_exactly_155_families_and_excludes_metadata():
    rows = read_csv(ROOT / "data/manifests/physmon_canonical_155.csv")
    canonical = [row for row in rows if row["is_canonical"].lower() == "true"]
    ids = [row["canonical_family_id"] for row in canonical]
    assert len(canonical) == 155
    assert len(ids) == len(set(ids))
    assert "assembly_summary" not in ids
    assert all(not family_id.endswith("_RENAME") for family_id in ids)


def test_derived_variable_renaming_variants_map_to_canonical_parents():
    canonical_ids = {
        row["canonical_family_id"]
        for row in read_csv(ROOT / "data/manifests/physmon_canonical_155.csv")
        if row["is_canonical"].lower() == "true"
    }
    derived = [
        json.loads(line)
        for line in (ROOT / "data/manifests/physmon_derived_variants.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert len(derived) == 10
    for row in derived:
        assert row["transformation_type"] == "variable_renaming"
        assert row["parent_canonical_family_id"] in canonical_ids
        assert row["derived_id"] not in canonical_ids


def test_canonical_evidence_v2_verifies_and_uses_explicit_model_ids():
    result = json.loads(
        (ROOT / "results/stage13/wave0/canonical_evidence_verification_v2.json").read_text(
            encoding="utf-8"
        )
    )
    assert result["status"] == "PASS"
    assert result["n_canonical_families"] == 155
    assert result["n_model_family_rows"] > 0
    assert result["n_variant_rows"] > 0

    family_rows = read_csv(ROOT / "results/canonical/model_family_evidence.csv")
    assert all(row["model_id"] and row["model_id"] != "PRIMARY_DENSE" for row in family_rows)
    assert all(row["source_experiment_ids"] for row in family_rows)


def test_final_table_hashes_match_gate_inputs():
    verification = json.loads(
        (ROOT / "results/stage13/wave0/canonical_evidence_verification_v2.json").read_text(
            encoding="utf-8"
        )
    )
    gate = json.loads((ROOT / "results/stage13/wave0/wave0_gate_v3.json").read_text(encoding="utf-8"))
    assert gate["input_hashes"]["family_table_hash"] == verification["family_table_hash"]
    assert gate["input_hashes"]["variant_table_hash"] == verification["variant_table_hash"]
    assert gate["input_hashes"]["manifest_hash"] == verification["manifest_hash"]
