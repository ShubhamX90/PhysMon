"""M250 repair round 1 (journal J15.1-059) of `roles_m250n_extra`: the specs the two-judge panel rejected (any high flag) or whose sentences the
blind naturalness rater rated artificial, repaired; every other spec is the `roles_m250n_extra` object, unchanged.

Brief: `/scratch/pabitra/physmon/repair_m250_r1/briefs/roles_m250n_extra.md` (built by `scripts/v2/s207_m250_repair_briefs.py` from
`docs/validation/v2/llm_panel/admission_m250/runs/score_two_judges/`). No model output exists on any of these structures, so they may
still be edited (dataset admission standard, preamble). Wording rules 1-8 of `roles_m250n_extra` apply to every changed sentence.

`CHANGES` records, per changed structure, each finding and how it was resolved; `DROPPED` holds structures that could not be repaired
(they move to `INFEASIBLE` with the reason and are replaced in a later batch).
"""

from __future__ import annotations

import dataclasses

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import rolevalue_v2 as r2
from physmon.benchmark.v2 import roles_m250n_extra as SRC

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


def _pair(sid: str, i: int, **kw):
    return dataclasses.replace(OLD[sid].pairs[i], **kw)


def _fix(sid: str, note: str, **kw) -> None:
    FIXED[sid] = dataclasses.replace(OLD[sid], notes=f"{OLD[sid].notes} M250 r1: {note}", **kw)


_BC = "The R sentence refers to '{}' before the context introduces it."

# --- S251 ---------------------------------------------------------------------------------------------------------------------------
_fix("S251", "pair 0 and 1 rewritten around a spring catapult that acts at the firing; the co-present object is a relay capsule.",
     scene_clause="A relay capsule waits on a launch rail nearby. A speed that a catapult gives the probe at the firing "
                  "comes on top of the speed from the motor.",
     scene_object_rationale="A relay capsule on a separate launch rail is a different body from the probe; speed given to it is not "
                            "given to the probe, so the launch speed of the probe is the stated one.",
     scene_refs=("relay capsule",),
     pairs=(_pair("S251", 0, frame="At the firing, a spring catapult gives {relation} a further {value} {unit} of upward speed.",
                  r_attach="the probe", d_attach="the relay capsule",
                  d_rationale="Speed given to the relay capsule stays with the capsule; the probe keeps the launch speed from its motor "
                              "and the moon, its radius and its gravity are those stated.",
                  before_context_reason=_BC.format("the probe") + " 'the firing' likewise."),
            _pair("S251", 1, frame="{relation} the probe a further {value} {unit} of upward speed.",
                  r_attach="At the firing, a spring catapult also gives", d_attach="On an earlier test firing, a spring catapult gave",
                  d_rationale="A catapult gave the probe the further speed on an earlier test firing; at the stated firing the probe "
                              "has only the speed from its motor.")))
CHANGES["S251"] = (
    ("gpt high: R0 does not establish the intervening motion or whether the motor sets the final launch speed or adds an increment",
     "R0/R1 now act AT the firing ('At the firing, a spring catapult gives the probe a further {v} of upward speed') and the scene "
     "clause says a catapult's speed comes on top of the speed from the motor: one reading, launch speed v0 + q at the surface"),
    ("R0/R1 artificial ('Before the firing, a further 210 m/s of upward speed is given to the probe'; '... for one firing only')",
     "R0 'At the firing, a spring catapult gives the probe a further {v} of upward speed.'; R1 'At the firing, a spring catapult also "
     "gives the probe ...'; the redundant 'for one firing only' is dropped"),
    ("D0/N0 artificial (speed given to a weather balloon on an airless moon)",
     "scene object is a relay capsule on a separate launch rail: 'At the firing, a spring catapult gives the relay capsule a further "
     "{v} of upward speed.'"),
    ("D1/N1 slightly artificial ('it' unclear; 'for one firing only')",
     "'On an earlier test firing, a spring catapult gave the probe a further {v} of upward speed.'"))

