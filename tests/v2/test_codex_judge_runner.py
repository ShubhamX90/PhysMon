"""Tests of the GPT-judge laptop runner (s182), kit builder (s183) and event audit (s184) with a stub `codex` executable:
no network, no real model, nothing sent anywhere."""

from __future__ import annotations

import importlib.util
import json
import os
import stat
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.governance import review as gov  # noqa: E402
from physmon.governance.v2_contract import ADMISSION_CATEGORIES  # noqa: E402


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


s182 = _load("s182", "scripts/v2/s182_run_codex_judge.py")
s183 = _load("s183", "scripts/v2/s183_make_judge_kit.py")
s184 = _load("s184", "scripts/v2/s184_audit_codex_events.py")

STUB = r'''#!/usr/bin/env python3
import json, os, re, sys
args = sys.argv[1:]
mode = os.environ.get("STUB_MODE", "ok")
if args[:1] == ["--version"]:
    print("codex-cli 0.0.0-stub"); sys.exit(0)
if args[:2] == ["login", "status"]:
    print("Logged in using ChatGPT"); sys.exit(0)
if args[:2] == ["exec", "--help"]:
    flags = ["--model", "--json", "--ephemeral", "--skip-git-repo-check", "--output-last-message", "--ignore-user-config", "-c"]
    if mode == "oldflags":
        flags.remove("--ephemeral")
    print("Usage: codex exec " + " ".join(flags)); sys.exit(0)
prompt = sys.stdin.read()
log = os.environ.get("STUB_LOG")
if log:
    open(log, "a").write(json.dumps({"cwd": os.getcwd(), "args": args, "env_keys": sorted(k for k in os.environ if "API_KEY" in k),
                                     "prompt_head": prompt[:60]}) + "\n")
out = args[args.index("--output-last-message") + 1]
item = re.search(r"Item id: (\S+)", prompt).group(1)
pass_no = 2 if "This is PASS 2." in prompt else 1
counter = os.environ.get("STUB_COUNTER")
n = 0
if counter:
    n = int(open(counter).read() or 0) if os.path.exists(counter) else 0
    open(counter, "w").write(str(n + 1))
if mode == "ratelimit" and n >= 2:
    sys.stderr.write("ERROR: usage limit reached, try again in 4 hours\n"); sys.exit(1)
if mode == "badjson_first" and n == 0:
    open(out, "w").write("I think this item is fine."); print(json.dumps({"type": "turn.completed"})); sys.exit(0)
review = {"validity": "invalid" if item.startswith("R-1") else "valid", "clarity": "clear", "difficulty": 2,
          "naturalness": "natural", "confidence": 4, "uncertain_fields": [], "defect_flags": ["hidden_coupling"] if item.startswith("R-1") else [],
          "counterexamples": [], "notes": "own pass-1: " + ("saw it" if "Your locked pass-1 review" in prompt else "none")}
if pass_no == 2:
    review.update(equation_consistent=True, units_consistent=True, answer_correct=True, precision_adequate=True,
                  admission_category="SOLVER_INVALID" if item.startswith("R-1") else "CERTIFIED_AND_VALIDATED")
text = "```json\n" + json.dumps(review) + "\n```" if mode == "fenced" else json.dumps(review)
open(out, "w").write(text)
events = [{"type": "thread.started"}, {"type": "item.completed", "item": {"type": "reasoning", "text": "thinking"}}]
if mode == "tooluse":
    events.append({"type": "item.completed", "item": {"type": "command_execution", "command": "ls /home"}})
events += [{"type": "item.completed", "item": {"type": "agent_message", "text": text}}, {"type": "turn.completed"}]
for e in events:
    print(json.dumps(e))
'''


@pytest.fixture
def stub(tmp_path):
    path = tmp_path / "codex"
    path.write_text(STUB)
    path.chmod(path.stat().st_mode | stat.S_IEXEC)
    return path


