"""Quantum-mechanics batch of DECOY-v2 structures, S71 to S79, with gold solution plans (Stage 14.19; author agent for quantum mechanics).

Same pattern as `library_c.py`: a typed graph with input and computed nodes, an independently coded numeric solver (a bracketing root
finder, a quadrature, an ODE with an event, an energy-momentum balance), at least four numeric instantiations and a relevant edit that
moves the answer. Constants (hc, hbar c, the electron rest energy, c, the Rydberg energy, k e squared) are stated input nodes with
provenance "assumed" and a narrow domain, written in convenient units (eV nm, keV, km/s) so that no prompt contains scientific notation.

Topics: photoelectric effect, de Broglie wavelength of an accelerated electron, infinite square well, Bohr-atom recoil, Compton
scattering, an uncertainty-principle estimate of a binding energy, rectangular-barrier tunnelling, quantum harmonic oscillator
(molecular vibration) and the X-ray minimum wavelength with Bragg reflection.

Admission status: agent-verified, not expert-reviewed. The module also carries the gold solution plans (`PLANS`) of its structures.
"""

from __future__ import annotations

import math

from scipy.integrate import quad, solve_ivp
from scipy.optimize import brentq

from physmon.benchmark.v2 import dimensions as dm
from physmon.benchmark.v2.graph import Assumption, Structure
from physmon.benchmark.v2.library import _co, _in, _spec
from physmon.benchmark.v2.trace import Plan, Step

EV = dm.UNITS["eV"].factor  # joules per electronvolt (exact SI definition)

# --- solvers (independent routes; SI inputs in node order) -----------------------------------------


def _solve_photoelectron_speed(lam, phi, hc, mc2, c):
    # The speed as the root of (1/2) (mc2 / c^2) v^2 = hc / lam - phi, in electronvolts, with a bracketing root finder.
    excess = (hc / lam - phi) / EV
    mass_ev = mc2 / c ** 2 / EV
    return float(brentq(lambda v: 0.5 * mass_ev * v * v - excess, 0.0, 0.1 * c, xtol=1e-6, rtol=1e-14))


def _solve_de_broglie(kinetic, hc, mc2):
    # The wavelength at which a particle of momentum p = h / lambda has the stated kinetic energy p^2 / (2 m).
    def surplus(lam):
        return ((hc / lam) ** 2 / (2.0 * mc2) - kinetic) / kinetic

    return float(brentq(surplus, 1e-14, 1e-4, xtol=1e-30, rtol=1e-14))


def _solve_well_photon(width, n_i, n_f, hc, mc2):
    # The ground-state energy as the expectation value of p^2 / (2 m) in the normalised state sqrt(2/L) sin(pi x / L), by quadrature;
    # the quantisation condition k_n = n k_1 (n half-wavelengths in the well) then gives every level.
    hbar_c = hc / (2.0 * math.pi)
    integral, _ = quad(lambda u: (math.sqrt(2.0) * math.pi * math.cos(math.pi * u)) ** 2, 0.0, 1.0, epsabs=1e-13, epsrel=1e-13,
                       limit=200)
    e1 = hbar_c ** 2 / (2.0 * mc2 * width ** 2) * integral
    k_ratio_i, k_ratio_f = n_i, n_f
    return float(hc / ((k_ratio_i ** 2 - k_ratio_f ** 2) * e1))


def _solve_bohr_recoil(n_i, n_f, rydberg, mass, c):
    # The level drop as the integral of dE_n / dn = 2 Ry / n^3 between the two levels, then the recoil speed as the root of M v = E / c.
    photon, _ = quad(lambda n: 2.0 * rydberg / n ** 3, n_f, n_i, epsabs=0.0, epsrel=1e-13, limit=200)
    return float(brentq(lambda v: mass * v / (photon / c) - 1.0, 0.0, 1e4, xtol=1e-14, rtol=1e-14))


def _solve_compton_energy(lam0, theta, hc, mc2):
    # Energy and momentum conservation for the scattered photon energy e' (in units of the electron rest energy), by root finding.
    e0 = hc / lam0 / mc2

    def balance(e1):
        electron_momentum_sq = e0 ** 2 + e1 ** 2 - 2.0 * e0 * e1 * math.cos(theta)
        return (e0 - e1) + 1.0 - math.sqrt(1.0 + electron_momentum_sq)

    e1 = brentq(balance, 0.0, e0, xtol=1e-16, rtol=1e-14)
    return float((e0 - e1) * mc2)


def _solve_uncertainty_binding(zeff, hbar_c, mc2, ke2):
    # Minimise E(r) = (hbar c)^2 / (2 mc2 r^2) - Zeff ke2 / r numerically: the root of dE/dr, then the depth of the minimum.
    def slope(r):
        return -(hbar_c ** 2) / (mc2 * r ** 3) + zeff * ke2 / r ** 2

    r_star = brentq(slope, 1e-13, 1e-6, xtol=1e-24, rtol=1e-14)
    return float(-((hbar_c ** 2) / (2.0 * mc2 * r_star ** 2) - zeff * ke2 / r_star))


def _solve_tunnel_width(u0, energy, transmission, mc2, hbar_c):
    # The decay constant as the root of (hbar kappa)^2 / (2 m) = U0 - E, then the width as the root of exp(-2 kappa a) = T.
    deficit = u0 - energy
    kappa = brentq(lambda k: (hbar_c * k) ** 2 / (2.0 * mc2 * deficit) - 1.0, 1e3, 1e14, xtol=1e-6, rtol=1e-14)
    return float(brentq(lambda a: math.exp(-2.0 * kappa * a) / transmission - 1.0, 0.0, 100.0 / kappa, xtol=1e-25, rtol=1e-14))


