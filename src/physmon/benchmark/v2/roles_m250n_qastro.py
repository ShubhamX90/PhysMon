"""M250 phase 2, batch qastro: v2.1 role-by-value specifications for the new structures S273 to S282 (plan revision v2.2, section G;
the eight wording rules of the LLM-panel reviews J15.1-038/039/046; admission standard 3.2, 6.1, 6.2, 6.3).

Every spec follows `roles_m0v21` (the v2.1 design) on instance 0 of the new structure:

* one R/D quantity with three study values and two held-out values, always an extra amount that is added to a stated input and that the
  base text can accommodate without contradiction (rule 2); a co-present D (pair 0, `other_object_same_scene`) whose object is of a
  different type from the target object, is introduced by a number-free scene clause that states only physical facts, in the base context of
  every cell, and receives an ordinary, purposeful action (rules 3 and 4), and a same-object D (pair 1, `same_object_other_event`: history in
  an earlier run, never a change applied and then reversed) whose R twin names the moment of the question ("Before the position is
  measured": rules 1 and 5), with "only" whenever the event adds something (rule 7); the same frame, numeral and unit within a pair, an
  attachment-only difference, word counts within three, marker- and consequence-free wording, value hygiene;
* a C quantity where the physics supports a real cancellation (S276, S277, S280, S281);
* a K quantity where a genuine regime condition of the physics itself exists (S273: point-nucleus regime; S274: weak-field regime;
  S276: thermal energy small against the barrier; S280: impulsive-burn regime); the kind of regime is recorded in `K_KINDS`. K_out is
  recorded as infeasible with the reason in every case.

`INFEASIBLE` holds the structures that cannot honestly carry the design (none in this batch); `NO_C` and `NO_K` hold the reason a
structure has no C or K quantity, so that an absence is a judgement on record and not an omission.
"""

from __future__ import annotations

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import lib_m250_qastro as lq
from physmon.benchmark.v2 import rolevalue as rv
from physmon.benchmark.v2 import rolevalue_v2 as r2

P = rv.Phrasing
Pair = r2.PhrasePair
CO = r2.D_KIND_CO_PRESENT
EVENT = r2.D_KIND_OTHER_EVENT
V21 = r2.VERSION_V21
CERT_VERSION = "v2.1"


def _spec(sid: str, **fields) -> r2.RoleSpecV2:
    return r2.RoleSpecV2(structure_id=sid, version=V21, author="agent (M250 phase 2, qastro)", **fields)


def _ko(reason: str) -> r2.KOut:
    return r2.KOut(False, reason)


# --- S273 --------------------------------------------------------------------------------------------------------------------------

S273_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the radius of the nucleus", "length", "fm", (1.9, 2.1, 2.5), "The radius of the nucleus {relation} {value} {unit}.",
        (P("k0", "is"), P("k1", "has been measured as")),
        "10*q < r", "hc/(K + Z*ke2/(2*q))", 600.0, nonnumeric_fill="a known value"),
    _ko("A nucleus whose radius is comparable with the orbit radius would not be a point charge for the muon, which would then feel a force that "
        "is not the inverse-square attraction, and the stated premise that the only force is the electrostatic attraction would be contradicted; "
        "the Bohr levels used in the question would not exist."),
    (1.7, 2.3))

