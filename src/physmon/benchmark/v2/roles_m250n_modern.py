"""M250 phase 2, batch modern: v2.1 role-by-value specifications for the new structures S241 to S250 (plan revision v2.2, section G and the
five wording rules of the LLM-panel review J15.1-038/039; admission standard 3.2, 6.1, 6.2, 6.3).

Every spec follows `roles_m0v21` (the v2.1 design) on instance 0 of the new structure:

* one R/D quantity with three study values and two held-out values, always an extra amount that is added to a stated input and that the
  base text can accommodate without contradiction (rule 2); a co-present D (pair 0, `other_object_same_scene`) whose object is of a
  different type from the target object, is introduced by a number-free scene clause in the base context of every cell, and receives
  an ordinary, purposeful action (a lamp that lights a dial, a nozzle on a jet, a layer on a roof; rules 3 and 4); and a same-object D
  (pair 1, `same_object_other_event`: another measurement, run or exposure of the same apparatus) whose R twin is stated in the present
  tense and tied to the situation that the question asks about ("During this measurement", "For this shield"; rules 1 and 5);
  the same frame, numeral and unit within a pair, an attachment-only difference, word counts within three, marker- and consequence-free
  wording, value hygiene;
* a C quantity where the physics supports a real cancellation (S242, S245, S246, S247, S248, S250);
* a K quantity where a genuine regime condition of the physics itself exists (S241: threshold frequency of the cathode; S243: Coulomb-only
  regime, closest approach outside the nuclear radius; S245: resonance condition, Doppler shift inside the swept range); the kind of
  regime is recorded in `K_KINDS`. K_out is recorded as infeasible with the reason in every case.

`INFEASIBLE` holds the structures that cannot honestly carry the design (none in this batch); `NO_C` and `NO_K` hold the reason a
structure has no C or K quantity, so that an absence is a judgement on record and not an omission.
"""

from __future__ import annotations

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import lib_m250_modern as lm
from physmon.benchmark.v2 import rolevalue as rv
from physmon.benchmark.v2 import rolevalue_v2 as r2

P = rv.Phrasing
Pair = r2.PhrasePair
CO = r2.D_KIND_CO_PRESENT
EVENT = r2.D_KIND_OTHER_EVENT
V21 = r2.VERSION_V21


def _spec(sid: str, **fields) -> r2.RoleSpecV2:
    return r2.RoleSpecV2(structure_id=sid, version=V21, author="agent (M250 phase 2, modern)", **fields)


def _ko(reason: str) -> r2.KOut:
    return r2.KOut(False, reason)


# --- S241 --------------------------------------------------------------------------------------------------------------------------

S241_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the work function of the cathode", "energy", "eV", (1.7, 1.9, 2.1),
        "The work function of the cathode {relation} {value} {unit}.", (P("k0", "is"), P("k1", "has been measured as")),
        "Eph > q", "0", 3.9, nonnumeric_fill="a known value"),
    _ko("Below the threshold frequency no electron is released and the current is exactly zero; the question stays well posed, but a gold of "
        "exactly zero cannot be graded by a relative tolerance and cannot be told from a refusal, so no K_out cell is built."),
    (1.8, 2.25))