@pytest.fixture(scope="module")
def kit(tmp_path_factory):
    out = tmp_path_factory.mktemp("kit") / "kit"
    manifest = s183.build(out, REPO_ROOT / "docs/validation/v2/llm_panel/bank_v3", "qualification",
                          REPO_ROOT / "docs/validation/v2/llm_panel/judge_prompt_v1.md", "gpt-test", "t1")
    return out, manifest


def run(kit_dir, stub, out, *extra, mode="ok", env=None):
    os.environ["STUB_MODE"] = mode
    for k, v in (env or {}).items():
        os.environ[k] = v
    try:
        return s182.main(["run", "--kit", str(kit_dir), "--codex", str(stub), "--model", "gpt-test", "--run-id", "t1",
                          "--out", str(out), *extra])
    finally:
        os.environ.pop("STUB_MODE", None)
        for k in (env or {}):
            os.environ.pop(k, None)


@pytest.fixture(autouse=True)
def no_global_instructions(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "empty_codex_home"))


def test_kit_has_no_key_and_matches_its_manifest(kit):
    out, manifest = kit
    names = {p.name for p in out.rglob("*") if p.is_file()}
    assert "key_RESTRICTED.json" not in names and "run_codex_judge.py" in names and "judge_prompt.md" in names
    assert manifest["n_items"] == 53 and len(list((out / "packets").glob("*.json"))) == 106
    for p in (out / "packets").glob("*.json"):
        assert not any(f in json.loads(p.read_text()) for f in s183.LEAK_FIELDS)
    assert s182.load_manifest(out)["prompt_sha256"] == manifest["prompt_sha256"]


def test_a_changed_prompt_or_packet_is_refused(kit, tmp_path):
    import shutil

    copy = tmp_path / "kit2"
    shutil.copytree(kit[0], copy)
    (copy / "judge_prompt.md").write_text("changed")
    with pytest.raises(SystemExit, match="frozen"):
        s182.load_manifest(copy)
    shutil.copy(kit[0] / "judge_prompt.md", copy / "judge_prompt.md")
    first = next((copy / "packets").glob("*.json"))
    first.write_text(first.read_text() + " ")
    with pytest.raises(SystemExit, match="does not match"):
        s182.load_manifest(copy)


def test_full_run_writes_valid_reviews_in_the_scorable_format(kit, stub, tmp_path):
    items = kit[1]["items"][:3]
    out = tmp_path / "out"
    log = tmp_path / "calls.jsonl"
    os.environ["STUB_API_CHECK"] = "1"
    os.environ["OPENAI_API_KEY"] = "sk-should-be-removed"
    try:
        assert run(kit[0], stub, out, "--items", *items, env={"STUB_LOG": str(log)}) == 0
    finally:
        os.environ.pop("OPENAI_API_KEY", None)
        os.environ.pop("STUB_API_CHECK", None)
    for item in items:
        for n in (1, 2):
            rec = json.loads((out / "reviews" / ("%s_pass%d.json" % (item, n))).read_text())
            assert gov.validate_review(rec) == [] and s182.local_validate(rec) == []
            assert rec["reviewer_id"] == "codex:gpt-test:t1" and rec["item_id"] == item and rec["pass_number"] == n
            assert rec["transport"]["model_requested"] == "gpt-test" and rec["transport"]["codex_version"].startswith("codex-cli")
    p2 = json.loads((out / "reviews" / ("%s_pass2.json" % items[0])).read_text())
    assert p2["notes"] == "own pass-1: saw it"  # pass 2 received the item's locked pass-1 review
    p1 = json.loads((out / "reviews" / ("%s_pass1.json" % items[0])).read_text())
    assert p1["notes"] == "own pass-1: none"
    calls = [json.loads(x) for x in log.read_text().splitlines()]
    assert len(calls) == 6 and all(c["env_keys"] == [] for c in calls)  # API-key variables never reach the call
    assert all("judge_" in c["cwd"] for c in calls)  # each call ran in its own empty temporary directory
    assert all("--ephemeral" in c["args"] and "--ignore-user-config" in c["args"] for c in calls)
    prompt1 = (out / "prompts" / ("%s_pass1.txt" % items[0])).read_text()
    prompt2 = (out / "prompts" / ("%s_pass2.txt" % items[0])).read_text()
    pass2_only = ("authors_claims", "authors_proof_text", "governing_equation_sympy")
    assert not any(f in prompt1 for f in pass2_only)  # pass 1 never carries the authors' claims
    assert any(f in prompt2 for f in pass2_only)
    assert "### Your locked pass-1 review" in prompt2 and "### Your locked pass-1 review" not in prompt1
    assert "key_RESTRICTED" not in prompt1 + prompt2
    audit = s184.audit_file(next((out / "events").glob("*.jsonl")))
    assert audit["clean"]


