"""M250 repair round 1 (journal J15.1-059) of `roles_m250n_waves`: the specs the two-judge panel rejected (any high flag) or whose sentences the
blind naturalness rater rated artificial, repaired; every other spec is the `roles_m250n_waves` object, unchanged.

Brief: `/scratch/pabitra/physmon/repair_m250_r1/briefs/roles_m250n_waves.md` (built by `scripts/v2/s207_m250_repair_briefs.py` from
`docs/validation/v2/llm_panel/admission_m250/runs/score_two_judges/`). No model output exists on any of these structures, so they may
still be edited (dataset admission standard, preamble). Wording rules 1-8 of `roles_m250n_waves` apply to every changed sentence.

`CHANGES` records, per changed structure, each finding and how it was resolved; `DROPPED` holds structures that could not be repaired
(they move to `INFEASIBLE` with the reason and are replaced in a later batch).
"""

from __future__ import annotations

import dataclasses

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import rolevalue as rv
from physmon.benchmark.v2 import rolevalue_v2 as r2
from physmon.benchmark.v2 import roles_m250n_waves as SRC

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


def _drop_k(sid: str, reason: str) -> None:
    NO_K[sid] = reason
    K_KINDS.pop(sid, None)


# --- S231 --------------------------------------------------------------------------------------------------------------------------
# GPT high: R1 did not establish that the extra speed holds at the reflection or that it is additional to the stated 3 m/s. The extra
# speed becomes the speed of a trolley that carries the wall; the stated speed is relative to the trolley, which is at rest unless
# its motion is described (scene clause), so the wall moves at v + q relative to the still air for the whole recording.
S231_P0 = _pair("S231", 0, frame="The {relation} moves towards the loudspeaker at {value} {unit}.", r_attach="trolley",
                d_attach="conveyor belt",
                d_rationale="A conveyor belt that moves along the floor carries parcels only; the trolley, and so the wall that rides on "
                            "it, are as stated, and the belt stirs no air.",
                nonnumeric_fill="a low speed",
                before_context_reason="The R sentence refers to 'the trolley' before the context introduces it.")
S231_P1 = _pair("S231", 1, frame="The trolley was moving towards the loudspeaker at {value} {unit} {relation}.",
                r_attach="throughout the recording", d_attach="in an earlier run",
                d_rationale="The trolley moved in an earlier run, which is over; in the stated recording the wall moves "
                            "at the stated speed relative to a trolley that has no such motion.",
                nonnumeric_fill="a low speed")
FIXED["S231"] = dataclasses.replace(
    OLD["S231"], quantity_phrase="a trolley speed",
    relevant=rv.RelevantWiring("v", "add", "A trolley carrying the wall towards the loudspeaker at q adds q to the speed of the wall "
                                           "relative to the still air, which becomes v + q, and the beat is 2 f (v + q) / (c - v - q)."),
    scene_clause="The wall rides on a flat trolley, and the speed given for the wall is the speed it has relative to the trolley. "
                 "A conveyor belt carries parcels along the floor beside the loudspeaker; it "
                 "stirs no air, which stays still throughout.",
    scene_object_rationale="A conveyor belt on the floor is not the large flat wall that reflects the tone, so the tone, the echo "
                           "that the microphone records and the beat are those of the wall alone; the speed given for the wall is relative to "
                           "the trolley.",
    pairs=(S231_P0, S231_P1),
    notes=_note("S231", "the extra speed is that of a trolley that carries the wall (stated speed relative to the trolley); R1 'throughout the recording' fixes the timing and the addition."))
