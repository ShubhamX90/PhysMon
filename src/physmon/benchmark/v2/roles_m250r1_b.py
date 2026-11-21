"""M250 repair round 1 (journal J15.1-059) of `roles_m250_b`: the specs the two-judge panel rejected (any high flag) or whose sentences the
blind naturalness rater rated artificial, repaired; every other spec is the `roles_m250_b` object, unchanged.

Brief: `/scratch/pabitra/physmon/repair_m250_r1/briefs/roles_m250_b.md` (built by `scripts/v2/s207_m250_repair_briefs.py` from
`docs/validation/v2/llm_panel/admission_m250/runs/score_two_judges/`). No model output exists on any of these structures, so they may
still be edited (dataset admission standard, preamble). Wording rules 1-8 of `roles_m250_b` apply to every changed sentence.

`CHANGES` records, per changed structure, each finding and how it was resolved; `DROPPED` holds structures that could not be repaired
(they move to `INFEASIBLE` with the reason and are replaced in a later batch).
"""

from __future__ import annotations

import dataclasses

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import rolevalue as rv
from physmon.benchmark.v2 import rolevalue_v2 as r2
from physmon.benchmark.v2 import roles_m250_b as SRC

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

P = rv.Phrasing


def _pair(sid: str, i: int, **kw):
    return dataclasses.replace(OLD[sid].pairs[i], **kw)


def _fix(sid: str, note: str, **kw) -> r2.RoleSpecV2:
    spec = OLD[sid]
    return dataclasses.replace(spec, notes=f"{spec.notes} M250 r1: {note}".strip(), **kw)


def _no_k(sid: str, reason: str) -> None:
    NO_K[sid] = reason


# --- S24: the stated reservoir temperatures are those before any heating; the nearby object is a copper block -------------------

_S24_P0 = _pair(
    "S24", 0, frame="A burner under {relation} warms it by {value} {unit} before the first cycle.", r_attach="the hot reservoir",
    d_attach="the copper block",
    d_rationale="A burner that warms a copper block exchanges no heat with the engine's reservoirs; the temperatures of the engine's "
                "reservoirs are the stated ones.",
    nonnumeric_fill="a few kelvin",
    before_context_reason="The R sentence refers to 'the hot reservoir' before the context introduces the engine.")
_S24_P1 = _pair("S24", 1, nonnumeric_fill="a few kelvin")
FIXED["S24"] = _fix(
    "S24", "scene clause now says the stated reservoir temperatures are those at the outset (so R1 'Before the first cycle, a burner "
           "warmed the hot reservoir' has one reading: the engine runs at 600 K + q); the kettle (150 K would boil water) became a "
           "copper block; R0 states 'before the first cycle'.",
    scene_clause="A copper block stands nearby, and no heat passes between it and the engine or its reservoirs. The temperatures "
                 "stated for the reservoirs are those at the outset, before anything is done to them.",
    scene_object_rationale="A copper block that is warmed by its own burner exchanges no heat with the engine's reservoirs, so the "
                           "work done by the engine per cycle is still fixed by its stated heat and reservoir temperatures.",
    scene_refs=("copper block",), pairs=(_S24_P0, _S24_P1))
CHANGES["S24"] = (
    ("gpt high insufficient_boundary_condition: the warming variants do not establish that the stated 600 K is the temperature before "
     "the warming",
     "Scene clause (base condition) added: 'The temperatures stated for the reservoirs are those at the outset, before anything is "
     "done to them.' R0 now ends 'before the first cycle'; R1 unchanged ('Before the first cycle, a burner warmed the hot reservoir by "
     "150 K.'): one reading, the engine runs at the stated temperature plus the warming."),
    ("claude medium invalid_parameter_domain / D0 rated artificial: 'A burner then warms the kettle by 150 K.' (water would boil)",
     "The kettle is replaced by a copper block: D0 'A burner under the copper block warms it by 150 K before the first cycle.'"),
    ("claude low: 'then' leaves the timing of R0 ambiguous", "R0 'A burner under the hot reservoir warms it by 150 K before the first "
                                                         "cycle.' states the timing."),
    ("N0/N1/D1/R0/R1 slightly_artificial", "N0 and N1 keep 'a few kelvin'; N0 is the D0 sentence with the numeral replaced; R/D "
                                           "pair-0 sentences now read as a burner under the object (a purposeful action)."))

