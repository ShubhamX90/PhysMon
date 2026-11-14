#!/usr/bin/env python3
"""Stage 15 (G1, LLM review panel): build the requalification bank v5 for judge prompt v3.

Bank v5 is an unseen requalification set (split "requal") for prompt v3 (prompt v2 plus one sentence in rule 3: a false
claim by the authors is `high` whatever it is about). It repeats neither kind of key error found in bank v4 (J15.1-024):
F-909, a "valid" pendulum rewrite that states neither "simple" nor "small amplitude", and R-580, an "ideal" deletion that
does not decide the rms speed. Two safeguards are built in:

* Safeguard A (every planted under-specification): the script computes the answer under a concrete, physically standard
  alternative that the deletion allows and requires it to differ from the certified answer by more than 5% relative;
  the alternative and its answer are written to the key (`alternative`). A candidate that fails is dropped (and listed in
  the manifest). A deletion of a condition that rule 1 of the prompt exempts is dropped as well.
* Safeguard B (every item, and in particular every valid control): the conditions that decide the answer are listed per
  family or structure (`FAMILY_CONDITIONS`, `M0_CONDITIONS`) and each must be stated in every rendering, or be waived for
  a stated reason (a rule-1 standard idealisation, or a condition that cannot change the answer at the stated
  precision). A candidate that fails is not used for any item, so every defective item carries its declared defect only.
  The screened list, with reasons, is written to the manifest.

Composition (32 items: 22 defective, 10 valid):
1. 16 fresh legacy-style injections (`physmon.validation.defect_injection`) on DECOY-v1 families used neither by the
   14.5 planted bank, its genuine sample, nor bank v4's fresh items: 3 contradictory distractor, 3 numerical precision,
   1 each of hidden coupling, removed variable, inconsistent units, invalid parameter domain; 6 valid rewrites.
2. 6 condition deletions (3 boundary condition, 3 missing assumption) on unused v1 family texts or M0 problem texts,
   none of them one of bank v4's six (structure, edit) pairs.
3. 6 role-format plants (`rolevalue_bank.plant`) of the two false-claim types that prompt v3 targets
   (3 rendering_not_minimal, 3 failed_transformation_identity), on (structure, type) pairs used in neither bank v3 nor
   bank v4, each built on a certified instance never used in banks v3 or v4; and 4 valid role items on M0 bases not used as valid items in bank v4, each built on a certified instance
   never used in banks v3 or v4 (so its pass-1 text differs from every item a judge has seen).
Accepted terms are frozen per type as in s178/s186, except that a numerical-precision item whose displayed answer is
off by more than the stated precision also accepts `failed_transformation_identity` (decided before any v5 run).
Outputs as bank v4 (pass1/pass2 packets, key_RESTRICTED.json, manifest.json); refuses to overwrite; every packet is
scanned for key fields. Thresholds: `qualification_protocol_v3.md`.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import itertools
import json
import math
import random
import re
import sys
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

import sympy  # noqa: E402

from physmon.benchmark.v2 import roles_m0  # noqa: E402
from physmon.validation import defect_injection as di  # noqa: E402
from physmon.validation import rolevalue_bank as rb  # noqa: E402


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


s145 = _load("s145", "scripts/v2/s145_validation_materials.py")
s178 = _load("s178", "scripts/v2/s178_build_judge_bank.py")
s186 = _load("s186", "scripts/v2/s186_build_requal_bank.py")

SEED = 5151
LLM_PANEL = REPO_ROOT / "docs/validation/v2/llm_panel"
BANK_V3, BANK_V4 = LLM_PANEL / "bank_v3", LLM_PANEL / "bank_v4"
V2_MATERIALS = REPO_ROOT / "docs/validation/v2/materials/v2"
SPLIT = "requal"
DECIDED = "decided 2026-11-14, before any judge has seen bank v5 or prompt v3"

WANT_FRESH = {"contradictory_distractor_statement": 3, "invalid_numerical_precision": 3, "hidden_coupling": 1,
              "relevant_variable_removed_from_equation": 1, "inconsistent_units": 1, "invalid_parameter_domain": 1,
              "valid_equivalent_rewrite": 6}
WANT_DELETIONS = {"insufficient_boundary_condition": 3, "missing_assumption": 3}
WANT_ROLE_PLANTS = {"rendering_not_minimal": 3, "failed_transformation_identity": 3}
WANT_ROLE_VALID = 4
MIN_ALTERNATIVE_SHIFT = 0.05  # Safeguard A: relative change of the answer under the alternative
FALSE_CLAIM_TYPES = ("rendering_not_minimal", "failed_transformation_identity")
# bank v4's six condition deletions (s186.ROLE_CONDITION_EDITS): (structure, deleted phrase); none may recur
V4_DELETIONS = {(sid, old) for sid, (old, *_rest) in s186.ROLE_CONDITION_EDITS.items()}
V3_V4_INSTANCE = 0  # s178 and s186 build every role item with rolevalue_bank.base_item's default instance


# ---------------------------------------------------------------------------------------------------------------------
# Safeguard B: rule 1 of the prompt (every condition that decides the answer is stated)
# ---------------------------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Cond:
    """A condition that decides the answer. It passes when `stated_by` (a regex) matches every rendering of the item,
    or when it is waived for the stated reason (`waived`: a rule-1 standard idealisation of the apparatus, or a
    condition that cannot change the answer at the stated precision). Neither: the candidate fails."""

    condition: str
    stated_by: str | None = None
    waived: str | None = None


NON_REL = "non-relativistic speed: v/c < 1e-7, the relativistic answer agrees to better than 1e-13"
IDEAL_SOURCE = "rule 1: ideal batteries, sources and wires need not be stated unless a resistance is given"
PENDULUM = (Cond("simple pendulum (a point-like bob on a light string)"), Cond("small amplitude (T depends on it)"))
PERP = Cond("force perpendicular to the lever arm (tau = r F sin(theta))", r"\bperpendicular\b")
FAMILY_CONDITIONS: dict[str, tuple[str, tuple[Cond, ...]]] = {
    "CM_A_001": ("v = v0 + a t", (Cond("initial velocity", r"initially moving at \d"),
                                  Cond("acceleration along the motion ('undergoes constant acceleration' does not say "
                                       "speeding up; a deceleration gives -1 m/s)"))),
    "CM_A_002": ("x = v0 t + a t^2/2", (Cond("initial speed", r"starts with speed \d"),
                                        Cond("acceleration along the motion (a deceleration reverses the object and "
                                             "changes the distance)"))),
    "CM_A_007": ("F = m v^2 / r", (Cond("speed on the circle (uniform motion)", r"at constant speed \d"),)),
    "CM_A_STD_001": ("v = v0 + a t", (Cond("initial velocity", r"starts at \d"),
                                      Cond("acceleration along the motion", r"\baccelerates at \d"))),
    "CM_A_STD_002": ("x = v0 t + a t^2/2", (Cond("initial velocity", r"begins at \d"),
                                            Cond("acceleration along the motion", r"\baccelerates at \d"))),
    "CM_A_STD_003": ("K = m v^2 / 2", (Cond("non-relativistic motion", waived=NON_REL),)),
    "CM_A_STD_004": ("F = k x", (Cond("linear (Hookean) spring", r"has constant \d"),)),
    "CM_A_STD_005": ("F = m v^2 / r", ()),  # m v^2 / r at the stated speed needs nothing else
    "CM_A_STD_006": ("p = m v", (Cond("non-relativistic motion", waived=NON_REL),)),
    "CM_A_STD_008": ("W = F d", (Cond("force along the displacement (W = F d cos(theta))"),)),
    "CM_A_STD_009": ("tau = r F", (PERP,)),
    "CM_A_STD_010": ("v = f lambda", ()),
    "CM_A_STD_013": ("Q = C V", ()),
    "CM_A_STD_015": ("F = k q1 q2 / r^2", (Cond("point (or spherically symmetric) charges"),
                                           Cond("medium", r"Use k = "))),
    "CM_B_002": ("v = v0 + a t", (Cond("initial velocity", r"starts at speed \d"),
                                  Cond("acceleration along the motion", r"\baccelerates at \d"))),
    "CM_B_005": ("F = k x", (Cond("linear (Hookean) spring", r"spring constant \d"),)),
    "CM_B_006": ("p = m v", (Cond("non-relativistic motion", waived=NON_REL),)),
    "CM_B_007": ("F = m v^2 / r", (Cond("speed on the circle (uniform motion)", r"at constant speed \d"),)),
    "CM_B_010": ("tau = r F", (PERP,)),
    "CM_B_STD_003": ("alpha = tau / I", (Cond("the braking torque is the net torque",
                                              waived="rule 1: frictionless axles are a standard idealisation"),)),
    "CM_B_STD_013": ("F = G M m / r^2", (Cond("r measured from the planet's centre", r"orbits a planet .*at radius"),)),
    "CM_B_STD_014": ("F = G M m / r^2", (Cond("point masses, distance measured from the centre of the central mass"),)),
    "CM_B_UM_002": ("F_net = m a", ()),
    "CM_B_UM_004": ("f = mu_k m g", (Cond("horizontal surface (normal force m g)", r"horizontal surface"),
                                     Cond("sliding (kinetic friction)", r"\bslides\b"))),
    "CM_B_UM_005": ("T = m g", (Cond("bucket not accelerating", r"hangs motionless"),
                                Cond("light rope", waived="rule 1: light, inextensible strings"))),
    "CM_B_UM_007": ("F = m g sin(theta)", ()),
    "CM_B_UM_008": ("F_b = rho V g", (Cond("displaced volume", r"displaces \d"),)),
    "CM_B_UM_009": ("v = u + a t", (Cond("initial velocity", r"starts at \d"),
                                    Cond("acceleration along the motion", r"accelerates uniformly at \d"))),
    "CM_B_UM_011": ("v = g t", (Cond("released from rest", r"dropped from rest"),
                                Cond("free fall (no drag)", r"falls freely"))),
    "CM_B_UM_012": ("v = f lambda", ()),
    "CM_B_UM_013": ("v = 2 pi r / T", (Cond("uniform circular motion (otherwise 'the speed' is not one number)"),)),
    "CM_B_UM_016": ("I = P / V", ()),
    "CM_B_UM_019": ("I = emf / R", (Cond("battery internal resistance", r"negligible internal resistance"),)),
    "CM_B_UM_022": ("V = P / I", ()),
    "CM_B_UM_024": ("V = Q / C", ()),
    "CM_B_UM_027": ("tau = r F", (PERP,)),
    "CM_B_UM_029": ("tau = r F", (PERP,)),
    "CM_B_UM_030": ("tau = r F", (PERP,)),
    "CM_B_UM_033": ("f = sqrt(g / L) / (2 pi)", PENDULUM),
    "CM_B_UM_037": ("Q = C V", (Cond("capacitor charged to the source voltage", waived=IDEAL_SOURCE),)),
    "CM_B_UM_038": ("Q = C V", (Cond("capacitor charged to the source voltage", waived=IDEAL_SOURCE),)),
    "CM_B_UM_039": ("Q = C V", (Cond("capacitor charged to the source voltage", waived=IDEAL_SOURCE),)),
    "CM_B_UM_040": ("Q = C V", (Cond("capacitor charged to the source voltage", waived=IDEAL_SOURCE),)),
    "CM_B_UM_042": ("v_rel = v_A - v_frame", (Cond("directions of the two velocities (opposite directions give 35 "
                                                   "m/s)"),)),
    "CM_B_UM_046": ("v_cm = R omega", (Cond("rolling without slipping", r"rolls without slipping"),)),
    "CM_B_UM_050": ("f = sqrt(k / m) / (2 pi)", (Cond("massless spring (a spring's mass lowers the frequency; light "
                                                      "springs are not among rule 1's exemptions)"),)),
    "CM_B_UM_055": ("f = sqrt(g / L) / (2 pi)", PENDULUM),
    "CM_B_UM_056": ("f1 = v / (2 L)", (Cond("both ends of the string fixed (one free end gives v / (4 L))"),)),
    "EL_A_002": ("P = I^2 R", ()),
    "EL_A_004": ("F = k q1 q2 / r^2", (Cond("point charges", r"point charges"), Cond("medium", r"vacuum approximation"))),
    "EL_B_002": ("P = V^2 / R", ()),
}
INERTIAL = "the lab frame is inertial and nothing in the text sets the apparatus in motion (default of every item)"
M0_CONDITIONS: dict[str, tuple[str, tuple[Cond, ...]]] = {
    "S01": ("a = (m2 - m1) g / (m1 + m2 + M/2)", (
        Cond("pulley mass distribution (uniform solid disc, I = M R^2 / 2)", r"uniform solid disc"),
        Cond("string does not slip on the pulley", r"does not slip on the pulley"),
        Cond("light, inextensible string", r"light string"),
        Cond("frictionless axle", waived="rule 1: frictionless pulley axles"))),
    "S02": ("v = sqrt(2 g (sin(theta) - mu cos(theta)) d)", (
        Cond("released from rest", r"released from rest"),
        Cond("kinetic friction with the stated coefficient", r"coefficient of kinetic friction"))),
    "S07": ("VC = V0 (1 - exp(-t / (R C)))", (
        Cond("capacitor initially uncharged", r"initially uncharged"),
        Cond("series connection", r"in series"),
        Cond("ideal battery and wires", waived=IDEAL_SOURCE))),
    "S13": ("T = 2 pi sqrt(L / g)", (
        Cond("simple pendulum: a small bob on a light string", r"small bob hangs from a light string"),
        Cond("small amplitude", r"small amplitude"))),
    "S15": ("P = V^2 (1/R1 + 1/R2)", (
        Cond("battery internal resistance", r"negligible internal resistance"),
        Cond("parallel connection", r"in parallel"),
        Cond("ohmic resistors", waived="rule 1: ohmic resistors"))),
    "S20": ("di = f do / (do - f)", (
        Cond("thin lens, paraxial rays", r"thin converging lens"),
        Cond("object on the axis, in front of the lens", r"on the axis \d+ cm in front of the lens"))),
    "S26": ("theta2 = asin(n1 sin(theta1) / n2)", (
        Cond("flat interface", r"flat interface"),
        Cond("angles from the normal", r"measured from the normal"))),
    "S27": ("p = p0 + rho g h", (
        Cond("pressure at the free surface", r"pressure at the free surface is \d"),
        Cond("liquid at rest (hydrostatics)", waived=INERTIAL))),
    "S30": ("t = m c dT / P", (
        Cond("all of the heater power goes into the water", r"delivers [\d.]+ W to [\d.]+ kg of water"),
        Cond("constant specific heat", r"specific heat capacity of water is \d"),
        Cond("no phase change", waived="the question asks for a 40 K rise of the water's temperature, which "
                                       "presupposes liquid water throughout"))),
    "S55": ("vrms = sqrt(3 R T / M)", (
        Cond("thermal equilibrium at the stated temperature", r"thermal equilibrium at a temperature"),
        Cond("gas model", waived="vrms = sqrt(3RT/M) holds for any classical gas in equilibrium (equipartition); "
                                 "'ideal' is stated anyway"))),
    "S72": ("lambda = hc / sqrt(2 mc^2 K)", (
        Cond("starts from rest (K is the total kinetic energy)", r"starts from rest"),
        Cond("non-relativistic treatment", r"non-relativistically"))),
    "S92": ("T = (rho_l - rho_s) g a^3", (
        Cond("cube at rest and completely submerged", r"held at rest completely under the surface"),
        Cond("vertical string", r"light vertical string"))),
}


def screen(texts: list[str], entry: tuple[str, tuple[Cond, ...]] | None) -> dict:
    """Safeguard B for one candidate: every answer-deciding condition stated in every rendering, or waived."""

    if entry is None:
        return {"passed": False, "relation": None, "conditions": [], "reason": "no screen entry: not reviewed"}
    relation, conds = entry
    rows, failed = [], []
    for c in conds:
        if c.stated_by is not None and all(re.search(c.stated_by, t) for t in texts):
            rows.append({"condition": c.condition, "status": "stated", "evidence": c.stated_by})
        elif c.waived is not None:
            rows.append({"condition": c.condition, "status": "waived", "evidence": c.waived})
        else:
            rows.append({"condition": c.condition, "status": "NOT STATED", "evidence": None})
            failed.append(c.condition)
    reason = ("every answer-deciding condition is stated or waived" if conds else
              "no condition beyond the stated values decides the answer") if not failed else \
        "not stated: " + "; ".join(failed)
    return {"passed": not failed, "relation": relation, "conditions": rows, "reason": reason}


# ---------------------------------------------------------------------------------------------------------------------
# Safeguard A: condition deletions, each with a computed alternative
# ---------------------------------------------------------------------------------------------------------------------

G = 9.8


def _s72(relativistic: bool) -> float:  # de Broglie wavelength in pm of an electron with K = 150 eV
    k, mc2, hc = 150.0, 511e3, 1240.0
    pc = math.sqrt(k * k + 2 * k * mc2) if relativistic else math.sqrt(2 * k * mc2)
    return hc / pc * 1e3


@dataclass(frozen=True)
class Deletion:
    """A stated condition removed from an item's text. `certified` recomputes the certified answer by hand (checked
    against the item); `alternative_answer` is the answer under `alternative`, a concrete, physically standard case
    that the edited text allows."""

    target: str  # v1 family id or M0 structure id
    kind: str  # "legacy" (v1 family, every rendering edited) or "role" (M0 problem text)
    old: str
    new: str
    defect_type: str
    description: str
    certified: Callable[[], float]
    alternative: str
    alternative_answer: Callable[[], float]
    rule1_waived: str | None = None  # the deleted condition is one rule 1 exempts: not a defect, dropped


# In order of preference; the first three passing candidates of each type are used.
DELETIONS = (
    Deletion("CM_B_UM_011", "legacy", "is dropped from rest and falls freely", "falls freely",
             "insufficient_boundary_condition",
             "'dropped from rest' deleted ('Ball A falls freely'): the initial velocity is not stated",
             lambda: G * 1.5, "the ball is thrown straight down at 2.0 m/s: v = 2.0 + g t",
             lambda: 2.0 + G * 1.5),
    Deletion("CM_A_STD_002", "legacy", "Cart A begins at 3.0 m/s and accelerates", "Cart A accelerates",
             "insufficient_boundary_condition", "the initial velocity ('begins at 3.0 m/s') deleted",
             lambda: 3.0 * 3.0 + 0.5 * 2.0 * 3.0**2, "the cart starts from rest: x = a t^2 / 2",
             lambda: 0.5 * 2.0 * 3.0**2),
    Deletion("CM_B_010", "legacy", "A perpendicular force of", "A force of", "insufficient_boundary_condition",
             "'perpendicular' deleted: the direction of the force relative to the wrench is not stated",
             lambda: 0.5 * 30.0, "the force acts at 60 degrees to the handle: tau = r F sin(60 deg)",
             lambda: 0.5 * 30.0 * math.sin(math.radians(60))),
    Deletion("CM_B_UM_004", "legacy", "slides across a horizontal surface", "slides across a surface",
             "insufficient_boundary_condition", "'horizontal' deleted: the normal force is not determined",
             lambda: 0.3 * 5.0 * G, "the surface is a 30-degree incline: f = mu m g cos(30 deg)",
             lambda: 0.3 * 5.0 * G * math.cos(math.radians(30))),
    Deletion("S72", "role", " Treat the electron non-relativistically.", "", "missing_assumption",
             "non-relativistic treatment deleted", lambda: _s72(False),
             "relativistic momentum pc = sqrt(K^2 + 2 K mc^2)", lambda: _s72(True)),
    Deletion("S01", "role", ", which is a uniform solid disc of mass 2 kg.", " of mass 2 kg.", "missing_assumption",
             "'uniform solid disc' deleted: the pulley's moment of inertia (mass distribution) is not stated",
             lambda: (5 - 3) * G / (3 + 5 + 2 / 2), "the pulley is a thin ring (I = M R^2): a = (m2 - m1) g / (m1 + m2 + M)",
             lambda: (5 - 3) * G / (3 + 5 + 2)),
    Deletion("CM_B_UM_007", "legacy", "rests on a frictionless incline", "rests on an incline", "missing_assumption",
             "'frictionless' deleted", lambda: 2.0 * G * 0.5,
             "a rough incline holds the block at rest: the weight's downslope component is still m g sin(theta)",
             lambda: 2.0 * G * math.sin(math.radians(30))),
    Deletion("CM_B_UM_046", "legacy", "Wheel A rolls without slipping with radius 0.5 m and angular speed 12.0 rad/s.",
             "Wheel A, of radius 0.5 m, moves along the ground while turning at an angular speed of 12.0 rad/s.",
             "missing_assumption", "'rolls without slipping' removed: the rolling (no-slip) condition is not stated",
             lambda: 0.5 * 12.0, "the wheel slips (a driven wheel on a slippery road, slip ratio 0.2): "
                                 "v_cm = (1 - 0.2) R omega", lambda: 0.8 * 0.5 * 12.0),
    Deletion("S15", "role", " and negligible internal resistance", "", "missing_assumption",
             "'negligible internal resistance' deleted", lambda: 12.0**2 * (1 / 6 + 1 / 12),
             "internal resistance 0.5 ohm: P = (12 V * 4 / 4.5)^2 / 4 ohm",
             lambda: (12.0 * 4 / 4.5) ** 2 / 4, rule1_waived=IDEAL_SOURCE),
    Deletion("S30", "role", "An electric heater delivers 1500 W to 2 kg of water.",
             "An electric heater rated at 1500 W is used to heat 2 kg of water.", "missing_assumption",
             "'delivers 1500 W to the water' replaced by a 1500 W rating: that no heat is lost is not stated",
             lambda: 2 * 4186 * 40 / 1500, "10% of the heater's output is lost to the surroundings: "
                                           "t = m c dT / (0.9 P)", lambda: 2 * 4186 * 40 / (0.9 * 1500)),
    Deletion("CM_B_UM_008", "legacy", "is fully submerged in water", "is in water", "missing_assumption",
             "'fully submerged' deleted", lambda: 1000.0 * 0.002 * G,
             "the object floats partly submerged, displacing the stated 0.002 m^3", lambda: 1000.0 * 0.002 * G),
)


# ---------------------------------------------------------------------------------------------------------------------
# Inputs and exclusions
# ---------------------------------------------------------------------------------------------------------------------


def _key(path: Path) -> dict:
    return json.loads((path / "key_RESTRICTED.json").read_text(encoding="utf-8"))


def excluded_families() -> set[str]:
    """v1 families used by the 14.5 planted bank, its genuine sample, or bank v4's fresh items."""

    used = s186.excluded_families()
    used |= {k["structure_id"] for k in _key(BANK_V4).values() if k["source"] == "fresh_v1_inject"}
    return used