S241 = _spec(
    "S241", quantity_phrase="a further lamp", quantity_type="power", unit="mW", values=(1.7, 3.4, 6.2), heldout_values=(2.3, 4.6),
    relevant=rv.RelevantWiring("P", "add", "A further lamp that supplies q more light power to the cathode makes the power that falls on it "
                                           "P + q, and the number of photons per second, and so the current, grows in proportion."),
    conditional=S241_K,
    scene_clause="The current is read from the dial of a meter beside the cell, and the meter is shielded from the window of the cell.",
    scene_object_rationale="The dial of a meter beside the cell is lit by a lamp of its own; light that falls on the dial does not reach the "
                           "cathode, so the power on the cathode and the current are those of the stated beam.",
    scene_refs=("dial",), target_terms=("the cathode", "the cell", "the photocell"),
    pairs=(
        Pair("p0", "A further lamp supplies {value} {unit} more light power to {relation}.", "the cathode", "the dial of the meter", CO,
             "A lamp that lights the dial of the meter does not light the cathode, which is behind its window; the power that falls on "
             "the cathode is the stated one.", ("every released electron is collected", "falls on the cathode"), "a little",
             before_context_reason="The R sentence refers to 'the cathode' before the context introduces it, and 'more light power' has no "
                                   "referent until the stated power has been read."),
        Pair("p1", "{relation} {value} {unit} extra light onto the cathode.", "During this measurement, a second lamp puts",
             "During an earlier measurement only, a second lamp put", EVENT,
             "The further lamp was used in an earlier measurement, which is over; in the measurement of the question the cathode "
             "receives only the stated light.", ("every released electron is collected", "falls on the cathode"), "a little"),
    ),
    notes="M250 phase 2: R is further light power on the cathode; K is the work function of the cathode (photon energy above it); no C (see NO_C).")

# --- S242 --------------------------------------------------------------------------------------------------------------------------

S242_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the counting efficiency", "dimensionless", "1", (0.31, 0.36, 0.46), "The efficiency of the counter {relation} {value}.",
        (P("c0", "is"), P("c1", "has been measured as")),
        "log((q*A1)/(q*A2))/(lam1 - lam2)",
        ("count rate of the first isotope R1 = q A1 exp(-lam1 t)", "count rate of the second isotope R2 = q A2 exp(-lam2 t)",
         "equal count rates: q A1 exp(-lam1 t) = q A2 exp(-lam2 t)"),
        "log(q*A1/A2)/(lam1 - lam2)", nonnumeric_fill="a known value"),
    "standard", "That a counter with the same efficiency for both isotopes compares the activities and not the efficiency is taught in "
                "counting statistics, but it is not a headline fact.", (0.21, 0.26))

S242 = _spec(
    "S242", quantity_phrase="a further batch of the longer-lived isotope", quantity_type="activity", unit="Bq", values=(110.0, 170.0, 360.0),
    heldout_values=(280.0, 430.0),
    relevant=rv.RelevantWiring("A2", "add", "A further batch of the longer-lived isotope, added at the moment of preparation, makes its activity "
                                            "A2 + q, so the count rates cross earlier."),
    cancelling=S242_C,
    scene_clause="A waste drum for used vials stands beside the counter, outside its shielding.",
    scene_object_rationale="A waste drum for used vials is not counted by the counter and is not part of the sample, so what is put into it "
                           "leaves the activities of the two isotopes in the sample as stated.",
    scene_refs=("waste drum",), target_terms=("the sample",),
    pairs=(
        Pair("p0", "Another {value} {unit} batch of the longer-lived isotope is added to {relation}.", "the sample", "the waste drum", CO,
             "A batch that is put into the waste drum is not in the sample and not in the counter; the sample's activities are those of "
             "the stated batches.", ("decay independently", "the same efficiency"), "small",
             before_context_reason="The R sentence refers to 'the sample' and to 'the longer-lived isotope' before the context introduces them."),
        Pair("p1", "{relation} {value} {unit} of the same longer-lived isotope.",
             "At the moment of preparation of this sample, a technician mixes in",
             "At the moment of preparation of an earlier sample only, a technician mixed in", EVENT,
             "The batch was added to an earlier sample, which has been counted and is over; the sample of the question is made from "
             "the stated batches only.", ("decay independently", "the same efficiency"), "a small amount"),
    ),
    notes="M250 phase 2: R is a further batch of the longer-lived isotope; C is the counting efficiency (cancels in the ratio of the count "
          "rates); no K (see NO_K).")

# --- S243 --------------------------------------------------------------------------------------------------------------------------

S243_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the radius of the nuclei", "length", "fm", (6.6, 7.3, 7.5), "The nuclei of the foil {relation} {value} {unit}.",
        (P("k0", "have a radius of"), P("k1", "have a charge radius of")),
        "d > q", "q", 120.0, nonnumeric_fill="a known radius"),
    _ko("If the closest approach were inside the nuclear radius the alpha particle would meet the nuclear force and be absorbed or scattered "
        "by it; the premise of purely electrostatic scattering, stated in the question, would be contradicted, and no certified "
        "answer exists."),
    (6.3, 6.8))