# --- S25: C states zero initial current; K states the post-saturation model; the stated current is the one at the outset -----------

_S25_C = dataclasses.replace(
    OLD["S25"].cancelling, spec=dataclasses.replace(
        OLD["S25"].cancelling.spec,
        phrasings=(P("c0", "was raised from zero to this value at a steady rate over"), P("c1", "rose steadily from zero to this value in"))))
_S25_K_SPEC = dataclasses.replace(
    OLD["S25"].conditional.spec, frame="The core of the coil {relation} {value} {unit}, above which its flux no longer grows.")
FIXED["S25"] = _fix(
    "S25", "C0 now says the current started from zero (the cancellation derivation needs it); the K frame states the saturation model "
           "(flux stops growing above the limit) that makes the reference energy L q^2 / 2 follow; the scene clause states that the stated "
           "current is the steady current at the outset (R1 reading).",
    scene_clause="A small lamp, wired to its own battery, stands beside the coil; neither current nor magnetic flux passes between "
                 "the lamp's circuit and the coil. The current stated is the steady current at the outset.",
    cancelling=_S25_C, conditional=dataclasses.replace(OLD["S25"].conditional, spec=_S25_K_SPEC))
CHANGES["S25"] = (
    ("gpt high missing_assumption: K claims give the outside-regime energy L*q^2/2 without the post-saturation flux-current relation",
     "K frame now 'The core of the coil stays linear for currents up to 9.5 A, above which its flux no longer grows.' (and the "
     "'does not saturate below a current of' twin): with the flux fixed at its saturation value L q, the stored energy is "
     "the integral of i d(flux) = L q^2 / 2."),
    ("gpt high other: C0 does not specify the zero initial current the derivation needs",
     "C0 'The current was brought up to this value at a steady rate over 45 ms.' -> 'The current was raised from zero to this value at "
     "a steady rate over 45 ms.' (C1 already said 'from zero')."),
    ("claude low: R1 leaves room to read the stated 3 A as the post-increase current",
     "Scene clause adds 'The current stated is the steady current at the outset.'"),
)

# --- S28: stated acceleration is the unmodified car's and holds up to any top speed; assumption text fixed -------------------------

_S28_P0 = _pair(
    "S28", 0, frame="A tuning kit that adds {value} {unit} to the acceleration is fitted to {relation} before the start.",
    nonnumeric_fill="a little",
    before_context_reason="The R sentence refers to 'the car', which the context introduces, with an acceleration the context has not "
                          "yet stated; placed first it reads as a fact about a car not yet in the scene.")
_S28_P1 = _pair(
    "S28", 1, frame="{relation}, a tuning kit that adds {value} {unit} to the acceleration was fitted to the car.")
FIXED["S28"] = _fix(
    "S28", "scene clause: the stated acceleration is the car's as delivered and holds until any top speed (resolves the KO speed cap and "
           "the R reading 2 + q); R and D sentences say the kit is fitted (before the start); the A-start assumption text is "
           "corrected (STRUCTURE_OVERRIDES; base text and gold unchanged).",
    scene_clause="A motorbike waits at the roadside, off the road and clear of the car and the truck. The acceleration stated for the "
                 "car is the one it has as delivered, and it keeps that acceleration until it reaches its top speed, if it has one.",
    pairs=(_S28_P0, _S28_P1))


def _s28_structure() -> gr.Structure:
    base = SRC.STRUCTURE_FACTORIES["S28"]()
    fixed = tuple(
        dataclasses.replace(a, text="The truck, which already travels at constant speed, passes the stationary car at the instant "
                                    "the car starts from rest.") if a.assumption_id == "A-start" else a for a in base.assumptions)
    return dataclasses.replace(base, assumptions=fixed)


