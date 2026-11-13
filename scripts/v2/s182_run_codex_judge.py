#!/usr/bin/env python3
"""Stage 15 (G1, LLM review panel): run a GPT judge through OpenAI's Codex CLI signed in with a ChatGPT account.

Runs on the user's laptop, standard library only (Python 3.8+), from a judge kit built by `s183_make_judge_kit.py`
(frozen prompt + judge-facing packets; the answer key is never in the kit). Every call is a fresh, ephemeral `codex exec`
session in an empty temporary directory, so no call can see another item, another judge's review or the key.

Subcommands
  check   verify the Codex CLI flags this runner uses exist, show the login status, refuse global user instructions
  smoke   one trivial call: shows the Codex version, which event types appear, and that the login works
  run     review every item in the kit: pass 1 (packet 1 only), then pass 2 (packet 2 plus the item's own locked pass-1
          review); resumable (existing reviews are skipped); stops cleanly when the plan's usage limit is hit
  summary count reviews, retries and failures of a finished or interrupted run

Outputs under --out: reviews/<item>_pass{1,2}.json (the format `s179_score_judges.py` scores), prompts/ (the exact text sent),
events/ (Codex's --json event stream, audited by `s184_audit_codex_events.py`), stderr/, run_log.jsonl, summary.json.
The OPENAI_API_KEY and CODEX_API_KEY variables are removed from the environment of every call, so the ChatGPT login is
used and nothing is billed to an API account.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

RUNNER_VERSION = "1"
EXIT_RATE_LIMIT = 75

# Flags used, each with the spellings accepted in `codex exec --help` (names from OpenAI's Codex docs, 2026-11).
REQUIRED_FLAGS = (("--model",), ("--json",), ("--ephemeral",), ("--skip-git-repo-check",),
                  ("--output-last-message", "-o"))
OPTIONAL_FLAGS = {"ignore_user_config": "--ignore-user-config", "config_override": "-c"}
GLOBAL_INSTRUCTION_FILES = ("AGENTS.md", "AGENTS.override.md")
LIMIT_PATTERN = re.compile(r"rate.?limit|usage limit|quota|too many requests|\b429\b|try again (in|later)|limit reached",
                           re.IGNORECASE)

# Mirrors physmon.governance.review (a test in the repository asserts they are identical).
REVIEW_REQUIRED = ("reviewer_id", "item_id", "pass_number", "started_at", "completed_at", "minutes_spent",
                   "blinding_attestation", "validity", "clarity", "difficulty", "naturalness", "confidence",
                   "uncertain_fields", "defect_flags", "counterexamples", "notes")
PASS2_REQUIRED = ("equation_consistent", "units_consistent", "answer_correct", "precision_adequate", "admission_category")
VALIDITY = ("valid", "invalid", "uncertain")
CLARITY = ("clear", "ambiguous", "unclear")
NATURALNESS = ("natural", "slightly_artificial", "artificial")
SCALE = (1, 2, 3, 4, 5)
ADMISSION = ("CERTIFIED_AND_VALIDATED", "SOLVER_VALID_LANGUAGE_AMBIGUOUS", "SOLVER_INVALID", "ANSWER_AMBIGUOUS",
             "NATURALNESS_FLAG", "REVISED_REVALIDATED", "EXCLUDED", "UNREVIEWED")

TRANSPORT_NOTE = """---
## Transport instructions for this run (these replace the file-handling lines above)

