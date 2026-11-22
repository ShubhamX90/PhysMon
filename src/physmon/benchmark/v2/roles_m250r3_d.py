"""M250 repair round 3 (journal J15.1-063) of `roles_m250r2_d`: the specs the round-2 re-review rejected (any high flag) or whose sentences the
blind naturalness rater rated artificial, repaired again; every other spec is the `roles_m250r2_d` object, unchanged.

Brief: `/scratch/pabitra/physmon/repair_m250_r3/briefs/roles_m250r2_d.md` (`scripts/v2/s207_m250_repair_briefs.py` from
`docs/validation/v2/llm_panel/admission_m250r2/runs/score_two_judges/`). No model output exists on any of these structures. Earlier rounds'
history is in `roles_m250r2_d.CHANGES` and its SRC chain; wording rules 1-8 of the original module apply.

`CHANGES` records, per changed structure, each finding and how it was resolved; `DROPPED` holds structures that could not be repaired.
"""

from __future__ import annotations

import dataclasses

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import rolevalue_v2 as r2
from physmon.benchmark.v2 import roles_m250r2_d as SRC

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


_S82 = OLD["S82"]
_S82_P0 = dataclasses.replace(
    _S82.pairs[0],
    frame="Before the spectra are recorded, {relation} goes into an outburst that is still going on at the recording, and its "
    "surface temperature rises by {value} {unit}.",
)
FIXED["S82"] = dataclasses.replace(
    _S82, pairs=(_S82_P0, _S82.pairs[1]),
    notes=_S82.notes + " M250 r3: pair-0 sentence says the outburst is still going on at the recording (the raised temperature is the "
    "one at the recorded spectrum).",
)
CHANGES["S82"] = (
    ("gpt high insufficient_boundary_condition: R0 does not say the outburst is still underway at observation",
     "frame 'Before the spectra are recorded, X goes into an outburst that is still going on at the recording, and its surface "
     "temperature rises by 950 K.' (D0/N0 share the frame)"),
)

ROLE_SPECS: dict[str, r2.RoleSpecV2] = {sid: FIXED.get(sid, spec) for sid, spec in OLD.items() if sid not in DROPPED}
SPECS = ROLE_SPECS
INFEASIBLE: dict[str, str] = {**dict(SRC.INFEASIBLE), **{sid: f"repair round 3: {why}" for sid, why in DROPPED.items()}}
STRUCTURE_FACTORIES = {**SRC.STRUCTURE_FACTORIES, **STRUCTURE_OVERRIDES}


def structure(structure_id: str) -> gr.Structure:
    """The structure (repaired factory if any) with the repaired spec's scene clause appended to its base context."""

    return r2.with_scene(STRUCTURE_FACTORIES[structure_id](), ROLE_SPECS[structure_id].scene_clause)
