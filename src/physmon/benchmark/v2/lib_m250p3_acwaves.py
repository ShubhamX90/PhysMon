"""M250 phase 3, batch acwaves: ten new structures S321 to S330 (acoustics and mechanical waves) and their gold plans.

Standing waves on strings, beats, Doppler shifts with a rotating source, a moving observer and a wind, sound spreading from two sources,
waves in a heavy rope, reflection and transmission at a loaded junction of two strings, waves in a rail, water-wave group travel and the
boom of a supersonic aircraft. Same pattern as `lib_m250_waves.py`: a typed graph, an independently coded numeric solver (an arrival-time
scan, a crest-tracking root finder, a quadrature, a complex linear system for the amplitudes at a junction, a chain of masses and springs,
a complex-step derivative, a discretised string eigenproblem, a minimisation of arrival time), at least four numeric instantiations and a
relevant edit that moves the answer.

Every answer-deciding condition (initial and boundary conditions, the governing model where standard models compete, the constants the
solver uses) is stated in the prompt; the prompt carries no numeral that is not a graph input. Admission status: agent-verified, not
expert-reviewed.
"""

from __future__ import annotations

import cmath
import math

import numpy as np
from scipy.integrate import quad
from scipy.linalg import eigh_tridiagonal
from scipy.optimize import brentq, minimize_scalar

from physmon.benchmark.v2.graph import Assumption, Structure
from physmon.benchmark.v2.library import A_G, _co, _g, _in, _spec
from physmon.benchmark.v2.trace import Plan, Step

# --- solvers (independent routes; SI inputs in node order) -----------------------------------------------------------------------


def _solve_whirling_buzzer(f, r, rot, c):
    # The buzzer is at phase phi = rot t_e on its circle when it emits; the arrival time at a microphone at rest 6.1 m from the axis is
    # T(t_e) = t_e + distance / c. The frequency heard is f / (dT/dt_e), by a central difference, scanned over a whole turn and refined at
    # the highest and the lowest value.
    dist = 6.1
    step = 1e-6

    def heard(phi):
        def arrival(angle):
            return angle / rot + math.hypot(dist - r * math.cos(angle), r * math.sin(angle)) / c

        return f / ((arrival(phi + step) - arrival(phi - step)) / (2.0 * step / rot))

    grid = np.linspace(0.0, 2.0 * math.pi, 2001)
    values = np.array([heard(p) for p in grid])
    width = grid[1] - grid[0]
    top = minimize_scalar(lambda p: -heard(p), bounds=(grid[int(values.argmax())] - width, grid[int(values.argmax())] + width),
                          method="bounded", options={"xatol": 1e-12})
    bottom = minimize_scalar(heard, bounds=(grid[int(values.argmin())] - width, grid[int(values.argmin())] + width), method="bounded",
                             options={"xatol": 1e-12})
    return float(-top.fun - bottom.fun)


def _solve_wind_chase(f, c, vs, vo, w):
    # Track crests on the ground: crest n leaves the car (moving at vs from x = 0) at t = n / f and moves forward at c + w relative to
    # the road; the cyclist rides at vo from x = 100 m. The heard frequency is the inverse of the spacing of two arrivals.
    gap = 100.0

    def arrival(n):
        tn = n / f
        return brentq(lambda t: vs * tn + (c + w) * (t - tn) - gap - vo * t, tn, tn + 10.0, xtol=1e-15, rtol=1e-15)

    return float(1.0 / (arrival(4) - arrival(3)) - f)


def _solve_heavy_rope_pulse(mass, rope_mass, length, g):
    # The tension at height y above the block is (M + mu y) g and the pulse speed there is sqrt(T / mu); the time is the quadrature of
    # dy / speed over the rope.
    mu = rope_mass / length
    value, _ = quad(lambda y: 1.0 / math.sqrt((mass + mu * y) * g / mu), 0.0, length, epsabs=0.0, epsrel=1e-13)
    return float(value)


def _solve_string_junction(tension, rho, d1, d2, m, f, p0):
    # Continuity of the displacement and the force balance of the bead at the knot, written as a 2x2 complex linear system for the
    # reflected and transmitted amplitudes; the transmitted power fraction from the power carried by each wave, Z omega^2 A^2 / 2.
    w = 2.0 * math.pi * f
    k1 = w * math.sqrt(rho * math.pi * d1 ** 2 / 4.0 / tension)
    k2 = w * math.sqrt(rho * math.pi * d2 ** 2 / 4.0 / tension)
    # unknowns (r, t): 1 + r = t ; T (-i k2 t) - T (-i k1 + i k1 r) = -m w^2 t
    matrix = np.array([[1.0, -1.0], [-1j * k1 * tension, -1j * k2 * tension + m * w * w]], dtype=complex)
    rhs = np.array([-1.0, -1j * k1 * tension], dtype=complex)
    _r, t = np.linalg.solve(matrix, rhs)
    return float(p0 * (k2 / k1) * abs(t) ** 2)


def _solve_rail_gap(young, rho, dist, c):
    # A long chain of point masses joined by springs stands for the rail: spring constant E A / a and mass rho A a (A is any area); the
    # phase speed of its slowest waves is omega / k at k a = 1e-3. The gap is the arrival time through the air minus through the rail.
    area, spacing = 3.0e-3, 0.05
    spring, mass = young * area / spacing, rho * area * spacing
    ka = 1e-3
    omega = 2.0 * math.sqrt(spring / mass) * math.sin(ka / 2.0)
    speed = omega / (ka / spacing)
    return float(dist / c - dist / speed)


def _solve_two_speakers(eta, p1, r1, p2, r2):
    # The intensity of each speaker as its sound power over the area of the half sphere on hard ground, the area from a quadrature
    # of the polar angle; the powers of the two incoherent sounds add.
    def half_sphere(radius):
        value, _ = quad(lambda theta: 2.0 * math.pi * radius ** 2 * math.sin(theta), 0.0, math.pi / 2.0, epsabs=0.0, epsrel=1e-13)
        return value

    return float(eta * p1 / half_sphere(r1) + eta * p2 / half_sphere(r2))


def _solve_swell_travel_time(lam, dist, g):
    # d(omega)/dk by the complex-step derivative of the finite-depth dispersion relation omega^2 = g k tanh(k H) with a sea 6 km deep.
    k = 2.0 * math.pi / lam
    step = 1e-30
    kc = complex(k, step)
    omega = cmath.sqrt(g * kc * cmath.tanh(kc * 6000.0))
    return float(dist / (omega.imag / step))


def _eigen_fundamental(tension, mass, length, points=2400):
    # The lowest eigenvalue of the discretised string, -y'' = (omega^2 mu / T) y with fixed ends, on `points` interior points.
    h = length / (points + 1)
    mu = mass / length
    diag = np.full(points, 2.0 / h ** 2)
    off = np.full(points - 1, -1.0 / h ** 2)
    lowest = eigh_tridiagonal(diag, off, select="i", select_range=(0, 0), eigvals_only=True)[0]
    return math.sqrt(lowest * tension / mu) / (2.0 * math.pi)