STRUCTURE_OVERRIDES["S28"] = _s28_structure
CHANGES["S28"] = (
    ("gpt high contradictory_distractor_statement: KO0/KO1 speed cap contradicts the constant acceleration",
     "Scene clause: 'it keeps that acceleration until it reaches its top speed, if it has one.'"),
    ("gpt high missing_assumption + claude medium: R0/R1 leave open whether the stated 2 m/s^2 includes the kit",
     "Scene clause: 'The acceleration stated for the car is the one it has as delivered'; R0 'A tuning kit that adds 1.3 m/s2 to the "
     "acceleration is fitted to the car before the start.'; R1 'Before the start, a tuning kit that adds 1.3 m/s2 to the acceleration "
     "was fitted to the car.' (old R1 'Before the start, a tuning kit added 1.3 m/s2 to the acceleration of the car.', rated artificial)."),
    ("gpt high other: authors' first assumption says the stationary car passes the truck",
     "Assumption A-start text corrected to 'The truck, which already travels at constant speed, passes the stationary car at the instant "
     "the car starts from rest.' via STRUCTURE_OVERRIDES (only the assumption text; base problem text and gold unchanged)."),
    ("R0 slightly_artificial, D0/N0/D1/N1 slightly_artificial", "R/D/N share the new 'kit that adds ... is fitted to ...' frame."))

# --- S29: second sled replaces the crane; tension and speed stay as stated ------------------------------------------------------------

_S29_P0 = _pair(
    "S29", 0, frame="The rope of {relation} is then tilted {value} {unit} further above the horizontal.", r_attach="the sled being pulled",
    d_attach="the second sled",
    d_rationale="The rope of a second sled that stands beside the first is not the rope of the sled being pulled; tilting it leaves "
                "the angle, the tension and the speed of the first sled's rope as stated.",
    nonnumeric_fill="a few degrees",
    before_context_reason="The R sentence refers to 'the sled being pulled' before the context introduces it, and 'then' "
                          "presupposes the stated angle.")
_S29_P1 = _pair(
    "S29", 1, frame="{relation}, the rope of the sled being pulled was tilted {value} {unit} further above the horizontal.",
    nonnumeric_fill="a few degrees")
FIXED["S29"] = _fix(
    "S29", "D0/N0 now tilt the rope of a second sled (the crane jib was rated a pointless action); scene clause states that the tension "
           "and speed stay as stated when the rope is tilted (claude medium).",
    scene_clause="A second sled stands beside the first with a rope of its own, and neither sled touches the other or its rope. The "
                 "tension in the rope and the speed of the sled stay as stated if the rope is tilted.",
    scene_object_rationale="The rope of a second sled beside the first touches neither the first sled nor its rope, so the power the "
                           "rope delivers to the sled being pulled is unchanged.",
    scene_refs=("second sled",), pairs=(_S29_P0, _S29_P1))
CHANGES["S29"] = (
    ("D0 rated artificial: 'The jib of the crane is then tilted 17 deg further above the horizontal.' (pointless action)",
     "D0 'The rope of the second sled is then tilted 17 deg further above the horizontal.', same frame as R0 'The rope of the sled being "
     "pulled is then tilted ...'; N0 'a few degrees'."),
    ("claude medium: R does not say that tension and speed are unchanged after the tilt",
     "Scene clause: 'The tension in the rope and the speed of the sled stay as stated if the rope is tilted.'"),
    ("R0/R1 slightly_artificial ('the rope of the sled' awkward)", "R0/R1 name 'the sled being pulled'."))

# --- S31: the thrower stands on a platform at the cliff edge and the stone leaves from where the thrower stands --------------------------

_S31_P0 = _pair(
    "S31", 0, frame="A platform {value} {unit} high stands at the cliff edge, and {relation}.", r_attach="the thrower stands on top of it",
    d_attach="the surveyor stands on top of it",
    d_rationale="A surveyor who stands on a platform at the cliff edge is not the thrower; the stone is launched by the thrower from "
                "the cliff edge and its launch height is the stated height of the cliff.",
    nonnumeric_fill="a few metres",
    before_context_reason="The R sentence refers to 'the thrower' and 'the cliff edge' before the context introduces the throw and the "
                          "cliff.")
