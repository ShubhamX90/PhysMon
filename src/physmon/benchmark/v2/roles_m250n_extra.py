"""M250 phase 2, batch extra: v2.1 role-by-value specifications for the new structures S251 to S262 (plan revision v2.2, section G and the
wording rules 1 to 8 of the M0 v2.1/v2.2 panel and judge reviews; admission standard 3.2, 6.1, 6.2, 6.3).

Every spec follows `roles_m0v21` (the v2.1 design) on instance 0 of the new structure:

* one R/D quantity with three study values and two held-out values; a co-present D (pair 0, `other_object_same_scene`) whose object is
  introduced by a number-free scene clause in the base context of every cell, and a same-object D (pair 1, `same_object_other_event`: an
  earlier experiment of the same object, never a change applied and then reversed), the same frame, numeral and unit within a pair, an
  attachment-only difference, word counts within three, marker- and consequence-free wording, value hygiene;
* the wording rules of the panel and judge reviews: (1) the pair-1 R sentence says that the event is part of the very situation the question
  asks about, in the present tense, before the asked moment; (2) no R sentence contradicts a stated base value; (3) the action on the
  co-present object is an ordinary, purposeful one for that object; (4) the co-present object is never of the same type as the target;
  (5) present-tense questions are matched by present-tense R sentences; (6) every answer-determining condition is stated, number-free, in
  the base text; (7) a pair-1 event that adds something to the target says it applies for one run only, and any other pair-1 event is
  anchored in an earlier experiment; (8) no D or N sentence contradicts the scene clause or the base;
* a C quantity where the physics supports a real cancellation (S251, S253, S255, S256, S259, S260); the familiarity of each is tagged;
* a K quantity where a genuine regime condition of the physics itself exists (S254, S256, S260, S261, S262); the kind of regime is recorded
  in `K_KINDS`. K_out is recorded as infeasible with the reason in every case.

`INFEASIBLE` holds the structures that cannot honestly carry the design (none in this batch); `NO_C` and `NO_K` hold the reason a
structure has no C or K quantity, so that an absence is a judgement on record and not an omission.
"""

from __future__ import annotations

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import lib_m250_extra as le
from physmon.benchmark.v2 import rolevalue as rv
from physmon.benchmark.v2 import rolevalue_v2 as r2

P = rv.Phrasing
Pair = r2.PhrasePair
CO = r2.D_KIND_CO_PRESENT
EVENT = r2.D_KIND_OTHER_EVENT
V21 = r2.VERSION_V21


def _spec(sid: str, **fields) -> r2.RoleSpecV2:
    return r2.RoleSpecV2(structure_id=sid, version=V21, author="agent (M250 phase 2, extra)", **fields)


def _ko(reason: str) -> r2.KOut:
    return r2.KOut(False, reason)


# --- S251 --------------------------------------------------------------------------------------------------------------------------

S251_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the mass of the probe", "mass", "kg", (140.0, 270.0, 520.0), "The probe {relation} {value} {unit}.",
        (P("c0", "has a mass of"), P("c1", "is built with a mass of")),
        "q*g0*Rm**2/(q*g0*Rm - q*v0**2/2) - Rm",
        ("kinetic energy of the probe K = m v0^2 / 2", "total energy E = K - m g0 R", "turning point: E = - m g0 R^2 / r_max"),
        "q*v0**2/(2*q*g0)", nonnumeric_fill="a definite mass"),
    "famous", "That the mass of a body drops out of a height found from energy conservation in a gravitational field is a standard "
              "textbook point.", (190.0, 370.0))

S251 = _spec(
    "S251", quantity_phrase="a further upward speed", quantity_type="speed", unit="m/s", values=(60.0, 210.0, 330.0),
    heldout_values=(80.0, 280.0),
    relevant=rv.RelevantWiring("v0", "add", "A further upward speed given to the probe at the firing adds to its launch speed, so v0 becomes v0 + q."),
    cancelling=S251_C,
    scene_clause="A weather balloon waits on the ground nearby.",
    scene_object_rationale="A weather balloon waiting on the ground is a separate body from the probe; speed given to it is not given to "
                           "the probe, so the launch speed of the probe is the stated one.",
    scene_refs=("weather balloon",), target_terms=("probe", "moon", "motor", "height"),
    pairs=(
        Pair("p0", "Before the firing, a further {value} {unit} of upward speed is given to {relation}.", "the probe",
             "the weather balloon", CO,
             "Speed given to the weather balloon stays with the balloon; the probe keeps the launch speed from its motor and the "
             "moon, its radius and its gravity are those stated.", ("no atmosphere and does not rotate", "inverse-square law"),
             "small amount",
             before_context_reason="The R sentence refers to 'the probe' and 'the firing' before the context introduces them."),
        Pair("p1", "{relation} a further {value} {unit} of upward speed, for one firing only.",
             "When the probe is fired, it is also given", "On an earlier firing, it was also given", EVENT,
             "The probe was given the further speed on an earlier firing, for that firing only; at the stated firing it has only the "
             "launch speed of its motor.", ("no atmosphere and does not rotate", "inverse-square law"), "small amount"),
    ),
    notes="M250 phase 2: C is the mass of the probe (famous); no K (see NO_K).")

