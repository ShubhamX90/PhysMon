"""M250 repair round 3 (journal J15.1-063) of `roles_m250r2_a`: the specs the round-2 re-review rejected (any high flag) or whose sentences the
blind naturalness rater rated artificial, repaired again; every other spec is the `roles_m250r2_a` object, unchanged.

Brief: `/scratch/pabitra/physmon/repair_m250_r3/briefs/roles_m250r2_a.md` (`scripts/v2/s207_m250_repair_briefs.py` from
`docs/validation/v2/llm_panel/admission_m250r2/runs/score_two_judges/`). No model output exists on any of these structures. Earlier rounds'
history is in `roles_m250r2_a.CHANGES` and its SRC chain; wording rules 1-8 of the original module apply.

`CHANGES` records, per changed structure, each finding and how it was resolved; `DROPPED` holds structures that could not be repaired.
"""

from __future__ import annotations

import dataclasses

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import rolevalue_v2 as r2
from physmon.benchmark.v2 import roles_m250r2_a as SRC

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


_S21 = OLD["S21"]
FIXED["S21"] = dataclasses.replace(
    _S21,
    scene_clause=(
        "A street musician stands nearby with a violin. The air is still, and the question concerns only the sound of the siren. "
        "The tone given is the one the siren emits when first switched on. The listener measures the frequency only after the sound "
        "emitted once any tuning was finished has arrived, while the siren is still approaching."
    ),
    notes=_S21.notes + " M250 r3: scene clause fixes that the measurement is made after the sound emitted following any tuning has "
    "reached the listener, so the received frequency is that of the tuned siren (one reading for R0 and R1).",
)
CHANGES["S21"] = (
    ("gpt high insufficient_boundary_condition: nothing ensures sound emitted after retuning has reached the listener",
     "scene clause adds 'The listener measures the frequency only after the sound emitted once any tuning was finished has arrived, "
     "while the siren is still approaching.'; R and D sentences unchanged"),
    ("claude low: R0 does not say the listening occurs after the retuning", "covered by the same scene-clause sentence"),
)

ROLE_SPECS: dict[str, r2.RoleSpecV2] = {sid: FIXED.get(sid, spec) for sid, spec in OLD.items() if sid not in DROPPED}
SPECS = ROLE_SPECS
INFEASIBLE: dict[str, str] = {**dict(SRC.INFEASIBLE), **{sid: f"repair round 3: {why}" for sid, why in DROPPED.items()}}
STRUCTURE_FACTORIES = {**SRC.STRUCTURE_FACTORIES, **STRUCTURE_OVERRIDES}


def structure(structure_id: str) -> gr.Structure:
    """The structure (repaired factory if any) with the repaired spec's scene clause appended to its base context."""

    return r2.with_scene(STRUCTURE_FACTORIES[structure_id](), ROLE_SPECS[structure_id].scene_clause)
