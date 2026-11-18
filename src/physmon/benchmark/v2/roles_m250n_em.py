"""M250 phase 2, batch em: v2.1 role-by-value specifications for the new structures S211 to S220 (electromagnetism and circuits).

Every spec follows `roles_m0v21` / `roles_m250_c` (plan revision v2.2, section G; admission standard 3.1-3.5, 6.2, 6.3) and the five wording
rules of the M0 v2.1 panel review (journal J15.1-038/039):

1. A pair-1 R sentence describing an event ties the change to the very situation the question asks about (same object and apparatus,
   "before ... is ..." the asked moment), never bare past history.
2. No R sentence contradicts a stated base value or condition (an extra series resistor or an uncharged clip adds to a stated value
   without replacing it; the base texts avoid the word "total" where an extra element is added).
3. The action on a co-present D object is an ordinary, purposeful action for that object (a resistor in series with a lamp, a clip on
   a flag, a further battery in series with a neon sign's supply).
4. The co-present object is never of the same type as the target (lamp, flag, doorbell, flash unit, toy cart, neon sign, electroscope,
   Geiger counter, oscilloscope against bead, motor, coil, cable, capacitor circuit, block, plates, bead, slab).
5. R sentences are in the present tense and name the moment of the question ("before it is released", "before the capacitor is chosen"),
   so a present-tense question has no past-history reading.

6. Every answer-determining condition that a careful reader could doubt is stated, number-free, in the base text or the scene clause
   (ideal source, steady state, vacuum, no air resistance, a bead too small to disturb the charge; the co-present object is
   uncharged, has its own supply or is well clear of the apparatus).
7. A pair-1 D event that attaches or adds something to the target says it was there "for an earlier ... only".
8. No D or N sentence contradicts the scene clause or the base: each D acts on the co-present object with an ordinary action
   (attached, connected, accelerates, added), never as a stated state.

`K_KINDS` records the kind of each K regime (regime conditions of the physics itself); `INFEASIBLE`, `NO_C` and `NO_K` hold the reasons.
"""

from __future__ import annotations

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import lib_m250_em as lib
from physmon.benchmark.v2 import rolevalue as rv
from physmon.benchmark.v2 import rolevalue_v2 as r2

P = rv.Phrasing
Pair = r2.PhrasePair
CO = r2.D_KIND_CO_PRESENT
EVENT = r2.D_KIND_OTHER_EVENT
V21 = r2.VERSION_V21
E_CHARGE = "(1602176634/10**28)"  # the elementary charge as an exact rational (SI), used only inside a cancelling expression
EPS0 = "(8854/10**15)"  # the vacuum permittivity to four figures as an exact rational, cancels inside the expression


def _spec(sid: str, **fields) -> r2.RoleSpecV2:
    return r2.RoleSpecV2(structure_id=sid, version=V21, **fields)


# --- S211 ------------------------------------------------------------------------------------------------------------------------

S211_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the radius of the cavity", "length", "cm", (3.5, 5.5, 8.5), "The cavity {relation} {value} {unit}.",
        (P("c0", "has a radius of"), P("c1", "is hollowed out to a radius of")),
        f"q0*((((4/3)*pi*q**3*(3*{EPS0}*E0/R))*d)/(4*pi*{EPS0}*q**3))/m",
        ("charge of the removed material Qc = (4/3) pi a^3 rho, with rho = 3 eps0 E0 / R",
         "field of the removed ball at distance d from its centre = Qc d / (4 pi eps0 a^3)", "cavity field = that field (a^3 cancels)"),
        "q0*E0*d/(R*m)*(1 - (q/R)**2)", nonnumeric_fill="a known size"),
    "standard", "That the field in a spherical cavity is uniform and does not depend on the size of the cavity is a standard "
                "result of upper-level electrostatics (superposition with Gauss's law) but is not a headline fact.", (4.5, 7.0))