# --- S252 --------------------------------------------------------------------------------------------------------------------------

S252 = _spec(
    "S252", quantity_phrase="a further load of instruments", quantity_type="mass", unit="kg", values=(45.0, 95.0, 170.0),
    heldout_values=(65.0, 130.0),
    relevant=rv.RelevantWiring("m", "add", "A further load of instruments bolted to the satellite adds to its mass, so m becomes m + q."),
    scene_clause="A recovery ship waits at sea.",
    scene_object_rationale="A recovery ship at sea is a vessel outside the orbit; a load stowed aboard it is not carried by the "
                           "satellite, so the mass that the engines raise is the stated one.",
    scene_refs=("recovery ship",), target_terms=("satellite", "engines", "orbit"),
    pairs=(
        Pair("p0", "Before the satellite is raised, a further {value} {unit} of instruments is {relation}.", "bolted to the satellite",
             "stowed aboard the recovery ship", CO,
             "Instruments stowed aboard the recovery ship stay on the ship; the satellite keeps its stated mass and the orbits, "
             "the Earth and the neglected propellant mass are those stated.",
             ("mass of the burnt propellant is neglected", "inverse-square law"), "small amount",
             before_context_reason="The R sentence refers to 'the satellite' before the context introduces it."),
        Pair("p1", "{relation} a further {value} {unit} of instruments, for one flight only.",
             "When the satellite is raised, it also carries", "On an earlier flight, it also carried", EVENT,
             "The satellite carried the further instruments on an earlier flight, for that flight only; on the stated flight it has "
             "only its stated mass.", ("mass of the burnt propellant is neglected", "inverse-square law"), "small amount"),
    ),
    notes="M250 phase 2: no C or K (see NO_C, NO_K).")

# --- S253 --------------------------------------------------------------------------------------------------------------------------

_ZR = "((rho2*(c2/q)*q)/(rho1*(c1/q)*q))"
S253_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the frequency of the sound", "frequency", "Hz", (220.0, 640.0, 1500.0), "The sound {relation} {value} {unit}.",
        (P("c0", "has a frequency of"), P("c1", "is a steady tone at")),
        f"sqrt(2*rho2*c2*(4*{_ZR}/(1 + {_ZR})**2*Ii))",
        ("wavelength in each fluid lambda = c / f", "specific acoustic impedance Z = rho lambda f", "intensity transmission coefficient "
         "T = 4 Z1 Z2 / (Z1 + Z2)^2", "p = sqrt(2 Z I)"),
        "sqrt(2*rho2*c2*Ii)", nonnumeric_fill="a known frequency"),
    "standard", "That the intensity transmission at a plane boundary does not depend on the frequency follows from the impedances "
                "but is not a headline fact.", (310.0, 880.0))

S253 = _spec(
    "S253", quantity_phrase="a further sound intensity", quantity_type="intensity", unit="W/m^2", values=(0.008, 0.021, 0.036),
    heldout_values=(0.011, 0.027),
    relevant=rv.RelevantWiring("Ii", "add", "A further sound intensity falling on the water surface adds to the intensity of the incident wave, "
                                            "so Ii becomes Ii + q."),
    cancelling=S253_C,
    scene_clause="A boathouse stands on the shore.",
    scene_object_rationale="A boathouse on the shore is a building beside the water; sound falling on its wall does not fall on the "
                           "water surface, so the incident intensity is the stated one.",
    scene_refs=("boathouse",), target_terms=("water", "incident", "wave", "pressure"),
    pairs=(
        Pair("p0", "Before the pressure is measured, a further {value} {unit} of sound intensity falls on {relation}.",
             "the water surface", "the boathouse wall", CO,
             "Sound that falls on the boathouse wall does not fall on the water surface; the incident wave keeps its stated intensity "
             "and the two fluids are as stated.", ("normal incidence", "uniform and lossless"), "small amount",
             before_context_reason="The R sentence refers to 'the water surface' before the context introduces it."),
        Pair("p1", "{relation} a further {value} {unit} of sound intensity, for one trial only.",
             "While the wave arrives, the surface also receives", "On an earlier trial, the surface also received", EVENT,
             "The surface received the further intensity on an earlier trial, for that trial only; in the stated trial it receives only "
             "the stated incident wave.", ("normal incidence", "uniform and lossless"), "small amount"),
    ),
    notes="M250 phase 2: C is the frequency of the sound (impedance transmission); no K (see NO_K).")

