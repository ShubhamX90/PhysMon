"""M250 phase 2, batch waves: v2.1 role-by-value specifications for the new structures S231 to S240 (plan revision v2.2, section G;
admission standard 3.2, 6.1, 6.2, 6.3).

Every spec follows `roles_m0v21` (the v2.1 design) on instance 0 of the new structure:

* one R/D quantity with three study values and two held-out values; a co-present D (pair 0, `other_object_same_scene`) whose object is
  introduced by a number-free scene clause in the base context of every cell, is of a different type from the target object, and
  receives an ordinary, purposeful action (rules 3 and 4 of the 2026-11-15 panel review), and a same-object D (pair 1,
  `same_object_other_event`: history in an earlier run, never a change applied and then reversed) whose R twin names the moment of the
  question ("before the echo was recorded": rules 1 and 5), the same frame, numeral and unit within a pair, an attachment-only
  difference, word counts within three, marker- and consequence-free wording, value hygiene;
* a C quantity where the physics supports a real cancellation (S231, S233, S234, S235, S236, S238, S240);
* a K quantity where a genuine regime condition of the physics itself exists (S232, S234, S235, S236, S237, S238, S239, S240); the
  kind of regime is recorded in `K_KINDS`. K_out is recorded as infeasible with the reason in every case.

`INFEASIBLE` holds the structures that cannot honestly carry the design (none in this batch); `NO_C` and `NO_K` hold the reason a
structure has no C or K quantity, so that an absence is a judgement on record and not an omission.
"""

from __future__ import annotations

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import lib_m250_waves as lw
from physmon.benchmark.v2 import rolevalue as rv
from physmon.benchmark.v2 import rolevalue_v2 as r2

P = rv.Phrasing
Pair = r2.PhrasePair
CO = r2.D_KIND_CO_PRESENT
EVENT = r2.D_KIND_OTHER_EVENT
V21 = r2.VERSION_V21


def _spec(sid: str, **fields) -> r2.RoleSpecV2:
    return r2.RoleSpecV2(structure_id=sid, version=V21, author="agent (M250 phase 2, waves)", **fields)


def _ko(reason: str) -> r2.KOut:
    return r2.KOut(False, reason)


# --- S231 --------------------------------------------------------------------------------------------------------------------------

S231_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the distance of the wall from the loudspeaker when the tone begins", "length", "m", (45.0, 90.0, 140.0),
        "The wall {relation} {value} {unit} from the loudspeaker when the tone begins.", (P("c0", "stands"), P("c1", "is")),
        "1/(((q + c/f)*(c - v)/(c + v) + q)/c - (q*(c - v)/(c + v) + q)/c) - f",
        ("crest n meets the wall at t = (q + c n / f) / (c + v)", "the echo of that crest reaches the loudspeaker at T_n = (t (c - v) + q) / c",
         "echo frequency = 1 / (T_(n+1) - T_n)"),
        "2*f*v/(c - v)*(1 + q*f/(50*c))", nonnumeric_fill="a known distance"),
    "uncommon", "That the beat of a tone with its echo from a wall in uniform approach does not depend on how far away the wall is "
                "is true but is not a stated textbook fact.", (60.0, 120.0))

S231 = _spec(
    "S231", quantity_phrase="an extra speed", quantity_type="speed", unit="m/s", values=(0.7, 1.4, 2.2), heldout_values=(0.9, 1.8),
    relevant=rv.RelevantWiring("v", "add", "A motor that adds q to the speed of the wall makes it v + q, and the beat is "
                                           "2 f (v + q) / (c - v - q)."),
    cancelling=S231_C,
    scene_clause="A conveyor belt carries parcels along the floor beside the loudspeaker; it stirs no air, which stays still throughout.",
    scene_object_rationale="A conveyor belt on the floor is not the large flat wall that reflects the tone, so the tone, the echo "
                           "that the microphone records and the beat are those of the wall alone.",
    scene_refs=("conveyor belt",), target_terms=("the wall",),
    pairs=(
        Pair("p0", "A motor adds {value} {unit} to the speed of {relation}.", "the wall", "the conveyor belt", CO,
             "A motor that speeds up a conveyor belt acts on the belt only; the speed of the wall that reflects the tone, and so the "
             "echo and the beat, are the stated ones.", ("at rest in still air", "constant speed"), "a little",
             before_context_reason="The R sentence refers to 'the wall' before the context introduces it, and a speed to be added "
                                   "to has not yet been stated."),
        Pair("p1", "A motor had added {value} {unit} to the speed of the wall {relation}.", "before the echo was recorded",
             "for an earlier run only", EVENT,
             "The motor changed the speed of the wall in an earlier run, which is over; in the stated recording the wall moves at "
             "the stated constant speed.", ("at rest in still air", "constant speed"), "a little"),
    ),
    notes="M250 phase 2: R is an extra wall speed; C is the distance of the wall at the start of the tone (cancels through the "
          "difference of two echo arrival times); no K (see NO_K).")