S211 = _spec(
    "S211", quantity_phrase="a plastic clip", quantity_type="mass", unit="g", values=(0.25, 0.7, 1.4), heldout_values=(1.6, 1.9),
    relevant=rv.RelevantWiring("m", "add", "An uncharged clip attached to the bead adds its mass to the mass of the bead, so m becomes "
                                           "m + q while the charge of the bead is unchanged."),
    cancelling=S211_C,
    scene_clause="An uncharged cardboard flag stands on the bench beside the apparatus.",
    scene_object_rationale="A cardboard flag on the bench is not part of the ball, the cavity or the bead; it carries no charge that "
                           "reaches the cavity, so the field in the cavity and the bead are those of the problem.",
    scene_refs=("flag",), target_terms=("bead", "ball", "cavity"),
    pairs=(
        Pair("p0", "An uncharged {value} {unit} plastic clip is attached to {relation}.", "the bead before it is released",
             "the cardboard flag", CO,
             "A clip attached to a flag adds mass to the flag; the bead, the ball and the cavity are unchanged, so the bead's mass "
             "and its acceleration are those of the problem.", ("released from rest", "Neglect gravity"), "small",
             before_context_reason="The R sentence refers to 'the bead' and to its release before the context introduces them."),
        Pair("p1", "An uncharged {value} {unit} plastic clip {relation}.", "is stuck to the bead at the moment it is released",
             "was stuck to the bead for an earlier trial only", EVENT,
             "The clip was on the bead in an earlier trial, which is over; the bead of the stated release carries no clip, so its "
             "mass is the stated one.", ("released from rest", "Neglect gravity"), "small"),
    ),
    notes="M250 phase 2: C is the radius of the cavity (the field in a spherical cavity is uniform), no K (see NO_K).")

# --- S212 ------------------------------------------------------------------------------------------------------------------------

S212_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the rms voltage of the supply", "voltage", "V", (125.0, 190.0, 260.0), "The supply {relation} {value} {unit}.",
        (P("c0", "has an rms voltage of"), P("c1", "is held at an rms voltage of")),
        "(q*XL/Zmag**2)/(q*2*pi*f)",
        ("quadrature (inductive) current of the motor = V X_L / |Z|^2", "capacitor current = V omega C",
         "setting the two equal: C = (V X_L / |Z|^2) / (V omega)"),
        "XL/(2*pi*f*Zmag**2)*(q/230)", nonnumeric_fill="a known voltage"),
    "standard", "That the correcting capacitance does not depend on the supply voltage (reactive current and capacitor current both "
                "scale with it) is standard in power engineering but is not stated as a headline fact.", (290.0, 360.0))

S212 = _spec(
    "S212", quantity_phrase="a resistor", quantity_type="resistance", unit="Ω", values=(3.5, 7.5, 16.0), heldout_values=(5.5, 12.0),
    relevant=rv.RelevantWiring("R", "add", "A resistor in series with the motor, inside the branch across which the capacitor is "
                                           "connected, adds to the resistance of the motor branch, so R becomes R + q."),
    cancelling=S212_C,
    scene_clause="A table lamp with its own supply stands on the bench beside the apparatus.",
    scene_object_rationale="A table lamp with its own supply forms a circuit that shares no wire with the motor, the capacitor or "
                           "their supply, so the motor branch and the capacitor keep their stated values.",
    scene_refs=("lamp",), target_terms=("motor", "supply terminals", "capacitor"),
    pairs=(
        Pair("p0", "A {value} {unit} resistor is {relation}.", "connected in series with the motor", "connected in series with the "
             "table lamp", CO,
             "A resistor in series with the lamp lies in the lamp's own circuit; it shares no wire with the motor branch, so the "
             "resistance of the motor branch is the stated one.", ("ideal sinusoidal supply", "in parallel with the motor"), "small",
             before_context_reason="The R sentence refers to 'the motor' before the context introduces it."),
        Pair("p1", "A {value} {unit} resistor {relation}.", "is connected in series with the motor before the capacitor is chosen",
             "was connected in series with the motor for an earlier test only", EVENT,
             "The resistor was in series with the motor in an earlier test, which is over; in the stated circuit the motor branch has "
             "only its stated resistance and coil.", ("ideal sinusoidal supply", "in parallel with the motor"), "small"),
    ),
    notes="M250 phase 2: C is the rms supply voltage (it cancels from the in-phase condition); no K (see NO_K).")

# --- S213 ------------------------------------------------------------------------------------------------------------------------