def _solve_loaded_string_beat(rho_b, edge, rho_w, string_mass, length, g):
    # Archimedes from the pressure difference between the lower and the upper face of the cube (any depth); the fundamental of each string
    # as the lowest eigenvalue of its discretised wave equation; the beat is the difference of the two fundamentals.
    weight = rho_b * edge ** 3 * g
    top_depth = 0.37
    buoyancy = (rho_w * g * (top_depth + edge) - rho_w * g * top_depth) * edge ** 2
    return float(_eigen_fundamental(weight, string_mass, length) - _eigen_fundamental(weight - buoyancy, string_mass, length))


def _solve_resonance_tube(f, l1, l2, c0, t0):
    # The two successive resonances of a column closed at one end, L1 + e = lambda / 4 and L2 + e = 3 lambda / 4, as a linear system for
    # the wavelength and the end correction; then the temperature from the root of c0 sqrt(T / T0) = f lambda.
    lam, _e = np.linalg.solve(np.array([[0.25, -1.0], [0.75, -1.0]]), np.array([l1, l2]))
    speed = f * lam
    return float(brentq(lambda t: c0 * math.sqrt(t / t0) - speed, 1e-3, 1e9, xtol=1e-12, rtol=1e-14))


def _solve_sonic_boom(h, s, v, c):
    # The listener hears the first sound that arrives: the earliest of sigma / v + (path from the aircraft at sigma to the listener) / c
    # over the points sigma of the flight line (found by a bounded minimisation); that earliest arrival is the boom.
    def arrival(sigma):
        return sigma / v + math.hypot(h, s - sigma) / c

    best = minimize_scalar(arrival, bounds=(s - 40.0 * h, s + 40.0 * h), method="bounded", options={"xatol": 1e-9})
    return float(best.fun)


# --- structures --------------------------------------------------------------------------------------------------------------


def s321_whirling_buzzer_pitch_range() -> Structure:
    return Structure(
        "S321", "Spread of the pitch of a buzzer whirled on an arm and recorded at rest", "acoustics",
        "doppler_source_on_circle_extreme_frequencies",
        (_in("f", "frequency", "Hz", "frequency of the note of the buzzer", 1200.0, (500.0, 3000.0)),
         _in("r", "length", "m", "length of the arm", 0.8, (0.3, 2.0)),
         _in("rot", "angular_frequency", "rpm", "rotation rate of the arm", 240.0, (60.0, 600.0)),
         _in("c", "speed", "m/s", "speed of sound in the still air, a stated constant", 343.0, (330.0, 350.0), provenance="assumed"),
         _co("omega", "angular_frequency", "rad/s", "angular velocity of the arm", "rot"),
         _co("v", "speed", "m/s", "speed of the buzzer along its circle", "omega*r"),
         _co("fmax", "frequency", "Hz", "highest frequency recorded, from the buzzer moving straight towards the microphone",
             "f*c/(c - v)"),
         _co("fmin", "frequency", "Hz", "lowest frequency recorded, from the buzzer moving straight away from the microphone",
             "f*c/(c + v)"),
         _co("df", "frequency", "Hz", "amount by which the highest recorded frequency exceeds the lowest", "fmax - fmin")),
        "df",
        (Assumption("A-c", "The speed of sound has the stated constant value in the still air, does not depend on the frequency, and "
                           "is much greater than the speed of the buzzer.", "modelling", ("c",)),
         Assumption("A-rot", "In the relation omega = rot, rot stands for the rotation rate converted from revolutions per minute to "
                             "radians per second, that is omega = 2 pi x (rate in rpm) / 60.", "modelling", ("rot",)),
         Assumption("A-geometry", "The microphone is at rest in the plane of the circle and outside it, so that there is a point of the "
                                  "circle at which the buzzer moves directly towards the microphone and another at which it moves "
                                  "directly away; the buzzer is small and its note is steady.", "boundary_condition", ("r", "f"))),
        _spec("A small buzzer that sounds a steady note of frequency {f} Hz is fixed to the free end of a light arm of length {r} m. The "
              "arm turns at {rot} rpm in a horizontal plane about its other end, which is fixed on a vertical axis. A "
              "microphone stands at rest in the same horizontal plane, outside the circle that the buzzer traces, and the air is "
              "still. Take the speed of sound in the air as {c} m/s.",
              "By how much does the highest frequency that the microphone records from the buzzer exceed the lowest?",
              "difference between the highest and the lowest recorded frequency", "Hz",
              "A separate siren B on another hill sounds at {v} {u}, but it is unrelated to this buzzer.",
              "A reference buzzer B has a spread of {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the whirling.", "W", equivalent="kHz"),
        ("rot", 1.4), _solve_whirling_buzzer, 4,
        "the arrival time at the microphone of the sound emitted at every phase of the circle, with the heard frequency as f divided by the "
        "numerical derivative of the arrival time against the emission time, scanned over a whole turn for its highest and lowest value",
        solver_rel_tol=1e-7,
        instances=({"f": 1200.0, "r": 0.8, "rot": 240.0, "c": 343.0}, {"f": 900.0, "r": 0.6, "rot": 300.0, "c": 343.0},
                   {"f": 1500.0, "r": 1.0, "rot": 180.0, "c": 340.0}, {"f": 2000.0, "r": 0.5, "rot": 420.0, "c": 346.0}))


def s322_horn_heard_on_a_bicycle_in_a_wind() -> Structure:
    return Structure(
        "S322", "Shift of a car horn heard by a cyclist ahead of it in a following wind", "acoustics",
        "doppler_moving_source_moving_observer_with_wind",
        (_in("f", "frequency", "Hz", "frequency at which the horn sounds", 440.0, (200.0, 1200.0)),
         _in("c", "speed", "m/s", "speed of sound relative to the air, a stated constant", 343.0, (330.0, 350.0), provenance="assumed"),
         _in("vs", "speed", "m/s", "speed of the car relative to the road", 25.0, (20.0, 45.0)),
         _in("vo", "speed", "m/s", "speed of the cyclist relative to the road", 6.0, (2.0, 12.0)),
         _in("w", "speed", "m/s", "speed of the wind relative to the road, along the direction of travel", 8.0, (1.0, 15.0)),
         _co("ua", "speed", "m/s", "speed of the car relative to the air", "vs - w"),
         _co("ub", "speed", "m/s", "speed of the cyclist relative to the air", "vo - w"),
         _co("fo", "frequency", "Hz", "frequency of the horn heard by the cyclist", "f*(c - ub)/(c - ua)"),
         _co("df", "frequency", "Hz", "amount by which the heard frequency exceeds the frequency of the horn", "fo - f")),
        "df",
        (Assumption("A-medium", "The wind is uniform and steady and blows along the road in the direction of travel; the sound travels at "
                                "the stated speed relative to the moving air, whatever the speed of the source.", "modelling",
                    ("c", "w")),
         Assumption("A-motion", "While the horn is heard the car and the cyclist move at constant speeds along the same straight "
                                "line, the car behind the cyclist and faster than the cyclist, and it stays behind.", "boundary_condition", ("vs", "vo"))),
        _spec("A car whose horn sounds a steady note of frequency {f} Hz drives along a straight level road behind a cyclist who rides "
              "in the same direction. Relative to the road, the car travels at {vs} m/s and the cyclist at {vo} m/s, and the car "
              "stays behind the cyclist while the horn is heard. A steady wind blows along the road in the "
              "direction of travel at {w} m/s relative to the road. Take the speed of sound relative to the moving air as {c} m/s.",
              "By how much does the frequency of the horn that the cyclist hears exceed the frequency at which the horn sounds?",
              "amount by which the heard frequency exceeds the frequency of the horn", "Hz",
              "A separate whistle B in another town sounds at {v} {u}, but it is unrelated to this horn.",
              "A reference horn B is heard {v} {u} higher.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the sound.", "W", equivalent="kHz"),
        ("vs", 1.3), _solve_wind_chase, 5,
        "tracking successive wave crests on the road with a root finder: a crest leaves the car, moves forward at the speed of sound plus "
        "the wind speed until it meets the cyclist, and the heard frequency is the inverse of the spacing of two arrivals",
        solver_rel_tol=1e-8,
        instances=({"f": 440.0, "c": 343.0, "vs": 25.0, "vo": 6.0, "w": 8.0}, {"f": 600.0, "c": 343.0, "vs": 30.0, "vo": 8.0, "w": 5.0},
                   {"f": 350.0, "c": 340.0, "vs": 22.0, "vo": 4.0, "w": 10.0}, {"f": 800.0, "c": 346.0, "vs": 35.0, "vo": 10.0, "w": 3.0}))


