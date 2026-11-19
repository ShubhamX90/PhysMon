"""M250 phase 1, batch c: v2.1 role-by-value specifications for October structures S46, S47, S48, S51, S52, S53, S54, S56, S57,
S61, S62, S63, S64, S65, S66, S67 and S71 (plan revision v2.2, section G; admission standard 3.2, 6.1, 6.2, 6.3).

Every spec follows `roles_m0v21` (the M0 v2.1 design) on instance 0 of the October structure, whose graph is unchanged:

* one R/D quantity with three study values and two held-out values; a co-present D (pair 0, `other_object_same_scene`) whose object is
  introduced by a number-free scene clause in the base context of every cell, and a same-object D (pair 1, `same_object_other_event`:
  history in an earlier experiment, never a change applied and then reversed), the same frame, numeral and unit within a pair, an
  attachment-only difference, word counts within three, marker- and consequence-free wording, value hygiene;
* a C quantity where the physics supports a real cancellation (10 of 17 structures; 1 of the 10 tagged famous);
* a K quantity where a genuine threshold regime exists (7 of 17); K_out is recorded as infeasible with the reason in every case.

`INFEASIBLE` holds the structures that cannot honestly carry the design (none in this batch); `NO_C` and `NO_K` hold the reason a
structure has no C or K quantity, so that an absence is a judgement on record and not an omission.
"""

from __future__ import annotations

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import lib_electromagnetism, lib_optics, lib_quantum, lib_thermodynamics
from physmon.benchmark.v2 import rolevalue as rv
from physmon.benchmark.v2 import rolevalue_v2 as r2

P = rv.Phrasing
Pair = r2.PhrasePair
CO = r2.D_KIND_CO_PRESENT
EVENT = r2.D_KIND_OTHER_EVENT
V21 = r2.VERSION_V21


def _spec(sid: str, **fields) -> r2.RoleSpecV2:
    return r2.RoleSpecV2(structure_id=sid, version=V21, **fields)


# --- S46 -------------------------------------------------------------------------------------------------------------------------

S46 = _spec(
    "S46", quantity_phrase="an extra resistor", quantity_type="resistance", unit="Ω", values=(0.7, 1.3, 2.4),
    heldout_values=(0.9, 1.8),
    relevant=rv.RelevantWiring("R", "add", "A resistor in series with the resistor that joins the rails adds to the only resistance "
                                           "in the loop, so the loop resistance becomes R + q."),
    scene_clause="A small lamp, wired to its own battery, stands beside the rails. The rails are long enough for the rod to approach "
                 "its terminal speed, and the self-inductance of the loop is negligible.",
    scene_object_rationale="A lamp wired to a battery of its own closes a loop that shares no node with the rails or the resistor "
                           "and exerts no force on the rod, so the rod's terminal speed is fixed by the rod, the rails, the field "
                           "and the resistor alone.",
    scene_refs=("lamp",), target_terms=("rails", "rod", "resistor at the lower end"),
    pairs=(
        Pair("p0", "A {value} {unit} resistor is {relation}.", "wired in series with the resistor at the lower end",
             "wired in series with the lamp and its battery", CO,
             "A resistor in series with the lamp and its battery lies in the lamp's own loop; it shares no node with the loop "
             "formed by the rails, the rod and the resistor at the lower end, so the loop resistance of the rod is the stated one.",
             ("without friction", "have no other resistance"), "small",
             before_context_reason="The R sentence refers to 'the resistor at the lower end' before the context introduces any "
                                   "resistor, and 'the lamp' only exists once the scene clause has been read."),
        Pair("p1", "{relation}, a {value} {unit} resistor was wired in series with the resistor that joins the rails.",
             "For this run", "For an earlier run only", EVENT,
             "The resistor was in the rod's loop for an earlier run only, which is over; the loop of the stated run has only its stated "
             "resistor, and the field, the rails and the rod are those of the problem.", ("without friction", "have no other resistance"),
             "small"),
    ),
    notes="M250 phase 1: v2.1 spec for S46 on the October base problem; no C or K (see NO_C, NO_K).")

# --- S47 -------------------------------------------------------------------------------------------------------------------------

S47_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the number of turns of the secondary coil", "count", "1", (150.0, 400.0, 900.0), "The secondary coil {relation} {value} turns.",
        (P("c0", "has"), P("c1", "is wound with")),
        "(((a*q/q)*(Vs/(Rs + (a*q/q)**2*RL)))**2)*RL",
        ("primary turns N1 = a N2", "turns ratio = N1 / N2 = (a N2) / N2", "reflected resistance = (N1 / N2)^2 RL",
         "I2 = (N1 / N2) I1"),
        "((a/q)*(Vs/(Rs + (a/q)**2*RL)))**2*RL", nonnumeric_fill="a known number of"),
    "standard", "That an ideal transformer depends only on its turns ratio, not on the absolute number of turns, is taught with "
                "the reflected-resistance argument but is not a headline fact.", (250.0, 700.0))

S47_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the current rating of a fuse", "current", "A", (6.0, 9.0, 14.0),
        "The primary circuit contains a fuse that {relation} {value} {unit}.",
        (P("k0", "blows only above"), P("k1", "is rated at")), "I1 < q", "0", 0.3, nonnumeric_fill="a known current"),
    r2.KOut(False, "If the fuse blew, the load would carry no current afterwards, but the question 'what average power is dissipated "
                   "in the load' names no time: the answer would be a transient before the blow and zero after it, and a gold of "
                   "exactly zero cannot be graded by a relative tolerance."),
    (7.5, 12.0))

S47 = _spec(
    "S47", quantity_phrase="an extra resistor", quantity_type="resistance", unit="Ω", values=(1.5, 3.5, 7.0),
    heldout_values=(2.5, 5.0),
    relevant=rv.RelevantWiring("Rs", "add", "A resistor in series with the generator adds to its internal resistance, so the "
                                            "series resistance in the primary loop becomes Rs + q."),
    cancelling=S47_C, conditional=S47_K,
    scene_clause="A small heater, supplied by a second generator, stands beside the transformer. The connecting wires and the coils "
                 "have negligible resistance, and the generator has a constant rms emf.",
    scene_object_rationale="A heater supplied by a second generator closes a loop of its own that shares no node with the primary "
                           "circuit or the load, so the voltages and currents of the transformer's circuits are unchanged.",
    scene_refs=("heater",), target_terms=("generator that feeds", "primary coil", "the transformer", "the load"),
    pairs=(
        Pair("p0", "A {value} {unit} resistor is {relation}.", "connected in series with the generator that feeds the primary coil",
             "connected in series with the heater and its generator", CO,
             "A resistor in series with the heater and its generator lies in the heater's own loop; it shares no node with the "
             "primary circuit or the load, so the source resistance of the transformer's generator is the stated one.",
             ("ideal transformer", "purely resistive load"), "small",
             before_context_reason="The R sentence refers to 'the generator that feeds the primary coil' before the context introduces "
                                   "a generator or a primary coil."),
        Pair("p1", "{relation}, a {value} {unit} resistor was connected in series with the generator.", "For this run",
             "For an earlier run only", EVENT,
             "The resistor was in series with the generator for an earlier run only, which is over; the primary loop of the stated run "
             "has only the generator's stated internal resistance and the reflected load.", ("ideal transformer", "purely resistive load"),
             "small"),
    ),
    notes="M250 phase 1: C is the absolute number of secondary turns (real cancellation through the stated turns ratio), K is a fuse "
          "rating above the largest primary current of any instance.")