# --- S232 --------------------------------------------------------------------------------------------------------------------------

S232_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the depth of the water in the tank", "length", "cm", (40.0, 55.0, 75.0),
        "The depth of the water in the tank {relation} {value} {unit}.", (P("k0", "is"), P("k1", "has been measured as")),
        "k*q > 6", "sqrt(g*q)", 1.0, nonnumeric_fill="a known depth"),
    _ko("The problem states that the water is much deeper than the wavelength; a depth comparable with the wavelength would contradict "
        "that statement, and the dispersion relation of deep water, on which the question rests, would no longer apply."),
    (48.0, 66.0))

S232 = _spec(
    "S232", quantity_phrase="a reduction of the surface tension", quantity_type="surface_tension", unit="N/m",
    values=(0.009, 0.015, 0.023), heldout_values=(0.012, 0.019),
    relevant=rv.RelevantWiring("sigma", "subtract", "Detergent that reduces the surface tension by q makes it sigma - q, which changes "
                                                    "the term sigma k^3 / rho of the dispersion relation."),
    conditional=S232_K,
    scene_clause="A washing-up bowl of water stands on the bench beside the tank, and no tube or channel joins them.",
    scene_object_rationale="A washing-up bowl is a vessel of its own with its own water; what is done to the water in the bowl does "
                           "not reach the water of the tank, so the ripples of the tank keep their stated properties.",
    scene_refs=("washing-up bowl",), target_terms=("the tank",),
    pairs=(
        Pair("p0", "Detergent reduces the surface tension of {relation} by {value} {unit}.", "the water in the tank",
             "the water in the washing-up bowl", CO,
             "Detergent in the water of the washing-up bowl changes the surface tension of that water only; the water of the tank, "
             "and so its ripples, keep the stated surface tension.", ("much deeper than the wavelength", "viscosity is negligible"),
             "a little", before_context_reason="The R sentence refers to 'the tank' and to the surface tension of its water before the "
                                                "context introduces either."),
        Pair("p1", "Detergent had reduced the surface tension of the water by {value} {unit} {relation}.", "before the ripples were made",
             "for an earlier run only", EVENT,
             "Detergent was in the water in an earlier run, which is over; the water of the stated run has the stated surface "
             "tension when the ripples are made.", ("much deeper than the wavelength", "viscosity is negligible"), "a little"),
    ),
    notes="M250 phase 2: R is a detergent reduction of the surface tension; K is the water depth (deep-water regime); no C (see NO_C).")

# --- S233 --------------------------------------------------------------------------------------------------------------------------

S233_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the cross-section area of the beam", "area", "mm^2", (2.4, 5.5, 9.0), "The beam {relation} {value} {unit}.",
        (P("c0", "has a cross-sectional area of"), P("c1", "covers an area of")),
        "(P0/q*(1 - ((n*cos(theta) - cos(thetat))/(n*cos(theta) + cos(thetat)))**2))*q",
        ("intensity of the incident beam I0 = P0 / q", "transmitted intensity I_t = I0 (1 - R) per unit area of the beam",
         "transmitted power = I_t q"),
        "(P0/q*(1 - R))*q*cos(thetat)/cos(theta)", nonnumeric_fill="a known area"),
    "standard", "That a power fraction does not depend on the cross-section area of the beam follows from writing power as intensity "
                "times area; it is taught but not a headline fact.", (3.6, 7.2))