S243 = _spec(
    "S243", quantity_phrase="a further accelerating gap", quantity_type="energy", unit="MeV", values=(3.0, 3.6, 4.2), heldout_values=(1.3, 1.9),
    relevant=rv.RelevantWiring("K", "add", "A further accelerating gap that adds q to the kinetic energy of the alpha particles before the foil "
                                           "makes it K + q, and the head-on closest approach, and so the closest approach, falls."),
    conditional=S243_K,
    scene_clause="A second beam line in the hall, well to the side of the foil, carries protons to a detector test.",
    scene_object_rationale="A second beam line carries its own protons to its own detector; its particles do not reach the foil, so the energy "
                           "of the alpha particles and their scattering are those of the stated source.",
    scene_refs=("second beam line",), target_terms=("the alpha particles", "the alpha particle", "the foil"),
    pairs=(
        Pair("p0", "A further accelerating gap adds {value} {unit} to the kinetic energy of {relation} before they are directed at their targets.",
             "the alpha particles from the source", "the protons of the second beam line", CO,
             "An accelerating gap in the second beam line changes the energy of its protons only; the alpha particles that scatter from "
             "the foil keep the stated source energy.", ("purely electrostatic", "scattered only once"), "a little",
             before_context_reason="The R sentence refers to 'the alpha particles' and to their 'targets' before the context introduces them."),
        Pair("p1", "{relation} {value} {unit} more kinetic energy to each alpha particle before it reaches the foil.",
             "For this scattering, an extra accelerating stage gives", "For an earlier scattering only, an extra accelerating stage gave", EVENT,
             "The gap was used in an earlier scattering run, which is over; in the scattering of the question the alpha particles have "
             "the stated source energy.", ("purely electrostatic", "scattered only once"), "a little"),
    ),
    notes="M250 phase 2: R is a further accelerating gap before the foil; K is the nuclear radius (Coulomb-only regime); no C (see NO_C).")

# --- S244 --------------------------------------------------------------------------------------------------------------------------

S244 = _spec(
    "S244", quantity_phrase="a further accelerating gap", quantity_type="energy", unit="keV", values=(70.0, 130.0, 240.0),
    heldout_values=(95.0, 180.0),
    relevant=rv.RelevantWiring("K", "add", "A further accelerating gap that adds q to the kinetic energy of the positrons before they annihilate "
                                           "makes it K + q, which changes the total energy and the momentum shared by the photons."),
    scene_clause="An ion implanter with its own beam tube and power supplies stands beside the vacuum chamber.",
    scene_object_rationale="The ions of an implanter beside the chamber are accelerated in a separate tube and do not reach the positrons or the "
                           "electron that they annihilate with, so the positron energy is the stated one.",
    scene_refs=("implanter",), target_terms=("the positrons", "the positron"),
    pairs=(
        Pair("p0", "A further accelerating gap adds {value} {unit} to the kinetic energy of {relation} before they reach their targets.",
             "the positrons", "the ions of the implanter", CO,
             "An accelerating gap in the implanter changes the energy of its ions only; the positrons that annihilate keep the stated "
             "source energy.", ("exactly two photons", "free electron that is at rest"), "a little",
             before_context_reason="The R sentence refers to 'the positrons' before the context introduces them."),
        Pair("p1", "{relation} {value} {unit} more kinetic energy to the positron before it annihilates.",
             "For this annihilation, a further accelerating stage gives", "For an earlier annihilation only, a further accelerating stage gave",
             EVENT,
             "The gap was used in an earlier annihilation run, which is over; in the annihilation of the question the positron has the "
             "stated source energy.", ("exactly two photons", "free electron that is at rest"), "a little"),
    ),
    notes="M250 phase 2: R is a further accelerating gap before the annihilation; no C and no K (see NO_C, NO_K).")

