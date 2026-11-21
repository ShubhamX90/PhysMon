"""M250 repair round 1 (journal J15.1-059) of `roles_m250_a`: the specs the two-judge panel rejected (any high flag) or whose sentences the
blind naturalness rater rated artificial, repaired; every other spec is the `roles_m250_a` object, unchanged.

Brief: `/scratch/pabitra/physmon/repair_m250_r1/briefs/roles_m250_a.md` (built by `scripts/v2/s207_m250_repair_briefs.py` from
`docs/validation/v2/llm_panel/admission_m250/runs/score_two_judges/`). No model output exists on any of these structures, so they may
still be edited (dataset admission standard, preamble). Wording rules 1-8 of `roles_m250_a` apply to every changed sentence.

`CHANGES` records, per changed structure, each finding and how it was resolved; `DROPPED` holds structures that could not be repaired
(they move to `INFEASIBLE` with the reason and are replaced in a later batch).
"""

from __future__ import annotations

import dataclasses

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import rolevalue_v2 as r2
from physmon.benchmark.v2 import roles_m250_a as SRC

OLD: dict[str, r2.RoleSpecV2] = dict(getattr(SRC, "ROLE_SPECS", None) or SRC.SPECS)
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
    return f"{OLD[sid].notes} M250 r1: {text}".strip()


def _pair(sid: str, i: int, **kw):
    return dataclasses.replace(OLD[sid].pairs[i], **kw)


# --- S03 --------------------------------------------------------------------------------------------------------------------------
FIXED["S03"] = dataclasses.replace(
    OLD["S03"],
    pairs=(
        _pair("S03", 0, frame="Before the run, a {value} {unit} block is fixed onto {relation}."),
        _pair("S03", 1, frame="A {value} {unit} block was fixed onto the first cart {relation}.",
              r_attach="before it was set moving", d_attach="for an earlier run only"),
    ),
    scene_clause="A third cart waits at rest on a parallel track. The masses given are those of the bare carts and the speeds are "
                 "those just before they meet.",
    notes=_note("S03", "the scene clause states that the masses are those of the bare carts and the speeds those just before the "
                       "carts meet, and R1 fixes the block before the first cart is set moving, so the loaded cart is the one that "
                       "moves at the stated speed (one reading); R0/D0 read 'Before the run, ...'."))
CHANGES["S03"] = (
    ("claude high: insufficient_boundary_condition (R1 'just before the collision' does not say the loaded first cart still moves at "
     "the stated speed)",
     "scene clause now says the speeds are those just before the carts meet and the masses are those of the bare carts; R1 'A 1.3 kg "
     "block was fixed onto the first cart just before the collision.' -> 'A 1.3 kg block was fixed onto the first cart before it was "
     "set moving.' (block loaded first, so the stated speed is the loaded cart's speed)"),
    ("gpt high: rendering_not_minimal on N0/N1 (5.3b judge error, not counted)", "N sentences stay numeral-free by design"),
    ("rated slightly_artificial R0 'A 1.3 kg block is fixed onto the first cart before the collision.' (muddles stated mass)",
     "R0/D0 'Before the run, a 1.3 kg block is fixed onto the first cart / the third cart.'; the scene clause makes the stated mass "
     "the bare cart's"),
    ("rated slightly_artificial D1/N1 'for an earlier run only'", "kept the attachment (rule 7); frame now ties the R twin to 'before "
     "it was set moving'"),
)

# --- S04 --------------------------------------------------------------------------------------------------------------------------
FIXED["S04"] = dataclasses.replace(
    OLD["S04"],
    scene_clause="A trolley stands on the floor beside the table. The other end of the spring is fixed to a wall. The spring has "
                 "negligible mass, air resistance is negligible, and the mass given is that of the block alone.",
    notes=_note("S04", "the scene clause now fixes the spring's other end to a wall (so only the block moves) and states that the "
                       "block's mass is its own, so a weight stuck on it adds to it."))
CHANGES["S04"] = (
    ("gpt high: insufficient_boundary_condition (the spring's opposite end is not fixed)",
     "scene clause adds 'The other end of the spring is fixed to a wall.'"),
    ("rated slightly_artificial R1 'A 0.8 kg weight was stuck on top of the block before it was released.' (sits awkwardly with "
     "the stated mass)", "scene clause adds 'the mass given is that of the block alone'; sentence unchanged"),
)

# --- S05 --------------------------------------------------------------------------------------------------------------------------
NO_K["S05"] = ("The regime 'static friction below the driving torque' is not the operative condition: the disc is stated to be "
               "rotating, so the kinetic friction torque governs whatever the static friction torque is, and no out-of-regime law "
               "for this question is certified.")