S213_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the mass of each ion", "mass", "u", (16.0, 63.0, 133.0), "Each ion {relation} {value} {unit}.",
        (P("c0", "has a mass of"), P("c1", "weighs")),
        f"({E_CHARGE}*Vd/(q*d)*ell/(2*{E_CHARGE}*Va/q))*(ell/2 + L)",
        ("sideways acceleration a_y = Q Vd / (m d), with the ion charge Q (one elementary charge is used as the stand-in)",
         "forward speed squared v^2 = 2 Q Va / m", "tan(theta) = a_y ell / v^2 (the mass and the charge cancel)"),
        "Vd*ell/(2*d*Va)*(ell/2 + L)*(28*1.66053906660e-27/q)", nonnumeric_fill="a known mass"),
    "standard", "That the deflection of an ion beam in plates does not depend on the mass or charge of the ions (only on the two "
                "voltages and the geometry) is standard in cathode-ray-tube optics but is not stated as a headline fact.",
    (39.0, 98.0))

S213 = _spec(
    "S213", quantity_phrase="a further accelerating voltage", quantity_type="voltage", unit="V", values=(1100.0, 1700.0, 3200.0),
    heldout_values=(1900.0, 4200.0),
    relevant=rv.RelevantWiring("Va", "add", "A further accelerating potential difference that the ions cross before the plates adds to "
                                            "the first one, so the speed on entering the plates is set by Va + q."),
    cancelling=S213_C,
    scene_clause="An oscilloscope, which shoots electrons at its own screen, stands beside the apparatus.",
    scene_object_rationale="The electrons of an oscilloscope travel in the oscilloscope's own tube; they are not in the tube of the "
                           "ions and do not touch the ions' plates or screen, so the ions' beam is as stated.",
    scene_refs=("oscilloscope",), target_terms=("ions", "plates", "beam"),
    pairs=(
        Pair("p0", "A further {value} {unit} potential difference {relation}.", "accelerates the ions before they enter the plates",
             "accelerates the electrons of the oscilloscope", CO,
             "A potential difference that accelerates the oscilloscope's electrons acts on them in their own tube; the ions are "
             "accelerated through the stated potential difference only.", ("accelerated from rest", "deflecting plates"), "small",
             before_context_reason="The R sentence refers to 'the ions' and 'the plates' before the context introduces them."),
        Pair("p1", "A further {value} {unit} potential difference {relation}.", "is applied across an extra gap that the ions cross before reaching the plates",
             "was applied across an extra gap that the ions crossed for an earlier run only", EVENT,
             "The further potential difference acted on the ions in an earlier run, which is over; in the stated run the ions "
             "start from rest and cross only the stated potential difference.", ("accelerated from rest", "deflecting plates"),
             "small"),
    ),
    notes="M250 phase 2: C is the mass of each ion (q/m cancels in the deflection); no K (see NO_K).")

# --- S214 ------------------------------------------------------------------------------------------------------------------------

S214_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the time that the field takes to fall", "time", "ms", (45.0, 85.0, 450.0), "The field {relation} {value} {unit} to fall to zero.",
        (P("c0", "takes"), P("c1", "needs")),
        "(N*Phi/q)/R*q",
        ("average emf = N Phi / t", "average current = emf / R", "charge = average current x t"),
        "N*Phi/(q*R)", nonnumeric_fill="a known time"),
    "famous", "That the charge induced in a coil depends on the change of flux linkage and the resistance but not on how fast the "
              "flux changes is a staple textbook statement.", (70.0, 250.0))

S214_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the radius of the solenoid", "length", "cm", (5.5, 7.0, 9.5), "The solenoid {relation} {value} {unit}.",
        (P("k0", "has an inner radius of"), P("k1", "is wound on a tube of radius")),
        "rc < q", "N*B0*pi*q**2/R", 1.0, nonnumeric_fill="a known radius"),
    r2.KOut(False, "If the solenoid were narrower than the coil, the coil would not lie entirely inside it, contradicting the stated "
                   "geometry; the premise would be contradicted, not merely changed."),
    (6.0, 8.5))

