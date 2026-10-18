"""The second batch of DECOY-v2 structures, S11 to S20 (Stage 14.15; v2 B3 deliverable p.9).

Same pattern as `library.py`: a typed graph, an independently coded numeric solver for each structure (an ODE with an event, a
root finder, a linear system, a quadrature), two numeric instantiations and a relevant edit that moves the answer. These laws are
chosen to be shorter chains than the first batch, so that a 7 to 8 B model has a chance of solving them with reasoning (Stage 14.8
design gap 1), while still being new equation programs: `scripts/v2/s146_generate_structures.py` rejects any program whose
renaming-invariant hash equals a v1 template.

They are agent-authored candidates: solver-certified and UNREVIEWED. Independent expert review of the English text and the physics
is required before any use (v2 B4).
"""

from __future__ import annotations

import math

import numpy as np
from scipy.integrate import quad, solve_ivp
from scipy.optimize import brentq

from physmon.benchmark.v2.graph import Assumption, Structure
from physmon.benchmark.v2.library import A_G, _co, _g, _in, _spec

# --- solvers (independent routes; SI inputs in node order) -----------------------------------------


def _solve_braking(v0, mu, g):
    # Constant kinetic-friction deceleration integrated until the speed reaches zero; the distance at that event.
    def stopped(t, y):
        return y[1]

    stopped.terminal = True
    solution = solve_ivp(lambda t, y: [y[1], -mu * g], (0.0, 200.0), [0.0, v0], events=stopped, rtol=1e-11, atol=1e-13)
    return float(solution.y_events[0][0][0])


def _solve_curve(r, mu, g):
    # The speed at which the centripetal requirement v^2/r equals the friction limit mu g, found with a root finder.
    return float(brentq(lambda v: v * v / r - mu * g, 0.0, 500.0, xtol=1e-12, rtol=1e-14))


def _solve_pendulum(length, g):
    # Small-amplitude swing integrated from rest; four times the time of the first zero crossing is the period.
    omega2 = g / length

    def crossing(t, y):
        return y[0]

    crossing.terminal = True
    solution = solve_ivp(lambda t, y: [y[1], -omega2 * y[0]], (0.0, 100.0), [0.05, 0.0], events=crossing, rtol=1e-12,
                         atol=1e-14)
    return float(4.0 * solution.t_events[0][0])


def _solve_lift_power(m, h, t, g):
    # Work done by the weight-supporting force at constant speed, integrated over the time, divided by the time.
    speed = h / t
    work, _ = quad(lambda s: m * g * speed, 0.0, t)
    return float(work / t)


def _solve_parallel_power(volt, r1, r2):
    # Branch currents first, then the power drawn from the source.
    i1, i2 = volt / r1, volt / r2
    return float(volt * (i1 + i2))


def _solve_rl(volt, r, ind, t):
    solution = solve_ivp(lambda s, y: [(volt - r * y[0]) / ind], (0.0, t), [0.0], rtol=1e-11, atol=1e-13)
    return float(solution.y[0][-1])


def _solve_wall(dt, ra, rb):
    # The interface temperature from heat-flow continuity as a linear system, then the flow through the first layer.
    # unknowns (T_interface, q) with the cold side at 0: dt - T = q ra ; T - 0 = q rb
    matrix = np.array([[1.0, ra], [1.0, -rb]])
    rhs = np.array([dt, 0.0])
    return float(np.linalg.solve(matrix, rhs)[1])


def _solve_isothermal_work(p1, v1, ratio):
    # Work as the integral of p dV with p = p1 v1 / V along an isotherm.
    work, _ = quad(lambda v: p1 * v1 / v, v1, ratio * v1, epsabs=1e-12, epsrel=1e-12)
    return float(work)


def _solve_range(v, theta, g):
    # Integrate the flight from ground level until it returns to the ground; the horizontal distance at that event.
    def landed(t, y):
        return y[1]

    landed.terminal = True
    landed.direction = -1
    solution = solve_ivp(lambda t, y: [y[2], y[3], 0.0, -g], (0.0, 100.0), [0.0, 0.0, v * math.cos(theta), v * math.sin(theta)],
                         events=landed, rtol=1e-11, atol=1e-13)
    return float(solution.y_events[0][0][0])


