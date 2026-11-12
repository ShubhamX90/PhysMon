"""The M0 pilot structures (Stage 15; plan of record G1 item "M0 pilot structures", 8-12 structures with role-by-value
cells): S01 here, six from `roles_m0_a` and five from `roles_m0_b`, twelve in all across mechanics, fluids, optics,
circuits, thermodynamics and quantum physics. Every spec is reviewed by the lead agent (provisional sole reviewer under
the 2026-11-12 judge decision; LLM-panel and user review are still pending)."""

from __future__ import annotations

from physmon.benchmark.v2 import graph as gr
from physmon.benchmark.v2 import library
from physmon.benchmark.v2 import rolevalue as rv
from physmon.benchmark.v2 import roles_m0_a, roles_m0_b

P = rv.Phrasing

S01 = rv.RoleSpec(
    structure_id="S01", quantity_phrase="a small block", quantity_type="mass", unit="kg", values=(0.4, 0.8, 1.2),
    heldout_values=(0.6, 1.0),
    frame="A {value} {unit} block is {relation}.",
    relevant=rv.RelevantWiring("m1", "add", "a block tied beneath the left block moves with it, adding to its mass"),
    phrasings_r=(P("r0", "tied firmly beneath the left block"),
                 P("r1", "glued to the bottom of the left block so that it moves with it")),
    phrasings_d=(P("d0", "resting on a shelf beside the apparatus"),
                 P("d1", "sitting in a drawer in another room, unrelated to the setup")),
    nonnumeric_fill="small",
    cancelling=rv.CancellingSpec(
        "the pulley radius", "length", "cm", (8.0, 12.0, 16.0), "The pulley {relation} {value} {unit}.",
        (P("c0", "has a radius of"), P("c1", "measures, from its axle to its rim,")),
        "(m2 - m1)*g/(m1 + m2 + (M*q**2/2)/q**2)", ("I = M r^2 / 2", "a = (m2 - m1) g / (m1 + m2 + I / r^2)"),
        # the misuse that keeps r: reporting the pulley's angular acceleration a / r instead of the blocks' acceleration
        "(m2 - m1)*g/(m1 + m2 + M/2)/q"),
    conditional=rv.ConditionalSpec(
        "the string's breaking strength", "force", "N", (120.0, 200.0, 300.0), "The string {relation} {value} {unit}.",
        (P("k0", "can withstand a tension of up to"), P("k1", "is rated to break only above")),
        "Max(m1*(g + a), m2*(g - a)) < q", "g", 20.0),
    notes="C wrong law changed by the lead reviewer from a dimensionally invalid expression to the angular acceleration.",
)

ROLE_SPECS: dict[str, rv.RoleSpec] = {"S01": S01, **roles_m0_a.ROLE_SPECS, **roles_m0_b.ROLE_SPECS}
STRUCTURE_FACTORIES = {"S01": library.s01_atwood_massive_pulley, **roles_m0_a.STRUCTURE_FACTORIES,
                       **roles_m0_b.STRUCTURE_FACTORIES}


def structure(structure_id: str) -> gr.Structure:
    return STRUCTURE_FACTORIES[structure_id]()
