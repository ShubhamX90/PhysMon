"""M250 repair round 2 (journal J15.1-061) of `roles_m250r1_c`: the specs the two-judge re-review rejected (any high flag) or whose sentences
the blind naturalness rater rated artificial, repaired again; every other spec is the `roles_m250r1_c` object, unchanged.

Brief: `/scratch/pabitra/physmon/repair_m250_r2/briefs/roles_m250r1_c.md` (`scripts/v2/s207_m250_repair_briefs.py` from
`docs/validation/v2/llm_panel/admission_m250r1/runs/score_two_judges/`). No model output exists on any of these structures. The round-1
history of each structure is in `roles_m250r1_c.CHANGES`; wording rules 1-8 of the original module apply.

`CHANGES` records, per changed structure, each finding and how it was resolved; `DROPPED` holds structures that could not be repaired.
"""

from __future__ import annotations

import dataclasses

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import rolevalue as rv
from physmon.benchmark.v2 import rolevalue_v2 as r2
from physmon.benchmark.v2 import roles_m250r1_c as SRC

P = rv.Phrasing
OLD: dict[str, r2.RoleSpecV2] = dict(SRC.ROLE_SPECS)
TARGET_TERMS = SRC.TARGET_TERMS
NO_C: dict[str, str] = dict(SRC.NO_C)
NO_K: dict[str, str] = dict(SRC.NO_K)
K_KINDS = dict(getattr(SRC, "K_KINDS", {}) or {})
if hasattr(SRC, "CERT_VERSION"):
    CERT_VERSION = SRC.CERT_VERSION

# structure id -> tuple of (finding it answers, resolution); one entry per changed structure
CHANGES: dict[str, tuple[tuple[str, str], ...]] = {}

# structure id -> repaired spec (built from OLD[sid] with dataclasses.replace)
FIXED: dict[str, r2.RoleSpecV2] = {}

# structure id -> replacement structure factory (NEW structures only, when the base problem itself must change); default: SRC's
STRUCTURE_OVERRIDES: dict[str, object] = {}

# structure id -> reason the structure could not be repaired (it is removed from the specs and recorded as infeasible)
DROPPED: dict[str, str] = {}

_rep = dataclasses.replace


def _note(sid: str, text: str) -> str:
    return f"{OLD[sid].notes} M250 r2: {text}".strip()


# --- S52 -------------------------------------------------------------------------------------------------------------------------
_S52 = OLD["S52"]
FIXED["S52"] = _rep(
    _S52,
    pairs=(
        _rep(_S52.pairs[0], nonnumeric_fill="a small amount"),
        _rep(_S52.pairs[1], frame="{relation}, a heater warmed the water by {value} {unit}.",
             r_attach="Before the ice was added", d_attach="In an earlier run", nonnumeric_fill="a small amount"),
    ),
    notes=_note("S52", "N fill 'a small amount' (the unit is replaced together with the number); pair 1 'Before the ice was added, a "
                       "heater warmed the water by {v}.' (the scene clause already puts the starting temperature before any heating)."))
CHANGES["S52"] = (
    ("gpt high inconsistent_units: N0/N1 'a few kelvin' keep the unit kelvin although unit=null",
     "N fill 'a few kelvin' -> 'a small amount' ('... warms the water in the second container by a small amount'), so no unit is left"),
    ("R1 slightly_artificial 'After the water was poured in, a heater warmed the water by 17 K before the ice was added.'",
     "R1 'Before the ice was added, a heater warmed the water by 17 K.'; D1/N1 'In an earlier run, a heater warmed the water by ...'"),
    ("gpt high rendering_not_minimal (5.3b, not counted)", "numeral-free N sentence kept by design"),
)

# --- S53 -------------------------------------------------------------------------------------------------------------------------
_S53 = OLD["S53"]
FIXED["S53"] = _rep(
    _S53, conditional=None,
    notes=_note("S53", "K removed (foam 'burns away' above a 75 K temperature difference is physically implausible); C and pairs unchanged."))
NO_K["S53"] = ("A temperature-difference limit at which the foam is destroyed is not a believable property of building insulation at "
               "differences of tens of kelvin; a rating that merely warns would not fix the outside-regime physics.")
CHANGES["S53"] = (
    ("K1 artificial 'The foam burns away completely, leaving only the brick, once the temperature difference across the wall exceeds 75 K.' "
     "(K0 slightly_artificial likewise)",
     "K quantity removed (conditional=None, reason in NO_K): no honest wording makes a foam-destruction threshold of tens of kelvin plausible"),
    ("gpt high rendering_not_minimal (5.3b, not counted)", "numeral-free N sentence kept by design"),
)

# --- S54 -------------------------------------------------------------------------------------------------------------------------
_S54 = OLD["S54"]
FIXED["S54"] = _rep(
    _S54,
    scene_clause="A metal bracket and a metal disc, made of the same metal as the spheres, hang from a frame nearby. The radius given "
                 "for the second sphere is its radius as it was made, and the temperature given is that of its outer surface.",
    notes=_note("S54", "scene clause says the bracket and disc are of the same metal as the spheres, so thickening them by casting a layer "
                       "of that metal reads as an ordinary workshop step and 'the same metal' has one referent."))
