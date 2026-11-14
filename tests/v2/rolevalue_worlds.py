"""Synthetic role-by-value worlds with known truth, shared by the G1 analysis tests (not a test module).

A world is a set of structures, each with the core cells of the plan (no cue, N, R and D at 3 values x 2 phrasings) and
optionally C and K cells; every sample answers one category (the cell's gold, one of its foils, the placebo, or a
value matching nothing) with probabilities given per cell by the test, so every estimand has a known expected value.
"""

from __future__ import annotations

import sys
from collections.abc import Callable, Mapping
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.analysis import rolevalue_stats as rs  # noqa: E402

GOLD_D = 10.0
GOLD_R = (12.0, 14.0, 16.0)
COPY = (100.5, 200.5, 300.5)  # q converted to the target unit (same-dimension structures)
DIGIT = (0.4, 0.8, 1.2)  # the numeral read in the target unit (incompatible-unit structures)


def make_cells(sid: str, unit: str = "copy", with_ck: bool = False) -> dict[str, rs.Cell]:
    """Core cells of one structure; `unit` is "copy" (q has the target's dimension) or "digit_copy"."""

    copy_values = COPY if unit == "copy" else DIGIT
    cells = {f"{sid}:none": rs.Cell(f"{sid}:none", sid, "none", None, None, GOLD_D, {}, None, []),
             f"{sid}:N": rs.Cell(f"{sid}:N", sid, "N", None, "d0", GOLD_D, {}, None, [])}
    for z in range(3):
        for p in ("r0", "r1"):
            cells[f"{sid}:R:z{z}:{p}"] = rs.Cell(
                f"{sid}:R:z{z}:{p}", sid, "R", z, p, GOLD_R[z],
                {"neglect": GOLD_D, "add:y": GOLD_R[z] + 30, unit: copy_values[z]}, 2 * GOLD_R[z] - GOLD_D, [])
        for p in ("d0", "d1"):
            cells[f"{sid}:D:z{z}:{p}"] = rs.Cell(
                f"{sid}:D:z{z}:{p}", sid, "D", z, p, GOLD_D,
                {"relevant_twin": GOLD_R[z], "add:x": GOLD_D + 5 * (z + 1), "subtract:x": GOLD_D - 3 * (z + 1),
                 unit: copy_values[z]}, None, [])
        if with_ck:
            for st, foil, base in (("C", "wrong_law", 50.0), ("K", "out_of_regime", 70.0)):
                for p in (f"{st.lower()}0", f"{st.lower()}1"):
                    cells[f"{sid}:{st}:z{z}:{p}"] = rs.Cell(f"{sid}:{st}:z{z}:{p}", sid, st, z, p, GOLD_D,
                                                            {foil: base + z}, None, [])
    return cells


Probs = Callable[[rs.Cell, int], Mapping[str, float]]


def simulate(n_structures: int, k: int, probs: Probs, seed: int = 0, unit: Callable[[int], str] = lambda j: "copy",
             with_ck: bool = False, tokens: Callable[[rs.Cell, int], float] | None = None,
             budget: Callable[[rs.Cell, int], float] | None = None) -> tuple[dict[str, rs.Cell], list[dict]]:
    """k samples per R/D/C/K cell, 6k in the N cell and in the no-cue cell (the balanced design). `probs(cell, j)` maps
    categories ("correct", a foil name, "placebo") to probabilities; the remainder answers a value matching nothing.
    `budget(cell, j)` is the BUDGET_EXHAUSTED share (no value); `tokens(cell, j)` the mean generated tokens."""

    rng = np.random.default_rng(seed)
    cells: dict[str, rs.Cell] = {}
    records: list[dict] = []
    for j in range(n_structures):
        c = make_cells(f"S{j:02d}", unit(j), with_ck)
        cells.update(c)
        for key, cell in c.items():
            n = 6 * k if cell.stratum in ("N", "none") else k
            p = dict(probs(cell, j))
            names = list(p)
            weights = np.array([p[x] for x in names] + [max(0.0, 1 - sum(p.values()))])
            draws = rng.choice(len(weights), size=n, p=weights / weights.sum())
            for i, d in enumerate(draws):
                status = "COMPLETE"
                if budget is not None and rng.random() < budget(cell, j):
                    status, value = "BUDGET_EXHAUSTED", None
                elif d == len(names):
                    value = 5000.0 + 37.0 * i + 0.1 * j
                else:
                    name = names[d]
                    value = cell.gold if name == "correct" else (cell.placebo if name == "placebo" else cell.foils[name])
                correct = status == "COMPLETE" and value is not None and abs(value - cell.gold) <= 1e-9 * abs(cell.gold)
                rec = {"job_id": f"{key}:s{i}", "completion_status": status,
                       "grade_declared": "correct" if correct else "wrong", "value_in_gold_unit": value}
                if tokens is not None:
                    rec["n_generated_tokens"] = int(max(1, rng.poisson(tokens(cell, j))))
                records.append(rec)
    return cells, records
