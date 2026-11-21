"""M250 repair round 1 (journal J15.1-059) of `roles_m250n_mech`: the specs the two-judge panel rejected (any high flag) or whose sentences the
blind naturalness rater rated artificial, repaired; every other spec is the `roles_m250n_mech` object, unchanged.

Brief: `/scratch/pabitra/physmon/repair_m250_r1/briefs/roles_m250n_mech.md` (built by `scripts/v2/s207_m250_repair_briefs.py` from
`docs/validation/v2/llm_panel/admission_m250/runs/score_two_judges/`). No model output exists on any of these structures, so they may
still be edited (dataset admission standard, preamble). Wording rules 1-8 of `roles_m250n_mech` apply to every changed sentence.

`CHANGES` records, per changed structure, each finding and how it was resolved; `DROPPED` holds structures that could not be repaired
(they move to `INFEASIBLE` with the reason and are replaced in a later batch).
"""

from __future__ import annotations

import dataclasses

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import rolevalue_v2 as r2
from physmon.benchmark.v2 import roles_m250n_mech as SRC

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

# --- repairs ---------------------------------------------------------------------------------------------------------------------

def _note(sid: str, text: str) -> str:
    return f"{OLD[sid].notes} M250 r1: {text}".strip()


# S202: the base never said whether the rocket carries a payload (GPT high); D1 rated slightly artificial.
_S202_P = OLD["S202"].pairs
FIXED["S202"] = dataclasses.replace(
    OLD["S202"],
    scene_clause="A small service tug floats nearby. Besides its body, engine and fuel, the rocket carries only what is bolted to it.",
    pairs=(_S202_P[0], dataclasses.replace(_S202_P[1], d_attach="on its previous flight only")),
    notes=_note("S202", "the scene clause states that besides body, engine and fuel the rocket carries only what is bolted to it (main "
                        "session: not 'carries no payload', which the R sentence would contradict), so the base has no payload and R's "
                        "bolted payload is part of the final mass; D1/N1 'on its previous flight only' replaces 'for an earlier flight only'."))
CHANGES["S202"] = (
    ("gpt high insufficient_boundary_condition: payload mass or its absence never stated",
     "scene clause 'A small service tug floats nearby.' -> 'A small service tug floats nearby. Besides its body, engine and fuel, the rocket carries only what is bolted to it.' (main-session correction of the worker's 'The rocket carries no payload.')"),
    ("D1/N1 rated slightly_artificial ('for an earlier flight only')",
     "D1/N1 attachment 'for an earlier flight only' -> 'on its previous flight only'"),
)

# S203: the platform's acceleration in the base was unfixed (GPT high); R1 persistence ambiguous; N0 artificial; D/R slightly artificial.
_S203_P = OLD["S203"].pairs
_S203_P0 = dataclasses.replace(
    _S203_P[0],
    frame="The {relation} moves with a constant upward acceleration of {value} {unit} while the bead oscillates.",
    d_attach="load on the crane hook",
    d_rationale="The load on the crane hook is raised with its own acceleration; it is not attached to the platform, so the platform "
                "stays on the ground and the apparent gravity in the frame of the hoop is the stated g.")
_S203_P1 = dataclasses.replace(
    _S203_P[1],
    frame="The platform carrying the hoop was rising with a constant upward acceleration of {value} {unit} {relation}.",
    r_attach="while the oscillations were observed",
    d_attach="in an earlier run only",
    d_rationale="The platform rose in an earlier run, which is over; in the stated run the platform rests on the ground and g is the stated value.")
FIXED["S203"] = dataclasses.replace(
    OLD["S203"],
    scene_clause="A crane stands beside the platform. Unless it is set moving, the platform stays still on level ground.",
    pairs=(_S203_P0, _S203_P1),
    notes=_note("S203", "the scene clause fixes the platform's state (still on level ground unless it is set moving; main session: not 'rests', which R would contradict); R0/D0 'moves with a constant upward acceleration of "
                        "{v} while the bead oscillates' (load on the crane hook for D0); R1 'was rising ... while the oscillations were observed' "
                        "so the acceleration holds during the oscillations; D1/N1 'in an earlier run only'."))