FIXED["S05"] = dataclasses.replace(
    OLD["S05"],
    pairs=(
        _pair("S05", 0, d_rationale=OLD["S05"].pairs[0].d_rationale,
              frame="Before the torques are applied, a {value} {unit} disc of the same radius is bolted coaxially onto {relation}.",
              r_attach="the disc"),
        _pair("S05", 1, frame="A {value} {unit} disc of the same radius was bolted coaxially onto the disc {relation}."),
    ),
    conditional=None,
    scene_clause="A flywheel is mounted on a second shaft beside the disc. Any disc added is uniform and solid, and the mass given "
                 "is that of the disc alone.",
    notes=_note("S05", "the scene clause states that any added disc is uniform and solid and that the stated mass is the disc's own; "
                       "R sentences say 'the disc' (not 'this disc', which the flywheel sentence made ambiguous); the K quantity "
                       "(static friction torque) is removed (NO_K)."))
CHANGES["S05"] = (
    ("gpt high: missing_assumption (the added disc's mass distribution is not stated)",
     "scene clause adds 'Any disc added is uniform and solid'"),
    ("gpt high: other (static-friction K claims wrong: the disc is already rotating)",
     "conditional=None; reason recorded in NO_K['S05']"),
    ("rated slightly_artificial R1 ('this disc' ambiguous after the flywheel sentence)",
     "'onto this disc' -> 'onto the disc' in R0 and R1 (and the D1/N1 twins)"),
)

# --- S06 --------------------------------------------------------------------------------------------------------------------------
NO_K["S06"] = ("A power rating gives no failure mechanism (burn-out, drift or survival), so no certified out-of-regime answer for the "
               "current exists; the open-circuit case would be an unstated assumption.")
FIXED["S06"] = dataclasses.replace(
    OLD["S06"],
    pairs=(OLD["S06"].pairs[0], _pair("S06", 1, r_attach="before the current was measured")),
    conditional=None,
    notes=_note("S06", "K (power rating) removed, see NO_K; R1 now ties the series resistor to the measurement of the current."))
CHANGES["S06"] = (
    ("gpt high: other (K outside-regime reference 0 A does not follow from exceeding a power rating)",
     "conditional=None; reason in NO_K['S06']"),
    ("rated slightly_artificial R1 'A 3.5 Ω resistor was connected in series with the battery in this circuit.'",
     "attachment 'in this circuit' -> 'before the current was measured'"),
)

# --- S08 --------------------------------------------------------------------------------------------------------------------------
NO_K["S08"] = ("A voltage rating gives no failure model (short, open or survive), so the outside-regime energy C2 V^2/2 would rest on "
               "an unstated shorted-capacitor assumption and no certified out-of-regime answer exists.")
FIXED["S08"] = dataclasses.replace(
    OLD["S08"],
    conditional=None,
    scene_clause="A small lamp, wired to its own cell, stands beside the circuit. The capacitors start uncharged, the connecting "
                 "wires have negligible resistance. The energy asked about is the total stored in every capacitor connected "
                 "across the battery.",
    notes=_note("S08", "the scene clause states that the energy asked for is the total in every capacitor across the battery (so an "
                       "added parallel capacitor counts, one reading); K removed, see NO_K."))
CHANGES["S08"] = (
    ("claude and gpt high: R certified answers include the added capacitor but the question says 'the two capacitors together'",
     "scene clause adds 'The energy asked about is the total stored in every capacitor connected across the battery.' (base text "
     "frozen; base answer unchanged); the R capacitor is across the battery, the D0 capacitor is on the lamp's own cell"),
    ("gpt high: missing_assumption (K outside-regime energy assumes a shorted capacitor)",
     "conditional=None; reason in NO_K['S08']"),
)

# --- S09 --------------------------------------------------------------------------------------------------------------------------
FIXED["S09"] = dataclasses.replace(
    OLD["S09"],
    pairs=(
        _pair("S09", 0, frame="Before the block is added, {relation} receives a further {value} {unit} of water at the same "
                              "temperature as the water it already holds.",
              r_attach="the first container", d_attach="the second container"),
        _pair("S09", 1, frame="The first container was given a further {value} {unit} of water at the same temperature as its "
                              "own water {relation}.",
              r_attach="before the block was added", d_attach="for an earlier experiment only"),
    ),
    scene_clause="A second insulated container with some water stands beside it. The first container absorbs no heat itself, its "
                 "contents are stirred to one temperature, and no water boils or evaporates. Nothing from any other experiment is "
                 "left in the first container.",
    target_terms=("this container", "the container", "the first container"),
    notes=_note("S09", "the scene clause states that nothing from any other experiment is left in the first container (so the D1 "
                       "water leaves no state); R0/R1 are tied to the moment before the block is added and name the first container "
                       "(not 'this container'); the D twin gives the second container water at its own temperature."))
