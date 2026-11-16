"""M250 phase 2, batch waves: ten new DECOY-v2 structures S231 to S240 (waves, acoustics, optics, fluids) and their gold plans.

Same pattern as `lib_fluids.py`: a typed graph, an independently coded numeric solver (a crest-tracking root finder, a complex-step
derivative, a boundary-condition linear system for the Fresnel amplitudes, a ray trace of the zigzag, an ODE with an event, a quadrature,
a Jones-matrix product, a Bernoulli root), at least four numeric instantiations and a relevant edit that moves the answer.

Every answer-deciding condition (initial and boundary conditions, the governing model where standard models compete) is stated in the
prompt; the prompt carries no numeral that is not a graph input. Admission status: agent-verified, not expert-reviewed.
"""

from __future__ import annotations

import cmath
import math

import numpy as np
from scipy.integrate import quad, solve_ivp
from scipy.optimize import brentq

from physmon.benchmark.v2.graph import Assumption, Structure
from physmon.benchmark.v2.library import A_G, _co, _g, _in, _spec
from physmon.benchmark.v2.trace import Plan, Step

# --- solvers (independent routes; SI inputs in node order) -----------------------------------------------------------------------


def _solve_echo_beat(f, v, c):
    # Track crests: crest n leaves the loudspeaker at t = n/f, meets the wall (found with a root finder), and its echo returns at
    # the speed of sound; the echo frequency is the inverse of the spacing of two consecutive echo arrivals.
    x0 = 100.0

    def arrival(n):
        tn = n / f
        hit = brentq(lambda t: c * (t - tn) - (x0 - v * t), tn, tn + 2.0 * x0 / c, xtol=1e-15, rtol=1e-15)
        return hit + (x0 - v * hit) / c

    f_echo = 1.0 / (arrival(4) - arrival(3))
    return float(f_echo - f)


def _solve_ripple_group_speed(lam, sigma, rho, g):
    # d(omega)/dk by the complex-step derivative of omega(k) = sqrt(g k + sigma k^3 / rho).
    k = 2.0 * math.pi / lam
    step = 1e-30
    omega = cmath.sqrt(g * complex(k, step) + sigma * complex(k, step) ** 3 / rho)
    return float(omega.imag / step)


def _solve_fresnel_power(p0, theta, n):
    # Continuity of the tangential electric and magnetic fields at the surface as a 2x2 complex linear system for (r, t), then the
    # transmitted power fraction from the Poynting flux.
    cos_i = math.cos(theta)
    cos_t = cmath.sqrt(1.0 - (math.sin(theta) / n) ** 2)
    matrix = np.array([[-cos_i, -cos_t], [1.0, -n]], dtype=complex)
    rhs = np.array([-cos_i, -1.0], dtype=complex)
    _r, t = np.linalg.solve(matrix, rhs)
    return float(p0 * (n * cos_t / cos_i * abs(t) ** 2).real)


def _solve_rod_transit(length, n, theta, c):
    # Trace the zigzag leg by leg between the sides of a rod of arbitrary width and add up the path length.
    width = 3.7e-3
    ky = math.sin(theta) / n
    kx = math.sqrt(1.0 - ky * ky)
    x, path, transverse = 0.0, 0.0, width / 2.0
    while True:
        leg = transverse / ky
        advance = leg * kx
        if x + advance >= length:
            path += (length - x) / kx
            break
        x += advance
        path += leg
        transverse = width
    return float(n * path / c)


def _solve_float_period(rho_b, h, rho_l, g):
    # Newton's second law for the draught with the exact buoyant force (submerged volume), released from rest below equilibrium;
    # the period is four times the time to the first crossing of the equilibrium draught.
    area = 0.0123
    mass = rho_b * area * h

    def net_up(depth):
        return rho_l * g * area * min(max(depth, 0.0), h) - mass * g

    d_eq = brentq(net_up, 1e-9, h, xtol=1e-15, rtol=1e-15)

    def crossed(t, y):
        return y[0] - d_eq

    crossed.terminal = True
    crossed.direction = 1
    solution = solve_ivp(lambda t, y: [y[1], -net_up(y[0]) / mass], (0.0, 100.0), [0.75 * d_eq, 0.0], events=crossed,
                         rtol=1e-12, atol=1e-14)
    return float(4.0 * solution.t_events[0][0])


def _solve_helmholtz(volume, length, radius, beta, c):
    # Gas-spring oscillator: the neck plug (mass rho A Leff) on the adiabatic stiffness rho c^2 A^2 / V, integrated as an ODE; the
    # frequency is the inverse of four times the time to the first zero of the displacement.
    rho = 1.2
    area = math.pi * radius ** 2
    mass = rho * area * (length + 2.0 * beta * radius)
    stiffness = rho * c ** 2 * area ** 2 / volume

    def zero(t, y):
        return y[0]

    zero.terminal = True
    solution = solve_ivp(lambda t, y: [y[1], -stiffness / mass * y[0]], (0.0, 10.0), [1e-3, 0.0], events=zero, rtol=1e-12,
                         atol=1e-15)
    return float(1.0 / (4.0 * solution.t_events[0][0]))


def _solve_slope_crossing(distance, h1, h2, g):
    # The travel time as the quadrature of dx / c(x) along the uniformly sloping seabed.
    def depth(x):
        return h1 + (h2 - h1) * x / distance

    value, _ = quad(lambda x: 1.0 / math.sqrt(g * depth(x)), 0.0, distance, epsabs=0.0, epsrel=1e-13)
    return float(value)


def _solve_couette_power(eta, length, r1, r2, omega):
    # The torque from the angular-velocity drop across the gap, omega = (T / (2 pi L eta)) * integral of dr / r^3, by quadrature.
    integral, _ = quad(lambda r: 1.0 / r ** 3, r1, r2, epsabs=0.0, epsrel=1e-13)
    torque = omega / (integral / (2.0 * math.pi * length * eta))
    return float(torque * omega)


def _solve_retarder_power(p0, dn, thickness, wavelength, alpha):
    # Jones calculus: x-polarised light through a retarder rotated by alpha, then an analyser that passes y.
    delta = 2.0 * math.pi * dn * thickness / wavelength
    rotation = np.array([[math.cos(alpha), -math.sin(alpha)], [math.sin(alpha), math.cos(alpha)]])
    plate = rotation @ np.diag([1.0, cmath.exp(1j * delta)]) @ rotation.T
    out = plate @ np.array([1.0, 0.0])
    return float(p0 * abs(out[1]) ** 2)