# --- S245 --------------------------------------------------------------------------------------------------------------------------

S245_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the photon scattering rate of an atom", "rate", "MHz", (7.7, 9.3, 17.0), "Each atom {relation} {value} {unit}.",
        (P("c0", "scatters photons at a rate of"), P("c1", "scatters light at a rate of")),
        "q*(v0/((h/lam)*q/M))",
        ("force on the atom F = (h / lam) q, photon momentum times scattering rate", "deceleration a = F / M",
         "stopping time t = v0 / a", "number of photons scattered N = q t"),
        "q*v0*M*lam/h", nonnumeric_fill="a steady rate"),
    "uncommon", "That the number of photons needed to stop an atom does not depend on how fast they are scattered is true, but textbooks give "
                "the stopping time and distance, not this count.", (4.3, 6.2))

S245_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the frequency range of the sweep", "frequency", "GHz", (2.2, 2.4, 3.0), "The laser frequency {relation} {value} {unit}.",
        (P("k0", "is swept over a range of"), P("k1", "is swept through")),
        "v0/lam < q", "M*q*lam**2/h", 0.1, nonnumeric_fill="a known range"),
    _ko("If the sweep were narrower than the Doppler shift the atom would fall out of resonance before it had stopped and could not be brought "
        "to rest; the premise of the question, stated in the base text, would be contradicted and the question would have no certified answer."),
    (1.5, 1.7))

S245 = _spec(
    "S245", quantity_phrase="a faster nozzle", quantity_type="energy", unit="eV", values=(0.009, 0.011, 0.036), heldout_values=(0.014, 0.026),
    relevant=rv.RelevantWiring("K", "add", "A faster nozzle that adds q to the kinetic energy of the atoms before they meet the light makes it K + q, so "
                                           "the speed is higher and more photons are needed to stop them."),
    conditional=S245_K, cancelling=S245_C,
    scene_clause="A helium jet cools the walls of the oven, and its gas does not enter the atomic beam.",
    scene_object_rationale="A helium jet that cools the oven walls is a separate gas flow that is not in the atomic beam; a nozzle that speeds up "
                           "the jet does not change the kinetic energy of the atoms of the beam.",
    scene_refs=("helium jet",), target_terms=("the atoms", "each atom", "one atom"),
    pairs=(
        Pair("p0", "A faster nozzle adds {value} {unit} to the kinetic energy of {relation}.", "the atoms", "the helium jet", CO,
             "A nozzle that speeds up the helium jet does not act on the atoms of the beam; they keep the stated kinetic energy.",
             ("stays in resonance", "averages to zero"), "a little",
             before_context_reason="The R sentence refers to 'the atoms' before the context introduces them."),
        Pair("p1", "{relation} {value} {unit} more kinetic energy to each atom before it meets the laser light.",
             "For this slowing run, a faster nozzle gives", "For an earlier slowing run only, a faster nozzle gave", EVENT,
             "The faster nozzle was used in an earlier slowing run, which is over; in the run of the question the atoms enter the beam "
             "with the stated kinetic energy.", ("stays in resonance", "averages to zero"), "a little"),
    ),
    notes="M250 phase 2: R is a faster nozzle; C is the photon scattering rate (cancels between the stopping time and the number scattered); "
          "K is the frequency range of the sweep (resonance condition).")

# --- S246 --------------------------------------------------------------------------------------------------------------------------

S246_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the intensity of the unshielded beam", "intensity", "W/m^2", (0.62, 3.5, 7.3), "The unshielded beam {relation} {value} {unit}.",
        (P("c0", "has an intensity of"), P("c1", "carries an intensity of")),
        "(log(q/(q/F)) - muc*tc)/mupb",
        ("intensity behind the shield I_out = q / F", "intensity behind the shield I_out = q exp(-(muc tc + mupb t))",
         "ratio of the intensities I_out / q = 1 / F"),
        "log(F)/mupb", nonnumeric_fill="a known intensity"),
    "standard", "That the thickness that gives a stated attenuation factor does not depend on the intensity of the beam follows from the "
                "exponential law, but is not stated as a fact.", (0.35, 2.6))

