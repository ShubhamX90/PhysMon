"""M250 repair round 2 (journal J15.1-061) of `roles_m250r1n_modern`: the specs the two-judge re-review rejected (any high flag) or whose sentences
the blind naturalness rater rated artificial, repaired again; every other spec is the `roles_m250r1n_modern` object, unchanged.

Brief: `/scratch/pabitra/physmon/repair_m250_r2/briefs/roles_m250r1n_modern.md` (`scripts/v2/s207_m250_repair_briefs.py` from
`docs/validation/v2/llm_panel/admission_m250r1/runs/score_two_judges/`). No model output exists on any of these structures. The round-1
history of each structure is in `roles_m250r1n_modern.CHANGES`; wording rules 1-8 of the original module apply.

`CHANGES` records, per changed structure, each finding and how it was resolved; `DROPPED` holds structures that could not be repaired.
"""

from __future__ import annotations

import dataclasses

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import rolevalue_v2 as r2
from physmon.benchmark.v2 import roles_m250r1n_modern as SRC

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


# ---- S241 ----
FIXED["S241"] = dataclasses.replace(
    OLD["S241"],
    scene_clause="A wall chart beside the cell is lit by lamps of its own, and the window of the cell is shielded from them.",
    scene_object_rationale="A wall chart beside the cell is lit by lamps of its own; light that falls on the chart does not reach the "
                           "cathode, which is behind a shielded window, so the power on the cathode and the current are those of the "
                           "stated beam.",
    pairs=(
        _pair("S241", 0, frame="A further lamp puts {value} {unit} extra light of the same wavelength onto {relation}.",
              d_rationale="A further lamp that lights the wall chart does not reach the cathode, whose window is shielded from the "
                          "lamps that light the chart; the power that falls on the cathode is the stated one."),
        _pair("S241", 1, d_attach="For an earlier measurement only, a second lamp put"),
    ),
    notes=_note("S241", "D0 rationale named a meter dial; it now names the wall chart. Pair 0 frame is 'A further lamp puts {v} extra "
                        "light of the same wavelength onto ...' (plain wording, parallel to pair 1); scene clause: lamps of its own."))
CHANGES["S241"] = (
    ("gpt high other: D0/N0 rationale identifies the lit object as a meter dial, not the wall chart",
     "d_rationale rewritten: 'A further lamp that lights the wall chart does not reach the cathode, whose window is shielded from the "
     "lamps that light the chart; ...'"),
    ("rating D0/N0 artificial: 'A further lamp of the same wavelength as the light supplies 3.4 mW more light power to the wall chart.'",
     "'A further lamp puts 3.4 mW extra light of the same wavelength onto the wall chart.' (R0 'onto the cathode')"),
    ("coordinator rule: pair-1 D that adds light to the target says 'only'", "D1/N1 'For an earlier measurement only, a second lamp put ...'"),
    ("claude low: eV-to-joule factor vs stated e", "not changed: library solver out of scope; 0.011 percent."),
)

# ---- S246 ----
FIXED["S246"] = dataclasses.replace(
    OLD["S246"],
    pairs=(
        OLD["S246"].pairs[0],
        _pair("S246", 1, frame="{relation}, the builders laid {value} {unit} more concrete against the wall.",
              r_attach="In the final design of the shield", d_attach="For an earlier design of the shield only",
              d_rationale="The extra concrete belonged to an earlier design of the shield, which was replaced; the wall of the shield "
                          "of the question has the stated thickness."),
    ),
    notes=_note("S246", "pair 1: 'In the final design of the shield, the builders laid {v} more concrete against the wall.' / 'In an "
                        "earlier design of the shield, ...' ('its wall' and 'earlier shield' were ambiguous)."))
CHANGES["S246"] = (
    ("rating N1 artificial: 'For an earlier shield, the builders laid a little more concrete against its wall.'",
     "'For an earlier design of the shield only, the builders laid a little more concrete against the wall.'"),
    ("ratings D1/R1 slightly artificial ('its wall' ambiguous)", "'In the final design of the shield, ... against the wall.' / 'For an earlier design of the shield only, ...'"),
)


ROLE_SPECS: dict[str, r2.RoleSpecV2] = {sid: FIXED.get(sid, spec) for sid, spec in OLD.items() if sid not in DROPPED}
SPECS = ROLE_SPECS
INFEASIBLE: dict[str, str] = {**dict(SRC.INFEASIBLE), **{sid: f"repair round 2: {why}" for sid, why in DROPPED.items()}}
STRUCTURE_FACTORIES = {**SRC.STRUCTURE_FACTORIES, **STRUCTURE_OVERRIDES}


def structure(structure_id: str) -> gr.Structure:
    """The structure (repaired factory if any) with the repaired spec's scene clause appended to its base context."""

    return r2.with_scene(STRUCTURE_FACTORIES[structure_id](), ROLE_SPECS[structure_id].scene_clause)
