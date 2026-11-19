"""M250 phase 1, batch d: October structures S73-S95 (quantum, modern physics, fluids) in the role-by-value design of M0 v2.1.

Authority: plan revision v2.2 (`docs/registry/v2/g1/plan_revision_v2.2_2026-11-14.md`, sections A, G), the dataset admission standard
(sections 2-3), and `roles_m0v21` / `rolevalue_v2` (the certifier). Every spec is a `RoleSpecV2` with `version="v2.1"`, instance 0:

* one R/D quantity q with three study values and two held-out values, wired into one input of the October graph;
* pair p0: D puts q on a second object of the same scene that the number-free `scene_clause` (appended to the base context of every
  cell of the structure) introduces; pair p1: D is a genuine other event of the target object that leaves no state behind (history in
  an earlier experiment, or an event after the stated process). A change applied to the target and then reversed is never used;
* C and K quantities only where the physics honestly supports them; a structure with no honest R/D quantity is listed in
  `INFEASIBLE` with the reason instead of a spec.

`TARGET_TERMS` carries, for every spec, the target phrases and symbols that the H4 trace extractor reads (`target_phrases`,
`target_symbols`). The base graphs, instances and gold answers are those of dataset v1 and are not modified.
"""

from __future__ import annotations

import dataclasses

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import lib_fluids, lib_modern, lib_quantum
from physmon.benchmark.v2 import rolevalue as rv
from physmon.benchmark.v2 import rolevalue_v2 as r2

P = rv.Phrasing
Pair = r2.PhrasePair
CO = r2.D_KIND_CO_PRESENT
EVENT = r2.D_KIND_OTHER_EVENT
V21 = r2.VERSION_V21


def _spec(**fields) -> r2.RoleSpecV2:
    return r2.RoleSpecV2(version=V21, author="agent (M250 batch d)", **fields)


S73 = _spec(
    structure_id="S73", quantity_phrase="a widening of the well", quantity_type="length", unit="nm", values=(1.3, 2.4, 2.8),
    heldout_values=(0.7, 1.6),
    relevant=rv.RelevantWiring("L", "add", "Widening the well by q gives the width L + q, so the ground-state energy "
                                           "hc^2 / (8 mc2 (L + q)^2) and the energy difference of the two levels change."),
    scene_clause="A quantum dot is grown on the same chip. The electron stays in the well throughout.",
    scene_object_rationale="A quantum dot grown on the same chip is a separate confining region with its own electrons; it shares no "
                           "wall with the well, so the width of the well and the levels of its electron are unchanged.",
    scene_refs=("dot",), target_terms=("well",),
    pairs=(
        Pair("p0", "Before the transition, {relation} is widened by {value} {unit}.", "the well", "the dot", CO,
             "The quantum dot is a separate confining region; widening it (an ordinary step in tuning a dot) changes neither the "
             "width of the well nor the levels of its electron, so the photon of the well has the stated wavelength.",
             ("infinite square well", "one photon"), "a small amount",
             before_context_reason="The R sentence refers to 'the well' and 'the transition' before the context introduces the "
                                   "well or any transition; placed first, it has no referent."),
        Pair("p1", "The well was widened by {value} {unit} {relation}.", "before the electron made the transition",
             "in an earlier experiment on it", EVENT,
             "The well was widened in an earlier experiment on it, which is over; in the stated experiment the well has its stated "
             "width when the electron makes the transition.", ("infinite square well", "one photon"), "a small amount"),
    ),
    notes="M250 batch d. L gets q (a widening of the well before the transition). No C: a uniform shift of the potential inside the "
          "well cancels but contradicts the listed assumption that the potential inside the well is zero. No K: the walls are "
          "infinite by statement.")