def _solve_oscillator_level(k, mu, n, hbar_c, c):
    # The classical oscillation period from an ODE with an event (first zero crossing = a quarter period), then E = (n + 1/2) h f.
    scale = 1.0e-15  # time unit in seconds, so that the integration is well scaled
    stiffness = k / mu * scale ** 2

    def crossing(t, y):
        return y[0]

    crossing.terminal = True
    solution = solve_ivp(lambda t, y: [y[1], -stiffness * y[0]], (0.0, 100.0), [1.0, 0.0], events=crossing, rtol=1e-12,
                         atol=1e-14)
    period = 4.0 * float(solution.t_events[0][0]) * scale
    quantum = 2.0 * math.pi / period * hbar_c / c
    return float((n + 0.5) * quantum)


def _solve_xray_bragg(kinetic, d, hc):
    # The shortest wavelength is the root of hc / lambda = K; the Bragg angle is the root of sin(theta) = lambda / (2 d).
    lam = brentq(lambda x: hc / (x * kinetic) - 1.0, 1e-15, 1e-5, xtol=1e-30, rtol=1e-14)
    return float(brentq(lambda th: math.sin(th) - lam / (2.0 * d), 0.0, 0.5 * math.pi, xtol=1e-15, rtol=1e-14))


# --- shared constants -----------------------------------------------------------------------------------


def _hc():
    return _in("hc", "energy_length", "eV*nm", "Planck constant times the speed of light, a stated constant", 1240.0, (1235.0, 1245.0),
               provenance="assumed")


def _mc2():
    return _in("mc2", "energy", "keV", "rest energy of the electron, a stated constant", 511.0, (505.0, 515.0), provenance="assumed")


def _c():
    return _in("c", "speed", "km/s", "speed of light, a stated constant", 300000.0, (299000.0, 301000.0), provenance="assumed")


def _hbarc():
    return _in("hbarc", "energy_length", "eV*nm", "reduced Planck constant times the speed of light, a stated constant", 197.3,
               (196.0, 199.0), provenance="assumed")


A_HC = Assumption("A-hc", "The constant hc has the stated value and is used for every photon energy and wavelength.", "modelling", ("hc",))
A_MC2 = Assumption("A-mc2", "The electron rest energy has the stated value.", "modelling", ("mc2",))
A_C = Assumption("A-c", "The speed of light has the stated value.", "modelling", ("c",))
A_HBARC = Assumption("A-hbarc", "The constant hbar c has the stated value.", "modelling", ("hbarc",))


# --- structures -----------------------------------------------------------------------------------------


def s71_photoelectron_speed() -> Structure:
    return Structure(
        "S71", "Speed of the fastest photoelectrons", "quantum", "photoelectric_effect_speed",
        (_in("lam", "length", "nm", "wavelength of the incident light", 250.0, (150.0, 400.0)),
         _in("phi", "energy", "eV", "work function of the metal", 2.3, (1.5, 2.9)),
         _hc(), _mc2(), _c(),
         _co("Eph", "energy", "eV", "energy of one photon of the light", "hc/lam"),
         _co("Kmax", "energy", "eV", "maximum kinetic energy of an emitted electron", "Eph - phi"),
         _co("v", "speed", "km/s", "speed of the fastest photoelectrons", "c*sqrt(2*Kmax/mc2)")),
        "v",
        (A_HC, A_MC2, A_C,
         Assumption("A-one-photon", "Each electron absorbs one photon, and the fastest electrons lose no energy besides the work function.", "modelling", ("phi",)),
         Assumption("A-nonrel", "The electron speed is far below c, so the non-relativistic kinetic energy applies.", "modelling", ("mc2", "c"))),
        _spec("Light of wavelength {lam} nm falls on a metal surface whose work function is {phi} eV. Take hc = {hc} eV nm, the electron "
              "rest energy mc² = {mc2} keV and the speed of light c = {c} km/s.",
              "Using the non-relativistic relation between kinetic energy and speed, what is the speed of the fastest electrons "
              "emitted from the surface?", "speed of the fastest photoelectrons", "km/s",
              "A separate satellite B in another experiment moves at {v} {u}, but it is unrelated to the photoelectrons.",
              "Photoelectrons from a reference metal B have a speed of {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the photoelectric effect.", "W", equivalent="m/s"),
        ("lam", 0.8), _solve_photoelectron_speed, 5,
        "the speed as the root of one half of the electron mass times the speed squared minus the excess energy hc / lambda - phi, found with a bracketing root finder",
        solver_rel_tol=1e-9,
        instances=({"lam": 250.0, "phi": 2.3, "hc": 1240.0, "mc2": 511.0, "c": 300000.0},
                   {"lam": 300.0, "phi": 2.1, "hc": 1240.0, "mc2": 511.0, "c": 300000.0},
                   {"lam": 350.0, "phi": 2.75, "hc": 1240.0, "mc2": 511.0, "c": 300000.0},
                   {"lam": 220.0, "phi": 1.9, "hc": 1240.0, "mc2": 511.0, "c": 300000.0}))


