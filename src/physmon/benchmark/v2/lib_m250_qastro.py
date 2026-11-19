"""M250 phase 2, batch qastro: ten NEW structures, S273 to S282 (exploration pool), and their gold plans.

Authority: plan of record v2.2 (`docs/proposals/PhysMon_Research_v2.tex`, "Dataset plan"), the dataset admission standard
(`docs/registry/v2/g1/dataset_admission_standard.md`) and plan revision v2.2 section G. Domains: quantum and atomic physics (S273 to
S276), special relativity (S277 to S279) and astrophysics and gravitation (S280 to S282). Each structure is a typed graph with an
independently coded numeric solver (the Bohr levels through the effective Rydberg energy, an enumeration of the six Zeeman components,
a numerical quadrature of the probability density, a quadrature of the barrier integral, an explicit flight-time and proper-time
integration, a root finder on the invariant mass, an exact stable form of the transverse Doppler shift, the vis-viva equation of the
transfer ellipse, a ratio of masses, an absolute Stefan-Boltzmann computation), four numeric instantiations and a relevant edit that
moves the answer.

The situations are new against dataset v1 (S01-S95), every `library*` / `lib_*` structure (the infinite-well transition photon S73,
the hydrogen recoil S74, the uncertainty binding energy S75, the tunnelling barrier width S77, the proper lifetime S81, the Wien photon
energy S82, the circular-orbit work S252) and the other M250 ranges: the photon emitted when a muon is captured into a Bohr level, the
outermost components of the sodium D2 line in a weak field, the probability of finding a particle of a box state in a slice, the ratio
of proton to deuteron currents through one barrier, the survival of a pion beam in a decay tube, the threshold energy of a reaction on a
target at rest, the transverse Doppler shift of gamma rays from a rotor, the total speed change of a Hohmann transfer, the escape
speed of a uniform planet from its density and radius, and the luminosity of a star from its Wien peak and radius.

Constants whose units the unit table does not hold (the gravitational constant, the Stefan-Boltzmann constant, the Wien constant) do not
occur: the planets and stars are scaled against the Earth and the Sun. Every answer-deciding condition (initial and boundary
conditions, the governing model where models compete) is stated in the base text. `PLANS` holds the gold solving technique for each
structure, `LEVELS` and `TOPICS` label them. These are agent-authored candidates: solver-certified, not expert-reviewed.
"""

from __future__ import annotations

import math

from scipy.integrate import quad
from scipy.optimize import brentq

from physmon.benchmark.v2.graph import Assumption, Structure
from physmon.benchmark.v2.library import _co, _in, _spec
from physmon.benchmark.v2.trace import Plan, Step

# --- solvers (independent routes; SI inputs in input-node order) --------------------------------------------------------------------


def _solve_muon_capture_line(z, n, kinetic, mmu, mnuc, a0, ke2, hc):
    # The effective Rydberg energy of the two-body system (the electron value scaled by the reduced mass), then the Bohr binding energy
    # Z^2 Ry_eff / n^2, with the photon energy as the sum of the binding energy and the kinetic energy.
    mu = mmu * mnuc / (mmu + mnuc)
    rydberg_eff = ke2 / (2.0 * a0) * mu
    photon = kinetic + z * z * rydberg_eff / (n * n)
    return float(hc / photon)


def _solve_zeeman_outer_separation(lam, b, gu, gl, e, hbar, me, hc):
    # Enumerate the allowed components of the 2P3/2 -> 2S1/2 line (change of the magnetic quantum number 0 or +-1): each shifts by
    # (gu mu - gl ml) Bohr magnetons B, and the outer separation is the spread of the shifts.
    shifts = []
    for mu_u in (1.5, 0.5, -0.5, -1.5):
        for m_l in (0.5, -0.5):
            if abs(mu_u - m_l) <= 1.0 + 1e-12:
                shifts.append(gu * mu_u - gl * m_l)
    spread = max(shifts) - min(shifts)
    energy = spread * e * hbar * b / (2.0 * me)
    return float(lam * lam * energy / hc)


def _solve_box_slice_probability(box, n, x1, width):
    # Numerical quadrature of the probability density (2 / L) sin^2(n pi x / L) over the slice.
    def density(x):
        return 2.0 / box * math.sin(n * math.pi * x / box) ** 2

    value, _ = quad(density, x1, x1 + width, epsabs=1e-13, epsrel=1e-12, limit=2000)
    return float(value)


def _solve_isotope_tunnelling_ratio(v, a, mp, md, hbar):
    # The exponent of the transmission through the barrier as a quadrature of the decay constant across its width, for each particle;
    # the ratio is the exponential of the difference of the two exponents.
    def exponent(mass):
        kappa = math.sqrt(2.0 * mass * v) / hbar
        integral, _ = quad(lambda x: kappa, 0.0, a, epsabs=1e-12, epsrel=1e-13)
        return 2.0 * integral

    return float(math.exp(exponent(md) - exponent(mp)))


def _solve_pion_survival(pc, mc2, tau0, path, c):
    # Gamma and beta from the energy and the momentum, the flight time in the laboratory, the proper time on the way, and the survival
    # fraction of the exponential decay law in the proper time.
    gamma = math.sqrt(1.0 + (pc / mc2) ** 2)
    beta = (pc / mc2) / gamma
    flight = path / (beta * c)
    proper = flight / gamma
    return float(math.exp(-proper / tau0))


def _solve_threshold_energy(m1, m2, excess):
    # The invariant mass of the beam and target particles equals the total final rest energy at threshold: a root finder on the kinetic
    # energy of the beam particle.
    final_mass = m1 + m2 + excess

    def mismatch(kinetic):
        energy = kinetic + m1
        momentum_sq = energy * energy - m1 * m1
        return math.sqrt((energy + m2) ** 2 - momentum_sq) - final_mass

    return float(brentq(mismatch, 0.0, 1e3 * (m1 + m2 + excess), xtol=1e-12 * final_mass, rtol=1e-14))


def _solve_rotor_doppler_shift(frot, radius, e0, h, c):
    # The exact transverse Doppler shift f0 (1 - 1 / gamma) = f0 (1 - sqrt(1 - beta^2)) in a form that does not lose digits for a tiny beta.
    speed = 2.0 * math.pi * frot * radius
    beta2 = (speed / c) ** 2
    f0 = e0 / h
    return float(-f0 * math.expm1(0.5 * math.log1p(-beta2)))


def _solve_hohmann_delta_v(g0, planet, h1, h2):
    # The vis-viva equation on the circular orbits and on the transfer ellipse, whose semi-major axis is the mean of the two radii.
    gm = g0 * planet * planet
    r1, r2 = planet + h1, planet + h2
    a = 0.5 * (r1 + r2)
    v1, v2 = math.sqrt(gm / r1), math.sqrt(gm / r2)
    vp = math.sqrt(gm * (2.0 / r1 - 1.0 / a))
    va = math.sqrt(gm * (2.0 / r2 - 1.0 / a))
    return float((vp - v1) + (v2 - va))


def _solve_escape_speed_scaled(rho, radius, ve, rho_e, re):
    # The escape speed is sqrt(2 G M / R): scale the mass of a uniform sphere from the Earth's mass and then the ratio M / R.
    mass_ratio = (rho / rho_e) * (radius / re) ** 3
    return float(ve * math.sqrt(mass_ratio / (radius / re)))


