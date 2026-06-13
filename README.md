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

The local Mac repository and `~/PhysMons/` on Sharanga must be synchronized before job
submission and after job completion:

```bash
make sync-up
make sync-down
make sync-check
```

Large model weights, activation tensors, generated data, and Slurm working files are
excluded from normal syncs.

## Development

```bash
make install
make test
make lint
```

The canonical conda environment is `physmon`; see `environment.yml`.