def used_role_pairs() -> set[tuple[str, str]]:
    """(structure, defect type) of every role-format item of banks v3 and v4."""

    return {(k["structure_id"], k["defect_type"]) for path in (BANK_V3, BANK_V4) for k in _key(path).values()
            if k["source"].startswith("role_m0")}


def v4_valid_structures() -> set[str]:
    return {k["structure_id"] for k in _key(BANK_V4).values() if k["source"].startswith("role_m0")
            and k["defect_type"] == "valid"}


def used_id_numbers() -> set[int]:
    return {int(i.split("-")[1]) for path in (BANK_V3, BANK_V4) for i in _key(path)
            if re.fullmatch(r"[FR]-\d+", i)}


def _variants(family: dict) -> list[str]:
    return [str(v["prompt"]) for v in sorted(family["variants"], key=lambda v: int(v["variant_id"]))]


def _answer_value(display: str) -> float:
    return float(re.match(r"^\s*(-?[\d.]+(?:[eE][-+]?\d+)?)", display).group(1))


def certified_from_template(template: dict) -> float:
    """Recompute a v1 family's certified answer from its own governing equation and parameters."""

    params = {k: float(v["value"]) for k, v in template["parameters"].items() if isinstance(v.get("value"), (int, float))}
    return float(sympy.sympify(template["governing_equation_sympy"]).subs(params))


