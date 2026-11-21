"""M250 repair round 1 (journal J15.1-059) of `roles_m250_d`: the specs the two-judge panel rejected (any high flag) or whose sentences the
blind naturalness rater rated artificial, repaired; every other spec is the `roles_m250_d` object, unchanged.

Brief: `/scratch/pabitra/physmon/repair_m250_r1/briefs/roles_m250_d.md` (built by `scripts/v2/s207_m250_repair_briefs.py` from
`docs/validation/v2/llm_panel/admission_m250/runs/score_two_judges/`). No model output exists on any of these structures, so they may
still be edited (dataset admission standard, preamble). Wording rules 1-8 of `roles_m250_d` apply to every changed sentence.

`CHANGES` records, per changed structure, each finding and how it was resolved; `DROPPED` holds structures that could not be repaired
(they move to `INFEASIBLE` with the reason and are replaced in a later batch).
"""

from __future__ import annotations

import dataclasses

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import rolevalue_v2 as r2
from physmon.benchmark.v2 import roles_m250_d as SRC

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

def _note(sid: str, text: str) -> str:
    return f"{OLD[sid].notes} M250 r1: {text}".strip()


def _pairs(sid: str, p0: dict, p1: dict):
    return (dataclasses.replace(OLD[sid].pairs[0], **p0), dataclasses.replace(OLD[sid].pairs[1], **p1))


# ---- S73: gate electrodes give the widening an ordinary mechanism; pair-1 D is an event after the transition -------------------
FIXED["S73"] = dataclasses.replace(
    OLD["S73"],
    scene_clause="The walls of the well are set by gate electrodes. A quantum dot on the same chip is defined by gate electrodes of its own.",
    scene_object_rationale="A quantum dot on the same chip is defined by its own gate electrodes and holds its own electrons; it shares "
                           "no wall with the well of the problem, so the width of the well and the levels of its electron are unchanged.",
    scene_refs=("dot",),
    pairs=_pairs(
        "S73",
        dict(frame="Before the transition, the gate electrodes of {relation} are moved apart to widen it by {value} {unit}.",
             r_attach="the well", d_attach="the dot",
             d_rationale="Moving the gate electrodes of the dot widens that dot only; it shares no wall with the well "
                         "of the electron, so the width of the well and the photon wavelength are the stated ones.",
             before_context_reason="The R sentence refers to 'the well' and 'the transition' before the context introduces the "
                                   "well or any transition; placed first, it has no referent."),
        dict(frame="{relation}, the gate electrodes of the well were moved apart to widen it by {value} {unit}.",
             r_attach="Before the electron made the transition", d_attach="After the electron made the transition",
             d_rationale="The well was widened only after the electron had made the transition, an event after the stated process; "
                         "the transition took place in the well of the stated width."),
    ),
    notes=_note("S73", "gate electrodes make the widening an ordinary action (moving the electrodes apart) instead of an unexplained "
                       "change of the width; p0 D is a gate-defined dot with its own gates (an ordinary tuning step; the old 'widened dot' "
                       "was rated contrived); p1 D is after the transition so no widening can persist into the stated state."))
CHANGES["S73"] = (
    ("claude medium: D1/N1 'The well was widened by 2.4 nm in an earlier experiment on it' may leave the well wider than 0.5 nm",
     "p1 D/N now 'After the electron made the transition, the gate electrodes of the well were moved apart to widen it by ...': an "
     "event after the stated process, so the transition is in the well of the stated width."),
    ("gpt medium: N0/N1 omit numerals", "numeral-free by design (5.3b); kept as the D sentence with the fill 'a small amount'."),
    ("rating R0 artificial 'Before the transition, the well is widened by 2.4 nm.'",
     "'Before the transition, the gate electrodes of the well are moved apart to widen it by 2.4 nm.' (scene: walls set by gate "
     "electrodes)"),
    ("rating D0 slightly / N0 artificial 'the dot is widened by ...'",
     "D0/N0 'the gate electrodes of the dot are moved apart to widen it by ...'; scene clause 'A quantum dot on the same chip is "
     "defined by gate electrodes of its own' (the dot is now gate-defined, so widening it is an ordinary step)"),
    ("rating D1 artificial 'in an earlier experiment on it' / R1 slightly / N1 slightly",
     "R1 'Before the electron made the transition, the gate electrodes of the well were moved apart to widen it by 2.4 nm.'; "
     "D1/N1 'After the electron made the transition, ...'"),
)

