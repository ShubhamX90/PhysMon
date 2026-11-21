"""M250 repair round 1 (journal J15.1-059) of `roles_m250n_circ`: the specs the two-judge panel rejected (any high flag) or whose sentences the
blind naturalness rater rated artificial, repaired; every other spec is the `roles_m250n_circ` object, unchanged.

Brief: `/scratch/pabitra/physmon/repair_m250_r1/briefs/roles_m250n_circ.md` (built by `scripts/v2/s207_m250_repair_briefs.py` from
`docs/validation/v2/llm_panel/admission_m250/runs/score_two_judges/`). No model output exists on any of these structures, so they may
still be edited (dataset admission standard, preamble). Wording rules 1-8 of `roles_m250n_circ` apply to every changed sentence.

`CHANGES` records, per changed structure, each finding and how it was resolved; `DROPPED` holds structures that could not be repaired
(they move to `INFEASIBLE` with the reason and are replaced in a later batch).
"""

from __future__ import annotations

import dataclasses

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import rolevalue as rv
from physmon.benchmark.v2 import rolevalue_v2 as r2
from physmon.benchmark.v2 import roles_m250n_circ as SRC

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

Pair = r2.PhrasePair
CO = r2.D_KIND_CO_PRESENT
EVENT = r2.D_KIND_OTHER_EVENT
rep = dataclasses.replace
P = rv.Phrasing


def _note(sid: str, text: str) -> str:
    return f"{OLD[sid].notes} M250 r1: {text}"


def _context_with(sid: str, old: str, new: str) -> object:
    """A zero-argument factory: the SRC structure with `old` replaced by `new` in its base context (the gold is unchanged)."""

    def factory() -> gr.Structure:
        base = SRC.STRUCTURE_FACTORIES[sid]()
        assert old in base.render.context, (sid, old)
        return rep(base, render=rep(base.render, context=base.render.context.replace(old, new)))

    return factory


# --- S263: the bridge needs a stated supply; pair 1 R rewritten ----------------------------------------------------------------------

_S263_C = OLD["S263"].cancelling
S263_C = rep(_S263_C, spec=rep(_S263_C.spec, phrasings=(_S263_C.spec.phrasings[0], P("c1", "has a measured diameter of"))))
S263_P1 = Pair(
    "p1", "An extra {value} {unit} of resistance was joined in series with the box {relation}.",
    "before the galvanometer was brought to zero", "for an earlier trial only", EVENT,
    "The extra resistance was in the left gap in an earlier trial, for that trial only; in the stated trial the left gap holds only the "
    "box of the stated resistance.", ("uniform bridge wire", "negligible resistance"), "small amount")
FIXED["S263"] = rep(
    OLD["S263"], cancelling=S263_C, pairs=(OLD["S263"].pairs[0], S263_P1),
    scene_clause="A steady cell is joined across the ends of the bridge wire. A lamp on the bench is dimmed by a rheostat wired to a "
                 "small battery.",
    notes=_note("S263", "scene clause states the supply across the bridge wire (GPT: no excitation, so a zero reading need not give the "
                        "resistance ratio); R1/D1/N1 rewritten as an extra resistance joined in series with the box before the "
                        "galvanometer was brought to zero (R) or for an earlier trial only (D); C1 phrasing made plain."))
CHANGES["S263"] = (
    ("gpt high insufficient_boundary_condition: no nonzero excitation across the bridge ends is specified",
     "scene clause now begins 'A steady cell is joined across the ends of the bridge wire.', so a zero galvanometer reading fixes the "
     "resistance ratio"),
    ("rating R1 artificial: 'When the galvanometer is brought to zero, the left gap also contains a further 9.4 Ω of resistance in series "
     "with the box, for one trial only.'",
     "R1 is 'An extra 9.4 Ω of resistance was joined in series with the box before the galvanometer was brought to zero.' (one reading: "
     "the stated balance is found with the extra resistance in the left gap; no 'for one trial only' in R)"),
    ("rating D1/N1 slightly_artificial: redundant 'in an earlier trial ... for one trial only'",
     "D1 'An extra 9.4 Ω of resistance was joined in series with the box for an earlier trial only.'; N1 the same with 'small amount'"),
    ("rating C1 slightly_artificial: 'is drawn to a diameter of'", "C1 now 'has a measured diameter of'"),
)

