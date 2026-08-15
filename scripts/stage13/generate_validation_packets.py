#!/usr/bin/env python3
"""Generate blinded human-validation packet scaffolds."""

from __future__ import annotations

import argparse
import json

from governance_utils import REPO_ROOT, sha256_text, write_json, write_jsonl


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-dir", default="results/stage6/generated_full_benchmark")
    parser.add_argument("--n-families", type=int, default=25)
    parser.add_argument("--output", default="docs/validation/stage13_validation_packet_pass1.jsonl")
    parser.add_argument("--certificate-output", default="docs/validation/stage13_validation_packet_pass2.jsonl")
    parser.add_argument("--summary-output", default="results/stage13/benchmark_integrity/validation_packet_summary.json")
    args = parser.parse_args()

    pass1 = []
    pass2 = []
    for path in sorted((REPO_ROOT / args.generated_dir).glob("*.json"))[: args.n_families]:
        family = json.loads(path.read_text(encoding="utf-8"))
        fid = family.get("template_id", path.stem)
        base_prompt = ""
        if family.get("variants"):
            base_prompt = str(family["variants"][0].get("prompt", ""))
        pass1.append(
            {
                "packet_id": f"stage13::{sha256_text(fid)[:12]}",
                "template_id_blinded": sha256_text(fid)[:16],
                "prompt_text": base_prompt,
                "human_valid_physics": "",
                "human_cue_irrelevant": "",
                "human_notes": "",
            }
        )
        pass2.append(
            {
                "packet_id": f"stage13::{sha256_text(fid)[:12]}",
                "template_id": fid,
                "correct_answer": family.get("correct_answer", ""),
                "verifier_certified": family.get("verifier_certified", ""),
                "source_path": str(path.relative_to(REPO_ROOT)),
            }
        )
    write_jsonl(args.output, pass1)
    write_jsonl(args.certificate_output, pass2)
    write_json(
        args.summary_output,
        {
            "n_packet_rows": len(pass1),
            "pass1_output": args.output,
            "pass2_output": args.certificate_output,
            "status": "SOFTWARE_PACKET_READY_HUMAN_JUDGMENTS_PENDING",
            "paper_eligible": False,
        },
    )


if __name__ == "__main__":
    main()

