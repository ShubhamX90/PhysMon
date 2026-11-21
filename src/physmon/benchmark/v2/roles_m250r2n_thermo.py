"""M250 repair round 2 (journal J15.1-061) of `roles_m250r1n_thermo`: the specs the two-judge re-review rejected (any high flag) or whose sentences
the blind naturalness rater rated artificial, repaired again; every other spec is the `roles_m250r1n_thermo` object, unchanged.

Brief: `/scratch/pabitra/physmon/repair_m250_r2/briefs/roles_m250r1n_thermo.md` (`scripts/v2/s207_m250_repair_briefs.py` from
`docs/validation/v2/llm_panel/admission_m250r1/runs/score_two_judges/`). No model output exists on any of these structures. The round-1
history of each structure is in `roles_m250r1n_thermo.CHANGES`; wording rules 1-8 of the original module apply.

`CHANGES` records, per changed structure, each finding and how it was resolved; `DROPPED` holds structures that could not be repaired.
"""

from __future__ import annotations

import dataclasses

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import rolevalue_v2 as r2
from physmon.benchmark.v2 import roles_m250r1n_thermo as SRC

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

def _fix(sid: str, pairs: dict[int, dict] | None = None, note: str = "", **fields) -> r2.RoleSpecV2:
    old = OLD[sid]
    new_pairs = tuple(dataclasses.replace(p, **(pairs or {}).get(i, {})) for i, p in enumerate(old.pairs))
    return dataclasses.replace(old, pairs=new_pairs, notes=f"{old.notes} M250 r2: {note}".strip(), **fields)


# --- S224: GPT high (common temperature after admission unstated), N0 artificial (balloon with no tube) -------------------------------
FIXED["S224"] = _fix(
    "S224",
    pairs={1: dict(d_attach="For an earlier run only, the helium compartment took in")},  # main session: rule 7, no gas left behind
    scene_clause="A helium cylinder stands on the floor beside the container, and a balloon hangs from a hook next to it, to be filled "
                 "from the cylinder. Whenever a compartment is given more gas, the two gases settle to one common temperature, "
                 "with equal pressures, before they mix. The gases do not react.",
    scene_object_rationale="A balloon on a hook is a separate store of gas outside the container; helium let into it is not in the "
                           "container, so the amounts of the two gases that mix are the stated ones.",
    note="scene clause now states that after any addition the two gases settle to one common temperature with equal pressures (one "
         "reading of the certified composition-only entropy change); the balloon is filled from a helium cylinder (no 'no tube' "
         "incoherence for D0/N0).")
CHANGES["S224"] = (
    ("gpt high / claude medium: nothing states that the compartments regain a common temperature after the helium is admitted",
     "scene clause: 'Whenever a compartment is given more gas, the two gases settle to one common temperature, with equal "
     "pressures, before they mix.'"),
    ("N0 rated artificial: helium let into 'a balloon ... with no tube to it'",
     "scene clause now has a helium cylinder beside the container from which the balloon is filled; the 'no tube' remark is removed."),
)

# --- S225: GPT high x2 (earlier wrapping: removed or not?) ----------------------------------------------------------------------------
FIXED["S225"] = _fix(
    "S225",
    pairs={1: dict(frame="A further {value} {unit} of the same insulation {relation}.",
                   r_attach="is wrapped round the layer on the pipe before the heat flow becomes steady",
                   d_attach="was wrapped round the layer on the pipe for an earlier survey only",
                   d_rationale="The further insulation was wrapped round the layer for an earlier survey only (main session: 'stripped off afterwards' would be a change applied and reversed, standard 3.2), so nothing of it is there now; in the stated survey the insulation extends out to the stated radius.")},
    scene_clause="A hot-water tank, lagged with the same insulation, stands beside the pipe, clear of the pipe and its insulation. "
                 "The thermal conductivity of the insulation does not vary with temperature.",
    note="pair-1 D/N now say the earlier wrapping was stripped off afterwards (no state left behind, one reading); R1 'is wrapped "
         "round the layer on the pipe before the heat flow becomes steady'; the hot-water tank is already lagged with the same "
         "insulation (so 'a further' thickness on it is natural).")
