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

---

## Phase R4B — Rebuild the semi-synthetic recovery study on the SUBMITTED production workflow

Context: the round-four adversarial audit
(`bsm-public-rf-manuscript/docs/ANALYSIS_HANDOFF.md`, "Round-four audit of the
current recovery attempt — not accepted"; REVIEW-0015/REVIEW-0018) rejects the
current `scripts/run_bsm_recovery_study.py` because it runs a SEPARATE
reimplementation (residualized-product score + PCA + quadratic-only transform)
rather than the shipped production stages, and because of specific DGP/oracle/
comparator/replication/FWER defects. The generic runner
`rfm_pipeline.run_production_recovery_pipeline` / `ProductionRecoveryResult`
(rfm-pipeline Phase R4-S02) drives the actual production stages
(`condition_manuscript_outputs` → `screen_manuscript_empirical_null_terms` →
`discover_manuscript_interactions` with `fwer_max_stat_exact` at α=0.05 →
`discover_manuscript_nonlinear_transformations` → `select_manuscript_sparse_support`)
on arbitrary in-memory data. This phase rewrites the BSM driver to call that
production runner and fixes every listed defect. All BSM-specific code stays in
this repo; no BSM constants are added to rfm-pipeline. Validation gate:
`pixi run pytest tests/ --tb=short -q` (whole suite; do NOT weaken any test).

Authoritative defect list to close (from the handoff round-four audit):
1. Runs on 30 inputs while claiming the 160-input interface → run the full 160-input design (158 continuous + 2 binary).
2. Substitute pipeline → call `rfm_pipeline.run_production_recovery_pipeline` (the shipped stages).
3. Method changes (BH q=0.20, PCA ≤8) → use the submitted q=0.05 screen and 90%-variance PCA rule via the production specs.
4. `alt_reps` declared but not executed → run the replication loop; keep one machine-readable record per replicate; report Monte-Carlo uncertainty.
5. `correlated_redundant` uses independent uniforms → implement the declared correlation/redundancy mechanism and verify realized correlation.
6. Misspecified sine omitted from truth ledger → every planted term (incl. out-of-library) appears in the truth support and recovery denominators.
7. Train/eval share RNG/noise → share fixed coefficients/loadings but draw INDEPENDENT train and eval noise.
8. FWER at α=0.10 → validate the submitted α=0.05; use a candidate-family size relevant to the procedure.
9. False Wilson claim → do not assert interval coverage of the nominal rate as proof of control; use a prespecified calibration criterion and state uncertainty accurately.
10. Oracle uses only main-effect columns → construct the oracle design from the COMPLETE planted algebraic support (mains + interactions + transforms).
11. Elastic net on raw inputs at fixed penalty; proposed surrogate absent → all comparators use the same declared candidate library with training-only tuning and identical eval data; include the proposed selected-support workflow as its own comparator row.
12. Reproduction log is a summary → produce clean-run evidence (env, commit, command, gate output, artifact hashes, replicate status).

### Slice R4B-S01: Rebuild the driver on the production runner + fix DGP/oracle/comparator defects
**Phase:** R4B
**Depends on:** none
**Estimated size:** large

**Objective.** Replace the substitute pipeline in
`scripts/run_bsm_recovery_study.py` with calls to
`rfm_pipeline.run_production_recovery_pipeline` on the full 160-input BSM
semi-synthetic design, and fix defects 1,2,3,5,6,7,8,10,11 above.

**Files to modify:**
- `scripts/run_bsm_recovery_study.py`
- `tests/test_bsm_recovery_fwer.py` (update the gate to α=0.05 and production-stage usage — CORRECT the assertions to the valid procedure; do NOT weaken/skip/xfail)

**Do NOT modify:** any other file under `tests/`; `configs/`.

**Requirements (do NOT weaken tests):**
- The `BSMInputDesign` keeps all 160 inputs (158 continuous + 2 binary); the study runs on all 160 (no 30-input subset).
- `run_pipeline` delegates to `rfm_pipeline.run_production_recovery_pipeline(..., alpha=0.05, family_error_method="fwer_max_stat_exact")`; the residualized-product/quadratic-only reimplementation is removed. Screen uses q=0.05 and PCA the 90%-variance rule via the production specs.
- `correlated_redundant` draws inputs with a documented, verifiable correlation/redundancy structure (e.g. a shared latent factor across a block of inputs); the driver records the realized correlation.
- The truth ledger for each scenario includes EVERY planted term, including the out-of-library sine in `nonlinear_misspecified`; recovery denominators count it.
- Train and eval responses share the fixed coefficients/loadings but use INDEPENDENT noise draws (no RNG reset reuse).
- The oracle-OLS design is built from the full planted algebraic support (mains + planted interaction products + planted transforms), not raw mains only.
- Comparators (oracle-OLS, a sparse/multitask linear method, a nonlinear surrogate) are fit on the SAME declared candidate library with training-only tuning and evaluated on identical eval data; add a row for the proposed selected-support workflow itself.
- FWER is evaluated at α=0.05.

**Acceptance criteria:**
- [ ] `pixi run pytest tests/ --tb=short -q` passes.
- [ ] `tests/test_bsm_recovery_fwer.py` asserts α=0.05 interaction-FWER control on the null scenarios and that the driver path calls `run_production_recovery_pipeline` (e.g. via a spy/monkeypatch or by asserting production-stage retained sets are present in the result).
- [ ] `grep -n "run_production_recovery_pipeline" scripts/run_bsm_recovery_study.py` is non-empty; no residualized-product/quadratic-only reimplementation remains.
- [ ] `grep` confirms the design still exposes 160 inputs and 2 binary names.

### Slice R4B-S02: Execute replication loop, α=0.05 FWER with binomial CI, and clean reproduction log
**Phase:** R4B
**Depends on:** R4B-S01
**Estimated size:** medium

**Objective.** Close defects 4,9,12: run the declared replication loop with
per-replicate records and Monte-Carlo uncertainty, report empirical interaction
FWER at α=0.05 with a binomial (Wilson) CI under a prespecified calibration
criterion, and emit clean-run reproduction evidence.

**Files to modify:**
- `scripts/run_bsm_recovery_study.py`
- `tests/test_bsm_recovery_fwer.py` (add a replication/CI assertion if appropriate — do NOT weaken existing ones)

**Requirements (do NOT weaken tests):**
- Execute `alt_reps` alternative replicates per scenario and `fwer_reps` null replicates; write one machine-readable record per replicate to `artifacts/recovery_study/replicate_records.csv` (scenario, replicate index, seed, per-family selected/false counts, predictive metrics).
- Aggregate with Monte-Carlo uncertainty; `fwer_calibration.csv` reports α=0.05, empirical FWER, Wilson CI, n_replicates, and a boolean `passes_calibration` per a PRESPECIFIED criterion (e.g. point estimate ≤ α + 3·SE); the driver does NOT claim control merely because a CI contains α.
- `recovery_estimands.csv` aggregates precision/recall/FDP/exact-recovery/size per family across replicates (mean ± MC uncertainty), truth denominators including the out-of-library sine.
- `comparator_metrics.csv` includes the proposed selected-support workflow row alongside oracle-OLS, sparse-linear, and nonlinear surrogate.
- `reproduction_log.md` records: rfm-pipeline commit/pin, bsm-public-rf commit, exact `pixi run` command, `pixi run pytest tests/` gate result, master seed, per-artifact SHA-256 hashes, per-scenario replicate status (attempted/completed/failed), and the deliberate scale-reduction rationale.
- `--quick` smoke mode keeps the gate fast; a full `--seed 42` run remains runnable locally in minutes.

**Acceptance criteria:**
- [ ] `pixi run pytest tests/ --tb=short -q` passes.
- [ ] Running `--quick` writes `replicate_records.csv`, `fwer_calibration.csv` (with α=0.05 and `passes_calibration`), `recovery_estimands.csv`, `comparator_metrics.csv`, and a `reproduction_log.md` containing commit, command, gate result, and artifact hashes.
- [ ] `fwer_calibration.csv` has more than one replicate per scenario (replication actually executed), and no code asserts control from CI coverage alone.

### Pre-release follow-up (R4B)

- `pixi.toml` resolves `rfm-pipeline` via a local editable path
  (`{path = "../rfm-pipeline", editable = true}`) so the recovery study can use
  the unpushed exact-maxT wiring (rfm-pipeline `8d18878`). Before any public
  release, push that rfm-pipeline commit and repin `pixi.toml` to a fetchable
  rev, then relock. The reproduction log records the current pin verbatim.
- Full 30,000-run BSM production rerun with the exact interaction method
  (to replace the main-result stand-in artifacts) remains TABLED (AUs).
