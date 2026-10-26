#!/usr/bin/env python3
"""Stage 14.19: check a domain module of DECOY-v2 structures and gold plans (CPU only; the authoring loop's feedback tool).

For a module that defines `all_structures()` (new structures, optional) and `PLANS` (a dict structure_id -> `trace.Plan`, covering the
module's new structures and, optionally, existing ones), this prints for every structure: certification (every failed check), overlap of
its equation program with v1 templates and with all other batches, plan validity, the instance-0 prompt and the rendered gold trace.
It writes nothing. Exit code 0 only if every new structure is SOLVER_CERTIFIED, has no overlap, has at least `--min-instances`
instantiations and every plan is valid.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.benchmark.v2 import certify as ce  # noqa: E402
from physmon.benchmark.v2 import design as dg  # noqa: E402
from physmon.benchmark.v2 import trace as tr  # noqa: E402

EXISTING = ("library", "library_b", "library_c")


def _s146():
    spec = importlib.util.spec_from_file_location("s146", REPO_ROOT / "scripts/v2/s146_generate_structures.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", required=True, help="e.g. physmon.benchmark.v2.lib_quantum")
    parser.add_argument("--min-instances", type=int, default=4)
    parser.add_argument("--quiet", action="store_true", help="only failures and a summary")
    parser.add_argument("--others", nargs="*", default=[], help="other new domain modules to check program overlap against")
    args = parser.parse_args()
    module = importlib.import_module(args.module)
    structures = module.all_structures() if hasattr(module, "all_structures") else []
    plans = getattr(module, "PLANS", {})
    s146 = _s146()
    v1 = s146.v1_overlap()
    known_hashes: dict[str, str] = {}
    all_existing = {}
    for name in EXISTING:
        for s in importlib.import_module(f"physmon.benchmark.v2.{name}").all_structures():
            known_hashes[dg.structure_hash(s)] = s.structure_id
            all_existing[s.structure_id] = s
    for other in args.others:
        for s in importlib.import_module(other).all_structures():
            known_hashes[dg.structure_hash(s)] = s.structure_id
    failures = 0
    ids = [s.structure_id for s in structures]
    if len(set(ids)) != len(ids):
        print("FAIL duplicate structure ids in the module")
        failures += 1
    for s in structures:
        problems = []
        proof = ce.certify(s)
        if proof["status"] != "SOLVER_CERTIFIED":
            problems += [f"check {c['name']}: {c['detail']}" for c in proof["checks"] if not c["passed"]]
        program = dg.structure_hash(s)
        if v1["programs"].get(program):
            problems.append(f"program equals v1 template(s) {v1['programs'][program]}")
        if known_hashes.get(program):
            problems.append(f"program equals existing structure {known_hashes[program]}")
        if len(s.instances) < args.min_instances:
            problems.append(f"only {len(s.instances)} instantiations, need {args.min_instances}")
        if s.structure_id not in plans:
            problems.append("no plan")
        mutants = ce.mutation_report(s)
        missed = [r for r in mutants if r["kind"] == "negative" and r["outcome"] != "caught"]
        wrong = [r for r in mutants if r["kind"] == "positive" and r["outcome"] != "passed"]
        if missed or wrong:
            problems.append(f"mutation harness: {len(missed)} negative not caught, {len(wrong)} positive wrongly rejected")
        print(f"{'FAIL' if problems else 'ok  '} {s.structure_id} {s.title} [{s.domain}]")
        for p in problems:
            print("     -", p)
        failures += bool(problems)
    for sid, plan in plans.items():
        target = next((s for s in structures if s.structure_id == sid), all_existing.get(sid))
        if target is None:
            print(f"FAIL plan for unknown structure {sid}")
            failures += 1
            continue
        problems = tr.validate_plan(target, plan)
        print(f"{'FAIL' if problems else 'ok  '} plan {sid}")
        for p in problems:
            print("     -", p)
        failures += bool(problems)
        if not problems and not args.quiet:
            print(f"     prompt: {dg.context_text(target, dict(target.instances[0]))} {dg.question_text(target, dict(target.instances[0]))}")
            for i in range(len(target.instances)):
                rendered = tr.render_trace(target, plan, i)
                print(f"     instance {i}: gold {rendered['gold_answer']['value']:.6g} {rendered['gold_answer']['unit']}")
            print("     " + tr.render_trace(target, plan, 0)["text"].replace("\n", "\n     "))
    print(f"SUMMARY structures={len(structures)} plans={len(plans)} failures={failures}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