def _solve_lens(f, d_obj):
    # The image distance as the root of the thin-lens equation 1/f = 1/do + 1/di.
    return float(brentq(lambda di: 1.0 / d_obj + 1.0 / di - 1.0 / f, f * (1.0 + 1e-9), 1000.0 * f, xtol=1e-14, rtol=1e-13))


# --- structures ---------------------------------------------------------------------------------------


def s11_braking_distance() -> Structure:
    return Structure(
        "S11", "Braking distance of a car with locked wheels", "mechanics", "braking_distance_friction",
        (_in("v0", "speed", "m/s", "speed when braking starts", 20.0, (8.0, 30.0)),
         _in("mu", "coefficient", "1", "coefficient of kinetic friction between tyres and road", 0.5, (0.3, 0.9)),
         _g(),
         _co("d", "length", "m", "distance travelled before stopping", "v0**2/(2*mu*g)")),
        "d",
        (A_G, Assumption("A-level", "The road is level and the friction force is constant while the car slides.", "modelling", ("mu",)),
         Assumption("A-start", "The car starts braking at the stated speed and decelerates until it stops.", "boundary_condition", ("v0",))),
        _spec("A car travels at {v0} m/s on a level road and brakes with all its wheels locked. The coefficient of kinetic "
              "friction between the tyres and the road is {mu}. Take g = {g} m/s².",
              "How far does the car travel before it stops?", "braking distance of the car", "m",
              "A separate truck B on another road needs {v} {u} to stop, but it is unrelated to the car.",
              "A reference car B has a braking distance of {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the braking.", "W", equivalent="cm"),
        ("v0", 1.25), _solve_braking, 3,
        "constant kinetic-friction deceleration integrated with an adaptive ODE solver until the speed reaches zero",
        solver_rel_tol=1e-6,
        instances=({"v0": 20.0, "mu": 0.5, "g": 9.8}, {"v0": 15.0, "mu": 0.7, "g": 9.8}))


def s12_curve_speed() -> Structure:
    return Structure(
        "S12", "Maximum speed on a flat curve", "mechanics", "flat_curve_friction_speed",
        (_in("r", "length", "m", "radius of the curve", 50.0, (20.0, 100.0)),
         _in("mu", "coefficient", "1", "coefficient of static friction between tyres and road", 0.6, (0.4, 0.9)),
         _g(),
         _co("v", "speed", "m/s", "maximum speed without sliding", "sqrt(mu*g*r)")),
        "v",
        (A_G, Assumption("A-friction", "Static friction alone supplies the centripetal force and its limit is reached.", "modelling", ("mu", "r"))),
        _spec("A car drives around a flat circular curve of radius {r} m. The coefficient of static friction between the "
              "tyres and the road is {mu}. Take g = {g} m/s².",
              "What is the maximum speed at which the car can take the curve without sliding?", "maximum speed on the curve",
              "m/s", "A separate bus B on another bend travels at {v} {u}, but it is unrelated to the car.",
              "A reference car B takes a bend at {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the curve.", "W", equivalent="km/h"),
        ("r", 1.5), _solve_curve, 3,
        "the speed at which v squared over r equals mu g, found with a bracketing root finder",
        solver_rel_tol=1e-9,
        instances=({"r": 50.0, "mu": 0.6, "g": 9.8}, {"r": 80.0, "mu": 0.5, "g": 9.8}))


def s13_pendulum_period() -> Structure:
    return Structure(
        "S13", "Period of a small-amplitude pendulum", "mechanics", "small_amplitude_pendulum_period",
        (_in("L", "length", "m", "length of the string", 0.8, (0.2, 2.0)), _g(),
         _co("T", "time", "s", "period of one full oscillation", "2*pi*sqrt(L/g)")),
        "T",
        (A_G, Assumption("A-small", "The amplitude is small, the string is light and inextensible and air resistance is neglected.", "modelling", ("L",))),
        _spec("A small bob hangs from a light string of length {L} m and swings with a small amplitude. Take g = {g} m/s².",
              "What is the period of one full oscillation?", "period of the pendulum", "s",
              "A separate clock B on another wall has a period of {v} {u}, but it is unrelated to the bob.",
              "A reference pendulum B has a period of {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the swing.", "W", equivalent="ms"),
        ("L", 1.5), _solve_pendulum, 2,
        "the linear small-amplitude equation integrated from rest; four times the first zero crossing time",
        solver_rel_tol=1e-6,
        instances=({"L": 0.8, "g": 9.8}, {"L": 1.2, "g": 9.8}))


