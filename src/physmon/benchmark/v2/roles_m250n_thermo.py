"""M250 phase 2, batch thermo: v2.1 role-by-value specifications for the new structures S221 to S230 (plan revision v2.2, section G and the
wording rules of the M0 v2.1/v2.2 panel review; admission standard 3.2, 6.1, 6.2, 6.3).

Every spec follows `roles_m0v21` (the v2.1 design) on instance 0 of the new structure:

* one R/D quantity with three study values and two held-out values; a co-present D (pair 0, `other_object_same_scene`) whose object is
  introduced by a number-free scene clause in the base context of every cell, and a same-object D (pair 1, `same_object_other_event`: a
  different run or survey, never a change applied and then reversed), the same frame, numeral and unit within a pair, an
  attachment-only difference, word counts within three, marker- and consequence-free wording, value hygiene;
* the five wording rules of the panel review: (1) a pair-1 R sentence says that the event is part of the very situation the question
  asks about, in the present tense, before the asked moment; (2) no R sentence contradicts a stated base value (the R quantity is a
  further, added item, and where a base value is modified the base states it as a loading or starting value); (3) the action on the
  co-present object is an ordinary, purposeful one for that object; (4) the co-present object is never of the same type as the target;
  (5) the present tense of the question is matched by present-tense R sentences tied to the asked moment;
* a C quantity where the physics supports a real cancellation (S221 to S226, S228, S229); the familiarity of each is tagged;
* a K quantity where a genuine regime condition of the physics itself exists (S221, S223, S229); the kind of regime is recorded in
  `K_KINDS`. K_out is recorded as infeasible with the reason in every case.

`INFEASIBLE` holds the structures that cannot honestly carry the design (none in this batch); `NO_C` and `NO_K` hold the reason a
structure has no C or K quantity, so that an absence is a judgement on record and not an omission.
"""

from __future__ import annotations

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import lib_m250_thermo as lt
from physmon.benchmark.v2 import rolevalue as rv
from physmon.benchmark.v2 import rolevalue_v2 as r2

P = rv.Phrasing
Pair = r2.PhrasePair
CO = r2.D_KIND_CO_PRESENT
EVENT = r2.D_KIND_OTHER_EVENT
V21 = r2.VERSION_V21


def _spec(sid: str, **fields) -> r2.RoleSpecV2:
    return r2.RoleSpecV2(structure_id=sid, version=V21, author="agent (M250 phase 2, thermo)", **fields)


def _ko(reason: str) -> r2.KOut:
    return r2.KOut(False, reason)


# --- S221 --------------------------------------------------------------------------------------------------------------------------

S221_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the pressure of the gas", "pressure", "kPa", (150.0, 220.0, 410.0), "The gas {relation} {value} {unit}.",
        (P("c0", "is held at a pressure of"), P("c1", "stays at a pressure of")),
        "n*5*R*(T2 - T1)/2 + q*(n*R*(T2 - T1)/q)",
        ("p V = n R T, so the volume change is dV = n R dT / p", "work done by the gas W = p dV = p (n R dT / p)",
         "Q = n (5 R / 2) dT + p dV"),
        "n*3*R*(T2 - T1)/2 + q*(n*R*(T2 - T1)/q)", nonnumeric_fill="a known pressure"),
    "standard", "That the heat at constant pressure does not depend on the value of the pressure follows from Q = n Cp dT but is "
                "not stated as a fact in a first treatment.", (180.0, 330.0))

S221_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the characteristic temperature of the vibration", "temperature", "K", (2800.0, 3300.0, 4100.0),
        "The characteristic temperature of the vibrational motion of a nitrogen molecule {relation} {value} {unit}.",
        (P("k0", "is"), P("k1", "is quoted as")), "5*T2 < q", "9*n*R*(T2 - T1)/2", 1500.0, nonnumeric_fill="a known value"),
    _ko("A characteristic vibrational temperature of the order of the final temperature would excite the vibration and contradict the "
        "stated condition that the vibrational motion is not excited, so the question 'how much heat is supplied' would describe a "
        "different gas; the premise is contradicted, not merely changed."),
    (3100.0, 3700.0))