def _solve_siphon_crest(rho, crest, drop, p0, g):
    # The speed as the root of the Bernoulli balance between the reservoir surface and the open outlet, then Bernoulli again from the
    # surface to the highest point.
    speed = brentq(lambda v: (p0 + rho * g * drop) - (p0 + 0.5 * rho * v * v), 0.0, 100.0, xtol=1e-14, rtol=1e-14)
    return float(p0 - rho * g * crest - 0.5 * rho * speed * speed)


# --- structures --------------------------------------------------------------------------------------------------------------


def s231_echo_beat_approaching_wall() -> Structure:
    return Structure(
        "S231", "Beat frequency between a tone and its echo from an approaching wall", "waves", "doppler_echo_beat_from_moving_wall",
        (_in("f", "frequency", "Hz", "frequency of the tone", 440.0, (200.0, 1500.0)),
         _in("v", "speed", "m/s", "speed of the wall", 3.0, (0.5, 8.0)),
         _in("c", "speed", "m/s", "speed of sound in the still air, a stated constant", 343.0, (330.0, 350.0), provenance="assumed"),
         _co("f1", "frequency", "Hz", "frequency of the sound that reaches the wall", "f*(c + v)/c"),
         _co("f2", "frequency", "Hz", "frequency of the echo at the microphone", "f1*c/(c - v)"),
         _co("beat", "frequency", "Hz", "beat frequency between the tone and the echo", "f2 - f")),
        "beat",
        (Assumption("A-c", "The speed of sound has the stated constant value in the still air and does not depend on the frequency.",
                    "modelling", ("c",)),
         Assumption("A-wall", "The wall moves at constant speed along the line to the loudspeaker and reflects the sound straight "
                              "back with no change of frequency in its own frame; the air is still.", "boundary_condition", ("v", "f"))),
        _spec("A loudspeaker at rest in still air emits a steady tone of frequency {f} Hz. A large flat wall, facing the loudspeaker, "
              "moves directly towards it at a constant speed of {v} m/s and reflects the sound straight back. A microphone beside the "
              "loudspeaker records the tone together with the echo. Take the speed of sound in the still air as {c} m/s.",
              "What is the beat frequency between the tone and the echo that the microphone records?",
              "beat frequency between the tone and the echo", "Hz",
              "A separate organ pipe B in another hall sounds at {v} {u}, but it is unrelated to this loudspeaker.",
              "A reference loudspeaker B beats at {v} {u}.",
              "A separate sensor B reads {v} {u}, but it plays no part in the sound.", "W", equivalent="kHz"),
        ("v", 1.5), _solve_echo_beat, 3,
        "tracking successive wave crests with a root finder: the time each crest meets the moving wall, the return of its echo at the "
        "speed of sound, and the echo frequency as the inverse of the spacing of two consecutive echo arrivals",
        solver_rel_tol=1e-8,
        instances=({"f": 440.0, "v": 3.0, "c": 343.0}, {"f": 512.0, "v": 2.5, "c": 343.0}, {"f": 880.0, "v": 1.8, "c": 340.0},
                   {"f": 300.0, "v": 4.0, "c": 343.0}))


def s232_ripple_group_speed() -> Structure:
    return Structure(
        "S232", "Group speed of gravity-capillary ripples on deep water", "waves", "gravity_capillary_group_speed_deep_water",
        (_in("lam", "length", "cm", "wavelength of the ripples", 3.0, (1.0, 10.0)),
         _in("sigma", "surface_tension", "N/m", "surface tension of the water", 0.0728, (0.03, 0.08)),
         _in("rho", "density", "kg/m^3", "density of the water", 998.0, (900.0, 1100.0)),
         _g(),
         _co("k", "wavenumber", "1/m", "wavenumber of the ripples", "2*pi/lam"),
         _co("w", "angular_frequency", "rad/s", "angular frequency of the ripples", "sqrt(g*k + sigma*k**3/rho)"),
         _co("cg", "speed", "m/s", "group speed of the ripples", "(g + 3*sigma*k**2/rho)/(2*w)")),
        "cg",
        (A_G,
         Assumption("A-deep", "The water is deep (its depth is much greater than the wavelength), the waves have small amplitude and "
                              "the viscosity is negligible, so the dispersion relation is w^2 = g k + sigma k^3 / rho.",
                    "boundary_condition", ("lam", "sigma", "rho")),
         Assumption("A-group", "The group speed is d(w)/dk, the speed at which the energy of a narrow packet of these ripples travels.",
                    "modelling", ("lam",))),
        _spec("Small-amplitude ripples of wavelength {lam} cm travel across the surface of a deep tank of water of density {rho} kg/m³ "
              "and surface tension {sigma} N/m. The water is much deeper than the wavelength and its viscosity is negligible. Both "
              "gravity and surface tension act to restore the surface. Take g = {g} m/s².",
              "What is the group speed of the ripples?", "group speed of the ripples", "m/s",
              "A separate boat B in another harbour moves at {v} {u}, but it is unrelated to these ripples.",
              "A reference ripple pattern B has a group speed of {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the ripples.", "W", equivalent="cm/s"),
        ("lam", 0.5), _solve_ripple_group_speed, 4,
        "the group speed as the derivative d(omega)/dk of the dispersion relation, taken numerically with a complex-step derivative",
        solver_rel_tol=1e-9,
        instances=({"lam": 3.0, "sigma": 0.0728, "rho": 998.0, "g": 9.8}, {"lam": 4.0, "sigma": 0.0662, "rho": 983.0, "g": 9.8},
                   {"lam": 2.0, "sigma": 0.0626, "rho": 972.0, "g": 9.8}, {"lam": 5.0, "sigma": 0.0589, "rho": 958.0, "g": 9.8}))