def _solve_star_luminosity(lam, radius, tsun, lamsun):
    # An absolute computation of the radiated power 4 pi R^2 sigma T^4 for the star and for the Sun, with Wien's law written as a constant
    # lam T = lamsun Tsun, divided by each other; the constants sigma and the solar radius drop out of the ratio.
    sigma, rsun = 5.670374419e-8, 6.957e8
    wien = lamsun * tsun
    star = 4.0 * math.pi * (radius * rsun) ** 2 * sigma * (wien / lam) ** 4
    sun = 4.0 * math.pi * rsun ** 2 * sigma * tsun ** 4
    return float(star / sun)


# --- structures ---------------------------------------------------------------------------------------------------------------------


def s273_muon_capture_photon() -> Structure:
    return Structure(
        "S273", "Wavelength of the photon emitted when a slow muon is captured into a Bohr level", "atomic physics",
        "muonic_atom_radiative_capture_bohr_level",
        (_in("Z", "count", "1", "number of protons in the bare nucleus", 1.0, (1.0, 4.0)),
         _in("n", "count", "1", "principal quantum number of the level into which the muon is captured", 2.0, (1.0, 5.0)),
         _in("K", "energy", "eV", "kinetic energy of the muon relative to the nucleus before the capture", 150.0, (20.0, 1000.0)),
         _in("mmu", "dimensionless", "1", "mass of the muon in electron masses, a stated constant", 206.77, (206.0, 207.5),
             provenance="assumed"),
         _in("M", "dimensionless", "1", "mass of the nucleus in electron masses", 1836.15, (1800.0, 14000.0)),
         _in("a0", "length", "nm", "Bohr radius of the hydrogen atom, a stated constant", 0.05292, (0.0528, 0.0530), provenance="assumed"),
         _in("ke2", "energy_length", "eV*nm", "Coulomb constant times the elementary charge squared, a stated constant", 1.440, (1.43, 1.45),
             provenance="assumed"),
         _in("hc", "energy_length", "eV*nm", "product of the Planck constant and the speed of light, a stated constant", 1240.0, (1230.0, 1250.0),
             provenance="assumed"),
         _co("mu", "dimensionless", "1", "reduced mass of the muon and the nucleus in electron masses", "mmu*M/(mmu + M)"),
         _co("r", "length", "fm", "radius of the Bohr orbit of the muon in the level n", "n**2*a0/(Z*mu)"),
         _co("Eb", "energy", "eV", "binding energy of the muon in the level n", "Z*ke2/(2*r)"),
         _co("Eph", "energy", "eV", "energy of the emitted photon", "K + Eb"),
         _co("lam", "length", "pm", "wavelength of the emitted photon", "hc/Eph")),
        "lam",
        (Assumption("A-bohr", "The muon and the nucleus form a two-body Bohr atom: the orbit radius is n^2 a0 / (Z mu) with the reduced mass mu in electron "
                              "masses, and the binding energy is the Coulomb energy Z ke2 / (2 r).", "modelling", ("Z", "n", "M", "mmu")),
         Assumption("A-capture", "The muon is captured directly into the level n with the emission of a single photon, which carries away the kinetic "
                                 "energy that the muon has relative to the nucleus together with its binding energy; the recoil of the atom is neglected.",
                    "boundary_condition", ("K",)),
         Assumption("A-point", "The only force between the muon and the nucleus is the electrostatic attraction, and the orbit lies outside the nucleus.",
                    "modelling", ("Z",)),
         Assumption("A-constants", "a0, the Coulomb constant times e^2, hc and the muon mass are the stated constants.", "modelling", ("a0", "ke2", "hc", "mmu"))),
        _spec("A negative muon, whose kinetic energy relative to a bare nucleus is {K} eV, is captured by the nucleus directly into the Bohr level "
              "n = {n} and emits a single photon in doing so. The nucleus has a charge number of {Z} and a mass of {M} electron masses, and the muon has a mass of "
              "{mmu} electron masses. Describe the muon and the nucleus as a two-body Bohr atom with the reduced mass of the pair. The only force "
              "between them is the electrostatic attraction, and the recoil of the atom is neglected. Take the Bohr radius of the hydrogen atom to be "
              "{a0} nm, the Coulomb constant times the elementary charge squared to be {ke2} eV nm and hc = {hc} eV nm.",
              "What is the wavelength of the emitted photon?", "wavelength of the emitted photon", "pm",
              "A separate laser B in another laboratory emits light of wavelength {v} {u}, but it is unrelated to this capture.",
              "A reference capture B emits a photon of wavelength {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the capture.", "W", equivalent="nm",
              formats={"M": ".6g", "mmu": ".5g", "a0": ".4g"}),
        ("K", 1.5), _solve_muon_capture_line, 8,
        "the effective Rydberg energy of the reduced-mass atom and the Bohr binding energy Z^2 Ry_eff / n^2, instead of the orbit radius and the Coulomb energy",
        solver_rel_tol=1e-9,
        instances=({"Z": 1.0, "n": 2.0, "K": 150.0, "mmu": 206.77, "M": 1836.15, "a0": 0.05292, "ke2": 1.440, "hc": 1240.0},
                   {"Z": 2.0, "n": 3.0, "K": 300.0, "mmu": 206.77, "M": 7294.3, "a0": 0.05292, "ke2": 1.440, "hc": 1240.0},
                   {"Z": 1.0, "n": 3.0, "K": 60.0, "mmu": 206.77, "M": 3670.48, "a0": 0.0529, "ke2": 1.44, "hc": 1239.8},
                   {"Z": 1.0, "n": 4.0, "K": 100.0, "mmu": 206.77, "M": 1836.15, "a0": 0.05292, "ke2": 1.4400, "hc": 1240.0}))