# --- S254 --------------------------------------------------------------------------------------------------------------------------

S254_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the width of the mouth of the siren", "length", "cm", (14.0, 26.0, 38.0), "The mouth of the siren {relation} {value} {unit}.",
        (P("k0", "has a diameter of"), P("k1", "has a width of")), "5*q < r", "P*exp(-alpha*r)/(pi*q**2)", 6000.0,
        nonnumeric_fill="a modest size"),
    _ko("A mouth as wide as a fifth of the distance would make the siren an extended source whose intensity at the observer is not "
        "given by the point-source law, and the stated model of a point source would be contradicted; the premise is contradicted, not "
        "merely changed."),
    (18.0, 33.0))

S254 = _spec(
    "S254", quantity_phrase="a further walking distance", quantity_type="length", unit="m", values=(35.0, 75.0, 150.0),
    heldout_values=(48.0, 110.0),
    relevant=rv.RelevantWiring("r", "add", "A further walk away from the mast adds to the distance of the observer from the mast, so r "
                                           "becomes r + q."),
    conditional=S254_K,
    scene_clause="A dog lies by the mast.",
    scene_object_rationale="A dog lying by the mast is an animal that can walk; its walk does not move the observer, so the distance "
                           "of the observer from the mast is the stated one.",
    scene_refs=("dog",), target_terms=("observer", "siren", "intensity", "sound"),
    pairs=(
        Pair("p0", "Before the intensity is measured, {relation} walks {value} {unit} farther from the mast.", "the observer",
             "the dog", CO,
             "A walk of the dog does not move the observer; the observer keeps the stated distance from the mast and the siren, "
             "its power and the air are those stated.", ("high above the ground", "the air is still"), "a modest distance",
             before_context_reason="The R sentence refers to 'the observer' before the context introduces the observer."),
        Pair("p1", "{relation} the mast by {value} {unit} more.",
             "Before the reading is taken, the observer moves away from", "In an earlier experiment, the observer moved away from", EVENT,
             "The observer walked the further distance in an earlier experiment; in the stated measurement the observer is at the "
             "stated distance.", ("high above the ground", "the air is still"), "a modest distance"),
    ),
    notes="M250 phase 2: K is the width of the mouth of the siren (far-field regime); no C (see NO_C).")

# --- S255 --------------------------------------------------------------------------------------------------------------------------

S255_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the width of the strip", "length", "mm", (6.0, 14.0, 27.0), "The strip {relation} {value} {unit}.",
        (P("c0", "has a width of"), P("c1", "is cut to a width of")),
        "24*(a2 - a1)*(T - T0)*q/(h*(12 + (1 + E1/E2)*(1 + E2/E1))*q)*L**2/2",
        ("bending moment of the layers M = q * (moment per unit width)", "bending stiffness of the section = q * (stiffness per unit width)",
         "curvature = M / stiffness"),
        "24*(a2 - a1)*(T - T0)*q/(h*(12 + (1 + E1/E2)*(1 + E2/E1)))*L**2/2", nonnumeric_fill="a known width"),
    "standard", "That the bending of a free beam by a thermal mismatch does not depend on its width follows from the section "
                "analysis but is not usually stated.", (9.0, 21.0))

S255 = _spec(
    "S255", quantity_phrase="a further length of strip", quantity_type="length", unit="cm", values=(6.0, 11.0, 15.0),
    heldout_values=(8.0, 14.0),
    relevant=rv.RelevantWiring("L", "add", "Strip slid further out of the clamp before the measurement adds to the free length, so L becomes "
                                           "L + q."),
    cancelling=S255_C,
    scene_clause="A cable runs from a reel on the bench.",
    scene_object_rationale="A cable running from a reel is a line apart from the strip; cable paid out of the reel does not change the "
                           "length of the strip that projects from its clamp, so the free length is the stated one.",
    scene_refs=("cable",), target_terms=("strip", "clamp", "deflection", "heater"),
    pairs=(
        Pair("p0", "Before the deflection is measured, {relation} {value} {unit} further.", "the strip is slid out", "the cable is paid out",
             CO,
             "Cable paid out of the reel does not change the strip; the strip keeps its stated free length, layers and "
             "temperatures.", ("heated uniformly and slowly", "carries no load"), "a modest distance",
             before_context_reason="The R sentence refers to 'the strip' and 'the deflection' before the context introduces them."),
        Pair("p1", "{relation} {value} {unit} more of the strip.",
             "When the deflection is measured, the clamp also lets out", "In an earlier experiment, the clamp also let out",
             EVENT,
             "The clamp let out further strip in an earlier experiment; in the stated experiment the strip projects the stated length.",
             ("heated uniformly and slowly", "carries no load"), "a modest length"),
    ),
    notes="M250 phase 2: C is the width of the strip; no K (see NO_K).")

