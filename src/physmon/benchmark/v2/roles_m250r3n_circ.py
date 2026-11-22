"""M250 repair round 3 (journal J15.1-063) of `roles_m250r2n_circ`: the specs the round-2 re-review rejected (any high flag) or whose sentences the
blind naturalness rater rated artificial, repaired again; every other spec is the `roles_m250r2n_circ` object, unchanged.

Brief: `/scratch/pabitra/physmon/repair_m250_r3/briefs/roles_m250r2n_circ.md` (`scripts/v2/s207_m250_repair_briefs.py` from
`docs/validation/v2/llm_panel/admission_m250r2/runs/score_two_judges/`). No model output exists on any of these structures. Earlier rounds'
history is in `roles_m250r2n_circ.CHANGES` and its SRC chain; wording rules 1-8 of the original module apply.

`CHANGES` records, per changed structure, each finding and how it was resolved; `DROPPED` holds structures that could not be repaired.
"""

from __future__ import annotations

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import rolevalue_v2 as r2
from physmon.benchmark.v2 import roles_m250r2n_circ as SRC

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

import dataclasses  # noqa: E402

from physmon.benchmark.v2 import rolevalue as rv  # noqa: E402,F401

rep = dataclasses.replace


def _note(sid: str, text: str) -> str:
    return f"{OLD[sid].notes} M250 r3: {text}"


# --- S268 -----------------------------------------------------------------------------------------------------------------------------
FIXED["S268"] = rep(
    OLD["S268"],
    scene_clause="A torch on the bench is being tested with a small cell of its own.",
    scene_refs=("torch",),
    scene_object_rationale="A torch tested with a small cell is a circuit of its own; an emf put in series with that cell changes the "
                           "torch circuit only, so the battery of the solenoid circuit and the energy released keep their stated values.",
    pairs=(rep(OLD["S268"].pairs[0], d_attach="the cell of the torch",
               d_rationale="An emf inserted in series with the cell of the torch changes the torch circuit only; the battery of the "
                           "solenoid circuit keeps its stated emf, so the current of the solenoid and the heat released are the "
                           "stated ones."), OLD["S268"].pairs[1]),
    notes=_note("S268", "scene object is a torch tested with its own cell (was a wall doorbell), so D0 wires a battery to a cell that is "
                        "being tested anyway."))
CHANGES["S268"] = (
    ("rating D0 artificial: 'in series with the cell of the doorbell' (pointless action)",
     "scene 'A torch on the bench is being tested with a small cell of its own.'; D0 '... in series with the cell of the torch, in the "
     "same direction.'"),
)

# --- S270 -----------------------------------------------------------------------------------------------------------------------------
_p0, _p1 = OLD["S270"].pairs
FIXED["S270"] = rep(
    OLD["S270"],
    scene_clause="A toolbox stands on the trolley beside the recorder when the trolley sets off.",
    scene_object_rationale="A toolbox standing on the trolley is a load of its own; a technician who picks it up and carries it along "
                           "the trolley moves the toolbox only, so the recorder, the siren note and the reflected sound keep their "
                           "stated values.",
    pairs=(rep(_p0, frame="From the moment the trolley sets off, a technician riding on it walks steadily along its deck directly "
                          "away from the lorry at {value} {unit}, carrying {relation}.", nonnumeric_fill="a walking pace"),
           rep(_p1, frame="The recorder was carried along the trolley by a technician walking steadily directly away from the lorry "
                          "at {value} {unit} {relation}.", nonnumeric_fill="a walking pace")),
    notes=_note("S270", "scene says the toolbox is on the trolley when it sets off (D0 then carries it, no contradiction); "
                        "N fill 'a walking pace' (no 'steady ... steady'); R0/D0 'a technician riding on it walks ... along its deck'; "
                        "stale belt wording in the scene rationale replaced."))