def s233_fresnel_p_transmitted_power() -> Structure:
    return Structure(
        "S233", "Power entering glass for p-polarised light at oblique incidence", "optics", "fresnel_p_polarised_transmitted_power",
        (_in("P0", "power", "mW", "power of the incident beam", 5.0, (1.0, 50.0)),
         _in("theta", "angle", "deg", "angle of incidence, measured from the normal", 75.0, (5.0, 85.0)),
         _in("n", "refractive_index", "1", "refractive index of the glass", 1.5, (1.2, 2.0)),
         _co("thetat", "angle", "deg", "angle of refraction in the glass", "asin(sin(theta)/n)"),
         _co("rp", "amplitude_ratio", "1", "Fresnel amplitude reflection coefficient for p-polarised light",
             "(n*cos(theta) - cos(thetat))/(n*cos(theta) + cos(thetat))"),
         _co("R", "reflectance", "1", "fraction of the power that is reflected", "rp**2"),
         _co("Pt", "power", "mW", "power that enters the glass", "P0*(1 - R)")),
        "Pt",
        (Assumption("A-air", "The light travels in air, whose refractive index is taken as one, and the glass is homogeneous and "
                             "non-magnetic.", "modelling", ("n",)),
         Assumption("A-pol", "The electric field of the beam lies in the plane of incidence and only the first surface of the glass is "
                             "considered; the glass does not absorb light.", "boundary_condition", ("theta", "P0"))),
        _spec("A beam of light of power {P0} mW is polarised with its electric field in the plane of incidence. It travels in air and "
              "strikes the flat surface of a block of glass of refractive index {n} at an angle of incidence of {theta} degrees, "
              "measured from the normal. The glass does not absorb light, and only the first surface of the block is considered.",
              "What power enters the glass through this surface?", "power that enters the glass", "mW",
              "A separate laser B in another room emits {v} {u}, but it is unrelated to this beam.",
              "A reference beam B has a power of {v} {u}.",
              "A separate sensor B reads {v} {u}, but it plays no part in the beam.", "Hz", equivalent="W"),
        ("P0", 1.5), _solve_fresnel_power, 3,
        "the amplitudes of the reflected and transmitted waves as the solution of a 2x2 complex linear system from continuity of the "
        "tangential electric and magnetic fields, then the transmitted power from the Poynting flux",
        solver_rel_tol=1e-9,
        instances=({"P0": 5.0, "theta": 75.0, "n": 1.5}, {"P0": 8.0, "theta": 70.0, "n": 1.52}, {"P0": 3.0, "theta": 80.0, "n": 1.7},
                   {"P0": 12.0, "theta": 65.0, "n": 1.46}))


def s234_glass_rod_transit_time() -> Structure:
    return Structure(
        "S234", "Transit time of a light pulse along a glass rod by total internal reflection", "optics",
        "totally_internally_reflected_ray_transit_time",
        (_in("L", "length", "m", "length of the rod", 2.0, (0.5, 5.0)),
         _in("n", "refractive_index", "1", "refractive index of the glass", 1.8, (1.6, 2.0)),
         _in("theta", "angle", "deg", "angle of incidence on the end face, measured from the axis", 40.0, (10.0, 60.0)),
         _in("c", "speed", "km/s", "speed of light in vacuum, a stated constant", 300000.0, (299000.0, 300000.0), provenance="assumed"),
         _co("thr", "angle", "deg", "angle between the ray in the glass and the axis", "asin(sin(theta)/n)"),
         _co("ell", "length", "m", "length of the zigzag path along the rod", "L/cos(thr)"),
         _co("t", "time", "ns", "time taken by the pulse", "n*ell/c")),
        "t",
        (Assumption("A-c", "The speed of light in vacuum has the stated constant value, air has the refractive index of vacuum, and the "
                           "glass has no dispersion.", "modelling", ("c", "n")),
         Assumption("A-tir", "The pulse is totally internally reflected at the sides, so it travels without loss along the zigzag path "
                             "and the pulse travels at c/n in the glass.", "boundary_condition", ("L", "theta"))),
        _spec("A straight glass rod of length {L} m and refractive index {n} has flat, polished ends and polished sides. A narrow pulse "
              "of light in air strikes the centre of one end face at an angle of incidence of {theta} degrees to the axis of the rod, "
              "enters the glass, and is totally internally reflected at the sides until it reaches the other end. Take the speed of "
              "light in vacuum as {c} km/s.",
              "How long does the pulse take to travel from one end of the rod to the other?", "time taken by the pulse", "ns",
              "A separate pulse B in another rod takes {v} {u}, but it is unrelated to this rod.",
              "A reference rod B delays a pulse by {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the rod.", "W", equivalent="μs"),
        ("L", 1.5), _solve_rod_transit, 4,
        "a ray trace of the zigzag leg by leg between the sides of a rod of arbitrary width, adding up the path length, instead of the "
        "unfolded closed form L / cos",
        solver_rel_tol=1e-9,
        instances=({"L": 2.0, "n": 1.8, "theta": 40.0, "c": 300000.0}, {"L": 1.5, "n": 1.75, "theta": 30.0, "c": 300000.0},
                   {"L": 2.5, "n": 1.85, "theta": 55.0, "c": 299800.0}, {"L": 1.2, "n": 1.7, "theta": 35.0, "c": 300000.0}))


def s235_floating_cylinder_period() -> Structure:
    return Structure(
        "S235", "Period of vertical bobbing of a floating cylinder", "fluids", "floating_cylinder_vertical_oscillation_period",
        (_in("rho_b", "density", "kg/m^3", "density of the cylinder", 650.0, (400.0, 850.0)),
         _in("h", "length", "cm", "length of the cylinder", 30.0, (15.0, 80.0)),
         _in("rho_l", "density", "kg/m^3", "density of the liquid", 1000.0, (900.0, 1300.0)),
         _g(),
         _co("d0", "length", "cm", "equilibrium depth of the submerged part", "rho_b*h/rho_l"),
         _co("w", "angular_frequency", "rad/s", "angular frequency of the vertical oscillation", "sqrt(g/d0)"),
         _co("T", "time", "s", "period of the vertical oscillation", "2*pi/w")),
        "T",
        (A_G,
         Assumption("A-float", "The cylinder floats upright, partly submerged, and moves only vertically; the liquid is in a large tank "
                               "and the amplitude is small enough that the cylinder stays partly in and partly out of the liquid.",
                    "boundary_condition", ("rho_b", "h")),
         Assumption("A-drag", "Drag, surface effects and the motion of the liquid are neglected, so only gravity and the buoyant force "
                              "act.", "modelling", ("rho_l",))),
        _spec("A uniform cylinder of density {rho_b} kg/m³ and length {h} cm floats upright, partly submerged, in a large tank of a "
              "liquid of density {rho_l} kg/m³. It is pushed down slightly and released, and then bobs up and down vertically. Neglect "
              "drag and the motion of the liquid. Take g = {g} m/s².",
              "What is the period of the vertical oscillation of the cylinder?", "period of the vertical oscillation", "s",
              "A separate pendulum B in another laboratory has a period of {v} {u}, but it is unrelated to this cylinder.",
              "A reference float B oscillates with a period of {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the bobbing.", "W", equivalent="ms"),
        ("h", 1.5), _solve_float_period, 4,
        "Newton's second law for the draught with the exact buoyant force from the submerged volume, integrated as an ODE from rest below "
        "equilibrium; the period is four times the time to the first crossing of the equilibrium draught",
        solver_rel_tol=1e-6,
        instances=({"rho_b": 650.0, "h": 30.0, "rho_l": 1000.0, "g": 9.8}, {"rho_b": 700.0, "h": 25.0, "rho_l": 1000.0, "g": 9.8},
                   {"rho_b": 500.0, "h": 40.0, "rho_l": 1100.0, "g": 9.8}, {"rho_b": 600.0, "h": 50.0, "rho_l": 1030.0, "g": 9.8}))