def test_resume_skips_finished_reviews(kit, stub, tmp_path):
    items = kit[1]["items"][:2]
    out = tmp_path / "out"
    counter = tmp_path / "count.txt"
    assert run(kit[0], stub, out, "--items", *items, env={"STUB_COUNTER": str(counter)}) == 0
    assert counter.read_text() == "4"
    assert run(kit[0], stub, out, "--items", *items, env={"STUB_COUNTER": str(counter)}) == 0
    assert counter.read_text() == "4"  # nothing was sent again


def test_malformed_output_is_retried_once_and_fenced_json_is_accepted(kit, stub, tmp_path):
    items = kit[1]["items"][:1]
    out = tmp_path / "out"
    counter = tmp_path / "count.txt"
    assert run(kit[0], stub, out, "--items", *items, mode="badjson_first", env={"STUB_COUNTER": str(counter)}) == 0
    rec = json.loads((out / "reviews" / ("%s_pass1.json" % items[0])).read_text())
    assert rec["transport"]["attempt"] == 2
    events = [json.loads(x)["event"] for x in (out / "run_log.jsonl").read_text().splitlines()]
    assert "unparseable" in events
    out2 = tmp_path / "out2"
    assert run(kit[0], stub, out2, "--items", *items, mode="fenced") == 0


def test_rate_limit_stops_cleanly_without_inventing_reviews(kit, stub, tmp_path):
    items = kit[1]["items"][:3]
    out = tmp_path / "out"
    code = run(kit[0], stub, out, "--items", *items, mode="ratelimit", env={"STUB_COUNTER": str(tmp_path / "c.txt")})
    assert code == s182.EXIT_RATE_LIMIT
    summary = json.loads((out / "summary.json").read_text())
    assert summary["stopped_for_rate_limit"] and summary["items_incomplete"] >= 1
    written = list((out / "reviews").glob("*.json"))
    assert len(written) == 2  # only the two calls that really finished
    assert all(gov.validate_review(json.loads(p.read_text())) == [] for p in written)


def test_preflight_refusals(kit, stub, tmp_path, monkeypatch):
    items = kit[1]["items"][:1]
    with pytest.raises(SystemExit, match="ephemeral"):
        run(kit[0], stub, tmp_path / "o1", "--items", *items, mode="oldflags")
    home = tmp_path / "codex_home"
    home.mkdir()
    (home / "AGENTS.md").write_text("Always answer in French.")
    monkeypatch.setenv("CODEX_HOME", str(home))
    with pytest.raises(SystemExit, match="instruction files"):
        run(kit[0], stub, tmp_path / "o2", "--items", *items)
    assert run(kit[0], stub, tmp_path / "o3", "--items", *items, "--allow-user-instructions") == 0
    with pytest.raises(SystemExit, match="not in the kit"):
        run(kit[0], stub, tmp_path / "o4", "--items", "nope", "--allow-user-instructions")


