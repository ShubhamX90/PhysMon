"""M250 phase 2, batch circ: v2.1 role-by-value specifications for the new structures S263 to S272 (plan revision v2.2, section G and the
wording rules 1 to 8 of the M0 v2.1/v2.2 panel and judge reviews; admission standard 3.2, 6.1, 6.2, 6.3).

Every spec follows `roles_m0v21` (the v2.1 design) on instance 0 of the new structure:

* one R/D quantity with three study values and two held-out values; a co-present D (pair 0, `other_object_same_scene`) whose object is
  introduced by a number-free scene clause in the base context of every cell, and a same-object D (pair 1, `same_object_other_event`: an
  earlier experiment of the same object, never a change applied and then reversed), the same frame, numeral and unit within a pair, an
  attachment-only difference, word counts within three, marker- and consequence-free wording, value hygiene;
* the wording rules of the panel and judge reviews: (1) the pair-1 R sentence says that the event is part of the very situation the question
  asks about, in the present tense, before the asked moment; (2) no R sentence contradicts a stated base value, and every R sentence that
  changes a stated value reads as a further change; (3) the action on the co-present object is an ordinary, purposeful one for that object;
  (4) the co-present object is never of the same type as the target; (5) present-tense questions are matched by present-tense R sentences;
  (6) every answer-deciding condition is stated, number-free, in the base text; (7) a pair-1 event that attaches or adds something to the
  target says it applies for one run only, and any other pair-1 event is anchored in an earlier experiment; (8) no D or N sentence
  contradicts the scene clause or the base; the two pairs use genuinely different frames; no `a`/`A` stands before a number that is read
  with a vowel sound;
* a C quantity where the physics supports a real cancellation (S263, S264, S265, S267, S268, S269, S270, S271, S272); the familiarity of each
  is tagged;
* a K quantity where a genuine regime condition of the physics itself exists (S264, S266, S269, S271, S272); the kind of regime is recorded
  in `K_KINDS`. K_out is recorded as infeasible with the reason in every case.

`INFEASIBLE` holds the structures that cannot honestly carry the design (none in this batch); `NO_C` and `NO_K` hold the reason a
structure has no C or K quantity, so that an absence is a judgement on record and not an omission.
"""

from __future__ import annotations

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import lib_m250_circ as lc
from physmon.benchmark.v2 import rolevalue as rv
from physmon.benchmark.v2 import rolevalue_v2 as r2

P = rv.Phrasing
Pair = r2.PhrasePair
CO = r2.D_KIND_CO_PRESENT
EVENT = r2.D_KIND_OTHER_EVENT
V21 = r2.VERSION_V21
CERT_VERSION = "v2.1"


def _spec(sid: str, **fields) -> r2.RoleSpecV2:
    return r2.RoleSpecV2(structure_id=sid, version=V21, author="agent (M250 phase 2, circ)", **fields)


def _ko(reason: str) -> r2.KOut:
    return r2.KOut(False, reason)


# --- S263 --------------------------------------------------------------------------------------------------------------------------

S263_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the diameter of the bridge wire", "length", "mm", (0.42, 0.65, 0.93), "The bridge wire {relation} {value} {unit}.",
        (P("c0", "has a diameter of"), P("c1", "is drawn to a diameter of")),
        "R*((Lw - l)/(pi*q**2/4))/(l/(pi*q**2/4))*A/Lx",
        ("resistance of the left part of the bridge wire = rho_w l / (pi q^2 / 4)",
         "resistance of the right part = rho_w (Lw - l) / (pi q^2 / 4)", "the ratio of the two parts is (Lw - l) / l"),
        "R*(Lw - l)/l*(q/d)**2*A/Lx", nonnumeric_fill="a known diameter"),
    "standard", "That the section and the material of the bridge wire drop out of the balance condition, which depends only on the "
                "lengths, is taught with the metre bridge but not stated as a rule.", (0.55, 0.78))