# --- S252 ---------------------------------------------------------------------------------------------------------------------------
_fix("S252", "pair 1 reworded: 'the satellite' replaces the ambiguous 'it'; 'for one flight only' dropped.",
     pairs=(OLD["S252"].pairs[0],
            _pair("S252", 1, frame="{relation} a further {value} {unit} of instruments.",
                  r_attach="When it is raised, the satellite also carries", d_attach="On an earlier flight, the satellite also carried")))
CHANGES["S252"] = (
    ("D1 artificial ('On an earlier flight, it also carried ... for one flight only'; 'it' ambiguous after the recovery ship)",
     "'On an earlier flight, the satellite also carried a further {v} of instruments.'"),
    ("R1 slightly artificial ('for one flight only')", "'When it is raised, the satellite also carries a further {v} of instruments.'"))

# --- S253 ---------------------------------------------------------------------------------------------------------------------------
_fix("S253", "the further intensity is now the first loudspeaker being turned up (one wave, normal incidence, one frequency); the "
             "co-present object is a second loudspeaker facing the boathouse wall.",
     scene_clause="A boathouse stands on the shore. The wave comes from a first loudspeaker, which at first plays at the intensity "
                  "given, and a second loudspeaker faces the boathouse wall.",
     scene_object_rationale="A second loudspeaker facing the boathouse wall is a different source; turning it up changes the sound at the "
                            "wall, not the incident wave on the water, so the incident intensity is the stated one.",
     scene_refs=("second loudspeaker",),
     pairs=(_pair("S253", 0, frame="Before the pressure is measured, the intensity of the sound from {relation} is increased by "
                                   "{value} {unit}.",
                  r_attach="the first loudspeaker", d_attach="the second loudspeaker",
                  d_rationale="Turning up the second loudspeaker changes the sound at the boathouse wall; the incident wave from the "
                              "first loudspeaker keeps its stated intensity and the two fluids are as stated.",
                  before_context_reason=_BC.format("the first loudspeaker"), nonnumeric_fill="a small amount"),
            _pair("S253", 1, frame="{relation} the intensity of the sound from the first loudspeaker was increased by {value} {unit}.",
                  r_attach="Just before the pressure was measured,", d_attach="On an earlier trial,",
                  nonnumeric_fill="a small amount",
                  d_rationale="The first loudspeaker was turned up on an earlier trial; in the stated trial the incident wave has the "
                              "stated intensity.")))
CHANGES["S253"] = (
    ("gpt high: frequency, phase, coherence and direction of the additional field unspecified; Ii -> Ii + q unjustified",
     "no second wave any more: the first loudspeaker that makes the wave is turned up, so the incident wave stays one plane wave at "
     "normal incidence and one frequency; the scene clause says the stated intensity is the one at which it first plays"),
    ("gpt high: R0 does not say whether the additional sound overlaps the measured wave or has passed",
     "R0 'Before the pressure is measured, the intensity of the sound from the first loudspeaker is increased by {v}.' gives exactly "
     "one reading (the measured wave has the increased intensity)"),
    ("claude low: additional intensity presumed part of the same plane wave", "same wave, see above"),
    ("D0/N0 artificial ('falls on the boathouse wall')", "'... the intensity of the sound from the second loudspeaker is increased by {v}.'"),
    ("R0/R1 slightly artificial; D1/N1 slightly artificial ('for one trial only')",
     "R1 'Just before the pressure was measured, the intensity of the sound from the first loudspeaker was increased by {v}.'; D1 "
     "'On an earlier trial, ...'"))

# --- S254 ---------------------------------------------------------------------------------------------------------------------------
_fix("S254", "observer measures at the height of the siren; K (mouth width) removed; pair 1 reworded.",
     scene_clause="The observer measures with a microphone held at the height of the siren, and a dog lies by the mast.",
     conditional=None,
     pairs=(OLD["S254"].pairs[0],
            _pair("S254", 1, frame="{relation} walked {value} {unit} farther from the mast.",
                  r_attach="Just before the reading was taken, the observer", d_attach="In an earlier experiment, the observer",
                  nonnumeric_fill="a modest distance")))