S273 = _spec(
    "S273", quantity_phrase="a further accelerating gap", quantity_type="energy", unit="eV", values=(48.0, 116.0, 240.0),
    heldout_values=(68.0, 210.0),
    relevant=rv.RelevantWiring("K", "add", "A further accelerating gap that adds q to the kinetic energy of the muon before the capture makes it K + q, "
                                           "and the photon carries the larger energy K + q + Eb, so its wavelength is shorter."),
    conditional=S273_K,
    scene_clause="A second apparatus with an electron beam and a vacuum line of its own stands beside the capture chamber.",
    scene_object_rationale="The electrons of an apparatus beside the capture chamber travel in a vacuum line of their own and do not reach the muon or the "
                           "nucleus, so the kinetic energy of the muon and the photon of the capture are those of the stated muon.",
    scene_refs=("electron beam",), target_terms=("the muon", "the nucleus", "the capture", "the photon"),
    pairs=(
        Pair("p0", "A further accelerating gap adds {value} {unit} to the kinetic energy of {relation}.", "the muon",
             "the electron beam", CO,
             "An accelerating gap in the second apparatus changes the energy of its electrons only; the muon that is captured keeps the "
             "stated kinetic energy relative to the nucleus.", ("directly into the Bohr level", "single photon"), "a little",
             before_context_reason="The R sentence refers to 'the muon' before the context introduces it."),
        Pair("p1", "{relation} {value} {unit} more kinetic energy to the muon before the capture.",
             "For this capture, a further accelerating gap gives", "For an earlier capture only, a further accelerating gap gave", EVENT,
             "The gap was used for an earlier capture, which is over; in the capture of the question the muon has the stated kinetic energy "
             "relative to the nucleus.", ("directly into the Bohr level", "single photon"), "a little"),
    ),
    notes="M250 phase 2: R is a further accelerating gap before the capture; K is the radius of the nucleus (point-nucleus regime); no C (see NO_C).")

# --- S274 --------------------------------------------------------------------------------------------------------------------------

S274_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the fine-structure splitting of the P level", "energy", "eV", (0.0018, 0.0036, 0.004),
        "The fine-structure splitting of the P level {relation} {value} {unit}.", (P("k0", "is"), P("k1", "has been measured as")),
        "10*dE < q", "lam**2*2*Eb/hc", 0.00001, nonnumeric_fill="a known value"),
    _ko("In a field whose Zeeman energy is comparable with the fine-structure splitting the levels no longer shift in proportion to the field and the "
        "pattern of components is that of the intermediate or the Paschen-Back regime; the premise of the question, that every level splits in "
        "proportion to the field, would be contradicted and no certified answer exists."),
    (0.0024, 0.0029))

S274 = _spec(
    "S274", quantity_phrase="a second coil", quantity_type="magnetic_field", unit="mT", values=(36.0, 55.0, 83.0), heldout_values=(47.0, 66.0),
    relevant=rv.RelevantWiring("B", "add", "A second coil that adds q to the magnetic field at the vapour makes the field B + q, and the separation of "
                                           "the components is proportional to the field."),
    conditional=S274_K,
    scene_clause="A small compass lies on the bench outside the gap of the magnet.",
    scene_object_rationale="A compass on the bench beside the magnet is not at the vapour; a coil that acts on its field changes the field at the "
                           "compass only, so the field at the vapour is the stated one.",
    scene_refs=("compass",), target_terms=("the vapour", "the atoms", "the line", "the field"),
    pairs=(
        Pair("p0", "A second coil adds {value} {unit} to the magnetic field at {relation}.", "the vapour", "the compass", CO,
             "A second coil that is placed at the compass adds field there and not at the vapour; the field at the vapour is the stated one.",
             ("uniform magnetic field", "all six components"), "a little",
             before_context_reason="The R sentence refers to 'the vapour' before the context introduces it."),
        Pair("p1", "{relation} {value} {unit} more field at the vapour.", "During this measurement, a second coil gives",
             "During an earlier measurement only, a second coil gave", EVENT,
             "The second coil was used in an earlier measurement, which is over; in the measurement of the question the field at the vapour is "
             "the stated one.", ("uniform magnetic field", "all six components"), "a little"),
    ),
    notes="M250 phase 2: R is a second coil that adds field at the vapour; K is the fine-structure splitting of the P level (weak-field regime); no C "
          "(see NO_C).")

# --- S275 --------------------------------------------------------------------------------------------------------------------------