S263 = _spec(
    "S263", quantity_phrase="a further resistance", quantity_type="resistance", unit="Ω", values=(4.6, 9.4, 17.0),
    heldout_values=(6.3, 13.0),
    relevant=rv.RelevantWiring("R", "add", "A further resistance q in series with the resistance box makes the resistance in the left gap "
                                           "R + q, which changes the balance condition."),
    cancelling=S263_C,
    scene_clause="A lamp on the bench is dimmed by a rheostat wired to a small battery.",
    scene_object_rationale="A lamp dimmed by a rheostat on a battery is a circuit of its own; it carries none of the bridge current, so "
                           "the balance of the bridge and the resistivity found from it keep their stated values.",
    scene_refs=("rheostat",), target_terms=("resistance box", "box", "sample"),
    pairs=(
        Pair("p0", "Before the galvanometer is brought to zero, {relation} is raised by a further {value} {unit}.",
             "the resistance of the box", "the resistance of the rheostat", CO,
             "Raising the resistance of the rheostat that dims the lamp changes the lamp circuit only; the box in the left gap keeps "
             "its stated resistance, so the balance of the bridge and the resistivity found from it are the stated ones.",
             ("uniform bridge wire", "negligible resistance"), "small amount",
             before_context_reason="The R sentence refers to 'the box' and to the galvanometer before the context introduces them."),
        Pair("p1", "{relation} a further {value} {unit} of resistance in series with the box, for one trial only.",
             "When the galvanometer is brought to zero, the left gap also contains", "In an earlier trial, the left gap also contained",
             EVENT,
             "The left gap contained the further resistance in an earlier trial, for that trial only; in the stated trial it holds only "
             "the box of the stated resistance.", ("uniform bridge wire", "negligible resistance"), "small amount"),
    ),
    notes="M250 phase 2: R is a further resistance in the left gap; C is the diameter of the bridge wire (it drops out of the ratio of "
          "the two parts); no K (see NO_K).")

# --- S264 --------------------------------------------------------------------------------------------------------------------------

S264_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the peak voltage of the source", "voltage", "V", (7.5, 14.0, 26.0), "The source {relation} {value} {unit}.",
        (P("c0", "has a peak voltage of"), P("c1", "delivers a peak voltage of")),
        "atan(Abs((q/sqrt(R**2 + X**2)*(XL - XC))/(q/sqrt(R**2 + X**2)*R)))",
        ("current amplitude I = q / Z", "voltage across the resistor = I R", "net reactive voltage = I (XL - XC)"),
        "atan(Abs(q*(XL - XC)/(R*sqrt(R**2 + X**2))))", nonnumeric_fill="a known voltage"),
    "standard", "That the phase angle of a linear circuit does not depend on the amplitude of the drive follows from the linearity of the "
                "phasor diagram and is taught, but not as a headline fact.", (9.5, 18.0))

S264_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the self-resonant frequency of the inductor", "frequency", "kHz", (95.0, 140.0, 230.0),
        "The inductor {relation} {value} {unit}.", (P("k0", "has a self-resonant frequency of"), P("k1", "shows a self-resonance at")),
        "q > 10*f", "atan(Abs((2*pi*q*L - 1/(2*pi*q*C))/R))", 0.9, nonnumeric_fill="a known frequency"),
    _ko("The problem states that the inductor is an ideal component; a self-resonance within a tenth of the drive frequency would "
        "contradict that statement, and the reactance 2 pi f L on which the question rests would no longer describe the coil."),
    (120.0, 180.0))

S264 = _spec(
    "S264", quantity_phrase="a further resistance", quantity_type="resistance", unit="Ω", values=(6.5, 14.0, 27.0),
    heldout_values=(9.5, 19.0),
    relevant=rv.RelevantWiring("R", "add", "A further resistance q in series with the inductor makes the resistance of the series circuit "
                                           "R + q, which changes the tangent X / R of the phase angle."),
    cancelling=S264_C, conditional=S264_K,
    scene_clause="A small fan on the bench runs from a battery through a resistor.",
    scene_object_rationale="A fan on a battery with its own resistor is a circuit of its own; resistance put in series with the fan "
                           "changes the fan circuit only, so the phase angle of the series circuit keeps its stated value.",
    scene_refs=("fan",), target_terms=("resistor", "inductor", "capacitor", "series", "source"),
    pairs=(
        Pair("p0", "Before the phase angle is measured, a further {value} {unit} of resistance is wired in series with {relation}.",
             "the inductor", "the fan", CO,
             "Resistance wired in series with the fan changes the fan circuit only; the series circuit keeps its stated resistance, "
             "inductance and capacitance, and so its phase angle.", ("ideal components", "steady sinusoidal state"), "small amount",
             before_context_reason="The R sentence refers to 'the inductor' and to the phase angle before the context introduces them."),
        Pair("p1", "{relation} a further {value} {unit} of resistance, for one run only.",
             "While the phase angle is measured, the circuit also includes", "In an earlier run, the circuit also included", EVENT,
             "The circuit included the further resistance in an earlier run, for that run only; in the stated run it holds only the "
             "stated resistor, inductor and capacitor.", ("ideal components", "steady sinusoidal state"), "small amount"),
    ),
    notes="M250 phase 2: R is a further series resistance; C is the peak voltage of the source (it cancels in the ratio of the phasor "
          "voltages); K is the self-resonant frequency of the inductor (lumped, ideal-component regime).")