CHANGES["S231"] = (
    ("gpt high insufficient_boundary_condition: R1 does not establish that the increment precedes the reflection or is additional to "
     "the stated 3 m/s",
     "Old 'A motor had added 1.4 m/s to the speed of the wall before the echo was recorded' replaced by 'The trolley was moving towards "
     "the loudspeaker at 1.4 m/s throughout the recording'; the scene clause says the wall rides on a trolley and the speed given is relative "
     "to the trolley: exactly one reading, wall at 3 + 1.4 m/s relative to the air."),
    ("claude low: pluperfect only implicitly says the extra speed persists", "Same rewrite: 'throughout the recording'."),
    ("rated slightly_artificial R0/R1/D0/D1/N0/N1 ('A motor adds 1.4 m/s to the speed of the wall', 'for an earlier run only')",
     "R0 'The trolley moves towards the loudspeaker at 1.4 m/s.', D0 'The conveyor belt moves towards the loudspeaker at 1.4 m/s.', "
     "D1 'The trolley was moving ... in an earlier run.'; N fill 'a low speed'."),
)

# --- S232 --------------------------------------------------------------------------------------------------------------------------
# GPT high: the K outside-regime reference sqrt(g q) is not the finite-depth group speed. Replaced by the exact finite-depth group
# speed d(omega)/dk of w^2 = (g k + sigma k^3 / rho) tanh(k q).
_drop_k("S232", "The check needs an outside-regime law that differs from the answer at in-regime depths, and the only honest outside-regime "
                "law is the finite-depth group speed, which equals the deep-water answer at these depths; the regime is the stated "
                "deep-water one.")
FIXED["S232"] = dataclasses.replace(
    OLD["S232"], conditional=None,
    pairs=(_pair("S232", 0, nonnumeric_fill="a small amount"), _pair("S232", 1, nonnumeric_fill="a small amount")),
    notes=_note("S232", "K removed (see NO_K); N fill 'a small amount'."))
CHANGES["S232"] = (
    ("gpt high other: K claim sqrt(g*q) is not the finite-depth group speed of gravity-capillary waves",
     "K removed: the honest finite-depth group speed equals the stated answer at in-regime depths and so cannot serve as a separated "
     "outside-regime reference; NO_K['S232'] gives the reason."),
    ("gpt high rendering_not_minimal (5.3b judge error, not counted)", "N sentences stay numeral-free by design."),
    ("rated slightly_artificial N0/N1 'by a little'", "fill 'a small amount' ('by a small amount')."),
)

# --- S233 --------------------------------------------------------------------------------------------------------------------------
_S233_C = OLD["S233"].cancelling
S233_C = dataclasses.replace(
    _S233_C, spec=dataclasses.replace(
        _S233_C.spec,
        intermediate_relations=("intensity of the incident beam I0 = P0 / q",
                                "power that reaches the surface = I0 q",
                                "power that enters the glass = (1 - R) times the power that reaches the surface (a power fraction: "
                                "the refracted beam is wider or narrower, which does not matter for the power)")))
S233_P0 = _pair("S233", 0, frame="An optical amplifier adds {value} {unit} to the power of {relation}.", r_attach="the beam",
                d_attach="the second laser",
                d_rationale="An optical amplifier that raises the power of the second laser acts on that laser only; the power of the "
                            "beam that strikes the glass is the stated one.",
                nonnumeric_fill="a small amount",
                before_context_reason="The R sentence refers to 'the beam' and to its power before the context introduces them.")
S233_P1 = _pair("S233", 1, frame="An optical amplifier added {value} {unit} to the power of the beam {relation}.",
                r_attach="before it struck the glass", d_attach="in an earlier run",
                d_rationale="The amplifier added power to the beam in an earlier run, which is over; in the stated run the beam that "
                            "strikes the glass has the power at the laser, as stated.",
                nonnumeric_fill="a small amount")
FIXED["S233"] = dataclasses.replace(
    OLD["S233"], cancelling=S233_C, pairs=(S233_P0, S233_P1),
    relevant=rv.RelevantWiring("P0", "add", "An optical amplifier that adds q to the power of the beam, whose stated power is the power "
                                            "at the laser, makes the incident power P0 + q, and the transmitted power is "
                                            "(P0 + q) (1 - R)."),
    scene_clause="The beam leaves a laser fixed to the bench, and the power given for it is the power at the laser. A second laser "
                 "stands on the bench beside the block, turned away from it. The beam is narrow and parallel.",
    scene_object_rationale="A second laser turned away from the block sends no light onto it, so the power that strikes and enters the "
                           "block is that of the beam alone, whose stated power is the power at its laser.",
    scene_refs=("second laser",),
    notes=_note("S233", "the stated power is the power at the laser (scene clause), an optical amplifier adds q after it; the C "
                        "relations speak of power fractions through the same patch of the surface."))