S214 = _spec(
    "S214", quantity_phrase="a resistor", quantity_type="resistance", unit="Ω", values=(4.5, 9.5, 17.0), heldout_values=(6.5, 13.0),
    relevant=rv.RelevantWiring("R", "add", "A resistor in series with the coil adds to the resistance of the coil circuit, so R becomes "
                                           "R + q and the charge for a given change of flux falls."),
    cancelling=S214_C, conditional=S214_K,
    scene_clause="A doorbell, wired to a battery of its own, hangs on the wall beside the apparatus.",
    scene_object_rationale="A doorbell wired to its own battery closes a circuit that shares no wire with the coil circuit and sees no "
                           "flux change, so the coil circuit's resistance and the flux through the coil are those of the problem.",
    scene_refs=("doorbell",), target_terms=("coil", "solenoid", "circuit"),
    pairs=(
        Pair("p0", "A {value} {unit} resistor is {relation}.", "connected in series with the coil", "connected in series with the "
             "doorbell", CO,
             "A resistor in series with the doorbell lies in the doorbell's own circuit; it shares no wire with the coil circuit, so "
             "the resistance of the coil circuit is the stated one.", ("self-inductance is negligible", "falls steadily"), "small",
             before_context_reason="The R sentence refers to 'the coil' before the context introduces it."),
        Pair("p1", "A {value} {unit} resistor {relation}.", "is connected in series with the coil before the solenoid current is "
             "switched off", "was connected in series with the coil for an earlier run only", EVENT,
             "The resistor was in series with the coil in an earlier run, which is over; in the stated run the coil circuit has only its "
             "stated resistance.", ("self-inductance is negligible", "falls steadily"), "small"),
    ),
    notes="M250 phase 2: C is the time the field takes to fall (famous); K is the solenoid radius (the coil lies inside the field region).")

# --- S215 ------------------------------------------------------------------------------------------------------------------------

_Z0_LEN = "sqrt((Ltot/q)/(Ctot/q))"
S215_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the length of the cable", "length", "m", (45.0, 120.0, 310.0), "The cable {relation} {value} {unit}.",
        (P("c0", "has a length of"), P("c1", "is cut to a length of")),
        f"(Vs*{_Z0_LEN}/(Rs + {_Z0_LEN}))*(1 + (RL - {_Z0_LEN})/(RL + {_Z0_LEN}))",
        ("inductance per metre L' = Ltot / length", "capacitance per metre C' = Ctot / length",
         "characteristic impedance Z0 = sqrt(L' / C') (the length cancels)"),
        "(Vs*(sqrt(Ltot/Ctot)*q/60)/(Rs + sqrt(Ltot/Ctot)*q/60))*(1 + (RL - sqrt(Ltot/Ctot)*q/60)/(RL + sqrt(Ltot/Ctot)*q/60))",
        nonnumeric_fill="a known length"),
    "standard", "That the characteristic impedance of a uniform line does not depend on its length is standard in transmission-line "
                "theory but is not stated as a headline fact.", (75.0, 200.0))

S215 = _spec(
    "S215", quantity_phrase="a resistor", quantity_type="resistance", unit="Ω", values=(22.0, 42.0, 65.0), heldout_values=(28.0, 95.0),
    relevant=rv.RelevantWiring("Rs", "add", "A resistor in series with the source adds to its internal resistance, so the resistance "
                                            "that the source presents to the cable becomes Rs + q."),
    cancelling=S215_C,
    scene_clause="A signal lamp, run from a battery of its own, stands beside the apparatus.",
    scene_object_rationale="A signal lamp on its own battery forms a circuit that shares no wire with the source, the cable or the "
                           "load, so the source's internal resistance and the cable are those of the problem.",
    scene_refs=("signal lamp",), target_terms=("source", "cable", "load"),
    pairs=(
        Pair("p0", "A {value} {unit} resistor is {relation}.", "connected in series with the source", "connected in series with the "
             "signal lamp", CO,
             "A resistor in series with the signal lamp lies in the lamp's own circuit; it shares no wire with the source, so the "
             "source's internal resistance is the stated one.", ("lossless cable", "switched on at time zero"), "small",
             before_context_reason="The R sentence refers to 'the source' before the context introduces it."),
        Pair("p1", "A {value} {unit} resistor {relation}.", "is connected in series with the source before it is switched on",
             "was connected in series with the source for an earlier test only", EVENT,
             "The resistor was in series with the source in an earlier test, which is over; in the stated test the source has only "
             "its stated internal resistance.", ("lossless cable", "switched on at time zero"), "small"),
    ),
    notes="M250 phase 2: C is the length of the cable (the impedance does not depend on it); no K (see NO_K).")

