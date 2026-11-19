"""Role-by-value v2.1 specifications for M250 phase 1, batch b (S24 S25 S28 S29 S31 S32 S33 S34 S35 S36 S37 S38 S41 S42 S43 S44 S45).

October dataset-v1 structures upgraded to the role-by-value design of M0 v2.1 (plan revision v2.2, sections F and G; admission
standard 3.1-3.5, 2.3-2.4, 6.2): one R/D quantity with three study and two held-out values, two phrasing pairs (d0 a co-present object
that a number-free scene clause introduces in the base context of every cell, d1 an other event of the target object that leaves no
state behind), a C quantity and a K quantity where the physics supports one, target naming for the H4 extractor. Instance 0 is the
emitted instance. Nothing here changes a graph: the structures are the October ones with the scene clause appended to the context.

C and K are omitted, not forced, where no honest cancelling quantity or regime exists (`NO_C`, `NO_K` give the reason per structure).
Where a K quantity has no honest out-of-regime question (the base problem states the premise that the regime fails against), `KOut`
is infeasible with the reason and the certificate's `out_of_regime_law` is the misuse foil (the limit read as the working value).
"""

from __future__ import annotations

import dataclasses

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import lib_electromagnetism, lib_mechanics, library_c
from physmon.benchmark.v2 import rolevalue as rv
from physmon.benchmark.v2 import rolevalue_v2 as r2

P = rv.Phrasing
Pair = r2.PhrasePair
CO = r2.D_KIND_CO_PRESENT
EVENT = r2.D_KIND_OTHER_EVENT
V21 = r2.VERSION_V21

INFEASIBLE: dict[str, str] = {}  # structures that cannot honestly carry the design: none in this batch

# --- S24: Carnot engine ---------------------------------------------------------------------------------------------------------------

S24 = r2.RoleSpecV2(
    structure_id="S24", quantity_phrase="a temperature rise of the hot reservoir", quantity_type="temperature", unit="K",
    values=(70.0, 150.0, 250.0), heldout_values=(110.0, 190.0),
    relevant=rv.RelevantWiring("Th", "add", "Warming the engine's hot reservoir by q before the cycles makes its temperature Th + q; the heat taken in "
                                            "per cycle is stated, so the work is Qh (1 - Tc / (Th + q))."),
    pairs=(
        Pair("p0", "A burner then warms {relation} by {value} {unit}.", "the hot reservoir", "the kettle", CO,
             "A burner that warms a kettle of water exchanges no heat with the engine's reservoirs; the temperatures of the engine's "
             "reservoirs are the stated ones.", ("reversible heat engine", "in each cycle"), "a few kelvin",
             before_context_reason="The R sentence refers to 'the hot reservoir' before the context introduces the engine, and "
                                   "'then' presupposes the stated reservoir temperature."),
        Pair("p1", "{relation}, a burner warmed the hot reservoir by {value} {unit}.", "Before the first cycle",
             "In an earlier experiment", EVENT,
             "The hot reservoir was warmed in an earlier experiment, which is over; in the stated experiment the hot reservoir is "
             "at its stated temperature.", ("reversible heat engine", "in each cycle"), "a few kelvin"),
    ),
    cancelling=r2.CancellingV2(
        rv.CancellingSpec(
            "the amount of working gas", "amount_of_substance", "mol", (1.6, 3.4, 6.5),
            "The working substance {relation} {value} {unit} of an ideal gas.",
            (P("c0", "is"), P("c1", "consists of")),
            "q*8.314*(Th - Tc)*(Qh/(q*8.314*Th))",
            ("Qh = n R Th ln(V2/V1) (isothermal expansion at Th)", "Qc = n R Tc ln(V2/V1) (same volume ratio, set by the adiabats)",
             "W = Qh - Qc = n R (Th - Tc) ln(V2/V1)", "ln(V2/V1) = Qh / (n R Th) from the stated heat"),
            "q*8.314*(Th - Tc)*log(2)", nonnumeric_fill="a known amount"),
        "standard", "That a reversible engine's efficiency depends only on the reservoir temperatures, not on the working substance, "
                    "is textbook-standard (Carnot's theorem), but the amount of gas is not usually named.", (2.2, 4.6)),
    notes="Carnot cycle on q mol of an ideal gas: the heat Qh fixes the volume ratio, so n cancels. No K: a reversible engine between "
          "two reservoirs has no regime that can fail honestly.")

# --- S25: energy stored in a coil ---------------------------------------------------------------------------------------------------------

S25 = r2.RoleSpecV2(
    structure_id="S25", quantity_phrase="a step in the current", quantity_type="current", unit="A", values=(1.2, 2.8, 4.5),
    heldout_values=(1.8, 3.4),
    relevant=rv.RelevantWiring("Icur", "add", "A step of q in the steady current through the coil makes it Icur + q, and the stored "
                                              "energy is L (Icur + q)^2 / 2."),
    pairs=(
        Pair("p0", "A rheostat then increases the current through {relation} by {value} {unit}.", "the coil", "the lamp", CO,
             "A rheostat in the lamp's own circuit changes the lamp's current only; the current through the coil is the stated "
             "steady current.", ("ideal coil", "steady current"), "a small amount",
             before_context_reason="The R sentence refers to 'the coil' before the context introduces it, and 'then' presupposes the "
                                   "stated steady current."),
        Pair("p1", "{relation}, a rheostat increased the current through the coil by {value} {unit}.",
             "Before the energy was measured", "In an earlier experiment", EVENT,
             "The current through the coil was increased in an earlier experiment, which is over; in the stated experiment the "
             "coil carries its stated steady current.", ("ideal coil", "steady current"), "a small amount"),
    ),
    cancelling=r2.CancellingV2(
        rv.CancellingSpec(
            "the time over which the current was established", "time", "ms", (20.0, 45.0, 65.0),
            "The current {relation} {value} {unit}.",
            (P("c0", "was brought up to this value at a steady rate over"), P("c1", "rose steadily from zero to this value in")),
            "q*(Lind*Icur/q)*(Icur/2)",
            ("emf = L dI/dt = L I / T for a steady ramp of duration T", "power = emf x i(t), average current I / 2",
             "energy = average power x T"),
            "Lind*Icur**2/(2*q)", nonnumeric_fill="a short time"),
        "standard", "That the energy stored does not depend on how quickly the current was brought up is standard in treatments of "
                    "inductors but is not stated as a named fact.", (35.0, 85.0)),
    conditional=r2.ConditionalV2(
        rv.ConditionalSpec(
            "the saturation current of the core", "current", "A", (6.5, 9.5, 12.0),
            "The core of the coil {relation} {value} {unit}.",
            (P("k0", "stays linear for currents up to"), P("k1", "does not saturate below a current of")),
            "q > Icur", "Lind*q**2/2", 1.5),
        r2.KOut(False, "The problem states that the coil carries a steady current of 3 A and that it is ideal (constant inductance); "
                       "a core that saturated below 3 A would make the stored energy depend on an unstated saturated inductance, so "
                       "no question about this coil has a certified answer in that regime."),
        (8.5, 10.5)),
    notes="R is a current step; C is the ramp time (energy = average power x time cancels the time); K is the linear range of the "
          "core. The K foil Lind q^2/2 reads the saturation current as the working current.")

