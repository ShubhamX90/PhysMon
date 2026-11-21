"""M250 repair round 2 (journal J15.1-061) of `roles_m250r1_a`: the specs the two-judge re-review rejected (any high flag) or whose sentences
the blind naturalness rater rated artificial, repaired again; every other spec is the `roles_m250r1_a` object, unchanged.

Brief: `/scratch/pabitra/physmon/repair_m250_r2/briefs/roles_m250r1_a.md` (`scripts/v2/s207_m250_repair_briefs.py` from
`docs/validation/v2/llm_panel/admission_m250r1/runs/score_two_judges/`). No model output exists on any of these structures. The round-1
history of each structure is in `roles_m250r1_a.CHANGES`; wording rules 1-8 of the original module apply.

`CHANGES` records, per changed structure, each finding and how it was resolved; `DROPPED` holds structures that could not be repaired.
"""

from __future__ import annotations

import dataclasses

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import rolevalue_v2 as r2
from physmon.benchmark.v2 import roles_m250r1_a as SRC

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


# --- S04 --------------------------------------------------------------------------------------------------------------------------
NO_K["S04"] = ("Beyond its elastic limit the spring's force law is not given, so the maximum speed has no certified answer without an "
               "added model of permanent deformation; the formula q*sqrt(k/m) would rest on an unstated elastic-perfectly-plastic spring.")
FIXED["S04"] = dataclasses.replace(OLD["S04"], conditional=None,
                                   notes=_note("S04", "K (elastic limit) removed, see NO_K; R, D and C unchanged."))
CHANGES["S04"] = (
    ("gpt high: other (K outside-regime reference q*sqrt(k/m) is not generally valid)", "conditional=None; reason in NO_K['S04']"),
)

# --- S06 --------------------------------------------------------------------------------------------------------------------------
FIXED["S06"] = dataclasses.replace(
    OLD["S06"],
    pairs=(OLD["S06"].pairs[0], _pair("S06", 1, r_attach="and left there while the current was measured")),
    notes=_note("S06", "R1 now says the extra resistor is left in the circuit while the current is measured (one reading)."))
CHANGES["S06"] = (
    ("gpt high: insufficient_boundary_condition (R1 does not establish that the resistor is still connected during the measurement)",
     "R1 'A 3.5 \u03a9 resistor was connected in series with the battery before the current was measured.' -> '... in series with the "
     "battery and left there while the current was measured.'"),
)

# --- S09 --------------------------------------------------------------------------------------------------------------------------
FIXED["S09"] = dataclasses.replace(
    OLD["S09"],
    pairs=(
        OLD["S09"].pairs[0],
        _pair("S09", 1, frame="An extra {value} {unit} of water, at the same temperature as the water already in the first container, "
                              "was poured in {relation}.",
              r_attach="before the block was added", d_attach="for an earlier experiment only",
              d_rationale="The water was poured into the first container in an earlier experiment, which is over and leaves nothing "
                          "in it; in the stated experiment the container holds only its stated water."),
    ),
    notes=_note("S09", "pair-1 frame reworded ('An extra ... of water, at the same temperature as the water already in the first "
                       "container, was poured in ...'); the certified base value 8.24897 K is the correct result of the stated relations "
                       "(15400 / 1866.9) and is unchanged."))
CHANGES["S09"] = (
    ("gpt high: failed_transformation_identity (claims the stated relations give 8.24977 K)",
     "no change possible: 0.5*385*80 / (0.5*385 + 0.4*4186) = 15400/1866.9 = 8.24897 K, so the judge's 8.24977 is an arithmetic "
     "slip; the gold stays"),
    ("rated artificial N1 'The first container was given a further small amount of water ... for an earlier experiment only.'",
     "'An extra small amount of water, at the same temperature as the water already in the first container, was poured in during an "
     "earlier experiment.' (R1/D1 reworded alike)"),
    ("rated slightly_artificial R1 ('was given a further 0.55 kg' awkward after 0.4 kg)", "'An extra 0.55 kg of water ... was poured in "
     "before the block was added.'"),
)

# --- S11 --------------------------------------------------------------------------------------------------------------------------
FIXED["S11"] = dataclasses.replace(
    OLD["S11"],
    scene_clause="A bus drives along the same road. The car travels in a straight line, air resistance is negligible, and the "
                 "distance is measured from where braking begins. The speed given is the car's steady cruising speed.",
    notes=_note("S11", "the scene clause says the stated speed is the car's steady cruising speed, so a speed gain before braking "
                       "(R) adds to it: braking starts from v0 + q (one reading)."))
CHANGES["S11"] = (
    ("gpt high: insufficient_boundary_condition (is the stated 20 m/s before or after the added speed gain?)",
     "scene clause adds 'The speed given is the car's steady cruising speed.'"),
    ("gpt high: other (v0 defined as the braking-onset speed but R treats it as the speed before the gain)",
     "the stated speed is now explicitly the cruising speed before any gain; the structure's own assumption text ('starts braking at "
     "the stated speed') is frozen and still reads as the base case only"),
)