CHANGES["S233"] = (
    ("gpt high insufficient_boundary_condition: R0/R1 do not establish whether the stated 5 mW is before or after boosting",
     "Scene clause now says the power given for the beam is the power at its laser; R0 'An optical amplifier adds 3.4 mW to the power "
     "of the beam.', R1 'An optical amplifier added 3.4 mW to the power of the beam before it struck the glass.' (old: 'A booster ...')."),
    ("gpt high other: C relations equate transmitted irradiance with I0 (1-R) over the same cross-section",
     "Intermediate relations rewritten as power fractions: I0 = P0/q, power reaching the surface = I0 q, power entering = (1-R) times "
     "that, noting that the refracted beam has another width (claude low also resolved)."),
    ("rated artificial D0/N0/R0 ('A booster adds 3.4 mW to the power of the laser pointer')",
     "'An optical amplifier adds 3.4 mW to the power of the second laser.' (a laser on the bench, turned away from the block); N fill "
     "'a small amount'."),
    ("rated slightly_artificial D1/N1/R1 ('A booster had added ... for an earlier run only')",
     "'An optical amplifier added 3.4 mW to the power of the beam in an earlier run.' / before it struck the glass."),
)

# --- S234 --------------------------------------------------------------------------------------------------------------------------
_S234_C = OLD["S234"].cancelling
S234_C = dataclasses.replace(
    _S234_C, spec=dataclasses.replace(
        _S234_C.spec,
        intermediate_relations=("number of legs of the zigzag per unit length of the rod = tan(theta_r) / d (for a rod much longer "
                                "than it is wide)", "length of one leg = d / sin(theta_r)",
                                "total path = legs per unit length times L times the length of one leg")))
S234_P0 = _pair("S234", 0, frame="The {relation} is extended by {value} {unit} of the same glass, joined on in line with it.",
                r_attach="rod", d_attach="optical cable",
                d_rationale="A piece joined onto the optical cable lengthens the cable only; the length of the rod that carries the pulse "
                            "is the stated one.",
                nonnumeric_fill="a short length",
                before_context_reason="The R sentence refers to 'the rod' before the context introduces any rod.")
S234_P1 = _pair("S234", 1,
                frame="The rod was extended by {value} {unit} of the same glass, joined on in line with it, {relation}.",
                r_attach="before the pulse was sent", d_attach="for an earlier run only",
                d_rationale="The piece was joined on for an earlier run, which is over; in the stated run the pulse crosses a rod of "
                            "the stated length.",
                nonnumeric_fill="a short length")
_drop_k("S234", "If the liquid at the sides had an index above n cos(theta_r) the light would leak out through the sides and no pulse "
                "would reach the far end, so no outside-regime transit time exists to serve as a reference; the regime is the stated "
                "total internal reflection.")
FIXED["S234"] = dataclasses.replace(
    OLD["S234"], cancelling=S234_C, conditional=None, pairs=(S234_P0, S234_P1),
    relevant=rv.RelevantWiring("L", "add", "A piece of the same glass joined on in line with the rod, with the same index and the same "
                                           "width, makes its length L + q, and the transit time is n (L + q) / (c cos(theta_r))."),
    notes=_note("S234", "R is a piece of the same glass joined on in line; C relation speaks of legs per unit length; K removed "
                        "(see NO_K)."))
