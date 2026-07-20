# bsm-public-rf — Submission-package reconciliation plan

Driver: `slice-runner` (`.slice-runner.toml`). Validation gate per slice:
`pixi run pytest tests/ --tb=short -q`.

Context: the public artifact bundle, `configs/manuscript_case_study.yml`, and the
manuscript figures must be reconciled from the OLD 132-feature run to the
**corrected 123-feature canonical run** (157 enriched terms → 34 delta-pruned →
123 final; holdout macro-nRMSE 0.0714 [0.0699, 0.0724]; 17 retained PCA
components). The corrected `artifacts/tables/`, `artifacts/figure_data/`, and
`artifacts/final_model/` CSVs have already been pulled from the corrected HPC run
(`/projects/bsm/dhetting/corrected_run/.../final_manuscript_artifacts/`). The
corrected `tests/test_artifact_bundle_consistency.py` reference values have
already been set to the corrected numbers and define the gate — **do not weaken
or edit `tests/`.**

Corrected canonical numbers (authoritative, grounded in the pulled artifacts):

| quantity | old | corrected |
|---|---|---|
| retained PCA components | 20 | 17 |
| empirical-null retained terms | 69 | 70 |
| interaction candidate pairs | 62 | 62 |
| nonlinear discovered transforms | 41 | 25 |
| enriched / prefilter features | 172 | 157 |
| hc3-retained features | 172 | 157 |
| delta-pruned (removed) features | 40 | 34 |
| final features | 132 | 123 |
| final main effects | 54 | 52 |
| final interactions | 49 | 49 |
| final transformations | 29 | 22 |
| penalized-OLS holdout nRMSE | 0.0709 | 0.0706 |
| final-OLS holdout nRMSE | 0.0721 | 0.0714 |
| final-OLS nRMSE CI lower | 0.0706 | 0.0699 |
| final-OLS nRMSE CI upper | 0.0730 | 0.0724 |

---

### Slice PA-S01: Reconcile config + bundle + figures to corrected 123-model
**Phase:** PA
**Depends on:** none
**Estimated size:** medium

**Objective.** Make `configs/manuscript_case_study.yml`, the committed
`artifacts/final_model/` bundle, and the regenerated `figures/` all describe the
corrected 123-feature canonical run so that `pixi run pytest tests/` is green.

**Files to modify:**
- `configs/manuscript_case_study.yml`
- `artifacts/final_model/final_ols_summary.csv` (patch two reference cells only)
- `artifacts/final_model/per_output_intercepts.csv` (regenerate)
- `figures/*.svg`, `figures/*.pdf` (regenerate via script)

**Do NOT modify:** anything under `tests/`; `artifacts/tables/*`,
`artifacts/figure_data/*`, or the other `artifacts/final_model/*.csv` (already
corrected by upstream pull). Do NOT touch `artifacts/final_model/hc3_wald_intervals.csv`
(ungated, deferred to PA-S02) or `feature_drop_noref_nrmse_impact_full30k.csv`.

**Step 1 — config drift.** In `configs/manuscript_case_study.yml` apply exactly:
- `output_conditioning.temporary_reduction.retained_components: 20` → `17`
- `empirical_null_screen.retained_terms: 69` → `70`
- `nonlinear_discovery.identified_transformations: 41` → `25`
- `nonlinear_discovery.final_support_transformations: 29` → `22`
- `sparse_selection.source_selected_feature_count_reference: 172` → `157`
- In the `final_inferential_filter.feature_pruning.delta_threshold_override`
  comment, change "prunes 40 of the 172 enriched features to yield the 132
  final features" → "prunes 34 of the 157 enriched features to yield the 123
  final features".
- `final_model.final_predictor_count: 132` → `123`
- `final_model.final_main_effect_count: 54` → `52`
- `final_model.final_interaction_count: 49` → `49` (unchanged; verify)
- `final_model.final_transformation_count: 29` → `22`
- `final_model.intermediate_penalized_holdout_nrmse: 0.0709` → `0.0706`
- `final_model.final_ols_holdout_nrmse: 0.0721` → `0.0714`
- `final_model.final_ols_holdout_nrmse_ci_lower: 0.0706` → `0.0699`
- `final_model.final_ols_holdout_nrmse_ci_upper: 0.0730` → `0.0724`

**Step 2 — patch stale reference cells.** In
`artifacts/final_model/final_ols_summary.csv` the computed columns are already
corrected, but two annotation columns still carry old references. Change the
single data row's `manuscript_final_predictor_count_reference` from `132` to
`123` and `manuscript_final_ols_holdout_nrmse_reference` from `0.0721` to
`0.0714`. Do not alter any other cell.

**Step 3 — regenerate per-output intercepts.** The reduced-form intercept for
each output equals its per-output training mean. Regenerate
`artifacts/final_model/per_output_intercepts.csv` from the corrected
`artifacts/final_model/y_standardization.csv` (columns: `output_name`,
`original_position`, `mean`, `scale`) so it has columns `output_name,intercept`
where `intercept == mean`, one row per output, preserving `output_name` order:
```
pixi run python -c "import pandas as pd; y=pd.read_csv('artifacts/final_model/y_standardization.csv'); y[['output_name']].assign(intercept=y['mean']).to_csv('artifacts/final_model/per_output_intercepts.csv', index=False)"
```

**Step 4 — regenerate figures.** Run `pixi run reproduce-artifacts`. This reads
the corrected `artifacts/figure_data/` + `artifacts/tables/` and rewrites
`figures/*.svg` and (via Chrome headless) `figures/*.pdf`. Confirm the five
manuscript figures are rewritten: `figure_nrmse_bootstrap_summary.pdf`,
`figure_support_composition.pdf`, `figure_selected_by_module_count.pdf`,
`figure_per_output_nrmse_distribution.pdf`, `fig_module_pair_heatmap.pdf`.

**Acceptance criteria:**
- [ ] `pixi run pytest tests/ --tb=short -q` passes (all bundle-consistency,
      config-loadable, and cascade tests green).
- [ ] `configs/manuscript_case_study.yml` contains no `132`, `172`, `0.0721`,
      `0.0730`, `0.0709`, or `retained_components: 20` for the final-model /
      stage-count fields listed above.
- [ ] `figures/*.pdf` regenerated (non-empty) for the five manuscript figures.
- [ ] `git diff --stat` shows changes only to the files listed under
      "Files to modify" (plus figures); `tests/` unchanged.

---

### Slice PA-S02 (DEFERRED — not run this milestone): heavy/full-data bundle
**Phase:** PA
**Depends on:** PA-S01
**Estimated size:** large

Deferred because it requires either ~400 MB git churn or the raw BSM 30k
dataset, and the current directive is small/local:
- Replace `artifacts/final_model/hc3_wald_intervals.csv` (472 MB stale
  132-model → 412 MB corrected) — ungated by tests; large git object.
- Regenerate `artifacts/final_model/feature_drop_noref_nrmse_impact_full30k.csv`
  (needs full 30k dataset).
- Regenerate `artifacts/final_model/coefficient_column_metadata.csv` and the
  `configs/manuscript_*_metadata.yml` / `docs/manuscript_*` via
  `pixi run python scripts/build_metadata.py` (needs the private FY25Q4 report
  DOCX in rfm-pipeline).