# --- S48 -------------------------------------------------------------------------------------------------------------------------

S48_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the initial charge on the capacitor", "charge", "μC", (150.0, 480.0, 1200.0), "The capacitor {relation} {value} {unit} of charge.",
        (P("c0", "starts with"), P("c1", "initially holds")),
        "sqrt((q/(Lc*C) - q*(R/(2*Lc))**2)/q)/(2*pi)",
        ("L q'' + R q' + q / C = 0 is linear in the charge", "trial charge Q0 e^(s t): Q0 (L s^2 + R s + 1/C) e^(s t) = 0",
         "omega_d^2 = (Q0 / (L C) - Q0 (R / 2L)^2) / Q0"),
        "fd*(1 + q/(C*10))", nonnumeric_fill="a known amount"),
    "standard", "That the ringing frequency of a linear RLC circuit does not depend on how much charge starts on the capacitor "
                "(amplitude independence of a linear oscillator) is standard but is not stated as a named fact.", (300.0, 900.0))

S48 = _spec(
    "S48", quantity_phrase="an extra capacitor", quantity_type="capacitance", unit="μF", values=(7.0, 19.0, 33.0),
    heldout_values=(12.0, 27.0),
    relevant=rv.RelevantWiring("C", "add", "A capacitor in parallel with the capacitor adds to its capacitance, so the capacitance "
                                           "of the loop becomes C + q; the circuit stays underdamped for every study value."),
    cancelling=S48_C,
    scene_clause="A second circuit, with a coil and a capacitor of its own, is built on another board. The connecting wires have "
                 "negligible resistance.",
    scene_object_rationale="A second circuit on another board has its own coil and capacitor and shares no wire with the first loop; "
                           "the first loop's resistance, inductance and capacitance are unchanged by it.",
    scene_refs=("second circuit",), target_terms=("this circuit", "this loop"),
    pairs=(
        Pair("p0", "A {value} {unit} capacitor is {relation}.", "connected in parallel with the capacitor of this circuit",
             "connected in parallel with the capacitor of the second circuit", CO,
             "A capacitor in parallel with the capacitor of the second circuit adds capacitance to that circuit only; it shares no "
             "wire with the first loop, whose capacitance is the stated one.", ("in series in a closed loop", "with no source"),
             "small",
             before_context_reason="The R sentence refers to 'the capacitor of this circuit' before the context introduces a circuit "
                                   "or a capacitor."),
        Pair("p1", "{relation}, a {value} {unit} capacitor was connected in parallel with the capacitor.", "For this run",
             "For an earlier run only", EVENT,
             "The capacitor was in parallel with the loop's capacitor for an earlier run only, which is over; the loop of the stated run "
             "has only its stated capacitor.", ("in series in a closed loop", "with no source"), "small"),
    ),
    notes="M250 phase 1: C is the initial charge (linearity); no K (the initial charge is not given, so no regime predicate can be "
          "evaluated).")

# --- S51 -------------------------------------------------------------------------------------------------------------------------

S51_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the initial volume of the gas", "volume", "L", (10.0, 17.0, 24.0), "The gas {relation} {value} {unit}.",
        (P("c0", "starts with a volume of"), P("c1", "initially occupies")),
        "(n*R*T1/q)*q*(r**(gamma - 1) - 1)/(gamma - 1)",
        ("p1 = n R T1 / V1", "W = (p2 V2 - p1 V1) / (gamma - 1) = p1 V1 (r^(gamma - 1) - 1) / (gamma - 1)"),
        "n*R*T1*q*(r**(gamma - 1) - 1)/(gamma - 1)", nonnumeric_fill="a known volume"),
    "uncommon", "Textbooks write the adiabatic work with p1 V1 explicit; that the initial volume drops out once n and T1 fix "
                "p1 V1 is rarely stated.", (12.0, 19.0))

S51_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the compression limit of the piston", "ratio", "1", (12.0, 15.0, 20.0), "The piston {relation} {value}.",
        (P("k0", "stops at a compression ratio of"), P("k1", "can be pushed in only until the compression ratio reaches")),
        "r < q", "n*R*T1*(q**(gamma - 1) - 1)/(gamma - 1)", 4.0, nonnumeric_fill="a known ratio"),
    r2.KOut(False, "With a limit below the stated ratio of 8 the gas could not be compressed to ratio 8, so the question 'how much "
                   "work is done on the gas during the compression' would describe a compression the piston cannot make; the "
                   "premise is contradicted, not merely changed."),
    (13.0, 18.0))

S51 = _spec(
    "S51", quantity_phrase="a further amount of gas", quantity_type="amount", unit="mol", values=(0.7, 1.3, 2.2),
    heldout_values=(0.9, 1.7),
    relevant=rv.RelevantWiring("n", "add", "Further gas of the same kind at the same temperature in the cylinder before the "
                                           "compression adds to the amount of gas, so n becomes n + q."),
    cancelling=S51_C, conditional=S51_K,
    scene_clause="A second cylinder fitted with a piston stands beside the first.",
    scene_object_rationale="A second cylinder with its own piston and gas shares no gas or piston with the first, so the gas that "
                           "is compressed is the first cylinder's alone.",
    scene_refs=("second cylinder",), target_terms=("the cylinder", "this cylinder"),
    pairs=(
        Pair("p0", "Before the compression begins, a further {value} {unit} of the same gas at the same temperature is {relation}.",
             "let into the cylinder", "let into the second cylinder", CO,
             "Gas let into a second cylinder is not in the first; the amount of gas that the first piston compresses is the stated "
             "one.", ("compressed slowly and adiabatically", "ideal gas"), "small amount",
             before_context_reason="The R sentence refers to 'the cylinder' before the context introduces it, and 'at the same "
                                   "temperature' has no referent until the stated temperature has been read."),
        Pair("p1", "{relation}, the cylinder also held a further {value} {unit} of the same gas at the same temperature.", "In this run",
             "For an earlier run only", EVENT,
             "The cylinder held the further gas for an earlier run only, which is over; the cylinder of the stated run holds only its "
             "stated amount of gas.", ("compressed slowly and adiabatically", "ideal gas"), "small amount"),
    ),
    notes="M250 phase 1: C is the initial volume (p1 V1 = n R T1 fixes the product), K is the piston's compression limit.")

