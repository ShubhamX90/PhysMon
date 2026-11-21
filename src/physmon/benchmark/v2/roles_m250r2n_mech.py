"""M250 repair round 2 (journal J15.1-061) of `roles_m250r1n_mech`: the specs the two-judge re-review rejected (any high flag) or whose sentences
the blind naturalness rater rated artificial, repaired again; every other spec is the `roles_m250r1n_mech` object, unchanged.

Brief: `/scratch/pabitra/physmon/repair_m250_r2/briefs/roles_m250r1n_mech.md` (`scripts/v2/s207_m250_repair_briefs.py` from
`docs/validation/v2/llm_panel/admission_m250r1/runs/score_two_judges/`). No model output exists on any of these structures. The round-1
history of each structure is in `roles_m250r1n_mech.CHANGES`; wording rules 1-8 of the original module apply.

`CHANGES` records, per changed structure, each finding and how it was resolved; `DROPPED` holds structures that could not be repaired.
"""

from __future__ import annotations

import dataclasses

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import rolevalue_v2 as r2
from physmon.benchmark.v2 import roles_m250r1n_mech as SRC

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

def _note(sid: str, text: str) -> str:
    return f"{OLD[sid].notes} M250 r2: {text}".strip()


def _pair(sid: str, i: int, **kw):
    return dataclasses.replace(OLD[sid].pairs[i], **kw)


# ---- S202 ----
FIXED["S202"] = dataclasses.replace(
    OLD["S202"],
    scene_clause="A small service tug floats nearby. The empty mass given is that of the rocket alone.",
    pairs=(
        OLD["S202"].pairs[0],
        _pair("S202", 1, d_attach="for its previous flight only"),
    ),
    notes=_note("S202", "scene clause states what the stated empty mass covers (the rocket alone), so the base has no bolted cargo "
                        "and R's payload is added to the final mass; D1/N1 'for its previous flight only'."))
CHANGES["S202"] = (
    ("gpt high insufficient_boundary_condition: the amount of bolted cargo is never stated",
     "scene clause 'Besides its body, engine and fuel, the rocket carries only what is bolted to it.' -> 'The empty mass given is "
     "that of the rocket alone.' (the base has no cargo; R's payload is added to it)"),
    ("ratings D1/N1 slightly artificial 'on its previous flight only'", "'for its previous flight only'"),
)

# ---- S204 ----
FIXED["S204"] = dataclasses.replace(
    OLD["S204"],
    pairs=(
        OLD["S204"].pairs[0],
        _pair("S204", 1, frame="The skater moving east carried a {value} {unit} bag {relation}.",
              r_attach="throughout this glide and the collision", d_attach="on an earlier outing only",
              d_rationale="The bag was carried on an earlier outing, which is over; on the stated outing the skater carries nothing "
                          "but the stated mass."),
    ),
    notes=_note("S204", "pair 1 reworded in the active voice: 'The skater moving east carried a {v} bag throughout this glide and the "
                        "collision' / 'on an earlier outing only'."))
CHANGES["S204"] = (
    ("rating N1 artificial: 'A small bag was carried by the skater moving east on an earlier outing only.'",
     "'The skater moving east carried a small bag on an earlier outing only.'"),
    ("rating R1/D1 slightly artificial (passive, 'through the whole glide and the collision')",
     "R1 'The skater moving east carried a 12 kg bag throughout this glide and the collision.'; D1 '... on an earlier outing only.'"),
)


ROLE_SPECS: dict[str, r2.RoleSpecV2] = {sid: FIXED.get(sid, spec) for sid, spec in OLD.items() if sid not in DROPPED}
SPECS = ROLE_SPECS
INFEASIBLE: dict[str, str] = {**dict(SRC.INFEASIBLE), **{sid: f"repair round 2: {why}" for sid, why in DROPPED.items()}}
STRUCTURE_FACTORIES = {**SRC.STRUCTURE_FACTORIES, **STRUCTURE_OVERRIDES}


def structure(structure_id: str) -> gr.Structure:
    """The structure (repaired factory if any) with the repaired spec's scene clause appended to its base context."""

    return r2.with_scene(STRUCTURE_FACTORIES[structure_id](), ROLE_SPECS[structure_id].scene_clause)