S275 = _spec(
    "S275", quantity_phrase="a further strip", quantity_type="length", unit="nm", values=(0.16, 0.24, 0.56), heldout_values=(0.18, 0.4),
    relevant=rv.RelevantWiring("w", "add", "A further strip that adds q to the width of the slice makes the width w + q, and the probability is the "
                                           "integral of the density over the wider slice."),
    scene_clause="A second chip, which is being given a metal coating, lies on a stage beside the apparatus.",
    scene_object_rationale="A coating on a second chip beside the apparatus is not part of the well or of the probe, so the width of the slice in which "
                           "the probe responds is the stated one.",
    scene_refs=("second chip",), target_terms=("the slice", "the probe", "the electron", "the well"),
    pairs=(
        Pair("p0", "{relation} is widened by {value} {unit} more.", "The slice in which the probe responds",
             "The coating on the second chip", CO,
             "A width that is added to the coating of the second chip does not change the probe or the well; the slice in which the probe responds "
             "has the stated width.", ("infinite square well", "impenetrable walls"), "a little",
             before_context_reason="The R sentence refers to 'the slice' and 'the probe' before the context introduces them."),
        Pair("p1", "{relation} {value} {unit} more at its right-hand edge.",
             "Before the position is measured, the slice in which the probe responds is widened by",
             "In an earlier measurement only, the slice in which the probe responded was widened by", EVENT,
             "The slice was widened in an earlier measurement, which is over; in the measurement of the question the probe responds in the slice "
             "of the stated width.", ("infinite square well", "impenetrable walls"), "a little"),
    ),
    notes="M250 phase 2: R is a further strip that widens the slice; no C and no K (see NO_C, NO_K).")

# --- S276 --------------------------------------------------------------------------------------------------------------------------

S276_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the incident current of each beam", "current", "nA", (1.8, 5.2, 9.2), "The incident current of each beam {relation} {value} {unit}.",
        (P("c0", "is"), P("c1", "has been set to")),
        "(q*exp(-2*a*sqrt(2*mp*V)/hbar))/(q*exp(-2*a*sqrt(2*md*V)/hbar))",
        ("transmitted proton current I_p = q exp(-2 kp a)", "transmitted deuteron current I_d = q exp(-2 kd a)", "ratio of the transmitted currents "
                                                                                                                  "I_p / I_d"),
        "q*exp(-2*a*sqrt(2*mp*V)/hbar)", nonnumeric_fill="a known value"),
    "standard", "That the ratio of two transmitted currents does not depend on the incident current of the beams follows from the definition of the "
                "transmission but is not stated as a fact.", (6.1, 7.2))

S276_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the mean thermal energy of the particles", "energy", "eV", (0.015, 0.028, 0.032),
        "The mean thermal energy of the particles {relation} {value} {unit}.", (P("k0", "is"), P("k1", "is measured as")),
        "8*q < V", "sqrt(md/mp)", 0.2, nonnumeric_fill="a known value"),
    _ko("A thermal energy comparable with the height of the barrier would let particles cross above the barrier, and the premise of the question, that "
        "they cross only by tunnelling, would be contradicted; the exponential transmission would no longer give the transmitted current."),
    (0.017, 0.024))

S276 = _spec(
    "S276", quantity_phrase="a further bias", quantity_type="energy", unit="eV", values=(0.07, 0.15, 0.23), heldout_values=(0.09, 0.11),
    relevant=rv.RelevantWiring("V", "add", "A further bias that adds q to the height of the barrier makes it V + q, and both decay constants grow in "
                                           "proportion to the square root of the height."),
    cancelling=S276_C, conditional=S276_K,
    scene_clause="A guard electrode, held at its own potential, lies beside the barrier region.",
    scene_object_rationale="A guard electrode beside the barrier region is not the barrier; a bias that changes its potential step does not change the "
                           "height of the barrier, so the height above the kinetic energy of the particles is the stated one.",
    scene_refs=("guard electrode",), target_terms=("the barrier", "the particles", "protons", "deuterons"),
    pairs=(
        Pair("p0", "A further bias adds {value} {unit} to the height of {relation}.", "the barrier that the beams strike", "the step at the guard electrode", CO,
             "A bias that is applied to the guard electrode changes the potential step there and not the height of the barrier that the particles "
             "meet; the barrier has the stated height.", ("cross the barrier only by tunnelling", "equal numbers of particles"), "a little",
             before_context_reason="The R sentence refers to 'the barrier' before the context introduces it."),
        Pair("p1", "{relation} {value} {unit} to the height of the barrier.", "During this run, a further bias adds",
             "During an earlier run only, a further bias added", EVENT,
             "The bias was applied in an earlier run, which is over; in the run of the question the barrier has the stated height above the "
             "kinetic energy of the particles.", ("cross the barrier only by tunnelling", "equal numbers of particles"), "a little"),
    ),
    notes="M250 phase 2: R is a further bias on the barrier; C is the incident current of each beam (cancels in the ratio of the transmitted currents); "
          "K is the thermal energy of the particles (tunnelling regime).")