# --- S52 -------------------------------------------------------------------------------------------------------------------------

S52 = _spec(
    "S52", quantity_phrase="a rise of the water's temperature", quantity_type="temperature_change", unit="K",
    values=(6.0, 17.0, 29.0), heldout_values=(12.0, 23.0),
    relevant=rv.RelevantWiring("dTw", "add", "Warming the water by q before the ice is added makes its starting temperature above "
                                             "the melting point dTw + q, so the heat it can give up grows (all of the ice still "
                                             "melts)."),
    scene_clause="A second container, also perfectly insulated, holds warm water beside the first one. The water in the first container is stirred to one temperature and does not boil or evaporate.",
    scene_object_rationale="A second insulated container with its own warm water exchanges no heat with the first, so the starting "
                           "temperature of the first water and the heat it gives up are fixed by its stated values.",
    scene_refs=("second container",), target_terms=("the water in the container", "this container"),
    pairs=(
        Pair("p0", "Before the ice is added, a heater warms {relation} by {value} {unit}.", "the water in the container",
             "the water in the second container", CO,
             "A heater warming the water of a second container leaves the first container's water at its stated starting "
             "temperature; the two containers exchange no heat.", ("perfectly insulated container", "all of the ice melts"),
             "a few kelvin",
             before_context_reason="The R sentence refers to 'the ice' and 'the water in the container' before the context "
                                   "introduces them."),
        Pair("p1", "{relation}, a heater warmed the water by {value} {unit} before the ice was added.", "In this run",
             "In an earlier run", EVENT,
             "The water was warmed in an earlier run, which is over; in the stated run the water starts at its stated "
             "temperature when the ice is added.", ("perfectly insulated container", "all of the ice melts"), "a few kelvin"),
    ),
    notes="M250 phase 1: q is a warming of the water (a mass quantity would give add/subtract misuse foils within 1% of the base "
          "answer, because the heat given up depends weakly on the water mass); no C or K (see NO_C, NO_K).")

# --- S53 -------------------------------------------------------------------------------------------------------------------------

S53_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the temperature of the colder outer surface", "temperature", "K", (270.0, 276.0, 285.0),
        "The colder outer surface of the wall {relation} {value} {unit}.",
        (P("c0", "is at a temperature of"), P("c1", "is held at")),
        "((q + dT) - q)/(R1 + R2)",
        ("T_hot = T_cold + dT", "heat current = (T_hot - T_cold) / (R1 + R2)"),
        "q/(R1 + R2)", nonnumeric_fill="a known value"),
    "standard", "That steady conduction depends on the temperature difference and not on the absolute temperature level is basic "
                "heat-transfer knowledge but is not a headline fact.", (273.0, 280.0))

S53_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the temperature-difference limit of the foam", "temperature_difference", "K", (60.0, 75.0, 95.0),
        "The foam {relation} {value} {unit}.",
        (P("k0", "keeps its shape only for temperature differences below"),
         P("k1", "is rated for temperature differences of up to")), "dT < q", "dT/R1", 10.0, nonnumeric_fill="a known difference"),
    r2.KOut(False, "If the foam failed the wall would no longer be a two-layer wall of brick and foam, so 'at what rate does heat "
                   "flow through the wall' would describe a different wall; the premise is contradicted, not merely changed."),
    (65.0, 85.0))

S53 = _spec(
    "S53", quantity_phrase="a further temperature difference", quantity_type="temperature_difference", unit="K",
    values=(6.0, 13.0, 27.0), heldout_values=(9.0, 17.0),
    relevant=rv.RelevantWiring("dT", "add", "A temperature difference raised across the outer surfaces of the wall by q makes the "
                                            "difference dT + q, and the steady heat current is proportional to it."),
    cancelling=S53_C, conditional=S53_K,
    scene_clause="A shed with a wooden wall of its own stands nearby. The two layers of the wall are in perfect thermal contact, and "
                 "no heat leaves through the edges of the wall.",
    scene_object_rationale="A shed's wooden wall is a different wall with its own surfaces and temperatures; it exchanges no heat "
                           "with the wall of the problem, whose surfaces keep their stated temperature difference.",
    scene_refs=("shed",), target_terms=("this wall", "the wall"),
    pairs=(
        Pair("p0", "The temperature difference between the outer surfaces of {relation} is then raised by {value} {unit}.",
             "this wall", "the shed wall", CO,
             "The temperature difference across the shed's wall is a different pair of surfaces; it leaves the two outer surfaces "
             "of the brick and foam wall at their stated temperature difference.", ("steady and perpendicular", "two layers in contact"),
             "a few kelvin",
             before_context_reason="The R sentence says the difference is 'then' raised, which presupposes the stated difference "
                                   "between the outer surfaces of the wall; placed first it has no referent."),
        Pair("p1", "{relation}, the temperature difference between the outer surfaces of the wall was raised by {value} {unit}.",
             "For this survey", "In an earlier survey", EVENT,
             "The temperature difference was raised in an earlier survey, which is over; the difference of the stated survey is "
             "the stated one.", ("steady and perpendicular", "two layers in contact"), "a few kelvin"),
    ),
    notes="M250 phase 1: C is the cold-side temperature (only the difference enters), K is the foam's temperature-difference limit.")

# --- S54 -------------------------------------------------------------------------------------------------------------------------