# --- S256 --------------------------------------------------------------------------------------------------------------------------

S256_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the power of the electric heater", "power", "W", (120.0, 310.0, 640.0),
        "The block is heated by an electric heater {relation} {value} {unit}.",
        (P("c0", "of power"), P("c1", "with an output of")),
        "q*((m/M)*3*R*(T2 - T1)/q)",
        ("time of the heating t = Q / P", "heat delivered = P t", "Q = n C dT"),
        "(m/M)*3*R*(T2 - T1) + q*(T2 - T1)", nonnumeric_fill="a known"),
    "standard", "That the heat needed for a given temperature rise does not depend on the heater power follows from Q = n C dT but is "
                "not stated as a fact in a first treatment.", (210.0, 480.0))

S256_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the Debye temperature of lead", "temperature", "K", (88.0, 105.0, 122.0),
        "The Debye temperature of lead {relation} {value} {unit}.", (P("k0", "is"), P("k1", "is quoted as")), "T1 > 2*q",
        "(m/M)*(12*pi**4/5)*R*(T2**4 - T1**4)/(4*q**3)", 400.0, nonnumeric_fill="a known value"),
    _ko("A Debye temperature of the order of the temperature of the block would contradict the stated condition that the lattice "
        "vibrations are in the classical regime, so the heat capacity would no longer be 3R and the stated model would not apply; the "
        "premise is contradicted, not merely changed."),
    (96.0, 114.0))

S256 = _spec(
    "S256", quantity_phrase="a further mass of lead", quantity_type="mass", unit="kg", values=(0.07, 0.18, 0.52),
    heldout_values=(0.11, 0.29),
    relevant=rv.RelevantWiring("m", "add", "Further lead cast onto the block before the heating adds to its mass, so m becomes m + q."),
    cancelling=S256_C, conditional=S256_K,
    scene_clause="A lead weight hangs on a hook by the bench.",
    scene_object_rationale="A lead weight on a hook is a separate lump of lead; lead cast onto it is not cast onto the block, so the "
                           "mass that is heated is the stated one.",
    scene_refs=("lead weight",), target_terms=("block", "heated", "heat"),
    pairs=(
        Pair("p0", "Before the heating begins, a further {value} {unit} of lead is {relation}.", "cast onto the block",
             "cast onto the lead weight", CO,
             "Lead cast onto the lead weight stays on the weight; the block keeps its stated mass, and the heating and its end "
             "points are as stated.", ("stays solid", "loses no heat to the surroundings"), "small amount",
             before_context_reason="The R sentence refers to 'the block' before the context introduces it."),
        Pair("p1", "{relation} a further {value} {unit} of lead, for one heating only.",
             "When the heating begins, the block also includes", "In an earlier experiment, the block also included", EVENT,
             "The block included the further lead in an earlier experiment, for that experiment only; in the stated heating it has only "
             "its stated mass.", ("stays solid", "loses no heat to the surroundings"), "small amount"),
    ),
    notes="M250 phase 2: C is the power of the heater, K is the Debye temperature of lead (classical limit of the lattice heat capacity).")

# --- S257 --------------------------------------------------------------------------------------------------------------------------

S257 = _spec(
    "S257", quantity_phrase="a further activity of the parent isotope", quantity_type="activity", unit="Bq", values=(680.0, 1300.0, 2900.0),
    heldout_values=(900.0, 1800.0),
    relevant=rv.RelevantWiring("A0", "add", "Further parent isotope loaded into the column at the start adds to the activity of the parent "
                                            "at time zero, so A0 becomes A0 + q."),
    scene_clause="A shielded transport container stands on the bench.",
    scene_object_rationale="A shielded container on the bench is a store outside the column; isotope loaded into it is not in the "
                           "column, so the starting activity of the parent in the column is the stated one.",
    scene_refs=("transport container",), target_terms=("column", "daughter", "parent"),
    pairs=(
        Pair("p0", "At the start, a further {value} {unit} of the parent isotope is {relation}.", "loaded into the column",
             "loaded into the transport container", CO,
             "Isotope loaded into the transport container stays in the container; the column keeps its stated parent activity "
             "and the decay chain is as stated.", ("no daughter isotope", "stable nuclide"), "small amount",
             before_context_reason="The R sentence refers to 'the column' before the context introduces it."),
        Pair("p1", "{relation} a further {value} {unit} of the parent isotope, for one run only.",
             "At the start of the run, the column is also loaded with", "In an earlier run, the column was also loaded with", EVENT,
             "The column was loaded with the further isotope in an earlier run, for that run only; in the stated run it holds only its "
             "stated activity.", ("no daughter isotope", "stable nuclide"), "small amount"),
    ),
    notes="M250 phase 2: no C or K (see NO_C, NO_K).")

