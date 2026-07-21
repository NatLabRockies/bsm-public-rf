# BSM Semi-Synthetic Recovery Study — Reproduction Log

Generated: 2026-07-21T19:47:05.284610+00:00
Master seed: 42

## Environment

- bsm-public-rf commit: `16f89e2353672df7117852afa07b483510aae88d`
- rfm-pipeline pin: `{path = "../rfm-pipeline", editable = true}`

## Reproduce

```bash
pixi install --locked
pixi run python scripts/run_bsm_recovery_study.py --seed 42
```

## Validation gate

Command: `pixi run pytest tests/ --tb=short -q`

Status: **PASSED**

```
40 passed, 1367 warnings in 1877.81s (pixi run python -m pytest tests/)

(Captured from a separate `pixi run pytest tests/ --tb=short -q` run on this commit; re-run that command to reproduce.)
```

## Artifact hashes (SHA-256)

- `replicate_records.csv`: `23108f3f67c9af1f0837c7ab8eb7d696d9653d598aaf862c63dd18911697cb30`
- `fwer_calibration.csv`: `01965a799f6e4db1ccb22bfcc3981b29c662ed3aa2bed54ca645e27eaf004e6b`
- `recovery_estimands.csv`: `2bc6bdeef131143e6be0a92d5560169cf1c93002d61cfd7805ac74b35488a129`
- `comparator_metrics.csv`: `5a447a7ba234fdd5775edb3b39cd10c9d788619ff8e16c8996c17f2d52314538`
- `stage_retention.csv`: `0ab7bf9dde4e4fc6b9a444f5e142538873416e4d5c1487e5fc34681808825094`
- `recovery_manifest.json`: `f55c05ce6d28003da05312a09aa543441672d0d21d482ec845d2a65bc23c22f1`

## Per-scenario replicate status

| scenario | attempted | completed | failed |
| --- | --- | --- | --- |
| global_null | 100 | 100 | 0 |
| interaction_null | 100 | 100 | 0 |
| sparse_strong_hierarchical | 20 | 20 | 0 |
| weak_signal | 20 | 20 | 0 |
| correlated_redundant | 20 | 20 | 0 |
| pure_interaction | 20 | 20 | 0 |
| nonlinear_misspecified | 20 | 20 | 0 |

## Scale (deliberate reduction from executed HPC scale)

reduced-local BSM design: full 160-input design (158-continuous + 2-binary), n_outputs=40, n_runs=2000, B=199, B_screen=199, fwer_reps=100, alt_reps=20 — deliberate reduction from the executed ~30 000-run / 23 495-output HPC scale. Preserves empirical input ranges, the 158-continuous + 2-binary structure, multivariate low-rank responses (PCA path), hierarchical residualized interaction discovery, and train-only selection. Candidate-family logic (BH screening -> fwer_max_stat_exact selection at α=0.05) unchanged.

## Input design

- Full executed interface: 160 inputs (158 continuous + 2 binary scenario switches).
- Binary scenario switches: FM.Use Agnostic FS Conversion, OI.Use AEO Reference Oil.
- Continuous inputs resampled independently over their published [min_sample_value, max_sample_value] ranges (configs/manuscript_input_metadata.yml); binary switches drawn Bernoulli(0.5). This matches the executed independent-factor Monte-Carlo sensitivity design and preserves the empirical ranges and 158+2 structure without redistributing the raw run design.

## Candidate-family logic (unchanged from the submitted workflow)

Marginal permutation BH input screening -> PCA response reduction -> hierarchical residualized interaction scoring (interaction value added over linear + quadratic main-effect design) -> exact finite-permutation max-statistic (Westfall-Young) FWER selection; a parallel quadratic-library transformation-discovery stage uses the same residualized exact-FWER rule. All screening, PCA, scoring, and selection use train rows only.

## Empirical interaction FWER (null-interaction scenarios)

| scenario | alpha | FWER | Wilson 95% CI | n | passes_calibration |
| --- | --- | --- | --- | --- | --- |
| global_null | 0.05 | 0.010 | [0.002, 0.054] | 100 | True |
| interaction_null | 0.05 | 0.030 | [0.010, 0.085] | 100 | True |

## Scenario grid

- **global_null**: Complete global null: no main, interaction, or transform signal.
- **interaction_null**: Main effects (including both binary switches) and a nonlinear main-effect transform, but no true interactions.
- **sparse_strong_hierarchical**: Sparse strong-signal hierarchical model: main + continuous-continuous and continuous-binary interactions + a transformation term.
- **weak_signal**: Same hierarchical support as sparse_strong but low signal-to-noise.
- **correlated_redundant**: Dense active set with many candidate pairs (redundant active and inactive predictors) stressing selection precision.
- **pure_interaction**: Pure-interaction signals (continuous-continuous and binary-binary) with negligible marginal main effects; a required screen stress test.
- **nonlinear_misspecified**: Nonlinear main-effect signal via the declared transform library plus one misspecified form outside the library; a required stress test.

## Artifacts

- `replicate_records.csv` — per-replicate scenario, seed, selected/false counts, predictive metrics.
- `fwer_calibration.csv` — empirical interaction FWER + Wilson CI + passes_calibration per null scenario.
- `recovery_estimands.csv` — per-family (main/interaction/transformation/whole) precision, recall, FDP, exact-support recovery, selected size (mean ± MC uncertainty).
- `stage_retention.csv` — candidates vs retained at each discovery stage.
- `comparator_metrics.csv` — oracle-OLS, GBT, elastic-net, proposed-workflow predictive accuracy on independent test responses.
- `recovery_manifest.json` — locked scale/seed/scenario manifest.