S54 = _spec(
    "S54", quantity_phrase="a layer of metal", quantity_type="length", unit="cm", values=(2.5, 4.5, 7.5),
    heldout_values=(3.5, 6.5),
    relevant=rv.RelevantWiring("r2", "add", "A layer of the same metal plated onto the second sphere adds to its radius, so r2 "
                                            "becomes r2 + q and the radiating area grows with the square of that radius."),
    scene_clause="A metal bracket and a metal disc hang from a frame nearby.",
    scene_object_rationale="A bracket and a disc hanging from a frame nearby are not the spheres; at the temperature of the much "
                           "colder surroundings they exchange no appreciable radiation with the spheres and leave their radii and "
                           "surface temperatures as stated.",
    scene_refs=("bracket",), target_terms=("second sphere", "first sphere", "spheres"),
    pairs=(
        Pair("p0", "A {value} {unit} layer of the same metal is {relation}.", "plated onto the second sphere",
             "plated onto the bracket", CO,
             "A layer plated onto the bracket thickens the bracket only; the second sphere keeps its stated radius, surface "
             "temperature and finish.", ("same constant emissivity", "same surface finish"), "thin",
             before_context_reason="The R sentence refers to 'the second sphere' and says 'the same metal' before the context "
                                   "introduces the spheres or their metal."),
        Pair("p1", "A {value} {unit} layer of the same metal was {relation}.", "plated onto the second sphere",
             "plated onto the disc", CO,
             "A layer plated onto the disc thickens the disc only; the second sphere keeps its stated radius, surface temperature "
             "and finish.", ("same constant emissivity", "same surface finish"), "thin",
             d_kind_note="No honest same-object event exists for this quantity: a layer of metal plated onto the second sphere in "
                         "an earlier experiment is still on it, and the sphere cannot be 'before' its own radius. A second "
                         "co-present object of a different type (the disc, named in the scene clause with the bracket) is used "
                         "instead."),
    ),
    notes="M250 phase 1: both D pairs are co-present (bracket, disc), see d_kind_note; no C (an emissivity chosen freely would "
          "contradict the stated 1.5 kW of the first sphere) and no K.")

# --- S56 -------------------------------------------------------------------------------------------------------------------------

S56_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the length of the test", "time", "min", (40.0, 90.0, 150.0), "The refrigerator {relation} {value} {unit}.",
        (P("c0", "runs steadily for"), P("c1", "is monitored for")),
        "(Pc*q/COP)/q",
        ("heat removed Qc = Pc t", "work needed W = Qc / COP", "electrical power = W / t"),
        "Pc*q/COP", nonnumeric_fill="a known time"),
    "uncommon", "The electrical power of a refrigerator in steady operation does not depend on how long it is observed, but this "
                "is rarely stated as a fact about a calculation through energy.", (70.0, 120.0))

S56_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the continuous rating of the compressor motor", "power", "W", (260.0, 330.0, 480.0), "The compressor motor {relation} {value} {unit}.",
        (P("k0", "is rated for a continuous electrical input of up to"), P("k1", "has a continuous electrical rating of")),
        "Pw < q", "q", 20.0, nonnumeric_fill="a known rating"),
    r2.KOut(False, "With a rating below the needed power the refrigerator could not keep its interior at the stated temperature, "
                   "so the question 'what electrical power does the refrigerator need' would describe a refrigerator that does not "
                   "do the stated job; the premise is contradicted, not merely changed."),
    (290.0, 400.0))

S56 = _spec(
    "S56", quantity_phrase="an extra lamp", quantity_type="power", unit="W", values=(35.0, 55.0, 90.0),
    heldout_values=(40.0, 75.0),
    relevant=rv.RelevantWiring("Pc", "add", "A lamp that stays lit inside the refrigerator gives its electrical power to the "
                                            "interior as heat, so the rate at which heat must be removed becomes Pc + q."),
    cancelling=S56_C, conditional=S56_K,
    scene_clause="A chest freezer stands beside the refrigerator. The refrigerator runs steadily.",
    scene_object_rationale="A chest freezer has its own interior and compressor; a lamp inside it adds heat to the freezer's "
                           "interior, not to the refrigerator's, and the kitchen stays a reservoir at its stated temperature.",
    scene_refs=("freezer",), target_terms=("the refrigerator",),
    pairs=(
        Pair("p0", "A {value} {unit} lamp is kept lit inside {relation}.", "the refrigerator", "the chest freezer", CO,
             "A lamp inside the chest freezer heats the freezer's interior and the kitchen, which is a reservoir at constant "
             "temperature; the refrigerator's interior receives only its stated leak.", ("steady rate", "reversible (Carnot) refrigerator"),
             "small",
             before_context_reason="The R sentence refers to 'the refrigerator' before the context introduces it."),
        Pair("p1", "A {value} {unit} lamp was kept lit inside the refrigerator {relation}.", "during this test",
             "for an earlier test only", EVENT,
             "The lamp was lit inside the refrigerator for an earlier test only, which is over; the heat the refrigerator removes in "
             "the stated test is the stated steady rate.", ("steady rate", "reversible (Carnot) refrigerator"), "small"),
    ),
    notes="M250 phase 1: C is the length of the test (power = energy / time), K is the compressor's continuous rating.")

# --- S57 -------------------------------------------------------------------------------------------------------------------------

S57 = _spec(
    "S57", quantity_phrase="a further amount of water", quantity_type="mass", unit="kg", values=(0.7, 1.4, 3.3),
    heldout_values=(0.9, 1.9),
    relevant=rv.RelevantWiring("m", "add", "Further water at the same temperature in the tank adds to the mass of water that the "
                                           "engine cools to the lake temperature, so m becomes m + q."),
    scene_clause="A second tank, which is empty, stands beside the first.",
    scene_object_rationale="An empty second tank holds none of the water that the engine cools and is not connected to the engine "
                           "or the lake, so the water of the first tank is the stated mass.",
    scene_refs=("second tank",), target_terms=("the tank", "this tank"),
    pairs=(
        Pair("p0", "Before the engine is started, a further {value} {unit} of water at the same temperature is {relation}.",
             "poured into the tank", "poured into the second tank", CO,
             "Water poured into a second tank is not in the first tank and is not drawn on by the engine; the engine cools only "
             "the stated mass of water.", ("reversible heat engine", "well-insulated tank"), "small amount",
             before_context_reason="The R sentence refers to 'the tank' and to the engine before the context introduces them."),
        Pair("p1", "{relation}, the tank also held a further {value} {unit} of water at the same temperature.", "In this experiment",
             "For an earlier experiment only", EVENT,
             "The tank held the further water for an earlier experiment only, which is over; in the stated experiment the engine cools "
             "only the stated mass of water.", ("reversible heat engine", "well-insulated tank"), "small amount"),
    ),
    notes="M250 phase 1: no C or K (see NO_C, NO_K).")

# --- S61 -------------------------------------------------------------------------------------------------------------------------