# --- S28: car catching a truck -------------------------------------------------------------------------------------------------------------

S28 = r2.RoleSpecV2(
    structure_id="S28", quantity_phrase="an extra acceleration", quantity_type="acceleration", unit="m/s^2", values=(0.6, 1.3, 2.5),
    heldout_values=(0.8, 1.6),
    relevant=rv.RelevantWiring("a", "add", "A tuning kit that adds q to the car's acceleration makes it a + q, and the car draws level "
                                           "at t = 2 v / (a + q)."),
    pairs=(
        Pair("p0", "A tuning kit adds {value} {unit} to the acceleration of {relation}.", "the car", "the motorbike", CO,
             "A tuning kit fitted to a motorbike waiting at the roadside changes the motorbike's acceleration only; the car's "
             "acceleration and the truck's speed are the stated ones.", ("constant", "from rest"), "a little",
             before_context_reason="The R sentence refers to 'the car', which the context introduces, with an acceleration the "
                                   "context has not yet stated; placed first it reads as a fact about a car not yet in the scene."),
        Pair("p1", "{relation}, a tuning kit added {value} {unit} to the acceleration of the car.", "Before the start",
             "For an earlier run only", EVENT,
             "The kit was fitted to the car in an earlier run, which is over; in the stated run the car's constant acceleration is "
             "the stated one.", ("constant", "from rest"), "a little"),
    ),
    conditional=r2.ConditionalV2(
        rv.ConditionalSpec(
            "the top speed of the car", "speed", "m/s", (38.0, 46.0, 58.0), "The car {relation} {value} {unit}.",
            (P("k0", "has a top speed of"), P("k1", "cannot go faster than")),
            "q > a*t", "q**2/(2*a*(q - v))", 20.0),
        r2.KOut(True, "The question stays well posed when the top speed is below the speed the car would reach at the catch-up "
                      "instant but above the truck's speed: the car then accelerates to the top speed, keeps it, and draws level at "
                      "t = q^2 / (2 a (q - v)), which exists whenever q > v.", (17.0, 21.0)),
        (40.0, 52.0)),
    notes="R is extra acceleration from a tuning kit; K is the top speed of the car (the car reaches 2 v at the catch-up instant, so a "
          "higher top speed is never reached). No C: the answer 2 v / a has no quantity that enters and cancels.")

# --- S29: power of a rope at an angle -------------------------------------------------------------------------------------------------------

S29 = r2.RoleSpecV2(
    structure_id="S29", quantity_phrase="a tilt of the rope", quantity_type="angle", unit="deg", values=(12.0, 17.0, 24.0),
    heldout_values=(14.0, 21.0),
    relevant=rv.RelevantWiring("theta", "add", "Tilting the rope q further above the horizontal makes its angle theta + q; the "
                                               "tension and the speed are stated, so the power is F v cos(theta + q)."),
    pairs=(
        Pair("p0", "{relation} is then tilted {value} {unit} further above the horizontal.", "The rope of the sled",
             "The jib of the crane", CO,
             "The jib of a crane that stands beside the sled is not the rope; tilting it leaves the angle, the tension and the speed "
             "of the sled's rope as stated.", ("constant speed", "tension in the rope"), "a little",
             before_context_reason="The R sentence refers to 'the rope of the sled' before the context introduces them, and 'then' "
                                   "presupposes the stated angle."),
        Pair("p1", "{relation}, the rope of the sled was tilted {value} {unit} further above the horizontal.",
             "Before the power was measured", "In an earlier trial", EVENT,
             "The rope was tilted in an earlier trial, which is over; in the stated trial the rope makes its stated angle with "
             "the horizontal.", ("constant speed", "tension in the rope"), "a little"),
    ),
    cancelling=r2.CancellingV2(
        rv.CancellingSpec(
            "the time for which the sled is pulled", "time", "s", (25.0, 55.0, 85.0), "The sled is pulled {relation} {value} {unit}.",
            (P("c0", "for"), P("c1", "at this speed for")),
            "(F*cos(theta)*(v*q))/q",
            ("distance moved d = v t", "work done by the rope W = F cos(theta) d", "average power = W / t"),
            "F*cos(theta)*v*q", nonnumeric_fill="a known time"),
        "standard", "That the power of a constant force at constant speed does not depend on how long it acts is standard, but is "
                    "not a named classroom fact.", (65.0, 95.0)),
    conditional=r2.ConditionalV2(
        rv.ConditionalSpec(
            "the breaking strength of the rope", "force", "N", (150.0, 210.0, 280.0), "The rope {relation} {value} {unit}.",
            (P("k0", "can withstand a tension of up to"), P("k1", "is rated to break only above")),
            "F < q", "0", 25.0),
        r2.KOut(False, "The problem states that the rope pulls the sled with a tension of 40 N; a rope rated below that tension "
                       "would have broken, contradicting the stated pull, and a broken rope delivers no power, so the question "
                       "has no meaningful out-of-regime version."),
        (180.0, 240.0)),
    notes="R is a tilt of the rope at fixed tension and speed; C is the duration (work over time cancels it); K is the breaking "
          "strength of the rope.")

# --- S31: stone thrown from a cliff -------------------------------------------------------------------------------------------------------