# --- S277 --------------------------------------------------------------------------------------------------------------------------

S277_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the number of pions that each spill sends into the tube", "dimensionless", "1", (1100.0, 2700.0, 7900.0),
        "Each spill {relation} {value} pions into the tube.", (P("c0", "sends"), P("c1", "delivers")),
        "(q*exp(-Lp*mc2/(pc*c*tau0)))/q",
        ("number of pions that reach the end of the tube N = q exp(-Lp / Ld)", "fraction that survive = N / q"),
        "q*exp(-Lp*mc2/(pc*c*tau0))", nonnumeric_fill="a known number"),
    "standard", "That the surviving fraction does not depend on how many pions are sent follows from the definition of a fraction but is not stated "
                "as a fact.", (3300.0, 4700.0))

S277 = _spec(
    "S277", quantity_phrase="a further length of pipe", quantity_type="length", unit="m", values=(16.0, 34.0, 51.0), heldout_values=(18.0, 44.0),
    relevant=rv.RelevantWiring("Lp", "add", "A further length of pipe that adds q to the flight path makes it Lp + q, and the surviving fraction is "
                                            "exp(-(Lp + q) / Ld)."),
    cancelling=S277_C,
    scene_clause="A cooling-water line runs along the outside of the tube.",
    scene_object_rationale="A cooling-water line along the outside of the tube is not part of the flight path of the pions; pipe that is added to "
                           "it leaves the length of the tube that the pions fly through as stated.",
    scene_refs=("cooling-water line",), target_terms=("the flight path", "the tube", "the pions", "pion"),
    pairs=(
        Pair("p0", "{relation} gets {value} {unit} more pipe.", "The flight path of the pions", "The cooling-water line", CO,
             "Pipe that is added to the cooling-water line carries water and not pions; the tube through which the pions fly has the stated "
             "length.", ("evacuated tube", "constant speed"), "a little",
             before_context_reason="The R sentence refers to 'the flight path' and 'the pions' before the context introduces them."),
        Pair("p1", "{relation} {value} {unit} more, at the downstream end.", "Before the pions are counted, the flight path is lengthened by",
             "For an earlier run only, the flight path was lengthened by", EVENT,
             "The flight path was lengthened in an earlier run, which is over; in the run of the question the pions fly through a tube of the "
             "stated length.", ("evacuated tube", "constant speed"), "a little"),
    ),
    notes="M250 phase 2: R is a further length of pipe in the flight path; C is the number of pions that each spill sends (cancels in the surviving "
          "fraction); no K (see NO_K).")

# --- S278 --------------------------------------------------------------------------------------------------------------------------