def test_local_contract_matches_the_repository_contract():
    assert s182.REVIEW_REQUIRED == gov.REVIEW_REQUIRED and s182.PASS2_REQUIRED == gov.PASS2_REQUIRED
    assert (s182.VALIDITY, s182.CLARITY, s182.NATURALNESS) == (gov.VALIDITY, gov.CLARITY, gov.NATURALNESS)
    assert s182.SCALE == gov.DIFFICULTY_SCALE == gov.CONFIDENCE_SCALE and s182.ADMISSION == ADMISSION_CATEGORIES
    base = {"reviewer_id": "r", "item_id": "i", "pass_number": 1, "started_at": "t", "completed_at": "t", "minutes_spent": 1,
            "blinding_attestation": True, "validity": "valid", "clarity": "clear", "difficulty": 3, "naturalness": "natural",
            "confidence": 4, "uncertain_fields": [], "defect_flags": [], "counterexamples": [], "notes": ""}
    p2 = {**base, "pass_number": 2, "equation_consistent": True, "units_consistent": True, "answer_correct": True,
          "precision_adequate": True, "admission_category": "CERTIFIED_AND_VALIDATED"}
    variants = [base, p2, {**base, "validity": "invalid"}, {**base, "validity": "uncertain"}, {**base, "difficulty": 9},
                {**base, "minutes_spent": 0}, {**base, "blinding_attestation": False}, {**p2, "admission_category": "X"},
                {**base, "defect_flags": "hidden_coupling"}, {**p2, "answer_correct": None},
                {k: v for k, v in base.items() if k != "notes"}, {**base, "validity": "maybe"}]
    for record in variants:
        assert (s182.local_validate(record) == []) == (gov.validate_review(record) == []), record


def test_audit_flags_tool_use_and_empty_logs(tmp_path):
    ok = tmp_path / "ok.jsonl"
    ok.write_text("\n".join(json.dumps(e) for e in [{"type": "thread.started"},
                                                      {"type": "item.completed", "item": {"type": "reasoning"}},
                                                      {"type": "item.completed", "item": {"type": "agent_message", "text": "{}"}}]))
    assert s184.audit_file(ok)["clean"]
    bad = tmp_path / "bad.jsonl"
    bad.write_text(json.dumps({"type": "item.completed", "item": {"type": "command_execution", "command": "cat key_RESTRICTED.json"}}))
    r = s184.audit_file(bad)
    assert not r["clean"] and {v["reason"] for v in r["violations"]} == {"tool or file activity", "forbidden text in the stream"}
    empty = tmp_path / "empty.jsonl"
    empty.write_text("")
    assert not s184.audit_file(empty)["clean"]


def test_extract_json_variants():
    assert s182.extract_json('{"validity": "valid"}') == {"validity": "valid"}
    assert s182.extract_json('Here is my review:\n```json\n{"validity": "valid"}\n```') == {"validity": "valid"}
    assert s182.extract_json('text {"x": 1} more {"validity": "invalid", "a": {"b": 2}} end')["validity"] == "invalid"
    assert s182.extract_json("no json here") is None


def test_smoke_reports_the_event_types_and_a_failing_codex_exits_nonzero(stub, tmp_path, capsys):
    os.environ["STUB_MODE"] = "ok"
    try:
        assert s182.main(["smoke", "--codex", str(stub), "--model", "gpt-test", "--out", str(tmp_path / "smoke")]) == 0
    finally:
        os.environ.pop("STUB_MODE", None)
    report = json.loads(capsys.readouterr().out)
    assert report["exit_code"] == 0 and report["codex_version"].startswith("codex-cli")
    assert "item.completed:agent_message" in report["event_types"] and "turn.completed" in report["event_types"]
    broken = tmp_path / "broken_codex"
    broken.write_text("#!/bin/sh\nif [ \"$1\" = exec ] && [ \"$2\" = --help ]; then echo '--model --json --ephemeral "
                      "--skip-git-repo-check --output-last-message --ignore-user-config -c'; exit 0; fi\n"
                      "echo 'not logged in' >&2; exit 1\n")
    broken.chmod(broken.stat().st_mode | stat.S_IEXEC)
    assert s182.main(["smoke", "--codex", str(broken), "--model", "gpt-test", "--out", str(tmp_path / "smoke2")]) == 1