S77 = _spec(
    structure_id="S77", quantity_phrase="a replacement barrier", quantity_type="energy", unit="eV", values=(6.0, 7.2, 9.6),
    heldout_values=(7.6, 11.0),
    relevant=rv.RelevantWiring("U0", "replace", "The barrier is replaced by one of height q, so the decay constant "
                                                "kappa = sqrt(2 m (q - E)) / hbar changes and the width ln(1/T) / (2 kappa) with it."),
    scene_clause="A potential step is built on the same chip. Barrier heights are measured from the potential outside the barrier.",
    scene_object_rationale="A potential step built on the same chip is a different potential region; the electron approaches the "
                           "barrier only, so the height of the barrier and the width asked for are unchanged.",
    scene_refs=("step",), target_terms=("barrier",),
    pairs=(
        Pair("p0", "Before the electron arrives, {relation} is then replaced by one whose height is {value} {unit}.", "the barrier",
             "the step", CO,
             "The step is a different potential region that the electron does not approach; replacing it leaves the height of the "
             "barrier and the width asked for unchanged.", ("rectangular potential barrier", "kinetic energy"), "known",
             before_context_reason="The R sentence refers to 'the barrier' and to the electron's arrival before the context "
                                   "introduces them; placed first, it has no referent."),
        Pair("p1", "The barrier was then replaced by one whose height is {value} {unit} {relation}.", "before the electron approached it",
             "for an earlier experiment only", EVENT,
             "The barrier was replaced for an earlier experiment only, which is over; the electron of the stated problem approaches a "
             "barrier of the stated height.", ("rectangular potential barrier", "kinetic energy"), "known"),
    ),
    notes="M250 batch d. U0 replaced by q (an additive wiring on U0 or Ee is confounded with the opposite misuse on the other input, "
          "because the answer depends on U0 - Ee). No C: the only cancelling candidate (a shift of the zero of potential energy) "
          "would contradict the stated barrier height unless the height is declared relative to the near side. No K: the "
          "exponential form is stated.")

S82 = _spec(
    structure_id="S82", quantity_phrase="a rise of temperature", quantity_type="temperature", unit="K", values=(300.0, 950.0, 1500.0),
    heldout_values=(400.0, 850.0),
    relevant=rv.RelevantWiring("T2", "add", "A rise of the surface temperature of the second star by q gives T2 + q, so its peak "
                                            "wavelength is lam1 T1 / (T2 + q) and the photon energy hc / lam2 follows."),
    scene_clause="A tungsten calibration lamp is used beside the spectrometer.",
    scene_object_rationale="A calibration lamp beside the spectrometer is a separate light source; its filament temperature does "
                           "not enter the blackbody peak of the second star, so the answer for the star is unchanged.",
    scene_refs=("lamp",), target_terms=("star",),
    pairs=(
        Pair("p0", "Before the spectra are compared, the temperature of {relation} rises by {value} {unit}.", "the second star",
             "the lamp filament", CO,
             "The filament of the calibration lamp warms when the lamp is switched on; this changes the lamp's own spectrum only "
             "and not the peak of the second star, so the answer for the star is the stated one.",
             ("blackbody", "surface temperature"), "a small amount",
             before_context_reason="The R sentence refers to 'the second star' and to the comparison before the context "
                                   "introduces them; placed first, it has no referent."),
        Pair("p1", "The surface temperature of the second star rose by {value} {unit} {relation}.",
             "shortly before its spectrum was observed", "in an earlier outburst", EVENT,
             "The surface of the star rose in temperature in an earlier outburst, which is over; the star radiates at its stated "
             "surface temperature when its spectrum is considered.", ("blackbody", "surface temperature"), "a small amount"),
    ),
    notes="M250 batch d. T2 gets q. No C: the Wien constant is fixed by the first star and no other quantity cancels. No K: both stars "
          "are blackbodies by statement.")

