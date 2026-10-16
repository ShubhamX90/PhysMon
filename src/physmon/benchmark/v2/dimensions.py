"""Dimensional analysis for the typed DECOY-v2 generator (Stage 14.6; v2 B3.2, p.8; P2.1, p.18).

A physical quantity carries an exponent vector over the SI base dimensions. Expressions are checked by propagating
dimensions through sympy trees: sums need equal dimensions, powers need numeric exponents, transcendental functions
need dimensionless arguments. This is the dimensional checker that the Stage 13 certificates listed as unsupported
(`unsupported_no_dimensional_checker`).

Torque and energy share an SI dimension, so `N*m` and `J` are dimensionally equal here and distinguishing them is a
semantic (human) check, recorded in the structure's quantity types.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

import sympy

BASE = ("M", "L", "T", "I", "Th", "N")


class DimensionError(ValueError):
    """Raised when an expression or conversion is dimensionally inconsistent."""


@dataclass(frozen=True)
class Dim:
    """Exponents of (mass, length, time, current, temperature, amount)."""

    exps: tuple[Fraction, ...] = (Fraction(0),) * 6

    def __mul__(self, other: Dim) -> Dim:
        return Dim(tuple(a + b for a, b in zip(self.exps, other.exps, strict=True)))

    def __truediv__(self, other: Dim) -> Dim:
        return Dim(tuple(a - b for a, b in zip(self.exps, other.exps, strict=True)))

    def __pow__(self, power: int | Fraction) -> Dim:
        return Dim(tuple(a * Fraction(power) for a in self.exps))

    @property
    def dimensionless(self) -> bool:
        return all(e == 0 for e in self.exps)

    def label(self) -> str:
        parts = [f"{n}^{e}" for n, e in zip(BASE, self.exps, strict=True) if e != 0]
        return " ".join(parts) or "1"


def dim(**exponents: int | Fraction) -> Dim:
    unknown = set(exponents) - set(BASE)
    if unknown:
        raise KeyError(f"unknown base dimension(s) {sorted(unknown)}; expected {list(BASE)}")
    return Dim(tuple(Fraction(exponents.get(name, 0)) for name in BASE))


DIMLESS = dim()
_LENGTH, _MASS, _TIME = dim(L=1), dim(M=1), dim(T=1)
_FORCE = dim(M=1, L=1, T=-2)
_ENERGY = dim(M=1, L=2, T=-2)
_POWER = dim(M=1, L=2, T=-3)
_VOLT = dim(M=1, L=2, T=-3, I=-1)
_COULOMB = dim(I=1, T=1)
_FARAD = dim(M=-1, L=-2, T=4, I=2)
_OHM = dim(M=1, L=2, T=-3, I=-2)


@dataclass(frozen=True)
class Unit:
    name: str
    dim: Dim
    factor: float  # multiply a value in this unit by `factor` to get the SI value


def _units() -> dict[str, Unit]:
    table = [
        ("1", DIMLESS, 1.0), ("deg", DIMLESS, 3.141592653589793 / 180.0), ("rad", DIMLESS, 1.0),
        ("kg", _MASS, 1.0), ("g", _MASS, 1e-3),
        ("m", _LENGTH, 1.0), ("cm", _LENGTH, 1e-2), ("mm", _LENGTH, 1e-3), ("km", _LENGTH, 1e3),
        ("s", _TIME, 1.0), ("ms", _TIME, 1e-3), ("min", _TIME, 60.0), ("h", _TIME, 3600.0),
        ("m/s", _LENGTH / _TIME, 1.0), ("km/h", _LENGTH / _TIME, 1000.0 / 3600.0),
        ("m/s^2", _LENGTH / _TIME ** 2, 1.0), ("cm/s^2", _LENGTH / _TIME ** 2, 1e-2),
        ("rad/s", _TIME ** -1, 1.0), ("rad/s^2", _TIME ** -2, 1.0), ("Hz", _TIME ** -1, 1.0),
        ("N", _FORCE, 1.0), ("kN", _FORCE, 1e3), ("mN", _FORCE, 1e-3),
        ("J", _ENERGY, 1.0), ("kJ", _ENERGY, 1e3), ("mJ", _ENERGY, 1e-3),
        ("N*m", _ENERGY, 1.0), ("mN*m", _ENERGY, 1e-3),
        ("W", _POWER, 1.0), ("kW", _POWER, 1e3), ("mW", _POWER, 1e-3),
        ("Pa", _MASS / (_LENGTH * _TIME ** 2), 1.0), ("kPa", _MASS / (_LENGTH * _TIME ** 2), 1e3),
        ("kg*m^2", _MASS * _LENGTH ** 2, 1.0),
        ("V", _VOLT, 1.0), ("mV", _VOLT, 1e-3), ("kV", _VOLT, 1e3),
        ("A", dim(I=1), 1.0), ("mA", dim(I=1), 1e-3),
        ("Ω", _OHM, 1.0), ("kΩ", _OHM, 1e3),
        ("C", _COULOMB, 1.0), ("mC", _COULOMB, 1e-3), ("μC", _COULOMB, 1e-6),
        ("F", _FARAD, 1.0), ("mF", _FARAD, 1e-3), ("μF", _FARAD, 1e-6),
        ("K", dim(Th=1), 1.0), ("mol", dim(N=1), 1.0),
        ("J/(kg*K)", _ENERGY / (_MASS * dim(Th=1)), 1.0),
        ("N/m", _FORCE / _LENGTH, 1.0),
    ]
    return {name: Unit(name, d, f) for name, d, f in table}


UNITS = _units()


def unit(name: str) -> Unit:
    try:
        return UNITS[name]
    except KeyError as error:
        raise DimensionError(f"unknown unit {name!r}") from error


def to_si(value: float, unit_name: str) -> float:
    return float(value) * unit(unit_name).factor


def from_si(value: float, unit_name: str) -> float:
    return float(value) / unit(unit_name).factor


def convert(value: float, source: str, target: str) -> float:
    """Convert between two units of the same dimension; raise DimensionError otherwise."""

    a, b = unit(source), unit(target)
    if a.dim != b.dim:
        raise DimensionError(f"cannot convert {source} ({a.dim.label()}) to {target} ({b.dim.label()})")
    return float(value) * a.factor / b.factor


def expr_dimension(expression: sympy.Expr, symbol_dims: dict[str, Dim]) -> Dim:
    """Dimension of a sympy expression given the dimension of each free symbol."""

    if expression.is_Symbol:
        name = str(expression)
        if name not in symbol_dims:
            raise DimensionError(f"symbol {name!r} has no declared dimension")
        return symbol_dims[name]
    if expression.is_number:
        return DIMLESS
    if expression.is_Add:
        dims = [expr_dimension(arg, symbol_dims) for arg in expression.args]
        if any(d != dims[0] for d in dims[1:]):
            raise DimensionError(f"terms of a sum have different dimensions: {[d.label() for d in dims]}")
        return dims[0]
    if expression.is_Mul:
        result = DIMLESS
        for arg in expression.args:
            result = result * expr_dimension(arg, symbol_dims)
        return result
    if expression.is_Pow:
        base, exponent = expression.args
        base_dim = expr_dimension(base, symbol_dims)
        if not exponent.is_number:
            if not expr_dimension(exponent, symbol_dims).dimensionless or not base_dim.dimensionless:
                raise DimensionError("a symbolic exponent needs a dimensionless base and exponent")
            return DIMLESS
        return base_dim ** Fraction(int(exponent.p), int(exponent.q))
    if isinstance(expression, sympy.Function):
        if not all(expr_dimension(arg, symbol_dims).dimensionless for arg in expression.args):
            raise DimensionError(f"{expression.func.__name__} needs a dimensionless argument")
        return DIMLESS
    raise DimensionError(f"unsupported expression node {type(expression).__name__}")
