# Review Register — BSM Public RF

Durable record of audit findings requiring follow-up. Newest first.

______________________________________________________________________

## 2026-06-07 — Round 21: HPC reduce entrypoint imports absent tool module

- **Severity:** HIGH (when invoked from a pip-installed rfm-pipeline). `pixi run rfm-hpc-reduce --help` failed at import time in both rfm-pipeline (source tree) and bsm-public-rf (pip install): pinned `rfm_pipeline.hpc_reduce` imports `tools.run_manuscript_pipeline`, but `tools/` is not part of the installed package.
- **Round-21 partial fix (rfm-pipeline 7eea471):** corrected `REPO_ROOT = Path(__file__).resolve().parent.parent.parent` (was `.parent.parent`, which only added `src/` to sys.path). Now `rfm-hpc-reduce --help` works from a source-tree checkout. Verified locally.
- **bsm-public-rf:** pin bumped to `7eea471`. **Install-mode invocation of `rfm-hpc-reduce` still fails** because `tools/` does not ship in the installed package. This is **not** part of any actual workflow — `slurm_array_runner.py` templates always `cd "{repo_root}"` (an rfm-pipeline source checkout) before invoking `rfm-hpc-reduce`, so HPC nodes use the source-tree path. The install-mode failure is a latent footgun only.
- **Required follow-up for full fix:** move `_load_empirical_null_screening_result`, `_load_interaction_discovery_result`, `_load_nonlinear_discovery_result`, `_load_output_conditioning_result`, `_load_sparse_selection_result`, `_load_tables`, and `config_to_legacy_case_study` from `tools/run_manuscript_pipeline.py` into a proper module under `src/rfm_pipeline/` (e.g., `src/rfm_pipeline/manuscript_pipeline_helpers.py`); have `tools/run_manuscript_pipeline.py` re-export for back-compat. Add `rfm-hpc-reduce --help` and `rfm-hpc-worker --help` smoke tests in CI. ~30-50 LoC + tests.
______________________________________________________________________

## 2026-06-07 — Round 20: pullback bundle helper missing

- **Severity:** HIGH. `scripts/kestrel/pull_hpc_artifacts_bundle.sh` calls `tools/hpc_bundle_manifest.py` for create/analyze/metadata, but that file is absent from HEAD and `git ls-files`. `pixi run hpc-workflow ... --action collect --dry-run` still emits this broken command, so real collect/study-package pullback fails after HPC work completes. Required follow-up: restore/track the helper or replace the pullback path with existing `rfm_pipeline` bundle tooling and add a local test that referenced helper paths exist.

______________________________________________________________________

## 2026-06-07 — Round 16: HPC dry-run only validates 1 of 6 stages

- **Severity:** HIGH (silent false-confidence in reproducibility).
- **Evidence:** `prepare_full_pipeline_artifacts: true` in
  `configs/hpc/kestrel_publication_orchestration.yml` and
  `configs/hpc/dev/kestrel_workflow_small_distributed.yml` has **zero code
  consumers** in `scripts/hpc_workflow.py` (grep confirmed). Only
  `stage:` and `prepare_interaction_inputs` are honoured. The
  documented dry-run cascade through all 6 stages does not happen via
  the orchestration YAML — only `output_conditioning` is validated.
- **Mechanical fix applied (round 16):** dropped the dead key from both
  YAMLs; rewrote the misleading "Generate all 6 stages" comment to state
  the actual cascade contract (per-stage re-submit OR the
  `scripts/kestrel/controller_publication_full_dataset_distributed.sh` wrapper looping over the 6-stage
  tuple).
- **Required follow-up (not yet implemented):** either
  (a) implement a true full-pipeline cascade flag in
  `scripts/hpc_workflow.py` (orchestrator iterates STAGES, waits for
  each, submits next), with tests; OR
  (b) document the per-stage manual re-submit workflow in the
  publication-run README and add a wrapper that calls submit
  N times in sequence.
- **Why this matters:** a new user following the publication-run
  workflow will dry-run-validate stage 1, submit, and not realise
  stages 2-6 require additional invocations.

______________________________________________________________________

## 2026-06-07 — Round 16: monitor script polling loop missing

- **Severity:** MED.
- **Evidence:** `scripts/publication-run/03_monitor_publication_run.sh`
  accepted `[interval]` arg and advertised "check every X minutes"
  semantics but had no polling loop — single status check then exit.
- **Fix applied (round 16):** added optional polling loop. No arg →
  one-shot. With arg N → poll every N seconds until Ctrl-C. Trap on
  SIGINT for clean exit.

______________________________________________________________________

## 2026-06-07 — Deferred (multi-round)

- **Round 14 #4 (MED):** `configs/manuscript_runtime.yml`
  `manuscript_section:` strings stale vs v22 §3.1-3.6 numbering.
  ~9 yaml lines, doc-only.
- **Round 14 #5 (LOW):** `scripts/publication-run/README.md` and
  `QUICKSTART.md` overload "Stage" for both wrapper scripts and
  pipeline STAGES tuple. Terminology rename, not mechanical.
- **Round 15 (LOW):** `README.md` Zenodo DOI placeholder — waits on
  submission.