def s274_zeeman_outer_components() -> Structure:
    return Structure(
        "S274", "Separation of the outermost Zeeman components of an alkali D2 line", "atomic physics", "anomalous_zeeman_outer_components_weak_field",
        (_in("lam", "length", "nm", "wavelength of the D2 line in zero field", 589.0, (500.0, 900.0)),
         _in("B", "magnetic_field", "T", "magnitude of the uniform magnetic field", 0.50, (0.05, 1.0)),
         _in("gu", "dimensionless", "1", "Lande g-factor of the 2P3/2 level, a stated constant", 1.333, (1.32, 1.35), provenance="assumed"),
         _in("gl", "dimensionless", "1", "Lande g-factor of the 2S1/2 level, a stated constant", 2.002, (1.99, 2.01), provenance="assumed"),
         _in("e", "charge", "C", "elementary charge, a stated constant", 1.602e-19, (1.60e-19, 1.61e-19), provenance="assumed"),
         _in("hbar", "action", "J*s", "reduced Planck constant, a stated constant", 1.0546e-34, (1.05e-34, 1.06e-34), provenance="assumed"),
         _in("me", "mass", "kg", "electron mass, a stated constant", 9.109e-31, (9.10e-31, 9.12e-31), provenance="assumed"),
         _in("hc", "energy_length", "eV*nm", "product of the Planck constant and the speed of light, a stated constant", 1240.0, (1230.0, 1250.0),
             provenance="assumed"),
         _co("Eb", "energy", "eV", "Bohr magneton times the field", "e*hbar*B/(2*me)"),
         _co("dE", "energy", "eV", "energy separation of the two outermost components", "(gu + gl)*Eb"),
         _co("dlam", "length", "pm", "wavelength separation of the two outermost components", "lam**2*dE/hc")),
        "dlam",
        (Assumption("A-weak", "The field is weak enough that every level splits in proportion to the field, with all splittings much smaller than the "
                              "fine-structure splitting, so the Zeeman energy of a level is g m mu_B B.", "modelling", ("B",)),
         Assumption("A-components", "The six components of the 2P3/2 to 2S1/2 line, which obey the selection rule that the magnetic quantum number "
                                    "changes by 0 or 1, are all observed, and the outermost two are those with the largest and the smallest shift.",
                    "boundary_condition", ("gu", "gl")),
         Assumption("A-linear", "The wavelength separation follows from the energy separation to first order, dlam = lam^2 dE / (hc).", "modelling",
                    ("lam",)),
         Assumption("A-constants", "e, hbar, the electron mass and hc are the stated constants.", "modelling", ("e", "hbar", "me", "hc"))),
        _spec("A vapour of alkali-metal atoms in a uniform magnetic field of {B} T emits the longer-wavelength line of the principal doublet, the transition "
              "from the P level of total angular momentum three halves to the S level of total angular momentum one half, at a wavelength of {lam} nm in "
              "zero field. The Landé g-factor is {gu} for the P level and {gl} for the S level. "
              "The field is weak enough that every level splits in proportion to the field and all splittings are much smaller than the fine-structure "
              "splitting, and all six components of the line are observed. The wavelength shifts are small enough for a first-order treatment. "
              "Take e = {e} C, ħ = {hbar} J s, the electron mass {me} kg and hc = {hc} eV nm.",
              "What is the difference between the wavelengths of the two outermost components of the line?",
              "wavelength difference between the two outermost components", "pm",
              "A separate lamp B in another laboratory has two lines that are {v} {u} apart, but it is unrelated to this vapour.",
              "A reference vapour B has outermost components that are {v} {u} apart.",
              "A separate magnet B is rated at {v} {u}, but it plays no part in the splitting.", "W", equivalent="nm",
              formats={"e": ".4g", "hbar": ".5g", "me": ".4g", "gu": ".4g", "gl": ".4g"}),
        ("B", 1.5), _solve_zeeman_outer_separation, 8,
        "an enumeration of the six allowed components and the spread of their shifts, instead of the closed form (gu + gl) mu_B B",
        solver_rel_tol=1e-9,
        instances=({"lam": 589.0, "B": 0.50, "gu": 1.333, "gl": 2.002, "e": 1.602e-19, "hbar": 1.0546e-34, "me": 9.109e-31, "hc": 1240.0},
                   {"lam": 766.5, "B": 0.30, "gu": 1.333, "gl": 2.002, "e": 1.602e-19, "hbar": 1.0546e-34, "me": 9.109e-31, "hc": 1240.0},
                   {"lam": 780.2, "B": 0.45, "gu": 1.334, "gl": 2.0023, "e": 1.6022e-19, "hbar": 1.0546e-34, "me": 9.109e-31, "hc": 1239.8},
                   {"lam": 852.1, "B": 0.35, "gu": 1.333, "gl": 2.002, "e": 1.602e-19, "hbar": 1.055e-34, "me": 9.11e-31, "hc": 1240.0}))


def s275_box_slice_probability() -> Structure:
    return Structure(
        "S275", "Probability of finding an electron of a box state in a slice of the well", "quantum mechanics",
        "infinite_well_stationary_state_slice_probability",
        (_in("L", "length", "nm", "width of the well", 3.0, (1.0, 10.0)),
         _in("n", "count", "1", "quantum number of the stationary state of the electron", 2.0, (1.0, 6.0)),
         _in("x1", "length", "nm", "distance of the near edge of the slice from the left wall", 0.6, (0.05, 5.0)),
         _in("w", "length", "nm", "width of the slice", 0.9, (0.05, 5.0)),
         _co("u1", "dimensionless", "1", "phase n pi x / L at the near edge of the slice", "n*pi*x1/L"),
         _co("u2", "dimensionless", "1", "phase n pi x / L at the far edge of the slice", "n*pi*(x1 + w)/L"),
         _co("P", "dimensionless", "1", "probability of finding the electron in the slice", "w/L - (sin(2*u2) - sin(2*u1))/(2*n*pi)")),
        "P",
        (Assumption("A-well", "The walls are infinitely high and impenetrable, so the wavefunction vanishes at x = 0 and x = L and the stationary state "
                              "n has the probability density (2 / L) sin^2(n pi x / L).", "boundary_condition", ("L", "n")),
         Assumption("A-slice", "The slice lies inside the well, and the question asks for the probability that a measurement of the position finds "
                               "the electron in it.", "modelling", ("x1", "w"))),
        _spec("An electron is confined to a one-dimensional infinite square well of width {L} nm, with impenetrable walls, and is in the stationary state "
              "with quantum number n = {n}, counting the ground state as n equal to one. The position of the electron is measured with a probe that responds only "
              "within a slice of the well that begins {x1} nm from the left wall and is {w} nm wide.",
              "What is the probability that the probe finds the electron?", "probability of finding the electron in the slice", "1",
              "A separate electron B in another well is found in its slice with a probability of {v}, but it is unrelated to this electron.",
              "A reference electron B is found in its slice with a probability of {v}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the measurement.", "W",
              formats={"L": ".4g"}),
        ("w", 1.3), _solve_box_slice_probability, 4,
        "a numerical quadrature of the probability density over the slice, instead of the antiderivative with its sine terms",
        solver_rel_tol=1e-9,
        instances=({"L": 3.0, "n": 2.0, "x1": 0.6, "w": 0.9}, {"L": 2.0, "n": 1.0, "x1": 0.5, "w": 0.8},
                   {"L": 1.5, "n": 3.0, "x1": 0.3, "w": 0.45}, {"L": 4.0, "n": 3.0, "x1": 0.5, "w": 1.0}))


def s276_isotope_tunnelling_ratio() -> Structure:
    return Structure(
        "S276", "Ratio of the proton and deuteron currents transmitted through one barrier", "quantum mechanics",
        "isotope_tunnelling_ratio_rectangular_barrier",
        (_in("V", "energy", "eV", "height of the barrier above the kinetic energy of the incident particles", 0.40, (0.10, 1.0)),
         _in("a", "length", "pm", "thickness of the barrier", 30.0, (10.0, 100.0)),
         _in("mp", "mass", "u", "mass of the proton, a stated constant", 1.00728, (1.0, 1.01), provenance="assumed"),
         _in("md", "mass", "u", "mass of the deuteron, a stated constant", 2.01355, (2.0, 2.02), provenance="assumed"),
         _in("hbar", "action", "J*s", "reduced Planck constant, a stated constant", 1.0546e-34, (1.05e-34, 1.06e-34), provenance="assumed"),
         _co("kd", "wavenumber", "1/m", "decay constant of the deuteron wave inside the barrier", "sqrt(2*md*V)/hbar"),
         _co("kp", "wavenumber", "1/m", "decay constant of the proton wave inside the barrier", "sqrt(2*mp*V)/hbar"),
         _co("ratio", "dimensionless", "1", "ratio of the transmission of the proton to that of the deuteron", "exp(2*a*(kd - kp))")),
        "ratio",
        (Assumption("A-wkb", "The transmission of each particle is exp(-2 kappa a) with kappa = sqrt(2 m V) / hbar and no other factor.", "modelling",
                    ("V", "a")),
         Assumption("A-equal", "The two beams have equal numbers of particles per second and the same kinetic energy, which lies below the top of the "
                               "barrier, so the transmitted currents are in the ratio of the transmissions.", "boundary_condition", ("V",)),
         Assumption("A-barrier", "The barrier is rectangular with the same height and thickness for both particles.", "modelling", ("a",)),
         Assumption("A-constants", "The masses and hbar are the stated constants.", "modelling", ("mp", "md", "hbar"))),
        _spec("A beam of protons and a beam of deuterons, with equal numbers of particles per second and with the same kinetic energy, strike a "
              "rectangular potential barrier of thickness {a} pm. The top of the barrier is {V} eV above the kinetic energy of the particles, and the "
              "particles cross the barrier only by tunnelling. "
              "Take the probability that a particle passes through the barrier to be the exponential of minus twice the product of κ and the thickness, "
              "with κ equal to the square root of twice the product of the particle mass and the height, divided by ħ, and with no other factor, for each "
              "kind of particle. Take the proton mass to be {mp} u, the deuteron mass to be {md} u and ħ = {hbar} J s.",
              "What is the ratio of the transmitted proton current to the transmitted deuteron current?",
              "ratio of the transmitted proton current to the transmitted deuteron current", "1",
              "A separate pair of beams B in another apparatus has a transmitted current ratio of {v}, but it is unrelated to these beams.",
              "A reference pair of beams B has a transmitted current ratio of {v}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the tunnelling.", "W",
              formats={"mp": ".6g", "md": ".6g", "hbar": ".5g"}),
        ("V", 1.5), _solve_isotope_tunnelling_ratio, 5,
        "the exponent of each transmission as a quadrature of the decay constant over the barrier, instead of the closed form with the difference of the decay constants",
        solver_rel_tol=1e-9,
        instances=({"V": 0.40, "a": 30.0, "mp": 1.00728, "md": 2.01355, "hbar": 1.0546e-34},
                   {"V": 0.30, "a": 40.0, "mp": 1.00728, "md": 2.01355, "hbar": 1.0546e-34},
                   {"V": 0.60, "a": 25.0, "mp": 1.0073, "md": 2.0136, "hbar": 1.0546e-34},
                   {"V": 0.35, "a": 35.0, "mp": 1.00728, "md": 2.01355, "hbar": 1.055e-34}))


