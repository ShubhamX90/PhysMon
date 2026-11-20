"""Check 5.3b guard (amendment A1) as implemented in s190b, including flags that cite the N sentence's numbered D twin (J15.1-059)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("s190b", ROOT / "scripts/v2/s190b_score_m0v2_admission.py")
s190b = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(s190b)

ENTRY = {"sentence_labels": {"TAAAA": "N0", "TBBBB": "D0", "TCCCC": "N1", "TDDDD": "D1", "TEEEE": "R0"},
         "sentence_strata": {"TAAAA": "N", "TBBBB": "D", "TCCCC": "N", "TDDDD": "D", "TEEEE": "R"}}


def flag(reason: str, name: str = "rendering_not_minimal") -> dict[str, str]:
    return {"flag": name, "severity": "high", "reason": reason}


def test_twins_map_n_to_d_of_the_same_pair():
    assert s190b.n_twins(ENTRY) == {"TAAAA": "TBBBB", "TCCCC": "TDDDD"}


def test_n_only_flag_is_guarded():
    assert s190b.guarded_53b(flag("TAAAA and TCCCC omit the number."), s190b.n_twins(ENTRY))


def test_flag_citing_the_d_twins_is_guarded():
    assert s190b.guarded_53b(flag("TAAAA and TCCCC omit the 13 kW specified by their twins TBBBB and TDDDD."), s190b.n_twins(ENTRY))


def test_flag_citing_a_d_whose_n_is_not_named_counts():
    assert not s190b.guarded_53b(flag("TAAAA omits the number of TDDDD."), s190b.n_twins(ENTRY))


def test_flag_on_d_or_r_only_counts():
    twins = s190b.n_twins(ENTRY)
    assert not s190b.guarded_53b(flag("TBBBB is not minimal."), twins)
    assert not s190b.guarded_53b(flag("TAAAA and TEEEE differ."), twins)
    assert not s190b.guarded_53b(flag("no sentence named"), twins)


def test_other_flag_types_count():
    assert not s190b.guarded_53b(flag("TAAAA omits the number.", "missing_assumption"), s190b.n_twins(ENTRY))


def test_plain_set_keeps_the_original_behaviour():
    assert s190b.guarded_53b(flag("TAAAA omits the number."), {"TAAAA", "TCCCC"})
    assert not s190b.guarded_53b(flag("TAAAA omits the number of TBBBB."), {"TAAAA", "TCCCC"})