S221 = _spec(
    "S221", quantity_phrase="a further amount of nitrogen", quantity_type="amount", unit="mol", values=(0.7, 1.3, 2.4),
    heldout_values=(0.9, 1.8),
    relevant=rv.RelevantWiring("n", "add", "Further nitrogen at the same temperature in the cylinder when the heating begins adds to the "
                                           "amount of gas that is heated, so n becomes n + q."),
    cancelling=S221_C, conditional=S221_K,
    scene_clause="A steel gas bottle with a regulator stands beside the cylinder.",
    scene_object_rationale="A gas bottle with a regulator is a store of gas outside the cylinder; gas let into it is not in the "
                           "cylinder, so the amount of gas that is heated is the stated one.",
    scene_refs=("gas bottle",), target_terms=("the cylinder", "piston", "nitrogen"),
    pairs=(
        Pair("p0", "Before the heating begins, a further {value} {unit} of nitrogen at the same temperature is {relation}.",
             "let into the cylinder", "let into the gas bottle", CO,
             "Gas let into the gas bottle stays in the bottle; the cylinder keeps its stated amount of gas, and the pressure, "
             "temperatures and molecular motions of the problem are those stated.",
             ("heated slowly at constant pressure", "vibrational motion is not excited"), "small amount",
             before_context_reason="The R sentence refers to 'the cylinder' and to 'the same temperature' before the context "
                                   "introduces the cylinder or any temperature."),
        Pair("p1", "{relation} a further {value} {unit} of nitrogen at the same temperature.",
             "When the heating begins, the cylinder also holds", "In an earlier run, the cylinder also held", EVENT,
             "The cylinder held the further nitrogen in an earlier run, which is over; in the stated run the cylinder holds only its "
             "stated amount of gas.", ("heated slowly at constant pressure", "vibrational motion is not excited"), "small amount"),
    ),
    notes="M250 phase 2: C is the pressure of the gas (p dV = n R dT), K is the characteristic temperature of the vibration (frozen "
          "mode).")

# --- S222 --------------------------------------------------------------------------------------------------------------------------

S222_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the duration of the run", "time", "min", (35.0, 80.0, 150.0), "The machines {relation} {value} {unit}.",
        (P("c0", "run steadily for"), P("c1", "are tested for")),
        "(Tc/(Tm - Tc))*(1 - Tm/Th)*(Ph*q)/q",
        ("heat taken from the furnace in the run Q_h = P_h t", "work of the engine W = eta Q_h", "heat removed Q_c = COP W",
         "rate of removal = Q_c / t"),
        "(Tc/(Tm - Tc))*(1 - Tm/Th)*Ph*q", nonnumeric_fill="a known time"),
    "uncommon", "That the rate of heat removal of a steady machine does not depend on how long the run lasts is true but is rarely "
                "stated for a calculation that goes through energy.", (55.0, 110.0))

S222 = _spec(
    "S222", quantity_phrase="a further heat rate", quantity_type="power", unit="kW", values=(7.0, 13.0, 22.0),
    heldout_values=(9.0, 17.0),
    relevant=rv.RelevantWiring("Ph", "add", "Further heat that the furnace supplies to the engine adds to the rate at which the engine "
                                            "takes heat, so P_h becomes P_h + q."),
    cancelling=S222_C,
    scene_clause="A hot-water tank with an electric element stands in the plant room.",
    scene_object_rationale="A hot-water tank with its own element is a store of heat outside the machines; heat supplied to it does "
                           "not reach the engine, so the rate at which the engine takes heat is the stated one.",
    scene_refs=("hot-water tank",), target_terms=("engine", "furnace", "refrigerator", "cold room", "machines"),
    pairs=(
        Pair("p0", "A further {value} {unit} of heat is supplied {relation}.", "to the engine from the furnace",
             "to the hot-water tank by an element", CO,
             "Heat supplied to the hot-water tank by its element stays in the tank; the engine takes heat from the furnace at "
             "its stated rate, and the temperatures of the reservoirs are those stated.",
             ("reversible heat engine", "Both machines run steadily"), "small amount",
             before_context_reason="The R sentence refers to 'the engine' and 'the furnace' before the context introduces them."),
        Pair("p1", "{relation} a further {value} {unit} of heat from the furnace.",
             "While the machines run steadily, the engine takes", "In an earlier test, the engine took", EVENT,
             "The engine took the further heat in an earlier test, which is over; in the stated run it takes heat at its stated "
             "rate.", ("reversible heat engine", "Both machines run steadily"), "small amount"),
    ),
    notes="M250 phase 2: C is the duration of the run (rate = energy / time); no K (see NO_K).")