CHANGES["S270"] = (
    ("gpt high contradictory_distractor_statement: toolbox carried vs 'stands on the trolley beside the recorder'",
     "scene 'A toolbox stands on the trolley beside the recorder when the trolley sets off.'; D0 then carries it from that moment"),
    ("rating N1/N0 redundant 'steadily ... at a steady pace'", "N fill 'at a walking pace'"),
    ("rating R0 artificial / D1 artificial / D0 slightly_artificial: technician walking along a trolley",
     "R0/D0 'a technician riding on it walks steadily along its deck directly away from the lorry at 1.6 m/s'"),
    ("claude low: scene note mentions a belt", "scene_object_rationale rewritten without the belt"),
)

# --- S271 -----------------------------------------------------------------------------------------------------------------------------
_p0, _p1 = OLD["S271"].pairs
FIXED["S271"] = rep(
    OLD["S271"],
    scene_clause="A bar of the same metal lies on a rack beside the bench.",
    scene_refs=("bar",),
    scene_object_rationale="A bar on a rack is a body of its own; lengthening it changes that bar only, so the clamped rod, the "
                           "tube and the dust heaps keep their stated values.",
    pairs=(rep(_p0, d_attach="the bar",
               d_rationale="Metal joined onto the bar lengthens the bar only; the rod in the tube keeps its stated length, "
                           "so its frequency and the dust spacing are the stated ones."), _p1),
    notes=_note("S271", "hanging wire (and the false 'railing' rationale) replaced by a bar on a rack; D0 lengthens the bar."))
CHANGES["S271"] = (
    ("claude/gpt high other: d_rationale speaks of a railing; the item has a wire",
     "d_rationale now 'Metal joined onto the bar lengthens the bar only ...'; scene object is a bar"),
    ("rating D0/N0 artificial: lengthening an unrelated hanging wire",
     "D0 'Before the clamp is fitted, the bar is lengthened by joining on an extra 32 cm of the same metal and cross-section.'"),
)

# --- S272 -----------------------------------------------------------------------------------------------------------------------------
_p0, _p1 = OLD["S272"].pairs
FIXED["S272"] = rep(
    OLD["S272"],
    scene_clause="A neighbouring tube of the same kind, part full of water, stands beside it.",
    scene_refs=("neighbouring tube",),
    scene_object_rationale="A neighbouring tube of water is a body of its own; drawing its level down changes that tube only, so the water "
                           "level in the stated tube and the time between resonances keep their stated values.",
    pairs=(rep(_p0, d_attach="the water level in the neighbouring tube",
               d_rationale="A second tap that lowers the level in the neighbouring tube acts on the neighbouring tube only; the water in the stated "
                           "tube keeps its stated fall speed, so the time between resonances is the stated one."), _p1),
    notes=_note("S272", "garden pond replaced by a neighbouring tube standing beside the tube; D0 draws down the neighbouring tube."))
CHANGES["S272"] = (
    ("rating D0 artificial / N0 slightly_artificial: tap on a garden pond timed to a resonance",
     "D0 '... a second tap is opened that alone draws down the water level in the neighbouring tube at 0.9 cm/s.'"),
)

ROLE_SPECS: dict[str, r2.RoleSpecV2] = {sid: FIXED.get(sid, spec) for sid, spec in OLD.items() if sid not in DROPPED}
SPECS = ROLE_SPECS
INFEASIBLE: dict[str, str] = {**dict(SRC.INFEASIBLE), **{sid: f"repair round 3: {why}" for sid, why in DROPPED.items()}}
STRUCTURE_FACTORIES = {**SRC.STRUCTURE_FACTORIES, **STRUCTURE_OVERRIDES}


def structure(structure_id: str) -> gr.Structure:
    """The structure (repaired factory if any) with the repaired spec's scene clause appended to its base context."""

    return r2.with_scene(STRUCTURE_FACTORIES[structure_id](), ROLE_SPECS[structure_id].scene_clause)
