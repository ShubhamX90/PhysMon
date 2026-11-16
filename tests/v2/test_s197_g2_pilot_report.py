"""Tests of the G2 design-validation pilot report (`scripts/v2/s197_g2_pilot_report.py`) on a small synthetic record set built from
real M0 v2.2 cells with known answers. No GPU, no stored run is read."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
CELLS = REPO / "data/v2/dataset/m0_v22/cells.jsonl"
SPEC = importlib.util.spec_from_file_location("s197_report", REPO / "scripts/v2/s197_g2_pilot_report.py")
rep = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rep)

pytestmark = pytest.mark.skipif(not CELLS.exists(), reason="M0 v2.2 cells not present")

S01_NO_CUE = "S01-i0:no_cue"
S01_R0 = "S01-i0:R:z0:r0:after_context"
S01_R1 = "S01-i0:R:z0:r1:after_context"
S01_D0 = "S01-i0:D:z0:d0:after_context"
S01_N0 = "S01-i0:N:d0:after_context"
S26_NO_CUE = "S26-i0:no_cue"
S26_R1 = "S26-i0:R:z0:r1:after_context"
USED = (S01_NO_CUE, S01_R0, S01_R1, S01_D0, S01_N0, S26_NO_CUE, S26_R1)


@pytest.fixture(scope="module")
def rows():
    all_rows = {r["job_id"]: r for r in map(json.loads, CELLS.read_text().splitlines()) if r["job_id"] in USED}
    assert set(all_rows) == set(USED)
    return all_rows


def record(row, i, value, status="COMPLETE", grade=None, unparsed=False, tokens=500, text="x" * 600 + "END"):
    gold = row["gold_value"]
    ok = value is not None and abs(value - gold) <= 0.005 * abs(gold)
    g = grade or ("correct" if ok else "wrong")
    complete = status == "COMPLETE"
    return {"job_id": f"{row['job_id']}:s{i}", "completion_status": status, "gold_value": gold, "gold_unit": row["gold_unit"],
            "grade_declared": g if complete else status, "grade_convertible": g if complete else status,
            "grade_rel1pct": g if complete else status,
            "value_in_gold_unit": None if (unparsed or not complete) else value,
            "parsed_answer": None if not complete else {"unit": row["gold_unit"], "value": value},
            "n_generated_tokens": tokens, "generated_answer_raw": text}


def make_records(rows, d_unparsed=3, none_n=True):
    r0, r1, d0, n0 = rows[S01_R0], rows[S01_R1], rows[S01_D0], rows[S01_N0]
    base, add = rows[S01_NO_CUE]["gold_value"], d0["foils"]["add:m2"]
    out = []
    # no-cue: 6 correct, 12 wrong, 6 budget exhausted (one of them carries an adversarial "correct" grade)
    nc = rows[S01_NO_CUE]
    out += [record(nc, i, base) for i in range(6)] + [record(nc, i, 123.4) for i in range(6, 18)]
    out += [record(nc, i, None, status="BUDGET_EXHAUSTED", tokens=4096) for i in range(18, 24)]
    out[-1]["grade_declared"] = "correct"
    # R phrasing r0: 20 at the R gold, 4 at the base gold; r1: 4 at the R gold, 20 at the base gold
    out += [record(r0, i, r0["gold_value"] if i < 20 else base) for i in range(24)]
    out += [record(r1, i, r1["gold_value"] if i < 4 else base) for i in range(24)]
    # D: 10 base gold, 6 add:m2, 5 other, d_unparsed COMPLETE records without a value, rest 123.4
    vals = [base] * 10 + [add] * 6 + [55.5] * 5 + [None] * d_unparsed
    vals += [123.4] * (24 - len(vals))
    out += [record(d0, i, v, unparsed=v is None, grade="wrong" if v is None else None) for i, v in enumerate(vals)]
    # N: every answer is 123.4, which no certified route predicts
    out += [record(n0, i, 123.4 if none_n else base) for i in range(24)]
    # S26: no-cue all correct, R r1 cell: all at the base gold (neglect)
    s26b = rows[S26_NO_CUE]
    out += [record(s26b, i, s26b["gold_value"]) for i in range(24)]
    s26r = rows[S26_R1]
    out += [record(s26r, i, s26b["gold_value"]) for i in range(24)]
    return out


def run_report(rows, runs):
    return rep.build_report(list(rows.values()), runs)


def test_grading_block(rows):
    report, _ = run_report(rows, {"m": make_records(rows)})
    g = report["models"]["m"]["grading"]["all"]
    none = g["none"]
    assert none["o3_statuses"] == {"BUDGET_EXHAUSTED": 6, "COMPLETE": 42}  # S01 (18 + 6) and S26 (24)
    # non-COMPLETE is its own category: the denominator is the COMPLETE records; the adversarial "correct" budget record is not counted
    assert none["n_complete"] == 42 and none["correct"]["declared"] == {"k": 30, "n": 42, "share": 30 / 42}
    assert g["R"]["correct"]["declared"]["k"] == 24 and g["R"]["correct"]["declared"]["n"] == 72  # S26 R answers the base gold
    # a missing stratum row (C, K, support cells have no records here) never appears as a measured zero
    assert "C" not in g
    # gap between views: here the three views agree, so the gap is a measured zero with its denominator
    assert g["R"]["gap_rel1pct_minus_declared"] == {"k": 0, "n": 72, "share": 0.0}


def test_parse_failure_flag_over_five_percent(rows):
    report, _ = run_report(rows, {"m": make_records(rows, d_unparsed=3)})
    assert report["models"]["m"]["parse_flagged_cells"] == [S01_D0]
    assert report["models"]["m"]["cells"][S01_D0]["unparsed_complete"] == {"k": 3, "n": 24, "share": 3 / 24}
    report, _ = run_report(rows, {"m": make_records(rows, d_unparsed=1)})  # 1/24 = 4.2%, below the 5% flag
    assert report["models"]["m"]["parse_flagged_cells"] == []
    # a budget-exhausted cell is a format/budget matter, not a parse failure among COMPLETE
    assert report["models"]["m"]["cells"][S01_NO_CUE]["unparsed_complete"]["k"] == 0


def test_certification_shares_and_modal(rows):
    report, _ = run_report(rows, {"m": make_records(rows)})
    cells = report["models"]["m"]["cells"]
    r0, r1 = cells[S01_R0]["certification"], cells[S01_R1]["certification"]
    assert r0["r_gold"]["share"] == 20 / 24 and r0["base_gold"]["share"] == 4 / 24
    assert r1["r_gold"]["share"] == 4 / 24 and r1["base_gold"]["share"] == 20 / 24
    assert r0["modal"]["kind"] == "gold" and r1["modal"]["kind"] == "foil" and "neglect" in r1["modal"]["matches"]
    d = cells[S01_D0]["certification"]
    assert d["base_gold"] == {"k": 10, "n": 24, "share": 10 / 24}  # the 3 COMPLETE records without a value stay in the denominator
    assert d["misuse"]["by_class"]["add"]["k"] == 6 and d["misuse"]["any"]["k"] >= 6
    assert d["modal"]["status"] == "OK" and d["modal"]["kind"] == "gold" and d["modal"]["count"] == 10 and d["modal"]["n_valued"] == 21
    assert cells[S01_N0]["certification"]["modal"]["kind"] == "none" and cells[S01_N0]["certification"]["modal"]["value"] == 123.4
    assert cells[S01_N0]["certification"]["misuse"] is None  # N cells declare no misuse value
    assert rep.sig4(2.17777777) == 2.178


def test_modal_none_flag_needs_every_model(rows):
    both = {"a": make_records(rows), "b": make_records(rows)}
    report, _ = run_report(rows, both)
    assert S01_N0 in report["modal_none_in_every_model"] and S01_D0 not in report["modal_none_in_every_model"]
    mixed = {"a": make_records(rows), "b": make_records(rows, none_n=False)}  # model b answers the N cell with the base gold
    report, _ = run_report(rows, mixed)
    assert S01_N0 not in report["modal_none_in_every_model"]
    assert S01_R0 not in report["modal_none_in_every_model"]


def test_ambiguity_block(rows):
    report, _ = run_report(rows, {"m": make_records(rows)})
    amb = report["models"]["m"]["ambiguity"]
    s01 = amb["per_structure"]["S01"]["R"]
    assert s01["agreement"] == "DISAGREE" and s01["diff"] == pytest.approx(16 / 24)
    assert s01["a"]["n"] == 24 and s01["b"]["n"] == 24
    assert amb["per_structure"]["S01"]["D"]["agreement"] == rep.NOT_EVALUATED  # D has only phrasing d0 here
    assert "S01" in amb["wording_dependent"]
    assert amb["cross_structure_rule_B"]["R"]["agreement"] == rep.NOT_EVALUATED  # fewer than 6 structures (decision 4)
    med = amb["medium_flag_cells"]
    assert med["S26 R:r1"][S26_R1]["certification"]["base_gold"]["share"] == 1.0
    assert med["S55 R:r1"] == rep.NOT_EVALUATED  # no S55 cell in this synthetic set
    assert report["wording_dependent"] == {"S01": ["m"]} and report["wording_review_required"] == []
    two, _ = run_report(rows, {"a": make_records(rows), "b": make_records(rows)})
    assert two["wording_review_required"] == ["S01"]


def test_agreement_states():
    assert rep.agreement_per_structure(200, 400, 200, 400, 0.10)["agreement"] == "AGREE"
    assert rep.agreement_per_structure(20, 24, 4, 24, 0.10)["agreement"] == "DISAGREE"
    assert rep.agreement_per_structure(10, 24, 8, 24, 0.10)["agreement"] == "UNRESOLVED"
    assert rep.agreement_per_structure(0, 0, 5, 24, 0.10)["agreement"] == rep.NOT_EVALUATED


def test_feasibility_block(rows):
    report, _ = run_report(rows, {"m": make_records(rows)})
    f = report["models"]["m"]["feasibility"]["by_structure"]["S01"]
    assert f["no_cue"]["correct_of_all_samples"] == {"k": 6, "n": 24, "share": 0.25}
    assert f["no_cue"]["correct_of_complete"]["share"] == 6 / 18 and f["no_cue"]["n_noncomplete"] == 6
    assert f["no_cue"]["in_band"] is False  # 0.25 < 0.30
    assert f["T_R"]["of_complete"] == {"k": 24, "n": 48, "share": 0.5}
    assert f["budget_exhaustion"] == {"k": 6, "n": 120, "share": 6 / 120} and f["format_failure"]["k"] == 0
    assert f["tokens"]["max"] == 4096 and f["tokens"]["n"] == 120
    s26 = report["models"]["m"]["feasibility"]["by_structure"]["S26"]
    assert s26["no_cue"]["in_band"] is False  # 1.0 > 0.85


def test_missing_records_are_not_evaluated(rows):
    report, _ = run_report(rows, {"m": make_records(rows)[:24]})  # only the no-cue cell has records
    m = report["models"]["m"]
    assert m["n_cells_without_records"] == len(rows) - 1
    assert m["cells"][S01_R0]["status"] == rep.NOT_EVALUATED
    assert m["grading"]["all"]["R"] == {"status": rep.NOT_EVALUATED, "n_cells": 2 + 1, "n_cells_missing": 3}
    assert m["grading"]["by_structure"]["S01"]["R"]["status"] == rep.NOT_EVALUATED
    assert rep.fmt(m["cells"][S01_R0].get("tracking_all")) == rep.NOT_EVALUATED


def test_format_failures_are_not_wrong(rows):
    records = make_records(rows)
    nc = rows[S01_NO_CUE]
    records += [record(nc, 24 + i, None, status="UNPARSEABLE") for i in range(3)]
    report, _ = run_report(rows, {"m": records})
    cell = report["models"]["m"]["cells"][S01_NO_CUE]
    assert cell["statuses"]["UNPARSEABLE"] == 3 and cell["n_complete"] == 18
    assert cell["correct"]["declared"]["n"] == 18  # not in the denominator, so never wrong
    assert cell["format_flag"] is True and cell["parse_flag"] is False
    assert report["models"]["m"]["feasibility"]["by_structure"]["S01"]["format_failure"]["k"] == 3


def test_audit_sample_is_seeded_and_tailed(rows):
    records = make_records(rows)
    _, first = run_report(rows, {"m": records})
    _, second = run_report(rows, {"m": list(reversed(records))})
    assert first == second  # independent of record order
    per_stratum = {s: [x for x in first if x["stratum"] == s] for s in {x["stratum"] for x in first}}
    assert all(len(v) <= rep.AUDIT_N for v in per_stratum.values()) and len(per_stratum["R"]) == 10
    assert all(len(x["response_tail"]) == 400 and x["response_tail"].endswith("END") for x in first if x["completion_status"] == "COMPLETE")
    assert {"cell", "gold_value", "parsed_answer", "response_tail"} <= set(first[0])


def test_cli_writes_and_refuses_overwrite(rows, tmp_path, capsys):
    rec_path = tmp_path / "raw_records.jsonl"
    rec_path.write_text("\n".join(json.dumps(r) for r in make_records(rows)) + "\n")
    out = tmp_path / "out"
    args = ["--cells", str(CELLS), "--records", f"run_a={rec_path}", "--out-dir", str(out)]
    assert rep.main(args) == 0
    assert sorted(p.name for p in out.iterdir()) == sorted(rep.OUTPUT_FILES)
    md = (out / "report.md").read_text()
    assert "### 1. Grading" in md and "### 4. Feasibility" in md and "no F1-F3" in md
    assert json.loads((out / "report.json").read_text())["models"]["run_a"]["n_records"] == len(make_records(rows))
    before = {p.name: p.read_text() for p in out.iterdir()}
    assert rep.main(args) == 2
    assert "refusing to overwrite" in capsys.readouterr().err
    assert {p.name: p.read_text() for p in out.iterdir()} == before
    with pytest.raises(FileExistsError):
        rep.write_outputs(out, {}, [])
    (out / "report.md").unlink()
    with pytest.raises(FileExistsError):  # one existing file is enough to refuse, and nothing else is written
        rep.write_outputs(out, {}, [])
    assert not (out / "report.md").exists()
