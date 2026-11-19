"""M250 phase 2, batch mech: v2.1 role-by-value specifications for the ten new mechanics structures S201 to S210 (`lib_m250_mech`).

Authority: plan revision v2.2 (sections A and G), the dataset admission standard (2-3, 6) and the wording rules of the M0 v2.1 panel review
(J15.1-038, J15.1-039), applied to every sentence here:

1. a same-object R sentence of pair 1 says that the event changes the very situation the question asks about, with a marker that ties it to
   the asked moment ("Before the driving force was applied, ..."), never a bare past history; the D twin differs only in the attachment;
2. no R sentence contradicts a stated base value or condition: every R quantity is something that is ADDED to the situation (a load, a
   payload, a ring, a damper, an upward acceleration of the support), never a restatement or a change of a stated input;
3. the action on the co-present D object is an ordinary, purposeful action for that object (clay stuck to a trolley, a bag carried by a
   coach, a tag stuck to a dish, a lift accelerating upward), never a pointless precise action on furniture;
4. the co-present object is never of the same type as the target (a trolley, a tug, a crane, a coach, a dish, a lift, a toolbox, a
   grinding wheel, a vase, a door; the targets are a block, a rocket, a bead, skaters, a coin, a tank, the blocks, discs, a rod, a block);
5. the R sentences of pair 1 tie the change to the moment the question asks about ("before the engine was fired", "shortly before the
   collision"), so that the present-tense question and the past-tense sentence have one reading;
6. every answer-determining condition that a careful reader could doubt is stated, number-free, in the base text (no other object exerts a
   force, air resistance negligible, ideal spring and damper, rigid discs, incompressible liquid with negligible evaporation, a motor that
   keeps the hoop's angular speed constant), which is identical in every cell;
7. a pair-1 D event that attaches or adds something to the target (clay, payload, bag, tag, sandbag, ring, damper, a platform set rising) says
   that it was there for an earlier run only ("was stuck to the block for an earlier run only");
8. no D or N sentence contradicts the scene clause or the base: the objects are introduced in a standing or running state and the D action
   is an ordinary event on them.

Every spec has: one R/D quantity with three study values and two held-out values; pair 0 a co-present D whose object is introduced by a
number-free scene clause in the base context of every cell; pair 1 a same-object other event (history in an earlier run, never a change
applied and then reversed); the same frame, numeral and unit within a pair, an attachment-only difference, word counts within three,
marker- and consequence-free wording, value hygiene; a C quantity where a real symbolic cancellation exists (6 of 10; 2 tagged famous);
a K quantity where a genuine regime condition exists (3 of 10, `K_KINDS`). `INFEASIBLE`, `NO_C` and `NO_K` hold the reasons for what is absent.
"""

from __future__ import annotations

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import lib_m250_mech
from physmon.benchmark.v2 import rolevalue as rv
from physmon.benchmark.v2 import rolevalue_v2 as r2

P = rv.Phrasing
Pair = r2.PhrasePair
CO = r2.D_KIND_CO_PRESENT
EVENT = r2.D_KIND_OTHER_EVENT
V21 = r2.VERSION_V21
ONLY_EARLIER_RUN = "for an earlier run only"


def _spec(sid: str, **fields) -> r2.RoleSpecV2:
    return r2.RoleSpecV2(structure_id=sid, version=V21, author="agent (M250 phase 2, mech)", **fields)


# --- S201 ------------------------------------------------------------------------------------------------------------------------

S201_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the phase of the driving force at time zero", "angle", "deg", (75.0, 110.0, 125.0),
        "At time zero the driving force {relation} {value} {unit} into its cycle.",
        (P("c0", "is"), P("c1", "has advanced")),
        "sqrt((F0*cos(q)/(m*den))**2 + (F0*sin(q)/(m*den))**2)",
        ("driving force F0 cos(w t + q)", "steady response x = (F0 / m den) cos(w t + q - delta): its in-phase part F0 cos(q) / (m den) and "
                                          "its quadrature part F0 sin(q) / (m den)", "amplitude = root of the sum of the squares of the two parts"),
        "F0*cos(q)/(m*den)", nonnumeric_fill="a known phase"),
    "standard", "That the steady amplitude does not depend on the phase at which the drive starts is taught with the phase-shifted "
                "response x = A cos(w t + q - delta), but it is not a headline fact.", (105.0, 120.0))