NO_K["S254"] = ("A finite mouth would need a stated radiation pattern and source model; the point-source regime of the problem has no "
                "sharp threshold quantity and no honest out-of-regime intensity within the stated model.")
K_KINDS.pop("S254", None)
CHANGES["S254"] = (
    ("claude and gpt high: height of siren vs observer, distance from the mast does not fix the path length",
     "scene clause: 'The observer measures with a microphone held at the height of the siren', so the distance from the mast is the "
     "distance from the siren and r -> r + q is exact"),
    ("gpt high: K claim (5q<r, finite-mouth intensity) does not follow from the point-source model",
     "K removed (conditional=None, NO_K reason)"),
    ("N1 artificial ('moved away from the mast by a modest distance more')",
     "'In an earlier experiment, the observer walked a modest distance farther from the mast.' (D1/R1 share the frame '... walked "
     "{v} farther from the mast.')"))

# --- S255 ---------------------------------------------------------------------------------------------------------------------------
_fix("S255", "co-present object is a measuring tape (pulled out), pair 1 uses the strip pulled out of the clamp.",
     scene_clause="The strip can be slid through the clamp when the clamp is loosened, and a measuring tape lies on the bench.",
     scene_object_rationale="A measuring tape on the bench is a separate object; tape pulled out of its case does not change the length "
                            "of the strip that projects from the clamp, so the free length is the stated one.",
     scene_refs=("measuring tape",),
     pairs=(_pair("S255", 0, frame="Before the deflection is measured, {relation} is pulled out {value} {unit} further.",
                  r_attach="the strip", d_attach="the measuring tape",
                  d_rationale="Tape pulled out of its case does not change the strip; the strip keeps its stated free length, layers and "
                              "temperatures."),
            _pair("S255", 1, frame="{relation} the strip was pulled out of the clamp {value} {unit} further.",
                  r_attach="Just before the deflection was measured,", d_attach="In an earlier experiment,",
                  nonnumeric_fill="a modest distance")))
CHANGES["S255"] = (
    ("N0/D0 artificial/slightly (cable paid out from a reel)", "'Before the deflection is measured, the measuring tape is pulled out "
                                                               "{v} further.'"),
    ("D1/N1 artificial ('the clamp also let out ...')",
     "'In an earlier experiment, the strip was pulled out of the clamp {v} further.'"),
    ("R0/R1 slightly artificial", "R0 'the strip is pulled out {v} further'; R1 'Just before the deflection was measured, the strip was "
                                  "pulled out of the clamp {v} further.'"))

# --- S256 ---------------------------------------------------------------------------------------------------------------------------
_fix("S256", "'cast onto' replaced by 'added to'; pair 1 reworded; K (Debye temperature) removed.",
     conditional=None,
     pairs=(_pair("S256", 0, frame="Before the heating begins, a further {value} {unit} of lead is added to {relation}.",
                  r_attach="the block", d_attach="the lead weight"),
            _pair("S256", 1, frame="{relation} a further {value} {unit} of lead was added to the block, for one heating only.",
                  r_attach="Just before the heating began,", d_attach="In an earlier experiment,")))
NO_K["S256"] = ("The Debye low-temperature law needs the block temperature to be much below the Debye temperature, which contradicts "
                "the stated classical regime; no sharp threshold gives a definite out-of-regime heat for the stated model.")
K_KINDS.pop("S256", None)
CHANGES["S256"] = (
    ("gpt high: outside-regime reference is the low-T Debye asymptote, not implied by the complement of T1 > 2q",
     "K removed (conditional=None, NO_K reason)"),
    ("gpt high rendering_not_minimal (5.3b)", "not counted; N sentences stay numeral-free"),
    ("R0/R1 artificial ('cast onto the block'; 'also includes ... for one heating only')",
     "'a further {v} of lead is added to the block'; R1 'Just before the heating began, a further {v} of lead was added to the "
     "block, for one heating only.'"),
    ("D0/N0 artificial ('cast onto the lead weight')", "'... is added to the lead weight.'"),
    ("D1 slightly artificial", "'In an earlier experiment, a further {v} of lead was added to the block, for one heating only.'"))

