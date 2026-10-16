"""Tests for the typed DECOY-v2 generator, certifier, mutation harness and factor cells (Stage 14.6)."""

from __future__ import annotations

import glob
import sys
from pathlib import Path

import pytest
import sympy
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.benchmark.v2 import certify as ce  # noqa: E402
from physmon.benchmark.v2 import design as dg  # noqa: E402
from physmon.benchmark.v2 import dimensions as dm  # noqa: E402
from physmon.benchmark.v2 import graph as gr  # noqa: E402
from physmon.benchmark.v2 import library as lib  # noqa: E402

STRUCTURES = lib.all_structures()
BY_ID = {s.structure_id: s for s in STRUCTURES}


def test_ten_distinct_structures_with_two_instantiations_each():
    assert [s.structure_id for s in STRUCTURES] == [f"S{i:02d}" for i in range(1, 11)]
    assert len({s.law_family for s in STRUCTURES}) == 10
    assert {s.domain for s in STRUCTURES} == {"mechanics", "circuits", "thermodynamics"}
    for s in STRUCTURES:
        assert len(s.instances) >= 2 and s.solver_arity == len(s.inputs)


@pytest.mark.parametrize("structure", STRUCTURES, ids=lambda s: s.structure_id)
def test_the_independent_solver_matches_the_graph_at_every_instantiation(structure):
    evaluator = gr.compile_target(structure)
    for instance in structure.instances:
        si = {n.name: dm.to_si(instance[n.name], n.unit) for n in structure.inputs}
        graph_value = evaluator(si)
        solver_value = structure.solver(*gr.solver_inputs(structure, si))
        assert solver_value == pytest.approx(graph_value, rel=structure.solver_rel_tol)


@pytest.mark.parametrize("structure", STRUCTURES, ids=lambda s: s.structure_id)
def test_every_structure_is_solver_certified_but_never_reviewed(structure):
    proof = ce.certify(structure)
    failed = [c["name"] for c in proof["checks"] if not c["passed"]]
    assert failed == [] and proof["status"] == "SOLVER_CERTIFIED"
    assert [c["name"] for c in proof["checks"]] == list(ce.CHECK_NAMES)
    assert proof["admission_category"] == "UNREVIEWED"
    assert "English text" in proof["statement"]
    assert proof["program_hash"] and proof["structure_uuid"] and proof["symbolic_derivation"]


def test_certification_is_deterministic():
    assert ce.certify(BY_ID["S02"]) == ce.certify(BY_ID["S02"])


def test_mutation_report_catches_every_planted_defect_for_an_intended_reason_and_keeps_rewrites():
    rows = []
    for structure in STRUCTURES:
        rows += ce.mutation_report(structure)
    assert len(rows) >= 90
    negatives = [r for r in rows if r["kind"] == "negative"]
    positives = [r for r in rows if r["kind"] == "positive"]
    assert all(r["outcome"] == "caught" and r["failed_for_an_intended_reason"] for r in negatives), \
        [r for r in negatives if r["outcome"] != "caught" or not r["failed_for_an_intended_reason"]]
    assert all(r["outcome"] == "passed" for r in positives)
    mutators = {r["mutator_id"] for r in rows}
    assert mutators >= {"cue_leak_into_equation", "unit_error", "sign_flip", "remove_required_input", "swap_target",
                        "hidden_dependence", "divisor_domain_includes_zero", "drop_sole_assumption",
                        "misdeclared_answer_unit", "equivalent_rewrite", "rename_symbols"}


def test_the_divisor_mutator_only_uses_true_singularities():
    # C1 appears only inside C1 + C2: zero C1 is not a singularity, so the mutator must not pick it.
    assert "C1" not in dg_divisors(BY_ID["S08"])
    assert "R3" in dg_divisors(BY_ID["S06"])


def dg_divisors(structure):
    return ce._denominator_inputs(structure)


def test_a_cue_wired_into_the_equation_is_rejected_by_two_independent_checks():
    mutant = next(m for m in ce.mutants(BY_ID["S01"]) if m.mutator_id == "cue_leak_into_equation")
    failed = {c["name"] for c in ce.certify(mutant.structure)["checks"] if not c["passed"]}
    assert {"nuisance_independence", "route_agreement"} <= failed


def test_a_mass_declared_in_metres_fails_the_dimensional_check():
    mutant = next(m for m in ce.mutants(BY_ID["S01"]) if m.mutator_id == "unit_error")
    checks = {c["name"]: c for c in ce.certify(mutant.structure)["checks"]}
    assert not checks["dimensions"]["passed"]


def test_every_feasible_cell_has_prompt_numerals_that_trace_to_the_graph():
    total = 0
    for structure in STRUCTURES:
        for cell in dg.all_cells(structure):
            if cell.feasible:
                total += 1
                assert dg.prompt_matches_graph(structure, cell), (structure.structure_id, cell.cell_id)
    assert total >= 180


def test_infeasible_cells_carry_a_reason_and_no_prompt():
    seen = 0
    for structure in STRUCTURES:
        for cell in dg.all_cells(structure):
            if not cell.feasible:
                seen += 1
                assert cell.reason and cell.prompt == ""
    assert seen >= 5  # some cells really are impossible (for example no low-overlap near match)