def s236_helmholtz_resonance() -> Structure:
    return Structure(
        "S236", "Resonance frequency of a flask with a narrow neck", "waves", "helmholtz_resonator_frequency_end_correction",
        (_in("V", "volume", "L", "volume of the flask", 1.5, (0.5, 5.0)),
         _in("l", "length", "cm", "length of the neck", 4.0, (1.0, 10.0)),
         _in("a", "length", "cm", "radius of the neck", 1.2, (0.5, 2.5)),
         _in("beta", "coefficient", "1", "end correction at each end of the neck, in neck radii", 0.85, (0.6, 1.0),
             provenance="assumed"),
         _in("c", "speed", "m/s", "speed of sound in the air, a stated constant", 343.0, (330.0, 350.0), provenance="assumed"),
         _co("A", "area", "cm^2", "cross-section area of the neck", "pi*a**2"),
         _co("Leff", "length", "cm", "effective length of the air plug in the neck", "l + 2*beta*a"),
         _co("f", "frequency", "Hz", "resonance frequency of the flask", "c*sqrt(A/(V*Leff))/(2*pi)")),
        "f",
        (Assumption("A-end", "The effective length of the plug is the neck length plus the stated multiple of the neck radius at each "
                             "end; the speed of sound has the stated constant value.", "modelling", ("beta", "c")),
         Assumption("A-lumped", "The air in the neck moves as a rigid plug on the adiabatic cushion of the air in the flask, and the "
                                "flask is much smaller than the wavelength of the sound.", "boundary_condition", ("V", "l", "a"))),
        _spec("A flask of volume {V} L has a cylindrical neck of length {l} cm and radius {a} cm that opens to the air. The air in the "
              "neck moves as a rigid plug, with an effective length equal to the neck length plus {beta} times the neck radius at each "
              "end, and it compresses the air in the flask adiabatically. The flask is much smaller than the wavelength of the sound it "
              "makes. The speed of sound in the air is {c} m/s.",
              "What is the resonance frequency of the flask?", "resonance frequency of the flask", "Hz",
              "A separate tuning fork B in another room sounds at {v} {u}, but it is unrelated to this flask.",
              "A reference flask B resonates at {v} {u}.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the resonance.", "W", equivalent="kHz"),
        ("V", 1.5), _solve_helmholtz, 5,
        "a gas-spring oscillator, the neck plug on the adiabatic stiffness, integrated as an ODE with an event at the first zero of the "
        "displacement, instead of the closed form of the resonance frequency",
        solver_rel_tol=1e-6,
        instances=({"V": 1.5, "l": 4.0, "a": 1.2, "beta": 0.85, "c": 343.0}, {"V": 2.0, "l": 6.0, "a": 1.0, "beta": 0.85, "c": 343.0},
                   {"V": 1.0, "l": 3.0, "a": 0.9, "beta": 0.85, "c": 340.0}, {"V": 2.5, "l": 5.0, "a": 1.5, "beta": 0.85, "c": 343.0}))


def s237_tsunami_slope_crossing() -> Structure:
    return Structure(
        "S237", "Crossing time of a tsunami over a uniformly sloping continental shelf", "waves", "shallow_water_wave_travel_time_over_slope",
        (_in("D", "length", "km", "horizontal length of the slope", 60.0, (10.0, 200.0)),
         _in("h1", "length", "m", "depth of the sea at the seaward end", 200.0, (100.0, 1000.0)),
         _in("h2", "length", "m", "depth of the sea at the landward end", 20.0, (5.0, 100.0)),
         _g(),
         _co("c1", "speed", "m/s", "wave speed at the seaward end", "sqrt(g*h1)"),
         _co("c2", "speed", "m/s", "wave speed at the landward end", "sqrt(g*h2)"),
         _co("t", "time", "min", "time taken by a wave crest to cross the slope", "2*D/(c1 + c2)")),
        "t",
        (A_G,
         Assumption("A-shallow", "The wavelength is much greater than the depth, so the wave is a shallow-water wave of local speed "
                                 "sqrt(g h); its height, refraction and reflection are neglected.", "modelling", ("h1", "h2")),
         Assumption("A-slope", "The depth changes linearly with horizontal distance from the stated value at the seaward end to the "
                               "stated value at the landward end.", "boundary_condition", ("D",))),
        _spec("A tsunami of very long wavelength approaches the shore over a continental shelf that slopes uniformly: across a horizontal "
              "distance of {D} km the depth of the sea falls steadily from {h1} m at the seaward end to {h2} m at the landward end. "
              "Treat the wave as a shallow-water wave that travels at the speed sqrt(g h) set by the local depth h, and neglect its "
              "height, refraction and reflection. Take g = {g} m/s².",
              "How long does a wave crest take to cross this slope?", "time taken by a wave crest to cross the slope", "min",
              "A separate swell B in another ocean needs {v} {u} to cross, but it is unrelated to this tsunami.",
              "A reference wave B takes {v} {u} for the same slope.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the crossing.", "W", equivalent="s"),
        ("h2", 2.0), _solve_slope_crossing, 4,
        "the travel time as the quadrature of dx / c(x) along the sloping seabed, with the local depth linear in x",
        solver_rel_tol=1e-9,
        instances=({"D": 60.0, "h1": 200.0, "h2": 20.0, "g": 9.8}, {"D": 40.0, "h1": 150.0, "h2": 15.0, "g": 9.8},
                   {"D": 90.0, "h1": 300.0, "h2": 25.0, "g": 9.8}, {"D": 50.0, "h1": 250.0, "h2": 30.0, "g": 9.8}))