# --- S264: K removed (ideal inductor has no self-resonance); pair 1 R rewritten --------------------------------------------------------

S264_P1 = Pair(
    "p1", "The circuit was fitted with an extra {value} {unit} of series resistance {relation}.",
    "before the phase angle was measured", "for an earlier run only", EVENT,
    "The circuit was fitted with the extra series resistance in an earlier run, for that run only; in the stated run it holds only the "
    "stated resistor, inductor and capacitor.", ("ideal components", "steady sinusoidal state"), "small amount")
FIXED["S264"] = rep(
    OLD["S264"], conditional=None, pairs=(OLD["S264"].pairs[0], S264_P1),
    notes=_note("S264", "K (self-resonant frequency of the inductor) removed: it contradicts the stated ideal inductor and its "
                        "reference expression is not the physics of self-resonance (see NO_K); pair 1 now names the series connection "
                        "('extra ... of series resistance') and ties R to the moment before the phase angle was measured."))
NO_K["S264"] = ("The inductor is stated to be ideal, so it has no self-resonance; a real coil's self-resonance would need parasitic "
                "capacitance that the problem excludes, and no other quantity of this series circuit has a threshold that changes the "
                "phase angle.")
K_KINDS.pop("S264", None)
CHANGES["S264"] = (
    ("claude high contradictory_distractor_statement / gpt high contradictory_distractor_statement / gpt high hidden_coupling / gpt high "
     "other: K (self-resonant frequency 140 kHz) contradicts the ideal inductor, and the out-of-regime reference expression is wrong",
     "conditional=None; reason recorded in NO_K['S264']; K_KINDS entry removed"),
    ("gpt high missing_assumption: R1 'the circuit also includes a further 14 Ω of resistance' does not say how it is connected",
     "R1 is 'The circuit was fitted with an extra 14 Ω of series resistance before the phase angle was measured.'"),
    ("rating R1/D1/N1 slightly_artificial: 'for one run only' redundancy",
     "D1 '... for an earlier run only.'; N1 the same with 'small amount'"),
    ("claude medium other: K reference expression", "moot, K removed"),
)

# --- S265: pair 1 rewritten (N1 artificial: 'higher by a further small amount') --------------------------------------------------------

S265_P1 = Pair(
    "p1", "The rms mains voltage was {value} {unit} above its nominal value {relation}.",
    "when the load voltage was measured", "for an earlier run only", EVENT,
    "The mains voltage was above its nominal value in an earlier run, for that run only; in the stated measurement the transformer is "
    "fed with the stated mains voltage.", ("ideal switch", "no smoothing capacitor"), "a small amount")
FIXED["S265"] = rep(
    OLD["S265"], pairs=(OLD["S265"].pairs[0], S265_P1),
    notes=_note("S265", "pair 1 rewritten: 'The rms mains voltage was {v} above its nominal value' (R: when the load voltage was "
                        "measured; D/N: for an earlier run only), replacing 'higher by a further {v}' that has no antecedent."))
CHANGES["S265"] = (
    ("rating N1 artificial: 'In an earlier experiment, the rms mains voltage was higher by a further small amount.'",
     "N1 'The rms mains voltage was a small amount above its nominal value for an earlier run only.'"),
    ("rating D1/R1 slightly_artificial: 'higher by a further 14 V'",
     "R1 'The rms mains voltage was 14 V above its nominal value when the load voltage was measured.'; D1 '... for an earlier run only.'"),
)

# --- S266: K removed; R states a resistive load at a held voltage ---------------------------------------------------------------------

S266_P0 = rep(
    OLD["S266"].pairs[0],
    frame="Before the winding losses are measured, an extra {value} {unit} of resistive load is connected to {relation}.",
    nonnumeric_fill="small amount")
S266_P1 = Pair(
    "p1", "The secondary winding also fed an extra {value} {unit} of resistive load {relation}.",
    "while the winding losses were measured", "for an earlier run only", EVENT,
    "The secondary winding fed the extra load in an earlier run, for that run only; in the stated run it feeds only the stated load.",
    ("core loss are negligible", "steady sinusoidal"), "small amount")