# --- S257 ---------------------------------------------------------------------------------------------------------------------------
_fix("S257", "pair 1 reworded around 'the column was loaded with'.",
     pairs=(OLD["S257"].pairs[0],
            _pair("S257", 1, frame="{relation} the column was loaded with a further {value} {unit} of the parent isotope, for one run only.",
                  r_attach="At the start of this run,", d_attach="In an earlier run,")))
CHANGES["S257"] = (
    ("R1 artificial ('At the start of the run, the column is also loaded with ...')",
     "'At the start of this run, the column was loaded with a further {v} of the parent isotope, for one run only.'"),
    ("D1 slightly artificial ('also ... a further')", "'In an earlier run, the column was loaded with a further {v} of the parent "
                                                      "isotope, for one run only.'"))

# --- S258 ---------------------------------------------------------------------------------------------------------------------------


def _s258_base():
    base = SRC.STRUCTURE_FACTORIES["S258"]()
    ctx = base.render.context
    old = ("A source is made and is then left to stand for {age} years. When it is made it contains {m} g of a radioactive isotope of "
           "cobalt.")
    new = ("A source is made by putting {m} g of a radioactive isotope of cobalt into a capsule, and is then left to stand for {age} "
           "years.")
    assert old in ctx, ctx
    return dataclasses.replace(base, render=dataclasses.replace(base.render, context=ctx.replace(old, new)))


STRUCTURE_OVERRIDES["S258"] = _s258_base
_fix("S258", "base text now says the source is made by putting the cobalt into a capsule, so a further amount put into the capsule "
             "adds without contradicting a stated content.",
     pairs=(_pair("S258", 0, frame="When the source is made, a further {value} {unit} of the radioactive cobalt is put into {relation}.",
                  r_attach="the capsule", d_attach="the vault"),
            _pair("S258", 1, frame="In making the source, a further {value} {unit} of the radioactive cobalt goes into {relation}.",
                  r_attach="the capsule", d_attach="the waste drum")))
CHANGES["S258"] = (
    ("gpt high: R0/R1 contradict 'When it is made it contains 0.004 g'",
     "base now reads 'A source is made by putting 0.004 g of a radioactive isotope of cobalt into a capsule' (base gold unchanged); R: "
     "'a further {v} of the radioactive cobalt is put into the capsule' / 'goes into the capsule'"),
    ("R0/R1 artificial ('incorporated into the source', 'goes into the source')", "see above"),
    ("D0/D1 frames", "'is put into the vault' / 'goes into the waste drum' (same frame as R)"))

# --- S259 ---------------------------------------------------------------------------------------------------------------------------
_fix("S259", "scene clause states the flask walls start at the gas temperature and the gas takes the wall temperature; pair 1 reworded.",
     scene_clause="A window frame leans against the wall. The flask walls start at the temperature of the gas, and the gas comes to "
                  "the temperature of the walls.",
     pairs=(OLD["S259"].pairs[0],
            _pair("S259", 1, frame="{relation}, sunshine warmed the flask by {value} {unit}.",
                  r_attach="Just before the speeds were measured", d_attach="In an earlier experiment",
                  nonnumeric_fill="a modest amount")))
CHANGES["S259"] = (
    ("gpt high: flask's initial thermal state / thermal boundary condition unspecified",
     "scene clause: 'The flask walls start at the temperature of the gas, and the gas comes to the temperature of the walls.'"),
    ("N1 artificial ('the sunlit flask was also a modest amount warmer than at the start')",
     "'In an earlier experiment, sunshine warmed the flask by a modest amount.'; R1 'Just before the speeds were measured, sunshine "
     "warmed the flask by {v}.'"))

