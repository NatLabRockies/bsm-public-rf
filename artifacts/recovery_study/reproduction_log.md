# BSM Semi-Synthetic Recovery Study — Reproduction Log

Generated: 2026-07-22T23:48:27.985598+00:00
Master seed: 42

## Environment

- bsm-public-rf commit: `8556f2afb7c58a867eca9acc6daacf60c2f62210`
- rfm-pipeline pin: `{path = "../rfm-pipeline", editable = true}`

## Reproduce

```bash
pixi install --locked
pixi run python scripts/run_bsm_recovery_study.py --seed 42
```

## Validation gate

Command: `pixi run pytest tests/ --tb=short -q`

Status: **NOT_EXECUTED_IN_PROCESS**

```
Not executed in-process. Run `pixi run pytest tests/ --tb=short -q` on a clean checkout to validate; the suite exercises the FWER-control keystone gates.
```

## Artifact hashes (SHA-256)

- `replicate_records.csv`: `6b0a7d6a7f16b7b760a4460af9c09fba09cfdb214b0eb4a2c8cbeadc5013861e`
- `fwer_calibration.csv`: `d00d4fc4a34877b0a31ee4dbc5c3217a15e4358e5ebe4e30b5fb3cf5d4633556`
- `recovery_estimands.csv`: `0fc598ecf941780e15182fb0f779abee754ed58fad3bf3b99ba5f389e00af281`
- `comparator_metrics.csv`: `d0162a545ff275a0a33c54b032a5d8c24b76868c6a3bad8a5f876df7e5d2686a`
- `stage_retention.csv`: `1ec9487940b005e381d13477530be577e26fdb2216ff3fe47109f0f4470a3491`
- `recovery_manifest.json`: `bda8cce46849c9ffa65f10697ca2a65c0353cf068bd4b1ecca078acd294be608`

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

reduced-local BSM design: 158-continuous first-order candidate design (the 2 binary scenario switches are excluded from the candidate set, as in production), n_outputs=40, n_runs=2000, B=199, B_screen=199, fwer_reps=100, alt_reps=20 — deliberate reduction from the executed ~30 000-run / 23 495-output HPC scale. Preserves empirical input ranges and the 158-continuous first-order structure, multivariate low-rank responses (PCA path), hierarchical residualized interaction discovery, and train-only selection. Candidate-family logic (BH screening -> fwer_max_stat_exact selection at α=0.05) unchanged.

## Input design

- Full executed interface: 160 inputs (158 continuous + 2 binary scenario switches).
- Binary scenario switches: FM.Use Agnostic FS Conversion, OI.Use AEO Reference Oil.
- First-order candidate design (screened by the recovery study): 158 continuous inputs. The two binary scenario switches are excluded from the candidate set exactly as the production feature catalog excludes them (generate_feature_catalog.py special columns); they are scenario/stratification variables, not predictor candidates.
- Continuous inputs resampled independently over their published [min_sample_value, max_sample_value] ranges (configs/manuscript_input_metadata.yml). This matches the executed independent-factor Monte-Carlo sensitivity design and preserves the empirical ranges and 158-continuous first-order structure without redistributing the raw run design.

## Candidate-family logic (unchanged from the submitted workflow)

Marginal permutation BH input screening -> PCA response reduction -> hierarchical residualized interaction scoring (interaction value added over linear + quadratic main-effect design) -> exact finite-permutation max-statistic (Westfall-Young) FWER selection; a parallel quadratic-library transformation-discovery stage uses the same residualized exact-FWER rule. All screening, PCA, scoring, and selection use train rows only.

## Empirical interaction FWER (null-interaction scenarios)

| scenario | alpha | FWER | Wilson 95% CI | n | passes_calibration |
| --- | --- | --- | --- | --- | --- |
| global_null | 0.05 | 0.000 | [0.000, 0.037] | 100 | True |
| interaction_null | 0.05 | 0.010 | [0.002, 0.054] | 100 | True |

## Scenario grid

- **global_null**: Complete global null: no main, interaction, or transform signal.
- **interaction_null**: Continuous main effects and a nonlinear main-effect transform, but no true interactions.
- **sparse_strong_hierarchical**: Sparse strong-signal hierarchical model: continuous main effects + a continuous-continuous interaction + a transformation term.
- **weak_signal**: Same hierarchical support as sparse_strong but low signal-to-noise.
- **correlated_redundant**: Dense active set with many candidate pairs (redundant active and inactive predictors) stressing selection precision.
- **pure_interaction**: Pure continuous-continuous interaction signal with negligible marginal main effects; a required screen stress test.
- **nonlinear_misspecified**: Nonlinear main-effect signal via the declared transform library plus one misspecified form outside the library; a required stress test.

## Artifacts

- `replicate_records.csv` — per-replicate scenario, seed, selected/false counts, predictive metrics.
- `fwer_calibration.csv` — empirical interaction FWER + Wilson CI + passes_calibration per null scenario.
- `recovery_estimands.csv` — per-family (main/interaction/transformation/whole) precision, recall, FDP, exact-support recovery, selected size (mean ± MC uncertainty).
- `stage_retention.csv` — candidates vs retained at each discovery stage.
- `comparator_metrics.csv` — oracle-OLS, GBT, elastic-net, proposed-workflow predictive accuracy on independent test responses.
- `recovery_manifest.json` — locked scale/seed/scenario manifest.