CHANGES["S234"] = (
    ("gpt high missing_assumption (and claude low): the coupler's index and alignment are not stated",
     "R0 'The rod is extended by 1.3 m of the same glass, joined on in line with it.'; R1 'The rod was extended by 1.3 m of the same "
     "glass, joined on in line with it, before the pulse was sent.' (old: 'A glass coupler adds 1.3 m to the length of the rod')."),
    ("gpt high other: C claim treats L tan/d as the literal number of legs",
     "C relation now 'number of legs per unit length = tan(theta_r) / d (rod much longer than wide)'."),
    ("gpt high other: K reference q*ell/c uses the liquid's index as if it were the glass's",
     "K removed: no outside-regime transit time exists once the light leaks; NO_K['S234'] gives the reason."),
    ("rated artificial D0/N0/R0 ('A glass coupler adds 1.3 m to the length of the optical cable')",
     "D0 'The optical cable is extended by 1.3 m of the same glass, joined on in line with it.'; N fill 'a short length'."),
    ("rated slightly_artificial D1/N1/R1", "'The rod was extended by ... for an earlier run only' / before the pulse was sent."),
)

# --- S235 --------------------------------------------------------------------------------------------------------------------------
_S235_C = OLD["S235"].cancelling
S235_C = dataclasses.replace(
    _S235_C, spec=dataclasses.replace(
        _S235_C.spec, values=(24.0, 32.0, 42.0),
        phrasings=(rv.Phrasing("c0", "has a radius of"), rv.Phrasing("c1", "is cut to a radius of"))),
    heldout_values=(27.0, 36.0))
_drop_k("S235", "A release deep enough to submerge the whole cylinder has an exact piecewise period (constant buoyant force, then "
                "simple harmonic motion), which is undefined at in-regime release depths, so no outside-regime reference law can be "
                "checked against the stated answer; the regime is the stated partial submersion.")
S235_P0 = _pair("S235", 0,
                frame="The {relation} is built up by {value} {unit} of the same wood, glued on top with the same cross-section.",
                r_attach="cylinder", d_attach="raft",
                d_rationale="Wood glued on top of the raft thickens the raft only; the density and the length of the cylinder that is "
                            "pushed down are the stated ones.",
                nonnumeric_fill="a short length",
                before_context_reason="The R sentence refers to 'the cylinder' and to its wood before the context introduces them.")
S235_P1 = _pair("S235", 1,
                frame="The cylinder was built up by {value} {unit} of the same wood, glued on top with the same cross-section, {relation}.",
                r_attach="before it was pushed down", d_attach="for an earlier run only",
                d_rationale="The extra wood was on the cylinder for an earlier run, which is over; in the stated run the cylinder that "
                            "is pushed down has the stated length.",
                nonnumeric_fill="a short length")
FIXED["S235"] = dataclasses.replace(
    OLD["S235"], cancelling=S235_C, conditional=None, pairs=(S235_P0, S235_P1),
    relevant=rv.RelevantWiring("h", "add", "A length q of the same wood glued on top of the cylinder with the same cross-section makes "
                                           "its length h + q at the same density, so the submerged length is rho_b (h + q) / rho_l."),
    scene_clause="The cylinder is made of wood. A small wooden raft also floats in the tank, far from the cylinder. The liquid is "
                 "otherwise at rest.",
    scene_object_rationale="A small raft floating in the large tank has its own draught and its own motion; it does not touch the "
                           "cylinder, so the cylinder's period is fixed by its own density and length; the cylinder is wooden, so "
                           "'the same wood' has the stated density.",
    notes=_note("S235", "C radii 24, 32, 42 cm (a 30 cm cylinder of relative density 0.65 floats upright only for r > 20 cm); R builds "
                        "the cylinder up with the same wood and cross-section (scene clause: the cylinder is wooden); K removed "
                        "(see NO_K)."))
