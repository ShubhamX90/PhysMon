"""Tests for the dimensional-analysis layer (Stage 14.6)."""

from __future__ import annotations

import sys
from fractions import Fraction
from pathlib import Path

import pytest
import sympy

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.benchmark.v2 import dimensions as dm  # noqa: E402


def _dims(**kw):
    return {k: dm.unit(u).dim for k, u in kw.items()}


def test_dimension_arithmetic_and_labels():
    force = dm.unit("N").dim
    assert force == dm.unit("kg").dim * dm.unit("m/s^2").dim
    assert dm.unit("J").dim == dm.unit("N").dim * dm.unit("m").dim
    assert (dm.unit("m").dim ** 2).exps[1] == Fraction(2)
    assert dm.DIMLESS.dimensionless and not force.dimensionless
    assert dm.dim(M=1).label() == "M^1"
    with pytest.raises(KeyError):
        dm.dim(X=1)


def test_unit_conversion_and_incompatible_conversion():
    assert dm.convert(2.0, "kJ", "J") == pytest.approx(2000.0)
    assert dm.convert(36.0, "km/h", "m/s") == pytest.approx(10.0)
    assert dm.to_si(4.0, "μF") == pytest.approx(4e-6)
    assert dm.from_si(0.015, "mJ") == pytest.approx(15.0)
    with pytest.raises(dm.DimensionError):
        dm.convert(1.0, "kg", "m")
    with pytest.raises(dm.DimensionError):
        dm.unit("furlong")


def test_torque_and_energy_are_dimensionally_equal_and_that_is_documented():
    assert dm.unit("N*m").dim == dm.unit("J").dim


def test_expression_dimension_of_a_correct_law():
    m, a, t, v0 = sympy.symbols("m a t v0")
    dims = _dims(m="kg", a="m/s^2", t="s", v0="m/s")
    assert dm.expr_dimension(m * a, dims) == dm.unit("N").dim
    assert dm.expr_dimension(v0 + a * t, dims) == dm.unit("m/s").dim
    assert dm.expr_dimension(sympy.sqrt(2 * a * t ** 2), dims) == dm.unit("m/s^2").dim ** Fraction(1, 2) * dm.unit("s").dim
    assert dm.expr_dimension(sympy.exp(-t / t), dims) == dm.DIMLESS


def test_inconsistent_expressions_are_rejected():
    m, a, t, v0 = sympy.symbols("m a t v0")
    dims = _dims(m="kg", a="m/s^2", t="s", v0="m/s")
    with pytest.raises(dm.DimensionError):
        dm.expr_dimension(v0 + a, dims)  # speed plus acceleration
    with pytest.raises(dm.DimensionError):
        dm.expr_dimension(sympy.sin(t), dims)  # a dimensional argument to a transcendental function
    with pytest.raises(dm.DimensionError):
        dm.expr_dimension(m * sympy.Symbol("undeclared"), dims)


def test_mass_given_in_metres_is_caught_by_the_checker():
    force, mass, accel = sympy.symbols("F m a")
    right = _dims(F="N", m="kg", a="m/s^2")
    wrong = _dims(F="N", m="m", a="m/s^2")
    assert dm.expr_dimension(force / mass, right) == dm.unit("m/s^2").dim
    assert dm.expr_dimension(force / mass, wrong) != dm.unit("m/s^2").dim