S278 = _spec(
    "S278", quantity_phrase="a further final particle", quantity_type="energy", unit="MeV", values=(47.0, 104.0, 184.0), heldout_values=(82.0, 148.0),
    relevant=rv.RelevantWiring("Q", "add", "A further final particle that carries q of rest energy adds q to the excess of the final rest energy, which "
                                           "becomes Q + q."),
    scene_clause="A second target station, with its own beam line, stands in the same hall.",
    scene_object_rationale="A second target station with its own beam line has its own beam and target; a particle that is created there is not "
                           "among the final particles of the reaction of the question, so the excess of rest energy is the stated one.",
    scene_refs=("second target station",), target_terms=("the reaction", "this reaction", "the beam particle", "the target particle"),
    pairs=(
        Pair("p0", "{relation} gets {value} {unit} more.", "The rest energy of the final particles",
             "The beam energy of the second target station", CO,
             "A particle that is created at the second target station is not a final particle of the reaction of the question; the final "
             "particles of that reaction have the stated excess of rest energy.", ("reaction runs at its threshold", "exceeds the total rest energy"),
             "a little",
             before_context_reason="The R sentence refers to 'the reaction' before the context introduces it."),
        Pair("p1", "{relation} {value} {unit} more rest energy.", "In this reaction, the final particles carry",
             "In an earlier reaction only, the final particles carried", EVENT,
             "The further particle was created in an earlier reaction, which is over; the final particles of the reaction of the question have "
             "the stated excess of rest energy.", ("reaction runs at its threshold", "exceeds the total rest energy"), "a little"),
    ),
    notes="M250 phase 2: R is a further final particle that adds rest energy; no C and no K (see NO_C, NO_K).")

# --- S279 --------------------------------------------------------------------------------------------------------------------------

S279 = _spec(
    "S279", quantity_phrase="a further ring", quantity_type="length", unit="cm", values=(1.9, 3.7, 5.6), heldout_values=(2.2, 4.6),
    relevant=rv.RelevantWiring("R", "add", "A further ring that adds q to the radius of the rotor makes the radius R + q, and the speed of the source and "
                                           "the shift grow in proportion to the radius and to its square."),
    scene_clause="A belt-driven vacuum pump stands beside the rotor housing.",
    scene_object_rationale="A pulley of a vacuum pump beside the rotor housing is not part of the rotor that carries the source; a ring that is added to "
                           "it leaves the radius of the circle on which the source moves as stated.",
    scene_refs=("vacuum pump",), target_terms=("the rotor", "the source", "the absorber", "the gamma rays"),
    pairs=(
        Pair("p0", "The radius of {relation} gets {value} {unit} more.", "the rotor that carries the source",
             "the pulley of the vacuum pump", CO,
             "A ring that is added to the pulley of the vacuum pump changes the pump and not the rotor; the source moves on a circle of the "
             "stated radius.", ("constant rotation frequency", "straight line in the laboratory"), "a little",
             before_context_reason="The R sentence refers to 'the rotor' and 'the source' before the context introduces them."),
        Pair("p1", "{relation} {value} {unit} more in rim radius, at the same rotation frequency.", "Before the shift is measured, the rotor that carries the source has grown by",
             "For an earlier run only, the rotor that carried the source had grown by", EVENT,
             "The rotor was made larger for an earlier run, which is over; in the run of the question the source moves on a circle of the stated "
             "radius.", ("constant rotation frequency", "straight line in the laboratory"), "a little"),
    ),
    notes="M250 phase 2: R is a further ring that enlarges the rotor; no C and no K (see NO_C, NO_K).")

# --- S280 --------------------------------------------------------------------------------------------------------------------------

S280_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the mass of the spacecraft", "mass", "kg", (850.0, 1400.0, 2300.0), "The spacecraft {relation} {value} {unit}.",
        (P("c0", "has a mass of"), P("c1", "has been weighed at")),
        "(q*(Rp*sqrt(g0/(Rp + h1))*(sqrt(2*(Rp + h2)/(2*Rp + h1 + h2)) - 1)) + q*(Rp*sqrt(g0/(Rp + h2))*(1 - sqrt(2*(Rp + h1)/(2*Rp + h1 + h2)))))/q",
        ("impulse of the first burn J1 = q (vp - v1)", "impulse of the second burn J2 = q (v2 - va)", "total change of speed = (J1 + J2) / q"),
        "(q*(Rp*sqrt(g0/(Rp + h1))*(sqrt(2*(Rp + h2)/(2*Rp + h1 + h2)) - 1)))/q", nonnumeric_fill="a known mass"),
    "standard", "That the change of speed of a burn does not depend on the mass of the spacecraft, which only changes the impulse and the propellant, is "
                "taught in rocket dynamics but is not a headline fact.", (1100.0, 1900.0))