# --- S223 --------------------------------------------------------------------------------------------------------------------------

S223_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the power of the electric heater", "power", "W", (180.0, 450.0, 900.0), "The ice is heated by an electric heater {relation} {value} {unit}.",
        (P("c0", "of power"), P("c1", "with an output of")),
        "(q*(m*Lf/q))/T0 + m*c*log(Tw/T0)",
        ("time to melt the ice t = m L_f / P", "heat taken in while melting = P t", "entropy of melting = (P t) / T_melt"),
        "(m*Lf/q)/T0 + m*c*log(Tw/T0)", nonnumeric_fill="a known"),
    "standard", "That the entropy produced by a slow heating does not depend on the heater power follows from S = integral of dQ / T "
                "but is not a headline fact.", (260.0, 640.0))

S223_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the boiling point of the water", "temperature", "K", (366.0, 371.0, 378.0),
        "The water {relation} {value} {unit} at the local pressure.", (P("k0", "boils at"), P("k1", "has a boiling point of")),
        "Tw < q", "m*Lf/T0 + m*c*log(q/T0)", 300.0, nonnumeric_fill="a known temperature"),
    _ko("A boiling point at or below the final temperature would make the water boil before it reaches that temperature, which "
        "contradicts the stated condition that the water stays liquid; the premise is contradicted, not merely changed."),
    (368.0, 375.0))

S223 = _spec(
    "S223", quantity_phrase="a further mass of ice", quantity_type="mass", unit="kg", values=(0.07, 0.13, 0.36),
    heldout_values=(0.09, 0.22),
    relevant=rv.RelevantWiring("m", "add", "Further ice at its melting point in the block when the heating begins adds to the mass that "
                                           "melts and warms, so m becomes m + q."),
    cancelling=S223_C, conditional=S223_K,
    scene_clause="A water dispenser stands in the corridor outside the laboratory.",
    scene_object_rationale="A water dispenser is a store of water and ice outside the laboratory; ice put into it is not part of the "
                           "block that is heated, so the mass of ice that melts is the stated one.",
    scene_refs=("dispenser",), target_terms=("block", "meltwater", "heated slowly"),
    pairs=(
        Pair("p0", "Before the heating begins, a further {value} {unit} of ice at its melting point is {relation}.",
             "added to the block", "put into the dispenser", CO,
             "Ice put into the dispenser stays there; the block keeps its stated mass, and the heating, the melting and the final "
             "temperature of the problem are those stated.", ("heated slowly", "melted completely"), "small amount",
             before_context_reason="The R sentence refers to 'the block' and 'the heating' before the context introduces them."),
        Pair("p1", "{relation} a further {value} {unit} of ice at its melting point.",
             "When the heating begins, the block also includes", "In an earlier run, the block also included", EVENT,
             "The block included the further ice in an earlier run, which is over; in the stated run the block has only its "
             "stated mass.", ("heated slowly", "melted completely"), "small amount"),
    ),
    notes="M250 phase 2: C is the power of the heater (the heat is P t), K is the boiling point of the water (phase state).")

# --- S224 --------------------------------------------------------------------------------------------------------------------------

