"""M250 phase 2, batch em: ten new electromagnetism and circuits structures S211 to S220 for the M250 exploration pool.

Ten structures, each a genuinely new physical situation with its own symbolic program and an independently coded numeric solver:
the field inside a cavity of a uniformly charged ball (Gauss's law and superposition), power-factor correction of a motor (phasors),
the spot of an ion beam on a screen (deflection plates), the charge induced in a coil by a collapsing solenoid field (Faraday), the
first plateau of a pulse on a mismatched transmission line (reflection), the peak voltage when charge is passed between two capacitors
through an ideal inductor (LC transfer), a charged block driven up a rough incline by a horizontal field (forces with friction), the
force between the plates of a capacitor that stays on its battery (virtual work), the pitch of a helical path in a magnetic field, and
the force that draws a dielectric slab into a capacitor on a battery (energy method).

No problem needs a physical constant that is awkward to print: every numeral in a prompt is human-sized and is an input node, and no
numeral of the text is a literal (all numbers are nodes). Levels: five upper-university (S211, S212, S215, S216, S220), five
introductory; all ten have three or more relations. Each module-level structure has at least four numeric instantiations.

The module also holds a gold solution plan (`trace.Plan`) for each structure, with a course level and a topic string.

Admission status: agent-authored, solver-certified, not expert-reviewed. No human physicist has reviewed any of this text.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq

from physmon.benchmark.v2.graph import Assumption, Structure
from physmon.benchmark.v2.library import A_G, _co, _g, _in, _spec
from physmon.benchmark.v2.trace import Plan, Step

# --- solvers (independent routes; SI inputs in node order) -----------------------------------------------------------------


def _solve_cavity_bead(e0, radius, d, q0, m):
    # Superposition of two uniformly charged balls evaluated as vectors at a point of the cavity: the whole ball (field e0/R times the
    # position from its centre) and a ball of opposite charge density that fills the cavity (centre displaced by d).
    centre_ball = np.array([0.0, 0.0, 0.0])
    centre_cavity = np.array([d, 0.0, 0.0])
    point = np.array([d + 0.0131, 0.0071, -0.0043])
    field = (e0 / radius) * ((point - centre_ball) - (point - centre_cavity))
    return float(np.linalg.norm(q0 * field) / m)


def _solve_power_factor(r, ind, f):
    # The motor branch admittance 1/(R + j w L) plus the capacitor branch j w C: the capacitance at which the imaginary part of the
    # total admittance (the supply current's quadrature component) vanishes, found with a bracketing root finder.
    w = 2.0 * math.pi * f

    def quadrature(c):
        return (1.0 / complex(r, w * ind) + 1j * w * c).imag

    return float(brentq(quadrature, 0.0, 10.0, xtol=1e-16, rtol=1e-14))


def _solve_ion_spot(va, vd, ell, gap, dist):
    # Integrate an ion of arbitrary specific charge: first through a one-metre accelerating gap, then through the plates, then along
    # the straight drift; the specific charge cancels.
    qm = 5.0e6
    length = 1.0

    def exit_gap(t, y):
        return y[0] - length

    exit_gap.terminal = True
    stage1 = solve_ivp(lambda t, y: [y[1], qm * va / length], (0.0, 10.0), [0.0, 0.0], events=exit_gap, rtol=1e-12, atol=1e-14)
    speed = float(stage1.y_events[0][0][1])
    t_plates = ell / speed
    stage2 = solve_ivp(lambda t, y: [y[1], qm * vd / gap], (0.0, t_plates), [0.0, 0.0], rtol=1e-12, atol=1e-14)
    y_exit, vy = float(stage2.y[0][-1]), float(stage2.y[1][-1])
    return float(y_exit + vy * dist / speed)


def _solve_induced_charge(b0, rc, n, r):
    # Integrate the current i = emf / R over a one-second ramp, with the emf found from a numerical time derivative of the flux
    # linkage; the ramp time cancels.
    ramp = 1.0
    area = math.pi * rc * rc

    def linkage(t):
        return n * area * b0 * (1.0 - t / ramp)

    h = 1.0e-4

    def charge_rate(t, y):
        emf = -(linkage(t + h) - linkage(t - h)) / (2.0 * h)
        return [emf / r]

    solution = solve_ivp(charge_rate, (0.0, ramp), [0.0], rtol=1e-11, atol=1e-14)
    return float(solution.y[0][-1])


def _solve_line_load(l_tot, c_tot, vs, rs, rl):
    # Telegrapher's equations for a lossless line of an arbitrary length (one metre): the characteristic impedance from the per-metre
    # parameters, the launched wave from the source-end loop equation, and the load-end boundary condition, each solved as a small
    # linear system for the wave amplitudes.
    z0 = math.sqrt((l_tot / 1.0) / (c_tot / 1.0))
    # source end at t = 0+: unknowns (V, I): V + Rs I = Vs and V - Z0 I = 0 (no backward wave yet)
    v_launch, _ = np.linalg.solve(np.array([[1.0, rs], [1.0, -z0]]), np.array([vs, 0.0]))
    # load end: unknowns (V_L, I_L, V_b) with V_L = V_f + V_b, Z0 I_L = V_f - V_b and V_L = R_L I_L
    matrix = np.array([[1.0, 0.0, -1.0], [0.0, z0, 1.0], [1.0, -rl, 0.0]])
    v_load, _, _ = np.linalg.solve(matrix, np.array([v_launch, v_launch, 0.0]))
    return float(v_load)


def _solve_lc_transfer(c1, c2, v0, v2):
    # Integrate the loop equation of the ideal circuit for the charge on the second capacitor, with an arbitrary inductance (it sets
    # only the time scale), and take the largest voltage on it over one and a half periods.
    ind = 0.37
    q_total = c1 * v0 + c2 * v2
    omega = math.sqrt((c1 + c2) / (ind * c1 * c2))
    period = 2.0 * math.pi / omega
    times = np.linspace(0.0, 1.5 * period, 300001)
    solution = solve_ivp(lambda t, y: [y[1], ((q_total - y[0]) / c1 - y[0] / c2) / ind], (0.0, 1.5 * period), [c2 * v2, 0.0],
                         t_eval=times, rtol=1e-12, atol=1e-18)
    return float(np.max(solution.y[0]) / c2)


def _solve_block_on_incline(m, qb, e_field, theta, mu, s, g):
    # Vector route: the weight and the electric force as vectors, resolved along and normal to the slope; the equation of motion
    # is integrated until the block has slid the distance s.
    weight = np.array([0.0, -m * g])
    electric = np.array([qb * e_field, 0.0])
    along = np.array([math.cos(theta), math.sin(theta)])
    normal = np.array([-math.sin(theta), math.cos(theta)])
    total = weight + electric
    normal_force = -float(total @ normal)
    net = float(total @ along) - mu * normal_force

    def reach(t, y):
        return y[0] - s

    reach.terminal = True
    solution = solve_ivp(lambda t, y: [y[1], net / m], (0.0, 100.0), [0.0, 0.0], events=reach, rtol=1e-12, atol=1e-14)
    return float(solution.y_events[0][0][1])


def _solve_plate_force(c0, d0, d1, volt):
    # Virtual work at constant voltage: the force is one half V squared times the magnitude of dC/dd, with C(d) = C0 d0 / d
    # differentiated numerically at the final separation.
    h = 1.0e-6 * d1

    def cap(d):
        return c0 * d0 / d

    slope = (cap(d1 + h) - cap(d1 - h)) / (2.0 * h)
    return float(0.5 * volt * volt * abs(slope))


def _solve_helix_pitch(m, qc, b, vpar):
    # Integrate the Lorentz force in three dimensions for a bead with an arbitrary perpendicular speed and read the advance along
    # the field at the second time that the transverse velocity component vanishes (one full turn).
    vperp = 3.0

    def rhs(t, y):
        omega = qc * b / m
        return [y[3], y[4], y[5], omega * y[4], -omega * y[3], 0.0]

    def halfturn(t, y):
        return y[4]

    halfturn.terminal = False
    estimate = 2.0 * math.pi * m / (qc * b)
    solution = solve_ivp(rhs, (0.0, 1.6 * estimate), [0.0, 0.0, 0.0, vperp, 0.0, vpar], events=halfturn, rtol=1e-12, atol=1e-14,
                         dense_output=True)
    times = [float(t) for t in solution.t_events[0] if t > 1e-9]
    return float(solution.sol(times[1])[2])


def _solve_slab_force(c0, kappa, ell, volt):
    # Energy method: the capacitance of the part-filled capacitor as a function of the inserted length, differentiated numerically
    # at an arbitrary insertion, then F = (1/2) V^2 dC/dx.
    def cap(x):
        return c0 * (1.0 + (kappa - 1.0) * x / ell)

    x0, h = 0.37 * ell, 1.0e-4 * ell
    return float(0.5 * volt * volt * (cap(x0 + h) - cap(x0 - h)) / (2.0 * h))


# --- structures ------------------------------------------------------------------------------------------------------------


def s211_cavity_bead_acceleration() -> Structure:
    return Structure(
        "S211", "Acceleration of a bead released in the cavity of a charged ball", "electromagnetism", "uniform_field_in_offset_cavity",
        (_in("E0", "electric_field", "kV/m", "field magnitude at the surface of the ball before the cavity was cut", 40.0, (10.0, 100.0)),
         _in("R", "length", "cm", "radius of the ball", 20.0, (10.0, 40.0)),
         _in("d", "length", "cm", "distance from the centre of the ball to the centre of the cavity", 6.0, (2.0, 9.0)),
         _in("q0", "charge", "μC", "charge of the bead", 2.0, (0.5, 5.0)),
         _in("m", "mass", "g", "mass of the bead", 0.5, (0.2, 2.0)),
         _co("Ecav", "electric_field", "kV/m", "field in the cavity", "E0*d/R"),
         _co("F", "force", "mN", "electric force on the bead", "q0*Ecav"),
         _co("a", "acceleration", "m/s^2", "initial acceleration of the bead", "F/m")),
        "a",
        (Assumption("A-fixed", "The ball is an insulator whose remaining charge stays fixed where it was, spread uniformly through the "
                               "solid material; the bead is small enough not to disturb that charge.", "modelling", ("E0", "R")),
         Assumption("A-cavity", "The cavity is spherical, empty and wholly inside the ball.", "boundary_condition", ("d",)),
         Assumption("A-gravity", "Gravity is neglected and the bead is released from rest.", "boundary_condition", ("q0", "m"))),
        _spec("A solid insulating ball of radius {R} cm carries electric charge fixed in its material and spread uniformly through its "
              "volume. Before anything is removed, the electric field at its surface has a magnitude of {E0} kV/m. A spherical cavity is "
              "then hollowed out of the ball, wholly inside it, with its centre {d} cm from the centre of the ball; the charge of the "
              "remaining material stays where it was and the cavity is empty. A small bead of mass {m} g and charge {q0} μC, small enough "
              "not to disturb the charge of the ball, is released from rest at a point inside the cavity. Neglect gravity.",
              "What is the magnitude of the initial acceleration of the bead?", "initial acceleration of the bead", "m/s^2",
              "A separate bead B in another experiment accelerates at {v} {u}, but it is unrelated to this ball.",
              "A reference bead B accelerates at {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the motion of the bead.", "W", equivalent="cm/s^2"),
        ("d", 1.5), _solve_cavity_bead, 5,
        "superposition of two uniformly charged balls, the whole ball and a ball of opposite charge density in the cavity, evaluated as "
        "vectors at a point of the cavity",
        solver_rel_tol=1e-9,
        instances=({"E0": 40.0, "R": 20.0, "d": 6.0, "q0": 2.0, "m": 0.5}, {"E0": 25.0, "R": 15.0, "d": 5.0, "q0": 3.0, "m": 0.8},
                   {"E0": 60.0, "R": 30.0, "d": 8.0, "q0": 1.5, "m": 0.4}, {"E0": 35.0, "R": 24.0, "d": 9.0, "q0": 4.0, "m": 1.2}))


def s212_power_factor_capacitor() -> Structure:
    return Structure(
        "S212", "Capacitor that makes a motor's supply current in phase with the voltage", "electromagnetism",
        "parallel_capacitor_unity_power_factor",
        (_in("R", "resistance", "Ω", "resistance of the motor winding", 10.0, (4.0, 30.0)),
         _in("L", "inductance", "mH", "inductance of the motor winding", 50.0, (20.0, 120.0)),
         _in("f", "frequency", "Hz", "frequency of the supply", 50.0, (40.0, 120.0)),
         _co("XL", "resistance", "Ω", "reactance of the winding", "2*pi*f*L"),
         _co("Zmag", "resistance", "Ω", "magnitude of the impedance of the motor", "sqrt(R**2 + XL**2)"),
         _co("C", "capacitance", "μF", "capacitance that cancels the quadrature current", "XL/(2*pi*f*Zmag**2)")),
        "C",
        (Assumption("A-motor", "The motor is a resistor in series with an inductor of the stated values, and its impedance does not "
                               "depend on the capacitor.", "modelling", ("R", "L")),
         Assumption("A-supply", "The supply is an ideal sinusoidal voltage source of the stated frequency and the capacitor is ideal.",
                    "modelling", ("f",))),
        _spec("A motor is modelled as a resistor of {R} Ω in series with a coil of inductance {L} mH. It is connected to an ideal "
              "sinusoidal supply of frequency {f} Hz, and an ideal capacitor is connected across the supply terminals, in parallel with the "
              "motor. The currents are in the steady state.",
              "What capacitance makes the current drawn from the supply in phase with the supply voltage?",
              "capacitance that puts the supply current in phase with the voltage", "μF",
              "A separate capacitor B on another board has a capacitance of {v} {u}, but it is unrelated to this motor.",
              "A reference capacitor B has a capacitance of {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the circuit.", "W", equivalent="mF"),
        ("L", 1.5), _solve_power_factor, 3,
        "the complex admittance of the motor branch plus the capacitor branch, with the capacitance at which its imaginary part "
        "vanishes found by a bracketing root finder",
        solver_rel_tol=1e-9,
        instances=({"R": 10.0, "L": 50.0, "f": 50.0}, {"R": 8.0, "L": 40.0, "f": 60.0}, {"R": 15.0, "L": 80.0, "f": 50.0},
                   {"R": 6.0, "L": 30.0, "f": 100.0}))


def s213_ion_beam_spot() -> Structure:
    return Structure(
        "S213", "Displacement of an ion beam's spot on a screen after deflecting plates", "electromagnetism",
        "accelerated_ion_plate_deflection_on_screen",
        (_in("Va", "voltage", "V", "accelerating potential difference", 2000.0, (500.0, 5000.0)),
         _in("Vd", "voltage", "V", "potential difference across the deflecting plates", 100.0, (40.0, 300.0)),
         _in("ell", "length", "cm", "length of the deflecting plates", 5.0, (3.0, 8.0)),
         _in("d", "length", "cm", "separation of the deflecting plates", 1.0, (0.6, 2.0)),
         _in("L", "length", "cm", "distance from the ends of the plates to the screen", 30.0, (15.0, 50.0)),
         _co("tanth", "ratio", "1", "tangent of the deflection angle on leaving the plates", "Vd*ell/(2*d*Va)"),
         _co("yexit", "length", "cm", "sideways displacement on leaving the plates", "tanth*ell/2"),
         _co("ysc", "length", "cm", "displacement of the spot from the undeflected position", "yexit + tanth*L")),
        "ysc",
        (Assumption("A-ions", "The ions all have the same charge and mass, start from rest, and move non-relativistically in a vacuum.",
                    "modelling", ("Va",)),
         Assumption("A-field", "The field between the plates is uniform and perpendicular to the beam, and zero outside the plates; the "
                               "ions enter midway between the plates, parallel to them, and leave without striking them.",
                    "boundary_condition", ("Vd", "ell", "d")),
         Assumption("A-drift", "Beyond the plates the ions move in a straight line to the screen; gravity is neglected.", "modelling",
                    ("L",))),
        _spec("Positive ions of one kind, all with the same charge, are accelerated from rest through a potential difference of {Va} V "
              "in an evacuated tube. They then enter, midway between and parallel to two flat deflecting plates {ell} cm long and {d} cm "
              "apart, with a potential difference of {Vd} V across the plates; the field between the plates is uniform and there is none "
              "outside them, and the ions leave the plates without striking them. The ions then travel in a straight line to a screen "
              "{L} cm beyond the ends of the plates. Neglect gravity.",
              "How far from the undeflected position do the ions strike the screen?", "displacement of the spot on the screen", "cm",
              "A separate beam B in another tube strikes its screen {v} {u} from the centre, but it is unrelated to this tube.",
              "A reference beam B strikes its screen {v} {u} from the centre.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the deflection.", "W", equivalent="mm"),
        ("Vd", 1.5), _solve_ion_spot, 5,
        "a time-stepped integration of an ion of arbitrary specific charge through the accelerating gap, the plates and the drift",
        solver_rel_tol=1e-7,
        instances=({"Va": 2000.0, "Vd": 100.0, "ell": 5.0, "d": 1.0, "L": 30.0}, {"Va": 1500.0, "Vd": 80.0, "ell": 6.0, "d": 1.2, "L": 25.0},
                   {"Va": 3000.0, "Vd": 200.0, "ell": 4.0, "d": 0.8, "L": 40.0}, {"Va": 2500.0, "Vd": 150.0, "ell": 7.0, "d": 1.5, "L": 20.0}))


def s214_induced_charge() -> Structure:
    return Structure(
        "S214", "Charge driven round a coil by a collapsing solenoid field", "electromagnetism", "faraday_induced_charge_in_coil",
        (_in("B0", "magnetic_field", "mT", "initial field strength inside the solenoid", 80.0, (20.0, 200.0)),
         _in("rc", "length", "cm", "radius of the coil", 3.0, (1.5, 5.0)),
         _in("N", "count", "1", "number of turns of the coil", 200.0, (50.0, 500.0)),
         _in("R", "resistance", "Ω", "resistance of the coil circuit", 12.0, (5.0, 40.0)),
         _co("A", "area", "cm^2", "area enclosed by one turn", "pi*rc**2"),
         _co("Phi", "magnetic_flux", "mWb", "change of flux through one turn", "B0*A"),
         _co("Q", "charge", "mC", "total charge that flows through the coil", "N*Phi/R")),
        "Q",
        (Assumption("A-field", "The field inside the solenoid is uniform and parallel to the axis, and zero outside it; the coil is "
                               "coaxial with the solenoid and lies entirely inside it.", "boundary_condition", ("B0", "rc")),
         Assumption("A-coil", "The self-inductance of the coil is negligible and its resistance is constant.", "modelling",
                    ("N", "R"))),
        _spec("The magnetic field inside a long solenoid is uniform, parallel to the axis of the solenoid, and zero outside it. A "
              "circular coil of {N} turns and radius {rc} cm lies entirely inside the solenoid, coaxial with it, with its plane "
              "perpendicular to the axis; the circuit of the coil, with the wires that close it, has a resistance of {R} Ω, and its self-inductance is "
              "negligible. The current in the solenoid is switched off, and the field inside it falls steadily from {B0} mT to zero.",
              "What total charge flows round the coil circuit while the field falls to zero?", "total charge that flows round the coil",
              "mC",
              "A separate capacitor B on another bench holds a charge of {v} {u}, but it is unrelated to this coil.",
              "A reference coil B passes a charge of {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the induction.", "W", equivalent="μC"),
        ("B0", 1.5), _solve_induced_charge, 4,
        "the current integrated over a ramp of arbitrary duration, with the emf from a numerical time derivative of the flux linkage",
        solver_rel_tol=1e-7,
        instances=({"B0": 80.0, "rc": 3.0, "N": 200.0, "R": 12.0}, {"B0": 50.0, "rc": 2.0, "N": 300.0, "R": 8.0},
                   {"B0": 120.0, "rc": 4.0, "N": 150.0, "R": 20.0}, {"B0": 60.0, "rc": 2.5, "N": 400.0, "R": 15.0}))


def s215_transmission_line_load_voltage() -> Structure:
    return Structure(
        "S215", "Load voltage during the first plateau of a pulse on a mismatched line", "electromagnetism",
        "transmission_line_first_arrival_load_voltage",
        (_in("Ltot", "inductance", "mH", "total inductance of the cable", 0.025, (0.01, 0.1)),
         _in("Ctot", "capacitance", "nF", "total capacitance of the cable", 10.0, (2.0, 20.0)),
         _in("Vs", "voltage", "V", "emf of the source", 10.0, (5.0, 30.0)),
         _in("Rs", "resistance", "Ω", "internal resistance of the source", 25.0, (10.0, 100.0)),
         _in("RL", "resistance", "Ω", "resistance of the load", 150.0, (20.0, 500.0)),
         _co("Z0", "resistance", "Ω", "characteristic impedance of the cable", "sqrt(Ltot/Ctot)"),
         _co("Vinc", "voltage", "V", "voltage of the wave launched into the cable", "Vs*Z0/(Rs + Z0)"),
         _co("Gam", "ratio", "1", "reflection coefficient at the load", "(RL - Z0)/(RL + Z0)"),
         _co("VL", "voltage", "V", "voltage across the load after the first arrival", "Vinc*(1 + Gam)")),
        "VL",
        (Assumption("A-lossless", "The cable is lossless, with inductance and capacitance spread uniformly along it; its length does "
                                  "not enter the answer.", "modelling", ("Ltot", "Ctot")),
         Assumption("A-step", "The source is switched on as an ideal step at time zero onto a cable that is initially uncharged and "
                              "carries no current; the answer is the load voltage once the first wavefront has arrived and before "
                              "any wave reflected at the source end returns.", "boundary_condition", ("Vs", "Rs", "RL"))),
        _spec("A lossless cable has a total inductance of {Ltot} mH and a total capacitance of {Ctot} nF. At one end a source of emf "
              "{Vs} V and internal resistance {Rs} Ω is switched on at time zero, when the cable is uncharged and carries no current. "
              "The far end of the cable is connected to a load resistor of {RL} Ω.",
              "What is the voltage across the load just after the first wavefront reaches it, before any wave reflected at the source "
              "end has returned to the load?", "voltage across the load after the first arrival", "V",
              "A separate battery B in another circuit supplies {v} {u}, but it is unrelated to this cable.",
              "A reference load B has {v} {u} across it.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the pulse.", "W", equivalent="mV"),
        ("RL", 1.5), _solve_line_load, 5,
        "the telegrapher's equations for a lossless line, with the launched wave from the source-end loop equation and the load-end "
        "boundary condition each solved as a small linear system",
        solver_rel_tol=1e-9,
        instances=({"Ltot": 0.025, "Ctot": 10.0, "Vs": 10.0, "Rs": 25.0, "RL": 150.0},
                   {"Ltot": 0.04, "Ctot": 8.0, "Vs": 12.0, "Rs": 20.0, "RL": 100.0},
                   {"Ltot": 0.02, "Ctot": 16.0, "Vs": 20.0, "Rs": 40.0, "RL": 300.0},
                   {"Ltot": 0.05, "Ctot": 5.0, "Vs": 15.0, "Rs": 50.0, "RL": 60.0}))


def s216_lc_transfer_peak_voltage() -> Structure:
    return Structure(
        "S216", "Largest voltage on a precharged capacitor joined through an ideal inductor", "electromagnetism",
        "lc_charge_sharing_overshoot_voltage",
        (_in("C1", "capacitance", "μF", "capacitance of the first capacitor", 40.0, (10.0, 100.0)),
         _in("C2", "capacitance", "μF", "capacitance of the second capacitor", 10.0, (5.0, 60.0)),
         _in("V0", "voltage", "V", "initial voltage of the first capacitor", 100.0, (60.0, 300.0)),
         _in("V2", "voltage", "V", "initial voltage of the second capacitor", 20.0, (5.0, 40.0)),
         _co("Q0", "charge", "μC", "total charge on the two joined plates", "C1*V0 + C2*V2"),
         _co("Veq", "voltage", "V", "common voltage at which the capacitors would balance", "Q0/(C1 + C2)"),
         _co("Vmax", "voltage", "V", "largest voltage across the second capacitor", "2*Veq - V2")),
        "Vmax",
        (Assumption("A-ideal", "The inductor and the wires have no resistance and the capacitors are ideal, so the oscillation "
                               "continues without loss.", "modelling", ("C1", "C2")),
         Assumption("A-start", "The capacitors are joined with their positive plates together, so the charges on the joined plates "
                               "add, and there is no current in the inductor when the switch closes.", "boundary_condition",
                    ("V0", "V2"))),
        _spec("A capacitor of {C1} μF is charged to {V0} V, and a second capacitor of {C2} μF is charged to {V2} V. The capacitors are "
              "connected, with their positive plates joined, through an ideal inductor and a switch, with no resistance anywhere in "
              "the circuit. The switch is closed at time zero, when there is no current in the inductor.",
              "What is the largest voltage that ever appears across the second capacitor?", "largest voltage across the second "
              "capacitor", "V",
              "A separate capacitor B on another board is charged to {v} {u}, but it is unrelated to this circuit.",
              "A reference capacitor B is charged to {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the oscillation.", "W", equivalent="mV"),
        ("C2", 1.5), _solve_lc_transfer, 4,
        "the loop equation of the lossless circuit integrated in time for the charge on the second capacitor, taking the largest "
        "voltage reached",
        solver_rel_tol=1e-6,
        instances=({"C1": 40.0, "C2": 10.0, "V0": 100.0, "V2": 20.0}, {"C1": 25.0, "C2": 25.0, "V0": 80.0, "V2": 15.0},
                   {"C1": 60.0, "C2": 15.0, "V0": 150.0, "V2": 30.0}, {"C1": 30.0, "C2": 45.0, "V0": 200.0, "V2": 10.0}))


def s217_charged_block_on_incline() -> Structure:
    return Structure(
        "S217", "Speed of a charged block driven up a rough incline by a horizontal field", "electromagnetism",
        "charged_block_incline_horizontal_field_friction",
        (_in("m", "mass", "kg", "mass of the block", 0.5, (0.35, 0.65)),
         _in("qb", "charge", "μC", "charge of the block", 30.0, (25.0, 35.0)),
         _in("E", "electric_field", "kV/m", "magnitude of the horizontal field", 600.0, (500.0, 700.0)),
         _in("theta", "angle", "deg", "angle of the incline above the horizontal", 25.0, (15.0, 30.0)),
         _in("mu", "coefficient", "1", "coefficient of kinetic friction", 0.2, (0.05, 0.25)),
         _in("s", "length", "m", "distance slid up the incline", 0.8, (0.5, 1.5)),
         _g(),
         _co("Nn", "force", "N", "normal force of the incline on the block", "m*g*cos(theta) + qb*E*sin(theta)"),
         _co("Fd", "force", "N", "component of weight and electric force along the slope, up the slope positive",
             "qb*E*cos(theta) - m*g*sin(theta)"),
         _co("Ff", "force", "N", "kinetic friction force", "mu*Nn"),
         _co("acc", "acceleration", "m/s^2", "acceleration up the slope", "(Fd - Ff)/m"),
         _co("v", "speed", "m/s", "speed after sliding the distance", "sqrt(2*acc*s)")),
        "v",
        (A_G, Assumption("A-incline", "The incline is fixed and insulating, so the block keeps its charge; the field is uniform and "
                                      "horizontal and lies in the vertical plane that contains the line of the slope.",
                         "boundary_condition", ("E", "theta")),
         Assumption("A-motion", "The block is at rest at the foot of the incline when the field is switched on, and it slides up the "
                                "slope at once; its size is negligible.", "boundary_condition", ("s", "mu"))),
        _spec("A small block of mass {m} kg carries a charge of {qb} μC. It rests at the foot of a fixed insulating incline that "
              "rises at {theta}° above the horizontal; the coefficient of kinetic friction between the block and the incline is {mu}. "
              "A uniform horizontal electric field of magnitude {E} kV/m, pointing in the horizontal direction in which the incline "
              "rises, is switched on, and the block begins to slide up the slope. Neglect air resistance. Take g = {g} m/s².",
              "How fast is the block moving once it has slid {s} m up the slope?", "speed of the block", "m/s",
              "A separate cart B on another track moves at {v} {u}, but it never interacts with this block.",
              "A reference cart B moves at {v} {u}.",
              "A separate heater B is rated at {v} {u}, but it plays no part in the motion.", "W", equivalent="km/h"),
        ("E", 0.85), _solve_block_on_incline, 7,
        "the weight and the electric force as vectors resolved along and normal to the slope, with the equation of motion integrated "
        "until the block has slid the distance",
        solver_rel_tol=1e-7,
        instances=({"m": 0.5, "qb": 30.0, "E": 600.0, "theta": 25.0, "mu": 0.2, "s": 0.8, "g": 9.8},
                   {"m": 0.4, "qb": 25.0, "E": 500.0, "theta": 20.0, "mu": 0.15, "s": 1.0, "g": 9.8},
                   {"m": 0.6, "qb": 35.0, "E": 700.0, "theta": 28.0, "mu": 0.1, "s": 1.2, "g": 9.8},
                   {"m": 0.45, "qb": 28.0, "E": 550.0, "theta": 18.0, "mu": 0.25, "s": 0.6, "g": 9.8}))


def s218_capacitor_plate_force() -> Structure:
    return Structure(
        "S218", "Force between the plates of a capacitor pulled apart on its battery", "electromagnetism",
        "constant_voltage_plate_attraction_after_separation",
        (_in("C0", "capacitance", "pF", "capacitance at the first separation", 100.0, (50.0, 300.0)),
         _in("d0", "length", "mm", "first separation of the plates", 2.0, (1.0, 3.0)),
         _in("d1", "length", "mm", "final separation of the plates", 5.0, (3.5, 8.0)),
         _in("V", "voltage", "V", "emf of the battery", 900.0, (300.0, 1500.0)),
         _co("C1", "capacitance", "pF", "capacitance at the final separation", "C0*d0/d1"),
         _co("Qc", "charge", "nC", "charge on the plates at the final separation", "C1*V"),
         _co("E1", "electric_field", "kV/m", "field between the plates at the final separation", "V/d1"),
         _co("F", "force", "mN", "force that one plate exerts on the other", "Qc*E1/2")),
        "F",
        (Assumption("A-battery", "The battery stays connected, so the voltage across the plates is the emf at every separation; the "
                                 "battery is ideal.", "boundary_condition", ("V",)),
         Assumption("A-parallel", "The plates stay flat and parallel and the gap is air taken as a vacuum; edge effects are neglected, "
                                  "so the capacitance is inversely proportional to the separation.", "modelling", ("C0", "d0", "d1"))),
        _spec("The plates of an air-filled parallel-plate capacitor are {d0} mm apart, and the capacitance is {C0} pF. The capacitor is "
              "connected to an ideal battery of emf {V} V and stays connected, and the plates are slowly pulled apart, staying parallel, "
              "until they are {d1} mm apart. Treat the air as a vacuum and neglect edge effects.",
              "What is the magnitude of the electrostatic force that one plate exerts on the other at the final separation?",
              "force between the plates at the final separation", "mN",
              "A separate spring B in another apparatus exerts a force of {v} {u}, but it is unrelated to this capacitor.",
              "A reference capacitor B has plates that attract with a force of {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the attraction.", "W", equivalent="N"),
        ("d1", 0.8), _solve_plate_force, 4,
        "virtual work at constant voltage: one half V squared times the magnitude of dC/dd, with the capacitance as a function of the "
        "separation differentiated numerically",
        solver_rel_tol=1e-7,
        instances=({"C0": 100.0, "d0": 2.0, "d1": 5.0, "V": 900.0}, {"C0": 80.0, "d0": 1.5, "d1": 4.0, "V": 600.0},
                   {"C0": 150.0, "d0": 2.5, "d1": 6.0, "V": 1200.0}, {"C0": 60.0, "d0": 1.0, "d1": 4.5, "V": 800.0}))


def s219_helix_pitch() -> Structure:
    return Structure(
        "S219", "Pitch of the helical path of a charged bead in a magnetic field", "electromagnetism",
        "helical_pitch_from_cyclotron_period",
        (_in("m", "mass", "g", "mass of the bead", 0.5, (0.2, 2.0)),
         _in("qc", "charge", "mC", "charge of the bead", 5.0, (2.0, 8.0)),
         _in("B", "magnetic_field", "T", "magnetic field strength", 0.8, (0.3, 1.5)),
         _in("vpar", "speed", "m/s", "component of the velocity along the field", 12.0, (5.0, 30.0)),
         _co("wc", "angular_frequency", "rad/s", "angular frequency of the circling", "qc*B/m"),
         _co("T", "time", "s", "time for one complete turn", "2*pi/wc"),
         _co("p", "length", "m", "pitch of the helix", "vpar*T")),
        "p",
        (Assumption("A-field", "The magnetic field is uniform and is the only force on the bead; the motion is non-relativistic and "
                               "gravity and radiation are neglected.", "modelling", ("m", "qc", "B")),
         Assumption("A-velocity", "The component of the velocity perpendicular to the field is not zero, so the path is a helix; the "
                                  "component along the field is constant.", "boundary_condition", ("vpar",))),
        _spec("A small bead of mass {m} g carrying a charge of {qc} mC moves in a vacuum through a uniform magnetic field of {B} T and "
              "is acted on by no other force. Its velocity has a component of {vpar} m/s along the field and a non-zero component "
              "perpendicular to it, so the bead follows a helix. Neglect gravity.",
              "What is the pitch of the helix, the distance that the bead advances along the field in one complete turn?",
              "pitch of the helix", "m",
              "A separate screw B on another bench advances {v} {u} per turn, but it is unrelated to this bead.",
              "A reference helix B has a pitch of {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the motion.", "W", equivalent="cm"),
        ("m", 1.5), _solve_helix_pitch, 4,
        "a three-dimensional integration of the Lorentz force for a bead of arbitrary perpendicular speed, reading the advance along "
        "the field at the second zero of the transverse velocity",
        solver_rel_tol=1e-7,
        instances=({"m": 0.5, "qc": 5.0, "B": 0.8, "vpar": 12.0}, {"m": 0.8, "qc": 4.0, "B": 0.6, "vpar": 8.0},
                   {"m": 0.3, "qc": 6.0, "B": 1.0, "vpar": 20.0}, {"m": 1.2, "qc": 3.0, "B": 0.5, "vpar": 15.0}))


def s220_dielectric_slab_force() -> Structure:
    return Structure(
        "S220", "Force that draws a dielectric slab into a capacitor on its battery", "electromagnetism",
        "dielectric_slab_force_constant_voltage_virtual_work",
        (_in("C0", "capacitance", "pF", "capacitance of the empty capacitor", 200.0, (100.0, 400.0)),
         _in("kappa", "coefficient", "1", "dielectric constant of the slab", 4.0, (2.0, 8.0)),
         _in("ell", "length", "cm", "length of the plates, along which the slab slides", 10.0, (6.0, 20.0)),
         _in("V", "voltage", "V", "emf of the battery", 500.0, (200.0, 1000.0)),
         _co("Cfull", "capacitance", "pF", "capacitance with the slab fully inside", "kappa*C0"),
         _co("dC", "capacitance", "pF", "gain of capacitance from empty to full", "Cfull - C0"),
         _co("dCdx", "capacitance_per_length", "F/m", "rate of increase of capacitance with inserted length", "dC/ell"),
         _co("F", "force", "mN", "electric force drawing the slab in", "V**2*dCdx/2")),
        "F",
        (Assumption("A-battery", "The battery is ideal and stays connected, so the voltage across the plates is the emf.",
                    "boundary_condition", ("V",)),
         Assumption("A-slab", "The slab has the width of the plates, fills the gap between them and is partly inserted, away from "
                              "both ends of the plates, so that the capacitance rises linearly with the inserted length; fringe "
                              "fields and friction are neglected.", "modelling", ("C0", "kappa", "ell"))),
        _spec("An air-filled parallel-plate capacitor has a capacitance of {C0} pF, and its plates are {ell} cm long. A slab of "
              "linear dielectric of constant {kappa}, with the same width as the plates and thickness equal to their separation, is partly "
              "inserted between them, entering along their length and well away from both ends of the plates. The capacitor is "
              "connected to an ideal battery of emf {V} V and stays connected. Treat the air as a vacuum. Neglect fringe fields and friction.",
              "What is the magnitude of the electric force that draws the slab into the capacitor?",
              "electric force that draws the slab in", "mN",
              "A separate magnet B in another apparatus pulls with a force of {v} {u}, but it is unrelated to this slab.",
              "A reference slab B is drawn in by a force of {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the attraction.", "W", equivalent="N"),
        ("kappa", 1.5), _solve_slab_force, 4,
        "the energy method: the capacitance of the part-filled capacitor as a function of the inserted length, differentiated "
        "numerically at an arbitrary insertion, then one half V squared times dC/dx",
        solver_rel_tol=1e-7,
        instances=({"C0": 200.0, "kappa": 4.0, "ell": 10.0, "V": 500.0}, {"C0": 150.0, "kappa": 3.0, "ell": 8.0, "V": 400.0},
                   {"C0": 300.0, "kappa": 5.0, "ell": 15.0, "V": 700.0}, {"C0": 120.0, "kappa": 6.0, "ell": 12.0, "V": 300.0}))


ALL = (s211_cavity_bead_acceleration, s212_power_factor_capacitor, s213_ion_beam_spot, s214_induced_charge,
       s215_transmission_line_load_voltage, s216_lc_transfer_peak_voltage, s217_charged_block_on_incline, s218_capacitor_plate_force,
       s219_helix_pitch, s220_dielectric_slab_force)


def all_structures() -> list[Structure]:
    return [factory() for factory in ALL]


STRUCTURES: dict[str, Structure] = {s.structure_id: s for s in all_structures()}

# --- gold solution plans ---------------------------------------------------------------------------------------------------

PLANS: dict[str, Plan] = {
    "S211": Plan(
        approach="Treat the ball with the cavity as a whole ball of uniform charge density plus a ball of opposite charge density that "
                 "fills the cavity. Inside a uniformly charged ball the field grows in proportion to the distance from its centre, "
                 "so the two fields subtract to a uniform field in the cavity, which gives the force and then the acceleration.",
        steps=(
            Step("Ecav", "Superposition with Gauss's law for a uniformly charged ball: inside the ball the field is E(r) = E_surface "
                         "r/R, directed away from the centre, so the whole ball gives E0 r1/R and the cavity ball of opposite "
                         "charge gives -E0 r2/R",
                 "At a point of the cavity the two position vectors differ by the vector from the ball's centre to the cavity's "
                 "centre, so the fields add to E0 d/R, the same everywhere in the cavity and pointing along the line of centres."),
            Step("F", "Electric force on a charge: F = q E for a charge in an electric field",
                 "The field in the cavity is uniform and the bead is small, so the force on it is its charge times that field."),
            Step("a", "Newton's second law: acceleration = force / mass, with gravity neglected",
                 "The electric force is the only force on the bead, so dividing it by the mass gives the initial acceleration."),
        ),
        check="If the cavity were centred on the ball (d = 0) the field in it must vanish, and the formula gives zero; the field "
              "must grow in proportion to d, and the point of release inside the cavity cannot matter because the field is uniform."),
    "S212": Plan(
        approach="The supply current is in phase with the voltage when the total admittance is purely real. The motor branch has an inductive part to its admittance, and the capacitor must supply an equal and opposite susceptance.",
        steps=(
            Step("XL", "Inductive reactance: X_L = omega L = 2 pi f L",
                 "The coil's reactance at the supply frequency sets the quadrature part of the motor's impedance."),
            Step("Zmag", "Magnitude of a series R-L impedance: |Z| = sqrt(R^2 + X_L^2)",
                 "The resistance and reactance are in quadrature, so the impedance magnitude is their root sum of squares, which "
                 "gives the admittance Y = 1/(R + j X_L) = (R - j X_L)/|Z|^2."),
            Step("C", "Condition for unity power factor: the capacitor's susceptance omega C equals the motor's inductive susceptance "
                      "X_L/|Z|^2, so C = X_L/(omega |Z|^2)",
                 "The motor branch contributes -j X_L/|Z|^2 to the admittance and the capacitor contributes +j omega C; the "
                 "imaginary parts cancel when they are equal, whatever the supply voltage is."),
        ),
        check="With R = 0 the formula reduces to C = 1/(omega^2 L), the capacitor that resonates with the coil in parallel; a larger "
              "resistance needs a smaller capacitance, and the result must be positive."),
    "S213": Plan(
        approach="The ions gain their speed from the accelerating voltage. Between the plates they feel a constant sideways force and "
                 "acquire a sideways velocity and displacement; beyond the plates they drift in a straight line. The ratio of the "
                 "sideways to the forward velocity depends only on the two voltages and the geometry.",
        steps=(
            Step("tanth", "Kinematics of a charge in crossed motion: the forward speed v satisfies (1/2) m v^2 = q Va, the sideways "
                          "acceleration is q Vd/(m d) for a time ell/v, so tan(theta) = v_y/v = Vd ell/(2 d Va)",
                 "The charge and mass of the ions cancel in the ratio of the sideways velocity to the forward velocity, so the "
                 "deflection angle follows from the voltages and the plate geometry."),
            Step("yexit", "Uniform sideways acceleration over the plate length: the displacement is half the final sideways velocity "
                          "times the transit time, so y_exit = tan(theta) ell/2",
                 "The sideways displacement grows quadratically with time, so at the plate exit it is half of tan(theta) times the "
                 "plate length."),
            Step("ysc", "Straight-line motion beyond the plates: the spot is displaced by y_exit + L tan(theta)",
                 "After the plates no force acts, so the ions keep the exit direction and add L tan(theta) over the drift distance."),
        ),
        check="The same result follows by extrapolating the exit ray backwards to the midpoint of the plates, giving "
              "tan(theta)(L + ell/2); doubling the plate voltage doubles the displacement and doubling the accelerating voltage "
              "halves it."),
    "S214": Plan(
        approach="The change of flux through the coil, times the number of turns, divided by the resistance, is the charge that flows; "
                 "the time over which the field falls does not matter. Find the flux through one turn, then the charge.",
        steps=(
            Step("A", "Area of a circular turn: A = pi r^2",
                 "The coil lies entirely inside the uniform field, so the flux is the field times the area enclosed by one turn."),
            Step("Phi", "Magnetic flux through a loop perpendicular to a uniform field: Phi = B A, so the change of flux is B0 A",
                 "The field falls from B0 to zero, so the flux through each turn falls by B0 A."),
            Step("Q", "Faraday's law and Ohm's law: emf = N dPhi/dt and I = emf/R, so the charge Q = integral of I dt = N Delta Phi / R",
                 "The induced emf is the rate of change of the flux linkage; integrating the current over the time of the change "
                 "leaves the total change of flux linkage divided by the resistance."),
        ),
        check="The result does not contain the time taken, as it must for a total charge; doubling the number of turns doubles the "
              "flux linkage but not the resistance, so it doubles the charge."),
    "S215": Plan(
        approach="A step on a lossless line launches a wave whose voltage is set by the source and the characteristic impedance; at the "
                 "load the wave is partly reflected, and the load voltage is the sum of the incident and reflected voltages until "
                 "the reflection from the source end returns.",
        steps=(
            Step("Z0", "Characteristic impedance of a lossless line: Z0 = sqrt(L'/C') with L' and C' per unit length, which equals "
                       "sqrt(L_total/C_total) because the length cancels",
                 "The line is uniform, so the inductance and capacitance per metre are the totals divided by the same length, and "
                 "the ratio of the two is the ratio of the totals."),
            Step("Gam", "Reflection coefficient at a resistive load: Gamma = (RL - Z0)/(RL + Z0)",
                 "The load imposes V = RL I on the sum of the incident and reflected waves, which fixes the fraction of the "
                 "incident wave that is reflected."),
            Step("Vinc", "The source and the line form a voltage divider at the instant of switching: the launched wave has voltage "
                         "Vs Z0/(Rs + Z0)",
                 "Before any reflection returns the source sees only the line, which acts like a resistor Z0, so the launched "
                 "voltage is the divider fraction of the emf."),
            Step("VL", "Voltage at the load is the incident plus the reflected wave: V_L = V_inc (1 + Gamma)",
                 "Until the reflection from the source end arrives, the voltage across the load is the sum of the first incident "
                 "wave and the wave reflected from the load."),
        ),
        check="For a matched load (RL = Z0) the reflection coefficient is zero and the load sees the launched voltage; for an open "
              "load the voltage doubles, and for a short it is zero."),
    "S216": Plan(
        approach="Charge moves between the capacitors through the inductor like a mass on a spring: the voltage on the second capacitor "
                 "oscillates about the balance value, starting from its initial value at rest, so it overshoots the balance value by "
                 "as much as it started below it.",
        steps=(
            Step("Q0", "Charge conservation for the joined plates: the total charge is Q = C1 V0 + C2 V2",
                 "The positive plates are joined, so their charges add, and with no resistance this total is conserved as charge "
                 "moves between the capacitors."),
            Step("Veq", "Common voltage at balance: with both capacitors at the same voltage the total charge is shared in proportion "
                        "to capacitance, so the balance voltage is Q/(C1 + C2)",
                 "At the balance point, where no net voltage drives the current, the two capacitors have equal voltages and hold "
                 "the conserved total charge, which fixes the centre of the oscillation."),
            Step("Vmax", "Simple harmonic oscillation from rest: the voltage on the second capacitor is Veq + (V2 - Veq) cos(w t), so "
                         "its largest value is Veq + (Veq - V2) = 2 Veq - V2",
                 "The loop equation L q2'' = (Q - q2)/C1 - q2/C2 has the balance charge as its equilibrium; the current is zero at "
                 "the start, so the voltage swings from V2 to the mirror value on the other side of Veq, and the inductance sets "
                 "only the period."),
        ),
        check="The largest voltage is independent of the inductance; if the second capacitor started at the balance voltage nothing "
              "would move and the formula gives Veq, and as C2 goes to zero the largest voltage approaches 2 V0."),
    "S217": Plan(
        approach="Resolve the weight and the electric force along and normal to the slope. The normal force fixes the friction; the "
                 "net force along the slope gives the acceleration, and constant acceleration from rest gives the speed.",
        steps=(
            Step("Fd", "Components along the slope: the electric force contributes q E cos(theta) up the slope and the weight "
                       "contributes m g sin(theta) down it",
                 "Both forces are resolved onto the line of the slope; the difference is the force that drives the block up before "
                 "friction is taken into account."),
            Step("Nn", "Equilibrium of forces normal to the incline: N = m g cos(theta) + q E sin(theta)",
                 "The horizontal field pushes the block into the slope as well as along it, so the component of the electric force "
                 "normal to the slope adds to the normal component of the weight."),
            Step("Ff", "Kinetic friction: F_f = mu N, directed down the slope while the block slides up",
                 "The block is sliding, so the friction force has its kinetic magnitude, the coefficient times the normal force."),
            Step("acc", "Newton's second law along the slope: a = (F_drive - F_friction)/m",
                 "The net force along the slope is the driving component minus the friction, and dividing by the mass gives the "
                 "constant acceleration."),
            Step("v", "Constant acceleration from rest: v^2 = 2 a s",
                 "The block starts from rest and accelerates uniformly through the distance s along the slope."),
        ),
        check="With the field off the block would not move up; with no friction and no incline angle the speed would be "
              "sqrt(2 q E s/m); the speed must be real, which needs the driving force to exceed the friction."),
    "S218": Plan(
        approach="At constant voltage the plate charge changes as the plates separate. The force on one plate is half the charge on the "
                 "other plate times the field of that other plate's partner, that is half Q E for the total field E between the plates.",
        steps=(
            Step("C1", "Parallel-plate capacitance is inversely proportional to the separation: C = C0 d0/d",
                 "The area and the dielectric are unchanged, so only the separation changes the capacitance."),
            Step("E1", "Uniform field between parallel plates: E = V/d",
                 "The voltage across the plates is the emf and the separation is the final one, so the field is the emf divided by "
                 "the separation."),
            Step("Qc", "Definition of capacitance: Q = C V at the battery voltage",
                 "The battery keeps the voltage equal to its emf, so the charge on the plates at the final separation is C1 V."),
            Step("F", "Force on one plate in the field of the other: F = (1/2) Q E, because the field of the other plate alone is half "
                      "the total field between the plates",
                 "The charge on one plate lies in the field produced by the other plate, which is half of E, so the force on it is "
                 "Q E/2."),
        ),
        check="The same force follows from virtual work, F = (1/2) V^2 |dC/dd| = (1/2) V^2 C0 d0/d1^2; the force falls as the "
              "inverse square of the separation at fixed voltage."),
    "S219": Plan(
        approach="The component of the velocity along the field is constant, and the perpendicular component circles at the cyclotron "
                 "frequency. The pitch is the constant speed along the field times the time of one turn, which does not depend on "
                 "the perpendicular speed.",
        steps=(
            Step("wc", "Newton's second law with the Lorentz force for circular motion perpendicular to a uniform field: "
                       "q v B = m v^2/r gives omega = q B/m",
                 "The magnetic force on the perpendicular component acts as the centripetal force, and the resulting angular "
                 "frequency does not depend on the size of that component."),
            Step("T", "Period of circular motion: T = 2 pi/omega",
                 "One complete turn of the projected circular motion takes one period, whatever the radius."),
            Step("p", "Uniform motion along the field: the advance in one turn is v_parallel times the time T",
                 "No force acts along the field, so the bead advances along it at constant speed while it completes one circle."),
        ),
        check="The pitch grows in proportion to the mass and to the speed along the field, and falls as the charge or the field "
              "increases; for a very large field the helix becomes tightly wound, and the result is in metres."),
    "S220": Plan(
        approach="At constant voltage the force on the slab is half the square of the voltage times the rate at which capacitance "
                 "rises with the inserted length. The capacitance of the part-filled capacitor rises linearly with the inserted "
                 "length, so the force does not depend on how far the slab is in.",
        steps=(
            Step("Cfull", "A capacitor filled by a dielectric of constant kappa has kappa times the capacitance: C = kappa C0",
                 "With the slab fully in, the whole gap is filled, so the capacitance is the empty value times the dielectric "
                 "constant."),
            Step("dC", "Capacitance of the part-filled capacitor as two parallel capacitors, one filled and one empty, gives a "
                       "total that rises linearly from C0 to kappa C0 over the length",
                 "The filled and empty parts add in parallel, so the total changes linearly with the inserted length, and the "
                 "full rise from empty to filled is the difference of the end values."),
            Step("dCdx", "Rate of change of capacitance with the inserted length: dC/dx = (C_full - C0)/ell",
                 "The capacitance is linear in x, so its slope is the total rise divided by the plate length, the same at every "
                 "insertion."),
            Step("F", "Virtual work at constant voltage: the force along x is F = (1/2) V^2 dC/dx",
                 "The battery supplies energy as the slab moves in, and the net mechanical work per unit displacement equals the "
                 "rate of increase of (1/2) C V^2 with x."),
        ),
        check="The force is independent of the insertion depth and grows with the square of the battery voltage; with kappa = 1 the "
              "slab is air and the force is zero."),
}

LEVELS: dict[str, str] = {
    "S211": "upper_university", "S212": "upper_university", "S213": "intro_university", "S214": "intro_university",
    "S215": "upper_university", "S216": "upper_university", "S217": "intro_university", "S218": "intro_university",
    "S219": "intro_university", "S220": "upper_university",
}

TOPICS: dict[str, str] = {
    "S211": "Gauss's law and superposition: uniform field in a cavity of a uniformly charged ball",
    "S212": "phasor analysis of a parallel RLC branch: power-factor correction",
    "S213": "motion of ions through an accelerating gap and deflecting plates",
    "S214": "Faraday's law: charge induced in a coil by a falling field",
    "S215": "pulse reflection on a mismatched lossless transmission line",
    "S216": "LC oscillation: charge transfer between capacitors through an inductor",
    "S217": "charged block on a rough incline in a horizontal electric field",
    "S218": "electrostatic force between capacitor plates at constant voltage",
    "S219": "helical motion of a charge in a magnetic field",
    "S220": "force on a dielectric slab in a capacitor by the energy method",
}