_S31_P1 = _pair(
    "S31", 1, frame="{relation}, the thrower stood on a platform {value} {unit} high at the cliff edge.",
    r_attach="When the stone was thrown", d_attach="In an earlier experiment",
    d_rationale="The thrower stood on a platform in an earlier experiment, which is over; in the stated experiment the stone leaves "
                "from the stated height.",
    nonnumeric_fill="a few metres")
FIXED["S31"] = _fix(
    "S31", "the R sentences now put the thrower on a platform (R0 'and the thrower stands on top of it', R1 'When the stone was "
           "thrown'); the scene clause says the stone leaves the thrower's hand at the level of the spot where the thrower stands, so "
           "the launch height is h + q with one reading; D0 has the surveyor on the platform.",
    scene_clause="A surveyor stands further along the cliff edge, clear of the stone's path. The stone leaves the thrower's hand at the "
                 "level of the spot where the thrower stands.",
    pairs=(_S31_P0, _S31_P1))
CHANGES["S31"] = (
    ("claude high + gpt high: R0/R1 do not establish a launch from the platform (stone is thrown 'from the edge of a cliff')",
     "Scene clause: 'The stone leaves the thrower's hand at the level of the spot where the thrower stands.' R0 'A platform 14 m high "
     "stands at the cliff edge, and the thrower stands on top of it.'; R1 'When the stone was thrown, the thrower stood on a platform "
     "14 m high at the cliff edge.' (old R0 'The thrower then climbs onto a platform 14 m above the cliff edge.')."),
    ("R0 rated artificial; N1 rated artificial; D0/D1/N0 slightly_artificial",
     "R0 no longer describes a climb after the throw; D0 'A platform 14 m high stands at the cliff edge, and the surveyor stands on top "
     "of it.'; D1/N1 'In an earlier experiment, the thrower stood on a platform 14 m high / a few metres high at the cliff edge.'"),
    ("claude medium: R sentences contradict 'thrown from the edge'", "The scene clause ties the launch to where the thrower stands."))

# --- S32: K states what the spring stores beyond its limit ----------------------------------------------------------------------------

_S32_K_SPEC = dataclasses.replace(
    OLD["S32"].conditional.spec, frame="The spring {relation} {value} {unit}, and stores no more energy beyond that.")
FIXED["S32"] = _fix(
    "S32", "K frame states the model behind the reference law (beyond the limit the spring stores no more energy, so the slide is "
           "k q^2 / (2 mu m g)).",
    conditional=dataclasses.replace(OLD["S32"].conditional, spec=_S32_K_SPEC))
CHANGES["S32"] = (
    ("gpt high other: the outside-regime expression k*q^2/(2*mu*m*g) does not follow from an elastic limit alone",
     "K sentences now read 'The spring obeys Hooke's law up to a compression of 28 cm, and stores no more energy beyond that.' (and the "
     "'stays elastic' twin): with that stated, the energy is k q^2/2 and the slide k q^2/(2 mu m g)."),
    ("gpt high rendering_not_minimal: numeral-free N controls omit mass and unit",
     "NOT CHANGED: this is the 5.3b by-design property (N sentences carry no numeral; the packet states it); no repair possible."),
)

# --- S34: hinged incline; K removed; C1 wording ---------------------------------------------------------------------------------------

_S34_P0 = _pair("S34", 0, nonnumeric_fill="a few degrees")
_S34_P1 = _pair("S34", 1, nonnumeric_fill="a few degrees")
_S34_C = dataclasses.replace(
    OLD["S34"].cancelling, spec=dataclasses.replace(
        OLD["S34"].cancelling.spec, phrasings=(P("c0", "has a radius of"), P("c1", "is solid, with a radius of"))))
