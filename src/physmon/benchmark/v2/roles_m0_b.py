"""Role-by-value specifications, batch M0-b (Stage 15; plan of record Sections 4.2 "four role strata", 4.3 "role-by-value
design").

Structures: S07 (RC charging voltage), S15 (power in two parallel resistors), S30 (time for a heater to warm water),
S55 (rms speed of gas molecules), S72 (de Broglie wavelength of an accelerated electron).

Each `RoleSpec` attaches one quantity q in the relevant role R (wired into one input node) and in the structurally
disconnected role D (same frame and numeral, q on an object with no causal path to the target). Where the physics is
genuinely right, a cancelling (C) or conditionally irrelevant (K) quantity of the same system is added:

* S07 K: the time at which the circuit is broken again; irrelevant while it is later than the asked time (an ideal,
  non-leaking capacitor), otherwise the capacitor stops charging at that time.
* S15 K: the current rating of a fuse in the first resistor's branch; irrelevant while the branch current is below it,
  otherwise the branch opens and only the second resistor dissipates.
* S30 C: the initial water temperature; it enters T_final = T_initial + dT and Q = m c (T_final - T_initial) and cancels
  (no boiling at any value: T_initial + dT stays below 373 K for every instance).
* S55 C: the amount of gas; it enters U = (3/2) n R T and the total mass n M and cancels from v_rms.
"""

from __future__ import annotations

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import lib_quantum, lib_thermodynamics, library, library_b, library_c
from physmon.benchmark.v2 import rolevalue as rv

P = rv.Phrasing

S07 = rv.RoleSpec(
    structure_id="S07", quantity_phrase="an extra resistor", quantity_type="resistance", unit="kΩ",
    values=(1.0, 2.0, 5.0), heldout_values=(1.5, 3.0),
    frame="A {value} {unit} resistor is {relation}.",
    relevant=rv.RelevantWiring(
        "R", "add", "a resistor in series in the single charging loop adds to the series resistance, so the time constant "
                    "becomes (R + q) C while the emf and the capacitance are unchanged"),
    phrasings_r=(P("r0", "connected in series between the battery and the capacitor"),
                 P("r1", "inserted into the charging loop in series with the existing resistor")),
    phrasings_d=(P("d0", "lying in a parts tray on the bench"),
                 P("d1", "soldered onto a spare board in a drawer, not part of this circuit")),
    nonnumeric_fill="small",
    conditional=rv.ConditionalSpec(
        "the time at which the circuit is broken again", "time", "ms", (300.0, 500.0, 1000.0),
        "The circuit {relation} {value} {unit} after the connection is made.",
        (P("k0", "is broken again by opening a switch"), P("k1", "is disconnected from the battery")),
        "q > t", "V0*(1 - exp(-q/tau))", 50.0),
    notes="K: before the break the circuit is unchanged, so the voltage at the asked time is the ordinary charging value; "
          "were the break earlier than the asked time, the non-leaking capacitor would hold V0 (1 - exp(-t_break / RC)).",
)

S15 = rv.RoleSpec(
    structure_id="S15", quantity_phrase="an extra cell", quantity_type="voltage", unit="V",
    values=(1.5, 3.0, 6.0), heldout_values=(4.5, 9.0),
    frame="A {value} {unit} cell of negligible internal resistance is {relation}.",
    relevant=rv.RelevantWiring(
        "V", "add", "an ideal cell in series with the battery, aiding it, raises the emf across the parallel pair to V + q; "
                    "the two resistors remain the only dissipating elements"),
    phrasings_r=(P("r0", "connected in series with the battery, aiding its emf"),
                 P("r1", "added in series with the battery, oriented so that the two emfs add")),
    phrasings_d=(P("d0", "lying unused in a drawer"),
                 P("d1", "powering a wall clock that has no connection with this circuit")),
    nonnumeric_fill="small",
    conditional=rv.ConditionalSpec(
        "the current rating of a fuse in the first resistor's branch", "current", "A", (3.0, 5.0, 10.0),
        "The first resistor's branch contains a fuse of negligible resistance that {relation} {value} {unit}.",
        (P("k0", "blows only at currents above"), P("k1", "is rated at")),
        "V/R1 < q", "V**2/R2", 1.0),
    notes="R is wired on the emf, not on a resistance: a resistor added in series with one branch would itself dissipate "
          "power, and the question asks for the power of the two resistors only. K: below its rating the fuse carries the "
          "branch current V / R1 unchanged; above it the branch opens and only the second resistor dissipates.",
)