S31 = r2.RoleSpecV2(
    structure_id="S31", quantity_phrase="a platform height", quantity_type="length", unit="m", values=(6.0, 14.0, 28.0),
    heldout_values=(9.0, 22.0),
    relevant=rv.RelevantWiring("h", "add", "A thrower on a platform q above the cliff edge launches the stone from a height h + q, "
                                           "so the fall time is sqrt(2 (h + q) / g)."),
    pairs=(
        Pair("p0", "The {relation} then climbs onto a platform {value} {unit} above the cliff edge.", "thrower", "surveyor", CO,
             "A surveyor who stands further along the cliff edge on a platform is not the thrower; the stone's launch height is the "
             "stated height of the cliff.", ("horizontally", "level ground"), "a little",
             before_context_reason="The R sentence refers to 'the thrower' and 'the cliff edge' before the context introduces the "
                                   "throw and the cliff."),
        Pair("p1", "The thrower climbed onto a platform {value} {unit} above the cliff edge {relation}.", "before the stone was thrown",
             "in an earlier experiment", EVENT,
             "The thrower stood on a platform in an earlier experiment, which is over; in the stated experiment the stone leaves "
             "from the stated height.", ("horizontally", "level ground"), "a little"),
    ),
    cancelling=r2.CancellingV2(
        rv.CancellingSpec(
            "the mass of the stone", "mass", "kg", (0.6, 1.8, 3.5), "The stone {relation} {value} {unit}.",
            (P("c0", "has a mass of"), P("c1", "is a rock with a mass of")),
            "v*sqrt(2*h/((q*g)/q))",
            ("weight W = m g", "vertical acceleration a = W / m", "fall time t = sqrt(2 h / a)", "range = v t"),
            "v*sqrt(2*h*q/g)", nonnumeric_fill="a known mass"),
        "famous", "Mass independence of free fall (Galileo) is a headline classroom fact.", (1.1, 2.7)),
    notes="R puts the thrower on a platform above the cliff edge; C is the stone's mass (free fall). No K: the base problem already "
          "states the idealisations (no air resistance, level ground) and no quantity decides between regimes.")

# --- S32: spring launch and slide ---------------------------------------------------------------------------------------------------------

S32 = r2.RoleSpecV2(
    structure_id="S32", quantity_phrase="a weight fixed to the block", quantity_type="mass", unit="kg", values=(0.7, 1.5, 2.2),
    heldout_values=(0.9, 1.6),
    relevant=rv.RelevantWiring("m", "add", "A weight fixed to the block moves with it and presses on the table, so the friction "
                                           "force is mu (m + q) g while the stored spring energy is unchanged."),
    pairs=(
        Pair("p0", "A {value} {unit} weight is fixed to {relation}.", "the block", "the trolley", CO,
             "A weight fixed to a trolley on a neighbouring table adds no load to the block or its table; the block's mass and "
             "friction are the stated ones.", ("spring constant", "coefficient of kinetic friction"), "small",
             before_context_reason="The R sentence refers to 'the block', which the context introduces afterwards, and says nothing "
                                   "of the spring that the context describes."),
        Pair("p1", "A {value} {unit} weight was fixed to the block {relation}.", "before it was released",
             "for an earlier experiment only", EVENT,
             "The weight was fixed to the block in an earlier experiment, which is over; in the stated experiment the block has "
             "only its stated mass.", ("spring constant", "coefficient of kinetic friction"), "small"),
    ),
    conditional=r2.ConditionalV2(
        rv.ConditionalSpec(
            "the elastic limit of the spring", "length", "cm", (22.0, 28.0, 36.0), "The spring {relation} {value} {unit}.",
            (P("k0", "obeys Hooke's law up to a compression of"), P("k1", "stays elastic up to a compression of")),
            "q > x", "k*q**2/(2*mu*m*g)", 5.0),
        r2.KOut(False, "The problem states that the spring is compressed by 10 cm, obeys Hooke's law and pushes the block; a spring "
                       "with an elastic limit below the compression would contradict the stated compression, and the energy it "
                       "then stores is not given by any quantity in the problem."),
        (24.0, 31.0)),
    notes="R is a weight fixed to the block (friction grows); K is the elastic limit of the spring (the foil reads the limit as "
          "the compression). No C: every quantity of the base that enters the distance also changes it.")

# --- S33: ball bouncing off a wall ---------------------------------------------------------------------------------------------------------

S33 = r2.RoleSpecV2(
    structure_id="S33", quantity_phrase="a lump of clay", quantity_type="mass", unit="g", values=(35.0, 75.0, 120.0),
    heldout_values=(55.0, 95.0),
    relevant=rv.RelevantWiring("m", "add", "A lump of clay stuck to the ball moves with it, so the ball's mass is m + q and the "
                                           "impulse is (m + q)(v + e v)."),
    pairs=(
        Pair("p0", "A {value} {unit} lump of clay is stuck to {relation}.", "the ball", "the toy cart", CO,
             "Clay stuck to a toy cart on the floor adds no mass to the ball that hits the wall; the impact of the stated ball is "
             "unchanged.", ("rigid wall", "coefficient of restitution"), "small",
             before_context_reason="The R sentence refers to 'the ball' before the context introduces it."),
        Pair("p1", "A {value} {unit} lump of clay was stuck to the ball {relation}.", "before it hit the wall",
             "for an earlier experiment only", EVENT,
             "The clay was stuck to the ball in an earlier experiment, which is over; in the stated experiment the ball has only "
             "its stated mass.", ("rigid wall", "coefficient of restitution"), "small"),
    ),
    notes="R is a lump of clay stuck to the ball (mass). No C or K: the force is the impulse over the contact time, and every quantity of the "
          "base enters it; the base states the idealisations (rigid wall, negligible weight) rather than leaving a regime open.")

# --- S34: sphere rolling up an incline ---------------------------------------------------------------------------------------------------------