def s238_couette_viscometer_power() -> Structure:
    return Structure(
        "S238", "Power to turn the rotor of a concentric-cylinder viscometer", "fluids", "couette_viscometer_driving_power",
        (_in("eta", "viscosity", "Pa*s", "dynamic viscosity of the oil", 0.4, (0.05, 2.0)),
         _in("L", "length", "cm", "length of the rotor", 10.0, (3.0, 20.0)),
         _in("R1", "length", "mm", "radius of the rotor", 20.0, (10.0, 30.0)),
         _in("R2", "length", "mm", "inner radius of the fixed cylinder", 22.0, (11.0, 45.0)),
         _in("rot", "angular_frequency", "rpm", "rotation rate of the rotor", 120.0, (10.0, 600.0)),
         _co("omega", "angular_frequency", "rad/s", "angular velocity of the rotor", "rot"),
         _co("T", "torque", "N*m", "torque on the rotor",
             "4*pi*eta*L*omega*R1**2*R2**2/(R2**2 - R1**2)"),
         _co("P", "power", "W", "power needed to turn the rotor", "T*omega")),
        "P",
        (Assumption("A-couette", "The oil is Newtonian and sticks to both surfaces, its flow is steady, laminar and purely azimuthal, "
                                 "and end effects are neglected.", "boundary_condition", ("eta", "R1", "R2")),
         Assumption("A-rpm", "The rotation rate in revolutions per minute is converted to the angular velocity omega = 2 pi rot / 60.",
                    "modelling", ("rot",))),
        _spec("A cylindrical rotor of radius {R1} mm and length {L} cm is turned at {rot} rpm about its axis inside a fixed, coaxial "
              "hollow cylinder of inner radius {R2} mm. The gap between them is filled with oil of viscosity {eta} Pa·s, which sticks "
              "to both surfaces. The flow of the oil is steady and laminar, and end effects are negligible.",
              "What power is needed to keep the rotor turning at this rate?", "power needed to turn the rotor", "W",
              "A separate heater B in another room dissipates {v} {u}, but it is unrelated to this rotor.",
              "A reference motor B delivers {v} {u}.",
              "A separate sensor B reads {v} {u}, but it plays no part in the viscometer.", "Hz", equivalent="mW"),
        ("rot", 1.5), _solve_couette_power, 5,
        "the torque from the drop of the angular velocity across the gap, omega = (T / (2 pi L eta)) times the integral of dr / r^3, "
        "evaluated by quadrature, then power as torque times angular velocity",
        solver_rel_tol=1e-9,
        instances=({"eta": 0.4, "L": 10.0, "R1": 20.0, "R2": 22.0, "rot": 120.0},
                   {"eta": 0.25, "L": 8.0, "R1": 15.0, "R2": 16.5, "rot": 200.0},
                   {"eta": 0.8, "L": 12.0, "R1": 25.0, "R2": 27.0, "rot": 90.0},
                   {"eta": 0.15, "L": 6.0, "R1": 18.0, "R2": 19.5, "rot": 300.0}))


def s239_retarder_between_crossed_polarisers() -> Structure:
    return Structure(
        "S239", "Light through a birefringent plate between crossed polarisers", "optics", "wave_plate_jones_crossed_analyser_power",
        (_in("P0", "power", "mW", "power of the incident light", 8.0, (1.0, 20.0)),
         _in("dn", "refractive_index_difference", "1", "difference of the refractive indices of the slow and fast axes", 0.0092,
             (0.005, 0.02)),
         _in("d", "length", "μm", "thickness of the plate", 24.0, (5.0, 100.0)),
         _in("lam", "length", "nm", "wavelength of the light", 589.0, (400.0, 800.0)),
         _in("alpha", "angle", "deg", "angle between the fast axis and the polarisation of the light", 30.0, (5.0, 80.0)),
         _co("delta", "phase", "rad", "phase difference between the two axes", "2*pi*dn*d/lam"),
         _co("s", "fraction", "1", "factor sin^2 of half the phase difference", "sin(delta/2)**2"),
         _co("P", "power", "mW", "power that passes the analyser", "P0*sin(2*alpha)**2*s")),
        "P",
        (Assumption("A-plate", "The plate does not absorb or reflect light and its two axes differ only in refractive index; the light "
                               "crosses it at normal incidence.", "modelling", ("dn", "d")),
         Assumption("A-pol", "The incident light is linearly polarised along the x axis and the analyser passes only light polarised "
                             "along the y axis.", "boundary_condition", ("P0", "alpha", "lam"))),
        _spec("Light of wavelength {lam} nm and power {P0} mW, linearly polarised along the x axis, crosses a thin birefringent plate "
              "at normal incidence. The plate has a thickness of {d} μm, its two axes differ in refractive index by {dn}, and its fast "
              "axis makes an angle of {alpha} degrees with the x axis. The plate does not absorb light. The light then meets an "
              "analyser that passes only light polarised along the y axis.",
              "What power passes the analyser?", "power that passes the analyser", "mW",
              "A separate laser B in another room emits {v} {u}, but it is unrelated to this plate.",
              "A reference beam B passes {v} {u}.",
              "A separate sensor B reads {v} {u}, but it plays no part in the optics.", "Hz", equivalent="W"),
        ("P0", 1.5), _solve_retarder_power, 5,
        "Jones calculus: the x-polarised field through the rotated retarder matrix, then the y component of the output field squared",
        solver_rel_tol=1e-9,
        instances=({"P0": 8.0, "dn": 0.0092, "d": 24.0, "lam": 589.0, "alpha": 30.0},
                   {"P0": 6.0, "dn": 0.0091, "d": 28.0, "lam": 633.0, "alpha": 35.0},
                   {"P0": 10.0, "dn": 0.0092, "d": 18.0, "lam": 532.0, "alpha": 20.0},
                   {"P0": 4.0, "dn": 0.009, "d": 55.0, "lam": 589.0, "alpha": 40.0}))