CHANGES["S225"] = (
    ("gpt high: T6641[D1]/T26FA[N1] do not state that the earlier wrapping was removed",
     "D1 now 'A further 1.8 cm of the same insulation was wrapped round the layer on the pipe in an earlier survey and stripped off "
     "afterwards.'; N1 likewise with 'small thickness'."),
    ("gpt high: authors' claim that the earlier wrapping leaves no state behind is false if it is retained",
     "d_rationale and the sentence now say the wrapping has been stripped off, so the claim is true."),
    ("D0/N0 slightly artificial: 'a further' implies insulation on the tank never mentioned",
     "scene clause: 'A hot-water tank, lagged with the same insulation, stands beside the pipe ...'."),
    ("D1/N1/R1 slightly artificial wording", "reworded as above."),
)

# --- S226: N0 artificial (kettle heater timed to the shields) ------------------------------------------------------------------------
FIXED["S226"] = _fix(
    "S226",
    pairs={0: dict(d_attach="the water in the bath",
                   d_rationale="Warming the water in the bath leaves the hot plate, the cold plate and the shields at their stated "
                               "temperatures and surface properties.")},
    scene_clause="A thermostatic water bath stands on the bench beside the apparatus, and no heat passes between the bath and the "
                 "plates or the shields. The plates and the shields are opaque.",
    scene_object_rationale="A water bath on the bench is a store of warm water outside the vacuum between the plates; warming its "
                           "water does not change the temperature of either plate or of a shield.",
    scene_refs=("bath",),
    note="co-present object is a thermostatic water bath that a heater plausibly warms (replaces the kettle on a hob).")
CHANGES["S226"] = (
    ("N0 rated artificial: kettle heater timed to 'before the shields settle' links unrelated things",
     "co-present object is now a thermostatic water bath on the bench; D0 '... keeps the water in the bath 70 K above its initial "
     "temperature.', N0 '... a few kelvin ...'."),
    ("D0/D1/R0/R1/N1 slightly artificial", "left as in round 1: the timing phrase is what gives the single certified reading."),
)

# --- S230: D1 artificial ('took on'), stale rationale about the mould ---------------------------------------------------------------
FIXED["S230"] = _fix(
    "S230",
    pairs={0: dict(d_rationale="Metal placed in the warming cabinet is not part of either block; the blocks keep their stated "
                               "masses and initial temperatures."),
           1: dict(frame="A further {value} {unit} of the same metal, at the same temperature, {relation}.",
                   r_attach="is fixed to the hotter block just before the blocks touch",
                   d_attach="was fixed to the hotter block for an earlier run only",
                   d_rationale="The further metal was fixed to the hotter block in an earlier run, which is over; in the stated run "
                               "the hotter block has only its stated mass.")},
    note="pair 1 reworded ('is fixed to the hotter block just before the blocks touch' / 'was fixed to the hotter block in an "
         "earlier run': a block no longer 'takes on' metal); pair-0 d_rationale now speaks of the warming cabinet.")
CHANGES["S230"] = (
    ("D1 rated artificial: 'the hotter block took on a further 1.1 kg of the same metal'",
     "D1 now 'A further 1.1 kg of the same metal, at the same temperature, was fixed to the hotter block in an earlier run.'; R1 "
     "'... is fixed to the hotter block just before the blocks touch.'"),
    ("claude medium / gpt low: d_rationale speaks of metal poured into a mould",
     "pair-0 d_rationale now speaks of metal placed in the warming cabinet."),
)

ROLE_SPECS: dict[str, r2.RoleSpecV2] = {sid: FIXED.get(sid, spec) for sid, spec in OLD.items() if sid not in DROPPED}
SPECS = ROLE_SPECS
INFEASIBLE: dict[str, str] = {**dict(SRC.INFEASIBLE), **{sid: f"repair round 2: {why}" for sid, why in DROPPED.items()}}
STRUCTURE_FACTORIES = {**SRC.STRUCTURE_FACTORIES, **STRUCTURE_OVERRIDES}


def structure(structure_id: str) -> gr.Structure:
    """The structure (repaired factory if any) with the repaired spec's scene clause appended to its base context."""

    return r2.with_scene(STRUCTURE_FACTORIES[structure_id](), ROLE_SPECS[structure_id].scene_clause)