CHANGES["S203"] = (
    ("gpt high insufficient_boundary_condition: platform's acceleration not fixed in the base; R1 does not say whether the acceleration continues",
     "scene clause -> 'A crane stands beside the platform. Unless it is set moving, the platform stays still on level ground.'; R1 'was set rising ... before the "
     "oscillations were observed' -> 'was rising ... while the oscillations were observed' (one reading: it holds during the oscillations)"),
    ("claude medium: R1 past-phase reading possible", "same R1 rewrite"),
    ("N0 artificial ('The hook of the crane accelerates upward at a constant rate of a few metres per second squared while the bead oscillates.')",
     "pair-0 frame 'The {relation} moves with a constant upward acceleration of {value} {unit} while the bead oscillates.'; D0/N0 subject "
     "'load on the crane hook' instead of 'hook of the crane'; N0 now '... upward acceleration of a few metres per second squared ...'"),
    ("D0/R0/R1/D1/N1 slightly_artificial", "R0/D0 reworded as above; D1/N1 'for an earlier run only' -> 'in an earlier run only'"),
)

# S204: R1 did not say the bag stays with the skater through the collision (GPT high) nor which speed (Claude medium); D1/N1 artificial.
_S204_P = OLD["S204"].pairs
_S204_P1 = dataclasses.replace(
    _S204_P[1],
    frame="A {value} {unit} bag was carried by the skater moving east {relation}.",
    r_attach="through the whole glide and the collision",
    d_attach="on an earlier outing only",
    d_rationale="The bag was carried on an earlier outing, which is over; on the stated outing the skater carries nothing but the stated mass.")
FIXED["S204"] = dataclasses.replace(
    OLD["S204"],
    pairs=(_S204_P[0], _S204_P1),
    notes=_note("S204", "R1 'A {v} bag was carried by the skater moving east through the whole glide and the collision' (the bag stays with the "
                        "skater, so the stated 4 m/s is the speed of skater and bag); D1/N1 'A {v} bag was carried ... on an earlier outing only'."))
CHANGES["S204"] = (
    ("gpt high insufficient_boundary_condition: R1 does not state the bag remains with the skater during the collision",
     "R1 'The skater moving east picked up a 12 kg bag shortly before the collision.' -> 'A 12 kg bag was carried by the skater moving east "
     "through the whole glide and the collision.'"),
    ("claude medium: R1 does not say whether the stated 4 m/s holds after the pickup", "same rewrite: the bag is carried throughout, so 4 m/s is the speed of skater and bag"),
    ("D1 and N1 artificial ('picked up a 12 kg bag on an earlier outing only')",
     "'A 12 kg bag was carried by the skater moving east on an earlier outing only.' (N1: 'A small bag was carried ... on an earlier outing only.')"),
    ("R0 slightly_artificial", "unchanged frame (passive 'carried by'), the quantity is added to the skater's load and is plain English"),
)

# S205: a 6 g price tag on a 12 g coin is implausible (R0, R1, D1, N1 artificial) -> a steel washer taped to the coin.
_S205_P = OLD["S205"].pairs
_S205_P0 = dataclasses.replace(
    _S205_P[0], frame="A {value} {unit} washer is {relation}.", r_attach="taped to the coin", d_attach="lying in the dish",
    d_rationale="A washer lying in the dish loads the dish only; the coin keeps its stated mass.")
_S205_P1 = dataclasses.replace(
    _S205_P[1], frame="A {value} {unit} washer was taped to the coin {relation}.", r_attach="before the turntable was started",
    d_attach="in an earlier trial only",
    d_rationale="The washer was taped to the coin in an earlier trial, which is over; the coin of the stated run has only its stated mass.")