def s277_pion_survival_fraction() -> Structure:
    return Structure(
        "S277", "Fraction of a pion beam that survives a decay tube", "special relativity", "relativistic_decay_in_flight_survival_fraction",
        (_in("pc", "energy", "GeV", "momentum of a pion times the speed of light", 4.0, (0.5, 20.0)),
         _in("mc2", "energy", "MeV", "rest energy of the charged pion, a stated constant", 139.57, (139.0, 140.0), provenance="assumed"),
         _in("tau0", "time", "ns", "mean lifetime of the charged pion at rest, a stated constant", 26.03, (25.5, 26.5), provenance="assumed"),
         _in("Lp", "length", "m", "length of the tube that the pions fly through", 100.0, (10.0, 500.0)),
         _in("c", "speed", "m/s", "speed of light, a stated constant", 2.998e8, (2.99e8, 3.00e8), provenance="assumed"),
         _co("gb", "dimensionless", "1", "product of gamma and beta of the pions", "pc/mc2"),
         _co("Ld", "length", "m", "mean decay length of the pions in the laboratory", "gb*c*tau0"),
         _co("F", "dimensionless", "1", "fraction of the pions that have not decayed at the end of the tube", "exp(-Lp/Ld)")),
        "F",
        (Assumption("A-decay", "A pion is lost only by decay, with the exponential law in its proper time, and the pions neither interact with anything "
                               "nor are absorbed along the tube.", "modelling", ("tau0",)),
         Assumption("A-straight", "All pions have the same momentum and fly along the axis of the tube at constant speed, and the survivors are those "
                                  "that have not decayed.", "boundary_condition", ("pc", "Lp")),
         Assumption("A-constants", "The pion rest energy, its lifetime and the speed of light are the stated constants.", "modelling",
                    ("mc2", "tau0", "c"))),
        _spec("A beam of charged pions, each with a momentum such that its momentum times the speed of light is {pc} GeV, flies along the axis of an "
              "evacuated tube of length {Lp} m. A pion is lost only by decay, which follows the exponential law in the time that a clock carried by "
              "the pion would show, and the pions neither interact with anything nor are absorbed along the tube. All pions have the same momentum "
              "and move at constant speed. Take the pion rest energy to be {mc2} MeV, its mean lifetime at rest to be {tau0} ns and c = {c} m/s.",
              "What fraction of the pions reaches the end of the tube without having decayed?", "fraction of the pions that reach the end of the tube",
              "1",
              "A separate beam B in another tube has a surviving fraction of {v}, but it is unrelated to this beam.",
              "A reference beam B has a surviving fraction of {v}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the decay.", "W",
              formats={"c": ".4g", "mc2": ".5g"}),
        ("Lp", 1.5), _solve_pion_survival, 5,
        "gamma and beta from the energy and momentum, the flight time in the laboratory and the proper time on the way, instead of the decay length gamma beta c tau",
        solver_rel_tol=1e-9,
        instances=({"pc": 4.0, "mc2": 139.57, "tau0": 26.03, "Lp": 100.0, "c": 2.998e8},
                   {"pc": 2.5, "mc2": 139.57, "tau0": 26.03, "Lp": 60.0, "c": 2.998e8},
                   {"pc": 8.0, "mc2": 139.6, "tau0": 26.0, "Lp": 250.0, "c": 2.997e8},
                   {"pc": 1.8, "mc2": 139.57, "tau0": 26.03, "Lp": 40.0, "c": 2.998e8}))


def s278_threshold_kinetic_energy() -> Structure:
    return Structure(
        "S278", "Threshold kinetic energy of a beam particle on a target at rest", "special relativity", "fixed_target_reaction_threshold_invariant_mass",
        (_in("m1", "energy", "MeV", "rest energy of the beam particle", 938.27, (100.0, 2000.0)),
         _in("m2", "energy", "MeV", "rest energy of the target particle", 938.27, (100.0, 2000.0)),
         _in("Q", "energy", "MeV", "excess of the total rest energy of the final particles over that of the beam and target particles", 134.98,
             (1.0, 3000.0)),
         _co("W", "energy", "MeV", "total rest energy of the final particles", "m1 + m2 + Q"),
         _co("Eb", "energy", "MeV", "total energy of the beam particle at threshold", "(W**2 - m1**2 - m2**2)/(2*m2)"),
         _co("K", "energy", "MeV", "threshold kinetic energy of the beam particle", "Eb - m1")),
        "K",
        (Assumption("A-threshold", "At threshold the final particles are produced together at rest relative to each other, so their invariant mass is "
                                   "the total rest energy W and the energy of the final state is carried by their common motion.", "boundary_condition",
                    ("Q",)),
         Assumption("A-target", "The target particle is free and at rest in the laboratory, and energy and momentum are conserved.", "boundary_condition",
                    ("m2",))),
        _spec("A beam particle of rest energy {m1} MeV strikes a free target particle of rest energy {m2} MeV that is at rest in the laboratory. The "
              "reaction produces final particles whose total rest energy exceeds the total rest energy of the beam and target particles by {Q} MeV. "
              "Energy and momentum are conserved, and the reaction runs at its threshold, so that the final particles move together with no motion "
              "relative to each other.",
              "What is the smallest kinetic energy that the beam particle needs for the reaction to occur?",
              "smallest kinetic energy of the beam particle", "MeV",
              "A separate reaction B in another experiment has a threshold of {v} {u}, but it is unrelated to this reaction.",
              "A reference reaction B has a threshold kinetic energy of {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the reaction.", "W", equivalent="GeV"),
        ("Q", 1.5), _solve_threshold_energy, 3,
        "a root finder on the beam kinetic energy that makes the invariant mass of the beam and target equal the final rest energy, instead of the closed form",
        solver_rel_tol=1e-9,
        instances=({"m1": 938.27, "m2": 938.27, "Q": 134.98}, {"m1": 938.27, "m2": 938.27, "Q": 1876.54},
                   {"m1": 139.57, "m2": 938.27, "Q": 535.45}, {"m1": 493.68, "m2": 938.27, "Q": 881.05}))