You review one item in a single step. Everything you need is in this message. Do not read any files, run any commands,
use any tools or the web. Do not look for other information about the item.
Your final message must be exactly one JSON object, the review for this pass in the schema above, with nothing before or
after it and no code fences. Leave `reviewer_id`, `started_at`, `completed_at`, `minutes_spent` and `blinding_attestation`
to the harness (any values you give are replaced).
"""


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def local_validate(record: dict) -> list:
    """The review contract of physmon.governance.review.validate_review, reproduced so this file needs nothing else."""

    errors = []
    for name in REVIEW_REQUIRED:
        if name not in record or record[name] in (None, ""):
            if name in ("uncertain_fields", "defect_flags", "counterexamples", "notes") and name in record:
                continue
            errors.append("missing required field '%s'" % name)
    if errors:
        return errors
    if record["pass_number"] not in (1, 2):
        errors.append("pass_number must be 1 or 2")
    if record["blinding_attestation"] is not True:
        errors.append("blinding_attestation must be true")
    for name, allowed in (("validity", VALIDITY), ("clarity", CLARITY), ("naturalness", NATURALNESS),
                          ("difficulty", SCALE), ("confidence", SCALE)):
        if record[name] not in allowed:
            errors.append("%s=%r is not one of %s" % (name, record[name], list(allowed)))
    if not isinstance(record["minutes_spent"], (int, float)) or isinstance(record["minutes_spent"], bool) \
            or record["minutes_spent"] <= 0:
        errors.append("minutes_spent must be a positive number")
    for name in ("uncertain_fields", "defect_flags", "counterexamples"):
        if not isinstance(record[name], list):
            errors.append("%s must be a list" % name)
    if errors:
        return errors
    if record["validity"] == "uncertain" and not record["uncertain_fields"]:
        errors.append("validity 'uncertain' needs at least one entry in uncertain_fields")
    if record["validity"] == "invalid" and not record["defect_flags"]:
        errors.append("validity 'invalid' needs at least one entry in defect_flags")
    if record["pass_number"] == 2:
        for name in PASS2_REQUIRED:
            if name not in record or record[name] in (None, ""):
                errors.append("pass 2 needs '%s'" % name)
        if record.get("admission_category") not in ADMISSION:
            errors.append("admission_category must be one of %s" % list(ADMISSION))
    return errors


def extract_json(text: str):
    """The review object in a model message: the whole text, a fenced block, or the first object that has `validity`."""

    text = (text or "").strip()
    candidates = [text]
    candidates += re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    for cand in candidates:
        try:
            obj = json.loads(cand)
            if isinstance(obj, dict):
                return obj
        except ValueError:
            pass
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", text):
        try:
            obj, _ = decoder.raw_decode(text[match.start():])
        except ValueError:
            continue
        if isinstance(obj, dict) and "validity" in obj:
            return obj
    return None


def finalize_review(obj: dict, item: str, pass_no: int, reviewer_id: str, started: str, completed: str, elapsed_s: float,
                    transport: dict) -> dict:
    """Fill what only the harness knows; everything the judge decided stays as it wrote it."""

    review = dict(obj)
    review.update(reviewer_id=reviewer_id, item_id=item, pass_number=pass_no, started_at=started, completed_at=completed,
                  minutes_spent=round(max(elapsed_s, 1.0) / 60.0, 2), blinding_attestation=True)
    for name in ("uncertain_fields", "defect_flags", "counterexamples"):
        review.setdefault(name, [])
    review.setdefault("notes", "")
    review["transport"] = transport
    return review


def build_prompt(frozen: str, item: str, reviewer_id: str, pass_no: int, packet: dict, pass1_review: dict | None = None) -> str:
    parts = [frozen.rstrip("\n"), "", TRANSPORT_NOTE, "Reviewer id: %s" % reviewer_id, "Item id: %s" % item,
             "This is PASS %d." % pass_no, ""]
    if pass_no == 1:
        parts += ["Review pass 1 now, from this packet alone. Do not use anything else about the item.", "",
                  "### Pass-1 packet", json.dumps(packet, indent=2, ensure_ascii=False)]
    else:
        locked = {k: v for k, v in (pass1_review or {}).items() if k != "transport"}
        parts += ["Your locked pass-1 review follows, then the pass-2 packet. Review pass 2 now.", "",
                  "### Your locked pass-1 review", json.dumps(locked, indent=2, ensure_ascii=False), "",
                  "### Pass-2 packet", json.dumps(packet, indent=2, ensure_ascii=False)]
    return "\n".join(parts) + "\n"


def clean_env() -> dict:
    return {k: v for k, v in os.environ.items() if k not in ("OPENAI_API_KEY", "CODEX_API_KEY")}


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME") or (Path.home() / ".codex"))


def global_instructions() -> list:
    return [str(codex_home() / n) for n in GLOBAL_INSTRUCTION_FILES if (codex_home() / n).exists()]


def codex_help(codex: str) -> str:
    out = subprocess.run([codex, "exec", "--help"], capture_output=True, text=True, timeout=120, env=clean_env())
    return (out.stdout or "") + (out.stderr or "")


def flag_report(codex: str) -> dict:
    help_text = codex_help(codex)
    required = {"/".join(alts): any(a in help_text for a in alts) for alts in REQUIRED_FLAGS}
    optional = {name: flag in help_text for name, flag in OPTIONAL_FLAGS.items()}
    return {"required": required, "optional": optional, "ok": all(required.values())}


def codex_version(codex: str) -> str:
    try:
        out = subprocess.run([codex, "--version"], capture_output=True, text=True, timeout=60, env=clean_env())
        return (out.stdout or out.stderr).strip()
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def event_types(stdout: str) -> dict:
    counts = {}
    for line in (stdout or "").splitlines():
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        kind = str(ev.get("type"))
        item = ev.get("item")
        if isinstance(item, dict) and item.get("type"):
            kind += ":" + str(item["type"])
        counts[kind] = counts.get(kind, 0) + 1
    return counts


class Runner:
    def __init__(self, args: argparse.Namespace, kit: Path, out: Path):
        self.args, self.kit, self.out = args, kit, out
        self.lock = threading.Lock()
        self.stop = threading.Event()
        self.version = codex_version(args.codex)
        self.frozen = (kit / "judge_prompt.md").read_text(encoding="utf-8")
        self.reviewer_id = "codex:%s:%s" % (args.model, args.run_id)
        for sub in ("reviews", "prompts", "events", "stderr"):
            (out / sub).mkdir(parents=True, exist_ok=True)

    def log(self, event: dict) -> None:
        with self.lock:
            with (self.out / "run_log.jsonl").open("a", encoding="utf-8") as handle:
                handle.write(json.dumps({"at": now(), **event}, ensure_ascii=False) + "\n")

    def command(self, last_message: Path) -> list:
        cmd = [self.args.codex, "exec", "--model", self.args.model, "--ephemeral", "--skip-git-repo-check", "--json",
               "--output-last-message", str(last_message)]
        if not self.args.keep_user_config:
            cmd.append("--ignore-user-config")
        if self.args.reasoning_effort:
            cmd += ["-c", 'model_reasoning_effort="%s"' % self.args.reasoning_effort]
        return cmd + ["-"]

    def call(self, prompt: str, tag: str, attempt: int):
        """One fresh codex session in an empty directory. Returns (last_message, stdout, stderr, returncode, seconds)."""

        base = "%s_a%d" % (tag, attempt)
        with tempfile.TemporaryDirectory(prefix="judge_") as empty:
            last = Path(empty) / "last_message.txt"
            start = time.time()
            try:
                proc = subprocess.run(self.command(last), input=prompt, capture_output=True, text=True,
                                      cwd=empty, timeout=self.args.timeout, env=clean_env())
                stdout, stderr, rc = proc.stdout, proc.stderr, proc.returncode
            except subprocess.TimeoutExpired as exc:
                stdout = (exc.stdout.decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else exc.stdout) or ""
                stderr, rc = "timeout after %ss" % self.args.timeout, -9
            message = last.read_text(encoding="utf-8") if last.exists() else ""
        (self.out / "events" / (base + ".jsonl")).write_text(stdout or "", encoding="utf-8")
        (self.out / "stderr" / (base + ".txt")).write_text(stderr or "", encoding="utf-8")
        return message, stdout or "", stderr or "", rc, time.time() - start

    def review_once(self, item: str, pass_no: int, packet: dict, pass1: dict | None):
        """Up to two attempts (a fresh session each, identical prompt). Returns the review, or None with a reason."""

        tag = "%s_pass%d" % (item, pass_no)
        prompt = build_prompt(self.frozen, item, self.reviewer_id, pass_no, packet, pass1)
        (self.out / "prompts" / (tag + ".txt")).write_text(prompt, encoding="utf-8")
        reason = "no attempt"
        for attempt in (1, 2):
            if self.stop.is_set():
                return None, "stopped"
            started = now()
            message, stdout, stderr, rc, seconds = self.call(prompt, tag, attempt)
            if rc != 0 or '"turn.failed"' in stdout:  # a clean exit with a normal event stream is never a failure
                if LIMIT_PATTERN.search(stderr + stdout):
                    self.stop.set()
                    self.log({"item": item, "pass": pass_no, "attempt": attempt, "event": "rate_limit", "rc": rc})
                    return None, "rate_limit"
                reason = "codex exit %s" % rc
                self.log({"item": item, "pass": pass_no, "attempt": attempt, "event": "process_failure", "rc": rc,
                          "stderr_tail": (stderr or "")[-300:]})
                continue
            obj = extract_json(message)
            if obj is None:
                reason = "no JSON object in the final message"
                self.log({"item": item, "pass": pass_no, "attempt": attempt, "event": "unparseable"})
                continue
            transport = {"runner_version": RUNNER_VERSION, "codex_version": self.version, "model_requested": self.args.model,
                         "reasoning_effort": self.args.reasoning_effort or None, "attempt": attempt,
                         "prompt_sha256": sha256_text(prompt), "frozen_prompt_sha256": sha256_text(self.frozen),
                         "transport_note_sha256": sha256_text(TRANSPORT_NOTE), "event_types": event_types(stdout)}
            review = finalize_review(obj, item, pass_no, self.reviewer_id, started, now(), seconds, transport)
            problems = local_validate(review)
            if problems:
                reason = "invalid review: %s" % "; ".join(problems[:3])
                self.log({"item": item, "pass": pass_no, "attempt": attempt, "event": "invalid_review", "problems": problems})
                continue
            self.log({"item": item, "pass": pass_no, "attempt": attempt, "event": "ok", "seconds": round(seconds, 1)})
            return review, "ok"
        return None, reason

    def run_item(self, item: str) -> dict:
        result = {"item": item, "pass1": None, "pass2": None}
        packets = self.kit / "packets"
        p1_path = self.out / "reviews" / ("%s_pass1.json" % item)
        p2_path = self.out / "reviews" / ("%s_pass2.json" % item)
        if p1_path.exists():
            pass1 = json.loads(p1_path.read_text(encoding="utf-8"))
            result["pass1"] = "existing"
        else:
            packet = json.loads((packets / ("%s_pass1_packet.json" % item)).read_text(encoding="utf-8"))
            pass1, reason = self.review_once(item, 1, packet, None)
            result["pass1"] = reason
            if pass1 is None:
                return result
            p1_path.write_text(json.dumps(pass1, indent=2, ensure_ascii=False), encoding="utf-8")
        if p2_path.exists():
            result["pass2"] = "existing"
            return result
        packet = json.loads((packets / ("%s_pass2_packet.json" % item)).read_text(encoding="utf-8"))
        pass2, reason = self.review_once(item, 2, packet, pass1)
        result["pass2"] = reason
        if pass2 is not None:
            p2_path.write_text(json.dumps(pass2, indent=2, ensure_ascii=False), encoding="utf-8")
        return result


def load_manifest(kit: Path) -> dict:
    manifest = json.loads((kit / "manifest.json").read_text(encoding="utf-8"))
    frozen = (kit / "judge_prompt.md").read_text(encoding="utf-8")
    if sha256_text(frozen) != manifest["prompt_sha256"]:
        raise SystemExit("Refusing: judge_prompt.md does not match the kit manifest (the prompt is frozen).")
    for item in manifest["items"]:
        for n in (1, 2):
            path = kit / "packets" / ("%s_pass%d_packet.json" % (item, n))
            if sha256_text(path.read_text(encoding="utf-8")) != manifest["packet_sha256"]["%s_pass%d" % (item, n)]:
                raise SystemExit("Refusing: packet %s does not match the kit manifest." % path.name)
    return manifest


def preflight(args: argparse.Namespace) -> None:
    if shutil.which(args.codex) is None and not Path(args.codex).exists():
        raise SystemExit("Codex CLI not found (%s). Install it, run `codex login`, then rerun." % args.codex)
    report = flag_report(args.codex)
    if not report["ok"]:
        missing = [k for k, v in report["required"].items() if not v]
        raise SystemExit("This Codex version does not list the flags %s in `codex exec --help`; update Codex or adjust "
                         "the runner before any item is sent." % missing)
    if not args.keep_user_config and not report["optional"]["ignore_user_config"]:
        raise SystemExit("`--ignore-user-config` is not listed by this Codex version; rerun with --keep-user-config only "
                         "after checking that your config.toml sets no instructions, MCP servers or tools.")
    if args.reasoning_effort and not report["optional"]["config_override"]:
        raise SystemExit("`-c` (config override) is not listed by this Codex version; drop --reasoning-effort.")
    found = global_instructions()
    if found and not args.allow_user_instructions:
        raise SystemExit("Global Codex instruction files exist (%s); they would be sent to the judge with every call. "
                         "Move them away or pass --allow-user-instructions and record why." % found)


def cmd_check(args: argparse.Namespace) -> int:
    print("codex version:", codex_version(args.codex))
    report = flag_report(args.codex) if shutil.which(args.codex) or Path(args.codex).exists() else {"ok": False}
    print("flags:", json.dumps(report))
    status = subprocess.run([args.codex, "login", "status"], capture_output=True, text=True, timeout=60, env=clean_env())
    print("login status:", (status.stdout or status.stderr).strip(), "(exit %d)" % status.returncode)
    print("global instruction files:", global_instructions() or "none")
    print("API-key variables set in this shell (removed for every call):",
          [k for k in ("OPENAI_API_KEY", "CODEX_API_KEY") if os.environ.get(k)] or "none")
    return 0 if report.get("ok") and status.returncode == 0 else 1


def cmd_smoke(args: argparse.Namespace) -> int:
    preflight(args)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    fake_kit = out / "smoke_kit"
    fake_kit.mkdir(exist_ok=True)
    (fake_kit / "judge_prompt.md").write_text("Smoke test. Reply with the JSON object {\"validity\": \"valid\"} only.\n")
    runner = Runner(args, fake_kit, out)
    prompt = ("Item id: smoke\nReply with exactly this JSON object and nothing else: "
              "{\"validity\": \"valid\", \"smoke\": true}\n")
    message, stdout, stderr, rc, seconds = runner.call(prompt, "smoke", 1)
    print(json.dumps({"codex_version": runner.version, "model": args.model, "exit_code": rc, "seconds": round(seconds, 1),
                      "final_message": message.strip()[:300], "event_types": event_types(stdout),
                      "stderr_tail": (stderr or "")[-300:]}, indent=2))
    return 0 if rc == 0 and extract_json(message) is not None else 1


def cmd_run(args: argparse.Namespace) -> int:
    kit, out = Path(args.kit), Path(args.out)
    manifest = load_manifest(kit)
    preflight(args)
    items = args.items or manifest["items"]
    unknown = [i for i in items if i not in manifest["items"]]
    if unknown:
        raise SystemExit("Items not in the kit: %s" % unknown)
    out.mkdir(parents=True, exist_ok=True)
    runner = Runner(args, kit, out)
    runner.log({"event": "run_start", "model": args.model, "codex_version": runner.version, "n_items": len(items),
                "run_id": args.run_id, "kit_manifest_sha256": sha256_text(json.dumps(manifest, sort_keys=True))})
    results = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        for res in pool.map(runner.run_item, items):
            results.append(res)
            print("%-8s pass1=%-28s pass2=%s" % (res["item"], res["pass1"], res["pass2"]), flush=True)
    return finish(runner, results)


def finish(runner: Runner, results: list) -> int:
    ok = [r for r in results if r["pass1"] in ("ok", "existing") and r["pass2"] in ("ok", "existing")]
    failed = [r for r in results if r not in ok]
    stopped = runner.stop.is_set()
    summary = {"run_id": runner.args.run_id, "model": runner.args.model, "codex_version": runner.version,
               "items_complete": len(ok), "items_incomplete": len(failed), "stopped_for_rate_limit": stopped,
               "incomplete": failed, "finished_at": now()}
    (runner.out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    runner.log({"event": "run_end", **{k: summary[k] for k in ("items_complete", "items_incomplete", "stopped_for_rate_limit")}})
    print(json.dumps({k: summary[k] for k in ("items_complete", "items_incomplete", "stopped_for_rate_limit")}))
    if stopped:
        print("Usage limit reached: wait for the plan's window to reset and rerun the same command; finished reviews are "
              "kept and skipped.", file=sys.stderr)
        return EXIT_RATE_LIMIT
    return 0 if not failed else 1


def cmd_summary(args: argparse.Namespace) -> int:
    out = Path(args.out)
    reviews = sorted((out / "reviews").glob("*.json"))
    log = [json.loads(x) for x in (out / "run_log.jsonl").read_text().splitlines() if x.strip()] \
        if (out / "run_log.jsonl").exists() else []
    counts = {}
    for e in log:
        counts[e["event"]] = counts.get(e["event"], 0) + 1
    print(json.dumps({"reviews_written": len(reviews), "log_events": counts}, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("check", "smoke", "run", "summary"):
        p = sub.add_parser(name)
        p.add_argument("--codex", default="codex", help="path to the Codex CLI")
        p.add_argument("--model", default="gpt-6.1-sol", help="exact model id, recorded in every review")
        p.add_argument("--run-id", default=datetime.now(timezone.utc).strftime("gpt_%Y%m%d"))
        p.add_argument("--out", default="out")
        p.add_argument("--timeout", type=int, default=900, help="seconds per call")
        p.add_argument("--reasoning-effort", default=None, help="optional, passed as -c model_reasoning_effort=...")
        p.add_argument("--keep-user-config", action="store_true",
                       help="do not pass --ignore-user-config (only if that flag breaks the login)")
        p.add_argument("--allow-user-instructions", action="store_true")
        if name == "run":
            p.add_argument("--kit", default=".")
            p.add_argument("--items", nargs="*", default=None, help="a subset (trial runs: use a different --out)")
            p.add_argument("--workers", type=int, default=1)
    return parser


def main(argv: list | None = None) -> int:
    args = build_parser().parse_args(argv)
    return {"check": cmd_check, "smoke": cmd_smoke, "run": cmd_run, "summary": cmd_summary}[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