# ---- S77: barrier rebuilt from another material; pair-1 D after the electron's encounter ---------------------------------------
FIXED["S77"] = dataclasses.replace(
    OLD["S77"],
    scene_clause="A second barrier of the same kind is built on the same chip. Barrier heights are measured from the potential outside the barrier.",
    scene_object_rationale="A second barrier built on the same chip is a different potential region; the electron approaches the "
                           "barrier of the problem only, so the height of that barrier and the width asked for are unchanged.",
    scene_refs=("second barrier",), target_terms=("the barrier",),
    pairs=_pairs(
        "S77",
        dict(frame="Before the electron arrives, {relation} is rebuilt from a different material, with its height set to {value} {unit}.",
             r_attach="the barrier", d_attach="the second barrier", nonnumeric_fill="a new value",
             d_rationale="Rebuilding the second barrier gives that barrier a new height; the electron does not approach it, so the "
                         "height of the barrier of the problem and the width asked for are unchanged."),
        dict(frame="{relation}, it was rebuilt from a different material, with its height set to {value} {unit}.",
             r_attach="Before the electron approached the barrier", d_attach="After the electron had left the barrier",
             nonnumeric_fill="a new value",
             d_rationale="The barrier was rebuilt only after the electron had left it, an event after the stated process; the "
                         "electron of the stated problem approached a barrier of the stated height."),
    ),
    notes=_note("S77", "'then replaced ... for an earlier experiment only' wording removed; the barrier is 'rebuilt from a different "
                       "material, with its height set to {v}'; p0 D is a second barrier (the step rated incoherent), p1 D is "
                       "after the electron left the barrier."))
CHANGES["S77"] = (
    ("claude low: 'was then replaced ... for an earlier experiment only' awkward",
     "p1 D/N now 'After the electron had left the barrier, it was rebuilt from a different material, with its height set to ...'"),
    ("rating R0 artificial 'Before the electron arrives, the barrier is then replaced by one whose height is 7.2 eV.'",
     "'Before the electron arrives, the barrier is rebuilt from a different material, with its height set to 7.2 eV.'"),
    ("rating D0 artificial / N0 artificial 'the step is then replaced by one whose height is ...'",
     "'... the second barrier is rebuilt from a different material, with its height set to ...'; N fill 'a new value'"),
    ("rating R1 artificial 'was then replaced ... before the electron approached it'",
     "'Before the electron approached the barrier, it was rebuilt from a different material, with its height set to 7.2 eV.'"),
    ("rating D1/N1 artificial 'for an earlier experiment only'",
     "'After the electron had left the barrier, it was rebuilt ...' (event after the stated process)"),
)

# ---- S82: outbursts; pair-0 D a third star; pair-1 D after the spectrum was recorded --------------------------------------------
FIXED["S82"] = dataclasses.replace(
    OLD["S82"],
    scene_clause="A third star in the same field is observed with the same spectrometer. The second and the third star brighten from "
                 "time to time in outbursts.",
    scene_object_rationale="A third star in the same field is a separate blackbody; its surface temperature does not enter the "
                           "blackbody peak of the second star, so the answer for the second star is unchanged.",
    scene_refs=("third star",), target_terms=("second star",),
    pairs=_pairs(
        "S82",
        dict(frame="Before the spectra are recorded, {relation} goes into an outburst and its surface temperature rises by {value} {unit}.",
             r_attach="the second star", d_attach="the third star",
             d_rationale="The outburst of the third star raises the temperature of that star only; it does not change the peak of the "
                         "second star, so the answer for the second star is the stated one.",
             before_context_reason="The R sentence refers to 'the second star' and to the recording of the spectra before the context "
                                   "introduces them; placed first, it has no referent."),
        dict(frame="{relation}, the star went into an outburst and its surface temperature rose by {value} {unit}.",
             r_attach="Before the spectrum of the second star was recorded",
             d_attach="After the spectrum of the second star was recorded",
             d_rationale="The outburst came after the spectrum had been recorded, an event after the stated process; the star radiated "
                         "at its stated surface temperature when its spectrum was recorded."),
    ),
    notes=_note("S82", "second and third star are variables that brighten in outbursts (an ordinary reason for a temperature rise); "
                       "p0 D is the third star (the tungsten filament would exceed its melting point at 2900 K + q); p1 D is an "
                       "outburst after the spectrum was recorded, so no earlier temperature change is left unspecified."))