# --- S265 --------------------------------------------------------------------------------------------------------------------------

S265_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the resistance of the load", "resistance", "Ω", (18.0, 47.0, 82.0), "The load {relation} {value} {unit}.",
        (P("c0", "has a resistance of"), P("c1", "is a resistor of")),
        "q*((2/pi)*(Vp*cos(th0) - 2*Vd*(pi/2 - th0))/q)",
        ("average load current = (1 / pi) integral of (v - 2 Vd) / q over the conducting interval", "load voltage = q times that current"),
        "(2/pi)*(Vp - 2*Vd)*q/(q + 20)", nonnumeric_fill="a known resistance"),
    "standard", "That the average voltage across a resistive load does not depend on its resistance, because the diode is modelled by a "
                "constant drop, follows from Ohm's law but is not a stated textbook fact.", (33.0, 68.0))

S265 = _spec(
    "S265", quantity_phrase="a further supply voltage", quantity_type="voltage", unit="V", values=(8.0, 14.0, 21.0),
    heldout_values=(10.0, 17.0),
    relevant=rv.RelevantWiring("Vm", "add", "A further rms voltage on the supply of the transformer makes the mains voltage Vm + q, which "
                                           "changes the peak voltage of the secondary."),
    cancelling=S265_C,
    scene_clause="A lamp on the bench runs from a variable supply.",
    scene_object_rationale="A lamp on a variable supply is a circuit of its own; a change in the supply voltage of the lamp changes the "
                           "lamp only, so the supply of the transformer and the load voltage of the rectifier keep their stated values.",
    scene_refs=("lamp",), target_terms=("transformer", "rectifier", "load", "diode", "mains"),
    pairs=(
        Pair("p0", "Before the load voltage is measured, the rms supply voltage of {relation} is raised by a further {value} {unit}.",
             "the transformer", "the lamp", CO,
             "Raising the supply voltage of the lamp changes the lamp only; the transformer keeps its stated mains voltage, so the "
             "load voltage of the rectifier is the stated one.", ("ideal switch", "no smoothing capacitor"), "small amount",
             before_context_reason="The R sentence refers to 'the transformer' and to the load voltage before the context introduces them."),
        Pair("p1", "{relation} higher by a further {value} {unit}.",
             "While the load voltage is measured, the rms mains voltage is", "In an earlier experiment, the rms mains voltage was",
             EVENT,
             "The mains voltage was higher by the further amount in an earlier experiment, which is over; in the stated measurement "
             "the transformer is fed with the stated mains voltage.", ("ideal switch", "no smoothing capacitor"), "small amount"),
    ),
    notes="M250 phase 2: R is a further rms mains voltage; C is the resistance of the load (the constant-drop model makes the average "
          "voltage independent of it); no K (see NO_K).")

# --- S266 --------------------------------------------------------------------------------------------------------------------------

S266_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the peak flux density of the core as a fraction of its saturation value", "ratio", "1", (0.42, 0.57, 0.68),
        "The core {relation} {value} of its saturation flux density.", (P("k0", "is driven to"), P("k1", "operates at")),
        "q < 0.8", "Ploss*(1 + q**2)", 1.4, nonnumeric_fill="a known fraction"),
    _ko("The problem states that the magnetising current is negligible; a core driven beyond its saturation flux density would draw a "
        "large magnetising current, contradicting that statement, and the ampere-turn balance of the question would no longer hold."),
    (0.456, 0.63))