S201_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the extension up to which the spring obeys Hooke's law", "length", "cm", (3.6, 5.4, 11.0), "The spring {relation} {value} {unit}.",
        (P("k0", "obeys Hooke's law for extensions of up to"), P("k1", "follows Hooke's law only up to an extension of")),
        "A < q", "q", 0.5, nonnumeric_fill="a known extension"),
    r2.KOut(False, "Beyond the Hooke limit the force law of the spring is not given, so the steady amplitude would have no definite changed "
                   "value; the base problem states that the spring obeys Hooke's law for the extensions that occur."),
    (4.2, 6.8))

S201 = _spec(
    "S201", quantity_phrase="a lump of clay", quantity_type="mass", unit="g", values=(120.0, 420.0, 900.0), heldout_values=(170.0, 650.0),
    relevant=rv.RelevantWiring("m", "add", "A lump of clay stuck to the block adds to its mass, so the mass in the equation of motion "
                                           "becomes m + q; the natural frequency and the amplitude change."),
    cancelling=S201_C, conditional=S201_K,
    scene_clause="A small trolley stands on another horizontal track beside this one.",
    scene_object_rationale="A trolley on a track beside the first has its own wheels and is not touched by the block, the spring or the "
                           "damper, so the block's equation of motion and its steady oscillation are unchanged.",
    scene_refs=("trolley",), target_terms=("block", "spring", "damper", "driving", "force"),
    pairs=(
        Pair("p0", "A {value} {unit} lump of clay is {relation}.", "stuck to the block", "stuck to the trolley", CO,
             "Clay stuck to the trolley loads the trolley on its own track; the block, its spring and its damper are untouched, so the mass "
             "in the block's equation of motion is the stated one.", ("frictionless track", "transient motion has died out"), "small",
             before_context_reason="The R sentence refers to 'the block' before the context introduces any block, and the scene clause "
                                   "introduces the trolley only after the context."),
        Pair("p1", "A {value} {unit} lump of clay was stuck to the block {relation}.", "before the driving force was applied",
             ONLY_EARLIER_RUN, EVENT,
             "The clay was stuck to the block in an earlier run, which is over; the block of the stated run carries only its stated mass.",
             ("frictionless track", "transient motion has died out"), "small"),
    ),
    notes="M250 phase 2: R is clay stuck to the block (an addition to the mass); C is the phase of the drive; K is the Hooke range of the spring.")

# --- S202 ------------------------------------------------------------------------------------------------------------------------

S202_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the rate at which the engine burns fuel", "mass_rate", "kg/s", (12.0, 27.0, 65.0),
        "The engine {relation} {value} {unit}.",
        (P("c0", "burns fuel at a steady rate of"), P("c1", "consumes fuel at a constant rate of")),
        "u*log(m0/(m0 - q*(mf/q)))",
        ("burn time tb = mf / r", "mass at the end of the burn m0 - r tb", "dv = u r dt / m integrated over the burn time"),
        "u*log(m0/(m0 - q))", nonnumeric_fill="a known rate"),
    "standard", "That the final speed of a rocket in free space depends on the mass ratio and not on how fast the fuel is burned is a "
                "standard consequence of the rocket equation but is not usually stated as a fact.", (18.0, 45.0))