CHANGES["S82"] = (
    ("gpt high: insufficient_boundary_condition: history sentences do not say which temperature is observed / that the star returns",
     "p1 D/N now 'After the spectrum of the second star was recorded, the star went into an outburst and its surface temperature "
     "rose by ...': an event after the stated process, so the observed temperature is the stated 2900 K and nothing needs to be "
     "reversed; R1 'Before the spectrum of the second star was recorded, ...' ties the rise to the recorded spectrum."),
    ("gpt high: hidden_coupling: an earlier outburst may leave a temperature change",
     "'in an earlier outburst' removed; D1 outburst follows the recording (see above)."),
    ("rating R0 artificial 'Before the spectra are compared, the temperature of the second star rises by 950 K.'",
     "'Before the spectra are recorded, the second star goes into an outburst and its surface temperature rises by 950 K.' "
     "(scene: the second and third star brighten in outbursts)"),
    ("rating R1 artificial 'rose by 950 K shortly before its spectrum was observed'",
     "'Before the spectrum of the second star was recorded, the star went into an outburst and its surface temperature rose by 950 K.'"),
    ("rating D0/N0 slightly 'the temperature of the lamp filament rises by ...'",
     "D0/N0 'the third star goes into an outburst and its surface temperature rises by ...'; the lamp clause is dropped"),
)

# ---- S91: emptied and refilled manometers; K removed -------------------------------------------------------------------------
NO_K["S91"] = ("The only candidate, the absolute pressure in the wide section, bounds the throat pressure only through the cavitation "
               "limit (the vapour pressure of the liquid, not zero); below that limit the flow no longer follows Bernoulli's equation "
               "and no certified out-of-regime flow law exists, and replacing the manometer difference by the absolute pressure was "
               "not justified physically (both judges).")
FIXED["S91"] = dataclasses.replace(
    OLD["S91"],
    scene_clause="A second manometer, joined to a different pipe, hangs on the same wall. Each manometer can be emptied and refilled "
                 "with a different liquid. The liquid in the U-tube does not mix with the flowing liquid.",
    scene_object_rationale="A second manometer joined to a different pipe does not measure anything in this pipe; draining and "
                           "refilling it changes neither the pressure difference between the wide section and the throat nor the "
                           "reading of the U-tube.",
    scene_refs=("second manometer",), target_terms=("u-tube", "pipe"),
    pairs=_pairs(
        "S91",
        dict(frame="Before the levels are read, the liquid in {relation} is emptied and refilled with a liquid whose density is {value} {unit}.",
             r_attach="the U-tube", d_attach="the second manometer",
             d_rationale="The second manometer is joined to a different pipe; refilling it changes nothing in the U-tube, so the "
                         "reading of the U-tube and the flow rate it gives are the stated ones."),
        dict(frame="{relation}, the U-tube was emptied and refilled with a liquid whose density is {value} {unit}.",
             r_attach="Before the levels were read", d_attach="After the levels had been read",
             d_rationale="The U-tube was refilled only after the levels had been read, an event after the stated process; the "
                         "reading of the stated problem was made with the stated liquid."),
    ),
    conditional=None,
    notes=_note("S91", "K removed (judges: the q > dp regime and the substitution of q for dp in the out-of-regime law are not "
                       "physical); refilling wording replaces the 'replaced ... for an earlier experiment only' wording; p0 D is a "
                       "second manometer on a different pipe (the barometer rated pointless); p1 D after the levels were read."))
CHANGES["S91"] = (
    ("gpt high: K claims turn an absolute-pressure feasibility constraint into a different flow law",
     "K quantity removed (conditional=None), reason in NO_K."),
    ("claude low: K regime is cavitation vapour pressure, not zero", "K quantity removed."),
    ("rating D0/N0 artificial 'the liquid in the barometer is replaced by one whose density is ...'",
     "'the liquid in the second manometer is emptied and refilled with a liquid of density ...'; scene: second manometer on a "
     "different pipe, each manometer can be refilled"),
    ("rating R1 artificial: contradicts the stated 13600 kg/m3 liquid",
     "'Before the levels were read, the U-tube was emptied and refilled with a liquid of density 2500 kg/m3.'; scene says the "
     "manometers can be emptied and refilled"),
    ("rating R0 slightly / D1 / N1 'for an earlier experiment only' misplaced",
     "R0 'Before the levels are read, the liquid in the U-tube is emptied and refilled with ...'; D1/N1 'After the levels had been "
     "read, the U-tube was emptied and refilled with ...'"),
)

