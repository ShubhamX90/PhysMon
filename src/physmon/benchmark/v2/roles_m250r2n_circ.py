"""M250 repair round 2 (journal J15.1-061) of `roles_m250r1n_circ`: the specs the two-judge re-review rejected (any high flag) or whose sentences
the blind naturalness rater rated artificial, repaired again; every other spec is the `roles_m250r1n_circ` object, unchanged.

Brief: `/scratch/pabitra/physmon/repair_m250_r2/briefs/roles_m250r1n_circ.md` (`scripts/v2/s207_m250_repair_briefs.py` from
`docs/validation/v2/llm_panel/admission_m250r1/runs/score_two_judges/`). No model output exists on any of these structures. The round-1
history of each structure is in `roles_m250r1n_circ.CHANGES`; wording rules 1-8 of the original module apply.

`CHANGES` records, per changed structure, each finding and how it was resolved; `DROPPED` holds structures that could not be repaired.
"""

from __future__ import annotations

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import rolevalue_v2 as r2
from physmon.benchmark.v2 import roles_m250r1n_circ as SRC

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

import dataclasses  # noqa: E402

from physmon.benchmark.v2 import rolevalue as rv  # noqa: E402

rep = dataclasses.replace
Pair = r2.PhrasePair
EVENT = r2.D_KIND_OTHER_EVENT
CO = r2.D_KIND_CO_PRESENT


def _note(sid: str, text: str) -> str:
    return f"{OLD[sid].notes} M250 r2: {text}"


# --- S265 -----------------------------------------------------------------------------------------------------------------------------
_P = OLD["S265"].pairs[0]
FIXED["S265"] = rep(
    OLD["S265"],
    pairs=(rep(_P, frame="Before the load voltage is measured, the rms voltage supplied to {relation} is raised by {value} {unit}.",
               nonnumeric_fill="a small amount"), OLD["S265"].pairs[1]),
    notes=_note("S265", "pair 0 reworded without 'a further' ('the rms voltage supplied to the lamp is raised by {v}')."))
CHANGES["S265"] = (
    ("rating N0 artificial / D0 slightly_artificial: 'the rms supply voltage of the lamp is raised by a further small amount'",
     "pair 0 now 'Before the load voltage is measured, the rms voltage supplied to the lamp is raised by 14 V.' (N0: 'by a small "
     "amount'); R0 the same with 'the transformer'"),
)

# --- S266 -----------------------------------------------------------------------------------------------------------------------------
_P0, _P1 = OLD["S266"].pairs
FIXED["S266"] = rep(
    OLD["S266"],
    pairs=(rep(_P0, frame="Before the winding losses are measured, an additional {value} {unit} resistive load is connected to "
                          "{relation}.", nonnumeric_fill="small"),
           rep(_P1, frame="The secondary winding also fed an additional {value} {unit} resistive load {relation}.",
               nonnumeric_fill="small")),
    notes=_note("S266", "N0/N1 read 'an additional small resistive load' instead of 'an extra small amount of resistive load'."))
CHANGES["S266"] = (
    ("rating N0 artificial: 'an extra small amount of resistive load is connected to the charger'",
     "frame 'an additional {value} {unit} resistive load is connected to ...'; N0 'an additional small resistive load'"),
    ("rating N1/D1/D0 slightly_artificial", "pair 1 'The secondary winding also fed an additional 140 W resistive load ...'; N1 "
                                            "'an additional small resistive load'"),
)

# --- S267 -----------------------------------------------------------------------------------------------------------------------------
_P0 = OLD["S267"].pairs[0]
FIXED["S267"] = rep(
    OLD["S267"],
    scene_clause=OLD["S267"].scene_clause.replace("small battery", "its own small cell"),
    pairs=(rep(_P0, frame="Before the switch is closed, an extra {value} {unit} capacitor is wired in parallel with {relation}.",
               nonnumeric_fill="small"), OLD["S267"].pairs[1]),
    notes=_note("S267", "scene clause says the flash unit is charged from its own small cell, so 'the battery' means only the "
                        "circuit's battery; pair 0 'an extra {v} capacitor is wired in parallel with ...'."))
CHANGES["S267"] = (
    ("rating N0 artificial: 'a further small amount of capacitance is wired in parallel with the flash unit'",
     "frame 'an extra {value} {unit} capacitor is wired in parallel with ...'; N0 'an extra small capacitor'"),
    ("gpt medium other: 'the battery' can refer to either circuit", "scene clause now 'charged from its own small cell'"),
)