def _relative(a: float, b: float) -> float:
    return abs(a - b) / abs(b)


# ---------------------------------------------------------------------------------------------------------------------
# Item builders
# ---------------------------------------------------------------------------------------------------------------------


def legacy_pass2(template: dict, family: dict, variants: list[str], equation: str | None = None,
                 answer: str | None = None) -> dict:
    return {"variants": variants, "governing_equation_latex": template["governing_equation_latex"],
            "governing_equation_sympy": equation or template["governing_equation_sympy"],
            "parameters": s145.parameter_table(template), "target_quantity": template["target_quantity"],
            "target_units": template["target_units"], "certified_answer_display": answer or family["correct_answer"],
            "authors_proof_text": s145.author_proof(template)}


def deletion_items(families: dict, templates: dict, family_screens: dict) -> tuple[list[dict], list[dict]]:
    """Safeguard A applied to every deletion candidate; returns the items used and the record of every candidate."""

    items, record, taken = [], [], Counter()
    for d in DELETIONS:
        row = {"target": d.target, "kind": d.kind, "defect_type": d.defect_type, "deleted": d.old,
               "replacement": d.new, "alternative": d.alternative}
        if d.kind == "legacy":
            family, template = families[d.target], templates[d.target]
            texts = _variants(family)
            stated_answer = _answer_value(family["correct_answer"])
            base_screen = family_screens.get(d.target) or screen(texts, FAMILY_CONDITIONS.get(d.target))
        else:
            base = rb.base_item(d.target, f"tmp-del-{d.target}")
            texts = [base["problem"]]
            stated_answer = base["base_answer"]
            base_screen = screen(texts, M0_CONDITIONS.get(d.target))
        if any(t.count(d.old) != 1 for t in texts):
            raise SystemExit(f"{d.target}: the phrase to delete does not occur exactly once in every rendering")
        if (d.target, d.old) in V4_DELETIONS:
            raise SystemExit(f"{d.target}: this deletion is one of bank v4's")
        certified, alt = d.certified(), d.alternative_answer()
        if _relative(certified, stated_answer) > 1e-4:
            raise SystemExit(f"{d.target}: recomputed certified answer {certified} != stated {stated_answer}")
        shift = _relative(alt, certified)
        row.update(certified_answer=float(f"{certified:.6g}"), alternative_answer=float(f"{alt:.6g}"),
                   relative_shift=round(shift, 6), base_screen=base_screen["reason"])
        if not base_screen["passed"]:
            row.update(used=False, reason="the unedited item already fails the rule-1 screen (two defects)")
        elif d.rule1_waived:
            row.update(used=False, reason=f"the deleted condition is exempt under rule 1 ({d.rule1_waived}): "
                                          "its deletion is not a defect")
        elif shift <= MIN_ALTERNATIVE_SHIFT:
            row.update(used=False, reason=f"Safeguard A: the alternative changes the answer by {shift:.2%} "
                                          f"(<= {MIN_ALTERNATIVE_SHIFT:.0%}); the deletion does not decide the answer")
        elif taken[d.defect_type] >= WANT_DELETIONS[d.defect_type]:
            row.update(used=False, reason="passes; not needed (enough items of this type earlier in the list)")
        else:
            taken[d.defect_type] += 1
            row.update(used=True, reason=f"passes: the alternative changes the answer by {shift:.1%}")
            alternative = {"case": d.alternative, "answer": float(f"{alt:.6g}"),
                           "certified_answer": float(f"{certified:.6g}"), "relative_difference": round(shift, 4),
                           "unit": None}
            edited = [t.replace(d.old, d.new) for t in texts]
            entry = FAMILY_CONDITIONS.get(d.target) if d.kind == "legacy" else M0_CONDITIONS.get(d.target)
            if screen(edited, entry)["passed"]:
                raise SystemExit(f"{d.target}: the deleted phrase is not one of the screen's deciding conditions")
            if d.kind == "legacy":
                alternative["unit"] = template["target_units"]
                items.append({"kind": "legacy", "family": d.target, "defect_type": d.defect_type,
                              "expected_verdict": "invalid", "detectable_in": "pass1", "description": d.description,
                              "source": "fresh_v1_condition_deleted", "alternative": alternative,
                              "pass1": {"variants": edited}, "pass2": legacy_pass2(template, family, edited)})
            else:
                alternative["unit"] = base["target_unit"]
                items.append({**base, "problem": edited[0], "kind": "role",
                              "defect_type": d.defect_type, "expected_verdict": "invalid", "detectable_in": "pass1",
                              "description": d.description, "source": "role_m0_condition_deleted",
                              "alternative": alternative})
        record.append(row)
    short = {t: n - taken[t] for t, n in WANT_DELETIONS.items() if taken[t] < n}
    if short:
        raise SystemExit(f"not enough deletion candidates pass Safeguard A: {short}")
    return items, record