S202 = _spec(
    "S202", quantity_phrase="a payload", quantity_type="mass", unit="kg", values=(50.0, 190.0, 310.0), heldout_values=(70.0, 210.0),
    relevant=rv.RelevantWiring("md", "add", "A payload bolted to the rocket adds to the mass that remains when the fuel has been burned, so "
                                            "the final mass becomes md + q (the base says the empty mass is without payload)."),
    cancelling=S202_C,
    scene_clause="A small service tug floats nearby.",
    scene_object_rationale="A tug floating nearby exerts no force on the rocket and takes no fuel from it, so the rocket's masses and exhaust "
                           "speed are unchanged.",
    scene_refs=("tug",), target_terms=("rocket", "engine", "fuel"),
    pairs=(
        Pair("p0", "A {value} {unit} payload is {relation}.", "bolted to the rocket", "bolted to the tug", CO,
             "A payload bolted to the tug loads the tug only; the rocket keeps its stated empty mass, fuel and exhaust speed.",
             ("empty space", "starts at rest"), "small",
             before_context_reason="The R sentence refers to 'the rocket' before the context introduces it."),
        Pair("p1", "A {value} {unit} payload was bolted to the rocket {relation}.", "before the engine was fired",
             "for an earlier flight only", EVENT,
             "The payload was bolted to the rocket on an earlier flight, which is over; the rocket of the stated flight carries only its "
             "stated empty mass.", ("empty space", "starts at rest"), "small"),
    ),
    notes="M250 phase 2: R is a payload (added to the empty mass); C is the burn rate (cancels in the rocket equation); no K (see NO_K).")

# --- S203 ------------------------------------------------------------------------------------------------------------------------

S203_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the mass of the bead", "mass", "g", (13.0, 26.0, 48.0), "The bead {relation} {value} {unit}.",
        (P("c0", "has a mass of"), P("c1", "has been weighed at")),
        "2*pi/sqrt((q*R**2*Om**2*s0**2)/(q*R**2))",
        ("kinetic energy T = q R^2 (theta'^2 + Om^2 sin^2 theta) / 2", "equation of motion q R^2 theta'' = q R^2 Om^2 sin theta cos theta - q g R sin theta",
         "stiffness over inertia: q R^2 Om^2 sin^2 theta0 / (q R^2)"),
        "(2*pi/sqrt(Om**2*s0**2))*sqrt(1 + q*100)", nonnumeric_fill="a known mass"),
    "famous", "That the motion of a bead on a smooth hoop does not depend on its mass is the same classroom fact as the pendulum's "
              "independence of the bob's mass.", (16.0, 31.0))

S203 = _spec(
    "S203", quantity_phrase="an upward acceleration", quantity_type="acceleration", unit="m/s^2", values=(1.2, 2.1, 5.6),
    heldout_values=(1.7, 3.1),
    relevant=rv.RelevantWiring("g", "add", "A platform that accelerates upward adds its acceleration to the apparent gravity in the frame of the "
                                           "hoop, so g becomes g + q in the equilibrium condition and in the oscillation frequency."),
    cancelling=S203_C,
    scene_clause="A crane stands beside the platform.",
    scene_object_rationale="A crane beside the platform does not touch the platform, the hoop or the bead, so the apparent gravity in the "
                           "frame of the hoop is the stated one.",
    scene_refs=("crane",), target_terms=("platform", "hoop", "bead"),
    pairs=(
        Pair("p0", "The {relation} accelerates upward at a constant rate of {value} {unit} while the bead oscillates.",
             "platform that carries the hoop", "hook of the crane", CO,
             "The hook of a crane is raised with its own acceleration; it is not attached to the platform, so the platform stays at rest and "
             "the apparent gravity in the frame of the hoop is the stated g.", ("without friction", "rests in equilibrium"),
             "a few metres per second squared",
             before_context_reason="The R sentence refers to 'the platform that carries the hoop' and to 'the bead' before the context introduces them."),
        Pair("p1", "The platform carrying the hoop was set rising with a constant upward acceleration of {value} {unit} {relation}.",
             "before the oscillations were observed", ONLY_EARLIER_RUN, EVENT,
             "The platform was set rising in an earlier run, which is over; in the stated run the platform stands still and g is the stated value.",
             ("without friction", "rests in equilibrium"), "a few metres per second squared"),
    ),
    notes="M250 phase 2: R is an upward acceleration of the platform (added to g); C is the mass of the bead (famous); no K (see NO_K).")