def s323_pulse_up_a_rope_with_a_weight() -> Structure:
    return Structure(
        "S323", "Travel time of a pulse up a heavy rope that carries a block", "waves", "transverse_pulse_on_hanging_rope_with_end_load",
        (_in("M", "mass", "kg", "mass of the block", 2.0, (0.5, 10.0)),
         _in("mr", "mass", "kg", "mass of the rope", 1.5, (0.3, 5.0)),
         _in("L", "length", "m", "length of the rope", 12.0, (3.0, 40.0)),
         _g(),
         _co("a", "length", "m", "length of rope that has the weight of the block", "M*L/mr"),
         _co("b", "length", "m", "length of rope that has the weight of the block and the whole rope", "a + L"),
         _co("t", "time", "s", "time taken by the pulse to travel up the rope", "2*(sqrt(b) - sqrt(a))/sqrt(g)")),
        "t",
        (A_G,
         Assumption("A-rope", "The rope is uniform, flexible and inextensible, much narrower than it is long, and the tension at each "
                              "point is the weight of everything hanging below it; the pulse is small and travels at sqrt(T / mu) "
                              "where T is the local tension and mu the mass per unit length.", "modelling", ("mr", "L")),
         Assumption("A-block", "The block hangs at rest from the lower end of the rope, and the pulse starts at that end.",
                    "boundary_condition", ("M",))),
        _spec("A uniform rope of mass {mr} kg and length {L} m hangs vertically from a high fixed support, with a block of mass {M} kg "
              "tied to its lower end. The rope is flexible, inextensible and much narrower than it is long, and the block hangs at "
              "rest. A short transverse pulse of small amplitude is sent up the rope from the block. Take g = {g} m/s².",
              "How long does the pulse take to travel from the block to the support?",
              "time taken by the pulse to travel up the rope", "s",
              "A separate swing B in another park takes {v} {u} to swing across, but it is unrelated to this rope.",
              "A reference rope B carries a pulse in {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the rope.", "W", equivalent="ms"),
        ("M", 1.5), _solve_heavy_rope_pulse, 4,
        "the local tension (M + mu y) g and the local pulse speed sqrt(T / mu), integrated over the rope as a quadrature of dy / speed, "
        "instead of the closed form with square roots",
        solver_rel_tol=1e-9,
        instances=({"M": 2.0, "mr": 1.5, "L": 12.0, "g": 9.8}, {"M": 3.5, "mr": 0.8, "L": 20.0, "g": 9.8},
                   {"M": 1.2, "mr": 2.4, "L": 8.0, "g": 9.8}, {"M": 6.0, "mr": 3.0, "L": 25.0, "g": 9.8}))


def s324_power_through_a_loaded_knot() -> Structure:
    return Structure(
        "S324", "Fraction of a wave's power that passes a knot between two strings with a bead on it", "waves",
        "two_string_junction_with_point_mass_power_transmission",
        (_in("T", "force", "N", "tension of the strings", 100.0, (50.0, 300.0)),
         _in("rho", "density", "kg/m^3", "density of the steel of the strings, a stated constant", 7850.0, (7700.0, 8000.0),
             provenance="assumed"),
         _in("d1", "length", "mm", "diameter of the thin string", 0.5, (0.3, 0.8)),
         _in("d2", "length", "mm", "diameter of the thick string", 1.0, (0.8, 1.5)),
         _in("m", "mass", "g", "mass of the bead at the knot", 0.5, (0.1, 2.0)),
         _in("f", "frequency", "Hz", "frequency of the wave", 120.0, (50.0, 400.0)),
         _in("P0", "power", "mW", "power carried by the incident wave", 20.0, (5.0, 100.0)),
         _co("Z1", "mechanical_impedance", "kg/s", "wave impedance of the thin string", "sqrt(T*rho*pi*d1**2/4)"),
         _co("Z2", "mechanical_impedance", "kg/s", "wave impedance of the thick string", "sqrt(T*rho*pi*d2**2/4)"),
         _co("omega", "angular_frequency", "rad/s", "angular frequency of the wave", "2*pi*f"),
         _co("Xm", "mechanical_impedance", "kg/s", "impedance of the bead, its mass times the angular frequency", "m*omega"),
         _co("tr", "fraction", "1", "fraction of the incident power carried on along the thick string", "4*Z1*Z2/((Z1 + Z2)**2 + Xm**2)"),
         _co("Pt", "power", "mW", "power carried on along the thick string", "P0*tr")),
        "Pt",
        (Assumption("A-string", "Each string is uniform, flexible and under the stated tension, which the wave does not change; the waves "
                                "are transverse, small and in one plane, gravity is neglected, and the density of the steel has the "
                                "stated constant value.", "modelling", ("T", "rho")),
         Assumption("A-knot", "The strings are very long and nothing returns from their far ends; the bead is so small that it acts as a "
                              "point mass at the knot, where the displacement is continuous.", "boundary_condition", ("m", "d1", "d2")),
         Assumption("A-wave", "A steady sinusoidal wave travels along the thin string towards the knot, and the power is that carried by the "
                              "waves in the steady state.", "boundary_condition", ("f",))),
        _spec("Two circular steel strings of the same density {rho} kg/m³ are knotted together end to end: the thin string has diameter {d1} mm "
              "and the thick string has diameter {d2} mm. Both are uniform, flexible and stretched to the same tension of {T} N, which the "
              "waves do not change, and both are so long that nothing returns from their far ends. A small bead of mass {m} g is fixed "
              "at the knot and acts as a point mass. A steady sinusoidal transverse wave of small amplitude and frequency {f} Hz "
              "travels along the thin string towards the knot, carrying a power of {P0} mW. Gravity is neglected.",
              "What power is carried on along the thick string?",
              "power carried on along the thick string", "mW",
              "A separate amplifier B in another house delivers {v} {u}, but it is unrelated to these strings.",
              "A reference knot B passes {v} {u}.",
              "A separate lamp B is lit at {v} {u}, but it plays no part in the strings.", "Hz", equivalent="W"),
        ("m", 2.0), _solve_string_junction, 7,
        "the continuity of the displacement and the force balance of the bead at the knot written as a 2x2 complex linear system for the "
        "reflected and the transmitted amplitude, and the transmitted power from the power carried by each wave",
        solver_rel_tol=1e-9,
        instances=({"T": 100.0, "rho": 7850.0, "d1": 0.5, "d2": 1.0, "m": 0.5, "f": 120.0, "P0": 20.0},
                   {"T": 150.0, "rho": 7850.0, "d1": 0.4, "d2": 0.9, "m": 0.3, "f": 200.0, "P0": 35.0},
                   {"T": 80.0, "rho": 7800.0, "d1": 0.6, "d2": 1.2, "m": 0.8, "f": 90.0, "P0": 12.0},
                   {"T": 200.0, "rho": 7850.0, "d1": 0.35, "d2": 1.1, "m": 0.25, "f": 300.0, "P0": 50.0}))