def precision_terms(family: dict, shown: str) -> tuple[list[str], str]:
    """Accepted terms of a numerical-precision item: the frozen term, plus failed_transformation_identity when the shown
    answer is off by more than half a unit in the last digit of the certified answer as stated (its precision)."""

    certified_text = re.match(r"^\s*(-?[\d.]+(?:[eE][-+]?\d+)?)", family["correct_answer"]).group(1)
    mantissa = certified_text.lower().split("e")[0].lstrip("-")
    exponent = int(certified_text.lower().split("e")[1]) if "e" in certified_text.lower() else 0
    decimals = len(mantissa.split(".")[1]) if "." in mantissa else 0
    half_unit = 0.5 * 10 ** (exponent - decimals)
    error = abs(_answer_value(shown) - float(certified_text))
    terms = list(s178.ACCEPTED_TERMS["invalid_numerical_precision"])
    if error > half_unit:
        terms.append("failed_transformation_identity")
        basis = (f"shown {shown} vs certified {family['correct_answer']}: off by {error:g}, more than the stated "
                 f"precision (+/- {half_unit:g}), so the shown answer does not follow from the relation either; "
                 f"failed_transformation_identity also accepted ({DECIDED})")
    else:
        basis = f"shown answer within the stated precision; frozen terms only ({DECIDED})"
    return terms, basis


