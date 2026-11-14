"""Tests of the requalification bank v5 (s187: Safeguards A and B, exclusions, determinism) and of s179's scoring under
`--protocol v3`, including a check that v2 scoring is byte-identical to the scorer as it was before v3 was added."""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import random
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))
PANEL = REPO_ROOT / "docs/validation/v2/llm_panel"
BANK = PANEL / "bank_v5"


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module  # dataclasses with postponed annotations look their module up here
    spec.loader.exec_module(module)
    return module


s187 = _load("s187", "scripts/v2/s187_build_requal_bank_v5.py")
s179 = _load("s179", "scripts/v2/s179_score_judges.py")


def _read(bank: Path):
    key = json.loads((bank / "key_RESTRICTED.json").read_text())
    p1 = {json.loads(x)["item_id"]: json.loads(x) for x in (bank / "pass1_packets.jsonl").read_text().splitlines()}
    p2 = {json.loads(x)["item_id"]: json.loads(x) for x in (bank / "pass2_packets.jsonl").read_text().splitlines()}
    return key, p1, p2


key, p1, p2 = _read(BANK)


def _texts(item_id: str) -> list[str]:
    packet = p1[item_id]
    return packet["variants"] if packet["kind"] == "legacy" else [packet["problem"]]


def test_build_is_deterministic_and_matches_the_committed_bank(tmp_path):
    manifest = s187.build(tmp_path / "v5")
    for name in ("pass1_packets.jsonl", "pass2_packets.jsonl", "key_RESTRICTED.json", "manifest.json"):
        assert (tmp_path / "v5" / name).read_bytes() == (BANK / name).read_bytes(), name
    assert manifest["seed"] == 5151
    assert s187.main(["--out", str(tmp_path / "v5")]) == 2  # refuses to overwrite


def test_composition():
    assert len(key) == 32 and set(p1) == set(p2) == set(key)
    assert sum(k["expected_verdict"] == "invalid" for k in key.values()) == 22
    assert all(k["split"] == "requal" for k in key.values())
    counts = {t: sum(k["defect_type"] == t for k in key.values()) for t in {k["defect_type"] for k in key.values()}}
    assert counts == {"contradictory_distractor_statement": 3, "invalid_numerical_precision": 3, "hidden_coupling": 1,
                      "relevant_variable_removed_from_equation": 1, "inconsistent_units": 1,
                      "invalid_parameter_domain": 1, "valid_equivalent_rewrite": 6, "insufficient_boundary_condition": 3,
                      "missing_assumption": 3, "rendering_not_minimal": 3, "failed_transformation_identity": 3,
                      "valid": 4}
    false_claims = [k for k in key.values() if k["source"] == "role_m0_plant_v5"]
    assert len(false_claims) == 6 and {k["defect_type"] for k in false_claims} == set(s187.FALSE_CLAIM_TYPES)


def test_packets_leak_nothing():
    for pk in list(p1.values()) + list(p2.values()):
        assert not any(f in pk for f in s187.s178.LEAK_FIELDS), pk["item_id"]
        assert all("label" not in c for c in pk.get("authors_claims", []))
        assert pk["kind"] in ("legacy", "role")
    for item_id, pk in p1.items():
        assert "authors_claims" not in pk and "certified_answer_display" not in pk  # pass 1 is blind


