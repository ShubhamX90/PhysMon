"""Role-by-value specifications for M0 v2, batch b (S26, S07, S15, S30, S55, S72). See `rolevalue_v2` for the rules and
`roles_m0v2_a` for how these differ from the M0 specs."""

from __future__ import annotations

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import lib_quantum, lib_thermodynamics, library, library_b, library_c
from physmon.benchmark.v2 import rolevalue as rv
from physmon.benchmark.v2 import rolevalue_v2 as r2

P = rv.Phrasing
Pair = r2.PhrasePair

S26 = r2.RoleSpecV2(
    structure_id="S26", quantity_phrase="a tilt", quantity_type="angle", unit="deg", values=(6.0, 11.0, 14.0),
    heldout_values=(8.0, 13.0),
    relevant=rv.RelevantWiring("theta1", "add", "Tilting the incoming ray q further from the normal within the plane of "
                                                "incidence makes the angle of incidence theta1 + q; the media and the "
                                                "interface are unchanged."),
    pairs=(
        Pair("p0", "The incoming ray is then tilted {value} {unit} farther from {relation}.",
             "the normal, in the plane of incidence", "the vertical", "other_object_same_scene",
             "A ceiling lamp above the bench turns no ray in the experiment; the angle of incidence of the ray at the "
             "interface is untouched.", ("flat interface", "angle of incidence"), "a little",
             d_frame="A ceiling lamp above the bench is then tilted {value} {unit} farther from {relation}.",
             frame_mismatch_reason="The R quantity tilts the ray itself, so the subject is the ray and the reference is the "
                                   "normal; a co-present D needs another object with its own reference direction, so the "
                                   "subject and the reference (a ceiling lamp, the vertical) differ as well as the attachment. "
                                   "A ray tilted 'from the vertical' would not be the stated angle of incidence.",
             before_context_reason="The R sentence refers to 'the incoming ray' and 'the normal' before the context "
                                   "introduces them, and says the tilt is 'then' given, which presupposes the stated angle."),
        Pair("p1", "The laser that produces this ray is then tilted {value} {unit} farther from the normal in the plane of "
                   "incidence and {relation}.", "left there", "tilted back again", "same_object_undone_event",
             "The laser is tilted back to its earlier direction, so the ray meets the interface at the stated angle of "
             "incidence.", ("flat interface", "angle of incidence"), "a little"),
    ),
    notes="R values (6, 11, 14) deg replace (5, 10, 15) deg: 10 deg shares its digits with the refractive index 1 input; larger values coincide with R answers or foils of other cells. "
          "No C or K (see roles_m0_a).",
)

S07 = r2.RoleSpecV2(
    structure_id="S07", quantity_phrase="an extra resistor", quantity_type="resistance", unit="kΩ", values=(1.5, 3.5, 7.0),
    heldout_values=(2.5, 4.0),
    relevant=rv.RelevantWiring("R", "add", "A resistor in series in the single charging loop adds to the series resistance, "
                                           "so the time constant becomes (R + q) C while the emf and the capacitance are "
                                           "unchanged."),
    pairs=(
        Pair("p0", "A {value} {unit} resistor is {relation}.", "connected in series between the battery and the capacitor",
             "connected in series with a lamp and a second battery", "other_object_same_scene",
             "A resistor in series with a lamp and a second battery closes a complete loop of its own; it shares no node "
             "with the capacitor's charging loop, and an ideal emf is unaffected by whatever else is connected to it.",
             ("initially uncharged", "connected in series"), "small",
             before_context_reason="The R sentence refers to 'the battery and the capacitor' before the context introduces "
                                   "them, and the context's own 'a battery' would then read as a second battery."),
        Pair("p1", "Before the connection was made, a {value} {unit} resistor was wired into the charging loop and "
                   "{relation}.", "left there", "taken out again", "same_object_undone_event",
             "The resistor was taken out of the loop again before the connection was made, so the charging loop contains "
             "only its stated resistor.", ("initially uncharged", "connected in series"), "small"),
    ),
    conditional=r2.ConditionalV2(
        rv.ConditionalSpec(
            "the time at which the circuit is broken again", "time", "ms", (250.0, 400.0, 750.0),
            "The circuit {relation} {value} {unit} after the connection is made.",
            (P("k0", "is broken again by opening a switch"), P("k1", "is cut off from the battery")),
            "q > t", "V0*(1 - exp(-q/tau))", 50.0),
        r2.KOut(True, "The question asks for the capacitor voltage at a stated time after the connection, so it stays well "
                      "posed when the circuit is opened earlier than that time: an ideal capacitor with no discharge path "
                      "keeps the charge it had at the break, V0 (1 - exp(-t_break / RC)). Assumes an ideal, non-leaking "
                      "capacitor, which the in-regime answer does not need.", (30.0, 60.0)), (350.0, 600.0)),
    notes="R values (1.5, 3.5, 7) kOhm replace (1, 2, 5): 5 kOhm equalled the resistor input and 2 shared its digits with "
          "20 uF. K times avoid 500 ms (the digits of the 5 kOhm input).",
)

