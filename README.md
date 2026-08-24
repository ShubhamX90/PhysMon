# PhysMon

PhysMon is a research codebase for hidden-state detection of model-specific physics
shortcut sensitivity under solver-verified, physics-preserving counterfactual edits.

The governing scientific specification is stored in `docs/proposal/`:

- `physmon_proposal.pdf`
- `physmon_supplementary.pdf`

Implementation must preserve the proposal's core distinction between prompt condition,
observed model behaviour, and internal representation (§3.1). The primary monitoring
target is model-specific behavioural shortcut sensitivity, not cue presence (§3.3-§3.4).
Benchmark construction must be symbolic-template-first (§5.3), with artefact controls
reported before hidden-state claims are interpreted (§6.2 and §9).

## Repository Layout

- `src/physmon/`: importable package for formal constructs, benchmark tooling, model
  instrumentation, probing, causal interventions, and utilities.
- `scripts/`: executable validation and experiment entry points.
- `slurm/templates/`: reusable Sharanga job templates.
- `docs/`: proposal, construct spec, decision log, and assumption tracker.
- `data/`: committed templates and validated/split metadata. Large generated data is
  excluded from Git.
- `results/`: small summary outputs only. Large tensors and activation-derived artifacts
  live on Sharanga scratch.

## Sync Invariant

The local repository and `~/PhysMons/` on Sharanga must be deployed from a reviewed,
committed source snapshot before job submission. Always inspect the direction-specific
dry-run first:

```bash
make remote-preflight
make sync-plan-up
make sync-up
python scripts/ops/remote_preflight.py --strict --expect-aligned

make sync-plan-down
make sync-down
```

`sync-up` and `sync-down` are non-destructive by default. `sync-check` remains a
backward-compatible alias for `sync-plan-up`; `sync-plan-prune` is inspection only and
never deletes. Large model weights, activation tensors, generated data, Slurm working
files, and remote deployment-lease state are excluded from normal syncs. See
[`skills/physmon-sharanga/SKILL.md`](skills/physmon-sharanga/SKILL.md) for the shared
Sharanga and Slurm workflow.

## Development

```bash
make install
make test
make lint
```

The canonical conda environment is `physmon`; see `environment.yml`.

Stage 13 governing-document rule: the complete Part II v1.1 plan in `docs/proposal/PhysMon_Part_II_Next_Phase_Scientific_and_Experimental_Plan.pdf` must be read together with `docs/proposals/PhysMon_Part_II_v1.1_Erratum_2026-07-03.pdf`; the erratum supersedes only renamed donor-control statements.