S61 = _spec(
    "S61", quantity_phrase="a shift of the screen", quantity_type="length", unit="cm", values=(35.0, 70.0, 150.0),
    heldout_values=(55.0, 110.0),
    relevant=rv.RelevantWiring("D", "add", "Moving the screen q farther from the slits raises the slit-to-screen distance to D + q."),
    scene_clause="A camera on a tripod stands near the slits to photograph the pattern. The screen is parallel to the slits.",
    scene_object_rationale="A camera near the slits is not in the light path and does not touch the screen or the slits, so the "
                           "slit-to-screen distance and the fringe positions are unchanged.",
    scene_refs=("camera",), target_terms=("screen", "slits", "pattern"),
    pairs=(
        Pair("p0", "The {relation} is then moved a further {value} {unit} away from the slits.", "screen", "camera", CO,
             "A camera moved away from the slits leaves the screen where the problem put it, so the slit-to-screen distance is "
             "the stated one.", ("small-angle approximation", "normal incidence"), "small distance",
             before_context_reason="The R sentence refers to 'the screen' and 'the slits' before the context introduces them, and "
                                   "'then' presupposes their stated placement."),
        Pair("p1", "The screen was moved a further {value} {unit} away from the slits {relation}.", "before the pattern was recorded",
             "in an earlier experiment", EVENT,
             "The screen was moved farther from the slits in an earlier experiment, which is over; in the stated experiment it "
             "stands at its stated distance.", ("small-angle approximation", "normal incidence"), "small distance"),
    ),
    notes="M250 phase 1: no C or K (see NO_C, NO_K).")

# --- S62 -------------------------------------------------------------------------------------------------------------------------

S62_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the cross-sectional area of the beam", "area", "mm^2", (14.0, 25.0, 60.0), "The beam {relation} {value} {unit}.",
        (P("c0", "has a cross-sectional area of"), P("c1", "covers an area of")),
        "((P0/q)/2*cos(th1)**2*cos(th2)**2)*q",
        ("intensity I0 = P0 / A", "I after each polariser: I1 = I0 / 2, I2 = I1 cos^2(th1), I3 = I2 cos^2(th2)",
         "power P3 = I3 A"),
        "(P0/q)/2*cos(th1)**2*cos(th2)**2", nonnumeric_fill="a known area"),
    "standard", "That a uniform beam's power and intensity are proportional, so the beam area drops out of a chain of Malus-law "
                "steps, is standard but is not stated as a fact.", (18.0, 45.0))

S62_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the damage threshold of the polarisers", "power", "mW", (150.0, 250.0, 350.0), "Each polariser {relation} {value} {unit}.",
        (P("k0", "is rated for a beam power of up to"), P("k1", "is damaged by beams stronger than")),
        "P0 < q", "P0", 20.0, nonnumeric_fill="a known power"),
    r2.KOut(False, "If a polariser were damaged by the beam, what it passes would be undefined (a burnt polariser neither "
                   "transmits along one axis nor blocks the other), so the question 'what is the power that emerges' would have "
                   "no single answer."),
    (200.0, 330.0))

S62 = _spec(
    "S62", quantity_phrase="a rise of the laser output", quantity_type="power", unit="mW", values=(15.0, 35.0, 70.0),
    heldout_values=(25.0, 55.0),
    relevant=rv.RelevantWiring("P0", "add", "A rise of the laser output by q before the beam reaches the first polariser makes the "
                                            "incident power P0 + q, and the transmitted power is proportional to it."),
    cancelling=S62_C, conditional=S62_K,
    scene_clause="A lamp, aimed at a wall, stands beside the laser.",
    scene_object_rationale="A lamp aimed at a wall sends no light through the three polarisers, so the power that "
                           "reaches them and the power that emerges are fixed by the laser alone.",
    scene_refs=("lamp",), target_terms=("laser beam", "polariser", "the laser"),
    pairs=(
        Pair("p0", "The output of the {relation} is then increased by {value} {unit}.", "laser", "lamp", CO,
             "A change of the output of a lamp aimed at a wall sends no light through the polarisers; the incident power of "
             "the stack is the stated one.", ("three ideal polarisers", "unpolarised laser beam"), "a small amount",
             before_context_reason="The R sentence refers to 'the laser' before the context introduces it, and 'then' presupposes "
                                   "the stated power."),
        Pair("p1", "The output of the laser was increased by {value} {unit} {relation}.", "before the beam reached the first polariser",
             "in an earlier experiment", EVENT,
             "The output of the laser was increased in an earlier experiment, which is over; the beam of the stated experiment "
             "has its stated power.", ("three ideal polarisers", "unpolarised laser beam"), "a small amount"),
    ),
    notes="M250 phase 1: C is the beam area (power = intensity x area), K is the polarisers' damage threshold.")

# --- S63 -------------------------------------------------------------------------------------------------------------------------

S63_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the pressure of the gas", "pressure", "kPa", (35.0, 150.0, 250.0), "The gas in the pipe {relation} {value} {unit}.",
        (P("c0", "is at a pressure of"), P("c1", "is kept at an absolute pressure of")),
        "3/(4*L)*sqrt(gam*q/(q*M/(R*T)))",
        ("density from the ideal-gas law: rho = p M / (R T)", "speed of sound: c^2 = gamma p / rho",
         "second-lowest resonance of a closed-open pipe: f = 3 c / (4 L)"),
        "3/(4*L)*sqrt(gam*q/1.2)", nonnumeric_fill="a known pressure"),
    "standard", "That the speed of sound in an ideal gas depends on temperature and molar mass and not on pressure (density "
                "follows pressure) is standard but is not stated as a named fact.", (55.0, 190.0))

S63_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the liquefaction temperature of the gas", "temperature", "K", (90.0, 120.0, 150.0), "The gas {relation} {value} {unit}.",
        (P("k0", "liquefies only at temperatures below"), P("k1", "stays gaseous down to a temperature of")),
        "T > q", "0", 400.0, nonnumeric_fill="a known temperature"),
    r2.KOut(False, "If the gas had liquefied there would be no gas column to resonate, so the question 'what is the second-lowest "
                   "frequency at which the gas column in the pipe resonates' would have no answer."),
    (100.0, 135.0))