def s14_lift_power() -> Structure:
    return Structure(
        "S14", "Average power of a motor lifting a load", "mechanics", "constant_speed_lift_power",
        (_in("m", "mass", "kg", "mass of the load", 80.0, (50.0, 200.0)),
         _in("h", "length", "m", "height of the lift", 6.0, (2.0, 10.0)),
         _in("t", "time", "s", "time taken for the lift", 10.0, (4.0, 20.0)),
         _g(),
         _co("P", "power", "W", "average mechanical power delivered to the load", "m*g*h/t")),
        "P",
        (A_G, Assumption("A-const", "The load rises at constant speed and friction in the lifting gear is neglected.", "modelling", ("m", "h", "t"))),
        _spec("A motor lifts a load of {m} kg through a height of {h} m at constant speed in {t} s. Take g = {g} m/s².",
              "What average mechanical power does the motor deliver to the load?", "average power delivered to the load", "W",
              "A separate pump B on another floor delivers {v} {u}, but it is unrelated to the load.",
              "A reference motor B delivers {v} {u}.",
              "A separate meter B reads {v} {u}, but it plays no part in the lift.", "Hz", equivalent="kW"),
        ("m", 1.25), _solve_lift_power, 4,
        "the work of the supporting force at constant speed integrated over the lifting time, divided by the time",
        solver_rel_tol=1e-9,
        instances=({"m": 80.0, "h": 6.0, "t": 10.0, "g": 9.8}, {"m": 120.0, "h": 4.0, "t": 8.0, "g": 9.8}))


def s15_parallel_power() -> Structure:
    return Structure(
        "S15", "Power dissipated by two parallel resistors", "circuits", "parallel_resistor_power",
        (_in("V", "voltage", "V", "battery emf", 12.0, (6.0, 24.0)),
         _in("R1", "resistance", "Ω", "first resistor", 6.0, (4.0, 20.0)),
         _in("R2", "resistance", "Ω", "second resistor", 12.0, (8.0, 40.0)),
         _co("P", "power", "W", "total power dissipated", "V**2*(1/R1 + 1/R2)")),
        "P",
        (Assumption("A-battery", "The battery has negligible internal resistance and the wires have negligible resistance.", "modelling", ("V",)),
         Assumption("A-ohmic", "Both resistors are ohmic.", "modelling", ("R1", "R2"))),
        _spec("A battery of emf {V} V and negligible internal resistance is connected across two resistors in parallel, of "
              "{R1} Ω and {R2} Ω.",
              "What total power do the two resistors dissipate?", "total power dissipated by the resistors", "W",
              "A separate heater B on another board dissipates {v} {u}, but it shares no connection with this circuit.",
              "A reference circuit B dissipates {v} {u}.",
              "A separate oscillator B runs at {v} {u}, but it is not part of this circuit.", "Hz", equivalent="mW"),
        ("V", 1.25), _solve_parallel_power, 3,
        "the branch currents computed first, then the power drawn from the source",
        solver_rel_tol=1e-9,
        instances=({"V": 12.0, "R1": 6.0, "R2": 12.0}, {"V": 9.0, "R1": 5.0, "R2": 15.0}))


