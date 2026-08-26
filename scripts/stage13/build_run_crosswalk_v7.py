#!/usr/bin/env python3
"""Build a run-level registry crosswalk from real Slurm evidence (v7).

The v6 crosswalk derived its "expected runs" by globbing filenames under
``results/`` and slugifying each path, which Task V6.40 explicitly forbids
("Do not create expected runs from ... output directories ... alone").  It
produced 621 pseudo-runs, matched 28, and reported 4.5% coverage against a
denominator that never corresponded to anything that executed.

v7 takes its denominator from evidence that a job actually ran: the Sharanga
Slurm log root joined to Slurm accounting, collected by
``scripts/ops/collect_sharanga_run_inventory.py``.  Every expected run therefore
has a real job ID, a real terminal state, and real log paths.

Matching is deliberately conservative.  A registry experiment is matched to a job
only when their identifying tokens overlap; anything weaker is reported as
unmatched rather than guessed, and the confidence of each mapping is recorded.
Coverage is reported against jobs that plausibly correspond to registrable
science, with infrastructure jobs (smoke tests, environment validation) counted
separately instead of being silently dropped from the denominator.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from governance_utils import read_jsonl, write_csv, write_json  # noqa: E402


# Job-name markers for infrastructure work that is not a registrable experiment.
INFRASTRUCTURE_MARKERS = (
    "smoke", "validate", "tl_", "hooks", "part2_", "dl_", "download",
)

TOKEN_SPLIT = re.compile(r"[^a-z0-9]+")

# Short tokens carry no identifying power and cause false matches.
STOPWORDS = {
    "physmon", "run", "job", "the", "and", "for", "a1", "h100", "h200", "a100",
    "cpu", "gpu", "v2", "v3", "v4", "rerun", "fix",
}


def tokens(text: str) -> set[str]:
    return {
        token
        for token in TOKEN_SPLIT.split(str(text).lower())
        if len(token) > 2 and token not in STOPWORDS
    }


# Expanded forms for the abbreviations used in job names.
ALIASES = {
    "s6": "stage6", "s8": "stage8", "s9": "stage9", "s10": "stage10",
    "s11": "stage11", "s12": "stage12", "s95": "stage95",
    "beh": "behavioural", "att": "attention", "attn": "attention",
    "probe": "probing", "xcue": "cross_cue", "xfam": "cross_family",
    "llm": "llama", "ds": "deepseek", "don": "donor", "donren": "donor_renamed",
    "mhk": "multi_head_knockout", "ko": "knockout", "exp": "expansion",
    "ent": "entropy", "corr": "correctness", "ans": "answer", "suf": "sufficiency",
    "inj": "injection", "cond": "condition", "sweep": "sweep", "act": "activations",
}


def expand(token_set: set[str]) -> set[str]:
    expanded = set(token_set)
    for token in token_set:
        if token in ALIASES:
            expanded.update(tokens(ALIASES[token]))
    return expanded


def is_infrastructure(job_name: str) -> bool:
    lowered = str(job_name).lower()
    return any(marker in lowered for marker in INFRASTRUCTURE_MARKERS)


MODEL_NAMES = {"qwen", "llama", "deepseek", "mistral", "gemma"}

# Experiment-kind markers. A job whose kind contradicts the registry entry's kind
# is a different experiment even when stage and model agree, so it may not be
# reported as a full match.
KIND_MARKERS = {
    "extraction": ("extract", "act"),
    "behavioural": ("behavioural", "beh", "d1", "d2"),
    "probing": ("probe", "probing", "sweep"),
    "causal": ("patch", "knockout", "mhk", "donor", "inject", "gate"),
    "attention": ("attention", "attn"),
    "baseline": ("baseline", "entropy", "judge", "selfcon", "consistency"),
}


def kind_of(text: str) -> str | None:
    """Best-effort experiment kind for a job name or registry entry."""

    lowered = str(text).lower()
    for kind, markers in KIND_MARKERS.items():
        if any(re.search(rf"(?:^|[^a-z]){re.escape(m)}(?:[^a-z]|$)", lowered) for m in markers):
            return kind
    return None
STAGE_RE = re.compile(r"(?:stage|s)(\d{1,2})(?![0-9])")


def stage_of(text: str) -> str | None:
    """Extract a stage number from a job name or registry stage field.

    Stage agreement is the strongest cheap signal available. Without it, a job
    name of the form <stage><model> matches any registry entry sharing only the
    model, which manufactures coverage.
    """

    match = STAGE_RE.search(str(text).lower())
    return match.group(1) if match else None


def registry_identity(entry: dict[str, Any]) -> set[str]:
    parts = [
        entry.get("experiment_id", ""),
        entry.get("task_id", ""),
        entry.get("stage", ""),
        entry.get("model_id", ""),
    ]
    return expand(tokens(" ".join(str(p) for p in parts)))


def match_job(
    job_tokens: set[str],
    registry: list[dict[str, Any]],
    job_stage: str | None = None,
    entry_stage_cache: dict[int, str | None] | None = None,
    job_kind: str | None = None,
) -> tuple[str, str, float]:
    """Return (experiment_id, mapping_status, score) for the best registry match."""

    entry_stage_cache = entry_stage_cache if entry_stage_cache is not None else {}

    best_id, best_score = "", 0.0
    for entry in registry:
        identity = registry_identity(entry)
        if not identity:
            continue

        # A disagreeing stage is disqualifying, not merely low-scoring.
        if job_stage and entry_stage_cache.get(id(entry)) and job_stage != entry_stage_cache[id(entry)]:
            continue

        overlap = job_tokens & identity
        if not overlap:
            continue

        # Overlapping only on the model name is not identification: nearly every
        # experiment shares a model with nearly every job.
        discriminative = overlap - MODEL_NAMES
        if not discriminative:
            continue

        score = len(overlap) / max(1, len(job_tokens))
        if score > best_score:
            best_id, best_score = str(entry.get("experiment_id", "")), score

    # A contradicted experiment kind downgrades an otherwise strong match.
    if best_id and job_kind:
        for entry in registry:
            if str(entry.get("experiment_id", "")) == best_id:
                entry_kind = kind_of(
                    f"{entry.get('experiment_id','')} {entry.get('experiment_class','')}"
                )
                if entry_kind and entry_kind != job_kind:
                    return best_id, "partially_matched", best_score
                break

    # "matched" additionally requires that the stage was positively confirmed.
    if best_score >= 0.5 and best_id and job_stage:
        for entry in registry:
            if str(entry.get("experiment_id", "")) == best_id:
                if entry_stage_cache.get(id(entry)) == job_stage:
                    return best_id, "matched", best_score
                break
        return best_id, "partially_matched", best_score
    if best_score >= 0.5:
        return best_id, "partially_matched", best_score
    if best_score >= 0.25:
        return best_id, "partially_matched", best_score
    return "", "unmatched", best_score


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", default="results/stage13/wave0/sharanga_run_inventory_v7.jsonl")
    parser.add_argument("--registry", default="docs/registry/experiment_registry.jsonl")
    parser.add_argument("--crosswalk-out", default="docs/registry/historical_run_crosswalk_v7.csv")
    parser.add_argument("--runs-out", default="results/stage13/wave0/expected_historical_runs_v7.jsonl")
    parser.add_argument("--coverage-out", default="results/stage13/wave0/registry_coverage_v7.json")
    args = parser.parse_args()

    inventory = [row for row in read_jsonl(args.inventory) if row.get("job_id")]
    registry = read_jsonl(args.registry)

    # Stage per registry entry, resolved once from its stage field or experiment id.
    entry_stage_cache = {
        id(entry): stage_of(str(entry.get("stage", "")) or str(entry.get("experiment_id", "")))
        for entry in registry
    }

    expected_runs: list[dict[str, Any]] = []
    crosswalk: list[dict[str, Any]] = []
    status_counts: Counter = Counter()

    for job in inventory:
        job_name = str(job.get("job_name_from_log", ""))
        infrastructure = is_infrastructure(job_name)
        job_tokens = expand(tokens(job_name))
        experiment_id, mapping_status, score = match_job(
            job_tokens, registry, stage_of(job_name), entry_stage_cache, kind_of(job_name)
        )

        # Panel identity is only claimed when a matched registry entry supplies it.
        panel_identity = "unresolved"
        if experiment_id:
            for entry in registry:
                if str(entry.get("experiment_id")) == experiment_id:
                    panel_identity = str(entry.get("family_manifest") or "unresolved")
                    break

        run = {
            "expected_run_id": f"sharanga_job_{job['job_id']}",
            "job_id": job["job_id"],
            "job_id_source": job.get("job_id_source", ""),
            "job_name": job_name,
            "experiment_family": job_name,
            "model_id": next(
                (m for m in ("qwen", "llama", "deepseek", "mistral") if m in job_name.lower()),
                "unresolved",
            ),
            "configuration_identity": job.get("header", {}).get("script", "") or "unresolved",
            "panel_identity": panel_identity,
            "terminal_state": job.get("terminal_state", "unknown"),
            "partition": job.get("partition", ""),
            "exit_code": job.get("exit_code", ""),
            "elapsed": job.get("elapsed", ""),
            "submit": job.get("submit", ""),
            "end": job.get("end", ""),
            "logs": job.get("stdout_path", ""),
            "stderr": job.get("stderr_path", ""),
            "stdout_bytes": job.get("stdout_bytes"),
            "run_class": "infrastructure" if infrastructure else "candidate_science_run",
            "confidence": "high" if job.get("accounting_status") == "sacct" else "low",
        }
        expected_runs.append(run)

        if infrastructure:
            mapping_status = "infrastructure_not_registrable"
        status_counts[mapping_status] += 1
        crosswalk.append(
            {
                **{k: run[k] for k in (
                    "expected_run_id", "job_id", "job_name", "model_id",
                    "panel_identity", "terminal_state", "run_class",
                )},
                "registry_experiment_id": experiment_id,
                "mapping_status": mapping_status,
                "match_score": round(score, 3),
            }
        )

    science_runs = [r for r in crosswalk if r["run_class"] == "candidate_science_run"]
    matched = sum(1 for r in science_runs if r["mapping_status"] == "matched")
    partial = sum(1 for r in science_runs if r["mapping_status"] == "partially_matched")
    unmatched = sum(1 for r in science_runs if r["mapping_status"] == "unmatched")

    coverage = {
        "denominator_source": "sharanga_slurm_logs_joined_to_sacct",
        "supersedes": "results/stage13/wave0/registry_coverage_v6.json",
        "supersession_reason": (
            "v6 derived 621 expected runs by slugifying results/** filenames, which "
            "Task V6.40 forbids; no v6 expected run was evidence that a job executed."
        ),
        "n_jobs_in_inventory": len(inventory),
        "n_infrastructure_jobs": sum(
            1 for r in crosswalk if r["mapping_status"] == "infrastructure_not_registrable"
        ),
        "n_expected_science_runs": len(science_runs),
        "matched": matched,
        "partial": partial,
        "unmatched": unmatched,
        "irrecoverable": 0,
        "coverage_fraction": round((matched + partial) / len(science_runs), 4) if science_runs else 0.0,
        "strict_coverage_fraction": round(matched / len(science_runs), 4) if science_runs else 0.0,
        "n_registry_entries": len(registry),
        "terminal_states": dict(Counter(r["terminal_state"] for r in science_runs)),
        "panel_identity_resolved": sum(
            1 for r in science_runs if r["panel_identity"] != "unresolved"
        ),
        "note": (
            "Coverage is reported against jobs with real Slurm identities. Infrastructure "
            "jobs are counted separately rather than dropped from the denominator. "
            "Unmatched jobs are reported as unmatched, never inferred."
        ),
    }

    write_json(args.coverage_out, coverage)
    write_csv(
        args.crosswalk_out,
        crosswalk,
        [
            "expected_run_id", "job_id", "job_name", "model_id", "panel_identity",
            "terminal_state", "run_class", "registry_experiment_id",
            "mapping_status", "match_score",
        ],
    )
    with (Path(args.runs_out)).open("w", encoding="utf-8") as handle:
        for run in expected_runs:
            handle.write(json.dumps(run, sort_keys=True) + "\n")

    print(json.dumps(coverage, indent=2))


if __name__ == "__main__":
    main()
