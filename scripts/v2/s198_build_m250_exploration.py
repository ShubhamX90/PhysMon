#!/usr/bin/env python3
"""Stage 15: build the M250 EXPLORATION integration set (`data/v2/dataset/m250_explore_v1/`) with every MACHINE check of the dataset
admission standard (`docs/registry/v2/g1/dataset_admission_standard.md`, checks 1.1-1.3, 2.1-2.8 and 2.7b, 3.1-3.5, 4.1, 4.2, 6.2, 6.3).

Inputs (explicit list `SOURCES`, no globbing; a module that is missing or fails to import is reported, never skipped silently):

* `M0_MODULE`              the M0 structures: `roles_m0v25` (else v23, v22); their cells are those of
                           `s192_build_m0_v21.py` (the builder the M0 datasets were made with); panel status ADMITTED for roles_m0v25 (pointers to the two-judge runs);
* `roles_m250_a` to `_d`   upgraded dataset-v1 structures (base problem = the v1 problem + the scene clause);
* `roles_m250n_<domain>`   new structures from `lib_m250_<domain>` (no v1 text: the base-problem check is the rendered base problem + the
                           scene clause, with the gold from the independent solver route of the certifier).

Per structure the builder certifies the spec (`rolevalue_v2.certify_v2` on the v2.1 rules, see the judgement call in the README),
builds the cells and gold traces with the M0 v2.1 builder (`s192`, called per structure so that one failing structure cannot stop the
build), runs the grading dry run (`s194`), the planted-mutation tests and the overlap detectors, and records every check with
PASS / FAIL and its values in `admission/<structure_id>.json`. A structure failing any machine check is REJECTED: it keeps its
admission record and certificate (failed evidence is preserved) and has no cells. Panel checks (5.x, 6.1) are `PENDING` except for
the M0 v2.5 structures, which are two-judge ADMITTED (pointers recorded). Dataset-level checks (6.2 familiarity, 6.3 composition) are reported in
`composition.json`, not forced. Data role: EXPLORATION. Instance 0 of every structure, as in M0.

Deterministic apart from the build date (`--date`, default today); refuses to overwrite an existing directory.
Usage: s198_build_m250_exploration.py [--out data/v2/dataset/m250_explore_v1] [--date YYYY-MM-DD]
Exit status: 0 built; 1 built but a source module is missing or failed to import, or the provenance check found a CONFLICT; 2 refused.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime
import difflib
import hashlib
import importlib
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import traceback
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from physmon.benchmark.v2 import certify  # noqa: E402
from physmon.benchmark.v2 import design as dg  # noqa: E402
from physmon.benchmark.v2 import dimensions as dm  # noqa: E402
from physmon.benchmark.v2 import graph as gr  # noqa: E402
from physmon.benchmark.v2 import rolevalue as rv  # noqa: E402
from physmon.benchmark.v2 import rolevalue_v2 as r2  # noqa: E402
from physmon.benchmark.v2 import roles_m0v2  # noqa: E402
from physmon.benchmark.v2 import traces_v2 as t2  # noqa: E402

GENERATOR = "scripts/v2/s198_build_m250_exploration.py"
GENERATOR_VERSION = "s198 v1"
DATASET_ID = "m250_explore_v1"
DATA_ROLE = "EXPLORATION"
INSTANCE = 0
PASS, FAIL, NOT_EVALUATED, PENDING = "PASS", "FAIL", "NOT_EVALUATED", "PENDING"
ADMITTED, REJECTED, NOT_BUILT = "MACHINE_ADMITTED", "REJECTED", "NOT_BUILT_INFEASIBLE"
TEXT_FLAG, JACCARD_FLAG = 0.85, 0.8
MIN_REASON = 20  # characters of a NO_C / NO_K reason
KINDS = ("M0", "UPGRADED_V1", "NEW")
UPPER_LEVEL = "upper_university"
MULTI_STEP_NODES = 3  # a structure with at least this many computed relations counts as multi-step (6.3)
PLAN_MODULES = ("lib_m250_mech", "lib_m250_em", "lib_m250_thermo", "lib_m250_waves", "lib_m250_modern", "lib_m250_extra", "lib_m250_circ",
                "lib_m250_qastro")
PANEL_DIRS = "docs/validation/v2/llm_panel"
# The M0 structures come from roles_m0v25 (final: all 11 two-judge ADMITTED); older modules only as a fallback when it is absent.
M0_MODULES = ("roles_m0v25", "roles_m0v23", "roles_m0v22")
M0_MODULE = next((m for m in M0_MODULES if importlib.util.find_spec(f"physmon.benchmark.v2.{m}") is not None), M0_MODULES[-1])
M0_VERSIONS = {"roles_m0v25": "m0_v2.5", "roles_m0v23": "m0_v2.3", "roles_m0v22": "m0_v2.2"}
# two-judge panel admission of the M0 v2.5 structures: the run directory that holds each structure's final verdict
M0_PANEL_RUN = {**dict.fromkeys(("S01", "S07", "S13", "S15", "S20", "S27", "S30"), "admission_m0v23"),
                **dict.fromkeys(("S72", "S92"), "admission_m0v24"), **dict.fromkeys(("S26", "S55"), "admission_m0v25")}


def m0_version(module_name: str) -> str:
    return M0_VERSIONS.get(module_name, "m0_v2.2")


M0_VERSION = m0_version(M0_MODULE)

# (key, spec module, kind, library module of new structures)
SOURCES: tuple[tuple[str, str, str, str | None], ...] = (
    ("m0", M0_MODULE, "M0", None),
    ("m250_a", "roles_m250_a", "UPGRADED_V1", None),
    ("m250_b", "roles_m250_b", "UPGRADED_V1", None),
    ("m250_c", "roles_m250_c", "UPGRADED_V1", None),
    ("m250_d", "roles_m250_d", "UPGRADED_V1", None),
    ("m250n_mech", "roles_m250n_mech", "NEW", "lib_m250_mech"),
    ("m250n_em", "roles_m250n_em", "NEW", "lib_m250_em"),
    ("m250n_thermo", "roles_m250n_thermo", "NEW", "lib_m250_thermo"),
    ("m250n_waves", "roles_m250n_waves", "NEW", "lib_m250_waves"),
    ("m250n_modern", "roles_m250n_modern", "NEW", "lib_m250_modern"),
    ("m250n_extra", "roles_m250n_extra", "NEW", "lib_m250_extra"),
    ("m250n_circ", "roles_m250n_circ", "NEW", "lib_m250_circ"),
    ("m250n_qastro", "roles_m250n_qastro", "NEW", "lib_m250_qastro"),
)
# every structure library (the pool of check 1.1 and 1.2): explicit, no globbing
LIB_MODULES = ("library", "library_b", "library_c", "lib_mechanics", "lib_electromagnetism", "lib_thermodynamics", "lib_optics",
               "lib_quantum", "lib_modern", "lib_fluids", "lib_m250_mech", "lib_m250_em", "lib_m250_thermo", "lib_m250_waves",
               "lib_m250_modern", "lib_m250_extra", "lib_m250_circ", "lib_m250_qastro")


def _load_script(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


s192 = _load_script("s192_build_m0_v21", "scripts/v2/s192_build_m0_v21.py")
s194 = _load_script("s194_grading_dry_run", "scripts/v2/s194_grading_dry_run.py")
ORIGINAL_TARGET_TERMS = s192.s188.target_terms
s192.readme = lambda *args, **kwargs: ""  # the per-structure build in a scratch directory needs no README
V1_DATASET = "data/v2/dataset/v1/dataset.jsonl"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sid_key(sid: str) -> tuple[int, str]:
    digits = re.sub(r"\D", "", sid)
    return (int(digits) if digits else 0, sid)


def six(x: float) -> float:
    return float(f"{x:.6g}")


def mask_numbers(text: str) -> str:
    return re.sub(r"\d+(?:[.,]\d+)?(?:[eE][+-]?\d+)?", "#", text)


# --- check records ---------------------------------------------------------------------------------------------------------------

def mk(cid: str, name: str, ok: bool | None, why: str = "", **values: Any) -> dict[str, Any]:
    status = NOT_EVALUATED if ok is None else (PASS if ok else FAIL)
    record: dict[str, Any] = {"id": cid, "name": name, "status": status}
    if why and status != PASS:
        record["why"] = why
    if values:
        record["values"] = values
    return record


def group_check(cid: str, name: str, cert: dict[str, Any], names: tuple[str, ...], optional: tuple[str, ...] = (),
                **values: Any) -> dict[str, Any]:
    """PASS when every named certify_v2 check exists and passed (optional names are read when present)."""

    checks = cert.get("checks", {})
    got: dict[str, bool | None] = {n: (bool(checks[n]["ok"]) if n in checks else None) for n in names}
    got.update({n: bool(checks[n]["ok"]) for n in optional if n in checks})
    bad = sorted(n for n, ok in got.items() if ok is not True)
    return mk(cid, name, not bad, "failed or missing in the certificate: " + ", ".join(bad), certificate_checks=got, **values)


# --- sources -----------------------------------------------------------------------------------------------------------------------

@dataclass
class Source:
    key: str
    module_name: str
    kind: str
    lib_module: str | None = None
    module: Any = None
    error: str | None = None
    specs: dict[str, r2.RoleSpecV2] = field(default_factory=dict)
    infeasible: dict[str, str] = field(default_factory=dict)
    no_c: dict[str, str] = field(default_factory=dict)
    no_k: dict[str, str] = field(default_factory=dict)
    target_terms: dict[str, Any] = field(default_factory=dict)
    levels: dict[str, str] = field(default_factory=dict)
    cert_version: str | None = None

    def bind(self, module: Any, levels: dict[str, str] | None = None) -> Source:
        self.module = module
        specs = getattr(module, "SPECS", None) or getattr(module, "ROLE_SPECS", None)
        if not specs or not callable(getattr(module, "structure", None)):
            self.error = "module has no SPECS/ROLE_SPECS or no structure()"
            return self
        self.specs = dict(specs)
        self.infeasible = dict(getattr(module, "INFEASIBLE", {}) or {})
        self.no_c = dict(getattr(module, "NO_C", {}) or {})
        self.no_k = dict(getattr(module, "NO_K", {}) or {})
        self.target_terms = dict(getattr(module, "TARGET_TERMS", {}) or {})
        self.levels = dict(levels or {})
        self.cert_version = getattr(module, "CERT_VERSION", None)
        return self

    @classmethod
    def load(cls, key: str, module_name: str, kind: str, lib_module: str | None) -> Source:
        source = cls(key, module_name, kind, lib_module)
        try:
            module = importlib.import_module(f"physmon.benchmark.v2.{module_name}")
        except ModuleNotFoundError as exc:
            source.error = f"module not found: {exc}"
            return source
        except Exception as exc:  # a module another agent is still writing may be broken; report, do not crash
            source.error = f"import failed: {exc!r}"
            return source
        levels: dict[str, str] = {}
        if lib_module:
            try:
                levels = dict(getattr(importlib.import_module(f"physmon.benchmark.v2.{lib_module}"), "LEVELS", {}))
            except Exception as exc:
                source.error = f"library module {lib_module} failed to import: {exc!r}"
                return source
        return source.bind(module, levels)

    def structure(self, sid: str) -> gr.Structure:
        return self.module.structure(sid)


def discover(sources: tuple[tuple[str, str, str, str | None], ...] = SOURCES) -> list[Source]:
    return [Source.load(*entry) for entry in sources]


def merged_plans() -> dict[str, Any]:
    plans = dict(t2.plans())
    for name in PLAN_MODULES:
        try:
            plans.update(getattr(importlib.import_module(f"physmon.benchmark.v2.{name}"), "PLANS", {}))
        except Exception:  # a library not written yet has no plans; a structure that needs one fails its build, visibly
            continue
    return plans


# --- the pool of existing structures (checks 1.1 and 1.2) ----------------------------------------------------------------------------

@dataclass
class Entry:
    sid: str
    origin: str
    hash: str
    cluster: str
    relations: frozenset[str]
    text: str
    signatures: frozenset[tuple[tuple[float, ...], float]]
    inputs0: tuple[float, ...]


def relation_hashes(structure: gr.Structure) -> frozenset[str]:
    names = [n.name for n in structure.nodes]
    return frozenset(dg.canonical_program_hash(gr.parse_expr(n.expr, names)) for n in structure.computed)


def value_signatures(structure: gr.Structure) -> tuple[frozenset[tuple[tuple[float, ...], float]], tuple[float, ...]]:
    signatures: set[tuple[tuple[float, ...], float]] = set()
    first: tuple[float, ...] = ()
    for index, instance in enumerate(structure.instances):
        shown = tuple(sorted(six(x) for x in r2.displayed_inputs(structure, index).values()))
        signatures.add((shown, six(dg.gold_for(structure, dict(instance)))))
        first = first or shown
    return frozenset(signatures), first


def entry_of(structure: gr.Structure, origin: str, cluster: str | None = None) -> Entry:
    signatures, first = value_signatures(structure)
    return Entry(structure.structure_id, origin, dg.structure_hash(structure), cluster or f"V2C-{structure.structure_id}",
                 relation_hashes(structure), mask_numbers(rv._assemble(structure, INSTANCE, "", "after_context")), signatures,
                 first)


@dataclass
class Pool:
    entries: list[Entry]
    v1_ids: frozenset[str]
    v1_rows: dict[str, dict[str, Any]]
    errors: list[str]

    @classmethod
    def build(cls, dataset: Path) -> Pool:
        rows = [json.loads(line) for line in dataset.read_text(encoding="utf-8").splitlines() if line.strip()]
        v1 = {f"{r['structure_id']}:{r['instance']}": r for r in rows}
        entries: list[Entry] = []
        errors: list[str] = []
        for sid in sorted({r["structure_id"] for r in rows}, key=sid_key):
            row = v1[f"{sid}:0"]
            entries.append(Entry(sid, "dataset_v1", row["symbolic_program_hash"], row["template_cluster_id"], frozenset(),
                                 mask_numbers(row["problem"]), frozenset(), ()))
        for module_name in LIB_MODULES:
            try:
                module = importlib.import_module(f"physmon.benchmark.v2.{module_name}")
                for factory in module.ALL:
                    entries.append(entry_of(factory(), f"library:{module_name}"))
            except Exception as exc:
                errors.append(f"{module_name}: {exc!r}")
        return cls(entries, frozenset(r["structure_id"] for r in rows), v1, errors)


_POOLS: dict[str, Pool] = {}


def pool_for(dataset: Path) -> Pool:
    key = str(dataset)
    if key not in _POOLS:
        _POOLS[key] = Pool.build(dataset)
    return _POOLS[key]


# --- detectors (pure functions; the tests plant duplicates through them) -------------------------------------------------------------

def detect_text(candidate: str, pool: list[Entry], own: str) -> dict[str, Any]:
    """Number-masked base-problem ratio against every pool entry except the candidate itself."""

    best_score, best = 0.0, None
    for entry in pool:
        if entry.sid == own or not entry.text:
            continue
        score = difflib.SequenceMatcher(a=candidate, b=entry.text, autojunk=False).ratio()
        if score > best_score:
            best_score, best = score, entry
    return {"nearest": None if best is None else best.sid, "origin": None if best is None else best.origin,
            "score": round(best_score, 4), "threshold": TEXT_FLAG, "flagged": best_score >= TEXT_FLAG}


def detect_program(program_hash: str, relations: frozenset[str], pool: list[Entry], own: str) -> dict[str, Any]:
    equal = sorted({e.sid for e in pool if e.sid != own and e.hash == program_hash})
    best_score, best = 0.0, None
    for entry in pool:
        if entry.sid == own or not entry.relations or not relations:
            continue
        score = len(relations & entry.relations) / len(relations | entry.relations)
        if score > best_score:
            best_score, best = score, entry
    return {"equal_program_hash_with": equal, "nearest_by_relation_set": None if best is None else best.sid,
            "relation_jaccard": round(best_score, 4), "threshold": JACCARD_FLAG, "flagged": best_score >= JACCARD_FLAG,
            "equal_hash": bool(equal)}


def detect_values(signatures: frozenset[tuple[tuple[float, ...], float]], inputs0: tuple[float, ...], pool: list[Entry],
                  own: str) -> dict[str, Any]:
    identical = sorted({e.sid for e in pool if e.sid != own and signatures & e.signatures})
    best_score, best = 0.0, None
    mine = Counter(inputs0)
    for entry in pool:
        if entry.sid == own or not entry.inputs0:
            continue
        theirs = Counter(entry.inputs0)
        union = sum((mine | theirs).values())
        score = sum((mine & theirs).values()) / union if union else 0.0
        if score > best_score:
            best_score, best = score, entry
    return {"identical_signature_with": identical, "nearest_by_input_values": None if best is None else best.sid,
            "input_multiset_jaccard": round(best_score, 4), "identical": bool(identical)}


def identity_checks(sid: str, kind: str, structure: gr.Structure, pool: Pool, admitted: list[Entry],
                    v1_row: dict[str, Any] | None) -> list[dict[str, Any]]:
    cluster = (v1_row or {}).get("template_cluster_id") or f"V2C-{sid}"
    candidate = entry_of(structure, "candidate", cluster)
    others = [*pool.entries, *admitted]
    in_v1 = sid in pool.v1_ids
    id_ok = in_v1 if kind != "NEW" else not in_v1
    same_hash = sorted({e.sid for e in others if e.sid != sid and e.hash == candidate.hash})
    same_cluster = sorted({e.sid for e in others if e.sid != sid and e.cluster == candidate.cluster})
    why = ""
    if same_hash:
        why += "symbolic_program_hash equal to " + ", ".join(same_hash) + "; "
    if same_cluster:
        why += "template_cluster_id equal to " + ", ".join(same_cluster) + "; "
    if not id_ok:
        why += "structure_id is not a dataset v1 structure" if kind != "NEW" else "structure_id already exists in dataset v1"
    checks = [mk("1.1", "unique template cluster and symbolic program", not same_hash and not same_cluster and id_ok, why,
                 template_cluster_id=candidate.cluster, symbolic_program_hash=candidate.hash,
                 compared_with=f"dataset v1 ({len(pool.v1_ids)} structures), {len(LIB_MODULES)} library modules, and "
                               f"{len(admitted)} previously admitted candidates; the structure's own id is excluded",
                 pool_load_errors=pool.errors,
                 not_checkable="DECOY-v1 and the EPC pool: no machine-readable structure pool exists in the repository",
                 duplicates_by_hash=same_hash, duplicates_by_cluster=same_cluster)]
    text = detect_text(candidate.text, others, sid)
    program = detect_program(candidate.hash, candidate.relations, others, sid)
    values = detect_values(candidate.signatures, candidate.inputs0, others, sid)
    checks.append(mk("1.2.text", "text overlap (number-masked base problem, difflib ratio)", not text["flagged"],
                     f"nearest {text['nearest']} at {text['score']} >= {TEXT_FLAG}", **text))
    program_why = (f"equal program hash with {program['equal_program_hash_with']}; " if program["equal_hash"] else "") + (
        f"nearest {program['nearest_by_relation_set']} at Jaccard {program['relation_jaccard']}")
    checks.append(mk("1.2.program", "program overlap (equal canonical hash; relation-set Jaccard)",
                     not program["equal_hash"] and not program["flagged"], program_why, **program))
    checks.append(mk("1.2.value_signature", "value signature (identical sorted displayed inputs and gold)", not values["identical"],
                     f"identical with {values['identical_signature_with']}", **values))
    return checks


# --- provenance, base problem ----------------------------------------------------------------------------------------------------------

def git_state() -> dict[str, Any]:
    try:
        head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True, timeout=20)
        dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=REPO_ROOT, capture_output=True,
                               text=True, timeout=20)
        return {"commit": head.stdout.strip() or None, "tracked_files_modified": bool(dirty.stdout.strip())}
    except Exception as exc:
        return {"commit": None, "error": repr(exc)}


def spec_hash(spec: r2.RoleSpecV2) -> str:
    return hashlib.sha256(json.dumps(dataclasses.asdict(spec), sort_keys=True, default=str).encode("utf-8")).hexdigest()


def provenance_check(spec: r2.RoleSpecV2, source: Source, build_date: str, git: dict[str, Any]) -> dict[str, Any]:
    fields = {"created_by": "agent" if spec.author.lower().startswith("agent") else spec.author, "author_agent": spec.author,
              "generator": GENERATOR, "generator_version": GENERATOR_VERSION, "git": git, "spec_module": source.module_name,
              "spec_version": spec.version, "spec_hash": spec_hash(spec), "date": build_date}
    missing = sorted(k for k in ("created_by", "author_agent", "generator_version", "spec_hash", "date") if not fields[k])
    return mk("1.3", "provenance fields", not missing, "missing: " + ", ".join(missing), **fields,
              consistency_check="dataset-level: scripts/check_provenance_consistency.py on the README (manifest.json)")


def base_problem_check(kind: str, structure: gr.Structure, spec: r2.RoleSpecV2, v1_row: dict[str, Any] | None) -> dict[str, Any]:
    """3.4 part: the base problem is the original problem plus the scene clause, with the gold unchanged."""

    clause = spec.scene_clause
    rendered = rv._assemble(structure, INSTANCE, "", "after_context")
    gold = dg.gold_for(structure, dict(structure.instances[INSTANCE]))
    if kind != "NEW":
        name = "base problem = v1 problem + scene clause, gold unchanged"
        if v1_row is None:
            return mk("3.4.base", name, False, "no dataset v1 row for this structure, so the base problem cannot be compared")
        expected = v1_row["problem"].replace("\n\n", f" {clause}\n\n", 1)
        gold_v1 = v1_row["gold_answer"]["value"]
        same_gold = abs(gold - gold_v1) <= 1e-12 * max(abs(gold), abs(gold_v1))
        return mk("3.4.base", name, rendered == expected and same_gold,
                  "the rendered base problem differs from the v1 problem with the clause inserted" if rendered != expected
                  else "the base gold differs from the v1 gold", base_problem_equal=rendered == expected, gold=gold,
                  gold_v1=gold_v1)
    name = "rendered base problem + scene clause, gold from the certifier"
    context = structure.render.context
    if not clause or not context.endswith(clause):
        return mk("3.4.base", name, False, "the scene clause is not the end of the base context")
    original = dataclasses.replace(structure, render=dataclasses.replace(
        structure.render, context=context[: -len(clause)].rstrip()))
    expected = rv._assemble(original, INSTANCE, "", "after_context").replace("\n\n", f" {clause}\n\n", 1)
    si = rv.display_inputs_si(original, INSTANCE)
    graph_gold = gr.target_value_display(original, si)
    solver_gold = dm.from_si(original.solver(*gr.solver_inputs(original, si)), original.render.target_unit)
    solver_tol = 10 * max(original.solver_rel_tol, 1e-9)  # the certifier's own route-agreement tolerance
    same_gold = abs(gold - graph_gold) <= 1e-12 * max(abs(gold), abs(graph_gold)) and abs(gold - solver_gold) <= solver_tol * max(
        abs(gold), abs(solver_gold))
    return mk("3.4.base", name, rendered == expected and same_gold,
              "the base problem is not the original plus the clause" if rendered != expected else "the base gold changed",
              base_problem_equal=rendered == expected, gold=gold, gold_original_graph=graph_gold, gold_independent_solver=solver_gold)


# --- wording checks beyond the certificate: article agreement and pair distinctness (3.7, 3.8) ---------------------------------------------

ARTICLE_NUMBER = re.compile(r"(?<![\w'])([aA])\s+(\d+)")


def vowel_sound_number(integer_part: str) -> bool:
    """True when the integer is read with a vowel sound: eight, eighty, eight hundred, eleven, eighteen (and thousands of them)."""

    return integer_part[0] == "8" or (len(integer_part) % 3 == 2 and integer_part[:2] in ("11", "18"))


def article_violations(sentences: list[str]) -> list[str]:
    """Sentences with 'a' or 'A' directly before a number that is read with a vowel sound."""

    return [t for t in sentences if any(vowel_sound_number(m.group(2)) for m in ARTICLE_NUMBER.finditer(t))]


def rendered_sentences(spec: r2.RoleSpecV2) -> list[str]:
    """Every R, D, N, C, K and K_out sentence at every study and held-out value (the cells emit only the study values)."""

    out: list[str] = []
    for pair in spec.pairs:
        out.append(r2.pair_sentence(pair, "D", None, spec.unit))
        for value in (*spec.values, *spec.heldout_values):
            out += [r2.pair_sentence(pair, "R", value, spec.unit), r2.pair_sentence(pair, "D", value, spec.unit)]
    for wrapped, extra in ((spec.cancelling, ()), (spec.conditional, spec.conditional.k_out.values if spec.conditional else ())):
        if wrapped is None:
            continue
        sub = wrapped.spec
        for value in (*sub.values, *wrapped.heldout_values, *extra):
            out += [rv._sentence(sub.frame, value, sub.unit, p.relation, sub.nonnumeric_fill) for p in sub.phrasings]
    return out


FUNCTION_WORDS = frozenset(
    "a an the is was were are be been being also then and or of on to in it its that this by with at for as had has have did does do "
    "there here which who after before".split())


def frame_tokens(sentence: str, attach: str, value: float, unit: str, keep_function_words: bool) -> list[str]:
    """Lower-case word sequence of a sentence with the attachment phrase, the numeral and the unit removed ('also' never counts)."""

    text = sentence.replace(attach, " ").replace(rv._fmt(value), " ").replace(dg.display_unit(unit), " ")
    words = [w for w in re.findall(r"[a-z]+", text.lower()) if w != "also"]
    return words if keep_function_words else [w for w in words if w not in FUNCTION_WORDS]


def pair_word_difference(spec: r2.RoleSpecV2, role: str) -> dict[str, Any]:
    """The pair-0 and pair-1 frames of a role (R or D) after removing the attachment, numeral and unit."""

    value = spec.values[len(spec.values) // 2]
    seqs, contents = [], []
    for p in spec.pairs[:2]:
        sentence, attach = r2.pair_sentence(p, role, value, spec.unit), p.r_attach if role == "R" else p.d_attach
        seqs.append(frame_tokens(sentence, attach, value, spec.unit, True))
        contents.append(set(frame_tokens(sentence, attach, value, spec.unit, False)))
    return {"frames_differ": seqs[0] != seqs[1], "frame_pair0": " ".join(seqs[0]), "frame_pair1": " ".join(seqs[1]),
            "content_words_only_pair0": sorted(contents[0] - contents[1]), "content_words_only_pair1": sorted(contents[1] - contents[0]),
            "information_only": "the number of differing content words is recorded, not required"}


def wording_checks(spec: r2.RoleSpecV2) -> list[dict[str, Any]]:
    bad = article_violations(rendered_sentences(spec))
    same: list[str] = []
    for value in (*spec.values, *spec.heldout_values):
        p0, p1 = spec.pairs[0], spec.pairs[1]
        for role in ("R", "D"):
            if r2.pair_sentence(p0, role, value, spec.unit) == r2.pair_sentence(p1, role, value, spec.unit):
                same.append(f"{role.lower()}0 = {role.lower()}1 at {value}")
    differences = {role: pair_word_difference(spec, role) for role in ("R", "D")}
    close = [f"{role.lower()}0 and {role.lower()}1 frames identical after removing the attachment ('also' ignored)"
             for role, d in differences.items() if not d["frames_differ"]]
    return [mk("3.7", "article agreement: no 'a' before a number read with a vowel sound (8, 11, 18, 80-89, 800-899, ...)", not bad,
               f"{len(bad)} sentence(s): {bad[:3]}", violations=bad[:10]),
            mk("3.8", "pair distinctness: r0 != r1 and d0 != d1 at every study and held-out value, and the pair-0 frame differs from "
                      "the pair-1 frame after removing the attachment ('also'-only differences fail; tense or order pass)",
               not same and not close, "; ".join([*same[:4], *close]), identical=same, word_difference=differences)]


# --- the planted mutation tests (2.6) ------------------------------------------------------------------------------------------------------

def mutation_tests(structure: gr.Structure, spec: r2.RoleSpecV2) -> list[dict[str, Any]]:
    """Each planted defect must make `certify_v2` fail; a mutation that still certifies is a hole in the certificate (P3.3)."""

    mutants: list[tuple[str, str, gr.Structure, r2.RoleSpecV2 | None]] = []
    n = len(spec.values)
    op = spec.relevant.op
    if op in ("add", "subtract", "scale"):
        tiny = tuple((1.0 if op == "scale" else 0.0) + 1e-9 * (k + 1) for k in range(n))
        mutants.append(("identity_values", "R values too close to the identity to move the answer", structure,
                        dataclasses.replace(spec, values=tiny, heldout_values=tuple(t * 1.5 for t in tiny))))
    if n >= 3:
        mutants.append(("repeated_values", "two identical study values", structure,
                        dataclasses.replace(spec, values=(spec.values[0], spec.values[0], *spec.values[2:]))))
    mutants.append(("broken_solver", "independent solver route 1% off", dataclasses.replace(
        structure, solver=lambda *xs: 1.01 * structure.solver(*xs)), None))
    if spec.cancelling is not None:
        c = spec.cancelling
        mutants.append(("broken_cancellation", "C expression that no longer cancels q", structure, dataclasses.replace(
            spec, cancelling=dataclasses.replace(c, spec=dataclasses.replace(c.spec, expr_with_q=f"({c.spec.expr_with_q})*(1+q)")))))
    if spec.conditional is not None:
        k = spec.conditional
        cr = k.spec.counter_regime_value
        mutants.append(("out_of_regime_values", "K values taken from outside the regime", structure, dataclasses.replace(
            spec, conditional=dataclasses.replace(k, spec=dataclasses.replace(k.spec, values=(cr, cr * 1.1, cr * 1.2))))))
    p0, p1 = spec.pairs[0], spec.pairs[1]
    mutants.append(("marker_word_in_d", "a marker word in a D phrasing", structure, dataclasses.replace(
        spec, pairs=(dataclasses.replace(p0, d_attach=p0.d_attach + " unconnected"), p1))))
    mutants.append(("reversal_in_d", "a D phrasing that undoes a change", structure, dataclasses.replace(
        spec, pairs=(p0, dataclasses.replace(p1, d_attach=p1.d_attach + " and taken out again")))))
    mutants.append(("digit_in_scene_clause", "a number in the scene clause", structure, dataclasses.replace(
        spec, scene_clause=spec.scene_clause[:-1] + " 5.")))
    report = []
    for mutant_id, note, mutated_structure, mutated_spec in mutants:
        try:
            cert = r2.certify_v2(mutated_structure, mutated_spec or spec)
            caught, failed, raised = not cert["passed"], cert["failed"], None
        except Exception as exc:  # the certifier raising on a planted defect still keeps the defect out
            caught, failed, raised = True, [], repr(exc)
        report.append({"mutation": mutant_id, "note": note, "caught": caught, "failed_checks": failed[:6], "raised": raised})
    return report


# --- cells, traces and the per-structure build ------------------------------------------------------------------------------------------------

def build_rows(source: Source, sid: str, structure: gr.Structure, spec: r2.RoleSpecV2, dataset: Path, plans: dict[str, Any],
               version: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any] | None, str | None]:
    """The cells, traces and certificate record of one structure from the M0 v2.1 builder (`s192`), or an error text."""

    s192.roles_m0v21 = SimpleNamespace(ROLE_SPECS={sid: spec}, structure=lambda _sid: structure)
    s192.VERSION = version
    s192.t2 = SimpleNamespace(plans=lambda: plans, trace_for_role_cell=t2.trace_for_role_cell,
                              trace_for_support=t2.trace_for_support)
    terms = source.target_terms
    if sid in terms:
        s192.s188.target_terms = lambda structure_id: {"target_phrases": list(terms[structure_id][0]),
                                                      "target_symbols": list(terms[structure_id][1])}
    else:  # the M0 builder's own table (rows of M0 v2.2 stay byte-identical to m0_v22)
        s192.s188.target_terms = ORIGINAL_TARGET_TERMS
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "build"
        try:
            manifest = s192.build(out, dataset)
        except SystemExit as exc:
            return [], [], None, f"build self-check failed: {exc.code}"
        rows = [json.loads(x) for x in (out / "cells.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
        traces = [json.loads(x) for x in (out / "traces.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
        record = json.loads((out / "certificates.json").read_text(encoding="utf-8")).get(sid)
    if manifest["excluded"]:
        return [], [], record, "the builder excluded the structure: " + ", ".join(manifest["excluded"][0]["failed"])
    return rows, traces, record, None


def separation_check(cert: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    """2.5: every misuse value and the placebo is separated from the gold at two or more of three study values."""

    degenerate = set((cert["checks"].get("degenerate_misuse_foils", {}).get("detail") or {}).get("names", []))
    separation: dict[str, dict[str, int]] = {}
    foil_pairs: dict[str, list[str]] = {}
    low: list[str] = []
    for stratum in ("R", "D", "C", "K"):
        cells = [r for r in rows if r["stratum"] == stratum and r["family"] == "role_by_value" and not r["heldout"]]
        if not cells:
            continue
        phrasing = sorted({r["phrasing_id"] for r in cells})[0]
        series = sorted((r for r in cells if r["phrasing_id"] == phrasing), key=lambda r: r["value_index"])
        counts: Counter = Counter()
        inseparable: Counter = Counter()
        names: set[str] = {"placebo"} if stratum == "R" else set()
        for r in series:
            named = {"gold": r["gold_value"], **{k: v for k, v in r["foils"].items() if v is not None}}
            if r.get("placebo") is not None:
                named["placebo"] = r["placebo"]
            names |= set(r["foils"])
            unsep = rv._not_separated(named)
            for name in named:
                if name != "gold" and ("gold", name) not in unsep and (name, "gold") not in unsep:
                    counts[name] += 1
            for a, b in unsep:
                if "gold" not in (a, b):
                    inseparable[f"{a}~{b}"] += 1
        needed = min(2, len(series))
        separation[stratum] = dict(sorted(counts.items()))
        foil_pairs[stratum] = sorted(p for p, c in inseparable.items() if len(series) - c < needed)
        low += [f"{stratum}:{name}" for name in sorted(names) if counts[name] < needed and name not in degenerate]
    certified = all(cert["checks"].get(n, {}).get("ok") is True for n in ("no_confounded_foils_except_degenerate",
                                                                          "foils_not_equal_to_other_cells_golds"))
    return mk("2.5", "misuse curves and placebo separated from the gold at 2+ of 3 study values", certified and not low,
              ("foils below 2 of 3: " + ", ".join(low)) if low else "certify_v2 foil checks failed",
              separated_study_values_per_foil=separation, degenerate_misuse_foils=sorted(degenerate),
              inseparable_misuse_pairs_recorded_as_confounded=foil_pairs)


def cell_checks(spec: r2.RoleSpecV2, cert: dict[str, Any], rows: list[dict[str, Any]],
                traces: list[dict[str, Any]]) -> list[dict[str, Any]]:
    checks = [separation_check(cert, rows)]
    by_job = {t["job_id"]: t for t in traces}
    job_ids = {r["job_id"] for r in rows}
    missing, extra = sorted(job_ids - set(by_job)), sorted(set(by_job) - job_ids)
    wrong = []
    for r in rows:
        trace = by_job.get(r["job_id"])
        if trace is None:
            continue
        gold = trace["gold_trace"]["gold_answer"]["value"]
        last = trace["gold_trace"]["steps"][-1]
        tol = 1e-9 * max(abs(gold), abs(r["gold_value"]))
        if abs(gold - r["gold_value"]) > tol or last.get("kind") != "answer" or abs(last["value"] - r["gold_value"]) > tol:
            wrong.append(r["job_id"])
    checks.append(mk("2.7", "gold trace for every cell, last value equals the cell gold (1e-9)", not (missing or extra or wrong),
                     f"{len(missing)} cells without a trace, {len(extra)} traces without a cell, {len(wrong)} wrong last values",
                     n_cells=len(rows), n_traces=len(traces), cells_without_trace=missing[:5], wrong_last_value=wrong[:5]))
    bad_terms = [r["job_id"] for r in rows if not r.get("target_symbols") or not r.get("target_phrases")]
    checks.append(mk("2.7b", "target naming (target_symbols and target_phrases on every row)", not bad_terms,
                     f"{len(bad_terms)} rows without target terms", n_rows=len(rows), rows_without=bad_terms[:5]))
    absent = [r["job_id"] for r in rows if spec.scene_clause not in r["prompt"]]
    checks.append(mk("3.2.scene", "the scene clause is in every cell's base context", not absent, f"{len(absent)} rows without it",
                     n_rows=len(rows)))
    failures41: list[dict[str, Any]] = []
    failures42: list[dict[str, Any]] = []
    alt_unit: list[dict[str, Any]] = []
    n_checks = 0
    for r in rows:
        result = s194.dry_run_cell(r)
        n_checks += sum(result["checks"].values())
        for f in result["failures"]:
            entry = {k: f[k] for k in ("cell", "check", "view", "text", "grade")}
            if f["check"].startswith("gold_alt_unit"):
                alt_unit.append(entry)  # a grader finding on extreme unit rewrites, not one of the three declared answer formats
            else:
                (failures42 if f["check"].startswith("foil:") else failures41).append(entry)
    checks.append(mk("4.1", "grading dry run: the gold in every declared format grades CORRECT under every view", not failures41,
                     f"{len(failures41)} failures", n_cells=len(rows), n_checks_run_all_kinds=n_checks, failures=failures41[:8],
                     alt_unit_findings_not_blocking={"count": len(alt_unit), "examples": alt_unit[:4], "note": (
                         "s194 also rewrites the gold in every other unit of its dimension (up to 17-digit integers); the standard "
                         "requires the three declared answer formats, so these are recorded, not blocking")}))
    checks.append(mk("4.2", "foil dry run: every misuse value and the placebo grade NOT CORRECT under the primary view",
                     not failures42, f"{len(failures42)} failures", failures=failures42[:8]))
    return checks


def certificate_checks(sid: str, source: Source, spec: r2.RoleSpecV2, structure: gr.Structure, cert: dict[str, Any],
                       graph: dict[str, Any], mutations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    ncheck = cert.get("numeric", {}).get("checks", {})
    failed_graph = [c["name"] for c in graph["checks"] if not c["passed"]]
    checks.append(mk("2.1", "typed dependency graph; dimension check on every relation; solver route; prompt matches graph",
                     graph["status"] == "SOLVER_CERTIFIED", "certify.certify failed: " + ", ".join(failed_graph),
                     status=graph["status"], checks={c["name"]: c["passed"] for c in graph["checks"]},
                     n_nodes=len(structure.nodes), units={n.name: n.unit for n in structure.nodes}))
    seps: list[float] = []
    tokens_differ = True
    for p in ncheck.get("per_instance", []):
        for yr in p["y_r"].values():
            seps.append(abs(yr - p["y_d"]) / max(abs(yr), abs(p["y_d"])))
            tokens_differ &= f"{yr:.4g}" != f"{p['y_d']:.4g}"
    rd = all(ncheck.get(n, {}).get("ok") is True for n in ("routes_agree", "r_separated_from_d", "r_values_distinct"))
    counts_ok = len(spec.values) >= 3 and len(spec.heldout_values) >= 2
    checks.append(mk("2.2", "R and D cells: certified at 3 study and 2 held-out values; R separated from D; answer tokens differ",
                     rd and counts_ok and tokens_differ and bool(seps) and min(seps) > rv.LOOSEST_REL_TOL,
                     "R/D certificate failed or too few values", n_study_values=len(spec.values),
                     n_heldout_values=len(spec.heldout_values), min_relative_r_d_separation=min(seps) if seps else None,
                     loosest_tolerance=rv.LOOSEST_REL_TOL, answer_tokens_differ_4sf=tokens_differ,
                     per_instance_checks={n: ncheck.get(n, {}).get("ok") for n in (
                         "routes_agree", "r_separated_from_d", "r_values_distinct")}))
    if spec.cancelling is not None:
        c = ncheck.get("cancelling", {})
        fields = ("q_present_unsimplified", "derivative_zero", "numeric_invariance", "wrong_law_separated_at_2_of_3",
                  "intermediate_relations_listed", "expr_dimension_ok")
        got = {f: c.get(f) for f in fields}
        got["heldout_two_certified"] = cert["checks"].get("c_heldout_two_certified", {}).get("ok")
        got["familiarity_tag"] = cert["checks"].get("c_familiarity_tag", {}).get("ok")
        bad = sorted(k for k, v in got.items() if v is not True)
        checks.append(mk("2.3", "C cells: symbolic cancellation (dy/dq = 0) and numeric invariance", not bad,
                         "failed: " + ", ".join(bad), feasible=True, certificate=got,
                         relations_containing_q=list(spec.cancelling.spec.intermediate_relations)))
    else:
        reason = source.no_c.get(sid, "")
        recorded = len(reason) >= MIN_REASON or source.kind == "M0"
        checks.append(mk("2.3", "C cells (not feasible: reason recorded)", recorded, "no C cell and no NO_C reason on record",
                         feasible=False, reason=reason or "not recorded (the M0 specs carry no NO_C table)"))
    if spec.conditional is not None:
        k = ncheck.get("conditional", {})
        got = {f: k.get(f) for f in ("predicate_holds_at_all_values", "counter_regime_value_breaks_predicate",
                                     "out_of_regime_law_separated", "predicate_dimension_ok", "out_of_regime_dimension_ok")}
        got["heldout_two_certified"] = cert["checks"].get("k_heldout_two_certified", {}).get("ok")
        got["k_out_reason_recorded"] = cert["checks"].get("k_out_judged", {}).get("ok")
        ko = spec.conditional.k_out
        ko_name = "k_out_predicate_false_and_answer_moves" if ko.feasible else "k_out_infeasible_has_no_values"
        got[ko_name] = cert["checks"].get(ko_name, {}).get("ok")
        bad = sorted(name for name, v in got.items() if v is not True)
        checks.append(mk("2.4", "K cells: regime predicate true at every study value; counter-regime value; K_out feasibility",
                         not bad, "failed: " + ", ".join(bad), feasible=True, certificate=got,
                         predicate=spec.conditional.spec.predicate, counter_regime_value=spec.conditional.spec.counter_regime_value,
                         k_out_feasible=ko.feasible, k_out_reason=ko.reason))
    else:
        reason = source.no_k.get(sid, "")
        recorded = len(reason) >= MIN_REASON or source.kind == "M0"
        checks.append(mk("2.4", "K cells (not feasible: reason recorded)", recorded, "no K cell and no NO_K reason on record",
                         feasible=False, reason=reason or "not recorded (the M0 specs carry no NO_K table)"))
    uncaught = [m["mutation"] for m in mutations if not m["caught"]]
    checks.append(mk("2.6", "planted mutations rejected by the certifier (role-spec mutations; broken cancellation, out-of-regime K)",
                     not uncaught, "mutations that still certified: " + ", ".join(uncaught), mutations=mutations,
                     graph_mutation_report="not run: certify.mutation_report costs about 18 s per structure"))
    complete = r2.complete(spec, cert)
    checks.append(mk("2.8", "feasibility: complete (R and D at three values in two phrasing pairs); infeasible strata recorded",
                     complete, "the role certificate failed: " + ", ".join(cert["failed"]), complete=complete,
                     failed_certificate_checks=cert["failed"]))
    pairs = cert.get("pairs", [])
    checks.append(group_check("3.1", "phrasing pairs: same frame, numeral and unit; word counts within 3", cert,
                              ("exactly_two_pairs", "same_frame_numeral_unit_or_declared_unmatched", "word_count_ok",
                               "frame_mismatch_reason_ok", "numerals_ok", "attach_has_no_digit"),
                              pairs=[{"pair_id": p["pair_id"], "token_difference": p["token_difference"],
                                      "word_counts": p["word_counts"], "frame_matched": p["pair_frame_matched"]} for p in pairs]))
    checks.append(group_check("3.2", "D kinds: co-present and other event; D not on the target; rationale; scene clause", cert,
                              ("d_kinds", "d_not_on_target", "reversal_free", "d_rationale_ok", "scene_clause_ok",
                               "scene_clause_in_base_context", "d0_refers_to_scene_object", "remoteness_free_d"),
                              d_kinds=[p["d_kind"] for p in pairs], d_rationales=[p["d_rationale"] for p in pairs],
                              scene_clause=spec.scene_clause))
    checks.append(group_check("3.3", "lexicons: marker free and consequence free (D, N, R, C, K sentences)", cert,
                              ("consequence_free", "marker_free"),
                              ("cancelling_consequence_free", "cancelling_marker_free", "conditional_consequence_free",
                               "conditional_marker_free")))
    checks.append(group_check("3.4", "conditions untouched: stated conditions occur in the base text", cert,
                              ("conditions_listed", "conditions_in_base_text"),
                              conditions_preserved=[p["conditions_preserved"] for p in pairs]))
    study = [h for key, series in cert.get("hygiene", {}).items() if "heldout" not in key for h in series]
    checks.append(group_check("3.5", "value hygiene: no study value equals a displayed input; digit overlap recorded", cert,
                              ("value_hygiene", "heldout_value_hygiene"),
                              max_digit_overlap_with_inputs=max((h["digit_overlap_with_inputs"] for h in study), default=None),
                              max_digit_overlap_with_gold=max((h["digit_overlap_with_gold"] for h in study), default=None)))
    return checks


# --- one structure ------------------------------------------------------------------------------------------------------------------------

@dataclass
class Result:
    sid: str
    source: Source
    status: str = REJECTED
    checks: list[dict[str, Any]] = field(default_factory=list)
    rows: list[dict[str, Any]] = field(default_factory=list)
    traces: list[dict[str, Any]] = field(default_factory=list)
    certificate: dict[str, Any] = field(default_factory=dict)
    summary: dict[str, Any] = field(default_factory=dict)
    entry: Entry | None = None
    file_stem: str = ""

    @property
    def failed(self) -> list[dict[str, Any]]:
        return [c for c in self.checks if c["status"] == FAIL]


def spec_summary(source: Source, sid: str, structure: gr.Structure, spec: r2.RoleSpecV2, spec_raw: r2.RoleSpecV2,
                 v1_row: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "title": structure.title, "domain": v1_row["domain"] if v1_row else structure.domain, "law_family": structure.law_family,
        "level": (v1_row or {}).get("level") if source.kind != "NEW" else source.levels.get(sid),
        "n_computed_nodes": len(structure.computed), "quantity_phrase": spec.quantity_phrase, "unit": spec.unit,
        "values": list(spec.values), "heldout_values": list(spec.heldout_values), "scene_clause": spec.scene_clause,
        "spec_version": spec_raw.version, "has_c": spec.cancelling is not None, "has_k": spec.conditional is not None,
        "k_out_feasible": None if spec.conditional is None else spec.conditional.k_out.feasible,
        "c_familiarity": None if spec.cancelling is None else spec.cancelling.familiarity,
        "no_c_reason": source.no_c.get(sid), "no_k_reason": source.no_k.get(sid),
        "cert_version": source.cert_version or spec_raw.version}


def evaluate(source: Source, sid: str, pool: Pool, admitted: list[Entry], dataset: Path, plans: dict[str, Any], build_date: str,
             git: dict[str, Any]) -> Result:
    result = Result(sid, source, file_stem=sid)
    kind = source.kind
    v1_row = pool.v1_rows.get(f"{sid}:{INSTANCE}")
    try:
        structure = source.structure(sid)
        spec_raw = source.specs[sid]
    except Exception as exc:
        result.checks.append(mk("0", "structure and spec load", False, f"structure() raised {exc!r}"))
        return result
    # certify_v2 applies its strict rule set only when the version is "v2.1": the spec (or its module's CERT_VERSION) must say so
    cert_version = source.cert_version or spec_raw.version
    spec = dataclasses.replace(spec_raw, version=cert_version) if cert_version != spec_raw.version else spec_raw
    result.summary = spec_summary(source, sid, structure, spec, spec_raw, v1_row)
    try:
        result.checks.append(mk("3.0", "strict rule set: the spec is certified under version v2.1", cert_version == r2.VERSION_V21,
                                f"cert_version {cert_version!r}: certify_v2 would skip the reversal, co-present, time-anchor and "
                                "scene-clause checks", cert_version=cert_version, spec_version=spec_raw.version,
                                module_cert_version=source.cert_version))
        result.checks += identity_checks(sid, kind, structure, pool, admitted, v1_row)
        result.checks.append(provenance_check(spec_raw, source, build_date, git))
        cert = r2.certify_v2(structure, spec)
        graph = certify.certify(structure)
        mutations = mutation_tests(structure, spec)
        result.certificate = {"role_certificate": cert, "graph_certificate": {
            "status": graph["status"], "checks": graph["checks"], "program_hash": graph.get("program_hash")},
            "mutation_tests": mutations}
        result.checks += certificate_checks(sid, source, spec, structure, cert, graph, mutations)
        result.checks += wording_checks(spec)
        result.checks.append(base_problem_check(kind, structure, spec, v1_row))
        target_ok = sid in source.target_terms or (kind == "M0" and sid in roles_m0v2.TARGET_TERMS)
        if not target_ok:
            result.checks.append(mk("2.7b", "target naming", False, "no TARGET_TERMS entry for this structure"))
        blocked = [c["id"] for c in result.checks if c["id"] in ("2.8", "3.4.base") and c["status"] == FAIL]
        blocked += [] if target_ok else ["2.7b"]
        if blocked:
            for cid, name in (("2.5", "misuse separation"), ("2.7", "gold traces"), ("3.2.scene", "scene clause in every cell"),
                              ("4.1", "grading dry run"), ("4.2", "foil dry run")):
                result.checks.append(mk(cid, name, None, "no cells were built: " + ", ".join(blocked)))
        else:
            version = m0_version(source.module_name) if kind == "M0" else DATASET_ID
            rows, traces, record, error = build_rows(source, sid, structure, spec, dataset, plans, version)
            if record is not None:
                result.certificate["builder_record"] = {k: v for k, v in record.items() if k != "role_certificate"}
            if error:
                result.checks.append(mk("B", "cell and trace build", False, error))
                for cid in ("2.5", "2.7", "3.2.scene", "4.1", "4.2"):
                    result.checks.append(mk(cid, cid, None, "the cell build failed"))
            else:
                result.checks.append(mk("B", "cell and trace build (rendering, scene clause, base problem self-checks)", True,
                                        n_cells=len(rows), n_traces=len(traces)))
                result.checks += cell_checks(spec, cert, rows, traces)
                result.rows, result.traces = rows, traces
        tag = None if spec.cancelling is None else spec.cancelling.familiarity
        result.checks.append(mk("6.2", "familiarity tag of the C quantity (the share across the set is in composition.json)",
                                spec.cancelling is None or tag in r2.FAMILIARITY, "invalid familiarity tag", tag=tag,
                                reason=None if spec.cancelling is None else spec.cancelling.familiarity_reason))
        result.entry = entry_of(structure, "admitted_candidate", (v1_row or {}).get("template_cluster_id"))
    except Exception as exc:  # a failing structure must be REJECTED with its evidence, never crash the build
        result.checks.append(mk("X", "internal error while checking", False, f"{exc!r}", traceback=traceback.format_exc()[-1500:]))
    if result.failed or not result.rows:
        if not result.failed:
            result.checks.append(mk("B", "cell and trace build", False, "no cells were produced"))
        result.status, result.rows, result.traces = REJECTED, [], []
    else:
        result.status = ADMITTED
    return result


# --- composition (6.2, 6.3) ---------------------------------------------------------------------------------------------------------------

DOMAIN_SYNONYMS = {"nuclear": "nuclear physics", "atomic": "atomic physics", "relativity": "special relativity",
                   "statistical mechanics": "statistical physics", "solid state physics": "solid state"}


def normalize_domain(label: str) -> str:
    """One canonical domain label: lower case, underscores and hyphens as spaces, then the synonym map."""

    text = re.sub(r"[\s_-]+", " ", (label or "").strip().lower())
    return DOMAIN_SYNONYMS.get(text, text)


def normalize_level(label: str | None) -> str | None:
    """One canonical level label: 'upper-university', 'upper university' and 'upper_university' are the same."""

    return None if not label else re.sub(r"[\s-]+", "_", label.strip().lower())


def composition(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Dataset-level checks over admitted structures; each record has domain, level, n_computed, kind, has_c, has_k, familiarity."""

    applied = {r["domain"]: normalize_domain(r["domain"]) for r in records if normalize_domain(r["domain"]) != r["domain"]}
    levels_applied = {r["level"]: normalize_level(r["level"]) for r in records if r.get("level") and normalize_level(r["level"]) != r["level"]}
    records = [{**r, "domain": normalize_domain(r["domain"]), "level": normalize_level(r.get("level"))} for r in records]
    n = len(records)
    domains = Counter(r["domain"] for r in records)
    top = max(domains.values(), default=0)
    advanced = [r for r in records if r.get("level") == UPPER_LEVEL or r.get("n_computed", 0) >= MULTI_STEP_NODES]
    new = [r for r in records if r["kind"] == "NEW"]
    with_c = [r for r in records if r["has_c"]]
    famous = [r for r in with_c if r.get("familiarity") == "famous"]

    def share(part: int, whole: int) -> float | None:
        return None if whole == 0 else round(part / whole, 4)

    c_share, k_share = share(sum(r["has_c"] for r in new), len(new)), share(sum(r["has_k"] for r in new), len(new))
    adv_share, fam_share, top_share = share(len(advanced), n), share(len(famous), len(with_c)), share(top, n)
    return {
        "label_normalisation": {
            "domain_rule": "lower case; underscores and hyphens read as spaces; synonyms mapped (DOMAIN_SYNONYMS)",
            "domain_synonyms": DOMAIN_SYNONYMS, "domain_labels_changed": dict(sorted(applied.items())),
            "level_rule": "lower case; hyphens and spaces read as underscores", "level_labels_changed": dict(sorted(levels_applied.items()))},
        "n_admitted_structures": n, "by_kind": dict(sorted(Counter(r["kind"] for r in records).items())),
        "6.3": {
            "domains": dict(sorted(domains.items())), "n_domains": len(domains), "largest_domain_share": top_share,
            "domains_ok": len(domains) >= 10 and (top_share or 0) <= 0.25,
            "upper_university_or_multi_step": {"count": len(advanced), "share": adv_share, "rule": (
                f"level == {UPPER_LEVEL} or at least {MULTI_STEP_NODES} computed relations"), "ok": (adv_share or 0) >= 0.2},
            "new_structures": len(new), "c_feasible_share_of_new": c_share, "c_ok": (c_share or 0) >= 0.5,
            "k_feasible_share_of_new": k_share, "k_ok": (k_share or 0) >= 0.3,
            "note": "reported, not forced (admission standard 6.3)"},
        "6.2": {"c_quantities": len(with_c), "famous": len(famous), "famous_share": fam_share,
                "by_tag": dict(sorted(Counter(r.get("familiarity") for r in with_c).items())), "ok": (fam_share or 0) <= 0.5,
                "note": "at most half famous across the admitted set at each milestone"}}


