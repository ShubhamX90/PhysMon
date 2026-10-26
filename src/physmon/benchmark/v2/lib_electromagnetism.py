"""Electromagnetism and circuits structures S41 to S48 and gold solution plans (Stage 14.19; domain author agent).

Eight new structures: charge sharing between conducting spheres, a stretched wire on a battery, a dielectric slab in a capacitor that
stays on its battery, a wire levitated by a magnetic force, a charged bead accelerated and bent by a magnetic field, a rod on inclined
rails in a vertical field, a loaded transformer fed from a source with internal resistance, and the ringing frequency of a damped
series RLC circuit. Each has a typed graph with two to four computed nodes, an independently coded numeric solver (a root finder, an
ODE, a linear system, the roots of a characteristic polynomial, a direct numerical definition), at least four numeric instantiations
and a relevant edit. No problem needs a constant that is awkward to print (k, mu0, e, epsilon0): those problems are posed through
ratios, capacities, macroscopic charges and given fields so that every numeral in a prompt is human-sized and is an input node.

The module also holds the gold solution plans (`trace.Plan`) for these eight structures and for the existing structures S06, S07, S08,
S15, S16 and S25 of the same domain, with a course level and a topic string for each.

Admission status: agent-verified, not expert-reviewed. Solver certification covers the graph, the independent solver route and the
rendered numerals; a separate verifier agent re-derives each answer blind. No human physicist has reviewed any of this text.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq

from physmon.benchmark.v2.graph import Assumption, Structure
from physmon.benchmark.v2.library import A_G, _co, _g, _in, _spec
from physmon.benchmark.v2.trace import Plan, Step

# --- solvers (independent routes; SI inputs in node order, constants included) ---------------------


def _solve_charge_sharing(f0, rq, d0, d1):
    # Fix Coulomb's constant from the first state with the smaller charge set to one unit (the unit cancels), then evaluate
    # Coulomb's law directly for the charge left on each sphere after contact.
    q_small, q_large = 1.0, -rq
    k_eff = f0 * d0 ** 2 / (abs(q_small * q_large))
    q_each = 0.5 * (q_small + q_large)
    return float(k_eff * q_each * q_each / d1 ** 2)


def _solve_stretched_wire(r0, k, volt):
    # Direct definition R = rho L / A with the volume fixed: choose rho = L0 = 1 so that A0 = 1/R0, then stretch and take I^2 R.
    rho, length0 = 1.0, 1.0
    area0 = rho * length0 / r0
    volume = area0 * length0
    length = k * length0
    area = volume / length
    resistance = rho * length / area
    current = volt / resistance
    return float(current ** 2 * resistance)


def _solve_slab_charge(c0, d, t, kappa, volt):
    # The empty gap as two capacitors in series (an air layer and a dielectric layer): equal charge, loop law, linear system in
    # (Q, Va, Vd). Capacitances are scaled to picofarad and charge to picocoulomb to keep the matrix well conditioned.
    scale = 1.0e12
    c_air = c0 * scale * d / (d - t)
    c_die = kappa * c0 * scale * d / t
    matrix = np.array([[1.0, -c_air, 0.0], [1.0, 0.0, -c_die], [0.0, 1.0, 1.0]])
    rhs = np.array([0.0, 0.0, volt])
    charge_pc = float(np.linalg.solve(matrix, rhs)[0])
    return float((charge_pc - c0 * scale * volt) / scale)


def _solve_levitation(m, length, b, g):
    # The current at which the net vertical force B I L - m g changes sign, found with a bracketing root finder.
    return float(brentq(lambda i: b * i * length - m * g, 0.0, 1.0e4, xtol=1e-13, rtol=1e-14))


def _solve_bead_radius(m, q, volt, b):
    # Stage 1: the bead is pushed from rest across a gap of one metre by the uniform field V / (1 m); the speed at the exit event.
    gap = 1.0

    def exit_gap(t, y):
        return y[0] - gap

    exit_gap.terminal = True
    stage1 = solve_ivp(lambda t, y: [y[1], q * volt / (gap * m)], (0.0, 100.0), [0.0, 0.0], events=exit_gap, rtol=1e-12, atol=1e-14)
    speed = float(stage1.y_events[0][0][1])
    # Stage 2: the Lorentz force q v x B integrated over one cyclotron period; the radius is half the largest sideways excursion.
    omega = q * b / m
    period = 2.0 * math.pi / omega
    times = np.linspace(0.0, period, 4001)
    stage2 = solve_ivp(lambda t, y: [y[2], y[3], omega * y[3], -omega * y[2]], (0.0, period), [0.0, 0.0, speed, 0.0], t_eval=times,
                       rtol=1e-12, atol=1e-14)
    return float(np.max(np.abs(stage2.y[1])) / 2.0)


def _solve_rail_terminal(m, r, ell, b, theta, g):
    # Equation of motion m dv/dt = m g sin(theta) - (B cos(theta) ell)^2 v / R integrated from rest for forty relaxation times.
    drag = (b * math.cos(theta) * ell) ** 2 / r
    horizon = 40.0 * m / drag
    solution = solve_ivp(lambda t, y: [g * math.sin(theta) - drag * y[0] / m], (0.0, horizon), [0.0], rtol=1e-11, atol=1e-13)
    return float(solution.y[0][-1])


def _solve_transformer_load(vs, rs, a, rl):
    # The source loop, the two ideal-transformer relations and Ohm's law in the load as a linear system in (V1, I1, V2, I2).
    matrix = np.array([[1.0, rs, 0.0, 0.0], [1.0, 0.0, -a, 0.0], [0.0, 0.0, 1.0, -rl], [0.0, a, 0.0, -1.0]])
    rhs = np.array([vs, 0.0, 0.0, 0.0])
    _, _, _, i2 = np.linalg.solve(matrix, rhs)
    return float(rl * i2 * i2)


def _solve_ringing(r, ind, c):
    # The natural frequencies are the roots of the characteristic polynomial L s^2 + R s + 1/C = 0; the ringing frequency is the
    # imaginary part of the complex pair divided by two pi.
    roots = np.roots([ind, r, 1.0 / c])
    return float(np.max(np.abs(roots.imag)) / (2.0 * math.pi))


# --- structures ---------------------------------------------------------------------------------------


def s41_charge_sharing() -> Structure:
    return Structure(
        "S41", "Force between two conducting spheres after they touch", "electromagnetism", "coulomb_force_after_charge_sharing",
        (_in("F0", "force", "mN", "attractive force before contact", 80.0, (20.0, 200.0)),
         _in("rq", "ratio", "1", "ratio of the larger charge magnitude to the smaller", 5.0, (2.5, 9.0)),
         _in("d0", "length", "cm", "separation of the centres before contact", 30.0, (10.0, 40.0)),
         _in("d1", "length", "cm", "separation of the centres after contact", 60.0, (10.0, 100.0)),
         _co("qshare", "ratio", "1", "charge magnitude left on each sphere after contact, in units of the smaller initial charge",
             "(rq - 1)/2"),
         _co("Frel", "ratio", "1", "force magnitude after contact divided by force magnitude before contact",
             "qshare**2/rq*(d0/d1)**2"),
         _co("F1", "force", "mN", "force magnitude between the spheres after contact", "F0*Frel")),
        "F1",
        (Assumption("A-point", "The spheres are small compared with their separations, so each acts as a point charge, and nothing "
                               "else disturbs the field.", "modelling", ("d0", "d1")),
         Assumption("A-contact", "The spheres are identical conductors: on contact the total charge is shared equally and none "
                                 "leaks away.", "modelling", ("rq",)),
         Assumption("A-force", "The force is the electrostatic force in air, taken as a vacuum.", "modelling", ("F0",))),
        _spec("Two small identical conducting spheres carry charges of opposite sign. The charge on the first sphere is {rq} times "
              "as large in magnitude as the charge on the second. With their centres {d0} cm apart, the spheres attract each other "
              "with a force of {F0} mN. The spheres are touched together and then moved apart until their centres are {d1} cm apart. "
              "Treat the spheres as point charges.",
              "What is the magnitude of the force between the spheres now?", "force between the spheres after contact", "mN",
              "A separate pair of spheres B on another bench exerts a force of {v} {u} on each other, but it is unrelated to this pair.",
              "A reference pair of spheres B exerts a force of {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the force.", "W", equivalent="N"),
        ("d1", 1.25), _solve_charge_sharing, 4,
        "Coulomb's law evaluated directly with an effective constant fixed by the first state and the charge left on each sphere "
        "after contact",
        solver_rel_tol=1e-9,
        instances=({"F0": 80.0, "rq": 5.0, "d0": 30.0, "d1": 60.0}, {"F0": 45.0, "rq": 3.0, "d0": 20.0, "d1": 10.0},
                   {"F0": 120.0, "rq": 7.0, "d0": 24.0, "d1": 36.0}, {"F0": 36.0, "rq": 4.0, "d0": 15.0, "d1": 45.0}))


def s42_stretched_wire_power() -> Structure:
    return Structure(
        "S42", "Power dissipated by a wire after it is drawn out", "electromagnetism", "stretched_wire_resistance_power",
        (_in("R0", "resistance", "Ω", "resistance of the wire before it is drawn out", 2.0, (0.5, 5.0)),
         _in("k", "ratio", "1", "factor by which the length is increased", 3.0, (1.5, 5.0)),
         _in("V", "voltage", "V", "battery emf", 12.0, (3.0, 24.0)),
         _co("Rnew", "resistance", "Ω", "resistance of the drawn-out wire", "R0*k**2"),
         _co("I", "current", "A", "current in the drawn-out wire", "V/Rnew"),
         _co("P", "power", "W", "power dissipated in the drawn-out wire", "V*I")),
        "P",
        (Assumption("A-volume", "The wire stays uniform when it is drawn out: its volume and its resistivity do not change.",
                    "modelling", ("R0", "k")),
         Assumption("A-battery", "The battery is ideal with negligible internal resistance and the connecting leads have negligible "
                                 "resistance.", "modelling", ("V",))),
        _spec("A uniform metal wire has a resistance of {R0} Ω. It is drawn out until its length is {k} times its original length. "
              "Its volume and the resistivity of the metal are unchanged. The drawn-out wire is then connected across an ideal "
              "battery of emf {V} V.",
              "What power does the drawn-out wire dissipate?", "power dissipated in the drawn-out wire", "W",
              "A separate heater B on another bench dissipates {v} {u}, but it is unrelated to this wire.",
              "A reference wire B dissipates {v} {u}.",
              "A separate oscillator B runs at {v} {u}, but it is not part of this circuit.", "Hz", equivalent="mW"),
        ("k", 0.8), _solve_stretched_wire, 3,
        "the definition R = rho L / A with the volume held fixed, evaluated for the drawn-out wire, then the power as I squared R",
        solver_rel_tol=1e-9,
        instances=({"R0": 2.0, "k": 3.0, "V": 12.0}, {"R0": 1.5, "k": 2.0, "V": 9.0}, {"R0": 2.5, "k": 4.0, "V": 20.0},
                   {"R0": 0.8, "k": 2.5, "V": 6.0}))


def s43_dielectric_slab_charge() -> Structure:
    return Structure(
        "S43", "Extra charge drawn by a capacitor when a dielectric slab is inserted", "electromagnetism",
        "partial_dielectric_slab_constant_voltage",
        (_in("C0", "capacitance", "pF", "capacitance of the empty capacitor", 100.0, (50.0, 300.0)),
         _in("d", "length", "mm", "separation of the plates", 6.0, (4.5, 10.0)),
         _in("t", "length", "mm", "thickness of the dielectric slab", 3.0, (1.0, 4.0)),
         _in("kappa", "coefficient", "1", "dielectric constant of the slab", 4.0, (2.0, 6.0)),
         _in("V", "voltage", "V", "battery emf", 12.0, (6.0, 24.0)),
         _co("frac", "ratio", "1", "fraction of the gap filled by the slab", "t/d"),
         _co("C", "capacitance", "pF", "capacitance with the slab inserted", "C0/(1 - frac*(1 - 1/kappa))"),
         _co("dQ", "charge", "nC", "additional charge supplied by the battery", "(C - C0)*V")),
        "dQ",
        (Assumption("A-parallel", "The slab has the same area as the plates and lies parallel to them; edge effects are neglected, "
                                  "so the capacitor is a stack of two layers in series.", "modelling", ("d", "t")),
         Assumption("A-battery", "The battery stays connected and is ideal, so the voltage across the capacitor is the emf before "
                                 "and after the insertion.", "boundary_condition", ("V",)),
         Assumption("A-dielectric", "The slab is a linear dielectric of the stated constant, and the empty gap is a vacuum.",
                    "modelling", ("kappa", "C0"))),
        _spec("An empty parallel-plate capacitor has a capacitance of {C0} pF and a plate separation of {d} mm. It is connected to a "
              "battery of emf {V} V and fully charged. With the battery still connected, a slab of dielectric constant {kappa} and "
              "thickness {t} mm, with the same area as the plates, is slid between the plates parallel to them, without touching "
              "either plate.",
              "How much additional charge does the battery supply to the capacitor?", "additional charge supplied by the battery",
              "nC",
              "A separate capacitor B on another board holds a charge of {v} {u}, but it is unrelated to this capacitor.",
              "A reference capacitor B holds a charge of {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the charging.", "W", equivalent="μC"),
        ("kappa", 1.25), _solve_slab_charge, 5,
        "the gap treated as an air layer and a dielectric layer in series, solved as a linear system for the charge, minus the "
        "initial charge",
        solver_rel_tol=1e-9,
        instances=({"C0": 100.0, "d": 6.0, "t": 3.0, "kappa": 4.0, "V": 12.0}, {"C0": 60.0, "d": 8.0, "t": 4.0, "kappa": 5.0, "V": 20.0},
                   {"C0": 90.0, "d": 6.0, "t": 3.0, "kappa": 3.0, "V": 15.0}, {"C0": 120.0, "d": 5.0, "t": 4.0, "kappa": 4.0, "V": 10.0}))


def s44_wire_levitation_current() -> Structure:
    return Structure(
        "S44", "Current that levitates a rod in a magnetic field", "electromagnetism", "magnetic_force_balances_weight",
        (_in("m", "mass", "g", "mass of the rod", 25.0, (10.0, 80.0)),
         _in("L", "length", "cm", "length of the rod in the field", 50.0, (20.0, 100.0)),
         _in("B", "magnetic_field", "mT", "magnetic field strength", 350.0, (100.0, 800.0)),
         _g(),
         _co("W", "force", "N", "weight of the rod", "m*g"),
         _co("I", "current", "A", "current needed to support the rod", "W/(B*L)")),
        "I",
        (A_G, Assumption("A-field", "The field is uniform, horizontal and perpendicular to the rod, which lies entirely in the field; "
                                    "the current direction is chosen so that the magnetic force points upward.", "boundary_condition",
                         ("B", "L")),
         Assumption("A-leads", "The flexible leads that carry the current exert no force on the rod.", "modelling", ("m",))),
        _spec("A straight horizontal rod of mass {m} grams and length {L} cm lies at right angles to a uniform horizontal magnetic "
              "field of {B} mT, and the whole rod is in the field. The current in the rod is directed so that the magnetic force on it points upward. Take "
              "g = {g} m/s².",
              "What current must the rod carry for the magnetic force to just support its weight?",
              "current that supports the rod", "A",
              "A separate wire B on another bench carries a current of {v} {u}, but it is unrelated to this rod.",
              "A reference rod B carries a current of {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the support.", "W", equivalent="mA"),
        ("B", 0.8), _solve_levitation, 4,
        "the current at which the net upward force B I L minus m g changes sign, found with a bracketing root finder",
        solver_rel_tol=1e-9,
        instances=({"m": 25.0, "L": 50.0, "B": 350.0, "g": 9.8}, {"m": 40.0, "L": 30.0, "B": 500.0, "g": 9.8},
                   {"m": 18.0, "L": 40.0, "B": 280.0, "g": 9.8}, {"m": 60.0, "L": 80.0, "B": 450.0, "g": 9.8}))


def s45_bead_circle_radius() -> Structure:
    return Structure(
        "S45", "Radius of the path of an accelerated charged bead in a magnetic field", "electromagnetism",
        "accelerated_charge_circular_orbit_radius",
        (_in("m", "mass", "g", "mass of the bead", 0.1, (0.05, 0.5)),
         _in("q", "charge", "mC", "charge of the bead", 2.0, (0.5, 5.0)),
         _in("V", "voltage", "V", "potential difference through which the bead is accelerated", 2.5, (1.0, 20.0)),
         _in("B", "magnetic_field", "T", "magnetic field strength", 0.8, (0.3, 1.5)),
         _co("v", "speed", "m/s", "speed of the bead on entering the field", "sqrt(2*q*V/m)"),
         _co("wc", "angular_frequency", "rad/s", "cyclotron angular frequency of the bead", "q*B/m"),
         _co("r", "length", "cm", "radius of the circular path", "v/wc")),
        "r",
        (Assumption("A-vacuum", "The motion is non-relativistic and takes place in a vacuum; gravity and radiation are neglected.",
                    "modelling", ("m", "q")),
         Assumption("A-start", "The bead starts from rest and gains its speed only from the stated potential difference.",
                    "boundary_condition", ("V",)),
         Assumption("A-field", "The magnetic field is uniform and perpendicular to the velocity of the bead on entry.",
                    "boundary_condition", ("B",))),
        _spec("A small bead of mass {m} grams carries a charge of {q} mC. Starting from rest, it is accelerated through a potential "
              "difference of {V} V in a vacuum and then enters a region of uniform magnetic field of {B} T, perpendicular to its "
              "velocity. Neglect gravity and any radiation.",
              "What is the radius of the circular path of the bead in the magnetic field?", "radius of the circular path", "cm",
              "A separate bead B in another chamber moves on a circle of radius {v} {u}, but it is unrelated to this bead.",
              "A reference bead B moves on a circle of radius {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the motion.", "W", equivalent="m"),
        ("B", 1.25), _solve_bead_radius, 4,
        "the exit speed from the equation of motion across the accelerating gap, then the Lorentz-force equations integrated over one "
        "period and half the largest sideways excursion",
        solver_rel_tol=1e-6,
        instances=({"m": 0.1, "q": 2.0, "V": 2.5, "B": 0.8}, {"m": 0.2, "q": 1.0, "V": 4.0, "B": 0.5},
                   {"m": 0.25, "q": 2.5, "V": 5.0, "B": 1.0}, {"m": 0.4, "q": 4.0, "V": 2.0, "B": 1.2}))


def s46_rail_terminal_speed() -> Structure:
    return Structure(
        "S46", "Terminal speed of a rod sliding down inclined rails in a vertical field", "electromagnetism",
        "inclined_rails_terminal_speed",
        (_in("m", "mass", "g", "mass of the rod", 50.0, (20.0, 200.0)),
         _in("R", "resistance", "Ω", "resistance of the resistor joining the rails", 0.5, (0.2, 2.0)),
         _in("ell", "length", "cm", "distance between the rails", 40.0, (20.0, 80.0)),
         _in("B", "magnetic_field", "T", "vertical magnetic field strength", 0.6, (0.3, 1.2)),
         _in("theta", "angle", "deg", "angle of the rails above the horizontal", 30.0, (15.0, 45.0)),
         _g(),
         _co("Fg", "force", "N", "component of the weight along the rails", "m*g*sin(theta)"),
         _co("Beff", "magnetic_field", "T", "component of the field perpendicular to the plane of the rails", "B*cos(theta)"),
         _co("v", "speed", "m/s", "terminal speed of the rod", "Fg*R/(Beff*ell)**2")),
        "v",
        (A_G, Assumption("A-rails", "The rails are long and frictionless, the rod stays horizontal and in contact with both rails, "
                                    "and only the resistor has resistance.", "modelling", ("R", "ell")),
         Assumption("A-field", "The magnetic field is uniform and vertical, and self-inductance is negligible.", "modelling",
                    ("B", "theta"))),
        _spec("Two long parallel conducting rails are a distance of {ell} cm apart and slope at {theta} degrees above the "
              "horizontal. A resistor of {R} Ω joins them at the lower end; the rails and the rod have no other resistance. A uniform "
              "magnetic field of {B} T points vertically upward throughout the region. A horizontal rod of mass {m} grams lies across "
              "the rails and slides down them without friction, always in contact with both rails. Take g = {g} m/s².",
              "What is the terminal speed that the sliding rod approaches?", "terminal speed of the rod", "m/s",
              "A separate cart B on another track moves at {v} {u}, but it is unrelated to this rod.",
              "A reference rod B slides at {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the sliding.", "W", equivalent="cm/s"),
        ("R", 1.25), _solve_rail_terminal, 6,
        "the equation of motion m dv/dt = m g sin(theta) - (B cos(theta) ell)^2 v / R integrated with an adaptive ODE solver from "
        "rest for forty relaxation times",
        solver_rel_tol=1e-6,
        instances=({"m": 50.0, "R": 0.5, "ell": 40.0, "B": 0.6, "theta": 30.0, "g": 9.8},
                   {"m": 80.0, "R": 1.0, "ell": 50.0, "B": 0.8, "theta": 25.0, "g": 9.8},
                   {"m": 30.0, "R": 0.8, "ell": 30.0, "B": 1.0, "theta": 40.0, "g": 9.8},
                   {"m": 100.0, "R": 1.5, "ell": 60.0, "B": 0.5, "theta": 20.0, "g": 9.8}))


def s47_transformer_load_power() -> Structure:
    return Structure(
        "S47", "Load power through a transformer from a source with internal resistance", "electromagnetism",
        "transformer_reflected_resistance_power",
        (_in("Vs", "voltage", "V", "rms emf of the generator", 100.0, (50.0, 240.0)),
         _in("Rs", "resistance", "Ω", "internal resistance of the generator", 20.0, (5.0, 50.0)),
         _in("a", "ratio", "1", "ratio of primary turns to secondary turns", 3.0, (2.0, 10.0)),
         _in("RL", "resistance", "Ω", "resistance of the load", 20.0, (2.0, 40.0)),
         _co("Rref", "resistance", "Ω", "load resistance as seen from the primary side", "a**2*RL"),
         _co("I1", "current", "A", "rms current in the primary circuit", "Vs/(Rs + Rref)"),
         _co("I2", "current", "A", "rms current in the load", "a*I1"),
         _co("P", "power", "W", "average power dissipated in the load", "I2**2*RL")),
        "P",
        (Assumption("A-ideal", "The transformer is ideal: perfect coupling, no losses and negligible magnetising current.",
                    "modelling", ("a",)),
         Assumption("A-rms", "All emfs and currents are rms values, the load is purely resistive and the generator is a sinusoidal "
                             "source in series with its internal resistance.", "modelling", ("Vs", "Rs", "RL"))),
        _spec("An AC generator of rms emf {Vs} V and internal resistance {Rs} Ω is connected to the primary coil of an ideal "
              "transformer. The primary coil has {a} times as many turns as the secondary coil. A purely resistive load of {RL} Ω "
              "is connected across the secondary coil.",
              "What average power is dissipated in the load?", "average power dissipated in the load", "W",
              "A separate heater B in another workshop dissipates {v} {u}, but it is unrelated to this circuit.",
              "A reference load B dissipates {v} {u}.",
              "A separate oscillator B runs at {v} {u}, but it is not part of this circuit.", "Hz", equivalent="kW"),
        ("RL", 1.5), _solve_transformer_load, 4,
        "the source loop, the ideal-transformer voltage and current relations and Ohm's law in the load solved as a 4x4 linear system",
        solver_rel_tol=1e-9,
        instances=({"Vs": 100.0, "Rs": 20.0, "a": 3.0, "RL": 20.0}, {"Vs": 120.0, "Rs": 10.0, "a": 2.0, "RL": 5.0},
                   {"Vs": 150.0, "Rs": 25.0, "a": 5.0, "RL": 4.0}, {"Vs": 230.0, "Rs": 15.0, "a": 4.0, "RL": 6.0}))


def s48_rlc_ringing_frequency() -> Structure:
    return Structure(
        "S48", "Ringing frequency of a damped series RLC circuit", "electromagnetism", "damped_series_rlc_frequency",
        (_in("R", "resistance", "Ω", "total resistance of the circuit", 60.0, (10.0, 80.0)),
         _in("Lc", "inductance", "mH", "inductance of the coil", 100.0, (80.0, 400.0)),
         _in("C", "capacitance", "μF", "capacitance of the capacitor", 40.0, (10.0, 40.0)),
         _co("alpha", "rate", "1/s", "damping rate R/(2L)", "R/(2*Lc)"),
         _co("w0", "angular_frequency", "rad/s", "undamped angular frequency", "1/sqrt(Lc*C)"),
         _co("wd", "angular_frequency", "rad/s", "damped angular frequency", "sqrt(w0**2 - alpha**2)"),
         _co("fd", "frequency", "Hz", "frequency of the damped oscillation", "wd/(2*pi)")),
        "fd",
        (Assumption("A-series", "The resistor, coil and capacitor are ideal and in series; any resistance of the coil is included in "
                                "the stated resistance, and there is no source.", "modelling", ("R", "Lc", "C")),
         Assumption("A-underdamped", "The circuit is underdamped: the resistance is small enough that the charge oscillates.",
                    "boundary_condition", ("R",))),
        _spec("A resistor of {R} Ω, a coil of inductance {Lc} mH and a capacitor of {C} μF are connected in series in a closed loop "
              "with no source. The capacitor starts with some charge, and the charge then oscillates with decreasing amplitude.",
              "What is the frequency of these damped oscillations?", "frequency of the damped oscillation", "Hz",
              "A separate oscillator B in another circuit rings at {v} {u}, but it is unrelated to this loop.",
              "A reference circuit B rings at {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the oscillation.", "W", equivalent="kHz"),
        ("Lc", 1.5), _solve_ringing, 3,
        "the natural frequencies as the roots of the characteristic polynomial L s squared plus R s plus one over C, taking the "
        "imaginary part of the complex pair",
        solver_rel_tol=1e-9,
        instances=({"R": 60.0, "Lc": 100.0, "C": 40.0}, {"R": 24.0, "Lc": 80.0, "C": 20.0}, {"R": 20.0, "Lc": 100.0, "C": 10.0},
                   {"R": 50.0, "Lc": 200.0, "C": 25.0}))


ALL = (s41_charge_sharing, s42_stretched_wire_power, s43_dielectric_slab_charge, s44_wire_levitation_current, s45_bead_circle_radius,
       s46_rail_terminal_speed, s47_transformer_load_power, s48_rlc_ringing_frequency)


def all_structures() -> list[Structure]:
    return [factory() for factory in ALL]


# --- gold solution plans --------------------------------------------------------------------------------

PLANS: dict[str, Plan] = {
    # ---- existing structures of the domain -------------------------------------------------------------
    "S06": Plan(
        approach="The current in one branch of a parallel pair that sits in series with another resistor is found by working from the "
                 "inside out: first replace the pair by its equivalent resistance, then find the one current the battery drives, then "
                 "the voltage that current produces across the pair, and last the current in the branch that was asked for.",
        steps=(
            Step("R23", "Resistors in parallel: the reciprocal of the equivalent resistance is the sum of the reciprocals, "
                        "1/R_eq = 1/R2 + 1/R3, which for two resistors is R2 R3/(R2 + R3)",
                 "The two resistors are connected between the same two junctions, so they share one voltage and their currents add; "
                 "replacing them by one equivalent resistor turns the network into a simple series circuit."),
            Step("Req", "Resistors in series add: the total resistance is the sum of the individual resistances, R_total = R1 + R_pair",
                 "The series resistor and the equivalent pair carry the same current, so the battery sees their sum as its load."),
            Step("Itot", "Ohm's law for the whole circuit: the current equals the emf divided by the total resistance, I = V/R",
                 "With a battery of negligible internal resistance the full emf drives the current through the total resistance, "
                 "which gives the single current that leaves the battery."),
            Step("V23", "Ohm's law for the equivalent resistor of the pair: the voltage across it is the current times its resistance, "
                        "V = I R",
                 "All of the battery current passes through the pair, so this product is the voltage across the parallel "
                 "combination, and the same voltage appears across each of its two resistors."),
            Step("I3", "Ohm's law for a single branch: the current in a resistor is the voltage across it divided by its resistance, "
                       "I = V/R",
                 "The second resistor of the pair has the pair voltage across it, so dividing that voltage by its own resistance "
                 "gives the branch current the question asks for."),
        ),
        check="The two branch currents must add up to the total current, V23/R2 + V23/R3 = Itot, and the pair voltage must be smaller "
              "than the battery emf because part of the emf is used up across the series resistor; making R3 very large would drive "
              "its current toward zero."),
    "S07": Plan(
        approach="The capacitor charges exponentially toward the battery emf with a time constant set by the resistance and the "
                 "capacitance. Find the time constant, express the elapsed time in units of it, and then evaluate the charging law.",
        steps=(
            Step("tau", "The RC time constant: tau = R C, the product of the series resistance and the capacitance",
                 "The loop equation for the charging circuit contains only the combination R C as a time scale, so it sets how fast "
                 "the capacitor voltage approaches the emf."),
            Step("x", "Dimensionless time: the elapsed time divided by the time constant, x = t/tau",
                 "The charging law depends on time only through this ratio, so computing it first makes the final evaluation a "
                 "one-line exponential."),
            Step("VC", "The charging law of an RC circuit, from Kirchhoff's loop rule V0 = I R + q/C with q = 0 at the start: "
                       "V_C = V0 (1 - e^(-t/tau))",
                 "The capacitor starts uncharged and is charged through the resistor from an ideal battery, so its voltage rises "
                 "from zero toward V0 and at time t equals V0 times one minus the decaying exponential."),
        ),
        check="At t = 0 the formula gives zero, at very long times it approaches the emf, and at t = tau it gives about 63 percent of the "
              "emf, so the answer must lie between zero and V0 and be larger the larger x is."),
    "S08": Plan(
        approach="Two capacitors in series across a battery behave like one equivalent capacitor connected across the same emf. Find "
                 "the equivalent capacitance, then the energy stored in it, which equals the total energy stored in the two capacitors.",
        steps=(
            Step("Ceq", "Capacitors in series: the reciprocal of the equivalent capacitance is the sum of the reciprocals, "
                        "1/C_eq = 1/C1 + 1/C2, which for two capacitors is C1 C2/(C1 + C2)",
                 "Series capacitors hold the same charge, and the voltage across the pair is the sum of their voltages, so they act "
                 "like a single capacitor smaller than either; this is the capacitance that the battery sees."),
            Step("Estore", "Energy stored in a capacitor: U = (1/2) C V^2, applied to the equivalent capacitor across the battery emf",
                 "The energy stored in the series pair equals the energy of the equivalent capacitor charged to the emf, because the "
                 "equivalent capacitor stores the same charge at the same total voltage; the capacitors were initially uncharged "
                 "and are fully charged."),
        ),
        check="The two stored energies (1/2) Q^2/C1 and (1/2) Q^2/C2 with the common charge Q = Ceq V must add to the same value, and the "
              "answer must be smaller than the energy that either capacitor alone would store across the full emf."),
    "S15": Plan(
        approach="Each resistor of a parallel pair has the full battery voltage across it, so the power in each is V squared over its "
                 "resistance and the total power is the sum of the two.",
        steps=(
            Step("P", "Electric power in a resistor, P = V^2/R (from P = V I and Ohm's law), summed over the two parallel resistors: "
                      "P = V^2 (1/R1 + 1/R2)",
                 "Resistors in parallel across an ideal battery each have the whole emf across them, so each dissipates V^2/R, and "
                 "the total dissipated power is the sum of these two terms."),
        ),
        check="The total power must equal the emf times the total battery current, V (V/R1 + V/R2), which is the same expression, and "
              "it must be larger than the power in either resistor alone; removing one resistor must leave only its own term."),
    "S16": Plan(
        approach="After the switch closes, the current in a series RL circuit rises exponentially toward its final value V/R with a "
                 "time constant L over R. Find the time constant, the elapsed time in units of it, and then evaluate the rise law.",
        steps=(
            Step("tau", "The RL time constant: tau = L/R, the inductance divided by the series resistance",
                 "Kirchhoff's loop rule for the circuit, V = I R + L dI/dt, has L/R as its only time scale, so it sets how quickly "
                 "the current approaches its final value."),
            Step("x", "Dimensionless time: the elapsed time divided by the time constant, x = t/tau",
                 "The current rise depends on time only through this ratio, so computing it first reduces the final step to "
                 "evaluating an exponential."),
            Step("I", "The current rise in an RL circuit, solving V = I R + L dI/dt with I = 0 at t = 0: I = (V/R)(1 - e^(-t/tau))",
                 "The coil opposes any sudden change of current, so the current starts at zero and grows toward the steady value V/R "
                 "that Ohm's law would give if the coil were absent."),
        ),
        check="At t = 0 the formula gives zero, at long times it tends to V/R, and the answer can never exceed V/R; at t = tau it "
              "reaches about 63 percent of V/R, which gives a quick order-of-magnitude test."),
    "S25": Plan(
        approach="The energy in the magnetic field of an ideal coil depends only on its inductance and the steady current, so one "
                 "application of the stored-energy formula, with the unit converted at the end, is enough.",
        steps=(
            Step("Wm", "Energy stored in an inductor: U = (1/2) L I^2, the work done against the induced emf while the current is "
                       "raised from zero to I (the integral of L i di)",
                 "The coil is ideal and carries a steady current, so all the work done in building up the current is stored in its "
                 "magnetic field, and the formula gives this energy directly."),
        ),
        check="The energy scales with the square of the current, so doubling the current must quadruple the answer; the unit is "
              "henry times ampere squared, which is a joule."),
    # ---- new structures -----------------------------------------------------------------------------------
    "S41": Plan(
        approach="The charges are not given, but only their ratio and one force, so work with ratios and let the unknown constants "
                 "cancel. First find the charge on each sphere after they touch, then use Coulomb's law to compare the new force with the "
                 "old one, and finally scale the given force.",
        steps=(
            Step("qshare", "Conservation of charge together with the symmetry of two identical conductors: on contact the total charge "
                           "(q1 + q2) is divided equally, so each sphere gets (q1 + q2)/2",
                 "The charges have opposite signs, so with the smaller charge as the unit they are +1 and -(rq) and they partly cancel; "
                 "each sphere is left with magnitude (rq - 1)/2 in these units, and both now have the same sign as the larger charge, "
                 "so the force becomes repulsive."),
            Step("Frel", "Coulomb's law: the force between point charges is proportional to the product of the charges and inversely "
                         "proportional to the square of their separation, F = k qa qb / r^2; the ratio of two states cancels k",
                 "Before contact the force is proportional to rq times 1 divided by d0 squared, and afterwards to qshare squared "
                 "divided by d1 squared, so the ratio of new to old force is qshare squared over rq times (d0/d1) squared, with no need "
                 "for k or the actual charges."),
            Step("F1", "Scaling by a ratio: the new force equals the given force times the force ratio just found",
                 "The old force was given, and the ratio converts it to the force after contact, which is the quantity asked for."),
        ),
        check="If the two charges were equal and opposite (rq = 1) they would cancel completely on contact and the formula gives zero "
              "force; if the spheres end up at the same separation as before, the force changes only by the charge factor qshare "
              "squared over rq, that is (rq - 1)^2/(4 rq), and it is smaller than the original force whenever that factor is below one."),
    "S42": Plan(
        approach="Drawing the wire out changes its length and cross-section while the volume stays the same, so first find how the "
                 "resistance changes, then the current that the battery drives through the new wire, and then the power.",
        steps=(
            Step("Rnew", "Resistance of a uniform conductor, R = rho L / A, with the volume V = A L held constant: if the length is "
                         "multiplied by k, the area is divided by k and the resistance is multiplied by k^2",
                 "The metal and its resistivity are unchanged, so only the geometry matters: a wire k times longer is also k times "
                 "thinner in area, and both effects raise the resistance, giving k squared times the original resistance."),
            Step("I", "Ohm's law: the current in a resistor equals the voltage across it divided by its resistance, I = V/R",
                 "The drawn-out wire is connected directly across an ideal battery, so the whole emf appears across it and this "
                 "ratio gives its current."),
            Step("P", "Electric power: the rate of energy dissipation in a resistor is P = V I",
                 "The battery supplies the voltage V while the current I flows through the wire, and all of this power is dissipated as "
                 "heat in the wire, which is the quantity asked for."),
        ),
        check="The power can also be written as V squared over the new resistance, which gives the same number; stretching the wire "
              "(k larger than one) raises the resistance and lowers the power, and for k = 1 the result is V^2/R0 as for the original wire."),
    "S43": Plan(
        approach="With the battery connected the voltage is fixed, so the extra charge is the change of capacitance times the emf. "
                 "Find the fraction of the gap that the slab fills, use it to get the new capacitance, and then multiply the change "
                 "of capacitance by the emf.",
        steps=(
            Step("frac", "Geometry of the gap: the slab fills the fraction t/d of the plate separation d",
                 "The slab has the same area as the plates, so only the thickness matters; the fraction tells how much of the gap "
                 "is filled by dielectric and how much remains empty."),
            Step("C", "The capacitance of a parallel-plate capacitor is C = eps0 A / (gap), and a dielectric layer of constant kappa and "
                      "thickness t counts as an air layer of thickness t/kappa; the empty layer and the dielectric layer are in series, "
                      "so C = C0 / (1 - frac (1 - 1/kappa))",
                 "The electric field is perpendicular to the plates and so to both layers, the same charge is on every layer, and "
                 "the voltages of the two layers add; so the new capacitance follows from the empty capacitance and the fraction "
                 "filled, without knowing the plate area or eps0."),
            Step("dQ", "Definition of capacitance: Q = C V, so with the voltage held at the emf the charge changes by (C - C0) V",
                 "The battery stays connected, so the voltage is the emf both before and after the insertion; the charge was C0 V "
                 "and becomes C V, and the difference is the extra charge the battery supplies."),
        ),
        check="If the slab fills the gap completely (frac = 1) the capacitance becomes kappa C0, and if there is no dielectric "
              "(kappa = 1) or no slab (frac = 0) it stays C0 and the extra charge is zero; the answer must be positive because the "
              "capacitance rises."),
    "S44": Plan(
        approach="The rod is in equilibrium, so the upward magnetic force must equal the weight. Compute the weight first, then "
                 "use the formula for the magnetic force on a current-carrying wire to solve for the current.",
        steps=(
            Step("W", "Weight: the gravitational force on a mass m is W = m g",
                 "The magnetic force has to cancel the weight, so the weight is the force that has to be supplied; the mass must be "
                 "in kilograms and the result is in newtons."),
            Step("I", "Magnetic force on a straight current-carrying wire in a uniform field: F = I L B sin(angle), which equals I L B "
                      "when the wire is perpendicular to the field; setting F = W gives I = W/(B L)",
                 "The rod is at right angles to the field and lies entirely in it, so the force is the full product I L B, directed "
                 "upward as stated; equilibrium of the vertical forces fixes the current that the question asks for."),
        ),
        check="Doubling the field or the length must halve the required current, and doubling the mass must double it; with a field "
              "of a few tenths of a tesla and a rod a few tens of centimetres long, a current of order one ampere for a rod of a few "
              "tens of grams is reasonable."),
    "S45": Plan(
        approach="First find the speed the bead gains in the accelerating potential difference, using energy conservation. The magnetic "
                 "force then bends the path into a circle, so find the angular frequency of that motion and divide the speed by it "
                 "to get the radius.",
        steps=(
            Step("v", "Work-energy theorem for a charge in an electric field: the kinetic energy gained from rest equals the charge "
                      "times the potential difference, (1/2) m v^2 = q V",
                 "The bead starts from rest and the only force that does work is the electric force, because the magnetic force is "
                 "always perpendicular to the velocity and does no work; solving for v gives the speed on entering the field."),
            Step("wc", "Newton's second law with the Lorentz force for a charge moving perpendicular to a uniform magnetic field: "
                          "q v B = m v^2/r, which means the charge circles with angular frequency omega = q B/m",
                 "The magnetic force is perpendicular to the velocity and has constant size, so it acts as a pure centripetal force; "
                 "the angular frequency of this circular motion does not depend on the speed and is set by the charge, the mass and the "
                 "field."),
            Step("r", "Circular motion: the speed equals the angular frequency times the radius, v = omega r, so r = v/omega",
                 "Both the speed on entry and the angular frequency are known, and this relation gives the radius of the path that "
                 "the question asks for, here converted to centimetres."),
        ),
        check="The radius is r = m v/(q B), so it grows with the speed and falls as the field is increased, and it equals "
              "sqrt(2 m V/q)/B, which is the same expression with the speed eliminated; the units of r come out as metres."),
    "S46": Plan(
        approach="The rod speeds up until the magnetic braking force along the rails balances the pull of gravity along the rails. "
                 "Find the component of the field that matters for the loop, resolve the weight along the incline, and then set up "
                 "the force balance with the induced emf and current to solve for the speed.",
        steps=(
            Step("Beff", "Magnetic flux through a loop is Phi = B A cos(angle between B and the normal to the loop), so only the "
                         "component of the vertical field normal to the plane of the rails, B cos(theta), changes the flux",
                 "The field is vertical but the loop lies in the sloping plane, so the effective field for the flux and for the force "
                 "along the slope is B cos(theta); the same factor enters the induced emf and the force component along the rails."),
            Step("Fg", "Resolution of the weight on an incline: the component of the weight m g along the slope is m g sin(theta)",
                 "Only this component accelerates the rod down the rails, so at the terminal speed it is the force that the magnetic "
                 "braking force along the rails has to balance."),
            Step("v", "Faraday's law, emf = B_eff ell v, Ohm's law, I = emf/R, and the magnetic force on the rod, F = B_eff I ell along "
                      "the slope, together with force balance at constant speed: Fg = B_eff^2 ell^2 v/R, so v = Fg R/(B_eff ell)^2",
                 "As the rod moves, the area of the loop changes and an emf is induced; the resulting current feels a force that "
                 "opposes the motion (Lenz's law) and grows with speed, so the speed levels off where this force equals the component "
                 "of the weight along the slope."),
        ),
        check="At the terminal speed the power supplied by gravity, Fg v, must equal the power dissipated in the resistor, "
              "(B_eff ell v)^2/R, which is the same equation; a larger resistance (less braking current) must give a higher "
              "terminal speed, and a flat track (theta = 0) gives zero speed."),
    "S47": Plan(
        approach="An ideal transformer makes the load look like a resistor of a_squared times RL in the primary circuit, which is in "
                 "series with the generator's internal resistance. Find this reflected resistance, the primary current from the series "
                 "loop, convert it to the secondary current with the turns ratio, and then the power in the load.",
        steps=(
            Step("Rref", "Impedance reflection by an ideal transformer: with V2 = V1/a and I2 = a I1, the resistance seen at the "
                         "primary is V1/I1 = a^2 V2/I2 = a^2 R_L",
                 "The primary circuit contains the generator and the transformer, so the whole secondary circuit can be replaced by "
                 "one resistor a squared times the load resistance connected across the primary, which turns the problem into a "
                 "simple series circuit."),
            Step("I1", "Ohm's law for the series loop of the generator: the rms current equals the emf divided by the total resistance, "
                       "I = Vs/(Rs + Rref)",
                 "The generator's internal resistance and the reflected load resistance are in series with the same current, so the "
                 "primary current follows from the emf and the sum of the two resistances."),
            Step("I2", "Ideal transformer current relation: the ampere-turns are equal, N1 I1 = N2 I2, so I2 = a I1 with a = N1/N2",
                 "With more turns on the primary than on the secondary the current is stepped up in the secondary, and this gives the "
                 "rms current that flows through the load."),
            Step("P", "Joule heating in a resistor: the average power is P = I_rms^2 R",
                 "The load is purely resistive and the currents are rms values, so the average power dissipated in the load is the "
                 "square of its rms current times its resistance."),
        ),
        check="The power taken from the generator, I1^2 (Rs + Rref), minus the power lost in the internal resistance, I1^2 Rs, must "
              "equal the load power I2^2 RL, because the ideal transformer dissipates nothing; with Rs = 0 the load power would be "
              "Vs^2/(a^2 RL)."),
    "S48": Plan(
        approach="For a series RLC circuit without a source the charge obeys a damped oscillator equation. Compute the damping rate "
                 "and the undamped angular frequency, combine them into the damped angular frequency, and convert it to a frequency "
                 "in hertz.",
        steps=(
            Step("alpha", "Kirchhoff's loop rule for the series circuit, L q'' + R q' + q/C = 0, which has the damping form with "
                          "alpha = R/(2L) as the decay rate of the amplitude",
                 "Dividing the loop equation by L puts it in the standard damped-oscillator form, and the term with the first "
                 "derivative then defines the damping rate R/(2L), which is how fast the amplitude falls as e^(-alpha t)."),
            Step("w0", "The undamped LC oscillation has angular frequency omega0 = 1/sqrt(L C), from the same equation "
                         "with R = 0",
                 "The coil and capacitor alone would exchange energy at this angular frequency, and it is the restoring term in "
                 "the damped equation, so it is needed for the next step."),
            Step("wd", "Solution of the damped oscillator: q is proportional to e^(-alpha t) cos(omega_d t) with "
                       "omega_d = sqrt(omega0^2 - alpha^2) when alpha < omega0",
                 "Trying exponential solutions e^(s t) in the loop equation gives s = -alpha plus or minus i omega_d; the imaginary part "
                 "is the angular frequency of the oscillation, which is lower than omega0 because of the damping."),
            Step("fd", "Relation between frequency and angular frequency: f = omega/(2 pi)",
                 "The question asks for a frequency in hertz and the previous step gave an angular frequency in radians per second, "
                 "so dividing by two pi gives the number of oscillations per second."),
        ),
        check="With R = 0 the formula must reduce to the LC frequency 1/(2 pi sqrt(L C)), and the damped frequency must always be "
              "smaller than that; the oscillation exists only while alpha is smaller than omega0, which holds for the stated values."),
}

LEVELS: dict[str, str] = {
    "S06": "high_school", "S07": "intro_university", "S08": "intro_university", "S15": "high_school", "S16": "intro_university",
    "S25": "intro_university",
    "S41": "high_school", "S42": "high_school", "S43": "intro_university", "S44": "high_school", "S45": "intro_university",
    "S46": "intro_university", "S47": "intro_university", "S48": "upper_university",
}

TOPICS: dict[str, str] = {
    "S06": "Ohm's law and series-parallel resistor networks",
    "S07": "RC charging transient",
    "S08": "capacitors in series and stored energy",
    "S15": "power in parallel resistors",
    "S16": "RL current rise transient",
    "S25": "energy stored in an inductor",
    "S41": "Coulomb force and charge sharing between conductors",
    "S42": "resistivity, resistance of a stretched wire and electric power",
    "S43": "parallel-plate capacitor with a partial dielectric slab",
    "S44": "magnetic force on a current-carrying rod",
    "S45": "charge accelerated by a potential difference then circling in a magnetic field",
    "S46": "Faraday induction and magnetic braking of a rod on inclined rails",
    "S47": "ideal transformer, reflected resistance and rms power",
    "S48": "damped oscillations of a series RLC circuit",
}