FIXED["S266"] = rep(
    OLD["S266"], conditional=None, pairs=(S266_P0, S266_P1),
    scene_clause="A stiff supply to the primary holds the rms voltage across the load constant. A battery charger on the bench feeds a "
                 "small lamp.",
    notes=_note("S266", "K (peak flux density) removed: its reference expression Ploss*(1+q^2) is not derivable (see NO_K); the R/D/N "
                        "sentences say the extra load is resistive; the scene clause says the load voltage is held constant, so the "
                        "extra load is drawn at the stated voltage; pair 1 rewritten without 'for one run only' in R."))
NO_K["S266"] = ("Saturation of the core would need the magnetisation curve and the excitation, which the problem does not give; no "
                "honest outside-regime law follows from the stated ideal-transformer model, and no other quantity has a threshold that "
                "changes the winding heat.")
K_KINDS.pop("S266", None)
CHANGES["S266"] = (
    ("gpt high missing_assumption: the extra load's power factor / resistive nature is not specified",
     "R0/D0/N0 'an extra 140 W of resistive load is connected to ...'; R1/D1/N1 'The secondary winding also fed an extra 140 W of "
     "resistive load ...'"),
    ("gpt high relevant_variable_removed_from_equation: reactive power of the extra load omitted", "resolved by 'resistive' (no reactive power)"),
    ("gpt high other: K reference expression Ploss*(1+q^2) is not a saturation law", "conditional=None; reason in NO_K['S266']; K_KINDS entry removed"),
    ("claude medium missing_assumption: extra 140 W not said to be drawn at the same 24 V",
     "scene clause: 'A stiff supply to the primary holds the rms voltage across the load constant.'"),
    ("rating D1/N1/R1 slightly_artificial: 'for one run only' wording", "R1 'while the winding losses were measured'; D1 'for an earlier run only'"),
    ("rating D0/N0/R0 slightly_artificial: 'a further 140 W of load'", "'an extra 140 W of resistive load'"),
)

# --- S267: R1 artificial --------------------------------------------------------------------------------------------------------------

S267_P1 = Pair(
    "p1", "The capacitor had an extra {value} {unit} of capacitance wired across it {relation}.",
    "before the switch was closed", "for an earlier run only", EVENT,
    "The capacitor had the extra capacitance across it in an earlier run, for that run only; in the stated run it is alone across the "
    "second resistor.", ("without leakage", "negligible internal resistance"), "small amount")
FIXED["S267"] = rep(
    OLD["S267"], pairs=(OLD["S267"].pairs[0], S267_P1),
    notes=_note("S267", "pair 1 rewritten: 'The capacitor had an extra {v} of capacitance wired across it' before the switch was closed "
                        "(R) or for an earlier run only (D/N)."))
CHANGES["S267"] = (
    ("rating R1 artificial: 'When the switch is closed, the capacitor also has a further 15 μF of capacitance in parallel with it, for "
     "one run only.' (clashes with the stated 22 μF)",
     "R1 'The capacitor had an extra 15 μF of capacitance wired across it before the switch was closed.' (an addition made before the "
     "closing, no 'for one run only')"),
    ("rating D1/N1 slightly_artificial", "D1 '... for an earlier run only.'; N1 the same with 'small amount'"),
)

# --- S268: polarity and timing of the extra emf; D0/N0 artificial ---------------------------------------------------------------------

S268_P0 = rep(
    OLD["S268"].pairs[0],
    frame="Before the switch is closed, a second ideal battery of {value} {unit} emf is joined in series with {relation}, in the same "
          "direction.",
    r_attach="the battery", d_attach="the cell of the doorbell", nonnumeric_fill="small")
S268_P1 = Pair(
    "p1", "The circuit contained a second ideal battery of {value} {unit} emf in series with the first, in the same direction, {relation}.",
    "from the moment the switch was closed", "for an earlier run only", EVENT,
    "The circuit contained the second battery in an earlier run, for that run only; in the stated run the first battery alone drives the "
    "current.", ("ideal battery", "negligible resistance"), "small")
FIXED["S268"] = rep(
    OLD["S268"], pairs=(S268_P0, S268_P1),
    notes=_note("S268", "R/D/N say the second battery is ideal and in the same direction, and that it is present from before the "
                        "switch is closed (so the current is steady at V + q when the switch opens); D0 puts the emf in series with the "
                        "cell of the doorbell."))