# --- S258 --------------------------------------------------------------------------------------------------------------------------

S258 = _spec(
    "S258", quantity_phrase="a further mass of cobalt", quantity_type="mass", unit="g", values=(0.0013, 0.0027, 0.0056),
    heldout_values=(0.0018, 0.0039),
    relevant=rv.RelevantWiring("m", "add", "Further radioactive cobalt incorporated into the source when it is made adds to its mass of the "
                                           "isotope, so m becomes m + q."),
    scene_clause="A shielded vault and a waste drum stand in the corridor.",
    scene_object_rationale="A shielded vault and a waste drum in the corridor are stores of their own; cobalt put into either is not in "
                           "the source, so the mass of the isotope in the source is the stated one.",
    scene_refs=("vault",), target_terms=("source", "isotope", "activity"),
    pairs=(
        Pair("p0", "When the source is made, a further {value} {unit} of the radioactive cobalt is {relation}.",
             "incorporated into the source", "stored in the vault", CO,
             "Cobalt stored in the vault stays in the vault; the source keeps its stated mass of the isotope and its age, half-life "
             "and decay products are as stated.", ("decay products are not radioactive", "removed from it while it stands"),
             "small amount",
             before_context_reason="The R sentence refers to 'the source' before the context introduces it."),
        Pair("p1", "In making the source, a further {value} {unit} of the radioactive cobalt goes {relation}.",
             "into the source", "into the waste drum", CO,
             "Cobalt tipped into the waste drum stays in the drum; the source keeps its stated mass of the isotope and its age, "
             "half-life and decay products are as stated.", ("decay products are not radioactive", "removed from it while it stands"),
             "small amount",
             d_kind_note="A source is made once, so no earlier event of the same source exists that could be stated without "
                         "contradicting the base; a second co-present object (the waste drum) is used for pair 1."),
    ),
    notes="M250 phase 2: no C or K (see NO_C, NO_K); pair 1 is a second co-present pair (d_kind_note).")

# --- S259 --------------------------------------------------------------------------------------------------------------------------

S259_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the pressure of the gas", "pressure", "kPa", (35.0, 62.0, 150.0), "The gas in the flask {relation} {value} {unit}.",
        (P("c0", "is at a pressure of"), P("c1", "is held at a pressure of")),
        "n*((q/(kB*T))*(erfc(vc/sqrt(2*kB*T/m)) + 2*(vc/sqrt(2*kB*T/m))*exp(-(vc/sqrt(2*kB*T/m))**2)/sqrt(pi)))/(q/(kB*T))",
        ("number density of the gas n_d = p / (k T)", "number density of the fast atoms = n_d * F", "fraction F = (fast per volume) / n_d"),
        "n*(erfc(vc/sqrt(2*kB*T/m)) + 2*(vc/sqrt(2*kB*T/m))*exp(-(vc/sqrt(2*kB*T/m))**2)/sqrt(pi))*(q/101325)",
        nonnumeric_fill="a known pressure"),
    "uncommon", "That the shape of the Maxwell speed distribution does not depend on the pressure or the density of the gas is true but "
                "is rarely stated for a calculation that goes through number densities.", (44.0, 210.0))