S63 = _spec(
    "S63", quantity_phrase="a temperature rise", quantity_type="temperature", unit="K", values=(25.0, 45.0, 70.0),
    heldout_values=(35.0, 55.0),
    relevant=rv.RelevantWiring("T", "add", "Warming the gas in the pipe by q before the resonances are measured gives it the "
                                           "temperature T + q; the speed of sound depends on that temperature."),
    cancelling=S63_C, conditional=S63_K,
    scene_clause="A second pipe, filled with a different gas, stands beside the first one.",
    scene_object_rationale="A second pipe with a different gas shares no gas or wall with the first, so the first pipe's gas "
                           "keeps its stated temperature and the speed of sound in it is unchanged.",
    scene_refs=("second pipe",), target_terms=("the gas in the pipe", "this pipe"),
    pairs=(
        Pair("p0", "Before the resonances are measured, a heater warms {relation} by {value} {unit}.", "the gas in the pipe",
             "the gas in the second pipe", CO,
             "A heater warming the gas in a second pipe leaves the gas of the first pipe at its stated temperature, so the "
             "speed of sound in the first pipe is the stated one.", ("ideal gas", "neglect end corrections"), "a few kelvin",
             before_context_reason="The R sentence refers to 'the gas in the pipe' and to the resonances before the context "
                                   "introduces them."),
        Pair("p1", "{relation}, a heater warmed the gas in the pipe by {value} {unit} before its resonances were measured.",
             "In this experiment", "In an earlier experiment", EVENT,
             "The gas was warmed in an earlier experiment, which is over; in the stated experiment it is at its stated "
             "temperature when the resonances are measured.", ("ideal gas", "neglect end corrections"), "a few kelvin"),
    ),
    notes="M250 phase 1: C is the gas pressure (density follows it), K is the gas's liquefaction temperature.")

# --- S64 -------------------------------------------------------------------------------------------------------------------------

S64_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the object's height", "length", "cm", (2.5, 3.5, 4.0), "The object {relation} {value} {unit}.",
        (P("c0", "has a height of"), P("c1", "is an upright arrow with a height of")),
        "f2*(sep - do*(q*f1/(do - f1))/q)/((sep - do*(q*f1/(do - f1))/q) - f2)",
        ("ray parallel to the axis then through the focus: h1 / h = f1 / (do - f1)",
         "ray through the centre of the lens: h1 / h = di1 / do", "o2 = sep - di1", "thin lens: 1/o2 + 1/di2 = 1/f2"),
        "f2*(sep - q*f1/(do - f1))/((sep - q*f1/(do - f1)) - f2)", nonnumeric_fill="a known value"),
    "standard", "The lens equation has no object height in it, so the cancellation is visible in the formula; it is taught with "
                "the magnification relations.", (3.0, 5.0))

S64 = _spec(
    "S64", quantity_phrase="a shift of the second lens", quantity_type="length", unit="cm", values=(6.0, 14.0, 24.0),
    heldout_values=(8.0, 19.0),
    relevant=rv.RelevantWiring("sep", "add", "Moving the second lens q farther from the first lens makes the lens separation "
                                             "sep + q, so the first image is farther in front of the second lens."),
    cancelling=S64_C,
    scene_clause="A lamp on the bench lights the object. The lenses and the object stay on one common axis.",
    scene_object_rationale="A lamp on the bench that lights the object is not in the light path and does not touch either lens, so the "
                           "lens separation and the image positions are unchanged.",
    scene_refs=("lamp",), target_terms=("second lens", "first lens", "object"),
    pairs=(
        Pair("p0", "The {relation} is then moved a further {value} {unit} away from the first lens.", "second lens", "lamp", CO,
             "A lamp moved away from the first lens leaves the second lens where the problem put it, so the lens separation is "
             "the stated one.", ("thin converging lens", "on the axis"), "small distance",
             before_context_reason="The R sentence refers to 'the second lens' and 'the first lens' before the context introduces "
                                   "them, and 'then' presupposes their stated placement."),
        Pair("p1", "The second lens was moved a further {value} {unit} away from the first lens {relation}.", "before the image was located",
             "in an earlier experiment", EVENT,
             "The second lens was moved farther from the first lens in an earlier experiment, which is over; in the stated "
             "experiment it stands at its stated distance.", ("thin converging lens", "on the axis"), "small distance"),
    ),
    notes="M250 phase 1: C is the object's height (magnification relations); no K (see NO_K).")

# --- S65 -------------------------------------------------------------------------------------------------------------------------

S65 = _spec(
    "S65", quantity_phrase="a liquid", quantity_type="refractive_index", unit="1", values=(1.33, 1.2, 1.38),
    heldout_values=(1.26, 1.36),
    relevant=rv.RelevantWiring("n0", "replace", "A liquid in front of the fibre end replaces the air as the medium that the rays "
                                                "enter from, so the outside index n0 becomes q."),
    scene_clause="A glass trough, which is empty, stands beside the fibre.",
    scene_object_rationale="A glass trough beside the fibre is not in front of the end face and does not touch the fibre, so the "
                           "medium that the rays enter the fibre from is still the stated one.",
    scene_refs=("trough",), target_terms=("the air", "fibre end", "end face", "end of the fibre"),
    pairs=(
        Pair("p0", "A clear liquid whose refractive index is {value} {unit} {relation}.", "now replaces the air in front of the fibre end",
             "is now poured into the trough beside the fibre", CO,
             "A liquid poured into a trough beside the fibre is not in front of the fibre's end face; the rays still enter the fibre from "
             "the stated air.", ("flat end", "plane containing the axis"), "a known value",
             before_context_reason="The R sentence refers to 'the air in front of the fibre end' before the context introduces them, "
                                   "and 'now' presupposes the stated air."),
        Pair("p1", "{relation}, the end of the fibre was dipped into a liquid whose refractive index is {value} {unit}.",
             "For this experiment", "For an earlier experiment only", EVENT,
             "The fibre end was dipped into the liquid for an earlier experiment only, which is over; in the stated experiment the "
             "rays enter from the stated air.", ("flat end", "plane containing the axis"), "a known value"),
    ),
    notes="M250 phase 1: R uses replace on the outside index as the M0 S92 liquid; no C or K (see NO_C, NO_K).")

# --- S66 -------------------------------------------------------------------------------------------------------------------------

S66_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the distance to the screen", "length", "m", (1.5, 2.5, 3.5), "The screen {relation} {value} {unit} from the grating.",
        (P("c0", "is placed"), P("c1", "stands")),
        "atan(q*tan(asin(m*lam2/d))/q) - atan(q*tan(asin(m*lam1/d))/q)",
        ("spot position on the screen: y = L tan(theta) for each wavelength", "angle recovered from the position: theta = atan(y / L)"),
        "q*(tan(asin(m*lam2/d)) - tan(asin(m*lam1/d)))", nonnumeric_fill="a known distance"),
    "uncommon", "That an angle measured from spot positions does not depend on the screen distance is used in practice but is "
                "rarely stated as a fact about the grating equation.", (1.8, 3.0))

