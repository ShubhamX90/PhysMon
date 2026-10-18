# DECOY-v2 structures v2 (Stage 14.15)

10 new structures (S11 to S20), each with two numeric instantiations and eleven predeclared factor cells, built by
`scripts/v2/s146_generate_structures.py --library library_b` at source commit `f492bfc`.

Status: **SOLVER_CERTIFIED and UNREVIEWED.** Certification covers the typed graph, an independently coded numeric
solver, dimensional consistency, the assumptions list, and the match between every numeral in every rendered prompt
and the graph. It does not certify the English text or the modelling choices. Independent expert review (v2 B4,
`docs/validation/v2/validator_handbook_v2.md`) is required before any use, and no model has been run on these items.

- `S11.json` to `S20.json`: graph, assumptions, prompt grammar, instantiations, proof object.
- `factor_cell_manifest.jsonl`: 220 cells (212 feasible) with the v2 §9.1 factor fields.
- `admissibility.json`: the factor axes and the feasibility matrix, with a reason for every infeasible cell.
- `mutation_report.json`: 91 mutants; negative mutants not caught: 0;
  equivalent rewrites wrongly rejected: 0.
- `lineage.json`: authorship and the overlap check against the 155 v1 templates.