def s279_rotor_transverse_doppler() -> Structure:
    return Structure(
        "S279", "Transverse Doppler shift of gamma rays from the rim of a rotor", "special relativity", "rotor_transverse_doppler_shift_gamma_rays",
        (_in("frot", "frequency", "Hz", "rotation frequency of the rotor", 600.0, (100.0, 1500.0)),
         _in("R", "length", "cm", "radius of the circle on which the source moves", 12.0, (2.0, 40.0)),
         _in("E0", "energy", "keV", "energy of the gamma-ray photons in the rest frame of the source", 14.4, (5.0, 120.0)),
         _in("h", "action", "eV*s", "Planck constant, a stated constant", 4.1357e-15, (4.13e-15, 4.14e-15), provenance="assumed"),
         _in("c", "speed", "m/s", "speed of light, a stated constant", 2.998e8, (2.99e8, 3.00e8), provenance="assumed"),
         _co("v", "speed", "m/s", "speed of the source on the rim", "2*pi*frot*R"),
         _co("f0", "frequency", "Hz", "frequency of the gamma rays in the rest frame of the source", "E0/h"),
         _co("df", "frequency", "MHz", "decrease of the frequency at the absorber", "f0*v**2/(2*c**2)")),
        "df",
        (Assumption("A-geometry", "The rotor turns at a constant rate, the source moves on a circle of the stated radius, and the absorber is at rest on "
                                  "the axis; the gamma rays travel in a straight line in the laboratory from the source to the absorber.",
                    "boundary_condition", ("frot", "R")),
         Assumption("A-leading", "The shift is evaluated to leading order in (v/c)^2, which is f0 v^2 / (2 c^2) for the decrease of the frequency.",
                    "modelling", ("c",)),
         Assumption("A-constants", "h and c are the stated constants.", "modelling", ("h", "c"))),
        _spec("A source of gamma rays is fixed to the rim of a rotor and moves on a circle of radius {R} cm at a constant rotation frequency of "
              "{frot} Hz. The photons have an energy of {E0} keV in the rest frame of the source. An absorber at rest on the axis of the rotor receives "
              "the gamma rays, which travel from the source to the absorber along a straight line in the laboratory. Evaluate the shift to leading order "
              "in v/c. Take h = {h} eV s and c = {c} m/s.",
              "By how much is the frequency of the gamma rays at the absorber below their frequency in the rest frame of the source?",
              "decrease of the frequency at the absorber", "MHz",
              "A separate source B in another experiment shows a frequency shift of {v} {u}, but it is unrelated to this rotor.",
              "A reference rotor B gives a frequency shift of {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the shift.", "W", equivalent="kHz",
              formats={"h": ".5g", "c": ".4g"}),
        ("R", 1.5), _solve_rotor_doppler_shift, 5,
        "the exact shift f0 (1 - sqrt(1 - beta^2)) written with a logarithm and an exponential that keep the digits for a tiny beta, instead of the leading-order form",
        solver_rel_tol=1e-9,
        instances=({"frot": 600.0, "R": 12.0, "E0": 14.4, "h": 4.1357e-15, "c": 2.998e8},
                   {"frot": 1000.0, "R": 8.0, "E0": 23.9, "h": 4.1357e-15, "c": 2.998e8},
                   {"frot": 350.0, "R": 25.0, "E0": 6.2, "h": 4.136e-15, "c": 2.997e8},
                   {"frot": 800.0, "R": 15.0, "E0": 67.0, "h": 4.1357e-15, "c": 2.998e8}))


def s280_hohmann_total_speed_change() -> Structure:
    return Structure(
        "S280", "Total speed change of a Hohmann transfer between two circular orbits", "gravitation", "hohmann_transfer_total_delta_v_vis_viva",
        (_in("g0", "acceleration", "m/s^2", "gravitational acceleration at the surface of the planet, a stated constant", 1.62, (1.5, 10.0),
             provenance="assumed"),
         _in("Rp", "length", "km", "radius of the planet, a stated constant", 1737.0, (1500.0, 7000.0), provenance="assumed"),
         _in("h1", "length", "km", "altitude of the initial circular orbit", 100.0, (100.0, 1000.0)),
         _in("h2", "length", "km", "altitude of the final circular orbit", 2500.0, (1000.0, 50000.0)),
         _co("r1", "length", "km", "radius of the initial orbit", "Rp + h1"),
         _co("r2", "length", "km", "radius of the final orbit", "Rp + h2"),
         _co("v1", "speed", "km/s", "speed in the initial circular orbit", "Rp*sqrt(g0/r1)"),
         _co("v2", "speed", "km/s", "speed in the final circular orbit", "Rp*sqrt(g0/r2)"),
         _co("vp", "speed", "km/s", "speed at the nearest point of the transfer ellipse", "v1*sqrt(2*r2/(r1 + r2))"),
         _co("va", "speed", "km/s", "speed at the farthest point of the transfer ellipse", "v2*sqrt(2*r1/(r1 + r2))"),
         _co("dv", "speed", "km/s", "sum of the speed changes of the two burns", "(vp - v1) + (v2 - va)")),
        "dv",
        (Assumption("A-field", "The planet is a uniform sphere whose gravity follows the inverse-square law with the stated surface value and radius; the "
                               "orbits are circular and coplanar, and no other body and no atmosphere act on the spacecraft.", "modelling",
                    ("g0", "Rp")),
         Assumption("A-impulsive", "Each burn is so short compared with the orbital period that it is treated as an instantaneous change of speed along "
                                   "the direction of motion, at the nearest point and at the farthest point of the transfer ellipse.",
                    "boundary_condition", ("h1", "h2")),
         Assumption("A-hohmann", "The transfer orbit is the ellipse that touches the initial circle at its nearest point and the final circle at its "
                                 "farthest point.", "modelling", ("h1", "h2"))),
        _spec("A spacecraft moves in a circular orbit at an altitude of {h1} km above a planet of radius {Rp} km, with gravitational acceleration "
              "{g0} m/s² at the surface of the planet. It is moved to a circular orbit at an altitude of {h2} km in the same plane by two engine burns "
              "along the direction of motion: the first puts it on the ellipse that touches the initial circle at its nearest point and the final "
              "circle at its farthest point, and the second, at the farthest point, makes the orbit circular. The pull of the planet follows the "
              "inverse-square law, the planet has no atmosphere, no other body acts, and each burn is so short compared with the orbital period that it "
              "is treated as an instantaneous change of speed.",
              "What is the total change of speed that the two burns supply?", "total change of speed of the two burns", "km/s",
              "A separate rocket B in another programme has a total speed change of {v} {u}, but it is unrelated to this spacecraft.",
              "A reference transfer B needs a total speed change of {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the transfer.", "W", equivalent="m/s",
              formats={"Rp": ".0f", "h1": ".0f", "h2": ".0f"}),
        ("h1", 3.0), _solve_hohmann_delta_v, 4,
        "the vis-viva equation on the circular orbits and on the transfer ellipse with its semi-major axis, instead of the scaling of the circular speed by the factor sqrt(2 r2 / (r1 + r2))",
        solver_rel_tol=1e-9,
        instances=({"g0": 1.62, "Rp": 1737.0, "h1": 100.0, "h2": 2500.0}, {"g0": 9.81, "Rp": 6371.0, "h1": 300.0, "h2": 35786.0},
                   {"g0": 3.71, "Rp": 3390.0, "h1": 400.0, "h2": 17000.0}, {"g0": 3.70, "Rp": 2440.0, "h1": 200.0, "h2": 6000.0}))