# --- S268 -----------------------------------------------------------------------------------------------------------------------------
_P0 = OLD["S268"].pairs[0]
FIXED["S268"] = rep(
    OLD["S268"],
    pairs=(rep(_P0, frame="Before the switch is closed, a second ideal battery of {value} {unit} emf is joined in series with "
                          "{relation}, in the same direction.", nonnumeric_fill="modest"),
           Pair("p1", "A second ideal battery of {value} {unit} emf was joined in series with the first, in the same direction, "
                      "{relation}.", "before the switch was closed", "for an earlier run only", EVENT,
                OLD["S268"].pairs[1].d_rationale, OLD["S268"].pairs[1].conditions_preserved, "modest")),
    notes=_note("S268", "N0/N1 'of modest emf'; R1 'A second ideal battery ... was joined in series with the first, in the same "
                        "direction, before the switch was closed'."))
CHANGES["S268"] = (
    ("rating N0 artificial: 'a second ideal battery of small emf is joined in series with the cell of the doorbell'",
     "N0 'a second ideal battery of modest emf is joined in series with ...'"),
    ("rating R1 slightly_artificial: 'The circuit contained ... from the moment the switch was closed'",
     "R1 'A second ideal battery of 7.5 V emf was joined in series with the first, in the same direction, before the switch was "
     "closed.' (D1: 'for an earlier run only')"),
)

# --- S270 -----------------------------------------------------------------------------------------------------------------------------
S270_P0 = Pair(
    "p0", "From the moment the trolley sets off, a technician walks steadily along it directly away from the lorry at {value} {unit}, "
          "carrying {relation}.", "the recorder", "the toolbox", CO,
    "A technician who carries the toolbox along the trolley moves the toolbox only; the recorder keeps the stated speed of the "
    "trolley, so the reflected sound and its shift are the stated ones.", ("in still air", "constant"), "a steady pace",
    before_context_reason="The R sentence refers to 'the recorder' and to the trolley before the context introduces them.")
S270_P1 = Pair(
    "p1", "The recorder was carried along the trolley by a technician walking steadily directly away from the lorry at {value} {unit} "
          "{relation}.", "from the moment the trolley set off", "for an earlier run only", EVENT,
    "The recorder was carried along the trolley in an earlier run, for that run only; in the stated run it rides still on the trolley "
    "at the stated speed.", ("in still air", "constant"), "a steady pace")
FIXED["S270"] = rep(
    OLD["S270"], quantity_phrase="a walking speed along the trolley", values=(1.1, 1.6, 2.4), heldout_values=(1.4, 2.0),
    relevant=rv.RelevantWiring("v", "add", "A technician who carries the recorder along the trolley at a further speed q makes the "
                                           "speed of the recorder v + q, which changes the Doppler shift of the reflected sound."),
    pairs=(S270_P0, S270_P1),
    notes=_note("S270", "the conveyor is replaced by a technician walking along the trolley (speeds 1.1-2.4 m/s); R carries the "
                        "recorder, D0 the toolbox; the walk starts when the trolley sets off, so the recorder speed is v + q "
                        "throughout."))
CHANGES["S270"] = (
    ("rating R0/D0/N0/R1/D1/N1 artificial or slightly_artificial: a conveyor belt on the trolley",
     "R0 'From the moment the trolley sets off, a technician walks steadily along it directly away from the lorry at 1.5 m/s, "
     "carrying the recorder.'; D0 '... carrying the toolbox.'; R1 'The recorder was carried along the trolley by a technician walking "
     "steadily directly away from the lorry at 1.5 m/s from the moment the trolley set off.'; D1 '... for an earlier run only.'; "
     "N0/N1 'at a steady pace'; speeds now 1.1-2.4 m/s (a walking pace)"),
)

# --- S271 -----------------------------------------------------------------------------------------------------------------------------
_P0 = OLD["S271"].pairs[0]
FIXED["S271"] = rep(
    OLD["S271"],
    scene_clause="A metal wire hangs from a hook beside the bench.",
    scene_refs=("wire",),
    scene_object_rationale="A wire on a hook is a body of its own; lengthening it changes the wire only, so the clamped "
                           "rod, the tube and the dust heaps keep their stated values.",
    pairs=(rep(_P0, frame="Before the clamp is fitted, {relation} is lengthened by joining on an extra {value} {unit} of the same "
                          "metal and cross-section.", r_attach="the rod", d_attach="the wire", nonnumeric_fill="small amount"),
           Pair("p1", "A {value} {unit} length of the same metal and cross-section was joined onto one end of the rod {relation}.",
                "before the clamp was fitted", "for an earlier run only", EVENT, OLD["S271"].pairs[1].d_rationale,
                OLD["S271"].pairs[1].conditions_preserved, "short")),
    notes=_note("S271", "railing replaced by a wire on a hook; 'welding' replaced by 'joining'; R1 'A 32 cm length of the same "
                        "metal and cross-section was joined onto one end of the rod before the clamp was fitted'."))