S259 = _spec(
    "S259", quantity_phrase="a further warming by sunshine", quantity_type="temperature_change", unit="K", values=(9.0, 17.0, 31.0),
    heldout_values=(12.0, 24.0),
    relevant=rv.RelevantWiring("T", "add", "Sunshine that warms the flask by q before the speeds are measured adds to the temperature of "
                                           "the gas, so T becomes T + q."),
    cancelling=S259_C,
    scene_clause="A window frame leans against the wall.",
    scene_object_rationale="A window frame leaning against the wall is a piece of joinery apart from the flask; sunshine that warms "
                           "it does not warm the flask, so the temperature of the gas is the stated one.",
    scene_refs=("window frame",), target_terms=("flask", "helium", "atoms", "gas"),
    pairs=(
        Pair("p0", "Before the speeds are measured, sunshine warms {relation} by {value} {unit}.", "the flask", "the window frame", CO,
             "Sunshine that warms the window frame leaves the flask and its gas at the stated temperature; the amount of gas and "
             "its equilibrium are as stated.", ("ideal monatomic gas", "Maxwell distribution"), "a modest amount",
             before_context_reason="The R sentence refers to 'the flask' and 'the speeds' before the context introduces them."),
        Pair("p1", "{relation} {value} {unit} warmer than at the start.",
             "When the speeds are measured, the sunlit flask is also", "In an earlier experiment, the sunlit flask was also",
             EVENT,
             "Sunshine warmed the flask in an earlier experiment; in the stated experiment the gas is at the stated temperature.",
             ("ideal monatomic gas", "Maxwell distribution"), "a modest amount"),
    ),
    notes="M250 phase 2: C is the pressure of the gas (Maxwell fraction); no K (see NO_K).")

# --- S260 --------------------------------------------------------------------------------------------------------------------------

S260_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the volume of the vessel", "volume", "L", (1.4, 5.2, 12.0), "The vessel {relation} {value} {unit}.",
        (P("c0", "has a volume of"), P("c1", "has an internal volume of")),
        "sqrt(8*kB*T/(pi*m))*sqrt(2)*pi*d**2*((p*q/(kB*T))/q)",
        ("number of molecules N = p V / (k T)", "number density n = N / V", "mean free path lambda = 1 / (sqrt(2) n sigma)",
         "z = v / lambda"),
        "sqrt(8*kB*T/(pi*m))*sqrt(2)*pi*d**2*(p*q/(kB*T))", nonnumeric_fill="a known volume"),
    "uncommon", "That the collision rate of a molecule does not depend on the size of the vessel follows from the number density but "
                "is rarely stated.", (2.3, 8.1))

S260_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the width of the vessel", "length", "cm", (4.5, 12.0, 33.0), "The vessel {relation} {value} {unit}.",
        (P("k0", "measures across"), P("k1", "has a width of")), "10*lam < q", "vbar/q", 0.00001, nonnumeric_fill="a modest size"),
    _ko("A vessel no wider than a few mean free paths would make the molecules collide mostly with the walls, which contradicts "
        "the stated condition that only collisions between molecules matter; the premise is contradicted, not merely changed."),
    (6.5, 21.0))

S260 = _spec(
    "S260", quantity_phrase="a further pressure of nitrogen", quantity_type="pressure", unit="kPa", values=(17.0, 33.0, 58.0),
    heldout_values=(24.0, 45.0),
    relevant=rv.RelevantWiring("p", "add", "Further nitrogen at the same temperature let into the vessel adds to the pressure of the gas "
                                           "in it, so p becomes p + q."),
    cancelling=S260_C, conditional=S260_K,
    scene_clause="A gas cylinder stands beside the vessel.",
    scene_object_rationale="A gas cylinder beside the vessel is a store of gas outside it; nitrogen let into the cylinder is not in the "
                           "vessel, so the pressure of the gas in the vessel is the stated one.",
    scene_refs=("gas cylinder",), target_terms=("vessel", "molecule", "collision"),
    pairs=(
        Pair("p0", "Before the collisions are counted, a further {value} {unit} of nitrogen at the same temperature is {relation}.",
             "let into the vessel", "let into the gas cylinder", CO,
             "Nitrogen let into the gas cylinder stays in the cylinder; the vessel keeps its stated pressure and temperature "
             "and the model of the molecules is as stated.", ("in thermal equilibrium", "only collisions between molecules"),
             "small amount",
             before_context_reason="The R sentence refers to 'the vessel' before the context introduces it."),
        Pair("p1", "{relation} a further {value} {unit} of nitrogen at the same temperature, for one run only.",
             "Before the collisions are counted, the vessel also holds", "In an earlier experiment, the vessel also held", EVENT,
             "The vessel held the further nitrogen in an earlier experiment, for that experiment only; in the stated run it has only its "
             "stated pressure.", ("in thermal equilibrium", "only collisions between molecules"), "small amount"),
    ),
    notes="M250 phase 2: C is the volume of the vessel, K is the width of the vessel (collisional regime, small Knudsen number).")

# --- S261 --------------------------------------------------------------------------------------------------------------------------

S261_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the Reynolds number limit of Stokes' law", "reynolds_number", "1", (0.7, 1.4, 2.6),
        "Stokes' law {relation} {value} {unit}.", (P("k0", "holds up to a Reynolds number of"),
                                                   P("k1", "is valid below a Reynolds number of")),
        "rf*vt*2*r/eta < q", "vt/(1 + 3*q/16)", 0.05, nonnumeric_fill="a known limit"),
    _ko("A Reynolds number above the limit of Stokes' law would make the drag on the sphere something other than the stated Stokes "
        "drag, so the terminal speed asked for would belong to a different drag law; the premise is contradicted, not merely changed."),
    (0.9, 1.9))