S246 = _spec(
    "S246", quantity_phrase="a further layer of concrete", quantity_type="length", unit="cm", values=(4.3, 7.7, 11.4),
    heldout_values=(5.6, 9.2),
    relevant=rv.RelevantWiring("tc", "add", "A further layer that adds q to the concrete wall makes its thickness tc + q, so the concrete supplies "
                                            "more of the attenuation and the lead sheet can be thinner."),
    cancelling=S246_C,
    scene_clause="A storage shed stands near the source, well to the side of the beam, and its roof is being renewed.",
    scene_object_rationale="The roof of a shed near the source is not between the source and the sheet of lead; a layer that is added to it "
                           "leaves the concrete wall, the lead and the required attenuation as stated.",
    scene_refs=("roof",), target_terms=("the concrete wall", "the wall", "the lead sheet"),
    pairs=(
        Pair("p0", "A further layer adds {value} {unit} to the thickness of {relation}.", "the concrete wall", "the shed roof", CO,
             "A layer that is added to the roof of the shed is not in the path of the beam; the concrete wall has the stated thickness.",
             ("narrow beam", "falls exponentially"), "a little",
             before_context_reason="The R sentence refers to 'the concrete wall' before the context introduces it."),
        Pair("p1", "{relation} {value} {unit} more concrete against the wall.", "For this shield, the builders lay",
             "For an earlier shield only, the builders laid", EVENT,
             "The layer was added in an earlier shield, which has been replaced; the wall of the shield of the question has the stated "
             "thickness.", ("narrow beam", "falls exponentially"), "a little"),
    ),
    notes="M250 phase 2: R is a further layer of concrete; C is the intensity of the unshielded beam (cancels in the required factor); no K (see NO_K).")

# --- S247 --------------------------------------------------------------------------------------------------------------------------

S247_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the energy of one photon of the beam", "energy", "eV", (2.1, 3.6, 4.1), "The photons of the beam {relation} {value} {unit}.",
        (P("c0", "have an energy of"), P("c1", "each carry an energy of")),
        "((((1 + Rf)*cos(theta)**2)*((I/q)*(q/c)))*A/m)*t",
        ("photon flux per area N = I / q, intensity over photon energy", "momentum of one photon = q / c",
         "momentum flux per area N q / c, times the factor (1 + Rf) cos^2(theta), is the pressure"),
        "((((1 + Rf)*cos(theta)**2)*(I/c))*A/m)*t*q", nonnumeric_fill="a known energy"),
    "standard", "That radiation pressure is the intensity over c, whatever the wavelength, is standard in the treatment of photon momentum but "
                "is not a headline fact.", (1.9, 2.6))

S247 = _spec(
    "S247", quantity_phrase="a second lamp", quantity_type="intensity", unit="W/m^2", values=(260.0, 470.0, 880.0),
    heldout_values=(210.0, 340.0),
    relevant=rv.RelevantWiring("I", "add", "A second lamp that adds q to the intensity of the light that reaches the mirror makes it I + q, and "
                                           "the force, the acceleration and the speed grow in proportion."),
    cancelling=S247_C,
    scene_clause="A projection screen hangs on a wall of the laboratory, lit by lamps that do not shine on the mirror.",
    scene_object_rationale="A projection screen on a wall is lit by its own lamp and is not the mirror; light that reaches the screen "
                           "does not reach the mirror, so the intensity at the mirror is the stated one.",
    scene_refs=("screen",), target_terms=("the mirror",),
    pairs=(
        Pair("p0", "A second lamp adds {value} {unit} to the intensity of the light that reaches {relation}.", "the mirror",
             "the projection screen", CO,
             "A second lamp that brightens the projection screen does not add light at the mirror; the intensity at the mirror is the "
             "stated one.", ("frictionless rail", "starts at rest"), "a little",
             before_context_reason="The R sentence refers to 'the mirror' before the context introduces it."),
        Pair("p1", "{relation} {value} {unit} more illumination onto the mirror.",
             "During this exposure, a second lamp gives", "During an earlier exposure only, a second lamp gave", EVENT,
             "The second lamp was used in an earlier exposure, which is over; in the exposure of the question the mirror receives only "
             "the stated beam.", ("frictionless rail", "starts at rest"), "a little"),
    ),
    notes="M250 phase 2: R is a second lamp that adds intensity at the mirror; C is the photon energy (cancels between photon flux and momentum "
          "per photon); no K (see NO_K).")