def s72_de_broglie_electron() -> Structure:
    return Structure(
        "S72", "De Broglie wavelength of an accelerated electron", "quantum", "de_broglie_wavelength_from_kinetic_energy",
        (_in("Ke", "energy", "eV", "kinetic energy gained by the electron", 150.0, (20.0, 500.0)),
         _hc(), _mc2(),
         _co("pc", "energy", "eV", "momentum of the electron multiplied by the speed of light", "sqrt(2*mc2*Ke)"),
         _co("lamdb", "length", "pm", "de Broglie wavelength of the electron", "hc/pc")),
        "lamdb",
        (A_HC, A_MC2,
         Assumption("A-rest", "The electron starts from rest and its kinetic energy is small compared with its rest energy, so the non-relativistic relation applies.", "modelling", ("mc2",)),
         Assumption("A-wave", "The de Broglie relation wavelength = h / momentum gives the wavelength of the electron.", "boundary_condition", ("Ke",))),
        _spec("An electron starts from rest and is accelerated until it has gained a kinetic energy of {Ke} eV. Treat the electron "
              "non-relativistically. Take hc = {hc} eV nm and the electron rest energy mc² = {mc2} keV.",
              "What is the de Broglie wavelength of the electron?", "de Broglie wavelength of the electron", "pm",
              "A separate electron beam B in another laboratory has a wavelength of {v} {u}, but it is unrelated to this electron.",
              "A reference electron B has a de Broglie wavelength of {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the electron's motion.", "W", equivalent="nm"),
        ("Ke", 1.25), _solve_de_broglie, 3,
        "the wavelength as the root of (h / lambda)^2 / (2 m) = K, the kinetic energy of a particle of that de Broglie wavelength, found with a bracketing root finder",
        solver_rel_tol=1e-9,
        instances=({"Ke": 150.0, "hc": 1240.0, "mc2": 511.0},
                   {"Ke": 54.0, "hc": 1240.0, "mc2": 511.0},
                   {"Ke": 100.0, "hc": 1240.0, "mc2": 511.0},
                   {"Ke": 300.0, "hc": 1240.0, "mc2": 511.0}))


def s73_infinite_well_photon() -> Structure:
    return Structure(
        "S73", "Photon emitted between levels of an infinite well", "quantum", "infinite_well_transition_wavelength",
        (_in("L", "length", "nm", "width of the well", 0.5, (0.3, 1.0)),
         _in("ni", "quantum_number", "1", "quantum number of the initial level", 3.0, (3.0, 5.0)),
         _in("nf", "quantum_number", "1", "quantum number of the final level", 1.0, (1.0, 2.0)),
         _hc(), _mc2(),
         _co("E1", "energy", "eV", "ground-state energy of the electron in the well", "hc**2/(8*mc2*L**2)"),
         _co("dE", "energy", "eV", "energy difference between the two levels", "(ni**2 - nf**2)*E1"),
         _co("lamph", "length", "nm", "wavelength of the emitted photon", "hc/dE")),
        "lamph",
        (A_HC, A_MC2,
         Assumption("A-well", "The walls are impenetrable and the potential inside the well is zero (an infinite square well of the stated width).", "modelling", ("mc2",)),
         Assumption("A-photon", "The transition emits one photon that carries the whole energy difference; the recoil of the walls is neglected. Every transition used has an odd change in quantum number, so it is allowed by the electric-dipole selection rule.", "boundary_condition", ("hc",))),
        _spec("An electron is confined in a one-dimensional infinite square well of width {L} nm. It makes a transition from the level "
              "with quantum number n = {ni} down to the level with quantum number n = {nf} and emits one photon. Take hc = {hc} eV nm "
              "and the electron rest energy mc² = {mc2} keV.",
              "What is the wavelength of the emitted photon?", "wavelength of the emitted photon", "nm",
              "A separate laser B in another laboratory emits light of wavelength {v} {u}, but it is unrelated to the well.",
              "A reference well B emits a photon of wavelength {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the transition.", "W", equivalent="μm"),
        ("L", 1.25), _solve_well_photon, 5,
        "the ground-state energy as the expectation value of p squared over 2 m in the normalised sine state, evaluated by quadrature, then the level energies from the quantisation condition k_n = n k_1 and the wavelength from their difference",
        solver_rel_tol=1e-9,
        instances=({"L": 0.5, "ni": 4.0, "nf": 1.0, "hc": 1240.0, "mc2": 511.0},
                   {"L": 0.8, "ni": 5.0, "nf": 2.0, "hc": 1240.0, "mc2": 511.0},
                   {"L": 0.6, "ni": 3.0, "nf": 2.0, "hc": 1240.0, "mc2": 511.0},
                   {"L": 0.4, "ni": 4.0, "nf": 1.0, "hc": 1240.0, "mc2": 511.0}))


def s74_bohr_recoil_speed() -> Structure:
    return Structure(
        "S74", "Recoil speed of a hydrogen atom emitting a photon", "quantum", "bohr_transition_photon_recoil",
        (_in("ni", "quantum_number", "1", "Bohr level the atom starts in", 3.0, (3.0, 7.0)),
         _in("nf", "quantum_number", "1", "Bohr level the atom ends in", 2.0, (1.0, 2.0)),
         _in("Ry", "energy", "eV", "Rydberg energy of hydrogen, a stated constant", 13.6, (13.5, 13.7), provenance="assumed"),
         _in("M", "mass", "u", "mass of the atom", 1.008, (1.0, 4.0)),
         _c(),
         _co("Eph", "energy", "eV", "energy of the emitted photon", "Ry*(1/nf**2 - 1/ni**2)"),
         _co("pph", "momentum", "kg*m/s", "momentum of the emitted photon", "Eph/c"),
         _co("vrec", "speed", "m/s", "recoil speed of the atom", "pph/M")),
        "vrec",
        (A_C,
         Assumption("A-bohr", "The electron levels follow the Bohr model with energies -Ry / n squared, using the same Rydberg energy for every isotope.", "modelling", ("Ry",)),
         Assumption("A-rest", "The atom is initially at rest, the photon momentum is its energy over c, and the recoil is non-relativistic.", "boundary_condition", ("M",))),
        _spec("An atom of a hydrogen isotope, with mass {M} u, is at rest in the Bohr level n = {ni}. It drops to the level n = {nf} by "
              "emitting one photon. Use the Bohr level energies of hydrogen, with a Rydberg energy of {Ry} eV, for every isotope, and "
              "take the speed of light c = {c} km/s.",
              "With what speed does the atom recoil?", "recoil speed of the atom", "m/s",
              "A separate cart B on another track moves at {v} {u}, but it is unrelated to the atom.",
              "A reference atom B recoils at {v} {u}.",
              "A separate heater B is rated at {v} {u}, but it plays no part in the emission.", "W", equivalent="cm/s"),
        ("M", 1.25), _solve_bohr_recoil, 5,
        "the photon energy as the integral of dE_n / dn = 2 Ry / n^3 between the two levels, then the recoil speed as the root of M v = E / c found with a bracketing root finder",
        solver_rel_tol=1e-9,
        instances=({"ni": 3.0, "nf": 2.0, "Ry": 13.6, "M": 1.008, "c": 300000.0},
                   {"ni": 4.0, "nf": 2.0, "Ry": 13.6, "M": 1.008, "c": 300000.0},
                   {"ni": 4.0, "nf": 1.0, "Ry": 13.6, "M": 2.014, "c": 300000.0},
                   {"ni": 6.0, "nf": 2.0, "Ry": 13.6, "M": 3.016, "c": 300000.0}))