def s240_siphon_crest_pressure() -> Structure:
    return Structure(
        "S240", "Pressure at the highest point of a siphon", "fluids", "siphon_crest_absolute_pressure_bernoulli",
        (_in("rho", "density", "kg/m^3", "density of the liquid", 1000.0, (700.0, 1300.0)),
         _in("H", "length", "m", "height of the highest point above the reservoir surface", 1.5, (0.5, 3.0)),
         _in("h", "length", "m", "depth of the outlet below the reservoir surface", 0.8, (0.3, 2.0)),
         _in("p0", "pressure", "kPa", "atmospheric pressure", 101.3, (95.0, 105.0)),
         _g(),
         _co("v", "speed", "m/s", "speed of the liquid in the tube", "sqrt(2*g*h)"),
         _co("pdyn", "pressure", "kPa", "dynamic pressure of the moving liquid", "rho*v**2/2"),
         _co("pc", "pressure", "kPa", "absolute pressure of the liquid at the highest point", "p0 - rho*g*H - pdyn")),
        "pc",
        (A_G,
         Assumption("A-ideal", "The liquid is incompressible and flows steadily without friction through a tube of uniform bore that "
                               "stays full, and the reservoir is so large that its level does not fall.", "modelling", ("rho", "h")),
         Assumption("A-atm", "The surface of the reservoir and the outlet are both open to the atmosphere at the stated pressure.",
                    "boundary_condition", ("p0", "H"))),
        _spec("A siphon is a tube of uniform bore filled with a liquid of density {rho} kg/m³. It rises from a large open reservoir to "
              "its highest point {H} m above the reservoir surface and then falls to an open outlet {h} m below that surface. The liquid "
              "flows steadily without friction and is incompressible, and the atmospheric pressure is {p0} kPa. Take g = {g} m/s².",
              "What is the absolute pressure of the liquid at the highest point of the tube?",
              "absolute pressure of the liquid at the highest point", "kPa",
              "A separate boiler B in another plant runs at {v} {u}, but it is unrelated to this siphon.",
              "A reference siphon B has a pressure of {v} {u} at its highest point.",
              "A separate lamp B is rated at {v} {u}, but it plays no part in the flow.", "W", equivalent="Pa"),
        ("H", 1.5), _solve_siphon_crest, 5,
        "the speed as the root of the Bernoulli balance between the surface and the outlet, then Bernoulli again from the surface to the "
        "highest point for the pressure",
        solver_rel_tol=1e-9,
        instances=({"rho": 1000.0, "H": 1.5, "h": 0.8, "p0": 101.3, "g": 9.8}, {"rho": 850.0, "H": 1.2, "h": 0.6, "p0": 101.0, "g": 9.8},
                   {"rho": 1100.0, "H": 2.0, "h": 1.0, "p0": 100.0, "g": 9.8}, {"rho": 920.0, "H": 0.9, "h": 1.4, "p0": 102.0, "g": 9.8}))


ALL = (s231_echo_beat_approaching_wall, s232_ripple_group_speed, s233_fresnel_p_transmitted_power, s234_glass_rod_transit_time,
       s235_floating_cylinder_period, s236_helmholtz_resonance, s237_tsunami_slope_crossing, s238_couette_viscometer_power,
       s239_retarder_between_crossed_polarisers, s240_siphon_crest_pressure)


def all_structures() -> list[Structure]:
    return [factory() for factory in ALL]


STRUCTURES: dict[str, Structure] = {s.structure_id: s for s in all_structures()}

# --- gold solution plans -----------------------------------------------------------------------------------------------------

