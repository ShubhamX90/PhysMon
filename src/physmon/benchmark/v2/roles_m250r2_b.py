"""M250 repair round 2 (journal J15.1-061) of `roles_m250r1_b`: the specs the two-judge re-review rejected (any high flag) or whose sentences
the blind naturalness rater rated artificial, repaired again; every other spec is the `roles_m250r1_b` object, unchanged.

Brief: `/scratch/pabitra/physmon/repair_m250_r2/briefs/roles_m250r1_b.md` (`scripts/v2/s207_m250_repair_briefs.py` from
`docs/validation/v2/llm_panel/admission_m250r1/runs/score_two_judges/`). No model output exists on any of these structures. The round-1
history of each structure is in `roles_m250r1_b.CHANGES`; wording rules 1-8 of the original module apply.

`CHANGES` records, per changed structure, each finding and how it was resolved; `DROPPED` holds structures that could not be repaired.
"""

from __future__ import annotations

import dataclasses

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import rolevalue_v2 as r2
from physmon.benchmark.v2 import roles_m250r1_b as SRC

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

P = dataclasses.replace


def _pr(sid: str, i: int, **kw):
    return dataclasses.replace(OLD[sid].pairs[i], **kw)


def _fx(sid: str, note: str, **kw) -> r2.RoleSpecV2:
    spec = OLD[sid]
    return dataclasses.replace(spec, notes=f"{spec.notes} M250 r2: {note}".strip(), **kw)


# --- S28: no speed limit in the scene; K quantity (top speed) removed -------------------------------------------------------------
FIXED["S28"] = _fx(
    "S28", "K removed: a top speed below 30 m/s ends the pursuit before the car draws level and needs a post-cap rule; the scene "
           "clause now says the car's speed is not limited, so the base answer needs no unstated condition.",
    scene_clause="A motorbike waits at the roadside, off the road and clear of the car and the truck. The acceleration stated for the "
                 "car is the one it has as delivered, and nothing limits the speed the car reaches during the chase.",
    conditional=None)
NO_K["S28"] = ("A top speed below 30 m/s ends the car's acceleration before it draws level with the truck, and the answer then depends "
               "on how the car moves after reaching the cap; the base problem states no top speed, so the quantity is removed.")
CHANGES["S28"] = (
    ("gpt high missing_assumption: unspecified top speed need not exceed 30 m/s and motion after a binding cap is not specified",
     "Scene clause: 'it keeps that acceleration until it reaches its top speed, if it has one' -> 'nothing limits the speed the car "
     "reaches during the chase'; the K quantity (KO0/KO1 'The car has a top speed of 21 m/s', K0/K1 46 m/s) is removed "
     "(conditional=None); NO_K['S28'] gives the reason."),
    ("R/D/N slightly_artificial (kit wording)", "Wording kept: judged only slightly artificial and the frame is shared by all cells."),
)

# --- S34: second board; the tilt is placed before the launch in R0 ---------------------------------------------------------------
FIXED["S34"] = _fx(
    "S34", "pair 0 frame 'X is tilted {v} more steeply before the sphere is launched' (R0 'then' left the timing open); D0/N0 tilt a "
           "second board hinged like the incline (the solar panel was rated artificial).",
    scene_clause="A second board, hinged at its foot like the incline, stands beside it. The incline is a board hinged at its foot, set "
                 "at the stated angle at first and clamped before the sphere is launched. Air resistance and rolling resistance are "
                 "negligible, and the incline is long enough for the sphere to come to rest on it.",
    scene_object_rationale="A second hinged board beside the incline does not touch the sphere or the incline, so the sphere's roll is "
                           "unchanged.",
    scene_refs=("second board",),
    pairs=(_pr("S34", 0, frame="{relation} is tilted {value} {unit} more steeply before the sphere is launched.",
               r_attach="The incline", d_attach="The second board",
               d_rationale="A second board beside the incline is not the incline; tilting it leaves the angle of the incline the sphere "
                           "rolls up as stated.",
               before_context_reason="The R sentence refers to 'the incline' before the context introduces it."),
           OLD["S34"].pairs[1]))
CHANGES["S34"] = (
    ("gpt high + claude medium: R0 'The incline is then tilted 13 deg more steeply.' does not place the tilt before launch",
     "R0 'The incline is tilted 13 deg more steeply before the sphere is launched.' (stated angle is the first setting; one reading)."),
    ("N0 artificial 'The solar panel is then tilted a few degrees more steeply.'; D0 slightly_artificial",
     "Second hinged board replaces the solar panel: D0 'The second board is tilted 13 deg more steeply before the sphere is launched.', "
     "N0 '... a few degrees more steeply before ...'."),
)

# --- S35: second bob replaces the reel -------------------------------------------------------------------------------------------
FIXED["S35"] = _fx(
    "S35", "D0/N0 let out the string of a second bob that hangs at rest (the reel line was rated artificial, 'then' incoherent).",
    scene_clause="A second bob hangs at rest from a string of its own beside the first, clear of it. The string does not stretch. The "
                 "length stated for the string is its length at the outset; once the string has been changed, the bob again moves at "
                 "constant speed in a horizontal circle at the stated angle with the vertical.",
    scene_object_rationale="A second bob hanging at rest from its own string does not touch the moving bob or its string, so the motion "
                           "of the bob is unchanged.",
    scene_refs=("second bob",),
    pairs=(_pr("S35", 0, frame="{relation} is let out by {value} {unit} before the bob is set moving.",
               d_attach="The second bob's string",
               d_rationale="The string of a second bob that hangs at rest is not the pendulum's string; lengthening it leaves the "
                           "length of the moving bob's string as stated."),
           OLD["S35"].pairs[1]))