FIXED["S34"] = _fix(
    "S34", "scene clause: the incline is a board hinged at its foot, set at the stated angle at first and clamped before the launch "
           "(R0/R1 then have one reading and no contradiction with 'fixed incline'); the K quantity (static friction) is removed because "
           "the out-of-regime reference law used the static coefficient as a kinetic one; C1 reworded.",
    scene_clause="A solar panel stands beside the incline. The incline is a board hinged at its foot, set at the stated angle at first "
                 "and clamped before the sphere is launched. Air resistance and rolling resistance are negligible, and the incline is "
                 "long enough for the sphere to come to rest on it.",
    pairs=(_S34_P0, _S34_P1), cancelling=_S34_C, conditional=None)
_no_k("S34", "When the static friction is too small the sphere slips, and the distance then depends on a kinetic friction law and on the "
             "initial spin, so no honest closed-form out-of-regime reference exists.")
CHANGES["S34"] = (
    ("gpt high insufficient_boundary_condition: R0 does not establish that the tilt finishes before launch",
     "Scene clause: 'The incline is a board hinged at its foot, set at the stated angle at first and clamped before the sphere is "
     "launched.' R0 'The incline is then tilted 13 deg more steeply.' and R1 'Before the sphere was set rolling, the incline was tilted "
     "13 deg more steeply.' now have one reading (clamped at the stated angle plus the tilt)."),
    ("R0/R1 rated artificial (contradict 'fixed' incline at 25 deg)", "Same scene clause: the stated angle is the first setting; "
                                                                      "the incline is clamped before the launch."),
    ("gpt high missing_assumption: outside-regime expression uses the static coefficient as the sliding coefficient",
     "K quantity removed (conditional=None); NO_K['S34'] gives the reason."),
    ("C1 slightly_artificial: 'The sphere measures, from its centre to its surface, 8.5 cm.'", "C1 'The sphere is solid, with a radius of "
                                                                                          "8.5 cm.'"),
)

# --- S35: stated length is the length at the outset; steady cone at the stated angle after any change --------------------------------

_S35_P0 = _pair(
    "S35", 0, frame="{relation} is then let out by {value} {unit}.", nonnumeric_fill="a short length")
_S35_P1 = _pair(
    "S35", 1, frame="{relation}, the string of the bob was let out by {value} {unit}.", nonnumeric_fill="a short length")
FIXED["S35"] = _fix(
    "S35", "scene clause: the stated length is the length at the outset and, after any change of the string, the bob again moves in a "
           "steady cone at the stated angle (one reading of R0/R1); the sentences say the string is let out (the reel line 'lengthened' "
           "was rated artificial).",
    scene_clause="A fishing reel lies on the bench, apart from the bob and its string. The string does not stretch. The length stated "
                 "for the string is its length at the outset; once the string has been changed, the bob again moves at constant speed "
                 "in a horizontal circle at the stated angle with the vertical.",
    pairs=(_S35_P0, _S35_P1))
CHANGES["S35"] = (
    ("claude high + gpt high: R0 (and R1) do not identify the operative length and the steady-motion state after the lengthening",
     "Scene clause: 'The length stated for the string is its length at the outset; once the string has been changed, the bob again "
     "moves at constant speed in a horizontal circle at the stated angle with the vertical.'"),
    ("claude medium: R1 may be read with the stated 1.2 m as the length after the lengthening", "Same clause (stated length is the "
                                                                                               "length at the outset)."),
    ("N0 rated artificial: 'The line on the reel is then lengthened by a little.'; D0/D1/N1 slightly_artificial",
     "p0 frame 'X is then let out by {v}.': D0 'The line on the reel is then let out by 0.7 m.', N0 '... let out by a short length.'; "
     "p1 'the string of the bob was let out by {v}'."),
)

# --- S36: a second rod replaces the see-saw ------------------------------------------------------------------------------------------

_S36_P0 = _pair(
    "S36", 0, r_attach="the swinging rod", d_attach="the second rod",
    d_rationale="The pivot of a second rod that hangs at rest is not the pivot of the swinging rod; moving it leaves the axis of the "
                "swinging rod where the problem put it.",
    nonnumeric_fill="a few centimetres",
    before_context_reason="The R sentence refers to 'the pivot of the swinging rod' before the context introduces it, and 'then' "
                          "presupposes the stated pivot.")