CHANGES["S54"] = (
    ("D0/N0 artificial 'A 4.5 cm layer of the same metal is cast around the bracket.' (pointless action; D1/N1 'the same metal' vaguely referenced)",
     "scene clause 'A metal bracket and a metal disc, made of the same metal as the spheres, hang from a frame nearby.' so the bracket and "
     "disc are thickened in the same workshop manner as the sphere; sentences unchanged"),
    ("gpt high rendering_not_minimal (5.3b, not counted)", "'thin' N fill kept by design"),
)

# --- S56 -------------------------------------------------------------------------------------------------------------------------
_S56 = OLD["S56"]
FIXED["S56"] = _rep(
    _S56,
    scene_clause="A chest freezer stands beside the refrigerator. The refrigerator runs steadily. Heat leaks into the interior through its walls at "
                 "the rate given. The electrical power asked for is only that drawn by the compressor "
                 "motor that drives the refrigeration cycle.",
    pairs=(
        _S56.pairs[0],
        _rep(_S56.pairs[1], frame="A {value} {unit} lamp {relation}.",
             r_attach="stays lit inside the refrigerator for as long as it runs steadily",
             d_attach="was kept lit inside the refrigerator in an earlier test only"),
    ),
    notes=_note("S56", "scene clause says heat leaks in at the rate given (the lamp adds to it); R1 'stays lit inside the refrigerator for as "
                       "long as it runs steadily' puts the lamp in the stated steady run, D1 is an earlier test only."))
CHANGES["S56"] = (
    ("gpt high insufficient_boundary_condition: R1 'was kept lit ... while the refrigerator ran steadily' is a past run, not the evaluated one",
     "R1 'A 55 W lamp stays lit inside the refrigerator for as long as it runs steadily.' (present, the scene's steady run); D1 'A 55 W lamp "
     "was kept lit inside the refrigerator in an earlier test only.'"),
    ("claude medium: 200 W read as total removal rate", "scene clause adds 'Heat leaks into the interior through its walls at the "
     "rate given.'"),
    ("D1/N1 slightly_artificial 'for an earlier test only' stilted", "'... in an earlier test only'"),
)

# --- S65 -------------------------------------------------------------------------------------------------------------------------
_S65 = OLD["S65"]
FIXED["S65"] = _rep(
    _S65,
    pairs=(
        _S65.pairs[0],
        _rep(_S65.pairs[1],
             frame="{relation}, the air in front of the fibre end was replaced by a clear liquid; its refractive index is {value} {unit}.",
             r_attach="Before the light was sent in", d_attach="For an earlier experiment only"),
    ),
    notes=_note("S65", "R1/D1 no longer say the fibre end 'was held in a liquid instead of in the air' (contradicted the opening); they "
                       "say the air in front of the end was replaced by a clear liquid, like R0, timed before the light was sent in."))
CHANGES["S65"] = (
    ("R1 artificial 'For this experiment, the end of the fibre was held in a liquid instead of in the air; ...' (contradicts 'from air')",
     "R1 'Before the light was sent in, the air in front of the fibre end was replaced by a clear liquid; its refractive index is 1.2.'; "
     "D1 'For an earlier experiment only, the air in front of the fibre end was replaced by a clear liquid; ...'"),
)

# --- S67 -------------------------------------------------------------------------------------------------------------------------
_S67 = OLD["S67"]
_S67_K = _rep(_S67.conditional, spec=_rep(_S67.conditional.spec, phrasings=(
    P("k0", "is damaged if the beam power exceeds"), P("k1", "is damaged by beams stronger than"))))
FIXED["S67"] = _rep(
    _S67, conditional=_S67_K,
    notes=_note("S67", "K0 is now a damage statement ('is damaged if the beam power exceeds 350 mW'), like K1, so both phrasings state "
                       "the threshold the K claim rests on."))
CHANGES["S67"] = (
    ("gpt high other: K0 'is rated for a beam power of up to 350 mW' is an operating rating, not a damage threshold",
     "K0 'The glass plate is damaged if the beam power exceeds 350 mW.' (K1 'is damaged by beams stronger than' unchanged)"),
)

ROLE_SPECS: dict[str, r2.RoleSpecV2] = {sid: FIXED.get(sid, spec) for sid, spec in OLD.items() if sid not in DROPPED}
SPECS = ROLE_SPECS
INFEASIBLE: dict[str, str] = {**dict(SRC.INFEASIBLE), **{sid: f"repair round 2: {why}" for sid, why in DROPPED.items()}}
STRUCTURE_FACTORIES = {**SRC.STRUCTURE_FACTORIES, **STRUCTURE_OVERRIDES}


def structure(structure_id: str) -> gr.Structure:
    """The structure (repaired factory if any) with the repaired spec's scene clause appended to its base context."""

    return r2.with_scene(STRUCTURE_FACTORIES[structure_id](), ROLE_SPECS[structure_id].scene_clause)
