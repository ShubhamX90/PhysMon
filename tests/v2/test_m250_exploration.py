"""Tests for the M250 EXPLORATION integration builder (s198) and its panel packets (s199).

One module-scoped build into a tmp directory: three M0 v2.2 structures (byte identity with `m0_v22`), one upgraded v1 structure
(S04), and planted fixtures: an exact copy of S04 under a new id (S901), a spec that cannot certify (S902), and a module whose
`structure()` raises (S903). The planted ones must be REJECTED with the failing check recorded and have no cells; the build must
not crash.
"""

from __future__ import annotations

import dataclasses
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.benchmark.v2 import roles_m250_a  # noqa: E402

M0_SIDS = ("S01", "S13", "S72")
V1 = REPO_ROOT / "data/v2/dataset/v1/dataset.jsonl"
M0_REF = REPO_ROOT / "data/v2/dataset/m0_v22/cells.jsonl"


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


s198 = _load("s198_t", "scripts/v2/s198_build_m250_exploration.py")
s199 = _load("s199_t", "scripts/v2/s199_m250_panel_packets.py")


def restricted(key: str, module: str, kind: str, ids: tuple[str, ...]):
    source = s198.Source.load(key, module, kind, None)
    assert not source.error, source.error
    source.specs = {sid: source.specs[sid] for sid in ids}
    return source


def planted_source():
    base_structure = roles_m250_a.structure("S04")
    spec = roles_m250_a.SPECS["S04"]
    terms = roles_m250_a.TARGET_TERMS["S04"]
    tiny = dataclasses.replace(spec, structure_id="S902", values=(1e-9, 2e-9, 3e-9))

    def structure(sid):
        if sid == "S903":
            raise RuntimeError("planted failure")
        return dataclasses.replace(base_structure, structure_id=sid)

    module = SimpleNamespace(
        SPECS={"S905": dataclasses.replace(spec, structure_id="S905", version="v2.2"), "S901": dataclasses.replace(spec, structure_id="S901"), "S902": tiny,
               "S903": dataclasses.replace(spec, structure_id="S903")},
        structure=structure, INFEASIBLE={"S904": "planted infeasible structure with a reason"}, NO_C={}, NO_K={},
        TARGET_TERMS={"S901": terms, "S902": terms, "S903": terms, "S905": terms})
    return s198.Source("planted", "planted_module", "NEW").bind(module, {})


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    sources = [restricted("m0", s198.M0_MODULE, "M0", M0_SIDS), restricted("m250_a", "roles_m250_a", "UPGRADED_V1", ("S04",)),
               planted_source(), s198.Source.load("gone", "roles_does_not_exist", "NEW", None)]
    out = tmp_path_factory.mktemp("m250") / "m250_explore_v1"
    manifest = s198.build(out, sources, V1, "2026-11-16")
    rows = [json.loads(x) for x in (out / "cells.jsonl").read_text(encoding="utf-8").splitlines()]
    return out, manifest, rows


def admission(out: Path, sid: str) -> dict:
    return json.loads((out / "admission" / f"{sid}.json").read_text(encoding="utf-8"))


REQUIRED = ("1.1", "1.2.text", "1.2.program", "1.2.value_signature", "1.3", "2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "2.7", "2.7b",
            "2.8", "3.0", "3.7", "3.8", "3.1", "3.2", "3.3", "3.4", "3.5", "3.4.base", "4.1", "4.2", "6.2")


def test_every_check_is_recorded_for_every_admitted_structure(built):
    out, manifest, _ = built
    assert set(manifest["admitted"]) == {*M0_SIDS, "S04"}
    for sid in manifest["admitted"]:
        record = admission(out, sid)
        ids = {c["id"] for c in record["checks"]}
        assert set(REQUIRED) <= ids, sorted(set(REQUIRED) - ids)
        assert all(c["status"] == "PASS" for c in record["checks"]), record["failed_checks"]
        assert record["data_role"] == "EXPLORATION" and record["instance"] == 0
        assert record["lineage"]["kind"] in ("M0", "UPGRADED_V1")
    assert admission(out, "S04")["panel"]["status"] == "PENDING"
    for sid in ("S01", "S13"):  # M0 is no longer an admitted pilot: PENDING like every other structure
        assert admission(out, sid)["panel"]["status"] == "PENDING" and admission(out, sid)["judge_checks_pending"]


def test_planted_exact_copy_is_caught_by_identity_and_overlap_checks(built):
    out, manifest, rows = built
    record = admission(out, "S901")
    assert record["status"] == "REJECTED"
    by_id = {c["id"]: c for c in record["checks"]}
    assert by_id["1.1"]["status"] == "FAIL" and "S04" in by_id["1.1"]["values"]["duplicates_by_hash"]
    assert by_id["1.2.program"]["status"] == "FAIL" and "S04" in by_id["1.2.program"]["values"]["equal_program_hash_with"]
    assert by_id["1.2.text"]["status"] == "FAIL" and by_id["1.2.text"]["values"]["score"] >= 0.85
    assert by_id["1.2.value_signature"]["status"] == "FAIL"
    assert not [r for r in rows if r["structure_id"] == "S901"]
    assert any(r["structure_id"] == "S901" for r in manifest["rejected"])