_S36_P1 = _pair("S36", 1, nonnumeric_fill="a few centimetres")
FIXED["S36"] = _fix(
    "S36", "D0/N0 now move the pivot of a second rod instead of a see-saw (rated artificial: a pointless action).",
    scene_clause="A second rod hangs at rest from a pivot of its own nearby, clear of the rod that swings and its axis.",
    scene_object_rationale="A second rod that hangs at rest from its own pivot does not touch the swinging rod or its axis, so the "
                           "oscillation of the swinging rod is unchanged.",
    scene_refs=("second rod",), pairs=(_S36_P0, _S36_P1))
CHANGES["S36"] = (
    ("D0 rated artificial: 'The pivot of the see-saw is then moved 20.5 cm closer to its centre.'",
     "D0 'The pivot of the second rod is then moved 20.5 cm closer to its centre.' (R0 'The pivot of the swinging rod is then moved ...')."),
    ("N0 rated artificial", "N0 'The pivot of the second rod is then moved a few centimetres closer to its centre.'"),
)

# --- S37: the raised orbit is again circular; the period asked for is that of the orbit at the time of the question --------------------

_S37_P0 = _pair("S37", 0, nonnumeric_fill="a few hundred kilometres")
_S37_P1 = _pair("S37", 1, nonnumeric_fill="a few hundred kilometres")
FIXED["S37"] = _fix(
    "S37", "scene clause: the stated altitude is that at the outset, a raised orbit is again circular with the altitude greater by the "
           "raise, and the period asked for is that of the orbit at the time of the question.",
    scene_clause="A space station orbits in a different plane and never comes close to the satellite. The altitude stated is that of "
                 "the satellite's orbit at the outset. If that orbit is raised, the satellite then moves in a new circular orbit whose "
                 "altitude is greater by the amount of the raise, and the period asked for is that of the orbit it is in at the time "
                 "of the question.",
    pairs=(_S37_P0, _S37_P1))
CHANGES["S37"] = (
    ("gpt high insufficient_boundary_condition: the final circularity / semimajor axis of the raised orbit is not specified",
     "Scene clause: 'If that orbit is raised, the satellite then moves in a new circular orbit whose altitude is greater by the amount "
     "of the raise, and the period asked for is that of the orbit it is in at the time of the question.'"),
    ("claude low: R0 does not say the asked period is the one after the raise", "Same clause."),
    ("N0/N1 slightly_artificial ('raised by a little')", "fill 'a few hundred kilometres'."),
)

# --- S38: the stated angle is the first setting; the person stands on the ladder at the angle at which it is finally left ----------

_S38_P0 = _pair("S38", 0, nonnumeric_fill="a few degrees")
_S38_P1 = _pair("S38", 1, nonnumeric_fill="a few degrees")
FIXED["S38"] = _fix(
    "S38", "scene clause: the stated angle is the first setting and the person stands on the ladder at the angle at which it is finally "
           "left (R1 no longer contradicts 'the person stands on the ladder at 62 deg'); the K quantity (static friction) is removed "
           "because the reference law kept N = (m + M) g and used the static coefficient as the friction force.",
    scene_clause="A hinged shutter is propped open beside the ladder. The angle stated for the ladder is the one at which it is first "
                 "set up, and the person stands still on it at the angle at which it is finally left.",
    pairs=(_S38_P0, _S38_P1), conditional=None)
_no_k("S38", "Below the needed friction the ladder slips and is not in equilibrium, so the ground force depends on the dynamics of the "
             "slide and on a kinetic friction law; no honest closed-form out-of-regime reference exists.")
CHANGES["S38"] = (
    ("claude high contradictory_distractor_statement + gpt high failed_transformation_identity: R1 (tilt before the person stood on "
     "the ladder) conflicts with the stated present-tense 62 deg",
     "Scene clause: 'The angle stated for the ladder is the one at which it is first set up, and the person stands still on it at the "
     "angle at which it is finally left.' R1 unchanged: one reading (62 - q deg while the person stands)."),
    ("gpt high other: outside-regime expression treats the static coefficient as the friction force and keeps N = (m+M)g",
     "K quantity removed (conditional=None); NO_K['S38'] gives the reason."),
    ("N0/N1/D0/D1 slightly_artificial", "fill 'a few degrees'."),
)