# --- S248 --------------------------------------------------------------------------------------------------------------------------

S248_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the angle between the spin and the field", "angle", "deg", (28.0, 43.0, 73.0),
        "The spin of the proton is {relation} {value} {unit} to the field.", (P("c0", "inclined at"), P("c1", "tilted at")),
        "(((gp*e/(2*mp))*B*sin(q))/sin(q))/(2*pi)",
        ("torque on the moment, mu B sin(q), with mu = (g e / 2 m) L", "component of the spin angular momentum perpendicular to the field, "
                                                                    "L sin(q)",
         "precession angular frequency = torque / perpendicular angular momentum"),
        "((gp*e/(2*mp))*B*sin(q))/(2*pi)", nonnumeric_fill="a known angle"),
    "standard", "That the Larmor frequency does not depend on the tilt of the spin follows from the torque equation but is not a headline fact.",
    (22.0, 32.0))

S248 = _spec(
    "S248", quantity_phrase="a second coil", quantity_type="magnetic_field", unit="mT", values=(44.0, 52.0, 60.0), heldout_values=(12.0, 25.0),
    relevant=rv.RelevantWiring("B", "add", "A second coil that adds q to the magnetic field at the sample makes the field B + q, and the precession "
                                           "frequency is proportional to the field."),
    cancelling=S248_C,
    scene_clause="A small compass lies on the bench outside the gap of the magnet.",
    scene_object_rationale="A compass on the bench beside the magnet is not at the sample; a coil that acts on its field changes the field at the "
                           "compass only, so the field at the sample is the stated one.",
    scene_refs=("compass",), target_terms=("the sample", "the proton"),
    pairs=(
        Pair("p0", "A second coil adds {value} {unit} to the magnetic field at {relation}.", "the sample", "the compass", CO,
             "A second coil that is placed at the compass adds field there and not at the sample; the field at the sample is the stated one.",
             ("free proton", "uniform, constant magnetic field"), "a little",
             before_context_reason="The R sentence refers to 'the sample' before the context introduces it."),
        Pair("p1", "{relation} {value} {unit} more field at the sample.", "During this measurement, a second coil gives",
             "During an earlier measurement only, a second coil gave", EVENT,
             "The second coil was used in an earlier measurement, which is over; in the measurement of the question the field at the "
             "sample is the stated one.", ("free proton", "uniform, constant magnetic field"), "a little"),
    ),
    notes="M250 phase 2: R is a second coil that adds field at the sample; C is the angle between the spin and the field (cancels in the "
          "precession frequency); no K (see NO_K).")

# --- S249 --------------------------------------------------------------------------------------------------------------------------

S249 = _spec(
    "S249", quantity_phrase="a further accelerating gap", quantity_type="energy", unit="MeV", values=(60.0, 75.0, 130.0), heldout_values=(35.0, 110.0),
    relevant=rv.RelevantWiring("K", "add", "A further accelerating gap that adds q to the kinetic energy of the protons before injection makes it K + q, "
                                           "which raises gamma and lowers the orbital frequency."),
    scene_clause="A second ion source feeds deuterons to another machine, which has its own magnet.",
    scene_object_rationale="A second ion source feeds its deuterons to another machine; they do not enter this magnetic field, so the energy of "
                           "the protons that do is the stated one.",
    scene_refs=("second ion source",), target_terms=("the protons", "a proton", "each proton"),
    pairs=(
        Pair("p0", "A further accelerating gap adds {value} {unit} to the kinetic energy of {relation}.", "the protons that enter this magnet",
             "the deuterons from the second ion source", CO,
             "An accelerating gap that acts on the deuterons of the second source does not act on the protons of the question, which keep "
             "the stated injection energy.", ("uniform, constant magnetic field", "neglect radiation"), "a little",
             before_context_reason="The R sentence refers to 'the protons' before the context introduces them."),
        Pair("p1", "{relation} {value} {unit} more kinetic energy to each proton before it enters the field.",
             "For this injection, a further accelerating gap gives", "For an earlier injection only, a further accelerating gap gave", EVENT,
             "The gap was used in an earlier injection, which is over; in the injection of the question the protons enter with the "
             "stated kinetic energy.", ("uniform, constant magnetic field", "neglect radiation"), "a little"),
    ),
    notes="M250 phase 2: R is a further accelerating gap before injection; no C and no K (see NO_C, NO_K).")

