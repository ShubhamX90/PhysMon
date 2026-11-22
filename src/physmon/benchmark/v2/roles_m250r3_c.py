"""M250 repair round 3 (journal J15.1-063) of `roles_m250r2_c`: the specs the round-2 re-review rejected (any high flag) or whose sentences the
blind naturalness rater rated artificial, repaired again; every other spec is the `roles_m250r2_c` object, unchanged.

Brief: `/scratch/pabitra/physmon/repair_m250_r3/briefs/roles_m250r2_c.md` (`scripts/v2/s207_m250_repair_briefs.py` from
`docs/validation/v2/llm_panel/admission_m250r2/runs/score_two_judges/`). No model output exists on any of these structures. Earlier rounds'
history is in `roles_m250r2_c.CHANGES` and its SRC chain; wording rules 1-8 of the original module apply.

`CHANGES` records, per changed structure, each finding and how it was resolved; `DROPPED` holds structures that could not be repaired.
"""

from __future__ import annotations

import dataclasses

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import rolevalue_v2 as r2
from physmon.benchmark.v2 import roles_m250r2_c as SRC

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


_S54 = OLD["S54"]
_S54_P0 = dataclasses.replace(
    _S54.pairs[0], d_attach="cast around the small ball",
    d_rationale="A layer cast around the small ball thickens that ball only; the second sphere keeps its stated radius, surface "
    "temperature and finish.",
)
_S54_P1 = dataclasses.replace(
    _S54.pairs[1], d_attach="cast around the small disc",
    d_rationale="A layer cast around the small disc thickens that disc only; the second sphere keeps its stated radius, surface "
    "temperature and finish.",
    d_kind_note="No honest same-object event exists for this quantity: a layer of metal cast around the second sphere in an earlier "
    "experiment is still on it. A second co-present object of a different type (the small disc, named in the scene clause with the "
    "small ball) is used instead.",
)
FIXED["S54"] = dataclasses.replace(
    _S54, pairs=(_S54_P0, _S54_P1),
    scene_clause=(
        "A small ball and a small disc, both of the same metal as the spheres, hang from a frame nearby. Metal cast around a body "
        "has the same surface finish as that body. The radius given for the second sphere is its radius as it was made, and the "
        "temperature given is that of its outer surface."
    ),
    scene_object_rationale="A small ball and a small disc hanging from a frame nearby are not the spheres; at the temperature of "
    "the much colder surroundings they exchange no appreciable radiation with the spheres and leave their radii and surface "
    "temperatures as stated.",
    scene_refs=("small ball",),
    notes=_S54.notes + " M250 r3: D objects are a small ball and a small disc (casting a thick layer around a hanging bracket was "
    "rated artificial); scene clause states that cast metal has the same surface finish.",
)
CHANGES["S54"] = (
    ("D0 rated artificial: 'A 4.5 cm layer of the same metal is cast around the bracket.'",
     "'... cast around the small ball.' (casting metal around a small ball of that metal is an ordinary foundry step)"),
    ("D1/N0/N1 slightly artificial (bracket, disc)", "'small ball' / 'small disc'"),
    ("claude low: new surface finish not stated", "scene clause: 'Metal cast around a body has the same surface finish as that body.'"),
    ("gpt high rendering_not_minimal (N sentences lack the number)", "5.3b judge error, N sentences numeral-free by design; unchanged"),
)

ROLE_SPECS: dict[str, r2.RoleSpecV2] = {sid: FIXED.get(sid, spec) for sid, spec in OLD.items() if sid not in DROPPED}
SPECS = ROLE_SPECS
INFEASIBLE: dict[str, str] = {**dict(SRC.INFEASIBLE), **{sid: f"repair round 3: {why}" for sid, why in DROPPED.items()}}
STRUCTURE_FACTORIES = {**SRC.STRUCTURE_FACTORIES, **STRUCTURE_OVERRIDES}


def structure(structure_id: str) -> gr.Structure:
    """The structure (repaired factory if any) with the repaired spec's scene clause appended to its base context."""

    return r2.with_scene(STRUCTURE_FACTORIES[structure_id](), ROLE_SPECS[structure_id].scene_clause)