S224_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the volume of the container", "volume", "L", (12.0, 42.0, 75.0), "The container {relation} {value} {unit}.",
        (P("c0", "has a volume of"), P("c1", "has an internal volume of")),
        "n1*R*log(q/((n1/n)*q)) + n2*R*log(q/((n2/n)*q))",
        ("at equal temperature and pressure each compartment has the volume V_i = x_i V", "entropy of each gas dS_i = n_i R ln(V / V_i)",
         "dS = sum of dS_i"),
        "n*R*log(q/(q/2))", nonnumeric_fill="a known volume"),
    "uncommon", "That the entropy of mixing does not depend on the size of the container follows from the mole-fraction form but is "
                "rarely stated.", (20.0, 50.0))

S224 = _spec(
    "S224", quantity_phrase="a further amount of helium", quantity_type="amount", unit="mol", values=(0.7, 1.3, 2.4),
    heldout_values=(0.9, 1.9),
    relevant=rv.RelevantWiring("n1", "add", "Further helium in the helium compartment before the gases mix adds to the amount "
                                            "of helium (the sliding partition keeps the pressures equal), so n1 becomes n1 + q."),
    cancelling=S224_C,
    scene_clause="A balloon hangs from a hook beside the container.",
    scene_object_rationale="A balloon on a hook is a separate store of gas outside the container; helium let into it is not in "
                           "the container, so the amounts of the two gases that mix are the stated ones.",
    scene_refs=("balloon",), target_terms=("helium compartment", "partition", "container", "argon"),
    pairs=(
        Pair("p0", "Before the gases are allowed to mix, a further {value} {unit} of helium is {relation}.",
             "let into the helium compartment", "let into the balloon", CO,
             "Helium let into the balloon stays in the balloon; the compartments keep their stated amounts of gas, and the "
             "temperature, the equal pressures and the mixing of the problem are those stated.",
             ("thermally insulated", "mix completely"), "small amount",
             before_context_reason="The R sentence refers to 'the helium compartment' and 'the partition' before the context "
                                   "introduces them."),
        Pair("p1", "{relation} a further {value} {unit} of helium.",
             "Before the gases are allowed to mix, the helium compartment also holds", "In an earlier run, the helium compartment also held",
             EVENT,
             "The compartment held the further helium in an earlier run, which is over; in the stated run it holds only its stated "
             "amount of helium.", ("thermally insulated", "mix completely"), "small amount"),
    ),
    notes="M250 phase 2: C is the volume of the container (the mole-fraction form); no K (see NO_K).")

# --- S225 --------------------------------------------------------------------------------------------------------------------------

S225_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the thermal conductivity of the insulation", "thermal_conductivity", "W/(m*K)", (0.065, 0.07, 0.15),
        "The insulation {relation} {value} {unit}.", (P("c0", "has a thermal conductivity of"), P("c1", "conducts heat with a conductivity of")),
        "(2*pi*q*(Tin - Tout)/log(r2/r1))*(log(rm/r1)/(2*pi*q))",
        ("heat current per unit length P/L = 2 pi k (T_in - T_out) / ln(r2 / r1)",
         "temperature drop to the asked radius = (P/L) ln(rm / r1) / (2 pi k)"),
        "(2*pi*q*(Tin - Tout)/log(r2/r1))*(log(rm/r1)/(2*pi))", nonnumeric_fill="a known conductivity"),
    "standard", "That the temperature profile in steady conduction does not depend on the conductivity of a uniform layer is taught "
                "for the plane wall; for a cylinder it is stated less often.", (0.085, 0.12))

