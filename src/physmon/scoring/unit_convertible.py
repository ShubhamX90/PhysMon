"""Unit-convertible grading of a parsed answer (Stage 14.20).

The declared correctness rule (protocol section 4b, `v2_scorer.classify_answer`) requires the unit to match the gold unit exactly after
normalising spacing and superscripts. The Stage 14.20 speed test showed that this marks physically identical answers wrong when a
model picks another unit of the same quantity or another spelling (1.125 J for 1125 mJ, 720 pC for 0.72 nC, "degrees" for deg, "years"
for yr). This module gives the SENSITIVITY label `correct_if_units_convertible`: the answer is converted to the gold unit with the
dimension registry (same dimension required, `1` excluded) and then judged by the declared rule, with the half-unit-in-the-last-
printed-place tolerance scaled by the conversion factor. It never replaces the declared label, and a unit of another dimension or an
unknown unit stays `wrong`.
"""

from __future__ import annotations

from physmon.scoring import v2_scorer as vs

ALIASES = {
    "degrees": "deg", "degree": "deg", "°": "deg", "years": "yr", "year": "yr", "seconds": "s", "second": "s", "sec": "s",
    "meters": "m", "meter": "m", "metres": "m", "metre": "m", "joules": "J", "joule": "J", "watts": "W", "watt": "W",
    "newtons": "N", "newton": "N", "volts": "V", "volt": "V", "amperes": "A", "ampere": "A", "amps": "A", "amp": "A",
    "ohms": "Ω", "ohm": "Ω", "hertz": "Hz", "kelvin": "K", "kelvins": "K", "pascals": "Pa", "pascal": "Pa", "grams": "g",
    "kilograms": "kg", "minutes": "min", "minute": "min", "hours": "h", "hour": "h", "radians": "rad", "radian": "rad",
    "farads": "F", "henries": "H", "teslas": "T", "coulombs": "C", "days": "d",
}

# Count and money units (Stage 15, non-physics control set). Each counted noun is its OWN dimension, so "12 cookies" never grades
# as "12 students" and no count is convertible to another noun or to a physical unit. `dollars` is the money dimension. `times`
# (a scale factor) is its own dimension as well: a bare `1` stays excluded from conversion exactly as for physical units, so a
# bare number is never accepted for a unit-bearing target. The registry is deliberately closed: an unlisted noun is an UNKNOWN_UNIT
# (wrong under every view, flagged), and a new noun is added here by dated amendment. Kept apart from `ALIASES` because the H4
# trace extractor reads `ALIASES` to recognise unit words.
COUNT_UNITS = {
    "dollars": "money", "cookies": "cookies", "pencils": "pencils", "seats": "seats", "stickers": "stickers",
    "sandwiches": "sandwiches", "students": "students", "rooms": "rooms", "points": "points", "books": "books",
    "seedlings": "seedlings", "buses": "buses", "sheets": "sheets", "times": "times",
}  # canonical (plural) form -> dimension key; every factor is 1 (money has only dollars)
COUNT_ALIASES = {
    "dollar": "dollars", "$": "dollars", "usd": "dollars", "cookie": "cookies", "pencil": "pencils", "seat": "seats",
    "sticker": "stickers", "sandwich": "sandwiches", "student": "students", "room": "rooms", "point": "points", "book": "books",
    "seedling": "seedlings", "bus": "buses", "sheet": "sheets", "time": "times",
}


def canonical_unit(unit: str) -> str:
    from physmon.benchmark.v2 import dimensions as dm

    cleaned = vs.normalise_unit(unit).replace("µ", "μ")
    if cleaned in dm.UNITS:
        return cleaned
    lowered = cleaned.lower()
    if lowered in ALIASES:
        return ALIASES[lowered]
    if lowered in COUNT_UNITS:
        return lowered
    return COUNT_ALIASES.get(lowered, cleaned)


def conversion_ratio(from_unit: str, to_unit: str) -> float | None:
    """The factor that turns a value in `from_unit` into `to_unit`, or None if either is unknown, they differ in dimension, or one is `1`."""

    from physmon.benchmark.v2 import dimensions as dm

    a, b = canonical_unit(from_unit), canonical_unit(to_unit)
    if a in COUNT_UNITS or b in COUNT_UNITS:
        return 1.0 if a in COUNT_UNITS and b in COUNT_UNITS and COUNT_UNITS[a] == COUNT_UNITS[b] else None
    if a == "1" or b == "1" or a not in dm.UNITS or b not in dm.UNITS:
        return None
    ua, ub = dm.UNITS[a], dm.UNITS[b]
    return ua.factor / ub.factor if ua.dim == ub.dim else None


def classify_convertible(parsed: vs.ParsedOutput, gold_value: float, gold_unit: str) -> str:
    """`correct`, `wrong`, or the parse status; equal to `classify_answer` when the units already match."""

    if parsed.status != "PARSED":
        return parsed.status
    if parsed.unit == vs.normalise_unit(gold_unit) or canonical_unit(parsed.unit) == canonical_unit(gold_unit):
        ratio = 1.0
    else:
        ratio = conversion_ratio(parsed.unit, gold_unit)
        if ratio is None:
            return "wrong"
    converted = parsed.value * ratio
    error = abs(converted - gold_value)
    half = vs.half_unit_in_last_place(parsed.value_text) * ratio
    right = error <= half * (1 + 1e-9) and error <= vs.COARSE_REL_TOL * max(abs(gold_value), 1e-300)
    return "correct" if right else "wrong"
