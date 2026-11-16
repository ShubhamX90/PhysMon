"""M250 phase 2, thermodynamics and statistical physics batch: ten new DECOY-v2 structures S221 to S230, with gold solution plans.

Written for the M250 exploration pool (plan of record v2.2). Same pattern as `lib_thermodynamics.py`: a typed graph of input and computed
nodes, an independently coded numeric solver (quadrature along a reversible path, a bracketing root finder, a linear system, a direct
sum or integral over the physical definition), four numeric instantiations and a relevant edit that moves the answer. Every stated
physical constant is an input node with provenance "assumed". Every answer-deciding condition (initial state, governing model,
boundary condition) is stated in the base context; the role quantities of the v2.1 specs are in `roles_m250n_thermo.py`.

Level: S221, S222, S223, S229, S230 introductory; S224 to S228 upper-university. Relations (computed nodes): S221 3, S222 4, S223 3,
S224 4, S225 3, S226 3, S227 3, S228 4, S229 3, S230 4.

Admission status: agent-authored and machine-certified only. No human physicist and no LLM panel has reviewed these problems or plans.
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


def _solve_isobaric_heating(n, t1, t2, r):
    # First law: internal energy change of the rotating, non-vibrating molecules (five quadratic degrees of freedom) plus the
    # work p dV done on the piston at a reference pressure, with V = n R T / p (the pressure drops out).
    p = 1.0e5
    d_u = n * 2.5 * r * (t2 - t1)
    work, _ = quad(lambda v: p, n * r * t1 / p, n * r * t2 / p, epsabs=0.0, epsrel=1e-13)
    return float(d_u + work)


def _solve_engine_refrigerator(p_h, t_h, t_m, t_c):
    # Energy and entropy balance of the two reversible machines as a linear system in (W, Q_m1, Q_c, Q_m2):
    # engine: P_h = W + Q_m1 and Q_m1 / T_m = P_h / T_h; refrigerator: Q_m2 = Q_c + W and Q_m2 / T_m = Q_c / T_c.
    matrix = np.array([[1.0, 1.0, 0.0, 0.0],
                       [0.0, 1.0 / t_m, 0.0, 0.0],
                       [1.0, 0.0, 1.0, -1.0],
                       [0.0, 0.0, -1.0 / t_c, 1.0 / t_m]])
    rhs = np.array([p_h, p_h / t_h, 0.0, 0.0])
    return float(np.linalg.solve(matrix, rhs)[2])


def _solve_ice_entropy(m, l_fusion, c, t_melt, t_water):
    # The entropy as the integral of dQ / T along the reversible heating path: melting at constant temperature, then warming.
    melting = m * l_fusion / t_melt
    warming, _ = quad(lambda t: m * c / t, t_melt, t_water, epsabs=0.0, epsrel=1e-13)
    return float(melting + warming)


def _solve_gibbs_mixing(n1, n2, r):
    # Each gas expands isothermally from its own compartment to the whole volume; at equal temperature and pressure the
    # compartment volumes are proportional to the amounts (reference state 300 K and 100 kPa), and dS = integral of n R dV / V.
    t_ref, p_ref = 300.0, 1.0e5
    v1, v2 = n1 * r * t_ref / p_ref, n2 * r * t_ref / p_ref
    total = v1 + v2
    s1, _ = quad(lambda v: n1 * r / v, v1, total, epsabs=0.0, epsrel=1e-13)
    s2, _ = quad(lambda v: n2 * r / v, v2, total, epsabs=0.0, epsrel=1e-13)
    return float(s1 + s2)


def _solve_pipe_temperature(t_in, t_out, r1, r_mid, r2):
    # Steady radial conduction through two shells in series: each thermal resistance is the integral of dr / (2 pi k r L), with a
    # reference conductivity and length; the temperature fall to the mid radius follows from the common heat current.
    k, length = 0.05, 1.0
    res_inner, _ = quad(lambda r: 1.0 / (2.0 * math.pi * k * length * r), r1, r_mid, epsabs=0.0, epsrel=1e-13)
    res_outer, _ = quad(lambda r: 1.0 / (2.0 * math.pi * k * length * r), r_mid, r2, epsabs=0.0, epsrel=1e-13)
    current = (t_in - t_out) / (res_inner + res_outer)
    return float(current * res_inner)


def _solve_shield_temperature(t_hot, t_cold):
    # Equal net radiative flux across the three gaps, written for the fourth powers x_a, x_b of the two shield temperatures:
    # (T1^4 - x_a) = (x_a - x_b) = (x_b - T2^4), a 2 x 2 linear system.
    matrix = np.array([[-2.0, 1.0], [1.0, -2.0]])
    rhs = np.array([-t_hot ** 4, -t_cold ** 4])
    x_a, _x_b = np.linalg.solve(matrix, rhs)
    return float(x_a ** 0.25)


def _solve_mean_energy(d_e, g, t, r):
    # The excited fraction as a logistic function of the log-odds ln g - dE / (R T); the mean energy is that fraction times the gap.
    log_odds = math.log(g) - d_e / (r * t)
    return float(d_e / (1.0 + math.exp(-log_odds)))


def _solve_plate_cooling_time(d, rho, c, h, t0, t_env, t_end):
    # The cooling time as the integral of dt = - (rho d A c dT) / (2 h A (T - T_env)) along the fall of the temperature,
    # for a reference area of one square metre (two faces lose heat).
    area = 1.0
    seconds, _ = quad(lambda t: rho * d * area * c / (2.0 * h * area * (t - t_env)), t_end, t0, epsabs=0.0, epsrel=1e-13)
    return float(seconds)


def _solve_bullet_temperature(v, fraction, c, t0):
    # Energy balance per kilogram: the heat taken in, c (T - T0), equals the fraction of the kinetic energy, found as the root of
    # the imbalance.
    heat = fraction * 0.5 * v * v
    return float(brentq(lambda t: c * (t - t0) - heat, t0, t0 + 1.0e5, xtol=1e-12, rtol=1e-15))


def _solve_entropy_generated(m1, m2, c, t1, t2):
    # The final temperature as the root of the energy balance of the two blocks; the entropy changes as integrals of dQ / T along
    # a reversible path of each block.
    final = brentq(lambda t: m1 * c * (t1 - t) - m2 * c * (t - t2), t2, t1, xtol=1e-13, rtol=1e-15)
    s1, _ = quad(lambda t: m1 * c / t, t1, final, epsabs=0.0, epsrel=1e-13)
    s2, _ = quad(lambda t: m2 * c / t, t2, final, epsabs=0.0, epsrel=1e-13)
    return float(s1 + s2)


# --- structures ---------------------------------------------------------------------------------------


def s221_diatomic_isobaric_heat() -> Structure:
    return Structure(
        "S221", "Heat needed to warm a diatomic gas at constant pressure", "thermodynamics", "diatomic_gas_isobaric_heat_rotational_modes",
        (_in("n", "amount", "mol", "amount of gas", 2.0, (0.5, 5.0)),
         _in("T1", "temperature", "K", "initial temperature of the gas", 300.0, (280.0, 320.0)),
         _in("T2", "temperature", "K", "final temperature of the gas", 360.0, (340.0, 420.0)),
         _in("R", "molar_gas_constant", "J/(mol*K)", "molar gas constant, a stated constant", 8.314, (8.30, 8.33), provenance="assumed"),
         _co("dT", "temperature_change", "K", "rise of the temperature of the gas", "T2 - T1"),
         _co("Cp", "molar_heat_capacity", "J/(mol*K)", "molar heat capacity at constant pressure of the gas", "7*R/2"),
         _co("Q", "energy", "kJ", "heat supplied to the gas", "n*Cp*dT")),
        "Q",
        (Assumption("A-ideal", "The gas is ideal and is heated slowly at constant pressure.", "modelling", ("n", "T1", "T2")),
         Assumption("A-modes", "The translational and rotational motions of the molecules are fully excited and the vibrational motion is not excited at any temperature of the heating.", "modelling", ("R",))),
        _spec("A cylinder with a movable piston holds {n} mol of nitrogen, a diatomic ideal gas, at a temperature of {T1} K. The gas is "
              "heated slowly at constant pressure until its temperature is {T2} K. Over this range the translational and rotational "
              "motions of the molecules are fully excited and their vibrational motion is not excited. Take the molar gas constant "
              "to be R = {R} J/(mol·K).",
              "How much heat is supplied to the gas?", "heat supplied to the gas", "kJ",
              "A separate burner B in another workshop releases {v} {u} of heat, but it is unrelated to this gas.",
              "A reference gas B takes in {v} {u} of heat.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the heating.", "W", equivalent="J"),
        ("n", 1.25), _solve_isobaric_heating, 4,
        "the first law, the internal energy change of five quadratic degrees of freedom plus the piston work integral of p dV, instead of the molar heat capacity at constant pressure",
        solver_rel_tol=1e-9,
        instances=({"n": 2.0, "T1": 300.0, "T2": 360.0, "R": 8.314},
                   {"n": 1.5, "T1": 290.0, "T2": 350.0, "R": 8.314},
                   {"n": 3.2, "T1": 310.0, "T2": 400.0, "R": 8.314},
                   {"n": 0.8, "T1": 285.0, "T2": 345.0, "R": 8.314}))


def s222_engine_driven_refrigerator() -> Structure:
    return Structure(
        "S222", "Heat removed by a refrigerator driven by a Carnot engine", "thermodynamics", "carnot_engine_driving_carnot_refrigerator",
        (_in("Ph", "power", "kW", "rate at which the engine takes heat from the furnace", 50.0, (20.0, 100.0)),
         _in("Th", "temperature", "K", "temperature of the furnace", 600.0, (500.0, 700.0)),
         _in("Tm", "temperature", "K", "temperature of the surroundings", 300.0, (290.0, 310.0)),
         _in("Tc", "temperature", "K", "temperature of the cold room", 265.0, (255.0, 275.0)),
         _co("eta", "ratio", "1", "efficiency of the reversible engine", "1 - Tm/Th"),
         _co("W", "power", "kW", "work output of the engine, which drives the refrigerator", "eta*Ph"),
         _co("COP", "coefficient", "1", "coefficient of performance of the reversible refrigerator", "Tc/(Tm - Tc)"),
         _co("Qc", "power", "kW", "rate at which the refrigerator removes heat from the cold room", "COP*W")),
        "Qc",
        (Assumption("A-reversible", "Both machines are reversible and run in steady operation; the engine and the refrigerator reject heat to the same surroundings.", "modelling", ("Th", "Tm", "Tc")),
         Assumption("A-work", "All of the work output of the engine is the work input of the refrigerator and none is lost.", "boundary_condition", ("Ph",))),
        _spec("A reversible heat engine takes heat at a rate of {Ph} kW from a furnace at {Th} K and rejects its waste heat to the "
              "surroundings at {Tm} K. All of the work that the engine delivers drives a reversible refrigerator, which keeps a cold room "
              "at {Tc} K and rejects its heat to the same surroundings. Both machines run steadily.",
              "At what rate does the refrigerator remove heat from the cold room?", "rate of heat removal from the cold room", "kW",
              "A separate chiller B in another plant removes heat at {v} {u}, but it is unrelated to this refrigerator.",
              "A reference refrigerator B removes heat at {v} {u}.",
              "A separate meter B reads {v} {u}, but it plays no part in the cooling.", "Hz", equivalent="W"),
        ("Ph", 1.25), _solve_engine_refrigerator, 4,
        "the energy balance and the entropy balance of each machine, solved together as a linear system, instead of the two efficiencies multiplied",
        solver_rel_tol=1e-9,
        instances=({"Ph": 50.0, "Th": 600.0, "Tm": 300.0, "Tc": 265.0},
                   {"Ph": 30.0, "Th": 550.0, "Tm": 295.0, "Tc": 260.0},
                   {"Ph": 80.0, "Th": 700.0, "Tm": 305.0, "Tc": 270.0},
                   {"Ph": 40.0, "Th": 520.0, "Tm": 290.0, "Tc": 258.0}))


def s223_ice_entropy_change() -> Structure:
    return Structure(
        "S223", "Entropy change of melting ice that is then warmed", "thermodynamics", "entropy_change_melting_then_warming",
        (_in("m", "mass", "kg", "mass of the ice", 0.2, (0.05, 1.0)),
         _in("Lf", "specific_latent_heat", "kJ/kg", "latent heat of fusion of ice, a stated constant", 334.0, (330.0, 336.0), provenance="assumed"),
         _in("c", "specific_heat", "J/(kg*K)", "specific heat capacity of liquid water, a stated constant", 4186.0, (4100.0, 4250.0), provenance="assumed"),
         _in("T0", "temperature", "K", "melting point of ice, a stated constant", 273.0, (272.0, 274.0), provenance="assumed"),
         _in("Tw", "temperature", "K", "final temperature of the meltwater", 313.0, (305.0, 400.0)),
         _co("Sm", "entropy", "J/K", "entropy change of the ice while it melts", "m*Lf/T0"),
         _co("Sw", "entropy", "J/K", "entropy change of the meltwater while it is warmed", "m*c*log(Tw/T0)"),
         _co("S", "entropy", "J/K", "total entropy change of the ice and the water", "Sm + Sw")),
        "S",
        (Assumption("A-reversible", "The heating is slow, so the ice and the water are in internal equilibrium at every moment.", "modelling", ("m", "Tw")),
         Assumption("A-constants", "The latent heat of fusion and the specific heat capacity of the liquid are constant, and the melting point is the stated constant.", "modelling", ("Lf", "c", "T0")),
         Assumption("A-liquid", "All of the ice melts and the water stays liquid up to its final temperature.", "boundary_condition", ("Tw",))),
        _spec("A block of ice of mass {m} kg is at its melting point of {T0} K. It is heated slowly until it has melted completely "
              "and the meltwater has reached a temperature of {Tw} K. The latent heat of fusion of ice is {Lf} kJ/kg and the specific "
              "heat capacity of liquid water is {c} J/(kg·K), constant over the heating. The water stays liquid.",
              "What is the total change of entropy of the ice and the water?", "total entropy change of the ice and the water", "J/K",
              "A separate gas B in another laboratory gains {v} {u} of entropy, but it is unrelated to this block.",
              "A reference block B of ice gains {v} {u} of entropy.",
              "A separate meter B reads {v} {u}, but it plays no part in the heating.", "W", equivalent=None),
        ("Tw", 1.2), _solve_ice_entropy, 5,
        "the entropy as the integral of dQ / T along the reversible heating path, melting at constant temperature then warming, by adaptive quadrature",
        solver_rel_tol=1e-9,
        instances=({"m": 0.2, "Lf": 334.0, "c": 4186.0, "T0": 273.0, "Tw": 313.0},
                   {"m": 0.5, "Lf": 334.0, "c": 4186.0, "T0": 273.0, "Tw": 325.0},
                   {"m": 0.1, "Lf": 334.0, "c": 4180.0, "T0": 273.0, "Tw": 308.0},
                   {"m": 0.35, "Lf": 334.0, "c": 4186.0, "T0": 273.0, "Tw": 333.0}))


def s224_gibbs_mixing_entropy() -> Structure:
    return Structure(
        "S224", "Entropy of mixing of two different ideal gases", "thermodynamics", "gibbs_entropy_of_mixing_two_ideal_gases",
        (_in("n1", "amount", "mol", "amount of helium", 1.5, (0.5, 3.0)),
         _in("n2", "amount", "mol", "amount of argon", 2.5, (0.5, 4.0)),
         _in("R", "molar_gas_constant", "J/(mol*K)", "molar gas constant, a stated constant", 8.314, (8.30, 8.33), provenance="assumed"),
         _co("n", "amount", "mol", "total amount of gas", "n1 + n2"),
         _co("x1", "ratio", "1", "mole fraction of helium after mixing", "n1/n"),
         _co("x2", "ratio", "1", "mole fraction of argon after mixing", "n2/n"),
         _co("dS", "entropy", "J/K", "total entropy change of the two gases", "-R*(n1*log(x1) + n2*log(x2))")),
        "dS",
        (Assumption("A-ideal", "Both gases are ideal and different species; they start at the same temperature and, because the partition slides freely, at the same pressure.", "modelling", ("n1", "n2")),
         Assumption("A-isolated", "The container is rigid and thermally insulated, so the mixing is adiabatic and does no work, and the temperature does not change.", "boundary_condition", ("n1", "n2")),
         Assumption("A-R", "The molar gas constant has the stated value.", "modelling", ("R",))),
        _spec("A rigid, thermally insulated container is divided into two compartments by a thin partition that is free to slide. One "
              "compartment holds {n1} mol of helium and the other holds {n2} mol of argon, both ideal gases at the same temperature, "
              "and the sliding partition keeps their pressures equal. The partition is then removed and the gases mix completely. "
              "Take the molar gas constant to be R = {R} J/(mol·K).",
              "What is the total entropy change of the two gases?", "total entropy change of the two gases", "J/K",
              "A separate gas B in another vessel gains {v} {u} of entropy, but it is unrelated to this container.",
              "A reference mixture B gains {v} {u} of entropy.",
              "A separate meter B reads {v} {u}, but it plays no part in the mixing.", "W", equivalent=None),
        ("n1", 1.25), _solve_gibbs_mixing, 3,
        "each gas expanding isothermally from its own compartment volume to the whole volume, the entropy as the integral of n R dV / V, instead of the mole-fraction formula",
        solver_rel_tol=1e-9,
        instances=({"n1": 1.5, "n2": 2.5, "R": 8.314},
                   {"n1": 2.0, "n2": 1.0, "R": 8.314},
                   {"n1": 3.0, "n2": 0.8, "R": 8.314},
                   {"n1": 1.2, "n2": 3.4, "R": 8.314}))


def s225_pipe_insulation_temperature() -> Structure:
    return Structure(
        "S225", "Temperature fall inside the insulation of a steam pipe", "thermodynamics", "radial_conduction_temperature_profile_cylinder",
        (_in("Tin", "temperature", "K", "temperature of the outer surface of the pipe", 420.0, (380.0, 480.0)),
         _in("Tout", "temperature", "K", "temperature of the outer surface of the insulation", 300.0, (285.0, 320.0)),
         _in("r1", "length", "cm", "outer radius of the pipe", 3.0, (2.0, 4.0)),
         _in("rm", "length", "cm", "radius at which the temperature is asked", 5.0, (4.5, 7.0)),
         _in("r2", "length", "cm", "outer radius of the insulation", 9.0, (8.0, 12.0)),
         _co("a", "ratio", "1", "logarithm of the ratio of the asked radius to the pipe radius", "log(rm/r1)"),
         _co("b", "ratio", "1", "logarithm of the ratio of the outer radius of the insulation to the pipe radius", "log(r2/r1)"),
         _co("dTm", "temperature_change", "K", "fall of the temperature from the pipe surface to the asked radius", "(Tin - Tout)*a/b")),
        "dTm",
        (Assumption("A-steady", "The heat flow is steady, purely radial and along a long straight pipe, with no heat flow along its axis.", "modelling", ("Tin", "Tout")),
         Assumption("A-uniform", "The insulation is uniform with a constant thermal conductivity and is in perfect contact with the pipe.", "modelling", ("r1", "r2", "rm"))),
        _spec("A long steam pipe has an outer radius of {r1} cm and its outer surface is held at {Tin} K. The pipe is wrapped in a "
              "uniform layer of insulation out to a radius of {r2} cm, and the outer surface of the insulation is held at {Tout} K. "
              "The heat flow is steady and purely radial.",
              "By how many kelvin does the temperature fall from the outer surface of the pipe to a radius of {rm} cm from its axis?",
              "temperature fall from the pipe surface to the stated radius", "K",
              "A separate boiler B in another plant runs at {v} {u}, but it is unrelated to this pipe.",
              "A reference pipe B has an outer surface at {v} {u}.",
              "A separate meter B reads {v} {u}, but it plays no part in the heat flow.", "W", equivalent=None),
        ("Tin", 1.1), _solve_pipe_temperature, 5,
        "the two shell resistances as integrals of dr / (2 pi k r L) in series for a reference conductivity and length, then the temperature from the common heat current",
        solver_rel_tol=1e-9,
        instances=({"Tin": 420.0, "Tout": 300.0, "r1": 3.0, "rm": 5.0, "r2": 9.0},
                   {"Tin": 400.0, "Tout": 290.0, "r1": 2.5, "rm": 4.8, "r2": 8.5},
                   {"Tin": 450.0, "Tout": 310.0, "r1": 3.5, "rm": 6.0, "r2": 10.0},
                   {"Tin": 390.0, "Tout": 295.0, "r1": 2.0, "rm": 5.5, "r2": 11.0}))


def s226_radiation_shield_temperature() -> Structure:
    return Structure(
        "S226", "Temperature of a radiation shield between two hot walls", "thermodynamics", "radiation_shields_equilibrium_temperature",
        (_in("T1", "temperature", "K", "temperature of the hot plate", 800.0, (600.0, 1000.0)),
         _in("T2", "temperature", "K", "temperature of the cold plate", 300.0, (250.0, 400.0)),
         _co("rt", "ratio", "1", "ratio of the cold plate temperature to the hot plate temperature", "T2/T1"),
         _co("x", "ratio", "1", "fourth power of the ratio of the shield temperature to the hot plate temperature", "(2 + rt**4)/3"),
         _co("Ts", "temperature", "K", "temperature of the shield nearer the hot plate", "T1*x**(1/4)")),
        "Ts",
        (Assumption("A-grey", "All the plate and shield surfaces are diffuse and grey with the same emissivity; only radiation transfers heat, across a vacuum.", "modelling", ("T1", "T2")),
         Assumption("A-steady", "The plates and the shields are large and parallel so that edge effects vanish; the situation is steady and each thin shield has one temperature.", "boundary_condition", ("T1", "T2"))),
        _spec("Two large parallel plates face each other across a vacuum, a hot plate at {T1} K and a cold plate at {T2} K. Two thin "
              "radiation shields, parallel to the plates, are placed one behind the other between them. All the surfaces are diffuse and "
              "grey and have the same emissivity. Only radiation transfers heat, the edges are negligible and the situation is steady.",
              "What is the temperature of the shield that is nearer the hot plate?", "temperature of the shield nearer the hot plate", "K",
              "A separate oven B in another kitchen has a wall at {v} {u}, but it is unrelated to these plates.",
              "A reference shield B has a temperature of {v} {u}.",
              "A separate meter B reads {v} {u}, but it plays no part in the radiation.", "W", equivalent=None),
        ("T1", 1.25), _solve_shield_temperature, 2,
        "equal net radiative flux across the three gaps written for the fourth powers of the shield temperatures, a 2 x 2 linear system, instead of the closed form with the weights two thirds and one third",
        solver_rel_tol=1e-9,
        instances=({"T1": 800.0, "T2": 300.0},
                   {"T1": 700.0, "T2": 320.0},
                   {"T1": 950.0, "T2": 280.0},
                   {"T1": 650.0, "T2": 350.0}))


def s227_excited_level_population() -> Structure:
    return Structure(
        "S227", "Mean energy per mole of a gas with a degenerate excited level", "thermodynamics", "boltzmann_two_level_mean_energy_with_degeneracy",
        (_in("dE", "molar_energy", "kJ/mol", "energy of the excited level above the ground level", 6.0, (2.0, 15.0)),
         _in("g", "ratio", "1", "degeneracy of the excited level", 3.0, (1.0, 5.0)),
         _in("T", "temperature", "K", "temperature of the gas", 300.0, (250.0, 400.0)),
         _in("R", "molar_gas_constant", "J/(mol*K)", "molar gas constant, a stated constant", 8.314, (8.30, 8.33), provenance="assumed"),
         _co("x", "ratio", "1", "energy gap in units of R T", "dE/(R*T)"),
         _co("w", "ratio", "1", "Boltzmann weight of the excited level relative to the ground level", "g*exp(-x)"),
         _co("U", "molar_energy", "kJ/mol", "mean energy per mole above the ground level", "dE*w/(1 + w)")),
        "U",
        (Assumption("A-equilibrium", "The molecules are in thermal equilibrium and obey Boltzmann statistics; they are independent of one another.", "modelling", ("dE", "T")),
         Assumption("A-levels", "Only the ground level, which is not degenerate, and the one excited level are accessible; every other level lies so high that it is empty, and the ground level is the zero of energy.", "boundary_condition", ("g",)),
         Assumption("A-R", "The molar gas constant has the stated value.", "modelling", ("R",))),
        _spec("A dilute gas is in thermal equilibrium at a temperature of {T} K. Each molecule has a ground level that is not "
              "degenerate, taken as the zero of energy, and one excited level that lies {dE} kJ/mol above it and has a degeneracy of "
              "{g}. Every other level of the molecule lies so high that it is empty. Take the molar gas constant to be "
              "R = {R} J/(mol·K).",
              "What is the mean energy of the molecules per mole, measured from the ground level?",
              "mean energy per mole above the ground level", "kJ/mol",
              "A separate furnace B in another laboratory stores {v} {u} of energy, but it is unrelated to this gas.",
              "A reference gas B has a mean energy of {v} {u}.",
              "A separate meter B reads {v} {u}, but it plays no part in the equilibrium.", "W", equivalent="J/mol"),
        ("T", 1.25), _solve_mean_energy, 4,
        "the mean energy as the energy gap times the excited fraction, written as a logistic function of the log-odds ln g - dE / (R T), instead of the weight divided by the partition function",
        solver_rel_tol=1e-9,
        instances=({"dE": 6.0, "g": 3.0, "T": 300.0, "R": 8.314},
                   {"dE": 4.0, "g": 2.0, "T": 350.0, "R": 8.314},
                   {"dE": 10.0, "g": 5.0, "T": 320.0, "R": 8.314},
                   {"dE": 3.0, "g": 1.0, "T": 280.0, "R": 8.314}))


def s228_plate_cooling_time() -> Structure:
    return Structure(
        "S228", "Time for a hot metal plate to cool in air", "thermodynamics", "lumped_capacitance_cooling_time_plate",
        (_in("d", "length", "mm", "thickness of the plate", 6.0, (2.0, 15.0)),
         _in("rho", "density", "kg/m^3", "density of the metal", 2700.0, (2500.0, 9000.0)),
         _in("c", "specific_heat", "J/(kg*K)", "specific heat capacity of the metal", 900.0, (380.0, 900.0)),
         _in("h", "heat_transfer_coefficient", "W/(m^2*K)", "heat transfer coefficient of each face", 25.0, (15.0, 60.0)),
         _in("T0", "temperature", "K", "initial temperature of the plate", 450.0, (400.0, 500.0)),
         _in("Te", "temperature", "K", "temperature of the air", 300.0, (290.0, 310.0)),
         _in("Tt", "temperature", "K", "temperature at which the plate is to be handled", 350.0, (330.0, 380.0)),
         _co("Lc", "length", "m", "half of the thickness: the volume of the plate divided by the area of both faces", "d/2"),
         _co("tau", "time", "s", "time constant of the cooling", "rho*c*Lc/h"),
         _co("th", "ratio", "1", "ratio of the initial to the final temperature excess over the air", "(T0 - Te)/(Tt - Te)"),
         _co("tc", "time", "min", "time for the plate to cool to the stated temperature", "tau*log(th)")),
        "tc",
        (Assumption("A-lumped", "The temperature of the plate is the same throughout at every instant, so one temperature describes it.", "modelling", ("d", "rho", "c")),
         Assumption("A-convection", "Both faces lose heat by convection with the stated constant coefficient, to air that stays at its temperature; the edges and radiation are neglected.", "modelling", ("h", "Te")),
         Assumption("A-start", "The plate starts at a uniform temperature.", "boundary_condition", ("T0",))),
        _spec("A thin metal plate of thickness {d} mm, density {rho} kg/m³ and specific heat capacity {c} J/(kg·K) is lifted from a "
              "furnace at a uniform temperature of {T0} K and hangs in air at {Te} K. Each face loses heat by convection "
              "with a heat transfer coefficient of {h} W/(m²·K). The edges and radiation are negligible, and at every instant the "
              "temperature of the plate is the same throughout.",
              "How long does the plate take to cool to {Tt} K?", "time for the plate to cool", "min",
              "A separate oven B in another workshop is held at {v} {u}, but it is unrelated to this plate.",
              "A reference plate B takes {v} {u} to cool.",
              "A separate meter B reads {v} {u}, but it plays no part in the cooling.", "W", equivalent="s"),
        ("h", 1.25), _solve_plate_cooling_time, 7,
        "the cooling time as the integral of dt = rho d c dT / (2 h (T - T_env)) along the fall of the temperature, by adaptive quadrature, instead of the exponential solution",
        solver_rel_tol=1e-9,
        instances=({"d": 6.0, "rho": 2700.0, "c": 900.0, "h": 25.0, "T0": 450.0, "Te": 300.0, "Tt": 350.0},
                   {"d": 4.0, "rho": 7800.0, "c": 480.0, "h": 30.0, "T0": 480.0, "Te": 295.0, "Tt": 340.0},
                   {"d": 10.0, "rho": 8900.0, "c": 390.0, "h": 20.0, "T0": 420.0, "Te": 305.0, "Tt": 370.0},
                   {"d": 3.0, "rho": 2700.0, "c": 880.0, "h": 40.0, "T0": 500.0, "Te": 292.0, "Tt": 360.0}))


def s229_bullet_final_temperature() -> Structure:
    return Structure(
        "S229", "Temperature of a bullet that stops in a steel plate", "thermodynamics", "kinetic_energy_to_heat_temperature_rise",
        (_in("v", "speed", "m/s", "speed of the bullet before the impact", 300.0, (150.0, 500.0)),
         _in("f", "ratio", "1", "fraction of the kinetic energy that becomes internal energy of the bullet", 0.5, (0.3, 0.9)),
         _in("c", "specific_heat", "J/(kg*K)", "specific heat capacity of the metal of the bullet", 130.0, (110.0, 400.0)),
         _in("T0", "temperature", "K", "temperature of the bullet when it was loaded", 293.0, (273.0, 303.0)),
         _co("ek", "specific_energy", "J/kg", "kinetic energy of the bullet per unit mass", "v**2/2"),
         _co("dT", "temperature_change", "K", "rise of the temperature of the bullet", "f*ek/c"),
         _co("Tf", "temperature", "K", "temperature of the bullet after the impact", "T0 + dT")),
        "Tf",
        (Assumption("A-fraction", "The stated fraction of the kinetic energy becomes internal energy of the bullet, shared uniformly through it; the rest goes into the plate.", "modelling", ("f", "v")),
         Assumption("A-c", "The specific heat capacity of the metal is the stated constant over the temperature range, and the bullet stays solid.", "modelling", ("c",))),
        _spec("A metal bullet, loaded at a temperature of {T0} K, hits a thick steel plate at a speed of {v} m/s and stops in it. A fraction "
              "{f} of its kinetic energy becomes internal energy of the bullet, shared uniformly through it, and the rest goes into the "
              "plate. The specific heat capacity of the metal of the bullet is {c} J/(kg·K) and is constant. The bullet stays solid.",
              "What is the temperature of the bullet just after it has stopped?", "temperature of the bullet after it has stopped", "K",
              "A separate furnace B in another foundry runs at {v} {u}, but it is unrelated to this bullet.",
              "A reference bullet B has a temperature of {v} {u}.",
              "A separate meter B reads {v} {u}, but it plays no part in the impact.", "W", equivalent=None),
        ("v", 1.25), _solve_bullet_temperature, 4,
        "the energy balance per kilogram, c (T - T0) equal to the share of the kinetic energy, as the root of the imbalance found with a bracketing root finder",
        solver_rel_tol=1e-9,
        instances=({"v": 300.0, "f": 0.5, "c": 130.0, "T0": 293.0},
                   {"v": 250.0, "f": 0.4, "c": 130.0, "T0": 288.0},
                   {"v": 320.0, "f": 0.45, "c": 140.0, "T0": 295.0},
                   {"v": 200.0, "f": 0.7, "c": 125.0, "T0": 285.0}))


def s230_entropy_generated_by_contact() -> Structure:
    return Structure(
        "S230", "Entropy generated when two metal blocks reach equilibrium", "thermodynamics", "entropy_generation_two_finite_bodies_contact",
        (_in("m1", "mass", "kg", "mass of the hotter block", 2.0, (0.5, 4.0)),
         _in("m2", "mass", "kg", "mass of the colder block", 3.0, (0.5, 5.0)),
         _in("c", "specific_heat", "J/(kg*K)", "specific heat capacity of the metal", 900.0, (380.0, 900.0)),
         _in("T1", "temperature", "K", "initial temperature of the hotter block", 360.0, (340.0, 400.0)),
         _in("T2", "temperature", "K", "initial temperature of the colder block", 290.0, (280.0, 310.0)),
         _co("Tf", "temperature", "K", "common final temperature of the two blocks", "(m1*T1 + m2*T2)/(m1 + m2)"),
         _co("S1", "entropy", "J/K", "entropy change of the hotter block", "m1*c*log(Tf/T1)"),
         _co("S2", "entropy", "J/K", "entropy change of the colder block", "m2*c*log(Tf/T2)"),
         _co("Sg", "entropy", "J/K", "total entropy change of the two blocks", "S1 + S2")),
        "Sg",
        (Assumption("A-isolated", "The two blocks exchange heat only with each other inside a rigid, perfectly insulated enclosure.", "boundary_condition", ("m1", "m2", "T1", "T2")),
         Assumption("A-c", "Both blocks are made of the same metal with the stated specific heat capacity, constant over the temperature range, and their volumes do not change appreciably.", "modelling", ("c",))),
        _spec("A hotter block of mass {m1} kg at {T1} K and a colder block of the same metal, of mass {m2} kg, at {T2} K are brought "
              "into thermal contact inside a rigid, perfectly insulated enclosure and come to a common temperature. The "
              "specific heat capacity of the metal is {c} J/(kg·K) and is constant, and the volumes of the blocks do not change "
              "appreciably.",
              "How much entropy is generated in the process?", "entropy generated in the process", "J/K",
              "A separate engine B in another plant produces {v} {u} of entropy, but it is unrelated to these blocks.",
              "A reference pair of blocks B generates {v} {u} of entropy.",
              "A separate meter B reads {v} {u}, but it plays no part in the contact.", "W", equivalent=None),
        ("m1", 1.25), _solve_entropy_generated, 5,
        "the final temperature as the root of the energy balance, then each entropy change as the integral of dQ / T along a reversible path of the block, by adaptive quadrature",
        solver_rel_tol=1e-9,
        instances=({"m1": 2.0, "m2": 3.0, "c": 900.0, "T1": 360.0, "T2": 290.0},
                   {"m1": 1.5, "m2": 1.0, "c": 385.0, "T1": 380.0, "T2": 300.0},
                   {"m1": 4.0, "m2": 2.5, "c": 500.0, "T1": 350.0, "T2": 285.0},
                   {"m1": 0.8, "m2": 3.2, "c": 450.0, "T1": 400.0, "T2": 295.0}))


ALL = (s221_diatomic_isobaric_heat, s222_engine_driven_refrigerator, s223_ice_entropy_change, s224_gibbs_mixing_entropy,
       s225_pipe_insulation_temperature, s226_radiation_shield_temperature, s227_excited_level_population,
       s228_plate_cooling_time, s229_bullet_final_temperature, s230_entropy_generated_by_contact)


def all_structures() -> list[Structure]:
    return [factory() for factory in ALL]


STRUCTURES: dict[str, Structure] = {s.structure_id: s for s in all_structures()}

# Level of each structure: "introductory" or "upper-university" (S224 to S228: statistical entropy of mixing, radial conduction, radiation
# networks, Boltzmann statistics with degeneracy, lumped-capacitance transients).
LEVELS: dict[str, str] = {
    "S221": "introductory", "S222": "introductory", "S223": "introductory", "S224": "upper-university",
    "S225": "upper-university", "S226": "upper-university", "S227": "upper-university", "S228": "upper-university",
    "S229": "introductory", "S230": "introductory",
}

# --- gold solution plans ---------------------------------------------------------------------------------

PLANS: dict[str, Plan] = {
    "S221": Plan(
        approach="We are asked for the heat needed to warm a diatomic ideal gas at constant pressure when only its translation and "
                 "rotation are excited. Find the temperature rise, the molar heat capacity at constant pressure from the equipartition "
                 "of energy, and then the heat from the heat capacity.",
        steps=(
            Step("Cp",
                 "Equipartition of energy: three translational and two rotational quadratic degrees of freedom give Cv = 5R/2, and Mayer's relation Cp = Cv + R gives Cp = 7R/2",
                 "The molecules rotate but do not vibrate over this range, so vibration adds no degree of freedom; heating at constant pressure also does work on the piston, which is the extra R."),
            Step("dT", "Definition of the temperature change, delta T = T2 - T1",
                 "The heat needed depends on how far the temperature rises, so we first take the difference of the final and initial temperatures."),
            Step("Q",
                 "Heat at constant pressure, Q = n Cp delta T",
                 "With the molar heat capacity at constant pressure known, the heat supplied is the amount of gas times Cp times the temperature rise."),
        ),
        check="The heat is larger than the change of internal energy, n (5R/2) delta T, by exactly the work n R delta T done on the piston, and "
              "it is 7/5 of the heat needed to warm the same gas at constant volume."),
    "S222": Plan(
        approach="The work of the engine is the input of the refrigerator. Find the engine efficiency from the reversible limit, the work "
                 "it delivers, the reversible coefficient of performance of the refrigerator, and then the heat it removes from the cold room.",
        steps=(
            Step("COP", "Coefficient of performance of a reversible refrigerator, COP = T_cold/(T_hot - T_cold) with the temperatures of the cold room and the surroundings",
                 "The refrigerator is reversible, so its entropy balance fixes how much heat it can lift out of the cold room per unit of work."),
            Step("eta", "Efficiency of a reversible (Carnot) engine, eta = 1 - T_cold/T_hot, from the entropy balance Q_h/T_h = Q_m/T_m",
                 "The engine is reversible, so it has no entropy production and its waste heat to the surroundings at Tm is fixed by the furnace temperature."),
            Step("W", "Definition of efficiency, W = eta Q_h, for the rate at which heat is taken from the furnace",
                 "The work output per unit time is the efficiency times the heat rate drawn from the furnace; all of it drives the refrigerator."),
            Step("Qc", "Definition of the coefficient of performance, Q_c = COP W",
                 "The heat removed from the cold room per unit time is the coefficient of performance times the work input per unit time."),
        ),
        check="With the same two machines the heat removed is between zero and Q_h times the product of the two ideal factors; for "
              "a furnace at the surroundings temperature the work and the removed heat both vanish."),
    "S223": Plan(
        approach="The entropy change is the heat taken in divided by the temperature along a reversible heating path. Find the "
                 "entropy gained while the ice melts at constant temperature, the entropy gained while the meltwater warms, and add them.",
        steps=(
            Step("Sm", "Entropy change at a phase transition, delta S = m L_f / T_melt (the heat m L_f is taken in at constant temperature)",
                 "The ice melts at its melting point, so the temperature is constant during this stage and the entropy change is just the latent heat divided by it."),
            Step("Sw", "Entropy change on warming a liquid of constant specific heat, delta S = integral of m c dT/T = m c ln(T_final/T_initial)",
                 "While the meltwater warms from the melting point to its final temperature the heat taken in at each temperature is m c dT, so the entropy is the integral of that over T."),
            Step("S", "Entropy is a state function and extensive, so the entropy changes of the successive stages add",
                 "The total change of entropy of the ice and the water is the sum of the melting part and the warming part."),
        ),
        check="The total is positive because heat is taken in, and it exceeds the melting part alone; for a final temperature equal to "
              "the melting point the warming part is zero."),
    "S224": Plan(
        approach="Each gas expands into the whole container at the same temperature, and for ideal gases the entropy changes of the "
                 "two gases are independent. Find the total amount and the mole fractions, then the sum of n R ln(1/x) over the gases.",
        steps=(
            Step("n", "Conservation of amount of substance, n = n1 + n2",
                 "The mole fractions after mixing need the total amount of gas in the container."),
            Step("x1", "Definition of the mole fraction, x = n_i/n; at equal temperature and pressure it is also the volume fraction",
                 "The helium occupies the fraction x1 of the final volume, and so it is the fraction of the volume that it had before the partition was removed."),
            Step("x2", "Definition of the mole fraction, x = n_i/n",
                 "The argon is treated in the same way: its initial compartment was the fraction x2 of the whole container."),
            Step("dS", "Entropy of mixing of ideal gases, delta S = -R (n1 ln x1 + n2 ln x2), from delta S_i = n_i R ln(V_final/V_i) for each gas expanding isothermally",
                 "Each ideal gas behaves as if the other were absent, so each gains the entropy of an isothermal expansion from its own compartment to the whole container, and these add."),
        ),
        check="The entropy change is positive for any two gases and is largest, n R ln 2, when the two amounts are equal; it vanishes "
              "when one amount tends to zero."),
    "S225": Plan(
        approach="For steady radial conduction the heat current through every cylindrical shell is the same, so the temperature "
                 "falls with the logarithm of the radius. Find the logarithms of the two radius ratios, then the temperature fall to the asked radius.",
        steps=(
            Step("a", "Radial conduction in a cylinder, T falls linearly with ln r, so the inner shell has the weight ln(rm/r1)",
                 "The thermal resistance of a shell between two radii is proportional to the logarithm of their ratio, so we need that logarithm for the shell from the pipe to the asked radius."),
            Step("b", "Radial conduction in a cylinder, the thermal resistance of the whole insulation is proportional to ln(r2/r1)",
                 "The same logarithm for the whole insulation layer gives the total resistance, in the same units as the inner shell."),
            Step("dTm", "Steady heat current through thermal resistances in series, T_in - T(rm) = (T_in - T_out) ln(rm/r1)/ln(r2/r1)",
                 "The heat current is the same through both shells, so the fraction of the total temperature drop across the inner shell is the ratio of the resistances; the conductivity and the pipe length cancel."),
        ),
        check="The fall is smaller than the full temperature difference and larger than the fall a flat slab would give over the same "
              "fraction of the thickness, because the area grows with the radius, so most of the drop is near the pipe."),
    "S226": Plan(
        approach="With the same emissivity everywhere, the net radiative flux between neighbouring surfaces is proportional to the "
                 "difference of the fourth powers of their temperatures, and the flux is the same across all three gaps. Solve for the "
                 "fourth powers of the shield temperatures.",
        steps=(
            Step("rt", "Definition of the temperature ratio, rt = T2/T1",
                 "Writing the cold plate temperature in units of the hot plate temperature reduces the problem to a dimensionless balance of fourth powers."),
            Step("x", "Stefan-Boltzmann radiation between parallel grey surfaces: net flux proportional to the difference of T^4, equal across the three gaps, so the fourth powers are evenly spaced",
                 "The steady flux through the stack is the same in every gap and the emissivity factor is the same for each gap, so the fourth power falls by equal steps; the shield nearer the hot plate is at two thirds of the way towards the hot value."),
            Step("Ts", "Taking the fourth root, Ts = T1 x^(1/4), to return from the fourth power to the temperature",
                 "The balance gave the fourth power of the shield temperature in units of T1^4, so the temperature is T1 times its fourth root."),
        ),
        check="The shield temperature lies between the two plate temperatures and nearer the hot plate; without the shields (no "
              "shield) the flux would be three times larger, and the emissivity does not appear in the answer."),
    "S227": Plan(
        approach="At thermal equilibrium the populations follow the Boltzmann factor weighted by the degeneracy. Find the energy gap "
                 "in units of R T, the weight of the excited level relative to the ground level, and the mean energy from the partition function.",
        steps=(
            Step("x", "Boltzmann factor exp(-E/(k T)) per molecule, written per mole as exp(-dE/(R T)); x = dE/(R T)",
                 "The dimensionless ratio of the energy gap to the thermal energy R T decides how strongly the excited level is populated."),
            Step("w", "Boltzmann distribution with degeneracy, the relative weight of a level is g exp(-E/(k T))",
                 "The excited level has g states, each with the same Boltzmann factor, so its weight relative to the non-degenerate ground level is g e^(-x)."),
            Step("U", "Mean energy from the partition function, U = dE w/Z with Z = 1 + w, the sum of the weights of the two accessible levels",
                 "Only the two levels are accessible, so the fraction of the molecules in the excited level is w/(1 + w), and each of them carries the energy dE above the ground level, which is the zero of energy."),
        ),
        check="The mean energy tends to zero at low temperature and to dE g/(1 + g) at very high temperature, where all states are "
              "equally likely; it never exceeds dE."),
    "S228": Plan(
        approach="With one temperature throughout the plate (lumped heat capacity) and heat lost by convection from both faces, the "
                 "temperature excess over the air decays exponentially. Find the time constant and the ratio of the temperature excesses, "
                 "then the time.",
        steps=(
            Step("Lc", "Characteristic length of a plate losing heat from both faces, the volume divided by the surface area, V/A = d/2",
                 "The heat capacity grows with the volume and the heat loss with the surface area of both faces, so only their ratio, half the thickness, matters; the face area cancels."),
            Step("th", "The solution T - T_env = (T0 - T_env) exp(-t/tau), so the ratio of the initial to the final excess is exp(t/tau)",
                 "The cooling is measured as a fall of the temperature excess over the air, so we form the ratio of the initial excess to the excess at the asked temperature."),
            Step("tau", "Lumped-capacitance model, m c dT/dt = -h A (T - T_env), with time constant tau = rho c (V/A)/h",
                 "The plate is at one temperature, so the energy balance of the whole plate gives an exponential decay with this time constant."),
            Step("tc", "Inverting the exponential law, t = tau ln(ratio of the temperature excesses)",
                 "The time to reach the asked temperature is the time constant times the natural logarithm of that ratio."),
        ),
        check="The time grows linearly with the thickness and the density and falls as the heat transfer coefficient grows; it vanishes "
              "when the asked temperature equals the initial one."),
    "S229": Plan(
        approach="The stated fraction of the kinetic energy of the bullet is turned into internal energy, so the temperature rise follows "
                 "from the specific heat capacity. Working per unit mass, find the kinetic energy, the temperature rise and the final temperature.",
        steps=(
            Step("ek", "Kinetic energy per unit mass, e = v^2/2",
                 "The energy that can be turned into heat is the kinetic energy; per unit mass it does not depend on the mass of the bullet."),
            Step("dT", "Heat and temperature rise, Q = m c delta T, with Q = f m v^2/2 the share of the kinetic energy that heats the bullet",
                 "Setting the heat taken in by the bullet equal to the stated fraction of its kinetic energy, the mass cancels and the rise is f e/c."),
            Step("Tf", "Final temperature is the initial temperature plus the rise, T = T0 + delta T",
                 "The question asks for the temperature of the bullet, not for its rise, so the initial temperature is added."),
        ),
        check="The rise is independent of the mass of the bullet, grows with the square of the speed, and is below the value for f = 1; "
              "it is of order a hundred kelvin for a speed of a few hundred metres per second in a soft metal."),
    "S230": Plan(
        approach="The blocks exchange heat only with each other, so energy conservation fixes the common final temperature. The "
                 "entropy change of each block is found along a reversible path, and the entropy generated is their sum.",
        steps=(
            Step("Tf", "Conservation of energy for an isolated pair of blocks, m1 c (T1 - Tf) = m2 c (Tf - T2)",
                 "No heat leaves the enclosure and the specific heat is the same, so the final temperature is the mass-weighted mean of the initial temperatures."),
            Step("S1", "Entropy change of a body of constant specific heat, delta S = m c ln(T_final/T_initial), the integral of dQ/T along a reversible path",
                 "Entropy is a state function, so we may use any reversible path between the same states; for the hotter block the result is negative."),
            Step("S2", "Entropy change of a body of constant specific heat, delta S = m c ln(T_final/T_initial)",
                 "The colder block is treated in the same way and gains entropy."),
            Step("Sg", "Entropy is extensive, so the entropy generated in an isolated system is the sum of the changes of its parts",
                 "The enclosure is isolated, so the total change of entropy of the two blocks is the entropy generated by the irreversible heat flow."),
        ),
        check="The result is positive, as the second law requires, and it vanishes when the two initial temperatures are equal."),
}