S15 = r2.RoleSpecV2(
    structure_id="S15", quantity_phrase="an extra cell", quantity_type="voltage", unit="V", values=(1.5, 3.0, 4.0),
    heldout_values=(2.0, 3.5),
    relevant=rv.RelevantWiring("V", "add", "An ideal cell in series with the battery, facing the same way, gives an emf "
                                           "V + q across the parallel pair; the two resistors remain the only dissipating "
                                           "elements."),
    pairs=(
        Pair("p0", "A {value} {unit} cell of negligible internal resistance is {relation}.",
             "connected in series with the battery, facing the same way",
             "connected in series with a small fan on the same bench", "other_object_same_scene",
             "A cell in series with a fan forms a loop of its own that shares no node with the two resistors; the "
             "resistors still see only the stated battery.", ("negligible internal resistance", "in parallel"), "small",
             before_context_reason="The R sentence refers to 'the battery', which the context introduces afterwards, and "
                                   "'facing the same way' has no reference yet."),
        Pair("p1", "While the circuit was being built, a {value} {unit} cell of negligible internal resistance was wired "
                   "in series with the battery, facing the same way, and {relation}.", "left there", "then taken out again",
             "same_object_undone_event",
             "The cell was taken out again while the circuit was being built, so the resistors are across the stated battery alone.",
             ("negligible internal resistance", "in parallel"), "small"),
    ),
    conditional=r2.ConditionalV2(
        rv.ConditionalSpec(
            "the current rating of a fuse in the first resistor's branch", "current", "A", (3.0, 5.0, 10.0),
            "The first resistor's branch contains a fuse of negligible resistance that {relation} {value} {unit}.",
            (P("k0", "blows only at currents above"), P("k1", "is rated at")), "V/R1 < q", "V**2/R2", 1.0),
        r2.KOut(False, "If the fuse blew, the power asked for ('what total power do the two resistors dissipate') would "
                       "depend on when it is read: the instant before the fuse blows (36 W) and after (12 W) are both "
                       "defensible, and the question names no time."), (4.0, 8.0)),
    notes="R values (1.5, 3, 4) V replace (1.5, 3, 6): 6 V equalled the R1 input and 4.5 V shared its digits with the 45.6 W R answer. R is wired on the emf as in M0.",
)

S30 = r2.RoleSpecV2(
    structure_id="S30", quantity_phrase="a jug of water", quantity_type="mass", unit="kg", values=(0.8, 1.4, 2.6),
    heldout_values=(0.5, 1.9),
    relevant=rv.RelevantWiring("m", "add", "Water at the same starting temperature mixed into the heated water before "
                                           "heating adds to the mass that the heater's power must warm by the stated rise."),
    pairs=(
        Pair("p0", "A jug holding {value} {unit} of water at the same starting temperature is {relation}.",
             "poured into the water before heating starts", "standing on the bench beside the heater",
             "other_object_same_scene",
             "A jug on the bench is not in the heated water and takes no energy from the heater, which delivers its "
             "stated power to the stated mass only.", ("specific heat capacity", "delivers"), "a small amount",
             before_context_reason="The R sentence refers to 'the water' and to 'heating', both introduced only in the "
                                   "context, and says 'at the same starting temperature' of a temperature not yet stated."),
        Pair("p1", "Before heating starts, a jug holding {value} {unit} of water at the same starting temperature is "
                   "emptied into the water and {relation}.", "left mixed in", "then scooped out again",
             "same_object_undone_event",
             "The same amount of water at the same temperature is scooped out again before heating, so the heater warms "
             "the stated mass.", ("specific heat capacity", "delivers"), "a small amount"),
    ),
    cancelling=r2.CancellingV2(
        rv.CancellingSpec(
            "the initial temperature of the water", "temperature", "K", (278.0, 288.0, 308.0),
            "The water {relation} {value} {unit}.",
            (P("c0", "starts at a temperature of"), P("c1", "is initially at a temperature of")),
            "m*c*((q + dT) - q)/P", ("T_final = T_initial + dT", "Q = m c (T_final - T_initial)", "t = Q / P"),
            "m*c*(q + dT)/P"),
        "standard", "That only the temperature change, not the starting temperature, sets the heat needed is basic "
                    "calorimetry but is not stated as a named fact.", (283.0, 298.0)),
    notes="R values (0.8, 1.4, 2.6) kg replace (0.5, 1, 2): 2 kg equalled the water mass input and 2.6 = 2 + 0.6 made a replace foil equal to another R answer. C temperatures (278, 288, "
          "308) K keep T_initial + dT below 373 K (largest 308 + 60 = 368 K) and clear of the R answers' digits.",
)

