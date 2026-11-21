"""M250 repair round 2 (journal J15.1-061) of `roles_m250r1n_extra`: the specs the two-judge re-review rejected (any high flag) or whose sentences
the blind naturalness rater rated artificial, repaired again; every other spec is the `roles_m250r1n_extra` object, unchanged.

Brief: `/scratch/pabitra/physmon/repair_m250_r2/briefs/roles_m250r1n_extra.md` (`scripts/v2/s207_m250_repair_briefs.py` from
`docs/validation/v2/llm_panel/admission_m250r1/runs/score_two_judges/`). No model output exists on any of these structures. The round-1
history of each structure is in `roles_m250r1n_extra.CHANGES`; wording rules 1-8 of the original module apply.

`CHANGES` records, per changed structure, each finding and how it was resolved; `DROPPED` holds structures that could not be repaired.
"""

from __future__ import annotations

import dataclasses

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import rolevalue_v2 as r2
from physmon.benchmark.v2 import roles_m250r1n_extra as SRC

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

def _pair(sid: str, i: int, **kw):
    return dataclasses.replace(OLD[sid].pairs[i], **kw)


def _fix(sid: str, note: str, **kw) -> None:
    FIXED[sid] = dataclasses.replace(OLD[sid], notes=f"{OLD[sid].notes} M250 r2: {note}", **kw)


# --- S251 ---------------------------------------------------------------------------------------------------------------------------
_fix("S251", "the relay capsule has its own motor and is fired at the same moment, so 'an additional speed' is coherent for it; the "
             "catapult is electromagnetic.",
     scene_clause="A relay capsule waits on a launch rail nearby and is fired at the same moment by a motor of its own. A speed "
                  "that a catapult gives the probe at the firing comes on top of the speed from the motor.",
     pairs=(_pair("S251", 0, frame="At the firing, an electromagnetic catapult gives {relation} an additional {value} {unit} of upward "
                                   "speed.",
                  d_rationale="Speed given to the relay capsule stays with the capsule, which has a motor of its own; the probe keeps "
                              "the launch speed from its motor and the moon, its radius and its gravity are those stated."),
            _pair("S251", 1, frame="{relation} the probe an additional {value} {unit} of upward speed.",
                  r_attach="At the firing, an electromagnetic catapult also gives",
                  d_attach="On an earlier test firing, an electromagnetic catapult gave")))
CHANGES["S251"] = (
    ("D0 artificial ('a spring catapult gives the relay capsule a further 210 m/s': the capsule has no prior speed)",
     "the capsule is fired at the same moment by a motor of its own (scene clause) and the sentence reads 'an additional {v} of upward "
     "speed' from an electromagnetic catapult"),
    ("N0/N1/R0/R1 slightly artificial ('spring catapult ... further')",
     "'an electromagnetic catapult' and 'an additional {v}' in all pair-0 and pair-1 sentences"))

# --- S253 ---------------------------------------------------------------------------------------------------------------------------
_fix("S253", "scene clause states the wave is a steady harmonic tone, that a change at the first loudspeaker is the same change in the "
             "incident intensity, and that the second loudspeaker's sound does not reach the water.",
     scene_clause="A boathouse stands on the shore. The wave is a steady harmonic tone from a first loudspeaker, which at first plays "
                  "at the intensity given; a change in the intensity of its sound is a change of the same size in the intensity of "
                  "the incident wave. A second loudspeaker faces the boathouse wall, and its sound does not reach the water.",
     scene_object_rationale="A second loudspeaker facing the boathouse wall is a different source whose sound does not reach the water; "
                            "turning it up changes the sound at the wall, not the incident wave, so the incident intensity is the "
                            "stated one.")
CHANGES["S253"] = (
    ("gpt high missing_assumption: harmonic wave not stated",
     "scene clause: 'The wave is a steady harmonic tone from a first loudspeaker'"),
    ("gpt high insufficient_boundary_condition: second source not excluded, source change not tied to the measured intensity",
     "scene clause: 'a change in the intensity of its sound is a change of the same size in the intensity of the incident wave' and "
     "'[the second loudspeaker's] sound does not reach the water'"),
    ("gpt high hidden_coupling: facing the wall does not exclude a path to the water",
     "'its sound does not reach the water' is stated"))

# --- S255 ---------------------------------------------------------------------------------------------------------------------------
_fix("S255", "N fill 'a few centimetres' replaces the vague 'a modest distance'; the tape is for reading the deflection.",
     scene_clause="The strip can be slid through the clamp when the clamp is loosened, and a measuring tape for reading the "
                  "deflection lies on the bench.",
     pairs=(_pair("S255", 0, nonnumeric_fill="a few centimetres"), _pair("S255", 1, nonnumeric_fill="a few centimetres")))
