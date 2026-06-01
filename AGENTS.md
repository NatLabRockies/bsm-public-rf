# BSM Case Study Repo (bsm-public-rf)

This is the BSM study reproducibility repository.

The generic pipeline framework is at NatLabRockies/rfm-pipeline.

## What this repo contains

- `configs/` — BSM-specific pipeline configuration files
- `artifacts/` — committed final model artifacts (CSV tables, not binary blobs)
- `scripts/` — thin reproduction scripts using rfm_pipeline
- `figures/` — output directory for generated figures

## What this repo does NOT contain

- Pipeline source code → that lives in NatLabRockies/rfm-pipeline
- Raw BSM input data → contact repo owners for access
- LaTeX manuscript → see NatLabRockies/bsm-public-rf-manuscript

## Autonomy level: ADVISORY

This repo does not have autonomous commit/push/PR enabled.
Do not make destructive git operations without user approval.

## Key files

- `configs/manuscript_case_study.yml` — main BSM study config
- `configs/manuscript_data_contract.yml` — data schema
- `artifacts/final_model/final_ols_summary.csv` — final fitted model
- `artifacts/final_model/final_support_features.csv` — screened feature set
