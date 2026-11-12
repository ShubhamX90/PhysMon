"""Tests for the role-by-value specifications of batch M0-a (S02, S13, S27, S92, S20, S26)."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.benchmark.v2 import roles_m0_a as m0a  # noqa: E402
from physmon.benchmark.v2 import rolevalue as rv  # noqa: E402

EXPECTED_STRATA = {"S02": {"C", "K"}, "S13": {"C"}, "S27": {"C"}, "S92": {"C", "K"}, "S20": {"C"}, "S26": set()}


def _check(structure_id: str) -> list[rv.RoleCell]:
    structure = m0a.structure(structure_id)
    spec = m0a.ROLE_SPECS[structure_id]
    cert = rv.certify_role_spec(structure, spec)
    assert cert["passed"], cert["failed"]
    assert not cert["strata_failed"], cert["strata_failed"]
    assert rv.complete(spec, cert)
    defined = {s for s, sub in (("C", spec.cancelling), ("K", spec.conditional)) if sub is not None}
    assert defined == EXPECTED_STRATA[structure_id]
    for name in ("cancelling", "conditional"):
        if name in cert["checks"]:
            assert cert["checks"][name]["passed"], cert["checks"][name]
    assert any(p.marker_free for p in spec.phrasings_r) and any(p.marker_free for p in spec.phrasings_d)
    cells: list[rv.RoleCell] = []
    for instance in range(len(structure.instances)):
        cells_i = rv.role_cells(structure, spec, instance, include_heldout=True)
        assert all(rv.prompt_value_check(c) for c in cells_i)
        assert {c.stratum for c in cells_i} == {"none", "N", "R", "D"} | defined
        assert not any(c.confounded for c in cells_i)
        cells.extend(cells_i)
    # minimal pair: the R and D prompts of one value differ only in the relational phrase
    by_id = {c.cell_id: c for c in cells if c.instance == 0}
    r, d = by_id["R:z1:r0:after_context"], by_id["D:z1:d0:after_context"]
    r_rel, d_rel = spec.phrasings_r[0].relation, spec.phrasings_d[0].relation
    assert r_rel in r.prompt and d_rel in d.prompt
    assert r.prompt.replace(r_rel, "X") == d.prompt.replace(d_rel, "X")
    assert not math.isclose(r.gold_value, d.gold_value, rel_tol=rv.LOOSEST_REL_TOL)
    assert all(c.gold_value == pytest.approx(d.gold_value) for c in cells
               if c.instance == 0 and c.stratum in ("none", "N", "D", "C", "K"))
    print(r.prompt, d.prompt, sep="\n---\n")
    return cells


def test_s02_rough_incline():
    cells = _check("S02")
    r = next(c for c in cells if c.cell_id == "R:z0:r0:after_context" and c.instance == 0)
    a = 9.8 * (math.sin(math.radians(30)) - 0.15 * math.cos(math.radians(30)))
    assert r.gold_value == pytest.approx(math.sqrt(2 * a * (4.0 + 1.0)), rel=1e-6)
    k = next(c for c in cells if c.stratum == "K")
    assert k.foils["out_of_regime"] == 0.0


def test_s13_pendulum():
    cells = _check("S13")
    r = next(c for c in cells if c.cell_id == "R:z0:r0:after_context" and c.instance == 0)
    assert r.gold_value == pytest.approx(2 * math.pi * math.sqrt((0.8 + 0.2) / 9.8), rel=1e-6)


def test_s27_pressure_at_depth():
    cells = _check("S27")
    r = next(c for c in cells if c.cell_id == "R:z0:r0:after_context" and c.instance == 0)
    assert r.gold_value == pytest.approx(101.0 + 10.0 + 1000 * 9.8 * 12.0 / 1000)


def test_s92_cube_under_liquid():
    cells = _check("S92")
    r = next(c for c in cells if c.cell_id == "R:z0:r0:after_context" and c.instance == 0)
    assert r.gold_value == pytest.approx((1150.0 - 600.0) * 9.8 * 0.1 ** 3)
    k = next(c for c in cells if c.stratum == "K")
    assert k.foils["out_of_regime"] == 0.0


def test_s20_thin_lens():
    cells = _check("S20")
    r = next(c for c in cells if c.cell_id == "R:z0:r0:after_context" and c.instance == 0)
    assert r.gold_value == pytest.approx(12.0 * 45.0 / (45.0 - 12.0))


def test_s26_refraction():
    cells = _check("S26")
    r = next(c for c in cells if c.cell_id == "R:z0:r0:after_context" and c.instance == 0)
    assert r.gold_value == pytest.approx(math.degrees(math.asin(math.sin(math.radians(45.0)) / 1.5)))
