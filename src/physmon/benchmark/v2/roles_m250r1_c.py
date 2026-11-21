"""M250 repair round 1 (journal J15.1-059) of `roles_m250_c`: the specs the two-judge panel rejected (any high flag) or whose sentences the
blind naturalness rater rated artificial, repaired; every other spec is the `roles_m250_c` object, unchanged.

Brief: `/scratch/pabitra/physmon/repair_m250_r1/briefs/roles_m250_c.md` (built by `scripts/v2/s207_m250_repair_briefs.py` from
`docs/validation/v2/llm_panel/admission_m250/runs/score_two_judges/`). No model output exists on any of these structures, so they may
still be edited (dataset admission standard, preamble). Wording rules 1-8 of `roles_m250_c` apply to every changed sentence.

`CHANGES` records, per changed structure, each finding and how it was resolved; `DROPPED` holds structures that could not be repaired
(they move to `INFEASIBLE` with the reason and are replaced in a later batch).
"""

from __future__ import annotations

import dataclasses

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import rolevalue as rv
from physmon.benchmark.v2 import rolevalue_v2 as r2
from physmon.benchmark.v2 import roles_m250_c as SRC

OLD: dict[str, r2.RoleSpecV2] = dict(getattr(SRC, "ROLE_SPECS", None) or SRC.SPECS)
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


P = rv.Phrasing
_rep = dataclasses.replace


def _note(sid: str, text: str) -> str:
    return f"{OLD[sid].notes} M250 r1: {text}".strip()


# --- S51 -------------------------------------------------------------------------------------------------------------------------
_S51 = OLD["S51"]
_S51_K = _rep(_S51.conditional, spec=_rep(_S51.conditional.spec, phrasings=(
    P("k0", "has a mechanical stop that allows a compression ratio of at most"), _S51.conditional.spec.phrasings[1])))
FIXED["S51"] = _rep(
    _S51, conditional=_S51_K,
    scene_clause="A second cylinder fitted with a piston, which already holds some gas, stands beside the first.",
    pairs=(
        _rep(_S51.pairs[0], r_attach="let into the first cylinder"),
        _rep(_S51.pairs[1],
             frame="{relation}, a further {value} {unit} of the same gas at the same temperature was let into the first cylinder.",
             r_attach="Before the compression began", d_attach="For an earlier run only",
             d_rationale="The further gas was let into the cylinder for an earlier run only, which is over; the cylinder of the stated "
                         "run holds only its stated amount of gas."),
    ),
    notes=_note("S51", "K0 is a limit wording ('has a mechanical stop that allows a compression ratio of at most'), not a stop at the "
                       "limit; R1/D1 are events ('a further ... was let into the first cylinder', before the compression began / for an "
                       "earlier run only); the second cylinder already holds gas so 'a further' reads naturally in D0/N0."))
CHANGES["S51"] = (
    ("claude+gpt high contradictory_distractor_statement / gpt high hidden_coupling on K0 'The piston stops at a compression ratio of 15.'",
     "K0 now 'The piston has a mechanical stop that allows a compression ratio of at most 15.' (a limit, not a stopping ratio; "
     "no longer contradicts ratio 8 and is no endpoint)"),
    ("R1 artificial 'In this run, the cylinder also held a further 1.3 mol ...' (contradicts 0.5 mol)",
     "R1 'Before the compression began, a further 1.3 mol of the same gas at the same temperature was let into the first cylinder.' "
     "(an addition before the compression, like R0)"),
    ("D1/N1 slightly_artificial 'the cylinder also held a further ...'",
     "D1/N1 share the new event frame: 'For an earlier run only, a further {v} of the same gas ... was let into the first cylinder.'"),
    ("D0/N0 slightly_artificial (a further amount into a second cylinder never said to hold gas)",
     "scene clause: 'A second cylinder fitted with a piston, which already holds some gas, stands beside the first.'; R0 attaches to "
     "'the first cylinder'"),
)

# --- S52 -------------------------------------------------------------------------------------------------------------------------
_S52 = OLD["S52"]
FIXED["S52"] = _rep(
    _S52,
    scene_clause="A second container, also perfectly insulated, holds warm water beside the first one. The water in the first "
                 "container is stirred to one temperature and does not boil or evaporate. The water is at its starting temperature "
                 "from the moment it is poured into the first container, before anything is done to it.",
    pairs=(
        _rep(_S52.pairs[0], r_attach="the water in the first container"),
        _rep(_S52.pairs[1], frame="{relation}, a heater warmed the water by {value} {unit} before the ice was added.",
             r_attach="After the water was poured in", d_attach="In an earlier run"),
    ),
    notes=_note("S52", "scene clause fixes the starting temperature as the temperature at pouring, before any heating (one reading); "
                       "R0 names 'the first container'; R1 'After the water was poured in, a heater warmed the water by {v} before the "
                       "ice was added.'"))
