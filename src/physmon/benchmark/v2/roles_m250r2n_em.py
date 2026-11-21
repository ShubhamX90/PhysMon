"""M250 repair round 2 (journal J15.1-061) of `roles_m250r1n_em`: the specs the two-judge re-review rejected (any high flag) or whose sentences
the blind naturalness rater rated artificial, repaired again; every other spec is the `roles_m250r1n_em` object, unchanged.

Brief: `/scratch/pabitra/physmon/repair_m250_r2/briefs/roles_m250r1n_em.md` (`scripts/v2/s207_m250_repair_briefs.py` from
`docs/validation/v2/llm_panel/admission_m250r1/runs/score_two_judges/`). No model output exists on any of these structures. The round-1
history of each structure is in `roles_m250r1n_em.CHANGES`; wording rules 1-8 of the original module apply.

`CHANGES` records, per changed structure, each finding and how it was resolved; `DROPPED` holds structures that could not be repaired.
"""

from __future__ import annotations

import dataclasses

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import rolevalue_v2 as r2
from physmon.benchmark.v2 import roles_m250r1n_em as SRC

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


# ---- S211 ----
FIXED["S211"] = dataclasses.replace(
    OLD["S211"],
    quantity_phrase="a plastic holder",
    pairs=(
        _pair("S211", 0, frame="An uncharged {value} {unit} plastic holder is attached to {relation}."),
        _pair("S211", 1, frame="An uncharged {value} {unit} plastic holder {relation}.",
              r_attach="is glued to the bead and moves with it when released",
              d_attach="was glued to the bead for an earlier trial only",
              d_rationale="The holder was on the bead in an earlier trial, which is over; the bead of the stated release carries no "
                          "holder, so its mass is the stated one."),
    ),
    notes=_note("S211", "the added mass is an uncharged plastic holder (a holder heavier than the bead is ordinary; a 'clip riding on' a "
                        "0.5 g bead was rated artificial); R1 'is glued to the bead and moves with it when released'."))
CHANGES["S211"] = (
    ("rating R1 artificial: 'An uncharged 0.7 g plastic clip rides on the bead when it is released.' (clip heavier than the bead)",
     "'An uncharged 0.7 g plastic holder is glued to the bead and moves with it when released.' (D1/N1 'was glued to the bead for "
     "an earlier trial only'; R0/D0/N0 say 'holder' too)"),
    ("ratings D0/N0/D1/N1 slightly artificial", "clip -> holder in all frames; D1 'glued ... for an earlier trial only'."),
)


ROLE_SPECS: dict[str, r2.RoleSpecV2] = {sid: FIXED.get(sid, spec) for sid, spec in OLD.items() if sid not in DROPPED}
SPECS = ROLE_SPECS
INFEASIBLE: dict[str, str] = {**dict(SRC.INFEASIBLE), **{sid: f"repair round 2: {why}" for sid, why in DROPPED.items()}}
STRUCTURE_FACTORIES = {**SRC.STRUCTURE_FACTORIES, **STRUCTURE_OVERRIDES}


def structure(structure_id: str) -> gr.Structure:
    """The structure (repaired factory if any) with the repaired spec's scene clause appended to its base context."""

    return r2.with_scene(STRUCTURE_FACTORIES[structure_id](), ROLE_SPECS[structure_id].scene_clause)