def s325_rail_sound_before_air_sound() -> Structure:
    return Structure(
        "S325", "Gap between the sound through a rail and the sound through the air", "waves", "longitudinal_wave_in_thin_rod_versus_air",
        (_in("E", "pressure", "MPa", "Young's modulus of the steel of the rail, a stated constant", 200000.0, (100000.0, 220000.0),
             provenance="assumed"),
         _in("rho", "density", "kg/m^3", "density of the steel of the rail, a stated constant", 7800.0, (7000.0, 8000.0),
             provenance="assumed"),
         _in("d", "length", "m", "distance of the listener from the struck end", 600.0, (100.0, 2000.0)),
         _in("c", "speed", "m/s", "speed of sound in the still air, a stated constant", 343.0, (330.0, 350.0), provenance="assumed"),
         _co("vr", "speed", "m/s", "speed of a longitudinal pulse in the rail", "sqrt(E/rho)"),
         _co("ta", "time", "s", "time taken by the sound through the air", "d/c"),
         _co("tr", "time", "s", "time taken by the pulse through the rail", "d/vr"),
         _co("gap", "time", "s", "time by which the sound through the air arrives after the sound through the rail", "ta - tr")),
        "gap",
        (Assumption("A-rod", "The rail is a uniform thin rod of steel, much thinner than the length of the pulse, so a longitudinal pulse "
                             "travels along it at sqrt(E / rho); the constants have the stated values.", "modelling", ("E", "rho")),
         Assumption("A-air", "The air is still, the speed of sound has the stated constant value, and the sound through the air "
                             "travels in a straight line from the struck end to the listener at the stated distance.",
                    "boundary_condition", ("c", "d"))),
        _spec("A hammer strikes the end of one rail of a long straight railway track along its length. The rail is a uniform thin steel "
              "rod of Young's modulus {E} MPa and density {rho} kg/m³, much thinner than the pulse is long, so a longitudinal pulse "
              "travels along it at the square root of the modulus over the density. A listener presses an ear to the rail at a "
              "distance of {d} m from the struck end and hears the pulse in the rail and, later, the sound that comes through the "
              "still air along the straight line from the struck end. Take the speed of sound in the air as {c} m/s.",
              "How long after the pulse in the rail does the sound through the air arrive?",
              "time by which the sound through the air arrives after the sound through the rail", "s",
              "A separate bell B in another village rings {v} {u} apart from its echo, but it is unrelated to this rail.",
              "A reference rail B has a gap of {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the rail.", "W", equivalent="ms"),
        ("d", 1.5), _solve_rail_gap, 4,
        "a long chain of point masses joined by springs for the rail, its phase speed at long wavelength found from the dispersion "
        "relation of the chain, instead of the square root of the modulus over the density",
        solver_rel_tol=1e-6,
        instances=({"E": 200000.0, "rho": 7800.0, "d": 600.0, "c": 343.0}, {"E": 210000.0, "rho": 7850.0, "d": 450.0, "c": 340.0},
                   {"E": 190000.0, "rho": 7750.0, "d": 900.0, "c": 346.0}, {"E": 205000.0, "rho": 7800.0, "d": 300.0, "c": 343.0}))


def s326_two_loudspeakers_on_hard_ground() -> Structure:
    return Structure(
        "S326", "Sound intensity from two loudspeakers on hard ground", "acoustics", "two_incoherent_point_sources_on_hard_ground",
        (_in("eta", "fraction", "1", "fraction of the electrical power that a loudspeaker turns into sound", 0.03, (0.01, 0.1)),
         _in("p1", "power", "W", "electrical power fed to the first loudspeaker", 120.0, (20.0, 400.0)),
         _in("r1", "length", "m", "distance of the first loudspeaker from the microphone", 12.0, (4.0, 40.0)),
         _in("p2", "power", "W", "electrical power fed to the second loudspeaker", 200.0, (20.0, 400.0)),
         _in("r2", "length", "m", "distance of the second loudspeaker from the microphone", 25.0, (4.0, 60.0)),
         _co("s1", "power", "W", "sound power of the first loudspeaker", "eta*p1"),
         _co("s2", "power", "W", "sound power of the second loudspeaker", "eta*p2"),
         _co("i1", "intensity", "W/m^2", "intensity of the sound of the first loudspeaker", "s1/(2*pi*r1**2)"),
         _co("i2", "intensity", "W/m^2", "intensity of the sound of the second loudspeaker", "s2/(2*pi*r2**2)"),
         _co("i", "intensity", "W/m^2", "total intensity of the sound at the microphone", "i1 + i2")),
        "i",
        (Assumption("A-half", "Each loudspeaker is a small source on the ground that radiates uniformly into the half-space above the "
                              "hard ground, and the air does not absorb the sound.", "modelling", ("eta",)),
         Assumption("A-incoherent", "The two loudspeakers play different tones, so their sounds are incoherent and their intensities "
                                    "add; the microphone is close to the ground and is the only receiver.", "boundary_condition",
                    ("r1", "r2"))),
        _spec("Two small loudspeakers of the same model stand on flat, hard ground in an open field. Each turns a fraction {eta} of the "
              "electrical power fed to it into sound, which it radiates uniformly into the half-space above the ground; the air does "
              "not absorb the sound. The first is fed {p1} W and is {r1} m from a microphone that stands on the ground; the second "
              "is fed {p2} W and is {r2} m from the microphone. They play different tones, so the intensities of their sounds add.",
              "What is the total sound intensity at the microphone?", "total intensity of the sound at the microphone", "W/m^2",
              "A separate stage B in another park gives an intensity of {v} {u}, but it is unrelated to these loudspeakers.",
              "A reference loudspeaker B gives an intensity of {v} {u} at the microphone.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the field.", "Hz", equivalent=None),
        ("p1", 1.5), _solve_two_speakers, 5,
        "the area of the half sphere around each loudspeaker as a quadrature over the polar angle, and the intensity as the sound power "
        "over that area, instead of the formula 2 pi r squared",
        solver_rel_tol=1e-9,
        instances=({"eta": 0.03, "p1": 120.0, "r1": 12.0, "p2": 200.0, "r2": 25.0},
                   {"eta": 0.05, "p1": 80.0, "r1": 8.0, "p2": 150.0, "r2": 20.0},
                   {"eta": 0.02, "p1": 300.0, "r1": 30.0, "p2": 100.0, "r2": 15.0},
                   {"eta": 0.04, "p1": 60.0, "r1": 6.0, "p2": 250.0, "r2": 35.0}))