CHANGES["S268"] = (
    ("gpt high missing_assumption: polarity of the extra source omitted",
     "'... a second ideal battery of 7.5 V emf is joined in series with the battery, in the same direction.' (R0); R1 '... in series "
     "with the first, in the same direction'"),
    ("gpt high insufficient_boundary_condition: steady state after inserting the source not established",
     "R0 'Before the switch is closed, ...'; R1 '... from the moment the switch was closed', so the stated steady current is the one "
     "with the extra emf"),
    ("rating D0/N0 artificial: 'a further 7.5 V of emf is inserted in series with the doorbell'",
     "D0 'Before the switch is closed, a second ideal battery of 7.5 V emf is joined in series with the cell of the doorbell, in the "
     "same direction.'; N0 the same with 'small emf'"),
    ("claude low other: 'for one run only' in R1", "R1 no longer carries it; D1 'for an earlier run only'"),
    ("rating R0/R1/D1/N1 slightly_artificial", "rewritten as above ('a second ideal battery of 7.5 V emf')"),
)

# --- S269: dropped --------------------------------------------------------------------------------------------------------------------

DROPPED["S269"] = (
    "the R quantity is a further pitch of the fork added to its stated frequency, and the base states that the pipe is tuned to exactly "
    "440 Hz; any R sentence that raises the pitch before the tuning contradicts that stated value (GPT failed_transformation_identity), "
    "and one that raises it after the tuning changes the gold; a repair needs an R quantity on a separate input, which this structure "
    "does not have, and the K reference expression (c2/(4q) - f) is not physics either")
K_KINDS.pop("S269", None)

# --- S270: R is a conveyor speed on the trolley (a separate quantity, absent in the base) --------------------------------------------

_S270_OLD = ("A recorder on a trolley starts beside the post, runs directly away from the lorry along the same line at a constant {v} "
             "m/s, and faces the lorry, so that it picks up the reflected sound.")
_S270_NEW = ("A recorder on a trolley faces the lorry, so that it picks up the reflected sound; the trolley starts beside the post and "
             "runs directly away from the lorry along the same line at a constant {v} m/s.")
STRUCTURE_OVERRIDES["S270"] = _context_with("S270", _S270_OLD, _S270_NEW)
S270_P0 = Pair(
    "p0", "Before the trolley sets off, a conveyor belt is started that carries {relation} along the trolley directly away from the "
          "lorry at {value} {unit}.",
    "the recorder", "the toolbox", CO,
    "A belt that carries the toolbox along the trolley moves the toolbox only; the recorder keeps the stated speed of the trolley, so "
    "the reflected sound and its shift are the stated ones.", ("in still air", "constant"), "a steady speed",
    before_context_reason="The R sentence refers to 'the recorder' and to the trolley before the context introduces them.")
S270_P1 = Pair(
    "p1", "The recorder was carried by a conveyor along the trolley, directly away from the lorry, at {value} {unit} {relation}.",
    "from the moment the trolley set off", "for an earlier run only", EVENT,
    "The recorder was carried along the trolley in an earlier run, for that run only; in the stated run it rides still on the trolley "
    "at the stated speed.", ("in still air", "constant"), "a steady speed")
FIXED["S270"] = rep(
    OLD["S270"], quantity_phrase="a conveyor speed", quantity_type="speed", unit="m/s", values=(4.8, 5.3, 5.8),
    heldout_values=(5.0, 5.6),
    relevant=rv.RelevantWiring("v", "add", "A conveyor that carries the recorder along the trolley at a further speed q makes the speed "
                                           "of the recorder v + q, which changes the Doppler shift of the reflected sound."),
    scene_clause="A toolbox stands on the trolley beside the recorder.",
    scene_object_rationale="A toolbox standing on the trolley is a load of its own; a belt that moves it along the trolley changes the "
                           "toolbox only, so the recorder, the siren note and the reflected sound keep their stated values.",
    scene_refs=("toolbox",), pairs=(S270_P0, S270_P1),
    notes=_note("S270", "R is now a conveyor speed on the trolley (v + q) instead of a pitch added to the stated 1500 Hz note, which "
                        "contradicted the steady note and left the emission time of the received crests open; the base context now "
                        "gives the trolley (not the recorder) the constant speed so that the recorder rides still on it; the scene "
                        "clause introduces a toolbox on the trolley (D0)."))