CHANGES["S255"] = (
    ("N0 artificial ('the measuring tape is pulled out a modest distance further' pointless)",
     "'... is pulled out a few centimetres further' and the tape is said to be for reading the deflection"),
    ("N1 slightly artificial ('a modest distance further')", "'a few centimetres further'"),
    ("claude low: bookkeeping label 'length of strip' for the tape", "not counted (no effect on strata or answers)"))

# --- S256 ---------------------------------------------------------------------------------------------------------------------------
_fix("S256", "lead is placed on the block (joined to it, at its temperature, heated with it); co-present object is a scale pan; the "
             "'for one heating only' wording is dropped.",
     scene_clause="A scale pan stands on the bench. Lead placed on the block is joined to it, is at its temperature and is heated "
                  "with it as part of the block; the mass given is that of the block alone.",
     scene_object_rationale="A scale pan is a separate object; lead placed on it is not placed on the block, so the mass that is "
                            "heated is the stated one.",
     scene_refs=("scale pan",),
     relevant=dataclasses.replace(OLD["S256"].relevant, rationale="Further lead placed on the block before the heating is joined to "
                                  "it and heated with it, so the mass becomes m + q."),
     pairs=(_pair("S256", 0, frame="Before the heating begins, a further {value} {unit} of lead is placed on {relation}.",
                  r_attach="the block", d_attach="the scale pan",
                  d_rationale="Lead placed on the scale pan stays on the pan; the block keeps its stated mass, and the heating and "
                              "its end points are as stated."),
            _pair("S256", 1, frame="{relation} a further {value} {unit} of lead was placed on the block.",
                  d_attach="For an earlier experiment only,",  # main session: 'only' says the lead is not on the block now (rule 7)
                  d_rationale="The block carried the further lead in an earlier experiment; in the stated heating it has only its "
                              "stated mass.")))
CHANGES["S256"] = (
    ("claude and gpt high: temperature and joining of the added lead unstated",
     "scene clause: lead placed on the block 'is joined to it, is at its temperature and is heated with it as part of the block; the "
     "mass given is that of the block alone'"),
    ("D0/N0 artificial (lead added to a lead weight on a hook)", "'... a further {v} of lead is placed on the scale pan.'"),
    ("D1 artificial ('added to the block, for one heating only')",
     "'In an earlier experiment, a further {v} of lead was placed on the block.'"),
    ("R0/R1 slightly artificial (no means of joining; 'for one heating only')",
     "'placed on the block' with the joining stated in the scene clause; 'for one heating only' dropped"))

# --- S262 ---------------------------------------------------------------------------------------------------------------------------
_fix("S262", "K (laminar-transition Reynolds number) removed; oil is poured in until deeper, tube closed until the draining starts.",
     conditional=None,
     scene_clause="A bucket with some oil in it stands beside the tank. The depth given is that of the oil in the tank when it is "
                  "first filled, and the tube is closed until the draining starts.",
     scene_object_rationale="A bucket of oil beside the tank is a separate vessel; oil poured into it does not enter the tank, so the "
                            "initial depth of the oil in the tank is the stated one.",
     pairs=(_pair("S262", 0, frame="Before the draining starts, more oil is poured into {relation} until the oil is {value} {unit} "
                                   "deeper.",
                  nonnumeric_fill="a little"),
            _pair("S262", 1, frame="{relation} more oil was poured into the tank until the oil was {value} {unit} deeper.",
                  nonnumeric_fill="a little")))
NO_K["S262"] = ("A laminar-transition Reynolds number does not determine an alternative flow law for the drainage time, so no "
                "honest out-of-regime reference time exists for the stated model.")
K_KINDS.pop("S262", None)
CHANGES["S262"] = (
    ("gpt high: K out-of-regime reference tc*q/1000 unjustified", "K removed (conditional=None, NO_K)"),
    ("R0/R1 slightly artificial (topping up after the tank was said to be filled)",
     "'Before the draining starts, more oil is poured into the tank until the oil is {v} deeper.'; the scene clause says the depth "
     "given is that when the tank is first filled and the tube is closed until the draining starts"),
    ("D0/N0/D1/N1 slightly artificial ('topped up by a modest depth')",
     "'... more oil is poured into the bucket until the oil is {v} deeper.'; fill 'a little'"))

ROLE_SPECS: dict[str, r2.RoleSpecV2] = {sid: FIXED.get(sid, spec) for sid, spec in OLD.items() if sid not in DROPPED}
SPECS = ROLE_SPECS
INFEASIBLE: dict[str, str] = {**dict(SRC.INFEASIBLE), **{sid: f"repair round 2: {why}" for sid, why in DROPPED.items()}}
STRUCTURE_FACTORIES = {**SRC.STRUCTURE_FACTORIES, **STRUCTURE_OVERRIDES}


def structure(structure_id: str) -> gr.Structure:
    """The structure (repaired factory if any) with the repaired spec's scene clause appended to its base context."""

    return r2.with_scene(STRUCTURE_FACTORIES[structure_id](), ROLE_SPECS[structure_id].scene_clause)