# --- build ---------------------------------------------------------------------------------------------------------------------------------------

def panel_record(result: Result) -> dict[str, Any]:
    if result.source.kind == "M0" and result.source.module_name == "roles_m0v25" and result.sid in M0_PANEL_RUN:
        run = M0_PANEL_RUN[result.sid]
        return {"status": "ADMITTED", "judges": "two-judge panel (Claude and GPT, prompt v3)",
                "records": [f"{PANEL_DIRS}/{run}/runs/score_two_judges/"],
                "note": "M0 v2.5 structure reviewed by the panel; not re-packaged"}
    return {"status": PENDING, "admission_5.x": PENDING, "naturalness_6.1": PENDING,
            "packets": "scripts/v2/s199_m250_panel_packets.py"}


def order_key(item: tuple[Source, str]) -> tuple[int, int, str]:
    source, sid = item
    return (KINDS.index(source.kind), *sid_key(sid))


def admission_record(res: Result) -> dict[str, Any]:
    base = {"M0": "dataset v1 instance 0 problem + scene clause (M0)",
            "UPGRADED_V1": "dataset v1 instance 0 problem + scene clause",
            "NEW": "rendered base problem + scene clause (no v1 text)"}[res.source.kind]
    return {
        "structure_id": res.sid, "dataset": DATASET_ID, "status": res.status, "data_role": DATA_ROLE, "instance": INSTANCE,
        "lineage": {"kind": res.source.kind, "spec_module": res.source.module_name, "base_problem": base},
        "summary": res.summary, "n_checks": len(res.checks), "n_pass": sum(c["status"] == PASS for c in res.checks),
        "failed_checks": [{"id": c["id"], "name": c["name"], "why": c.get("why", "")} for c in res.failed],
        "checks": res.checks, "panel": panel_record(res), "n_cells": len(res.rows),
        "cells_by_stratum": dict(sorted(Counter(r["stratum"] for r in res.rows).items())),
        "judge_checks_pending": [] if panel_record(res)["status"] == "ADMITTED" else ["5.1-5.4 panel review", "6.1 blind naturalness"]}