def s75_compton_electron_energy() -> Structure:
    return Structure(
        "S75", "Kinetic energy given to an electron in Compton scattering", "quantum", "compton_scattering_electron_energy",
        (_in("lam0", "length", "pm", "wavelength of the incident X-ray photon", 20.0, (5.0, 30.0)),
         _in("theta", "angle", "deg", "scattering angle of the photon", 90.0, (30.0, 150.0)),
         _hc(), _mc2(),
         _co("lamC", "length", "pm", "Compton wavelength of the electron", "hc/mc2"),
         _co("lam1", "length", "pm", "wavelength of the scattered photon", "lam0 + lamC*(1 - cos(theta))"),
         _co("Ke", "energy", "keV", "kinetic energy given to the electron", "hc/lam0 - hc/lam1")),
        "Ke",
        (A_HC, A_MC2,
         Assumption("A-free", "The electron is free and initially at rest, and the collision conserves energy and momentum.", "modelling", ("mc2",)),
         Assumption("A-angle", "The scattering angle is measured between the incident and the scattered photon directions.", "boundary_condition", ("theta",))),
        _spec("An X-ray photon of wavelength {lam0} pm scatters from a free electron that is initially at rest, and the photon leaves "
              "at an angle of {theta} degrees to its original direction. Take hc = {hc} eV nm and the electron rest energy "
              "mc² = {mc2} keV.",
              "What kinetic energy does the electron gain?", "kinetic energy gained by the electron", "keV",
              "A separate X-ray tube B in another laboratory runs at {v} {u}, but it is unrelated to this scattering.",
              "A reference electron B gains {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the scattering.", "W", equivalent="eV"),
        ("theta", 1.25), _solve_compton_energy, 4,
        "the scattered photon energy as the root of the energy balance with the electron momentum from the momentum triangle, found with a bracketing root finder",
        solver_rel_tol=1e-9,
        instances=({"lam0": 20.0, "theta": 90.0, "hc": 1240.0, "mc2": 511.0},
                   {"lam0": 10.0, "theta": 60.0, "hc": 1240.0, "mc2": 511.0},
                   {"lam0": 25.0, "theta": 120.0, "hc": 1240.0, "mc2": 511.0},
                   {"lam0": 15.0, "theta": 45.0, "hc": 1240.0, "mc2": 511.0}))


def s76_uncertainty_binding_energy() -> Structure:
    return Structure(
        "S76", "Binding energy from the uncertainty principle", "quantum", "uncertainty_principle_ground_state_estimate",
        (_in("Zeff", "coefficient", "1", "effective nuclear charge seen by the electron, in units of the elementary charge", 1.0, (1.0, 3.0)),
         _hbarc(), _mc2(),
         _in("ke2", "energy_length", "eV*nm", "Coulomb constant times the square of the elementary charge, a stated constant", 1.44,
             (1.40, 1.48), provenance="assumed"),
         _co("r0", "length", "nm", "radius that minimises the energy", "hbarc**2/(mc2*Zeff*ke2)"),
         _co("Eb", "energy", "eV", "binding energy of the electron", "Zeff*ke2/(2*r0)")),
        "Eb",
        (A_HBARC, A_MC2,
         Assumption("A-ke2", "The product of Coulomb's constant and the square of the elementary charge has the stated value.", "modelling", ("ke2",)),
         Assumption("A-estimate", "The momentum is taken as p = hbar / r with r the distance from the nucleus, and the non-relativistic kinetic energy is used.", "modelling", ("Zeff",))),
        _spec("An electron moves in the attractive Coulomb field of a nucleus whose effective charge, in units of the elementary charge, "
              "is {Zeff}. In an uncertainty-principle estimate of the ground state, the momentum of the electron is p = ħ/r, where r is "
              "its distance from the nucleus, so its energy is E(r) = (p squared divided by twice the electron mass) minus "
              "(the effective charge times k e² divided by r). Take ħc = {hbarc} eV nm, the electron rest energy mc² = {mc2} keV, and "
              "k e² = {ke2} eV nm, where k is Coulomb's constant and e is the elementary charge.",
              "Minimising E(r) over r, what is the binding energy of the electron, that is, the magnitude of the minimum value of E?",
              "binding energy of the electron", "eV",
              "A separate atom B in another laboratory has an ionisation energy of {v} {u}, but it is unrelated to this electron.",
              "A reference electron B is bound by {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the binding.", "W", equivalent="keV"),
        ("Zeff", 1.25), _solve_uncertainty_binding, 4,
        "the energy E(r) minimised numerically as the root of dE/dr, and the depth of the minimum evaluated there",
        solver_rel_tol=1e-9,
        instances=({"Zeff": 1.0, "hbarc": 197.3, "mc2": 511.0, "ke2": 1.44},
                   {"Zeff": 1.7, "hbarc": 197.3, "mc2": 511.0, "ke2": 1.44},
                   {"Zeff": 2.0, "hbarc": 197.3, "mc2": 511.0, "ke2": 1.44},
                   {"Zeff": 1.3, "hbarc": 197.3, "mc2": 511.0, "ke2": 1.44}))