S233 = _spec(
    "S233", quantity_phrase="an extra amount of power", quantity_type="power", unit="mW", values=(1.7, 3.4, 6.2), heldout_values=(2.3, 4.6),
    relevant=rv.RelevantWiring("P0", "add", "A booster that adds q to the power of the beam makes the incident power P0 + q, and the "
                                            "transmitted power is (P0 + q) (1 - R)."),
    cancelling=S233_C,
    scene_clause="A laser pointer lies on the bench beside the block and shines away from it. The beam is narrow and parallel.",
    scene_object_rationale="A laser pointer lying on the bench sends no light onto the block, so the power that strikes and enters "
                           "the block is that of the beam alone.",
    scene_refs=("laser pointer",), target_terms=("the beam",),
    pairs=(
        Pair("p0", "A booster adds {value} {unit} to the power of {relation}.", "the beam", "the laser pointer", CO,
             "A booster that raises the power of a laser pointer acts on the pointer only; the power of the beam that strikes the "
             "glass is the stated one.", ("polarised with its electric field in the plane of incidence", "does not absorb light"),
             "a little", before_context_reason="The R sentence refers to 'the beam' and to its power before the context introduces them."),
        Pair("p1", "A booster had added {value} {unit} to the power of the beam {relation}.", "before it struck the glass",
             "for an earlier run only", EVENT,
             "The booster added power to the beam in an earlier run, which is over; in the stated run the beam that strikes the glass "
             "has the stated power.", ("polarised with its electric field in the plane of incidence", "does not absorb light"),
             "a little"),
    ),
    notes="M250 phase 2: R is extra beam power; C is the beam cross-section (power as intensity times area); no K (see NO_K).")

# --- S234 --------------------------------------------------------------------------------------------------------------------------

S234_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the diameter of the rod", "length", "cm", (1.1, 2.5, 2.9), "The rod {relation} {value} {unit}.",
        (P("c0", "has a diameter of"), P("c1", "is drawn to a diameter of")),
        "n*(L*tan(thr)/q)*(q/sin(thr))/c",
        ("number of legs of the zigzag N = L tan(theta_r) / d", "length of one leg = d / sin(theta_r)", "total path = N times one leg"),
        "n*(L/cos(thr) + 2*q/sin(thr))/c", nonnumeric_fill="a known diameter"),
    "uncommon", "That the transit time of a ray in a rod does not depend on the rod's width is true but rarely stated.", (1.5, 2.4))

S234_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the refractive index of the liquid on the sides of the rod", "refractive_index", "1", (1.33, 1.37, 1.47),
        "The sides of the rod {relation} {value}.",
        (P("k0", "are in contact with oil of refractive index"), P("k1", "are coated with a liquid of refractive index")),
        "n*cos(thr) > q", "q*ell/c", 1.9, nonnumeric_fill="a known refractive index"),
    _ko("The problem states that the pulse is totally internally reflected at the sides; an oil index above n cos(theta_r) would let "
        "the light leave the rod, contradicting that statement, and the transit time to the far end would no longer be defined."),
    (1.35, 1.42))

S234 = _spec(
    "S234", quantity_phrase="an extension piece", quantity_type="length", unit="m", values=(0.7, 1.3, 2.2), heldout_values=(0.9, 1.6),
    relevant=rv.RelevantWiring("L", "add", "A glass coupler that adds q of the same glass to the length of the rod makes it L + q, and the "
                                           "transit time is n (L + q) / (c cos(theta_r))."),
    cancelling=S234_C, conditional=S234_K,
    scene_clause="A coil of optical cable lies on the bench beside the rod, and no light passes between them. The glass is not dispersive.",
    scene_object_rationale="A coil of optical cable on the bench carries no part of the pulse, so the pulse in the rod travels the length "
                           "and the glass that the problem states.",
    scene_refs=("optical cable",), target_terms=("the rod",),
    pairs=(
        Pair("p0", "A glass coupler adds {value} {unit} to the length of {relation}.", "the rod", "the optical cable", CO,
             "A coupler that lengthens the optical cable changes the cable only; the length of the rod that carries the pulse is "
             "the stated one.", ("totally internally reflected", "in air"), "a little",
             before_context_reason="The R sentence refers to 'the rod' before the context introduces any rod."),
        Pair("p1", "A glass coupler had added {value} {unit} to the length of the rod {relation}.", "before the pulse was sent",
             "for an earlier run only", EVENT,
             "The coupler lengthened the rod in an earlier run, which is over; in the stated run the pulse crosses a rod of the "
             "stated length.", ("totally internally reflected", "in air"), "a little"),
    ),
    notes="M250 phase 2: R is an extension of the rod; C is the rod's diameter (the zigzag count times the leg length); K is the "
          "refractive index of the liquid at the sides (total internal reflection persists).")