CHANGES["S09"] = (
    ("gpt high: insufficient_boundary_condition (water of the earlier experiment: removed or included?)",
     "scene clause adds 'Nothing from any other experiment is left in the first container.'"),
    ("claude low: R0 does not say whether the water is added before or after the exchange",
     "R0 'A further 0.55 kg of water ... is poured into this container.' -> 'Before the block is added, the first container "
     "receives a further 0.55 kg of water at the same temperature as the water it already holds.'"),
    ("rated artificial N0 'A further small amount of water at the same temperature is poured into the second container.'",
     "'Before the block is added, the second container receives a further small amount of water at the same temperature as the "
     "water it already holds.' (referent of 'same temperature' now explicit, container has water)"),
    ("rated slightly_artificial D1/N1/R0 ('this container', 'same temperature' ambiguous)",
     "'The first container was given a further 0.55 kg of water at the same temperature as its own water for an earlier experiment "
     "only.'"),
)

# --- S10 --------------------------------------------------------------------------------------------------------------------------
FIXED["S10"] = dataclasses.replace(
    OLD["S10"],
    pairs=(
        _pair("S10", 0, frame="Before the ball is launched, a {value} {unit} stand is fitted under the {relation}.",
              d_attach="loudspeaker",
              d_rationale="A stand fitted under a loudspeaker on a table beside the platform does not raise the platform, so the "
                          "launch height is the stated platform height."),
        _pair("S10", 1, frame="A {value} {unit} stand was fitted under the platform {relation}."),
    ),
    scene_clause="A loudspeaker stands on a table beside the platform. The ball is launched from the top of the platform, and the "
                 "height given is that of the platform alone.",
    scene_refs=("loudspeaker",),
    scene_object_rationale="A loudspeaker on a table beside the platform is not under the platform and does not touch the ball, so "
                           "the launch point and the trajectory are unchanged.",
    notes=_note("S10", "'a further 2.2 m stand is placed under the table' (a pointless action on furniture) replaced by a stand "
                       "fitted under a loudspeaker; 'further' dropped; the scene clause states the platform height is the platform "
                       "alone."))
CHANGES["S10"] = (
    ("rated artificial D0 'Before the ball is launched, a further 2.2 m stand is placed under the table.' / N0",
     "'Before the ball is launched, a 2.2 m stand is fitted under the loudspeaker.' (loudspeaker introduced by the scene clause)"),
    ("rated artificial N1 'A further small stand was placed under the platform for an earlier experiment only.'",
     "'A small stand was fitted under the platform for an earlier experiment only.' ('further' dropped)"),
    ("rated slightly_artificial R0/R1/D1 ('further 2.2 m stand')", "'further' dropped in all of them"),
)

# --- S11 --------------------------------------------------------------------------------------------------------------------------
FIXED["S11"] = dataclasses.replace(
    OLD["S11"],
    pairs=(
        _pair("S11", 0, frame="Before braking starts, the {relation} speeds up by {value} {unit}.",
              nonnumeric_fill="a small amount"),
        _pair("S11", 1, frame="{relation}, the car sped up by {value} {unit}.", r_attach="Before it started braking",
              d_attach="On an earlier run", nonnumeric_fill="a small amount"),
    ),
    notes=_note("S11", "'gains a further 4.5 m/s' (no referent for 'further') replaced by 'speeds up by 4.5 m/s'; D0 is tied to the "
                       "car's braking, D1 'On an earlier run, the car sped up by 4.5 m/s.'"))
CHANGES["S11"] = (
    ("rated artificial D1 'The car gained a further 4.5 m/s on an earlier run.'",
     "'On an earlier run, the car sped up by 4.5 m/s.'"),
    ("rated artificial N0/N1 ('gains a further small amount')",
     "N0 'Before braking starts, the bus speeds up by a small amount.' N1 'On an earlier run, the car sped up by a small "
     "amount.'"),
    ("rated slightly_artificial D0/R0/R1; claude low: wording slightly awkward", "'gains a further' -> 'speeds up by' in all sentences"),
    ("gpt medium: rendering_not_minimal (numeral-free controls)", "intentional N design, unchanged"),
)

