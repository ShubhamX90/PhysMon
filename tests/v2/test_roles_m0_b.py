"""Tests for the role-by-value specifications of batch M0-b (S07, S15, S30, S55, S72)."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.benchmark.v2 import rolevalue as rv  # noqa: E402
from physmon.benchmark.v2 import roles_m0_b as m0b  # noqa: E402


def _check(structure_id: str, strata: tuple[str, ...]) -> list[rv.RoleCell]:
    structure = m0b.structure(structure_id)
    spec = m0b.ROLE_SPECS[structure_id]
    assert spec.structure_id == structure.structure_id == structure_id
    cert = rv.certify_role_spec(structure, spec)
    assert cert["passed"], cert["failed"]
    assert not cert["strata_failed"], cert["strata_failed"]
    for name in strata:
        assert cert["checks"][name]["passed"], cert["checks"][name]
    assert rv.complete(spec, cert)
    assert any(p.marker_free for p in spec.phrasings_r) and any(p.marker_free for p in spec.phrasings_d)
    for instance in range(len(structure.instances)):
        cells = rv.role_cells(structure, spec, instance, positions=rv.POSITIONS, include_heldout=True)
        assert all(rv.prompt_value_check(c) for c in cells)
    cells = rv.role_cells(structure, spec, 0)
    by_id = {c.cell_id: c for c in cells}
    r, d = by_id["R:z1:r0:after_context"], by_id["D:z1:d0:after_context"]
    r_rel, d_rel = spec.phrasings_r[0].relation, spec.phrasings_d[0].relation
    assert r_rel in r.prompt and d_rel in d.prompt
    assert r.prompt.replace(r_rel, "X") == d.prompt.replace(d_rel, "X")  # minimal pair: only the relation differs
    assert not math.isclose(r.gold_value, d.gold_value, rel_tol=rv.LOOSEST_REL_TOL)
    expected = {"none", "N", "R", "D", *(("C",) if "cancelling" in strata else ()), *(("K",) if "conditional" in strata else ())}
    assert {c.stratum for c in cells} == expected
    return cells


def test_s07_rc_charging_series_resistor():
    cells = _check("S07", ("conditional",))
    r = next(c for c in cells if c.cell_id == "R:z0:r0:after_context")
    # 1 kΩ added in series: tau = 6 kΩ * 20 μF = 0.12 s; V = 12 (1 - exp(-0.08 / 0.12))
    assert r.gold_value == pytest.approx(12 * (1 - math.exp(-0.08 / 0.12)), rel=1e-9)
    assert "A 1 kΩ resistor is connected in series between the battery and the capacitor." in r.prompt


def test_s15_parallel_power_series_cell():
    cells = _check("S15", ("conditional",))
    r = next(c for c in cells if c.cell_id == "R:z0:r0:after_context")
    assert r.gold_value == pytest.approx(13.5 ** 2 * (1 / 6 + 1 / 12))
    k = next(c for c in cells if c.stratum == "K")
    assert k.gold_value == pytest.approx(36.0) and k.foils["out_of_regime"] == pytest.approx(12.0)


def test_s30_heating_time_added_water():
    cells = _check("S30", ("cancelling",))
    r = next(c for c in cells if c.cell_id == "R:z0:r0:after_context")
    assert r.gold_value == pytest.approx(2.5 * 4186 * 40 / 1500)
    c = next(c for c in cells if c.stratum == "C")
    assert c.gold_value == pytest.approx(2 * 4186 * 40 / 1500) and "wrong_law" in c.foils


def test_s55_rms_speed_heated_gas():
    cells = _check("S55", ("cancelling",))
    r = next(c for c in cells if c.cell_id == "R:z0:r0:after_context")
    assert r.gold_value == pytest.approx(math.sqrt(3 * 8.314 * 350 / 0.004), rel=1e-6)


def test_s72_de_broglie_second_stage():
    cells = _check("S72", ())
    r = next(c for c in cells if c.cell_id == "R:z0:r0:after_context")
    assert r.gold_value == pytest.approx(1240 / math.sqrt(2 * 511e3 * 200) * 1000, rel=1e-9)  # pm