S266 = _spec(
    "S266", quantity_phrase="a further load", quantity_type="power", unit="W", values=(65.0, 140.0, 310.0), heldout_values=(95.0, 220.0),
    relevant=rv.RelevantWiring("P", "add", "A further load of power q at the same voltage across the secondary makes the delivered power "
                                           "P + q, which changes both winding currents."),
    conditional=S266_K,
    scene_clause="A battery charger on the bench feeds a small lamp.",
    scene_object_rationale="A battery charger on the bench feeding a lamp is a circuit of its own; load connected to the charger draws "
                           "its current from the charger only, so the windings of the transformer keep their stated currents.",
    scene_refs=("charger",), target_terms=("transformer", "winding", "secondary", "primary"),
    pairs=(
        Pair("p0", "Before the winding losses are measured, a further {value} {unit} of load is connected to {relation}.",
             "the secondary winding", "the charger", CO,
             "Load connected to the charger draws current from the charger only; the secondary winding keeps its stated load, so the "
             "heat in the windings is the stated one.", ("core loss are negligible", "steady sinusoidal"), "small amount",
             before_context_reason="The R sentence refers to 'the secondary winding' and to the losses before the context introduces them."),
        Pair("p1", "{relation} a further {value} {unit} of load, for one run only.",
             "While the winding losses are measured, the secondary winding also feeds",
             "In an earlier run, the secondary winding also fed", EVENT,
             "The secondary winding fed the further load in an earlier run, for that run only; in the stated run it feeds only the "
             "stated load.", ("core loss are negligible", "steady sinusoidal"), "small amount"),
    ),
    notes="M250 phase 2: R is a further load on the secondary; K is the peak flux density of the core relative to saturation (the "
          "no-saturation regime of the ideal transformer); no C (see NO_C).")

# --- S267 --------------------------------------------------------------------------------------------------------------------------

S267_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the emf of the battery", "voltage", "V", (4.5, 7.5, 15.0), "The battery {relation} {value} {unit}.",
        (P("c0", "has an emf of"), P("c1", "supplies an emf of")),
        "-log(1 - (p*q*R2/(R1 + R2))/(q*R2/(R1 + R2)))*Rth*C",
        ("final voltage of the capacitor vf = q R2 / (R1 + R2)", "the stated fraction of it = p vf", "t = -tau ln(1 - p vf / vf)"),
        "-log(1 - p*q/(q + R1*10))*Rth*C", nonnumeric_fill="a known emf"),
    "standard", "That the time to reach a fraction of the final value does not depend on the emf of the battery is taught with the RC "
                "circuit, but with a divider the final value is not the emf, so it is not a headline fact.", (6.0, 12.0))

S267 = _spec(
    "S267", quantity_phrase="a further capacitance", quantity_type="capacitance", unit="μF", values=(6.2, 15.0, 33.0),
    heldout_values=(10.0, 24.0),
    relevant=rv.RelevantWiring("C", "add", "A further capacitance q wired in parallel with the capacitor makes the capacitance C + q, which "
                                           "lengthens the time constant."),
    cancelling=S267_C,
    scene_clause="A camera flash unit on the bench is charged from a small battery.",
    scene_object_rationale="A flash unit charged from a small battery is a circuit of its own; capacitance wired to the flash unit "
                           "changes that unit only, so the capacitor in the divider circuit keeps its stated capacitance.",
    scene_refs=("flash unit",), target_terms=("capacitor", "resistor", "switch", "divider"),
    pairs=(
        Pair("p0", "Before the switch is closed, a further {value} {unit} of capacitance is wired in parallel with {relation}.",
             "the capacitor", "the flash unit", CO,
             "Capacitance wired in parallel with the flash unit changes the flash unit only; the capacitor across the second resistor "
             "keeps its stated capacitance, so the charging time is the stated one.", ("without leakage", "negligible internal resistance"),
             "small amount",
             before_context_reason="The R sentence refers to 'the capacitor' and to the switch before the context introduces them."),
        Pair("p1", "{relation} a further {value} {unit} of capacitance in parallel with it, for one run only.",
             "When the switch is closed, the capacitor also has", "In an earlier run, the capacitor also had", EVENT,
             "The capacitor had the further capacitance in parallel in an earlier run, for that run only; in the stated run it is "
             "alone across the second resistor.", ("without leakage", "negligible internal resistance"), "small amount"),
    ),
    notes="M250 phase 2: R is a further capacitance in parallel; C is the battery emf (it cancels when the fraction is taken of the final "
          "value); no K (see NO_K).")

# --- S268 --------------------------------------------------------------------------------------------------------------------------

S268_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the resistance of the second resistor", "resistance", "Ω", (18.0, 47.0, 82.0), "The second resistor {relation} {value} {unit}.",
        (P("c0", "has a resistance of"), P("c1", "is chosen with a resistance of")),
        "q*I0**2*(L/(2*q))",
        ("the current decays as I = I0 exp(-q t / L)", "the heating rate is I^2 q", "the heat is the integral of I^2 q over time"),
        "L*I0**2/2*q/(q + R1)", nonnumeric_fill="a known resistance"),
    "famous", "That the heat released when an inductor current is switched into a resistor equals the stored energy, whatever the "
              "resistance, is a standard textbook point.", (27.0, 56.0))