CHANGES["S235"] = (
    ("claude high invalid_parameter_domain: C radii 2.5, 4.5, 7 cm are far below the r > 20 cm needed to float upright",
     "C values (24, 32, 42) cm, held out (27, 36) cm, all above 20.2 cm; c1 'is cut to a radius of'."),
    ("claude medium missing_assumption: 'the same wood' has no referent for the cylinder",
     "Scene clause 'The cylinder is made of wood.'"),
    ("gpt high missing_assumption: R omits the cross-section of the added wood",
     "R0 'The cylinder is built up by 9.5 cm of the same wood, glued on top with the same cross-section.' (old: 'A 9.5 cm length of the "
     "same wood is glued on top of the cylinder.'); R1 likewise, 'before it was pushed down'."),
    ("gpt high other: K reference 2*pi*sqrt((d0+q)/g) is wrong once the cylinder is fully submerged",
     "K removed: the exact piecewise period is undefined at in-regime release depths; NO_K['S235'] gives the reason."),
    ("rated artificial R0/R1 ('same wood' glued on top; contradicts the 30 cm cylinder)", "'built up by ... of the same wood' with the "
     "wooden cylinder stated; D0 'The raft is built up by 9.5 cm of the same wood, glued on top with the same cross-section.'"),
)

# --- S236 --------------------------------------------------------------------------------------------------------------------------
_S236_C = OLD["S236"].cancelling
S236_C = dataclasses.replace(
    _S236_C, spec=dataclasses.replace(_S236_C.spec, values=(0.9, 1.1, 1.3)), heldout_values=(0.95, 1.4))
S236_P0 = _pair("S236", 0, frame="The {relation} is extended by {value} {unit} of glass tube of the same bore.",
                r_attach="neck of the flask", d_attach="stem of the funnel",
                d_rationale="A tube joined onto the stem of the funnel lengthens the stem only; the neck of the flask that resonates has "
                            "the stated length.",
                nonnumeric_fill="a short length",
                before_context_reason="The R sentence refers to the neck of the flask before the context introduces the flask.")
S236_P1 = _pair("S236", 1,
                frame="The neck of the flask was extended by {value} {unit} of glass tube of the same bore {relation}.",
                r_attach="for the whole of the resonance measurement", d_attach="for an earlier run only",
                d_rationale="The tube was on the neck for an earlier run, which is over; in the stated measurement the neck has the "
                            "stated length.",
                nonnumeric_fill="a short length")
_drop_k("S236", "A flask whose size is comparable with the wavelength has no single resonance formula in terms of its longest dimension "
                "(it depends on the shape and the boundary conditions), so no honest outside-regime reference exists; the regime is the "
                "stated lumped one.")
FIXED["S236"] = dataclasses.replace(
    OLD["S236"], cancelling=S236_C, conditional=None, pairs=(S236_P0, S236_P1),
    notes=_note("S236", "R is stated as an extension of the neck that lasts for the whole measurement; C densities are ordinary air "
                        "densities (0.9, 1.1, 1.3 kg/m^3); K removed (see NO_K)."))
CHANGES["S236"] = (
    ("gpt high insufficient_boundary_condition (and claude medium): R1 does not say the tube stays on during the measurement",
     "R1 'The neck of the flask was extended by 3.2 cm of glass tube of the same bore for the whole of the resonance measurement.' "
     "(old: 'had been attached ... before its resonance was measured')."),
    ("gpt high other: K reference c/(4q) is not a general flask resonance",
     "K removed; NO_K['S236'] gives the reason."),
    ("rated slightly_artificial C0/C1 (air density 1.6 kg/m^3 unusually high; claude low)",
     "C values (0.9, 1.1, 1.3) kg/m^3, held out (0.95, 1.4); the wrong law (fixed atmospheric pressure) still differs by > 3%."),
    ("rated slightly_artificial D0/N0 ('of the same bore' has no referent), D1/N1, R1",
     "'The stem of the funnel is extended by 3.2 cm of glass tube of the same bore.' (the bore is that of the thing extended); D1 'for an "
     "earlier run only' kept."),
)

# --- S237 --------------------------------------------------------------------------------------------------------------------------
S237_P0 = _pair("S237", 0, frame="A spring tide is holding the water at the landward end of {relation} {value} {unit} higher than usual.",
                r_attach="the slope", d_attach="the harbour",
                d_rationale="A spring tide that holds the water of the harbour higher changes the harbour only; the depths of the slope "
                            "that the tsunami crosses are the stated ones.",
                nonnumeric_fill="a little",
                before_context_reason="The R sentence refers to 'the slope' before the context introduces it.")
