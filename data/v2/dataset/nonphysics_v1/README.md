# Non-physics dependency control set, version 1

Data role: **EXPLORATION** (G3). Status: **agent-authored, solver-certified, NOT yet reviewed by the LLM panel (and not yet reviewed by a human)**.

240 cells on 16 structures, a gold solving trace for every cell, and a certificate for every structure. Built by `scripts/v2/s191_build_nonphysics_controls.py` from `src/physmon/benchmark/v2/nonphysics.py` and `nonphysics_specs.py`; rebuild with the same command to get identical files (the builder refuses to overwrite).

## What this is

The plan of record (v2.2, "Supporting conditions") asks for a small non-physics dependency control, GSM-DC-style word problems with the same role manipulation as the physics set, "to tell a general numeric or dependency phenomenon from one that needs physical semantics". G1 decision 18 fixes its size: 16 structures, R and D at 3 values in 2 phrasings. **It is explicitly not powered: a null result on this set is INCONCLUSIVE**, not evidence of absence.

Each structure is an everyday problem with no physics in it (shopping, recipes, school and class counts, savings, tickets and seats, inventory, sharing, work schedules, league points, library books, garden rows, a school timetable, minibuses, print jobs; only counts, dollars and whole minutes), a small typed dependency graph of 2 to 4 relations with exact arithmetic, and an answer in a unit word. One extra sentence carries a number q:

- **R** (relevant): q enters one input of the graph (add, subtract, replace or scale) and the answer changes by a certified amount; the wiring and the reason are in `certificates.json`.
- **D** (disconnected): the same sentence frame, numeral and unit with a short attachment phrase that gives q no path to the answer. Pair 0 puts q on another person, shop, class or group that is already in the scene (introduced by one clause in the base text of every cell of the structure, no number): `other_object_same_scene`. Pair 1 puts q on the same object in another event that leaves no state behind (history before the stated situation): `same_object_other_event`. A change that is made and then reversed is cancellation and is not used (plan revision v2.2, G1 and G2).
- **N**: the D sentence with no number (one per pair), and the no-cue problem.

The rules are those of M0 v2 and the code imports them from `rolevalue_v2.py` (consequence and marker lexicons, remoteness list, pair matching with word counts within three, token differences, digit overlap), with the numerical machinery rewritten for exact arithmetic because the physics graph is tied to SI dimensions: study values equal no displayed numeral and share at most one leading digit with any input or answer; every R and D answer is exact, positive and, where the unit is a count, a whole number in every intermediate step; R answers are separated from D answers and from each other by more than 1%; misuse foils (copy or digit copy, replace, add, subtract on every input of q's unit) and the placebo are computed as in `rolevalue.py`, with confounded pairs recorded and foils that are algebraically the wired computation dropped and listed; no prompt uses a word from a small physics lexicon. Two held-out values per structure are certified and never emitted.

## Files

- `cells.jsonl`: one row per cell, the fields of `data/v2/dataset/m0_v2/cells.jsonl` that apply plus `domain: "nonphysics"` and `theme`; `target_phrases` and `target_symbols` for the H4 trace extractor (count units are not in the extractor's unit registry, so statements of the target are read through the naming chains those fields provide).
- `traces.jsonl`: one gold trace per cell, ending at the cell's gold (tested to 1e-9).
- `certificates.json`: per structure the base problem, relations, wiring, values and every check.
- `manifest.json`: counts and file hashes.

## Counts

By stratum: {'D': 96, 'N': 32, 'R': 96, 'none': 16}. D kinds: {'other_object_same_scene': 48, 'same_object_other_event': 48}. Wiring operations: {'add': 7, 'replace': 4, 'scale': 2, 'subtract': 3}.

## What has not been done

No LLM-panel or human review, and no model has seen the cells. Naturalness of the D and N sentences is the known weak point of this design (plan revision G3) and has not been rated. No grading dry run has been done with the registry units (dollars, cookies and so on are outside the unit registry).