# --- S204 ------------------------------------------------------------------------------------------------------------------------

S204 = _spec(
    "S204", quantity_phrase="a bag", quantity_type="mass", unit="kg", values=(3.5, 12.0, 15.0), heldout_values=(9.5, 13.0),
    relevant=rv.RelevantWiring("m1", "add", "A bag picked up by the eastbound skater travels with the skater, so the mass that moves east "
                                            "becomes m1 + q in the momentum balance and in the energies."),
    scene_clause="A coach stands beside the rink.",
    scene_object_rationale="A coach beside the rink is not one of the two colliding skaters and does not touch them, so their masses, speeds "
                           "and the energy of their collision are unchanged.",
    scene_refs=("coach",), target_terms=("skater", "skaters", "ice"),
    pairs=(
        Pair("p0", "A {value} {unit} bag is carried by {relation}.", "the skater moving east", "the coach", CO,
             "A bag carried by the coach adds to the coach's load only; the two colliding skaters keep their stated masses.",
             ("frictionless ice", "hold on to each other"), "small",
             before_context_reason="The R sentence refers to 'the skater moving east' before the context introduces any skater."),
        Pair("p1", "The skater moving east picked up a {value} {unit} bag {relation}.", "shortly before the collision",
             "on an earlier outing only", EVENT,
             "The bag was picked up on an earlier outing, which is over; on the stated outing the skater carries nothing but the stated mass.",
             ("frictionless ice", "hold on to each other"), "small"),
    ),
    notes="M250 phase 2: R is a bag carried by the eastbound skater (added to the mass); no C or K (see NO_C, NO_K).")

# --- S205 ------------------------------------------------------------------------------------------------------------------------

S205_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the largest friction force that the turntable can exert on the coin", "force", "mN", (65.0, 95.0, 135.0),
        "The friction between the coin and the turntable {relation} {value} {unit}.",
        (P("k0", "can reach at most"), P("k1", "holds the coin in place with a force of up to")),
        "f < q", "q", 5.0, nonnumeric_fill="a known force"),
    r2.KOut(False, "If the friction needed were beyond what the turntable can exert, the coin would slip, but the base problem states that "
                   "the coin has not slipped; a coin that slips has no friction force fixed by the stated motion, so the premise would be "
                   "contradicted, not merely changed."),
    (75.0, 105.0))

S205 = _spec(
    "S205", quantity_phrase="a price tag", quantity_type="mass", unit="g", values=(2.0, 6.0, 15.0), heldout_values=(3.0, 10.0),
    relevant=rv.RelevantWiring("m", "add", "A price tag stuck to the coin travels with it, so the mass that has to be accelerated "
                                           "becomes m + q and the friction force grows with it."),
    conditional=S205_K,
    scene_clause="A ceramic dish stands on a shelf beside the turntable.",
    scene_object_rationale="A dish on a shelf beside the turntable is not on the turntable and does not touch the coin, so the coin's mass and "
                           "the friction force on it are unchanged.",
    scene_refs=("dish",), target_terms=("coin", "turntable"),
    pairs=(
        Pair("p0", "A {value} {unit} price tag is stuck to {relation}.", "the coin", "the dish", CO,
             "A price tag stuck to the dish adds to the dish only; the coin keeps its stated mass.",
             ("has not slipped", "rests on a horizontal turntable"), "small",
             before_context_reason="The R sentence refers to 'the coin' before the context introduces it."),
        Pair("p1", "A {value} {unit} price tag was stuck to the coin {relation}.", "before the turntable was started",
             "for an earlier trial only", EVENT,
             "The tag was stuck to the coin in an earlier trial, which is over; the coin of the stated run has only its stated mass.",
             ("has not slipped", "rests on a horizontal turntable"), "small"),
    ),
    notes="M250 phase 2: R is a price tag on the coin (added to the mass); K is the largest static friction force (sliding versus static); no C.")

# --- S206 ------------------------------------------------------------------------------------------------------------------------