S280_K = r2.ConditionalV2(
    rv.ConditionalSpec(
        "the duration of each burn", "time", "min", (2.0, 3.0, 4.5), "Each engine burn {relation} {value} {unit}.",
        (P("k0", "lasts"), P("k1", "takes")),
        "10*q*v1 < 2*pi*r1", "dv + v1**2/r1*q", 40.0, nonnumeric_fill="a known time"),
    _ko("A burn whose duration is a sizeable part of the orbital period cannot be treated as an instantaneous change of speed: the spacecraft moves "
        "through a large angle during the burn and gravity acts on it all the while, and the premise of the question that each burn is instantaneous "
        "would be contradicted; no certified answer exists."),
    (2.6, 3.8))

S280 = _spec(
    "S280", quantity_phrase="a further altitude", quantity_type="length", unit="km", values=(350.0, 470.0, 590.0), heldout_values=(400.0, 520.0),
    relevant=rv.RelevantWiring("h1", "add", "A further altitude that adds q to the altitude of the initial orbit makes it h1 + q, and the radius and the "
                                            "speed of that orbit, and so the speed changes of the burns, change."),
    cancelling=S280_C, conditional=S280_K,
    scene_clause="A relay satellite circles the planet in a polar orbit that never meets the transfer ellipse.",
    scene_object_rationale="A relay satellite in a polar orbit has its own orbit and does not meet the transfer ellipse; a change of its altitude does "
                           "not change the initial or the final orbit of the spacecraft, so the speed changes of the burns are the stated ones.",
    scene_refs=("relay satellite",), target_terms=("the initial circular orbit", "the initial orbit", "the final orbit", "the spacecraft", "the burns"),
    pairs=(
        Pair("p0", "The altitude of {relation} gets {value} {unit} more.", "the initial circular orbit", "the orbit of the relay satellite",
             CO,
             "A change of the altitude of the orbit of the relay satellite does not change the initial circular orbit of the spacecraft or the "
             "transfer; the speed changes of the burns are those of the stated orbits.", ("in the same plane", "instantaneous change of speed"),
             "a little",
             before_context_reason="The R sentence refers to 'the initial circular orbit' before the context introduces it."),
        Pair("p1", "{relation} {value} {unit} higher still.", "Before the first burn, the initial circular orbit is placed",
             "For an earlier flight only, the initial circular orbit was placed", EVENT,
             "The initial orbit was placed higher for an earlier flight, which is over; in the flight of the question the spacecraft starts "
             "from the orbit of the stated altitude.", ("in the same plane", "instantaneous change of speed"), "a little"),
    ),
    notes="M250 phase 2: R is a further altitude of the initial orbit; C is the mass of the spacecraft (cancels in the change of speed); K is the duration "
          "of each burn (impulsive-burn regime).")

# --- S281 --------------------------------------------------------------------------------------------------------------------------

S281_C = r2.CancellingV2(
    rv.CancellingSpec(
        "the mass of the probe", "mass", "kg", (1690.0, 2270.0, 3000.0), "The probe {relation} {value} {unit}.",
        (P("c0", "has a mass of"), P("c1", "is built with a mass of")),
        "sqrt(2*(q*(ve*(R/RE)*sqrt(rho/rhoE))**2/2)/q)",
        ("kinetic energy that the probe needs at launch E = q v_esc^2 / 2", "speed from the energy v = sqrt(2 E / q)"),
        "sqrt((q*(ve*(R/RE)*sqrt(rho/rhoE))**2/2)/q)", nonnumeric_fill="a known mass"),
    "famous", "That the escape speed does not depend on the mass of the escaping body is a well-known fact of gravitation.", (1980.0, 2600.0))