# --- S12 --------------------------------------------------------------------------------------------------------------------------
FIXED["S12"] = dataclasses.replace(
    OLD["S12"],
    pairs=(
        _pair("S12", 0, frame="The {relation} keeps to a lane {value} {unit} further from the centre of the curve.",
              nonnumeric_fill="a little"),
        _pair("S12", 1, frame="{relation}, the car kept to a lane {value} {unit} further from the centre of the curve.",
              r_attach="On this run", d_attach="On an earlier run", nonnumeric_fill="a little"),
    ),
    scene_clause="A cyclist rides along a path beside the road. The road surface is flat with the same friction everywhere. The "
                 "radius given is that of the inner edge of the road.",
    notes=_note("S12", "the scene clause says the stated radius is that of the inner edge of the road, and R says the car keeps to a "
                       "lane further out on this run, so the radius of its path is r + q (one reading) instead of a displacement "
                       "'before it entered the curve'."))
CHANGES["S12"] = (
    ("gpt high: other (R1 'driven 7.5 m further ... before it entered the curve' does not establish a new turning radius); "
     "claude medium: lateral position on the approach",
     "R1 'On this run, the car kept to a lane 7.5 m further from the centre of the curve.'; the scene clause 'The radius given is "
     "that of the inner edge of the road.' makes the lane radius r + q"),
    ("rated slightly_artificial R0/D0/N0/D1/N1/R1 ('moves 7.5 m further from the centre')",
     "'keeps to a lane ... further from the centre of the curve' (cyclist lane for D0/N0)"),
)

# --- S14 --------------------------------------------------------------------------------------------------------------------------
NO_K["S14"] = ("A power maximum below the power the lift needs makes the stated lift impossible rather than giving an alternative "
               "answer P = q, so no certified out-of-regime answer exists for 'the average power delivered'.")
FIXED["S14"] = dataclasses.replace(
    OLD["S14"],
    conditional=None,
    scene_clause="A crate rests on the floor beside the motor. The mass given is that of the load alone.",
    notes=_note("S14", "K (motor maximum power) removed, see NO_K; the scene clause states the load's mass is its own, so a box "
                       "strapped onto it adds to it."))
CHANGES["S14"] = (
    ("gpt high: other (K reference P = q does not follow when the maximum is below the needed power)",
     "conditional=None; reason in NO_K['S14']"),
    ("rated slightly_artificial R1 'A 12 kg box was strapped onto the load before the lift began.' (sits awkwardly with the stated "
     "80 kg)", "scene clause adds 'The mass given is that of the load alone.'"),
)

# --- S17 --------------------------------------------------------------------------------------------------------------------------
FIXED["S17"] = dataclasses.replace(
    OLD["S17"],
    pairs=(
        _pair("S17", 0, frame="The hotter surface of {relation} is then warmed by {value} {unit}.", nonnumeric_fill="a few kelvin"),
        _pair("S17", 1, frame="The hotter surface of the wall was warmed by {value} {unit} {relation}.",
              r_attach="before the flow was measured", nonnumeric_fill="a few kelvin"),
    ),
    scene_clause="A partition with a hotter and a colder surface stands beside the wall. No heat leaves through the edges of the "
                 "wall. The colder surface of the wall keeps its temperature, the temperature difference given is the initial "
                 "one, and the flow asked about is the settled flow at the end.",
    notes=_note("S17", "the scene clause gives the partition a hotter surface, states the colder surface keeps its temperature, the "
                       "stated difference is the initial one and the flow asked about is the settled flow; 'a further' dropped; "
                       "R1 is tied to 'before the flow was measured'."))
CHANGES["S17"] = (
    ("claude high / gpt high: R1 'warmed ... before the test began' is already included in the stated 20 K (failed identity)",
     "scene clause: the difference given is the initial one and the flow asked about is the settled flow at the end; R1 'The hotter "
     "surface of the wall was warmed by 6.5 K before the flow was measured.'"),
    ("gpt high: R0 does not say the colder surface is unchanged or that the flow is the new steady one",
     "scene clause: 'The colder surface of the wall keeps its temperature ... the flow asked about is the settled flow at the end.'"),
    ("rated artificial D0/N0 (partition has no hotter surface, 'a further')",
     "scene clause 'A partition with a hotter and a colder surface'; 'The hotter surface of the partition is then warmed by 6.5 K.'"),
    ("rated slightly_artificial R0/D1/N1 ('then warmed by a further ...')", "'a further' dropped, 'by a few kelvin' for N"),
)

