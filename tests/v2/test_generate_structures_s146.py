"""End-to-end test for the Stage 14.6 structure-generation script."""

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
        "s146_generate_structures", REPO_ROOT / "scripts/v2/s146_generate_structures.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


s146 = _load()


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    base = tmp_path_factory.mktemp("s146")
    argv = sys.argv
    sys.argv = ["s146", "--out-base", str(base), "--version", "t1"]
    try:
        assert s146.main() == 0
    finally:
        sys.argv = argv
    return base / "t1"


def test_all_ten_structures_are_certified_and_unreviewed(built):
    summary = json.loads((built / "summary.json").read_text(encoding="utf-8"))
    assert summary["n_structures"] == 10 and summary["all_solver_certified"] is True
    assert set(summary["status"].values()) == {"SOLVER_CERTIFIED"}
    assert "UNREVIEWED" in summary["admission_category"]
    for index in range(1, 11):
        document = json.loads((built / f"S{index:02d}.json").read_text(encoding="utf-8"))
        assert document["proof"]["status"] == "SOLVER_CERTIFIED"
        assert document["proof"]["admission_category"] == "UNREVIEWED"
        assert len(document["instances"]) >= 2 and document["assumptions"]
    assert "UNREVIEWED" in (built / "README.md").read_text(encoding="utf-8")


def test_mutation_report_has_full_sensitivity_and_specificity(built):
    report = json.loads((built / "mutation_report.json").read_text(encoding="utf-8"))
    assert report["n_mutants"] >= 90
    assert report["n_negative_not_caught"] == 0 and report["n_positive_wrongly_rejected"] == 0
    for mutator, entry in report["summary_by_mutator"].items():
        assert entry["failed_for_an_intended_reason"] == entry["n"], mutator
        assert entry.get("sensitivity", entry.get("specificity")) == 1.0


def test_manifest_and_admissibility_record_every_cell_including_the_impossible_ones(built):
    rows = [json.loads(line) for line in (built / "factor_cell_manifest.jsonl").read_text(
        encoding="utf-8").splitlines() if line.strip()]
    admissibility = json.loads((built / "admissibility.json").read_text(encoding="utf-8"))
    assert len(rows) == admissibility["n_cells"] == 220
    assert 200 <= admissibility["n_feasible"] < 220
    assert all(r["admission_category"] == "UNREVIEWED" for r in rows)
    assert all(r["prompt_matches_graph"] for r in rows if r["feasible"])
    assert all(r["infeasible_reason"] for r in rows if not r["feasible"])
    assert len({r["structure_uuid"] for r in rows}) == 10


def test_lineage_shows_no_overlap_with_v1(built):
    lineage = json.loads((built / "lineage.json").read_text(encoding="utf-8"))
    assert lineage["v1_overlap"]["n_v1_templates"] == 155
    assert lineage["v1_overlap"]["n_v1_distinct_programs"] < lineage["v1_overlap"]["n_v1_governing_law_labels"]
    for entry in lineage["structures"]:
        assert entry["source_template_overlap"] == [] and entry["law_family_in_v1"] is False
        assert entry["parent_structures"] == []


def test_refuses_to_overwrite(built, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["s146", "--out-base", str(built.parent), "--version", "t1"])
    assert s146.main() == 2