def s77_tunnelling_barrier_width() -> Structure:
    return Structure(
        "S77", "Barrier width for a given tunnelling probability", "quantum", "rectangular_barrier_tunnelling_width",
        (_in("U0", "energy", "eV", "height of the barrier", 8.0, (6.0, 13.0)),
         _in("Ee", "energy", "eV", "kinetic energy of the electron", 5.0, (2.0, 5.5)),
         _in("Tr", "coefficient", "1", "required transmission probability", 0.001, (0.0001, 0.05)),
         _mc2(), _hbarc(),
         _co("dU", "energy", "eV", "amount by which the barrier exceeds the electron energy", "U0 - Ee"),
         _co("kappa", "wavenumber", "1/m", "decay constant of the wave function inside the barrier", "sqrt(2*mc2*dU)/hbarc"),
         _co("a", "length", "nm", "barrier width", "-log(Tr)/(2*kappa)")),
        "a",
        (A_MC2, A_HBARC,
         Assumption("A-rect", "The barrier is rectangular with the stated height and the electron arrives from one side with the stated kinetic energy.", "modelling", ("U0", "Ee")),
         Assumption("A-exp", "The transmission probability is given by the exponential approximation T = exp(-2 kappa a) for a wide barrier, with kappa = sqrt(2 m (U0 - E)) / hbar.", "modelling", ("Tr",))),
        _spec("An electron of kinetic energy {Ee} eV approaches a rectangular potential barrier of height {U0} eV. For a barrier "
              "of width a, take the transmission probability T to be exp(-x), where x is twice the product of a and a decay constant "
              "κ. The decay constant is defined by ħκ = the square root of the quantity (twice the electron mass times the "
              "difference between the barrier height and the electron kinetic energy). Take ħc = {hbarc} eV nm and the electron rest "
              "energy mc² = {mc2} keV.",
              "What barrier width a gives a transmission probability T = {Tr}?", "barrier width", "nm",
              "A separate film B in another laboratory is {v} {u} thick, but it is unrelated to the barrier.",
              "A reference barrier B has a width of {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the tunnelling.", "W", equivalent="pm"),
        ("U0", 1.25), _solve_tunnel_width, 5,
        "the decay constant as the root of (hbar kappa)^2 / (2 m) = U0 - E and the width as the root of exp(-2 kappa a) = T, both found with a bracketing root finder",
        solver_rel_tol=1e-9,
        instances=({"U0": 8.0, "Ee": 5.0, "Tr": 0.001, "mc2": 511.0, "hbarc": 197.3},
                   {"U0": 10.0, "Ee": 5.5, "Tr": 0.01, "mc2": 511.0, "hbarc": 197.3},
                   {"U0": 7.0, "Ee": 4.0, "Tr": 0.0001, "mc2": 511.0, "hbarc": 197.3},
                   {"U0": 9.0, "Ee": 5.0, "Tr": 0.005, "mc2": 511.0, "hbarc": 197.3}))


def s78_oscillator_level_energy() -> Structure:
    return Structure(
        "S78", "Vibrational level energy of a diatomic molecule", "quantum", "quantum_harmonic_oscillator_level",
        (_in("k", "stiffness", "N/m", "force constant of the bond", 1860.0, (400.0, 3000.0)),
         _in("mu", "mass", "u", "reduced mass of the two atoms", 6.86, (0.9, 15.0)),
         _in("n", "quantum_number", "1", "vibrational quantum number of the level", 1.0, (0.0, 4.0)),
         _hbarc(), _c(),
         _co("omega", "angular_frequency", "rad/s", "angular frequency of the vibration", "sqrt(k/mu)"),
         _co("hw", "energy", "eV", "energy quantum of the vibration", "hbarc*omega/c"),
         _co("En", "energy", "eV", "energy of the level above the bottom of the potential", "(n + 0.5)*hw")),
        "En",
        (A_HBARC, A_C,
         Assumption("A-sho", "The vibration is a small oscillation of a single particle of the stated reduced mass in a harmonic potential with the stated force constant.", "modelling", ("k", "mu")),
         Assumption("A-quantised", "The levels are those of the quantum harmonic oscillator, E_n = (n + 1/2) hbar omega.", "modelling", ("n",))),
        _spec("The vibration of a diatomic molecule is modelled as a quantum harmonic oscillator. The bond has a force constant of "
              "{k} N/m and the reduced mass of the two atoms is {mu} u. Take ħc = {hbarc} eV nm and the speed of light c = {c} km/s.",
              "What is the energy of the vibrational level with quantum number n = {n}, measured from the bottom of the potential "
              "well?", "energy of the vibrational level", "eV",
              "A separate laser photon B in another laboratory carries {v} {u}, but it is unrelated to the molecule.",
              "A reference molecule B has a level at {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the vibration.", "W", equivalent="keV"),
        ("k", 1.25), _solve_oscillator_level, 5,
        "the vibration frequency from the period of the classical oscillation, integrated as an ODE up to the first zero crossing, and the level energy (n + 1/2) h f",
        solver_rel_tol=1e-7,
        instances=({"k": 1860.0, "mu": 6.86, "n": 1.0, "hbarc": 197.3, "c": 300000.0},
                   {"k": 516.0, "mu": 0.98, "n": 2.0, "hbarc": 197.3, "c": 300000.0},
                   {"k": 2295.0, "mu": 7.0, "n": 0.0, "hbarc": 197.3, "c": 300000.0},
                   {"k": 966.0, "mu": 0.957, "n": 3.0, "hbarc": 197.3, "c": 300000.0}))


