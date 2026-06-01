# BSM Case Study Reproducibility

This repository contains the configuration, final model artifacts, and reproduction
scripts for the Biomass Scenario Model (BSM) reduced-form modeling case study.

The generic pipeline framework is in [NatLabRockies/rfm-pipeline](https://github.com/NatLabRockies/rfm-pipeline).

## Structure

```
configs/                  # BSM-specific pipeline configuration
  manuscript_case_study.yml         # Main case study config
  manuscript_data_contract.yml      # Data schema and feature definitions
  manuscript_paths.template.yml     # Path template (copy → manuscript_paths.yml)
  manuscript_runtime.yml            # Runtime settings
  datasets/real_data.yml            # BSM dataset source config
  hpc/                              # Kestrel HPC submission configs

artifacts/                # Committed final model artifacts
  final_model/            # Coefficients, support features, standardization
  tables/                 # Performance and ablation tables

scripts/                  # Thin reproduction scripts
figures/                  # Figure output directory (generated)
```

## Reproducing the results

### Prerequisites

1. Install [pixi](https://pixi.sh)
2. Clone this repository
3. Copy and edit the paths template:
   ```bash
   cp configs/manuscript_paths.template.yml configs/manuscript_paths.yml
   # Edit manuscript_paths.yml to point to your BSM data
   ```
4. Install dependencies:
   ```bash
   pixi install
   ```

### Run the full dataset pipeline (requires HPC)

```bash
pixi run reproduce-full
```

See `configs/hpc/` for Kestrel SLURM submission configs.

### Regenerate artifacts from committed model

```bash
pixi run reproduce-artifacts
```

## Data access

The BSM input data (`real_data.yml`) points to the NREL BSM output dataset.
Contact the repository owners for data access instructions.

## Citation

If you use this case study or the rfm-pipeline framework, please cite:

> Hettinger, D. et al. (2026). Reduced-form modeling workflow for large-scale
> simulator output. *Journal of Data Science*.