S281 = _spec(
    "S281", quantity_phrase="a further layer of rock", quantity_type="length", unit="km", values=(120.0, 310.0, 470.0), heldout_values=(230.0, 260.0),
    relevant=rv.RelevantWiring("R", "add", "A further layer of rock of the same density that adds q to the radius of the planet makes the radius R + q "
                                           "with the density unchanged, and the escape speed is proportional to the radius."),
    cancelling=S281_C,
    scene_clause="A small moon circles the planet.",
    scene_object_rationale="A small moon that circles the planet is a different body from the planet; a layer of rock that is added to its radius "
                           "leaves the radius and the density of the planet, and so the escape speed from its surface, as stated.",
    scene_refs=("moon",), target_terms=("the planet", "the probe", "the surface"),
    pairs=(
        Pair("p0", "A further layer of rock of the same density adds {value} {unit} to the radius of {relation}.", "the planet", "the moon", CO,
             "A layer of rock that is added to the moon changes the moon and not the planet; the planet keeps its stated radius and density.",
             ("uniform sphere", "does not rotate"), "a little",
             before_context_reason="The R sentence refers to 'the planet' before the context introduces it."),
        Pair("p1", "{relation} {value} {unit} more radius from rock of the same density.",
             "Before the launch speed is found, the planet is given",
             "For an earlier simulation only, the planet was given", EVENT,
             "The layer was part of an earlier simulation, which is over; in the problem of the question the planet is a uniform sphere of the "
             "stated radius and density.", ("uniform sphere", "does not rotate"), "a little"),
    ),
    notes="M250 phase 2: R is a further layer of rock of the same density; C is the mass of the probe (cancels in the escape speed); no K (see NO_K).")

# --- S282 --------------------------------------------------------------------------------------------------------------------------

S282 = _spec(
    "S282", quantity_phrase="a further expansion", quantity_type="dimensionless", unit="1", values=(0.33, 0.74, 1.24), heldout_values=(0.37, 1.03),
    relevant=rv.RelevantWiring("R", "add", "A further expansion that adds q solar radii to the radius of the star makes it R + q, and the luminosity is "
                                           "proportional to the square of the radius at the stated peak wavelength."),
    scene_clause="A dust disc circles the star well outside its surface.",
    scene_object_rationale="A dust disc that circles the star outside its surface is not part of the radiating surface; a change of its rim "
                           "leaves the radius of the star and its luminosity as stated.",
    scene_refs=("dust disc",), target_terms=("the star", "the Sun", "the peak", "the surface"),
    pairs=(
        Pair("p0", "The radius of {relation} gets {value} more, in solar radii.", "the radiating star", "the dust disc rim", CO,
             "A radius that is added to the rim of the dust disc moves the rim of the disc and not the surface of the star; the star "
             "keeps its stated radius.", ("black body", "inversely proportional to its surface temperature"), "a little",
             before_context_reason="The R sentence refers to 'the star' before the context introduces it."),
        Pair("p1", "{relation} {value} more, in solar radii, at the same peak wavelength.",
             "Before the luminosity is evaluated, the star has swollen by",
             "For an earlier observation only, the star had swollen by", EVENT,
             "The star was larger during an earlier observation, which is over; in the observation of the question the star has its stated "
             "radius and peak wavelength.", ("black body", "inversely proportional to its surface temperature"), "a little"),
    ),
    notes="M250 phase 2: R is a further expansion of the star at the same peak wavelength; no C and no K (see NO_C, NO_K).")


SPECS: dict[str, r2.RoleSpecV2] = {s.structure_id: s for s in (S273, S274, S275, S276, S277, S278, S279, S280, S281, S282)}
ROLE_SPECS = SPECS

STRUCTURE_FACTORIES = {f().structure_id: f for f in lq.ALL}

INFEASIBLE: dict[str, str] = {}

