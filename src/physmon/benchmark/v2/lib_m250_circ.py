"""M250 phase 2, batch circ: ten new DECOY-v2 structures S263 to S272 (AC and DC circuits and electronics; acoustics) and their gold plans.

Same pattern as `lib_fluids.py`: a typed graph, an independently coded numeric solver (a nodal analysis with a root finder for the
bridge null, a steady-state harmonic linear system, a quadrature of the conducting part of the rectified cycle, a power balance of the
loaded transformer, an ODE with an event, an ODE for the energy dissipated in a discharge, a root finder for a closed pipe, a crest
tracker with wind, a mode root finder with a node finder, a scan for the resonance instants of a draining tube), at least four numeric
instantiations and a relevant edit that moves the answer.

Every answer-deciding condition (initial and boundary conditions, the governing model where standard models compete) is stated in the
prompt; the prompt carries no numeral that is not a graph input. Admission status: agent-verified, not expert-reviewed.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.integrate import quad, solve_ivp
from scipy.optimize import brentq

from physmon.benchmark.v2.graph import Assumption, Structure
from physmon.benchmark.v2.library import _co, _in, _spec
from physmon.benchmark.v2.trace import Plan, Step

# --- solvers (independent routes; SI inputs in node order) -----------------------------------------------------------------------


def _solve_metre_bridge(Lw, R, ell, Lx, d):
    # Nodal analysis of the bridge with an arbitrary uniform bridge wire, supply and galvanometer; a root finder finds the unknown
    # resistance X that gives zero galvanometer current, and the resistivity follows from the sample dimensions.
    rate, supply, r_g = 0.8, 3.0, 120.0
    r_left, r_right = rate * ell, rate * (Lw - ell)

    def galvanometer(x):
        matrix = np.array([[1.0 / R + 1.0 / x + 1.0 / r_g, -1.0 / r_g], [-1.0 / r_g, 1.0 / r_left + 1.0 / r_right + 1.0 / r_g]])
        v_m, v_s = np.linalg.solve(matrix, np.array([supply / R, supply / r_left]))
        return (v_m - v_s) / r_g

    x = brentq(galvanometer, 1e-3, 1e6, xtol=1e-14, rtol=1e-14)
    return float(x * (math.pi * d * d / 4.0) / Lx)


def _solve_rlc_phase(R, L, C, f):
    # Steady-state charge q = a cos(wt) + b sin(wt) of L q'' + R q' + q / C = cos(wt) from a 2x2 linear system; the current q' has the
    # phase angle atan2(w a, w b) against the source, and the magnitude is returned.
    w = 2.0 * math.pi * f
    matrix = np.array([[1.0 / C - L * w * w, R * w], [-R * w, 1.0 / C - L * w * w]])
    a, b = np.linalg.solve(matrix, np.array([1.0, 0.0]))
    return float(abs(math.atan2(w * a, w * b)))


def _solve_bridge_rectifier(Vm, n, Vd):
    # Quadrature of the conducting part of the cycle: the load voltage is |v| minus the two forward drops while that is positive.
    v_peak = math.sqrt(2.0) * Vm / n
    start = brentq(lambda t: v_peak * math.sin(t) - 2.0 * Vd, 0.0, math.pi / 2.0, xtol=1e-15, rtol=1e-15)
    value, _ = quad(lambda t: max(abs(v_peak * math.sin(t)) - 2.0 * Vd, 0.0), 0.0, math.pi, points=[start, math.pi - start],
                    epsabs=0.0, epsrel=1e-13, limit=200)
    return float(value / math.pi)


def _solve_winding_loss(P, Vs, Np, Ns, Rp, Rs):
    # Power balance: the primary terminal voltage is the reflected secondary terminal voltage plus the drops in both windings; the
    # losses are the input power minus the delivered power.
    i_s = P / Vs
    i_p = i_s * Ns / Np
    v_p = i_p * Rp + (Np / Ns) * (Vs + i_s * Rs)
    return float(v_p * i_p - P)


def _solve_divider_charge(R1, R2, C, p):
    # The capacitor ODE with a stated battery emf, integrated until the voltage reaches the fraction p of its final value.
    emf = 9.0
    final = emf * R2 / (R1 + R2)

    def reached(t, y):
        return y[0] - p * final

    reached.terminal = True
    reached.direction = 1
    solution = solve_ivp(lambda t, y: [(emf - y[0]) / (R1 * C) - y[0] / (R2 * C)], (0.0, 1e3 * (R1 + R2) * C), [0.0], events=reached,
                         rtol=1e-12, atol=1e-14)
    return float(solution.t_events[0][0])


def _solve_discharge_heat(V, R1, N, a, ell, mu0):
    # The inductance of the long solenoid, then the energy dissipated by the decaying current in a discharge resistor, integrated as
    # an ODE (current and dissipated energy) after the battery branch opens.
    inductance = mu0 * N * N * math.pi * a * a / ell
    current = V / R1
    r_discharge = 25.0

    solution = solve_ivp(lambda t, y: [-r_discharge * y[0] / inductance, r_discharge * y[0] ** 2], (0.0, 60.0 * inductance / r_discharge),
                         [current, 0.0], rtol=1e-12, atol=1e-18, method="DOP853")
    return float(solution.y[1][-1])


def _solve_pipe_beat(f, T1, T2, c0, T0):
    # Resonance of the closed pipe as the root of cos(2 pi f L / c) (a pressure node at the open end): first the effective length
    # that makes it sound at the fork frequency in the cool air, then the new fundamental in the warm air.
    c1, c2 = c0 * math.sqrt(T1 / T0), c0 * math.sqrt(T2 / T0)
    length = brentq(lambda x: math.cos(2.0 * math.pi * f * x / c1), 0.5 * c1 / (4.0 * f), 1.5 * c1 / (4.0 * f), xtol=1e-15, rtol=1e-15)
    pipe = brentq(lambda g: math.cos(2.0 * math.pi * g * length / c2), 0.5 * f, 1.5 * f, xtol=1e-13, rtol=1e-15)
    return float(pipe - f)


def _solve_receding_reflector_echo(f, w, v, c):
    # Crest tracking in still air: a crest leaves the loudspeaker at rest, meets the receding reflector (found with a root finder), and
    # returns at the speed of sound until it meets the retreating microphone; the echo frequency is the inverse of the spacing of two
    # consecutive echo arrivals, and the answer is how far it lies below the tone.
    distance = 30.0

    def arrival(n):
        t_n = n / f
        hit = brentq(lambda t: c * (t - t_n) - (distance + w * t), t_n, t_n + 2.0 * distance / (c - w), xtol=1e-17, rtol=1e-15)
        x_hit = distance + w * hit
        return brentq(lambda t: x_hit - c * (t - hit) + v * t, hit, hit + 2.0 * x_hit / (c - v), xtol=1e-17, rtol=1e-15)

    return float(f - 1.0 / (arrival(5) - arrival(4)))


def _solve_kundt_spacing(Y, rho, Lr, c):
    # The free-free rod clamped at its middle: the strain vanishes at the free ends, cos(k L / 2) = 0, found with a root finder; then
    # the nodes of the standing wave p(x) = cos(2 pi f x / c) in the tube are located and their spacing measured.
    speed = math.sqrt(Y / rho)
    k = brentq(lambda x: math.cos(x * Lr / 2.0), 0.5 * math.pi / Lr, 1.5 * math.pi / Lr, xtol=1e-15, rtol=1e-15)
    f = speed * k / (2.0 * math.pi)
    kk = 2.0 * math.pi * f / c
    node1 = brentq(lambda x: math.cos(kk * x), 0.2 * math.pi / kk, 0.8 * math.pi / kk, xtol=1e-15, rtol=1e-15)
    node2 = brentq(lambda x: math.cos(kk * x), 1.2 * math.pi / kk, 1.8 * math.pi / kk, xtol=1e-15, rtol=1e-15)
    return float(node2 - node1)


def _solve_drain_resonance_interval(f, vw, c):
    # The air column L(t) = L0 - vw t resonates when cos(2 pi L / lambda) = 0; the first two such instants are found by a scan and a
    # root finder, and the interval between them is returned.
    lam = c / f
    top = 2.0

    def phase(t):
        return math.cos(2.0 * math.pi * (top - vw * t) / lam)

    grid = np.linspace(0.0, (top - 0.1) / vw, 40001)
    values = np.array([phase(t) for t in grid])
    crossings = np.nonzero(values[:-1] * values[1:] < 0.0)[0]
    first, second = (brentq(phase, grid[i], grid[i + 1], xtol=1e-13, rtol=1e-15) for i in crossings[:2])
    return float(second - first)


# --- structures --------------------------------------------------------------------------------------------------------------


def s263_metre_bridge_resistivity() -> Structure:
    return Structure(
        "S263", "Resistivity of a sample wire from the balance point of a metre bridge", "circuits", "metre_bridge_balance_resistivity",
        (_in("Lw", "length", "cm", "length of the bridge wire", 100.0, (90.0, 110.0)),
         _in("R", "resistance", "Ω", "resistance in the left gap", 12.0, (5.0, 50.0)),
         _in("l", "length", "cm", "distance of the balance point from the left end of the bridge wire", 41.5, (30.0, 70.0)),
         _in("Lx", "length", "m", "length of the sample wire", 1.5, (0.5, 3.0)),
         _in("d", "length", "mm", "diameter of the sample wire", 0.30, (0.15, 0.8)),
         _co("X", "resistance", "Ω", "resistance of the sample wire", "R*(Lw - l)/l"),
         _co("A", "area", "mm^2", "cross-section area of the sample wire", "pi*d**2/4"),
         _co("rho", "resistivity", "Ω*m", "resistivity of the material of the sample wire", "X*A/Lx")),
        "rho",
        (Assumption("A-null", "At the balance point the galvanometer carries no current, so the two arms of the bridge have equal "
                              "voltage ratios and the supply and the galvanometer do not enter.", "boundary_condition", ("l", "R")),
         Assumption("A-wire", "The bridge wire is uniform and the strips, leads and contact have negligible resistance; the sample wire is "
                              "uniform and at one steady temperature.", "modelling", ("Lw", "Lx", "d"))),
        _spec("In a metre bridge a uniform bridge wire of length {Lw} cm is stretched between two thick copper strips. A resistance box of "
              "{R} Ω is joined across the left gap and a straight sample wire of one uniform material, of length {Lx} m and diameter "
              "{d} mm, across the right gap. A sliding contact on the bridge wire is joined through a galvanometer to the junction of "
              "the box and the sample wire. The galvanometer reads zero when the contact is {l} cm from the left end of the bridge "
              "wire. The strips, the leads and the contact have negligible resistance, and the wires stay at one steady temperature.",
              "What is the resistivity of the material of the sample wire?", "resistivity of the material of the sample wire", "Ω*m",
              "A separate rheostat B in another laboratory has a resistivity of {v} {u}, but it is unrelated to this bridge.",
              "A reference wire B has a resistivity of {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the bridge.", "W", equivalent=None),
        ("R", 1.5), _solve_metre_bridge, 5,
        "a nodal analysis of the bridge with an arbitrary uniform bridge wire, supply and galvanometer, in which a root finder searches for "
        "the unknown resistance that makes the galvanometer current zero; the resistivity then follows from the sample dimensions",
        solver_rel_tol=1e-8,
        instances=({"Lw": 100.0, "R": 12.0, "l": 41.5, "Lx": 1.5, "d": 0.30}, {"Lw": 100.0, "R": 20.0, "l": 55.0, "Lx": 2.0, "d": 0.40},
                   {"Lw": 100.0, "R": 8.0, "l": 36.0, "Lx": 1.2, "d": 0.25}, {"Lw": 100.0, "R": 15.0, "l": 62.0, "Lx": 2.5, "d": 0.35}))


def s264_series_rlc_phase_angle() -> Structure:
    return Structure(
        "S264", "Phase angle between the current and the source voltage in a driven series RLC circuit", "circuits",
        "driven_series_rlc_phase_angle",
        (_in("R", "resistance", "Ω", "resistance of the resistor", 30.0, (10.0, 100.0)),
         _in("L", "inductance", "mH", "inductance of the inductor", 25.0, (10.0, 80.0)),
         _in("C", "capacitance", "μF", "capacitance of the capacitor", 6.0, (2.0, 20.0)),
         _in("f", "frequency", "Hz", "frequency of the source", 500.0, (250.0, 900.0)),
         _co("XL", "reactance", "Ω", "reactance of the inductor", "2*pi*f*L"),
         _co("XC", "reactance", "Ω", "reactance of the capacitor", "1/(2*pi*f*C)"),
         _co("X", "reactance", "Ω", "net reactance of the circuit", "XL - XC"),
         _co("phi", "angle", "deg", "magnitude of the phase angle between the source voltage and the current", "atan(Abs(X/R))")),
        "phi",
        (Assumption("A-ideal", "The source is an ideal sinusoidal voltage source and the inductor and the capacitor are ideal lumped "
                               "components, so the reactances are 2 pi f L and 1 / (2 pi f C) and the resistor has the stated resistance.",
                    "modelling", ("R", "L", "C", "f")),
         Assumption("A-steady", "The circuit is in its steady sinusoidal state, so the current has the same frequency as the source and a "
                                "fixed phase angle to it.", "boundary_condition", ("f",))),
        _spec("A resistor of {R} Ω, an inductor of {L} mH and a capacitor of {C} μF are joined in series across an ideal sinusoidal "
              "voltage source of frequency {f} Hz. The inductor and the capacitor are ideal components, and the circuit is in its steady "
              "sinusoidal state.",
              "What is the magnitude of the phase angle between the source voltage and the current?",
              "magnitude of the phase angle between the source voltage and the current", "deg",
              "A separate pendulum B in another laboratory swings at {v} {u}, but it is unrelated to this circuit.",
              "A reference circuit B has a phase angle of {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the circuit.", "W", equivalent="rad"),
        ("f", 1.5), _solve_rlc_phase, 4,
        "the steady-state charge of the driven oscillator equation L q'' + R q' + q / C = cos(wt) found from a 2x2 linear system for its "
        "cosine and sine coefficients, and the phase of the current q' read from them, instead of the impedance triangle",
        solver_rel_tol=1e-8,
        instances=({"R": 30.0, "L": 25.0, "C": 6.0, "f": 500.0}, {"R": 45.0, "L": 40.0, "C": 10.0, "f": 350.0},
                   {"R": 22.0, "L": 18.0, "C": 4.7, "f": 600.0}, {"R": 60.0, "L": 60.0, "C": 12.0, "f": 300.0}))


def s265_bridge_rectifier_average_voltage() -> Structure:
    return Structure(
        "S265", "Average load voltage of a bridge rectifier with forward diode drops", "circuits",
        "full_wave_bridge_constant_drop_average_voltage",
        (_in("Vm", "voltage", "V", "rms voltage of the mains supply", 230.0, (150.0, 250.0)),
         _in("n", "ratio", "1", "turns ratio of the transformer, primary to secondary", 4.0, (2.0, 6.0)),
         _in("Vd", "voltage", "V", "forward drop of a conducting diode, a stated model constant", 0.7, (0.5, 1.0), provenance="assumed"),
         _co("Vp", "voltage", "V", "peak voltage of the secondary", "sqrt(2)*Vm/n"),
         _co("th0", "angle", "rad", "phase at which the diodes start to conduct", "asin(2*Vd/Vp)"),
         _co("Vavg", "voltage", "V", "average voltage across the load",
             "(2/pi)*(Vp*cos(th0) - 2*Vd*(pi/2 - th0))")),
        "Vavg",
        (Assumption("A-drop", "Each diode is an ideal switch in series with a constant forward drop of the stated value: it conducts only "
                              "while its forward voltage exceeds that drop and then has no further resistance; two diodes conduct at a "
                              "time, so the load sees the rectified secondary voltage minus two drops.", "modelling", ("Vd",)),
         Assumption("A-source", "The transformer is ideal with no winding resistance, the supply is sinusoidal, and there is no smoothing "
                                "capacitor, so the load voltage is zero while no pair of diodes conducts.", "boundary_condition",
                    ("Vm", "n"))),
        _spec("A transformer with a primary-to-secondary turns ratio of {n} steps down a sinusoidal mains supply of {Vm} V rms to feed a bridge of four "
              "identical diodes, with no smoothing capacitor, across a resistive load. Each diode is an ideal switch in series with a "
              "constant forward drop of {Vd} V, so it conducts only while its forward voltage exceeds that drop, and two diodes conduct "
              "at a time. The transformer is ideal and its windings have no resistance.",
              "What is the average voltage across the load?", "average voltage across the load", "V",
              "A separate battery B in another laboratory supplies {v} {u}, but it is unrelated to this rectifier.",
              "A reference rectifier B has an average output of {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the rectifier.", "W", equivalent="mV"),
        ("Vm", 0.75), _solve_bridge_rectifier, 3,
        "a numerical quadrature over the conducting part of the cycle only, the load voltage being the rectified secondary minus the two "
        "forward drops while that is positive, with the turn-on phase found by a root finder, instead of the closed form",
        solver_rel_tol=1e-8,
        instances=({"Vm": 230.0, "n": 4.0, "Vd": 0.7}, {"Vm": 240.0, "n": 3.0, "Vd": 0.6}, {"Vm": 220.0, "n": 5.0, "Vd": 0.8},
                   {"Vm": 200.0, "n": 5.0, "Vd": 0.9}))


def s266_transformer_winding_loss() -> Structure:
    return Structure(
        "S266", "Power lost in the two windings of a loaded transformer", "circuits", "transformer_winding_copper_loss",
        (_in("P", "power", "W", "power delivered to the load", 480.0, (100.0, 2000.0)),
         _in("Vs", "voltage", "V", "rms voltage across the load", 24.0, (12.0, 48.0)),
         _in("Np", "turns", "1", "number of turns of the primary winding", 1200.0, (800.0, 2000.0)),
         _in("Ns", "turns", "1", "number of turns of the secondary winding", 120.0, (60.0, 400.0)),
         _in("Rp", "resistance", "Ω", "resistance of the primary winding", 3.0, (1.0, 10.0)),
         _in("Rs", "resistance", "Ω", "resistance of the secondary winding", 0.05, (0.02, 0.2)),
         _co("Is", "current", "A", "rms current in the secondary winding", "P/Vs"),
         _co("Ip", "current", "A", "rms current in the primary winding", "Is*Ns/Np"),
         _co("Ploss", "power", "W", "power dissipated in the two windings", "Is**2*Rs + Ip**2*Rp")),
        "Ploss",
        (Assumption("A-ideal-core", "The flux links every turn of both windings and the magnetising current, the leakage inductance and the "
                                    "core loss are negligible, so the currents are in the inverse ratio of the turns and the load is a "
                                    "resistor that takes the stated power at the stated voltage.", "modelling", ("Np", "Ns", "P", "Vs")),
         Assumption("A-winding", "The only losses are the heat in the two windings, each of the stated resistance, and the currents are "
                                 "steady sinusoidal rms values.", "boundary_condition", ("Rp", "Rs"))),
        _spec("A transformer has a primary winding of {Np} turns and resistance {Rp} Ω and a secondary winding of {Ns} turns and resistance "
              "{Rs} Ω. The secondary feeds a resistive load that takes {P} W at an rms voltage of {Vs} V across the load. All the flux "
              "links every turn of both windings, the magnetising current, the leakage inductance and the core loss are negligible, and "
              "the currents are steady sinusoidal.",
              "How much power is dissipated as heat in the two windings together?", "power dissipated as heat in the two windings", "W",
              "A separate heater B in another laboratory dissipates {v} {u}, but it is unrelated to this transformer.",
              "A reference transformer B loses {v} {u} in its windings.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the transformer.", "s", equivalent="kW"),
        ("P", 1.5), _solve_winding_loss, 6,
        "a power balance: the primary terminal voltage is built up from the reflected secondary voltage and the drops across both "
        "windings, and the losses are the input power minus the power delivered, instead of summing the winding heats directly",
        solver_rel_tol=1e-9,
        instances=({"P": 480.0, "Vs": 24.0, "Np": 1200.0, "Ns": 120.0, "Rp": 3.0, "Rs": 0.05},
                   {"P": 900.0, "Vs": 48.0, "Np": 1500.0, "Ns": 150.0, "Rp": 4.5, "Rs": 0.08},
                   {"P": 250.0, "Vs": 12.0, "Np": 800.0, "Ns": 100.0, "Rp": 2.5, "Rs": 0.06},
                   {"P": 1200.0, "Vs": 36.0, "Np": 1800.0, "Ns": 300.0, "Rp": 6.0, "Rs": 0.04}))


def s267_divider_capacitor_charging_time() -> Structure:
    return Structure(
        "S267", "Time for a capacitor on a resistor divider to reach a fraction of its final voltage", "circuits",
        "divider_thevenin_rc_charge_fraction_time",
        (_in("R1", "resistance", "kΩ", "series resistor from the battery", 4.7, (1.0, 20.0)),
         _in("R2", "resistance", "kΩ", "resistor across the capacitor", 6.8, (1.0, 20.0)),
         _in("C", "capacitance", "μF", "capacitance of the capacitor", 22.0, (1.0, 100.0)),
         _in("p", "ratio", "1", "fraction of its final voltage that the capacitor must reach", 0.9, (0.5, 0.95)),
         _co("Rth", "resistance", "kΩ", "Thevenin resistance seen by the capacitor", "R1*R2/(R1 + R2)"),
         _co("tau", "time", "ms", "time constant of the charging", "Rth*C"),
         _co("t", "time", "ms", "time for the capacitor voltage to reach the stated fraction of its final value", "-tau*log(1 - p)")),
        "t",
        (Assumption("A-ideal", "The battery has a constant emf and negligible internal resistance, the capacitor is ideal and does not "
                               "leak, and the switch closes at the start with the capacitor uncharged.", "boundary_condition", ("R1", "R2", "C")),
         Assumption("A-fraction", "The fraction is taken of the final steady voltage across the capacitor, which is the open-circuit "
                                  "(Thevenin) voltage of the divider, not of the battery emf.", "modelling", ("p",))),
        _spec("A battery of constant emf and negligible internal resistance is joined through a switch and a resistor of {R1} kΩ to a "
              "second resistor of {R2} kΩ. An ideal capacitor of {C} μF, uncharged at first and without leakage, is wired across the "
              "second resistor, and the other ends of the capacitor and the second resistor return to the battery. The switch is "
              "closed at the start, and the voltage across the capacitor then rises towards its final steady value.",
              "How long after the switch is closed does the capacitor voltage reach {p} of its final steady value?",
              "time for the capacitor voltage to reach the stated fraction of its final steady value", "ms",
              "A separate clock B in another laboratory shows {v} {u}, but it is unrelated to this circuit.",
              "A reference circuit B charges in {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the circuit.", "W", equivalent="s"),
        ("C", 1.5), _solve_divider_charge, 4,
        "the capacitor ODE with an explicit battery emf and both resistors, integrated until the voltage reaches the stated fraction of "
        "its final value, found with an event, instead of the Thevenin time constant",
        solver_rel_tol=1e-8,
        instances=({"R1": 4.7, "R2": 6.8, "C": 22.0, "p": 0.9}, {"R1": 10.0, "R2": 15.0, "C": 10.0, "p": 0.8},
                   {"R1": 3.3, "R2": 12.0, "C": 47.0, "p": 0.95}, {"R1": 15.0, "R2": 4.7, "C": 33.0, "p": 0.7}))


def s268_solenoid_discharge_heat() -> Structure:
    return Structure(
        "S268", "Heat released in a resistor when a solenoid current is switched into it", "circuits",
        "long_solenoid_stored_energy_dissipated_in_discharge_resistor",
        (_in("V", "voltage", "V", "emf of the battery", 12.0, (6.0, 24.0)),
         _in("R1", "resistance", "Ω", "resistance of the series resistor", 4.0, (2.0, 10.0)),
         _in("N", "turns", "1", "number of turns of the solenoid", 800.0, (400.0, 1500.0)),
         _in("a", "length", "cm", "radius of the solenoid", 1.5, (1.0, 3.0)),
         _in("ell", "length", "cm", "length of the solenoid", 40.0, (25.0, 60.0)),
         _in("mu0", "permeability", "T*m/A", "permeability of free space, a stated constant", 1.257e-6, (1.25e-6, 1.27e-6),
             provenance="assumed"),
         _co("L", "inductance", "mH", "inductance of the solenoid", "mu0*N**2*pi*a**2/ell"),
         _co("I0", "current", "A", "steady current in the solenoid", "V/R1"),
         _co("E", "energy", "mJ", "energy released as heat in the discharge resistor", "L*I0**2/2")),
        "E",
        (Assumption("A-mu0", "The permeability of free space has the stated value and the solenoid has no core.", "modelling", ("mu0",)),
         Assumption("A-long", "The solenoid is long compared with its radius, so its field is uniform inside and negligible outside, "
                              "and its winding has negligible resistance.", "modelling", ("N", "a", "ell")),
         Assumption("A-switch", "The battery is ideal and the current has reached its steady value before the switch opens; when it "
                                "opens, the whole current of the solenoid passes through the discharge resistor and no energy is "
                                "radiated.", "boundary_condition", ("V", "R1"))),
        _spec("An ideal battery of emf {V} V is joined through a switch and a resistor of {R1} Ω to a long air-cored solenoid of {N} "
              "turns, radius {a} cm and length {ell} cm, whose winding has negligible resistance. A second resistor is wired across the "
              "solenoid. The switch has been closed long enough for the current to reach its steady value, and then it opens, so that "
              "the current of the solenoid continues through the second resistor alone. Take μ₀ = {mu0} T·m/A.",
              "How much energy is released as heat in the second resistor after the switch opens?",
              "energy released as heat in the second resistor", "mJ",
              "A separate lamp B in another laboratory radiates {v} {u}, but it is unrelated to this circuit.",
              "A reference circuit B releases {v} {u} of heat.",
              "A separate meter B reads {v} {u}, but it plays no part in the circuit.", "s", equivalent="J",
              formats={"mu0": ".4g"}),
        ("V", 1.5), _solve_discharge_heat, 6,
        "the inductance of the long solenoid, then the decaying current integrated as an ODE together with the energy dissipated in an "
        "arbitrary discharge resistor, instead of the stored energy formula",
        solver_rel_tol=1e-8,
        instances=({"V": 12.0, "R1": 4.0, "N": 800.0, "a": 1.5, "ell": 40.0, "mu0": 1.257e-6},
                   {"V": 24.0, "R1": 6.0, "N": 1200.0, "a": 2.0, "ell": 50.0, "mu0": 1.257e-6},
                   {"V": 9.0, "R1": 3.0, "N": 600.0, "a": 1.2, "ell": 30.0, "mu0": 1.257e-6},
                   {"V": 18.0, "R1": 8.0, "N": 1000.0, "a": 2.5, "ell": 55.0, "mu0": 1.257e-6}))


def s269_pipe_fork_beat_after_warming() -> Structure:
    return Structure(
        "S269", "Beat frequency between a tuning fork and a closed pipe when the air in the pipe warms", "acoustics",
        "closed_pipe_tuned_to_fork_beat_after_temperature_rise",
        (_in("f", "frequency", "Hz", "frequency of the tuning fork", 440.0, (256.0, 880.0)),
         _in("T1", "temperature", "K", "temperature of the air when the pipe is tuned to the fork", 288.0, (275.0, 295.0)),
         _in("T2", "temperature", "K", "temperature of the air in the pipe when the fork and the pipe sound together", 301.0,
             (298.0, 318.0)),
         _in("c0", "speed", "m/s", "speed of sound in air at the reference temperature, a stated constant", 331.3, (330.0, 333.0),
             provenance="assumed"),
         _in("T0", "temperature", "K", "reference temperature of the speed of sound, a stated constant", 273.15, (273.0, 273.3),
             provenance="assumed"),
         _co("c1", "speed", "m/s", "speed of sound in the air of the pipe when it is tuned", "c0*sqrt(T1/T0)"),
         _co("Leff", "length", "m", "effective length of the pipe, including the end correction", "c1/(4*f)"),
         _co("c2", "speed", "m/s", "speed of sound in the warm air of the pipe", "c0*sqrt(T2/T0)"),
         _co("f2", "frequency", "Hz", "fundamental frequency of the pipe in the warm air", "c2/(4*Leff)"),
         _co("beat", "frequency", "Hz", "beat frequency between the fork and the pipe", "f2 - f")),
        "beat",
        (Assumption("A-c", "The speed of sound in dry air is c0 sqrt(T / T0) with the stated constants, and it does not depend on the "
                           "frequency or the amplitude.", "modelling", ("c0", "T0")),
         Assumption("A-pipe", "The pipe is closed at one end and open at the other and sounds in its fundamental; its effective length and "
                              "the frequency of the fork do not change with temperature, and the whole air column is at one temperature.",
                    "boundary_condition", ("f", "T1", "T2"))),
        _spec("A pipe closed at one end and open at the other is tuned, in air at {T1} K, so that its fundamental note has exactly the "
              "frequency {f} Hz of a tuning fork. The effective length of the pipe, including the end correction at its open end, and "
              "the frequency of the fork do not change with temperature. The air in the pipe, all at one temperature, is then at "
              "{T2} K, and the fork and the pipe sound together. Take the speed of sound in air as c₀ √(T / T₀), with c₀ = {c0} m/s "
              "and T₀ = {T0} K.",
              "What beat frequency is heard between the fork and the fundamental note of the pipe?",
              "beat frequency between the fork and the pipe", "Hz",
              "A separate organ B in another hall plays at {v} {u}, but it is unrelated to this pipe.",
              "A reference pipe B beats at {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the pipe.", "W", equivalent="kHz",
              formats={"c0": ".4g", "T0": ".5g"}),
        ("T2", 1.03), _solve_pipe_beat, 5,
        "the resonance of the closed pipe as the root of cos(2 pi f L / c) found with a root finder: first the effective length that "
        "makes the pipe sound at the fork frequency in the cool air, then the new fundamental in the warm air",
        solver_rel_tol=1e-8,
        instances=({"f": 440.0, "T1": 288.0, "T2": 301.0, "c0": 331.3, "T0": 273.15},
                   {"f": 512.0, "T1": 283.0, "T2": 304.0, "c0": 331.3, "T0": 273.15},
                   {"f": 256.0, "T1": 291.0, "T2": 310.0, "c0": 331.5, "T0": 273.15},
                   {"f": 660.0, "T1": 280.0, "T2": 299.0, "c0": 331.3, "T0": 273.15}))


def s270_receding_lorry_echo_on_retreating_cart() -> Structure:
    return Structure(
        "S270", "Fall in the frequency of the sound returned by a receding lorry and picked up on a retreating trolley", "acoustics",
        "doppler_receding_reflector_returned_sound_heard_by_retreating_observer",
        (_in("f", "frequency", "Hz", "frequency of the note", 1500.0, (500.0, 4000.0)),
         _in("w", "speed", "m/s", "speed at which the lorry recedes from the post", 6.0, (2.0, 15.0)),
         _in("v", "speed", "m/s", "speed at which the trolley retreats from the post", 9.0, (3.0, 15.0)),
         _in("c", "speed", "m/s", "speed of sound in the still air, a stated constant", 343.0, (330.0, 350.0), provenance="assumed"),
         _co("f1", "frequency", "Hz", "frequency of the sound that reaches the lorry", "f*(c - w)/c"),
         _co("f2", "frequency", "Hz", "frequency of the reflected sound that the recorder picks up", "f1*(c - v)/(c + w)"),
         _co("df", "frequency", "Hz", "amount by which the frequency of the reflected sound lies below the frequency of the note",
             "f - f2")),
        "df",
        (Assumption("A-c", "The speed of sound has the stated constant value in the still air and does not depend on the frequency.",
                    "modelling", ("c",)),
         Assumption("A-motion", "The lorry and the trolley move at constant speeds along one straight line through the post, the air "
                                "is still, and the flat rear panel of the lorry sends every wave crest straight back with no change of "
                                "frequency in its own rest frame.", "boundary_condition", ("w", "v", "f"))),
        _spec("A siren on a fixed post in still air sounds a steady note of frequency {f} Hz along a straight road. The flat rear panel "
              "of a lorry, facing the post, drives directly away from it at a constant {w} m/s and sends the sound straight back, with no "
              "change of frequency in its own rest frame. A recorder on a trolley starts beside the post, runs directly away from the "
              "lorry along the same line at a constant {v} m/s, and faces the lorry, so that it picks up the reflected sound. Take the "
              "speed of sound in the still air as {c} m/s.",
              "By how much does the frequency of the reflected sound that the recorder picks up lie below the frequency of the note?",
              "amount by which the frequency of the reflected sound lies below the frequency of the note", "Hz",
              "A separate bell B in another valley rings at {v} {u}, but it is unrelated to this siren.",
              "A reference recorder B picks up sound that lies {v} {u} below its note.",
              "A separate sensor B reads {v} {u}, but it plays no part in the note.", "W", equivalent="kHz"),
        ("v", 1.5), _solve_receding_reflector_echo, 4,
        "tracking successive wave crests with a root finder: a crest leaves the post, meets the receding lorry, returns at the speed of "
        "sound until it meets the retreating recorder, and the frequency of the reflected sound is the inverse of the spacing of two "
        "arrivals",
        solver_rel_tol=1e-8,
        instances=({"f": 1500.0, "w": 6.0, "v": 9.0, "c": 343.0}, {"f": 2200.0, "w": 4.0, "v": 12.0, "c": 343.0},
                   {"f": 900.0, "w": 9.0, "v": 6.0, "c": 340.0}, {"f": 3000.0, "w": 5.0, "v": 10.0, "c": 346.0}))


def s271_kundt_tube_dust_spacing() -> Structure:
    return Structure(
        "S271", "Spacing of the dust heaps in a Kundt's tube driven by a clamped rod", "acoustics",
        "kundt_tube_rod_longitudinal_mode_dust_node_spacing",
        (_in("Y", "pressure", "MPa", "Young's modulus of the rod", 70000.0, (50000.0, 210000.0)),
         _in("rho", "density", "kg/m^3", "density of the rod", 2700.0, (2000.0, 9000.0)),
         _in("Lr", "length", "m", "length of the rod", 1.2, (0.6, 2.0)),
         _in("c", "speed", "m/s", "speed of sound in the air of the tube, a stated constant", 343.0, (330.0, 350.0), provenance="assumed"),
         _co("vr", "speed", "m/s", "speed of longitudinal waves along the rod", "sqrt(Y/rho)"),
         _co("fr", "frequency", "Hz", "frequency of the fundamental longitudinal vibration of the rod", "vr/(2*Lr)"),
         _co("lam", "length", "cm", "wavelength of the sound in the air of the tube", "c/fr"),
         _co("d", "length", "cm", "spacing of adjacent dust heaps", "lam/2")),
        "d",
        (Assumption("A-c", "The speed of sound in the air of the tube has the stated constant value.", "modelling", ("c",)),
         Assumption("A-rod", "The rod is thin, so longitudinal waves travel along it at sqrt(Y / rho); it is clamped exactly at its middle "
                             "and vibrates in its fundamental longitudinal mode with free ends, and the air in the tube is driven at "
                             "that frequency by a disc on one end.", "boundary_condition", ("Y", "rho", "Lr")),
         Assumption("A-heaps", "The dust collects at the displacement nodes of the standing wave in the tube, which are half a wavelength "
                               "apart.", "modelling", ("c",))),
        _spec("In a Kundt's tube experiment a thin metal rod of length {Lr} m, Young's modulus {Y} MPa and density {rho} kg/m³ is "
              "clamped exactly at its middle and vibrates in its fundamental longitudinal mode with both ends free. A light disc on one "
              "end of the rod drives the air in a long glass tube, which holds a fine dust. Standing waves form in the air at the "
              "frequency of the rod, and the dust collects in heaps at the nodes. Take the speed of sound in the air of the tube as "
              "{c} m/s.",
              "What is the spacing between adjacent dust heaps?", "spacing between adjacent dust heaps", "cm",
              "A separate guitar B in another room has strings that are {v} {u} apart, but it is unrelated to this tube.",
              "A reference tube B has dust heaps {v} {u} apart.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the tube.", "W", equivalent="mm"),
        ("Lr", 1.5), _solve_kundt_spacing, 4,
        "the fundamental mode of the free rod found as the root of cos(k L / 2) = 0 (zero strain at the free ends), then the nodes of the "
        "standing wave in the tube located with a root finder and their spacing measured, instead of the half-wavelength formula",
        solver_rel_tol=1e-9,
        instances=({"Y": 70000.0, "rho": 2700.0, "Lr": 1.2, "c": 343.0}, {"Y": 110000.0, "rho": 8900.0, "Lr": 1.0, "c": 343.0},
                   {"Y": 200000.0, "rho": 7800.0, "Lr": 1.5, "c": 340.0}, {"Y": 70000.0, "rho": 2700.0, "Lr": 0.8, "c": 346.0}))


def s272_draining_tube_resonance_interval() -> Structure:
    return Structure(
        "S272", "Time between successive resonances as the water drains from a resonance tube", "acoustics",
        "draining_resonance_tube_successive_resonance_interval",
        (_in("f", "frequency", "Hz", "frequency of the tuning fork", 512.0, (256.0, 1024.0)),
         _in("vw", "speed", "cm/s", "speed at which the water level falls", 1.5, (0.5, 3.0)),
         _in("c", "speed", "m/s", "speed of sound in the air of the tube, a stated constant", 343.0, (330.0, 350.0), provenance="assumed"),
         _co("lam", "length", "m", "wavelength of the sound in the air column", "c/f"),
         _co("dh", "length", "cm", "fall of the water level between successive resonances", "lam/2"),
         _co("t", "time", "s", "time between successive resonances", "dh/vw")),
        "t",
        (Assumption("A-c", "The speed of sound in the air column has the stated constant value.", "modelling", ("c",)),
         Assumption("A-column", "The column is closed by the water surface and open at the top, and resonates whenever its length, plus a "
                                "fixed end correction, is an odd number of quarter wavelengths of the fork; the water level falls at a "
                                "steady speed that is small compared with the speed of sound.", "boundary_condition", ("vw", "f"))),
        _spec("A tall vertical glass tube, open at the top, holds water that drains steadily from the bottom, so that the water surface "
              "falls at a constant {vw} cm/s. A tuning fork of frequency {f} Hz sounds steadily over the open top, and the air column "
              "between the top and the water surface, closed below by the water, resonates loudly each time its length, plus a fixed end "
              "correction, is an odd number of quarter wavelengths. Take the speed of sound in the air as {c} m/s.",
              "How much time passes between two successive resonances as the water level falls?",
              "time between two successive resonances", "s",
              "A separate clock B in another laboratory ticks every {v} {u}, but it is unrelated to this tube.",
              "A reference tube B resonates every {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the tube.", "W", equivalent="ms"),
        ("vw", 1.5), _solve_drain_resonance_interval, 3,
        "the air column length falling linearly in time, with the instants at which cos(2 pi L / lambda) crosses zero located by a scan and "
        "a root finder and the interval between the first two measured, instead of the half-wavelength formula",
        solver_rel_tol=1e-8,
        instances=({"f": 512.0, "vw": 1.5, "c": 343.0}, {"f": 440.0, "vw": 2.0, "c": 343.0}, {"f": 384.0, "vw": 1.2, "c": 340.0},
                   {"f": 640.0, "vw": 2.5, "c": 346.0}))


ALL = (s263_metre_bridge_resistivity, s264_series_rlc_phase_angle, s265_bridge_rectifier_average_voltage, s266_transformer_winding_loss,
       s267_divider_capacitor_charging_time, s268_solenoid_discharge_heat, s269_pipe_fork_beat_after_warming, s270_receding_lorry_echo_on_retreating_cart,
       s271_kundt_tube_dust_spacing, s272_draining_tube_resonance_interval)


def all_structures() -> tuple[Structure, ...]:
    return tuple(factory() for factory in ALL)


STRUCTURES: dict[str, Structure] = {s.structure_id: s for s in all_structures()}


# --- gold plans (principle and reason per computed node, in dependency order) ----------------------------------------------------


PLANS: dict[str, Plan] = {
    "S263": Plan(
        approach="At the balance point no current flows through the galvanometer, so the sample wire and the resistance box divide the "
                 "supply voltage in the same ratio as the two parts of the bridge wire. Find the unknown resistance from the lengths, then "
                 "the cross-section of the sample wire, then the resistivity.",
        steps=(
            Step("A", "Area of a circle, A = pi d^2 / 4",
                 "The sample wire has a circular cross-section, and its area is needed to turn its resistance into a resistivity."),
            Step("X", "Balance of a metre bridge, R / X = l / (Lw - l)",
                 "With the galvanometer at zero the potential of the sliding contact equals that of the junction of the box and the "
                 "sample, and a uniform wire has resistance proportional to its length, so the ratio of the resistances equals the ratio "
                 "of the lengths and the unknown resistance is R (Lw - l) / l."),
            Step("rho", "Resistance of a uniform wire, X = rho Lx / A, so rho = X A / Lx",
                 "The sample is one uniform material with a uniform section, so the resistance is the resistivity times the length over "
                 "the area; the resistivity follows from the resistance found at balance."),
        ),
        check="Order of magnitude: a metal wire has a resistivity of about 10^-7 to 10^-6 ohm metres. Limiting case: if the contact stood at "
              "the middle of the bridge wire the sample would have the same resistance as the box."),
    "S264": Plan(
        approach="In the steady state the current in the series circuit has a phase angle to the source set by the ratio of the net "
                 "reactance to the resistance. Find the two reactances, their difference, then the angle.",
        steps=(
            Step("XC", "Reactance of a capacitor, XC = 1 / (2 pi f C)",
                 "The capacitor voltage lags the current by ninety degrees, and its opposition falls as the frequency or the capacitance "
                 "grows."),
            Step("XL", "Reactance of an inductor, XL = 2 pi f L",
                 "The inductor opposes a changing current with a voltage that leads the current by ninety degrees, and its opposition "
                 "grows in proportion to the frequency and the inductance."),
            Step("X", "Net reactance of a series circuit, X = XL - XC",
                 "The inductor and the capacitor voltages are in antiphase, so in the series circuit their reactances subtract."),
            Step("phi", "Phase angle of a series RLC circuit, tan(phi) = X / R",
                 "On the phasor diagram the resistor voltage is in phase with the current and the net reactive voltage is at right angles "
                 "to it, so the angle between the source voltage and the current has the tangent X / R; its magnitude is asked."),
        ),
        check="Limiting cases: at resonance XL = XC and the angle is zero; with no reactance difference the circuit is purely resistive. The "
              "angle is below ninety degrees for any finite resistance. The amplitude of the source does not enter."),
    "S265": Plan(
        approach="The load voltage is the rectified secondary voltage minus the two forward drops, but only while the diodes conduct. Find "
                 "the peak voltage of the secondary, the phase at which conduction starts, then average the load voltage over a cycle.",
        steps=(
            Step("Vp", "Peak of a sinusoid from its rms value, Vp = sqrt(2) Vrms, and the turns ratio of an ideal transformer, Vs = Vm / n",
                 "The ideal transformer divides the mains rms voltage by the turns ratio; the peak voltage of the secondary is root two "
                 "times its rms value."),
            Step("th0", "Conduction condition of a diode pair, Vp sin(th) = 2 Vd",
                 "Two diodes conduct at a time, so the rectified voltage must exceed two forward drops before any current flows; this "
                 "gives the phase th0 at which conduction starts."),
            Step("Vavg", "Average of the load voltage, (1 / pi) integral from th0 to pi - th0 of (Vp sin th - 2 Vd) d(th)",
                 "The rectified waveform repeats every half cycle and is zero outside the conduction interval, so the average over a "
                 "half cycle is the integral over the interval divided by pi; it evaluates to (2 / pi) (Vp cos th0 - 2 Vd (pi/2 - th0))."),
        ),
        check="Limiting case: with zero forward drop the average is the textbook 2 Vp / pi. The average is less than that by about the "
              "two drops times the conducting fraction of the cycle. Order of magnitude: an 80 V peak gives about 50 V."),
    "S266": Plan(
        approach="The windings dissipate heat in proportion to the squares of their currents. Find the secondary current from the delivered "
                 "power and voltage, the primary current from the turns ratio, then add the two winding heats.",
        steps=(
            Step("Is", "Electrical power of a resistive load, P = Vs Is",
                 "The load takes the stated power at the stated rms voltage, so the current in the secondary winding, which is the load "
                 "current, is the power divided by the voltage."),
            Step("Ip", "Ampere-turn balance of an ideal transformer, Np Ip = Ns Is",
                 "With negligible magnetising current the two windings produce equal and opposite magnetomotive forces, so the currents "
                 "are in the inverse ratio of the turns."),
            Step("Ploss", "Joule heating in each winding, P = I^2 R, summed over the two windings",
                 "The heat in a winding is the square of its current times its resistance, and the only losses are in the two windings."),
        ),
        check="Power balance: the input power is the sum of the delivered power and the two winding losses. The primary loss is smaller "
              "than the secondary loss would be if the secondary current flowed in the primary resistance, by the square of the turns ratio."),
    "S267": Plan(
        approach="The capacitor sees the two resistors as a battery of fixed voltage with the parallel combination of the resistors in "
                 "series, so it charges exponentially towards the open-circuit voltage of the divider. Find the Thevenin resistance, the "
                 "time constant, then the time to the stated fraction.",
        steps=(
            Step("Rth", "Thevenin resistance of the divider, Rth = R1 R2 / (R1 + R2)",
                 "With the battery replaced by its negligible internal resistance, the capacitor sees the two resistors in parallel."),
            Step("tau", "Time constant of an RC circuit, tau = Rth C",
                 "The capacitor charges through the Thevenin resistance, so the time constant is that resistance times the capacitance."),
            Step("t", "Exponential approach to the final value, v = vf (1 - exp(-t / tau)), so t = -tau ln(1 - p)",
                 "The capacitor voltage rises as a fraction p = 1 - exp(-t / tau) of the final value vf, the open-circuit voltage of the "
                 "divider; since the fraction is taken of that final value, the battery emf cancels."),
        ),
        check="Limiting case: for a fraction of 1 - 1/e the time is one time constant. The result does not depend on the battery emf, and "
              "is shorter than R1 C ln(1/(1 - p)) because the parallel combination is smaller than R1."),
    "S268": Plan(
        approach="While the switch is closed the solenoid carries a steady current set by the battery and the series resistor; when the "
                 "switch opens that current keeps flowing through the second resistor and its magnetic energy is turned into heat. Find the "
                 "inductance, the current, then the stored energy.",
        steps=(
            Step("I0", "Ohm's law in the steady state, I0 = V / R1",
                 "In the steady state an ideal solenoid has no voltage across it, so the whole battery voltage drops over the series "
                 "resistor and the second resistor carries no current."),
            Step("L", "Inductance of a long air-cored solenoid, L = mu0 N^2 pi a^2 / ell",
                 "The solenoid is long, so its field is uniform inside; the flux linkage per unit current gives the inductance."),
            Step("E", "Energy stored in an inductor, E = L I0^2 / 2",
                 "After the switch opens the current decays through the second resistor, which dissipates all the stored magnetic energy "
                 "(the integral of I^2 R from the exponential decay gives L I0^2 / 2 whatever the resistance), so the heat equals the "
                 "energy stored at the moment of opening."),
        ),
        check="Dimensional check: henry times ampere squared is a joule. The heat does not depend on the value of the second resistor, "
              "which only sets how fast the current decays. Order of magnitude: millijoules for a few-millihenry coil at a few amperes."),
    "S269": Plan(
        approach="The pipe was tuned to the fork in cool air, which fixes its effective length; in warmer air the speed of sound is higher "
                 "and the fundamental of the same pipe rises. Find the speeds of sound, the effective length, the new frequency, then the "
                 "beat.",
        steps=(
            Step("c1", "Speed of sound in an ideal gas, c = c0 sqrt(T / T0)",
                 "The speed of sound in air is proportional to the square root of the absolute temperature; this is the speed when the "
                 "pipe is tuned."),
            Step("c2", "Speed of sound in an ideal gas, c = c0 sqrt(T / T0)",
                 "The same relation at the higher temperature of the air when the fork and the pipe sound together."),
            Step("Leff", "Fundamental of a pipe closed at one end, f = c / (4 Leff)",
                 "The closed pipe has a displacement node at the closed end and an antinode near the open end, so a quarter wavelength "
                 "fits in the effective length; tuning it to the fork gives that length."),
            Step("f2", "Fundamental of a pipe closed at one end, f = c / (4 Leff), with the length unchanged",
                 "The effective length does not change, so the fundamental in the warm air is the new speed divided by four lengths."),
            Step("beat", "Beat frequency of two close tones, f_beat = |f2 - f|",
                 "The fork and the pipe sound together, and two close frequencies beat at their difference; the pipe is sharper than the "
                 "fork because the air is warmer."),
        ),
        check="Limiting case: with no temperature rise the beat is zero. For a small rise the beat is about f dT / (2 T), which is about "
              "ten hertz for a 440 hertz fork and a rise of thirteen kelvin near 290 kelvin."),
    "S270": Plan(
        approach="Sound moves through the still air, so each Doppler shift depends on the speeds of the moving parties relative to the air. "
                 "The receding lorry first acts as an observer that moves away from the oncoming sound, then as a source that moves away from "
                 "the recorder, and the retreating recorder finally moves along with the reflected sound. Find the frequency at the lorry, "
                 "the frequency of the reflected sound, then the difference from the note.",
        steps=(
            Step("f1", "Doppler effect for a moving observer and a source at rest, f1 = f (c - w) / c",
                 "The lorry moves away from the post at w, in the direction of travel of the sound, so it meets the wave crests less "
                 "often than a lorry at rest would."),
            Step("f2", "Doppler effect for a receding source and an observer moving with the wave, f2 = f1 (c - v) / (c + w)",
                 "The lorry sends back the frequency f1 while it moves away from the recorder at w, which lengthens the wavelength to "
                 "(c + w) / f1, and the trolley retreats at v in the direction of travel of the reflected sound, so the observer term is "
                 "c - v."),
            Step("df", "Frequency difference, df = f - f2",
                 "The question asks how far the frequency of the reflected sound lies below the note; it is lower because the lorry and the "
                 "trolley both move away from the sources of the sound they receive."),
        ),
        check="Limiting cases: with the lorry and the trolley at rest the reflected sound has the frequency of the note and the difference "
              "is zero. For speeds that are small compared with the speed of sound the difference is about f (2 w + v) / c, so it grows "
              "with either speed and the lorry counts twice as much as the trolley."),
    "S271": Plan(
        approach="The rod vibrates like a bar with both ends free and a node at its middle, so a half wavelength of the longitudinal wave "
                 "in the rod fits its length; the rod then drives the air at that frequency and the dust marks half-wavelength intervals "
                 "of the sound in air. Find the wave speed in the rod, its vibration frequency, the wavelength in air, then the spacing.",
        steps=(
            Step("vr", "Speed of longitudinal waves in a thin rod, v = sqrt(Y / rho)",
                 "The rod is thin, so a longitudinal pulse travels at the square root of Young's modulus over the density."),
            Step("fr", "Fundamental longitudinal mode of a free-free rod clamped at its middle, f = v / (2 L)",
                 "The middle is a displacement node and the two free ends are antinodes, so the rod length is half a wavelength of the "
                 "longitudinal wave."),
            Step("lam", "Wavelength of a wave, lambda = c / f",
                 "The disc forces the air in the tube at the frequency of the rod, so the sound in the air has the speed of sound divided "
                 "by that frequency."),
            Step("d", "Adjacent nodes of a standing wave are half a wavelength apart, d = lambda / 2",
                 "The dust is shaken away from the displacement antinodes and collects at the nodes, which are half a wavelength apart."),
        ),
        check="Order of magnitude: aluminium carries sound at about five kilometres per second, so a rod of about a metre rings at a few "
              "kilohertz and the heaps are a few centimetres apart. The spacing is proportional to the rod length and independent of its "
              "cross-section."),
    "S272": Plan(
        approach="The air column resonates each time its length changes by half a wavelength of the fork. The water level falls at a steady "
                 "speed, so the time between resonances is that half wavelength divided by the speed of the level. Find the wavelength, the "
                 "fall of the level between resonances, then the time.",
        steps=(
            Step("lam", "Wavelength of a wave, lambda = c / f",
                 "The fork sets the frequency of the sound in the air column, which has the stated speed of sound."),
            Step("dh", "Resonances of a column closed at one end: lengths (2n - 1) lambda / 4 minus the end correction, spaced by lambda / 2",
                 "Successive resonances differ by an extra half wavelength in the column length, whatever the end correction."),
            Step("t", "Uniform motion, t = distance / speed",
                 "The water level falls at a constant speed, so the time between two resonances is the fall of the level between them "
                 "divided by that speed."),
        ),
        check="Limiting case: a faster fall (larger speed) shortens the interval in inverse proportion, and a lower frequency lengthens it "
              "in proportion. Order of magnitude: a half wavelength of a few tens of centimetres at a centimetre per second gives tens "
              "of seconds."),
}

LEVELS: dict[str, str] = {
    "S263": "intro_university", "S264": "upper_university", "S265": "upper_university", "S266": "upper_university",
    "S267": "upper_university", "S268": "intro_university", "S269": "intro_university", "S270": "upper_university",
    "S271": "upper_university", "S272": "intro_university",
}

TOPICS: dict[str, str] = {
    "S263": "metre bridge balance and the resistivity of a wire",
    "S264": "phasor analysis of a driven series RLC circuit and the phase angle",
    "S265": "full-wave bridge rectifier with diode forward drops and the average load voltage",
    "S266": "copper loss in the windings of a loaded transformer",
    "S267": "RC charging through a resistor divider (Thevenin equivalent) to a fraction of the final voltage",
    "S268": "energy of a solenoid dissipated in a discharge resistor",
    "S269": "organ pipe tuned to a fork, speed of sound and temperature, beats",
    "S270": "Doppler shift of an echo from a receding reflector heard by a moving observer",
    "S271": "longitudinal vibration of a clamped rod and standing waves in a Kundt's tube",
    "S272": "resonance of an air column closed at one end as the water level falls",
}