S206_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the density of the liquid", "density", "kg/m^3", (950.0, 1200.0, 1800.0), "The liquid {relation} {value} {unit}.",
        (P("c0", "has a density of"), P("c1", "is a liquid of density")),
        "h0 - ((q*Om**2*R**2/2)/(q*g))/2",
        ("hydrostatic balance in the rotating frame: dp/dr = q Om^2 r and dp/dz = -q g", "slope of the free surface: dz/dr = (q Om^2 r) / (q g)"),
        "h0 - ((q/1000)*Om**2*R**2/(2*g))/2", nonnumeric_fill="a known density"),
    "standard", "That the shape of the free surface of a rotating liquid does not depend on its density is taught with the paraboloid "
                "z = w^2 r^2 / (2 g), but the density is rarely mentioned as cancelling.", (1100.0, 1400.0))

S206_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the height of the wall of the tank", "length", "cm", (55.0, 70.0, 90.0), "The inner wall of the tank {relation} {value} {unit}.",
        (P("k0", "rises to a height of"), P("k1", "is built to a height of")),
        "hw < q", "q - dh", 15.0, nonnumeric_fill="a known height"),
    r2.KOut(False, "The base problem states that the tank is tall enough that no liquid spills; a wall lower than the rim height of the "
                   "liquid would contradict it. Where liquid did spill the depth at the axis would be well posed (rim height minus the "
                   "paraboloid's rise), but the stated premise forbids that case."),
    (62.0, 80.0))

S206 = _spec(
    "S206", quantity_phrase="an upward acceleration", quantity_type="acceleration", unit="m/s^2", values=(1.9, 3.9, 5.6),
    heldout_values=(2.8, 4.2),
    relevant=rv.RelevantWiring("g", "add", "A platform that accelerates upward adds its acceleration to the apparent gravity in the frame of the "
                                           "tank, so g becomes g + q in the shape of the free surface."),
    cancelling=S206_C, conditional=S206_K,
    scene_clause="A goods lift serves the hall in which the tank stands.",
    scene_object_rationale="A goods lift in the same hall does not touch the tank or its platform, so the apparent gravity in the frame of the "
                           "tank is the stated one.",
    scene_refs=("goods lift",), target_terms=("platform", "tank"),
    pairs=(
        Pair("p0", "The {relation} accelerates upward at a constant rate of {value} {unit} while the tank spins.",
             "platform under the tank", "goods lift", CO,
             "A goods lift in the hall rises with its own acceleration; the platform under the tank stays at rest and the apparent gravity "
             "in the frame of the tank is the stated g.", ("no liquid spills", "turns with the tank as a solid body"),
             "a few metres per second squared",
             before_context_reason="The R sentence refers to 'the platform under the tank' before the context introduces the tank."),
        Pair("p1", "The platform under the tank was set rising with a constant upward acceleration of {value} {unit} {relation}.",
             "before the liquid reached steady rotation", ONLY_EARLIER_RUN, EVENT,
             "The platform was set rising in an earlier run, which is over; in the stated run the platform stands still and g is the stated value.",
             ("no liquid spills", "turns with the tank as a solid body"), "a few metres per second squared"),
    ),
    notes="M250 phase 2: R is an upward acceleration of the platform (added to g); C is the density of the liquid; K is the wall height (overflow).")

# --- S207 ------------------------------------------------------------------------------------------------------------------------