CHANGES["S271"] = (
    ("rating D0/N0 artificial: lengthening the laboratory railing", "D0 'Before the clamp is fitted, the wire is lengthened by "
                                                                    "joining on an extra 32 cm of the same metal and cross-section.'"),
    ("rating R0/R1/N1 slightly_artificial", "R0 'joining on'; R1 'A 32 cm length of the same metal and cross-section was joined onto "
                                            "one end of the rod before the clamp was fitted.'; N1 'A short length ...'"),
)

# --- S272 -----------------------------------------------------------------------------------------------------------------------------


def _s272_factory() -> gr.Structure:
    base = SRC.STRUCTURE_FACTORIES["S272"]()
    old = "through a tap, so that the water surface falls at a constant"
    assert old in base.render.context
    return rep(base, render=rep(base.render, context=base.render.context.replace(
        old, "through a tap, which alone draws down the water surface at a constant")))


STRUCTURE_OVERRIDES["S272"] = _s272_factory
_C = OLD["S272"].cancelling
S272_C = rep(_C, spec=rep(_C.spec, intermediate_relations=(
    "the column between the open top and the falling water surface lengthens as L = q + vw t",
    "it later resonates when L plus the end correction is 13 lam / 4 and then 15 lam / 4, two successive odd numbers of quarter "
    "wavelengths (13 lam / 4 is about 218 cm, above every listed q)", "t = (L_n - q) / vw at each resonance")))
S272_P0 = Pair(
    "p0", "Before the first resonance is heard, a second tap is opened that alone draws down {relation} at {value} {unit}.",
    "the water level in the tube", "the level of the pond", CO,
    "A second tap that lowers the level of the pond acts on the pond only; the water in the tube keeps its stated fall speed, so "
    "the time between resonances is the stated one.", ("closed below by the water", "constant"), "a steady rate",
    before_context_reason="The R sentence refers to 'the tube' and to the resonances before the context introduces them.")
S272_P1 = Pair(
    "p1", "A second tap on the tube, which alone draws down the water level at {value} {unit}, was also open {relation}.",
    "from before the first resonance was heard", "for an earlier run only", EVENT,
    "The second tap was open in an earlier run, for that run only; in the stated run the water in the tube falls at the stated speed.",
    ("closed below by the water", "constant"), "a steady rate")
FIXED["S272"] = rep(
    OLD["S272"], cancelling=S272_C, pairs=(S272_P0, S272_P1),
    notes=_note("S272", "base context now says the tap alone draws down the surface at the stated speed, so a second tap adds to it; "
                        "R/D/N reworded 'a second tap ... alone draws down ...'; C relation text states the resonances used."))
CHANGES["S272"] = (
    ("gpt high missing_assumption: 1.5 cm/s must be the original tap's isolated contribution",
     "base context: 'drains steadily from the bottom through a tap, which alone draws down the water surface at a constant 1.5 cm/s'"),
    ("gpt high rendering_not_minimal (5.3b judge error, not counted)", "N sentences stay numeral-free by design"),
    ("rating N0/N1 artificial, R1/D0/D1 slightly_artificial",
     "R0 'Before the first resonance is heard, a second tap is opened that alone draws down the water level in the tube at 0.9 cm/s.'; "
     "D0 '... draws down the level of the pond ...'; R1 'A second tap on the tube, which alone draws down the water level at 0.9 cm/s, "
     "was also open from before the first resonance was heard.'; N 'at a steady rate'"),
    ("claude medium other: mode numbers give negative times for q = 130, 190 cm",
     "not an error: lam = 343/512 m = 67 cm, so 13 lam / 4 = 218 cm exceeds every listed q and the times are positive; relation text "
     "now says 'it later resonates' and gives 218 cm"),
)

ROLE_SPECS: dict[str, r2.RoleSpecV2] = {sid: FIXED.get(sid, spec) for sid, spec in OLD.items() if sid not in DROPPED}
SPECS = ROLE_SPECS
INFEASIBLE: dict[str, str] = {**dict(SRC.INFEASIBLE), **{sid: f"repair round 2: {why}" for sid, why in DROPPED.items()}}
STRUCTURE_FACTORIES = {**SRC.STRUCTURE_FACTORIES, **STRUCTURE_OVERRIDES}


def structure(structure_id: str) -> gr.Structure:
    """The structure (repaired factory if any) with the repaired spec's scene clause appended to its base context."""

    return r2.with_scene(STRUCTURE_FACTORIES[structure_id](), ROLE_SPECS[structure_id].scene_clause)
