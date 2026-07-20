# BSM Semi-Synthetic Recovery Study — Reproduction Log

Generated: 2026-07-20T20:21:31.153312+00:00
Master seed: 42

## Reproduce

```bash
pixi install --locked
pixi run python scripts/run_bsm_recovery_study.py --seed 42
```

## Scale (deliberate reduction from executed HPC scale)

reduced-local BSM design: n_inputs=30 (158-continuous + 2-binary structure, subset to 28 continuous + 2 binary), n_outputs=40, n_runs=2000, B=199, B_screen=199, fwer_reps=100, alt_reps=20 — deliberate reduction from the executed ~30 000-run / 23 495-output HPC scale. Preserves empirical input ranges, the 158-continuous + 2-binary structure, multivariate low-rank responses (PCA path), hierarchical residualized interaction discovery, and train-only selection. Candidate-family logic (BH screening -> fwer_max_stat_exact selection) unchanged.

## Input design

- Full executed interface: 160 inputs (158 continuous + 2 binary scenario switches).
- Binary scenario switches: FM.Use Agnostic FS Conversion, OI.Use AEO Reference Oil.
- Continuous inputs resampled independently over their published [min_sample_value, max_sample_value] ranges (configs/manuscript_input_metadata.yml); binary switches drawn Bernoulli(0.5). This matches the executed independent-factor Monte-Carlo sensitivity design and preserves the empirical ranges and 158+2 structure without redistributing the raw run design.

## Candidate-family logic (unchanged from the submitted workflow)

Marginal permutation BH input screening -> PCA response reduction -> hierarchical residualized interaction scoring (interaction value added over linear + quadratic main-effect design) -> exact finite-permutation max-statistic (Westfall-Young) FWER selection; a parallel quadratic-library transformation-discovery stage uses the same residualized exact-FWER rule. All screening, PCA, scoring, and selection use train rows only.

## Empirical interaction FWER (null-interaction scenarios)

| scenario | alpha | FWER | Wilson 95% CI | n |
| --- | --- | --- | --- | --- |
| global_null | 0.1 | 0.000 | [0.000, 0.037] | 100 |
| interaction_null | 0.1 | 0.110 | [0.063, 0.186] | 100 |

## Scenario grid

- **global_null**: Complete global null: no main, interaction, or transform signal.
- **interaction_null**: Main effects (including both binary switches) and a nonlinear main-effect transform, but no true interactions.
- **sparse_strong_hierarchical**: Sparse strong-signal hierarchical model: main + continuous-continuous and continuous-binary interactions + a transformation term.
- **weak_signal**: Same hierarchical support as sparse_strong but low signal-to-noise.
- **correlated_redundant**: Dense active set with many candidate pairs (redundant active and inactive predictors) stressing selection precision.
- **pure_interaction**: Pure-interaction signals (continuous-continuous and binary-binary) with negligible marginal main effects; a required screen stress test.
- **nonlinear_misspecified**: Nonlinear main-effect signal via the declared transform library plus one misspecified form outside the library; a required stress test.

## Artifacts

- `fwer_calibration.csv` — empirical interaction FWER + Wilson CI per null scenario.
- `recovery_estimands.csv` — per-family (main/interaction/transformation/whole) precision, recall, FDP, exact-support recovery, selected size.
- `stage_retention.csv` — candidates vs retained at each discovery stage.
- `comparator_metrics.csv` — oracle-OLS, GBT, elastic-net predictive accuracy on independent test responses.
- `recovery_manifest.json` — locked scale/seed/scenario manifest.