S268 = _spec(
    "S268", quantity_phrase="a further emf", quantity_type="voltage", unit="V", values=(3.2, 7.5, 11.0), heldout_values=(4.4, 9.8),
    relevant=rv.RelevantWiring("V", "add", "A further emf q in series with the battery makes the emf V + q, which changes the steady "
                                           "current and so the stored energy."),
    cancelling=S268_C,
    scene_clause="A doorbell on the wall is powered by a small cell.",
    scene_object_rationale="A doorbell powered by a small cell is a circuit of its own; an emf put in series with the doorbell changes "
                           "the bell circuit only, so the battery of the solenoid circuit and the energy released keep their stated values.",
    scene_refs=("doorbell",), target_terms=("battery", "solenoid", "switch", "resistor"),
    pairs=(
        Pair("p0", "Before the switch opens, a further {value} {unit} of emf is inserted in series with {relation}.",
             "the battery", "the doorbell", CO,
             "An emf inserted in series with the doorbell changes the bell circuit only; the battery of the solenoid circuit keeps its "
             "stated emf, so the current of the solenoid and the heat released are the stated ones.",
             ("ideal battery", "negligible resistance"), "small amount",
             before_context_reason="The R sentence refers to 'the battery' and to the switch before the context introduces them."),
        Pair("p1", "{relation} a further {value} {unit} of emf in series with the battery, for one run only.",
             "Before the switch opens, the circuit also contains", "In an earlier run, the circuit also contained", EVENT,
             "The circuit contained the further emf in an earlier run, for that run only; in the stated run the battery alone drives "
             "the current.", ("ideal battery", "negligible resistance"), "small amount"),
    ),
    notes="M250 phase 2: R is a further emf in series with the battery; C is the discharge resistor (the heat equals the stored energy "
          "whatever it is); no K (see NO_K).")

# --- S269 --------------------------------------------------------------------------------------------------------------------------

S269_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the end correction at the open end of the pipe", "length", "cm", (0.99, 2.3, 3.4),
        "The open end of the pipe {relation} {value} {unit}.", (P("c0", "has an end correction of"), P("c1", "needs an end correction of")),
        "c0*sqrt(T2/T0)/(4*((c1/(4*f) - q) + q)) - f",
        ("physical length of the pipe = c1 / (4 f) - q", "effective length = physical length + q", "f2 = c2 / (4 effective length)"),
        "c0*sqrt(T2/T0)/(4*(c1/(4*f) - q)) - f", nonnumeric_fill="a known end correction"),
    "standard", "That a pipe tuned to a fork has an effective length fixed by the tuning, whatever part of it is end correction, is "
                "taught with resonance tubes but is not a headline fact.", (1.7, 2.6))

S269_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the displacement amplitude of the air at the open end of the pipe", "length", "μm", (6.4, 18.0, 47.0),
        "The air at the open end of the pipe {relation} {value} {unit}.",
        (P("k0", "oscillates with a displacement amplitude of"), P("k1", "moves with an amplitude of")),
        "600*q < Leff", "c2/(4*q) - f", 60000.0, nonnumeric_fill="a known amplitude"),
    _ko("The problem states that the speed of sound does not depend on the amplitude; a displacement amplitude comparable with the length "
        "of the pipe would make the wave strongly nonlinear and contradict that statement, so the question would not stay well posed."),
    (13.0, 34.0))

S269 = _spec(
    "S269", quantity_phrase="a further pitch", quantity_type="frequency", unit="Hz", values=(35.0, 62.0, 91.0),
    heldout_values=(48.0, 85.0),
    relevant=rv.RelevantWiring("f", "add", "A further pitch q of the fork makes its frequency f + q, which changes the frequency that the "
                                           "pipe is tuned to and so the beat."),
    cancelling=S269_C, conditional=S269_K,
    scene_clause="A guitar leans against the wall of the hall.",
    scene_object_rationale="A guitar leaning against the wall is an instrument of its own; tuning one of its strings changes that string "
                           "only, so the fork, the pipe and the beat keep their stated values.",
    scene_refs=("guitar",), target_terms=("pipe", "fork", "air in the pipe"),
    pairs=(
        Pair("p0", "Before the pipe is tuned, the pitch of {relation} is raised by a further {value} {unit}.",
             "the fork", "the guitar string", CO,
             "Raising the pitch of a guitar string changes that string only; the fork keeps its stated frequency, so the pipe is tuned "
             "to the stated frequency and the beat is the stated one.", ("do not change with temperature", "all at one temperature"),
             "small amount",
             before_context_reason="The R sentence refers to 'the fork' and to the tuning of the pipe before the context introduces them."),
        Pair("p1", "{relation} pitched higher by a further {value} {unit}.",
             "Before the pipe is tuned, the fork is", "In an earlier experiment, the fork was", EVENT,
             "The fork was pitched higher by the further amount in an earlier experiment, which is over; in the stated experiment the "
             "pipe is tuned to the stated frequency.", ("do not change with temperature", "all at one temperature"), "small amount"),
    ),
    notes="M250 phase 2: R is a further pitch of the fork (the answer is proportional to it, unlike the near-confounded temperature "
          "quantities); C is the end correction (the tuning fixes the effective length); K is the displacement amplitude of the air "
          "(linear acoustics).")