S34 = r2.RoleSpecV2(
    structure_id="S34", quantity_phrase="a tilt of the incline", quantity_type="angle", unit="deg", values=(7.0, 13.0, 18.0),
    heldout_values=(9.0, 16.0),
    relevant=rv.RelevantWiring("theta", "add", "Tilting the incline q more steeply makes its angle theta + q, and the sphere's "
                                               "deceleration is (5/7) g sin(theta + q)."),
    pairs=(
        Pair("p0", "{relation} is then tilted {value} {unit} more steeply.", "The incline", "The solar panel", CO,
             "A solar panel beside the incline is not the incline; tilting it leaves the angle of the incline the sphere rolls up "
             "as stated.", ("rolls without slipping", "fixed incline"), "a little",
             before_context_reason="The R sentence refers to 'the incline' before the context introduces it, and 'then' "
                                   "presupposes the stated angle."),
        Pair("p1", "{relation}, the incline was tilted {value} {unit} more steeply.", "Before the sphere was set rolling",
             "In an earlier experiment", EVENT,
             "The incline was tilted in an earlier experiment, which is over; in the stated experiment the incline makes its "
             "stated angle with the horizontal.", ("rolls without slipping", "fixed incline"), "a little"),
    ),
    cancelling=r2.CancellingV2(
        rv.CancellingSpec(
            "the radius of the sphere", "length", "cm", (3.5, 8.5, 12.0), "The sphere {relation} {value} {unit}.",
            (P("c0", "has a radius of"), P("c1", "measures, from its centre to its surface,")),
            "v0**2/(2*g*sin(theta)/(1 + ((2*q**2)/5)/q**2))",
            ("moment of inertia per unit mass I/m = (2/5) R^2", "rolling without slipping: a_cm = alpha R",
             "a = g sin(theta) / (1 + I / (m R^2))"),
            "v0**2/(2*g*sin(theta)/(1 + 2*q/5))", nonnumeric_fill="a known radius"),
        "standard", "That the acceleration of a rolling uniform sphere does not depend on its radius or mass is standard in rolling "
                    "motion, but not a headline fact.", (5.5, 10.0)),
    conditional=r2.ConditionalV2(
        rv.ConditionalSpec(
            "the coefficient of static friction", "coefficient", "1", (0.35, 0.45, 0.55),
            "The coefficient of static friction between the sphere and the incline {relation} {value}.",
            (P("k0", "is"), P("k1", "has been measured as")),
            "q > 2*tan(theta)/7", "v0**2/(2*g*(sin(theta) - q*cos(theta)))", 0.05),
        r2.KOut(False, "The problem states that the sphere rolls without slipping; a coefficient below (2/7) tan(theta) would make it "
                       "slip, contradicting the stated rolling, so the question about rolling without slipping does not apply "
                       "in that regime."),
        (0.38, 0.5)),
    notes="R is a tilt of the incline; C is the radius (I/(m R^2) = 2/5); K is the static friction needed to keep the sphere rolling "
          "(the foil is the distance if the sphere slid with kinetic friction q).")

# --- S35: conical pendulum -------------------------------------------------------------------------------------------------------------------

S35 = r2.RoleSpecV2(
    structure_id="S35", quantity_phrase="an extension of the string", quantity_type="length", unit="m", values=(0.4, 0.7, 1.1),
    heldout_values=(0.5, 0.9),
    relevant=rv.RelevantWiring("L", "add", "Lengthening the string by q makes its length L + q while the angle with the vertical is "
                                           "stated, so the revolution time is 2 pi sqrt((L + q) cos(theta) / g)."),
    pairs=(
        Pair("p0", "{relation} is then lengthened by {value} {unit}.", "The string of the bob", "The line on the reel", CO,
             "The line on a fishing reel on the bench is not the pendulum's string; lengthening it leaves the length of the "
             "pendulum's string as stated.", ("light string", "constant angle"), "a little",
             before_context_reason="The R sentence refers to 'the string of the bob' before the context introduces them."),
        Pair("p1", "{relation}, the string of the bob was lengthened by {value} {unit}.", "Before the bob was set moving",
             "In an earlier experiment", EVENT,
             "The string was lengthened in an earlier experiment, which is over; in the stated experiment the string has its "
             "stated length.", ("light string", "constant angle"), "a little"),
    ),
    cancelling=r2.CancellingV2(
        rv.CancellingSpec(
            "the mass of the bob", "mass", "kg", (0.45, 1.4, 3.4), "The bob {relation} {value} {unit}.",
            (P("c0", "has a mass of"), P("c1", "is a brass sphere with a mass of")),
            "2*pi*L*sin(theta)/sqrt(L*sin(theta)*((q*g/cos(theta))*sin(theta)/q))",
            ("vertical balance: T cos(theta) = m g", "centripetal: T sin(theta) = m v^2 / r", "v^2 = r g tan(theta)"),
            "2*pi*sqrt(q*L*cos(theta)/g)", nonnumeric_fill="a known mass"),
        "standard", "Mass independence of the conical pendulum's period follows from the same cancellation as for the simple pendulum "
                    "but is less often stated.", (0.8, 1.9)),
    notes="R is an extension of the string; C is the bob's mass (the tension is m g / cos(theta), so m cancels from v^2). No K.")

# --- S36: rod as a physical pendulum ------------------------------------------------------------------------------------------------------

S36 = r2.RoleSpecV2(
    structure_id="S36", quantity_phrase="a shift of the axis", quantity_type="length", unit="cm", values=(18.0, 20.5, 22.0),
    heldout_values=(17.0, 20.0),
    relevant=rv.RelevantWiring("d", "subtract", "Moving the axis q closer to the centre of the rod makes the distance d - q, and the "
                                                "period is 2 pi sqrt((L^2 / 12 + (d - q)^2) / (g (d - q)))."),
    pairs=(
        Pair("p0", "The pivot of {relation} is then moved {value} {unit} closer to its centre.", "the rod", "the see-saw", CO,
             "The pivot of a see-saw is not the rod's pivot; moving it leaves the axis of the rod where the problem put it.",
             ("thin uniform rod", "small amplitude"), "a little",
             before_context_reason="The R sentence refers to 'the pivot of the rod' before the context introduces it, and 'then' "
                                   "presupposes the stated pivot."),
        Pair("p1", "{relation}, the pivot of the rod was moved {value} {unit} closer to its centre.",
             "Before the rod was set swinging", "In an earlier experiment", EVENT,
             "The pivot was moved in an earlier experiment, which is over; in the stated experiment the axis passes through its "
             "stated point.", ("thin uniform rod", "small amplitude"), "a little"),
    ),
    cancelling=r2.CancellingV2(
        rv.CancellingSpec(
            "the mass of the rod", "mass", "kg", (0.4, 1.1, 2.4), "The rod {relation} {value} {unit}.",
            (P("c0", "has a mass of"), P("c1", "is a steel strip with a mass of")),
            "2*pi*sqrt((q*(L**2/12 + d**2))/(q*g*d))",
            ("moment of inertia about the axis I = m (L^2 / 12 + d^2)", "restoring torque = m g d theta",
             "omega^2 = m g d / I"),
            "2*pi*sqrt(q*(L**2/12 + d**2)/(g*d))", nonnumeric_fill="a known mass"),
        "famous", "Mass independence of a pendulum's period is a headline classroom fact.", (0.7, 1.8)),
    notes="R is a shift of the axis from the centre; C is the rod's mass (I and the torque both scale with m). No K: the amplitude "
          "regime has no out-of-regime answer separated from the small-angle one at the stated values.")