def s327_travel_time_of_an_ocean_swell() -> Structure:
    return Structure(
        "S327", "Time for the energy of an ocean swell to reach the coast from a distant storm", "waves", "deep_water_gravity_wave_group_travel_time",
        (_in("lam", "length", "m", "wavelength of the swell", 150.0, (50.0, 250.0)),
         _in("D", "length", "km", "distance of the storm centre out at sea, over which the swell travels to the coast", 1800.0, (500.0, 5000.0)),
         _g(),
         _co("k", "wavenumber", "1/m", "wavenumber of the swell", "2*pi/lam"),
         _co("omega", "angular_frequency", "rad/s", "angular frequency of the swell", "sqrt(g*k)"),
         _co("cg", "speed", "m/s", "group speed of the swell", "omega/(2*k)"),
         _co("t", "time", "h", "time taken by the energy of the swell to reach the coast", "D/cg")),
        "t",
        (A_G,
         Assumption("A-deep", "The ocean is much deeper than the wavelength, the waves are small gravity waves with negligible surface "
                              "tension, viscosity and wind, and the dispersion relation is omega^2 = g k.", "modelling", ("lam",)),
         Assumption("A-group", "The energy of the swell travels at the group speed d(omega)/dk along a straight line across the "
                               "stated distance of ocean, which has uniform depth.", "boundary_condition", ("D",))),
        _spec("A swell of long-crested surface waves of wavelength {lam} m travels across an ocean that is much deeper than the "
              "wavelength. The waves are small gravity waves, and surface tension, viscosity and wind are negligible, so the angular "
              "frequency and the wavenumber are related by ω² = g k. The energy of the swell travels at the group speed. The storm "
              "that raised the swell is centred {D} km out at sea, and the energy travels from it to the coast in a straight line. "
              "Take g = {g} m/s².",
              "How long does the energy of the swell take to reach the coast?",
              "time taken by the energy of the swell to reach the coast", "h",
              "A separate ferry B on another sea needs {v} {u} for its crossing, but it is unrelated to this swell.",
              "A reference swell B needs {v} {u} for the same crossing.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the swell.", "W", equivalent="min"),
        ("D", 1.5), _solve_swell_travel_time, 3,
        "the group speed as the complex-step derivative of the finite-depth dispersion relation omega^2 = g k tanh(k H) for a sea 6 km "
        "deep, instead of the deep-water closed form",
        solver_rel_tol=1e-8,
        instances=({"lam": 150.0, "D": 1800.0, "g": 9.8}, {"lam": 100.0, "D": 1200.0, "g": 9.8},
                   {"lam": 220.0, "D": 3000.0, "g": 9.8}, {"lam": 80.0, "D": 900.0, "g": 9.8}))


def s328_beat_between_a_string_in_air_and_one_in_water() -> Structure:
    return Structure(
        "S328", "Beat between two identical strings, one stretched by a cube in air and one by a cube in water", "acoustics",
        "stretched_string_fundamental_with_buoyant_load_beats",
        (_in("rb", "density", "kg/m^3", "density of each cube", 7800.0, (4000.0, 9000.0)),
         _in("a", "length", "cm", "edge of each cube", 5.0, (3.0, 7.0)),
         _in("rw", "density", "kg/m^3", "density of the water", 1000.0, (990.0, 1030.0)),
         _in("ms", "mass", "g", "mass of each string", 1.2, (0.5, 3.0)),
         _in("L", "length", "m", "vibrating length of each string", 0.8, (0.5, 1.2)),
         _g(),
         _co("V", "volume", "cm^3", "volume of a cube", "a**3"),
         _co("W", "force", "N", "weight of a cube, the tension of the string whose cube hangs in air", "rb*V*g"),
         _co("B", "force", "N", "buoyant force of the water on the immersed cube", "rw*V*g"),
         _co("Tw", "force", "N", "tension of the string whose cube is in the water", "W - B"),
         _co("f1", "frequency", "Hz", "fundamental frequency of the string whose cube hangs in air", "sqrt(W/(ms*L))/2"),
         _co("f2", "frequency", "Hz", "fundamental frequency of the string whose cube is in the water", "sqrt(Tw/(ms*L))/2"),
         _co("beat", "frequency", "Hz", "beat frequency of the two fundamentals", "f1 - f2")),
        "beat",
        (A_G,
         Assumption("A-string", "Each string is uniform, flexible and fixed at both ends of its vibrating length; its tension is the net "
                                "force of the hanging cube on it, the strings and the pulleys are light and frictionless, the "
                                "buoyancy of the air is neglected, and each string sounds its fundamental.", "modelling",
                    ("ms", "L")),
         Assumption("A-water", "The second cube is completely immersed in the water of a large tank and hangs at rest without touching "
                               "the tank; the water is at rest.", "boundary_condition", ("rw", "a"))),
        _spec("A sonometer has two identical strings, each of mass {ms} g and vibrating length {L} m. Each string is stretched by a "
              "solid cube of density {rb} kg/m³ and edge {a} cm that hangs from the end of the string over a light, frictionless "
              "pulley; the two cubes are identical. One cube hangs in the air, whose buoyancy is neglected. The other hangs at rest, "
              "completely immersed in the water of a large tank, without touching the tank; the density of the water is {rw} kg/m³. "
              "The strings are light and flexible, and each vibrates in its fundamental. Take g = {g} m/s².",
              "What beat frequency is heard when the two strings sound together?", "beat frequency of the two fundamentals", "Hz",
              "A separate organ B in another church beats at {v} {u}, but it is unrelated to these strings.",
              "A reference pair of strings B beats at {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the beating.", "W", equivalent=None),
        ("a", 1.2), _solve_loaded_string_beat, 6,
        "the buoyant force from the pressure difference between the lower and the upper face of the cube, and the fundamental of each "
        "string as the lowest eigenvalue of its discretised wave equation, instead of the closed form sqrt(T / (m L)) / 2",
        solver_rel_tol=1e-5,
        instances=({"rb": 7800.0, "a": 5.0, "rw": 1000.0, "ms": 1.2, "L": 0.8, "g": 9.8},
                   {"rb": 8500.0, "a": 4.0, "rw": 998.0, "ms": 0.9, "L": 0.7, "g": 9.8},
                   {"rb": 7200.0, "a": 6.0, "rw": 1020.0, "ms": 2.0, "L": 1.0, "g": 9.8},
                   {"rb": 5500.0, "a": 5.0, "rw": 1000.0, "ms": 1.5, "L": 0.9, "g": 9.8}))