# --- S270 --------------------------------------------------------------------------------------------------------------------------


def _arrival(n: int) -> str:
    hit = f"((q + c*{n}/f)/(c - w))"
    return f"((q + (c + w)*{hit})/(c - v))"


S270_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the distance of the lorry from the post when the note starts", "length", "m", (45.0, 82.0, 180.0),
        "The rear panel of the lorry {relation} {value} {unit} from the post when the note starts.", (P("c0", "is"), P("c1", "stands")),
        f"f - 1/({_arrival(6)} - {_arrival(5)})",
        ("crest n leaves the post at t = n / f and meets the lorry at t_h = (q + c t) / (c - w)",
         "the reflected crest reaches the recorder at T_n = (q + (c + w) t_h) / (c - v)", "frequency of the reflected sound = 1 / (T_(n+1) - T_n)"),
        "f*v/c + 0*q", nonnumeric_fill="a known distance"),
    "uncommon", "That the frequency of sound returned by a flat reflector in uniform motion does not depend on how far away the reflector "
                "is is true but is not a stated textbook fact.", (65.0, 140.0))

S270 = _spec(
    "S270", quantity_phrase="a further pitch", quantity_type="frequency", unit="Hz", values=(170.0, 410.0, 760.0),
    heldout_values=(260.0, 560.0),
    relevant=rv.RelevantWiring("f", "add", "A further pitch q of the note makes its frequency f + q, and the amount by which the returned "
                                           "sound lies below the note is proportional to the frequency."),
    cancelling=S270_C,
    scene_clause="A busker plays a violin on the pavement beside the road.",
    scene_object_rationale="A violin played on the pavement is an instrument of its own; tuning its pitch higher changes the violin "
                           "only, so the note of the siren and the reflected sound keep their stated frequency.",
    scene_refs=("violin",), target_terms=("siren", "note", "recorder", "lorry", "trolley", "reflected sound", "post"),
    pairs=(
        Pair("p0", "Before the reflected sound is picked up, the pitch of {relation} is raised by a further {value} {unit}.", "the note",
             "the violin", CO,
             "Raising the pitch of the violin changes the violin only; the note of the siren keeps its stated frequency, so the "
             "reflected sound and its shift are the stated ones.", ("in still air", "constant"), "small amount",
             before_context_reason="The R sentence refers to 'the note' and to the reflected sound before the context introduces them."),
        Pair("p1", "{relation} higher by a further {value} {unit}.", "While the reflected sound is picked up, the note is",
             "In an earlier experiment, the note was", EVENT,
             "The note was higher by the further amount in an earlier experiment, which is over; in the stated recording the siren "
             "sounds at the stated frequency.", ("in still air", "constant"), "small amount"),
    ),
    notes="M250 phase 2: R is a further pitch of the note (a speed R would be confounded with the speed of sound, a stated constant of "
          "the same dimension); C is the distance of the lorry at the start (it cancels in the spacing of two arrivals); no K "
          "(see NO_K).")

# --- S271 --------------------------------------------------------------------------------------------------------------------------

S271_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the cross-section area of the rod", "area", "cm^2", (0.85, 1.6, 2.9), "The rod {relation} {value} {unit}.",
        (P("c0", "has a cross-section of"), P("c1", "is cut from stock with a cross-section of")),
        "(c/(sqrt(Y*q/(rho*q))/(2*Lr)))/2",
        ("stiffness per unit length of the rod = Y q", "mass per unit length of the rod = rho q", "wave speed = sqrt(Y q / (rho q))"),
        "(c/(sqrt(Y/rho)/(2*Lr)))/2*(1 + 3000*q/Lr**2)", nonnumeric_fill="a known cross-section"),
    "uncommon", "That the longitudinal wave speed of a thin rod does not depend on its cross-section (stiffness and mass per length both "
                "scale with the area) is true but not a headline fact.", (0.98, 2.2))