S225 = _spec(
    "S225", quantity_phrase="a further layer of insulation", quantity_type="length", unit="cm", values=(2.5, 4.0, 7.5),
    heldout_values=(3.5, 6.5),
    relevant=rv.RelevantWiring("r2", "add", "A further layer of the same insulation wrapped round the layer puts the outer surface at "
                                            "r2 + q, the outermost surface staying at the stated temperature."),
    cancelling=S225_C,
    scene_clause="A hot-water tank stands beside the pipe.",
    scene_object_rationale="A hot-water tank is lagged separately from the pipe; insulation wrapped round the tank leaves the "
                           "insulation on the pipe, its radii and its surface temperatures as stated.",
    scene_refs=("hot-water tank",), target_terms=("pipe", "layer", "axis"),
    pairs=(
        Pair("p0", "A further {value} {unit} of the same insulation is wrapped {relation}.",
             "round the layer on the pipe", "round the hot-water tank", CO,
             "Insulation wrapped round the hot-water tank lies outside the pipe's layer; the pipe keeps its insulation out to the "
             "stated radius and the stated surface temperatures.", ("purely radial", "uniform layer of insulation"), "small thickness",
             before_context_reason="The R sentence refers to 'the layer' and 'the pipe' before the context introduces them."),
        Pair("p1", "{relation} a further {value} {unit} of the same insulation.",
             "While the temperatures are held, the layer is wrapped in", "In an earlier survey, the layer was wrapped in", EVENT,
             "The layer was wrapped in the further insulation in an earlier survey, which is over; in the stated survey it extends "
             "out to the stated radius.", ("purely radial", "uniform layer of insulation"), "small thickness"),
    ),
    notes="M250 phase 2: C is the conductivity of the insulation (cancels in the ratio of resistances); no K (see NO_K).")

# --- S226 --------------------------------------------------------------------------------------------------------------------------

S226_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the emissivity of the surfaces", "ratio", "1", (0.35, 0.6, 0.9), "The emissivity of every surface {relation} {value}.",
        (P("c0", "is"), P("c1", "has the value")),
        "(T1**4 - ((q/(2 - q))*(T1**4 - T2**4)/3)/(q/(2 - q)))**(1/4)",
        ("net flux between neighbouring grey surfaces F = sigma (eps / (2 - eps)) (Ta^4 - Tb^4)",
         "equal fluxes across the three gaps: F = G (T1^4 - T2^4) / 3 with G = sigma eps / (2 - eps)",
         "fall of T^4 across the first gap = F / G"),
        "((T1**4 + T2**4)/2)**(1/4)*(q/q)", nonnumeric_fill="a known value"),
    "standard", "That the temperatures of the shields do not depend on the common emissivity is a textbook result for equal "
                "emissivities but is not a headline fact.", (0.45, 0.65))

S226 = _spec(
    "S226", quantity_phrase="a further warming of the hot plate", quantity_type="temperature_change", unit="K",
    values=(35.0, 70.0, 140.0), heldout_values=(50.0, 105.0),
    relevant=rv.RelevantWiring("T1", "add", "A heater that warms the hot plate by q makes its temperature T1 + q."),
    cancelling=S226_C,
    scene_clause="A kettle stands on a hob in the corner of the laboratory.",
    scene_object_rationale="A kettle on a hob is a store of hot water outside the vacuum between the plates; warming its water does "
                           "not change the temperature of either plate or of a shield.",
    scene_refs=("kettle",), target_terms=("plate", "shield"),
    pairs=(
        Pair("p0", "A heater warms {relation} by {value} {unit}.", "the hot plate", "the water in the kettle", CO,
             "Warming the water in the kettle leaves the hot plate, the cold plate and the shields at their stated temperatures "
             "and surface properties.", ("diffuse and grey", "the situation is steady"), "a few kelvin",
             before_context_reason="The R sentence refers to 'the hot plate' before the context introduces it."),
        Pair("p1", "{relation} the hot plate by {value} {unit}.",
             "While the shields settle, a heater is warming", "In an earlier run, a heater warmed", EVENT,
             "A heater warmed the hot plate in an earlier run, which is over; in the stated run the hot plate is at its stated "
             "temperature.", ("diffuse and grey", "the situation is steady"), "a few kelvin"),
    ),
    notes="M250 phase 2: C is the common emissivity of the surfaces; no K (see NO_K).")

# --- S227 --------------------------------------------------------------------------------------------------------------------------