def s329_air_temperature_from_two_resonances() -> Structure:
    return Structure(
        "S329", "Temperature of the air from two successive resonances of a tube closed by a piston", "acoustics",
        "closed_tube_two_successive_resonances_end_correction_cancels",
        (_in("f", "frequency", "Hz", "frequency of the tuning fork", 512.0, (256.0, 1024.0)),
         _in("L1", "length", "cm", "length of the air column at the first resonance", 16.0, (10.0, 30.0)),
         _in("L2", "length", "cm", "length of the air column at the second resonance", 49.5, (35.0, 100.0)),
         _in("c0", "speed", "m/s", "speed of sound in air at the reference temperature, a stated constant", 331.3, (330.0, 333.0),
             provenance="assumed"),
         _in("T0", "temperature", "K", "reference temperature of the speed of sound, a stated constant", 273.15, (273.0, 273.3),
             provenance="assumed"),
         _co("lam", "length", "cm", "wavelength of the sound in the air column", "2*(L2 - L1)"),
         _co("c", "speed", "m/s", "speed of sound in the air column", "f*lam"),
         _co("T", "temperature", "K", "temperature of the air in the tube", "T0*(c/c0)**2")),
        "T",
        (Assumption("A-c", "The speed of sound in dry air is c0 sqrt(T / T0) with the stated constants, and it does not depend on the "
                           "frequency.", "modelling", ("c0", "T0")),
         Assumption("A-tube", "The column of air is closed at the piston and open at the other end, whose end correction is the same at "
                              "both resonances; the two resonances are successive, the first being the lowest, and the whole air "
                              "column is at one temperature.", "boundary_condition", ("L1", "L2", "f"))),
        _spec("A horizontal glass tube is open at one end and closed at the other by a movable piston. A tuning fork of frequency {f} Hz "
              "sounds steadily at the open end. As the piston is drawn back from the open end, the column of air between the open end "
              "and the piston resonates loudly for the first time when it is {L1} cm long and for the second time when it is {L2} cm "
              "long. The end correction at the open end is the same at both resonances, and the air in the tube is at one "
              "temperature. Take the speed of sound in the air as c₀ √(T / T₀), with c₀ = {c0} m/s and T₀ = {T0} K.",
              "What is the temperature of the air in the tube?", "temperature of the air in the tube", "K",
              "A separate oven B in another kitchen is at {v} {u}, but it is unrelated to this tube.",
              "A reference tube B holds air at {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the tube.", "W", equivalent=None,
              formats={"c0": ".4g", "T0": ".5g"}),
        ("f", 1.1), _solve_resonance_tube, 5,
        "the two resonance conditions L1 + e = lambda / 4 and L2 + e = 3 lambda / 4 as a 2x2 linear system for the wavelength and the end "
        "correction, then the temperature as the root of c0 sqrt(T / T0) equal to the speed found",
        solver_rel_tol=1e-8,
        instances=({"f": 512.0, "L1": 16.0, "L2": 49.5, "c0": 331.3, "T0": 273.15},
                   {"f": 440.0, "L1": 18.9, "L2": 58.0, "c0": 331.3, "T0": 273.15},
                   {"f": 384.0, "L1": 22.5, "L2": 68.0, "c0": 331.5, "T0": 273.15},
                   {"f": 640.0, "L1": 13.0, "L2": 40.0, "c0": 331.3, "T0": 273.15}))


def s330_boom_heard_after_a_supersonic_flypast() -> Structure:
    return Structure(
        "S330", "Delay of the sonic boom behind a supersonic aircraft that has passed an observation post", "acoustics",
        "mach_cone_boom_arrival_time_after_overhead_passage",
        (_in("h", "length", "km", "altitude of the aircraft", 8.0, (3.0, 15.0)),
         _in("s", "length", "km", "distance of the listener from the post, along the flight direction", 3.0, (0.5, 10.0)),
         _in("v", "speed", "m/s", "speed of the aircraft", 620.0, (400.0, 900.0)),
         _in("c", "speed", "m/s", "speed of sound in the still air at every height, a stated constant", 330.0, (300.0, 345.0),
             provenance="assumed"),
         _co("M", "mach_number", "1", "Mach number of the aircraft", "v/c"),
         _co("mu", "angle", "deg", "half-angle of the cone of the shock wave", "asin(1/M)"),
         _co("x", "length", "km", "distance behind the aircraft, along its path, at which the cone meets the ground", "h/tan(mu)"),
         _co("t", "time", "s", "time after the passage over the post at which the boom reaches the listener", "(s + x)/v")),
        "t",
        (Assumption("A-c", "The air is still and the speed of sound has the stated constant value at every height, so that the sound "
                           "travels in straight lines.", "modelling", ("c",)),
         Assumption("A-flight", "The aircraft flies at constant speed along a straight horizontal line at the stated altitude, directly "
                                "over a flat horizontal ground and over the post; the listener stands on the ground below this line, "
                                "ahead of the post.", "boundary_condition", ("h", "s", "v"))),
        _spec("An aircraft flies along a straight horizontal line at a constant {v} m/s and an altitude of {h} km, directly over a flat "
              "horizontal ground, in air that is still and in which the speed of sound is {c} m/s at every height, so that sound "
              "travels in straight lines. A straight road lies on the ground under the flight line. A listener stands on the road at a "
              "distance of {s} km from an observation post, ahead of it in the direction of flight. The aircraft passes directly over "
              "the post and is moving faster than sound.",
              "How long after the aircraft passes directly over the observation post does the listener hear its sonic boom?",
              "time after the passage over the post at which the boom reaches the listener", "s",
              "A separate thunderstorm B in another valley is heard {v} {u} after its flash, but it is unrelated to this aircraft.",
              "A reference aircraft B is heard {v} {u} after its passage.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the boom.", "W", equivalent="min"),
        ("h", 1.5), _solve_sonic_boom, 4,
        "the first sound to arrive at the listener, as the earliest of (time of emission + path / speed of sound) over every point of the "
        "flight line, found by a bounded minimisation, instead of the cone geometry",
        solver_rel_tol=1e-6,
        instances=({"h": 8.0, "s": 3.0, "v": 620.0, "c": 330.0}, {"h": 6.0, "s": 2.0, "v": 560.0, "c": 335.0},
                   {"h": 10.0, "s": 5.0, "v": 800.0, "c": 320.0}, {"h": 4.0, "s": 1.5, "v": 450.0, "c": 340.0}))


ALL = (s321_whirling_buzzer_pitch_range, s322_horn_heard_on_a_bicycle_in_a_wind, s323_pulse_up_a_rope_with_a_weight,
       s324_power_through_a_loaded_knot, s325_rail_sound_before_air_sound, s326_two_loudspeakers_on_hard_ground,
       s327_travel_time_of_an_ocean_swell, s328_beat_between_a_string_in_air_and_one_in_water,
       s329_air_temperature_from_two_resonances, s330_boom_heard_after_a_supersonic_flypast)


def all_structures() -> list[Structure]:
    return [factory() for factory in ALL]


STRUCTURES: dict[str, Structure] = {s.structure_id: s for s in all_structures()}

LEVELS: dict[str, str] = {
    "S321": "upper_university", "S322": "intro_university", "S323": "upper_university", "S324": "upper_university",
    "S325": "intro_university", "S326": "intro_university", "S327": "upper_university", "S328": "upper_university",
    "S329": "intro_university", "S330": "intro_university",
}

TOPICS: dict[str, str] = {
    "S321": "Doppler shift of a source moving on a circle, extreme frequencies heard by a microphone at rest",
    "S322": "Doppler effect with a moving source, a moving observer and a wind along the line of motion",
    "S323": "transverse pulse on a heavy hanging rope with an end load, position-dependent wave speed",
    "S324": "reflection and transmission of power at a junction of two strings loaded with a point mass",
    "S325": "longitudinal waves in a rod with Young's modulus compared with sound in air",
    "S326": "sound intensity from two incoherent sources on hard ground, inverse-square spreading into a half space",
    "S327": "group speed of deep-water gravity waves and the travel time of a swell",
    "S328": "string tension from a buoyant load, fundamental frequencies and beats",
    "S329": "resonances of an air column closed by a piston, end correction cancelling, temperature from the speed of sound",
    "S330": "Mach cone of a supersonic aircraft and the arrival time of the boom",
}