# --- S235 --------------------------------------------------------------------------------------------------------------------------

S235_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the radius of the cylinder", "length", "cm", (2.5, 4.5, 7.0), "The cylinder {relation} {value} {unit}.",
        (P("c0", "has a radius of"), P("c1", "is machined to a radius of")),
        "2*pi*sqrt(rho_b*(pi*q**2*h)/(rho_l*g*pi*q**2))",
        ("mass of the cylinder m = rho_b pi q^2 h", "buoyant stiffness k = rho_l g pi q^2", "T = 2 pi sqrt(m / k)"),
        "2*pi*sqrt((rho_b*pi*q**2*h + 2*pi*q**3*rho_l/3)/(rho_l*g*pi*q**2))", nonnumeric_fill="a known radius"),
    "uncommon", "That the bobbing period of a floating cylinder does not depend on its cross-section is true (mass and buoyant "
                "stiffness both scale with the area) but is not a headline fact.", (3.5, 5.5))

S235_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the distance below equilibrium from which the cylinder is released", "length", "cm", (1.1, 3.2, 3.8),
        "The cylinder is {relation} {value} {unit} below its equilibrium position.",
        (P("k0", "released from rest"), P("k1", "let go from rest")),
        "Min(d0, h - d0) > q", "2*pi*sqrt((d0 + q)/g)", 90.0, nonnumeric_fill="a known distance"),
    _ko("The problem states that the cylinder floats partly submerged and is pushed down slightly; a release from deeper than the "
        "submerged length would plunge it below the surface, contradicting 'slightly' and the partly submerged float."),
    (1.7, 2.9))

S235 = _spec(
    "S235", quantity_phrase="an extra length of wood", quantity_type="length", unit="cm", values=(3.5, 9.5, 14.0),
    heldout_values=(5.5, 12.5),
    relevant=rv.RelevantWiring("h", "add", "A length q of the same wood glued on top of the cylinder makes its length h + q at the same "
                                           "density, so the submerged length is rho_b (h + q) / rho_l."),
    cancelling=S235_C, conditional=S235_K,
    scene_clause="A small wooden raft also floats in the tank, far from the cylinder. The liquid is otherwise at rest.",
    scene_object_rationale="A small raft floating in the large tank has its own draught and its own motion; it does not touch the "
                           "cylinder, so the cylinder's period is fixed by its own density and length.",
    scene_refs=("raft",), target_terms=("the cylinder",),
    pairs=(
        Pair("p0", "A {value} {unit} length of the same wood is glued on top of {relation}.", "the cylinder", "the raft", CO,
             "Wood glued on top of the raft lengthens the raft only; the density and the length of the cylinder that is pushed "
             "down are the stated ones.", ("floats upright", "Neglect drag"), "short",
             before_context_reason="The R sentence refers to 'the cylinder' and to its wood before the context introduces them."),
        Pair("p1", "A {value} {unit} length of the same wood had been glued on top of the cylinder {relation}.",
             "before it was pushed down", "for an earlier run only", EVENT,
             "The extra wood was on the cylinder in an earlier run, which is over; in the stated run the cylinder that is pushed "
             "down has the stated length.", ("floats upright", "Neglect drag"), "short"),
    ),
    notes="M250 phase 2: R is an extra length of the same wood; C is the radius (mass and stiffness scale together); K is the release "
          "distance (the cylinder stays partly submerged and partly out).")

# --- S236 --------------------------------------------------------------------------------------------------------------------------

S236_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the density of the air", "density", "kg/m^3", (0.8, 1.6, 2.1), "The air in the flask {relation} {value} {unit}.",
        (P("c0", "has a density of"), P("c1", "is at a density of")),
        "(1/(2*pi))*sqrt((q*c**2*A**2/V)/(q*A*Leff))",
        ("mass of the neck plug m = q A Leff", "adiabatic stiffness k = q c^2 A^2 / V", "f = (1 / 2 pi) sqrt(k / m)"),
        "(1/(2*pi))*sqrt(1.4*101325*A/(q*V*Leff))", nonnumeric_fill="a known density"),
    "uncommon", "That the resonance of a Helmholtz resonator does not depend on the density of the air (mass and stiffness both "
                "scale with it) is true but not a headline fact.", (1.1, 1.9))