def test_no_overlap_with_earlier_banks():
    v3, v4 = (json.loads((PANEL / f"bank_v{n}/key_RESTRICTED.json").read_text()) for n in (3, 4))
    used_numbers = {int(i.split("-")[1]) for i in list(v3) + list(v4) if i[:2] in ("F-", "R-")}
    assert not {int(i.split("-")[1]) for i in key} & used_numbers
    families = [k["structure_id"] for k in key.values() if k["source"].startswith("fresh_v1")]
    assert len(families) == len(set(families)) == 20
    excluded = s187.s186.excluded_families() | {k["structure_id"] for k in v4.values() if k["source"] == "fresh_v1_inject"}
    assert not set(families) & excluded
    earlier_pairs = {(k["structure_id"], k["defect_type"]) for k in list(v3.values()) + list(v4.values())
                     if k["source"].startswith("role_m0")}
    plants = {(k["structure_id"], k["defect_type"]) for k in key.values() if k["source"] == "role_m0_plant_v5"}
    assert len(plants) == 6 and not plants & earlier_pairs
    v4_valid = {k["structure_id"] for k in v4.values() if k["source"].startswith("role_m0") and k["defect_type"] == "valid"}
    role_valid = {k["structure_id"] for k in key.values() if k["source"] == "role_m0_valid_v5"}
    assert len(role_valid) == 4 and not role_valid & v4_valid
    deletions = [d for d in s187.DELETIONS if any(k["structure_id"] == d.target and k["source"].endswith("deleted")
                                                  for k in key.values())]
    assert not {(d.target, d.old) for d in deletions} & s187.V4_DELETIONS
    m0 = [k["structure_id"] for k in key.values() if k["source"].startswith("role_m0")]
    assert len(m0) == len(set(m0)) == 12  # one item per M0 structure


def test_every_deletion_changes_the_answer_beyond_five_percent_and_happened():
    deleted = {i: k for i, k in key.items() if k["source"].endswith("condition_deleted")}
    assert len(deleted) == 6
    by_target = {d.target: d for d in s187.DELETIONS}
    for item_id, k in deleted.items():
        alt = k["alternative"]
        assert abs(alt["answer"] - alt["certified_answer"]) / abs(alt["certified_answer"]) > 0.05, item_id
        assert alt["case"] and alt["unit"]
        d = by_target[k["structure_id"]]
        assert d.rule1_waived is None and d.defect_type == k["defect_type"]
        assert all(d.old not in t for t in _texts(item_id))
        assert all(d.new in t for t in _texts(item_id))
        assert k["accepted_terms"] == ["insufficient_boundary_condition", "missing_assumption"] or \
            k["accepted_terms"] == ["missing_assumption", "insufficient_boundary_condition"]
    record = json.loads((BANK / "manifest.json").read_text())["safeguard_A_deletions"]
    assert all(r["relative_shift"] > 0.05 for r in record if r["used"])
    dropped = {r["target"] for r in record if not r["used"] and "Safeguard A" in r["reason"]}
    assert {"S72", "CM_B_UM_007", "CM_B_UM_008"} <= dropped  # the R-580 kind of error is caught


def test_safeguard_a_rejects_a_deletion_that_does_not_decide_the_answer():
    # bank v4's R-580 kind: a deleted condition under which the answer is unchanged
    d = next(d for d in s187.DELETIONS if d.target == "CM_B_UM_007")
    assert abs(d.alternative_answer() - d.certified()) / d.certified() < 0.05


def test_every_valid_control_passes_the_rule1_screen():
    valid = {i: k for i, k in key.items() if k["expected_verdict"] == "valid"}
    assert len(valid) == 10
    for item_id, k in valid.items():
        table = s187.FAMILY_CONDITIONS if k["source"] == "fresh_v1_inject" else s187.M0_CONDITIONS
        result = s187.screen(_texts(item_id), table[k["structure_id"]])
        assert result["passed"] and k["screen"]["passed"], (item_id, result)


def test_the_screen_catches_the_f909_kind_of_error():
    families = s187.s145.load_families()
    pendulum = s187._variants(families["CM_B_UM_033"])
    assert not s187.screen(pendulum, s187.FAMILY_CONDITIONS["CM_B_UM_033"])["passed"]
    assert not s187.screen(["anything"], None)["passed"]  # no entry: not reviewed, fails
    screened = json.loads((BANK / "manifest.json").read_text())["safeguard_B_screen"]
    assert not screened["v1_families"]["CM_B_UM_055"]["passed"]
    used = {k["structure_id"] for k in key.values()}
    assert all(screened["v1_families"].get(f, screened["m0_structures"].get(f))["passed"] for f in used)


