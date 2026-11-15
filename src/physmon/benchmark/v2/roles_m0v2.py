"""The M0 v2 structures: the same twelve structures as `roles_m0`, with revised specs (`roles_m0v2_a`, `roles_m0v2_b`)."""

from __future__ import annotations

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import rolevalue_v2 as r2
from physmon.benchmark.v2 import roles_m0v2_a, roles_m0v2_b

ROLE_SPECS: dict[str, r2.RoleSpecV2] = {**roles_m0v2_a.ROLE_SPECS, **roles_m0v2_b.ROLE_SPECS}
STRUCTURE_FACTORIES = {**roles_m0v2_a.STRUCTURE_FACTORIES, **roles_m0v2_b.STRUCTURE_FACTORIES}


# What the H4 trace extractor (`physmon.analysis.trace_extractor.TraceContext.target_phrases` / `target_symbols`) must read as a
# statement of the target: the target phrase of the question, its head noun, and the conventional symbols of the target
# quantity (written per structure because the default derivation from the question is unreliable for "how far", "how long" and
# the optics angle). Symbols are physically correct for the quantity; subscripts such as rms, f or 2 are handled by the extractor.
TARGET_TERMS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "S01": (("acceleration of the blocks", "acceleration"), ("a",)),
    "S02": (("speed of the block", "speed"), ("v",)),
    "S07": (("voltage across the capacitor", "voltage", "potential difference"), ("V", "V_C", "VC")),
    "S13": (("period of one full oscillation", "period"), ("T",)),
    "S15": (("total power", "power"), ("P",)),
    "S20": (("image distance", "distance from the lens", "distance"), ("d_i", "di", "s_i", "v")),
    "S26": (("angle of refraction", "refraction angle", "angle"), ("theta_2", "θ_2", "theta2", "θ2", "theta_r", "θ_r")),
    "S27": (("absolute pressure", "pressure"), ("P", "p")),
    "S30": (("time", "duration"), ("t",)),
    "S55": (("root-mean-square speed", "rms speed", "speed"), ("v_rms", "v")),
    "S72": (("de Broglie wavelength", "wavelength"), ("lambda", "λ")),
    "S92": (("tension in the string", "tension"), ("T",)),
}


def structure(structure_id: str) -> gr.Structure:
    return STRUCTURE_FACTORIES[structure_id]()
