#!/usr/bin/env python3
"""Generate Stage 13 v5 solver-derived certificates from structured YAML templates."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from physmon.validation.certificate_generator import generate_certificate  # noqa: E402

from governance_utils import REPO_ROOT, write_json  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default="data/manifests/physmon_canonical_155.jsonl")
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--certificate-dir", default="docs/validation/certificates_v5")
    parser.add_argument("--pass2-output", default="docs/validation/stage13_validation_packet_pass2_v5.jsonl")
    parser.add_argument("--summary-output", default="results/stage13/benchmark_integrity/certificate_generation_summary_v5.json")
    return parser.parse_args()


def load_manifest(path: str) -> list[dict[str, str]]:
    return [json.loads(line) for line in (REPO_ROOT / path).read_text(encoding="utf-8").splitlines() if line.strip()]


def find_yaml(fid: str) -> Path | None:
    matches = sorted((REPO_ROOT / "data/raw/templates").rglob(f"{fid}.yaml"))
    return matches[0] if matches else None


def stratify(rows: list[dict[str, str]], limit: int) -> list[dict[str, str]]:
    by_key: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if row.get("is_canonical") is True:
            by_key[(row.get("domain", ""), row.get("cue_type", ""), row.get("original_or_expansion", ""))].append(row)
    selected: list[dict[str, str]] = []
    for key in sorted(by_key):
        selected.extend(by_key[key][:2])
    for row in rows:
        if row.get("is_canonical") is True and row not in selected:
            selected.append(row)
        if len(selected) >= limit:
            break
    return selected[:limit]


def main() -> None:
    args = parse_args()
    cert_dir = REPO_ROOT / args.certificate_dir
    cert_dir.mkdir(parents=True, exist_ok=True)
    pass2_rows = []
    statuses = defaultdict(int)
    generated = []
    for row in stratify(load_manifest(args.manifest), args.limit):
        fid = row["canonical_family_id"]
        yaml_path = find_yaml(fid)
        if yaml_path is None:
            cert = {
                "family_id": fid,
                "certificate_status": "certificate_generation_blocked",
                "blocked_reason": "No structured YAML template found.",
            }
        else:
            cert = generate_certificate(yaml_path)
        statuses[cert.get("certificate_status", "unknown")] += 1
        if cert.get("certificate_status") == "certificate_generated":
            cert_path = cert_dir / f"{fid}.json"
            write_json(str(cert_path.relative_to(REPO_ROOT)), cert)
            generated.append(fid)
            pass2_rows.append(
                {
                    "packet_id": f"pass2_v5_{fid}",
                    "packet_version": "stage13_pass2_v5",
                    "pass_number": 2,
                    "family_id": fid,
                    "domain": row.get("domain"),
                    "cue_type": row.get("cue_type"),
                    "certificate_path": str(cert_path.relative_to(REPO_ROOT)),
                    "certificate": cert,
                    "human_fields": {
                        "validator_certificate_valid": None,
                        "validator_solver_derivation_correct": None,
                        "validator_canonical_answer_correct": None,
                        "notes": None,
                    },
                }
            )
    pass2_path = REPO_ROOT / args.pass2_output
    pass2_path.parent.mkdir(parents=True, exist_ok=True)
    pass2_path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in pass2_rows) + "\n", encoding="utf-8")
    write_json(
        args.summary_output,
        {
            "status": "CERTIFICATES_GENERATED_FROM_STRUCTURED_TEMPLATES" if generated else "CERTIFICATE_GENERATION_BLOCKED",
            "status_counts": dict(statuses),
            "n_pass2_packets": len(pass2_rows),
            "certificate_dir": args.certificate_dir,
            "pass2_output": args.pass2_output,
        },
    )


if __name__ == "__main__":
    main()