FIXED["S205"] = dataclasses.replace(
    OLD["S205"], quantity_phrase="a washer", values=(2.0, 5.0, 7.0), heldout_values=(3.0, 6.0),
    relevant=dataclasses.replace(OLD["S205"].relevant, rationale="A washer taped to the coin travels with it, so the mass that has to be "
                                                                   "accelerated becomes m + q and the friction force grows with it."),
    pairs=(_S205_P0, _S205_P1),
    notes=_note("S205", "the price tag (6 g, half the coin's mass) is replaced by a steel washer of 2 to 7 g taped to the coin; D0 'lying in the dish'; "
                        "D1 'in an earlier trial only'."))
CHANGES["S205"] = (
    ("R0/R1/D1/N1 artificial (a 6 g price tag stuck to a 12 g coin is implausible)",
     "'A 6 g price tag is stuck to the coin.' -> 'A 5 g washer is taped to the coin.'; study values 2/6/15 g -> 2/5/7 g (4 g would equal the displayed 4 s), held-out 3/6 g; "
     "R1 'A 5 g washer was taped to the coin before the turntable was started.'"),
    ("D1/N1 'A 6 g price tag was stuck to the coin for an earlier trial only.'", "'A 5 g washer was taped to the coin in an earlier trial only.' (N1: 'A small washer ...')"),
    ("D0 slightly_artificial ('A 6 g price tag is stuck to the dish.')", "'A 5 g washer is lying in the dish.'"),
)

# S207: N0 artificial (a sandbag placed in a toolbox); D0 slightly artificial.
_S207_P = OLD["S207"].pairs
FIXED["S207"] = dataclasses.replace(
    OLD["S207"],
    pairs=(dataclasses.replace(_S207_P[0], d_attach="lying on the toolbox",
                               d_rationale="A sandbag lying on the toolbox rests on the floor rig-side and touches none of the blocks, strings or pulleys; "
                                           "the masses on the strings are the stated ones."), _S207_P[1]),
    notes=_note("S207", "D0/N0 'A {v} sandbag is lying on the toolbox' replaces 'placed in the toolbox' (plain stative wording)."))
CHANGES["S207"] = (
    ("N0 artificial ('A small sandbag is placed in the toolbox.')", "'A small sandbag is lying on the toolbox.'"),
    ("D0 slightly_artificial ('A 2.4 kg sandbag is placed in the toolbox.')", "'A 2.4 kg sandbag is lying on the toolbox.'"),
)

# S208: N0/N1 artificial ('a ring whose moment of inertia is a small amount').
_S208_P = OLD["S208"].pairs
FIXED["S208"] = dataclasses.replace(
    OLD["S208"],
    pairs=(dataclasses.replace(_S208_P[0], frame="A ring is {relation}, and its moment of inertia is {value} {unit}.", nonnumeric_fill="small"),
           dataclasses.replace(_S208_P[1], frame="{relation}, a ring was glued to the second disc; its moment of inertia is {value} {unit}.",
                               r_attach="Before the spinning disc was lowered", d_attach="For an earlier run only", nonnumeric_fill="small")),
    notes=_note("S208", "frames 'A ring is {relation}, and its moment of inertia is {v}.' / '{relation}, a ring was glued to the second disc; its "
                        "moment of inertia is {v}.' so that N reads 'its moment of inertia is small'."))
CHANGES["S208"] = (
    ("gpt high rendering_not_minimal: N0/N1 omit number and unit (5.3b: N sentences carry no number by design)",
     "kept numeral-free by design; the N wording is now natural"),
    ("N0/N1 artificial ('A ring whose moment of inertia is a small amount ...')",
     "'A ring is fitted to the grinding wheel, and its moment of inertia is small.' / 'For an earlier run only, a ring was glued to the second "
     "disc; its moment of inertia is small.'"),
    ("D0/D1 slightly_artificial", "same frame rewrite"),
)

