"""M250 repair round 3 (journal J15.1-063) of `roles_m250r2n_waves`: the specs the round-2 re-review rejected (any high flag) or whose sentences the
blind naturalness rater rated artificial, repaired again; every other spec is the `roles_m250r2n_waves` object, unchanged.

Brief: `/scratch/pabitra/physmon/repair_m250_r3/briefs/roles_m250r2n_waves.md` (`scripts/v2/s207_m250_repair_briefs.py` from
`docs/validation/v2/llm_panel/admission_m250r2/runs/score_two_judges/`). No model output exists on any of these structures. Earlier rounds'
history is in `roles_m250r2n_waves.CHANGES` and its SRC chain; wording rules 1-8 of the original module apply.

`CHANGES` records, per changed structure, each finding and how it was resolved; `DROPPED` holds structures that could not be repaired.
"""

from __future__ import annotations

import dataclasses

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import rolevalue_v2 as r2
from physmon.benchmark.v2 import roles_m250r2n_waves as SRC

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

def _note(sid: str, text: str) -> str:
    return f"{OLD[sid].notes} M250 r3: {text}".strip()


def _pair(sid: str, i: int, **kw):
    return dataclasses.replace(OLD[sid].pairs[i], **kw)


# --- S232: the earlier run must leave no detergent in the tank -------------------------------------------------------------------------
FIXED["S232"] = dataclasses.replace(
    OLD["S232"],
    scene_clause="A washing-up bowl of water stands on the bench beside the tank, and no tube or channel joins them. The tank is "
                 "emptied, rinsed and refilled with clean water after every run. The surface tension given is that of the clean "
                 "water in the tank, before any detergent is added to it.",
    notes=_note("S232", "scene clause: the tank is emptied, rinsed and refilled with clean water after every run, so detergent of an "
                        "earlier run leaves no state behind."))
CHANGES["S232"] = (
    ("claude/gpt high hidden_coupling + insufficient_boundary_condition: detergent of an earlier run may remain in the tank water",
     "Scene clause adds 'The tank is emptied, rinsed and refilled with clean water after every run.' (old: nothing about the tank "
     "between runs); D1/N1 wording unchanged ('In an earlier run, detergent reduced ...')."),
    ("rated slightly_artificial N1 (sits awkwardly after the clean-water statement)",
     "The refill sentence now explains why an earlier run's detergent is gone; N1 wording unchanged."),
)

# --- S233: purposeful D object, plain timing --------------------------------------------------------------------------------------------
_S233_P0 = _pair("S233", 0, frame="Before the experiment starts, an optical amplifier adds {value} {unit} to the power of {relation}.")
FIXED["S233"] = dataclasses.replace(
    OLD["S233"], pairs=(_S233_P0, OLD["S233"].pairs[1]),
    scene_clause="The beam leaves a laser fixed to the bench, and the power given for it is the power at the laser. A second laser "
                 "stands on the bench beside the block, turned away from it, and is being made ready for another experiment. The "
                 "beam is narrow and parallel.",
    notes=_note("S233", "pair 0: 'Before the experiment starts, an optical amplifier adds ...' replaces 'Before any light reaches the "
                        "block'; the second laser is being made ready for another experiment."))
CHANGES["S233"] = (
    ("rated artificial N0 'Before any light reaches the block, an optical amplifier adds a small amount to the power of the second "
     "laser' (pointless action, odd timing)",
     "N0 'Before the experiment starts, an optical amplifier adds a small amount to the power of the second laser.'; scene clause: the "
     "second laser 'is being made ready for another experiment' (old: 'for use in another experiment')."),
    ("rated slightly_artificial D0/R0 (same timing phrase)", "Same frame: 'Before the experiment starts, an optical amplifier adds 3.4 mW to ...'."),
)