S237_P1 = _pair("S237", 1, frame="A spring tide held the water at the landward end of the slope {value} {unit} higher than usual "
                                 "{relation}.",
                r_attach="while the tsunami crossed it", d_attach="during an earlier survey",
                d_rationale="The tide held the water higher during an earlier survey, which is over and leaves nothing behind; while the "
                            "tsunami crosses, the depths of the slope are the stated ones.",
                nonnumeric_fill="a little")
_drop_k("S237", "Outside the long-wave regime the wave speed depends on the wavelength through tanh(k h) and the wavelength itself changes "
                "along the slope, so no single closed reference crossing time follows from the wavelength alone; the regime is the "
                "stated shallow-water one.")
FIXED["S237"] = dataclasses.replace(
    OLD["S237"], conditional=None, pairs=(S237_P0, S237_P1), values=(9.0, 33.0, 47.0), heldout_values=(14.0, 38.0),
    quantity_phrase="a spring tide",
    relevant=rv.RelevantWiring("h2", "add", "A spring tide that holds the water at the landward end q higher than usual makes the depth "
                                            "there h2 + q, which changes the wave speed there; the depth still varies steadily along "
                                            "the slope."),
    scene_clause="A fishing harbour lies along the same coast, well away from the sloping seabed. The depth along the slope always "
                 "varies steadily between its two ends. The sea is otherwise still.",
    scene_object_rationale="A fishing harbour has its own water and its own depths; a tide in the harbour leaves the slope that the "
                           "tsunami crosses unchanged, so the depths of the slope are the stated ones.",
    notes=_note("S237", "dredging is replaced by a spring tide (a transient change that leaves no state: R1 'while the tsunami crossed "
                        "it', D1 'during an earlier survey'); the scene clause keeps the depth varying steadily between the ends; "
                        "values 9, 33, 47 m; K removed (see NO_K)."))
CHANGES["S237"] = (
    ("gpt high hidden_coupling / insufficient_boundary_condition: dredging 'for an earlier survey only' can permanently alter the slope",
     "A spring tide is transient: R1 'A spring tide held the water at the landward end of the slope 33 m higher than usual while the "
     "tsunami crossed it.'; D1 '... during an earlier survey.' (old: 'For an earlier survey only, dredging added 33 m ...')."),
    ("gpt high missing_assumption: linearity of the modified seabed is not established",
     "Scene clause 'The depth along the slope always varies steadily between its two ends.'"),
    ("gpt high invalid_parameter_domain: K reference uses the deep-water speed", "K removed; NO_K['S237'] gives the reason."),
    ("rated artificial D1/R0/R1 (dredging 33 m of open shelf), slightly_artificial D0/N1",
     "R0 'A spring tide is holding the water at the landward end of the slope 33 m higher than usual.'; D0 the same at the harbour; "
     "values 9, 33, 47 m (held out 14, 38)."),
)

# --- S238 --------------------------------------------------------------------------------------------------------------------------
_S238_C = OLD["S238"].cancelling
S238_C = dataclasses.replace(
    _S238_C, spec=dataclasses.replace(
        _S238_C.spec,
        intermediate_relations=("kinematic viscosity nu = eta / q", "shear stress tau = q nu r d(omega)/dr",
                                "torque T = 4 pi (q nu) L omega R1^2 R2^2 / (R2^2 - R1^2)")))
_S238_K = OLD["S238"].conditional
S238_K = dataclasses.replace(
    _S238_K, spec=dataclasses.replace(
        _S238_K.spec, quantity_phrase="the rotation rate above which the flow is no longer purely circular",
        phrasings=(rv.Phrasing("k0", "stays purely circular up to a rotation rate of"),
                   rv.Phrasing("k1", "remains free of vortices up to"))),
    k_out=dataclasses.replace(
        _S238_K.k_out,
        reason="The problem states that the flow is steady and laminar and (scene clause) purely circular; a rotation rate above the "
               "onset of vortices would contradict that, and the circular-flow torque on which the question rests would not apply."))