# --- S216 ------------------------------------------------------------------------------------------------------------------------

_W = "sqrt((C1 + C2)/(q*C1*C2))"
S216_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the inductance of the coil", "inductance", "mH", (30.0, 120.0, 700.0), "The inductor {relation} {value} {unit}.",
        (P("c0", "has an inductance of"), P("c1", "is wound to an inductance of")),
        f"Veq + (V2 - Veq)*cos({_W}*(pi/{_W}))",
        ("angular frequency of the transfer w = sqrt((C1 + C2) / (L C1 C2))",
         "voltage on the second capacitor v2(t) = Veq + (V2 - Veq) cos w t",
         "first maximum at t = pi / w, where w t = pi (the inductance cancels)"),
        "Veq + (V2 - Veq)*exp(-q*100)", nonnumeric_fill="a known inductance"),
    "standard", "That the peak voltage of an LC charge transfer does not depend on the inductance (it only sets the period) is "
                "standard in circuit theory but is not stated as a headline fact.", (55.0, 300.0))

S216 = _spec(
    "S216", quantity_phrase="a further capacitor", quantity_type="capacitance", unit="μF", values=(7.0, 22.0, 35.0),
    heldout_values=(13.0, 27.0),
    relevant=rv.RelevantWiring("C1", "add", "A further capacitor charged to the same voltage, in parallel with the first capacitor, "
                                            "adds to its capacitance at the same voltage, so C1 becomes C1 + q."),
    cancelling=S216_C,
    scene_clause="A camera flash unit, run from a battery of its own, stands beside the circuit.",
    scene_object_rationale="A flash unit run from a battery of its own has no wire in common with the two capacitors, the inductor or "
                           "the switch, so the capacitance and charge that the transfer sees are the stated ones.",
    scene_refs=("flash unit",), target_terms=("first capacitor", "second capacitor", "inductor"),
    pairs=(
        Pair("p0", "A {value} {unit} capacitor, charged to the same voltage, is connected in parallel with {relation}.",
             "the first capacitor", "the flash unit", CO,
             "A capacitor in parallel with the flash unit adds capacitance to the flash unit only; it shares no wire "
             "with the circuit, whose first capacitor has its stated capacitance and charge.",
             ("positive plates joined", "no current in the inductor"), "small",
             before_context_reason="The R sentence refers to 'the first capacitor' before the context introduces it."),
        Pair("p1", "A {value} {unit} capacitor, charged to the same voltage, {relation}.",
             "is connected in parallel with the first capacitor before the switch is closed",
             "was connected in parallel with the first capacitor for an earlier run only", EVENT,
             "The capacitor was in parallel with the first capacitor in an earlier run, which is over; in the stated run the first "
             "capacitor stands alone.", ("positive plates joined", "no current in the inductor"), "small"),
    ),
    notes="M250 phase 2: C is the inductance (it sets only the period); no K (see NO_K).")

# --- S217 ------------------------------------------------------------------------------------------------------------------------

S217_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the coefficient of static friction", "coefficient", "1", (0.35, 0.55, 0.9),
        "The coefficient of static friction between the block and the incline {relation} {value}.",
        (P("k0", "is"), P("k1", "is equal to")),
        "Fd > q*Nn", "0", 1.6, nonnumeric_fill="a known value"),
    r2.KOut(False, "If the static friction were larger than the drive, the block would not move and the stated sliding would be "
                   "contradicted; the speed after a slide would be zero and a gold of exactly zero cannot be graded by a relative "
                   "tolerance."),
    (0.45, 0.75))