def fresh_items(rng: random.Random, families: dict, templates: dict, excluded: set[str],
                family_screens: dict) -> tuple[list[dict], dict]:
    """s186's selection (scarcest type first, spread over domains) on unused families that pass Safeguard B."""

    usable = {f for f in families if f not in excluded and family_screens[f]["passed"]}
    used: set[str] = set()
    items, shortfalls = [], {}
    order = sorted(WANT_FRESH, key=lambda dt: (sum(1 for f in usable if di.inject(dt, families[f], templates.get(f))
                                                   .applicable), dt))
    for defect_type in order:
        pool = [f for f in sorted(usable) if f not in used and di.inject(defect_type, families[f], templates.get(f))
                .applicable]
        rng.shuffle(pool)
        domains: Counter = Counter()
        picked = []
        while pool and len(picked) < WANT_FRESH[defect_type]:
            pool.sort(key=lambda f: domains[families[f]["domain"]])
            fid = pool.pop(0)
            domains[families[fid]["domain"]] += 1
            picked.append(fid)
            used.add(fid)
        if len(picked) < WANT_FRESH[defect_type]:
            shortfalls[defect_type] = WANT_FRESH[defect_type] - len(picked)
        for fid in picked:
            family, template = families[fid], templates[fid]
            inj = di.inject(defect_type, family, template)
            recomputed = certified_from_template(template)
            if _relative(recomputed, _answer_value(family["correct_answer"])) > 1e-3:
                raise SystemExit(f"{fid}: certified answer {family['correct_answer']} != recomputed {recomputed}")
            item = {"kind": "legacy", "family": fid, "defect_type": defect_type,
                    "expected_verdict": inj.expected_verdict, "detectable_in": inj.detectable_in,
                    "description": inj.description, "source": "fresh_v1_inject",
                    "accepted_terms": s186.LEGACY_ACCEPTED.get(defect_type, []),
                    "pass1": {"variants": inj.edited_prompts},
                    "pass2": legacy_pass2(template, family, inj.edited_prompts, inj.edited_equation, inj.edited_answer)}
            if defect_type == "invalid_numerical_precision":
                item["accepted_terms"], item["accepted_terms_basis"] = precision_terms(family, inj.edited_answer)
            if defect_type == "valid_equivalent_rewrite":
                final = screen(inj.edited_prompts, FAMILY_CONDITIONS.get(fid))
                if not final["passed"]:
                    raise SystemExit(f"{fid}: the rewrite fails the rule-1 screen")
                item["screen"] = final
            items.append(item)
    if shortfalls:
        raise SystemExit(f"fresh shortfalls: {shortfalls}")
    return items, {"usable_families": len(usable)}