CHANGES["S52"] = (
    ("gpt high insufficient_boundary_condition: before or after heating for the stated 40 K; R0 'the container' ambiguous; claude medium same",
     "scene clause adds 'The water is at its starting temperature from the moment it is poured into the first container, before "
     "anything is done to it.'; R0 'the water in the container' -> 'the water in the first container'; R1 'In this run, a heater "
     "warmed ...' -> 'After the water was poured in, a heater warmed the water by 17 K before the ice was added.'"),
    ("R1 slightly_artificial 'In this run, ...'", "same R1 rewrite (ties the heating to the pouring and to the ice)"),
)

# --- S53 -------------------------------------------------------------------------------------------------------------------------
_S53 = OLD["S53"]
_S53_K = _rep(_S53.conditional, spec=_rep(_S53.conditional.spec, phrasings=(
    P("k0", "is destroyed outright, leaving the brick bare, if the temperature difference across the wall exceeds"),
    P("k1", "burns away completely, leaving only the brick, once the temperature difference across the wall exceeds"))))
FIXED["S53"] = _rep(
    _S53, conditional=_S53_K,
    pairs=(
        _S53.pairs[0],
        _rep(_S53.pairs[1], r_attach="Just before the heat flow was measured", d_attach="In an earlier test of the wall"),
    ),
    notes=_note("S53", "K phrasings now say the foam is destroyed and the brick alone remains above the limit (so the outside-regime "
                       "reference dT / R1 is the stated physics, not an assumption); pair 1 R ties the raise to the measurement."))
CHANGES["S53"] = (
    ("gpt high missing_assumption: outside-regime P = dT/R1 needs the foam to vanish, 'keeps its shape' / 'rated' do not say that",
     "K0 'The foam is destroyed outright, leaving the brick bare, if the temperature difference across the wall exceeds 75 K.'; "
     "K1 'The foam burns away completely, leaving only the brick, once the temperature difference across the wall exceeds 75 K.' "
     "(old: 'keeps its shape only for temperature differences below' / 'is rated for temperature differences of up to')"),
    ("R1 low ambiguity + R1/D1 slightly_artificial 'For this survey ... was raised' / 'In an earlier survey ...'",
     "R1 'Just before the heat flow was measured, the temperature difference ... was raised by 13 K.'; D1 'In an earlier test of the "
     "wall, ...'"),
)

# --- S54 -------------------------------------------------------------------------------------------------------------------------
_S54 = OLD["S54"]
FIXED["S54"] = _rep(
    _S54,
    scene_clause="A metal bracket and a metal disc hang from a frame nearby. The radius given for the second sphere is its radius as "
                 "it was made, and the temperature given is that of its outer surface.",
    pairs=(
        _rep(_S54.pairs[0], r_attach="cast around the second sphere", d_attach="cast around the bracket"),
        _rep(_S54.pairs[1], frame="A {value} {unit} layer of the same metal was {relation}.", r_attach="cast around the second sphere",
             d_attach="cast around the disc"),
    ),
    notes=_note("S54", "scene clause: the stated radius is the radius as made, the stated temperature that of the outer surface (one "
                       "reading for before/after the layer); the layer is cast around the object (not 'plated', which is thin)."))
CHANGES["S54"] = (
    ("claude+gpt high insufficient_boundary_condition: stated 10 cm before or after the layer",
     "scene clause adds 'The radius given for the second sphere is its radius as it was made, and the temperature given is that of "
     "its outer surface.'"),
    ("R0/R1/D0/D1 artificial 'A 4.5 cm layer of the same metal is plated onto ...' (plating is thin; claude low)",
     "'A 4.5 cm layer of the same metal is cast around the second sphere / the bracket.' and '... was cast around the second sphere / "
     "the disc.'"),
)