def test_precision_items_accept_failed_transformation_identity_with_a_recorded_basis():
    for k in key.values():
        if k["defect_type"] == "invalid_numerical_precision":
            assert k["accepted_terms"] == ["invalid_numerical_precision", "failed_transformation_identity"]
            assert "before any judge has seen bank v5" in k["accepted_terms_basis"]
        elif k["source"] == "fresh_v1_inject":
            assert k["accepted_terms"] == s187.s186.LEGACY_ACCEPTED.get(k["defect_type"], [])
        else:
            assert k["accepted_terms"] == s187.s178.ACCEPTED_TERMS.get(k["defect_type"], [])
    family = {"correct_answer": "24.0 W"}
    assert "failed_transformation_identity" in s187.precision_terms(family, "20 W")[0]
    assert "failed_transformation_identity" not in s187.precision_terms(family, "24.04 W")[0]


# ---------------------------------------------------------------------------------------------------------------------
# s179 scoring
# ---------------------------------------------------------------------------------------------------------------------

TERMS = ("hidden_coupling", "missing_assumption", "relevant_variable_removed_from_equation",
         "failed_transformation_identity", "inconsistent_units", "invalid_parameter_domain",
         "insufficient_boundary_condition", "invalid_numerical_precision", "contradictory_distractor_statement",
         "rendering_not_minimal", "other", "not_a_term")


def synthetic_review_files(key, packets2, seed, accuracy=0.0):
    """A deterministic, mixed set of review files: right and wrong verdicts and terms, high and low severities, stratum
    assignments in several shapes, missing passes, unreadable JSON and records that fail the review contract. With
    probability `accuracy` a review is the correct one."""

    rng = random.Random(seed)
    files = {}
    for item_id in sorted(key):
        k = key[item_id]
        claims = packets2.get(item_id, {}).get("authors_claims")
        for n in (1, 2):
            r = {"reviewer_id": "synthetic", "item_id": item_id, "pass_number": n, "started_at": "t",
                 "completed_at": "t", "minutes_spent": 1, "blinding_attestation": True, "clarity": "clear",
                 "difficulty": 3, "naturalness": "natural", "confidence": 4, "counterexamples": [], "notes": ""}
            if rng.random() < accuracy:  # the correct review
                flags = [] if k["expected_verdict"] == "valid" else [(k.get("accepted_terms") or [k["defect_type"]])[0]]
                r.update(validity=k["expected_verdict"], uncertain_fields=[], defect_flags=flags,
                         defect_severity={f: "high" for f in flags})
                if n == 1 and claims is not None:
                    r["stratum_assignments"] = {c["sentence_id"]: {"stratum": c["stratum"]} for c in claims}
                if n == 2:
                    r.update(equation_consistent=True, units_consistent=True, answer_correct=True,
                             precision_adequate=True, admission_category="CERTIFIED_AND_VALIDATED")
                files[f"{item_id}_pass{n}.json"] = json.dumps(r, sort_keys=True)
                continue
            roll = rng.random()
            if roll < 0.06:
                continue  # missing review
            if roll < 0.09:
                files[f"{item_id}_pass{n}.json"] = "{not json"
                continue
            validity = rng.choice(("valid", "invalid", "invalid", "uncertain"))
            flags = rng.sample(TERMS, rng.randint(0, 2))
            if k["expected_verdict"] == "invalid" and rng.random() < 0.5:
                flags = [rng.choice(k.get("accepted_terms") or [k["defect_type"]])] + flags
            if validity == "invalid" and not flags:
                flags = ["other"]
            r.update(validity=validity, uncertain_fields=["answer"] if validity == "uncertain" else [],
                     defect_flags=flags,
                     defect_severity={f: rng.choice(("high", "medium", "low", "HIGH")) for f in flags})
            if rng.random() < 0.05:
                r["defect_flags"] = {"x": 1}  # wrong shape
            if n == 1 and claims is not None:
                shape = rng.choice(("dict", "str", "missing", "wrong"))
                r["stratum_assignments"] = {
                    c["sentence_id"]: ({"stratum": c["stratum"]} if shape == "dict" else
                                       c["stratum"].lower() if shape == "str" else {"stratum": "D"})
                    for c in claims if shape != "missing" or rng.random() < 0.5}
            if n == 2:
                r.update(equation_consistent=True, units_consistent=True, answer_correct=True, precision_adequate=True,
                         admission_category=rng.choice(("CERTIFIED_AND_VALIDATED", "SOLVER_INVALID", "BOGUS")))
            if rng.random() < 0.03:
                r["item_id"] = "mismatch"
            files[f"{item_id}_pass{n}.json"] = json.dumps(r, sort_keys=True)
    return files


