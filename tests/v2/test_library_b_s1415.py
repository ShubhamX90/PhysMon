"""End-to-end test for the second structure batch, S11 to S20 (Stage 14.15)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.benchmark.v2 import dimensions as dm  # noqa: E402
from physmon.benchmark.v2 import library, library_b  # noqa: E402


def _load():
    spec = importlib.util.spec_from_file_location("s146_generate_structures_b", REPO_ROOT / "scripts/v2/s146_generate_structures.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


s146 = _load()


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    base = tmp_path_factory.mktemp("s146b")
    argv = sys.argv
    sys.argv = ["s146", "--library", "library_b", "--out-base", str(base), "--version", "t1"]
    try:
        assert s146.main() == 0
    finally:
        sys.argv = argv
    return base / "t1"


def test_the_ids_are_s11_to_s20_and_do_not_collide_with_the_first_batch():
    ids_b = [s.structure_id for s in library_b.all_structures()]
    ids_a = [s.structure_id for s in library.all_structures()]
    assert ids_b == [f"S{i}" for i in range(11, 21)] and not set(ids_a) & set(ids_b)


def test_all_ten_structures_are_certified_unreviewed_and_the_readme_names_the_batch(built):
    summary = json.loads((built / "summary.json").read_text(encoding="utf-8"))
    assert summary["stage"] == "14.15" and summary["library"] == "library_b"
    assert summary["n_structures"] == 10 and summary["all_solver_certified"] is True
    assert set(summary["status"].values()) == {"SOLVER_CERTIFIED"} and set(summary["status"]) == {f"S{i}" for i in range(11, 21)}
    assert "UNREVIEWED" in summary["admission_category"]
    readme = (built / "README.md").read_text(encoding="utf-8")
    assert "S11 to S20" in readme and "UNREVIEWED" in readme and "no model has been run" in readme
    for index in range(11, 21):
        document = json.loads((built / f"S{index}.json").read_text(encoding="utf-8"))
        assert document["proof"]["status"] == "SOLVER_CERTIFIED" and document["proof"]["admission_category"] == "UNREVIEWED"
        assert len(document["instances"]) >= 2 and document["assumptions"]


def test_no_new_program_equals_a_v1_template_or_a_first_batch_program(built):
    lineage = json.loads((built / "lineage.json").read_text(encoding="utf-8"))
    assert all(row["source_template_overlap"] == [] and row["law_family_in_v1"] is False for row in lineage["structures"])
    first = json.loads((REPO_ROOT / "data/v2/structures/v1/lineage.json").read_text(encoding="utf-8"))
    hashes_a = {row["symbolic_program_hash"] for row in first["structures"]}
    hashes_b = {row["symbolic_program_hash"] for row in lineage["structures"]}
    assert len(hashes_b) == 10 and not hashes_a & hashes_b


def test_the_mutation_harness_misses_nothing_and_rejects_no_equivalent_rewrite(built):
    report = json.loads((built / "mutation_report.json").read_text(encoding="utf-8"))
    assert report["n_negative_not_caught"] == 0 and report["n_positive_wrongly_rejected"] == 0 and report["n_mutants"] > 60


def test_infeasible_cells_are_recorded_with_a_reason_and_most_cells_are_feasible(built):
    admissibility = json.loads((built / "admissibility.json").read_text(encoding="utf-8"))
    assert admissibility["n_cells"] == 220 and admissibility["n_feasible"] >= 200
    rows = [json.loads(line) for line in (built / "factor_cell_manifest.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    assert all(r["feasible"] or r["infeasible_reason"] for r in rows)
    assert all(r["admission_category"] == "UNREVIEWED" for r in rows)


def test_the_units_added_for_the_batch_are_dimensionally_consistent():
    assert dm.convert(200.0, "mH", "H") == pytest.approx(0.2)
    assert dm.convert(5.0, "L", "m^3") == pytest.approx(0.005)
    assert dm.unit("K/W").dim == dm.unit("K").dim / dm.unit("W").dim
    assert dm.unit("H").dim == dm.unit("V").dim * dm.unit("s").dim / dm.unit("A").dim
    with pytest.raises(dm.DimensionError):
        dm.convert(1.0, "K/W", "W")