S91 = _spec(
    structure_id="S91", quantity_phrase="a replacement manometer liquid", quantity_type="density", unit="kg/m^3",
    values=(1590.0, 2500.0, 3100.0), heldout_values=(1750.0, 3330.0),
    relevant=rv.RelevantWiring("rho_m", "replace", "The U-tube liquid is replaced by one of density q at the stated reading, so "
                                                   "the pressure difference is (q - rho) g dh and the flow rate follows from "
                                                   "the Bernoulli balance with continuity."),
    scene_clause="A mercury barometer hangs on the same wall. The liquid in the U-tube does not mix with the flowing liquid.",
    scene_object_rationale="A barometer hanging on the same wall is not joined to the pipe; it measures the air pressure of the room "
                           "and nothing in the pipe, so the pressure difference between the wide section and the throat is "
                           "unchanged.",
    scene_refs=("barometer",), target_terms=("u-tube", "manometer", "pipe"),
    pairs=(
        Pair("p0", "Before the levels are read, the liquid in {relation} is replaced by one whose density is {value} {unit}.",
             "the U-tube", "the barometer", CO,
             "The barometer is not joined to the pipe; replacing its liquid (as in a water-barometer demonstration) changes nothing "
             "in the U-tube, so the reading of the U-tube and the flow rate it gives are the stated ones.",
             ("U-tube manometer", "incompressible and frictionless"), "known",
             before_context_reason="The R sentence refers to 'the U-tube' and to the reading of its levels before the context "
                                   "introduces them; placed first, it has no referent."),
        Pair("p1", "The liquid in the U-tube was replaced by one whose density is {value} {unit} {relation}.",
             "before the levels were read", "for an earlier experiment only", EVENT,
             "The liquid was replaced for an earlier experiment only, which is over; the reading of the stated problem is made with the "
             "stated liquid.", ("U-tube manometer", "incompressible and frictionless"), "known"),
    ),
    cancelling=r2.CancellingV2(
        rv.CancellingSpec(
            "the height of the pipe's axis", "length", "m", (1.4, 2.1, 3.4),
            "The axis of the pipe {relation} {value} {unit} above the laboratory floor.",
            (P("c0", "lies"), P("c1", "is fixed")),
            "pi*d1**2/4*sqrt(2*(dp + rho*g*q - rho*g*q)/(rho*((d1/d2)**4 - 1)))",
            ("Bernoulli between the wide section and the throat: p1 + (1/2) rho v1^2 + rho g z1 = p2 + (1/2) rho v2^2 + rho g z2",
             "both sections lie on the axis at height q: z1 = z2 = q", "continuity: v2 = v1 (d1 / d2)^2",
             "manometer: p1 - p2 = (rho_m - rho) g dh"),
            "pi*d1**2/4*sqrt(2*(dp + rho*g*q)/(rho*((d1/d2)**4 - 1)))", nonnumeric_fill="a known height"),
        "standard", "That the elevation terms cancel for a horizontal pipe is a standard step of the Venturi derivation, but the "
                    "height of the pipe above the floor is rarely quoted and is not stated as a named fact.", (0.6, 0.9)),
    conditional=r2.ConditionalV2(
        rv.ConditionalSpec(
            "the absolute pressure in the wide section", "pressure", "kPa", (170.0, 240.0, 350.0),
            "The absolute pressure in the wide section of the pipe {relation} {value} {unit}.",
            (P("k0", "is"), P("k1", "is held at")),
            "q > dp",
            "pi*d1**2/4*sqrt(2*q/(rho*((d1/d2)**4 - 1)))", 5.0, nonnumeric_fill="a known value"),
        r2.KOut(False, "If the absolute pressure in the wide section were below the pressure difference of the manometer, the "
                       "pressure in the throat would be negative: the liquid would cavitate, Bernoulli's equation would no "
                       "longer link the stated reading to the flow, and the question 'the volume flow rate through the pipe' "
                       "would have no answer from the stated data."),
        (210.0, 260.0)),
    notes="M250 batch d. rho_m replaced by q. C: the height of the horizontal pipe cancels in the Bernoulli balance. K: the throat "
          "pressure q - dp stays positive (cavitation limit taken as zero, vapour pressure neglected); the out-of-regime law is the "
          "flow rate at which the throat pressure would reach zero.")