S66 = _spec(
    "S66", quantity_phrase="a replacement wavelength", quantity_type="length", unit="nm", values=(520.0, 560.0, 490.0),
    heldout_values=(530.0, 500.0),
    relevant=rv.RelevantWiring("lam1", "replace", "Light of wavelength q replaces the shorter wavelength of the beam, so lam1 "
                                                  "becomes q and the separation is measured between q and the longer wavelength."),
    cancelling=S66_C,
    scene_clause="A second spectrometer stands beside the grating. The beam consists of just the two wavelengths described.",
    scene_object_rationale="A second spectrometer beside the grating receives no light from the grating, so the beam, the grating "
                           "and the two wavelengths of the problem are unchanged.",
    scene_refs=("spectrometer",), target_terms=("shorter wavelength", "the beam"),
    pairs=(
        Pair("p0", "Light of {value} {unit} wavelength {relation}.", "now replaces the shorter wavelength in the beam",
             "now enters the second spectrometer", CO,
             "Light entering a second spectrometer is not in the beam that falls on the grating; the beam keeps its two stated "
             "wavelengths.", ("normal incidence", "transmission diffraction grating"), "a certain",
             before_context_reason="The R sentence refers to 'the shorter wavelength in the beam' before the context introduces "
                                   "the beam, and 'now' presupposes its stated wavelengths."),
        Pair("p1", "{relation}, light of {value} {unit} wavelength replaced the shorter wavelength in the beam.", "For this measurement",
             "For an earlier measurement only", EVENT,
             "The light replaced the shorter wavelength for an earlier measurement only, which is over; the beam of the stated "
             "measurement has its two stated wavelengths.", ("normal incidence", "transmission diffraction grating"),
             "a certain"),
    ),
    notes="M250 phase 1: R uses replace on the shorter wavelength; C is the distance to the screen; no K (see NO_K).")

# --- S67 -------------------------------------------------------------------------------------------------------------------------

S67_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the damage threshold of the plate", "power", "mW", (250.0, 350.0, 450.0), "The glass plate {relation} {value} {unit}.",
        (P("k0", "is rated for a beam power of up to"), P("k1", "is damaged by beams stronger than")),
        "P0 < q", "P0", 20.0, nonnumeric_fill="a known power"),
    r2.KOut(False, "If the plate were damaged by the beam, the transmitted power would depend on the damage (scattering, "
                   "absorption), so the question 'what is the total power transmitted' would have no single answer."),
    (300.0, 380.0))

S67 = _spec(
    "S67", quantity_phrase="a rise of the source output", quantity_type="power", unit="mW", values=(25.0, 35.0, 70.0),
    heldout_values=(20.0, 55.0),
    relevant=rv.RelevantWiring("P0", "add", "A rise of the source output by q before the beam reaches the plate makes the incident "
                                            "power P0 + q, and the transmitted power is proportional to it."),
    conditional=S67_K,
    scene_clause="A lamp, aimed at a wall, stands beside the plate.",
    scene_object_rationale="A lamp aimed at a wall sends no light onto the plate, so the power that falls on the plate and "
                           "the power it transmits are fixed by the source of the beam alone.",
    scene_refs=("lamp",), target_terms=("source of the beam", "plate", "beam"),
    pairs=(
        Pair("p0", "The output of the {relation} is then increased by {value} {unit}.", "source of the beam", "lamp", CO,
             "A change of the output of a lamp aimed at a wall sends no light onto the plate; the incident power is the stated "
             "one.", ("does not absorb light", "normal incidence"), "a small amount",
             before_context_reason="The R sentence refers to 'the source of the beam' before the context introduces a beam, and "
                                   "'then' presupposes the stated power."),
        Pair("p1", "The output of the source of the beam was increased by {value} {unit} {relation}.", "before the beam reached the plate",
             "in an earlier experiment", EVENT,
             "The output of the source was increased in an earlier experiment, which is over; the beam of the stated experiment "
             "has its stated power.", ("does not absorb light", "normal incidence"), "a small amount"),
    ),
    notes="M250 phase 1: K is the plate's damage threshold; no C (see NO_C).")

# --- S71 -------------------------------------------------------------------------------------------------------------------------

S71_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the intensity of the light", "intensity", "W/m^2", (20.0, 90.0, 160.0), "The light {relation} {value} {unit}.",
        (P("c0", "has an intensity of"), P("c1", "reaches the surface at an intensity of")),
        "c*sqrt(2*((q/(q*lam/hc)) - phi)/mc2)",
        ("photon flux Phi = I / (hc / lambda) = I lambda / (hc)", "energy per photon = I / Phi = hc / lambda",
         "Kmax = hc / lambda - phi"),
        "v*sqrt(q/10)", nonnumeric_fill="a known value"),
    "famous", "That the maximum kinetic energy of photoelectrons does not depend on the light's intensity is the headline "
              "observation of the photoelectric effect.", (45.0, 140.0))

S71 = _spec(
    "S71", quantity_phrase="a shift of the wavelength", quantity_type="length", unit="nm", values=(35.0, 55.0, 80.0),
    heldout_values=(40.0, 65.0),
    relevant=rv.RelevantWiring("lam", "subtract", "Shortening the wavelength of the light on the surface by q makes the "
                                                  "wavelength lam - q and the photon energy hc / (lam - q)."),
    cancelling=S71_C,
    scene_clause="A second lamp, of a different colour, shines on a screen nearby. No electric or magnetic field acts on the emitted electrons.",
    scene_object_rationale="A second lamp that shines on a screen sends no light onto the metal surface, so the photons that reach "
                           "the surface have the stated wavelength.",
    scene_refs=("second lamp",), target_terms=("metal surface", "the light"),
    pairs=(
        Pair("p0", "The wavelength of the {relation} is then shortened by {value} {unit}.", "light falling on the metal surface",
             "light from the second lamp", CO,
             "Shortening the wavelength of the second lamp's light changes the photons that reach the screen only; the photons on "
             "the metal surface keep the stated wavelength.", ("work function", "falls on a metal surface"), "a small amount",
             before_context_reason="The R sentence refers to 'the metal surface' before the context introduces it, and 'then' "
                                   "presupposes the stated wavelength."),
        Pair("p1", "The wavelength of the light was shortened by {value} {unit} {relation}.", "before it reached the metal surface",
             "in an earlier experiment", EVENT,
             "The wavelength of the light was shortened in an earlier experiment, which is over; the light of the stated "
             "experiment has its stated wavelength.", ("work function", "falls on a metal surface"), "a small amount"),
    ),
    notes="M250 phase 1: C is the light's intensity (famous); no K (see NO_K).")