# sha256 of the report file written by `s179 --split <split>` (no --protocol) on each synthetic set, computed with the
# scorer as committed in d5d1c36, before `--protocol` existed. They also depend on the frozen banks v3/v4 and on the
# wording of physmon.governance.review's validation messages (part of `review_errors`).
V2_REPORT_SHA256 = {
    ("bank_v3", "qualification", 1, 0.0): "5465b639a18b3798b3b042310af78516aa3b18f8d8044f07aa80acc520f5c327",
    ("bank_v3", "qualification", 4, 0.97): "e272c7406367481eef025b75e61a9eb2d6e8ba5038070df428647dcf149c627c",
    ("bank_v3", "heldout", 2, 0.0): "35a30c9eaa0d5e36b9bce8f304ba6cfcd931d9accd199275664f03dda12bf1b3",
    ("bank_v3", "heldout", 5, 0.9): "52cbf7e77a565f1676497a02256e1f62fe5971a4397342ad328ebcab59930331",
    ("bank_v4", "requal", 3, 0.0): "24103f8fe3666fed9ea8a70db6c9da83880f905fa430c97458010f1e243a00c6",
    ("bank_v4", "requal", 6, 0.95): "d91af5a3e96894e4af29e6aa94d200c3543e1e5c8dcc81a8cda60818e4d22db2",
    ("bank_v4", "requal", 7, 0.9): "bd91d4bfc9b119d47805a043804489c17d7d79337c9c513b25b44e2747c99fae",
}


def _run_s179(tmp_path: Path, bank: Path, split: str, files: dict, *extra: str) -> bytes:
    reviews, out = tmp_path / "reviews", tmp_path / "report.json"
    reviews.mkdir(parents=True)
    for name, text in files.items():
        (reviews / name).write_text(text)
    with contextlib.redirect_stdout(io.StringIO()):
        assert s179.main(["--reviews", str(reviews), "--bank", str(bank), "--split", split, "--out", str(out),
                          *extra]) == 0
    return out.read_bytes()


@pytest.mark.parametrize("case", sorted(V2_REPORT_SHA256))
def test_v2_scoring_is_byte_identical(case, tmp_path):
    bank_name, split, seed, accuracy = case
    bank = PANEL / bank_name
    k, _, packets2 = _read(bank)
    files = synthetic_review_files(k, packets2, seed, accuracy)
    default = _run_s179(tmp_path / "a", bank, split, files)
    assert hashlib.sha256(default).hexdigest() == V2_REPORT_SHA256[case]
    assert _run_s179(tmp_path / "b", bank, split, files, "--protocol", "v2") == default


def _perfect(k, packets2):
    return {(i, r["pass_number"]): r for i, r in
            ((name.rsplit("_pass", 1)[0], json.loads(text))
             for name, text in synthetic_review_files(k, packets2, 0, accuracy=1.0).items())}