S236_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the longest dimension of the flask", "length", "cm", (16.5, 20.5, 24.0),
        "The longest dimension of the flask {relation} {value} {unit}.", (P("k0", "is"), P("k1", "has been measured as")),
        "6*q*f < c", "c/(4*q)", 300.0, nonnumeric_fill="a known length"),
    _ko("The problem states that the flask is much smaller than the wavelength of its sound; a flask as long as a sixth of the "
        "wavelength would contradict that statement, and the plug-and-cushion model on which the question rests would fail."),
    (18.5, 22.0))

S236 = _spec(
    "S236", quantity_phrase="an extra glass tube", quantity_type="length", unit="cm", values=(1.7, 3.2, 6.3), heldout_values=(2.6, 4.7),
    relevant=rv.RelevantWiring("l", "add", "A glass tube of length q and the same bore attached to the end of the neck makes the neck "
                                           "length l + q at the same radius."),
    cancelling=S236_C, conditional=S236_K,
    scene_clause="A laboratory funnel stands in a clamp beside the flask, clear of the flask and its neck. The walls of the flask are rigid.",
    scene_object_rationale="A funnel in a clamp is a vessel of its own with its own stem; a tube attached to the stem leaves the neck, "
                           "the volume and the air of the flask as the problem states.",
    scene_refs=("funnel",), target_terms=("the flask",),
    pairs=(
        Pair("p0", "A {value} {unit} glass tube of the same bore is attached to the {relation}.", "neck of the flask",
             "stem of the funnel", CO,
             "A tube attached to the stem of the funnel lengthens the stem only; the neck of the flask that resonates has the "
             "stated length.", ("rigid plug", "adiabatically"), "short",
             before_context_reason="The R sentence refers to the neck of the flask before the context introduces the flask."),
        Pair("p1", "A {value} {unit} glass tube of the same bore had been attached to the neck of the flask {relation}.",
             "before its resonance was measured", "for an earlier run only", EVENT,
             "The tube was on the neck in an earlier run, which is over; in the stated measurement the neck has the stated length.",
             ("rigid plug", "adiabatically"), "short"),
    ),
    notes="M250 phase 2: R is an extra tube on the neck; C is the density of the air (mass and stiffness scale together); K is the "
          "longest dimension of the flask (lumped regime).")

# --- S237 --------------------------------------------------------------------------------------------------------------------------

S237_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the wavelength of the tsunami", "length", "km", (110.0, 170.0, 300.0), "The wavelength of the tsunami {relation} {value} {unit}.",
        (P("k0", "is"), P("k1", "has been measured as")),
        "q > 20*h1", "D/sqrt(g*q/(2*pi))", 2.0, nonnumeric_fill="a known length"),
    _ko("The problem states that the wavelength is very long and that the wave is a shallow-water wave; a wavelength comparable with "
        "the depth would contradict that statement and the speed sqrt(g h), on which the question rests, would not apply."),
    (140.0, 210.0))

S237 = _spec(
    "S237", quantity_phrase="a dredged depth", quantity_type="length", unit="m", values=(9.0, 33.0, 47.0), heldout_values=(14.0, 38.0),
    relevant=rv.RelevantWiring("h2", "add", "Dredging that adds q to the depth at the landward end makes it h2 + q, which changes the "
                                            "wave speed there."),
    conditional=S237_K,
    scene_clause="A fishing harbour lies along the same coast, well away from the sloping seabed. The sea is otherwise still.",
    scene_object_rationale="A fishing harbour has its own water and its own depths; dredging it leaves the slope that the tsunami "
                           "crosses unchanged, so the depths of the slope are the stated ones.",
    scene_refs=("harbour",), target_terms=("the slope",),
    pairs=(
        Pair("p0", "Dredging adds {value} {unit} to the depth of {relation}.", "the sea at the landward end of the slope",
             "the water at the landward end of the harbour", CO,
             "Dredging in the harbour changes the depth of the harbour only; the depths of the slope that the tsunami crosses are "
             "the stated ones.", ("shallow-water wave", "neglect its height"), "a little",
             before_context_reason="The R sentence refers to 'the slope' before the context introduces it."),
        Pair("p1", "{relation}, dredging added {value} {unit} to the depth at the landward end of the slope.",
             "Before the tsunami arrived", "For an earlier survey only", EVENT,
             "The dredging belongs to an earlier survey, which is over; on the slope that the tsunami crosses the depths are the "
             "stated ones.", ("shallow-water wave", "neglect its height"), "a little"),
    ),
    notes="M250 phase 2: R is a dredged depth at the landward end; K is the wavelength (long-wave regime); no C (see NO_C).")

