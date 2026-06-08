# Review Register — BSM Public RF

Durable record of audit findings requiring follow-up. Newest first.

______________________________________________________________________

## 2026-06-07 — Round 21: HPC reduce entrypoint imports absent tool module

- **Severity:** HIGH (when invoked from a pip-installed rfm-pipeline). `pixi run rfm-hpc-reduce --help` failed at import time in both rfm-pipeline (source tree) and bsm-public-rf (pip install): pinned `rfm_pipeline.hpc_reduce` imports `tools.run_manuscript_pipeline`, but `tools/` is not part of the installed package.
- **Round-21 partial fix (rfm-pipeline 7eea471):** corrected `REPO_ROOT = Path(__file__).resolve().parent.parent.parent` (was `.parent.parent`, which only added `src/` to sys.path). Now `rfm-hpc-reduce --help` works from a source-tree checkout. Verified locally.
- **CLOSED (round 22, rfm-pipeline 6826edd, bsm-public-rf 18b4555):** helpers moved into `src/rfm_pipeline/manuscript_pipeline_helpers.py` (installable package). `hpc_reduce.py` now imports cleanly without sys.path hacks. `pixi run rfm-hpc-reduce --help` verified in install mode under bsm-public-rf. Smoke tests added in rfm `tests/test_docs_snippets_smoke.py` to guard the regression.
- **Further cleanup (rfm-pipeline e53f9c0):** duplicate helper bodies removed from `tools/run_manuscript_pipeline.py`; that script now imports from the package (-370 LoC, single source of truth).
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
  the actual cascade contract.
- **CLOSED (round 22, rfm-pipeline b6ed313 + bsm orchestration update):**
  added `execution.stages` (ordered list) to `HpcExecutionConfig` and
  `build_remote_submit_commands`; orchestrator now emits one
  `rfm-hpc-submit` per (stage, tier) with per-stage output dirs.
  `configs/hpc/kestrel_publication_orchestration.yml` updated to use
  `stages:` list for all 6 stages. **Companion HIGH (round 22):**
  `scripts/hpc_workflow.py` previously short-circuited remote execution
  when `--dry-run`, so the remote `rfm-hpc-submit --dry-run` (which
  generates the SLURM scripts for inspection) never ran — fixed by
  always executing the submit SSH call; the safety comes from the
  remote command's own `--dry-run` flag (commit pending in bsm).
  Cascade + dry-run propagation guarded by new tests
  `tests/test_hpc_workflow_orchestration.py::
  test_submit_commands_cascade_over_stages_list` and
  `test_submit_commands_dry_run_propagates_to_rfm_hpc_submit`.

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
