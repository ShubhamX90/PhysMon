"""DECOY-v2 domain batch: modern physics (special relativity, atomic and nuclear), structures S81 to S86 (Stage 14.19).

Same pattern as `library_c.py`: a typed graph with input and computed nodes, an independently coded numeric solver for each structure
(a bracketing root finder, a linear system, a quadrature), several numeric instantiations, a relevant edit that moves the answer, and a
`RenderSpec` through `_spec`. Every structure also has a gold solution plan (`PLANS`): the named law behind each computed node and the
reason it applies, which `trace.render_trace` turns into a step-by-step gold trace.

Masses of nuclei are given as numbers of atomic mass units (a pure number, unit "1") or as mass excesses in MeV, so that every numeral
in a prompt has at most four significant figures and still carries the information the answer needs.

Admission status: agent-verified, not expert-reviewed.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.integrate import quad
from scipy.optimize import brentq

from physmon.benchmark.v2.graph import Assumption, Structure
from physmon.benchmark.v2.library import _co, _in, _spec
from physmon.benchmark.v2.trace import Plan, Step

# --- solvers (independent routes; SI inputs in node order) -----------------------------------------


def _solve_lifetime(beta, c, d):
    # The proper time from the invariant interval: (c tau)^2 = (c t)^2 - d^2, with t = d / (beta c); root found by bracketing.
    lab_time = d / (beta * c)
    interval = c * lab_time
    length = brentq(lambda s: s * s - (interval * interval - d * d), 0.0, interval, xtol=1e-12, rtol=1e-14)
    return float(length / c)


def _solve_wien_photon(lam1, t1, t2, hc):
    # Planck's spectral radiance per unit wavelength is largest where x / (1 - exp(-x)) = 5, with x = hc / (lambda k T).
    # Solve that condition for the dimensionless peak position x*, calibrate hc / k on the first star, then locate the peak of the
    # second star with a second root finder and convert it to a photon energy.
    x_star = brentq(lambda x: x / (1.0 - math.exp(-x)) - 5.0, 1.0, 10.0, xtol=1e-14, rtol=1e-14)
    hc_over_k = x_star * lam1 * t1

    def condition(lam):
        x = hc_over_k / (lam * t2)
        return x / (1.0 - math.exp(-x)) - 5.0

    peak = brentq(condition, 0.01 * lam1, 100.0 * lam1, xtol=1e-20, rtol=1e-14)
    return float(hc / peak)


def _solve_binding(zp, nn, dm, uc2):
    # The total binding energy as the integral of the constant energy per unit mass over the mass defect, shared among the nucleons.
    total, _ = quad(lambda m: uc2, 0.0, dm, epsabs=1e-25, epsrel=1e-12)
    return float(total / (zp + nn))


def _solve_radiocarbon(activity, activity0, half_life):
    # The decay constant (in units of 1 / half-life) from exp(-x) = 1/2, then the age from A0 exp(-x s) = A, both by root finding.
    x = brentq(lambda y: math.exp(-y) - 0.5, 0.0, 10.0, xtol=1e-15, rtol=1e-14)
    s = brentq(lambda u: activity0 * math.exp(-x * u) - activity, 0.0, 100.0, xtol=1e-14, rtol=1e-14)
    return float(s * half_life)


def _solve_alpha_energy(dp, dd, da, ad, aa):
    # Energy conservation (Ka + Kd = Q) and equal and opposite momenta (2 ma Ka = 2 md Kd), as a linear system in (Ka, Kd).
    q = dp - dd - da
    matrix = np.array([[1.0, 1.0], [aa, -ad]])
    rhs = np.array([q, 0.0])
    return float(np.linalg.solve(matrix, rhs)[0])


def _solve_proton_speed(e0, kinetic, c):
    # The speed as the root of the relativistic kinetic energy relation (1 / sqrt(1 - beta^2) - 1) = K / E0, bracketing beta.
    beta = brentq(lambda b: 1.0 / math.sqrt(1.0 - b * b) - 1.0 - kinetic / e0, 0.0, 1.0 - 1e-12, xtol=1e-15, rtol=1e-14)
    return float(beta * c)


# --- structures ---------------------------------------------------------------------------------------


def s81_proper_lifetime() -> Structure:
    return Structure(
        "S81", "Proper lifetime of a particle from its flight distance", "special relativity", "time_dilation_proper_lifetime",
        (_in("beta", "dimensionless", "1", "speed of the particle in units of the speed of light", 0.8, (0.5, 0.99)),
         _in("c", "speed", "km/s", "speed of light in vacuum, a stated constant", 299800.0, (299000.0, 300500.0), provenance="assumed"),
         _in("d", "length", "m", "distance between the production and the decay points in the laboratory", 60.0, (10.0, 500.0)),
         _co("v", "speed", "km/s", "speed of the particle in the laboratory", "beta*c"),
         _co("t", "time", "ns", "time of flight measured in the laboratory", "d/v"),
         _co("gamma", "dimensionless", "1", "Lorentz factor of the particle", "1/sqrt(1 - beta**2)"),
         _co("tau", "time", "ns", "proper lifetime of the particle, measured in its own rest frame", "t/gamma")),
        "tau",
        (Assumption("A-straight", "The particle moves in a straight line at a constant speed between its production and its decay.", "modelling", ("beta", "d")),
         Assumption("A-c", "The speed of light is the stated constant.", "modelling", ("c",)),
         Assumption("A-frames", "The distance is measured in the laboratory frame and the answer is the time between the two events in the particle's own rest frame.", "boundary_condition", ("d",))),
        _spec("An unstable particle is produced in a detector and decays after it has travelled {d} m through the laboratory in a straight "
              "line at a constant speed of {beta} times the speed of light, c. Take c = {c} km/s.",
              "What time elapses between the production and the decay of the particle as measured in the rest frame of the particle?",
              "time between production and decay in the rest frame of the particle", "ns",
              "A separate muon B in another experiment has a lifetime of {v} {u}, but it is unrelated to this particle.",
              "A reference particle B has a lifetime of {v} {u} in its own rest frame.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the flight of the particle.", "W", equivalent="μs"),
        ("d", 1.25), _solve_lifetime, 3,
        "the proper time from the invariant interval (c tau) squared = (c t) squared minus d squared, as the root of a bracketing root finder",
        solver_rel_tol=1e-9,
        instances=({"beta": 0.8, "c": 299800.0, "d": 60.0}, {"beta": 0.6, "c": 299800.0, "d": 45.0},
                   {"beta": 0.96, "c": 300000.0, "d": 120.0}, {"beta": 0.9, "c": 299800.0, "d": 100.0}))


def s82_wien_peak_photon() -> Structure:
    return Structure(
        "S82", "Photon energy at the peak of a second blackbody spectrum", "modern physics", "wien_displacement_peak_photon_energy",
        (_in("lam1", "length", "nm", "peak wavelength of the spectrum of the first star", 500.0, (300.0, 1000.0)),
         _in("T1", "temperature", "K", "surface temperature of the first star", 5800.0, (3000.0, 10000.0)),
         _in("T2", "temperature", "K", "surface temperature of the second star", 2900.0, (2000.0, 10000.0)),
         _in("hc", "energy_length", "eV*nm", "product of the Planck constant and the speed of light, a stated constant", 1240.0, (1230.0, 1250.0), provenance="assumed"),
         _co("lam2", "length", "nm", "peak wavelength of the spectrum of the second star", "lam1*T1/T2"),
         _co("Eph", "energy", "eV", "energy of a photon at the peak wavelength of the second star", "hc/lam2")),
        "Eph",
        (Assumption("A-blackbody", "Both stars radiate as ideal blackbodies, and the peak is the maximum of the spectral radiance per unit wavelength.", "modelling", ("lam1", "T1", "T2")),
         Assumption("A-hc", "The product hc is the stated constant.", "modelling", ("hc",))),
        _spec("The spectrum of the first star, which radiates as a blackbody at a surface temperature of {T1} K, has its maximum spectral "
              "radiance per unit wavelength at a wavelength of {lam1} nm. A second star also radiates as a blackbody, at a surface "
              "temperature of {T2} K. Take hc = {hc} eV nm.",
              "What is the energy of a photon whose wavelength equals the wavelength of maximum spectral radiance of the second star?",
              "photon energy at the spectral peak of the second star", "eV",
              "A separate photon source C emits photons of energy {v} {u}, but it is unrelated to the two stars.",
              "A reference photon source C emits photons of energy {v} {u}.",
              "A separate laser pointer C is rated at {v} {u}, but it plays no part in the starlight.", "W", equivalent="keV"),
        ("T2", 1.25), _solve_wien_photon, 4,
        "the Planck peak condition x / (1 - exp(-x)) = 5 solved with a bracketing root finder, calibrated on the first star, then the second star's peak located by a second root finder",
        solver_rel_tol=1e-9,
        instances=({"lam1": 500.0, "T1": 5800.0, "T2": 2900.0, "hc": 1240.0},
                   {"lam1": 480.0, "T1": 6000.0, "T2": 4000.0, "hc": 1240.0},
                   {"lam1": 600.0, "T1": 4800.0, "T2": 7200.0, "hc": 1240.0},
                   {"lam1": 725.0, "T1": 4000.0, "T2": 5800.0, "hc": 1230.0}))


def s83_binding_energy_per_nucleon() -> Structure:
    return Structure(
        "S83", "Binding energy per nucleon from the mass defect", "nuclear physics", "mass_defect_binding_energy_per_nucleon",
        (_in("Zp", "count", "1", "number of protons in the nucleus", 2.0, (1.0, 50.0)),
         _in("Nn", "count", "1", "number of neutrons in the nucleus", 2.0, (0.0, 80.0)),
         _in("dm", "dimensionless", "1", "mass defect of the nucleus, as a number of atomic mass units", 0.03038, (0.001, 1.0)),
         _in("uc2", "energy", "MeV", "energy equivalent of one atomic mass unit, a stated constant", 931.5, (931.0, 932.0), provenance="assumed"),
         _co("Anuc", "count", "1", "total number of nucleons", "Zp + Nn"),
         _co("Etot", "energy", "MeV", "total binding energy of the nucleus", "dm*uc2"),
         _co("eb", "energy", "MeV", "binding energy per nucleon", "Etot/Anuc")),
        "eb",
        (Assumption("A-defect", "The mass defect is the total mass of the separated protons and neutrons minus the mass of the nucleus, as a number of atomic mass units.", "modelling", ("dm",)),
         Assumption("A-uc2", "The energy equivalent of one atomic mass unit is the stated constant.", "modelling", ("uc2",))),
        _spec("A nucleus contains {Zp} protons and {Nn} neutrons. Its mass defect, the total mass of the separated nucleons minus the "
              "mass of the nucleus, is {dm} u. Take the energy equivalent of one atomic mass unit to be {uc2} MeV.",
              "What is the binding energy per nucleon of this nucleus?", "binding energy per nucleon", "MeV",
              "A separate nucleus B in another experiment has a binding energy per nucleon of {v} {u}, but it is unrelated to this nucleus.",
              "A reference nucleus B has a binding energy per nucleon of {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the binding of the nucleus.", "W", equivalent="keV"),
        ("dm", 1.25), _solve_binding, 4,
        "the total binding energy as the integral of the constant energy per unit mass over the mass defect, shared among the nucleons",
        solver_rel_tol=1e-9,
        instances=({"Zp": 2.0, "Nn": 2.0, "dm": 0.03038, "uc2": 931.5}, {"Zp": 6.0, "Nn": 6.0, "dm": 0.09894, "uc2": 931.5},
                   {"Zp": 8.0, "Nn": 8.0, "dm": 0.137, "uc2": 931.5}, {"Zp": 26.0, "Nn": 30.0, "dm": 0.5285, "uc2": 931.0}))


def s84_radiocarbon_age() -> Structure:
    return Structure(
        "S84", "Age of a charcoal sample from its radiocarbon activity", "nuclear physics", "radioactive_decay_age_from_activity",
        (_in("A", "activity", "Bq", "present activity of the radiocarbon in the sample", 150.0, (20.0, 200.0)),
         _in("A0", "activity", "Bq", "activity of the same mass of carbon from a living tree", 240.0, (220.0, 400.0)),
         _in("Thalf", "time", "yr", "half-life of radiocarbon, a stated constant", 5730.0, (5700.0, 5760.0), provenance="assumed"),
         _co("R", "dimensionless", "1", "fraction of the original activity that remains", "A/A0"),
         _co("lam", "rate", "1/s", "decay constant of radiocarbon", "log(2)/Thalf"),
         _co("t", "time", "yr", "time since the tree died", "-log(R)/lam")),
        "t",
        (Assumption("A-initial", "The radiocarbon activity per unit mass of carbon was the same, equal to that of a living tree, at the moment the tree died, and has only decreased by radioactive decay since.", "modelling", ("A", "A0")),
         Assumption("A-halflife", "The half-life of radiocarbon is the stated constant.", "modelling", ("Thalf",))),
        _spec("A charcoal sample from an archaeological site contains radiocarbon, the radioactive isotope of carbon used for dating, whose "
              "half-life is {Thalf} years. The radiocarbon in the sample has an activity of {A} Bq. The same mass of carbon taken from a "
              "living tree has an activity of {A0} Bq. Assume that the activity per unit mass of living carbon has always had this value and "
              "that the sample has decayed freely since the tree died.",
              "How many years ago did the tree die?", "time since the tree died", "yr",
              "A separate fossil B from another site is {v} {u} old, but it is unrelated to this sample.",
              "A reference sample B has an age of {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the dating.", "W", equivalent="d"),
        ("A", 0.9), _solve_radiocarbon, 3,
        "the decay constant from exp(-x) = 1/2 and the age from A0 exp(-x s) = A, both with bracketing root finders",
        solver_rel_tol=1e-9,
        instances=({"A": 150.0, "A0": 240.0, "Thalf": 5730.0}, {"A": 96.0, "A0": 250.0, "Thalf": 5730.0},
                   {"A": 45.0, "A0": 300.0, "Thalf": 5730.0}, {"A": 180.0, "A0": 300.0, "Thalf": 5700.0}))


def s85_alpha_decay_energy() -> Structure:
    return Structure(
        "S85", "Kinetic energy of an alpha particle from alpha decay", "nuclear physics", "alpha_decay_q_value_and_recoil_sharing",
        (_in("Dp", "energy", "MeV", "atomic mass excess of the parent atom", 23.67, (20.0, 60.0)),
         _in("Dd", "energy", "MeV", "atomic mass excess of the daughter atom", 16.37, (5.0, 60.0)),
         _in("Da", "energy", "MeV", "atomic mass excess of the neutral helium atom, a stated constant", 2.425, (2.3, 2.5), provenance="assumed"),
         _in("Ad", "count", "1", "mass number of the daughter nucleus", 222.0, (200.0, 240.0)),
         _in("Aa", "count", "1", "mass number of the alpha particle, a stated constant", 4.0, (3.0, 5.0), provenance="assumed"),
         _co("Q", "energy", "MeV", "total kinetic energy released in the decay", "Dp - Dd - Da"),
         _co("frac", "dimensionless", "1", "fraction of the released energy carried by the alpha particle", "Ad/(Ad + Aa)"),
         _co("Ka", "energy", "MeV", "kinetic energy of the alpha particle", "Q*frac")),
        "Ka",
        (Assumption("A-rest", "The parent nucleus is at rest and the decay has two products, the alpha particle and the daughter nucleus.", "boundary_condition", ("Dp", "Dd")),
         Assumption("A-atomic", "Atomic mass excesses can replace nuclear ones because the number of electrons is the same before and after the decay.", "modelling", ("Dp", "Dd", "Da")),
         Assumption("A-nonrel", "The recoil is treated non-relativistically and the mass ratio of the two products is the ratio of their mass numbers.", "modelling", ("Ad", "Aa"))),
        _spec("A heavy atom at rest decays by emitting an alpha particle. The atomic mass excess, that is the atomic mass minus the mass "
              "number expressed as an energy, is {Dp} MeV for the parent atom, {Dd} MeV for the daughter atom and {Da} MeV for the neutral "
              "helium atom. The daughter nucleus has mass number {Ad} and the alpha particle has mass number {Aa}. Treat the motion of the "
              "products non-relativistically and take the ratio of their masses to be the ratio of their mass numbers.",
              "What is the kinetic energy of the emitted alpha particle?", "kinetic energy of the alpha particle", "MeV",
              "A separate alpha particle B from another source has a kinetic energy of {v} {u}, but it is unrelated to this decay.",
              "A reference alpha particle B has a kinetic energy of {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the decay.", "W", equivalent="keV"),
        ("Dp", 1.1), _solve_alpha_energy, 5,
        "energy conservation and equal and opposite momenta of the two products, written as a 2 by 2 linear system for the two kinetic energies",
        solver_rel_tol=1e-9,
        instances=({"Dp": 23.67, "Dd": 16.37, "Da": 2.425, "Ad": 222.0, "Aa": 4.0},
                   {"Dp": 35.45, "Dd": 28.94, "Da": 2.425, "Ad": 228.0, "Aa": 4.0},
                   {"Dp": 47.31, "Dd": 40.61, "Da": 2.425, "Ad": 234.0, "Aa": 4.0},
                   {"Dp": 48.59, "Dd": 40.92, "Da": 2.425, "Ad": 235.0, "Aa": 4.0}))


def s86_proton_speed_from_kinetic_energy() -> Structure:
    return Structure(
        "S86", "Speed of a fast proton from its kinetic energy", "special relativity", "relativistic_kinetic_energy_speed",
        (_in("E0", "energy", "MeV", "rest energy of the proton, a stated constant", 938.3, (938.0, 938.6), provenance="assumed"),
         _in("K", "energy", "MeV", "kinetic energy of the proton", 500.0, (100.0, 3000.0)),
         _in("c", "speed", "km/s", "speed of light in vacuum, a stated constant", 299800.0, (299000.0, 300500.0), provenance="assumed"),
         _co("Etot", "energy", "MeV", "total energy of the proton", "K + E0"),
         _co("gamma", "dimensionless", "1", "Lorentz factor of the proton", "Etot/E0"),
         _co("beta", "dimensionless", "1", "speed of the proton in units of the speed of light", "sqrt(1 - 1/gamma**2)"),
         _co("v", "speed", "km/s", "speed of the proton", "beta*c")),
        "v",
        (Assumption("A-free", "The proton is a free particle moving in a vacuum, and special relativity applies in the laboratory frame.", "modelling", ("K",)),
         Assumption("A-constants", "The rest energy of the proton and the speed of light are the stated constants.", "modelling", ("E0", "c"))),
        _spec("A free proton moves through a vacuum. Its rest energy is {E0} MeV and its kinetic energy is {K} MeV. Take c = {c} km/s and "
              "use relativistic mechanics.",
              "What is the speed of the proton?", "speed of the proton", "km/s",
              "A separate rocket B in another experiment moves at {v} {u}, but it is unrelated to this proton.",
              "A reference proton B moves at {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the motion of the proton.", "W", equivalent="m/s"),
        ("K", 1.5), _solve_proton_speed, 3,
        "the speed as the root of 1 / sqrt(1 - beta squared) - 1 = K / E0, found with a bracketing root finder on beta",
        solver_rel_tol=1e-9,
        instances=({"E0": 938.3, "K": 500.0, "c": 299800.0}, {"E0": 938.3, "K": 200.0, "c": 299800.0},
                   {"E0": 938.3, "K": 1500.0, "c": 300000.0}, {"E0": 938.0, "K": 2000.0, "c": 299800.0}))


ALL = (s81_proper_lifetime, s82_wien_peak_photon, s83_binding_energy_per_nucleon, s84_radiocarbon_age, s85_alpha_decay_energy,
       s86_proton_speed_from_kinetic_energy)


def all_structures() -> list[Structure]:
    return [factory() for factory in ALL]


# --- gold solution plans -----------------------------------------------------------------------------------

PLANS = {
    "S81": Plan(
        approach="We want the time between production and decay in the particle's own rest frame. First describe the flight in the "
                 "laboratory frame, where the distance and the speed are known, to get the laboratory time of flight; then convert that "
                 "dilated time to the proper time with the Lorentz factor.",
        steps=(
            Step("gamma", "Definition of the Lorentz factor, gamma = 1 / sqrt(1 - beta squared), with beta the speed in units of c",
                 "Relating times in the laboratory and in the rest frame of a moving particle needs gamma; it is fixed by the speed "
                 "fraction beta alone."),
            Step("v", "Definition of the speed fraction: the speed is v = beta times c",
                 "The speed is given as a fraction of c, so multiplying by the stated value of c gives the laboratory speed that is needed "
                 "to turn the flight distance into a time."),
            Step("t", "Kinematics of uniform motion: distance = speed times time, so the laboratory time is t = d / v",
                 "In the laboratory frame the particle covers the distance d at constant speed v; this gives the laboratory time between "
                 "the two events, which is a dilated time and not yet the proper time."),
            Step("tau", "Time dilation: the laboratory time interval is gamma times the proper time, t = gamma tau",
                 "Production and decay happen at the same place in the particle's own frame, so a single clock moving with the particle "
                 "measures the proper time, the shortest possible interval; dividing the laboratory time by gamma gives it."),
        ),
        check="The proper time must be shorter than the laboratory time and tend to it as beta goes to zero, where gamma goes to one. "
              "As a second route, the invariant interval (c tau) squared = (c t) squared - d squared gives the same proper time."),
    "S82": Plan(
        approach="The peak wavelength of a blackbody spectrum scales inversely with temperature, so we first get the peak wavelength of "
                 "the second star from the data of the first star, and then convert that wavelength to a photon energy.",
        steps=(
            Step("lam2", "Wien's displacement law: the wavelength of maximum spectral radiance of a blackbody is inversely proportional "
                         "to its temperature, lambda_max times T = constant",
                 "Both stars are blackbodies, so the product of peak wavelength and temperature has the same value for both; the known pair "
                 "of the first star fixes it, which gives the peak wavelength of the second star without needing the value of Wien's constant."),
            Step("Eph", "Planck-Einstein relation for a photon: E = h f = h c / lambda",
                 "The question asks for the energy of a photon at the peak wavelength of the second star; with hc given in eV nm and the "
                 "wavelength in nm, the energy comes out directly in eV."),
        ),
        check="The hotter a star the shorter its peak wavelength and the larger the photon energy at the peak, so the sign of the change "
              "between the two stars must agree with the temperature ratio. The product of the photon energy in eV and the wavelength "
              "in nm must reproduce the stated value of hc."),
    "S83": Plan(
        approach="The binding energy of a nucleus is the energy equivalent of its mass defect. Get the total binding energy from the mass "
                 "defect, count the nucleons, and divide to get the binding energy per nucleon.",
        steps=(
            Step("Anuc", "Definition of the mass number: the number of nucleons is the number of protons plus the number of neutrons, A = Z + N",
                 "The binding energy per nucleon needs the total number of nucleons, which are both the protons and the neutrons."),
            Step("Etot", "Mass-energy equivalence, E = (delta m) c squared, applied to the mass defect: the binding energy is the energy "
                         "equivalent of the mass defect",
                 "When the separated nucleons bind into the nucleus, the mass defect is the mass that is released as energy; multiplying "
                 "the mass defect in atomic mass units by the energy equivalent of one atomic mass unit gives the total binding energy in MeV."),
            Step("eb", "Definition of the binding energy per nucleon, B / A",
                 "The quantity asked for is the average energy that binds each nucleon, which is the total binding energy divided by the "
                 "number of nucleons."),
        ),
        check="The result should be of the order of 8 MeV per nucleon, which is the typical value for stable nuclei (between about 7 and 9 MeV "
              "for most of them); the units also check, since atomic mass units times MeV per atomic mass unit give MeV."),
    "S84": Plan(
        approach="Radioactive activity falls exponentially with time, and the half-life is the only time scale. We find the fraction of the "
                 "activity that remains, convert the half-life to a decay constant, and invert the exponential decay law for the elapsed time.",
        steps=(
            Step("R", "The activity is proportional to the number of radioactive nuclei (A = lambda N), so the remaining fraction of the "
                      "nuclei equals the ratio of the activities, R = A / A0",
                 "The same mass of carbon from a living tree gives the activity at the moment of death, so the ratio of the present activity "
                 "to it is the fraction of radiocarbon that has not yet decayed."),
            Step("lam", "Relation between the half-life and the decay constant, lambda = ln 2 / T_half, which follows from N(T_half) = N0 / 2",
                 "The half-life is given but the exponential decay law needs the decay constant, so we convert one to the other."),
            Step("t", "Law of radioactive decay in activity form, A = A0 exp(-lambda t), solved for the time: t = ln(A0 / A) / lambda",
                 "The surviving fraction R is exp(-lambda t), so taking the natural logarithm and dividing by the decay constant gives "
                 "the time that has passed since the tree stopped taking up carbon."),
        ),
        check="If the activity were half of the living value the age would be exactly one half-life, and if the activity were equal to "
              "the living value the age would be zero; the age grows only logarithmically as the remaining fraction shrinks, "
              "so it must be a few half-lives at most for a measurable sample."),
    "S85": Plan(
        approach="The energy released in the decay appears as kinetic energy of the two products. First find the total energy release from "
                 "the mass excesses, then split it between the alpha particle and the recoiling daughter using momentum conservation in the "
                 "rest frame of the parent.",
        steps=(
            Step("Q", "Energy conservation with mass-energy equivalence: Q = (M_parent - M_daughter - M_alpha) c squared, and since the "
                      "mass number is conserved the mass-number parts cancel, so Q is the parent mass excess minus the daughter and alpha mass excesses",
                 "The energy released equals the energy equivalent of the mass that disappears; atomic masses can be used because the "
                 "number of electrons is the same before and after, and the mass excesses are already expressed as energies."),
            Step("frac", "Conservation of momentum with the parent at rest: the products have equal and opposite momenta, so with "
                         "K = p squared / 2m the kinetic energies are in the inverse ratio of the masses, K_alpha / K_daughter = m_daughter / m_alpha",
                 "Equal momenta mean the lighter alpha particle carries more kinetic energy; with the masses taken proportional to the mass "
                 "numbers, the alpha particle's share of the total is the daughter's mass number divided by the sum of the two."),
            Step("Ka", "Conservation of energy for the products, K_alpha + K_daughter = Q, combined with the share found from momentum conservation",
                 "The total kinetic energy is Q, and the alpha particle takes the fraction found above, so its kinetic energy is Q times that fraction."),
        ),
        check="The alpha particle is much lighter than the daughter, so it must carry almost all of Q, and its energy must be smaller than Q; "
              "the daughter's share Q minus K_alpha together with K_alpha must add up to Q."),
    "S86": Plan(
        approach="The speed follows from the Lorentz factor. Add the rest energy to the kinetic energy to get the total energy, divide by "
                 "the rest energy to get gamma, invert the definition of gamma to get the speed as a fraction of c, and multiply by c.",
        steps=(
            Step("Etot", "Relativistic energy: the total energy is the sum of the rest energy and the kinetic energy, E = K + m c squared",
                 "The kinetic energy and the rest energy are both given, and the total energy is the quantity that is linked to the speed through gamma."),
            Step("gamma", "Relativistic total energy, E = gamma m c squared, so gamma = E / (m c squared)",
                 "Dividing the total energy by the rest energy gives the Lorentz factor, which carries the information about the speed."),
            Step("beta", "Definition of the Lorentz factor, gamma = 1 / sqrt(1 - beta squared), inverted: beta = sqrt(1 - 1 / gamma squared)",
                 "The Lorentz factor is known and the speed fraction is the unknown, so we invert the definition."),
            Step("v", "Definition of the speed fraction, v = beta c",
                 "Multiplying the speed fraction by the stated value of the speed of light gives the speed in km/s."),
        ),
        check="The speed must stay below c and below the Newtonian value c sqrt(2 K / E0); the two agree when K is much smaller than the "
              "rest energy, and for K much larger than the rest energy the speed must approach c."),
}

LEVELS = {
    "S81": "intro_university",
    "S82": "intro_university",
    "S83": "high_school",
    "S84": "high_school",
    "S85": "upper_university",
    "S86": "intro_university",
}

TOPICS = {
    "S81": "time dilation: proper lifetime from the laboratory flight distance",
    "S82": "Wien displacement scaling and photon energy at the spectral peak",
    "S83": "binding energy per nucleon from the mass defect",
    "S84": "radiocarbon dating from the remaining activity",
    "S85": "alpha decay: energy release from mass excesses and sharing with the recoil",
    "S86": "relativistic kinetic energy and the speed of a proton",
}