CHANGES["S270"] = (
    ("gpt high insufficient_boundary_condition: R does not say whether the received reflection was emitted before or after the increase",
     "no change of the note any more; R is a conveyor on the trolley that runs from the moment the trolley sets off (R0: started before "
     "the trolley sets off; R1: from the moment the trolley set off), so the recorder speed is v + q throughout"),
    ("gpt high contradictory_distractor_statement: R1 says the note is 410 Hz higher against the steady 1500 Hz note",
     "the R quantity no longer touches the note"),
    ("rating R0/R1/D0/N0/N1 artificial, D1 slightly_artificial",
     "R0 'Before the trolley sets off, a conveyor belt is started that carries the recorder along the trolley directly away from the "
     "lorry at 4.8 m/s.'; D0 the same with 'the toolbox'; R1 'The recorder was carried by a conveyor along the trolley, directly away "
     "from the lorry, at 4.8 m/s from the moment the trolley set off.'; D1 '... for an earlier run only.'; N0/N1 'at a steady speed'"),
    ("claude low other: transient reading of a changed note", "no changed note"),
)

# --- S271: R rewritten with matching cross-section; C relation text corrected; K1 phrasing ------------------------------------------------

_S271_C = OLD["S271"].cancelling
S271_C = rep(_S271_C, spec=rep(_S271_C.spec, intermediate_relations=(
    "axial rigidity of the rod = Y q", "mass per unit length of the rod = rho q", "wave speed = sqrt(axial rigidity / mass per unit "
                                                                                 "length) = sqrt(Y q / (rho q))")))
_S271_K = OLD["S271"].conditional
S271_K = rep(_S271_K, spec=rep(_S271_K.spec, phrasings=(_S271_K.spec.phrasings[0], P("k1", "has a measured diameter of"))))
S271_P0 = rep(
    OLD["S271"].pairs[0],
    frame="Before the clamp is fitted, {relation} is lengthened by welding on an extra {value} {unit} of the same metal and "
          "cross-section.",
    nonnumeric_fill="small amount")
S271_P1 = Pair(
    "p1", "The rod was extended at one end by a section of the same metal and cross-section, {value} {unit} long, {relation}.",
    "before the clamp was fitted", "for an earlier run only", EVENT,
    "The rod was extended in an earlier run, for that run only; in the stated run it has only its stated length.",
    ("thin metal rod", "fundamental longitudinal mode"), "a few centimetres")
FIXED["S271"] = rep(
    OLD["S271"], cancelling=S271_C, conditional=S271_K, pairs=(S271_P0, S271_P1),
    notes=_note("S271", "R/D/N say the added piece has the same metal and cross-section as the rod and is added before the clamp is "
                        "fitted; C relation text says axial rigidity Y q (not stiffness per unit length); K1 phrasing 'has a measured "
                        "diameter of'; D0 lengthens the railing."))
CHANGES["S271"] = (
    ("gpt high missing_assumption: the extension does not specify a matching cross-section",
     "R0 '... is lengthened by welding on an extra 32 cm of the same metal and cross-section.'; R1 'The rod was extended at one end by "
     "a section of the same metal and cross-section, 32 cm long, before the clamp was fitted.'"),
    ("gpt high inconsistent_units: C relations call Y q a stiffness per unit length",
     "C relations now 'axial rigidity of the rod = Y q' and 'wave speed = sqrt(axial rigidity / mass per unit length)'"),
    ("gpt high rendering_not_minimal (5.3b judge error, not counted)", "N sentences stay numeral-free by design"),
    ("rating R1/D1 artificial, D0/N0 artificial, R0 slightly_artificial",
     "R1/D1 as above ('before the clamp was fitted' / 'for an earlier run only'); D0 'Before the clamp is fitted, the railing is "
     "lengthened by welding on an extra 32 cm of the same metal and cross-section.'; N0 the same with 'small amount'"),
    ("rating K1 slightly_artificial: 'is drawn to a diameter of'", "K1 now 'has a measured diameter of'"),
)

# --- S272: second outlet; K removed; C relation text corrected ---------------------------------------------------------------------------

STRUCTURE_OVERRIDES["S272"] = _context_with(
    "S272", "holds water that drains steadily from the bottom, so that", "holds water that drains steadily from the bottom through a "
                                                                          "tap, so that")