ROLE_SPECS: dict[str, r2.RoleSpecV2] = {s.structure_id: s for s in (
    S46, S47, S48, S51, S52, S53, S54, S56, S57, S61, S62, S63, S64, S65, S66, S67, S71)}
SPECS = ROLE_SPECS

STRUCTURE_FACTORIES = {
    "S46": lib_electromagnetism.s46_rail_terminal_speed,
    "S47": lib_electromagnetism.s47_transformer_load_power,
    "S48": lib_electromagnetism.s48_rlc_ringing_frequency,
    "S51": lib_thermodynamics.s51_adiabatic_compression_work,
    "S52": lib_thermodynamics.s52_ice_in_warm_water,
    "S53": lib_thermodynamics.s53_two_layer_wall_conduction,
    "S54": lib_thermodynamics.s54_radiated_power_scaling,
    "S56": lib_thermodynamics.s56_refrigerator_power,
    "S57": lib_thermodynamics.s57_available_work_from_hot_water,
    "S61": lib_optics.s61_double_slit_fringe,
    "S62": lib_optics.s62_polariser_stack,
    "S63": lib_optics.s63_closed_pipe_second_resonance,
    "S64": lib_optics.s64_two_lens_image,
    "S65": lib_optics.s65_fibre_acceptance_angle,
    "S66": lib_optics.s66_grating_line_separation,
    "S67": lib_optics.s67_glass_plate_transmission,
    "S71": lib_quantum.s71_photoelectron_speed,
}

# Structures that cannot honestly carry the design (no natural relevant quantity, no honest D). None in this batch.
INFEASIBLE: dict[str, str] = {}

NO_C: dict[str, str] = {
    "S46": "Every input of the terminal-speed formula matters; the only candidates (the rod's release height, the loop's "
           "self-inductance) cancel by a limit or by the steady state, not by an algebraic identity in the stated relations.",
    "S52": "No quantity of the calorimetry appears in the energy balance and then cancels; the melting point only fixes the "
           "reference of a temperature difference and is fixed physics, not a free quantity.",
    "S54": "An emissivity would cancel in the ratio of the two spheres' powers, but it is fixed by the stated 1.5 kW of the first "
           "sphere (about 0.84), so three different stated values would contradict the problem; the Stefan-Boltzmann constant is a "
           "constant, not a quantity with study values.",
    "S57": "The reservoir and engine relations carry no free quantity that enters an intermediate relation and cancels.",
    "S61": "The fringe position depends on every stated quantity; a slit width or the source intensity does not appear in the "
           "stated relations, so nothing enters and cancels.",
    "S65": "The acceptance angle depends on the three indices only; a fibre length or core diameter appears in no relation.",
    "S67": "A beam-area quantity would cancel as in S62 but the Fresnel relations are written for intensities and the plate "
           "has no further free quantity; not added so that C is not forced.",
}
NO_K: dict[str, str] = {
    "S46": "The only regime (a long rail, a negligible self-inductance) is approached asymptotically and has no exact threshold "
           "quantity; a resistor power rating has no definite out-of-regime answer for a terminal speed.",
    "S48": "The initial charge, which would fix a saturation or breakdown threshold, is not given, so no predicate can be evaluated.",
    "S52": "A container heat capacity or a mass limit would not leave the answer exactly unchanged inside the regime, and the "
           "problem states that the container exchange is negligible.",
    "S54": "A surroundings temperature would change the answer by more than the grading tolerance inside any regime that "
           "keeps absorption 'negligible', so the invariance claim would be false.",
    "S57": "A boiling point (the water stays liquid) has no definite out-of-regime answer for the maximum work.",
    "S61": "A screen width or slit width would not move the fringe position inside the regime, and outside it the question has "
           "no definite changed answer.",
    "S64": "The stated condition that the first image forms between the lenses is a property of the input values, not of a "
           "further quantity with a threshold.",
    "S65": "A bend radius or fibre length gives a gradual, not exact, change of the guided angle.",
    "S66": "A detector range or an order limit would not move the separation inside the regime and has no definite "
           "out-of-regime answer.",
    "S71": "A retarding potential or a surface condition does not change the emitted speed in or out of its regime.",
}


def structure(structure_id: str) -> gr.Structure:
    """The October structure with the spec's scene clause appended to its base context."""

    return r2.with_scene(STRUCTURE_FACTORIES[structure_id](), ROLE_SPECS[structure_id].scene_clause)


# What the H4 trace extractor (`TraceContext.target_phrases` / `target_symbols`) must read as a statement of the target: a phrase of the
# question, its head noun and the conventional symbols of the target quantity (and the graph's target node name).
TARGET_TERMS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "S46": (("terminal speed that the sliding rod approaches", "terminal speed", "speed"), ("v", "v_T", "v_t")),
    "S47": (("average power dissipated in the load", "average power", "power"), ("P", "P_L")),
    "S48": (("frequency of these damped oscillations", "frequency of the damped oscillations", "frequency"), ("f_d", "fd", "f")),
    "S51": (("work is done on the gas", "work done on the gas", "work"), ("W", "W_on")),
    "S52": (("heat does the original warm water give up", "heat given up", "heat"), ("Q", "Q_w", "Qlost")),
    "S53": (("rate does heat flow through the wall", "rate of heat flow", "rate"), ("P", "H", "Q_dot")),
    "S54": (("power does the second sphere radiate", "power radiated by the second sphere", "power"), ("P_2", "P2", "P")),
    "S56": (("electrical power does the refrigerator need", "electrical power", "power"), ("P_w", "Pw", "P", "W_dot")),
    "S57": (("maximum total work that the engine can deliver", "maximum total work", "maximum work", "work"), ("W", "W_max")),
    "S61": (("far from the centre of the pattern", "distance from the centre", "distance"), ("y", "y_3", "y_m")),
    "S62": (("power of the beam that emerges", "power of the beam", "power"), ("P_3", "P3", "P")),
    "S63": (("second-lowest frequency", "frequency"), ("f", "f_2")),
    "S64": (("far behind the second lens is the final image", "distance of the final image", "distance"), ("d_i", "di2", "di", "s_i")),
    "S65": (("largest angle", "angle of acceptance", "angle"), ("theta_max", "θ_max", "thm", "theta", "θ")),
    "S66": (("angular separation", "separation"), ("Delta theta", "Δθ", "dth", "dtheta")),
    "S67": (("total power of the light transmitted", "total power", "power"), ("P_t", "Pt", "P")),
    "S71": (("speed of the fastest electrons", "speed"), ("v", "v_max")),
}
