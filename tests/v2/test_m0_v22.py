"""Tests for M0 v2.2 (journal J15.1-038): M0 v2.1 minus S02 (rejected), with S20, S26 and S92 changed after the panel review.

The M0 v2.1 builder's own checks (scene clause is the only change to the October problem, base gold unchanged, rendering and
numeral self-checks, unique job ids) run inside the build. Here: the changed specs certify and are complete; their R golds equal
independent closed forms; every unchanged structure's cells equal M0 v2.1's except the version field.
"""

from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.benchmark.v2 import rolevalue_v2 as r2  # noqa: E402
from physmon.benchmark.v2 import roles_m0v21, roles_m0v22  # noqa: E402

G = 9.8
CHANGED = {"S20", "S26", "S92"}


def _load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    s195 = _load("s195", "scripts/v2/s195_build_m0_v22.py")
    out = tmp_path_factory.mktemp("m0v22") / "m0_v22"
    manifest = s195.s192.build(out, REPO_ROOT / "data/v2/dataset/v1/dataset.jsonl")
    rows = [json.loads(line) for line in (out / "cells.jsonl").read_text(encoding="utf-8").splitlines()]
    return manifest, rows


def test_s02_is_rejected_and_the_other_eleven_are_kept():
    assert set(roles_m0v22.REJECTED) == {"S02"}
    assert set(roles_m0v22.ROLE_SPECS) == set(roles_m0v21.ROLE_SPECS) - {"S02"}
    for sid, spec in roles_m0v22.ROLE_SPECS.items():
        assert (spec is roles_m0v21.ROLE_SPECS[sid]) == (sid not in CHANGED)
        if sid in CHANGED:
            assert spec.version == "v2.2"


@pytest.mark.parametrize("sid", sorted(CHANGED))
def test_changed_specs_certify_and_are_complete(sid):
    cert = r2.certify_v2(roles_m0v22.structure(sid), roles_m0v22.ROLE_SPECS[sid])
    assert not cert["failed"], cert["failed"]
    assert r2.complete(roles_m0v22.ROLE_SPECS[sid], cert)


def test_build_has_no_exclusions_and_eleven_structures(built):
    manifest, rows = built
    assert manifest["excluded"] == []
    assert manifest["n_structures"] == 11 and "S02" not in manifest["by_structure"]
    assert manifest["version"] == "m0_v2.2"


CLOSED = {
    "S20": lambda q: 12 * (40 + q) / (40 + q - 12),
    "S26": lambda q: math.degrees(math.asin(math.sin(math.radians(40 + q)) / 1.5)),
    "S92": lambda q: q * G * 1e-3 - 600 * 1e-3 * G,
}


@pytest.mark.parametrize("sid", sorted(CHANGED))
def test_r_golds_equal_closed_forms_and_d_golds_the_base(sid, built):
    _, rows = built
    base = next(r for r in rows if r["structure_id"] == sid and r["stratum"] == "none")["gold_value"]
    rd = [r for r in rows if r["structure_id"] == sid and r["family"] == "role_by_value" and r["stratum"] in ("R", "D")]
    assert len(rd) == 2 * 2 * 3  # R and D, two pairs, three study values (held-out values are certified, not celled)
    for r in rd:
        expected = CLOSED[sid](r["value"]) if r["stratum"] == "R" else base
        assert r["gold_value"] == pytest.approx(expected, rel=1e-9), r["cell_id"]


def test_changed_sentences_are_the_reviewed_fixes(built):
    _, rows = built
    sentences = {(r["structure_id"], r["stratum"], r["pair_id"]) : r["sentence"] for r in rows
                 if r["structure_id"] in CHANGED and r["stratum"] in ("R", "D", "N") and r.get("value_index") in (0, None)}
    text = " ".join(sentences.values())
    assert "stool" not in text and "desk lamp" not in text
    assert sentences[("S92", "R", "p1")].startswith("Before the tension was measured, the liquid in the tank was replaced")
    assert "with the string still holding the cube under it" in sentences[("S92", "D", "p1")]
    assert sentences[("S20", "D", "p0")].startswith("The lamp that stands beside the bench is then pushed")
    assert sentences[("S26", "D", "p0")].startswith("The camera that films the interface is then tilted")
    assert sentences[("S26", "R", "p1")].endswith("in the plane of incidence before the refraction was observed.")


def test_unchanged_structures_equal_m0_v21_except_the_version(built):
    _, rows = built
    committed = REPO_ROOT / "data/v2/dataset/m0_v21/cells.jsonl"
    old = {}
    for line in committed.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r["structure_id"] not in CHANGED | {"S02"}:
            old[r["job_id"]] = r
    new = {r["job_id"]: r for r in rows if r["structure_id"] not in CHANGED}
    assert set(new) == set(old)
    for job_id, r in new.items():
        a = {k: v for k, v in r.items() if k != "m0_version"}
        b = {k: v for k, v in old[job_id].items() if k != "m0_version"}
        assert a == b, job_id