S217 = _spec(
    "S217", quantity_phrase="a lead weight", quantity_type="mass", unit="kg", values=(0.1, 0.15, 0.35), heldout_values=(0.7, 1.0),
    relevant=rv.RelevantWiring("m", "add", "An uncharged lead weight strapped to the block adds its mass to the block, so m becomes "
                                           "m + q while the charge and the friction coefficient are unchanged."),
    conditional=S217_K,
    scene_clause="A toy cart stands on a shelf, well clear of the incline.",
    scene_object_rationale="A toy cart on a shelf is not on the incline and takes no part in the block's motion, so the block, the "
                           "incline and the field are those of the problem.",
    scene_refs=("toy cart",), target_terms=("block", "incline"),
    pairs=(
        Pair("p0", "A {value} {unit} lead weight is {relation}.", "strapped to the block", "strapped to the toy cart", CO,
             "A weight strapped to the cart loads the cart only; the block keeps its stated mass, so its acceleration up the slope is "
             "the stated one.", ("rests at the foot", "fixed insulating incline"), "small",
             before_context_reason="The R sentence refers to 'the block' before the context introduces it."),
        Pair("p1", "A {value} {unit} lead weight {relation}.", "is strapped to the block before the field is switched on",
             "was strapped to the block for an earlier trial only", EVENT,
             "The weight was on the block in an earlier trial, which is over; the block of the stated trial carries no weight, so "
             "its mass is the stated one.", ("rests at the foot", "fixed insulating incline"), "small"),
    ),
    notes="M250 phase 2: no C (see NO_C); K is the coefficient of static friction (sliding versus static).")

# --- S218 ------------------------------------------------------------------------------------------------------------------------

S218_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the breakdown field of the air", "electric_field", "kV/m", (1200.0, 1900.0, 2700.0),
        "The air between the plates {relation} {value} {unit}.",
        (P("k0", "breaks down in fields stronger than"), P("k1", "withstands fields of up to")),
        "V/d0 < q", "0", 300.0, nonnumeric_fill="a known field"),
    r2.KOut(False, "If the air broke down at the smallest separation the plates would discharge through a spark and the stated "
                   "connection to the battery with the plates pulled apart slowly would no longer describe the capacitor; the "
                   "force after a spark is not defined by the stated quantities and a zero gold cannot be graded."),
    (1500.0, 2300.0))

S218 = _spec(
    "S218", quantity_phrase="a further battery", quantity_type="voltage", unit="V", values=(250.0, 450.0, 650.0),
    heldout_values=(750.0, 1800.0),
    relevant=rv.RelevantWiring("V", "add", "A further battery in series with the first adds its emf to it, so the voltage that the "
                                           "capacitor stays connected to becomes V + q."),
    conditional=S218_K,
    scene_clause="A neon sign, run from a supply of its own, hangs on the wall beside the bench.",
    scene_object_rationale="A neon sign run from its own supply forms a circuit that shares no wire with the capacitor and its "
                           "battery, so the voltage across the plates is that of the problem.",
    scene_refs=("neon sign",), target_terms=("the battery", "plates", "capacitor"),
    pairs=(
        Pair("p0", "A further {value} {unit} battery is connected in series with {relation}.", "the battery", "the neon "
             "sign's supply", CO,
             "A battery in series with the neon sign's supply raises the voltage of the sign's circuit only; it shares no wire with the "
             "capacitor, whose battery has its stated emf.", ("stays connected", "slowly pulled apart"), "small",
             before_context_reason="The R sentence refers to 'the battery' before the context introduces it."),
        Pair("p1", "A further {value} {unit} battery {relation}.", "is connected in series with the battery before the plates are "
             "pulled apart", "was connected in series with the battery for an earlier run only", EVENT,
             "The further battery was in series with the battery in an earlier run, which is over; in the stated run the capacitor "
             "is connected to its stated battery only.", ("stays connected", "slowly pulled apart"), "small"),
    ),
    notes="M250 phase 2: no C (see NO_C); K is the breakdown field of the air (dielectric breakdown regime).")

# --- S219 ------------------------------------------------------------------------------------------------------------------------

S219_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the speed perpendicular to the field", "speed", "m/s", (2.5, 6.5, 14.0),
        "The component of its velocity perpendicular to the field {relation} {value} {unit}.",
        (P("c0", "is"), P("c1", "is measured as")),
        "vpar*2*pi*(m*q/(qc*B))/q",
        ("radius of the circular projection r = m v_perp / (q B)", "time of one turn T = 2 pi r / v_perp (v_perp cancels)",
         "pitch = v_par T"),
        "2*pi*(m*q/(qc*B))", nonnumeric_fill="a known value"),
    "famous", "That the period of a charge in a magnetic field does not depend on its speed is a headline fact of cyclotron "
              "motion.", (4.5, 9.0))