S227 = _spec(
    "S227", quantity_phrase="a further warming of the gas", quantity_type="temperature_change", unit="K",
    values=(22.0, 38.0, 70.0), heldout_values=(25.0, 50.0),
    relevant=rv.RelevantWiring("T", "add", "A heater that warms the gas by q makes its temperature T + q."),
    scene_clause="A water bath stands on the bench in the laboratory.",
    scene_object_rationale="A water bath is a vessel of water with its own thermometer; warming its water does not change the "
                           "temperature of the gas, whose temperature is stated.",
    scene_refs=("water bath",), target_terms=("gas", "molecule", "level"),
    pairs=(
        Pair("p0", "A heater warms {relation} by {value} {unit}.", "the gas", "the water bath", CO,
             "Warming the water bath leaves the gas at its stated temperature and its levels, degeneracy and equilibrium as "
             "stated.", ("thermal equilibrium", "so high that it is empty"), "a few kelvin",
             before_context_reason="The R sentence refers to 'the gas' before the context introduces it."),
        Pair("p1", "{relation} the gas by {value} {unit}.",
             "While the molecules equilibrate, a heater is warming", "In an earlier run, a heater warmed", EVENT,
             "A heater warmed the gas in an earlier run, which is over; in the stated run the gas is at its stated temperature.",
             ("thermal equilibrium", "so high that it is empty"), "a few kelvin"),
    ),
    notes="M250 phase 2: no C or K (see NO_C, NO_K).")

# --- S228 --------------------------------------------------------------------------------------------------------------------------

S228_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the area of each face of the plate", "area", "m^2", (0.42, 0.8, 1.6), "The plate {relation} {value} {unit}.",
        (P("c0", "has faces of area"), P("c1", "has a face area of")),
        "rho*c*(d*q/(2*q))/h*log((T0 - Te)/(Tt - Te))",
        ("volume of the plate V = d A", "heat capacity of the plate = rho c V", "heat loss coefficient of both faces = 2 h A",
         "time constant = rho c V / (2 h A)"),
        "rho*c*(d*q)/(2*h)*log((T0 - Te)/(Tt - Te))", nonnumeric_fill="a known area"),
    "standard", "That the cooling time of a lumped plate depends on its thickness and not on its face area is basic heat-transfer "
                "knowledge but is not stated as a fact.", (0.55, 1.2))

S228 = _spec(
    "S228", quantity_phrase="a draught of air", quantity_type="heat_transfer_coefficient", unit="W/(m^2*K)", values=(7.0, 13.0, 29.0),
    heldout_values=(11.0, 19.0),
    relevant=rv.RelevantWiring("h", "add", "A fan that adds q to the heat transfer coefficient of each face makes it h + q."),
    cancelling=S228_C,
    scene_clause="A finned heat sink for a furnace controller stands on the bench.",
    scene_object_rationale="A finned heat sink is cooled by its own fan; the fan changes the heat transfer of the heat sink and "
                           "leaves the coefficient of each face of the plate at its stated value.",
    scene_refs=("heat sink",), target_terms=("plate", "face"),
    pairs=(
        Pair("p0", "A fan adds {value} {unit} to the heat transfer coefficient of {relation}.", "each face of the plate",
             "the fins of the heat sink", CO,
             "A fan that cools the fins of the heat sink leaves the heat transfer coefficient of each face of the plate at its "
             "stated value.", ("convection", "the same throughout"), "a little",
             before_context_reason="The R sentence refers to 'each face of the plate' before the context introduces the plate."),
        Pair("p1", "{relation} {value} {unit} to the heat transfer coefficient of each face of the plate.",
             "While the plate cools, a fan is adding", "In an earlier run, a fan added", EVENT,
             "A fan added to the coefficient in an earlier run, which is over; in the stated run each face has its stated "
             "coefficient.", ("convection", "the same throughout"), "a little"),
    ),
    notes="M250 phase 2: C is the face area of the plate (V / A is d / 2); no K (see NO_K).")

# --- S229 --------------------------------------------------------------------------------------------------------------------------

S229_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the mass of the bullet", "mass", "g", (5.8, 8.2, 14.0), "The bullet {relation} {value} {unit}.",
        (P("c0", "has a mass of"), P("c1", "is cast with a mass of")),
        "T0 + f*(q*v**2/2)/(q*c)",
        ("kinetic energy of the bullet E = m v^2 / 2", "heat taken in Q = f E", "Q = m c dT"),
        "T0 + f*(q*v**2/2)/c", nonnumeric_fill="a known mass"),
    "famous", "That the mass of a falling or moving body drops out of the temperature rise from its kinetic energy is a standard "
              "textbook exercise.", (6.4, 11.0))

