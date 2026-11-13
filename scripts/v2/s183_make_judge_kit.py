#!/usr/bin/env python3
"""Stage 15 (G1): export a self-contained judge kit for running a GPT or Gemini judge on another machine.

The kit holds only what the judge may see: the frozen judge prompt, the judge-facing pass-1 and pass-2 packets of one bank
split, a manifest with the SHA-256 of each file, the standalone runner (`s182_run_codex_judge.py`, copied as
`run_codex_judge.py`) and a README. The answer key (`key_RESTRICTED.json`), the generator code and every other repository
file stay behind. The kit builder refuses to overwrite and scans every packet for key fields.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LEAK_FIELDS = ("defect_type", "expected_verdict", "detectable_in", "description", "structure_id", "split",
               "physicist_confirmation", "edited_answer", "original_answer", "family", "accepted_terms", "contested")

README = """# Judge kit

Contents: `run_codex_judge.py` (the runner, Python 3.8+, standard library only), `judge_prompt.md` (the frozen prompt),
`packets/` (judge-facing packets, {n_items} items), `manifest.json` (SHA-256 of every file; the runner refuses a changed
prompt or packet). There is no answer key in this folder, and none may be added.

## Steps (on the laptop)
1. Install the Codex CLI (OpenAI's install page) and sign in with the ChatGPT account:  `codex login`
   Check:  `codex login status`.  Do not set OPENAI_API_KEY or CODEX_API_KEY (the runner removes them anyway).
2. Move any global Codex instruction file away for the run (`~/.codex/AGENTS.md`, `AGENTS.override.md`): it would be sent to
   the judge with every call. The runner refuses to start while one exists.
3. `python run_codex_judge.py check --model {model}`   (flags, login status, instruction files)
4. `python run_codex_judge.py smoke --model {model} --out out_smoke`   (one trivial call; send the printed JSON back)
5. Trial on three items (separate folder, not part of the qualification):
   `python run_codex_judge.py run --kit . --model {model} --out out_trial --items {trial_items}`
6. The qualification run (about {n_calls} calls; the plan's usage window may stop it; rerun the same command later, finished
   reviews are skipped):
   `python run_codex_judge.py run --kit . --model {model} --run-id {run_id} --out out_{run_id}`
   Exit code 75 means the usage limit was reached.
7. Copy `out_{run_id}/` back (reviews/, events/, prompts/, run_log.jsonl, summary.json). On the cluster:
   `s184_audit_codex_events.py --events <dir>/events`, then `s179_score_judges.py --reviews <dir>/reviews`.

If `codex exec --help` lacks a flag the runner uses, it stops before sending anything and names it.
If `--ignore-user-config` breaks the login, check your config.toml is empty of instructions and tools, then add
`--keep-user-config`.
"""


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build(out: Path, bank: Path, split: str, prompt: Path, model: str, run_id: str) -> dict:
    key = json.loads((bank / "key_RESTRICTED.json").read_text(encoding="utf-8"))
    items = [i for i, k in key.items() if k["split"] == split]
    order = [json.loads(x)["item_id"] for x in (bank / "pass1_packets.jsonl").read_text().splitlines() if x.strip()]
    items = [i for i in order if i in items]
    p1 = {json.loads(x)["item_id"]: x for x in (bank / "pass1_packets.jsonl").read_text().splitlines() if x.strip()}
    p2 = {json.loads(x)["item_id"]: x for x in (bank / "pass2_packets.jsonl").read_text().splitlines() if x.strip()}
    out.mkdir(parents=True, exist_ok=False)
    (out / "packets").mkdir()
    packet_hashes = {}
    for item in items:
        for n, source in ((1, p1), (2, p2)):
            packet = json.loads(source[item])
            leaked = [f for f in LEAK_FIELDS if f in packet]
            if leaked:
                raise SystemExit("key field(s) %s in packet %s" % (leaked, item))
            text = json.dumps(packet, indent=2, ensure_ascii=False)
            (out / "packets" / ("%s_pass%d_packet.json" % (item, n))).write_text(text, encoding="utf-8")
            packet_hashes["%s_pass%d" % (item, n)] = sha256_text(text)
    frozen = prompt.read_text(encoding="utf-8")
    (out / "judge_prompt.md").write_text(frozen, encoding="utf-8")
    shutil.copy(REPO_ROOT / "scripts/v2/s182_run_codex_judge.py", out / "run_codex_judge.py")
    manifest = {"split": split, "bank": str(bank.relative_to(REPO_ROOT)) if bank.is_relative_to(REPO_ROOT) else str(bank),
                "bank_manifest_sha256": sha256_file(bank / "manifest.json"), "items": items, "n_items": len(items),
                "prompt_sha256": sha256_text(frozen), "prompt_source": str(prompt),
                "runner_sha256": sha256_file(out / "run_codex_judge.py"), "packet_sha256": packet_hashes}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    trial = " ".join(items[:3])
    (out / "README.md").write_text(README.format(n_items=len(items), n_calls=2 * len(items), model=model,
                                                  run_id=run_id, trial_items=trial), encoding="utf-8")
    return manifest


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--bank", default="docs/validation/v2/llm_panel/bank_v3")
    parser.add_argument("--split", default="qualification", choices=("qualification", "heldout", "requal"))
    parser.add_argument("--prompt", default="docs/validation/v2/llm_panel/judge_prompt_v1.md")
    parser.add_argument("--model", default="gpt-6.1-sol")
    parser.add_argument("--run-id", default="gpt_q1")
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    out = Path(args.out)
    if out.exists():
        print("Refusing to overwrite %s" % out, file=sys.stderr)
        return 2
    manifest = build(out, REPO_ROOT / args.bank, args.split, REPO_ROOT / args.prompt, args.model, args.run_id)
    print(json.dumps({k: manifest[k] for k in ("split", "n_items", "prompt_sha256", "runner_sha256")}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
