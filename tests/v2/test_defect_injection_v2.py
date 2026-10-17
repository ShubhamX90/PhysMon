"""Tests for the planted-defect injector (Stage 14.5): each rule must make exactly its declared edit."""

from __future__ import annotations

import glob
import json
import math
import re
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.validation import defect_injection as di  # noqa: E402


def _families():
    out = {}
    for path in sorted(glob.glob(str(REPO_ROOT / "results/stage6/generated_full_benchmark/*.json"))):
        if path.endswith("assembly_summary.json"):
            continue
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        out[data["template_id"]] = data
    return out


def _templates():
    out = {}
    for path in glob.glob(str(REPO_ROOT / "data/raw/templates/*.yaml")):
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        out[data["template_id"]] = data
    return out


FAMILIES, TEMPLATES = _families(), _templates()


def _prompts(family):
    return [v["prompt"] for v in sorted(family["variants"], key=lambda v: int(v["variant_id"]))]


def _applicable(defect_type, limit=3):
    found = []
    for family_id, family in FAMILIES.items():
        result = di.inject(defect_type, family, TEMPLATES.get(family_id))
        if result.applicable:
            found.append((family_id, family, result))
        if len(found) == limit:
            break
    return found


def test_every_defect_type_is_applicable_to_at_least_three_committed_families():
    for defect_type in di.DEFECT_TYPES:
        count = sum(
            di.inject(defect_type, f, TEMPLATES.get(fid)).applicable for fid, f in FAMILIES.items()
        )
        assert count >= 3, (defect_type, count)


def test_unknown_defect_type_raises():
    with pytest.raises(KeyError):
        di.inject("make_it_harder", next(iter(FAMILIES.values())))


def test_expected_verdicts_and_detection_pass():
    for defect_type in di.DEFECT_TYPES:
        _, _, result = _applicable(defect_type, 1)[0]
        assert result.expected_verdict == ("valid" if defect_type == di.CONTROL else "invalid")
        assert result.detectable_in == ("pass2" if defect_type in di.PASS2_ONLY else "pass1")


def test_hidden_coupling_changes_only_the_isolation_clause():
    for _, family, result in _applicable("hidden_coupling"):
        for original, edited in zip(_prompts(family), result.edited_prompts, strict=True):
            assert edited != original
            assert edited.replace("coupled to", "isolated from", 1) == original


def test_missing_assumption_is_limited_to_templates_where_the_assumption_is_needed():
    found = _applicable("missing_assumption", 10)
    assert {fid for fid, _, _ in found} == set(di.ASSUMPTION_CRITICAL)
    for _, family, result in found:
        for original, edited in zip(_prompts(family), result.edited_prompts, strict=True):
            assert len(edited) < len(original)
            assert di.numbers_in(edited) == di.numbers_in(original)
    # A template whose prompt gives the acceleration directly is not a real defect when 'frictionless' is deleted.
    assert not di.inject("missing_assumption", FAMILIES["CM_A_STD_001"], TEMPLATES["CM_A_STD_001"]).applicable


def test_control_keeps_every_number_and_unit_and_changes_the_wording():
    for _, family, result in _applicable(di.CONTROL, 5):
        for original, edited in zip(_prompts(family), result.edited_prompts, strict=True):
            assert edited != original
            assert di.numbers_in(edited) == di.numbers_in(original)
            assert edited.rstrip().endswith(".") and "Determine the" in edited


def test_invalid_parameter_domain_negates_exactly_one_mass_or_amount():
    for _, family, result in _applicable("invalid_parameter_domain"):
        for original, edited in zip(_prompts(family), result.edited_prompts, strict=True):
            before, after = di.numbers_in(original), di.numbers_in(edited)
            changed = [(a, b) for a, b in zip(before, after, strict=True) if a != b]
            assert len(before) == len(after) and len(changed) == 1
            assert changed[0][1] == "-" + changed[0][0]
            assert re.search(rf"{re.escape(changed[0][1])}\s*(?:kg|mol)\b", edited)
    # A temperature difference is not used: a negative change is a valid cooling.
    assert not di.inject("invalid_parameter_domain", FAMILIES["TH_B_UM_010"], TEMPLATES["TH_B_UM_010"]).applicable


def test_inconsistent_units_turns_one_mass_into_a_length():
    for _, family, result in _applicable("inconsistent_units"):
        for original, edited in zip(_prompts(family), result.edited_prompts, strict=True):
            assert edited.count("kg") == original.count("kg") - 1
            assert di.numbers_in(edited) == di.numbers_in(original)