S229_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the melting point of the metal", "temperature", "K", (540.0, 585.0, 640.0), "The metal of the bullet {relation} {value} {unit}.",
        (P("k0", "melts at"), P("k1", "has a melting point of")), "Tf < q", "q", 370.0, nonnumeric_fill="a known temperature"),
    _ko("A melting point below the final temperature would make the bullet melt, which contradicts the stated condition that the "
        "bullet stays solid; the premise is contradicted, not merely changed."),
    (560.0, 610.0))

S229 = _spec(
    "S229", quantity_phrase="a warming by sunshine", quantity_type="temperature_change", unit="K", values=(9.0, 17.0, 31.0),
    heldout_values=(12.0, 24.0),
    relevant=rv.RelevantWiring("T0", "add", "Sunshine that has warmed the bullet by q before the shot makes the temperature at the "
                                            "impact T0 + q."),
    cancelling=S229_C, conditional=S229_K,
    scene_clause="A steel target frame stands on the range.",
    scene_object_rationale="A steel target frame is a structure beside the plate that the bullet hits; sunshine that warms it does "
                           "not warm the bullet, so the temperature of the bullet is the stated one.",
    scene_refs=("target frame",), target_terms=("bullet", "plate"),
    pairs=(
        Pair("p0", "Sunshine has warmed {relation} by {value} {unit}.", "the bullet", "the target frame", CO,
             "Sunshine that has warmed the target frame leaves the bullet at its stated temperature and its speed and fraction of "
             "kinetic energy as stated.", ("stops in it", "stays solid"), "a few kelvin",
             before_context_reason="The R sentence refers to 'the bullet' before the context introduces it."),
        Pair("p1", "{relation} the bullet by {value} {unit}.",
             "Before the shot, sunshine has warmed", "On an earlier day, sunshine warmed", EVENT,
             "Sunshine warmed the bullet on an earlier day, which is over; at the stated shot the bullet is at its stated "
             "temperature.", ("stops in it", "stays solid"), "a few kelvin"),
    ),
    notes="M250 phase 2: C is the mass of the bullet (famous), K is the melting point of the metal (phase state).")

# --- S230 --------------------------------------------------------------------------------------------------------------------------

S230 = _spec(
    "S230", quantity_phrase="a further mass of metal", quantity_type="mass", unit="kg", values=(0.6, 1.1, 3.4),
    heldout_values=(0.8, 1.7),
    relevant=rv.RelevantWiring("m1", "add", "Further metal of the same kind at the temperature of the hotter block joined to that block "
                                            "adds to its mass, so m1 becomes m1 + q."),
    scene_clause="A casting mould stands beside the enclosure.",
    scene_object_rationale="A casting mould is a vessel for metal outside the enclosure; metal poured into it is not part of either "
                           "block, so the masses and temperatures of the two blocks are the stated ones.",
    scene_refs=("mould",), target_terms=("hotter block", "colder block", "enclosure"),
    pairs=(
        Pair("p0", "A further {value} {unit} of the same metal, at the temperature of the hotter block, is {relation}.",
             "added to the hotter block", "poured into the mould", CO,
             "Metal poured into the mould is not part of either block; the blocks keep their stated masses and initial "
             "temperatures.", ("rigid, perfectly insulated enclosure", "common temperature"), "small amount",
             before_context_reason="The R sentence refers to 'the hotter block' before the context introduces the blocks."),
        Pair("p1", "{relation} a further {value} {unit} of the same metal.",
             "Before the blocks touch, the hotter block also includes", "In an earlier run, the hotter block also included", EVENT,
             "The hotter block included the further metal in an earlier run, which is over; in the stated run it has only its "
             "stated mass.", ("rigid, perfectly insulated enclosure", "common temperature"), "small amount"),
    ),
    notes="M250 phase 2: no C or K (see NO_C, NO_K).")