NO_C: dict[str, str] = {
    "S273": "The photon energy is the sum of the kinetic and the binding energy and the wavelength follows from it; the masses are stated inputs "
            "that do not cancel, and no further free quantity enters an intermediate relation and then leaves it.",
    "S274": "The separation depends on the field, the wavelength and the g-factors; the observation angle and the number of atoms do not enter any "
            "relation of the energy separation, so no free quantity enters an intermediate relation and then leaves it.",
    "S275": "The probability depends on the state and on the edges of the slice; the mass of the particle and its energy would cancel from the "
            "wavefunction, but both need constants that are not in the graph, so no honest cancelling quantity can be written for the certified expression.",
    "S278": "The threshold follows from the invariant mass of the three stated rest energies; the speed of the centre of mass is fixed by them and "
            "no free quantity enters an intermediate relation and then leaves it.",
    "S279": "The shift follows from the speed of the source and the photon energy; the mass of the source or the phase of the rotor would not enter "
            "any relation, so no free quantity enters an intermediate relation and then leaves it.",
    "S282": "The luminosity follows from the peak wavelength and the radius; the distance of the star and the emissivity do not enter, and a "
            "quantity that enters the area and the temperature would not cancel.",
}

NO_K: dict[str, str] = {
    "S275": "The infinite-well model needs a wall height that is large against the energy of the state, but that energy needs the mass and Planck's "
            "constant, which are not in the graph; a wall-height quantity cannot be tied to the certified expression.",
    "S277": "The regime conditions (a constant momentum, no absorption in the tube) are stated premises without a threshold quantity; a gas pressure "
            "in the tube would give an absorption length, which is an equipment condition and not a regime of the physics of the decay.",
    "S278": "A binding of the target proton in a nucleus (a Fermi momentum) would change the kinematics, but it enters as a distribution and not as a "
            "threshold quantity with a definite out-of-regime answer.",
    "S279": "The leading-order condition (v much less than c) is fixed by the stated rotation frequency and radius, so it is approached gradually "
            "and has no free threshold quantity.",
    "S281": "The uniform-sphere model and the neglect of rotation and atmosphere are premises that are approached gradually; a rotation rate or "
            "an atmosphere would change the answer smoothly and has no definite out-of-regime law.",
    "S282": "The black-body condition is approached gradually (an emissivity or a spectral type); no free quantity has a threshold with a definite "
            "out-of-regime answer.",
}

# The kind of regime that each K quantity expresses (a condition of the physics itself, not an equipment rating).
K_KINDS: dict[str, str] = {
    "S273": "point-nucleus regime (orbit radius much larger than the nuclear radius, so the attraction is purely Coulomb)",
    "S274": "weak-field (Zeeman) regime: Zeeman energy much smaller than the fine-structure splitting, versus Paschen-Back",
    "S276": "tunnelling versus thermal activation (thermal energy much smaller than the barrier height)",
    "S280": "impulsive-burn regime (burn duration much shorter than the orbital period, so the burn is an instantaneous change of speed)",
}


def structure(structure_id: str) -> gr.Structure:
    """The new structure with the spec's scene clause appended to its base context."""

    return r2.with_scene(STRUCTURE_FACTORIES[structure_id](), SPECS[structure_id].scene_clause)


# What the H4 trace extractor (`TraceContext.target_phrases` / `target_symbols`) must read as a statement of the target.
TARGET_TERMS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "S273": (("wavelength of the emitted photon", "wavelength"), ("lam", "λ", "lambda")),
    "S274": (("difference between the wavelengths", "outermost components"), ("dlam", "Δλ", "d_lambda")),
    "S275": (("probability that the probe finds the electron", "probability"), ("P", "P_slice")),
    "S276": (("ratio of the transmitted proton current", "ratio"), ("ratio", "R_T", "T_p/T_d")),
    "S277": (("fraction of the pions", "fraction"), ("F", "f_s")),
    "S278": (("smallest kinetic energy", "kinetic energy"), ("K", "K_th", "T_th")),
    "S279": (("frequency of the gamma rays at the absorber", "below their frequency"), ("df", "Δf", "d_f")),
    "S280": (("total change of speed", "change of speed"), ("dv", "Δv", "delta_v")),
    "S281": (("speed must the probe have", "launch to escape", "speed"), ("vesc", "v_esc", "v_e")),
    "S282": (("times the luminosity of the Sun", "luminosity"), ("L", "L_star")),
}