# --- S37: circular orbit ---------------------------------------------------------------------------------------------------------------------

S37 = r2.RoleSpecV2(
    structure_id="S37", quantity_phrase="a rise of the orbit", quantity_type="length", unit="km", values=(300.0, 800.0, 1400.0),
    heldout_values=(450.0, 1100.0),
    relevant=rv.RelevantWiring("h", "add", "Raising the orbit by q makes the altitude h + q, so the radius is R + h + q and the period "
                                           "is 2 pi sqrt((R + h + q)^3 / (g R^2))."),
    pairs=(
        Pair("p0", "The orbit of {relation} is then raised by {value} {unit}.", "the satellite", "the space station", CO,
             "A space station in a different plane exerts a negligible force on the satellite; raising its orbit leaves the radius "
             "of the satellite's orbit as stated.", ("circular orbit", "uniform sphere"), "a little",
             before_context_reason="The R sentence refers to 'the satellite' before the context introduces it, and 'then' "
                                   "presupposes the stated orbit."),
        Pair("p1", "{relation}, the orbit of the satellite was raised by {value} {unit}.", "Before its period was measured",
             "In an earlier mission", EVENT,
             "The orbit was raised in an earlier mission, which is over; in the stated mission the satellite moves at its stated "
             "altitude.", ("circular orbit", "uniform sphere"), "a little"),
    ),
    cancelling=r2.CancellingV2(
        rv.CancellingSpec(
            "the mass of the satellite", "mass", "kg", (150.0, 750.0, 2500.0), "The satellite {relation} {value} {unit}.",
            (P("c0", "has a mass of"), P("c1", "is a probe with a mass of")),
            "2*pi*r/sqrt(((q*g*R**2/r**2)/q)*r)",
            ("gravitational force F = m g R^2 / r^2", "centripetal acceleration a = F / m", "v^2 = a r", "T = 2 pi r / v"),
            "2*pi*r/sqrt((q*g*R**2/r**2)*r)", nonnumeric_fill="a known mass"),
        "famous", "Independence of an orbit from the orbiting mass (the equivalence of gravitational and inertial mass) is a headline "
                  "fact.", (350.0, 1800.0)),
    notes="R is a rise of the orbit; C is the satellite's mass. No K: 'neglect drag' is stated as an idealisation and no honest "
          "out-of-regime law (a decaying orbit has no period) is available.")

# --- S38: ladder with a person on it -----------------------------------------------------------------------------------------------------------

S38 = r2.RoleSpecV2(
    structure_id="S38", quantity_phrase="a tilt of the ladder", quantity_type="angle", unit="deg", values=(14.0, 18.0, 22.0),
    heldout_values=(16.0, 20.0),
    relevant=rv.RelevantWiring("theta", "subtract", "Tilting the ladder q closer to the ground makes its angle theta - q; the "
                                                    "masses and the person's position are stated, so Fwall = (m/2 + M x) g / "
                                                    "tan(theta - q) and the ground still carries (m + M) g."),
    pairs=(
        Pair("p0", "{relation} is then tilted {value} {unit} closer to the ground.", "The ladder", "The shutter", CO,
             "A hinged shutter propped open beside the ladder does not touch it; tilting the shutter leaves the angle, the wall "
             "force and the ground force of the ladder as stated.", ("smooth vertical wall", "does not slip"), "a little",
             before_context_reason="The R sentence refers to 'the ladder' before the context introduces it, and 'then' presupposes "
                                   "the stated angle."),
        Pair("p1", "{relation}, the ladder was tilted {value} {unit} closer to the ground.", "Before the person stood on the ladder",
             "In an earlier experiment", EVENT,
             "The ladder was tilted in an earlier experiment, which is over; in the stated experiment the ladder makes its "
             "stated angle with the ground.", ("smooth vertical wall", "does not slip"), "a little"),
    ),
    cancelling=r2.CancellingV2(
        rv.CancellingSpec(
            "the length of the ladder", "length", "m", (3.5, 5.5, 7.5), "The ladder {relation} {value} {unit}.",
            (P("c0", "has a length of"), P("c1", "is a wooden ladder with a length of")),
            "sqrt((((m*q*g/2 + M*x*q*g)*cos(theta))/(q*sin(theta)))**2 + ((m + M)*g)**2)",
            ("torque about the foot: Fwall q sin(theta) = m g (q/2) cos(theta) + M g (x q) cos(theta)",
             "Fwall = (m/2 + M x) g / tan(theta)", "Ngnd = (m + M) g"),
            "sqrt((((m*q*g/2 + M*x*g)*cos(theta))/(q*sin(theta)))**2 + ((m + M)*g)**2)", nonnumeric_fill="a known length"),
        "standard", "That the wall force on a ladder does not depend on the ladder's length (the length is in every torque) is a "
                    "known feature of ladder problems but not a named fact.", (4.5, 6.5)),
    conditional=r2.ConditionalV2(
        rv.ConditionalSpec(
            "the coefficient of static friction at the ground", "coefficient", "1", (0.75, 1.15, 1.4),
            "The coefficient of static friction between the ladder and the ground {relation} {value}.",
            (P("k0", "is"), P("k1", "has been measured as")),
            "q*(m + M)*g > (m/2 + M*x)*g/tan(theta)", "(m + M)*g*sqrt(1 + q**2)", 0.2),
        r2.KOut(False, "The problem states that the ladder does not slip; a coefficient below the needed (m/2 + M x)/((m + M) tan "
                       "theta) would contradict that, and a sliding ladder is not in equilibrium, so the force of the ground "
                       "would no longer be fixed by the stated masses."),
        (0.85, 1.0)),
    notes="R is a tilt of the ladder (a mass quantity is not usable: add:m and add:M foils are inseparable at 0.1%); C is the ladder's length (it cancels from the torque balance); K is the static "
          "friction at the ground (the foil is the ground force at limiting friction q).")

# --- S41: charge sharing ------------------------------------------------------------------------------------------------------------------------