# --- S12 --------------------------------------------------------------------------------------------------------------------------
FIXED["S12"] = dataclasses.replace(
    OLD["S12"],
    scene_clause="A cyclist rides along a path beside the road. The road surface is flat with the same friction everywhere. The "
                 "radius given is that of the inner edge of the road, along which the car drives unless it keeps to a lane further out.",
    notes=_note("S12", "the scene clause says the car drives along the inner edge (the stated radius) unless it keeps to a lane "
                       "further out, so the car's path radius is stated for the base, D and C cells."))
CHANGES["S12"] = (
    ("gpt high: insufficient_boundary_condition (car's path radius unspecified when the 50 m is the inner edge)",
     "scene clause: '... the radius given is that of the inner edge of the road, along which the car drives unless it keeps to a "
     "lane further out.'"),
    ("claude low: base does not say the car follows the inner edge", "same clause"),
)

# --- S19 --------------------------------------------------------------------------------------------------------------------------
FIXED["S19"] = dataclasses.replace(
    OLD["S19"],
    scene_clause="A ramp stands on the field beside the launch point. The angle given is the launcher's initial setting, to which it "
                 "returns after every trial. The ball lands on the level ground.",
    notes=_note("S19", "the scene clause says the stated angle is the launcher's initial setting (restored after every trial), so a "
                       "lowering before the launch (R) gives theta - q and an earlier trial's lowering (D1) leaves no state."))
CHANGES["S19"] = (
    ("gpt high: insufficient_boundary_condition (is 35 degrees before or after the lowering?); claude medium; rated slightly_artificial R1",
     "scene clause adds 'The angle given is the launcher's initial setting, to which it returns after every trial.'; R/D sentences "
     "unchanged"),
)

# --- S21 --------------------------------------------------------------------------------------------------------------------------
FIXED["S21"] = dataclasses.replace(
    OLD["S21"],
    pairs=(
        _pair("S21", 0, frame="The {relation} is tuned up by {value} {unit} soon after the tone begins."),
        _pair("S21", 1, r_attach="after switch-on and before the measurement"),
    ),
    notes=_note("S21", "R0/D0 are timed 'soon after the tone begins'; R1 'after switch-on and before the measurement', so the "
                       "stated tone is the pre-tuning tone (one reading)."))
CHANGES["S21"] = (
    ("gpt high: insufficient_boundary_condition (R1 tuning before or after the switch-on that defines 440 Hz?); claude medium",
     "R1 'The siren was tuned up by 16 Hz just before the tone was measured.' -> '... after switch-on and before the measurement.'; "
     "R0 'The siren is then tuned up by 16 Hz.' -> 'The siren is tuned up by 16 Hz soon after the tone begins.'"),
    ("gpt high: rendering_not_minimal on N0/N1 (5.3b judge error, not counted)", "N sentences stay numeral-free by design"),
)

# Main-session review (J15.1-061): the authors' A-start assumption of S11 ("The car starts braking at the stated speed ...") contradicts
# the R sentence (the car speeds up before braking); only the assumption text changes (base text and gold unchanged).
def _s11_structure() -> gr.Structure:
    base = SRC.STRUCTURE_FACTORIES["S11"]()
    fixed = tuple(dataclasses.replace(a, text="The car brakes from the speed it has when braking begins and decelerates until it stops.")
                  if a.assumption_id == "A-start" else a for a in base.assumptions)
    return dataclasses.replace(base, assumptions=fixed)


STRUCTURE_OVERRIDES["S11"] = _s11_structure
CHANGES["S11"] = (*CHANGES.get("S11", ()), ("main-session review: authors' A-start assumption contradicted R",
                  "assumption text 'The car starts braking at the stated speed and decelerates until it stops.' -> 'The car brakes from "
                  "the speed it has when braking begins and decelerates until it stops.' (STRUCTURE_OVERRIDES)"))

ROLE_SPECS: dict[str, r2.RoleSpecV2] = {sid: FIXED.get(sid, spec) for sid, spec in OLD.items() if sid not in DROPPED}
SPECS = ROLE_SPECS
INFEASIBLE: dict[str, str] = {**dict(SRC.INFEASIBLE), **{sid: f"repair round 2: {why}" for sid, why in DROPPED.items()}}
STRUCTURE_FACTORIES = {**SRC.STRUCTURE_FACTORIES, **STRUCTURE_OVERRIDES}


def structure(structure_id: str) -> gr.Structure:
    """The structure (repaired factory if any) with the repaired spec's scene clause appended to its base context."""

    return r2.with_scene(STRUCTURE_FACTORIES[structure_id](), ROLE_SPECS[structure_id].scene_clause)