def test_text_detector_catches_a_planted_near_duplicate():
    pool = s198.pool_for(V1)
    original = next(e for e in pool.entries if e.sid == "S04" and e.origin == "dataset_v1")
    planted = original.text.replace("block", "cart", 1) + " It starts at rest."
    hit = s198.detect_text(planted, pool.entries, "S999")
    assert hit["flagged"] and hit["nearest"] == "S04" and hit["score"] >= 0.85
    unrelated = s198.detect_text("A completely different sentence about a lens # cm.", pool.entries, "S999")
    assert not unrelated["flagged"]


def test_planted_failing_specs_are_rejected_without_cells_and_without_a_crash(built):
    out, manifest, rows = built
    tiny = admission(out, "S902")
    assert tiny["status"] == "REJECTED" and "2.2" in {c["id"] for c in tiny["failed_checks"]}
    crash = admission(out, "S903")
    assert crash["status"] == "REJECTED" and crash["failed_checks"][0]["id"] == "0"
    assert not [r for r in rows if r["structure_id"] in ("S902", "S903")]
    assert "S902" in (out / "README.md").read_text(encoding="utf-8")
    assert [m["module"] for m in manifest["missing_or_broken_modules"]] == ["roles_does_not_exist"]
    assert "roles_does_not_exist" in (out / "README.md").read_text(encoding="utf-8")
    assert manifest["not_built_infeasible"][0]["structure_id"] == "S904"
    certificates = json.loads((out / "certificates.json").read_text(encoding="utf-8"))
    assert certificates["S902"]["status"] == "REJECTED" and certificates["S902"]["role_certificate"]["failed"]


def test_m0_v22_cells_are_identical_except_the_added_fields(tmp_path):
    """Built from `roles_m0v22` explicitly (the M0 module of the real build may be a later one)."""

    ids = ("S01", "S72")
    out = tmp_path / "m0only"
    manifest = s198.build(out, [restricted("m0", "roles_m0v22", "M0", ids)], V1, "2026-11-16")
    rows = [json.loads(x) for x in (out / "cells.jsonl").read_text(encoding="utf-8").splitlines()]
    reference = {json.loads(x)["job_id"]: json.loads(x) for x in M0_REF.read_text(encoding="utf-8").splitlines()}
    added = set(manifest["added_row_fields"])
    assert added == {"dataset", "data_role", "m250_lineage", "m250_source_module"}
    assert {r["structure_id"] for r in rows} == set(ids) and len(rows) > 60
    for row in rows:
        stripped = {k: v for k, v in row.items() if k not in added}
        assert json.dumps(stripped, ensure_ascii=False, sort_keys=True) == json.dumps(
            reference[row["job_id"]], ensure_ascii=False, sort_keys=True), row["job_id"]
        assert row["data_role"] == "EXPLORATION" and row["dataset"] == "m250_explore_v1"


def test_manifest_hashes_every_file(built):
    out, manifest, _ = built
    import hashlib
    for name, digest in manifest["file_sha256"].items():
        assert hashlib.sha256((out / name).read_bytes()).hexdigest() == digest
    assert "admission/S04.json" in manifest["file_sha256"] and "README.md" in manifest["file_sha256"]
    assert manifest["provenance_consistency"]["verdict"] in ("PASS", "NOT_EVALUATED")


def test_composition_matches_a_hand_count():
    def rec(domain, kind, c, k, level="intro_university", n=2, fam=None):
        return {"domain": domain, "kind": kind, "has_c": c, "has_k": k, "level": level, "n_computed": n, "familiarity": fam}

    records = [rec("mechanics", "M0", True, False, fam="famous"), rec("mechanics", "NEW", True, True, fam="famous"),
               rec("optics", "NEW", False, True), rec("optics", "NEW", True, False, level="upper_university", fam="uncommon"),
               rec("quantum", "UPGRADED_V1", False, False, n=3), rec("fluids", "NEW", False, False)]
    comp = s198.composition(records)
    c63, c62 = comp["6.3"], comp["6.2"]
    assert comp["n_admitted_structures"] == 6 and comp["by_kind"] == {"M0": 1, "NEW": 4, "UPGRADED_V1": 1}
    assert c63["n_domains"] == 4 and c63["largest_domain_share"] == round(2 / 6, 4) and not c63["domains_ok"]
    assert c63["upper_university_or_multi_step"]["count"] == 2 and c63["upper_university_or_multi_step"]["share"] == round(2 / 6, 4)
    assert c63["new_structures"] == 4 and c63["c_feasible_share_of_new"] == 0.5 and c63["c_ok"]
    assert c63["k_feasible_share_of_new"] == 0.5 and c63["k_ok"]
    assert c62["c_quantities"] == 3 and c62["famous"] == 2 and c62["famous_share"] == round(2 / 3, 4) and not c62["ok"]
    assert s198.composition([])["6.3"]["c_feasible_share_of_new"] is None