S41 = r2.RoleSpecV2(
    structure_id="S41", quantity_phrase="a further separation", quantity_type="length", unit="cm", values=(14.0, 26.0, 45.0),
    heldout_values=(18.0, 35.0),
    relevant=rv.RelevantWiring("d1", "add", "Moving the spheres q further apart makes the final separation d1 + q, and the force "
                                            "falls as 1 / (d1 + q)^2."),
    pairs=(
        Pair("p0", "{relation} then moved {value} {unit} further apart.", "The spheres are", "The magnets are", CO,
             "A pair of bar magnets on the bench exerts no electrostatic force on the conducting spheres; moving the magnets apart "
             "leaves the separation of the spheres as stated.", ("identical conducting spheres", "point charges"), "a little",
             before_context_reason="The R sentence refers to 'the spheres' before the context introduces them, and 'then' "
                                   "presupposes the stated separation."),
        Pair("p1", "{relation}, the spheres were moved {value} {unit} further apart.", "Before the force was measured",
             "In an earlier experiment", EVENT,
             "The spheres were moved apart in an earlier experiment, which is over; in the stated experiment their centres are "
             "at the stated separation.", ("identical conducting spheres", "point charges"), "a little"),
    ),
    cancelling=r2.CancellingV2(
        rv.CancellingSpec(
            "the radius of the spheres", "length", "cm", (1.5, 2.5, 4.0), "The spheres {relation} {value} {unit}.",
            (P("c0", "each have a radius of"), P("c1", "are solid balls, each of radius")),
            "F0*(((rq - 1)*q/(q + q))**2/rq)*(d0/d1)**2",
            ("charge shared in proportion to radius (capacitance): Q1' = (Q1 - Q2) q / (q + q)", "equal radii: Q' = (Q1 - Q2) / 2",
             "F = k Q'^2 / d^2"),
            "F0*(((rq - 1)/2)**2/rq)*((d0 + 2*q)/(d1 + 2*q))**2", nonnumeric_fill="a known radius"),
        "uncommon", "That identical conductors share charge equally whatever their size is not stated as a fact; the radius "
                    "enters only through the proportional sharing.", (2.0, 3.2)),
    notes="R is a further separation; C is the radius of the identical spheres (the shared charge divides by radius, so equal radii "
          "cancel). No K: the point-charge idealisation is stated and has no closed-form out-of-regime law.")

# --- S42: stretched wire ----------------------------------------------------------------------------------------------------------------------

S42 = r2.RoleSpecV2(
    structure_id="S42", quantity_phrase="an extra cell", quantity_type="voltage", unit="V", values=(3.5, 7.5, 16.0),
    heldout_values=(5.5, 14.0),
    relevant=rv.RelevantWiring("V", "add", "An ideal cell in series with the battery, facing the same way, gives an emf V + q across "
                                           "the drawn-out wire."),
    pairs=(
        Pair("p0", "A {value} {unit} cell of negligible internal resistance is {relation}, facing the same way.",
             "connected in series with the battery", "connected in series with the lamp's battery", CO,
             "A cell in series with the lamp's battery forms a loop of its own that shares no node with the wire; the wire is "
             "still across the stated battery alone.", ("ideal battery", "drawn out"), "small",
             before_context_reason="The R sentence refers to 'the battery', which the context introduces afterwards, and 'facing "
                                   "the same way' has no reference yet."),
        Pair("p1", "{relation}, a {value} {unit} cell of negligible internal resistance was connected in series with the battery, "
                   "facing the same way.", "Before the power was measured", "For an earlier experiment only", EVENT,
             "The cell was in series with the battery in an earlier experiment, which is over; in the stated experiment the wire "
             "is across the stated battery alone.", ("ideal battery", "drawn out"), "small"),
    ),
    cancelling=r2.CancellingV2(
        rv.CancellingSpec(
            "the original length of the wire", "length", "cm", (25.0, 45.0, 65.0), "The wire {relation} {value} {unit}.",
            (P("c0", "had an original length of"), P("c1", "was originally cut to a length of")),
            "V**2/(R0*((k*q)/q)*((k*q)/q))",
            ("new length L' = k L0", "constant volume: A' = A0 L0 / L' so A0 / A' = L' / L0",
             "R' = rho L' / A' = R0 (L' / L0)(A0 / A')"),
            "V**2/(R0*(k*q/q))", nonnumeric_fill="a known length"),
        "uncommon", "The length and the cross-section both change on drawing out and cancel in R' = k^2 R0; the original length is "
                    "not usually named.", (35.0, 55.0)),
    notes="R is an extra cell in series with the battery; C is the original length (R' = R0 k^2 for any L0 at constant volume). No K.")

# --- S43: dielectric slab ---------------------------------------------------------------------------------------------------------------------

S43 = r2.RoleSpecV2(
    structure_id="S43", quantity_phrase="an extra cell", quantity_type="voltage", unit="V", values=(3.5, 7.5, 21.0),
    heldout_values=(5.5, 14.0),
    relevant=rv.RelevantWiring("V", "add", "An ideal cell in series with the battery, facing the same way, gives an emf V + q across "
                                           "the capacitor; the extra charge is (C - C0)(V + q)."),
    pairs=(
        Pair("p0", "A {value} {unit} cell of negligible internal resistance is {relation}, facing the same way.",
             "connected in series with the battery", "connected in series with the lamp's battery", CO,
             "A cell in series with the lamp's battery forms a loop of its own that shares no node with the capacitor; the "
             "capacitor is still across the stated battery alone.", ("dielectric constant", "still connected"), "small",
             before_context_reason="The R sentence refers to 'the battery', which the context introduces afterwards, and 'facing "
                                   "the same way' has no reference yet."),
        Pair("p1", "{relation}, a {value} {unit} cell of negligible internal resistance was connected in series with the battery, "
                   "facing the same way.", "Before the slab was inserted", "For an earlier experiment only", EVENT,
             "The cell was in series with the battery in an earlier experiment, which is over; in the stated experiment the "
             "capacitor is across the stated battery alone.", ("dielectric constant", "still connected"), "small"),
    ),
    notes="R is an extra cell in series with the battery (V + q). No C or K: the capacitance is fixed by C0, d, t and kappa "
          "through the series layers, and no further quantity cancels or has a regime.")

# --- S44: levitated rod ------------------------------------------------------------------------------------------------------------------------