S261 = _spec(
    "S261", quantity_phrase="a further load of lead shot", quantity_type="mass", unit="g", values=(0.04, 0.09, 0.17),
    heldout_values=(0.06, 0.13),
    relevant=rv.RelevantWiring("m", "add", "Further lead shot loaded into the sphere before the release adds to its total mass, so m becomes "
                                           "m + q."),
    conditional=S261_K,
    scene_clause="A fishing float lies beside the tank.",
    scene_object_rationale="A fishing float beside the tank is a separate body from the sphere; shot loaded into it is not in the "
                           "sphere, so the total mass of the sphere is the stated one.",
    scene_refs=("fishing float",), target_terms=("sphere", "tank", "liquid"),
    pairs=(
        Pair("p0", "Before the release, a further {value} {unit} of lead shot is {relation}.", "loaded into the sphere",
             "loaded into the fishing float", CO,
             "Shot loaded into the fishing float stays in the float; the sphere keeps its stated mass and radius, and the liquid and "
             "its drag law are as stated.", ("liquid that is at rest", "the Stokes drag"), "small amount",
             before_context_reason="The R sentence refers to 'the sphere' before the context introduces it."),
        Pair("p1", "{relation} a further {value} {unit} of lead shot, for one release only.",
             "When the sphere is released, it is also loaded with", "On an earlier release, it was also loaded with", EVENT,
             "The sphere was loaded with the further shot on an earlier release, for that release only; at the stated release it holds "
             "only its stated load.", ("liquid that is at rest", "the Stokes drag"), "small amount"),
    ),
    notes="M250 phase 2: K is the Reynolds number limit of Stokes' law (regime of the drag law); no C (see NO_C).")

# --- S262 --------------------------------------------------------------------------------------------------------------------------

S262_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the Reynolds number up to which the flow stays laminar", "reynolds_number", "1", (1800.0, 2100.0, 2500.0),
        "The flow in the tube {relation} {value} {unit}.",
        (P("k0", "stays laminar up to a Reynolds number of"), P("k1", "remains laminar below a Reynolds number of")),
        "rho*(rho*g*h0*r**2/(8*eta*Lc))*2*r/eta < q", "tc*q/1000", 0.05, nonnumeric_fill="a known limit"),
    _ko("A Reynolds number limit below the actual Reynolds number of the flow would make the flow turbulent, which contradicts the "
        "stated condition that it is laminar at every depth, so the Poiseuille law would not give the drain time; the premise is "
        "contradicted, not merely changed."),
    (1950.0, 2300.0))

S262 = _spec(
    "S262", quantity_phrase="a further depth of oil", quantity_type="length", unit="cm", values=(7.0, 13.0, 21.0),
    heldout_values=(11.0, 17.0),
    relevant=rv.RelevantWiring("h0", "add", "Oil topped up in the tank before the draining starts adds to the initial depth, so h0 becomes "
                                            "h0 + q."),
    conditional=S262_K,
    scene_clause="A bucket of oil stands beside the tank.",
    scene_object_rationale="A bucket of oil beside the tank is a separate vessel; oil poured into it does not enter the tank, so the "
                           "initial depth of the oil in the tank is the stated one.",
    scene_refs=("bucket",), target_terms=("tank", "tube", "drain"),
    pairs=(
        Pair("p0", "Before the draining starts, the oil in {relation} is topped up by {value} {unit}.", "the tank", "the bucket", CO,
             "Oil topped up in the bucket stays in the bucket; the tank keeps its stated initial depth and the tube and the flow law "
             "are as stated.", ("steady and laminar at every depth", "end effects"), "a modest depth",
             before_context_reason="The R sentence refers to 'the tank' before the context introduces it."),
        Pair("p1", "{relation} topped up by {value} {unit}, for one experiment only.",
             "Before the draining starts, the oil in the tank is also", "In an earlier experiment, the oil in the tank was also", EVENT,
             "The oil in the tank was topped up in an earlier experiment, for that experiment only; in the stated experiment the tank "
             "starts at its stated depth.", ("steady and laminar at every depth", "end effects"), "a modest depth"),
    ),
    notes="M250 phase 2: K is the Reynolds number limit of laminar flow in the tube; no C (see NO_C).")


ROLE_SPECS: dict[str, r2.RoleSpecV2] = {
    s.structure_id: s for s in (S251, S252, S253, S254, S255, S256, S257, S258, S259, S260, S261, S262)}
