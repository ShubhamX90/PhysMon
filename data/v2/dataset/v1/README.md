# DECOY-v2 gold dataset v1 (Stage 14.19)

260 samples (80 structures; 50 structures have four numeric instantiations and 30 have two), each with a problem, a gold answer and a
gold solving trace. Built by `scripts/v2/s163_build_dataset.py` from the typed structures of `library`, `library_b`, `library_c` and
the seven domain modules `lib_*` (classical mechanics, electromagnetism, thermodynamics, optics and waves, quantum mechanics, modern
physics, fluids).

**Status: agent-verified, NOT reviewed by a human expert.** Every sample says `admission_category: UNREVIEWED`. Author, blind solver and
plan reviewer were agents (journal `docs/journal/stage14/14.19_gold_dataset.md`); the user replaced the human physicist review by this
agent chain. Levels are the author agent's judgement. Read `known_issues.json` before any analysis.

- `dataset.jsonl`: one sample per line: `problem`, `answer_unit`, `gold_answer`, `gold_trace` (the solving technique: restatement,
  givens, assumptions, approach, one derivation step per computed node with the named principle, why it applies, the relation, the
  substitution and the result, a sanity check, the answer), `inputs`, `relations`, `assumptions`, `solver_route`, `level`, `topic`,
  `certification`, `agent_verification`.
- `factor_cell_manifest.jsonl`: the 11 distractor cells of every instantiation (v2 section 9.1 factor fields), for the sensitivity runs.
- `summary.json`: counts and file hashes. `../verification_status.json`: per-structure verdicts and reviewer issues.

The gold trace is rendered from the typed graph, so its numbers cannot disagree with the graph; its last value equals the structure's
independent numeric solver. It is a solving technique, not text produced by a model.