# --- S234: D object is a second rod, not a coil of cable ----------------------------------------------------------------------------------
_S234_P0 = _pair("S234", 0, d_attach="glass tube",
                 d_rationale="A piece joined onto the glass tube lengthens the tube only; the length of the rod that carries the pulse "
                             "is the stated one.")
FIXED["S234"] = dataclasses.replace(
    OLD["S234"], pairs=(_S234_P0, OLD["S234"].pairs[1]), scene_refs=("glass tube",),
    scene_clause="A glass tube made of the same glass lies on the bench beside the rod, and no light passes between them. The glass is "
                 "not dispersive. The length given for the rod is its length as first cut.",
    notes=_note("S234", "D0/N0 lengthen a glass tube of the same glass (co-present object) instead of a coil of optical cable; main session: a tube, not a second rod, so that 'the rod' has one referent (rule 4)."))
CHANGES["S234"] = (
    ("rated artificial D0/N0 'The optical cable is lengthened by 1.3 m of the same glass, joined on in line with it, before the pulse "
     "is sent' (implausible: splicing bulk glass onto a cable coil)",
     "Scene clause now has 'A glass tube made of the same glass lies on the bench beside the rod'; D0 'The glass tube is lengthened by 1.3 m "
     "of the same glass, joined on in line with it, before the pulse is sent.'"),
)

# --- S238: final rate stated for the base problem; omega relation ---------------------------------------------------------------------
def _s238_base() -> gr.Structure:
    s = SRC.STRUCTURE_FACTORIES["S238"]()
    asm = tuple(
        dataclasses.replace(a, text="In the relation omega = rot, rot stands for the rotation rate converted from revolutions per "
                                    "minute to radians per second, that is omega = 2 pi x (rate in rpm) / 60.")
        if a.assumption_id == "A-rpm" else a for a in s.assumptions)
    return dataclasses.replace(s, assumptions=asm)


STRUCTURE_OVERRIDES["S238"] = _s238_base
FIXED["S238"] = dataclasses.replace(
    OLD["S238"],
    scene_clause="A magnetic stirrer on the bench beside the cylinder mixes a beaker of water for another experiment. The oil is "
                 "Newtonian and moves only in circles about the axis; it stays at one temperature, and its viscosity stays constant. "
                 "The rate given for the rotor is the rate at which it first runs, and its final rate is that same rate unless a "
                 "change of its speed setting is stated.",
    notes=_note("S238", "scene clause states the final rate (the first rate unless a change is stated); A-rpm assumption text states "
                        "that omega = rot means the rpm value converted to rad/s."))
CHANGES["S238"] = (
    ("gpt high insufficient_boundary_condition: the final rate is not specified for the base problem and the D/C additions",
     "Scene clause: 'its final rate is that same rate unless a change of its speed setting is stated' (old: only 'The rate given for "
     "the rotor is the rate at which it first runs')."),
    ("gpt high inconsistent_units: displayed relation omega = rot omits 2 pi / 60",
     "A-rpm assumption now 'In the relation omega = rot, rot stands for the rotation rate converted from revolutions per minute to "
     "radians per second, that is omega = 2 pi x (rate in rpm) / 60.' (base text and gold unchanged)."),
)

ROLE_SPECS: dict[str, r2.RoleSpecV2] = {sid: FIXED.get(sid, spec) for sid, spec in OLD.items() if sid not in DROPPED}
SPECS = ROLE_SPECS
INFEASIBLE: dict[str, str] = {**dict(SRC.INFEASIBLE), **{sid: f"repair round 3: {why}" for sid, why in DROPPED.items()}}
STRUCTURE_FACTORIES = {**SRC.STRUCTURE_FACTORIES, **STRUCTURE_OVERRIDES}


def structure(structure_id: str) -> gr.Structure:
    """The structure (repaired factory if any) with the repaired spec's scene clause appended to its base context."""

    return r2.with_scene(STRUCTURE_FACTORIES[structure_id](), ROLE_SPECS[structure_id].scene_clause)