S219 = _spec(
    "S219", quantity_phrase="a further charge", quantity_type="charge", unit="mC", values=(1.8, 3.4, 7.5), heldout_values=(2.6, 5.9),
    relevant=rv.RelevantWiring("qc", "add", "A further charge added to the bead adds to its charge, so qc becomes qc + q while its "
                                            "mass is unchanged."),
    cancelling=S219_C,
    scene_clause="An electroscope stands on the bench, well clear of the apparatus.",
    scene_object_rationale="An electroscope on the bench is not in the field and exchanges no charge with the bead, so the bead's "
                           "charge and the field are those of the problem.",
    scene_refs=("electroscope",), target_terms=("bead", "field"),
    pairs=(
        Pair("p0", "A further {value} {unit} of charge is {relation}.", "added to the bead before it enters the field",
             "added to the electroscope on the bench", CO,
             "Charge added to the electroscope stays on the electroscope; the bead keeps its stated charge, so the period of its "
             "circling is the stated one.", ("uniform magnetic field", "Neglect gravity"), "small amount",
             before_context_reason="The R sentence refers to 'the bead' and 'the field' before the context introduces them."),
        Pair("p1", "A further {value} {unit} of charge {relation}.", "sits on the bead as it enters the field",
             "sat on the bead for an earlier run only", EVENT,
             "The charge was added to the bead in an earlier run, which is over; the bead of the stated run carries only its stated "
             "charge.", ("uniform magnetic field", "Neglect gravity"), "small amount"),
    ),
    notes="M250 phase 2: C is the perpendicular speed (famous, cyclotron period); no K (see NO_K).")

# --- S220 ------------------------------------------------------------------------------------------------------------------------

S220_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the length of slab inside", "length", "cm", (2.5, 4.5, 6.5), "{value} {unit} of the slab {relation}.",
        (P("k0", "lies between the plates"), P("k1", "has been pushed between the plates")),
        "q < ell", "0", 25.0, nonnumeric_fill="A known length"),
    r2.KOut(False, "If the whole slab were between the plates it would no longer be partly inserted and the force would be zero; "
                   "this contradicts the stated partial insertion, and a gold of exactly zero cannot be graded by a relative "
                   "tolerance."),
    (3.5, 5.5))

S220 = _spec(
    "S220", quantity_phrase="a further battery", quantity_type="voltage", unit="V", values=(150.0, 350.0, 700.0),
    heldout_values=(250.0, 450.0),
    relevant=rv.RelevantWiring("V", "add", "A further battery in series with the first adds its emf to it, so the voltage that the "
                                           "capacitor stays connected to becomes V + q."),
    conditional=S220_K,
    scene_clause="A Geiger counter, run from a high-voltage supply of its own, stands beside the apparatus.",
    scene_object_rationale="A Geiger counter on its own supply forms a circuit that shares no wire with the capacitor and its "
                           "battery, so the voltage across the plates is that of the problem.",
    scene_refs=("Geiger counter",), target_terms=("the battery", "plates", "capacitor"),
    pairs=(
        Pair("p0", "A further {value} {unit} battery is connected in series with {relation}.", "the battery", "the Geiger "
             "counter's supply", CO,
             "A battery in series with the Geiger counter's supply raises the counter's voltage only; it shares no wire with the "
             "capacitor, whose battery has its stated emf.", ("stays connected", "Neglect fringe fields"), "small",
             before_context_reason="The R sentence refers to 'the battery' before the context introduces it."),
        Pair("p1", "A further {value} {unit} battery {relation}.", "is connected in series with the battery before the slab is "
             "inserted", "was connected in series with the battery for an earlier run only", EVENT,
             "The further battery was in series with the battery in an earlier run, which is over; in the stated run the capacitor "
             "is connected to its stated battery only.", ("stays connected", "Neglect fringe fields"), "small"),
    ),
    notes="M250 phase 2: no C (see NO_C); K is the length of slab inside (partial-insertion regime).")