def write_json(path: Path, obj: Any, **kwargs: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, default=str, **kwargs) + "\n", encoding="utf-8")


def build(out: Path, sources: list[Source], dataset: Path, build_date: str, pool: Pool | None = None) -> dict[str, Any]:
    pool = pool or pool_for(dataset)
    plans = merged_plans()
    git = git_state()
    work = sorted(((s, sid) for s in sources if not s.error for sid in s.specs), key=order_key)
    results: list[Result] = []
    seen: dict[str, str] = {}
    admitted: list[Entry] = []
    for source, sid in work:
        if sid in seen:
            dup = Result(sid, source, file_stem=f"{sid}__{source.key}")
            dup.checks.append(mk("1.1", "unique structure id", False, f"structure_id {sid} is also specified by {seen[sid]}"))
            results.append(dup)
            continue
        seen[sid] = source.key
        result = evaluate(source, sid, pool, admitted, dataset, plans, build_date, git)
        if result.status == ADMITTED and result.entry is not None:
            admitted.append(result.entry)
        results.append(result)
    not_built = [(s, sid, reason) for s in sources if not s.error
                 for sid, reason in sorted(s.infeasible.items(), key=lambda kv: sid_key(kv[0])) if sid not in s.specs]
    added = ("dataset", "data_role", "m250_lineage", "m250_source_module")
    rows: list[dict[str, Any]] = []
    for res in results:
        if res.status != ADMITTED:
            continue
        for row in res.rows:
            clash = [k for k in added if k in row]
            if clash:
                raise SystemExit(f"row field(s) {clash} already exist in {row['job_id']}")
            new_row = dict(row, dataset=DATASET_ID, data_role=DATA_ROLE, m250_lineage=res.source.kind,
                           m250_source_module=res.source.module_name)
            if res.source.kind == "NEW" and new_row.get("level") is None:
                new_row["level"] = res.summary.get("level")
            rows.append(new_row)
    traces = [t for res in results if res.status == ADMITTED for t in res.traces]
    admitted_records = [{"domain": r.summary["domain"], "level": r.summary.get("level"), "n_computed": r.summary["n_computed_nodes"],
                         "kind": r.source.kind, "has_c": r.summary["has_c"], "has_k": r.summary["has_k"],
                         "familiarity": r.summary["c_familiarity"]} for r in results if r.status == ADMITTED]
    comp = composition(admitted_records)
    comp["target"] = {"exploration_structures_planned": 130, "admitted": len(admitted_records),
                      "shortfall": max(0, 130 - len(admitted_records)), "rejected": sum(r.status == REJECTED for r in results)}
    out.mkdir(parents=True, exist_ok=False)
    (out / "admission").mkdir()
    for res in results:
        write_json(out / "admission" / f"{res.file_stem}.json", admission_record(res))
    for source, sid, reason in not_built:
        write_json(out / "admission" / f"{sid}.json", {
            "structure_id": sid, "dataset": DATASET_ID, "status": NOT_BUILT, "data_role": DATA_ROLE, "reason": reason,
            "source": source.key, "checks": [], "n_cells": 0,
            "note": "the spec module records that this structure cannot honestly carry the design (INFEASIBLE); no spec, no cells"})
    (out / "cells.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    (out / "traces.jsonl").write_text("".join(json.dumps(t, ensure_ascii=False, sort_keys=True) + "\n" for t in traces), encoding="utf-8")
    write_json(out / "certificates.json", {res.file_stem: {**res.certificate, "status": res.status} for res in results},
               ensure_ascii=False)
    write_json(out / "composition.json", comp)
    body = readme(results, sources, not_built, comp, pool, build_date, rows)
    consistency = provenance_consistency(body)
    text = body + (f"\nProvenance consistency (`scripts/check_provenance_consistency.py` on the text above): "
                   f"{consistency['verdict']} {consistency['status_counts']}.\n")
    (out / "README.md").write_text(text, encoding="utf-8")
    files = ["cells.jsonl", "traces.jsonl", "certificates.json", "composition.json", "README.md",
             *sorted(f"admission/{p.name}" for p in (out / "admission").iterdir())]
    summary = {
        "dataset": DATASET_ID, "data_role": DATA_ROLE, "instance": INSTANCE, "build_date": build_date, "generator": GENERATOR,
        "generator_version": GENERATOR_VERSION, "git": git, "n_cells": len(rows), "n_structures": len(admitted_records),
        "by_family": dict(sorted(Counter(r["family"] for r in rows).items())),
        "by_stratum": dict(sorted(Counter(r["stratum"] for r in rows).items())),
        "by_structure": dict(sorted(Counter(r["structure_id"] for r in rows).items(), key=lambda kv: sid_key(kv[0]))),
        "admitted": [r.sid for r in results if r.status == ADMITTED],
        "rejected": [{"structure_id": r.sid, "source": r.source.key, "failed_checks": [c["id"] for c in r.failed],
                      "reasons": [c.get("why", "") for c in r.failed]} for r in results if r.status == REJECTED],
        "not_built_infeasible": [{"structure_id": sid, "source": s.key, "reason": reason} for s, sid, reason in not_built],
        "missing_or_broken_modules": [{"key": s.key, "module": s.module_name, "error": s.error} for s in sources if s.error],
        "pool_load_errors": pool.errors, "composition": {"6.2": comp["6.2"], "6.3": comp["6.3"]},
        "provenance_consistency": consistency, "added_row_fields": list(added),
        "file_sha256": {name: sha256_file(out / name) for name in files}}
    write_json(out / "manifest.json", summary)
    return summary


def provenance_consistency(text: str) -> dict[str, Any]:
    try:
        module = _load_script("check_provenance_consistency", "scripts/check_provenance_consistency.py")
        facts = module.collect_facts(module.DEFAULT_TEMPLATES, module.DEFAULT_DATASET)
        hits = module.scan_text(text, facts)
        counts = dict(Counter(h["status"] for h in hits))
        return {"verdict": "CONFLICT" if counts.get("CONFLICT") else "PASS", "status_counts": counts,
                "conflicts": [h for h in hits if h["status"] == "CONFLICT"][:5]}
    except Exception as exc:
        return {"verdict": "NOT_EVALUATED", "status_counts": {}, "error": repr(exc)}


def readme(results: list[Result], sources: list[Source], not_built: list, comp: dict[str, Any], pool: Pool, build_date: str,
           rows: list[dict[str, Any]]) -> str:
    admitted = [r for r in results if r.status == ADMITTED]
    rejected = [r for r in results if r.status == REJECTED]
    c63, c62 = comp["6.3"], comp["6.2"]
    adv = c63["upper_university_or_multi_step"]
    lines = [
        "# M250 EXPLORATION integration set (machine checks)", "",
        f"Data role: **{DATA_ROLE}**. Built {build_date} by `{GENERATOR}` ({GENERATOR_VERSION}). Status: agent-authored, "
        "solver-certified, machine-admitted against the dataset admission standard (checks 1.1-1.3, 2.1-2.8, 2.7b, 3.1-3.5, 4.1, "
        "4.2, 6.2, 6.3); **not** panel-reviewed (checks 5.x and 6.1 are PENDING except for the M0 v2.5 structures, which are two-judge ADMITTED), not reviewed by a human. No model has "
        "seen these cells.", "",
        f"{len(rows)} cells (instance {INSTANCE} of each structure) on **{len(admitted)} admitted** structures; "
        f"**{len(rejected)} REJECTED**; {len(not_built)} recorded infeasible without a spec; "
        f"{sum(1 for s in sources if s.error)} source module(s) missing or broken.", "",
        "## Source modules", ""]
    for s in sources:
        lines.append(f"- `{s.module_name}` ({s.kind}): " + (f"**{s.error}**" if s.error else f"{len(s.specs)} specs"))
    if pool.errors:
        lines += ["", "Pool of existing structures could not load: " + "; ".join(pool.errors)]
    lines += ["", "## Admitted (machine)", "", "| structure | kind | domain | C | K | cells | panel |", "|---|---|---|---|---|---|---|"]
    for r in admitted:
        lines.append(f"| {r.sid} | {r.source.kind} | {r.summary['domain']} | {'yes' if r.summary['has_c'] else 'no'} | "
                     f"{'yes' if r.summary['has_k'] else 'no'} | {len(r.rows)} | "
                     f"{panel_record(r)['status']} |")
    lines += ["", "## REJECTED", ""]
    if not rejected:
        lines.append("None.")
    for r in rejected:
        lines.append(f"- **{r.sid}** ({r.source.key}): " + "; ".join(f"{c['id']} {c['name']}: {c.get('why', '')}" for c in r.failed))
    lines += ["", "Rejected structures keep their admission record (`admission/<id>.json`) and certificate; they have no cells and are "
              "never silently fixed (a replacement is a new spec, admission standard opening paragraph).", "",
              "## Infeasible without a spec (recorded by the spec modules)", ""]
    lines += [f"- **{sid}** ({s.key}): {reason}" for s, sid, reason in not_built] or ["None."]
    lines += [
        "", "## Composition (6.2, 6.3: reported, not forced)", "",
        f"- Domains: {c63['n_domains']} (need >= 10), largest share {c63['largest_domain_share']} (need <= 0.25): "
        f"{'OK' if c63['domains_ok'] else 'NOT MET'}. {c63['domains']}",
        f"- Upper-university or multi-step: {adv['count']} of {comp['n_admitted_structures']} (share {adv['share']}, need >= 0.2): "
        f"{'OK' if adv['ok'] else 'NOT MET'}. Rule: {adv['rule']}.",
        f"- New structures admitted: {c63['new_structures']}; C feasible {c63['c_feasible_share_of_new']} (need >= 0.5): "
        f"{'OK' if c63['c_ok'] else 'NOT MET'}; K feasible {c63['k_feasible_share_of_new']} (need >= 0.3): "
        f"{'OK' if c63['k_ok'] else 'NOT MET'}.",
        f"- Familiarity (6.2): {c62['famous']} of {c62['c_quantities']} C quantities famous (share {c62['famous_share']}, need <= 0.5): "
        f"{'OK' if c62['ok'] else 'NOT MET'}. {c62['by_tag']}",
        f"- Against the plan of record 5.2 target of 130 EXPLORATION structures: {comp['target']['admitted']} admitted, shortfall "
        f"{comp['target']['shortfall']}.", "",
        "## Judgement calls", "",
        "1. **Flags count as failures.** An overlap detector flag (text ratio >= 0.85, relation-set Jaccard >= 0.8) rejects the structure "
        "under 1.2, as does an equal program hash or an identical value signature. The nearest neighbour and score are recorded for every "
        "structure, so a reviewer can see how far each was from a threshold.",
        "2. **A structure is compared with its own id excluded**, so an upgraded v1 structure is not a duplicate of itself. Candidates are "
        "compared with the pool (dataset v1, every `library*`/`lib_*` structure) and with candidates admitted before them (M0 "
        "first, then upgraded, then new, by structure number), so two near-identical candidates do not both fall. DECOY-v1 and the EPC "
        "pool have no machine-readable structure pool in the repository and were not checked.",
        "3. **Strict rule set is required.** `certify_v2` applies the reversal, co-present-D, time-anchor and scene-clause rules only for "
        "version `v2.1`; check 3.0 fails any structure whose spec version (or its module's `CERT_VERSION`) is not `v2.1`, and the "
        "version is recorded as `cert_version`. Checks 3.7 (article agreement) and 3.8 (pair distinctness) read every rendered "
        "sentence at every study and held-out value.",
        "4. **Graph-level mutation report not run.** `certify.mutation_report` costs about 18 s per structure; 2.6 runs the role-spec "
        "mutations (identity values, repeated values, 1% solver error, broken cancellation, out-of-regime K values, marker word and "
        "reversal in D, digit in the scene clause) through `certify_v2`. Mutations that do not apply to a structure (no C, no K, a "
        "`replace` wiring) are not run for it.",
        "5. **Absent C or K needs a reason.** A structure without C (or K) must have a NO_C (NO_K) reason of at least 20 characters in its "
        "spec module, else 2.3 (2.4) fails; the M0 specs carry no such tables and pass with the absence noted.",
        "6. **Multi-step** (6.3) means at least 3 computed relations; upper-university is the level label of the v1 row or of "
        "`lib_m250_<domain>.LEVELS`.",
        "7. **Provenance consistency** (`scripts/check_provenance_consistency.py`) is run once on this README text (dataset level), not "
        "per structure; its verdict is in `manifest.json`.",
        "8. **Added row fields** against the M0 builder's rows: `dataset`, `data_role`, `m250_lineage`, `m250_source_module` (with `roles_m0v25` the M0 "
        "rows are otherwise byte-identical to `data/v2/dataset/m0_v25/cells.jsonl`; M0 module this build: `" + M0_MODULE + "`). New structures also get `level` from "
        "`lib_m250_<domain>.LEVELS` (the M0 builder leaves it empty).", "",
        "## What has not been done", "",
        "No panel review (5.x), no blind naturalness rating (6.1) for the structures marked PENDING; no human review; no model run. Panel "
        "packets: `scripts/v2/s199_m250_panel_packets.py`.", ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default=f"data/v2/dataset/{DATASET_ID}")
    parser.add_argument("--dataset", default=V1_DATASET)
    parser.add_argument("--date", default=datetime.date.today().isoformat())
    args = parser.parse_args(argv)
    out = Path(args.out) if Path(args.out).is_absolute() else REPO_ROOT / args.out
    if out.exists():
        print(f"Refusing to overwrite {out}", file=sys.stderr)
        return 2
    sources = discover()
    summary = build(out, sources, REPO_ROOT / args.dataset, args.date)
    print(json.dumps({k: summary[k] for k in ("n_cells", "n_structures", "admitted", "rejected", "not_built_infeasible",
                                              "missing_or_broken_modules", "composition")}, indent=2, default=str))
    broken = bool(summary["missing_or_broken_modules"]) or summary["provenance_consistency"]["verdict"] == "CONFLICT"
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