def s16_rl_current() -> Structure:
    return Structure(
        "S16", "Current in an RL circuit after closing the switch", "circuits", "rl_current_rise",
        (_in("V", "voltage", "V", "battery emf", 12.0, (6.0, 24.0)),
         _in("R", "resistance", "Ω", "series resistance", 20.0, (10.0, 40.0)),
         _in("Lc", "inductance", "mH", "inductance of the coil", 200.0, (50.0, 400.0)),
         _in("t", "time", "ms", "time after the circuit is closed", 15.0, (4.0, 40.0)),
         _co("tau", "time", "s", "time constant", "Lc/R"),
         _co("x", "dimensionless", "1", "elapsed time in units of the time constant", "t/tau"),
         _co("I", "current", "A", "current in the circuit", "V/R*(1 - exp(-x))")),
        "I",
        (Assumption("A-zero", "The current is zero when the circuit is closed.", "boundary_condition", ("Lc",)),
         Assumption("A-ideal", "The battery and wires are ideal and the coil has negligible resistance.", "modelling", ("V", "R"))),
        _spec("A coil of inductance {Lc} mH and negligible resistance is connected in series with a {R} Ω resistor to a battery "
              "of emf {V} V. The circuit is closed at the start of the experiment.",
              "What is the current in the circuit {t} ms after it is closed?", "current in the circuit", "A",
              "A separate circuit B on another board carries {v} {u}, but it shares no connection with this circuit.",
              "A reference circuit B carries {v} {u}.",
              "A separate oscillator B runs at {v} {u}, but it is not part of this circuit.", "Hz", equivalent="mA"),
        ("t", 1.5), _solve_rl, 4,
        "the equation L dI/dt = V - R I integrated with an adaptive ODE solver",
        solver_rel_tol=1e-6,
        instances=({"V": 12.0, "R": 20.0, "Lc": 200.0, "t": 15.0}, {"V": 9.0, "R": 15.0, "Lc": 150.0, "t": 20.0}))


def s17_wall_heat_flow() -> Structure:
    return Structure(
        "S17", "Heat flow through a two-layer wall", "thermodynamics", "two_layer_wall_heat_flow",
        (_in("dT", "temperature_change", "K", "temperature difference between the outer surfaces", 20.0, (10.0, 40.0)),
         _in("Ra", "thermal_resistance", "K/W", "thermal resistance of the first layer", 0.1, (0.05, 0.5)),
         _in("Rb", "thermal_resistance", "K/W", "thermal resistance of the second layer", 0.15, (0.05, 0.5)),
         _co("q", "power", "W", "rate of heat flow through the wall", "dT/(Ra + Rb)")),
        "q",
        (Assumption("A-steady", "The heat flow is steady and one-dimensional through both layers.", "modelling", ("dT",)),
         Assumption("A-series", "The layers are in good thermal contact, so their resistances add.", "modelling", ("Ra", "Rb"))),
        _spec("A wall consists of two layers in series. The first layer has a thermal resistance of {Ra} K/W and the second "
              "layer has a thermal resistance of {Rb} K/W. The temperature difference between the two outer surfaces is "
              "{dT} K, and the heat flow is steady.",
              "What is the rate of heat flow through the wall?", "rate of heat flow through the wall", "W",
              "A separate wall B in another room loses heat at {v} {u}, but it is unrelated to this wall.",
              "A reference wall B loses heat at {v} {u}.",
              "A separate meter B reads {v} {u}, but it plays no part in the heat flow.", "Hz", equivalent="kW"),
        ("dT", 1.25), _solve_wall, 3,
        "heat-flow continuity at the interface solved as a linear system, then the flow through the first layer",
        solver_rel_tol=1e-9,
        instances=({"dT": 20.0, "Ra": 0.1, "Rb": 0.15}, {"dT": 30.0, "Ra": 0.2, "Rb": 0.1}))


