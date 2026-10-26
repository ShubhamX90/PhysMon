#!/usr/bin/env python3
"""Stage 14.19: assemble the gold dataset from certified structures, their gold plans and their agent-verification status (CPU only).

Inputs: the structure libraries (`library`, `library_b`, `library_c` and the domain modules `lib_*`), the plans, levels and topics the
domain modules define, and a verification-status file (structure id -> accepted | accepted_after_repair | excluded, with the
reviewers' issues). Only accepted structures enter the dataset. For every instantiation of an accepted structure the dataset has one
sample: the problem text, the gold answer, the gold solving trace rendered from the typed graph, the assumptions, the inputs, the
equation relations, the independent-solver route, the author's level and topic judgement, the certification result, and the agent
verification record. The 11-cell distractor manifest of the accepted structures is written beside it for the later sensitivity runs.

Every sample carries the admission category UNREVIEWED and states that no human expert reviewed it. Excluded structures are listed
with their reasons, never silently dropped.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.benchmark.v2 import certify as ce  # noqa: E402
from physmon.benchmark.v2 import design as dg  # noqa: E402
from physmon.benchmark.v2 import trace as tr  # noqa: E402

OUT_ROOT = "data/v2/dataset"
BASE_LIBRARIES = ("library", "library_b", "library_c")
DOMAIN_MODULES = ("lib_mechanics", "lib_electromagnetism", "lib_thermodynamics", "lib_optics", "lib_quantum", "lib_modern", "lib_fluids")
ACCEPTED = ("accepted", "accepted_after_repair")


def load_sources(base: tuple[str, ...], domains: tuple[str, ...]) -> dict[str, Any]:
    structures: dict[str, Any] = {}
    origin: dict[str, str] = {}
    for name in (*base, *domains):
        module = importlib.import_module(f"physmon.benchmark.v2.{name}")
        for s in module.all_structures() if hasattr(module, "all_structures") else []:
            if s.structure_id in structures:
                raise ValueError(f"duplicate structure id {s.structure_id} in {name} and {origin[s.structure_id]}")
            structures[s.structure_id] = s
            origin[s.structure_id] = name
    plans: dict[str, tr.Plan] = {}
    levels: dict[str, str] = {}
    topics: dict[str, str] = {}
    plan_origin: dict[str, str] = {}
    for name in domains:
        module = importlib.import_module(f"physmon.benchmark.v2.{name}")
        for sid, plan in getattr(module, "PLANS", {}).items():
            if sid in plans:
                raise ValueError(f"two plans for {sid}: {name} and {plan_origin[sid]}")
            plans[sid], plan_origin[sid] = plan, name
            levels[sid] = getattr(module, "LEVELS", {}).get(sid, "unlabelled")
            topics[sid] = getattr(module, "TOPICS", {}).get(sid, "")
    return {"structures": structures, "origin": origin, "plans": plans, "levels": levels, "topics": topics, "plan_origin": plan_origin}


def sample_record(structure: Any, plan: tr.Plan, instance: int, meta: dict[str, Any], proof: dict[str, Any] | None) -> dict[str, Any]:
    display = dict(structure.instances[instance])
    trace = tr.render_trace(structure, plan, instance)
    program_hash = dg.structure_hash(structure)
    return {
        "sample_id": f"{structure.structure_id}-i{instance}", "structure_id": structure.structure_id, "instance": instance,
        "structure_uuid": dg.structure_uuid(structure), "symbolic_program_hash": program_hash,
        "template_cluster_id": f"V2C-{structure.structure_id}", "title": structure.title, "domain": structure.domain,
        "law_family": structure.law_family, "topic": meta["topic"], "level": meta["level"], "level_judged_by": "author agent",
        "problem": f"{dg.context_text(structure, display)}\n\n{dg.question_text(structure, display)}",
        "answer_unit": dg.display_unit(structure.render.target_unit), "gold_answer": trace["gold_answer"],
        "gold_trace": {"approach": plan.approach, "check": plan.check, "steps": trace["steps"], "text": trace["text"],
                       "kind": "solving technique rendered from the typed graph; not model-generated text"},
        "inputs": [{"name": n.name, "description": n.description, "value": display[n.name], "unit": dg.display_unit(n.unit),
                    "provenance": n.provenance} for n in structure.inputs],
        "relations": [{"node": n.name, "unit": dg.display_unit(n.unit), "expr_si": n.expr} for n in structure.computed],
        "assumptions": [a.text for a in structure.assumptions], "solver_route": structure.solver_route,
        "certification": None if proof is None else {"status": proof["status"], "checks_passed": sum(c["passed"] for c in proof["checks"]),
                                                     "checks_total": len(proof["checks"])},
        "admission_category": "UNREVIEWED",
        "review_statement": "No human expert has reviewed this item; it was checked by author, blind-solver and plan-reviewer agents.",
        "agent_verification": meta["verification"],
    }


def build(sources: dict[str, Any], status: dict[str, Any], certify: bool) -> tuple[list[dict], list[dict], list[dict]]:
    samples: list[dict] = []
    manifest: list[dict] = []
    excluded: list[dict] = []
    for sid, structure in sorted(sources["structures"].items()):
        verdict = status.get(sid, {})
        state = verdict.get("status", "not_verified")
        if state not in ACCEPTED or sid not in sources["plans"]:
            excluded.append({"structure_id": sid, "title": structure.title, "state": state if sid in sources["plans"] else "no_plan",
                             "issues": verdict.get("issues", [])})
            continue
        proof = ce.certify(structure) if certify else None
        if certify and proof["status"] != "SOLVER_CERTIFIED":
            excluded.append({"structure_id": sid, "title": structure.title, "state": "not_certified", "issues": []})
            continue
        meta = {"topic": sources["topics"].get(sid, ""), "level": sources["levels"].get(sid, "unlabelled"),
                "verification": {"status": state, "author_module": sources["plan_origin"].get(sid), "blind_solver_matched": verdict.get("blind_match"),
                                 "reviewer_issues_recorded": verdict.get("issues", [])}}
        for i in range(len(structure.instances)):
            samples.append(sample_record(structure, sources["plans"][sid], i, meta, proof))
        manifest += dg.manifest_rows(structure)
    return samples, manifest, excluded


def summarise(samples: list[dict], excluded: list[dict]) -> dict[str, Any]:
    by_structure = Counter(s["structure_id"] for s in samples)
    return {"n_samples": len(samples), "n_structures": len(by_structure), "excluded": excluded,
            "samples_by_domain": dict(Counter(s["domain"] for s in samples)),
            "structures_by_domain": dict(Counter(next(s["domain"] for s in samples if s["structure_id"] == k) for k in by_structure)),
            "samples_by_level": dict(Counter(s["level"] for s in samples)),
            "samples_by_topic_count": len({s["topic"] for s in samples}),
            "instances_per_structure": dict(Counter(by_structure.values()))}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--status", required=True, help="JSON: structure id -> {status, blind_match, issues}")
    parser.add_argument("--version", default="v1")
    parser.add_argument("--out-root", default=OUT_ROOT)
    parser.add_argument("--domains", nargs="*", default=list(DOMAIN_MODULES))
    parser.add_argument("--no-certify", action="store_true")
    args = parser.parse_args()
    out = (REPO_ROOT / args.out_root / args.version).resolve()
    if out.exists() and any(out.iterdir()):
        print(f"Refusing to reuse non-empty directory: {out}", file=sys.stderr)
        return 2
    status = json.loads(Path(args.status).read_text(encoding="utf-8"))
    sources = load_sources(BASE_LIBRARIES, tuple(args.domains))
    samples, manifest, excluded = build(sources, status, certify=not args.no_certify)
    out.mkdir(parents=True, exist_ok=True)
    (out / "dataset.jsonl").write_text("".join(json.dumps(s, sort_keys=True, ensure_ascii=False) + "\n" for s in samples), encoding="utf-8")
    (out / "factor_cell_manifest.jsonl").write_text("".join(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n" for r in manifest), encoding="utf-8")
    summary = {"stage": "14.19", "version": args.version, "inputs": {"status_file_sha256": hashlib.sha256(Path(args.status).read_bytes()).hexdigest()},
               "command": " ".join(sys.argv), **summarise(samples, excluded),
               "admission": "every sample UNREVIEWED: no human expert review; agent-verified only",
               "file_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir()) if p.is_file()}}
    (out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("n_samples", "n_structures", "samples_by_domain", "samples_by_level", "instances_per_structure")}, indent=2))
    return 0 if samples else 1


if __name__ == "__main__":
    raise SystemExit(main())