def _plant_ok(structure_id: str, defect_type: str, instance: int) -> tuple[bool, str]:
    """A role plant must produce a well-defined item on the given instance: for a flipped operation, every claimed answer
    finite, positive and more than 5% from the certified one (a zero or negative input would make the claim nonsense,
    not a defect); for a rendering plant, the shown number of D0 differs from that of its claimed R0 twin."""

    base = rb.base_item(structure_id, f"tmp-{structure_id}", instance)
    try:
        planted = rb.plant(base, defect_type)
    except (ValueError, ArithmeticError, IndexError) as exc:  # a solver finds no solution for a nonsense input
        return False, f"plant fails on instance {instance}: {exc!r}"
    if defect_type == "failed_transformation_identity":
        true = next(c for c in base["claims"] if c["stratum"] == "R")["certified_answers"]
        wrong = next(c for c in planted["claims"] if c["stratum"] == "R")["certified_answers"]
        for v, w in wrong.items():
            if not (math.isfinite(w) and w > 0 and _relative(w, true[v]) > MIN_ALTERNATIVE_SHIFT):
                return False, (f"instance {instance}: claimed answer {w} at q = {v} is not a clean wrong answer "
                               f"(true {true[v]})")
    if defect_type == "rendering_not_minimal":
        text = {x["label"]: x["text"] for x in planted["sentences"]}
        numbers = {lab: re.findall(r"\d+(?:\.\d+)?", text[lab]) for lab in ("D0", "R0")}
        if numbers["D0"] == numbers["R0"]:
            return False, f"instance {instance}: D0 shows the same number as R0 ({numbers['R0']})"
    return True, "ok"


