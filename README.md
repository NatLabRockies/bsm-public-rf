# BSM Reduced-Form Model — Manuscript Reproduction Repository

This repository contains the configuration, committed artifacts, and helper scripts needed to reproduce the published Biomass Scenario Model (BSM) reduced-form modeling results with `rfm-pipeline`.

## Prerequisites

- Python >= 3.10
- [Pixi](https://pixi.sh)
- `rfm-pipeline` (installed automatically by `pixi install` in this repository)
- Access to the BSM simulation data required for reproduction

**HPC-only prerequisites** (required only for step 4 — full pipeline re-run):

- SLURM HPC cluster access (the publication run used NREL's Kestrel)
- `SCRATCH_DIR` environment variable set to your cluster scratch root
  (e.g., `export SCRATCH_DIR=/scratch/${USER}`)
- `SLURM_ACCOUNT` environment variable set to your HPC allocation account
- BSM dataset placed at `${SCRATCH_DIR}/bsm/bsm-public-rf/artifacts/preprocessed_real_data_30k/`

## Input Data

BSM simulation data are not included in this repository. A full reproduction requires:

- `X.parquet` — input matrix
- `Y.parquet` — output matrix
- `all_input_metadata.parquet`
- `output_metadata.parquet`
- `manuscript_feature_catalog.parquet`
- `fixed_holdout_assignments.parquet`

Obtain these files from the data release associated with the manuscript, or generate them with the corresponding BSM simulation and preprocessing workflow before running this repository.

## Installation

```bash
git clone https://github.com/NatLabRockies/bsm-public-rf.git
cd bsm-public-rf
pixi install
```

## Configuration

Create a local paths file from the template and update it for your environment:

```bash
cp configs/manuscript_paths_template.yml configs/manuscript_paths.yml
```

`configs/manuscript_paths.yml` is gitignored. Set each path in that file to your local BSM input data and writable output location. If you adapt the optional cluster configs under `configs/hpc/`, also set any required environment-specific paths such as `BSM_DATA_ROOT` or `SCRATCH_DIR`.

## Reproducing the manuscript

1. Install the environment with `pixi install`.
2. Copy `configs/manuscript_paths_template.yml` to `configs/manuscript_paths.yml` and edit the paths.
3. Regenerate manuscript-facing outputs from the committed model artifacts:
   ```bash
   pixi run reproduce-artifacts
   ```
4. (**HPC only** — requires Kestrel access, BSM dataset, and `SCRATCH_DIR` set)
   Re-run the full pipeline from scratch:
   ```bash
   pixi run reproduce-full
   ```
   This uses `configs/hpc/kestrel_publication_full_dataset.yml` and submits SLURM
   jobs. See `scripts/publication-run/README.md` for the full orchestration workflow.
5. Collect regenerated figures from `figures/` and produced artifacts from `artifacts/` or your configured output directory.

## Repository structure

- `configs/` — dataset, runtime, and optional cluster configuration files
- `scripts/` — reproduction entry points that call `rfm-pipeline`
- `artifacts/` — committed manuscript artifacts and model outputs
- `figures/` — generated figures

## Citation

Citation information for the manuscript should be added here when the final publication metadata are available.