# --- S56 -------------------------------------------------------------------------------------------------------------------------
_S56 = OLD["S56"]
_S56_C = _rep(_S56.cancelling, spec=_rep(_S56.cancelling.spec, phrasings=(P("c0", "is tested for"), _S56.cancelling.spec.phrasings[1])))
FIXED["S56"] = _rep(
    _S56, cancelling=_S56_C,
    scene_clause="A chest freezer stands beside the refrigerator. The refrigerator runs steadily. The electrical power asked for is "
                 "only that drawn by the compressor motor that drives the refrigeration cycle.",
    pairs=(
        _rep(_S56.pairs[0], frame="A {value} {unit} lamp is kept lit {relation}.", r_attach="inside the refrigerator",
             d_attach="above the chest freezer",
             d_rationale="A lamp above the chest freezer heats the kitchen, which is a reservoir at constant temperature; the "
                         "refrigerator's interior receives only its stated leak."),
        _rep(_S56.pairs[1], r_attach="while the refrigerator ran steadily"),
    ),
    notes=_note("S56", "scene clause: the asked power is the compressor motor's alone (a lamp's power is not counted); D0 lamp above the "
                       "freezer (purposeful); R1 'while the refrigerator ran steadily'; C0 'is tested for'."))
CHANGES["S56"] = (
    ("gpt high missing_assumption: electrical input excludes the lamp's own consumption",
     "scene clause adds 'The electrical power asked for is only that drawn by the compressor motor that drives the refrigeration cycle.'"),
    ("D0/N0 artificial 'A 55 W lamp is kept lit inside the chest freezer.'", "'A 55 W lamp is kept lit above the chest freezer.'"),
    ("R1 low 'during this test' (no test is introduced)", "R1 '... kept lit inside the refrigerator while the refrigerator ran steadily.'"),
    ("C0 slightly_artificial 'The refrigerator runs steadily for 90 min.' (repeats the scene)", "'The refrigerator is tested for 90 min.'"),
)

# --- S57 -------------------------------------------------------------------------------------------------------------------------
_S57 = OLD["S57"]
FIXED["S57"] = _rep(
    _S57,
    scene_clause="A second tank, holding some water of its own, stands beside the first.",
    pairs=(
        _rep(_S57.pairs[0], r_attach="poured into the first tank"),
        _rep(_S57.pairs[1],
             frame="{relation}, a further {value} {unit} of water at the same temperature was poured into the first tank.",
             r_attach="Before the engine was started", d_attach="For an earlier experiment only",
             d_rationale="The further water was poured into the tank for an earlier experiment only, which is over; in the stated "
                         "experiment the engine cools only the stated mass of water."),
    ),
    notes=_note("S57", "R1/D1 are events ('a further ... was poured into the first tank'); the second tank holds some water so 'a "
                       "further' reads naturally in D0/N0; R0 names 'the first tank'."))
CHANGES["S57"] = (
    ("R1 artificial 'In this experiment, the tank also held a further 1.4 kg ...' (contradicts 2 kg; 'the tank' ambiguous)",
     "R1 'Before the engine was started, a further 1.4 kg of water at the same temperature was poured into the first tank.'"),
    ("D1/N1 slightly_artificial", "D1/N1 share the event frame ('For an earlier experiment only, a further ... was poured into the first tank.')"),
    ("D0/N0 slightly_artificial (a further amount into a tank described as empty)",
     "scene clause 'A second tank, holding some water of its own, stands beside the first.'"),
)

# --- S65 -------------------------------------------------------------------------------------------------------------------------
_S65 = OLD["S65"]
FIXED["S65"] = _rep(
    _S65,
    scene_clause="A glass trough, which is empty, stands beside the fibre. The flat end face of the fibre is perpendicular to its axis.",
    pairs=(
        _rep(_S65.pairs[0], frame="A clear liquid {relation}; its refractive index is {value} {unit}.", nonnumeric_fill="well known"),
        _rep(_S65.pairs[1],
             frame="{relation}, the end of the fibre was held in a liquid instead of in the air; the refractive index of the liquid "
                   "is {value} {unit}.",
             nonnumeric_fill="well known"),
    ),
    notes=_note("S65", "scene clause states that the end face is perpendicular to the axis; the index goes into a second clause so the "
                       "N fill ('well known') reads grammatically; R1 says the liquid is there instead of the air."))