# --- gold solution plans -----------------------------------------------------------------------------------------------------

PLANS: dict[str, Plan] = {
    "S321": Plan(
        approach="The microphone is at rest, so every note it records is Doppler shifted by the component of the buzzer's velocity along "
                 "the line to the microphone. The shift is greatest when the buzzer moves straight at the microphone and smallest when it "
                 "moves straight away, and both happen at points of the circle because the microphone is outside it. Find the speed of the "
                 "buzzer, then the highest and lowest frequencies, then their difference.",
        steps=(
            Step("omega", "Conversion of the rotation rate to angular velocity, omega = 2 pi x (rate in rpm) / 60",
                 "The speed along the circle needs the angular velocity in radians per second."),
            Step("v", "Speed on a circle, v = omega r",
                 "The buzzer moves on a circle of the arm's length at the angular velocity of the arm."),
            Step("fmax",
                 "Doppler effect for a source moving straight towards a stationary observer, f' = f c / (c - v)",
                 "From a point of the circle the microphone lies along the tangent, so the buzzer moves directly at it and the crests are "
                 "crowded together; this is the highest frequency."),
            Step("fmin",
                 "Doppler effect for a source moving straight away from a stationary observer, f' = f c / (c + v)",
                 "At the opposite tangent point the buzzer moves directly away and the crests are spread out; this is the lowest "
                 "frequency."),
            Step("df", "Difference of the two frequencies, f_max - f_min",
                 "The question asks by how much the highest recorded frequency exceeds the lowest."),
        ),
        check="Limiting cases: for v much smaller than c the spread is about 2 f v / c, and it vanishes when the arm is at rest. Order of "
              "magnitude: a note of 1200 Hz on a buzzer at 20 m/s spreads by about 140 Hz. The distance of the microphone does not "
              "enter, as long as it is outside the circle."),
    "S322": Plan(
        approach="Sound moves at the speed c relative to the moving air, so work in the frame of the air: find how fast the car and the "
                 "cyclist move relative to the air, apply the Doppler formula for a source and an observer moving along one line, and "
                 "subtract the frequency of the horn.",
        steps=(
            Step("ua", "Velocity transformation to the frame of the air, u = v - w",
                 "The wind carries the air along the road, so the speed of the car relative to the air is its speed over the road "
                 "minus the wind speed."),
            Step("ub", "Velocity transformation to the frame of the air, u = v - w",
                 "The same wind changes the speed of the cyclist relative to the air by the same amount."),
            Step("fo",
                 "Doppler effect for a moving source and a moving observer, f' = f (c - u_observer) / (c - u_source), speeds relative to the air",
                 "The sound has speed c in the air; the observer ahead of the source moves away from the crests at u_observer and the source "
                 "moves towards the observer at u_source."),
            Step("df", "Difference of the heard and the emitted frequency, f' - f",
                 "The question asks by how much the heard frequency exceeds the frequency at which the horn sounds."),
        ),
        check="Limiting cases: with no wind and a stationary cyclist the formula reduces to f c / (c - v), and if the car and the cyclist "
              "move at the same speed nothing changes the frequency. Only the speeds relative to the air matter, so a steady wind can "
              "change the shift only through the two differences. The distance between them does not enter."),
    "S323": Plan(
        approach="The tension of the rope is not uniform: at a point it is the weight of the block plus the rope below that point, so the "
                 "pulse speeds up as it climbs. Write the local speed, add the times for each small piece, and evaluate the sum in closed form.",
        steps=(
            Step("a", "Weight of the block expressed as a length of rope, a = M / mu with mu = m_rope / L",
                 "At a height y above the block the tension is (M + mu y) g = mu g (a + y), so a is the length of rope that weighs as "
                 "much as the block."),
            Step("b", "Total hanging length, b = a + L",
                 "At the top the tension is the weight of the block and the whole rope, which is mu g b."),
            Step("t", "Local wave speed on a string v = sqrt(T / mu) and time = integral of dy / v, giving t = 2 (sqrt(b) - sqrt(a)) / sqrt(g)",
                 "With T = mu g (a + y) the speed is sqrt(g (a + y)), and the integral of dy / sqrt(g (a + y)) from y = 0 to L is "
                 "2 (sqrt(a + L) - sqrt(a)) / sqrt(g)."),
        ),
        check="Limiting cases: with a very heavy block (a much larger than L) the tension is uniform and t tends to L / sqrt(g a); with no "
              "block (a = 0) it is 2 sqrt(L / g), the time for a pulse on a freely hanging rope. The result lies between these and is in seconds."),
    "S324": Plan(
        approach="Treat the knot as a boundary between two strings of different wave impedance with a point mass on it. The displacement is "
                 "continuous and the net force of the strings accelerates the bead, which fixes the transmitted amplitude; the power carried "
                 "by a wave is proportional to the impedance times the square of the amplitude.",
        steps=(
            Step("Z1", "Wave impedance of a string, Z = sqrt(T mu), with mu = rho pi d^2 / 4",
                 "The mass per unit length of a circular steel string follows from its density and diameter; the impedance sets how much "
                 "force a wave of a given velocity needs."),
            Step("Z2", "Wave impedance of a string, Z = sqrt(T mu), with mu = rho pi d^2 / 4",
                 "The thick string has the same density and tension but another diameter, so another impedance."),
            Step("omega", "Angular frequency of a wave, omega = 2 pi f",
                 "The bead's inertia is felt through its acceleration, which grows with the angular frequency."),
            Step("Xm", "Inertia of the bead at the knot as an impedance, X = m omega",
                 "The bead's equation of motion m times acceleration equals the net force of the strings gives, for a sinusoidal wave, an "
                 "impedance m omega in series with the second string."),
            Step("tr",
                 "Power transmission at a loaded junction, 4 Z1 Z2 / ((Z1 + Z2)^2 + (m omega)^2)",
                 "Continuity of the displacement and the force balance at the knot give the transmitted amplitude 2 Z1 / (Z1 + Z2 + i m omega); "
                 "the power ratio is Z2 / Z1 times the square of its magnitude."),
            Step("Pt", "Definition of the transmitted fraction of the power, P_t = P0 x fraction",
                 "The question asks for the power carried on along the thick string, which is the incident power times the fraction."),
        ),
        check="Limiting cases: with no bead the fraction is 4 Z1 Z2 / (Z1 + Z2)^2, which is one for equal strings; a very heavy bead (m omega "
              "much larger than the impedances) stops the wave and the power tends to zero. The power lies between zero and the incident power."),
    "S325": Plan(
        approach="A longitudinal pulse in a thin rod travels at the square root of Young's modulus over the density, which is much faster "
                 "than sound in air. Find both travel times for the stated distance and subtract.",
        steps=(
            Step("ta", "Uniform motion, t = d / c",
                 "The sound through the air travels the straight line to the listener at the speed of sound."),
            Step("vr", "Speed of longitudinal waves in a thin rod, v = sqrt(E / rho)",
                 "The rail is thin compared with the pulse, so it stretches and compresses along its length as a rod with modulus E."),
            Step("tr", "Uniform motion, t = d / v",
                 "The pulse travels along the rail the same distance at the speed of the rod wave."),
            Step("gap", "Difference of the two arrival times, t_air - t_rail",
                 "The question asks how long after the pulse in the rail the sound through the air arrives."),
        ),
        check="Order of magnitude: steel carries sound at about five kilometres per second, fifteen times faster than air, so at 600 m the "
              "rail pulse arrives in about 0.12 s and the air sound in about 1.75 s. The gap is almost the whole air time."),
    "S326": Plan(
        approach="Each loudspeaker radiates its sound power into the half space above the hard ground, so its intensity at the microphone "
                 "is the sound power over the area of a half sphere through the microphone. The two tones are incoherent, so the "
                 "intensities add.",
        steps=(
            Step("s1", "Conversion efficiency, sound power = eta x electrical power",
                 "Only the fraction eta of the electrical power fed to the first loudspeaker is radiated as sound."),
            Step("s2", "Conversion efficiency, sound power = eta x electrical power",
                 "The second loudspeaker is of the same model, so the same fraction of its electrical power becomes sound."),
            Step("i1", "Intensity of a source radiating into a half space, I = P / (2 pi r^2)",
                 "The sound spreads over a half sphere because the hard ground reflects it upwards, so the area is 2 pi r^2."),
            Step("i2", "Intensity of a source radiating into a half space, I = P / (2 pi r^2)",
                 "The same law applies to the second loudspeaker at its own distance."),
            Step("i", "Incoherent sources: the intensities add, I = I1 + I2",
                 "The loudspeakers play different tones, so there is no interference that depends on the phase and the powers add."),
        ),
        check="Limiting cases: doubling the distance of one loudspeaker divides its intensity by four, and with one loudspeaker switched "
              "off the result is the intensity of the other alone. Order of magnitude: a few watts of sound at ten metres gives a few "
              "hundredths of a milliwatt per square metre."),
    "S327": Plan(
        approach="The energy of a wave packet moves at the group speed, the derivative of the angular frequency with respect to the "
                 "wavenumber. For deep-water gravity waves the dispersion relation gives it directly, and the time is the width of the "
                 "ocean over the group speed.",
        steps=(
            Step("k", "Definition of the wavenumber, k = 2 pi / lambda",
                 "The dispersion relation is written in terms of the wavenumber, so the wavelength is converted first."),
            Step("omega", "Dispersion relation of deep-water gravity waves, omega^2 = g k",
                 "The ocean is much deeper than the wavelength and surface tension is negligible, so only gravity restores the surface."),
            Step("cg", "Group speed, c_g = d omega / dk = omega / (2 k) for omega = sqrt(g k)",
                 "The swell is a group of waves that are dispersive, so its energy moves at the derivative of omega, half the phase speed."),
            Step("t", "Uniform motion, t = D / c_g",
                 "The energy travels the straight distance of ocean at the group speed."),
        ),
        check="Limiting cases: longer waves travel faster, with c_g proportional to the square root of the wavelength, so doubling the "
              "wavelength shortens the time by a factor of the square root of two. Order of magnitude: a 150 m swell moves at about 7.7 m/s "
              "and crosses 1800 km in about two and a half days."),
    "S328": Plan(
        approach="The tension of each string is the net force of its cube: the full weight for the cube in air and the weight minus the "
                 "buoyant force for the cube in water. The fundamental frequency grows with the square root of the tension, and the "
                 "two nearby frequencies beat at their difference.",
        steps=(
            Step("V", "Volume of a cube, V = a^3", "The weight and the buoyant force both follow from the volume of a cube."),
            Step("B", "Archimedes' principle, B = rho_water V g",
                 "The cube in the water is completely immersed, so it displaces its own volume of water."),
            Step("W", "Weight of a body, W = rho V g; at rest the tension equals the weight",
                 "The cube in air hangs at rest, so the string pulls up with the full weight."),
            Step("Tw", "Equilibrium of the immersed cube, T = W - B",
                 "The cube hangs at rest, so the string supports the weight minus the buoyant force."),
            Step("f1", "Fundamental of a string fixed at both ends, f = sqrt(T / (m L)) / 2 for a string of mass m and length L",
                 "The wave speed is sqrt(T / mu) with mu = m / L, and the fundamental has half a wavelength on the string."),
            Step("f2", "Fundamental of a string fixed at both ends, f = sqrt(T / (m L)) / 2",
                 "The second string differs only in its tension."),
            Step("beat", "Beat frequency, the difference of the two frequencies, f1 - f2",
                 "Two tones with nearby frequencies produce an amplitude that oscillates at the difference frequency."),
        ),
        check="Limiting cases: with the water as dense as the cubes (rb = rw) the second tension vanishes, and with no water density the "
              "beat is zero. The ratio f2 / f1 is sqrt(1 - rw / rb) whatever the string, and the beat is f1 (1 - sqrt(1 - rw / rb)); a "
              "few hertz for a note of fifty hertz and steel cubes."),
    "S329": Plan(
        approach="A column closed at one end resonates at lengths that differ by half a wavelength, whatever the end correction. The "
                 "difference of the two lengths gives the wavelength, the fork's frequency then gives the speed of sound, and the speed "
                 "gives the temperature.",
        steps=(
            Step("lam", "Successive resonances of a column closed at one end: lengths (2n - 1) lambda / 4 minus the end correction, so L2 - L1 = lambda / 2",
                 "The end correction is the same at both resonances and cancels in the difference, so twice the difference of the lengths "
                 "is the wavelength."),
            Step("c", "Wave relation, c = f lambda",
                 "The fork sets the frequency of the sound in the column, so the speed is the frequency times the wavelength."),
            Step("T", "Speed of sound in air, c = c0 sqrt(T / T0), solved for T = T0 (c / c0)^2",
                 "The stated law links the speed of sound to the temperature of the air, so the measured speed gives the temperature."),
        ),
        check="Limiting case: at c = c0 the temperature is T0 = 273.15 K. Order of magnitude: a speed of about 343 m/s corresponds to about "
              "293 K, room temperature. A first resonance alone would need the end correction, which the two lengths avoid."),
    "S330": Plan(
        approach="A supersonic aircraft drags a cone of shock waves behind it, with half-angle arcsin(c / v). The boom is heard when the "
                 "cone reaches the listener, which happens after the aircraft has flown on a distance h / tan(mu) beyond the listener's "
                 "position. Find the Mach number, the cone angle, that distance, then the time from the post.",
        steps=(
            Step("M", "Definition of the Mach number, M = v / c", "The cone exists only for M greater than one, and its shape depends on M."),
            Step("mu", "Half-angle of the Mach cone, sin(mu) = c / v = 1 / M",
                 "Each point of the flight line emits sound that spreads in a sphere; the spheres have the envelope of a cone with this angle."),
            Step("x", "Geometry of the cone, the aircraft is h / tan(mu) ahead of the point where the cone meets the ground below it",
                 "The cone surface behind the aircraft slopes down to the ground at the angle mu to the flight line."),
            Step("t", "Uniform motion, t = (s + x) / v",
                 "The listener is s ahead of the post; the cone reaches the listener when the aircraft is x beyond the listener, so the "
                 "aircraft has then flown s + x from the post at speed v."),
        ),
        check="Limiting cases: as the speed approaches the speed of sound, mu tends to 90 degrees and x tends to zero, so the boom arrives "
              "about when the aircraft is overhead the listener; at high Mach number x tends to h M. Order of magnitude: at Mach 1.9 and "
              "8 km the cone meets the ground about 13 km behind the aircraft."),
}