def s281_escape_speed_from_density() -> Structure:
    return Structure(
        "S281", "Escape speed of a uniform planet from its density and radius", "gravitation", "escape_speed_uniform_sphere_scaled_to_earth",
        (_in("rho", "density", "g/cm^3", "mean density of the planet", 3.93, (0.5, 10.0)),
         _in("R", "length", "km", "radius of the planet", 3390.0, (500.0, 20000.0)),
         _in("ve", "speed", "km/s", "escape speed from the surface of the Earth, a stated constant", 11.19, (11.1, 11.3), provenance="assumed"),
         _in("rhoE", "density", "g/cm^3", "mean density of the Earth, a stated constant", 5.51, (5.4, 5.6), provenance="assumed"),
         _in("RE", "length", "km", "radius of the Earth, a stated constant", 6371.0, (6300.0, 6400.0), provenance="assumed"),
         _co("x", "dimensionless", "1", "radius of the planet in Earth radii", "R/RE"),
         _co("y", "dimensionless", "1", "density of the planet in Earth densities", "rho/rhoE"),
         _co("vesc", "speed", "km/s", "escape speed from the surface of the planet", "ve*x*sqrt(y)")),
        "vesc",
        (Assumption("A-uniform", "The planet and the Earth are uniform spheres, each with its stated mean density, so that the mass is proportional to "
                                 "the density and the cube of the radius.", "modelling", ("rho", "R")),
         Assumption("A-escape", "Escape is from the surface to infinity with just enough speed to arrive at rest; the planet does not rotate and has "
                                "no atmosphere, and no other body acts.", "boundary_condition", ("R",)),
         Assumption("A-constants", "The escape speed, the mean density and the radius of the Earth are the stated constants.", "modelling",
                    ("ve", "rhoE", "RE"))),
        _spec("A probe is to be launched from the surface of a planet so that it just escapes to infinity. The planet is a uniform sphere of radius {R} km "
              "and mean density {rho} g/cm³, it does not rotate and has no atmosphere, and the pull of any other body is ignored. The Earth is likewise "
              "a uniform sphere, of radius {RE} km and mean density {rhoE} g/cm³, with an escape speed of {ve} km/s at its surface.",
              "What speed must the probe have at launch to escape from the surface of the planet?", "launch speed for escape from the planet", "km/s",
              "A separate probe B launched from another planet needs {v} {u}, but it is unrelated to this probe.",
              "A reference probe B needs a launch speed of {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the launch.", "W", equivalent="m/s",
              formats={"R": ".0f", "RE": ".0f"}),
        ("R", 1.3), _solve_escape_speed_scaled, 5,
        "the mass of the planet from the ratio of the densities and the cubes of the radii, then the speed from sqrt(2 G M / R) as a ratio to the Earth value",
        solver_rel_tol=1e-9,
        instances=({"rho": 3.93, "R": 3390.0, "ve": 11.19, "rhoE": 5.51, "RE": 6371.0}, {"rho": 5.24, "R": 6052.0, "ve": 11.19, "rhoE": 5.51, "RE": 6371.0},
                   {"rho": 3.34, "R": 1737.0, "ve": 11.2, "rhoE": 5.5, "RE": 6371.0}, {"rho": 5.43, "R": 2440.0, "ve": 11.19, "rhoE": 5.51, "RE": 6371.0}))


def s282_star_luminosity_from_wien_peak() -> Structure:
    return Structure(
        "S282", "Luminosity of a star from the peak of its spectrum and its radius", "astrophysics", "star_luminosity_wien_stefan_scaled_to_sun",
        (_in("lam", "length", "nm", "wavelength at which the spectrum of the star peaks", 292.0, (200.0, 1000.0)),
         _in("R", "dimensionless", "1", "radius of the star in solar radii", 1.71, (0.3, 5.0)),
         _in("Tsun", "temperature", "K", "surface temperature of the Sun, a stated constant", 5772.0, (5700.0, 5800.0), provenance="assumed"),
         _in("lamsun", "length", "nm", "wavelength at which the spectrum of the Sun peaks, a stated constant", 502.0, (495.0, 510.0),
             provenance="assumed"),
         _co("T", "temperature", "K", "surface temperature of the star", "Tsun*lamsun/lam"),
         _co("A", "dimensionless", "1", "surface area of the star in solar areas", "R**2"),
         _co("L", "dimensionless", "1", "luminosity of the star in solar luminosities", "A*(T/Tsun)**4")),
        "L",
        (Assumption("A-blackbody", "The star and the Sun radiate as black bodies from their surfaces, so the power is proportional to the area and to the "
                                   "fourth power of the surface temperature.", "modelling", ("R", "Tsun")),
         Assumption("A-wien", "The wavelength of the peak of the spectrum is inversely proportional to the surface temperature (Wien's law), with the "
                              "stated values for the Sun as the scale.", "modelling", ("lam", "lamsun")),
         Assumption("A-constants", "The surface temperature and the peak wavelength of the Sun are the stated constants.", "modelling",
                    ("Tsun", "lamsun"))),
        _spec("A star radiates as a black body from its surface, and the peak of its spectrum is at a wavelength of {lam} nm. Its radius is {R} times "
              "the radius of the Sun. The Sun radiates as a black body, with a surface temperature of {Tsun} K and a spectrum that peaks at a wavelength "
              "of {lamsun} nm, and the peak wavelength of a black body is inversely proportional to its surface temperature.",
              "How many times the luminosity of the Sun is the luminosity of the star?", "luminosity of the star in solar luminosities", "1",
              "A separate star B in another catalogue has a luminosity of {v} solar luminosities, but it is unrelated to this star.",
              "A reference star B has a luminosity of {v} solar luminosities.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the radiation of the star.", "W",
              formats={"Tsun": ".4g"}),
        ("R", 1.3), _solve_star_luminosity, 4,
        "the absolute radiated power 4 pi R^2 sigma T^4 of the star and of the Sun with Wien's law written as a constant, divided by each other, instead of the ratio of areas and temperatures",
        solver_rel_tol=1e-9,
        instances=({"lam": 292.0, "R": 1.71, "Tsun": 5772.0, "lamsun": 502.0}, {"lam": 302.0, "R": 2.36, "Tsun": 5772.0, "lamsun": 502.0},
                   {"lam": 444.0, "R": 2.05, "Tsun": 5770.0, "lamsun": 501.0}, {"lam": 551.0, "R": 0.86, "Tsun": 5772.0, "lamsun": 502.0}))


ALL = (s273_muon_capture_photon, s274_zeeman_outer_components, s275_box_slice_probability, s276_isotope_tunnelling_ratio,
       s277_pion_survival_fraction, s278_threshold_kinetic_energy, s279_rotor_transverse_doppler, s280_hohmann_total_speed_change,
       s281_escape_speed_from_density, s282_star_luminosity_from_wien_peak)


def all_structures() -> list[Structure]:
    return [factory() for factory in ALL]


STRUCTURES: dict[str, Structure] = {s.structure_id: s for s in all_structures()}

# --- gold solution plans ----------------------------------------------------------------------------------------------------------