def test_cell_factors_follow_the_predeclared_bands():
    for structure in STRUCTURES:
        for instance in range(len(structure.instances)):
            gold = dg.gold_for(structure, structure.instances[instance])
            cells = {c: dg.render_cell(structure, instance, c) for c in dg.CELL_IDS}
            for cid in ("nongov_same_unit_near_high_overlap", "nongov_same_unit_near_low_overlap"):
                cell = cells[cid]
                if cell.feasible:
                    assert abs(cell.cue_value / abs(gold) - 1) <= dg.NEAR_BAND + 1e-9
                    shared = dg.common_leading_digits(cell.cue_value, gold)
                    assert (shared >= dg.HIGH_OVERLAP_MIN) if cid.endswith("high_overlap") else \
                        (shared <= dg.LOW_OVERLAP_MAX)
            assert cells["nongov_same_unit_moderate"].cue_value == pytest.approx(abs(gold) * dg.MODERATE_FACTOR,
                                                                                 rel=5e-3)
            assert cells["nongov_same_unit_far"].cue_value == pytest.approx(abs(gold) * dg.FAR_FACTOR, rel=5e-3)
            incompatible = cells["nongov_incompatible_unit_near"]
            assert dm.unit(incompatible.cue_unit).dim != dm.unit(structure.render.target_unit).dim
            convertible = cells["nongov_same_magnitude_convertible_unit"]
            if convertible.feasible:
                back = dm.convert(convertible.cue_value, convertible.cue_unit, structure.render.target_unit)
                assert back == pytest.approx(abs(gold), rel=5e-3)
                assert convertible.cue_value != pytest.approx(abs(gold), rel=1e-2)  # digits differ
            reversal = cells["role_reversal"]
            assert reversal.gold_value == pytest.approx(gold - reversal.cue_value)
            edit = cells["relevant_edit"]
            assert abs(edit.gold_value - gold) / abs(gold) >= ce.MIN_RELEVANT_EFFECT
            assert edit.expected_effect == "changed" and cells["no_cue"].expected_effect == "invariant"


def test_the_nonnumeric_extra_sentence_has_no_numeral_and_the_cue_numeral_appears_once():
    for structure in STRUCTURES:
        assert dg.prompt_numbers(structure.render.nonnumeric_sentence) == []
        cell = dg.render_cell(structure, 0, "nongov_same_unit_moderate")
        extra = len(dg.prompt_numbers(cell.prompt)) - len(structure.inputs) - len(structure.render.fixed_numbers)
        assert extra == 1


def test_identity_is_deterministic_renaming_invariant_and_distinct():
    hashes = {s.structure_id: dg.structure_hash(s) for s in STRUCTURES}
    assert len(set(hashes.values())) == 10
    assert dg.structure_uuid(BY_ID["S03"]) == dg.structure_uuid(lib.s03_elastic_collision())
    renamed = next(m for m in ce.mutants(BY_ID["S03"]) if m.mutator_id == "rename_symbols").structure
    assert dg.structure_hash(renamed) == hashes["S03"]


def test_no_new_structure_collides_with_any_v1_template():
    v1_hashes, v1_laws = {}, set()
    for path in glob.glob(str(REPO_ROOT / "data/raw/templates/**/*.yaml"), recursive=True):
        template = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        names = list(template["parameters"]) + ["pi"]
        expression = gr.parse_expr(str(template["governing_equation_sympy"]), names)
        v1_hashes[dg.canonical_program_hash(expression)] = template["template_id"]
        v1_laws.add(str(template.get("governing_law")))
    # 155 v1 families reduce to 31 distinct renaming-invariant equation programs (many reuse one law).
    assert 25 <= len(v1_hashes) <= 60
    for structure in STRUCTURES:
        assert dg.structure_hash(structure) not in v1_hashes, structure.structure_id
        assert structure.law_family not in v1_laws


def test_manifest_rows_carry_the_v2_data_contract_fields_and_start_unreviewed():
    rows = dg.manifest_rows(BY_ID["S06"])
    assert len(rows) == 2 * len(dg.CELL_IDS)
    required = {"structure_uuid", "template_cluster_id", "symbolic_program_hash", "cue_semantic_role", "unit_type",
                "numeric_proximity", "digit_overlap", "cue_position", "isolation_condition", "cue_numeric_value",
                "gold_value", "prompt_sha256", "prompt_matches_graph"}
    for row in rows:
        assert row["admission_category"] == "UNREVIEWED"
        if row["feasible"]:
            assert required <= set(row) and row["prompt_matches_graph"] is True
        else:
            assert row["infeasible_reason"]


def test_graph_rejects_cycles_and_undeclared_symbols():
    base = BY_ID["S01"]
    cyc = gr.Node("a", "computed", "x", "kg", "d", expr="m_eff")
    cyc2 = gr.Node("m_eff", "computed", "x", "kg", "d", expr="a")
    import dataclasses
    with pytest.raises(gr.GraphError):
        gr.topological_order(dataclasses.replace(base, nodes=(cyc, cyc2)))
    undeclared = gr.Node("a", "computed", "x", "kg", "d", expr="mystery")
    with pytest.raises(gr.GraphError):
        gr.topological_order(dataclasses.replace(base, nodes=(undeclared,)))


def test_node_names_that_collide_with_sympy_constants_stay_plain_symbols():
    expr = gr.parse_expr("I + E + C", ["I", "E", "C"])
    assert {str(s) for s in expr.free_symbols} == {"I", "E", "C"}
    assert sympy.sympify("I").is_number  # the default parser would have treated I as the imaginary unit
