"""M250 phase 2, batch extra: twelve new DECOY-v2 structures S251 to S262 (gravitation, acoustics, solid state, nuclear, fluids, statistics).

Written for the M250 exploration pool (plan of record v2.2). Same pattern as `lib_thermodynamics.py`: a typed graph of input and computed
nodes, an independently coded numeric solver (quadrature, root finder, matrix exponential, a linear system, an ODE integration), four
numeric instantiations and a relevant edit that moves the answer. Every stated physical constant is an input node with provenance
"assumed". Every answer-deciding condition (initial state, governing model, boundary condition) is stated in the base context; the role
quantities of the v2.1 specs are in `roles_m250n_extra.py`.

Level: S251, S253, S255, S257, S259, S260, S262 upper-university; S252, S254, S256, S258, S261 introductory. Relations (computed nodes):
S251 4, S252 3, S253 4, S254 3, S255 6, S256 4, S257 4, S258 5, S259 4, S260 4, S261 3, S262 3.

Admission status: agent-authored and machine-certified only. No human physicist and no LLM panel has reviewed these problems or plans.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.integrate import quad, solve_ivp
from scipy.linalg import expm
from scipy.optimize import brentq

from physmon.benchmark.v2.graph import Assumption, Structure
from physmon.benchmark.v2.library import _co, _in, _spec
from physmon.benchmark.v2.trace import Plan, Step

U_KG = 1.66053906660e-27

# --- solvers (independent routes; SI inputs in node order) -----------------------------------------


def _solve_vertical_launch(g0, r_moon, v0):
    # Work-energy: the greatest height H is the root of the integral of the local gravity along the climb equal to v0^2 / 2.
    def deficit(height):
        work, _ = quad(lambda z: g0 * (r_moon / (r_moon + z)) ** 2, 0.0, height, epsabs=0.0, epsrel=1e-13)
        return work - 0.5 * v0 * v0

    return float(brentq(deficit, 1.0, 50.0 * r_moon, xtol=1e-9, rtol=1e-15))


def _solve_orbit_raising(m, g0, r_earth, h1, h2):
    # Total energy of each circular orbit from the centripetal balance g(r) = v^2 / r (speed by root finding) plus the potential energy.
    def energy(radius):
        gravity = g0 * (r_earth / radius) ** 2
        speed = brentq(lambda v: v * v / radius - gravity, 1.0, 1.0e5, xtol=1e-12, rtol=1e-15)
        return m * (0.5 * speed * speed - g0 * r_earth ** 2 / radius)

    return float(energy(r_earth + h2) - energy(r_earth + h1))


def _solve_air_water_pressure(rho1, c1, rho2, c2, i_inc):
    # Continuity of pressure and of normal velocity at the interface as a 2 x 2 linear system for the reflected and transmitted
    # pressure amplitudes of an incident wave of pressure amplitude sqrt(2 Z1 I).
    z1, z2 = rho1 * c1, rho2 * c2
    p_inc = math.sqrt(2.0 * z1 * i_inc)
    matrix = np.array([[1.0, -1.0], [-1.0 / z1, -1.0 / z2]])
    rhs = np.array([-p_inc, -p_inc / z1])
    _p_refl, p_trans = np.linalg.solve(matrix, rhs)
    return float(p_trans)


def _solve_siren_intensity(power, distance, alpha):
    # The intensity integrated outward from a reference radius of one metre: dI/dr = - (2 / r + alpha) I (spherical spreading and absorption).
    r0 = 1.0
    start = power / (4.0 * math.pi * r0 * r0) * math.exp(-alpha * r0)
    sol = solve_ivp(lambda r, y: [-(2.0 / r + alpha) * y[0]], (r0, distance), [start], method="DOP853", rtol=1e-13, atol=1e-30)
    return float(sol.y[0][-1])


def _solve_bimetal_tip(length, thickness, a1, a2, e1, e2, t0, t1):
    # Force and moment balance of the two layers (z from -t to 0 and from 0 to t, t = thickness / 2) for the strain of the interface
    # and the curvature, as a 2 x 2 linear system; the tip deflection of the curved strip is curvature * length^2 / 2.
    half = thickness / 2.0
    d_t = t1 - t0
    layers = ((e1, a1, -half, 0.0), (e2, a2, 0.0, half))

    def moment(power, young, lo, hi):
        value, _ = quad(lambda z: young * z ** power, lo, hi, epsabs=0.0, epsrel=1e-13)
        return value

    matrix = np.zeros((2, 2))
    rhs = np.zeros(2)
    for young, alpha, lo, hi in layers:
        matrix[0, 0] += moment(0, young, lo, hi)
        matrix[0, 1] += moment(1, young, lo, hi)
        matrix[1, 0] += moment(1, young, lo, hi)
        matrix[1, 1] += moment(2, young, lo, hi)
        rhs[0] += alpha * d_t * moment(0, young, lo, hi)
        rhs[1] += alpha * d_t * moment(1, young, lo, hi)
    curvature = np.linalg.solve(matrix, rhs)[1]
    return float(abs(curvature) * length * length / 2.0)


def _solve_dulong_petit_heat(mass, molar_mass, t1, t2, gas_constant):
    # Equipartition: six quadratic degrees of freedom per atom (three kinetic, three potential), U = n * 6 * (R / 2) * T; the heat is the
    # integral of dU along the heating.
    moles = mass / molar_mass
    heat, _ = quad(lambda t: moles * 6.0 * 0.5 * gas_constant, t1, t2, epsabs=0.0, epsrel=1e-13)
    return float(heat)


def _solve_daughter_activity(a0, t_parent, t_daughter, t):
    # The two coupled decay equations as a matrix exponential acting on the numbers of atoms.
    lp, ld = math.log(2.0) / t_parent, math.log(2.0) / t_daughter
    start = np.array([a0 / lp, 0.0])
    state = expm(np.array([[-lp, 0.0], [lp, -ld]]) * t) @ start
    return float(ld * state[1])


def _solve_source_activity(mass, atom_mass, half_life, age):
    # Integrate dN/dt = - lambda N from the number of atoms at the making of the source, then A = lambda N.
    n0 = mass / atom_mass
    lam = math.log(2.0) / half_life
    sol = solve_ivp(lambda t, y: [-lam * y[0]], (0.0, age), [n0], method="DOP853", rtol=1e-13, atol=1e-30)
    return float(lam * sol.y[0][-1])


def _solve_fast_amount(amount, mass, k_b, temperature, v_cut):
    # The Maxwell speed distribution integrated from the cut speed to infinity.
    a = mass / (2.0 * k_b * temperature)
    norm = 4.0 * math.pi * (a / math.pi) ** 1.5
    total, _ = quad(lambda v: norm * v * v * math.exp(-a * v * v), v_cut, math.inf, epsabs=0.0, epsrel=1e-13)
    return float(amount * total)


def _solve_collision_rate(pressure, temperature, diameter, mass, k_b):
    # Mean speed by quadrature over the Maxwell distribution; the collision rate as sqrt(2) n sigma v_mean with n from the ideal-gas law.
    a = mass / (2.0 * k_b * temperature)
    norm = 4.0 * math.pi * (a / math.pi) ** 1.5
    v_mean, _ = quad(lambda v: norm * v ** 3 * math.exp(-a * v * v), 0.0, math.inf, epsabs=0.0, epsrel=1e-13)
    number_density = pressure / (k_b * temperature)
    return float(math.sqrt(2.0) * number_density * math.pi * diameter ** 2 * v_mean)


def _solve_stokes_speed(mass, radius, rho_fluid, eta, g):
    # Force balance on the sphere at constant speed: weight - buoyancy - Stokes drag = 0, solved for the speed by root finding.
    volume = 4.0 / 3.0 * math.pi * radius ** 3
    return float(brentq(lambda v: mass * g - rho_fluid * volume * g - 6.0 * math.pi * eta * radius * v, 0.0, 100.0, xtol=1e-14, rtol=1e-15))


def _solve_capillary_drain(eta, rho, radius, length, area, h0, h1, g):
    # Time as the integral of dt = A dh / Q(h), with the Poiseuille flow rate Q = pi rho g h r^4 / (8 eta L) at the head h.
    seconds, _ = quad(lambda h: area * 8.0 * eta * length / (math.pi * rho * g * h * radius ** 4), h1, h0, epsabs=0.0, epsrel=1e-13)
    return float(seconds)


# --- structures ---------------------------------------------------------------------------------------


def s251_vertical_launch_from_moon() -> Structure:
    return Structure(
        "S251", "Greatest height reached by a probe fired upward from a small moon", "gravitation", "vertical_launch_inverse_square_energy_conservation",
        (_in("g0", "acceleration", "m/s^2", "gravitational acceleration at the surface of the moon, a stated constant", 1.62, (1.55, 1.70), provenance="assumed"),
         _in("Rm", "length", "km", "radius of the moon, a stated constant", 1737.0, (1700.0, 1760.0), provenance="assumed"),
         _in("v0", "speed", "m/s", "launch speed of the probe from its motor", 1500.0, (900.0, 2000.0)),
         _co("k0", "specific_energy", "J/kg", "kinetic energy per unit mass at the launch", "v0**2/2"),
         _co("eps", "specific_energy", "J/kg", "total energy per unit mass of the probe", "k0 - g0*Rm"),
         _co("rmax", "length", "m", "distance of the highest point from the centre of the moon", "g0*Rm**2/(-eps)"),
         _co("H", "length", "km", "greatest height above the surface", "rmax - Rm")),
        "H",
        (Assumption("A-field", "The pull of the moon is the inverse-square gravity of a uniform sphere, with the stated surface value and radius; no other body acts.", "modelling", ("g0", "Rm")),
         Assumption("A-bound", "The moon has no atmosphere and does not rotate, and the launch speed is below the escape speed, so the probe reaches a highest point and falls back.", "boundary_condition", ("v0",))),
        _spec("A probe is fired vertically upward from the surface of a small moon by a rocket motor that gives it a launch speed of {v0} m/s. "
              "The moon has no atmosphere and does not rotate, no other body acts on the probe, and the pull of the moon follows the "
              "inverse-square law with distance from its centre. The moon has radius {Rm} km, and the gravitational acceleration at its "
              "surface is {g0} m/s².",
              "What greatest height above the surface does the probe reach?", "greatest height above the surface", "km",
              "A separate balloon B rises {v} {u} above a launch site on another moon, but it is unrelated to this probe.",
              "A reference probe B reaches a height of {v} {u}.",
              "A separate gauge B reads {v} {u}, but it plays no part in the firing.", "s", equivalent="m"),
        ("v0", 1.2), _solve_vertical_launch, 3,
        "the work-energy balance with the local gravity integrated along the climb and the height found by root finding, instead of the closed form of the energy equation",
        solver_rel_tol=1e-8,
        instances=({"g0": 1.62, "Rm": 1737.0, "v0": 1500.0},
                   {"g0": 1.62, "Rm": 1737.0, "v0": 1300.0},
                   {"g0": 1.63, "Rm": 1740.0, "v0": 1800.0},
                   {"g0": 1.60, "Rm": 1730.0, "v0": 1100.0}))


def s252_orbit_raising_work() -> Structure:
    return Structure(
        "S252", "Work done by the engines in raising a satellite between circular orbits", "gravitation", "orbit_raising_circular_to_circular_work",
        (_in("m", "mass", "kg", "mass of the satellite", 850.0, (300.0, 1500.0)),
         _in("g0", "acceleration", "m/s^2", "gravitational acceleration at the surface of the Earth, a stated constant", 9.8, (9.7, 9.9), provenance="assumed"),
         _in("Re", "length", "km", "radius of the Earth, a stated constant", 6371.0, (6300.0, 6400.0), provenance="assumed"),
         _in("h1", "length", "km", "altitude of the initial circular orbit", 400.0, (300.0, 600.0)),
         _in("h2", "length", "km", "altitude of the final circular orbit", 1200.0, (900.0, 1600.0)),
         _co("r1", "length", "m", "radius of the initial orbit", "Re + h1"),
         _co("r2", "length", "m", "radius of the final orbit", "Re + h2"),
         _co("W", "energy", "kJ", "work done by the engines", "m*g0*Re**2*(1/r1 - 1/r2)/2")),
        "W",
        (Assumption("A-field", "The Earth is a uniform sphere of the stated radius whose gravity follows the inverse-square law with the stated surface value; the orbits are circular and the atmosphere, the Moon and the Sun are ignored.", "modelling", ("g0", "Re")),
         Assumption("A-work", "All of the change of the total (kinetic plus potential) energy of the satellite is supplied by the engines; the loss of mass of the burnt propellant is neglected.", "boundary_condition", ("m",))),
        _spec("A satellite of mass {m} kg moves in a circular orbit at an altitude of {h1} km above the Earth. Its engines raise it to a "
              "higher circular orbit at an altitude of {h2} km. The Earth is a uniform sphere of radius {Re} km with gravitational "
              "acceleration {g0} m/s² at its surface, and the pull follows the inverse-square law. The atmosphere, the Moon and the Sun "
              "are ignored, and the mass of the burnt propellant is neglected.",
              "How much work do the engines do in raising the satellite?", "work done by the engines", "kJ",
              "A separate crane B does {v} {u} of work on another site, but it is unrelated to this satellite.",
              "A reference satellite B needs {v} {u} of work.",
              "A separate meter B reads {v} {u}, but it plays no part in the orbit.", "W", equivalent="J"),
        ("m", 1.25), _solve_orbit_raising, 5,
        "the total energy of each orbit from the centripetal balance (speed by root finding) plus the potential energy, instead of the closed form minus the half of the potential energy",
        solver_rel_tol=1e-8,
        instances=({"m": 850.0, "g0": 9.8, "Re": 6371.0, "h1": 400.0, "h2": 1200.0},
                   {"m": 600.0, "g0": 9.8, "Re": 6371.0, "h1": 350.0, "h2": 1000.0},
                   {"m": 1200.0, "g0": 9.81, "Re": 6378.0, "h1": 500.0, "h2": 1500.0},
                   {"m": 420.0, "g0": 9.8, "Re": 6371.0, "h1": 320.0, "h2": 950.0}))


def s253_air_water_transmission() -> Structure:
    return Structure(
        "S253", "Pressure amplitude of sound transmitted from air into water", "acoustics", "plane_wave_normal_incidence_impedance_transmission",
        (_in("rho1", "density", "kg/m^3", "density of the air", 1.2, (1.1, 1.3)),
         _in("c1", "speed", "m/s", "speed of sound in the air", 343.0, (330.0, 350.0)),
         _in("rho2", "density", "kg/m^3", "density of the water", 998.0, (990.0, 1030.0)),
         _in("c2", "speed", "m/s", "speed of sound in the water", 1482.0, (1400.0, 1550.0)),
         _in("Ii", "intensity", "W/m^2", "intensity of the incident sound wave", 0.012, (0.002, 0.05)),
         _co("rz", "ratio", "1", "ratio of the acoustic impedance of the water to that of the air", "(rho2*c2)/(rho1*c1)"),
         _co("tr", "ratio", "1", "fraction of the incident intensity that is transmitted", "4*rz/(1 + rz)**2"),
         _co("It", "intensity", "W/m^2", "intensity of the transmitted wave", "tr*Ii"),
         _co("pt", "pressure", "Pa", "pressure amplitude of the transmitted wave", "sqrt(2*rho2*c2*It)")),
        "pt",
        (Assumption("A-plane", "The waves are plane and harmonic, the surface is flat and horizontal, the incidence is normal, and both fluids are uniform and lossless.", "modelling", ("rho1", "c1", "rho2", "c2")),
         Assumption("A-boundary", "The pressure and the normal velocity of the fluid are continuous across the surface, and the water is deep, so that nothing returns from below.", "boundary_condition", ("Ii",))),
        _spec("A plane sound wave travels in air and strikes a flat water surface at normal incidence. The air has density {rho1} kg/m³ and the "
              "speed of sound in it is {c1} m/s; the water has density {rho2} kg/m³ and the speed of sound in it is {c2} m/s. The "
              "intensity of the incident wave is {Ii} W/m². The water is deep, so nothing returns from below, and both fluids are "
              "uniform and lossless; the pressure and the normal velocity of the fluid are continuous across the surface.",
              "What is the pressure amplitude of the sound wave in the water?", "pressure amplitude of the sound wave in the water", "Pa",
              "A separate loudspeaker B gives a pressure amplitude of {v} {u} in a hall, but it is unrelated to this wave.",
              "A reference wave B has a pressure amplitude of {v} {u} in the water.",
              "A separate meter B reads {v} {u}, but it plays no part in the transmission.", "Hz", equivalent="kPa"),
        ("Ii", 1.5), _solve_air_water_pressure, 5,
        "the continuity of pressure and of normal velocity written as a linear system for the reflected and transmitted amplitudes, instead of the intensity transmission factor",
        solver_rel_tol=1e-9,
        instances=({"rho1": 1.2, "c1": 343.0, "rho2": 998.0, "c2": 1482.0, "Ii": 0.012},
                   {"rho1": 1.25, "c1": 340.0, "rho2": 1025.0, "c2": 1500.0, "Ii": 0.03},
                   {"rho1": 1.15, "c1": 346.0, "rho2": 1000.0, "c2": 1450.0, "Ii": 0.005},
                   {"rho1": 1.3, "c1": 331.0, "rho2": 1010.0, "c2": 1520.0, "Ii": 0.02}))


def s254_siren_intensity_with_absorption() -> Structure:
    return Structure(
        "S254", "Sound intensity at a distance from a siren with air absorption", "acoustics", "point_source_inverse_square_with_exponential_absorption",
        (_in("P", "power", "W", "sound power radiated by the siren", 40.0, (10.0, 100.0)),
         _in("r", "length", "m", "distance of the observer from the mast", 60.0, (30.0, 120.0)),
         _in("alpha", "attenuation_coefficient", "1/m", "intensity absorption coefficient of the air", 0.004, (0.001, 0.01)),
         _co("area", "area", "m^2", "area of the sphere through the observer", "4*pi*r**2"),
         _co("I0", "intensity", "W/m^2", "intensity without absorption", "P/area"),
         _co("I", "intensity", "W/m^2", "intensity at the observer", "I0*exp(-alpha*r)")),
        "I",
        (Assumption("A-point", "The siren is a point source that radiates uniformly in all directions, high above the ground so that nothing reflects, in still air.", "modelling", ("P",)),
         Assumption("A-absorb", "The air absorbs the sound so that the intensity of the outgoing wave falls by the factor exp(-alpha x) over a path x in addition to the spreading, with a constant coefficient.", "modelling", ("alpha",))),
        _spec("A siren on a tall mast radiates sound of power {P} W uniformly in all directions; it is high above the ground, so nothing "
              "reflects the sound, and the air is still. Besides the spreading of the wave, the air absorbs the sound: over a path x the "
              "intensity of the outgoing wave is reduced by the factor exp(−αx), with a constant α = {alpha} per metre. An observer starts "
              "at a distance of {r} m from the mast.",
              "What sound intensity does the observer measure?", "sound intensity at the observer", "W/m^2",
              "A separate lamp B gives an irradiance of {v} {u} in another yard, but it is unrelated to this sound.",
              "A reference observer B measures {v} {u}.",
              "A separate meter B reads {v} {u}, but it plays no part in the sound.", "s", equivalent=None),
        ("P", 1.3), _solve_siren_intensity, 3,
        "the intensity integrated outward from a reference radius as an ODE with spherical spreading and absorption, instead of the closed form with the area of the sphere",
        solver_rel_tol=1e-8,
        instances=({"P": 40.0, "r": 60.0, "alpha": 0.004},
                   {"P": 25.0, "r": 45.0, "alpha": 0.006},
                   {"P": 80.0, "r": 100.0, "alpha": 0.002},
                   {"P": 15.0, "r": 35.0, "alpha": 0.008}))


def s255_bimetal_tip_deflection() -> Structure:
    return Structure(
        "S255", "Tip deflection of a heated bimetallic strip", "solid_state", "bimetallic_strip_timoshenko_curvature_thermal_mismatch",
        (_in("L", "length", "cm", "length of the strip", 20.0, (10.0, 30.0)),
         _in("h", "length", "mm", "total thickness of the strip", 1.0, (0.5, 2.0)),
         _in("a1", "thermal_expansion_coefficient", "1/K", "linear expansion coefficient of the steel layer, a stated constant", 0.000012, (0.000010, 0.000014), provenance="assumed"),
         _in("a2", "thermal_expansion_coefficient", "1/K", "linear expansion coefficient of the brass layer, a stated constant", 0.000019, (0.000017, 0.000021), provenance="assumed"),
         _in("E1", "pressure", "MPa", "Young modulus of the steel layer, a stated constant", 200000.0, (190000.0, 210000.0), provenance="assumed"),
         _in("E2", "pressure", "MPa", "Young modulus of the brass layer, a stated constant", 100000.0, (90000.0, 110000.0), provenance="assumed"),
         _in("T0", "temperature", "K", "initial temperature of the strip", 293.0, (280.0, 300.0)),
         _in("T", "temperature", "K", "final temperature of the strip", 353.0, (330.0, 400.0)),
         _co("dT", "temperature_change", "K", "temperature rise of the strip", "T - T0"),
         _co("da", "thermal_expansion_coefficient", "1/K", "difference of the expansion coefficients", "a2 - a1"),
         _co("n", "ratio", "1", "ratio of the moduli of the two layers", "E1/E2"),
         _co("Dn", "ratio", "1", "stiffness factor of the two-layer section", "12 + (1 + n)*(1 + 1/n)"),
         _co("kap", "curvature", "1/m", "curvature of the heated strip", "24*da*dT/(h*Dn)"),
         _co("delta", "length", "mm", "deflection of the free end", "kap*L**2/2")),
        "delta",
        (Assumption("A-beam", "The strip is a thin beam of two bonded layers of equal thickness and the same width, with linear elastic behaviour and constants independent of temperature, and its curvature is small.", "modelling", ("E1", "E2", "a1", "a2")),
         Assumption("A-clamp", "One end of the strip is clamped with the strip horizontal and unstressed at the initial temperature; the whole strip is heated uniformly and slowly, and no load acts on it.", "boundary_condition", ("T0", "T"))),
        _spec("A bimetallic strip is made of two bonded layers of equal thickness and equal width, a steel layer with linear expansion "
              "coefficient {a1} per kelvin and Young modulus {E1} MPa, and a brass layer with linear expansion coefficient {a2} per kelvin "
              "and Young modulus {E2} MPa. The strip is clamped at one end and projects a length of {L} cm from the clamp; its total thickness is {h} mm. It is "
              "horizontal and free of stress at an initial temperature of {T0} K, and is then heated uniformly and slowly to {T} K. "
              "The constants do not depend on temperature, the strip carries no load, and its curvature stays small.",
              "What is the vertical deflection of the free end of the strip?", "vertical deflection of the free end", "mm",
              "A separate bridge B sags by {v} {u} under traffic, but it is unrelated to this strip.",
              "A reference strip B has its free end deflected by {v} {u}.",
              "A separate meter B reads {v} {u}, but it plays no part in the heating.", "s", equivalent="cm"),
        ("T", 1.1), _solve_bimetal_tip, 8,
        "the force and the moment balance of the two layers written as a linear system for the strain of the interface and the curvature, instead of the Timoshenko closed form",
        solver_rel_tol=1e-8,
        instances=({"L": 20.0, "h": 1.0, "a1": 0.000012, "a2": 0.000019, "E1": 200000.0, "E2": 100000.0, "T0": 293.0, "T": 353.0},
                   {"L": 15.0, "h": 0.8, "a1": 0.000012, "a2": 0.000018, "E1": 200000.0, "E2": 110000.0, "T0": 290.0, "T": 370.0},
                   {"L": 25.0, "h": 1.5, "a1": 0.000011, "a2": 0.000019, "E1": 205000.0, "E2": 100000.0, "T0": 295.0, "T": 345.0},
                   {"L": 12.0, "h": 0.6, "a1": 0.000013, "a2": 0.000020, "E1": 195000.0, "E2": 95000.0, "T0": 285.0, "T": 335.0}))


def s256_dulong_petit_heat() -> Structure:
    return Structure(
        "S256", "Heat needed to warm a lead block with the classical heat capacity", "solid_state", "dulong_petit_classical_lattice_heat_capacity",
        (_in("m", "mass", "kg", "mass of the lead block", 0.5, (0.2, 1.5)),
         _in("M", "molar_mass", "g/mol", "molar mass of lead, a stated constant", 207.2, (206.0, 208.0), provenance="assumed"),
         _in("T1", "temperature", "K", "initial temperature of the block", 300.0, (280.0, 320.0)),
         _in("T2", "temperature", "K", "final temperature of the block", 360.0, (340.0, 420.0)),
         _in("R", "molar_gas_constant", "J/(mol*K)", "molar gas constant, a stated constant", 8.314, (8.30, 8.33), provenance="assumed"),
         _co("n", "amount", "mol", "amount of lead in the block", "m/M"),
         _co("Cm", "molar_heat_capacity", "J/(mol*K)", "molar heat capacity of the solid", "3*R"),
         _co("dT", "temperature_change", "K", "rise of the temperature of the block", "T2 - T1"),
         _co("Q", "energy", "kJ", "heat supplied to the block", "n*Cm*dT")),
        "Q",
        (Assumption("A-classical", "Over the whole heating the lattice vibrations are in the classical regime, so the molar heat capacity of the solid takes its constant equipartition value, 3R, and the volume change is neglected.", "modelling", ("R", "M")),
         Assumption("A-solid", "The block stays solid and is heated slowly and uniformly, and no heat is lost to the surroundings.", "boundary_condition", ("T1", "T2"))),
        _spec("A block of lead of mass {m} kg is at a temperature of {T1} K. It is heated slowly and uniformly to {T2} K, stays solid, "
              "and loses no heat to the surroundings. Over this range the lattice vibrations are in the classical regime, so the molar "
              "heat capacity of the solid has its constant equipartition value, three times R, with the molar gas constant R = {R} J/(mol·K). "
              "The molar mass of lead is {M} g/mol.",
              "How much heat is supplied to the block?", "heat supplied to the block", "kJ",
              "A separate furnace B releases {v} {u} of heat in another workshop, but it is unrelated to this block.",
              "A reference block B takes in {v} {u} of heat.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the heating.", "W", equivalent="J"),
        ("m", 1.25), _solve_dulong_petit_heat, 5,
        "the internal energy of six quadratic degrees of freedom per atom integrated along the heating, instead of the molar heat capacity 3R times the temperature rise",
        solver_rel_tol=1e-9,
        instances=({"m": 0.5, "M": 207.2, "T1": 300.0, "T2": 360.0, "R": 8.314},
                   {"m": 0.8, "M": 207.2, "T1": 290.0, "T2": 350.0, "R": 8.314},
                   {"m": 0.3, "M": 207.0, "T1": 310.0, "T2": 400.0, "R": 8.31},
                   {"m": 1.2, "M": 207.2, "T1": 285.0, "T2": 345.0, "R": 8.314}))


def s257_daughter_activity() -> Structure:
    return Structure(
        "S257", "Activity of a daughter isotope in a generator column", "nuclear", "two_member_decay_chain_bateman_daughter_activity",
        (_in("A0", "activity", "Bq", "activity of the parent isotope at the start", 4000.0, (1000.0, 9000.0)),
         _in("Tp", "time", "h", "half-life of the parent isotope", 66.0, (40.0, 100.0)),
         _in("Td", "time", "h", "half-life of the daughter isotope", 6.0, (3.0, 10.0)),
         _in("t", "time", "h", "time since the start", 24.0, (10.0, 48.0)),
         _co("lp", "rate", "1/s", "decay constant of the parent", "log(2)/Tp"),
         _co("ld", "rate", "1/s", "decay constant of the daughter", "log(2)/Td"),
         _co("rr", "ratio", "1", "ratio of the decay constant of the daughter to the difference of the decay constants", "ld/(ld - lp)"),
         _co("Ad", "activity", "Bq", "activity of the daughter isotope", "A0*rr*(exp(-lp*t) - exp(-ld*t))")),
        "Ad",
        (Assumption("A-chain", "The parent decays only to the daughter, and the daughter decays to a stable nuclide; no daughter is present at the start, and nothing is removed from the column or added to it afterwards.", "boundary_condition", ("A0", "t")),
         Assumption("A-law", "Each decay follows the exponential law with the constant decay constant ln 2 divided by the half-life.", "modelling", ("Tp", "Td"))),
        _spec("A generator column is loaded at time zero with a parent isotope of activity {A0} Bq and contains no daughter isotope at that "
              "moment. The parent has a half-life of {Tp} h and decays only to the daughter, which has a half-life of {Td} h and decays "
              "to a stable nuclide. Nothing is removed from the column or added to it afterwards.",
              "What is the activity of the daughter isotope in the column at a time {t} h after the loading?", "activity of the daughter isotope", "Bq",
              "A separate sample B has an activity of {v} {u} in another laboratory, but it is unrelated to this column.",
              "A reference column B holds a daughter of activity {v} {u}.",
              "A separate meter B reads {v} {u}, but it plays no part in the decay.", "m", equivalent="Hz"),
        ("A0", 1.3), _solve_daughter_activity, 4,
        "the two coupled decay equations written as a matrix exponential acting on the numbers of atoms, instead of the closed Bateman expression",
        solver_rel_tol=1e-8,
        instances=({"A0": 4000.0, "Tp": 66.0, "Td": 6.0, "t": 24.0},
                   {"A0": 2500.0, "Tp": 50.0, "Td": 5.0, "t": 18.0},
                   {"A0": 7000.0, "Tp": 90.0, "Td": 8.0, "t": 36.0},
                   {"A0": 1500.0, "Tp": 45.0, "Td": 4.0, "t": 12.0}))


def s258_cobalt_source_activity() -> Structure:
    return Structure(
        "S258", "Activity of a cobalt source after some years of decay", "nuclear", "radioactive_source_activity_from_mass_and_age",
        (_in("m", "mass", "g", "mass of the radioactive cobalt in the source when it was made", 0.004, (0.001, 0.01)),
         _in("Ma", "mass", "u", "mass of one atom of the radioactive cobalt, a stated constant", 59.93, (59.0, 61.0), provenance="assumed"),
         _in("Th", "time", "yr", "half-life of the radioactive cobalt, a stated constant", 5.27, (5.0, 5.5), provenance="assumed"),
         _in("age", "time", "yr", "age of the source", 8.0, (2.0, 15.0)),
         _co("N", "ratio", "1", "number of radioactive atoms when the source was made", "m/Ma"),
         _co("lam", "rate", "1/s", "decay constant", "log(2)/Th"),
         _co("A0", "activity", "Bq", "activity when the source was made", "lam*N"),
         _co("f", "ratio", "1", "fraction of the atoms that has not decayed", "exp(-lam*age)"),
         _co("A", "activity", "Bq", "present activity of the source", "A0*f")),
        "A",
        (Assumption("A-law", "The decay follows the exponential law with the stated half-life; the decay products are not radioactive and nothing is added to or removed from the source.", "modelling", ("Th", "Ma")),),
        _spec("A source is made and is then left to stand for {age} years. When it is made it contains {m} g of a radioactive isotope of "
              "cobalt. One atom of this isotope has a mass of {Ma} u and the half-life of the isotope is {Th} years. The decay "
              "products are not radioactive, and nothing is added to the source or removed from it while it stands.",
              "What is the activity of the source at the end of that time?", "present activity of the source", "Bq",
              "A separate source B has an activity of {v} {u} in another hospital, but it is unrelated to this source.",
              "A reference source B has an activity of {v} {u}.",
              "A separate meter B reads {v} {u}, but it plays no part in the decay.", "m", equivalent="Hz"),
        ("m", 1.3), _solve_source_activity, 4,
        "the integration of the decay equation for the number of atoms with an adaptive ODE solver, instead of the closed exponential law",
        solver_rel_tol=1e-8,
        instances=({"m": 0.004, "Ma": 59.93, "Th": 5.27, "age": 8.0},
                   {"m": 0.002, "Ma": 59.93, "Th": 5.27, "age": 3.0},
                   {"m": 0.008, "Ma": 60.0, "Th": 5.3, "age": 12.0},
                   {"m": 0.0015, "Ma": 59.9, "Th": 5.2, "age": 6.0}))


def s259_fast_atom_fraction() -> Structure:
    return Structure(
        "S259", "Amount of the atoms of a gas that exceed a given speed", "statistical_physics", "maxwell_distribution_fraction_above_cut_speed",
        (_in("n", "amount", "mol", "amount of helium in the flask", 0.5, (0.2, 1.5)),
         _in("m", "mass", "u", "mass of one atom of the gas", 4.003, (3.9, 4.1)),
         _in("kB", "boltzmann_constant", "J/K", "Boltzmann constant, a stated constant", 1.381e-23, (1.3e-23, 1.4e-23), provenance="assumed"),
         _in("T", "temperature", "K", "temperature of the gas", 300.0, (250.0, 400.0)),
         _in("vc", "speed", "m/s", "cut speed", 2000.0, (1500.0, 2600.0)),
         _co("vp", "speed", "m/s", "most probable speed of the atoms", "sqrt(2*kB*T/m)"),
         _co("x", "ratio", "1", "cut speed in units of the most probable speed", "vc/vp"),
         _co("F", "ratio", "1", "fraction of the atoms faster than the cut speed", "erfc(x) + 2*x*exp(-x**2)/sqrt(pi)"),
         _co("nf", "amount", "mol", "amount of the atoms faster than the cut speed", "n*F")),
        "nf",
        (Assumption("A-maxwell", "The gas is an ideal monatomic gas in thermal equilibrium, so the speeds of its atoms follow the Maxwell distribution, and the atoms do not react or ionise.", "modelling", ("kB", "m")),),
        _spec("A sealed flask holds {n} mol of helium gas, an ideal monatomic gas, which starts at a temperature of {T} K. After the gas has come to "
              "thermal equilibrium in the flask, the speeds of its atoms are measured. One atom has a mass of {m} u. Take the "
              "Boltzmann constant to be {kB} J/K. The speeds follow the Maxwell distribution.",
              "What amount of the helium has atoms with a speed greater than {vc} m/s?", "amount of the atoms faster than the cut speed", "mol",
              "A separate cylinder B holds {v} {u} of gas in another laboratory, but it is unrelated to this flask.",
              "A reference flask B holds {v} {u} of fast atoms.",
              "A separate meter B reads {v} {u}, but it plays no part in the measurement.", "m", equivalent=None, formats={"kB": ".4g"}),
        ("T", 1.2), _solve_fast_amount, 5,
        "the Maxwell speed distribution integrated numerically from the cut speed to infinity, instead of the error-function closed form",
        solver_rel_tol=1e-8,
        instances=({"n": 0.5, "m": 4.003, "kB": 1.381e-23, "T": 300.0, "vc": 2000.0},
                   {"n": 0.8, "m": 4.0, "kB": 1.381e-23, "T": 280.0, "vc": 1800.0},
                   {"n": 0.3, "m": 4.1, "kB": 1.381e-23, "T": 350.0, "vc": 2500.0},
                   {"n": 1.2, "m": 3.95, "kB": 1.381e-23, "T": 260.0, "vc": 1700.0}))


def s260_molecular_collision_rate() -> Structure:
    return Structure(
        "S260", "Collision rate of a molecule of nitrogen in a rigid vessel", "statistical_physics", "kinetic_theory_collision_frequency_mean_free_path",
        (_in("p", "pressure", "kPa", "pressure of the gas", 80.0, (20.0, 150.0)),
         _in("T", "temperature", "K", "temperature of the gas", 300.0, (250.0, 400.0)),
         _in("d", "length", "pm", "effective diameter of a molecule", 370.0, (340.0, 400.0)),
         _in("m", "mass", "u", "mass of a molecule", 28.0, (27.0, 29.0)),
         _in("kB", "boltzmann_constant", "J/K", "Boltzmann constant, a stated constant", 1.381e-23, (1.3e-23, 1.4e-23), provenance="assumed"),
         _co("sig", "area", "m^2", "collision cross-section of a molecule", "pi*d**2"),
         _co("lam", "length", "m", "mean free path", "kB*T/(sqrt(2)*sig*p)"),
         _co("vbar", "speed", "m/s", "mean speed of the molecules", "sqrt(8*kB*T/(pi*m))"),
         _co("z", "frequency", "GHz", "collision rate of one molecule", "vbar/lam")),
        "z",
        (Assumption("A-gas", "The gas is ideal and in thermal equilibrium, the molecules are hard spheres of the stated effective diameter with Maxwell-distributed speeds, and all of the molecules move.", "modelling", ("kB", "d", "m")),
         Assumption("A-collisions", "Only collisions between molecules are counted; the mean free path is much shorter than the vessel, so that collisions with the walls are negligible.", "boundary_condition", ("p", "T"))),
        _spec("A rigid vessel holds nitrogen, an ideal gas, at a pressure of {p} kPa and a temperature of {T} K. The molecules are hard "
              "spheres of effective diameter {d} pm and mass {m} u, with Maxwell-distributed speeds. Take the Boltzmann constant to be "
              "{kB} J/K. The vessel is large compared with the mean free path, so only collisions between molecules are counted, "
              "and the gas is in thermal equilibrium.",
              "How many collisions with other molecules does one molecule make each second?", "collisions per second of one molecule", "GHz",
              "A separate vessel B has a molecule collision rate of {v} {u} in another laboratory, but it is unrelated to this gas.",
              "A reference gas B has a collision rate of {v} {u}.",
              "A separate meter B reads {v} {u}, but it plays no part in the collisions.", "m", equivalent="MHz", formats={"kB": ".4g"}),
        ("p", 1.5), _solve_collision_rate, 5,
        "the mean speed by quadrature over the Maxwell speed distribution and the rate as sqrt(2) n sigma v with n from the ideal-gas law, instead of the mean speed divided by the mean free path",
        solver_rel_tol=1e-8,
        instances=({"p": 80.0, "T": 300.0, "d": 370.0, "m": 28.0, "kB": 1.381e-23},
                   {"p": 50.0, "T": 280.0, "d": 365.0, "m": 28.0, "kB": 1.381e-23},
                   {"p": 120.0, "T": 350.0, "d": 380.0, "m": 28.5, "kB": 1.381e-23},
                   {"p": 30.0, "T": 260.0, "d": 360.0, "m": 27.5, "kB": 1.381e-23}))


def s261_loaded_sphere_stokes_speed() -> Structure:
    return Structure(
        "S261", "Terminal speed of a loaded sphere sinking in a viscous liquid", "fluids", "stokes_terminal_speed_with_buoyancy_loaded_sphere",
        (_in("m", "mass", "g", "total mass of the sphere with its load", 0.25, (0.2, 0.35)),
         _in("r", "length", "mm", "radius of the sphere", 2.0, (1.8, 2.2)),
         _in("rf", "density", "kg/m^3", "density of the liquid", 1260.0, (1200.0, 1300.0)),
         _in("eta", "viscosity", "Pa*s", "viscosity of the liquid", 1.0, (0.8, 1.4)),
         _in("g", "acceleration", "m/s^2", "gravitational acceleration, a stated constant", 9.8, (9.7, 9.9), provenance="assumed"),
         _co("V", "volume", "m^3", "volume of the sphere", "4*pi*r**3/3"),
         _co("rs", "density", "kg/m^3", "mean density of the sphere", "m/V"),
         _co("vt", "speed", "cm/s", "terminal speed of the sphere", "2*g*r**2*(rs - rf)/(9*eta)")),
        "vt",
        (Assumption("A-stokes", "The liquid is at rest and unbounded, the sphere sinks at constant speed with its centre on a vertical line, and the drag is the Stokes drag with the buoyant force of the displaced liquid.", "modelling", ("rf", "eta", "g")),
         Assumption("A-terminal", "The sphere has reached its terminal speed, and the load stays inside the sphere and does not change its radius.", "boundary_condition", ("m", "r"))),
        _spec("A small sphere of radius {r} mm, loaded with lead shot to a total mass of {m} g, is released at the surface of a deep "
              "tank of liquid that is at rest. The liquid has density {rf} kg/m³ and viscosity {eta} Pa·s, and the drag on the sphere "
              "is the Stokes drag. The sphere sinks along a vertical line far from the walls of the tank, and the shot stays inside the "
              "sphere. Take g = {g} m/s².",
              "What is the terminal speed of the sphere?", "terminal speed of the sphere", "cm/s",
              "A separate bubble B rises at {v} {u} in another tank, but it is unrelated to this sphere.",
              "A reference sphere B sinks at {v} {u}.",
              "A separate gauge B reads {v} {u}, but it plays no part in the sinking.", "W", equivalent="m/s"),
        ("m", 1.2), _solve_stokes_speed, 5,
        "the force balance weight minus buoyancy minus Stokes drag equal to zero solved for the speed by root finding, instead of the closed terminal-speed formula",
        solver_rel_tol=1e-8,
        instances=({"m": 0.25, "r": 2.0, "rf": 1260.0, "eta": 1.0, "g": 9.8},
                   {"m": 0.3, "r": 2.1, "rf": 1230.0, "eta": 1.2, "g": 9.8},
                   {"m": 0.22, "r": 1.9, "rf": 1280.0, "eta": 0.9, "g": 9.81},
                   {"m": 0.28, "r": 2.0, "rf": 1210.0, "eta": 1.3, "g": 9.8}))


def s262_capillary_drain_time() -> Structure:
    return Structure(
        "S262", "Time for a tank to drain through a long narrow tube in laminar flow", "fluids", "poiseuille_drain_exponential_head_decay",
        (_in("eta", "viscosity", "Pa*s", "viscosity of the oil", 0.12, (0.08, 0.2)),
         _in("rho", "density", "kg/m^3", "density of the oil", 900.0, (850.0, 950.0)),
         _in("r", "length", "mm", "inner radius of the tube", 3.0, (2.5, 3.5)),
         _in("Lc", "length", "cm", "length of the tube", 50.0, (30.0, 80.0)),
         _in("A", "area", "cm^2", "cross-sectional area of the tank", 100.0, (60.0, 200.0)),
         _in("h0", "length", "cm", "initial depth of the oil in the tank", 40.0, (30.0, 60.0)),
         _in("h1", "length", "cm", "final depth of the oil in the tank", 10.0, (5.0, 20.0)),
         _in("g", "acceleration", "m/s^2", "gravitational acceleration, a stated constant", 9.8, (9.7, 9.9), provenance="assumed"),
         _co("tau", "time", "s", "time constant of the draining", "8*eta*Lc*A/(pi*rho*g*r**4)"),
         _co("lr", "ratio", "1", "natural logarithm of the ratio of the depths", "log(h0/h1)"),
         _co("tc", "time", "min", "time to drain from the initial to the final depth", "tau*lr")),
        "tc",
        (Assumption("A-poiseuille", "The flow in the tube is steady and laminar (Poiseuille flow) at every depth, driven by the hydrostatic pressure of the oil depth alone; end effects and the kinetic energy of the outflow are neglected.", "modelling", ("eta", "rho", "g")),
         Assumption("A-tank", "The tube is horizontal and joined to the bottom of an open tank with vertical walls, the oil is incompressible and its viscosity is constant, and the oil level falls slowly.", "boundary_condition", ("h0", "h1"))),
        _spec("An open tank with vertical walls and cross-sectional area {A} cm² is filled to an initial depth of {h0} cm with oil of density "
              "{rho} kg/m³ and viscosity {eta} Pa·s. The oil drains through a horizontal tube of length {Lc} cm and inner radius {r} mm "
              "joined to the bottom of the tank. The flow in the tube is steady and laminar at every depth and is driven by the "
              "hydrostatic pressure of the oil depth alone; end effects and the kinetic energy of the outflow are neglected. Take "
              "g = {g} m/s².",
              "How long does the oil take to fall to a depth of {h1} cm?", "time for the oil to fall to the final depth", "min",
              "A separate bath B drains in {v} {u} in another laboratory, but it is unrelated to this tank.",
              "A reference tank B drains in {v} {u}.",
              "A separate gauge B reads {v} {u}, but it plays no part in the draining.", "W", equivalent="s"),
        ("h0", 1.3), _solve_capillary_drain, 8,
        "the time as the integral of the tank area times dh over the Poiseuille flow rate at each depth, by adaptive quadrature, instead of the exponential decay of the depth",
        solver_rel_tol=1e-8,
        instances=({"eta": 0.12, "rho": 900.0, "r": 3.0, "Lc": 50.0, "A": 100.0, "h0": 40.0, "h1": 10.0, "g": 9.8},
                   {"eta": 0.1, "rho": 880.0, "r": 3.2, "Lc": 60.0, "A": 120.0, "h0": 50.0, "h1": 15.0, "g": 9.8},
                   {"eta": 0.15, "rho": 920.0, "r": 2.8, "Lc": 40.0, "A": 80.0, "h0": 35.0, "h1": 8.0, "g": 9.81},
                   {"eta": 0.09, "rho": 870.0, "r": 3.4, "Lc": 70.0, "A": 150.0, "h0": 45.0, "h1": 12.0, "g": 9.8}))


ALL = (s251_vertical_launch_from_moon, s252_orbit_raising_work, s253_air_water_transmission, s254_siren_intensity_with_absorption,
       s255_bimetal_tip_deflection, s256_dulong_petit_heat, s257_daughter_activity, s258_cobalt_source_activity, s259_fast_atom_fraction,
       s260_molecular_collision_rate, s261_loaded_sphere_stokes_speed, s262_capillary_drain_time)


def all_structures() -> list[Structure]:
    return [factory() for factory in ALL]


STRUCTURES: dict[str, Structure] = {s.structure_id: s for s in all_structures()}

LEVELS: dict[str, str] = {
    "S251": "upper-university", "S252": "introductory", "S253": "upper-university", "S254": "introductory",
    "S255": "upper-university", "S256": "introductory", "S257": "upper-university", "S258": "introductory",
    "S259": "upper-university", "S260": "upper-university", "S261": "introductory", "S262": "upper-university",
}

# --- gold solution plans ---------------------------------------------------------------------------------


def _plan(sid: str, approach: str, steps: dict[str, tuple[str, str]], check: str) -> Plan:
    from physmon.benchmark.v2 import graph as gr  # local import: ordering follows the graph's dependency order

    structure = STRUCTURES[sid]
    order = [n.name for n in gr.topological_order(structure) if n.kind == "computed"]
    return Plan(approach=approach, steps=tuple(Step(name, *steps[name]) for name in order), check=check)


PLANS: dict[str, Plan] = {
    "S251": _plan(
        "S251",
        "The probe moves only under the pull of the moon, so its total energy per unit mass is conserved. Find the total energy from the launch "
        "speed and the potential at the surface, then the distance at which the kinetic energy is zero, then subtract the radius.",
        {"k0": ("Kinetic energy per unit mass, e = v^2/2",
                "The launch speed fixes the kinetic energy per unit mass, which does not depend on the mass of the probe."),
         "eps": ("Total energy per unit mass in an inverse-square field, e = v^2/2 - g0 R (the potential at the surface is -G M/R = -g0 R)",
                 "The pull of the moon is conservative, so the kinetic energy at launch plus the potential at the surface is the total energy of the probe."),
         "rmax": ("Energy conservation at the highest point, where the speed is zero: e = -G M/r_max = -g0 R^2/r_max",
                  "At the highest point only the potential energy remains, so the negative total energy fixes the distance from the centre of the moon."),
         "H": ("Height is distance from the centre minus the radius of the moon, H = r_max - R",
               "The question asks for the height above the surface, not the distance from the centre.")},
        "The height is larger than the flat-field value v^2/(2 g0), which would hold if the pull did not weaken with height, and it grows without "
        "limit as the launch speed approaches the escape speed."),
    "S252": _plan(
        "S252",
        "The work of the engines equals the change of the total mechanical energy of the satellite. For a circular orbit the total energy is minus "
        "the kinetic energy. Find the two orbit radii and the difference of the two total energies.",
        {"r1": ("Radius of a circular orbit, r = R_E + altitude", "The altitude is measured from the surface, while the law of gravity needs the distance from the centre of the Earth."),
         "r2": ("Radius of a circular orbit, r = R_E + altitude", "The final orbit is treated in the same way as the initial orbit."),
         "W": ("Work-energy theorem with the total energy of a circular orbit, E = -G M m/(2 r) = -m g0 R^2/(2 r)",
               "The engines supply the change of the total energy; for a circular orbit the centripetal condition makes the kinetic energy half of the magnitude of the potential energy, so E is minus the kinetic energy.")},
        "The work is positive and is less than the change of the potential energy alone, because the kinetic energy decreases as the satellite goes up; "
        "it vanishes when the two altitudes are equal."),
    "S253": _plan(
        "S253",
        "At a boundary between two fluids the pressure and the normal velocity are continuous, so the transmitted power fraction depends only on the "
        "ratio of the acoustic impedances. Find the ratio, the power fraction, the transmitted intensity and then the pressure amplitude in the water.",
        {"rz": ("Specific acoustic impedance of a fluid, Z = rho c, and the ratio Z2/Z1", "The reflection at the surface is decided by how well the impedances of the two fluids match."),
         "tr": ("Intensity transmission coefficient at normal incidence, T = 4 Z1 Z2/(Z1 + Z2)^2 = 4 r/(1 + r)^2", "Continuity of pressure and velocity gives the fraction of the incident power that enters the water."),
         "It": ("Transmitted intensity is the transmission coefficient times the incident intensity", "The intensity of the incident wave is given, and a fraction T of it is transmitted."),
         "pt": ("Intensity of a plane wave, I = p^2/(2 Z), so p = sqrt(2 Z I)", "The question asks for a pressure amplitude in the water, so the impedance of the water converts the transmitted intensity.")},
        "The transmission coefficient is tiny, about a tenth of a percent, yet the pressure amplitude in the water is nearly twice the incident one; "
        "the intensity transmitted never exceeds the incident intensity."),
    "S254": _plan(
        "S254",
        "The sound spreads over a sphere and is also absorbed. Find the area of the sphere through the observer, the intensity without absorption, "
        "and then reduce it by the absorption factor.",
        {"area": ("Area of a sphere, A = 4 pi r^2", "A point source radiates uniformly, so the power is spread over the whole sphere through the observer."),
         "I0": ("Definition of intensity for a point source, I = P/(4 pi r^2)", "Without absorption the intensity is the power divided by the area of the sphere."),
         "I": ("Exponential absorption of the intensity along the path, I = I0 exp(-alpha r)", "The air removes a constant fraction of the intensity per unit path, so the spreading result is multiplied by this factor.")},
        "The result is smaller than the value without absorption and tends to it as alpha tends to zero; it falls faster than 1/r^2 at large distance."),
    "S255": _plan(
        "S255",
        "The layer with the larger expansion coefficient wants to be longer than the other, so the bonded strip bends. For two layers of equal "
        "thickness the curvature follows from the balance of force and moment in the section; the free end then moves through the curvature times "
        "the length squared over two.",
        {"dT": ("Temperature rise, dT = T - T0", "The thermal strain is driven by the rise of the temperature of the strip."),
         "da": ("Difference of the expansion coefficients, da = a2 - a1", "Only the mismatch of the free thermal strains of the two layers bends the strip."),
         "n": ("Ratio of the Young moduli of the layers, n = E1/E2", "The stiffness of the section and the position of its neutral axis depend on the ratio of the moduli."),
         "Dn": ("Section stiffness factor of a two-layer beam of equal layer thickness, 12 + (1 + n)(1 + 1/n)", "The balance of force and moment in the section gives this combination for equal thicknesses."),
         "kap": ("Timoshenko bimetal formula for equal layers, curvature = 24 da dT/(h Dn)", "The curvature is the thermal mismatch strain divided by the thickness, reduced by the stiffness factor."),
         "delta": ("Deflection of the free end of a uniformly curved cantilever of small curvature, delta = kappa L^2/2", "The strip is clamped at one end and bent to a circular arc, so the free end moves by the curvature times the length squared over two.")},
        "For equal moduli the stiffness factor is 16 and the curvature is 3 da dT/(2 h), the classical result; the deflection grows with the "
        "square of the length and falls as the strip gets thicker."),
    "S256": _plan(
        "S256",
        "In the classical regime each atom of the solid has six quadratic degrees of freedom, so the molar heat capacity is 3R and does not depend "
        "on temperature. Find the amount of lead, the molar heat capacity and the temperature rise, then the heat.",
        {"n": ("Amount of substance, n = m/M", "The molar heat capacity refers to one mole, so the mass of the block is converted to an amount."),
         "Cm": ("Law of Dulong and Petit (equipartition with six quadratic degrees of freedom per atom), C = 3R", "In the classical regime the energy of the lattice is 3 R T per mole, so its heat capacity is constant."),
         "dT": ("Temperature rise, dT = T2 - T1", "The heat depends on the rise of the temperature of the block."),
         "Q": ("Heat at a constant molar heat capacity, Q = n C dT", "The block is heated slowly with a constant heat capacity and no heat loss, so all of the heat raises its energy.")},
        "The result is the mass times a specific heat capacity of about 120 J/(kg K) times the temperature rise, the known order for lead; it "
        "grows linearly with the mass and the rise."),
    "S257": _plan(
        "S257",
        "The parent decays exponentially and feeds the daughter, which decays itself. Find the two decay constants, the factor that couples them, "
        "and then the daughter activity from the difference of the two exponentials.",
        {"lp": ("Decay constant from the half-life, lambda = ln 2/T", "The decay of each isotope is exponential, and the half-life fixes the constant."),
         "ld": ("Decay constant from the half-life, lambda = ln 2/T", "The daughter is treated in the same way as the parent."),
         "rr": ("Coupling factor of a two-member chain, lambda_d/(lambda_d - lambda_p)", "The rate of production of the daughter is the activity of the parent, and solving the coupled equations gives this factor."),
         "Ad": ("Bateman solution for the daughter with no daughter at the start, A_d = A_0 lambda_d/(lambda_d - lambda_p) (exp(-lambda_p t) - exp(-lambda_d t))", "The daughter is produced by the parent and removed by its own decay, so its activity is the difference of the two exponentials.")},
        "The daughter activity is zero at the start, rises to a maximum, and then follows the parent; it never exceeds the parent activity at the "
        "time of the maximum when the parent is longer lived."),
    "S258": _plan(
        "S258",
        "Find the number of radioactive atoms from the mass, the decay constant from the half-life, the activity when the source was made, and then "
        "the fraction that survives after the age of the source.",
        {"N": ("Number of atoms as the mass of the isotope divided by the mass of one atom, N = m/m_atom", "The activity is proportional to the number of radioactive atoms, which is counted from the mass."),
         "lam": ("Decay constant from the half-life, lambda = ln 2/T_half", "The exponential decay law is fixed by the decay constant, which follows from the half-life."),
         "A0": ("Definition of activity, A = lambda N", "The activity is the decay constant times the number of atoms present."),
         "f": ("Exponential decay law, N(t)/N(0) = exp(-lambda t)", "The source has decayed for its age, so only this fraction of the atoms remains."),
         "A": ("Activity is proportional to the number of atoms, A = A0 exp(-lambda t)", "The present activity is the activity when the source was made times the surviving fraction.")},
        "After one half-life the activity has halved; the present activity is below the initial one and is of the order of ten gigabecquerel for a few "
        "milligrams of a short-lived isotope."),
    "S259": _plan(
        "S259",
        "The speeds follow the Maxwell distribution, whose scale is the most probable speed. Find that scale, the cut speed in its units, and then "
        "the fraction above the cut speed from the integral of the distribution, times the amount of gas.",
        {"vp": ("Most probable speed of the Maxwell distribution, v_p = sqrt(2 k T/m)", "The distribution depends on the speed only through its ratio to this scale."),
         "x": ("Dimensionless variable, x = v_c/v_p", "The fraction above a cut speed depends only on the cut speed measured in units of the most probable speed."),
         "F": ("Tail of the Maxwell distribution, F = erfc(x) + (2/sqrt(pi)) x exp(-x^2)", "Integrating the distribution of the speeds from the cut speed to infinity gives this closed form."),
         "nf": ("Amount of the fast atoms as the fraction times the total amount, n_f = n F", "The fraction refers to all the atoms, so the amount of the fast ones is that fraction of the amount in the flask.")},
        "The fraction lies between zero and one, tends to one as the cut speed tends to zero, and falls rapidly as the cut speed grows; it rises with "
        "the temperature."),
    "S260": _plan(
        "S260",
        "A molecule collides about once per mean free path travelled, so the collision rate is the mean speed over the mean free path. Find the "
        "cross-section, the mean free path, the mean speed, and then the ratio.",
        {"sig": ("Collision cross-section of hard spheres of diameter d, sigma = pi d^2", "Two molecules collide when their centres come within one diameter, so the target area is this circle."),
         "lam": ("Mean free path, lambda = k T/(sqrt(2) sigma p), from n = p/(k T) and lambda = 1/(sqrt(2) n sigma)", "The factor sqrt(2) accounts for the motion of the other molecules; the ideal-gas law gives the number density."),
         "vbar": ("Mean speed of a Maxwell gas, v = sqrt(8 k T/(pi m))", "The distance travelled each second is the mean speed."),
         "z": ("Collision rate as the mean speed divided by the mean free path, z = v/lambda", "The molecule travels one mean free path between two successive collisions.")},
        "The rate grows linearly with the pressure and as the square root of the temperature; for nitrogen at atmospheric pressure it is of the "
        "order of several billion per second."),
    "S261": _plan(
        "S261",
        "At the terminal speed the weight is balanced by the buoyant force and the Stokes drag. Find the volume and the mean density of the loaded "
        "sphere, and then the speed from the force balance.",
        {"V": ("Volume of a sphere, V = 4 pi r^3/3", "The mean density and the buoyant force both need the volume of the sphere."),
         "rs": ("Definition of mean density, rho = m/V", "The load is inside the sphere, so the sphere behaves as one body of this mean density."),
         "vt": ("Force balance with Archimedes' principle and Stokes drag, (rho_s - rho_f) V g = 6 pi eta r v, which gives v = 2 g r^2 (rho_s - rho_f)/(9 eta)", "At constant speed there is no net force, so the weight minus the buoyant force equals the viscous drag.")},
        "The speed is positive only if the sphere is denser than the liquid, grows with the square of the radius, and falls as the viscosity "
        "grows."),
    "S262": _plan(
        "S262",
        "The flow rate through the tube is proportional to the depth, so the depth decays exponentially. Find the time constant, the logarithm of "
        "the depth ratio, and the time as their product.",
        {"tau": ("Poiseuille flow with A dh/dt = -pi rho g h r^4/(8 eta L), which gives the time constant tau = 8 eta L A/(pi rho g r^4)", "The flow rate through a long narrow tube is proportional to the driving pressure, hence to the depth, so the depth falls exponentially."),
         "lr": ("Natural logarithm of the ratio of the initial to the final depth", "The depth follows h = h0 exp(-t/tau), so the time for a given fall depends on the logarithm of the depth ratio."),
         "tc": ("Solution of the exponential decay, t = tau ln(h0/h1)", "Inverting the exponential law gives the time to reach the final depth.")},
        "The time grows linearly with the viscosity, the tube length and the tank area, and as the inverse fourth power of the tube radius; it "
        "vanishes when the final depth equals the initial depth."),
}