# --- S41: the force asked for is at the final separation; N fill reads naturally ------------------------------------------------------

_S41_P0 = _pair("S41", 0, nonnumeric_fill="a few centimetres")
_S41_P1 = _pair("S41", 1, nonnumeric_fill="a few centimetres")
FIXED["S41"] = _fix(
    "S41", "scene clause: the force asked for is the one at the final separation of the spheres, after all their moves (R1 reading); "
           "N fill 'a few centimetres' (N0 'a little further apart' was rated artificial).",
    scene_clause="A pair of bar magnets lies on the bench. The spheres are insulated from their surroundings, and no other charges "
                 "are near them. The force asked for is the one at the final separation of the spheres, after all their moves.",
    pairs=(_S41_P0, _S41_P1))
CHANGES["S41"] = (
    ("gpt high insufficient_boundary_condition + claude medium: R1 leaves the position of the extra move in the sequence open",
     "Scene clause: 'The force asked for is the one at the final separation of the spheres, after all their moves.'"),
    ("N0 rated artificial: 'The magnets are then moved a little further apart.'",
     "N0 'The magnets are then moved a few centimetres further apart.' (N1 likewise)."),
)

# --- S42: the cell goes in series with the battery across the wire; the lamp glows dimly ----------------------------------------------

_S42_P0 = _pair(
    "S42", 0, frame="A {value} {unit} cell of negligible internal resistance is connected in series with {relation}, facing the same way.",
    r_attach="the battery across the wire", d_attach="the lamp's battery")
_S42_P1 = _pair(
    "S42", 1, frame="{relation}, a {value} {unit} cell of negligible internal resistance was connected in series with the battery "
                    "across the wire, facing the same way.", r_attach="Just before the power was measured")
FIXED["S42"] = _fix(
    "S42", "the R sentences name 'the battery across the wire' (the scene's lamp battery made 'the battery' ambiguous); R1 reads "
           "'Just before the power was measured'; the lamp glows dimly so that an extra cell for its battery has a purpose.",
    scene_clause="A small lamp, wired to a battery of its own, glows dimly beside the circuit. The leads have negligible resistance, "
                 "and the wire stays at a constant temperature.",
    pairs=(_S42_P0, _S42_P1))
CHANGES["S42"] = (
    ("gpt high insufficient_boundary_condition: R0/R1 say 'the battery' after two batteries are introduced",
     "R0 '... connected in series with the battery across the wire, facing the same way.'; R1 'Just before the power was measured, a 7.5 V "
     "cell ... was connected in series with the battery across the wire, facing the same way.'; D0 keeps 'the lamp's battery'."),
    ("claude low: R1 relies on inferring that the cell stays in place", "R1 'Just before the power was measured' (the cell is part of "
                                                                       "the circuit at the measurement)."),
    ("N0 rated artificial (cell added to a bystander lamp's battery)", "The lamp glows dimly (scene clause), so an added cell for the "
                                                                       "lamp's battery has a purpose."),
)

# --- S43: the cell is in series with the battery from before the capacitor is first charged ---------------------------------------------

_S43_P0 = _pair(
    "S43", 0, frame="A {value} {unit} cell of negligible internal resistance was connected in series with {relation}, facing the same "
                    "way, before the capacitor was first charged.",
    r_attach="the battery across the capacitor", d_attach="the lamp's battery")
_S43_P1 = _pair(
    "S43", 1, frame="{relation}, a {value} {unit} cell of negligible internal resistance was connected in series with the battery "
                    "across the capacitor, facing the same way.", r_attach="Before the capacitor was first charged")
FIXED["S43"] = _fix(
    "S43", "the R cell is in series with the battery from before the capacitor is first charged, so the extra charge is measured from "
           "the cell-inclusive charged state and the cell stays in the circuit during the insertion; the R sentences name 'the "
           "battery across the capacitor'; the lamp glows dimly.",
    scene_clause="A small lamp, wired to a battery of its own, glows dimly beside the capacitor. The leads have negligible "
                 "resistance, and edge effects at the plates are negligible.",
    pairs=(_S43_P0, _S43_P1))