SPECS = ROLE_SPECS

STRUCTURE_FACTORIES = {f().structure_id: f for f in le.ALL}

K_KINDS: dict[str, str] = {
    "S254": "far-field (point-source) regime: the source is small compared with the distance",
    "S256": "classical limit of the lattice heat capacity (Debye temperature below the temperature of the solid)",
    "S260": "collisional regime (mean free path much shorter than the vessel, small Knudsen number)",
    "S261": "creeping-flow regime of the drag law (Reynolds number below the limit of Stokes' law)",
    "S262": "laminar flow (Reynolds number below the transition value)",
}

# Structures that cannot honestly carry the design. None in this batch.
INFEASIBLE: dict[str, str] = {}

NO_C: dict[str, str] = {
    "S252": "Every stated quantity (mass, radii, altitudes, gravity) survives in the work; a free quantity such as the duration of the "
            "transfer or the thrust appears in no stated relation, so nothing enters and cancels.",
    "S254": "Power, distance and absorption all survive in the intensity; a free quantity such as the frequency would change the "
            "absorption coefficient, so it does not cancel.",
    "S257": "Both half-lives, the starting activity and the time all survive in the daughter activity; a free quantity such as the "
            "volume of the column appears in no stated relation, so nothing enters and cancels.",
    "S258": "Mass, atomic mass, half-life and age all survive in the activity; a free quantity such as the volume of the source "
            "appears in no stated relation, so nothing enters and cancels.",
    "S261": "Mass, radius, density, viscosity and gravity all survive in the terminal speed; a free quantity such as the depth of "
            "the tank appears in no stated relation, so nothing enters and cancels.",
    "S262": "Viscosity, density, tube dimensions, tank area and depths all survive in the time; a free quantity such as the "
            "temperature of the oil would change the viscosity, so it does not cancel.",
}
NO_K: dict[str, str] = {
    "S251": "The only regime condition (a launch speed below the escape speed) is a property of the stated speed, not of a further "
            "quantity, and the out-of-regime answer (escape) is not a number of the same kind.",
    "S252": "The regime of circular orbits above the atmosphere has no sharp threshold quantity and no definite out-of-regime answer.",
    "S253": "The plane-wave, flat-surface regime has no sharp threshold quantity and no definite out-of-regime pressure amplitude.",
    "S255": "The small-curvature condition changes the answer continuously and by less than the grading tolerance inside the regime, so "
            "no out-of-regime law separates from the in-regime answer at the study values.",
    "S257": "The chain has no regime threshold: the answer is one closed form for any two half-lives that differ.",
    "S258": "The exponential law of decay has no regime threshold and no definite out-of-regime answer.",
    "S259": "The classical (Maxwell) regime has no sharp threshold quantity stated by the problem and no definite out-of-regime "
            "answer for the fast amount at the study values.",
}


def structure(structure_id: str) -> gr.Structure:
    """The new structure with the spec's scene clause appended to its base context."""

    return r2.with_scene(le.STRUCTURES[structure_id], ROLE_SPECS[structure_id].scene_clause)


# What the H4 trace extractor (`TraceContext.target_phrases` / `target_symbols`) must read as a statement of the target: a phrase of the
# question, its head noun and the conventional symbols of the target quantity (and the graph's target node name).
TARGET_TERMS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "S251": (("greatest height above the surface", "greatest height", "height"), ("H", "h_max", "h")),
    "S252": (("work do the engines do", "work", "engines"), ("W", "W_eng", "ΔE")),
    "S253": (("pressure amplitude of the sound wave in the water", "pressure amplitude", "pressure"), ("pt", "p_t", "p")),
    "S254": (("sound intensity does the observer measure", "sound intensity", "intensity"), ("I", "I_obs")),
    "S255": (("vertical deflection of the free end", "deflection", "free end"), ("delta", "δ", "d")),
    "S256": (("heat is supplied to the block", "heat supplied", "heat"), ("Q", "Q_heat")),
    "S257": (("activity of the daughter isotope", "activity", "daughter"), ("Ad", "A_d", "A")),
    "S258": (("activity of the source at the end of that time", "activity", "source"), ("A", "A_t")),
    "S259": (("amount of the helium has atoms", "amount", "atoms"), ("nf", "n_f", "n")),
    "S260": (("collisions with other molecules does one molecule make each second", "collisions", "each second"), ("z", "Z", "f")),
    "S261": (("terminal speed of the sphere", "terminal speed", "speed"), ("vt", "v_t", "v")),
    "S262": (("long does the oil take to fall", "how long", "time"), ("tc", "t_c", "t")),
}