S238_P0 = _pair("S238", 0, frame="The speed setting of {relation} is raised by {value} {unit}.", r_attach="the rotor",
                d_attach="the stirrer",
                d_rationale="Raising the speed setting of the stirrer changes the stirrer only; the rotation rate of the rotor in the "
                            "question is the stated one.",
                nonnumeric_fill="a small amount",
                before_context_reason="The R sentence refers to 'the rotor' and to its speed setting before the context introduces them.")
S238_P1 = _pair("S238", 1, frame="The speed setting of the rotor was raised by {value} {unit} {relation}.",
                r_attach="before the power was measured", d_attach="for an earlier run only",
                d_rationale="The setting was raised for an earlier run, which is over; in the stated measurement the rotor turns at the "
                            "stated rate.",
                nonnumeric_fill="a small amount")
FIXED["S238"] = dataclasses.replace(
    OLD["S238"], cancelling=S238_C, conditional=S238_K, pairs=(S238_P0, S238_P1), quantity_phrase="a raised speed setting",
    relevant=rv.RelevantWiring("rot", "add", "A speed setting raised by q makes the rotation rate of the rotor rot + q, and the power "
                                             "grows as the square of the rate."),
    scene_clause="A magnetic stirrer stands on the bench beside the cylinder. The oil is Newtonian and moves only in circles about the "
                 "axis; it stays at one temperature, and its viscosity stays constant. The rate given for the rotor is the rate at "
                 "which it first runs.",
    scene_object_rationale="A magnetic stirrer shares no oil, no cylinder and no motor with the rotor, so the rotor that is turned and "
                           "the oil around it are as the problem states.",
    notes=_note("S238", "scene clause states the Newtonian oil and the purely circular flow and that the given rate is the first rate; "
                        "R is a raised speed setting; the C shear stress carries the factor r; K is the limit of purely circular flow."))
CHANGES["S238"] = (
    ("gpt high insufficient_boundary_condition: R1 does not say whether 120 rpm is before or after the increase",
     "Scene clause 'The rate given for the rotor is the rate at which it first runs.'; R1 'The speed setting of the rotor was raised by "
     "75 rpm before the power was measured.' (old: 'A motor had added 75 rpm to the rotation rate of the rotor before the power was "
     "measured')."),
    ("gpt high missing_assumption: the Newtonian model and the purely azimuthal flow are not in the rendered problem",
     "Scene clause 'The oil is Newtonian and moves only in circles about the axis.'"),
    ("gpt high inconsistent_units: C shear stress tau = q nu d(omega)/dr", "Relation now 'tau = q nu r d(omega)/dr'."),
    ("gpt high other: K 'free of vortices' presented as a laminarity threshold",
     "K phrasings now 'stays purely circular up to a rotation rate of' / 'remains free of vortices up to'; quantity phrase and k_out "
     "reason speak of purely circular flow."),
    ("rated artificial D0/N0/R0/R1/N1 ('A motor adds 75 rpm to the rotation rate of the stirrer/rotor')",
     "'The speed setting of the stirrer is raised by 75 rpm.' / '... of the rotor is raised by 75 rpm.'; N fill 'a small amount'."),
)

# --- S239 --------------------------------------------------------------------------------------------------------------------------
S239_P0 = _pair("S239", 0, frame="Polishing then thins {relation} by {value} {unit}.")
_drop_k("S239", "Finite coherence lowers the visibility of the retarder fringes continuously with the ratio of the path difference to "
                "the coherence length, so no sharp regime boundary leaves the answer exactly unchanged; the light is treated as "
                "monochromatic.")
FIXED["S239"] = dataclasses.replace(
    OLD["S239"], conditional=None, pairs=(S239_P0, OLD["S239"].pairs[1]),
    scene_clause="A glass lens lies on the polishing bench beside the plate. The thickness given for the plate is its thickness before "
                 "any polishing. Reflections at the surfaces of the plate are negligible.",
    notes=_note("S239", "scene clause: the stated thickness is the thickness before polishing; R0/D0 'Polishing then thins ...'; K "
                        "removed (see NO_K)."))