CHANGES["S43"] = (
    ("gpt high insufficient_boundary_condition: does not specify whether the additional charge excludes charging caused by connecting "
     "the cell after the initial 12 V state",
     "R0 '... was connected in series with the battery across the capacitor, facing the same way, before the capacitor was first "
     "charged.'; R1 'Before the capacitor was first charged, a 7.5 V cell ... was connected in series with the battery across the "
     "capacitor, facing the same way.'"),
    ("claude medium: R1 does not state that the cell remains connected during the insertion",
     "The cell is part of the battery circuit from before the first charging; the base says the battery stays connected."),
    ("D0/N0/R0 slightly_artificial", "Lamp glows dimly (scene clause); R0 is in the past tense and names the battery across the "
                                     "capacitor."),
)

# --- S45: the extra voltage acts while the bead is accelerated; wiring text without the symbol clash ---------------------------------

_S45_P0 = _pair(
    "S45", 0, frame="An extra {value} {unit} is applied across {relation} while the bead is being accelerated.")
_S45_P1 = _pair(
    "S45", 1, frame="{relation}, an extra {value} {unit} was applied across the accelerating gap.",
    r_attach="While the bead was being accelerated", d_attach="In an earlier experiment")
_S45_REL = rv.RelevantWiring(
    "V", "add", "An extra potential applied across the accelerating gap while the bead crosses it adds to the stated potential difference; "
                "the bead gains its charge times the sum of the two as kinetic energy, and the speed follows from that.")
FIXED["S45"] = _fix(
    "S45", "R sentences state that the extra voltage acts while the bead is accelerated; the scene clause introduces 'the accelerating "
           "gap'; the bulb glows dimly; the wiring rationale no longer uses q for both the charge and the added voltage.",
    scene_clause="A small bulb is wired to a supply of its own beside the apparatus and glows dimly. The bead crosses the accelerating "
                 "gap between two plates, and no electric field acts on it outside the gap.",
    relevant=_S45_REL, pairs=(_S45_P0, _S45_P1))
CHANGES["S45"] = (
    ("gpt high insufficient_boundary_condition: R1 does not establish that the extra voltage remains across the gap during acceleration",
     "R1 'While the bead was being accelerated, an extra 6.5 V was applied across the accelerating gap.'; R0 '... applied across the "
     "accelerating gap while the bead is being accelerated.' (old R1 'An extra 6.5 V was applied across the accelerating gap before the "
     "bead was released.')"),
    ("gpt high inconsistent_units: wiring uses q for both the bead charge and the extra voltage",
     "Wiring rationale reworded without symbols: 'the bead gains its charge times the sum of the two as kinetic energy'. (The input "
     "name of the charge is the library's; not changed.)"),
    ("claude low: 'the accelerating gap' not introduced", "Scene clause: 'The bead crosses the accelerating gap between two plates, "
                                                          "and no electric field acts on it outside the gap.'"),
    ("D0/N0 slightly_artificial (extra voltage with no baseline across the bulb)", "The bulb glows dimly (scene clause)."),
)

ROLE_SPECS: dict[str, r2.RoleSpecV2] = {sid: FIXED.get(sid, spec) for sid, spec in OLD.items() if sid not in DROPPED}
SPECS = ROLE_SPECS
INFEASIBLE: dict[str, str] = {**dict(SRC.INFEASIBLE), **{sid: f"repair round 1: {why}" for sid, why in DROPPED.items()}}
STRUCTURE_FACTORIES = {**SRC.STRUCTURE_FACTORIES, **STRUCTURE_OVERRIDES}


def structure(structure_id: str) -> gr.Structure:
    """The structure (repaired factory if any) with the repaired spec's scene clause appended to its base context."""

    return r2.with_scene(STRUCTURE_FACTORIES[structure_id](), ROLE_SPECS[structure_id].scene_clause)
