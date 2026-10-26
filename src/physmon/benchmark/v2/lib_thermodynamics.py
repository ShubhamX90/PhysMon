"""Thermodynamics and statistical physics batch of DECOY-v2 structures, S51 to S57, with gold solution plans (Stage 14.19).

Written by the specialised thermodynamics author agent. Same pattern as `library_c.py`: a typed graph with input and computed nodes, an
independently coded numeric solver (a bracketing root finder, a quadrature, a linear system, a direct numerical definition), four numeric
instantiations and a relevant edit that moves the answer. Every physical constant that a solver needs is a stated input node with
provenance "assumed".

The module also holds the gold solution plans (`trace.Plan`) of the seven new structures and of six existing structures of this domain
(S09, S17, S18, S23, S24, S30). A plan is the shared solving technique: the named law at each step, why it applies, and a sanity check.

Admission status: agent-verified, not expert-reviewed. No human physicist has reviewed these problems or plans.
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


def _solve_adiabatic_compression(n, t1, r, gamma, gas_constant):
    # Work done on the gas as the integral of p dV along the curve p V^gamma = const, fixed by the initial state.
    # The reference initial volume is arbitrary (one cubic metre); the work does not depend on it.
    v1 = 1.0
    v2 = v1 / r
    constant = n * gas_constant * t1 * v1 ** (gamma - 1.0)  # p1 V1^gamma = n R T1 V1^(gamma - 1)
    work, _ = quad(lambda v: constant * v ** (-gamma), v2, v1, epsabs=0.0, epsrel=1e-13)
    return float(work)


def _solve_ice_water(m_ice, l_fusion, m_water, c, d_t_water):
    # Energy balance as a function of the final excess temperature x: heat taken in by the ice (melting, then warming as liquid)
    # minus the heat given up by the warm water; the root is the final temperature, then the heat given up by the water.
    def imbalance(x):
        return m_ice * l_fusion + m_ice * c * x - m_water * c * (d_t_water - x)

    final = brentq(imbalance, 0.0, d_t_water, xtol=1e-13, rtol=1e-15)
    return float(m_water * c * (d_t_water - final))


def _solve_two_layer_wall(area, l1, k1, l2, k2, d_t):
    # Continuity of the heat current at the interface as a linear system in (interface temperature rise, heat current):
    # T_i + P R1 = dT (first layer) and P R2 - T_i = 0 (second layer), measuring temperature from the cold surface.
    r1 = l1 / (k1 * area)
    r2 = l2 / (k2 * area)
    solution = np.linalg.solve(np.array([[1.0, r1], [-1.0, r2]]), np.array([d_t, 0.0]))
    return float(solution[1])


def _solve_radiated_power(p1, r1, t1, r2, t2):
    # Direct numerical definition: the first sphere fixes the product (emissivity x Stefan-Boltzmann constant) from P = e sigma A T^4,
    # and that value is then used for the second sphere.
    e_sigma = p1 / (4.0 * math.pi * r1 ** 2 * t1 ** 4)
    return float(e_sigma * 4.0 * math.pi * r2 ** 2 * t2 ** 4)


def _solve_rms_speed(temperature, molar_mass, gas_constant):
    # The second moment of the Maxwell-Boltzmann speed distribution, integrated numerically; its square root is the rms speed.
    def density(v):
        return 4.0 * math.pi * (molar_mass / (2.0 * math.pi * gas_constant * temperature)) ** 1.5 * v * v * math.exp(
            -molar_mass * v * v / (2.0 * gas_constant * temperature))

    scale = math.sqrt(gas_constant * temperature / molar_mass)
    mean_square, _ = quad(lambda v: v * v * density(v), 0.0, 40.0 * scale, epsabs=0.0, epsrel=1e-12, limit=200)
    return float(math.sqrt(mean_square))


def _solve_fridge_power(p_cold, t_cold, t_hot, fraction):
    # A reversible refrigerator: energy balance Qh - W = Qc and entropy balance Qh / Th = Qc / Tc as a linear system in (Qh, W);
    # the real refrigerator needs the reversible work divided by the achieved fraction of the reversible performance.
    solution = np.linalg.solve(np.array([[1.0, -1.0], [1.0, 0.0]]), np.array([p_cold, p_cold * t_hot / t_cold]))
    return float(solution[1] / fraction)


def _solve_available_work(m, c, t_body, t_lake):
    # A reversible engine takes dQ = m c dT from the body at temperature T and rejects dQ T_lake / T to the lake:
    # the work is the integral of (1 - T_lake / T) m c dT as the body cools to the lake temperature.
    work, _ = quad(lambda t: (1.0 - t_lake / t) * m * c, t_lake, t_body, epsabs=0.0, epsrel=1e-13)
    return float(work)


# --- structures ---------------------------------------------------------------------------------------


def s51_adiabatic_compression_work() -> Structure:
    return Structure(
        "S51", "Work needed to compress a gas adiabatically", "thermodynamics", "adiabatic_compression_work_on_gas",
        (_in("n", "amount", "mol", "amount of gas", 0.5, (0.2, 2.0)),
         _in("T1", "temperature", "K", "initial temperature of the gas", 300.0, (280.0, 350.0)),
         _in("r", "ratio", "1", "compression ratio, the initial volume divided by the final volume", 8.0, (3.0, 12.0)),
         _in("gamma", "ratio", "1", "heat capacity ratio of the gas, a stated constant", 1.4, (1.3, 1.7), provenance="assumed"),
         _in("R", "molar_gas_constant", "J/(mol*K)", "molar gas constant, a stated constant", 8.314, (8.30, 8.33), provenance="assumed"),
         _co("T2", "temperature", "K", "final temperature of the gas", "T1*r**(gamma - 1)"),
         _co("W", "energy", "kJ", "work done on the gas", "n*R*(T2 - T1)/(gamma - 1)")),
        "W",
        (Assumption("A-reversible", "The compression is slow and reversible and no heat flows into or out of the gas.", "modelling", ("T1", "r")),
         Assumption("A-gamma", "The gas is ideal and its heat capacity ratio is the stated constant over the whole compression.", "modelling", ("gamma",)),
         Assumption("A-R", "The molar gas constant has the stated value.", "modelling", ("R",))),
        _spec("A cylinder fitted with a piston holds {n} mol of an ideal gas at a temperature of {T1} K. The gas is compressed slowly and "
              "adiabatically, so no heat flows into or out of it. The compression ratio, the initial volume divided by the final volume, "
              "is {r}. The heat capacity ratio of the gas is {gamma} and it stays constant. Take the molar gas constant to be "
              "R = {R} J/(mol·K).",
              "How much work is done on the gas during the compression?", "work done on the gas", "kJ",
              "A separate pump B in another laboratory does {v} {u} of work per stroke, but it is unrelated to this gas.",
              "A reference gas B has {v} {u} of work done on it.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the compression.", "W", equivalent="J"),
        ("r", 1.25), _solve_adiabatic_compression, 5,
        "the work as the integral of p dV along the adiabat p V^gamma = constant, fixed by the initial state, computed by adaptive quadrature",
        solver_rel_tol=1e-9,
        instances=({"n": 0.5, "T1": 300.0, "r": 8.0, "gamma": 1.4, "R": 8.314},
                   {"n": 0.8, "T1": 290.0, "r": 6.0, "gamma": 1.4, "R": 8.314},
                   {"n": 1.2, "T1": 320.0, "r": 5.0, "gamma": 1.67, "R": 8.314},
                   {"n": 0.3, "T1": 350.0, "r": 10.0, "gamma": 1.3, "R": 8.314}))


def s52_ice_in_warm_water() -> Structure:
    return Structure(
        "S52", "Heat given up by warm water that melts ice", "thermodynamics", "ice_melting_in_warm_water_heat_given_up",
        (_in("mi", "mass", "kg", "mass of the ice", 0.08, (0.05, 0.12)),
         _in("Lf", "specific_latent_heat", "kJ/kg", "latent heat of fusion of ice, a stated constant", 334.0, (330.0, 336.0), provenance="assumed"),
         _in("mw", "mass", "kg", "mass of the warm water", 0.5, (0.4, 0.6)),
         _in("c", "specific_heat", "J/(kg*K)", "specific heat capacity of water, a stated constant", 4186.0, (4100.0, 4250.0), provenance="assumed"),
         _in("dTw", "temperature_change", "K", "initial temperature of the warm water above the melting point of ice", 40.0, (35.0, 60.0)),
         _co("Qw", "energy", "kJ", "heat the warm water could give up in cooling to the melting point", "mw*c*dTw"),
         _co("Qm", "energy", "kJ", "heat needed to melt all of the ice", "mi*Lf"),
         _co("dTf", "temperature_change", "K", "final temperature of the mixture above the melting point", "(Qw - Qm)/((mi + mw)*c)"),
         _co("Qlost", "energy", "kJ", "heat given up by the warm water", "mw*c*(dTw - dTf)")),
        "Qlost",
        (Assumption("A-isolated", "The container is perfectly insulated: heat is exchanged only between the ice and the water.", "modelling", ("mi", "mw", "dTw")),
         Assumption("A-melts", "All of the ice melts, so the final mixture is liquid water above the melting point.", "boundary_condition", ("Lf",)),
         Assumption("A-c", "The specific heat capacity of water is the stated constant for the whole temperature range.", "modelling", ("c",))),
        _spec("Ice at its melting point is added to warm water in a perfectly insulated container. The ice has a mass of {mi} kg. The "
              "water has a mass of {mw} kg and starts {dTw} K above the melting point of ice. The latent heat of fusion of ice is "
              "{Lf} kJ/kg and the specific heat capacity of water is {c} J/(kg·K). Heat exchange with the container and the "
              "surroundings is negligible, and all of the ice melts.",
              "How much heat does the original warm water give up while the mixture comes to thermal equilibrium?",
              "heat given up by the warm water", "kJ",
              "A separate mixture B in another laboratory takes in {v} {u} of heat, but it is unrelated to this container.",
              "A reference mixture B has water that gives up {v} {u} of heat.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the melting.", "W", equivalent="J"),
        ("mi", 1.25), _solve_ice_water, 5,
        "the final temperature as the root of the energy balance (heat taken in by the ice and its meltwater minus heat given up by the water), found with a bracketing root finder",
        solver_rel_tol=1e-9,
        instances=({"mi": 0.08, "Lf": 334.0, "mw": 0.5, "c": 4186.0, "dTw": 40.0},
                   {"mi": 0.1, "Lf": 334.0, "mw": 0.4, "c": 4186.0, "dTw": 45.0},
                   {"mi": 0.12, "Lf": 334.0, "mw": 0.6, "c": 4186.0, "dTw": 50.0},
                   {"mi": 0.06, "Lf": 334.0, "mw": 0.45, "c": 4186.0, "dTw": 55.0}))


def s53_two_layer_wall_conduction() -> Structure:
    return Structure(
        "S53", "Heat conducted through a wall of brick and foam", "thermodynamics", "two_layer_wall_conduction_from_conductivities",
        (_in("A", "area", "m^2", "area of the wall", 12.0, (5.0, 30.0)),
         _in("L1", "length", "cm", "thickness of the brick layer", 20.0, (5.0, 30.0)),
         _in("k1", "thermal_conductivity", "W/(m*K)", "thermal conductivity of the brick", 0.8, (0.4, 1.2)),
         _in("L2", "length", "cm", "thickness of the foam layer", 5.0, (2.0, 10.0)),
         _in("k2", "thermal_conductivity", "W/(m*K)", "thermal conductivity of the foam", 0.04, (0.02, 0.08)),
         _in("dT", "temperature_change", "K", "temperature difference between the two outer surfaces", 20.0, (10.0, 40.0)),
         _co("R1", "thermal_resistance", "K/W", "thermal resistance of the brick layer", "L1/(k1*A)"),
         _co("R2", "thermal_resistance", "K/W", "thermal resistance of the foam layer", "L2/(k2*A)"),
         _co("P", "power", "W", "rate of heat flow through the wall", "dT/(R1 + R2)")),
        "P",
        (Assumption("A-steady", "The heat flow is steady and one-dimensional, perpendicular to the layers, and no heat is lost from the edges.", "modelling", ("A", "dT")),
         Assumption("A-contact", "The two layers are in perfect thermal contact and each has the stated uniform thermal conductivity.", "modelling", ("L1", "k1", "L2", "k2"))),
        _spec("A wall of area {A} m² is made of two layers in contact. The first layer is brick, {L1} cm thick, with a thermal "
              "conductivity of {k1} W/(m·K). The second layer is foam insulation, {L2} cm thick, with a thermal conductivity of "
              "{k2} W/(m·K). The temperature difference between the two outer surfaces of the wall is {dT} K. The heat flow is "
              "steady and perpendicular to the layers.",
              "At what rate does heat flow through the wall?", "rate of heat flow through the wall", "W",
              "A separate wall B in another building loses heat at {v} {u}, but it is unrelated to this wall.",
              "A reference wall B loses heat at {v} {u}.",
              "A separate meter B reads {v} {u}, but it plays no part in the heat flow.", "Hz", equivalent="kW"),
        ("dT", 1.25), _solve_two_layer_wall, 6,
        "the heat current and the interface temperature from continuity of heat flow at the interface, solved as a linear system",
        solver_rel_tol=1e-9,
        instances=({"A": 12.0, "L1": 20.0, "k1": 0.8, "L2": 5.0, "k2": 0.04, "dT": 20.0},
                   {"A": 8.0, "L1": 15.0, "k1": 0.9, "L2": 8.0, "k2": 0.05, "dT": 25.0},
                   {"A": 15.0, "L1": 25.0, "k1": 0.6, "L2": 6.0, "k2": 0.03, "dT": 30.0},
                   {"A": 10.0, "L1": 10.0, "k1": 1.0, "L2": 4.0, "k2": 0.04, "dT": 15.0}))


def s54_radiated_power_scaling() -> Structure:
    return Structure(
        "S54", "Thermal radiation from a second hot sphere", "thermodynamics", "stefan_boltzmann_sphere_scaling",
        (_in("P1", "power", "kW", "power radiated by the first sphere", 1.5, (0.3, 3.0)),
         _in("r1", "length", "cm", "radius of the first sphere", 5.0, (2.0, 8.0)),
         _in("T1", "temperature", "K", "surface temperature of the first sphere", 1000.0, (700.0, 1300.0)),
         _in("r2", "length", "cm", "radius of the second sphere", 10.0, (2.0, 15.0)),
         _in("T2", "temperature", "K", "surface temperature of the second sphere", 1200.0, (700.0, 1500.0)),
         _co("Fa", "dimensionless", "1", "ratio of the surface areas, second to first", "(r2/r1)**2"),
         _co("Ft", "dimensionless", "1", "ratio of the radiated power per unit area, second to first", "(T2/T1)**4"),
         _co("P2", "power", "kW", "power radiated by the second sphere", "P1*Fa*Ft")),
        "P2",
        (Assumption("A-emissivity", "Both spheres have the same constant emissivity and radiate from their whole surface.", "modelling", ("r1", "r2")),
         Assumption("A-surroundings", "The surroundings are much colder than the spheres, so the radiation they absorb is negligible.", "modelling", ("T1", "T2")),
         Assumption("A-power", "The power given for the first sphere is the net power it radiates.", "boundary_condition", ("P1",))),
        _spec("A hot metal sphere of radius {r1} cm has a surface temperature of {T1} K and radiates {P1} kW of thermal radiation into "
              "much colder surroundings. A second sphere with the same surface finish has a radius of {r2} cm and a surface temperature "
              "of {T2} K. Both spheres have the same constant emissivity, and the radiation they absorb from the surroundings is "
              "negligible.",
              "What power does the second sphere radiate?", "power radiated by the second sphere", "kW",
              "A separate furnace B in another workshop radiates {v} {u}, but it is unrelated to the spheres.",
              "A reference sphere B radiates {v} {u}.",
              "A separate meter B reads {v} {u}, but it plays no part in the radiation.", "Hz", equivalent="W"),
        ("T2", 1.25), _solve_radiated_power, 5,
        "the product of emissivity and the Stefan-Boltzmann constant fixed from the first sphere (P = e sigma A T^4), then used for the second sphere",
        solver_rel_tol=1e-9,
        instances=({"P1": 1.5, "r1": 5.0, "T1": 1000.0, "r2": 10.0, "T2": 1200.0},
                   {"P1": 0.6, "r1": 4.0, "T1": 900.0, "r2": 6.0, "T2": 1100.0},
                   {"P1": 0.85, "r1": 6.0, "T1": 800.0, "r2": 3.0, "T2": 1000.0},
                   {"P1": 0.75, "r1": 3.0, "T1": 1100.0, "r2": 8.0, "T2": 900.0}))


def s55_rms_speed_of_gas() -> Structure:
    return Structure(
        "S55", "Root-mean-square speed of gas molecules", "thermodynamics", "kinetic_theory_rms_speed_from_molar_energy",
        (_in("T", "temperature", "K", "temperature of the gas", 300.0, (200.0, 600.0)),
         _in("M", "molar_mass", "g/mol", "molar mass of the gas", 4.0, (2.0, 90.0)),
         _in("R", "molar_gas_constant", "J/(mol*K)", "molar gas constant, a stated constant", 8.314, (8.30, 8.33), provenance="assumed"),
         _co("Ek", "molar_energy", "kJ/mol", "mean translational kinetic energy of one mole of molecules", "3*R*T/2"),
         _co("vrms", "speed", "m/s", "root-mean-square speed of the molecules", "sqrt(2*Ek/M)")),
        "vrms",
        (Assumption("A-ideal", "The gas is ideal and classical, in thermal equilibrium, and only the translational motion of the molecules counts.", "modelling", ("T", "M")),
         Assumption("A-R", "The molar gas constant has the stated value.", "modelling", ("R",))),
        _spec("A sample of an ideal gas is in thermal equilibrium at a temperature of {T} K. The molar mass of the gas is {M} g/mol. "
              "Take the molar gas constant to be R = {R} J/(mol·K).",
              "What is the root-mean-square speed of the gas molecules?", "root-mean-square speed of the molecules", "m/s",
              "A separate jet B in another hangar flies at {v} {u}, but it is unrelated to the gas.",
              "A reference gas B has molecules with a root-mean-square speed of {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the molecular motion.", "W", equivalent="km/s"),
        ("T", 1.25), _solve_rms_speed, 3,
        "the second moment of the Maxwell-Boltzmann speed distribution integrated numerically, then its square root",
        solver_rel_tol=1e-8,
        instances=({"T": 300.0, "M": 4.0, "R": 8.314},
                   {"T": 400.0, "M": 32.0, "R": 8.314},
                   {"T": 300.0, "M": 28.0, "R": 8.314},
                   {"T": 350.0, "M": 44.0, "R": 8.314}))


def s56_refrigerator_power() -> Structure:
    return Structure(
        "S56", "Electrical power needed by a refrigerator", "thermodynamics", "refrigerator_fraction_of_carnot_power",
        (_in("Pc", "power", "W", "rate at which heat is removed from the interior", 200.0, (100.0, 600.0)),
         _in("Tc", "temperature", "K", "temperature of the interior", 275.0, (255.0, 280.0)),
         _in("Th", "temperature", "K", "temperature of the kitchen", 300.0, (290.0, 310.0)),
         _in("f", "ratio", "1", "fraction of the reversible coefficient of performance that the refrigerator achieves", 0.3, (0.2, 0.7)),
         _co("COPr", "coefficient", "1", "coefficient of performance of a reversible refrigerator between the two temperatures", "Tc/(Th - Tc)"),
         _co("COP", "coefficient", "1", "coefficient of performance of the real refrigerator", "f*COPr"),
         _co("Pw", "power", "W", "electrical power needed", "Pc/COP")),
        "Pw",
        (Assumption("A-steady", "The refrigerator runs in steady operation and all of its electrical power input is the work done on the working fluid.", "modelling", ("Pc", "f")),
         Assumption("A-reservoirs", "The interior and the kitchen are heat reservoirs at constant temperature.", "boundary_condition", ("Tc", "Th"))),
        _spec("A refrigerator keeps its interior at a temperature of {Tc} K in a kitchen at {Th} K. Heat leaks into the interior, so the "
              "refrigerator must remove heat from it at a steady rate of {Pc} W. The refrigerator achieves a fraction {f} of the "
              "coefficient of performance of a reversible (Carnot) refrigerator working between the same two temperatures.",
              "What electrical power does the refrigerator need?", "electrical power needed by the refrigerator", "W",
              "A separate freezer B in another kitchen draws {v} {u}, but it is unrelated to this refrigerator.",
              "A reference refrigerator B draws {v} {u}.",
              "A separate meter B reads {v} {u}, but it plays no part in the cooling.", "Hz", equivalent="kW"),
        ("f", 1.25), _solve_fridge_power, 4,
        "the reversible work from the energy balance and the entropy balance solved as a linear system, then divided by the achieved fraction",
        solver_rel_tol=1e-9,
        instances=({"Pc": 200.0, "Tc": 275.0, "Th": 300.0, "f": 0.3},
                   {"Pc": 150.0, "Tc": 270.0, "Th": 295.0, "f": 0.35},
                   {"Pc": 300.0, "Tc": 260.0, "Th": 305.0, "f": 0.25},
                   {"Pc": 250.0, "Tc": 278.0, "Th": 298.0, "f": 0.3}))


def s57_available_work_from_hot_water() -> Structure:
    return Structure(
        "S57", "Maximum work from a tank of hot water and a lake", "thermodynamics", "reversible_engine_finite_body_available_work",
        (_in("m", "mass", "kg", "mass of the water in the tank", 2.0, (1.0, 5.0)),
         _in("c", "specific_heat", "J/(kg*K)", "specific heat capacity of water, a stated constant", 4186.0, (4100.0, 4250.0), provenance="assumed"),
         _in("Tb", "temperature", "K", "initial temperature of the water in the tank", 360.0, (320.0, 370.0)),
         _in("Tl", "temperature", "K", "temperature of the lake", 290.0, (275.0, 300.0)),
         _co("Q", "energy", "kJ", "heat given up by the water in cooling to the lake temperature", "m*c*(Tb - Tl)"),
         _co("dS", "entropy", "J/K", "decrease of the entropy of the water", "m*c*log(Tb/Tl)"),
         _co("W", "energy", "kJ", "maximum work the engine can deliver", "Q - Tl*dS")),
        "W",
        (Assumption("A-reversible", "The engine is reversible, runs in whole cycles and rejects its waste heat to the lake.", "modelling", ("Tb", "Tl")),
         Assumption("A-reservoir", "The lake is so large that its temperature stays constant, and the tank loses no heat except through the engine.", "boundary_condition", ("Tl",)),
         Assumption("A-c", "The specific heat capacity of water is the stated constant, and the water stays liquid.", "modelling", ("c", "m"))),
        _spec("A well-insulated tank holds {m} kg of water at a temperature of {Tb} K. A lake, large enough that its temperature stays at "
              "{Tl} K, serves as a cold reservoir. A reversible heat engine runs between the water and the lake, drawing heat from "
              "the water until the water has cooled to the temperature of the lake. The specific heat capacity of water is "
              "{c} J/(kg·K) and is constant.",
              "What is the maximum total work that the engine can deliver?", "maximum work delivered by the engine", "kJ",
              "A separate generator B in another plant delivers {v} {u} of work, but it is unrelated to this engine.",
              "A reference engine B delivers {v} {u} of work.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the cooling.", "W", equivalent="J"),
        ("m", 1.25), _solve_available_work, 4,
        "the work as the integral of (1 - T_lake / T) m c dT over the cooling of the water, computed by adaptive quadrature",
        solver_rel_tol=1e-9,
        instances=({"m": 2.0, "c": 4186.0, "Tb": 360.0, "Tl": 290.0},
                   {"m": 1.5, "c": 4186.0, "Tb": 350.0, "Tl": 285.0},
                   {"m": 3.0, "c": 4186.0, "Tb": 370.0, "Tl": 295.0},
                   {"m": 2.5, "c": 4180.0, "Tb": 340.0, "Tl": 280.0}))


ALL = (s51_adiabatic_compression_work, s52_ice_in_warm_water, s53_two_layer_wall_conduction, s54_radiated_power_scaling,
       s55_rms_speed_of_gas, s56_refrigerator_power, s57_available_work_from_hot_water)


def all_structures() -> list[Structure]:
    return [factory() for factory in ALL]


# --- gold solution plans ---------------------------------------------------------------------------------

PLANS: dict[str, Plan] = {
    # --- new structures -------------------------------------------------------------------------------
    "S51": Plan(
        approach="We are asked for the work done on a gas that is compressed slowly with no heat exchange. First find the final temperature "
                 "from the adiabatic law for an ideal gas, then use the first law of thermodynamics with zero heat: the work done on the "
                 "gas equals the increase of its internal energy.",
        steps=(
            Step("T2",
                 "Reversible adiabatic process of an ideal gas: T V^(gamma - 1) is constant, equivalently p V^gamma is constant",
                 "The compression is slow (quasi-static) and no heat flows, so the gas moves along an adiabat. With the compression ratio "
                 "r = V1/V2 the law gives T2 = T1 r^(gamma - 1), which tells us how hot the gas becomes."),
            Step("W",
                 "First law of thermodynamics, delta U = Q + W_on with Q = 0, and delta U = n Cv delta T for an ideal gas, with "
                 "Cv = R/(gamma - 1) from gamma = Cp/Cv and Mayer's relation Cp - Cv = R",
                 "No heat is exchanged, so all the work done on the gas goes into internal energy. Writing Cv through gamma and R lets us "
                 "compute the work from the temperature rise already found: W = n R (T2 - T1)/(gamma - 1)."),
        ),
        check="The work is positive because compressing a gas adiabatically heats it. It tends to zero as r tends to 1, and it exceeds "
              "the work of an isothermal compression to the same volume, n R T1 ln r, because the hotter gas pushes back harder."),
    "S52": Plan(
        approach="The heat given up by the warm water is the heat taken in by the ice, which first melts and then warms as liquid. We "
                 "check that the water holds enough energy to melt all the ice, find the final temperature from the energy balance of the "
                 "isolated mixture, and then compute the heat that the water released.",
        steps=(
            Step("Qm",
                 "Latent heat of fusion, Q = m L_f: melting takes in this heat at constant temperature",
                 "The ice is already at its melting point, so the first thing that happens to it is melting. This is the energy that "
                 "must be supplied before the meltwater can get warmer."),
            Step("Qw",
                 "Specific heat relation Q = m c delta T for a temperature change without a phase change",
                 "This is the heat the warm water would give up if it cooled all the way down to the melting point of ice. Comparing it "
                 "with the heat Qm needed to melt the ice tells us whether the ice melts completely."),
            Step("dTf",
                 "Calorimetry, conservation of energy in an isolated system: heat lost by the water equals heat gained by the ice and its "
                 "meltwater, mw c (dTw - dTf) = Qm + mi c dTf",
                 "Nothing exchanges heat with the surroundings, and Qw is larger than Qm so all the ice melts and the final temperature "
                 "is above the melting point. Solving the balance for dTf gives (Qw - Qm)/((mi + mw) c)."),
            Step("Qlost",
                 "Specific heat relation Q = m c delta T applied to the original warm water as it cools from dTw to dTf above the melting point",
                 "The question asks for the heat the warm water gives up, which is its mass times its specific heat times its own "
                 "temperature drop, now that the final temperature is known."),
        ),
        check="The final temperature lies between the melting point and the starting temperature of the water. The heat the water "
              "gave up must equal the heat the ice took in, Qm + mi c dTf, which is an independent way to confirm the number."),
    "S53": Plan(
        approach="In steady conduction the same heat current passes through both layers, so the layers behave like resistors in series. "
                 "Find the thermal resistance of each layer from its thickness, conductivity and area, add them, and divide the "
                 "temperature difference by the total resistance.",
        steps=(
            Step("R1",
                 "Fourier's law of heat conduction through a slab, P = k A delta T / L, written as delta T = P R with thermal resistance R = L/(k A)",
                 "The brick layer conducts heat according to its thickness and conductivity; expressing this as a thermal resistance lets "
                 "us combine the layers like electrical resistors. The thickness must be converted to metres."),
            Step("R2",
                 "Fourier's law of heat conduction, with thermal resistance R = L/(k A)",
                 "The foam layer has the same area but a different thickness and conductivity, so it has its own resistance; this layer "
                 "is the part of the wall that most strongly limits the heat current when its conductivity is small."),
            Step("P",
                 "Thermal resistances in series add (steady heat current is continuous), and the heat current is P = delta T / R_total, the thermal analogue of Ohm's law",
                 "In steady state no heat accumulates at the interface, so the same P flows through both layers and the temperature "
                 "drops across them add up to the given difference between the outer surfaces."),
        ),
        check="The heat current must be smaller than the current through either layer alone with the full temperature difference, "
              "dT/R1 or dT/R2, and the layer with the larger resistance takes the larger share of the temperature drop. Doubling the "
              "temperature difference doubles the heat current."),
    "S54": Plan(
        approach="The radiated power of a hot body follows the Stefan-Boltzmann law, P = e sigma A T^4. Because both spheres have the same "
                 "emissivity, the unknown product e sigma cancels in the ratio of the two powers, so the second power is the first one "
                 "times the area ratio times the fourth power of the temperature ratio.",
        steps=(
            Step("Fa",
                 "Surface area of a sphere, A = 4 pi r^2, so the area ratio is (r2/r1)^2",
                 "The spheres have the same shape, and a body radiates from its whole surface, so the power scales with the surface "
                 "area; the area ratio is the square of the ratio of radii."),
            Step("Ft",
                 "Stefan-Boltzmann law: the power radiated per unit area is e sigma T^4, so the ratio is (T2/T1)^4",
                 "The surface finish is the same, so e and sigma cancel in the ratio of emitted power per unit area, and only the "
                 "absolute temperatures (in kelvin) matter."),
            Step("P2",
                 "Stefan-Boltzmann law P = e sigma A T^4 applied to both spheres and divided: P2 = P1 (A2/A1)(T2/T1)^4",
                 "Combining the area factor and the temperature factor with the known power of the first sphere gives the power of "
                 "the second sphere without needing the value of the emissivity or of sigma."),
        ),
        check="If the two spheres were identical (same radius, same temperature) the result must equal the first power. Doubling the "
              "radius multiplies the power by 4, doubling the absolute temperature multiplies it by 16, and the ratio is dimensionless "
              "so the answer carries the same unit as the given power."),
    "S55": Plan(
        approach="In the kinetic theory of an ideal gas the mean translational kinetic energy depends only on temperature. Find the "
                 "mean kinetic energy per mole, then convert it to a speed using the molar mass: the rms speed is the speed whose "
                 "kinetic energy equals this mean.",
        steps=(
            Step("Ek",
                 "Equipartition theorem for translation: each molecule has mean kinetic energy (3/2) k_B T, so one mole has (3/2) R T",
                 "The gas is ideal and classical, so the three translational degrees of freedom each carry (1/2) k_B T on average. "
                 "Using the molar gas constant R gives the energy of one mole of molecules from the temperature alone."),
            Step("vrms",
                 "Definition of the root-mean-square speed through the mean kinetic energy, (1/2) M v_rms^2 = Ek per mole",
                 "The mean kinetic energy per mole equals half the molar mass times the mean square speed, and the rms speed is the "
                 "square root of that mean square, so v_rms = sqrt(2 Ek / M); the molar mass must be in kilograms per mole."),
        ),
        check="The result equals sqrt(3 R T / M), the standard kinetic-theory formula. Lighter molecules are faster at the same "
              "temperature, the speed grows as the square root of the absolute temperature, and typical speeds are of the order of "
              "hundreds of metres per second, comparable to the speed of sound."),
    "S56": Plan(
        approach="A real refrigerator needs more work than a reversible one. Find the coefficient of performance of a reversible "
                 "refrigerator between the two temperatures, scale it by the given fraction to get the real coefficient of performance, "
                 "and then divide the rate of heat removal by it to get the electrical power.",
        steps=(
            Step("COPr",
                 "Coefficient of performance of a reversible (Carnot) refrigerator: COP = Qc/W with Qc/Qh = Tc/Th (zero entropy production) and Qh = Qc + W, giving Tc/(Th - Tc)",
                 "The first law relates the heat rejected to the heat removed and the work, and the second law for a reversible cycle "
                 "fixes the ratio of the heats by the absolute temperatures; together they give the best possible COP for these temperatures."),
            Step("COP",
                 "Definition of the fraction of the reversible performance achieved: COP = f times COP of the reversible refrigerator",
                 "The real machine is irreversible, so it removes less heat per unit of work than the ideal one; the problem states how "
                 "much less, as the fraction f."),
            Step("Pw",
                 "Definition of the coefficient of performance, COP = heat removed / work input, applied to rates: Pw = Pc / COP",
                 "The coefficient of performance links the rate at which heat is removed from the interior to the electrical power "
                 "that has to be supplied, so the power follows by division."),
        ),
        check="The electrical power must be larger than the power of a reversible refrigerator (the real COP is smaller than the "
              "reversible one). As the kitchen temperature approaches the interior temperature the reversible COP grows without limit "
              "and the required power tends to zero, and the heat rejected to the kitchen, Pc + Pw, exceeds the heat removed."),
    "S57": Plan(
        approach="The engine works between a finite body that cools down and a large lake. Its maximum work is the heat given up by "
                 "the water minus the heat that must be rejected to the lake, and the second law fixes the rejected heat for a "
                 "reversible engine through the entropy that the water loses. We find the heat, the entropy change, then the work.",
        steps=(
            Step("Q",
                 "Specific heat relation Q = m c delta T for the water cooling from Tb to the lake temperature Tl",
                 "This is the total heat that the water gives up to the engine as it cools to the lake temperature, which is the "
                 "energy input of the engine over the whole process."),
            Step("dS",
                 "Entropy change for heat exchanged reversibly, dS = dQ/T with dQ = m c dT, so the entropy decrease is m c ln(Tb/Tl)",
                 "The temperature of the water changes continuously, so the entropy lost by the water is found by integrating "
                 "dQ/T. A reversible engine produces no entropy, so this loss is exactly the entropy gained by the lake."),
            Step("W",
                 "First law for the engine (work = heat taken in minus heat rejected) and second law for a reversible engine "
                 "(total entropy change zero): the rejected heat is Tl times the entropy decrease of the water, so W = Q - Tl dS",
                 "The lake receives the rejected heat at its constant temperature Tl, so the rejected heat is Tl times the entropy "
                 "it gains, which equals dS; subtracting it from Q gives the largest possible work."),
        ),
        check="The work is positive and smaller than Q, and it is smaller than Q times the Carnot efficiency 1 - Tl/Tb of the initial "
              "temperature, because the water gets colder as heat is drawn from it. As Tb approaches Tl the work tends to zero faster "
              "than Q does."),
    # --- existing structures of this domain (plans only) ----------------------------------------------
    "S09": Plan(
        approach="The block and the water form an isolated system, so the heat lost by the hot block equals the heat gained by the "
                 "water. Find the common final temperature from this energy balance, then subtract the water's initial temperature "
                 "to get the rise that the question asks for.",
        steps=(
            Step("Tf",
                 "Calorimetry, conservation of energy for an isolated system with Q = m c delta T for each body: m1 c1 (T1 - Tf) = m2 c2 (Tf - T2)",
                 "The container is insulated and no phase change occurs, so the heat leaving the block all enters the water. Solving "
                 "the balance for Tf gives the average of the two initial temperatures weighted by the heat capacities m c."),
            Step("dT",
                 "Definition of a temperature change, delta T = T_final - T_initial",
                 "The question asks by how much the water warms up, which is its final temperature minus the temperature it "
                 "started at."),
        ),
        check="The final temperature must lie between the two initial temperatures, and the rise of the water must be positive and "
              "smaller than the initial temperature difference. If the water's heat capacity is much larger than the block's, the "
              "rise is small, and in the opposite case the final temperature approaches that of the block."),
    "S17": Plan(
        approach="In steady heat flow the same heat current passes through both layers of the wall. The layers act as thermal "
                 "resistances in series, so add the resistances and divide the temperature difference by the total.",
        steps=(
            Step("q",
                 "Thermal resistances in series add, and the steady heat current is q = delta T / R_total (thermal analogue of Ohm's law)",
                 "In steady state no heat builds up at the interface between the layers, so one heat current flows through both and "
                 "the temperature drops across the layers add up to the temperature difference between the outer surfaces."),
        ),
        check="The heat current must be smaller than dT/Ra and dT/Rb, the currents each layer alone would pass, and it must double "
              "when the temperature difference doubles. Its unit, kelvin divided by kelvin per watt, is the watt."),
    "S18": Plan(
        approach="The work done by the gas is the integral of pressure over volume. For an ideal gas at constant temperature the "
                 "pressure is inversely proportional to the volume, so the integral can be done in closed form.",
        steps=(
            Step("W",
                 "Work done by a gas, W = integral of p dV, together with Boyle's law for an isothermal ideal gas, p V = constant = p1 V1",
                 "The expansion is slow and isothermal, so the pressure at volume V is p1 V1 / V. Integrating this from the initial "
                 "volume V1 to rho V1 gives W = p1 V1 ln(rho)."),
        ),
        check="The work is positive for an expansion (rho larger than one) and tends to zero as rho tends to one. It is less than "
              "p1 V1 (rho - 1), the work at the initial pressure, because the pressure falls during the expansion, and for an "
              "isothermal ideal gas it equals the heat absorbed since the internal energy does not change."),
    "S23": Plan(
        approach="The amount of gas is fixed, so the ideal gas law says that p V / T has the same value in the initial and the final "
                 "state. Equate the two values and solve for the final pressure, using absolute temperatures.",
        steps=(
            Step("p2",
                 "Combined gas law from the ideal gas law p V = n R T with n fixed: p1 V1 / T1 = p2 V2 / T2",
                 "The gas is ideal and sealed, so n R is the same in both states and cancels. Solving for the final pressure "
                 "gives p2 = p1 V1 T2 / (V2 T1); the temperatures must be in kelvin."),
        ),
        check="If the volume and temperature are unchanged the pressure stays the same. At constant temperature, halving the volume "
              "doubles the pressure (Boyle's law), and at constant volume the pressure grows in proportion to the absolute "
              "temperature (Gay-Lussac's law)."),
    "S24": Plan(
        approach="For a reversible engine the second law fixes the ratio of the rejected heat to the absorbed heat through the "
                 "reservoir temperatures, and the first law gives the net work as the difference of the two heats.",
        steps=(
            Step("W",
                 "First law over one cycle, W = Qh - Qc, and the Clausius equality for a reversible cycle, Qc/Tc = Qh/Th (zero total entropy change)",
                 "The engine returns to its initial state each cycle, so the work equals the heat taken in minus the heat rejected, "
                 "and reversibility makes the rejected heat Qh Tc/Th. This gives W = Qh (1 - Tc/Th)."),
        ),
        check="The work is always smaller than Qh and tends to zero as the cold temperature approaches the hot one. It would equal "
              "Qh only for a cold reservoir at absolute zero, so the efficiency 1 - Tc/Th must lie between zero and one."),
    "S30": Plan(
        approach="The energy needed to warm the water is given by its specific heat capacity. The heater supplies energy at a "
                 "constant rate, so the time is the needed energy divided by the power.",
        steps=(
            Step("t",
                 "Specific heat relation Q = m c delta T for the energy needed, and the definition of power, P = Q/t, so t = m c delta T / P",
                 "All the heater power goes into the water and none is lost, so the energy delivered in time t is P t. Setting this "
                 "equal to the energy needed to raise the temperature of the water gives the time."),
        ),
        check="The units work out: kilogram times joule per kilogram kelvin times kelvin gives joules, and joules divided by watts "
              "give seconds. Doubling the power halves the time, doubling the mass or the temperature rise doubles it, and a heater "
              "of kilowatt size needs a few minutes to warm a few litres of water by tens of kelvin."),
}

LEVELS: dict[str, str] = {
    "S51": "intro_university", "S52": "high_school", "S53": "high_school", "S54": "intro_university",
    "S55": "intro_university", "S56": "intro_university", "S57": "upper_university",
    "S09": "high_school", "S17": "intro_university", "S18": "intro_university", "S23": "high_school",
    "S24": "intro_university", "S30": "high_school",
}

TOPICS: dict[str, str] = {
    "S51": "adiabatic compression of an ideal gas and the first law",
    "S52": "latent heat of fusion and calorimetry with ice and water",
    "S53": "conduction through a two-layer wall",
    "S54": "Stefan-Boltzmann radiation scaling with radius and temperature",
    "S55": "kinetic theory: rms speed of gas molecules",
    "S56": "refrigerator with a fraction of the Carnot coefficient of performance",
    "S57": "maximum work from cooling a finite body against a reservoir (entropy)",
    "S09": "calorimetry: temperature rise of water from a hot block",
    "S17": "series thermal resistances in a two-layer wall",
    "S18": "work of an isothermal ideal gas expansion",
    "S23": "combined gas law for a sealed gas",
    "S24": "work output of a reversible heat engine",
    "S30": "heating time of water with a heater",
}
