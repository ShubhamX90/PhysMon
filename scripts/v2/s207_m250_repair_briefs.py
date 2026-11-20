#!/usr/bin/env python3
"""Stage 15: per-source-module repair briefs for the M250 repair round 1 (journal J15.1-059).

Reads the two-judge score (`s190b` report), the restricted key (sentence id -> label), the pass-2 packets (problem, sentences,
authors' claims) and the naturalness verdicts of `docs/validation/v2/llm_panel/admission_m250/`, and writes one Markdown brief per
spec module listing every structure that must change: REJECTED structures (any high flag) and ADMITTED structures with a sentence
rated artificial or a D sentence more than one level worse than its R twin (standard 6.1). Every flag of both judges (high, medium,
low) is quoted with the sentence ids resolved to labels (R0, D1, N0, C1, K0, ...), and every naturalness rating with its sentence.

Usage: s207_m250_repair_briefs.py --out DIR      (writes DIR/<module>.md and DIR/index.json)
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ADM = REPO_ROOT / "docs/validation/v2/llm_panel/admission_m250"
DATASET = REPO_ROOT / "data/v2/dataset/m250_explore_v1"


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def module_of() -> dict[str, str]:
    out = {}
    for path in sorted((DATASET / "admission").glob("*.json")):
        rec = json.loads(path.read_text(encoding="utf-8"))
        sid = rec.get("structure_id") or path.stem
        module = (rec.get("lineage") or {}).get("spec_module")
        if module:
            out[sid] = module
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    report = json.loads((ADM / "runs/score_two_judges/admission_report.json").read_text(encoding="utf-8"))
    key = json.loads((ADM / "key_RESTRICTED.json").read_text(encoding="utf-8"))
    packets = {p["item_id"]: p for p in load_jsonl(ADM / "pass2_packets.jsonl")}
    npackets = {p["item_id"]: p for p in load_jsonl(ADM / "naturalness_packets.jsonl")}
    modules = module_of()

    nat_by_sid: dict[str, list[tuple[str, str, str, str]]] = defaultdict(list)
    for nid, rec in report["sentences"].items():
        rating = rec["ratings"].get("claude", {})
        nat_by_sid[rec["structure_id"]].append((rec["label"], rating.get("rating", "?"), rating.get("reason", ""),
                                                npackets[nid]["inserted_sentence"]))

    briefs: dict[str, list[str]] = defaultdict(list)
    index: dict[str, list[dict]] = defaultdict(list)
    for item, s in sorted(report["structures"].items(), key=lambda kv: int(re.sub(r"\D", "", kv[1]["structure_id"]) or 0)):
        sid = s["structure_id"]
        rewrite = s["naturalness"]["rewrite"]
        if s["status"] == "ADMIT" and not rewrite:
            continue
        labels = key[item]["sentence_labels"]
        module = modules.get(sid, "UNKNOWN")

        def lab(text: str, labels: dict = labels) -> str:
            return re.sub(r"\bT[0-9A-F]{4}\b", lambda m: f"{m.group(0)}[{labels.get(m.group(0), '?')}]", text)

        lines = [f"## {sid}  -  panel status {s['status']}" + (f"; sentences to rewrite (6.1): {', '.join(rewrite)}" if rewrite else ""), ""]
        packet = packets[item]
        lines += ["Base problem as the judges saw it (the scene clause is part of it):", "", "```", packet["problem"], "```", "",
                  f"Base answer: {packet['base_answer']} {packet.get('target_unit', '')}", "", "Authors' stated assumptions:"]
        lines += [f"- {a}" for a in packet.get("assumptions", [])]
        lines += ["", "Sentences (id[label]: text):"]
        lines += [f"- {x['sentence_id']}[{labels.get(x['sentence_id'], '?')}]: {x['text']}" for x in packet["sentences"]]
        lines += ["", "Judge verdicts (every flag; 'high' rejects; 5.3b-guarded flags are listed under warnings and do not count):"]
        for judge, v in s["judges"].items():
            lines.append(f"- **{judge}**: status {v['status']}, validity {v['validity']}, category {v['admission_category']}")
            for f in v["flags"]:
                lines.append(f"  - [{f['severity']}] {f['flag']}: {lab(f['reason'])}")
            for w in v.get("warnings", []):
                lines.append(f"  - warning: {lab(w)}")
        if s.get("notes"):
            lines += [f"- note: {n}" for n in s["notes"]]
        lines += ["", "Blind naturalness ratings (Claude rater; artificial = must be rewritten):"]
        for label, rating, reason, text in sorted(nat_by_sid.get(sid, [])):
            lines.append(f"- {label} [{rating}] \"{text}\" - {reason}")
        lines.append("")
        briefs[module] += lines
        index[module].append({"structure_id": sid, "status": s["status"], "rewrite": rewrite,
                              "high_flags": sorted({f"{j}:{f['flag']}" for j, v in s["judges"].items() for f in v["flags"]
                                                    if f["severity"] == "high"})})

    for module, lines in briefs.items():
        header = [f"# Repair brief: `{module}` ({len(index[module])} structures)", ""]
        (out / f"{module}.md").write_text("\n".join(header + lines), encoding="utf-8")
    (out / "index.json").write_text(json.dumps(index, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps({m: len(v) for m, v in sorted(index.items())}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