S207 = _spec(
    "S207", quantity_phrase="a sandbag", quantity_type="mass", unit="kg", values=(0.5, 2.4, 3.8), heldout_values=(1.7, 3.6),
    relevant=rv.RelevantWiring("m1", "add", "A sandbag hung from the single block travels with it, so the mass on the first string becomes "
                                            "m1 + q."),
    scene_clause="A toolbox stands on the floor beside the rig.",
    scene_object_rationale="A toolbox on the floor does not touch the blocks, the strings or the pulleys, so the accelerations of the blocks "
                           "are fixed by the stated masses and g.",
    scene_refs=("toolbox",), target_terms=("single block", "pulley", "string", "blocks"),
    pairs=(
        Pair("p0", "A {value} {unit} sandbag is {relation}.", "hung from the single block", "placed in the toolbox", CO,
             "A sandbag placed in the toolbox rests on the floor and touches none of the blocks, strings or pulleys; the masses on the strings "
             "are the stated ones.", ("without friction", "released from rest"), "small",
             before_context_reason="The R sentence refers to 'the single block' before the context introduces any block."),
        Pair("p1", "A {value} {unit} sandbag was hung from the single block {relation}.", "before the blocks were released",
             ONLY_EARLIER_RUN, EVENT,
             "The sandbag was hung from the single block in an earlier run, which is over; the single block of the stated run carries only "
             "its stated mass.", ("without friction", "released from rest"), "small"),
    ),
    notes="M250 phase 2: R is a sandbag hung from the single block (added to m1); no C or K (see NO_C, NO_K).")

# --- S208 ------------------------------------------------------------------------------------------------------------------------

S208_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the friction torque between the faces of the discs", "torque", "N*m", (2.5, 6.5, 17.0),
        "The faces of the discs {relation} {value} {unit}.",
        (P("c0", "slip against each other with a constant friction torque of"), P("c1", "rub with a steady friction torque of")),
        "q*(n1**2*(I1*I2/(I1 + I2))/(2*q))",
        ("common speed reached after t = I1 I2 w1 / ((I1 + I2) q)", "relative speed falls linearly: w_rel = w1 - q t (I1 + I2) / (I1 I2)",
         "heat = friction torque q times the integral of the relative speed over the slipping time"),
        "q*n1*(I1*I2/(I1 + I2))*n1/q", nonnumeric_fill="a known torque"),
    "standard", "That the energy lost in a rotational collision does not depend on the friction torque of the faces is the rotational "
                "analogue of the energy lost in a perfectly inelastic collision, but is not stated as a fact.", (3.5, 14.0))

S208 = _spec(
    "S208", quantity_phrase="a ring", quantity_type="moment_of_inertia", unit="kg*m^2", values=(0.015, 0.04, 0.075),
    heldout_values=(0.025, 0.055),
    relevant=rv.RelevantWiring("I2", "add", "A ring glued to the stationary disc adds its moment of inertia about the axle to the disc's, "
                                            "so I2 becomes I2 + q."),
    cancelling=S208_C,
    scene_clause="A grinding wheel stands on a bench nearby.",
    scene_object_rationale="A grinding wheel on a bench is not on the axle of the discs and does not touch them, so the moments of inertia "
                           "of the two discs and the energy dissipated in their coupling are unchanged.",
    scene_refs=("grinding wheel",), target_terms=("disc", "discs", "axle"),
    pairs=(
        Pair("p0", "A ring whose moment of inertia is {value} {unit} is {relation}.", "glued to the second disc", "fitted to the grinding wheel", CO,
             "A ring fitted to the grinding wheel adds to the wheel's moment of inertia only; the second disc keeps its stated moment of inertia.",
             ("frictionless axle", "grip each other"), "a small amount",
             before_context_reason="The R sentence refers to 'the second disc' before the context introduces it."),
        Pair("p1", "A ring whose moment of inertia is {value} {unit} was glued to the second disc {relation}.",
             "before the spinning disc was lowered", ONLY_EARLIER_RUN, EVENT,
             "The ring was glued to the second disc in an earlier run, which is over; the second disc of the stated run has only its stated "
             "moment of inertia.", ("frictionless axle", "grip each other"), "a small amount"),
    ),
    notes="M250 phase 2: R is a ring glued to the stationary disc (added to I2); C is the friction torque of the faces; no K (see NO_K).")

# --- S209 ------------------------------------------------------------------------------------------------------------------------