# --- S238 --------------------------------------------------------------------------------------------------------------------------

S238_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the density of the oil", "density", "kg/m^3", (780.0, 860.0, 930.0), "The oil {relation} {value} {unit}.",
        (P("c0", "has a density of"), P("c1", "is a mineral oil of density")),
        "omega*(4*pi*(q*(eta/q))*L*omega*R1**2*R2**2/(R2**2 - R1**2))",
        ("kinematic viscosity nu = eta / q", "shear stress tau = q nu d(omega)/dr", "torque T = 4 pi (q nu) L omega R1^2 R2^2 / (R2^2 - R1^2)"),
        "P*q/1000", nonnumeric_fill="a known density"),
    "uncommon", "That the viscous torque in steady laminar Couette flow does not depend on the density of the oil is true (inertia "
                "plays no part) but not a headline fact.", (820.0, 900.0))

S238_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the rotation rate above which the flow is no longer laminar", "angular_frequency", "rpm", (3500.0, 6500.0, 9000.0),
        "The oil flow {relation} {value} {unit}.",
        (P("k0", "stays laminar up to a rotation rate of"), P("k1", "remains free of vortices up to")),
        "rot < q", "P*(q/rot)**2", 5.0, nonnumeric_fill="a known rotation rate"),
    _ko("The problem states that the flow is steady and laminar; a rotation rate above the onset of vortices would contradict that "
        "statement, and the laminar torque on which the question rests would not apply."),
    (5200.0, 8000.0))

S238 = _spec(
    "S238", quantity_phrase="an extra rotation rate", quantity_type="angular_frequency", unit="rpm", values=(35.0, 75.0, 160.0),
    heldout_values=(50.0, 110.0),
    relevant=rv.RelevantWiring("rot", "add", "A motor that adds q to the rotation rate of the rotor makes it rot + q, and the power "
                                             "grows as the square of the rate."),
    cancelling=S238_C, conditional=S238_K,
    scene_clause="A magnetic stirrer stands on the bench beside the cylinder. The oil stays at one temperature, and its viscosity stays constant.",
    scene_object_rationale="A magnetic stirrer shares no oil, no cylinder and no motor with the rotor, so the rotor that is turned and "
                           "the oil around it are as the problem states.",
    scene_refs=("stirrer",), target_terms=("the rotor",),
    pairs=(
        Pair("p0", "A motor adds {value} {unit} to the rotation rate of {relation}.", "the rotor", "the stirrer", CO,
             "A motor that speeds up the stirrer acts on the stirrer only; the rotation rate of the rotor in the question is the "
             "stated one.", ("steady and laminar", "end effects are negligible"), "a little",
             before_context_reason="The R sentence refers to 'the rotor' and to its rotation rate before the context introduces them."),
        Pair("p1", "A motor had added {value} {unit} to the rotation rate of the rotor {relation}.", "before the power was measured",
             "for an earlier run only", EVENT,
             "The motor changed the rotation rate in an earlier run, which is over; in the stated measurement the rotor turns at "
             "the stated rate.", ("steady and laminar", "end effects are negligible"), "a little"),
    ),
    notes="M250 phase 2: R is an extra rotation rate; C is the density of the oil (kinematic viscosity times density); K is the onset "
          "rate of vortices (laminar regime).")

# --- S239 --------------------------------------------------------------------------------------------------------------------------

S239_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the coherence length of the light", "length", "μm", (120.0, 350.0, 900.0),
        "The coherence length of the light {relation} {value} {unit}.", (P("k0", "is"), P("k1", "has been measured as")),
        "q > 10*dn*d", "P0*sin(2*alpha)**2/2", 0.5, nonnumeric_fill="a known length"),
    _ko("The problem treats the plate as giving a definite phase difference between its two axes; a coherence length shorter than "
        "the path difference dn d would make the two components incoherent, and the question would need the spectrum of the light."),
    (200.0, 500.0))