# --- S250 --------------------------------------------------------------------------------------------------------------------------

S250_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the distance of the film from the crystal", "length", "cm", (21.0, 43.0, 62.0), "The film {relation} {value} {unit} from the crystal.",
        (P("c0", "is placed"), P("c1", "stands")),
        "atan(q*tan(2*asin(lam/(2*d)))/q)/2",
        ("the reflected beam leaves at twice the glancing angle, 2 theta, to the incident beam", "radius of the diffraction ring on the film r = q tan(2 theta)",
         "glancing angle recovered from the ring theta = (1 / 2) atan(r / q)"),
        "atan(q*tan(2*asin(lam/(2*d))))/2", nonnumeric_fill="a known distance"),
    "uncommon", "That the angle recovered from a diffraction ring does not depend on how far the film is from the crystal is true by the "
                "construction of the ring radius, but it is rarely stated.", (37.0, 67.0))

S250 = _spec(
    "S250", quantity_phrase="a further accelerating stage", quantity_type="energy", unit="keV", values=(7.3, 8.4, 9.5), heldout_values=(2.1, 4.4),
    relevant=rv.RelevantWiring("K", "add", "A further accelerating stage that adds q to the kinetic energy of the electrons before they reach the crystal "
                                           "makes it K + q, which shortens the wavelength and lowers the Bragg angle."),
    cancelling=S250_C,
    scene_clause="A sputter gun that fires ions at samples to clean them stands beside the diffraction chamber, with its own vacuum line.",
    scene_object_rationale="The ions of a sputter gun beside the chamber travel in their own tube and do not reach the electron beam or the "
                           "crystal, so the energy of the electrons and the angle of the reflection are those of the stated gun.",
    scene_refs=("sputter gun",), target_terms=("the electrons", "an electron"),
    pairs=(
        Pair("p0", "A further accelerating stage adds {value} {unit} to the kinetic energy of {relation} before they reach their targets.",
             "the electrons from the gun", "the ions of the sputter gun", CO,
             "An accelerating stage in the sputter gun changes the energy of its ions only; the electrons that are diffracted keep "
             "the stated gun energy.", ("relativistic momentum", "first-order Bragg reflection"), "a little",
             before_context_reason="The R sentence refers to 'the electrons' before the context introduces them."),
        Pair("p1", "{relation} {value} {unit} more kinetic energy to each electron before it reaches the crystal.",
             "For this exposure, a further accelerating stage gives", "For an earlier exposure only, a further accelerating stage gave", EVENT,
             "The stage was used in an earlier exposure, which is over; in the exposure of the question the electrons have the stated "
             "gun energy.", ("relativistic momentum", "first-order Bragg reflection"), "a little"),
    ),
    notes="M250 phase 2: R is a further accelerating stage; C is the distance of the film (cancels in the angle read from the ring); no K (see NO_K).")


SPECS: dict[str, r2.RoleSpecV2] = {s.structure_id: s for s in (S241, S242, S243, S244, S245, S246, S247, S248, S249, S250)}
ROLE_SPECS = SPECS

STRUCTURE_FACTORIES = {f().structure_id: f for f in lm.ALL}

INFEASIBLE: dict[str, str] = {}