def unseen_instance(structure_id: str) -> int:
    """The certified instance used for a valid role item or a role plant: the lowest one never used in banks v3 or v4
    (both build every role item on instance V3_V4_INSTANCE through `rolevalue_bank.base_item`'s default)."""

    n = len(roles_m0.structure(structure_id).instances)
    unused = [i for i in range(n) if i != V3_V4_INSTANCE]
    if not unused:
        raise SystemExit(f"{structure_id}: no certified instance unused by banks v3 and v4")
    return unused[0]


def earlier_pass1_texts() -> set[str]:
    """Every problem text and rendering shown in pass 1 of banks v3 and v4."""

    texts: set[str] = set()
    for path in (BANK_V3, BANK_V4):
        for line in (path / "pass1_packets.jsonl").read_text(encoding="utf-8").splitlines():
            packet = json.loads(line)
            texts.update(packet.get("variants", []))
            if "problem" in packet:
                texts.add(packet["problem"])
    return texts


def role_items(rng: random.Random, m0_screens: dict, deletion_structures: list[str]) -> tuple[list[dict], dict]:
    """Choose the role plants and valid role items: unused (structure, type) pairs and unused valid bases that pass the
    screen, with as few repeated M0 structures across the whole bank as possible (ties broken by the seeded rng). Valid
    role items and role plants are built on an instance never used in banks v3 or v4, so their pass-1 problem text is
    unseen; the condition deletions stay on instance 0 (their edit already makes the text new)."""

    used_pairs, v4_valid = used_role_pairs(), v4_valid_structures()
    instance_of = {s: unseen_instance(s) for s in sorted(m0_screens)}
    unseen_screens = {s: screen([rb.base_item(s, "tmp", i)["problem"]], M0_CONDITIONS.get(s))
                      for s, i in instance_of.items()}
    passing = sorted(s for s in m0_screens if m0_screens[s]["passed"] and unseen_screens[s]["passed"])
    eligible = {}
    reasons = {}
    for defect in WANT_ROLE_PLANTS:
        eligible[defect] = []
        for s in passing:
            if (s, defect) in used_pairs:
                reasons[f"{s}|{defect}"] = "pair used in bank v3 or v4"
                continue
            ok, why = _plant_ok(s, defect, instance_of[s])
            if not ok:
                reasons[f"{s}|{defect}"] = why
                continue
            eligible[defect].append(s)
    eligible["valid"] = [s for s in passing if s not in v4_valid]
    for s in sorted(m0_screens):
        if s in v4_valid:
            reasons[f"{s}|valid"] = "valid item in bank v4"
        elif s not in passing:
            reasons[f"{s}|valid"] = "fails the rule-1 screen"
    (d1, n1), (d2, n2) = WANT_ROLE_PLANTS.items()
    best, options = None, []
    for a in itertools.combinations(eligible[d1], n1):
        for b in itertools.combinations(eligible[d2], n2):
            for c in itertools.combinations(eligible["valid"], WANT_ROLE_VALID):
                structures = list(a) + list(b) + list(c) + list(deletion_structures)
                repeats = len(structures) - len(set(structures))
                if best is None or repeats < best:
                    best, options = repeats, []
                if repeats == best:
                    options.append((a, b, c))
    if not options:
        raise SystemExit(f"no feasible role assignment: {eligible}")
    a, b, c = options[rng.randrange(len(options))]
    items = []
    seen = earlier_pass1_texts()
    plant_instances = {}
    for defect, structures in ((d1, a), (d2, b)):
        for s in structures:
            planted = rb.plant(rb.base_item(s, f"tmp-{defect}-{s}", instance_of[s]), defect)
            if planted["problem"] in seen:
                raise SystemExit(f"{s} instance {instance_of[s]}: the pass-1 text was shown in bank v3 or v4")
            plant_instances[s] = {"defect_type": defect, "instance": instance_of[s],
                                  "base_answer": planted["base_answer"], "target_unit": planted["target_unit"],
                                  "description": planted["description"]}
            items.append({**planted, "kind": "role", "source": "role_m0_plant_v5"})
    valid_instances = {}
    for s in c:
        instance = unseen_instance(s)
        base = rb.base_item(s, f"tmp-valid-{s}", instance)
        final = screen([base["problem"]], M0_CONDITIONS.get(s))
        if not final["passed"]:
            raise SystemExit(f"{s} instance {instance}: fails the rule-1 screen")
        if base["problem"] in seen:
            raise SystemExit(f"{s} instance {instance}: the pass-1 text was shown in bank v3 or v4")
        valid_instances[s] = {"instance": instance, "base_answer": base["base_answer"],
                              "target_unit": base["target_unit"]}
        items.append({**base, "kind": "role", "source": "role_m0_valid_v5", "screen": final})
    info = {"eligible": eligible, "not_eligible": reasons, "repeated_structures": best,
            "n_optimal_assignments": len(options), "chosen": {d1: list(a), d2: list(b), "valid": list(c)},
            "valid_role_instances": valid_instances, "plant_instances": plant_instances,
            "screens_at_unseen_instance": unseen_screens}
    return items, info


