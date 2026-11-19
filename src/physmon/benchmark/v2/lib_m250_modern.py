"""M250 phase 2, batch modern: ten NEW modern-physics structures, S241 to S250 (exploration pool), and their gold plans.

Authority: plan of record v2.2 (`docs/proposals/PhysMon_Research_v2.tex`, "Dataset plan"), the dataset admission standard
(`docs/registry/v2/g1/dataset_admission_standard.md`) and plan revision v2.2 section G. Each structure is a typed graph with an
independently coded numeric solver (a root finder for the crossing of two decays, the orbit equation of the Coulomb problem, the
linear system of energy and momentum conservation, the collinear energy-momentum balance of a decay in flight, a numerical
quadrature of the stopping process, a ray-by-ray attenuation product), four numeric instantiations and a relevant edit that moves the
answer.

The situations are new against dataset v1 (S01-S95), every `library*` / `lib_*` structure (including S71-S79 and S81-S86) and the other M250
ranges: the current of a vacuum photocell, the crossing time of two radioactive decays seen by one counter, the closest approach of an
alpha particle at a given scattering angle, positron annihilation in flight, the number of photons that stop an atom, a two-layer gamma
shield, the speed gained by a mirror pushed by an oblique beam of light, the proton precession frequency in a magnetic field, the
relativistic cyclotron frequency and the Bragg angle of relativistic electrons.

Every answer-deciding condition (initial and boundary conditions, the governing model where models compete) is stated in the base
text. `PLANS` holds the gold solving technique for each structure, `LEVELS` and `TOPICS` label them. These are agent-authored
candidates: solver-certified, not expert-reviewed.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.integrate import quad
from scipy.optimize import brentq

from physmon.benchmark.v2.graph import Assumption, Structure
from physmon.benchmark.v2.library import _co, _in, _spec
from physmon.benchmark.v2.trace import Plan, Step

# --- solvers (independent routes; SI inputs in input-node order) --------------------------------------------------------------------


def _solve_photocell_current(lam, power, eta, hc, e):
    # Electrons released per joule of light at this wavelength, then the charge per second delivered by the stated power.
    photon_energy_ev = hc / lam / e
    electrons_per_joule = eta / (photon_energy_ev * e)
    return float(power * electrons_per_joule * e)


def _solve_equal_count_rates(a1, a2, t1, t2):
    # The time at which the two exponential count rates cross, found with a bracketing root finder on the difference of the rates.
    l1, l2 = math.log(2.0) / t1, math.log(2.0) / t2

    def difference(t):
        return a1 * math.exp(-l1 * t) - a2 * math.exp(-l2 * t)

    high = 1.0 / l2
    while difference(high) > 0.0:
        high *= 2.0
    return float(brentq(difference, 0.0, high, xtol=1e-12, rtol=1e-14))


def _solve_closest_approach(z, k, theta, e, eps0):
    # Energy and angular momentum conservation in the Coulomb field: r^2 - D r - b^2 = 0 at the turning point, with the head-on distance
    # D = 2 Z e^2 / (4 pi eps0 K) and the impact parameter b = (D / 2) cot(theta / 2) of the hyperbolic orbit that deflects by theta.
    head_on = 2.0 * z * e * e / (4.0 * math.pi * eps0 * k)
    impact = head_on / 2.0 / math.tan(theta / 2.0)
    return float(np.max(np.real(np.roots([1.0, -head_on, -impact * impact]))))


def _solve_forward_photon(kinetic, mc2):
    # Energy and momentum conservation for the two collinear photons as a 2x2 linear system in (E_forward, E_backward); the positron
    # momentum comes from the invariant (K + m c^2)^2 - (m c^2)^2.
    momentum = math.sqrt((kinetic + mc2) ** 2 - mc2 ** 2)
    matrix = np.array([[1.0, 1.0], [1.0, -1.0]])
    rhs = np.array([kinetic + 2.0 * mc2, momentum])
    return float(np.linalg.solve(matrix, rhs)[0])


def _solve_stopping_photons(mass, lam, kinetic, h):
    # Follow the atom absorption by absorption: each photon removes h / (m lam) from its speed, until it has stopped.
    step = h / lam / mass
    count = 0
    speed = math.sqrt(2.0 * kinetic / mass)
    block = 1000
    while speed > block * step:  # whole blocks of a thousand photons first, then single photons
        speed -= block * step
        count += block
    while speed > 0.5 * step:
        speed -= step
        count += 1
    return float(count + speed / step)  # the fractional part of the last absorption, so that the count is continuous


def _solve_shield_thickness(muc, tc, mupb, factor):
    # Walk the intensity through the concrete (a product of exponential factors) and then find the lead thickness at which the
    # transmitted fraction equals 1 / factor, with a root finder on the logarithm of the transmitted fraction.
    through_concrete = math.exp(-muc * tc)

    def log_fraction(t):
        return math.log(through_concrete * math.exp(-mupb * t)) + math.log(factor)

    return float(brentq(log_fraction, 0.0, 3.0, xtol=1e-14, rtol=1e-14))


def _solve_mirror_speed(intensity, reflectivity, theta, area, mass, duration, c):
    # Momentum balance per area gives the normal force: the absorbed part gives up its normal momentum flux and the specularly reflected
    # part reverses it. The mirror then accelerates from rest along its rail; the speed is the time integral of the constant acceleration.
    normal_flux = intensity * math.cos(theta) / c * math.cos(theta)
    force = area * ((1.0 - reflectivity) * normal_flux + reflectivity * 2.0 * normal_flux)
    speed, _ = quad(lambda t: force / mass, 0.0, duration, epsabs=1e-14, epsrel=1e-13)
    return float(speed)


def _solve_proton_precession(b, g, e, mp):
    # The precession angular frequency from the torque on the moment and the spin angular momentum, omega = (g e / 2 m) B, then f.
    gyro = g * e / (2.0 * mp)
    return float(gyro * b / (2.0 * math.pi))


def _solve_cyclotron_frequency(kinetic, b, m, e, c):
    # Gamma from the relativistic energy, then the speed from beta, the radius from p = gamma m v = e B r, and f = v / (2 pi r).
    gamma = 1.0 + kinetic / (m * c * c)
    beta = math.sqrt(1.0 - 1.0 / (gamma * gamma))
    speed = beta * c
    radius = gamma * m * speed / (e * b)
    return float(speed / (2.0 * math.pi * radius))


def _solve_bragg_angle(kinetic, mc2, hc, d):
    # Wavelength from the relativistic momentum written through gamma and beta, then Bragg's law with a root finder on theta.
    gamma = 1.0 + kinetic / mc2
    beta = math.sqrt(1.0 - 1.0 / (gamma * gamma))
    momentum_c = gamma * beta * mc2
    lam = hc / momentum_c
    target = lam / (2.0 * d)
    return float(brentq(lambda theta: math.sin(theta) - target, 0.0, math.pi / 2.0, xtol=1e-16, rtol=1e-15))


# --- structures ---------------------------------------------------------------------------------------------------------------------


def s241_photocell_current() -> Structure:
    return Structure(
        "S241", "Current of a vacuum photocell in steady light", "modern physics", "photocell_current_photon_flux_efficiency",
        (_in("lam", "length", "nm", "wavelength of the light", 400.0, (350.0, 620.0)),
         _in("P", "power", "mW", "power of the light that falls on the cathode", 5.0, (0.5, 60.0)),
         _in("eta", "dimensionless", "1", "probability that one incident photon releases one collected electron", 0.003, (0.0003, 0.05)),
         _in("hc", "energy_length", "eV*nm", "product of the Planck constant and the speed of light, a stated constant", 1240.0, (1230.0, 1250.0),
             provenance="assumed"),
         _in("e", "charge", "C", "elementary charge, a stated constant", 1.602e-19, (1.60e-19, 1.61e-19), provenance="assumed"),
         _co("Eph", "energy", "eV", "energy of one photon of the light", "hc/lam"),
         _co("Ndot", "rate", "1/s", "number of photons that fall on the cathode per second", "P/Eph"),
         _co("I", "current", "μA", "current of released electrons that reaches the anode", "eta*e*Ndot")),
        "I",
        (Assumption("A-saturation", "The anode voltage is high enough that every released electron is collected, so the current does not depend on it.",
                    "boundary_condition", ("eta",)),
         Assumption("A-photon", "The light is monochromatic, every photon of it has the energy hc / lam, and the stated power is the power that reaches "
                                "the cathode.", "modelling", ("lam", "P")),
         Assumption("A-constants", "hc and e are the stated constants.", "modelling", ("hc", "e"))),
        _spec("A vacuum photocell has a metal cathode behind a window. Light of wavelength {lam} nm and power {P} mW falls on the cathode, and "
              "each photon that reaches the cathode releases one electron with a probability of {eta}. The anode voltage is high enough that every "
              "released electron is collected, and the window passes all of the light to the cathode. Take hc = {hc} eV nm and e = {e} C.",
              "What current flows through the photocell?", "current through the photocell", "μA",
              "A separate photocell B in another apparatus carries a current of {v} {u}, but it is unrelated to this cell.",
              "A reference photocell B carries a current of {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the photocell current.", "W", equivalent="nA",
              formats={"e": ".4g", "eta": ".4g"}),
        ("P", 1.5), _solve_photocell_current, 5,
        "the electrons released per joule of light written through the photon energy in electron volts, times the power and the elementary charge",
        solver_rel_tol=1e-9,
        instances=({"lam": 400.0, "P": 5.0, "eta": 0.003, "hc": 1240.0, "e": 1.602e-19},
                   {"lam": 450.0, "P": 12.0, "eta": 0.0012, "hc": 1240.0, "e": 1.602e-19},
                   {"lam": 360.0, "P": 2.4, "eta": 0.015, "hc": 1230.0, "e": 1.609e-19},
                   {"lam": 520.0, "P": 30.0, "eta": 0.0008, "hc": 1250.0, "e": 1.602e-19}))


def s242_equal_count_rates() -> Structure:
    return Structure(
        "S242", "Time at which two decaying isotopes give equal count rates", "nuclear physics", "two_exponential_decay_crossing_time",
        (_in("A1", "activity", "Bq", "activity of isotope 1 at the moment of preparation", 9000.0, (1000.0, 25000.0)),
         _in("A2", "activity", "Bq", "activity of isotope 2 at the moment of preparation", 400.0, (50.0, 900.0)),
         _in("T1", "time", "h", "half-life of isotope 1", 6.0, (1.0, 15.0)),
         _in("T2", "time", "h", "half-life of isotope 2", 72.0, (20.0, 250.0)),
         _co("lam1", "rate", "1/s", "decay constant of isotope 1", "log(2)/T1"),
         _co("lam2", "rate", "1/s", "decay constant of isotope 2", "log(2)/T2"),
         _co("t", "time", "h", "time from the preparation at which the two count rates are equal", "log(A1/A2)/(lam1 - lam2)")),
        "t",
        (Assumption("A-independent", "The two isotopes decay independently: neither is produced by the decay of the other, and each decays "
                                      "by the exponential law from its stated initial activity.", "modelling", ("A1", "A2", "T1", "T2")),
         Assumption("A-counter", "The counter detects a decay of either isotope with the same efficiency, which does not change in time, so the "
                                 "count rates are in the ratio of the activities.", "boundary_condition", ("A1", "A2"))),
        _spec("A radioactive sample is made from a batch of a short-lived isotope, with a half-life of {T1} h and an activity of {A1} Bq at "
              "the moment of preparation, and a batch of a longer-lived isotope, with a half-life of {T2} h and an activity of {A2} Bq at "
              "that moment. The two isotopes decay independently, and neither is produced by the decay of the other. A counter detects the "
              "decays of both isotopes in the sample, and only those, with the same efficiency, and background counts are negligible.",
              "How long after the moment of preparation do the two isotopes give equal count rates?",
              "time at which the two count rates are equal", "h",
              "A separate sample B in another laboratory has equal count rates for its two isotopes after {v} {u}, but it is unrelated to this sample.",
              "A reference sample B gives equal count rates after {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the decay.", "W", equivalent="min"),
        ("A2", 1.5), _solve_equal_count_rates, 4,
        "the crossing of the two exponential count rates found with a bracketing root finder on their difference",
        solver_rel_tol=1e-9,
        instances=({"A1": 2400.0, "A2": 500.0, "T1": 6.0, "T2": 72.0}, {"A1": 6000.0, "A2": 350.0, "T1": 3.0, "T2": 48.0},
                   {"A1": 3100.0, "A2": 200.0, "T1": 12.0, "T2": 168.0}, {"A1": 7500.0, "A2": 600.0, "T1": 2.5, "T2": 30.0}))


def s243_closest_approach_at_angle() -> Structure:
    return Structure(
        "S243", "Closest approach of an alpha particle scattered through a given angle", "nuclear physics",
        "rutherford_closest_approach_at_scattering_angle",
        (_in("Z", "count", "1", "number of protons in a nucleus of the foil", 79.0, (70.0, 92.0)),
         _in("K", "energy", "MeV", "kinetic energy of an alpha particle when it leaves the source", 5.0, (3.0, 9.0)),
         _in("theta", "dimensionless", "deg", "angle through which the alpha particle is scattered", 90.0, (30.0, 170.0)),
         _in("e", "charge", "C", "elementary charge, a stated constant", 1.602e-19, (1.60e-19, 1.61e-19), provenance="assumed"),
         _in("eps0", "permittivity", "F/m", "permittivity of free space, a stated constant", 8.854e-12, (8.80e-12, 8.90e-12), provenance="assumed"),
         _co("ke2", "energy_length", "eV*nm", "Coulomb constant times the elementary charge squared", "e**2/(4*pi*eps0)"),
         _co("D", "length", "fm", "distance of closest approach in a head-on collision", "2*Z*ke2/K"),
         _co("s", "dimensionless", "1", "sine of half the scattering angle", "sin(theta/2)"),
         _co("d", "length", "fm", "distance of closest approach of the scattered alpha particle", "D/2*(1 + 1/s)")),
        "d",
        (Assumption("A-coulomb", "The force between an alpha particle and a nucleus is purely electrostatic between point charges 2e and Ze.",
                    "modelling", ("Z", "K")),
         Assumption("A-fixed", "The nucleus is much heavier than the alpha particle and stays at rest, and each alpha particle is scattered "
                               "only once, by a single nucleus.", "boundary_condition", ("theta",)),
         Assumption("A-constants", "e and eps0 are the stated constants, and the motion is non-relativistic.", "modelling", ("e", "eps0"))),
        _spec("Alpha particles leave a source with a kinetic energy of {K} MeV and are directed at a thin foil of a single heavy element, each "
              "nucleus of which has {Z} protons. The nuclei are much heavier than an alpha particle and stay at rest, the force between an "
              "alpha particle and a nucleus is purely electrostatic, and each alpha particle is scattered only once. The electrons of the atoms do "
              "not affect the motion, and the motion is non-relativistic. One alpha particle is scattered through an angle of {theta} degrees. Take e = {e} C and the permittivity of free space to be {eps0} F/m.",
              "What is the smallest distance between this alpha particle and the centre of the nucleus that scatters it?",
              "distance of closest approach", "fm",
              "A separate nucleus B in another foil has a closest approach of {v} {u}, but it is unrelated to this nucleus.",
              "A reference alpha particle B comes within {v} {u} of its nucleus.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the scattering.", "W", equivalent="pm",
              formats={"e": ".4g", "eps0": ".4g"}),
        ("K", 1.25), _solve_closest_approach, 5,
        "energy and angular momentum conservation at the turning point of the orbit as a quadratic for the radius, with the impact parameter from the deflection angle",
        solver_rel_tol=1e-9,
        instances=({"Z": 79.0, "K": 5.0, "theta": 90.0, "e": 1.602e-19, "eps0": 8.854e-12},
                   {"Z": 82.0, "K": 7.7, "theta": 60.0, "e": 1.602e-19, "eps0": 8.854e-12},
                   {"Z": 78.0, "K": 4.2, "theta": 140.0, "e": 1.609e-19, "eps0": 8.85e-12},
                   {"Z": 83.0, "K": 6.0, "theta": 120.0, "e": 1.602e-19, "eps0": 8.854e-12}))


def s244_annihilation_in_flight() -> Structure:
    return Structure(
        "S244", "Energy of the forward photon from positron annihilation in flight", "special relativity",
        "positron_annihilation_in_flight_forward_photon",
        (_in("K", "energy", "keV", "kinetic energy of the positron when it leaves the source", 800.0, (50.0, 5000.0)),
         _in("mc2", "energy", "keV", "rest energy of the electron and of the positron, a stated constant", 511.0, (505.0, 517.0), provenance="assumed"),
         _co("Etot", "energy", "keV", "total energy of the positron and the electron", "K + 2*mc2"),
         _co("pc", "energy", "keV", "momentum of the positron times the speed of light", "sqrt(K**2 + 2*K*mc2)"),
         _co("Ef", "energy", "keV", "energy of the photon that travels forward", "(Etot + pc)/2")),
        "Ef",
        (Assumption("A-target", "The electron is free and at rest, and the positron and the electron annihilate into exactly two photons.",
                    "boundary_condition", ("K",)),
         Assumption("A-collinear", "The two photons are emitted along the line of motion of the positron, one forward and one backward.",
                    "boundary_condition", ("K",)),
         Assumption("A-rest", "The rest energies of the electron and the positron are the stated constant.", "modelling", ("mc2",))),
        _spec("Positrons leave a source with a kinetic energy of {K} keV. One positron annihilates with a free electron that is at rest, and "
              "the annihilation produces exactly two photons, which travel along the line of motion of the positron, one forward (in the "
              "direction in which the positron moves) and one backward. No other particle is produced. Take the rest energy of the electron and of the positron to be mc² = {mc2} keV.",
              "What is the energy of the photon that travels forward?", "energy of the forward photon", "keV",
              "A separate gamma source B in another laboratory emits photons of energy {v} {u}, but it is unrelated to this annihilation.",
              "A reference photon B from another annihilation has an energy of {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the annihilation.", "W", equivalent="MeV"),
        ("K", 1.5), _solve_forward_photon, 2,
        "energy and momentum conservation for the two collinear photons as a 2 by 2 linear system, with the positron momentum from the energy-momentum invariant",
        solver_rel_tol=1e-9,
        instances=({"K": 800.0, "mc2": 511.0}, {"K": 300.0, "mc2": 511.0}, {"K": 1500.0, "mc2": 510.99}, {"K": 2600.0, "mc2": 511.0}))


def s245_photons_to_stop_atom() -> Structure:
    return Structure(
        "S245", "Number of photon absorptions that stop an atom in a laser beam", "atomic physics", "laser_slowing_photon_count",
        (_in("M", "mass", "u", "mass of one atom", 23.0, (6.0, 140.0)),
         _in("lam", "length", "nm", "wavelength of the laser light", 589.0, (300.0, 1100.0)),
         _in("K", "energy", "eV", "kinetic energy of one atom when it enters the laser beam", 0.0763, (0.005, 0.5)),
         _in("h", "action", "J*s", "Planck constant, a stated constant", 6.626e-34, (6.62e-34, 6.63e-34), provenance="assumed"),
         _co("pph", "momentum", "kg*m/s", "momentum of one photon of the laser light", "h/lam"),
         _co("v0", "speed", "m/s", "speed of the atoms when they enter the laser beam", "sqrt(2*K/M)"),
         _co("dv", "speed", "m/s", "decrease of the speed of the atom in one absorption", "pph/M"),
         _co("N", "dimensionless", "1", "number of photons that the atom absorbs before it stops", "v0/dv")),
        "N",
        (Assumption("A-resonance", "The laser light is directed against the motion of the atoms and its frequency is swept so that each atom stays in "
                                   "resonance and keeps absorbing photons until it has stopped.", "boundary_condition", ("K",)),
         Assumption("A-recoil", "Each absorbed photon is re-emitted in a random direction, so the recoil of the emitted photons averages to zero; the "
                                "speed is small enough for the motion to be non-relativistic.", "modelling", ("M", "lam")),
         Assumption("A-h", "h is the stated constant.", "modelling", ("h",))),
        _spec("Atoms of mass {M} u move in a beam, each with a kinetic energy of {K} eV. They meet laser light of wavelength {lam} nm that is directed against their "
              "motion. The frequency of the light is swept so that each atom stays in resonance and keeps absorbing photons until it has stopped. "
              "Each absorbed photon is re-emitted in a random direction, so the recoil from the emitted photons averages to zero. The motion is along the beam "
              "and non-relativistic, and no other force acts on the atoms. Take h = {h} J s.",
              "How many photons must one atom absorb to be brought to rest?", "number of photons absorbed before the atom stops", "1",
              "A separate atom B in another experiment absorbs {v} photons, but it is unrelated to this atom.",
              "A reference atom B absorbs {v} photons before it stops.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the slowing of the atoms.", "W",
              formats={"h": ".4g"}),
        ("K", 1.5), _solve_stopping_photons, 4,
        "the atom followed photon by photon, removing h / (M lam) from its speed per absorption until it has stopped, in blocks and then singly",
        solver_rel_tol=1e-9,
        instances=({"M": 23.0, "lam": 589.0, "K": 0.0763, "h": 6.626e-34}, {"M": 87.0, "lam": 780.0, "K": 0.0406, "h": 6.626e-34},
                   {"M": 39.0, "lam": 767.0, "K": 0.052, "h": 6.63e-34}, {"M": 133.0, "lam": 852.0, "K": 0.0276, "h": 6.626e-34}))


def s246_gamma_shield_lead_thickness() -> Structure:
    return Structure(
        "S246", "Lead thickness that completes a gamma shield behind a concrete wall", "nuclear physics",
        "two_layer_gamma_attenuation_thickness",
        (_in("muc", "attenuation_coefficient", "1/m", "linear attenuation coefficient of concrete for the gamma rays", 15.0, (8.0, 18.0)),
         _in("tc", "length", "cm", "thickness of the concrete wall", 30.0, (10.0, 40.0)),
         _in("mupb", "attenuation_coefficient", "1/m", "linear attenuation coefficient of lead for the gamma rays", 80.0, (50.0, 120.0)),
         _in("F", "dimensionless", "1", "factor by which the shield must reduce the intensity", 10000.0, (8000.0, 1000000.0)),
         _co("xc", "dimensionless", "1", "attenuation exponent of the concrete wall", "muc*tc"),
         _co("L", "dimensionless", "1", "attenuation exponent that the whole shield must provide", "log(F)"),
         _co("tpb", "length", "cm", "thickness of the lead sheet", "(L - xc)/mupb")),
        "tpb",
        (Assumption("A-narrow", "The gamma rays form a narrow beam and each interaction removes a photon from it, so the transmitted intensity falls "
                                "exponentially with the thickness of each material.", "modelling", ("muc", "mupb")),
         Assumption("A-order", "The beam passes through the concrete first and then through the lead; the attenuation coefficients are those for the "
                               "energy of the gamma rays.", "boundary_condition", ("tc",))),
        _spec("A narrow beam of gamma rays passes through a concrete wall of thickness {tc} cm and then through a sheet of lead. Each material "
              "removes photons from the beam, and the intensity falls exponentially with the thickness of each. For these gamma rays the linear "
              "attenuation coefficient is {muc} m⁻¹ for concrete and {mupb} m⁻¹ for lead. The intensity behind the lead is to be {F} times smaller "
              "than the intensity that the beam would have without the wall and the sheet. Photons that are scattered out of the beam are lost "
              "to it, and the coefficients are those for the energy of these gamma rays.",
              "How thick must the lead sheet be?", "thickness of the lead sheet", "cm",
              "A separate shield B in another building has a lead sheet of thickness {v} {u}, but it is unrelated to this shield.",
              "A reference shield B uses a lead sheet of thickness {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the shielding.", "W", equivalent="mm",
              formats={"F": ".6g"}),
        ("tc", 0.7), _solve_shield_thickness, 4,
        "the beam followed through the concrete as an exponential factor, then the lead thickness at which the transmitted fraction equals 1 / F found with a root finder",
        solver_rel_tol=1e-9,
        instances=({"muc": 15.0, "tc": 30.0, "mupb": 80.0, "F": 10000.0}, {"muc": 12.0, "tc": 20.0, "mupb": 100.0, "F": 50000.0},
                   {"muc": 16.5, "tc": 25.0, "mupb": 65.0, "F": 9000.0}, {"muc": 9.5, "tc": 38.0, "mupb": 110.0, "F": 100000.0}))


def s247_radiation_pressure_oblique_mirror() -> Structure:
    return Structure(
        "S247", "Speed gained by a mirror pushed along its rail by an oblique beam", "modern physics",
        "photon_momentum_radiation_force_oblique_mirror_speed",
        (_in("I", "intensity", "W/m^2", "intensity of the beam, measured perpendicular to the beam", 1400.0, (100.0, 5000.0)),
         _in("Rf", "dimensionless", "1", "fraction of the incident light that the mirror reflects specularly", 0.9, (0.1, 0.99)),
         _in("theta", "dimensionless", "deg", "angle between the beam and the normal to the mirror", 30.0, (0.0, 75.0)),
         _in("A", "area", "m^2", "area of the mirror", 100.0, (20.0, 400.0)),
         _in("m", "mass", "kg", "mass of the mirror", 0.5, (0.1, 5.0)),
         _in("t", "time", "h", "time for which the beam acts on the mirror", 24.0, (1.0, 72.0)),
         _in("c", "speed", "km/s", "speed of light in vacuum, a stated constant", 299800.0, (299000.0, 300500.0), provenance="assumed"),
         _co("fac", "dimensionless", "1", "geometric and reflection factor of the normal momentum transfer", "(1 + Rf)*cos(theta)**2"),
         _co("p0", "pressure", "Pa", "radiation pressure of this beam on a perfectly absorbing surface perpendicular to it", "I/c"),
         _co("p", "pressure", "Pa", "radiation pressure on the mirror, normal to its surface", "fac*p0"),
         _co("F", "force", "N", "normal force of the light on the mirror", "p*A"),
         _co("a", "acceleration", "m/s^2", "acceleration of the mirror along its rail", "F/m"),
         _co("v", "speed", "m/s", "speed of the mirror after the stated time", "a*t")),
        "v",
        (Assumption("A-reflection", "The part of the light that is not reflected is absorbed, and the reflected part leaves in the direction of "
                                    "specular reflection.", "modelling", ("Rf",)),
         Assumption("A-rail", "The mirror starts at rest and can move only along a frictionless rail that is normal to its surface, so that only the "
                              "normal component of the force accelerates it; its speed stays far below c, so the intensity and the angle do not change.",
                    "boundary_condition", ("m", "t")),
         Assumption("A-beam", "The beam is uniform, its intensity is measured perpendicular to its direction, and it illuminates the whole mirror.",
                    "boundary_condition", ("I", "theta", "A")),
         Assumption("A-c", "c is the stated constant.", "modelling", ("c",))),
        _spec("A uniform beam of light of intensity {I} W/m², measured perpendicular to the beam, illuminates the whole of a plane mirror of "
              "area {A} m² and mass {m} kg. The beam makes an angle of {theta} degrees with the normal to the mirror. The mirror reflects a "
              "fraction {Rf} of the incident light specularly and absorbs the rest. The mirror starts at rest and can move only along a "
              "frictionless rail that is normal to its surface. Its speed stays far below c, the beam acts for {t} h, the mirror is in vacuum, and no other force acts along the rail. Heating of the mirror is neglected. Take c = {c} km/s.",
              "What speed does the mirror reach along the rail?", "speed of the mirror along the rail", "m/s",
              "A separate light sail B in another experiment reaches a speed of {v} {u}, but it is unrelated to this mirror.",
              "A reference mirror B reaches a speed of {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the motion of the mirror.", "W", equivalent="cm/s",
              formats={"Rf": ".4g"}),
        ("I", 1.5), _solve_mirror_speed, 7,
        "the momentum balance per unit area (absorbed part plus twice the reflected part, in the normal component) and the speed as the time integral of the constant acceleration",
        solver_rel_tol=1e-9,
        instances=({"I": 1400.0, "Rf": 0.9, "theta": 30.0, "A": 100.0, "m": 0.5, "t": 24.0, "c": 299800.0},
                   {"I": 3000.0, "Rf": 0.6, "theta": 45.0, "A": 250.0, "m": 2.0, "t": 12.0, "c": 299800.0},
                   {"I": 800.0, "Rf": 0.97, "theta": 10.0, "A": 60.0, "m": 0.3, "t": 48.0, "c": 300000.0},
                   {"I": 4000.0, "Rf": 0.35, "theta": 60.0, "A": 300.0, "m": 4.0, "t": 6.0, "c": 299800.0}))


def s248_proton_precession_frequency() -> Structure:
    return Structure(
        "S248", "Precession frequency of the spin of a free proton in a magnetic field", "modern physics", "proton_spin_larmor_frequency",
        (_in("B", "magnetic_field", "mT", "magnetic field at the sample", 350.0, (50.0, 2000.0)),
         _in("gp", "dimensionless", "1", "g-factor of the proton, a stated constant", 5.586, (5.5, 5.7), provenance="assumed"),
         _in("e", "charge", "C", "elementary charge, a stated constant", 1.602e-19, (1.60e-19, 1.61e-19), provenance="assumed"),
         _in("mp", "mass", "kg", "mass of the proton, a stated constant", 1.673e-27, (1.67e-27, 1.68e-27), provenance="assumed"),
         _co("wc", "angular_frequency", "rad/s", "cyclotron angular frequency e B / m of a charge e and mass m", "e*B/mp"),
         _co("wL", "angular_frequency", "rad/s", "angular frequency of the precession of the proton spin", "gp*wc/2"),
         _co("f", "frequency", "MHz", "frequency of the precession of the proton spin", "wL/(2*pi)")),
        "f",
        (Assumption("A-free", "The proton is free and is the only magnetic moment that matters; its magnetic moment is g e / (2 m) times its spin "
                              "angular momentum, and the field is uniform and constant.", "modelling", ("B", "gp")),
         Assumption("A-constants", "g, e and the proton mass are the stated constants.", "modelling", ("gp", "e", "mp"))),
        _spec("The spin of a free proton precesses about a uniform, constant magnetic field of {B} mT at the sample, and no other magnetic field acts there. The magnetic moment of the "
              "proton is g e divided by twice m, times its spin angular momentum, where m is its mass and e is the elementary charge. Take g = {gp}, "
              "e = {e} C and m = {mp} kg.",
              "At what frequency does the spin of the proton precess?", "precession frequency of the proton spin", "MHz",
              "A separate radio transmitter B in another building runs at {v} {u}, but it is unrelated to this proton.",
              "A reference proton B precesses at {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the precession.", "W", equivalent="kHz",
              formats={"e": ".4g", "mp": ".4g"}),
        ("B", 1.5), _solve_proton_precession, 4,
        "the precession angular frequency from the torque on the moment and the spin angular momentum, omega = (g e / 2 m) B, then divided by two pi",
        solver_rel_tol=1e-9,
        instances=({"B": 350.0, "gp": 5.586, "e": 1.602e-19, "mp": 1.673e-27}, {"B": 250.0, "gp": 5.586, "e": 1.602e-19, "mp": 1.673e-27},
                   {"B": 150.0, "gp": 5.59, "e": 1.609e-19, "mp": 1.675e-27}, {"B": 450.0, "gp": 5.586, "e": 1.602e-19, "mp": 1.673e-27}))


def s249_relativistic_cyclotron_frequency() -> Structure:
    return Structure(
        "S249", "Orbital frequency of a relativistic proton in a uniform magnetic field", "special relativity",
        "relativistic_cyclotron_frequency",
        (_in("K", "energy", "MeV", "kinetic energy of the proton when it is injected", 100.0, (5.0, 500.0)),
         _in("B", "magnetic_field", "T", "magnetic field", 1.2, (0.3, 3.0)),
         _in("m", "mass", "kg", "mass of the proton, a stated constant", 1.673e-27, (1.67e-27, 1.68e-27), provenance="assumed"),
         _in("e", "charge", "C", "elementary charge, a stated constant", 1.602e-19, (1.60e-19, 1.61e-19), provenance="assumed"),
         _in("c", "speed", "km/s", "speed of light in vacuum, a stated constant", 299800.0, (299000.0, 300500.0), provenance="assumed"),
         _co("gamma", "dimensionless", "1", "Lorentz factor of the proton", "1 + K/(m*c**2)"),
         _co("w", "angular_frequency", "rad/s", "angular frequency of the orbit", "e*B/(gamma*m)"),
         _co("f", "frequency", "MHz", "orbital frequency of the proton", "w/(2*pi)")),
        "f",
        (Assumption("A-field", "The magnetic field is uniform and constant, the proton moves perpendicular to it, and no electric field acts after "
                               "injection; radiation losses are neglected.", "boundary_condition", ("K", "B")),
         Assumption("A-rel", "The motion is described by relativistic mechanics, with the momentum gamma m v.", "modelling", ("K", "m", "c")),
         Assumption("A-constants", "The proton mass, the elementary charge and the speed of light are the stated constants.", "modelling",
                    ("m", "e", "c"))),
        _spec("Protons are injected, perpendicular to a uniform, constant magnetic field of {B} T, with a kinetic energy of {K} MeV, and then "
              "move on circular orbits; no electric field acts on them after injection. Use relativistic mechanics, with momentum γ m v, and neglect radiation. Take m = {m} kg, "
              "e = {e} C and c = {c} km/s.",
              "At what frequency does a proton go round its orbit?", "orbital frequency of the proton", "MHz",
              "A separate oscillator B in another laboratory runs at {v} {u}, but it is unrelated to this proton.",
              "A reference proton B circulates at {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the orbit of the proton.", "W", equivalent="kHz",
              formats={"e": ".4g", "m": ".4g"}),
        ("K", 2.0), _solve_cyclotron_frequency, 5,
        "gamma from the relativistic energy, then the speed, the radius from gamma m v = e B r, and the frequency as v / (2 pi r)",
        solver_rel_tol=1e-9,
        instances=({"K": 100.0, "B": 1.2, "m": 1.673e-27, "e": 1.602e-19, "c": 299800.0},
                   {"K": 30.0, "B": 0.8, "m": 1.673e-27, "e": 1.602e-19, "c": 299800.0},
                   {"K": 250.0, "B": 2.1, "m": 1.675e-27, "e": 1.609e-19, "c": 300000.0},
                   {"K": 400.0, "B": 1.7, "m": 1.673e-27, "e": 1.602e-19, "c": 299800.0}))


def s250_relativistic_electron_bragg_angle() -> Structure:
    return Structure(
        "S250", "Bragg angle of relativistic electrons diffracted from a crystal", "modern physics", "relativistic_electron_bragg_diffraction",
        (_in("K", "energy", "keV", "kinetic energy of an electron when it leaves the gun", 5.0, (1.0, 200.0)),
         _in("mc2", "energy", "keV", "rest energy of the electron, a stated constant", 511.0, (505.0, 517.0), provenance="assumed"),
         _in("hc", "energy_length", "eV*nm", "product of the Planck constant and the speed of light, a stated constant", 1240.0, (1230.0, 1250.0),
             provenance="assumed"),
         _in("d", "length", "pm", "spacing of the lattice planes", 200.0, (150.0, 500.0)),
         _co("pc", "energy", "keV", "momentum of the electron times the speed of light", "sqrt(K**2 + 2*K*mc2)"),
         _co("lam", "length", "pm", "de Broglie wavelength of the electron", "hc/pc"),
         _co("theta", "dimensionless", "deg", "glancing angle of the first-order Bragg reflection", "asin(lam/(2*d))")),
        "theta",
        (Assumption("A-rel", "The momentum of the electron is the relativistic momentum, so that (pc)^2 = K^2 + 2 K mc^2, and the de Broglie wavelength is "
                             "hc / (pc).", "modelling", ("K", "mc2")),
         Assumption("A-bragg", "The first-order reflection from a single family of parallel lattice planes obeys Bragg's law with the stated spacing, "
                               "and the glancing angle is measured from the planes.", "boundary_condition", ("d",)),
         Assumption("A-constants", "hc and the electron rest energy are the stated constants.", "modelling", ("hc", "mc2"))),
        _spec("Electrons leave a gun with a kinetic energy of {K} keV and are diffracted from a crystal in vacuum. One family of parallel lattice planes, "
              "with a spacing of {d} pm, gives a first-order Bragg reflection. Use the relativistic momentum of the electron and its de "
              "Broglie wavelength. Take hc = {hc} eV nm and the electron rest energy mc² = {mc2} keV.",
              "At what glancing angle, measured from the lattice planes, does the first-order reflection occur?",
              "glancing angle of the first-order Bragg reflection", "deg",
              "A separate crystal B in another laboratory reflects at {v} {u}, but it is unrelated to this crystal.",
              "A reference crystal B reflects at an angle of {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the diffraction.", "W", equivalent="rad"),
        ("K", 1.5), _solve_bragg_angle, 4,
        "the wavelength from the relativistic momentum written through gamma and beta, then Bragg's law solved for the angle with a root finder",
        solver_rel_tol=1e-9,
        instances=({"K": 5.0, "mc2": 511.0, "hc": 1240.0, "d": 200.0}, {"K": 12.0, "mc2": 511.0, "hc": 1240.0, "d": 250.0},
                   {"K": 30.0, "mc2": 510.99, "hc": 1230.0, "d": 180.0}, {"K": 2.5, "mc2": 511.0, "hc": 1250.0, "d": 320.0}))


ALL = (s241_photocell_current, s242_equal_count_rates, s243_closest_approach_at_angle, s244_annihilation_in_flight,
       s245_photons_to_stop_atom, s246_gamma_shield_lead_thickness, s247_radiation_pressure_oblique_mirror,
       s248_proton_precession_frequency, s249_relativistic_cyclotron_frequency, s250_relativistic_electron_bragg_angle)


def all_structures() -> list[Structure]:
    return [factory() for factory in ALL]


STRUCTURES: dict[str, Structure] = {s.structure_id: s for s in all_structures()}

# --- gold solution plans ----------------------------------------------------------------------------------------------------------

PLANS: dict[str, Plan] = {
    "S241": Plan(
        approach="The current is the number of electrons collected per second times the elementary charge. Find the energy of one photon, "
                 "then how many photons arrive per second, then multiply by the probability that a photon releases an electron.",
        steps=(
            Step("Eph", "Planck-Einstein relation, E = h c / lambda, with hc given in eV nm",
                 "Light of one wavelength comes in photons of the same energy, and with hc in eV nm and the wavelength in nm the "
                 "energy comes out in electron volts."),
            Step("Ndot", "Power as photon energy times photon rate, P = N_dot E_ph",
                 "The stated power is the energy that reaches the cathode per second, so dividing it by the energy of one photon "
                 "gives the number of photons that arrive per second."),
            Step("I", "Current as charge per second, I = eta e N_dot, with every released electron collected",
                 "A fraction eta of the photons releases one electron each, and the anode voltage is high enough to collect all of "
                 "them, so the current is the electron rate times the elementary charge."),
        ),
        check="Order of magnitude: one milliwatt of visible light is about 10^15 to 10^16 photons per second, and a probability of a few "
              "tenths of a percent gives microamperes. The current is proportional to the power and to the wavelength."),
    "S242": Plan(
        approach="Each isotope's count rate is proportional to its activity, and the counter has the same efficiency for both, so the count "
                 "rates are equal exactly when the activities are equal. Find the two decay constants and solve for the time at which "
                 "the exponentially falling activities cross.",
        steps=(
            Step("lam1", "Relation between half-life and decay constant, lambda = ln 2 / T_half",
                 "The activity of each isotope falls as exp(-lambda t), and the half-life is the time in which it falls to one half, "
                 "so the decay constant of isotope 1 follows from its half-life."),
            Step("lam2", "Relation between half-life and decay constant, lambda = ln 2 / T_half",
                 "The same relation gives the decay constant of isotope 2, which is smaller because its half-life is longer."),
            Step("t", "Exponential decay of each activity, A_i exp(-lambda_i t), set equal: A1 exp(-lam1 t) = A2 exp(-lam2 t)",
                 "Equal count rates mean equal activities. Taking logarithms gives ln(A1 / A2) = (lam1 - lam2) t, so the time is "
                 "ln(A1 / A2) divided by the difference of the decay constants."),
        ),
        check="Limiting cases: if the two activities started equal the time would be zero, and the time grows only logarithmically with the ratio "
              "of the activities. It must be positive, because the short-lived isotope starts higher and falls faster."),
    "S243": Plan(
        approach="The alpha particle moves in the Coulomb field of the nucleus, which stays at rest. Find the head-on closest approach from "
                 "energy conservation, then the closest approach for the stated deflection from the geometry of the hyperbolic orbit.",
        steps=(
            Step("ke2", "Coulomb constant times the elementary charge squared, e^2 / (4 pi eps0)",
                 "The electrostatic potential energy of two point charges is the product of the charges times e^2 / (4 pi eps0) / r, "
                 "and this combination, in eV nm, is the unit in which the potential energy is easiest to compare with a kinetic energy."),
            Step("s", "Half the scattering angle, sin(theta / 2)",
                 "For a Coulomb orbit the closest approach and the impact parameter are fixed by the deflection through the sine "
                 "and cotangent of half the scattering angle."),
            Step("D", "Energy conservation for a head-on collision, K = (2 e)(Z e) / (4 pi eps0 D), so D = 2 Z e^2 / (4 pi eps0 K)",
                 "In a head-on collision the alpha particle stops where its whole kinetic energy has become electrostatic potential "
                 "energy; this distance D is the largest possible closest approach scale of the orbit."),
            Step("d", "Closest approach on the hyperbolic Rutherford orbit, d = (D / 2)(1 + 1 / sin(theta / 2))",
                 "Energy and angular momentum conservation at the turning point give r^2 - D r - b^2 = 0, with the impact parameter "
                 "b = (D / 2) cot(theta / 2); its positive root is the closest approach, which reduces to D for a deflection of 180 degrees."),
        ),
        check="Limiting cases: for theta = 180 degrees the result equals D, the head-on value, and for small angles it grows without bound as "
              "the alpha particle passes far from the nucleus. The result must exceed D / 2, and falls as the energy rises."),
    "S244": Plan(
        approach="Treat the positron and the electron as one system with a definite total energy and momentum, and share these between the "
                 "two photons, one forward and one backward, using conservation of energy and of momentum along the line of motion.",
        steps=(
            Step("Etot", "Energy of the system, the kinetic energy plus the rest energies of the positron and of the electron, K + 2 m c^2",
                 "The electron is at rest and has only its rest energy, and the positron has its rest energy plus its kinetic energy."),
            Step("pc", "Relativistic energy-momentum relation, (K + m c^2)^2 = (pc)^2 + (m c^2)^2, so pc = sqrt(K^2 + 2 K m c^2)",
                 "Only the positron moves, so the total momentum of the system is the momentum of the positron."),
            Step("Ef", "Conservation of energy and of momentum for two collinear photons, E_f + E_b = E_tot and E_f - E_b = pc",
                 "Photons carry momentum equal to their energy over c, forward positive and backward negative; solving the two equations "
                 "gives the forward energy as half the sum of the total energy and pc."),
        ),
        check="Limiting case: with no kinetic energy the photons share the energy equally, 511 keV each. The forward photon always carries more "
              "than the backward one, and the two energies add to the total energy and differ by pc."),
    "S245": Plan(
        approach="Each absorbed photon changes the momentum of the atom by the momentum of the photon, opposite to its motion; the emitted photons "
                 "recoil in random directions and average to zero. Divide the initial speed, found from the kinetic energy, by the change of "
                 "speed per absorption.",
        steps=(
            Step("pph", "Momentum of a photon, p = h / lambda",
                 "Light of wavelength lambda is made of photons that each carry the momentum h / lambda along the beam, and this is "
                 "the momentum that an absorbing atom takes up."),
            Step("v0", "Non-relativistic kinetic energy, K = M v0^2 / 2, so v0 = sqrt(2 K / M)",
                 "The atoms are slow compared with the speed of light, so their speed follows from the kinetic energy and the "
                 "mass, with the energy converted from electron volts to joules and the mass from atomic mass units to kilograms."),
            Step("dv", "Conservation of momentum in one absorption, M dv = p, so dv = p / M",
                 "The atom absorbs the photon completely, so the momentum that it gains is the photon momentum, directed against the "
                 "atom's velocity, and its speed falls by p / M; the non-relativistic relation is accurate for these speeds."),
            Step("N", "Repeated absorption, N dv = v0, so N = v0 / dv",
                 "The speed falls by the same amount in each absorption because the emitted photons average to zero recoil, so the "
                 "number of absorptions that stops the atom is the initial speed divided by the decrease per absorption."),
        ),
        check="Order of magnitude: a sodium atom at several hundred metres per second loses about three centimetres per second per absorption, so it "
              "needs tens of thousands of photons. The number scales with the square root of the kinetic energy and the mass and inversely with the "
              "photon momentum."),
    "S246": Plan(
        approach="The intensity of a narrow beam falls exponentially with the thickness of each material, so the exponents add. Find the exponent "
                 "that the whole shield must supply, subtract the exponent of the concrete, and divide the rest by the coefficient of lead.",
        steps=(
            Step("L", "Required attenuation, I / I0 = 1 / F, so the whole shield needs the exponent ln(F)",
                 "The intensity behind the shield must be smaller than the unshielded intensity by the factor F, so the total exponent "
                 "mu_c t_c + mu_pb t_pb must equal ln(F)."),
            Step("xc", "Exponential attenuation, I = I0 exp(-mu x), applied to the concrete: exponent mu_c t_c",
                 "The concrete wall reduces the intensity by the factor exp(-mu_c t_c); its exponent is the product of the coefficient and "
                 "the thickness, with the thickness in metres."),
            Step("tpb", "Additivity of the exponents of successive layers, mu_pb t_pb = L - x_c",
                 "The concrete already supplies x_c of the required exponent, so the lead must supply the difference, which divided by "
                 "mu_pb is the thickness of the sheet."),
        ),
        check="Limiting cases: a wall that already supplies the whole exponent needs no lead, and a thicker wall needs a thinner sheet. The "
              "source intensity does not appear, because only the ratio of the intensities is fixed."),
    "S247": Plan(
        approach="Light carries momentum, with a flux equal to its intensity over c. The mirror receives the normal part of the momentum that "
                 "it absorbs, and twice that part for the light that it reflects. Find the pressure, then the force on the whole mirror, "
                 "then the acceleration, and integrate it over the time.",
        steps=(
            Step("fac", "Normal momentum transfer per unit area for a reflectivity Rf: absorbed (1 - Rf) plus reflected 2 Rf, so (1 + Rf), "
                        "times cos^2(theta) from the oblique incidence",
                 "The beam's momentum flux per unit area of the mirror is I cos(theta) / c, and only its normal component, a further "
                 "factor cos(theta), is transferred to the mirror, so the geometry gives cos^2(theta); the reflected part reverses the "
                 "normal component, which doubles its transfer."),
            Step("p0", "Momentum flux of a beam of intensity I, I / c",
                 "A beam of intensity I carries I / c of momentum per unit area per second along its direction; this is the pressure on "
                 "a perfectly absorbing surface perpendicular to the beam."),
            Step("p", "Radiation pressure on the mirror, p = (1 + Rf) cos^2(theta) I / c",
                 "Multiplying the pressure on a perfect absorber by the combined reflection and geometry factor gives the normal "
                 "pressure on the partly reflecting mirror."),
            Step("F", "Force from a pressure on an area, F = p A",
                 "The beam illuminates the whole mirror, so the pressure acts on its full area, and the normal force is the product."),
            Step("a", "Newton's second law along the rail, a = F / m",
                 "The rail is frictionless and normal to the mirror, so the normal force is the only force along it and the "
                 "acceleration is constant."),
            Step("v", "Kinematics of constant acceleration from rest, v = a t",
                 "The mirror starts at rest and its speed stays far below c, so the force does not change and the speed is the "
                 "acceleration times the time, with the time converted to seconds."),
        ),
        check="Limiting cases: a perfectly reflecting mirror at normal incidence feels 2 I / c, a perfectly absorbing one I / c, and at grazing "
              "incidence the force falls to zero. Order of magnitude: sunlight, about 1.4 kW/m^2, exerts about 5 micropascals, so a "
              "hundred square metres on a half-kilogram mirror gives some tens of metres per second in a day."),
    "S248": Plan(
        approach="A magnetic moment in a field feels a torque, and because it is tied to the spin angular momentum, the spin precesses about the "
                 "field. The angular frequency of the precession is the gyromagnetic ratio times the field.",
        steps=(
            Step("wc", "Cyclotron angular frequency of a charge e and mass m in a field B, e B / m",
                 "The gyromagnetic ratio of a spin with g-factor g is g e / (2 m), so the quantity e B / m, which is the cyclotron "
                 "angular frequency, is the natural unit for the precession."),
            Step("wL", "Larmor precession, omega = gamma B with gamma = g e / (2 m)",
                 "The torque on the moment is mu B sin(alpha), and the change of the component of the spin perpendicular to the field "
                 "has the same sin(alpha) factor, so the angular frequency of the precession is gamma B for every angle."),
            Step("f", "Relation between angular frequency and frequency, f = omega / (2 pi)",
                 "The question asks for the frequency in megahertz, so the angular frequency is divided by 2 pi."),
        ),
        check="Order of magnitude: for a proton the frequency is about 42.6 MHz per tesla, so a field of a third of a tesla gives about 15 MHz. "
              "The frequency is proportional to the field."),
    "S249": Plan(
        approach="In a magnetic field a charge circles with angular frequency eB divided by its relativistic mass. Find the Lorentz factor from "
                 "the kinetic energy, then the angular frequency, then the frequency.",
        steps=(
            Step("gamma", "Relativistic kinetic energy, K = (gamma - 1) m c^2, so gamma = 1 + K / (m c^2)",
                 "The kinetic energy is the total energy minus the rest energy, and gamma is the ratio of the total energy to the rest energy."),
            Step("w", "Circular motion in a magnetic field with the relativistic momentum, gamma m v = e B r, so w = v / r = e B / (gamma m)",
                 "The magnetic force e v B is perpendicular to the velocity and supplies the centripetal force on the momentum "
                 "gamma m v; the speed cancels from the angular frequency, which depends on the energy only through gamma."),
            Step("f", "Relation between angular frequency and frequency, f = w / (2 pi)",
                 "The orbital frequency is the number of revolutions per second, the angular frequency over 2 pi."),
        ),
        check="Limiting case: for a kinetic energy small compared with the rest energy gamma tends to one and the frequency to the non-relativistic "
              "value e B / (2 pi m), about 15.2 MHz per tesla for a proton. The frequency falls as the energy rises."),
    "S250": Plan(
        approach="The electron behaves as a wave with the de Broglie wavelength h / p. Find the relativistic momentum from the kinetic energy, "
                 "then the wavelength, then the angle at which a family of planes reflects it in first order.",
        steps=(
            Step("pc", "Relativistic energy-momentum relation, (pc)^2 = K^2 + 2 K m c^2",
                 "The total energy is K + m c^2 and E^2 = (pc)^2 + (m c^2)^2; this gives the momentum, as pc in keV, without a "
                 "non-relativistic approximation."),
            Step("lam", "de Broglie relation, lambda = h / p = h c / (pc)",
                 "The wavelength of a particle is Planck's constant over its momentum, and with hc in eV nm and pc in eV it comes out in nm."),
            Step("theta", "Bragg's law for the first order, 2 d sin(theta) = lambda",
                 "Waves reflected from successive planes interfere constructively when the path difference, 2 d sin(theta), is one "
                 "wavelength; the angle is measured from the planes."),
        ),
        check="Limiting cases: for a kinetic energy small compared with 511 keV the relation reduces to lambda = h / sqrt(2 m K), and the angle "
              "falls as the energy rises. The argument of the arcsine must be below one, which it is here by a wide margin."),
}

LEVELS: dict[str, str] = {
    "S241": "intro_university", "S242": "intro_university", "S243": "upper_university", "S244": "upper_university",
    "S245": "intro_university", "S246": "intro_university", "S247": "intro_university", "S248": "intro_university",
    "S249": "upper_university", "S250": "upper_university",
}

TOPICS: dict[str, str] = {
    "S241": "photon flux, photoelectric efficiency and the saturated current of a vacuum photocell",
    "S242": "two independent exponential decays and the time at which their count rates are equal",
    "S243": "Rutherford scattering: distance of closest approach at a given scattering angle",
    "S244": "relativistic kinematics of positron annihilation in flight into two collinear photons",
    "S245": "photon recoil: the number of absorptions that bring an atom to rest in laser slowing",
    "S246": "exponential attenuation of gamma rays in a two-layer shield",
    "S247": "photon momentum, radiation pressure on an oblique partly reflecting mirror and the speed gained along a rail",
    "S248": "Larmor precession of the proton spin and the nuclear magnetic resonance frequency",
    "S249": "relativistic mass increase and the cyclotron frequency of a proton in a magnetic field",
    "S250": "relativistic de Broglie wavelength and first-order Bragg diffraction of electrons",
}