S93 = _spec(
    structure_id="S93", quantity_phrase="a widening of the hole", quantity_type="length", unit="mm", values=(0.6, 1.3, 1.9),
    heldout_values=(0.5, 1.7),
    relevant=rv.RelevantWiring("d", "add", "Widening the hole by q gives the diameter d + q, so the hole area is pi (d + q)^2 / 4 "
                                           "and the draining time (A / a) sqrt(2 / g) (sqrt(h0) - sqrt(h1)) changes."),
    scene_clause="A rain barrel with a hole in its bottom stands beside the tank. Water leaves the tank only through its hole, and the hole stays circular.",
    scene_object_rationale="A rain barrel with its own hole drains through that hole; its water and its hole are not part of the "
                           "tank, so the draining of the tank is unchanged.",
    scene_refs=("barrel",), target_terms=("tank",),
    pairs=(
        Pair("p0", "Before the level is timed, the hole in the bottom of {relation} is widened by a further {value} {unit}.", "the tank",
             "the barrel", CO,
             "The hole of the rain barrel is widened (to drain the barrel faster); the barrel drains through its own hole, so the "
             "hole of the tank and the time asked for are the stated ones.", ("small circular hole", "ideal"), "small amount",
             before_context_reason="The R sentence refers to 'the tank' and 'the level' before the context introduces them."),
        Pair("p1", "The hole in the bottom of the tank was widened by a further {value} {unit} {relation}.", "before the level was timed",
             "after the timing ended", EVENT,
             "The hole was widened after the timing had ended, an event after the stated process; the time for the level to fall "
             "between the stated heights was set by the stated hole.", ("small circular hole", "ideal"), "small amount"),
    ),
    cancelling=r2.CancellingV2(
        rv.CancellingSpec(
            "the density of the water", "density", "kg/m^3", (958.0, 962.0, 997.0), "The water {relation} {value} {unit}.",
            (P("c0", "has a density of"), P("c1", "has been measured to have a density of")),
            "(A/a)*sqrt(2*q/(q*g))*(sqrt(h0) - sqrt(h1))",
            ("hydrostatic pressure at the hole: p = rho g h", "Bernoulli between the surface and the jet: p = (1/2) rho v^2",
             "outflow speed: v = sqrt(2 p / rho)"),
            "(A/a)*sqrt(2/(q*g))*(sqrt(h0) - sqrt(h1))", nonnumeric_fill="a known density"),
        "standard", "That the outflow speed of Torricelli's law does not depend on the density of the liquid is standard but is "
                    "usually stated for the speed, not for the draining time.", (972.0, 994.0)),
    notes="M250 batch d. d gets q. C: the density cancels between the hydrostatic pressure and the kinetic term. No K: the ideal "
          "liquid and the small hole are stated.")

S94 = _spec(
    structure_id="S94", quantity_phrase="an extra length of pipe", quantity_type="length", unit="m", values=(3.4, 5.1, 7.3),
    heldout_values=(4.2, 6.2),
    relevant=rv.RelevantWiring("L", "add", "A further q of pipe of the same bore joined on gives the length L + q, so the pressure "
                                           "drop 128 eta (L + q) Q / (pi d^4) and the power dp Q grow with it."),
    scene_clause="A garden hose lies alongside the pipe.",
    scene_object_rationale="A garden hose lying alongside the pipe carries its own water; it is not joined to the pipe, so the "
                           "length of the pipe and the power needed to drive its flow are unchanged.",
    scene_refs=("hose",), target_terms=("pipe",),
    pairs=(
        Pair("p0", "Before the flow is started, a further {value} {unit} of tubing of the same bore is joined to {relation}.", "the pipe",
             "the hose", CO,
             "The extra tubing is joined to the hose (to reach the tap); the hose carries its own flow, so the length of the pipe "
             "and the power needed for its flow are the stated ones.", ("laminar", "straight horizontal"), "short length",
             before_context_reason="The R sentence refers to 'the pipe' and to the flow before the context introduces them; "
                                   "placed first, it has no referent."),
        Pair("p1", "A further {value} {unit} of tubing of the same bore was joined to the pipe {relation}.", "before the flow was started",
             "for an earlier experiment only", EVENT,
             "The extra tubing was joined for an earlier experiment only, which is over; the power needed to drive the flow in "
             "the stated length is the stated one.", ("laminar", "straight horizontal"), "short length"),
    ),
    cancelling=r2.CancellingV2(
        rv.CancellingSpec(
            "the pressure at the outlet of the pipe", "pressure", "kPa", (91.0, 96.0, 101.0),
            "The liquid leaves the pipe {relation} {value} {unit}.",
            (P("c0", "at a pressure of"), P("c1", "at a measured pressure of")),
            "((q + dp) - q)*Q",
            ("pressure at the inlet: p_in = p_out + dp", "pressure drop along the pipe: dp = p_in - p_out",
             "power: P = (p_in - p_out) Q"),
            "(q + dp)*Q", nonnumeric_fill="a known pressure"),
        "standard", "That only the pressure difference between the ends of the pipe enters the power, not the pressure at which "
                    "the liquid leaves, is routine in fluids but is not stated as a named fact.", (94.0, 99.0)),
    notes="M250 batch d. L gets q. C: the pressure at the outlet cancels in the pressure drop. K: for laminar flow the "
          "density does not enter (Re < 2000); the out-of-regime law is the Blasius turbulent power. The counter-regime density is "
          "a formal value (every instance must leave the regime), not a real liquid.")