S55 = r2.RoleSpecV2(
    structure_id="S55", quantity_phrase="a temperature rise", quantity_type="temperature", unit="K", values=(50.0, 100.0, 200.0),
    heldout_values=(75.0, 160.0),
    relevant=rv.RelevantWiring("T", "add", "Warming the gas sample itself by q before the speeds are measured gives it the "
                                           "equilibrium temperature T + q; v_rms depends only on that temperature and the "
                                           "molar mass."),
    pairs=(
        Pair("p0", "Before the molecular speeds are measured, a heater warms {relation} by {value} {unit}.",
             "this gas sample in its flask", "a second gas sample in another flask", "other_object_same_scene",
             "A second sample in another flask exchanges no heat with this sample, which stays at its stated temperature.",
             ("thermal equilibrium", "ideal gas"), "a few kelvin",
             before_context_reason="The R sentence refers to 'this gas sample', which the context introduces afterwards, and "
                                   "'before the molecular speeds are measured' would then precede the stated equilibrium "
                                   "temperature, so the order of warming and the stated 300 K would be reversed."),
        Pair("p1", "A heater warms this gas sample by {value} {unit} and {relation}.",
             "holds it there while its molecular speeds are measured",
             "then lets it cool back before its molecular speeds are measured", "same_object_undone_event",
             "The sample cools back to its earlier temperature before its speeds are measured, so the measurement is at "
             "the stated temperature.", ("thermal equilibrium", "ideal gas"), "a few kelvin"),
    ),
    cancelling=r2.CancellingV2(
        rv.CancellingSpec(
            "the amount of gas in the sample", "amount_of_substance", "mol", (0.5, 2.0, 5.0),
            "The gas sample {relation} {value} {unit}.",
            (P("c0", "contains"), P("c1", "consists of an amount of gas equal to")),
            "sqrt(2*(3*q*R*T/2)/(q*M))",
            ("U = (3/2) n R T (total translational kinetic energy)", "m_total = n M", "U = (1/2) m_total v_rms^2"),
            "sqrt(3*R*T/(q*M))"),
        "standard", "The rms speed formula sqrt(3RT/M) has no amount of gas in it, so the cancellation is visible in the "
                    "standard formula.", (2.5, 3.5)),
    notes="R as in M0 (values 50, 100, 200 K pass the hygiene rules).",
)

S72 = r2.RoleSpecV2(
    structure_id="S72", quantity_phrase="extra kinetic energy", quantity_type="energy", unit="eV", values=(40.0, 90.0, 180.0),
    heldout_values=(60.0, 130.0),
    relevant=rv.RelevantWiring("Ke", "add", "A second accelerating stage acting on the same electron adds q to its kinetic "
                                            "energy, so its momentum is sqrt(2 m (Ke + q)); the non-relativistic treatment "
                                            "still holds (Ke + q at most 330 eV)."),
    pairs=(
        Pair("p0", "Before the wavelength is determined, a further {value} {unit} of kinetic energy is given {relation}.",
             "to this electron by a second accelerating stage", "to a proton by an accelerating stage on the same bench",
             "other_object_same_scene",
             "Energy given to a proton by a stage on the same bench does not reach the electron; the electron's kinetic "
             "energy is the stated one.", ("starts from rest", "non-relativistically"), "small amount",
             before_context_reason="The R sentence refers to 'this electron' and to the wavelength before the context "
                                   "introduces either, and 'a further' energy presupposes the stated one."),
        Pair("p1", "Before the wavelength is determined, the electron gains a further {value} {unit} in one more "
                   "accelerating gap and {relation}.", "keeps it in the drift region", "loses it in a retarding gap",
             "same_object_undone_event",
             "The electron gives the energy back in a retarding gap, so its kinetic energy is the stated one when the "
             "wavelength is determined.", ("starts from rest", "non-relativistically"), "small amount"),
    ),
    notes="R values (40, 90, 180) eV replace (50, 100, 200): 100 eV shared its digits with the 100.15 pm answer. No C or K.",
)

ROLE_SPECS: dict[str, r2.RoleSpecV2] = {"S26": S26, "S07": S07, "S15": S15, "S30": S30, "S55": S55, "S72": S72}

STRUCTURE_FACTORIES = {
    "S26": library_c.s26_snell_refraction,
    "S07": library.s07_rc_charging,
    "S15": library_b.s15_parallel_power,
    "S30": library_c.s30_heating_time,
    "S55": lib_thermodynamics.s55_rms_speed_of_gas,
    "S72": lib_quantum.s72_de_broglie_electron,
}


def structure(structure_id: str) -> gr.Structure:
    return STRUCTURE_FACTORIES[structure_id]()