PLANS: dict[str, Plan] = {
    "S273": Plan(
        approach="The muon and the nucleus form a hydrogen-like atom whose orbit is smaller than the electron's by the reduced mass and the charge. "
                 "The photon carries away the binding energy of the level and the kinetic energy that the muon had, so find the reduced mass, the "
                 "orbit radius, the binding energy, the photon energy and then the wavelength.",
        steps=(
            Step("mu", "Reduced mass of a two-body system, mu = m1 m2 / (m1 + m2), here in electron masses",
                 "The muon and the nucleus both move about their common centre of mass, so the Bohr levels are those of one particle of the reduced "
                 "mass in the field of the nucleus."),
            Step("r", "Bohr orbit radius for the reduced mass, r = n^2 a0 / (Z mu)",
                 "The Bohr radius a0 belongs to an electron of one electron mass bound to a proton; a heavier reduced mass shrinks the orbit in "
                 "proportion and a larger charge shrinks it again."),
            Step("Eb", "Coulomb binding energy of a circular orbit, E = Z ke2 / (2 r)",
                 "For a circular Coulomb orbit the kinetic energy is half the magnitude of the potential energy, so the binding energy is half "
                 "the Coulomb energy at the orbit radius."),
            Step("Eph", "Energy conservation at the capture, E_photon = K + E_binding",
                 "The muon starts with the kinetic energy K relative to the nucleus and ends in a bound level; the photon carries off the whole "
                 "difference, the recoil of the atom being neglected."),
            Step("lam", "Planck-Einstein relation, lambda = h c / E",
                 "With hc in eV nm and the photon energy in eV the wavelength comes out in nm, which is converted to pm."),
        ),
        check="Limiting cases: for a very heavy nucleus and an electron in place of the muon the binding energy tends to 13.6 eV Z^2 / n^2; "
              "for K = 0 the photon energy is the binding energy alone, about 0.63 keV for muonic hydrogen with n = 2, and the "
              "wavelength is of the order of a nanometre."),
    "S274": Plan(
        approach="Each level shifts by g m mu_B B in a weak field. The six components of the 2P3/2 to 2S1/2 line shift by g_u m_u - g_l m_l Bohr "
                 "magnetons B for changes of m by 0 or 1, and the two outermost components are the two with the extreme shifts, which are "
                 "+(g_u + g_l)/2 and -(g_u + g_l)/2 Bohr magnetons B, so their separation is (g_u + g_l) mu_B B. Convert the energy separation to "
                 "a wavelength separation.",
        steps=(
            Step("Eb", "Bohr magneton times the field, mu_B B = e hbar B / (2 m_e)",
                 "The Zeeman energy of a level is g m mu_B B, so this is the unit in which all shifts of the components are counted."),
            Step("dE", "Selection rule and extreme components: the largest shift is (g_u + g_l)/2 mu_B B (m_u = 1/2 to m_l = -1/2) and the smallest is its negative",
                 "The shifts of the six allowed components are plus and minus 5/3, 1 and 1/3 Bohr magnetons B for g_u = 4/3 and g_l = 2; the outermost "
                 "two are plus and minus (g_u + g_l)/2, which differ by g_u + g_l."),
            Step("dlam", "Differential of lambda = hc / E, d lambda = lambda^2 dE / (hc)",
                 "A small change of the photon energy changes the wavelength by lambda^2 / (hc) times the energy change, to first order."),
        ),
        check="Order of magnitude: mu_B B is 29 micro-eV at 0.5 T, so the energy separation is about 0.1 meV and the wavelength separation about "
              "0.03 nm for the sodium D2 line. The separation is proportional to the field and to the square of the wavelength."),
    "S275": Plan(
        approach="The probability of finding the electron in the slice is the integral of the probability density (2 / L) sin^2(n pi x / L) over the "
                 "slice. Write the integral with the phases n pi x / L at the two edges and evaluate the antiderivative.",
        steps=(
            Step("u1", "Phase of the stationary-state wavefunction, n pi x / L, at the near edge",
                 "The state n is sin(n pi x / L) times a constant, so the phase at the near edge sets the lower limit of the integral."),
            Step("u2", "Phase of the stationary-state wavefunction, n pi x / L, at the far edge",
                 "The far edge of the slice is at x1 + w, and its phase sets the upper limit."),
            Step("P", "Integral of the probability density, P = integral of (2 / L) sin^2(n pi x / L) dx = w / L - [sin(2 u2) - sin(2 u1)] / (2 n pi)",
                 "Writing sin^2 as (1 - cos 2 theta) / 2 gives a uniform part, w / L, and an oscillating part that depends on the phases at the edges."),
        ),
        check="Limiting cases: for a slice that covers the whole well (x1 = 0, w = L) the probability is 1; for a narrow slice it tends to the density "
              "at its centre times the width, and for a large n the oscillating part is small and the probability tends to the classical value w / L."),
    "S276": Plan(
        approach="Inside the barrier the wave of each particle decays with the constant kappa = sqrt(2 m V) / hbar, and the transmission is exp(-2 kappa a). "
                 "The transmitted currents of equal incident beams are in the ratio of the transmissions, so find the two decay constants and the "
                 "exponential of the difference of the exponents.",
        steps=(
            Step("kd", "Decay constant of the wave in a barrier, kappa = sqrt(2 m V) / hbar, for the deuteron mass",
                 "The deuteron has about twice the mass, so its decay constant is larger by the square root of the mass ratio."),
            Step("kp", "Decay constant of the wave in a barrier, kappa = sqrt(2 m V) / hbar, for the proton mass",
                 "The Schroedinger equation inside the barrier gives an exponentially decaying wave whose rate depends on the mass and on how far "
                 "the barrier top is above the kinetic energy."),
            Step("ratio", "Ratio of the transmissions, exp(-2 kp a) / exp(-2 kd a) = exp(2 a (kd - kp))",
                 "With equal incident currents the transmitted currents are in the ratio of the transmissions, so the ratio is the exponential of the "
                 "difference of the exponents."),
        ),
        check="Limiting cases: for a vanishing thickness the ratio tends to 1, and it grows exponentially with the thickness; it is greater than 1 "
              "because the lighter particle tunnels more easily. For a ratio of the masses of two it is exp(2 a kp (sqrt(2) - 1))."),
    "S277": Plan(
        approach="The pions are relativistic, so a clock carried by a pion runs slowly and the mean decay length in the laboratory is gamma beta c tau0. "
                 "Find gamma beta from the momentum and the rest energy, then the decay length, then the surviving fraction from the exponential law.",
        steps=(
            Step("gb", "Relativistic momentum, p = gamma m v, so pc / (m c^2) = gamma beta",
                 "Dividing the momentum times c by the rest energy gives the product of gamma and beta directly, with no need for the speed."),
            Step("Ld", "Time dilation, decay length = gamma beta c tau0",
                 "In the laboratory the mean lifetime is gamma tau0 and the speed is beta c, so the mean distance covered before decay is gamma beta c tau0."),
            Step("F", "Exponential decay law along the path, N / N0 = exp(-L / L_decay)",
                 "The fraction of pions that have not decayed after the length Lp is the exponential of minus the length in units of the decay length."),
        ),
        check="Limiting cases: for a zero length the fraction is 1, and for a tube much longer than the decay length it tends to 0. The decay length is "
              "gamma beta times 7.8 m, about 224 m at 4 GeV, so a 100 m tube transmits about 64 percent."),
    "S278": Plan(
        approach="At threshold the final particles move together, so the invariant mass of the beam and target particles equals the final rest energy. "
                 "Find the total final rest energy, then the beam energy from the invariant mass of a particle on a target at rest, then the kinetic energy.",
        steps=(
            Step("W", "Rest energy of the final state, W = m1 + m2 + Q",
                 "The final particles carry the rest energy of the beam and target particles plus the excess Q."),
            Step("Eb", "Invariant mass of the beam and target, W^2 = m1^2 + m2^2 + 2 E_b m2",
                 "The invariant (E_total^2 - (p_total c)^2) is the same in every frame; in the laboratory the target has energy m2 and no momentum, and at "
                 "threshold it equals the square of the final rest energy, which gives the beam energy."),
            Step("K", "Kinetic energy is the total energy minus the rest energy, K = E_b - m1",
                 "The question asks for the kinetic energy of the beam particle, not its total energy."),
        ),
        check="Limiting case: for a small excess the threshold tends to Q (m1 + m2) / m2, which is 2 Q for equal masses; for the pi0 in "
              "proton-proton collisions it is about 280 MeV, a little more than twice the pion rest energy, because the final state must also carry momentum."),
    "S279": Plan(
        approach="In the laboratory the source moves at the speed v of the rim while the gamma rays travel radially to the absorber, so the photons are "
                 "emitted at right angles to the velocity of the source. Their frequency is then lower than the rest-frame frequency by the factor "
                 "1 / gamma, which to leading order is a decrease of f0 v^2 / (2 c^2).",
        steps=(
            Step("f0", "Photon energy and frequency, E = h f",
                 "The frequency of the photons in the rest frame of the source is the photon energy over Planck's constant."),
            Step("v", "Speed on a circle, v = 2 pi f R",
                 "The source goes round a circle of radius R once per rotation period 1 / f."),
            Step("df", "Transverse Doppler effect (time dilation), f_obs = f0 / gamma, so f0 - f_obs = f0 (1 - 1/gamma) = f0 v^2 / (2 c^2) to leading order",
                 "A photon that travels at right angles to the velocity of its source in the laboratory shows only the time dilation of the source, "
                 "so its frequency is lowered by gamma and, for v much less than c, by the fraction v^2 / (2 c^2)."),
        ),
        check="Order of magnitude: a speed of 450 m/s gives (v/c)^2 / 2 of about 1e-12 and, for gamma rays of frequency near 3.5e18 Hz, a shift of a "
              "few MHz; the shift grows with the square of the rotation frequency and of the radius."),
    "S280": Plan(
        approach="The two burns change the speed from the circular speed to the speed on the transfer ellipse and back to the circular speed of the "
                 "final orbit. Find the orbit radii and circular speeds, the speeds at the ends of the transfer ellipse, and add the two changes of speed.",
        steps=(
            Step("r1", "Orbit radius from the centre, r = R_p + h",
                 "The altitude is measured from the surface, while the orbit equations use the distance from the centre of the planet."),
            Step("r2", "Orbit radius from the centre, r = R_p + h",
                 "The same relation gives the radius of the final orbit."),
            Step("v1", "Circular orbit: v^2 / r = G M / r^2, with G M = g0 R_p^2",
                 "The gravitational pull supplies the centripetal force; G M is found from the surface gravity, so v = R_p sqrt(g0 / r)."),
            Step("v2", "Circular orbit: v^2 / r = G M / r^2, with G M = g0 R_p^2",
                 "The same relation gives the speed in the final circular orbit, which is lower."),
            Step("va", "Conservation of angular momentum, v_a = v_p r1 / r2, equivalently v2 sqrt(2 r1 / (r1 + r2))",
                 "At the farthest point the speed on the ellipse is below the circular speed of the final orbit, so the second burn adds speed too."),
            Step("vp", "Conservation of energy and of angular momentum on the transfer ellipse, v_p = v1 sqrt(2 r2 / (r1 + r2))",
                 "At the nearest point the speed on an ellipse of semi-major axis (r1 + r2) / 2 follows from the vis-viva equation; it exceeds the "
                 "circular speed, so the first burn adds speed."),
            Step("dv", "Sum of the speed changes of the two burns, (v_p - v1) + (v2 - v_a)",
                 "The two burns are along the direction of motion, and each changes the speed by the difference of the speeds before and after it."),
        ),
        check="Limiting case: for r2 close to r1 both changes of speed tend to zero; from a low orbit around the Earth to the geostationary orbit the "
              "total is about 3.9 km/s, of which the first burn supplies about 2.4 km/s."),
    "S281": Plan(
        approach="The escape speed is sqrt(2 G M / R), and for a uniform sphere the mass is proportional to the density and the cube of the radius, so the "
                 "speed is proportional to the radius and to the square root of the density. Scale the known value for the Earth by these two ratios.",
        steps=(
            Step("x", "Ratio of the radii, R / R_E",
                 "For a uniform sphere M = (4 pi / 3) rho R^3, so M / R = (4 pi / 3) rho R^2 and the escape speed varies as R sqrt(rho)."),
            Step("y", "Ratio of the densities, rho / rho_E",
                 "The mass also depends on the density, in proportion, so the speed is scaled by the square root of this ratio."),
            Step("vesc", "Escape speed of a uniform sphere, v = sqrt(8 pi G rho / 3) R, scaled to the Earth: v = v_E (R / R_E) sqrt(rho / rho_E)",
                 "Energy conservation gives v^2 / 2 = G M / R; the ratio of this to the Earth value removes G."),
        ),
        check="Limiting cases: for the Earth's own radius and density the result is the Earth's escape speed, 11.2 km/s; the speed is proportional to the radius "
              "at fixed density, and a planet of the Moon's size and rock density has an escape speed of about 2.4 km/s."),
    "S282": Plan(
        approach="Wien's law gives the surface temperature of the star from the Sun's by the ratio of the peak wavelengths, and the Stefan-Boltzmann law "
                 "makes the luminosity proportional to the surface area and to the fourth power of the temperature. Write everything as ratios to the Sun.",
        steps=(
            Step("A", "Area of a sphere, 4 pi R^2, relative to the Sun, so A = (R / R_sun)^2",
                 "The radiating area is proportional to the square of the radius, and the radius is given in solar radii."),
            Step("T", "Wien's displacement law, lambda_peak T = constant, so T = T_sun lambda_sun / lambda",
                 "A black body of half the peak wavelength has twice the surface temperature, and the Sun supplies the constant."),
            Step("L", "Stefan-Boltzmann law, L = 4 pi R^2 sigma T^4, relative to the Sun: L / L_sun = (R / R_sun)^2 (T / T_sun)^4",
                 "The constant sigma cancels in the ratio, so the luminosity in solar units is the ratio of areas times the fourth power of the ratio of temperatures."),
        ),
        check="Limiting cases: for the radius and the peak wavelength of the Sun the luminosity is one solar luminosity; doubling the radius multiplies it "
              "by 4 and halving the peak wavelength multiplies it by 16."),
}