S95 = _spec(
    structure_id="S95", quantity_phrase="an extra load", quantity_type="mass", unit="kg", values=(340.0, 560.0, 710.0),
    heldout_values=(430.0, 620.0),
    relevant=rv.RelevantWiring("m", "add", "A further load of mass q on the large piston gives the load m + q, so the gauge "
                                           "pressure at the large piston is (m + q) g / A2 and the force on the small piston "
                                           "(pL + rho g h) A1 follows."),
    scene_clause="A bottle jack stands beside the lift. The oil stays in the lift and is incompressible.",
    scene_object_rationale="A bottle jack standing beside the lift has its own oil and ram; it is not joined to the lift, so the "
                           "force needed on the small piston of the lift is unchanged.",
    scene_refs=("jack",), target_terms=("lift", "piston"),
    pairs=(
        Pair("p0", "Before the force is applied, a further {value} {unit} load is placed on {relation}.", "the large piston",
             "the jack", CO,
             "The load is placed on the jack, which is not joined to the lift; the load on the lift and the force needed on its "
             "small piston are the stated ones.", ("in equilibrium", "light"), "small",
             before_context_reason="The R sentence refers to 'the large piston' and to the applied force before the context "
                                   "introduces them; placed first, it has no referent."),
        Pair("p1", "A further {value} {unit} load was placed on the large piston {relation}.",
             "before the force was applied", "for an earlier experiment only", EVENT,
             "The load was placed for an earlier experiment only, which is over; the lift of the stated problem carries the stated "
             "load.", ("in equilibrium", "light"), "small"),
    ),
    cancelling=r2.CancellingV2(
        rv.CancellingSpec(
            "the atmospheric pressure", "pressure", "kPa", (91.0, 94.0, 96.0), "The atmospheric pressure {relation} {value} {unit}.",
            (P("c0", "is"), P("c1", "was measured at")),
            "((q + pL + rho*g*h) - q)*A1",
            ("absolute pressure at the large piston: p_L = p_atm + m g / A2", "absolute pressure at the small piston: "
             "p_S = p_L + rho g h", "force balance on the small piston: F + p_atm A1 = p_S A1"),
            "(q + pL + rho*g*h)*A1", nonnumeric_fill="a known pressure"),
        "standard", "That the atmosphere acts on both outer faces and drops out of the force is standard in hydraulics, and the "
                    "problem itself mentions it, but the actual pressure is never needed or quoted.", (92.0, 95.0)),
    notes="M250 batch d. m gets q. C: the atmospheric pressure cancels between the two pistons. No K: the oil is incompressible by "
          "statement and a compressibility effect would be below the grading tolerance.")


SPECS: dict[str, r2.RoleSpecV2] = {s.structure_id: s for s in (
    S73, S77, S82, S91, S93, S94, S95)}