def test_contradictory_statement_restates_the_cue_at_a_value_that_collides_with_no_other_number():
    for _, family, result in _applicable("contradictory_distractor_statement"):
        variants = sorted(family["variants"], key=lambda v: int(v["variant_id"]))
        for variant, edited in zip(variants, result.edited_prompts, strict=True):
            original = di.numbers_in(variant["prompt"])
            added = di.numbers_in(edited)
            assert len(added) == len(original) + 1
            assert re.search(r"A later note reports this same quantity as [-\d.eE+]+ ?\S* instead\.\)", edited)
            new_value = float(re.search(r"quantity as ([-\d.eE+]+)", edited).group(1))
            assert new_value != float(variant["cue_value"])
            assert all(not di._same_number(new_value, float(n)) for n in original), (variant["prompt"], new_value)


def test_contradictory_statement_avoids_the_collisions_found_in_review():
    # Review J14.5-010: 0.2 m (the target's own distance) and 0.1 m (the target's own depth) made the note ambiguous.
    for fid, bad in (("CM_B_STD_011", "0.2"), ("CM_B_STD_006", "0.1")):
        result = di.inject("contradictory_distractor_statement", FAMILIES[fid], TEMPLATES.get(fid))
        assert result.applicable
        assert all(f"quantity as {bad} " not in edited and f"quantity as {bad}0 " not in edited
                   for edited in result.edited_prompts)


def test_failed_transformation_alters_only_rendering_one_so_renderings_disagree():
    for _, family, result in _applicable("failed_transformation_identity"):
        variants = sorted(family["variants"], key=lambda v: int(v["variant_id"]))
        changed = [int(v["variant_id"]) for v, e in zip(variants, result.edited_prompts, strict=True)
                   if e != v["prompt"]]
        assert changed == [1]
        edited = result.edited_prompts[1]
        assert di.numbers_in(edited) != di.numbers_in(variants[1]["prompt"])


def test_insufficient_boundary_condition_removes_a_needed_initial_condition_cleanly():
    found = _applicable("insufficient_boundary_condition", 10)
    assert {fid for fid, _, _ in found} == set(di.BOUNDARY_EDITS) == {"CM_A_008", "CM_B_009", "CM_B_UM_047"}
    for _, family, result in found:
        for original, edited in zip(_prompts(family), result.edited_prompts, strict=True):
            assert "rest" in original and "rest" not in edited
            assert len(edited) < len(original)
            assert " which is." not in edited and ", ." not in edited  # no dangling fragment
    # CM_A_008 restates 'initially at rest (0.0 m/s)': the value is deleted with the words, so none is left behind.
    edited = di.inject("insufficient_boundary_condition", FAMILIES["CM_A_008"], TEMPLATES["CM_A_008"]).edited_prompts[0]
    assert "0.0 m/s" not in edited and "at rest" not in edited


def test_dropped_from_rest_is_not_planted_because_dropped_already_means_released_from_rest():
    # Review J14.5-010 (Q009): the user judged this edit not defective.
    assert "CM_B_UM_011" not in di.BOUNDARY_EDITS
    assert not di.inject("insufficient_boundary_condition", FAMILIES["CM_B_UM_011"], TEMPLATES["CM_B_UM_011"]).applicable


def test_equation_defect_really_disagrees_with_the_certified_answer():
    import sympy

    for family_id, family, result in _applicable("relevant_variable_removed_from_equation"):
        template = TEMPLATES[family_id]
        parameters = {k: float(v["value"]) for k, v in template["parameters"].items()}
        certified = float(template["correct_answer"]["value"])
        edited_value = float(sympy.sympify(result.edited_equation).subs(parameters))
        assert not math.isclose(edited_value, certified, rel_tol=1e-6)
        assert result.edited_prompts == _prompts(family)  # prompt untouched; defect lives in the equation


def test_precision_defect_is_a_clear_error_not_a_borderline_one():
    for _, family, result in _applicable("invalid_numerical_precision", 10):
        certified = float(str(family["correct_answer"]).split()[0])
        shown = float(result.edited_answer.split()[0])
        assert abs(shown - certified) / abs(certified) >= 0.05
        assert result.edited_answer.split()[1:] == str(family["correct_answer"]).split()[1:]