S239 = _spec(
    "S239", quantity_phrase="a thinning of the plate", quantity_type="length", unit="μm", values=(3.5, 6.5, 11.0),
    heldout_values=(4.5, 8.5),
    relevant=rv.RelevantWiring("d", "subtract", "Polishing that thins the plate by q makes its thickness d - q at the same "
                                                "birefringence."),
    conditional=S239_K,
    scene_clause="A glass lens lies on the polishing bench beside the plate. Reflections at the surfaces of the plate are negligible.",
    scene_object_rationale="A glass lens on the polishing bench is not in the path of the light, so the light crosses only the plate "
                           "and its thickness and axes are the stated ones.",
    scene_refs=("lens",), target_terms=("the plate",),
    pairs=(
        Pair("p0", "Polishing thins {relation} by {value} {unit}.", "the plate", "the lens", CO,
             "Polishing thins the lens only; the plate that the light crosses has the stated thickness.",
             ("thin birefringent plate", "does not absorb light"), "a little",
             before_context_reason="The R sentence refers to 'the plate' before the context introduces it."),
        Pair("p1", "Polishing had thinned the plate by {value} {unit} {relation}.", "before the light was sent through it",
             "in an earlier run", EVENT,
             "The plate was measured in an earlier run, which is over; the measurement leaves the plate as it was, so the light "
             "crosses a plate of the stated thickness.", ("thin birefringent plate", "does not absorb light"), "a small margin",
             d_frame="A micrometer had measured the thickness of the plate to within {value} {unit} {relation}.",
             frame_mismatch_reason="The R event is a thinning, which leaves a lasting change; the D event is a measurement of the same "
                                   "plate that leaves none, so the two cannot share one frame."),
    ),
    notes="M250 phase 2: R is a thinning of the plate by polishing; K is the coherence length of the light; no C (see NO_C).")

# --- S240 --------------------------------------------------------------------------------------------------------------------------

S240_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the bore of the tube", "length", "mm", (9.0, 16.0, 24.0), "The tube {relation} {value} {unit}.",
        (P("c0", "has an inner diameter of"), P("c1", "has a bore of")),
        "p0 - rho*g*H - rho*(v*(pi*q**2/4)/(pi*q**2/4))**2/2",
        ("flow rate at the outlet Q = (pi q^2 / 4) v", "speed at the highest point = Q / (pi q^2 / 4)", "dynamic pressure rho v^2 / 2"),
        "p0 - rho*g*H", nonnumeric_fill="a known diameter"),
    "standard", "That the speed at the highest point of a uniform tube equals the outlet speed, whatever the bore, follows from "
                "continuity and is taught with the siphon.", (12.0, 20.0))

S240_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the vapour pressure of the liquid", "pressure", "kPa", (3.2, 12.0, 31.0), "The liquid {relation} {value} {unit}.",
        (P("k0", "vaporises at an absolute pressure of"), P("k1", "begins to boil at an absolute pressure of")),
        "pc > q", "q", 110.0, nonnumeric_fill="a known pressure"),
    _ko("The problem states that the liquid flows steadily through a tube that stays full; if the pressure at the highest point fell "
        "to the vapour pressure the liquid would boil there and the column would break, contradicting the stated flow."),
    (8.3, 19.9))

S240 = _spec(
    "S240", quantity_phrase="another liquid", quantity_type="density", unit="kg/m^3", values=(760.0, 1180.0, 1340.0),
    heldout_values=(810.0, 1260.0),
    relevant=rv.RelevantWiring("rho", "replace", "Replacing the liquid by one of density q makes the density rho = q, which changes "
                                                 "both the hydrostatic term and the dynamic term at the highest point."),
    cancelling=S240_C, conditional=S240_K,
    scene_clause="A garden hose runs from a water butt along the ground beside the reservoir, and no liquid passes between the hose and the siphon or the reservoir.",
    scene_object_rationale="A garden hose from a water butt shares no tube, no liquid and no outlet with the siphon, so the pressure "
                           "in the siphon is fixed by its own heights and its own liquid.",
    scene_refs=("water butt",), target_terms=("the siphon",),
    pairs=(
        Pair("p0", "The liquid in {relation} is replaced by one of {value} {unit} density.", "the siphon", "the water butt", CO,
             "Replacing the liquid in the water butt changes the contents of the butt only; the liquid in the siphon and so its "
             "pressure at the highest point are those of the stated liquid.", ("without friction", "incompressible"), "different",
             before_context_reason="The R sentence refers to 'the siphon' and to its liquid before the context introduces them."),
        Pair("p1", "The liquid in the siphon had been replaced by one of {value} {unit} density {relation}.",
             "before the flow began", "for an earlier run only", EVENT,
             "The liquid was replaced in an earlier run, which is over; in the stated flow the siphon carries the stated liquid.",
             ("without friction", "incompressible"), "different"),
    ),
    notes="M250 phase 2: R is another liquid in the siphon (density replaced; wiring the height instead would be confounded because "
          "the answer is symmetric in H and h); C is the bore of the tube (continuity); K is the vapour pressure of the liquid "
          "(phase state at the highest point).")