# Structures of the batch that cannot honestly carry the design, with the reason (never a forced spec).
# Quantities that look like a K candidate but are not an honest regime (never forced into a spec).
NO_C: dict[str, str] = {
    "S73": "A uniform shift of the potential inside the well would cancel in the transition energy, but it contradicts the "
           "stated assumption that the potential inside the well is zero; no other quantity enters the levels hc^2 n^2 / (8 mc2 L^2) "
           "and then drops out, so a C quantity would have to be forced.",
    "S77": "The only cancelling candidate is a shift of the zero of potential energy, which moves the barrier height and the "
           "kinetic energy together; it contradicts the stated barrier height unless that height is declared relative to the near "
           "side, and no other quantity of the exponential transmission formula cancels.",
    "S82": "The peak wavelength comes from the Wien displacement law fixed by the first star, and the photon energy is hc over it. "
           "A star's radius or luminosity would cancel, but neither is a node of the graph (no Stefan-Boltzmann relation is part "
           "of the problem), so a C built on it would be forced, not physical.",
}
NO_K: dict[str, str] = {
    "S73": "The walls are infinite by statement, so there is no finite-wall regime with a value; the only candidate, a finite "
           "wall height, would change the question to a finite well that the base problem does not state and has no certified "
           "closed form here.",
    "S77": "The exponential form of the transmission probability is stated for the problem; the regime quantity (a barrier thin "
           "enough that the exponential approximation fails) is the answer itself, and the out-of-regime transmission law "
           "is not stated, so no K quantity with a certified counter-regime answer exists.",
    "S82": "Both stars are blackbodies by statement and Wien's law holds for every temperature; there is no regime quantity "
           "(such as an emissivity or an optical-depth threshold) in the problem with a certified out-of-regime law.",
    "S93": "The regime (ideal liquid, small hole, negligible surface speed) is stated as assumptions without a free value; the "
           "quantities that could define it, the tank and hole diameters, are already inputs, and a viscosity or surface-speed "
           "correction would change the law without a certified out-of-regime answer for this question.",
    "S95": "The oil is incompressible by statement, and a compressibility effect would be far below the grading tolerance; the "
           "pistons are light and frictionless by statement, so no regime quantity with a counter-regime answer exists.",
    "S94": "The only candidate is the density of the liquid with the laminar regime Re < 2000. Every real liquid satisfies that "
           "regime in this pipe at the stated speed and diameter, and the counter-regime value would have to be about 40,000 "
           "kg/m^3, which no liquid has. A regime that real values cannot leave is not an honest K (plan wants a regime that "
           "real values could leave).",
}