NO_C: dict[str, str] = {
    "S241": "The saturated photocurrent depends on the power, the wavelength and the efficiency; the anode voltage does not enter any "
            "relation (it only has to be high enough), so no free quantity enters an intermediate relation and then leaves it.",
    "S243": "The closest approach follows from the energy, the charge number and the angle; a further quantity such as the foil thickness or the "
            "impact parameter is either fixed by the angle or does not enter, so nothing enters and cancels.",
    "S244": "The two photon energies follow from the energy and momentum balance; the mass of the electron is a stated constant and no further "
            "free quantity enters and cancels.",
    "S249": "A speed or an orbit radius would enter the intermediate relations and cancel, but both are fixed by the stated kinetic energy and "
            "field, so a stated value would contradict the problem; the frequency has no other free quantity.",
}

NO_K: dict[str, str] = {
    "S242": "A dead time or a counting limit of the counter would be an equipment rating, and a regime between the isotopes (one feeding "
            "the other) is excluded by the base text; no free quantity with a definite out-of-regime answer remains.",
    "S244": "The only regime conditions (a free electron at rest, a positron far above the binding energy of the electron) are approached "
            "gradually and have no exact threshold quantity; positronium formation would not give the stated two collinear photons.",
    "S246": "The attenuation coefficients are inputs for the stated photon energy; a photon-energy threshold (the K edge of lead, pair "
            "production) would change the coefficients, which are given, and not a further quantity with a definite answer.",
    "S247": "A threshold such as the damage intensity of the mirror would be an equipment rating, and the speed condition (far below c) is "
            "approached gradually, so no exact threshold quantity with a definite out-of-regime answer exists.",
    "S248": "The regime conditions (a free proton, a field that is uniform) are approached gradually; a chemical shift or a field gradient has "
            "no definite out-of-regime answer for the frequency.",
    "S249": "A pole radius that must exceed the orbit radius would be an equipment condition, and the orbit radius is fixed by the stated "
            "energy and field; no threshold of the physics itself is left.",
    "S250": "Bragg's law needs the wavelength to be below twice the spacing, but that is a property of two inputs, not of a further quantity; "
            "a different spacing would be a different structure.",
}

# The kind of regime that each K quantity expresses (a condition of the physics itself, not an equipment rating).
K_KINDS: dict[str, str] = {
    "S241": "below/above threshold frequency (photon energy above the work function)",
    "S243": "Coulomb-only regime (closest approach outside the nuclear radius)",
    "S245": "resonance condition (Doppler shift of the atoms within the swept frequency range)",
}


def structure(structure_id: str) -> gr.Structure:
    """The new structure with the spec's scene clause appended to its base context."""

    return r2.with_scene(STRUCTURE_FACTORIES[structure_id](), SPECS[structure_id].scene_clause)


# What the H4 trace extractor (`TraceContext.target_phrases` / `target_symbols`) must read as a statement of the target.
TARGET_TERMS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "S241": (("current flows through the photocell", "current through the photocell", "current"), ("I", "I_ph")),
    "S242": (("equal count rates", "how long", "time"), ("t", "t_eq")),
    "S243": (("smallest distance", "distance of closest approach", "distance"), ("d", "r_min")),
    "S244": (("energy of the photon that travels forward", "energy of the forward photon", "energy"), ("Ef", "E_f", "E_forward")),
    "S245": (("how many photons", "number of photons"), ("N", "N_ph")),
    "S246": (("how thick must the lead sheet be", "thickness of the lead sheet", "thickness"), ("tpb", "t_Pb", "t_pb")),
    "S247": (("speed does the mirror reach", "speed of the mirror", "speed"), ("v", "v_m")),
    "S248": (("frequency does the spin of the proton precess", "precession frequency", "frequency"), ("f", "f_L", "ν")),
    "S249": (("frequency does a proton go round its orbit", "orbital frequency", "frequency"), ("f", "f_c")),
    "S250": (("glancing angle", "first-order reflection"), ("theta", "θ", "theta_B")),
}