S209 = _spec(
    "S209", quantity_phrase="a further piece of clay", quantity_type="mass", unit="kg", values=(0.07, 0.13, 0.21),
    heldout_values=(0.09, 0.17),
    relevant=rv.RelevantWiring("m", "add", "A further piece of clay pressed onto the lump travels with it and sticks with it, so the mass "
                                           "that hits the rod becomes m + q."),
    scene_clause="A vase stands on a shelf above the table.",
    scene_object_rationale="A vase on a shelf above the table is not on the table and does not touch the rod or the lump, so the collision of "
                           "the lump with the rod is unchanged.",
    scene_refs=("vase",), target_terms=("lump", "rod", "clay", "table"),
    pairs=(
        Pair("p0", "A further {value} {unit} piece of clay is pressed onto {relation}.", "the lump", "the vase", CO,
             "Clay pressed onto the vase adds to the vase only; the lump of clay that hits the rod keeps its stated mass.",
             ("smooth horizontal table", "sticks to the rod"), "small",
             before_context_reason="The R sentence refers to 'the lump' before the context introduces it."),
        Pair("p1", "A further {value} {unit} piece of clay was pressed onto the lump {relation}.", "before the lump hit the rod",
             ONLY_EARLIER_RUN, EVENT,
             "The extra clay was pressed onto the lump in an earlier run, which is over; the lump of the stated run has only its stated mass.",
             ("smooth horizontal table", "sticks to the rod"), "small"),
    ),
    notes="M250 phase 2: R is a further piece of clay pressed onto the lump (added to m); no C or K (see NO_C, NO_K).")

# --- S210 ------------------------------------------------------------------------------------------------------------------------

S210_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the spring constant", "spring_constant", "N/m", (30.0, 60.0, 110.0), "The spring {relation} {value} {unit}.",
        (P("c0", "has a spring constant of"), P("c1", "has a stiffness of")),
        "(2*m/b)*log(sqrt((q/2)/(q*f**2/2)))",
        ("energy of the oscillation E = q A^2 / 2 (the envelope energy falls as the square of the amplitude)", "amplitude ratio from the energy "
                                                                                                             "ratio: A / A0 = sqrt(E / E0)"),
        "(2*m/b)*log(1/f)*(1 + q/1000)", nonnumeric_fill="a known stiffness"),
    "standard", "That the decay of the envelope of a damped oscillator is set by m and b alone and not by the spring is standard but is "
                "not a headline fact.", (40.0, 70.0))

S210 = _spec(
    "S210", quantity_phrase="an extra damper", quantity_type="damping_coefficient", unit="kg/s", values=(0.15, 0.19, 0.29),
    heldout_values=(0.17, 0.25),
    relevant=rv.RelevantWiring("b", "add", "A second damper fitted alongside the first adds its damping coefficient, so b becomes b + q."),
    cancelling=S210_C,
    scene_clause="A heavy door stands in the wall beside the track.",
    scene_object_rationale="A door in the wall beside the track is not connected to the block, the spring or the damper, so the damping of "
                           "the block is the stated one.",
    scene_refs=("door",), target_terms=("block", "spring", "damper", "track"),
    pairs=(
        Pair("p0", "An extra damper with a damping coefficient of {value} {unit} is {relation}.", "fitted to the block alongside the first",
             "fitted to the door", CO,
             "A damper fitted to the door damps the door only; the block keeps its stated damper.",
             ("frictionless track", "released from rest"), "a small value",
             before_context_reason="The R sentence refers to 'the block' and to 'the first' damper before the context introduces them."),
        Pair("p1", "An extra damper with a damping coefficient of {value} {unit} was fitted to the block {relation}.",
             "before the block was released", ONLY_EARLIER_RUN, EVENT,
             "The extra damper was fitted to the block in an earlier run, which is over; the block of the stated run has only its stated "
             "damper.", ("frictionless track", "released from rest"), "a small value"),
    ),
    notes="M250 phase 2: R is an extra damper (added to b); C is the spring constant; no K (see NO_K).")


ROLE_SPECS: dict[str, r2.RoleSpecV2] = {s.structure_id: s for s in (S201, S202, S203, S204, S205, S206, S207, S208, S209, S210)}
SPECS = ROLE_SPECS
STRUCTURE_FACTORIES = {sid: (lambda sid=sid: lib_m250_mech.STRUCTURES[sid]) for sid in ROLE_SPECS}