S30 = rv.RoleSpec(
    structure_id="S30", quantity_phrase="a jug of water", quantity_type="mass", unit="kg",
    values=(0.5, 1.0, 2.0), heldout_values=(0.75, 1.5),
    frame="A jug holding {value} {unit} of water at the same starting temperature is {relation}.",
    relevant=rv.RelevantWiring(
        "m", "add", "water at the same starting temperature mixed into the heated water before heating adds to the mass "
                    "that the heater's power must warm by the required rise"),
    phrasings_r=(P("r0", "poured into the water before the heater is switched on"),
                 P("r1", "emptied into the heated water and stirred in before heating starts")),
    phrasings_d=(P("d0", "standing on a shelf in the next room"),
                 P("d1", "kept in another kitchen, separate from this heater")),
    nonnumeric_fill="a small amount",
    cancelling=rv.CancellingSpec(
        "the initial temperature of the water", "temperature", "K", (283.0, 293.0, 303.0),
        "The water {relation} {value} {unit}.",
        (P("c0", "starts at a temperature of"), P("c1", "is initially at a temperature of")),
        "m*c*((q + dT) - q)/P",
        ("T_final = T_initial + dT", "Q = m c (T_final - T_initial)", "t = Q / P"),
        "m*c*(q + dT)/P"),
    notes="C values keep T_initial + dT below 373 K for every instance (largest 303 + 60 = 363 K), so no boiling occurs. "
          "Wrong law: the heat computed with the final absolute temperature in place of the rise.",
)

S55 = rv.RoleSpec(
    structure_id="S55", quantity_phrase="a temperature rise", quantity_type="temperature", unit="K",
    values=(50.0, 100.0, 200.0), heldout_values=(75.0, 150.0),
    frame="Before the molecular speeds are measured, a heater raises the temperature {relation} by {value} {unit}.",
    relevant=rv.RelevantWiring(
        "T", "add", "heating the gas sample itself by q before the speeds are measured raises its equilibrium temperature "
                    "to T + q, and v_rms depends only on that temperature and the molar mass"),
    phrasings_r=(P("r0", "of this gas sample, held in a closed rigid container,"),
                 P("r1", "of the gas sample above")),
    phrasings_d=(P("d0", "of an empty oven in the next room"),
                 P("d1", "of an unrelated metal block on another bench")),
    nonnumeric_fill="a few kelvin",
    cancelling=rv.CancellingSpec(
        "the amount of gas in the sample", "amount_of_substance", "mol", (0.5, 2.0, 5.0),
        "The gas sample {relation} {value} {unit}.",
        (P("c0", "contains"), P("c1", "consists of an amount of gas equal to")),
        "sqrt(2*(3*q*R*T/2)/(q*M))",
        ("U = (3/2) n R T (total translational kinetic energy)", "m_total = n M", "U = (1/2) m_total v_rms^2"),
        "sqrt(3*R*T/(q*M))"),
    notes="C wrong law: dividing by the total mass n M while using the molar energy 3RT/2.",
)

S72 = rv.RoleSpec(
    structure_id="S72", quantity_phrase="extra kinetic energy", quantity_type="energy", unit="eV",
    values=(50.0, 100.0, 200.0), heldout_values=(75.0, 150.0),
    frame="Before the wavelength is determined, a further {value} {unit} of kinetic energy is given {relation}.",
    relevant=rv.RelevantWiring(
        "Ke", "add", "a second accelerating stage acting on the same electron adds q to its kinetic energy, so its momentum "
                     "is sqrt(2 m (Ke + q)); the non-relativistic treatment still holds (Ke + q at most 500 eV)"),
    phrasings_r=(P("r0", "to this electron by a second accelerating stage"),
                 P("r1", "to the electron above as it crosses one more accelerating gap")),
    phrasings_d=(P("d0", "to a proton circulating in a cyclotron in another building"),
                 P("d1", "to a separate ion beam on another bench")),
    nonnumeric_fill="small amount",
    notes="No C or K: no quantity of this one-relation system cancels, and a regime quantity (e.g. a relativistic "
          "threshold) has no out-of-regime law that differs from the gold by more than 1% inside the regime.",
)

ROLE_SPECS: dict[str, rv.RoleSpec] = {"S07": S07, "S15": S15, "S30": S30, "S55": S55, "S72": S72}

STRUCTURE_FACTORIES = {
    "S07": library.s07_rc_charging,
    "S15": library_b.s15_parallel_power,
    "S30": library_c.s30_heating_time,
    "S55": lib_thermodynamics.s55_rms_speed_of_gas,
    "S72": lib_quantum.s72_de_broglie_electron,
}


def structure(structure_id: str) -> gr.Structure:
    return STRUCTURE_FACTORIES[structure_id]()
