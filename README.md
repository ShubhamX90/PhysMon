# PhysMon

PhysMon is a research codebase for hidden-state detection of model-specific physics
shortcut sensitivity under solver-verified, physics-preserving counterfactual edits.

The governing scientific specification is stored in `docs/proposal/`:

- `physmon_proposal.pdf`
- `physmon_supplementary.pdf`

**Stage 14 onwards:** the plan of record is `docs/proposals/PhysMon_Research_v2.pdf`
(PhysMon Research Redesign v2.0, 14 October 2026; navigation digest in
`docs/proposals/PhysMon_Research_v2_working_digest.md`). It adds a mandatory benchmark
red-team phase (Phase B) before any new mechanistic claim and replaces the June Part II plan as
guidance. The older documents below remain the historical record.

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

## Working Model

PhysMon is edited, tested, and run directly on Sharanga in `~/PhysMons` (Claude Code
over Remote SSH). GitHub (`origin`, reached over SSH as
`git@github-physmon:ShubhamX90/PhysMon.git`) is the shared record for review and
handoff. There is no maintained laptop mirror and no sync step. Jobs read the live
worktree, so commit and push from a clean tree before a serious run and record the
full SHA.

The old `make sync-*` / `remote-preflight` targets and the `scripts/ops/` lease helpers
belong to the retired mirror workflow. The Makefile targets refuse to run unless
`PHYSMON_ALLOW_SYNC=1` is set. See
[`skills/physmon-sharanga/SKILL.md`](skills/physmon-sharanga/SKILL.md) for the shared
Sharanga, Git, and Slurm workflow. Large model weights, activation tensors, generated
data, and Slurm working files stay out of Git.

### Runtime paths

Cluster locations are not hardcoded in source. `src/physmon/utils/paths.py` resolves them
from the environment, and the model registry writes each model as
`${PHYSMON_MODEL_ROOT}/<directory>`:

| Variable | Default | Holds |
|---|---|---|
| `SCRATCH` | `/scratch/pabitra` | Per-account scratch root |
| `PHYSMON_MODEL_ROOT` | `$SCRATCH/models` | Model weights (`docs/model_registry.yml`) |
| `PHYSMON_SCRATCH_ROOT` | `$SCRATCH/physmon` | Activations, logs, checkpoints, caches |

Restore or add model weights with `scripts/download_model.py --model-key <key>`
(registry-driven, pinned revision, hash-verified; manifests land in
`docs/model_manifests/`). The `#SBATCH --output` log paths in `slurm/templates/` stay
literal because Slurm does not expand environment variables there.

## Development

```bash
make install
make test
make lint
```

The canonical conda environment is `physmon`; see `environment.yml`.

Stage 13 governing-document rule: the complete Part II v1.1 plan in `docs/proposal/PhysMon_Part_II_Next_Phase_Scientific_and_Experimental_Plan.pdf` must be read together with `docs/proposals/PhysMon_Part_II_v1.1_Erratum_2026-07-03.pdf`; the erratum supersedes only renamed donor-control statements.