# Structures that cannot honestly carry the design. None in this batch.
INFEASIBLE: dict[str, str] = {}

K_KINDS: dict[str, str] = {
    "S201": "linear (Hooke) range of the spring: the response is linear only up to a limiting extension",
    "S205": "static versus sliding friction: static friction holds the coin only up to its largest value",
    "S206": "containment (overflow): the liquid stays in the tank only while the rim of the wall is above the rim of the surface",
}

NO_C: dict[str, str] = {
    "S204": "The energy converted in a perfectly inelastic collision depends on the masses and the relative speed only; no quantity of the "
            "system enters an intermediate relation and cancels (the collision duration never enters momentum conservation, and a "
            "frame speed would be a change of the stated velocities, not a quantity of the system).",
    "S205": "Every quantity of the turntable enters the friction force; the largest quantity that does not (the radius of the turntable) "
            "appears in no relation, so nothing enters and cancels.",
    "S207": "Every mass enters the acceleration; the radii of the pulleys and the lengths of the strings appear in no relation, and the "
            "tensions are intermediate unknowns fixed by the masses, not free quantities.",
    "S209": "The impulse equations contain only the masses, the speed and the lever arm; the collision duration and the contact force "
            "never enter, and the table is smooth so no friction quantity exists.",
}
NO_K: dict[str, str] = {
    "S202": "The only regimes (negligible gravity, a speed far below that of light) are limits with no exact threshold quantity that changes the "
            "answer at the stated precision; a tank or burn limit would contradict the stated total fuel.",
    "S203": "A regime quantity (a friction coefficient, a small-angle limit) would not leave the period exactly unchanged inside the regime "
            "and has no definite out-of-regime answer: the small-oscillation period is the base problem itself.",
    "S204": "The only regime is the brief collision on frictionless ice, which is stated and has no quantity with a threshold.",
    "S207": "The taut-string condition is a property of the masses, not of a further quantity; a breaking tension would be an equipment "
            "rating with no definite out-of-regime answer.",
    "S208": "The slipping stage ends when the speeds match; a clutch capacity would be an equipment rating, and a friction regime quantity "
            "does not change the dissipated energy.",
    "S209": "The impact is stated to stick; an adhesion threshold would need an out-of-regime collision law that the problem does not define.",
    "S210": "The light-damping condition (critical damping) needs the spring constant, which the problem does not state; once a spring "
            "constant is stated, the out-of-regime law (overdamped decay) is complex at every in-regime value, so no separated alternative "
            "answer exists.",
}


def structure(structure_id: str) -> gr.Structure:
    """The structure with the spec's scene clause appended to its base context."""

    return r2.with_scene(lib_m250_mech.STRUCTURES[structure_id], ROLE_SPECS[structure_id].scene_clause)


# What the H4 trace extractor must read as a statement of the target: a phrase of the question, its head noun and the conventional symbols.
TARGET_TERMS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "S201": (("amplitude of the steady oscillation", "amplitude"), ("A", "x_0")),
    "S202": (("speed of the rocket after all the fuel has been burned", "speed of the rocket", "speed"), ("vf", "v_f", "v")),
    "S203": (("period of small oscillations", "period"), ("T", "T_s")),
    "S204": (("kinetic energy is converted", "energy converted", "kinetic energy"), ("dK", "ΔK", "Q")),
    "S205": (("friction force that the turntable exerts", "friction force"), ("f", "F_f", "f_s")),
    "S206": (("depth of the liquid at the axis", "depth of the liquid", "depth"), ("ha", "h_a", "h")),
    "S207": (("downward acceleration of the single block", "downward acceleration", "acceleration"), ("a1", "a_1", "a")),
    "S208": (("mechanical energy is dissipated as heat", "energy is dissipated", "energy"), ("dE", "ΔE", "Q")),
    "S209": (("angular speed of the rod and clay together", "angular speed"), ("w", "ω", "omega")),
    "S210": (("how long after the release", "time"), ("t", "t_f", "T")),
}