def test_v3_perfect_judge_qualifies_and_each_criterion_can_fail():
    perfect = _perfect(key, p2)
    res = s179.score(perfect, key, p2, "requal", "v3")
    assert res["verdict"] == "QUALIFIED" and res["protocol"] == "v3"
    assert set(res["checks"]) == {"R1_detected_for_declared_reason", "R2_valid_accepted", "R3_retargeted_types_detected",
                                  "R4_no_type_with_3_or_more_items_missed", "R5_false_claim_role_plants_detected"}
    assert res["checks"]["R5_false_claim_role_plants_detected"]["n"] == 6
    assert res["checks"]["R5_false_claim_role_plants_detected"]["min_detected"] == 5
    assert res["blind_stratum_agreement"]["n"] > 0  # v3 counts the v5 valid role items

    def with_misses(item_ids, verdict="valid"):
        out = dict(perfect)
        for i in item_ids:
            out[(i, 2)] = {**perfect[(i, 2)], "validity": verdict, "defect_flags": [] if verdict == "valid" else
                           ["other"], "defect_severity": {}}
        return out

    plants = sorted(i for i, k in key.items() if k["source"] == "role_m0_plant_v5")
    one = s179.score(with_misses(plants[:1]), key, p2, "requal", "v3")
    assert one["checks"]["R5_false_claim_role_plants_detected"]["pass"]
    two = s179.score(with_misses(plants[:2]), key, p2, "requal", "v3")
    assert not two["checks"]["R5_false_claim_role_plants_detected"]["pass"] and two["verdict"] == "NOT_QUALIFIED"
    ma = [i for i, k in key.items() if k["defect_type"] == "missing_assumption"]
    r3 = s179.score(with_misses(ma[:2]), key, p2, "requal", "v3")
    assert not r3["checks"]["R3_retargeted_types_detected"]["pass"]
    fti = [i for i, k in key.items() if k["defect_type"] == "failed_transformation_identity"]
    r4 = s179.score(with_misses(fti), key, p2, "requal", "v3")
    assert r4["checks"]["R4_no_type_with_3_or_more_items_missed"]["missed_types"] == ["failed_transformation_identity"]
    valid = [i for i, k in key.items() if k["expected_verdict"] == "valid"]
    r2 = s179.score(with_misses(valid[:2], "invalid"), key, p2, "requal", "v3")
    assert not r2["checks"]["R2_valid_accepted"]["pass"]  # 8 of 10 < 0.85
    defective = [i for i, k in key.items() if k["expected_verdict"] == "invalid"
                 and k["defect_type"] not in s179.RETARGETED + s179.FALSE_CLAIM_TYPES]
    r1 = s179.score(with_misses(defective[:4]), key, p2, "requal", "v3")
    assert not r1["checks"]["R1_detected_for_declared_reason"]["pass"]  # 18 of 22 < 0.85


def test_v3_precision_items_accept_the_transformation_term():
    perfect = _perfect(key, p2)
    for i, k in key.items():
        if k["defect_type"] == "invalid_numerical_precision":
            perfect[(i, 2)] = {**perfect[(i, 2)], "defect_flags": ["failed_transformation_identity"],
                               "defect_severity": {"failed_transformation_identity": "high"}}
    res = s179.score(perfect, key, p2, "requal", "v3")
    assert res["per_type"]["invalid_numerical_precision"]["detected"] == 3 and res["verdict"] == "QUALIFIED"


def test_v3_is_defined_only_for_the_requal_split(tmp_path):
    with pytest.raises(ValueError):
        s179.score({}, key, p2, "qualification", "v3")
    with pytest.raises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
        s179.main(["--reviews", str(tmp_path), "--split", "heldout", "--protocol", "v3", "--out", str(tmp_path / "o")])


# ---------------------------------------------------------------------------------------------------------------------
# rolevalue_bank.base_item(instance=...): earlier banks unchanged; v5 valid role items unseen
# ---------------------------------------------------------------------------------------------------------------------


