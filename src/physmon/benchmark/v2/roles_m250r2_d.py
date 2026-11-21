"""M250 repair round 2 (journal J15.1-061) of `roles_m250r1_d`: the specs the two-judge re-review rejected (any high flag) or whose sentences
the blind naturalness rater rated artificial, repaired again; every other spec is the `roles_m250r1_d` object, unchanged.

Brief: `/scratch/pabitra/physmon/repair_m250_r2/briefs/roles_m250r1_d.md` (`scripts/v2/s207_m250_repair_briefs.py` from
`docs/validation/v2/llm_panel/admission_m250r1/runs/score_two_judges/`). No model output exists on any of these structures. The round-1
history of each structure is in `roles_m250r1_d.CHANGES`; wording rules 1-8 of the original module apply.

`CHANGES` records, per changed structure, each finding and how it was resolved; `DROPPED` holds structures that could not be repaired.
"""

from __future__ import annotations

import dataclasses

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import rolevalue_v2 as r2
from physmon.benchmark.v2 import roles_m250r1_d as SRC

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


# ---- S77 ----
FIXED["S77"] = dataclasses.replace(
    OLD["S77"],
    pairs=(
        _pair("S77", 0, frame="Before the electron is sent in, {relation} is replaced by one of a different material, with its "
                              "height set to {value} {unit}."),
        _pair("S77", 1, frame="{relation}, the barrier was replaced by one of a different material, with its height set to "
                              "{value} {unit}.",
              r_attach="Before the electron was sent in", d_attach="For an earlier run only",
              d_rationale="The barrier was replaced only for an earlier run, which is over; the electron of the stated problem meets "
                          "the barrier of the stated height."),
    ),
    notes=_note("S77", "'rebuilt ... before the electron arrives' (rated incoherent/artificial) -> 'Before the electron is sent in, the "
                       "barrier is replaced by one of a different material, with its height set to {v}'; p1 D 'For an earlier run only, "
                       "the barrier was replaced ...' (no state left behind; 'it' replaced by 'the barrier')."))
CHANGES["S77"] = (
    ("rating D0/N0 artificial 'Before the electron arrives, the second barrier is rebuilt from a different material, ...'",
     "'Before the electron is sent in, the second barrier is replaced by one of a different material, with its height set to ...'"),
    ("rating R1 artificial (ambiguous 'it'): 'Before the electron approached the barrier, it was rebuilt ...'",
     "'Before the electron was sent in, the barrier was replaced by one of a different material, with its height set to 7.2 eV.'"),
    ("rating R0/D1/N1 slightly artificial",
     "R0 'replaced by one of a different material'; D1/N1 'For an earlier run only, the barrier was replaced ...'"),
    ("gpt medium: N sentences omit numerals", "numeral-free by design (5.3b)."),
)

# ---- S82 ----
FIXED["S82"] = dataclasses.replace(
    OLD["S82"],
    scene_clause="A third star in the same field is observed with the same spectrometer. The second and the third star brighten from "
                 "time to time in outbursts that last for days, and the temperature given for the second star is its temperature "
                 "between outbursts.",
    pairs=(
        OLD["S82"].pairs[0],
        _pair("S82", 1, frame="{relation} raised the surface temperature of the star by {value} {unit}.",
              r_attach="An outburst still going on when the spectrum of the second star was recorded",
              d_attach="An earlier outburst, over before the spectrum of the second star was recorded,",
              d_rationale="The outburst was over before the spectrum was recorded, so it leaves nothing behind; the star radiated at "
                          "its stated temperature between outbursts when its spectrum was recorded."),
    ),
    notes=_note("S82", "scene clause: outbursts last for days and the given temperature of the second star is the one between outbursts; "
                       "p1 R is an outburst still going on at the recording, D an earlier outburst already over at the recording, so "
                       "the epoch of the question (the recorded spectrum) is fixed in both."))
CHANGES["S82"] = (
    ("gpt high insufficient_boundary_condition: epoch of the question is not recording; rise before recording does not fix the "
     "temperature at recording",
     "scene clause: 'outbursts that last for days, and the temperature given for the second star is its temperature between outbursts'; "
     "R1 'An outburst still going on when the spectrum of the second star was recorded raised the surface temperature of the star by "
     "950 K.' (T = T2 + q at the recording); D1 'An earlier outburst, over before the spectrum ... was recorded, raised ...' (T = T2)."),
    ("gpt high rendering_not_minimal (N omits number)", "5.3b judge error: numeral-free by design, unchanged."),
    ("claude low: D1 present tense could mean the post-outburst temperature", "D1 outburst is over before the recording, so the star is at its between-outbursts 2900 K in the recorded spectrum."),
)


ROLE_SPECS: dict[str, r2.RoleSpecV2] = {sid: FIXED.get(sid, spec) for sid, spec in OLD.items() if sid not in DROPPED}
SPECS = ROLE_SPECS
INFEASIBLE: dict[str, str] = {**dict(SRC.INFEASIBLE), **{sid: f"repair round 2: {why}" for sid, why in DROPPED.items()}}
STRUCTURE_FACTORIES = {**SRC.STRUCTURE_FACTORIES, **STRUCTURE_OVERRIDES}


def structure(structure_id: str) -> gr.Structure:
    """The structure (repaired factory if any) with the repaired spec's scene clause appended to its base context."""

    return r2.with_scene(STRUCTURE_FACTORIES[structure_id](), ROLE_SPECS[structure_id].scene_clause)