_S272_C = OLD["S272"].cancelling
S272_C = rep(_S272_C, spec=rep(
    _S272_C.spec, expr_with_q="((15*lam/4 - q)/vw) - ((13*lam/4 - q)/vw)",
    intermediate_relations=("the column between the open top and the falling water surface lengthens as L = q + vw t",
                            "it resonates when L plus the end correction is 13 lam / 4 and then 15 lam / 4, two successive odd "
                            "numbers of quarter wavelengths", "t = (L_n - q) / vw at each resonance")))
S272_P0 = Pair(
    "p0", "Before the first resonance is heard, a second outlet is opened that alone would lower {relation} at {value} {unit}.",
    "the water level in the tube", "the level of the pond", CO,
    "A second outlet that lowers the level of the pond acts on the pond only; the water in the tube keeps its stated fall speed, so "
    "the time between resonances is the stated one.", ("closed below by the water", "constant"), "a steady rate",
    before_context_reason="The R sentence refers to 'the tube' and to the resonances before the context introduces them.")
S272_P1 = Pair(
    "p1", "The tube also had a second outlet open that alone would lower the water level at {value} {unit} {relation}.",
    "from before the first resonance was heard", "for an earlier run only", EVENT,
    "The second outlet was open in an earlier run, for that run only; in the stated run the water in the tube falls at the stated speed.",
    ("closed below by the water", "constant"), "a steady rate")
FIXED["S272"] = rep(
    OLD["S272"], conditional=None, cancelling=S272_C, pairs=(S272_P0, S272_P1),
    notes=_note("S272", "base context says the water drains 'through a tap' so that a second outlet is an addition, not a change of the "
                        "stated speed; R/D/N say the second outlet would alone lower the level at {v} and is open from before the first "
                        "resonance; C relations say the column lengthens (L = q + vw t); K removed (see NO_K)."))
NO_K["S272"] = ("A tube radius above the cut-off of the first cross mode would carry modes that the fixed-end-correction quarter-wave "
                "model of the problem cannot describe, and no honest closed-form outside-regime answer follows from that model; no "
                "other quantity of the draining tube has a threshold that changes the interval.")
K_KINDS.pop("S272", None)
CHANGES["S272"] = (
    ("claude high other / gpt high other: the C relations make the air column shrink (q - vw t); it lengthens as the water falls",
     "C relations now 'L = q + vw t', resonance at 13 lam / 4 and 15 lam / 4 (less the end correction), 't = (L_n - q) / vw'; "
     "expr_with_q ((15 lam/4 - q)/vw) - ((13 lam/4 - q)/vw)"),
    ("gpt high insufficient_boundary_condition: R0 gives an increased speed before the first resonance with no continuation",
     "R0 'Before the first resonance is heard, a second outlet is opened that alone would lower the water level in the tube at 0.9 "
     "cm/s.' (the outlet stays open); R1 'The tube also had a second outlet open ... from before the first resonance was heard.'; the "
     "base says the water drains 'through a tap'"),
    ("gpt high other: radius claims / outside-regime expression do not follow from the model", "conditional=None; reason in NO_K['S272']"),
    ("gpt high rendering_not_minimal (5.3b judge error, not counted)", "N sentences stay numeral-free by design"),
    ("rating R0/R1/D0/N0 artificial (contradict the constant 1.5 cm/s; 'drawn down at a rate raised by')",
     "an added second outlet as above; D0 'a second outlet is opened that alone would lower the level of the pond at 0.9 cm/s'; "
     "N0/N1 'at a steady rate'"),
)

ROLE_SPECS: dict[str, r2.RoleSpecV2] = {sid: FIXED.get(sid, spec) for sid, spec in OLD.items() if sid not in DROPPED}
SPECS = ROLE_SPECS
INFEASIBLE: dict[str, str] = {**dict(SRC.INFEASIBLE), **{sid: f"repair round 1: {why}" for sid, why in DROPPED.items()}}
STRUCTURE_FACTORIES = {**SRC.STRUCTURE_FACTORIES, **STRUCTURE_OVERRIDES}


def structure(structure_id: str) -> gr.Structure:
    """The structure (repaired factory if any) with the repaired spec's scene clause appended to its base context."""

    return r2.with_scene(STRUCTURE_FACTORIES[structure_id](), ROLE_SPECS[structure_id].scene_clause)