CHANGES["S35"] = (
    ("N0 artificial 'The line on the reel is then let out by a short length.'; D0 slightly_artificial",
     "D0 'The second bob\'s string is let out by 0.7 m before the bob is set moving.'; N0 '... by a short length before the bob is "
     "set moving.'; R0 'The string of the bob is let out by 0.7 m before the bob is set moving.'"),
    ("gpt medium rendering_not_minimal (N sentences numeral-free)", "Not changed: by design."),
)

# --- S36: timing of the pivot move fixed before the swinging --------------------------------------------------------------------
FIXED["S36"] = _fx(
    "S36", "scene clause says the stated distance is the pivot's position at the outset; pair 0 R/D/N move the pivot before the rod is "
           "set swinging (R0 moved a pivot of a rod already swinging).",
    scene_clause="A second rod hangs at rest from a pivot of its own nearby, clear of the rod that swings and its axis. The distance "
                 "stated from the centre of the rod to its axis is the distance at the outset.",
    pairs=(_pr("S36", 0, frame="The pivot of {relation} is moved {value} {unit} closer to its centre before the swinging starts.",
               r_attach="the rod", before_context_reason="The R sentence refers to 'the rod' before the context introduces it."),
           OLD["S36"].pairs[1]))
CHANGES["S36"] = (
    ("gpt high: R1 does not say whether the stated 0.3 m offset applies before or after the move",
     "Scene clause: 'The distance stated from the centre of the rod to its axis is the distance at the outset.' R1 unchanged "
     "(0.3 m at the outset, moved 20.5 cm before the swinging)."),
    ("claude low: R0 moves the pivot of a rod described as swinging",
     "R0 'The pivot of the rod is moved 20.5 cm closer to its centre before the swinging starts.'; D0/N0 likewise with 'the second "
     "rod'."),
)

# --- S38: the ladder is not moved once the person stands on it -----------------------------------------------------------------
FIXED["S38"] = _fx(
    "S38", "scene clause: the stated angle is the angle at the outset and the ladder is not moved once the person stands on it; pair 0 "
           "R/D/N put the tilt before the person climbs on.",
    scene_clause="A hinged shutter is propped open beside the ladder. The angle stated for the ladder is its angle at the outset, and "
                 "once the person stands on the ladder it is not moved again.",
    pairs=(_pr("S38", 0, frame="{relation} is tilted {value} {unit} closer to the ground before the person climbs onto the ladder.",
               before_context_reason="The R sentence refers to 'the ladder' before the context introduces it."),
           OLD["S38"].pairs[1]))
CHANGES["S38"] = (
    ("gpt high: final equilibrium angle not specified", "Scene clause: 'The angle stated for the ladder is its angle at the outset, "
                                                       "and once the person stands on the ladder it is not moved again.' R0/R1 tilt "
                                                       "the ladder before the person stands on it, so the ground force is at 62 - q deg."),
    ("R1 slightly_artificial (convoluted set-up)", "The set-up sentence is now short and plain."),
)

# --- S41: glass rods replace the magnets; the extra move follows the stated one -----------------------------------------------
FIXED["S41"] = _fx(
    "S41", "R1 'Afterwards' places the extra move after the stated 60 cm separation; the meta sentence about the force asked for is "
           "dropped; D0/N0 move a pair of uncharged glass rods (bar magnets were rated artificial; main session: rods, not spheres, so that 'the spheres' has one referent).",
    scene_clause="A pair of uncharged glass rods lies on the bench, far from the charged spheres. The charged spheres are insulated from "
                 "their surroundings, and no other charges are near them.",
    scene_object_rationale="Uncharged glass rods far from the charged spheres exert no electrostatic force on them, so the force "
                           "between the spheres is unchanged.",
    scene_refs=("glass rods",),
    pairs=(_pr("S41", 0, d_attach="The glass rods are",
               d_rationale="A pair of uncharged glass rods on the bench exerts no electrostatic force on the charged spheres; moving "
                           "them apart leaves the separation of the charged spheres as stated."),
           _pr("S41", 1, r_attach="Afterwards")))
CHANGES["S41"] = (
    ("gpt high + claude low: R1 'Before the force was measured' does not fix the move relative to the stated 60 cm",
     "R1 'Afterwards, the spheres were moved 26 cm further apart.'; scene clause no longer carries the 'force asked for' sentence."),
    ("D0, N0 artificial (bar magnets)", "D0 'The glass rods are then moved 26 cm further apart.', N0 '... a few centimetres further "
                                        "apart.'"),
)

ROLE_SPECS: dict[str, r2.RoleSpecV2] = {sid: FIXED.get(sid, spec) for sid, spec in OLD.items() if sid not in DROPPED}
SPECS = ROLE_SPECS
INFEASIBLE: dict[str, str] = {**dict(SRC.INFEASIBLE), **{sid: f"repair round 2: {why}" for sid, why in DROPPED.items()}}
STRUCTURE_FACTORIES = {**SRC.STRUCTURE_FACTORIES, **STRUCTURE_OVERRIDES}


def structure(structure_id: str) -> gr.Structure:
    """The structure (repaired factory if any) with the repaired spec's scene clause appended to its base context."""

    return r2.with_scene(STRUCTURE_FACTORIES[structure_id](), ROLE_SPECS[structure_id].scene_clause)
