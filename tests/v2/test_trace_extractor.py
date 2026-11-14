"""Tests of the frozen H4 trace extractor (`physmon.analysis.trace_extractor`, version h4-v1; G1 decision 12).

Three suites guard `EXTRACTOR_FROZEN`:

* SYNTHETIC: hand-written traces with hand labels, one per rule (must agree 100%);
* REAL: 37 generations copied verbatim into `fixtures/trace_extractor_real_traces.json` from `results/stage15/s15_cal_*`
  (Llama-3.1-8B, Qwen2.5-7B, Qwen3-8B non-thinking and Qwen3-8B thinking), each with a hand label read from the trace and a
  synthetic misuse set (the stage-15 calibration has no D cells). Three known disagreements are pinned as
  `KNOWN_REAL_DISAGREEMENTS` (unitless final values whose symbol is not in the target's symbol list: the extractor reports
  NO_TRACE_VALUE or follows an earlier same-unit value), so a rule change that moves any other label fails;
* the fingerprint pin: `extractor_fingerprint()` hashes the source of every rule function and every pattern, and must equal
  `PINNED_FINGERPRINT`. Changing a rule after any G3 record exists requires a new `TRACE_EXTRACTOR_VERSION`, a new pin, and a
  re-run of both suites.

Choices made where the specification was ambiguous (all conservative; see the module docstring for the rules):
the trace ends before the FIRST final-answer line; a value with a unit of another dimension is never a target statement and
units are never stripped; unitless values count only at the end of an equation chain whose head names the target (phrase or
symbol); a statement is ignored when it restates a prompt numeral or q, unless the model names it as the target and it is the
gold or a misuse value; a value within the declared rule OR within 0.1% counts as matching (long printed values carry the
rounding noise of earlier steps); a value matching only after a sign flip is TRACE_AMBIGUOUS (magnitude questions), never
TRACE_OTHER; two matching misuse values are TRACE_AMBIGUOUS even when they belong to one curve class.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from physmon.analysis import rolevalue_stats as rs  # noqa: E402
from physmon.analysis import scorecard as sc  # noqa: E402
from physmon.analysis import trace_extractor as te  # noqa: E402

PINNED_FINGERPRINT = "923ddaa18664f39031efb8388fed0535bbbf87457ad1c3ae612f543cf20525e3"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "trace_extractor_real_traces.json"
KNOWN_REAL_DISAGREEMENTS = {"llama-S56-i3-s2-hard", "llama-S13-i0-s0-hard", "qwen25-S20-i1-s4-hard"}

GOLD = 5.3866
MISUSE = {"add:x": 6.4, "copy": 3.0}


def ctx(gold=GOLD, unit="m/s", misuse=None, phrases=("speed",), symbols=("v",), prompt=(), q=None, view="declared"):
    return te.TraceContext(gold, unit, dict(MISUSE if misuse is None else misuse), tuple(phrases), tuple(symbols),
                           tuple(prompt), q, view)


def classify(text, thinking=False, **kw):
    return te.classify_trace(te.trace_region(text, thinking_expected=thinking), ctx(**kw))


def record(text, final_value, thinking=False, status="COMPLETE", unit="m/s"):
    return {"generated_answer_raw": text, "thinking_mode": "on" if thinking else "none", "completion_status": status,
            "value_in_gold_unit": final_value, "gold_unit": unit}


# (id, text, thinking, ctx kwargs, expected label)
SYNTHETIC = [
    ("correct-then-final-contaminated", "Compute v = sqrt(2 * 9.8 * 1.48) = 5.3866 m/s.\nFinal answer: 6.4 m/s", False, {},
     "TRACE_CORRECT"),
    ("misuse-computed-in-trace", "Adding the extra term: v = 5.3866 + 1.0134 = 6.4 m/s\nFinal answer: 6.4 m/s", False, {},
     "TRACE_MISUSE(add:x)"),
    ("last-wins-correct", "v = 6.4 m/s at first.\nChecking the arithmetic: v = 5.39 m/s.\nSo the speed is 5.39 m/s.", False, {},
     "TRACE_CORRECT"),
    ("last-wins-misuse", "v = 5.39 m/s.\nWait, adding the extra term: speed = 6.4 m/s.", False, {}, "TRACE_MISUSE(add:x)"),
    ("other-dimension-before", "a = 2.1 m/s^2 first.\nThen v = 5.3866 m/s.\nThe acceleration was 2.1 m/s^2.", False, {},
     "TRACE_CORRECT"),
    ("other-dimension-only", "The acceleration is 2.1 m/s^2 and the time is 2.6 s.", False, {}, "NO_TRACE_VALUE"),
    ("kmh-to-ms", "The block moves at v = 19.4 km/h.", False, {}, "TRACE_CORRECT"),
    ("kmh-misuse", "So v = 23.04 km/h.", False, {}, "TRACE_MISUSE(add:x)"),
    ("m-to-cm-correct", "The distance is d = 2.5 m.", False,
     {"gold": 250.0, "unit": "cm", "misuse": {"add:x": 300.0}, "phrases": ("distance",), "symbols": ("d",)}, "TRACE_CORRECT"),
    ("m-to-cm-misuse", "The distance is d = 3.0 m.", False,
     {"gold": 250.0, "unit": "cm", "misuse": {"add:x": 300.0}, "phrases": ("distance",), "symbols": ("d",)},
     "TRACE_MISUSE(add:x)"),
    ("latex-frac-approx-text", "$v = \\frac{12}{2.2276} \\approx 5.39 \\, \\text{m/s}$", False, {}, "TRACE_CORRECT"),
    ("latex-boxed-bare-number", "Therefore the speed is \\boxed{5.39}", False, {}, "TRACE_CORRECT"),
    ("latex-boxed-with-unit", "$$\\boxed{v = 5.39 \\text{ m/s}}$$", False, {}, "TRACE_CORRECT"),
    ("latex-backslash-space", "\\text{speed} \\approx 6.4\\ \\text{m/s}", False, {}, "TRACE_MISUSE(add:x)"),
    ("latex-mathrm-fraction-unit", "$v = 5.39\\,\\mathrm{m}/\\mathrm{s}$", False, {}, "TRACE_CORRECT"),
    ("rounding-chain", "v = 5.3866 \\approx 5.39 m/s", False, {}, "TRACE_CORRECT"),
    ("rounding-chain-to-one-digit", "v ≈ 5.3866 m/s ≈ 5.4 m/s ≈ 5 m/s", False, {}, "TRACE_OTHER"),
    ("rounding-chain-coarse-ok", "v = 5.3866 m/s, which rounds to 5.4 m/s", False, {}, "TRACE_CORRECT"),
    ("restated-input-ignored", "The block already moves at 2.0 m/s and has mass 3 kg.", False,
     {"prompt": ((2.0, "m/s"), (3.0, "kg"))}, "NO_TRACE_VALUE"),
    ("restated-input-other-unit-ignored", "That is 7.2 km/h = 2 m/s at the start.", False, {"prompt": ((7.2, "km/h"),)},
     "NO_TRACE_VALUE"),
    ("q-value-ignored", "The other cart has 0.8 m/s.", False, {"q": (0.8, "m/s")}, "NO_TRACE_VALUE"),
    ("q-named-as-target-is-misuse", "So the speed is 0.8 m/s.", False,
     {"q": (0.8, "m/s"), "prompt": ((0.8, "m/s"),), "misuse": {"copy": 0.8}}, "TRACE_MISUSE(copy)"),
    ("named-restated-input-not-a-target-value", "So the speed is 2.0 m/s.", False, {"prompt": ((2.0, "m/s"),)},
     "NO_TRACE_VALUE"),
    ("ambiguous-gold-and-misuse", "v = 5.39 m/s", False, {"misuse": {"add:x": 5.388, "copy": 3.0}}, "TRACE_AMBIGUOUS"),
    ("ambiguous-two-misuse-values", "v = 6.4 m/s", False, {"misuse": {"a:x": 6.4, "b:y": 6.4}}, "TRACE_AMBIGUOUS"),
    ("no-trace-final-only", "Final answer: 6.4 m/s", False, {}, "NO_TRACE"),
    ("no-trace-blank", "  \n ", False, {}, "NO_TRACE"),
    ("no-value-in-trace", "We apply energy conservation and solve for the unknown.\nFinal answer: 6.4 m/s", False, {},
     "NO_TRACE_VALUE"),
    ("thinking-correct", "<think>\nLet me compute. v = 5.3866 m/s.\n</think>\n\nFinal answer: 6.4 m/s", True, {},
     "TRACE_CORRECT"),
    ("thinking-final-line-inside-thinking", "<think>\nFinal answer: 6.4 m/s\nWait. v = 5.39 m/s\n</think>\n"
     "The speed is therefore 5.39 m/s.\n\nFinal answer: 5.39 m/s", True, {}, "TRACE_CORRECT"),
    ("thinking-misuse-after-marker", "<think>\nv = 5.3866 m/s\n</think>\nChecking again, speed = 6.4 m/s.\nFinal answer: 6.4 m/s",
     True, {}, "TRACE_MISUSE(add:x)"),
    ("thinking-unclosed", "<think>\nv = 6.4 m/s so far, still thinking", True, {}, "TRACE_MISUSE(add:x)"),
    ("sci-e-notation", "d = 4.5e-4 m", False, {"gold": 4.5e-4, "unit": "m", "misuse": {"add:x": 9e-4}, "phrases": ("distance",),
                                               "symbols": ("d",)}, "TRACE_CORRECT"),
    ("sci-latex-times", "d = 4.5 \\times 10^{-4} \\, \\text{m}", False,
     {"gold": 4.5e-4, "unit": "m", "misuse": {"add:x": 9e-4}, "phrases": ("distance",), "symbols": ("d",)}, "TRACE_CORRECT"),
    ("sci-unicode-times-plain-exponent", "d = 4.5 × 10^-4 m", False,
     {"gold": 4.5e-4, "unit": "m", "misuse": {"add:x": 9e-4}, "phrases": ("distance",), "symbols": ("d",)}, "TRACE_CORRECT"),
    ("sci-star-times-converted-prefix", "d = 0.45 mm and 4.5 * 10^{-4} m", False,
     {"gold": 4.5e-4, "unit": "m", "misuse": {"add:x": 9e-4}, "phrases": ("distance",), "symbols": ("d",)}, "TRACE_CORRECT"),
    ("sci-misuse", "d = 9 \\times 10^{-4} m", False,
     {"gold": 4.5e-4, "unit": "m", "misuse": {"add:x": 9e-4}, "phrases": ("distance",), "symbols": ("d",)},
     "TRACE_MISUSE(add:x)"),
    ("sci-unitless-named", "d = 4.5 * 10^{-4}", False,
     {"gold": 4.5e-4, "unit": "m", "misuse": {"add:x": 9e-4}, "phrases": ("distance",), "symbols": ("d",)}, "TRACE_CORRECT"),
    ("negative-correct", "v = -3.2 m/s", False, {"gold": -3.2, "misuse": {"add:x": -6.0}}, "TRACE_CORRECT"),
    ("negative-unicode-minus", "v = \u22123.2 m/s", False, {"gold": -3.2, "misuse": {"add:x": -6.0}}, "TRACE_CORRECT"),
    ("negative-sign-only-is-ambiguous", "v = 3.2 m/s", False, {"gold": -3.2, "misuse": {"add:x": -6.0}}, "TRACE_AMBIGUOUS"),
    ("negative-misuse", "v = -6.0 m/s", False, {"gold": -3.2, "misuse": {"add:x": -6.0}}, "TRACE_MISUSE(add:x)"),
    ("binary-minus-is-not-a-sign", "v = 8.4 - 5.2 = 3.2 m/s", False, {"gold": 3.2, "misuse": {"add:x": 13.6}}, "TRACE_CORRECT"),
    ("incompatible-unit-never-stripped", "The momentum is p = 5.3866 kg*m/s.", False, {}, "NO_TRACE_VALUE"),
    ("incompatible-unit-force", "p = 5.3866 N", False, {}, "NO_TRACE_VALUE"),
    ("named-with-incompatible-unit", "So the speed is 5.3866 kg.", False, {}, "NO_TRACE_VALUE"),
    ("unit-identity-before", "Recall 1 km = 1000 m.\nv = 5.3866 m/s", False, {"unit": "m/s"}, "TRACE_CORRECT"),
    ("unit-identity-after", "v = 5.3866 m/s\nRecall that 1 m/s = 3.6 km/h.", False, {}, "TRACE_CORRECT"),
    ("discarded-root", "v = 5.3866 m/s.\nWe discard the negative root, v = -6.4 m/s.", False, {}, "TRACE_CORRECT"),
    ("equation-chain-unitless", "v = 12/2.2276 = 5.39", False, {}, "TRACE_CORRECT"),
    ("unitless-unnamed-ignored", "x = 6.4 and the answer is 6.4", False, {}, "NO_TRACE_VALUE"),
    ("declared-rejects-near-miss", "v = 5.35 m/s", False, {}, "TRACE_OTHER"),
    ("rel1pct-accepts-near-miss", "v = 5.35 m/s", False, {"view": "rel1pct"}, "TRACE_CORRECT"),
    ("words-for-unit", "The speed is 5.39 meters per second.", False, {}, "TRACE_CORRECT"),
    ("thousands-separator", "P = 117,600 Pa", False,
     {"gold": 117600.0, "unit": "Pa", "misuse": {"add:x": 150000.0}, "phrases": ("pressure",), "symbols": ("P",)},
     "TRACE_CORRECT"),
    ("final-subscript-symbol", "v_f = 5.39", False, {}, "TRACE_CORRECT"),
    ("initial-subscript-symbol-not-target", "v_0 = 6.4", False, {}, "NO_TRACE_VALUE"),
    ("variable-after-single-letter-unit", "the factor is 8 m L^2 here", False,
     {"gold": 8.0, "unit": "m", "misuse": {"add:x": 9.0}}, "NO_TRACE_VALUE"),
    ("trailing-parenthetical", "the speed is 5.39 (rounded)", False, {}, "TRACE_CORRECT"),
    ("target-phrase-not-in-statement", "the speed was recorded as 6.4", False, {}, "NO_TRACE_VALUE"),
]


@pytest.mark.parametrize("case", SYNTHETIC, ids=[c[0] for c in SYNTHETIC])
def test_synthetic_trace_labels(case):
    _, text, thinking, kw, expected = case
    assert classify(text, thinking, **kw).label == expected


def test_synthetic_suite_agrees_100_percent_and_covers_every_class():
    got = [classify(t, th, **kw).label for _, t, th, kw, _ in SYNTHETIC]
    assert got == [c[4] for c in SYNTHETIC]
    classes = {lab.split("(")[0] for lab in got}
    assert set(te.CLASSES) <= classes


# --- record level -------------------------------------------------------------------------------------------------------

def test_final_answer_line_is_excluded_from_the_trace():
    text = "v = 5.3866 m/s\nFinal answer: 6.4 m/s"
    assert te.trace_region(text, thinking_expected=False) == "v = 5.3866 m/s"
    res = te.classify_record(record(text, 6.4), ctx())
    assert res.status == "TRACE_CORRECT" and res.matches_gold and res.matches_misuse == []


def test_first_of_several_final_lines_ends_the_trace():
    text = "v = 5.3866 m/s\nFinal answer: 6.4 m/s\nHmm.\nFinal answer: 6.4 m/s"
    assert te.trace_region(text, thinking_expected=False) == "v = 5.3866 m/s"


def test_latex_wrapped_final_line_is_excluded():
    text = "v = 5.3866 m/s\n**Final answer:** \\boxed{6.4} m/s"
    assert "6.4" not in te.trace_region(text, thinking_expected=False)


def test_every_record_keeps_all_candidate_statements_and_matches():
    res = classify("a = 2.1 m/s^2\nv = 6.4 m/s\nv = 5.39 m/s")
    assert [s.text for s in res.statements] == ["6.4", "5.39"] and res.n_candidates == 2
    assert res.matches_gold and res.matches_misuse == []
    ambiguous = classify("v = 5.39 m/s", misuse={"add:x": 5.388, "copy": 3.0})
    assert ambiguous.matches_gold and ambiguous.matches_misuse == ["add:x"]
    flipped = classify("v = 3.2 m/s", gold=-3.2, misuse={"add:x": -6.0})
    assert flipped.sign_only and flipped.matches_gold and not flipped.matches_misuse


def test_declared_view_tolerance_rule():
    assert te.within_tolerance("5.39", 5.39, 1.0, GOLD, "declared")
    assert te.within_tolerance("5.4", 5.4, 1.0, GOLD, "declared")
    assert not te.within_tolerance("5", 5.0, 1.0, GOLD, "declared")  # half a unit would allow it; the 0.5% guard does not
    assert te.within_tolerance("5.38660001", 5.38660001, 1.0, GOLD, "declared")
    assert te.within_tolerance("252.984", 252.984, 1.0, 252.9822, "declared")  # long value, intermediate rounding noise
    assert not te.within_tolerance("5.35", 5.35, 1.0, GOLD, "declared")
    assert te.within_tolerance("5.35", 5.35, 1.0, GOLD, "rel1pct")
    assert te.within_tolerance("19.4", 19.4, 1 / 3.6, GOLD, "declared")


def test_view_names_are_normalised():
    assert te.normalise_view("grade_declared") == "declared" and te.normalise_view("grade_rel1pct") == "rel1pct"
    with pytest.raises(ValueError):
        te.normalise_view("grade_nonsense")


def test_normalisation_examples():
    assert te.normalise_trace("$4.5 \\times 10^{-4}\\,\\text{m}$").strip() == "4.5e-4 m"
    assert te.normalise_trace("\\frac{12}{2.2}").strip() == "(12)/(2.2)"
    assert te.normalise_trace("1.5 \\approx 1.6").strip() == "1.5 ≈ 1.6"
    assert te.normalise_trace("117,600 Pa").strip() == "117600 Pa"
    assert te.normalise_trace("x = 45^\\circ ok").split()[:4] == ["x", "=", "45", "deg"]


def test_target_terms_from_the_question():
    assert te.derive_target_terms("What is the speed of the block after it has slid that distance?") == (("speed",), ("v",))
    assert te.derive_target_terms("Using the relation between kinetic energy and speed, what is the speed of the electrons?")[0] \
        == ("speed",)
    assert te.derive_target_terms("How far from the lens is the real image formed?")[0] == ("distance",)
    assert te.derive_target_terms("What is the angular separation between the two wavelengths?") == ((), ())


def test_context_from_row_reads_prompt_and_role():
    row = {"prompt": "A block of mass 2 kg moves at 3.0 m/s. A cart nearby has 0.8 m/s.\n\nWhat is the speed of the block?",
           "gold_value": 5.3866, "gold_unit": "m/s", "foils": {"copy": 0.8, "neglect": 5.0},
           "role": {"value": 0.8, "unit": "m/s"}}
    c = te.context_from_row(row, None, "grade_declared")
    assert c.target_phrases == ("speed",) and c.target_symbols == ("v",) and c.view == "declared"
    assert c.q == (0.8, "m/s") and c.misuse == {"copy": 0.8} and (3.0, "m/s") in c.prompt_numerals


# --- TC and the scorecard hook ------------------------------------------------------------------------------------------------

def d_cell(key="S01-i0:D:z0:d0", stratum="D", value_index=0, heldout=False, foils=None, confounded=None):
    return rs.Cell(key, "S01", stratum, value_index, "d0", GOLD, dict(foils or {"add:x": 6.4, "copy": 3.0}), None,
                   list(confounded or []), heldout)


def rec(cell, i, trace, final, **kw):
    text = f"{trace}\nFinal answer: {final} m/s" if trace is not None else f"Final answer: {final} m/s"
    r = record(text, final, **kw)
    r["job_id"] = f"{cell}:s{i}"
    return r


def world():
    cell = d_cell()
    cells = {cell.key: cell, "S01-i0:R:z0:r0": d_cell("S01-i0:R:z0:r0", stratum="R"),
             "S01-i0:D:z9:d0": d_cell("S01-i0:D:z9:d0", value_index=9, heldout=True)}
    k = cell.key
    records = [
        rec(k, 0, "v = 5.3866 m/s", 6.4),  # TRACE_CORRECT
        rec(k, 1, "v = 6.4 m/s", 6.4),  # TRACE_MISUSE
        rec(k, 2, "v = 7.7 m/s", 6.4),  # TRACE_OTHER
        rec(k, 3, "v = -5.3866 m/s", 6.4),  # TRACE_AMBIGUOUS (sign only)
        rec(k, 4, "We solve for the unknown.", 6.4),  # NO_TRACE_VALUE
        rec(k, 5, None, 6.4),  # NO_TRACE
        rec(k, 6, "v = 5.39 m/s", 5.39),  # final is the gold: not eligible
        rec(k, 7, "v = 9.9 m/s", 9.9),  # final matches nothing: not eligible
        rec(k, 8, "v = 3.0 m/s", 3.0),  # final matches a non-attributed class: not eligible
        {**rec(k, 9, "v = 5.3866 m/s", 6.4), "completion_status": "BUDGET_EXHAUSTED"},  # not complete
        rec("S01-i0:R:z0:r0", 0, "v = 5.3866 m/s", 6.4),  # another stratum
        rec("S01-i0:D:z9:d0", 0, "v = 5.3866 m/s", 6.4),  # held-out value
    ]
    return records, cells


def test_trace_inputs_counts_and_the_tc_estimand():
    records, cells = world()
    out = te.trace_inputs(records, cells, {"add": {"attribution": "ATTRIBUTED"}, "copy": {"attribution": "NOT_ATTRIBUTED"}},
                          "grade_declared")
    assert out["extractor_frozen"] is True and out["extractor_version"] == "h4-v1" and out["reasoning_trace"] is True
    assert (out["x"], out["n"]) == (1, 3) and out["relevance_delta"] is None
    c = out["counts"]
    assert (c["TRACE_CORRECT"], c["TRACE_MISUSE"], c["TRACE_OTHER"], c["TRACE_AMBIGUOUS"], c["NO_TRACE_VALUE"],
            c["NO_TRACE"]) == (1, 1, 1, 1, 1, 1)
    assert c["d_samples_complete"] == 9 and c["final_matches_attributed_curve"] == 6 and c["excluded_from_n"] == 3
    assert c["final_also_within_gold_tolerance"] == 1
    assert out["sensitivity"]["unclassifiable_as_not_correct"]["x"] == 1
    assert out["sensitivity"]["unclassifiable_as_not_correct"]["n"] == 6
    assert out["attributed_curves"] == ["add"] and out["by_curve"]["add"]["TRACE_CORRECT"] == 1


def test_trace_inputs_with_a_list_of_curves_and_record_details():
    records, cells = world()
    out = te.trace_inputs(records, cells, ["add"], "declared", return_records=True)
    assert [r["label"] for r in out["records"]][:2] == ["TRACE_CORRECT", "TRACE_MISUSE(add:x)"]
    assert te.trace_inputs(records, cells, [], "declared")["n"] == 0


def test_confounded_foils_are_not_attributed_matches():
    records, cells = world()
    cells["S01-i0:D:z0:d0"].confounded.append("add:x~gold")
    assert te.trace_inputs(records, cells, ["add"], "declared")["n"] == 0


def test_non_reasoning_records_give_no_reasoning_trace_and_h4_not_evaluated():
    cell = d_cell()
    records = [rec(cell.key, i, None, 6.4) for i in range(6)]
    out = te.trace_inputs(records, {cell.key: cell}, ["add"], "declared")
    assert out["reasoning_trace"] is False and out["counts"]["NO_TRACE"] == 6 and out["n"] == 0
    from test_scorecard import family, inputs, misuse_entry, status

    att = {"D": {"add": misuse_entry("ATTRIBUTED", 0.3)}}
    assert status(sc.scorecard(inputs(family=family(f1=0.3), misuse=att, trace=out)), "H4") == "NOT_EVALUATED"


def test_trace_inputs_feed_h4_unchanged():
    from test_scorecard import family, inputs, misuse_entry, status

    cell = d_cell()
    att = {"D": {"add": misuse_entry("ATTRIBUTED", 0.3)}}

    def h4(n_correct, n_misuse):
        recs = [rec(cell.key, i, "v = 5.3866 m/s", 6.4) for i in range(n_correct)]
        recs += [rec(cell.key, n_correct + i, "v = 6.4 m/s", 6.4) for i in range(n_misuse)]
        trace = te.trace_inputs(recs, {cell.key: cell}, ["add"], "declared")
        return status(sc.scorecard(inputs(family=family(f1=0.3), misuse=att, trace=trace)), "H4")

    assert h4(45, 15) == "SUPPORTED"
    assert h4(10, 50) == "CONTRADICTED"
    assert h4(4, 3) == "INCONCLUSIVE"


# --- the freeze guard ---------------------------------------------------------------------------------------------------------

def test_extractor_is_frozen_at_the_pinned_version_and_fingerprint():
    assert te.EXTRACTOR_FROZEN is True
    assert te.TRACE_EXTRACTOR_VERSION == "h4-v1"
    assert te.extractor_fingerprint() == PINNED_FINGERPRINT, (
        "a rule of the extractor changed: after any G3 record this needs a new TRACE_EXTRACTOR_VERSION")


# --- real traces --------------------------------------------------------------------------------------------------------------

def real_cases():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def real_label(case):
    c = te.context_from_row({"prompt": case["prompt"], "gold_unit": case["gold_unit"], "gold_value": case["gold"],
                             "foils": case["misuse"]}, None, case["view"])
    return te.classify_trace(te.trace_region(case["text"], thinking_expected=case["thinking_mode"] == "on"), c).label


def test_real_traces_cover_four_model_configurations_and_enough_cases():
    cases = real_cases()
    assert len(cases) >= 15
    assert {c["model_id"] for c in cases} >= {"Qwen/Qwen3-8B"} and len({c["run"] for c in cases}) == 4
    families = {c["model_id"].split("/")[-1].split("-")[0] for c in cases}
    assert len(families) >= 3
    assert any(c["thinking_mode"] == "on" for c in cases)


def test_real_traces_are_verbatim_copies_of_the_stage15_records():
    first = real_cases()[0]
    source = REPO_ROOT / "results" / "stage15" / first["run"] / "raw_records.jsonl"
    if not source.exists():
        pytest.skip("stage-15 raw records not present")
    wanted = {(c["run"], c["job_id"]): c["text"] for c in real_cases()}
    seen = 0
    for run in {c["run"] for c in real_cases()}:
        path = REPO_ROOT / "results" / "stage15" / run / "raw_records.jsonl"
        for line in path.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            if (run, r["job_id"]) in wanted:
                assert r["generated_answer_raw"] == wanted[(run, r["job_id"])]
                seen += 1
    assert seen == len(wanted)


def test_real_trace_agreement_with_the_hand_labels():
    cases = real_cases()
    disagreements = {c["id"] for c in cases if real_label(c) != c["hand_label"]}
    assert disagreements == KNOWN_REAL_DISAGREEMENTS
    assert 1 - len(disagreements) / len(cases) >= 0.90