# --- S19 --------------------------------------------------------------------------------------------------------------------------
FIXED["S19"] = dataclasses.replace(
    OLD["S19"],
    pairs=(
        _pair("S19", 0, frame="Before the ball is launched, the {relation} is lowered by {value} {unit}.",
              nonnumeric_fill="a few degrees"),
        _pair("S19", 1, frame="The launch direction was lowered by {value} {unit} {relation}.", nonnumeric_fill="a few degrees"),
    ),
    notes=_note("S19", "R0/D0 'Before the ball is launched, ... is lowered by {v}' fix the timing (the lowering precedes the flight "
                       "asked about); 'a further' dropped."))
CHANGES["S19"] = (
    ("gpt high: insufficient_boundary_condition (R0 'then lowered' placed after the landing sentence); claude medium",
     "R0 'The launch direction is then lowered by a further 14°.' -> 'Before the ball is launched, the launch direction is lowered "
     "by 14°.'"),
    ("rated artificial D0 'The ramp is then lowered by a further 14°.'", "'Before the ball is launched, the ramp is lowered by 14°.'"),
    ("rated slightly_artificial N0/N1/D1/R1 ('further few degrees')", "'a further' dropped; N 'by a few degrees'"),
)

# --- S21 --------------------------------------------------------------------------------------------------------------------------
FIXED["S21"] = dataclasses.replace(
    OLD["S21"],
    pairs=(
        _pair("S21", 0, frame="The {relation} is then tuned up by {value} {unit}.", d_attach="violin", nonnumeric_fill="a small amount",
              d_rationale="A violin is another sound source; tuning it changes the sound of the violin, not the frequency the siren "
                          "emits or the frequency the listener hears from the siren."),
        _pair("S21", 1, frame="The siren was tuned up by {value} {unit} {relation}.", r_attach="just before the tone was measured",
              nonnumeric_fill="a small amount"),
    ),
    scene_clause="A street musician stands nearby with a violin. The air is still, and the question concerns only the sound of the "
                 "siren. The tone given is the one the siren emits when first switched on.",
    scene_refs=("violin",),
    scene_object_rationale="A street musician with a violin is another sound source; it neither changes the siren's tone nor the "
                           "relative motion of the siren and the listener.",
    notes=_note("S21", "the scene clause states that the stated tone is the siren's tone when first switched on, so the tuning "
                       "(R) comes after it and the heard frequency is for the tuned siren; the horn is replaced by a violin that "
                       "can be tuned; 'a further' dropped."))
CHANGES["S21"] = (
    ("gpt high: failed_transformation_identity (R1 tuning before the measurement of the stated emitted frequency)",
     "scene clause 'The tone given is the one the siren emits when first switched on.'; R1 'The siren was tuned up by 16 Hz just "
     "before the tone was measured.'"),
    ("claude medium: R0 does not say whether retuning precedes the listening", "same scene clause; R0 'The siren is then tuned up by "
     "16 Hz.'"),
    ("rated artificial D0/N0 'The horn is then tuned up by a further 16 Hz.'", "'The violin is then tuned up by 16 Hz.' / 'by a small "
     "amount' (violin introduced by the scene clause)"),
    ("rated artificial N1 / slightly_artificial D1,R0,R1 ('further')", "'a further' dropped; N1 'The siren was tuned up by a small "
     "amount on an earlier run.'"),
)

# Main-session review (J15.1-059): the repaired S08 kept the certified R answers only by a scene clause that redefines what the
# frozen v1 question's "the two capacitors together" means; that is not an honest repair of the base text, so S08 is dropped.
DROPPED["S08"] = ("both judges (high): the R sentence adds a capacitor in parallel, but the frozen dataset-v1 question asks for the energy "
                  "in 'the two capacitors together'; the base text cannot change for an upgraded-v1 structure, so the R role has no "
                  "unambiguous answer")

ROLE_SPECS: dict[str, r2.RoleSpecV2] = {sid: FIXED.get(sid, spec) for sid, spec in OLD.items() if sid not in DROPPED}
SPECS = ROLE_SPECS
INFEASIBLE: dict[str, str] = {**dict(SRC.INFEASIBLE), **{sid: f"repair round 1: {why}" for sid, why in DROPPED.items()}}
STRUCTURE_FACTORIES = {**SRC.STRUCTURE_FACTORIES, **STRUCTURE_OVERRIDES}


def structure(structure_id: str) -> gr.Structure:
    """The structure (repaired factory if any) with the repaired spec's scene clause appended to its base context."""

    return r2.with_scene(STRUCTURE_FACTORIES[structure_id](), ROLE_SPECS[structure_id].scene_clause)