CHANGES["S239"] = (
    ("gpt high insufficient_boundary_condition: 24 um is not identified as the thickness before polishing",
     "Scene clause 'The thickness given for the plate is its thickness before any polishing.'; R0 'Polishing then thins the plate by "
     "6.5 um.'"),
    ("gpt high hidden_coupling: finite coherence changes the visibility continuously, exact independence does not follow",
     "K removed; NO_K['S239'] gives the reason."),
    ("rated slightly_artificial R0 (abrupt thinning after the thickness is given); claude low on R0 timing",
     "'Polishing then thins the plate by 6.5 um.' with the scene clause; D0 'Polishing then thins the lens by 6.5 um.'"),
)

# --- S240 --------------------------------------------------------------------------------------------------------------------------
S240_P0 = _pair("S240", 0, d_attach="the beaker",
                d_rationale="Replacing the liquid in the beaker changes the contents of the beaker only; the liquid in the siphon and so "
                            "its pressure at the highest point are those of the stated liquid.")
S240_P1 = _pair("S240", 1, frame="The liquid in the siphon was replaced by one of {value} {unit} density {relation}.")
FIXED["S240"] = dataclasses.replace(
    OLD["S240"], pairs=(S240_P0, S240_P1),
    scene_clause="A beaker of water stands on the bench beside the reservoir, and no liquid passes between it and the siphon or the "
                 "reservoir. The reservoir holds the same liquid as the siphon, and the density given is that of the liquid first put "
                 "in them.",
    scene_object_rationale="A beaker of water on the bench shares no tube, no liquid and no outlet with the siphon, so the pressure in "
                           "the siphon is fixed by its own heights and its own liquid.",
    scene_refs=("beaker",),
    notes=_note("S240", "the co-present object is a beaker; the given density is that of the liquid first put in the siphon and the "
                        "reservoir, so R1 reads as a replacement of it; R1 in the simple past."))
CHANGES["S240"] = (
    ("rated artificial R1 'The liquid in the siphon had been replaced by one of 1180 kg/m3 density before the flow began' (contradicts "
     "the stated 1000 kg/m3)",
     "Scene clause 'the density given is that of the liquid first put in them'; R1 'The liquid in the siphon was replaced by one of "
     "1180 kg/m3 density before the flow began.'"),
    ("rated artificial D0/N0 (replacing the contents of a garden water butt)",
     "D0 'The liquid in the beaker is replaced by one of 1180 kg/m3 density.' (a beaker of water on the bench)."),
    ("claude low: the reservoir liquid might not be replaced", "Scene clause 'The reservoir holds the same liquid as the siphon'."),
)


# Main-session review (J15.1-059): the only repair the build admits needs a spring tide 9-47 m above usual (physically absurd;
# real spring tides are a few metres), and smaller values fail the value-distinctness and foil checks.
DROPPED["S237"] = ("no physically plausible R quantity: the added water height must be 9-47 m to pass the value and foil checks, far "
                   "beyond any tide, and dredging (the v1 R) leaves a persistent state for the earlier-survey D")

ROLE_SPECS: dict[str, r2.RoleSpecV2] = {sid: FIXED.get(sid, spec) for sid, spec in OLD.items() if sid not in DROPPED}
SPECS = ROLE_SPECS
INFEASIBLE: dict[str, str] = {**dict(SRC.INFEASIBLE), **{sid: f"repair round 1: {why}" for sid, why in DROPPED.items()}}
STRUCTURE_FACTORIES = {**SRC.STRUCTURE_FACTORIES, **STRUCTURE_OVERRIDES}


def structure(structure_id: str) -> gr.Structure:
    """The structure (repaired factory if any) with the repaired spec's scene clause appended to its base context."""

    return r2.with_scene(STRUCTURE_FACTORIES[structure_id](), ROLE_SPECS[structure_id].scene_clause)