PLANS: dict[str, Plan] = {
    "S231": Plan(
        approach="The wall is a moving receiver of the tone and then a moving source of the echo, so the Doppler effect acts twice. "
                 "First find the frequency that the approaching wall receives, then the frequency of the echo that it sends back to "
                 "the stationary microphone, and finally the difference between the echo and the original tone, which is the beat.",
        steps=(
            Step("f1",
                 "Doppler effect for a stationary source and an observer moving towards it at speed v: f1 = f (c + v) / c",
                 "The wall moves towards the loudspeaker, so it meets the crests more often than they are emitted. Taking the wall "
                 "as the observer of the stationary source gives the frequency that the wall receives."),
            Step("f2",
                 "Doppler effect for a source (the wall, re-emitting the sound) moving towards a stationary observer: f2 = f1 c / (c - v)",
                 "The wall re-emits the sound it received at the frequency f1, and as a source moving towards the microphone it "
                 "crowds the crests together. The combination of the two shifts is f2 = f (c + v) / (c - v)."),
            Step("beat",
                 "Beat frequency of two superposed tones: the difference of their frequencies, f2 - f",
                 "The microphone records the original tone and the echo together. Two tones of nearby frequencies give an "
                 "amplitude that oscillates at the difference frequency, which is the beat asked for."),
        ),
        check="Limiting case: for v much smaller than c the beat is about 2 f v / c, and it is zero when the wall is at rest. Order of "
              "magnitude: 440 Hz with a wall at 3 m/s gives about 8 Hz. The distance to the wall does not enter at all."),
    "S232": Plan(
        approach="Ripples with a wavelength of a few centimetres are restored by gravity and by surface tension. The group speed is "
                 "the slope of the dispersion relation, so write the angular frequency as a function of the wavenumber and "
                 "differentiate it.",
        steps=(
            Step("k", "Definition of the wavenumber, k = 2 pi / lambda",
                 "The dispersion relation of waves on deep water is written in terms of the wavenumber, so the wavelength is "
                 "converted to k first."),
            Step("w",
                 "Dispersion relation of gravity-capillary waves on deep water, w^2 = g k + sigma k^3 / rho",
                 "The water is much deeper than the wavelength, so the depth does not enter. Gravity gives the term g k and the "
                 "surface tension gives sigma k^3 / rho; both restore the surface, and their sum is w^2."),
            Step("cg",
                 "Group speed as the derivative of the angular frequency, cg = dw/dk = (g + 3 sigma k^2 / rho) / (2 w)",
                 "A narrow packet of ripples carries its energy at the group speed, d(w)/dk, which differs from the phase speed w/k "
                 "because the waves are dispersive. Differentiating w^2 = g k + sigma k^3 / rho gives 2 w dw = (g + 3 sigma k^2 / rho) dk."),
        ),
        check="Limiting cases: for long waves (surface tension negligible) cg tends to half the phase speed, sqrt(g / k) / 2; for very "
              "short waves cg tends to three halves of the phase speed. The units are m/s."),
    "S233": Plan(
        approach="At oblique incidence the reflected fraction of a p-polarised beam depends on the angle, so use Snell's law for the "
                 "angle in the glass, the Fresnel amplitude coefficient for p-polarisation, then the reflected fraction of the power; "
                 "the rest enters the glass.",
        steps=(
            Step("thetat", "Snell's law, sin(theta_t) = sin(theta) / n",
                 "The Fresnel coefficient needs the angle of the refracted ray in the glass, and the light goes from air, of "
                 "index one, into the glass of index n."),
            Step("rp",
                 "Fresnel equation for the amplitude reflection coefficient of p-polarised light, "
                 "r_p = (n cos(theta) - cos(theta_t)) / (n cos(theta) + cos(theta_t))",
                 "The electric field lies in the plane of incidence, so the p-polarisation formula applies; it follows from "
                 "continuity of the tangential electric and magnetic fields at the surface."),
            Step("R", "The reflectance is the square of the amplitude coefficient, R = r_p^2",
                 "The power carried by a wave is proportional to the square of its amplitude, and the incident and reflected waves "
                 "are in the same medium, so the reflected fraction of the power is r_p squared."),
            Step("Pt", "Conservation of energy at a non-absorbing surface, P_t = P0 (1 - R)",
                 "The glass does not absorb light and only the first surface is considered, so whatever is not reflected enters the "
                 "glass; this is the power asked for."),
        ),
        check="Limiting cases: at normal incidence R = ((n - 1) / (n + 1))^2 and r_p vanishes at Brewster's angle arctan(n), where all "
              "of the power enters. The result lies between zero and the incident power P0."),
    "S234": Plan(
        approach="The pulse zigzags down the rod by total internal reflection, so its path is longer than the rod. Find the angle of the "
                 "ray in the glass from Snell's law, then the length of the path, then the time at the speed of light in the glass.",
        steps=(
            Step("thr", "Snell's law at the end face, sin(theta) = n sin(theta_r), with theta_r measured from the axis",
                 "The ray enters the glass through the flat end, whose normal is the axis of the rod, so the angle of incidence and "
                 "the angle of refraction are both measured from the axis."),
            Step("ell", "Geometry of the zigzag: each reflection leaves the angle with the axis unchanged, so the path length is L / cos(theta_r)",
                 "Total internal reflection at the sides only reverses the transverse component of the motion; the axial component "
                 "of each leg adds up to the length of the rod, so the path is the rod length divided by the cosine of the angle. "
                 "The width of the rod does not matter."),
            Step("t", "Speed of light in a medium, v = c / n, and time = path / speed",
                 "The pulse travels the whole zigzag path in glass at c / n, so the time is the path length times n divided by the "
                 "speed of light in vacuum."),
        ),
        check="Limiting case: at normal incidence the path is the rod length and the time is n L / c. The time grows with the angle of "
              "incidence because the path lengthens. Order of magnitude: two metres of glass takes about ten nanoseconds."),
    "S235": Plan(
        approach="A floating cylinder bobs like a mass on a spring: the buoyant force changes by the weight of the displaced liquid for "
                 "each extra length submerged. Find the equilibrium depth, then the angular frequency of the oscillation, then the period.",
        steps=(
            Step("d0", "Archimedes' principle and equilibrium of a floating body, rho_l g A d0 = rho_b g A h",
                 "The cylinder floats at rest, so the buoyant force equals its weight; the cross-section area A cancels, leaving "
                 "the submerged length d0 = rho_b h / rho_l."),
            Step("w",
                 "Newton's second law with a restoring force proportional to the displacement: m y'' = -rho_l g A y, so w^2 = g / d0",
                 "A small vertical displacement y changes the submerged volume by A y, so the net force is -rho_l g A y. With the "
                 "mass m = rho_b A h this is simple harmonic motion with w^2 = rho_l g / (rho_b h) = g / d0."),
            Step("T", "Period of simple harmonic motion, T = 2 pi / w",
                 "The motion is simple harmonic as long as the cylinder stays partly submerged, so the period follows from the "
                 "angular frequency and does not depend on the amplitude."),
        ),
        check="Limiting case: a cylinder that is nearly as dense as the liquid floats deep (d0 close to h) and oscillates more slowly, with "
              "the period of a pendulum of length d0, T = 2 pi sqrt(d0 / g). The result does not depend on the radius or on the amplitude."),
    "S236": Plan(
        approach="The flask is a Helmholtz resonator: the air in the neck is a mass and the air in the flask is a spring. The resonance "
                 "frequency follows from the neck area, the effective neck length and the flask volume.",
        steps=(
            Step("A", "Area of a circle, A = pi a^2",
                 "The neck has a circular cross-section, and its area sets both the mass of the moving plug and the stiffness of the "
                 "air cushion."),
            Step("Leff", "Effective length of the plug including the end corrections, Leff = l + 2 beta a",
                 "The air just outside each end of the neck also moves, so the plug is longer than the neck by the stated multiple "
                 "of the radius at each end."),
            Step("f",
                 "Resonance of a mass on a gas spring, w^2 = (rho c^2 A^2 / V) / (rho A Leff), so f = (c / 2 pi) sqrt(A / (V Leff))",
                 "A displacement x of the plug changes the pressure in the flask adiabatically by rho c^2 A x / V, giving a "
                 "restoring force rho c^2 A^2 x / V on the plug of mass rho A Leff. The density cancels, and the frequency is "
                 "w / 2 pi."),
        ),
        check="Dimensional check: m/s times the square root of m^2 / (m^3 m) is 1/s. Scaling: a larger flask or a longer neck lowers the "
              "frequency, and a wider neck raises it. Order of magnitude: a one-litre bottle hums at about one hundred hertz."),
    "S237": Plan(
        approach="A shallow-water wave travels at sqrt(g h), which changes along the slope. The crossing time is the integral of the "
                 "distance divided by the local speed, and with a depth that is linear in the distance this integral has a simple form.",
        steps=(
            Step("c1", "Speed of a shallow-water wave, c = sqrt(g h)",
                 "The wavelength is much greater than the depth, so the speed depends only on the local depth; this is the speed at "
                 "the seaward end."),
            Step("c2", "Speed of a shallow-water wave, c = sqrt(g h)",
                 "The same relation at the landward end, where the water is shallow and the wave is much slower."),
            Step("t",
                 "Travel time as an integral, t = integral of dx / c(x), with h linear in x, which gives t = 2 D / (c1 + c2)",
                 "Because h varies linearly with x, dx / sqrt(g h) integrates to 2 (sqrt(h1) - sqrt(h2)) D / ((h1 - h2) sqrt(g)), "
                 "and this equals 2 D / (c1 + c2). It is the time for a crest to cross the slope, expressed here in minutes."),
        ),
        check="Bounds: the crossing time lies between D / c1 and D / c2. Limiting case: if h2 equalled h1 the speed would be uniform "
              "and the time would be D / c1. The slow shallow end dominates the time."),
    "S238": Plan(
        approach="In the narrow gap the oil shears; the torque that the rotor must overcome is fixed by the viscosity and the velocity "
                 "profile between the cylinders. Find the angular velocity, the viscous torque for steady laminar flow, then the power.",
        steps=(
            Step("omega", "Conversion of the rotation rate, omega = 2 pi N / 60",
                 "The viscous torque is written with the angular velocity in radians per second, so the rotation rate in "
                 "revolutions per minute is converted first."),
            Step("T",
                 "Viscous shear stress tau = eta r d(omega)/dr in steady azimuthal flow gives the torque T = 4 pi eta L omega R1^2 R2^2 / (R2^2 - R1^2)",
                 "The torque transmitted through every cylindrical layer of oil is the same, so tau 2 pi r L r is constant and the "
                 "angular velocity falls as 1 / r^2 between the sticking surfaces of the rotor and the outer cylinder. Fitting the "
                 "boundary values omega at R1 and zero at R2 gives the torque."),
            Step("P", "Power of a torque turning at angular velocity omega, P = T omega",
                 "The rotor turns steadily, so the driving power equals the rate at which the viscous torque is overcome."),
        ),
        check="Limiting case: for a narrow gap the torque reduces to 2 pi eta L omega R^3 / (gap), the plane Couette result. The power "
              "grows as the square of the rotation rate and in proportion to the viscosity and length."),
    "S239": Plan(
        approach="A retarder rotated against the polarisation splits the light into two components, delays one of them by a phase "
                 "difference, and the crossed analyser makes them interfere. Find the phase difference, its interference factor, then "
                 "the power.",
        steps=(
            Step("delta", "Phase difference accumulated across a birefringent plate, delta = 2 pi dn d / lambda",
                 "The slow axis has the higher index, so the light along it is delayed by dn d over the plate; in units of the "
                 "wavelength this gives the phase difference."),
            Step("s", "Interference factor of two equal-amplitude components, sin^2(delta / 2)",
                 "The analyser projects the two components onto the y axis, where they have equal and opposite signs; their "
                 "phase difference delta makes the sum of their fields proportional to sin(delta / 2)."),
            Step("P", "Jones calculus for a rotated retarder between crossed polarisers, P = P0 sin^2(2 alpha) sin^2(delta / 2)",
                 "The component of the x-polarised field along each axis is cos(alpha) and sin(alpha); projecting both on y and "
                 "adding with the phase difference gives an amplitude sin(2 alpha) sin(delta / 2), so the power is its square times P0."),
        ),
        check="Limiting cases: with the axis along x or y (alpha zero or ninety degrees) nothing passes, and with a phase difference "
              "of pi (a half-wave plate) at forty-five degrees all of the power passes. The result never exceeds P0."),
    "S240": Plan(
        approach="The liquid flows at the speed set by the drop to the outlet, and at the highest point its pressure is the atmospheric "
                 "pressure minus the pressure needed to lift the liquid and to give it kinetic energy. Find the speed first, then the "
                 "dynamic pressure, then Bernoulli's equation to the highest point.",
        steps=(
            Step("v", "Bernoulli's equation between the reservoir surface and the open outlet, both at atmospheric pressure: v = sqrt(2 g h)",
                 "The reservoir is large, so the surface speed is zero, and both ends are at atmospheric pressure, so the whole drop "
                 "h of the outlet below the surface goes into kinetic energy. The speed of the liquid is the same everywhere in a "
                 "tube of uniform bore."),
            Step("pdyn", "Dynamic pressure of a moving liquid, rho v^2 / 2",
                 "At the highest point the liquid moves at the same speed, so part of its energy per volume is kinetic, and the "
                 "pressure falls by this amount in addition to the hydrostatic part."),
            Step("pc",
                 "Bernoulli's equation between the surface and the highest point, p0 = p_c + rho g H + rho v^2 / 2",
                 "The highest point is H above the surface, so the liquid is lifted against gravity and moves with speed v; the "
                 "absolute pressure there is p0 minus the hydrostatic term minus the dynamic term."),
        ),
        check="Limiting case: with no flow (h tending to zero) the pressure reduces to the hydrostatic value p0 - rho g H. The "
              "pressure must stay positive, and above the vapour pressure of the liquid, for the siphon to work."),
}

LEVELS: dict[str, str] = {
    "S231": "intro_university", "S232": "upper_university", "S233": "upper_university", "S234": "intro_university",
    "S235": "intro_university", "S236": "upper_university", "S237": "intro_university", "S238": "upper_university",
    "S239": "upper_university", "S240": "intro_university",
}

TOPICS: dict[str, str] = {
    "S231": "double Doppler shift of an echo from a moving wall and the beat frequency",
    "S232": "dispersion and group speed of gravity-capillary ripples on deep water",
    "S233": "Fresnel reflection of p-polarised light at oblique incidence",
    "S234": "total internal reflection in a glass rod and the transit time of a pulse",
    "S235": "buoyancy and the simple harmonic bobbing of a floating cylinder",
    "S236": "Helmholtz resonance of a flask with a neck, with end corrections",
    "S237": "shallow-water wave speed and the crossing time over a sloping seabed",
    "S238": "viscous torque in a concentric-cylinder viscometer",
    "S239": "Jones calculus for a birefringent plate between crossed polarisers",
    "S240": "Bernoulli's equation and the pressure at the crest of a siphon",
}