def test_packets_are_written_without_key_leaks_and_never_overwrite(built, tmp_path):
    out, _, _ = built
    assert s199.packet_structures(out) == sorted([*M0_SIDS, "S04"], key=s198.sid_key)
    packets, scratch = tmp_path / "packets", tmp_path / "scratch"
    assert s199.main(["--dataset", str(out), "--out", str(packets), "--scratch", str(scratch)]) == 0
    for name in ("pass1_packets.jsonl", "pass2_packets.jsonl", "naturalness_packets.jsonl"):
        lines = [json.loads(x) for x in (packets / name).read_text(encoding="utf-8").splitlines()]
        assert lines
        for packet in lines:
            assert s199.leak_scan(packet) == [], (name, packet.get("item_id"))
    pass1 = [json.loads(x) for x in (packets / "pass1_packets.jsonl").read_text(encoding="utf-8").splitlines()]
    assert {p["item_id"] for p in pass1} == {f"M250-{sid}" for sid in (*M0_SIDS, "S04")}
    pass2 = [json.loads(x) for x in (packets / "pass2_packets.jsonl").read_text(encoding="utf-8").splitlines()]
    n_claims = [c for p in pass2 for c in p["authors_claims"] if c.get("numeral_free_twin_of")]
    assert n_claims and all(c["note"] == s199.N_NOTE for c in n_claims)
    assert not any("note" in c for p in pass2 for c in p["authors_claims"] if not c.get("numeral_free_twin_of"))
    assert (scratch / "m250_admission").is_dir() and (scratch / "m250_naturalness").is_dir()
    assignment = json.loads((packets / "assignment_naturalness.json").read_text(encoding="utf-8"))
    assert assignment["run_id"] == "m250_naturalness"
    keys = json.loads((packets / "naturalness_key_RESTRICTED.json").read_text(encoding="utf-8"))
    for batch in assignment["batches"]:
        assert len(batch["items"]) <= 24
        structures = [keys[i]["structure_id"] for i in batch["items"]]
        assert all(structures.count(s) <= 2 for s in structures)
        groups = [(keys[i]["structure_id"], keys[i]["group"]) for i in batch["items"]]
        assert len(groups) == len(set(groups))
    assert json.loads((packets / "assignment_admission.json").read_text(encoding="utf-8"))["run_id"] == "m250_admission"
    assert s199.main(["--dataset", str(out), "--out", str(packets), "--scratch", str(scratch)]) == 2


def test_spec_certified_under_a_version_other_than_v21_is_rejected(built):
    out, _, rows = built
    record = admission(out, "S905")
    assert record["status"] == "REJECTED" and "3.0" in {c["id"] for c in record["failed_checks"]}
    assert record["summary"]["cert_version"] == "v2.2" and not [r for r in rows if r["structure_id"] == "S905"]
    assert admission(out, "S04")["summary"]["cert_version"] == "v2.1"


def test_article_detector_flags_vowel_sound_numbers_only():
    flagged = ["A 8 kg block", "a 11 m rod", "a 18 N push", "pushed by a 85 N force", "a 8.5 kg block", "a 800 g mass",
               "a 11000 m ridge"]
    fine = ["An 8 kg block", "a 7 kg block", "a 0.8 kg block", "a 180 kg block", "a 12 kg block", "a 110 kg block", "an 18 N push"]
    assert s198.article_violations(flagged) == flagged
    assert s198.article_violations(fine) == []


def test_planted_article_and_pair_violations_fail_the_wording_checks():
    spec = roles_m250_a.SPECS["S04"]
    assert all(c["status"] == "PASS" for c in s198.wording_checks(spec))
    p0, p1 = spec.pairs
    article = dataclasses.replace(spec, values=(8.0, 11.0, 18.0), pairs=(
        dataclasses.replace(p0, frame="A {value} {unit} " + p0.frame.split("{unit} ", 1)[1]), p1))
    assert {c["id"]: c["status"] for c in s198.wording_checks(article)}["3.7"] == "FAIL"
    twin = dataclasses.replace(spec, pairs=(p0, dataclasses.replace(
        p1, frame=p0.frame, r_attach=p0.r_attach, d_attach=p0.d_attach)))
    result = {c["id"]: c for c in s198.wording_checks(twin)}
    assert result["3.8"]["status"] == "FAIL" and result["3.8"]["values"]["identical"]


def test_pair_differing_only_by_also_fails_distinctness_but_tense_passes():
    spec = roles_m250_a.SPECS["S04"]
    p0 = spec.pairs[0]
    twin = dataclasses.replace(spec, pairs=(p0, dataclasses.replace(
        p0, pair_id="p1", frame=p0.frame.replace(" is stuck", " is also stuck"))))
    result = {c["id"]: c for c in s198.wording_checks(twin)}["3.8"]
    assert result["status"] == "FAIL" and not result["values"]["word_difference"]["R"]["frames_differ"]
    tense = dataclasses.replace(spec, pairs=(p0, dataclasses.replace(p0, pair_id="p1", frame=p0.frame.replace(" is stuck", " was stuck"))))
    assert {c["id"]: c for c in s198.wording_checks(tense)}["3.8"]["status"] == "PASS"
    assert {c["id"]: c for c in s198.wording_checks(spec)}["3.8"]["status"] == "PASS"