# ---------------------------------------------------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------------------------------------------------


def build(out: Path) -> dict:
    rng = random.Random(SEED)
    families, templates = s145.load_families(), s145.load_templates()
    excluded = excluded_families()
    unused = sorted(f for f in families if f not in excluded)
    family_screens = {f: screen(_variants(families[f]), FAMILY_CONDITIONS.get(f)) for f in unused}
    m0_screens = {s: screen([rb.base_item(s, "tmp")["problem"]], M0_CONDITIONS.get(s)) for s in sorted(M0_CONDITIONS)}

    deleted, deletion_record = deletion_items(families, templates, family_screens)
    reserved = excluded | {d["family"] for d in deleted if d["kind"] == "legacy"}
    fresh, fresh_info = fresh_items(rng, families, templates, reserved, family_screens)
    roles, role_info = role_items(rng, m0_screens,
                                  [d["structure_id"] for d in deleted if d["kind"] == "role"])

    legacy = fresh + [d for d in deleted if d["kind"] == "legacy"]
    role = roles + [d for d in deleted if d["kind"] == "role"]
    free = sorted(set(range(100, 1000)) - used_id_numbers())
    numbers = rng.sample(free, len(legacy) + len(role))
    p1, p2, key = [], [], {}
    for item, n in zip(legacy, numbers[:len(legacy)], strict=True):
        item_id = f"F-{n}"
        p1.append({"item_id": item_id, "kind": "legacy", **item["pass1"]})
        p2.append({"item_id": item_id, "kind": "legacy", **item["pass2"]})
        key[item_id] = {"defect_type": item["defect_type"], "expected_verdict": item["expected_verdict"],
                        "detectable_in": item["detectable_in"], "description": item["description"],
                        "source": item["source"], "structure_id": item["family"], "split": SPLIT,
                        "accepted_terms": item.get("accepted_terms",
                                                   s178.ACCEPTED_TERMS.get(item["defect_type"], [])),
                        "contested": None}
        for extra in ("alternative", "screen", "accepted_terms_basis"):
            if extra in item:
                key[item_id][extra] = item[extra]
    for item, n in zip(role, numbers[len(legacy):], strict=True):
        item = {**item, "item_id": f"R-{n}"}
        a, b = rb.packets(item, s178.SEED)
        p1.append({**a, "kind": "role"})
        p2.append({**b, "kind": "role"})
        key[item["item_id"]] = {"defect_type": item["defect_type"], "expected_verdict": item["expected_verdict"],
                                "detectable_in": item["detectable_in"], "description": item["description"],
                                "source": item["source"], "structure_id": item["structure_id"], "split": SPLIT,
                                "accepted_terms": s178.ACCEPTED_TERMS.get(item["defect_type"], []), "contested": None}
        key[item["item_id"]]["instance"] = item.get("instance", V3_V4_INSTANCE)
        for extra in ("alternative", "screen"):
            if extra in item:
                key[item["item_id"]][extra] = item[extra]
    for packet in p1 + p2:
        leaked = [f for f in s178.LEAK_FIELDS if f in packet]
        if leaked:
            raise SystemExit(f"key field(s) {leaked} in packet {packet['item_id']}")
    order = sorted(key, key=lambda i: hashlib.sha256(f"{SEED}:{i}".encode()).hexdigest())
    p1.sort(key=lambda p: order.index(p["item_id"]))
    p2.sort(key=lambda p: order.index(p["item_id"]))
    out.mkdir(parents=True, exist_ok=False)
    files = {"pass1_packets.jsonl": "".join(json.dumps(p, ensure_ascii=False, sort_keys=True) + "\n" for p in p1),
             "pass2_packets.jsonl": "".join(json.dumps(p, ensure_ascii=False, sort_keys=True) + "\n" for p in p2),
             "key_RESTRICTED.json": json.dumps(key, indent=2, sort_keys=True) + "\n"}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    manifest = {
        "n_items": len(key), "split": SPLIT, "seed": SEED,
        "by_type": dict(Counter(k["defect_type"] for k in key.values())),
        "expected": dict(Counter(k["expected_verdict"] for k in key.values())),
        "by_source": dict(Counter(k["source"] for k in key.values())),
        "excluded_families": len(excluded), "unused_families": len(unused), **fresh_info,
        "accepted_terms_change": (
            "invalid_numerical_precision items whose displayed answer is off by more than the stated precision also "
            f"accept failed_transformation_identity (the shown answer then does not follow from the relation); {DECIDED}. "
            "Every other type keeps the terms frozen in s178.ACCEPTED_TERMS / s186.LEGACY_ACCEPTED."),
        "safeguard_A_deletions": deletion_record,
        "safeguard_B_screen": {
            "v1_families": {f: family_screens[f] for f in unused},
            "m0_structures": m0_screens,
            "dropped": sorted([f"{f}: {r['reason']}" for f, r in family_screens.items() if not r["passed"]]
                              + [f"{s}: {r['reason']}" for s, r in m0_screens.items() if not r["passed"]])},
        "role_assignment": role_info,
        "sha256": {n: hashlib.sha256(t.encode()).hexdigest() for n, t in files.items()},
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default="docs/validation/v2/llm_panel/bank_v5")
    args = parser.parse_args(argv)
    out = REPO_ROOT / args.out if not Path(args.out).is_absolute() else Path(args.out)
    if out.exists():
        print(f"Refusing to overwrite {out}", file=sys.stderr)
        return 2
    manifest = build(out)
    print(json.dumps({k: manifest[k] for k in ("n_items", "by_type", "expected", "by_source", "sha256")}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