LEVELS: dict[str, str] = {
    "S273": "intro_university", "S274": "upper_university", "S275": "upper_university", "S276": "upper_university",
    "S277": "intro_university", "S278": "upper_university", "S279": "upper_university", "S280": "upper_university",
    "S281": "intro_university", "S282": "intro_university",
}

TOPICS: dict[str, str] = {
    "S273": "Bohr levels of a muonic atom with the reduced mass and the photon emitted in a radiative capture",
    "S274": "anomalous Zeeman effect: the six components of the D2 line of an alkali atom in a weak magnetic field",
    "S275": "particle in an infinite one-dimensional well: the probability of finding the particle in a slice",
    "S276": "tunnelling through a rectangular barrier: the isotope effect for a proton and a deuteron",
    "S277": "time dilation of unstable particles in flight: the surviving fraction of a pion beam in a decay tube",
    "S278": "relativistic kinematics of a fixed-target reaction: the threshold kinetic energy from the invariant mass",
    "S279": "transverse Doppler effect and time dilation: the frequency shift of gamma rays from the rim of a rotor",
    "S280": "orbital mechanics of the Hohmann transfer: the total speed change from the vis-viva equation",
    "S281": "gravitation of a uniform sphere: the escape speed of a planet from its density and radius",
    "S282": "Wien's law and the Stefan-Boltzmann law: the luminosity of a star from its spectral peak and radius",
}