def s79_xray_bragg_angle() -> Structure:
    return Structure(
        "S79", "Bragg angle of the shortest X-ray wavelength", "quantum", "duane_hunt_limit_bragg_angle",
        (_in("Ke", "energy", "keV", "kinetic energy of the electrons hitting the anode", 30.0, (20.0, 60.0)),
         _in("d", "length", "pm", "spacing between the atomic planes of the crystal", 282.0, (150.0, 400.0)),
         _hc(),
         _co("lammin", "length", "pm", "shortest wavelength of the X-rays produced", "hc/Ke"),
         _co("theta", "angle", "deg", "glancing angle of the first-order reflection", "asin(lammin/(2*d))")),
        "theta",
        (A_HC,
         Assumption("A-limit", "The shortest wavelength is produced when an electron gives all of its kinetic energy to a single photon.", "modelling", ("Ke",)),
         Assumption("A-bragg", "The reflection is first order and the angle is measured from the atomic planes, not from their normal.", "boundary_condition", ("d",))),
        _spec("Electrons strike the anode of an X-ray tube with a kinetic energy of {Ke} keV. The X-rays of the shortest wavelength "
              "that the tube produces are reflected from a crystal whose atomic planes are {d} pm apart. Take hc = {hc} eV nm.",
              "At what glancing angle, measured from the atomic planes, does the first-order Bragg reflection of this shortest "
              "wavelength occur?", "glancing angle of the first-order reflection", "deg",
              "A separate crystal B in another laboratory reflects X-rays at an angle of {v} {u}, but it is unrelated to this tube.",
              "A reference crystal B reflects at an angle of {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the reflection.", "W", equivalent="rad"),
        ("Ke", 1.25), _solve_xray_bragg, 3,
        "the shortest wavelength as the root of hc / lambda = K and the glancing angle as the root of sin(theta) = lambda / (2 d), both found with a bracketing root finder",
        solver_rel_tol=1e-9,
        instances=({"Ke": 30.0, "d": 282.0, "hc": 1240.0},
                   {"Ke": 40.0, "d": 282.0, "hc": 1240.0},
                   {"Ke": 25.0, "d": 201.0, "hc": 1240.0},
                   {"Ke": 45.0, "d": 314.0, "hc": 1240.0}))


ALL = (s71_photoelectron_speed, s72_de_broglie_electron, s73_infinite_well_photon, s74_bohr_recoil_speed, s75_compton_electron_energy,
       s76_uncertainty_binding_energy, s77_tunnelling_barrier_width, s78_oscillator_level_energy, s79_xray_bragg_angle)


def all_structures() -> list[Structure]:
    return [factory() for factory in ALL]


# --- gold solution plans -----------------------------------------------------------------------------------