CHANGES["S65"] = (
    ("gpt high missing_assumption: flat end not stated perpendicular to the axis",
     "scene clause adds 'The flat end face of the fibre is perpendicular to its axis.'"),
    ("N1 artificial 'a liquid whose refractive index is a known value' (gpt high rendering_not_minimal is 5.3b, not counted)",
     "N fill 'well known' in a closing clause: 'For an earlier experiment only, the end of the fibre was held in a liquid instead of "
     "in the air; the refractive index of the liquid is well known.'"),
    ("claude medium R1 'was dipped into a liquid' does not say the liquid replaces the air",
     "R1/D1 frame 'the end of the fibre was held in a liquid instead of in the air; the refractive index of the liquid is {v}.'"),
)

# --- S66 -------------------------------------------------------------------------------------------------------------------------
_S66 = OLD["S66"]
FIXED["S66"] = _rep(
    _S66,
    pairs=(_rep(_S66.pairs[0], nonnumeric_fill="a different"), _rep(_S66.pairs[1], nonnumeric_fill="a different")),
    notes=_note("S66", "N fill 'a different' (was 'a certain') so N0/N1 read naturally: 'Light of a different wavelength ...'."))
CHANGES["S66"] = (
    ("N0 artificial 'Light of a certain wavelength now enters the second spectrometer.'",
     "'Light of a different wavelength now enters the second spectrometer.' (N1 likewise)"),
)

# --- S67 -------------------------------------------------------------------------------------------------------------------------
_S67 = OLD["S67"]
FIXED["S67"] = _rep(
    _S67,
    pairs=(
        _S67.pairs[0],
        _rep(_S67.pairs[1], frame="{relation}, the output of the source of the beam was increased by {value} {unit}.",
             r_attach="After the beam was set up and before the transmitted power was measured",
             d_attach="In an earlier experiment, before the transmitted power was measured"),
    ),
    notes=_note("S67", "R1 places the rise after the beam was set up (the stated beam power) and before the measurement: one reading "
                       "(incident power = stated + rise)."))
CHANGES["S67"] = (
    ("gpt high insufficient_boundary_condition + R1 artificial 'increased by 35 mW before the beam reached the plate'",
     "R1 'After the beam was set up and before the transmitted power was measured, the output of the source of the beam was "
     "increased by 35 mW.'; D1 'In an earlier experiment, before the transmitted power was measured, ...'"),
)

# --- S71 -------------------------------------------------------------------------------------------------------------------------
_S71 = OLD["S71"]
FIXED["S71"] = _rep(
    _S71,
    scene_clause="A second lamp, of a different colour, shines on a screen nearby. No electric or magnetic field acts on the emitted "
                 "electrons. The wavelength given for the light is the one that its source emits when it is first switched on.",
    pairs=(
        _S71.pairs[0],
        _rep(_S71.pairs[1],
             frame="{relation}, the source of the light was tuned to a wavelength {value} {unit} shorter.",
             r_attach="Before the electrons were measured", d_attach="In an earlier experiment", nonnumeric_fill="slightly"),
    ),
    notes=_note("S71", "scene clause: the given wavelength is what the source first emits; R1 'Before the electrons were measured, the "
                       "source of the light was tuned to a wavelength {v} shorter.' (one reading: 250 nm is the original)."))
CHANGES["S71"] = (
    ("gpt high other + claude medium: R1 'shortened by 55 nm before it reached the metal surface' (250 nm original or arriving?); R1 artificial",
     "scene clause adds 'The wavelength given for the light is the one that its source emits when it is first switched on.'; R1 "
     "'Before the electrons were measured, the source of the light was tuned to a wavelength 55 nm shorter.'; D1 'In an earlier "
     "experiment, the source of the light was tuned to a wavelength 55 nm shorter.'; N1 fill 'slightly' (gpt rendering_not_minimal is 5.3b)"),
)

ROLE_SPECS: dict[str, r2.RoleSpecV2] = {sid: FIXED.get(sid, spec) for sid, spec in OLD.items() if sid not in DROPPED}
SPECS = ROLE_SPECS
INFEASIBLE: dict[str, str] = {**dict(SRC.INFEASIBLE), **{sid: f"repair round 1: {why}" for sid, why in DROPPED.items()}}
STRUCTURE_FACTORIES = {**SRC.STRUCTURE_FACTORIES, **STRUCTURE_OVERRIDES}


def structure(structure_id: str) -> gr.Structure:
    """The structure (repaired factory if any) with the repaired spec's scene clause appended to its base context."""

    return r2.with_scene(STRUCTURE_FACTORIES[structure_id](), ROLE_SPECS[structure_id].scene_clause)