S271_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the diameter of the rod", "length", "mm", (6.5, 8.21, 13.0), "The rod {relation} {value} {unit}.",
        (P("k0", "has a diameter of"), P("k1", "is drawn to a diameter of")),
        "10*q < Lr", "q", 200.0, nonnumeric_fill="a known diameter"),
    _ko("The problem states that the rod is thin; a diameter of the order of the length of the rod would contradict that statement, "
        "and the wave speed sqrt(Y / rho) of a thin rod on which the question rests would not apply."),
    (7.5, 9.6))

S271 = _spec(
    "S271", quantity_phrase="a further length of metal", quantity_type="length", unit="cm", values=(14.0, 32.0, 55.0),
    heldout_values=(22.0, 45.0),
    relevant=rv.RelevantWiring("Lr", "add", "A further length q of the same metal welded onto one end makes the rod length Lr + q, which "
                                            "changes the vibration frequency and so the dust spacing."),
    cancelling=S271_C, conditional=S271_K,
    scene_clause="A metal railing runs along the wall of the laboratory.",
    scene_object_rationale="A railing along the wall is a fixture of its own; metal welded onto the railing lengthens the railing only, "
                           "so the rod and the dust spacing in the tube keep their stated values.",
    scene_refs=("railing",), target_terms=("rod", "tube", "dust"),
    pairs=(
        Pair("p0", "Before the clamp is fitted, a further {value} {unit} of the same metal is welded onto one end of {relation}.",
             "the rod", "the railing", CO,
             "Metal welded onto the railing lengthens the railing only; the rod keeps its stated length, so its frequency and the "
             "dust spacing are the stated ones.", ("thin metal rod", "fundamental longitudinal mode"), "small amount",
             before_context_reason="The R sentence refers to 'the rod' before the context introduces it."),
        Pair("p1", "{relation} a further {value} {unit} of the same metal welded on, for one experiment only.",
             "When the clamp is fitted, the rod also has", "In an earlier experiment, the rod also had", EVENT,
             "The rod had the further metal welded on in an earlier experiment, for that experiment only; in the stated experiment it "
             "has only its stated length.", ("thin metal rod", "fundamental longitudinal mode"), "small amount"),
    ),
    notes="M250 phase 2: R is a further length of rod; C is the cross-section of the rod (stiffness and mass per length cancel); K is "
          "the rod diameter (thin-rod regime).")

# --- S272 --------------------------------------------------------------------------------------------------------------------------

S272_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the length of the air column when the water starts to fall", "length", "cm", (85.0, 130.0, 190.0),
        "The air column {relation} {value} {unit} long when the water starts to fall.", (P("c0", "is"), P("c1", "measures")),
        "((q - 3*lam/4)/vw) - ((q - 5*lam/4)/vw)",
        ("the column length is q - vw t", "it resonates when it equals 5 lam / 4 and then 3 lam / 4 (less the end correction)",
         "t = (q - L_n) / vw at each resonance"),
        "(q - 3*lam/4)/vw", nonnumeric_fill="a known length"),
    "uncommon", "That the time between successive resonances does not depend on how long the column is at the start is true but not a "
                "stated textbook fact.", (100.0, 160.0))

S272_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the inner radius of the tube", "length", "cm", (1.8, 2.6, 3.2), "The tube {relation} {value} {unit}.",
        (P("k0", "has an inner radius of"), P("k1", "is bored to an inner radius of")),
        "q < 0.29*lam", "q/vw", 40.0, nonnumeric_fill="a known radius"),
    _ko("The problem states that the air column resonates in quarter wavelengths of the fork; a tube whose radius is a large fraction of "
        "the wavelength would carry cross modes and contradict that statement, so the column would not resonate as described."),
    (2.4, 3.0))