INFEASIBLE: dict[str, str] = {
    "S84": "The only inputs that change the age of this sample are its measured activity A, the activity of living carbon A0 and "
           "the half-life (a stated constant). Replacing the sample by another one (A replace) changes which tree the question "
           "is about, so the R contradicts the base; a background count (A subtract) contradicts the stated activity of the "
           "radiocarbon in the sample; A0 and the half-life are stated constants of the dating assumption. No quantity changes "
           "the asked age of THIS sample without replacing it or contradicting the prompt, so no spec (including the mass C).",
    "S74": "The inputs are the stated Bohr levels of the very atom (at rest in level n = 3, dropping to n = 2), its stated mass and "
           "constants. Re-preparing the atom in another level contradicts 'at rest in the Bohr level n = 3'; replacing it by "
           "another isotope offers only three honest masses (1, 2, 3 u) and contradicts the stated mass; attaching a fragment "
           "changes the Bohr levels through the bond. No R wording is true to the base, so no spec (new wording rule 2).",
    "S75": "Every input is a stated property of the scattering itself: the photon has the stated wavelength when it scatters. A "
           "preceding event that lengthens the wavelength (a first collision, a filter) contradicts 'a photon of wavelength 20 pm "
           "scatters', as the S02 extra release distance contradicted 'released from rest' (new wording rule 2); the angle is "
           "likewise a stated outcome, and the constants are stated.",
    "S76": "Zeff is a model input of the estimate, stated as the effective charge of the nucleus. Replacing the nucleus contradicts the "
           "stated charge, and the only second object with an effective charge is another nucleus, the same type as the target "
           "(new wording rule 4), so the co-present D has no different-type object and the R has no honest wording.",
    "S78": "The R quantity would have to be an isotopic replacement of the molecule (reduced mass), which contradicts the stated "
           "reduced mass; the co-present D needs another object that carries an isotopic reduced mass, which can only be another "
           "diatomic molecule, the same type as the target (new wording rule 4, ambiguous referent 'the molecule').",
    "S79": "The prompt states the kinetic energy with which the electrons strike the anode. A further accelerating stage before the "
           "anode contradicts that stated strike energy, and a replacement of the strike energy leaves no different-type object "
           "that is struck by electrons of a stated energy in the same frame (new wording rules 2 and 4).",
    "S81": "Every input is either a stated constant (c), the dimensionless speed beta or the lab flight distance d. A relevant event "
           "on d ('a further q of flight') contradicts the stated 'decays after it has travelled d at a constant speed', and an "
           "event on beta contradicts the stated constant speed; no honest additive or replacing event leaves the statement true.",
    "S85": "The released energy is Q = Dp - Dd - Da, so an excitation of the parent (Dp + q) is numerically identical to the opposite "
           "misuse on the daughter or the helium excess (Dd - q, Da - q): every additive event on one mass excess is confounded with "
           "a subtractive misuse on another, so the misuse curves cannot be separated from the gold (admission 2.5, blocking). The "
           "only other input that moves the answer is the daughter mass number, which no event changes honestly, and replacing the "
           "parent excess alone would describe a different parent whose daughter, stated in the problem, would differ.",
    "S86": "The answer is the speed, which saturates at c: two of the four instances start at 1500 and 2000 MeV, where a further energy "
           "that moves the speed by more than the loosest tolerance (1%) needs several GeV, and at those energies the misuse of "
           "replacing K by q lands within 1% of the relevant answer (confounded, blocking). Instances where the relevant event is "
           "distinguishable from its misuse and from D at all four instances do not exist for an additive event on K.",
    "S83": "The inputs are the proton number, the neutron number and the mass defect of one fixed nucleus; the mass defect is not "
           "independent of the nucleon numbers, and the energy equivalent of the atomic mass unit is a stated constant. Changing "
           "any one input by an event describes a different nucleus, and the mass defect is dimensionless in the graph, so a "
           "quantity in physical units cannot be wired into it.",
}

STRUCTURE_FACTORIES = {
    "S73": lib_quantum.s73_infinite_well_photon,
    "S77": lib_quantum.s77_tunnelling_barrier_width,
    "S82": lib_modern.s82_wien_peak_photon,
    "S91": lib_fluids.s91_venturi_flow_rate,
    "S93": lib_fluids.s93_tank_drain_time,
    "S94": lib_fluids.s94_poiseuille_pump_power,
    "S95": lib_fluids.s95_hydraulic_lift_force,
}

# What the H4 trace extractor must read as a statement of the target: the target phrase of the question, its head noun, and the
# conventional symbols of the target quantity (format of `roles_m0v2.TARGET_TERMS`).
TARGET_TERMS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "S73": (("wavelength of the emitted photon", "wavelength"), ("lambda", "λ")),
    "S77": (("barrier width", "width"), ("a", "w")),
    "S82": (("energy of a photon", "photon energy", "energy"), ("E", "E_ph")),
    "S91": (("volume flow rate", "flow rate"), ("Q",)),
    "S93": (("how long", "time"), ("t", "T")),
    "S94": (("power needed to drive the flow", "power"), ("P",)),
    "S95": (("force", "force that must be applied"), ("F",)),
}


def structure(structure_id: str) -> gr.Structure:
    """The October structure with the spec's scene clause appended to its base context."""

    return r2.with_scene(STRUCTURE_FACTORIES[structure_id](), SPECS[structure_id].scene_clause)


def with_changes(structure_id: str, **changes) -> r2.RoleSpecV2:
    return dataclasses.replace(SPECS[structure_id], **changes)