SPECS: dict[str, r2.RoleSpecV2] = {s.structure_id: s for s in (S231, S232, S233, S234, S235, S236, S237, S238, S239, S240)}
ROLE_SPECS = SPECS

STRUCTURE_FACTORIES = {f().structure_id: f for f in lw.ALL}

INFEASIBLE: dict[str, str] = {}

NO_C: dict[str, str] = {
    "S232": "The ripple dispersion relation takes only the wavelength, the surface tension, the density and g; no further quantity of "
            "the system enters an intermediate relation and then leaves it.",
    "S237": "The crossing time depends only on D, h1, h2 and g; the density of the water cancels in the derivation of sqrt(g h) but "
            "no relation of the structure contains it, so no quantity enters a relation of the graph and then leaves it.",
    "S239": "The two components and the phase difference use only the plate, the wavelength and the axis angle; no further quantity "
            "enters and cancels.",
}

NO_K: dict[str, str] = {
    "S231": "The speed of the wall is below the speed of sound by the stated values, but that is a property of two inputs, not of a "
            "further quantity with a threshold; a wall faster than sound would produce a shock, which the question does not describe.",
    "S233": "The Fresnel formulas hold at every angle of incidence from air into glass; no regime of a further quantity changes the "
            "answer, and total internal reflection cannot occur in this direction.",
}

# The kind of regime that each K quantity expresses (a condition of the physics itself, not an equipment rating).
K_KINDS: dict[str, str] = {
    "S232": "deep-water regime (depth much greater than the wavelength)",
    "S234": "total internal reflection (outer index below n cos theta_r)",
    "S235": "partial submersion (the cylinder stays partly in and partly out of the liquid; small-amplitude regime)",
    "S236": "lumped-element regime (flask much smaller than the wavelength)",
    "S237": "long-wave (shallow-water) regime (wavelength much greater than the depth)",
    "S238": "laminar flow (below the onset of vortices)",
    "S239": "coherence regime (coherence length greater than the path difference)",
    "S240": "phase state (the liquid does not vaporise at the highest point)",
}


def structure(structure_id: str) -> gr.Structure:
    """The new structure with the spec's scene clause appended to its base context."""

    return r2.with_scene(STRUCTURE_FACTORIES[structure_id](), SPECS[structure_id].scene_clause)


# What the H4 trace extractor (`TraceContext.target_phrases` / `target_symbols`) must read as a statement of the target.
TARGET_TERMS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "S231": (("beat frequency between the tone and the echo", "beat frequency"), ("beat", "f_beat", "Δf")),
    "S232": (("group speed of the ripples", "group speed"), ("cg", "c_g", "v_g")),
    "S233": (("power enter the glass", "power that enters the glass", "power"), ("Pt", "P_t", "P")),
    "S234": (("pulse take to travel", "time taken", "long does the pulse take"), ("t", "T")),
    "S235": (("period of the vertical oscillation", "period"), ("T", "T_p")),
    "S236": (("resonance frequency of the flask", "resonance frequency", "frequency"), ("f", "f_0", "f_H")),
    "S237": (("wave crest take to cross this slope", "time", "crest take"), ("t", "T")),
    "S238": (("power is needed to keep the rotor turning", "power needed", "power"), ("P", "P_in")),
    "S239": (("power passes the analyser", "power"), ("P", "P_out")),
    "S240": (("absolute pressure of the liquid at the highest point", "absolute pressure", "pressure"), ("pc", "p_c", "p_top", "p")),
}