def test_bank_v4_rebuilds_identically_and_bank_v3_role_packets_are_unchanged(tmp_path):
    s187.s186.build(tmp_path / "v4")
    for name in ("pass1_packets.jsonl", "pass2_packets.jsonl", "key_RESTRICTED.json", "manifest.json"):
        assert (tmp_path / "v4" / name).read_bytes() == (PANEL / "bank_v4" / name).read_bytes(), name
    # bank v3's pass-2 K claims were reworded for bank v4 (before the instance parameter existed), so only its key and
    # pass-1 packets still rebuild byte for byte
    with contextlib.redirect_stdout(io.StringIO()):
        s187.s178.build(tmp_path / "v3")
    for name in ("pass1_packets.jsonl", "key_RESTRICTED.json"):
        assert (tmp_path / "v3" / name).read_bytes() == (PANEL / "bank_v3" / name).read_bytes(), name


def test_base_item_default_is_instance_zero():
    from physmon.validation import rolevalue_bank as rb

    for sid in ("S01", "S07", "S72"):
        assert rb.base_item(sid, "x") == rb.base_item(sid, "x", 0)
        assert rb.base_item(sid, "x", 1)["problem"] != rb.base_item(sid, "x")["problem"]


def test_valid_items_and_plants_use_an_unseen_instance_with_hand_checked_answers():
    import math

    seen = s187.earlier_pass1_texts()
    hand = {  # base answers of instance 1, recomputed by hand
        "S02": math.sqrt(2 * 9.8 * (math.sin(math.radians(40)) - 0.1 * math.cos(math.radians(40))) * 5),  # m/s
        "S07": 9 * (1 - math.exp(-150e-3 / (8e3 * 15e-6))),  # V
        "S13": 2 * math.pi * math.sqrt(1.2 / 9.8),  # s
        "S15": 9**2 * (1 / 5 + 1 / 15),  # W
        "S20": 10 * 35 / (35 - 10),  # cm
        "S26": math.degrees(math.asin(1.2 * math.sin(math.radians(35)) / 1.7)),  # deg
        "S27": 100 + 850 * 9.8 * 20 / 1000,  # kPa
        "S55": math.sqrt(3 * 8.314 * 400 / 0.032),  # m/s
        "S72": 1240 / math.sqrt(2 * 511e3 * 54) * 1e3,  # pm (hc / pc, non-relativistic)
        "S92": (1100 - 450) * 9.8 * 0.15**3,  # N
    }
    unseen = {i: k for i, k in key.items() if k["source"] in ("role_m0_valid_v5", "role_m0_plant_v5")}
    assert len(unseen) == 10
    for item_id, k in unseen.items():
        assert k["instance"] != s187.V3_V4_INSTANCE
        assert p1[item_id]["problem"] not in seen
        expected = hand[k["structure_id"]]
        assert abs(p2[item_id]["base_answer"] - expected) / expected < 1e-5, item_id
    assert all(k["instance"] == 0 for k in key.values() if k["source"] == "role_m0_condition_deleted")


def test_false_claim_plants_are_clean_on_their_instance():
    for item_id, k in key.items():
        claims = {c["sentence_id"]: c for c in p2[item_id].get("authors_claims", [])}
        if k["defect_type"] == "failed_transformation_identity":
            from physmon.validation import rolevalue_bank as rb

            true = next(c for c in rb.base_item(k["structure_id"], "x", k["instance"])["claims"]
                        if c["stratum"] == "R")["certified_answers"]
            for c in claims.values():
                if c["stratum"] == "R":
                    for v, w in c["certified_answers"].items():
                        assert w > 0 and abs(w - true[v]) / true[v] > 0.05, (item_id, v)
        if k["defect_type"] == "rendering_not_minimal":
            texts = {s["sentence_id"]: s["text"] for s in p1[item_id]["sentences"]}
            pairs = [(sid, c["minimal_pair_with"]) for sid, c in claims.items() if "minimal_pair_with" in c]
            assert any(texts[a] != texts[b] and
                       s187.re.findall(r"\d+(?:\.\d+)?", texts[a]) != s187.re.findall(r"\d+(?:\.\d+)?", texts[b])
                       for a, b in pairs), item_id