PLANS: dict[str, Plan] = {
    "S71": Plan(
        approach="The question asks for the speed of the fastest photoelectrons. Work in energy units: get the photon energy from the "
                 "wavelength, subtract the work function (Einstein's photoelectric equation) to obtain the maximum kinetic energy, and "
                 "only then convert that kinetic energy into a speed with the non-relativistic relation.",
        steps=(
            Step("Eph", "Planck-Einstein relation: a photon of wavelength lambda carries the energy E = h c / lambda.",
                 "Light interacts with the electrons in the metal one photon at a time, so the energy a single electron can receive is "
                 "the energy of one photon, which the stated product hc and the wavelength give directly."),
            Step("Kmax", "Einstein's photoelectric equation: K_max = E_photon - phi, which is conservation of energy for one photon "
                         "absorbed by one electron.",
                 "The most energetic electrons come from the surface and lose only the minimum energy phi needed to escape the metal, so "
                 "all the rest of the photon energy remains as their kinetic energy."),
            Step("v", "Non-relativistic kinetic energy K = (1/2) m v^2, so v = c sqrt(2 K / (m c^2)) when the mass is written through "
                      "the rest energy m c^2.",
                 "The kinetic energy is only a few electronvolts, tiny compared with the electron rest energy, so the classical "
                 "relation is accurate, and using the rest energy over c squared as the mass lets us use the stated constants."),
        ),
        check="At the threshold, where the photon energy equals the work function, K_max and v vanish, and below it no electron is "
              "emitted. A kinetic energy of a few electronvolts against a rest energy of hundreds of keV gives v/c of a few "
              "thousandths, which confirms that the non-relativistic treatment is justified."),
    "S72": Plan(
        approach="The question asks for the de Broglie wavelength of an electron whose kinetic energy is known. Find the momentum "
                 "(multiplied by c so that it is an energy) from the kinetic energy, then apply lambda = h / p in the form hc / (p c).",
        steps=(
            Step("pc", "Non-relativistic kinetic energy K = p^2 / (2 m), so p c = sqrt(2 (m c^2) K).",
                 "The electron started from rest, so the whole energy it gained is kinetic, and K is far below the rest energy, so the "
                 "classical formula holds; solving for p and multiplying by c gives a momentum in energy units that matches hc."),
            Step("lamdb", "de Broglie relation: a particle of momentum p has the wavelength lambda = h / p = h c / (p c).",
                 "Matter behaves as a wave with a wavelength set by its momentum, so dividing the stated hc by p c gives the wavelength "
                 "directly in length units."),
        ),
        check="The wavelength falls as one over the square root of the kinetic energy, so more energy gives a shorter wavelength. "
              "Dimensionally, hc is energy times length and p c is an energy, so the ratio is a length. For tens to hundreds of "
              "electronvolts the result is of the order of atomic spacings, which is why electrons of this energy diffract from crystals."),
    "S73": Plan(
        approach="The photon carries the energy difference between two levels of the well, and its wavelength then follows from "
                 "lambda = hc / E. So first find the ground-state energy of an electron in a well of this width, scale it to the two "
                 "levels with E_n = n^2 E_1, and convert the energy difference into a wavelength.",
        steps=(
            Step("E1", "Energy levels of the infinite square well: E_n = n^2 h^2 / (8 m L^2), which for n = 1, with h written through "
                       "hc and m through its rest energy, is E_1 = (hc)^2 / (8 (m c^2) L^2).",
                 "The wave function must vanish at both walls, which fits n half-wavelengths into the width L, so the allowed momenta "
                 "and hence the energies are quantised; E_1 is the unit in which all the levels of this well are measured."),
            Step("dE", "Level spectrum E_n = n^2 E_1 and conservation of energy: the photon takes the energy difference "
                       "E_i - E_f = (n_i^2 - n_f^2) E_1.",
                 "The electron goes from a higher to a lower level and the energy it loses is carried away by one photon, the recoil "
                 "of the walls being negligible, so this difference is the photon energy."),
            Step("lamph", "Planck-Einstein relation E = h c / lambda, so lambda = h c / E.",
                 "The photon energy is now known, and the stated product hc converts it directly into the wavelength of the light."),
        ),
        check="The ground-state energy scales as 1/L^2, so a wider well has closer levels and a longer photon wavelength, "
              "lambda proportional to L^2. Dimensionally (J m)^2 / (J m^2) is an energy. A well of atomic size (a fraction of a nanometre) gives "
              "level spacings of several electronvolts, so the photon lies in the ultraviolet or visible range, as expected for atomic-size confinement."),
    "S74": Plan(
        approach="An atom that emits a photon recoils, and its recoil momentum equals the photon momentum. So find the photon energy "
                 "from the Bohr levels, turn it into a momentum with p = E / c, and divide by the atom mass to get the recoil speed.",
        steps=(
            Step("Eph", "Bohr model of hydrogen: the level energies are E_n = -Ry / n^2, so the photon carries the level drop "
                        "E = Ry (1/n_f^2 - 1/n_i^2), by conservation of energy.",
                 "The atom goes from level n_i to the lower level n_f and the energy difference leaves as a single photon, so the "
                 "Bohr energies give the photon energy (the recoil energy is negligible)."),
            Step("pph", "Momentum of a photon: p = E / c.",
                 "Recoil is a momentum effect, so we need the momentum of the photon, which follows from its energy and the speed of light."),
            Step("vrec", "Conservation of linear momentum: the atom starts at rest, so M v = p_photon and v = p / M.",
                 "No external force acts during the emission, so the atom must take up the photon momentum in the opposite direction; "
                 "the speed is tiny, so a non-relativistic momentum M v is adequate."),
        ),
        check="The recoil speed is only of the order of a metre per second, and the recoil kinetic energy M v^2 / 2 is many orders of "
              "magnitude smaller than the photon energy, which justifies neglecting it in the first step. The speed is inversely "
              "proportional to the mass, so a heavier isotope recoils more slowly."),
    "S75": Plan(
        approach="The photon loses energy to the electron, so the electron's kinetic energy is the difference between the photon "
                 "energies before and after the collision. Find the wavelength shift from the Compton formula, hence the scattered "
                 "wavelength, and take the difference of hc / lambda.",
        steps=(
            Step("lamC", "Compton wavelength of the electron: lambda_C = h / (m c) = hc / (m c^2).",
                 "It is the natural length scale of the wavelength change in photon-electron scattering, and it can be formed from the "
                 "two stated constants, hc and the electron rest energy."),
            Step("lam1", "Compton scattering formula, from conservation of energy and momentum for a photon hitting a free electron "
                         "at rest: lambda' - lambda = lambda_C (1 - cos theta).",
                 "It gives the wavelength of the scattered photon for the stated scattering angle; the shift does not depend on the "
                 "initial wavelength, so we add it to the incident wavelength."),
            Step("Ke", "Conservation of energy with the electron initially at rest: K = E - E' = hc / lambda - hc / lambda'.",
                 "The photon is the only source of energy, so what it loses between the two wavelengths is exactly the kinetic energy "
                 "given to the electron."),
        ),
        check="For theta tending to zero the shift and K vanish, and the shift reaches at most twice the Compton wavelength at "
              "180 degrees. The electron energy must be positive and smaller than the incident photon energy, and it grows as the "
              "angle or the photon energy increases."),
    "S76": Plan(
        approach="Write the electron's energy as a function of its distance r using p = hbar / r, find the radius that minimises it, "
                 "and evaluate the minimum. Its magnitude is the binding energy.",
        steps=(
            Step("r0", "Minimising E(r) = (hbar c)^2 / (2 (m c^2) r^2) - Zeff k e^2 / r: setting dE/dr = 0 gives "
                       "r0 = (hbar c)^2 / ((m c^2) Zeff k e^2), the Bohr radius when Zeff is one.",
                 "Confining the electron to a smaller radius raises its kinetic energy as 1/r^2, while the attraction lowers the "
                 "potential energy only as 1/r, so the energy has a minimum, and that radius is the estimate of the size of the ground state."),
            Step("Eb", "At the minimum the kinetic energy is half the magnitude of the potential energy (virial theorem for a 1/r "
                       "potential), so E_min = -Zeff k e^2 / (2 r0), and the binding energy is its magnitude.",
                 "Substituting r0 back into E(r) gives the depth of the minimum; the electron needs exactly this energy to be removed "
                 "from the nucleus."),
        ),
        check="For one unit of effective charge the result is the familiar ground-state energy of hydrogen, and the binding energy "
              "scales as Zeff squared, as for a hydrogen-like ion. Dimensionally, an energy times a length divided by a length is an energy."),
    "S77": Plan(
        approach="The question asks for the width of the barrier for which the stated approximate transmission probability has the "
                 "given value. Find how far the barrier top lies above the electron's energy, then the decay constant of the wave "
                 "inside the barrier, and then invert T = exp(-2 kappa a) for the width.",
        steps=(
            Step("dU", "Classically forbidden region: the electron's kinetic energy lies below the barrier top by U0 - E.",
                 "Inside the barrier the wave function does not oscillate but decays, and the rate of decay is set by how much the "
                 "barrier exceeds the electron energy."),
            Step("kappa", "Time-independent Schroedinger equation inside a constant potential above the energy: "
                          "psi proportional to exp(-kappa x) with kappa = sqrt(2 m (U0 - E)) / hbar = sqrt(2 (m c^2) (U0 - E)) / (hbar c).",
                 "The decay constant kappa controls how quickly the probability falls across the barrier, and the stated rest energy "
                 "and hbar c let us compute it from the energy deficit."),
            Step("a", "Exponential (thick-barrier) approximation for tunnelling: T = exp(-2 kappa a), so a = -ln(T) / (2 kappa).",
                 "The stated transmission probability is a known number, so taking the natural logarithm of the exponential "
                 "approximation and solving for a gives the barrier width."),
        ),
        check="A wider barrier or a larger deficit gives a smaller transmission, so a falls as kappa rises and grows as the "
              "required T gets smaller. If T tended to one the width would tend to zero. A deficit of a few electronvolts gives "
              "kappa of several per nanometre, so widths of a fraction of a nanometre are the expected order of magnitude."),
    "S78": Plan(
        approach="The levels of a quantum harmonic oscillator are E_n = (n + 1/2) hbar omega, so the task is to find the angular "
                 "frequency from the bond stiffness and the reduced mass, turn hbar omega into an energy with the stated constants, "
                 "and apply the level formula.",
        steps=(
            Step("omega", "Harmonic oscillator: a particle of (reduced) mass mu on a spring-like force of constant k oscillates "
                          "with angular frequency omega = sqrt(k / mu).",
                 "Small vibrations of the bond between two atoms behave like one particle of the reduced mass in a harmonic "
                 "potential, so this frequency characterises the molecule's vibration."),
            Step("hw", "Planck's relation for the oscillator quantum: the level spacing is hbar omega = (hbar c)(omega / c).",
                 "The levels are equally spaced by one quantum hbar omega, and writing hbar as (hbar c)/c lets us evaluate it in "
                 "electronvolts from the stated constants."),
            Step("En", "Quantised oscillator levels: E_n = (n + 1/2) hbar omega.",
                 "The quantum number n counts quanta above the ground state, and the extra one half is the zero-point energy, so "
                 "this formula gives the level energy measured from the bottom of the potential well."),
        ),
        check="A stiffer bond or lighter atoms raise omega, and the energy of level n is the spacing times (n + 1/2), so level zero "
              "has half a quantum. A spacing of a few tenths of an electronvolt corresponds to infrared light of a few micrometres, "
              "which is the right range for molecular vibrations."),
    "S79": Plan(
        approach="First find the shortest X-ray wavelength the tube produces from the electron energy, then use Bragg's law for "
                 "first-order reflection to find the glancing angle at which a crystal reflects that wavelength.",
        steps=(
            Step("lammin", "Duane-Hunt limit (energy conservation): the most energetic photon takes the whole kinetic energy K of "
                           "an electron, so lambda_min = h c / K.",
                 "X-rays are produced when electrons decelerate in the anode, and an electron cannot give a photon more energy than "
                 "it has, so the largest photon energy fixes the shortest wavelength."),
            Step("theta", "Bragg's law for constructive reflection from parallel planes: 2 d sin(theta) = m lambda, with order m = 1, "
                          "so theta = arcsin(lambda / (2 d)).",
                 "Reflections from successive planes interfere constructively when their path difference is one wavelength, which "
                 "fixes the glancing angle, measured from the planes, for the wavelength just found."),
        ),
        check="The ratio lambda / (2 d) must lie below one for a reflection to exist, and here it is small, so the angle is small. "
              "A higher tube energy gives a shorter wavelength and so a smaller angle, and a larger plane spacing also reduces the angle."),
}

LEVELS: dict[str, str] = {
    "S71": "high_school", "S72": "high_school", "S73": "intro_university", "S74": "intro_university",
    "S75": "intro_university", "S76": "upper_university", "S77": "upper_university", "S78": "intro_university",
    "S79": "high_school",
}

TOPICS: dict[str, str] = {
    "S71": "photoelectric effect: speed of the fastest photoelectrons",
    "S72": "de Broglie wavelength of an electron from its kinetic energy",
    "S73": "photon emitted between levels of a particle in a one-dimensional infinite well",
    "S74": "Bohr model of hydrogen: photon emission and atomic recoil",
    "S75": "Compton scattering: kinetic energy given to the electron",
    "S76": "Heisenberg uncertainty estimate of a hydrogen-like binding energy",
    "S77": "tunnelling through a rectangular barrier: width from the transmission",
    "S78": "quantum harmonic oscillator: vibrational level of a diatomic molecule",
    "S79": "X-ray minimum wavelength (Duane-Hunt) and Bragg reflection",
}