# --- S260 ---------------------------------------------------------------------------------------------------------------------------
_fix("S260", "K (width of the vessel) removed; pair 1 reworded.",
     conditional=None,
     pairs=(OLD["S260"].pairs[0],
            _pair("S260", 1, frame="{relation} a further {value} {unit} of nitrogen at the same temperature was let into the vessel, "
                                   "for one run only.",
                  r_attach="Just before the collisions were counted,", d_attach="In an earlier experiment,")))
NO_K["S260"] = ("The collision frequency of a molecule in equilibrium is fixed by density, temperature and cross-section; a vessel width "
                "enters it at no threshold when wall collisions are excluded by the question, so no honest regime conditional exists.")
K_KINDS.pop("S260", None)
CHANGES["S260"] = (
    ("gpt high: width K claim invokes vbar/q wall encounters although wall collisions are excluded", "K removed (conditional=None, NO_K)"),
    ("R1 artificial ('the vessel also holds a further 33 kPa ... for one run only' contradicts 80 kPa)",
     "'Just before the collisions were counted, a further {v} of nitrogen at the same temperature was let into the vessel, for one "
     "run only.'"))

# --- S261 ---------------------------------------------------------------------------------------------------------------------------
_fix("S261", "K (Stokes limit) removed; pair 1 reworded.",
     conditional=None,
     pairs=(OLD["S261"].pairs[0],
            _pair("S261", 1, frame="{relation} a further {value} {unit} of lead shot was loaded into the sphere, for one release only.",
                  r_attach="Just before this release,", d_attach="On an earlier release,")))
NO_K["S261"] = ("A cutoff Reynolds number of Stokes' law does not determine a corrected drag or terminal speed, so no definite "
                "out-of-regime answer exists for the stated model.")
K_KINDS.pop("S261", None)
CHANGES["S261"] = (
    ("gpt high: K out-of-regime speed vt/(1+3q/16) unjustified", "K removed (conditional=None, NO_K)"),
    ("R1 artificial ('it is also loaded ... for one release only' contradicts total mass)",
     "'Just before this release, a further {v} of lead shot was loaded into the sphere, for one release only.'"),
    ("D1/N1 slightly artificial ('it' ambiguous)", "'On an earlier release, a further {v} of lead shot was loaded into the sphere, "
                                                   "for one release only.'"))

# --- S262 ---------------------------------------------------------------------------------------------------------------------------
_fix("S262", "pair 1 reworded without 'also' and 'for one experiment only'.",
     pairs=(OLD["S262"].pairs[0],
            _pair("S262", 1, frame="{relation} the oil in the tank was topped up by {value} {unit}.",
                  r_attach="Just before the draining started,", d_attach="In an earlier experiment,")))
CHANGES["S262"] = (
    ("R1 artificial ('the oil in the tank is also topped up by 13 cm, for one experiment only')",
     "'Just before the draining started, the oil in the tank was topped up by {v}.'"),
    ("D1 artificial ('In an earlier experiment ... for one experiment only')",
     "'In an earlier experiment, the oil in the tank was topped up by {v}.'"))

ROLE_SPECS: dict[str, r2.RoleSpecV2] = {sid: FIXED.get(sid, spec) for sid, spec in OLD.items() if sid not in DROPPED}
SPECS = ROLE_SPECS
INFEASIBLE: dict[str, str] = {**dict(SRC.INFEASIBLE), **{sid: f"repair round 1: {why}" for sid, why in DROPPED.items()}}
STRUCTURE_FACTORIES = {**SRC.STRUCTURE_FACTORIES, **STRUCTURE_OVERRIDES}


def structure(structure_id: str) -> gr.Structure:
    """The structure (repaired factory if any) with the repaired spec's scene clause appended to its base context."""

    return r2.with_scene(STRUCTURE_FACTORIES[structure_id](), ROLE_SPECS[structure_id].scene_clause)
