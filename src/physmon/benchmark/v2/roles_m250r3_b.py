"""M250 repair round 3 (journal J15.1-063) of `roles_m250r2_b`: the specs the round-2 re-review rejected (any high flag) or whose sentences the
blind naturalness rater rated artificial, repaired again; every other spec is the `roles_m250r2_b` object, unchanged.

Brief: `/scratch/pabitra/physmon/repair_m250_r3/briefs/roles_m250r2_b.md` (`scripts/v2/s207_m250_repair_briefs.py` from
`docs/validation/v2/llm_panel/admission_m250r2/runs/score_two_judges/`). No model output exists on any of these structures. Earlier rounds'
history is in `roles_m250r2_b.CHANGES` and its SRC chain; wording rules 1-8 of the original module apply.

`CHANGES` records, per changed structure, each finding and how it was resolved; `DROPPED` holds structures that could not be repaired.
"""

from __future__ import annotations

import dataclasses

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import rolevalue_v2 as r2
from physmon.benchmark.v2 import roles_m250r2_b as SRC

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

# structure id -> replacement structure factory (when the base problem or its assumptions must change); default: SRC's
STRUCTURE_OVERRIDES: dict[str, object] = {}

# structure id -> reason the structure could not be repaired (it is removed from the specs and recorded as infeasible)
DROPPED: dict[str, str] = {}


_S35 = OLD["S35"]
_S35_P0 = dataclasses.replace(
    _S35.pairs[0],
    frame="{relation} is let out by {value} {unit} before the first bob is set moving.",
    r_attach="The first bob's string",
    d_attach="The second bob's string",
    d_rationale="The string of a second bob that hangs at rest is not the pendulum's string; lengthening it leaves the length of the "
    "moving bob's string as stated.",
)
FIXED["S35"] = dataclasses.replace(
    _S35, pairs=(_S35_P0, _S35.pairs[1]),
    notes=_S35.notes + " M250 r3: pair-0 frame 'before the first bob is set moving' names the moving bob, so the second bob's "
    "string is let out for its own reason (adjusting where it hangs) and no bob is ambiguous.",
)
CHANGES["S35"] = (
    ("D0 rated artificial: 'The second bob's string is let out by 0.7 m before the bob is set moving' (pointless; which bob moves?)",
     "frame now '... before the first bob is set moving' (R: 'The first bob's string is let out ...', D: 'The second bob's string ...'); "
     "N0 follows the same frame"),
    ("claude low: 'the bob' ambiguous in D0/N0", "'the first bob' names the moving bob"),
)

_S41 = OLD["S41"]
_S41_P0 = dataclasses.replace(
    _S41.pairs[0],
    d_attach="The wooden blocks are",
    d_rationale="Uncharged wooden blocks far from the charged spheres exert no electrostatic force on them; moving the blocks apart "
    "leaves the separation of the charged spheres as stated.",
)
FIXED["S41"] = dataclasses.replace(
    _S41, pairs=(_S41_P0, _S41.pairs[1]),
    scene_clause="Two uncharged wooden blocks stand on the bench, far from the charged spheres, marking out the space for a later "
    "set-up. The charged spheres are insulated from their surroundings, and no other charges are near them.",
    scene_object_rationale="Uncharged wooden blocks far from the charged spheres exert no electrostatic force on them, so the force "
    "between the spheres is unchanged.",
    scene_refs=("wooden blocks",),
    notes=_S41.notes + " M250 r3: D0/N0 move two wooden blocks that mark out the space for a later set-up (glass rods moved apart "
    "for no reason were rated artificial).",
)
CHANGES["S41"] = (
    ("D0 rated artificial: 'The glass rods are then moved 26 cm further apart.' (pointless action)",
     "'The wooden blocks are then moved 26 cm further apart.'; scene clause: two wooden blocks mark out the space for a later set-up"),
    ("N0 slightly artificial: glass rods moved a few centimetres", "same wooden-block object"),
)

ROLE_SPECS: dict[str, r2.RoleSpecV2] = {sid: FIXED.get(sid, spec) for sid, spec in OLD.items() if sid not in DROPPED}
SPECS = ROLE_SPECS
INFEASIBLE: dict[str, str] = {**dict(SRC.INFEASIBLE), **{sid: f"repair round 3: {why}" for sid, why in DROPPED.items()}}
STRUCTURE_FACTORIES = {**SRC.STRUCTURE_FACTORIES, **STRUCTURE_OVERRIDES}


def structure(structure_id: str) -> gr.Structure:
    """The structure (repaired factory if any) with the repaired spec's scene clause appended to its base context."""

    return r2.with_scene(STRUCTURE_FACTORIES[structure_id](), ROLE_SPECS[structure_id].scene_clause)