def s18_isothermal_work() -> Structure:
    return Structure(
        "S18", "Work done by a gas expanding at constant temperature", "thermodynamics", "isothermal_expansion_work",
        (_in("p1", "pressure", "kPa", "initial pressure", 200.0, (100.0, 400.0)),
         _in("V1", "volume", "m^3", "initial volume", 0.005, (0.001, 0.01)),
         _in("rho", "ratio", "1", "final volume divided by initial volume", 2.0, (1.5, 4.0)),
         _co("W", "energy", "J", "work done by the gas", "p1*V1*log(rho)")),
        "W",
        (Assumption("A-ideal", "The gas is ideal and the expansion is slow and isothermal.", "modelling", ("p1", "V1")),
         Assumption("A-initial", "The pressure and volume given are those of the gas before the expansion.", "boundary_condition", ("rho",))),
        _spec("A gas at a pressure of {p1} kPa occupies {V1} m³ in a cylinder. It expands slowly at constant temperature until "
              "its volume is {rho} times its initial volume.",
              "How much work does the gas do during the expansion?", "work done by the gas", "J",
              "A separate engine B on another bench does {v} {u} of work per stroke, but it is unrelated to this gas.",
              "A reference gas B does {v} {u} of work.",
              "A separate meter B reads {v} {u}, but it plays no part in the expansion.", "Hz", equivalent="kJ"),
        ("p1", 1.25), _solve_isothermal_work, 3,
        "the integral of p dV along the isotherm p = p1 V1 / V, computed by adaptive quadrature",
        solver_rel_tol=1e-9,
        instances=({"p1": 200.0, "V1": 0.005, "rho": 2.0}, {"p1": 300.0, "V1": 0.004, "rho": 3.0}))


def s19_projectile_range() -> Structure:
    return Structure(
        "S19", "Range of a projectile on level ground", "mechanics", "projectile_range_level_ground",
        (_in("v", "speed", "m/s", "launch speed", 20.0, (12.0, 30.0)),
         _in("theta", "angle", "deg", "launch angle above the horizontal", 35.0, (20.0, 60.0)),
         _g(),
         _co("R", "length", "m", "horizontal range", "v**2*sin(2*theta)/g")),
        "R",
        (A_G, Assumption("A-drag", "Air resistance is neglected.", "modelling", ("v", "theta")),
         Assumption("A-level", "The ball is launched from and lands on the same level ground.", "boundary_condition", ("v",))),
        _spec("A ball is launched from level ground with speed {v} m/s at {theta} degrees above the horizontal. Neglect air "
              "resistance and take g = {g} m/s².",
              "What is the horizontal distance from the launch point to where the ball lands?", "horizontal range of the ball",
              "m", "A separate drone B flies a horizontal distance of {v} {u}, but it plays no part in the ball's motion.",
              "A reference ball B lands {v} {u} from its launch point.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the ball's motion.", "W", equivalent="cm"),
        ("v", 1.25), _solve_range, 3,
        "the planar flight integrated with an adaptive ODE solver until the ball returns to the ground",
        solver_rel_tol=1e-6,
        instances=({"v": 20.0, "theta": 35.0, "g": 9.8}, {"v": 25.0, "theta": 50.0, "g": 9.8}))


def s20_thin_lens_image() -> Structure:
    return Structure(
        "S20", "Image distance of a thin converging lens", "optics", "thin_lens_image_distance",
        (_in("f", "length", "cm", "focal length of the lens", 12.0, (8.0, 14.0)),
         _in("do", "length", "cm", "distance of the object from the lens", 40.0, (20.0, 60.0)),
         _co("di", "length", "cm", "distance of the image from the lens", "f*do/(do - f)")),
        "di",
        (Assumption("A-thin", "The lens is thin and the rays are close to the axis.", "modelling", ("f",)),
         Assumption("A-object", "The object is on the axis, beyond the focal length, on the side the light comes from.", "boundary_condition", ("do",))),
        _spec("A thin converging lens has a focal length of {f} cm. An object is placed on the axis {do} cm in front of the lens.",
              "How far from the lens is the real image formed?", "distance of the image from the lens", "cm",
              "A separate lens B on another bench forms an image {v} {u} from it, but it is unrelated to this lens.",
              "A reference lens B forms an image {v} {u} from it.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the imaging.", "W", equivalent="m"),
        ("do", 1.25), _solve_lens, 2,
        "the thin-lens equation 1/f = 1/do + 1/di solved for di with a bracketing root finder",
        solver_rel_tol=1e-9,
        instances=({"f": 12.0, "do": 40.0}, {"f": 10.0, "do": 35.0}))


ALL = (s11_braking_distance, s12_curve_speed, s13_pendulum_period, s14_lift_power, s15_parallel_power, s16_rl_current,
       s17_wall_heat_flow, s18_isothermal_work, s19_projectile_range, s20_thin_lens_image)


def all_structures() -> list[Structure]:
    return [factory() for factory in ALL]