S44 = r2.RoleSpecV2(
    structure_id="S44", quantity_phrase="a field added by coils", quantity_type="magnetic_field", unit="mT",
    values=(90.0, 160.0, 240.0), heldout_values=(120.0, 200.0),
    relevant=rv.RelevantWiring("B", "add", "A pair of coils that adds q to the field around the rod makes the field B + q, so the "
                                           "supporting current is m g / ((B + q) L)."),
    pairs=(
        Pair("p0", "A pair of coils adds {value} {unit} to the field {relation}.", "in which the rod lies",
             "in which the compass lies", CO,
             "The coils add field only where the compass lies, in a region of its own on the bench; the field at the rod is the "
             "stated one.", ("whole rod is in the field", "points upward"), "a little",
             before_context_reason="The R sentence refers to 'the rod', which the context introduces afterwards."),
        Pair("p1", "A pair of coils added {value} {unit} to the field around the rod {relation}.", "before the current was set",
             "for an earlier experiment only", EVENT,
             "The coils added field in an earlier experiment, which is over; in the stated experiment the field is the stated "
             "field.", ("whole rod is in the field", "points upward"), "a little"),
    ),
    conditional=r2.ConditionalV2(
        rv.ConditionalSpec(
            "the width of the uniform field", "length", "cm", (95.0, 125.0, 150.0), "The uniform field extends {value} {unit} {relation}.",
            (P("k0", "along the line of the rod"), P("k1", "in the direction of the rod")),
            "q > L", "m*g/(B*q)", 25.0),
        r2.KOut(False, "The problem states that the whole rod is in the field; a field narrower than the rod would contradict that "
                       "statement, so the question as asked (the whole rod in a uniform field) does not apply."),
        (100.0, 135.0)),
    notes="R is field added by coils; K is the width of the uniform field (wider than the rod: the whole rod is in the field). No C: "
          "I = m g / (B L) has no quantity that enters and cancels.")

# --- S45: charged bead ---------------------------------------------------------------------------------------------------------------------

S45 = r2.RoleSpecV2(
    structure_id="S45", quantity_phrase="an extra accelerating potential", quantity_type="voltage", unit="V", values=(3.5, 6.5, 12.0),
    heldout_values=(4.5, 9.0),
    relevant=rv.RelevantWiring("V", "add", "An extra potential applied across the accelerating gap adds to the potential difference, "
                                           "so the bead gains q (V + q) energy and the speed is sqrt(2 q (V + q) / m)."),
    pairs=(
        Pair("p0", "An extra {value} {unit} is applied across {relation}.", "the accelerating gap", "the bulb", CO,
             "A bulb wired to a supply of its own does not change the potential difference across the bead's gap; the bead's "
             "speed and path are those of the stated potential difference.", ("from rest", "vacuum"), "voltage",
             before_context_reason="The R sentence refers to 'the accelerating gap' before the context introduces the bead and its "
                                   "acceleration."),
        Pair("p1", "An extra {value} {unit} was applied across the accelerating gap {relation}.", "before the bead was released",
             "for an earlier experiment only", EVENT,
             "The extra potential was applied in an earlier experiment, which is over; in the stated experiment the bead is "
             "accelerated through the stated potential difference.", ("from rest", "vacuum"), "voltage"),
    ),
    notes="R is an extra accelerating potential. No C or K: the radius sqrt(2 m V / q)/B has no cancelling quantity, and the "
          "non-relativistic and vacuum idealisations are stated, not open.")

# Scene clauses, rationales and target terms per structure (one place, so the specs above stay readable). -----------------------------------

SCENES: dict[str, tuple[str, str, tuple[str, ...], tuple[str, ...]]] = {
    "S24": ("A kettle of water stands nearby, and no heat passes between it and the engine or its reservoirs.",
            "A kettle of water on a burner of its own exchanges no heat with the engine's reservoirs, so the work done by the "
            "engine per cycle is still fixed by its stated heat and reservoir temperatures.",
            ("kettle",), ("the engine", "hot reservoir")),
    "S25": ("A small lamp, wired to its own battery, stands beside the coil; neither current nor magnetic flux passes between the lamp's circuit and the coil.",
            "A lamp on its own battery closes a loop of its own and shares no node with the coil, so the coil's steady current "
            "and stored energy are unchanged.", ("lamp",), ("the coil", "coil")),
    "S28": ("A motorbike waits at the roadside, off the road and clear of the car and the truck.",
            "A motorbike waiting at the roadside is not on the road section where the car and the truck move, so the "
            "kinematics of the chase are unchanged.", ("motorbike",), ("the car", "the truck")),
    "S29": ("A small crane stands beside the sled and touches neither the sled nor the rope.",
            "A crane beside the sled does not touch the sled or its rope, so the power of the rope is unchanged.",
            ("crane",), ("the sled", "the rope")),
    "S31": ("A surveyor stands further along the cliff edge, clear of the stone's path.",
            "A surveyor standing along the cliff edge is not on the stone's path and exerts no force on the stone, so the "
            "stone's flight is unchanged.", ("surveyor",), ("thrower", "the stone", "the cliff edge")),
    "S32": ("A trolley stands on a neighbouring table. The spring is ideal and its mass is negligible.",
            "A trolley on a neighbouring table is not touched by the spring, the block or its table, so the block's slide is "
            "unchanged.", ("trolley",), ("the block",)),
    "S33": ("A toy cart stands on the floor beside the wall, clear of the ball's path.",
            "A toy cart beside the wall is not in the line of the impact and does not touch the ball, so the impact is unchanged.",
            ("cart",), ("the ball",)),
    "S34": ("A solar panel stands beside the incline. Air resistance and rolling resistance are negligible, and the incline is long enough for the sphere to come to rest on it.",
            "A solar panel beside the incline does not touch the sphere or the incline, so the sphere's roll is unchanged.",
            ("solar panel",), ("the incline", "the sphere")),
    "S35": ("A fishing reel lies on the bench, apart from the bob and its string. The string does not stretch.",
            "A fishing reel on the bench does not touch the bob or its string, so the motion of the bob is unchanged.",
            ("reel",), ("the string", "the bob")),
    "S36": ("A see-saw stands nearby, clear of the rod and its axis.",
            "A see-saw nearby does not touch the rod or its pivot, so the rod's oscillation is unchanged.",
            ("see-saw",), ("the rod",)),
    "S37": ("A space station orbits in a different plane and never comes close to the satellite.",
            "A space station in another plane exerts a negligible force on the satellite (the problem neglects the gravity of "
            "other bodies), so the satellite's orbit is unchanged.", ("space station",), ("the satellite",)),
    "S38": ("A hinged shutter is propped open beside the ladder. The person stands still on the ladder.",
            "A shutter propped open beside the ladder does not touch the ladder, the wall surface it leans on or the ground "
            "under it, so the forces on the ladder are unchanged.", ("shutter",), ("the ladder",)),
    "S41": ("A pair of bar magnets lies on the bench. The spheres are insulated from their surroundings, and no other charges are near them.",
            "Bar magnets exert no electrostatic force on conducting spheres, so the force between the spheres is unchanged.",
            ("magnets",), ("the spheres are", "the spheres")),
    "S42": ("A small lamp, wired to a battery of its own, stands beside the circuit. The leads have negligible resistance, and the wire stays at a constant temperature.",
            "A lamp on a battery of its own closes a loop of its own and shares no node with the wire, so the wire still sees "
            "only the stated battery.", ("lamp",), ("the battery", "the wire")),
    "S43": ("A small lamp, wired to a battery of its own, stands beside the capacitor. The leads have negligible resistance, and edge effects at the plates are negligible.",
            "A lamp on a battery of its own closes a loop of its own and shares no node with the capacitor, so the capacitor "
            "still sees only the stated battery and its charge is unchanged.", ("lamp",), ("the battery", "the capacitor")),
    "S44": ("A small compass lies on the bench nearby. The wires that carry current to the rod exert no force on it.",
            "A compass lying on the bench does not touch the rod and is not in the magnet's field at the rod, so the force "
            "balance on the rod is unchanged.", ("compass",), ("in which the rod lies", "the rod")),
    "S45": ("A small bulb is wired to a supply of its own beside the apparatus. No electric field acts on the bead outside the gap.",
            "A bulb on a supply of its own does not change the potential difference across the bead's gap, so the bead's speed "
            "and path are unchanged.", ("bulb",), ("the accelerating gap", "the bead")),
}

