"""Tests for the v7 structure-first leakage audit.

These target the specific ways a leakage audit can lie: truncating its
population, inventing duplicates through bad rendering, resolving pairs without
evidence, or reporting a detector it never ran.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "scripts" / "stage13" / "run_leakage_audit_v7.py"
AUDIT_PATH = REPO_ROOT / "results" / "stage13" / "benchmark_integrity" / "leakage_audit_v7.json"


def _load():
    spec = importlib.util.spec_from_file_location("run_leakage_audit_v7", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


audit_module = _load()


def _record(**overrides):
    base = {
        "family_id": "F1",
        "variant_id": 0,
        "prompt": "a prompt",
        "split": "original",
        "derived_parent": "",
        "governing_equation": "v_0 + a * t",
        "governing_symbols": ["a", "t", "v_0"],
        "canonical_answer": "11.0 m/s",
        "exact_prompt_hash": "h1",
        "number_masked_hash": "n1",
        "equation_hash": "e1",
        "structure_hash": "s1",
        "cue_template_hash": "c1",
    }
    base.update(overrides)
    return base


def test_renaming_invariant_structure_collapses_variable_names():
    # Renaming every symbol must not hide a shared structure.
    assert audit_module.renaming_invariant_structure(
        "v_0 + a * t"
    ) == audit_module.renaming_invariant_structure("u_0 + b * s")


def test_renaming_invariant_structure_distinguishes_real_structure():
    assert audit_module.renaming_invariant_structure(
        "v_0 + a * t"
    ) != audit_module.renaming_invariant_structure("v_0 * a + t")


def test_same_family_pairs_are_expected_not_review_workload():
    a = _record(family_id="F1", prompt="x")
    b = _record(family_id="F1", prompt="y")
    relation, _ = audit_module.classify(a, b)
    assert relation == "within_same_family_expected"
    assert relation not in audit_module.UNRESOLVED_RELATIONS


def test_derived_parent_pairs_are_expected_not_review_workload():
    a = _record(family_id="F1_RENAME", derived_parent="F1", prompt="x")
    b = _record(family_id="F1", prompt="y")
    relation, _ = audit_module.classify(a, b)
    assert relation == "derived_parent_expected"
    assert relation not in audit_module.UNRESOLVED_RELATIONS


def test_scaffold_resolution_requires_recorded_evidence():
    # Different physics, similar wording -> resolved, and the evidence is recorded.
    a = _record(family_id="F1", equation_hash="e1", canonical_answer="11.0 m/s",
                governing_equation="v_0 + a*t", structure_hash="s1")
    b = _record(family_id="F2", equation_hash="e2", canonical_answer="6.0 N*m",
                governing_equation="r*F", structure_hash="s2",
                governing_symbols=["F", "r"], prompt="different", number_masked_hash="n2")
    relation, evidence = audit_module.classify(a, b)
    assert relation == "cross_family_template_scaffold_resolved"
    assert evidence["resolved_by"]
    assert evidence["equation_a"] != evidence["equation_b"]
    assert evidence["answer_a"] != evidence["answer_b"]


def test_identical_equation_and_answer_is_never_resolved_as_scaffold():
    # Same physics across families must stay in review, however the wording reads.
    a = _record(family_id="F1", prompt="p1", number_masked_hash="n1", structure_hash="s1")
    b = _record(family_id="F2", prompt="p2", number_masked_hash="n2", structure_hash="s1")
    relation, _ = audit_module.classify(a, b)
    assert relation in audit_module.UNRESOLVED_RELATIONS


def test_cross_family_identical_prompt_is_an_exact_duplicate():
    a = _record(family_id="F1", prompt="identical text")
    b = _record(family_id="F2", prompt="identical text")
    relation, _ = audit_module.classify(a, b)
    assert relation == "cross_family_exact_duplicate"
    assert relation in audit_module.UNRESOLVED_RELATIONS


def test_number_masked_match_is_a_numeric_sibling():
    a = _record(family_id="F1", prompt="lever 0.3 m force 20 N", number_masked_hash="same")
    b = _record(family_id="F2", prompt="lever 0.5 m force 30 N", number_masked_hash="same")
    relation, _ = audit_module.classify(a, b)
    assert relation == "cross_family_numeric_sibling"
    assert relation in audit_module.UNRESOLVED_RELATIONS


def test_bucket_pairs_only_pairs_within_a_shared_signature():
    records = [
        _record(family_id="F1", structure_hash="s1"),
        _record(family_id="F2", structure_hash="s1"),
        _record(family_id="F3", structure_hash="s2"),
    ]
    pairs = audit_module.bucket_pairs(records, "structure_hash")
    assert pairs == {(0, 1)}


def test_rendering_uses_production_renderer_so_parameters_are_substituted():
    """Families sharing a template but differing in parameters must render differently.

    Substituting only the cue would leave {r_A}/{F_A} in place and make these two
    families look byte-identical, manufacturing false exact duplicates.
    """

    import yaml

    a = yaml.safe_load((REPO_ROOT / "data/raw/templates/CM_B_UM_027.yaml").read_text())
    b = yaml.safe_load((REPO_ROOT / "data/raw/templates/CM_B_UM_028.yaml").read_text())
    prompts_a = audit_module.render_variants(a)
    prompts_b = audit_module.render_variants(b)
    assert prompts_a and prompts_b
    assert "{" not in prompts_a[0], "unsubstituted placeholder left in rendered prompt"
    assert set(prompts_a).isdisjoint(set(prompts_b))


@pytest.mark.skipif(not AUDIT_PATH.exists(), reason="audit artifact not generated yet")
class TestGeneratedAudit:
    @staticmethod
    def _audit():
        return json.loads(AUDIT_PATH.read_text(encoding="utf-8"))

    def test_population_is_not_truncated(self):
        audit = self._audit()
        assert audit["population_truncated"] is False
        assert audit["n_families"] == 155

    def test_status_is_one_of_the_allowed_values(self):
        assert self._audit()["status"] in {
            "PASS",
            "FAIL_EXACT_CROSS_SPLIT_DUPLICATE",
            "INCOMPLETE_PENDING_CROSS_FAMILY_REVIEW",
        }

    def test_status_cannot_be_pass_while_unresolved_candidates_remain(self):
        audit = self._audit()
        if audit["unresolved_cross_family_review"] > 0:
            assert audit["status"] != "PASS"

    def test_review_workload_is_reported_at_family_granularity(self):
        audit = self._audit()
        assert audit["unresolved_family_pairs"] <= audit["unresolved_cross_family_review"]
        assert audit["unresolved_family_clusters"] >= 1

    def test_no_detector_is_claimed_active_without_emitting_a_field(self):
        detectors = self._audit()["detectors"]
        # The embedding detector has no local implementation and must say so.
        assert detectors["semantic_template_similarity"].startswith("not_available")
        # Lexical similarity must not be presented as a trigger.
        assert "tiebreaker" in detectors["lexical_similarity"]

    def test_supersession_of_v6_is_recorded_with_a_reason(self):
        audit = self._audit()
        assert audit["supersedes"].endswith("leakage_audit_v6.json")
        assert len(audit["supersession_reason"]) > 40