# S209: the rod's initial state unstated (GPT high), R0 timing unspecified; D0/N0 artificial (clay pressed onto a vase).
_S209_P = OLD["S209"].pairs
_S209_P0 = dataclasses.replace(
    _S209_P[0], frame="A further {value} {unit} piece of clay is {relation}.", r_attach="pressed onto the lump and travels with it",
    d_attach="pressed onto the pot and stays there",
    d_rationale="Clay pressed onto the pot adds to the pot only; the lump of clay that hits the rod keeps its stated mass.")
FIXED["S209"] = dataclasses.replace(
    OLD["S209"],
    scene_clause="A half-finished pot stands on a shelf above the table. The rod is at rest on the table before the clay arrives.",
    scene_refs=("pot",), pairs=(_S209_P0, _S209_P[1]),
    scene_object_rationale="A pot on a shelf above the table is not on the table and does not touch the rod or the lump, so the collision of the "
                           "lump with the rod is unchanged; the rod being at rest before the impact is the situation the stated answer assumes.",
    notes=_note("S209", "scene clause states that the rod is at rest before the impact; the vase becomes a half-finished pot (clay is added to pots); "
                        "R0 'pressed onto the lump and travels with it' / D0 'pressed onto the pot and stays there'."))
CHANGES["S209"] = (
    ("gpt high insufficient_boundary_condition: rod's initial translational and angular velocities unspecified",
     "scene clause 'A vase stands on a shelf above the table.' -> 'A half-finished pot stands on a shelf above the table. The rod is at rest on "
     "the table before the clay arrives.'"),
    ("gpt: R0 attachment time unspecified", "R0 'A further 0.13 kg piece of clay is pressed onto the lump and travels with it.'"),
    ("D0/N0 artificial ('A further 0.13 kg piece of clay is pressed onto the vase.')",
     "'A further 0.13 kg piece of clay is pressed onto the pot and stays there.' (pot replaces vase in the scene)"),
)

# S210: N0/N1 artificial ('a damping coefficient of a small value').
_S210_P = OLD["S210"].pairs
FIXED["S210"] = dataclasses.replace(
    OLD["S210"],
    pairs=(dataclasses.replace(_S210_P[0], frame="An extra damper whose damping coefficient is {value} {unit} is {relation}.", nonnumeric_fill="small"),
           dataclasses.replace(_S210_P[1], frame="An extra damper whose damping coefficient is {value} {unit} was fitted to the block {relation}.",
                               nonnumeric_fill="small")),
    notes=_note("S210", "frames 'An extra damper whose damping coefficient is {v} ...' so that N reads 'whose damping coefficient is small'."))
CHANGES["S210"] = (
    ("gpt high rendering_not_minimal on N0/N1 (5.3b judge error, N numeral-free by design)", "kept numeral-free by design"),
    ("N0/N1 artificial ('an extra damper with a damping coefficient of a small value')", "'An extra damper whose damping coefficient is small is fitted to the door.' (N1 likewise)"),
)

ROLE_SPECS: dict[str, r2.RoleSpecV2] = {sid: FIXED.get(sid, spec) for sid, spec in OLD.items() if sid not in DROPPED}
SPECS = ROLE_SPECS
INFEASIBLE: dict[str, str] = {**dict(SRC.INFEASIBLE), **{sid: f"repair round 1: {why}" for sid, why in DROPPED.items()}}
STRUCTURE_FACTORIES = {**SRC.STRUCTURE_FACTORIES, **STRUCTURE_OVERRIDES}


def structure(structure_id: str) -> gr.Structure:
    """The structure (repaired factory if any) with the repaired spec's scene clause appended to its base context."""

    return r2.with_scene(STRUCTURE_FACTORIES[structure_id](), ROLE_SPECS[structure_id].scene_clause)