ROLE_SPECS: dict[str, r2.RoleSpecV2] = {s.structure_id: s for s in (S211, S212, S213, S214, S215, S216, S217, S218, S219, S220)}
SPECS = ROLE_SPECS

STRUCTURE_FACTORIES = {
    "S211": lib.s211_cavity_bead_acceleration, "S212": lib.s212_power_factor_capacitor, "S213": lib.s213_ion_beam_spot,
    "S214": lib.s214_induced_charge, "S215": lib.s215_transmission_line_load_voltage, "S216": lib.s216_lc_transfer_peak_voltage,
    "S217": lib.s217_charged_block_on_incline, "S218": lib.s218_capacitor_plate_force, "S219": lib.s219_helix_pitch,
    "S220": lib.s220_dielectric_slab_force,
}

# Structures that cannot honestly carry the design. None in this batch.
INFEASIBLE: dict[str, str] = {}

NO_C: dict[str, str] = {
    "S217": "Every input (mass, charge, field, angle, friction coefficient, distance) enters the speed; no free quantity enters a "
            "relation and then cancels. The release height or the time taken appear in no relation.",
    "S218": "The plate area is already fixed by the stated capacitance and separation, so a stated area would contradict the "
            "problem, and the time taken to pull the plates apart appears in no relation (it would be an irrelevant, not a "
            "cancelling, quantity).",
    "S220": "The plate width is already contained in the stated capacitance, so a stated width would over-determine the problem, "
            "and no other free quantity enters a relation and cancels.",
}
NO_K: dict[str, str] = {
    "S211": "The regimes that could matter (a bead small enough not to disturb the charge, a cavity wholly inside the ball) are "
            "stated conditions of the base problem, not quantities with a definite out-of-regime answer.",
    "S212": "The condition that the capacitor does not resonate with the line (no regime change of the physics) has no threshold "
            "quantity; a capacitor voltage rating would be an equipment rating, not a regime of the physics.",
    "S213": "A relativistic correction would not move the answer by more than the loosest grading tolerance at any speed these "
            "ions reach, and the condition that the ions miss the plates is a stated condition, not a further quantity.",
    "S215": "The only regime (the step is ideal, the first wavefront has arrived) is stated in the base problem; a finite rise "
            "time would contradict the stated ideal step.",
    "S216": "A coil or wire resistance would make the oscillation lossy; the largest voltage would then depend on the resistance "
            "gradually, with no exact threshold at which the answer changes.",
    "S219": "The perpendicular speed is not given in the base problem, so no predicate (such as a field region that is wide "
            "enough, or a non-relativistic speed) can be evaluated at the stated values.",
}

# The kind of each K regime: a regime condition of the physics itself.
K_KINDS: dict[str, str] = {
    "S214": "geometric regime: the field region contains the coil (flux limited by the coil or by the solenoid)",
    "S217": "sliding versus static: static friction exceeded by the drive",
    "S218": "dielectric breakdown of the gas (below or above the breakdown field)",
    "S220": "partial versus full insertion of the slab (force independent of depth only while the slab is partly in)",
}


def structure(structure_id: str) -> gr.Structure:
    """The new structure with the spec's scene clause appended to its base context."""

    return r2.with_scene(STRUCTURE_FACTORIES[structure_id](), ROLE_SPECS[structure_id].scene_clause)


TARGET_TERMS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "S211": (("initial acceleration of the bead", "initial acceleration", "acceleration"), ("a", "a_0")),
    "S212": (("capacitance makes the current", "capacitance"), ("C", "C_p")),
    "S213": (("far from the undeflected position", "distance from the undeflected position", "far"), ("ysc", "y", "Y_s")),
    "S214": (("total charge", "charge"), ("Q", "Q_total")),
    "S215": (("voltage across the load", "voltage"), ("VL", "V_L")),
    "S216": (("largest voltage", "voltage"), ("Vmax", "V_max")),
    "S217": (("how fast is the block moving", "block moving", "speed"), ("v", "v_f")),
    "S218": (("electrostatic force", "force"), ("F", "F_e")),
    "S219": (("pitch of the helix", "pitch"), ("p", "P")),
    "S220": (("electric force that draws the slab", "force"), ("F", "F_e")),
}