# ---- S93: reaming the hole (diameter increase stated); pair-1 D after the timing ----------------------------------------------
FIXED["S93"] = dataclasses.replace(
    OLD["S93"],
    scene_clause="A rain barrel with a hole in its bottom stands beside the tank. Water leaves the tank only through the hole in its "
                 "bottom, and the hole stays circular.",
    pairs=_pairs(
        "S93",
        dict(frame="Before the level is timed, the hole in the bottom of {relation} is reamed out to a diameter {value} {unit} larger.",
             nonnumeric_fill="slightly"),
        dict(frame="{relation}, the hole in the bottom of the tank was reamed out to a diameter {value} {unit} larger.",
             r_attach="Before the level was timed", d_attach="After the level had been timed", nonnumeric_fill="slightly",
             d_rationale="The hole was reamed out after the timing had ended, an event after the stated process; the time for the "
                         "level to fall between the stated heights was set by the stated hole."),
    ),
    notes=_note("S93", "'widened by a further {v}' (implied an earlier widening) replaced by 'reamed out to a diameter {v} larger'; p1 frame shared by R/D/N with attachments Before/After the level was timed; scene clause names the hole "
                       "of the tank unambiguously."))
CHANGES["S93"] = (
    ("rating N1 artificial 'was widened by a further small amount after the timing ended'",
     "'After the level had been timed, the hole in the bottom of the tank was reamed out, to a diameter slightly larger.'"),
    ("rating R0/R1/D0/D1/N0 slightly 'widened by a further {v}' (implies an unmentioned earlier widening)",
     "'... is reamed out to a diameter {v} larger' for the barrel (D0) and the tank (R0, R1, D1)"),
    ("claude low: 'its hole' follows the barrel sentence", "scene clause: 'through the hole in its bottom' ('its' = the tank)"),
    ("claude low / rating C0 C1 slightly: density 962 kg/m3 unusual", "left as is (hot water, a physical value; no flag counted)."),
)

# ---- S94: Newtonian incompressible liquid stated; the pipe is lengthened at its outlet end ----------------------------------
FIXED["S94"] = dataclasses.replace(
    OLD["S94"],
    scene_clause="A garden hose lies alongside the pipe. The liquid is Newtonian and incompressible.",
    pairs=_pairs(
        "S94",
        dict(frame="Before the flow is started, a further {value} {unit} of tubing of the same bore is joined to the outlet end of "
                   "{relation}, lengthening it."),
        dict(frame="{relation}, a further {value} {unit} of tubing of the same bore was joined to the outlet end of the pipe, "
                   "lengthening it.",
             r_attach="Before the flow was started", d_attach="After the flow had ended",
             d_rationale="The tubing was joined only after the flow had ended, an event after the stated process; the power needed "
                         "to drive the flow in the stated length is the stated one."),
    ),
    notes=_note("S94", "scene clause states that the liquid is Newtonian and incompressible; R sentences say the tubing is joined "
                       "to the outlet end and lengthens the pipe (one reading of 'the pipe' in the question); p1 D is after the flow "
                       "had ended."))
CHANGES["S94"] = (
    ("gpt high: missing_assumption Newtonian incompressible liquid not stated",
     "scene clause 'The liquid is Newtonian and incompressible.'"),
    ("gpt high / claude low: pressure-drop endpoints ambiguous for R0/R1",
     "'... joined to the outlet end of the pipe, lengthening it': the pipe of the question is the lengthened pipe."),
    ("rating D0/N0 slightly 'joined to the hose' / R0/R1 slightly / D1/N1 slightly 'for an earlier experiment only'",
     "D0/N0 'to the outlet end of the hose, lengthening it'; D1/N1 'After the flow had ended, ... joined to the outlet end of the "
     "pipe, lengthening it.'"),
)


ROLE_SPECS: dict[str, r2.RoleSpecV2] = {sid: FIXED.get(sid, spec) for sid, spec in OLD.items() if sid not in DROPPED}
SPECS = ROLE_SPECS
INFEASIBLE: dict[str, str] = {**dict(SRC.INFEASIBLE), **{sid: f"repair round 1: {why}" for sid, why in DROPPED.items()}}
STRUCTURE_FACTORIES = {**SRC.STRUCTURE_FACTORIES, **STRUCTURE_OVERRIDES}


def structure(structure_id: str) -> gr.Structure:
    """The structure (repaired factory if any) with the repaired spec's scene clause appended to its base context."""

    return r2.with_scene(STRUCTURE_FACTORIES[structure_id](), ROLE_SPECS[structure_id].scene_clause)