S272 = _spec(
    "S272", quantity_phrase="a further drain speed", quantity_type="speed", unit="cm/s", values=(0.4, 0.9, 1.37),
    heldout_values=(0.6, 1.3),
    relevant=rv.RelevantWiring("vw", "add", "A further fall speed q of the water level makes the speed vw + q, which shortens the time "
                                            "between successive resonances."),
    cancelling=S272_C, conditional=S272_K,
    scene_clause="A garden pond drains through a pipe beside the tube.",
    scene_object_rationale="A garden pond is a body of water of its own; drawing its level down faster changes the pond only, so the "
                           "water level in the tube and the time between resonances keep their stated values.",
    scene_refs=("pond",), target_terms=("the tube", "air column", "fork"),
    pairs=(
        Pair("p0", "Before the first resonance is heard, the level in {relation} is drawn down at a rate raised by a further "
                   "{value} {unit}.", "the tube", "the pond", CO,
             "Drawing the level of the pond down faster changes the pond only; the water in the tube keeps its stated fall speed, so "
             "the time between resonances is the stated one.", ("closed below by the water", "constant"), "small amount",
             before_context_reason="The R sentence refers to 'the tube' and to the resonances before the context introduces them."),
        Pair("p1", "{relation} faster by a further {value} {unit}.", "While the resonances are heard, the water level in the tube falls",
             "In an earlier experiment, the water level in the tube fell", EVENT,
             "The water level in the tube fell faster by the further amount in an earlier experiment, which is over; in the stated "
             "experiment it falls at the stated speed.", ("closed below by the water", "constant"), "small amount"),
    ),
    notes="M250 phase 2: R is a further fall speed of the water level; C is the starting length of the air column (the interval of two "
          "resonances does not depend on it); K is the radius of the tube (plane-wave regime).")


SPECS: dict[str, r2.RoleSpecV2] = {s.structure_id: s for s in (S263, S264, S265, S266, S267, S268, S269, S270, S271, S272)}
ROLE_SPECS = SPECS

STRUCTURE_FACTORIES = {f().structure_id: f for f in lc.ALL}

INFEASIBLE: dict[str, str] = {}

NO_C: dict[str, str] = {
    "S266": "The winding heat takes only the delivered power and voltage, the turns and the two winding resistances; no further "
            "quantity of the transformer enters a relation of the graph and then leaves it.",
}

NO_K: dict[str, str] = {
    "S263": "The balance condition holds for any uniform wire and any supply; no regime of a further quantity changes the answer, and the "
            "galvanometer reading is zero by the statement of the problem.",
    "S265": "The constant-drop model is stated, and the diodes conduct at every stated supply (the peak voltage exceeds two drops by a wide "
            "margin); no further quantity has a threshold that changes the answer.",
    "S267": "The ideal-capacitor and ideal-battery conditions are stated outright; no further quantity of the circuit has a threshold that "
            "changes the answer.",
    "S268": "The long-solenoid condition is carried by the stated length and radius, which are inputs; no further quantity has a "
            "threshold that changes the answer.",
    "S270": "Both speeds are subsonic by the stated values, but that is a property of inputs and not of a further quantity with a "
            "threshold that changes the answer; a lorry or cart faster than sound is not described.",
}

# The kind of regime that each K quantity expresses (a condition of the physics itself, not an equipment rating).
K_KINDS: dict[str, str] = {
    "S264": "lumped-element regime (drive frequency far below the self-resonance of the coil, so the inductor is a pure inductance)",
    "S266": "no-saturation regime of a transformer core (peak flux density below saturation, so the magnetising current stays negligible)",
    "S269": "linear-acoustics regime (displacement amplitude much smaller than the wavelength, so the speed of sound is amplitude-independent)",
    "S271": "thin-rod regime (diameter much smaller than the length, so transverse inertia is negligible and the wave speed is sqrt(Y / rho))",
    "S272": "plane-wave regime (tube radius below the cutoff of the first cross mode at the frequency of the fork)",
}


def structure(structure_id: str) -> gr.Structure:
    """The new structure with the spec's scene clause appended to its base context."""

    return r2.with_scene(STRUCTURE_FACTORIES[structure_id](), SPECS[structure_id].scene_clause)


# What the H4 trace extractor (`TraceContext.target_phrases` / `target_symbols`) must read as a statement of the target.
TARGET_TERMS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "S263": (("resistivity of the material", "resistivity"), ("rho", "ρ")),
    "S264": (("magnitude of the phase angle", "phase angle"), ("phi", "φ")),
    "S265": (("average voltage across the load", "average voltage"), ("Vavg", "V_avg", "V_dc")),
    "S266": (("power is dissipated as heat in the two windings", "dissipated as heat", "power"), ("Ploss", "P_loss")),
    "S267": (("how long after the switch is closed", "capacitor voltage reach", "how long"), ("t", "t_p")),
    "S268": (("energy is released as heat", "energy released", "how much energy"), ("E", "Q")),
    "S269": (("beat frequency", "beat"), ("beat", "f_beat")),
    "S270": (("frequency of the reflected sound", "lie below the frequency"), ("df", "Δf")),
    "S271": (("spacing between adjacent dust heaps", "spacing"), ("d", "δ")),
    "S272": (("time passes between two successive resonances", "how much time", "time"), ("t", "T")),
}