ROLE_SPECS: dict[str, r2.RoleSpecV2] = {s.structure_id: s for s in (S221, S222, S223, S224, S225, S226, S227, S228, S229, S230)}
SPECS = ROLE_SPECS

STRUCTURE_FACTORIES = {f().structure_id: f for f in lt.ALL}

K_KINDS: dict[str, str] = {
    "S221": "frozen internal mode (characteristic vibrational temperature far above the temperature of the gas)",
    "S223": "phase state (boiling point above the final temperature of the water)",
    "S229": "phase state (melting point above the final temperature of the bullet)",
}

# Structures that cannot honestly carry the design. None in this batch.
INFEASIBLE: dict[str, str] = {}

NO_C: dict[str, str] = {
    "S227": "Every stated quantity (gap, degeneracy, temperature, gas constant) enters the Boltzmann weight and survives in the mean "
            "energy; a number of molecules or a volume appears in no stated relation, so nothing enters and cancels.",
    "S230": "Both masses, both temperatures and the specific heat all survive in the entropy generated; a free quantity such as the "
            "enclosure volume appears in no relation, so nothing enters and cancels.",
}
NO_K: dict[str, str] = {
    "S222": "The only regime (the cold room colder than the surroundings, the furnace hotter) is a property of the stated "
            "temperatures, not of a further quantity with a threshold, and has no definite out-of-regime answer.",
    "S224": "The regime of ideal-gas behaviour has no sharp threshold quantity and the entropy of mixing has no definite answer for "
            "a gas outside it; identical gases (zero entropy of mixing) are a different structure, not a numerical threshold.",
    "S225": "A pipe length that makes the radial approximation good approaches the regime asymptotically, with no exact threshold, "
            "and no definite out-of-regime temperature.",
    "S226": "A gas pressure below which convection is negligible has no sharp threshold and no definite out-of-regime answer for "
            "the shield temperature.",
    "S227": "A higher level at an energy q above the ground level changes the mean energy continuously and by less than the grading "
            "tolerance inside any regime in which it is 'empty', so no out-of-regime law separates from the in-regime answer "
            "at the study values.",
    "S228": "The Biot number condition changes the answer continuously and by less than the grading tolerance inside the regime, "
            "so no out-of-regime law separates from the in-regime answer at the study values.",
    "S230": "A melting point above the hotter block's temperature would be a regime condition, but no definite out-of-regime "
            "answer is defined by the stated relations (the latent heat is not given).",
}


def structure(structure_id: str) -> gr.Structure:
    """The new structure with the spec's scene clause appended to its base context."""

    return r2.with_scene(lt.STRUCTURES[structure_id], ROLE_SPECS[structure_id].scene_clause)


# What the H4 trace extractor (`TraceContext.target_phrases` / `target_symbols`) must read as a statement of the target: a phrase of the
# question, its head noun and the conventional symbols of the target quantity (and the graph's target node name).
TARGET_TERMS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "S221": (("heat is supplied to the gas", "heat supplied", "heat"), ("Q", "Q_p")),
    "S222": (("rate does the refrigerator remove heat", "remove heat", "rate"), ("Qc", "Q_c", "Q_dot_c")),
    "S223": (("total change of entropy", "change of entropy", "entropy"), ("S", "ΔS", "dS")),
    "S224": (("total entropy change", "entropy change", "entropy"), ("dS", "ΔS", "S")),
    "S225": (("temperature fall from the outer surface", "temperature fall", "kelvin"), ("dTm", "ΔT", "ΔT_m")),
    "S226": (("temperature of the shield", "temperature"), ("Ts", "T_s", "T")),
    "S227": (("mean energy of the molecules", "mean energy", "energy"), ("U", "E_mean", "E")),
    "S228": (("long does the plate take to cool", "time to cool", "how long"), ("tc", "t_c", "t")),
    "S229": (("temperature of the bullet", "temperature"), ("Tf", "T_f", "T")),
    "S230": (("entropy is generated", "entropy generated", "entropy"), ("Sg", "S_g", "ΔS_gen")),
}