# What the H4 trace extractor must read as a statement of the target: the target phrase of the question and its head noun, and the
# conventional symbols of the target quantity (see `roles_m0v2.TARGET_TERMS`).
TARGET_TERMS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "S24": (("net work", "work done", "work"), ("W", "W_net")),
    "S25": (("energy stored", "stored energy", "energy"), ("U", "W", "U_B", "E")),
    "S28": (("how long", "time"), ("t",)),
    "S29": (("power",), ("P",)),
    "S31": (("horizontal distance", "distance"), ("x", "d", "R")),
    "S32": (("total distance", "distance"), ("s", "d", "x")),
    "S33": (("average force", "force"), ("F", "F_avg")),
    "S34": (("how far along the incline", "distance along the incline", "distance"), ("d", "s", "x")),
    "S35": (("time for one complete revolution", "period", "time"), ("T",)),
    "S36": (("period of the small oscillations", "period"), ("T",)),
    "S37": (("orbital period", "period"), ("T",)),
    "S38": (("total force that the ground exerts", "total force", "force"), ("F", "R", "F_g")),
    "S41": (("force between the spheres", "force"), ("F", "F'", "F_2")),
    "S42": (("power", "power dissipated"), ("P",)),
    "S43": (("additional charge", "charge"), ("ΔQ", "dQ", "Q")),
    "S44": (("current",), ("I",)),
    "S45": (("radius of the circular path", "radius"), ("r", "R")),
}

NO_C: dict[str, str] = {
    "S28": "The catch-up time 2 v / a is the answer of two stated quantities; no further quantity enters a relation and cancels.",
    "S32": "Every quantity of the base (k, x, m, mu, g) changes the distance; no additional quantity of the system enters and cancels.",
    "S33": "The force is the impulse over the contact time; every stated quantity enters it and no further quantity cancels.",
    "S43": "C0, d, t, kappa and V fix the series capacitance; a plate area would over-determine C0 (it is fixed by C0 and d).",
    "S44": "I = m g / (B L) contains each stated quantity once; no further quantity enters and cancels.",
    "S45": "r = sqrt(2 m V / q) / B contains each stated quantity; no further quantity enters and cancels.",
}
NO_K: dict[str, str] = {
    "S24": "A reversible engine between two reservoirs has no stated or implicit regime that can fail.",
    "S31": "No quantity decides between regimes; air resistance and level ground are stated idealisations.",
    "S33": "Rigid wall and negligible weight are stated idealisations; a finite wall mass would contradict 'rigid wall'.",
    "S35": "No stated idealisation has a quantity that decides it with a closed-form out-of-regime answer.",
    "S36": "The small-amplitude regime has no out-of-regime law that differs by more than 1% at amplitudes still called small.",
    "S37": "A decaying orbit has no period, so a drag regime has no out-of-regime answer.",
    "S41": "The point-charge idealisation has no closed-form out-of-regime law for conducting spheres.",
    "S42": "The constant-resistivity idealisation has no stated quantity with a closed-form regime law.",
    "S43": "Breakdown of the dielectric would short the capacitor: no answer exists outside the regime.",
    "S45": "Non-relativistic motion in a vacuum is stated; no quantity decides it with a closed-form out-of-regime answer.",
}

_ALL = (S24, S25, S28, S29, S31, S32, S33, S34, S35, S36, S37, S38, S41, S42, S43, S44, S45)


def _with_scene(spec: r2.RoleSpecV2) -> r2.RoleSpecV2:
    clause, rationale, refs, target_terms = SCENES[spec.structure_id]
    return dataclasses.replace(spec, version=V21, scene_clause=clause, scene_object_rationale=rationale, scene_refs=refs,
                               target_terms=target_terms)


SPECS: dict[str, r2.RoleSpecV2] = {s.structure_id: _with_scene(s) for s in _ALL}
STRUCTURE_FACTORIES = {
    "S24": library_c.s24_carnot_work,
    "S25": library_c.s25_inductor_energy,
    "S28": library_c.s28_catch_up_time,
    "S29": library_c.s29_power_of_angled_force,
    "S31": lib_mechanics.s31_cliff_throw_distance,
    "S32": lib_mechanics.s32_spring_launch_slide,
    "S33": lib_mechanics.s33_wall_bounce_force,
    "S34": lib_mechanics.s34_rolling_sphere_up_incline,
    "S35": lib_mechanics.s35_conical_pendulum_period,
    "S36": lib_mechanics.s36_rod_physical_pendulum,
    "S37": lib_mechanics.s37_circular_orbit_period,
    "S38": lib_mechanics.s38_ladder_ground_force,
    "S41": lib_electromagnetism.s41_charge_sharing,
    "S42": lib_electromagnetism.s42_stretched_wire_power,
    "S43": lib_electromagnetism.s43_dielectric_slab_charge,
    "S44": lib_electromagnetism.s44_wire_levitation_current,
    "S45": lib_electromagnetism.s45_bead_circle_radius,
}


def structure(structure_id: str) -> gr.Structure:
    """The October structure with the spec's scene clause appended to its base context."""

    return r2.with_scene(STRUCTURE_FACTORIES[structure_id](), SPECS[structure_id].scene_clause)
