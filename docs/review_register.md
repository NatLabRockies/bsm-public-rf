# Review Register — BSM Public RF

Durable record of audit findings requiring follow-up. Newest first.

## 2026-08-11 — G11 integration reconciliation remains blocked

- **Severity:** BLOCKER (integration/review sequencing). Isolated worktree
  `/Users/dhetting/src/bsm-public-rf-g11-integration` was created at required
  G10 base `47849a518fa7a90dc29ec5bff41d86774768beac`; its existing G10 repair
  diff is preserved there without changing the source worktree.
- **Retained:** compatible G11-G0 config from `c2d6731`,
  `configs/g11_campaign_contract.toml`. It is `OPEN`, uses
  `max_stat_adjusted_p_mc`, `B_screen=3199`, `B_interaction=999`, and all
  scenarios retain 158 continuous plus two binary inputs. It has no scheduler
  command or result claim.
- **Rejected:** control commits `5e5bfcc` and `fee4368` conflict with the
  newer uncommitted G10 control snapshot/dispatch bundle. The latter must remain
  authoritative because it preserves the G10 no-results/no-PASS controls.
  `c347370` is also rejected: its HPC manifest pins displaced commit identities
  and embeds `sbatch`, so it would be stale and cannot satisfy no-submit
  readiness in this integration worktree.
- **Validation:** G11 config static assertions passed; `tests/test_bsm_recovery_fwer.py`
  passed (18). The combined targeted run had 24 passing tests and five
  failures solely for absent regenerated PDF figures. Figures/results were not
  regenerated or restored because they are quarantined, and full gates are red.
  No commit, push, scheduler submission, manuscript-result edit, or PASS claim.

______________________________________________________________________

## 2026-08-10 — G0/B pre-execution control repair

- **Severity:** BLOCKER (scientific execution). The recovery-study controls were
  rebuilt from the current handoff in a fresh worktree. G0, A, and B remain
  **OPEN**.
- **Implemented:** tracked control snapshot + checksum manifest; strict
  canonical contract; scenario-keyed development seed ledger; typed 160-field
  DGP; four binary-cell validation in both splits; bounded row-level
  heteroscedasticity; typed truth; canonical pair construction; fail-closed
  terminal-ledger validation; null aggregation that retains empty-family
  records and permits one-pair families; status-only manifests.
- **Quarantine:** unsupported recovery-study CSV/JSON/log outputs were removed
  rather than relabeled as evidence. No calibration, scheduler, HPC,
  production, holdout, or result-generation task was run.
- **Remaining blockers:** the paired generic production adapter/reducer must
  reach its pinned clean commit and receive independent G0/A review before any
  development execution or later gate is considered.

______________________________________________________________________

## 2026-07-30 — Corrected 30k run promoted: canonical re-baseline 123 → 245

- **Severity:** HIGH (headline scientific numbers). The corrected main-effect-conditioned interaction method (rfm-pipeline 0965994) 30k Kestrel run (`publication_full_dataset_distributed_20260723`) supersedes the prior 123-feature canonical run. Artifacts, canonical config, consistency tests, and the manuscript were re-baselined.
- **Number changes (old 123-run → corrected 245-run):** final predictors 123→**245** (main 52→**63**, interaction 49→**159**, transformation 22→**23**); enriched candidate 157→**367** (70 first-order + 272 interactions + 25 transforms); stable/HC3-retained 157→**360**; delta-pruned 34→**115**; interaction pairs discovered 62→**272**; holdout NRMSE 0.0714→**0.0679** (CI [0.0699,0.0724]→**[0.0663,0.0690]**); penalized OLS 0.0706→**0.0682**. Unchanged: 23,495/9,954 outputs, 17 PCA comps, 70 screened terms, null 0.1653, main-effects/screened OLS 0.0812, seed 123.
- **NARRATIVE CHANGE requiring author review:** old text claimed "the marginal-impact pruning step is the *only* stage that removes enriched terms." In the corrected run sparse selection + stability also removes 7 terms (367→360), so §Results and §Reduction-counts prose were rewritten to state both sparse-selection (7) and delta-pruning (115) remove terms while HC3 removes none. Interactions are now the majority of the support (159/245 = 65%). Author should confirm the reframing reads correctly.
- **Tooling fix (`scripts/build_metadata.py`):** `_strip_transform` / `cross_reference_inputs` only handled prefix transform naming (`sqrt_x`); the pipeline emits suffixes (`x_sqrt/_sq/_log1p/_inv`), so 23/245 transform features were mislabeled `identity` and self-referenced their base input. Added suffix handling + focused tests (`tests/test_build_metadata_transforms.py`, 10 pass). Metadata regenerated: 0/245 unmatched.
- **Stale artifact REMOVED:** `artifacts/final_model/feature_drop_noref_nrmse_impact_full30k.csv` (506 rows, prior 132-model) was an orphaned one-off diagnostic — the corrected pipeline does not emit it (Kestrel `feature_pruning` stage produces only `feature_pruning_impact.csv`), it is not manuscript-cited, not referenced by any test or reproduce script, and is not regenerable without a bespoke full-30k-data script. Removed from the release bundle (`git rm`) and dropped from the final_model README rather than ship stale/non-reproducible values.
- **Config-echo correction:** `final_ols_summary.csv` carried pipeline-echoed `manuscript_*_reference` cells = 132/0.0721 (from a stale Kestrel case-study config, matching neither canonical). Corrected to 245/0.0679 to match the re-baselined manuscript; actual run outputs untouched.
- **Validation:** full bsm-public-rf suite 53 pass (incl. re-baselined `test_artifact_bundle_consistency.py`, `test_manuscript_config_reconciliation.py`). Figures + metadata regenerated via `pixi run reproduce-artifacts` / `build_metadata.py`.
- **Disposition:** artifacts + config + tests updated in bsm-public-rf; `manuscript.tex` updated in bsm-public-rf-manuscript. Both **local only, uncommitted** (advisory repo — awaiting owner approval to commit).

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

______________________________________________________________________

## 2026-06-08 — Round 23: cascade shard-dir collision + dependency gap

- **Severity:** HIGH (both rfm-pipeline and bsm-public-rf).
- **Evidence:**
  - rfm `hpc_submit.py:163` set `output_root = artifact_dir/hpc_shards`
    regardless of `--stage`, so cascade stages shared `_SUCCESS.json`
    markers — stage 2's `_find_incomplete_task_ids` would treat all
    shards as already complete and skip real work.
  - rfm `build_remote_submit_commands` emitted N pixi commands per
    cascade run with no SLURM `--dependency=afterok` chain, allowing
    stage N+1 to start before stage N reduce completes (race on
    canonical stage artifact).
  - bsm orchestration consumed the flat command list with no way to
    capture or thread reduce job IDs between stages.
  - bsm pullback used `bsm_*.out` log glob (job names are `rfm_*`),
    `empirical_null_screen` (HPC name is `empirical_null_screening`),
    and `cpu_nodes_<n>/hpc_scripts/manifest.jsonl` (cascade uses
    `cpu_nodes_<n>_<stage>/hpc_scripts/manifest.jsonl`).
  - bsm 04-collect `find -name "$stage"` matched nested non-canonical
    directories.
  - bsm `--dry-run` help still said "without executing" after r22 made
    it always SSH-execute.
- **CLOSED (round 23, rfm-pipeline 8ca839d + 7c33036, bsm ef49f17):**
  - rfm: per-stage shard output dirs (`hpc_shards_<stage>`);
    `rfm-hpc-submit --depends-on-job-id` flag injects
    `#SBATCH --dependency=afterok:<id>` into array and GPU array
    scripts; emits `RFM_HPC_SUBMIT_REDUCE_JOB_ID=<id>` marker on
    stdout; new `build_remote_submit_command_groups` returns
    `[(stage|None, [cmds])]` so orchestrators can chain; status
    command emits per-stage `hpc_shards_<stage>` entries; validation
    picks stage XOR stages; prep block keys off `effective_stages()`.
  - bsm: orchestrator uses the grouped builder, captures each cascade
    stage's reduce job id from the marker line, and rewrites the next
    stage's commands to append `--depends-on-job-id <id>`. Pullback
    log glob → `rfm_*`, stage name fixed to `empirical_null_screening`,
    per-stage script-dir pullback added. 04-collect tightened to
    depth-2 stage path check. `--dry-run` help rewritten with SSH
    prereq.
  - Doc drift: `docs/HPC_DISTRIBUTED_EXECUTION.md` `rfm-hpc-shard`
    typo → `rfm-hpc-worker`; rfm `README.md:94` stage names aligned
    with `_VALID_STAGES`; `paper/paper.md:107` "shipped pre-fitted
    Random Forest" rephrased to "regenerated from collected runs via
    `plot_sensitivity_rf_figures.py`".
- **Tests:** rfm 462 pass / 11 skip (added per-stage shard test +
  array-dependency injection tests + grouped-builder test); bsm 20
  pass; orchestrator smoke-import + marker parser verified.

______________________________________________________________________

## 2026-06-07 — Round 24: orchestrator parity, marker robustness, name drift

- **Severity:** HIGH (both repos).
- **Evidence:**
  - rfm `tools/run_hpc_workflow.py` never adopted the round-23
    grouped builder; the rfm orchestrator submitted cascade stages
    via the flat `build_remote_submit_commands` list with no
    dependency chaining, so jobs raced ahead of upstream reduce.
  - rfm `tools/hpc_bundle_manifest.py:463` scanned legacy
    `hpc_shards` only; missed per-stage `hpc_shards_<stage>` outputs
    after the round-23 layout change.
  - rfm `src/rfm_pipeline/hpc_submit.py:343` still built the manifest
    `output_path` against the legacy un-suffixed `hpc_shards`
    directory while workers now write to `hpc_shards_<stage>`.
  - rfm `_make_submit_all_script` reduce-only path referenced
    `ARRAY_JOB_ID` even when no array job was generated (would be
    unbound).
  - rfm `pixi.toml` task `hpc-small-test` and
    `docs/RUNNING_MANUSCRIPT_REPRODUCTION.md:57` pointed at
    `scripts/kestrel/run_small_distributed_test_local.sh` which does
    not exist in the repository (the entire `scripts/kestrel/`
    directory is absent on the rfm side).
  - bsm `scripts/hpc_workflow.py:368` silently ignored a missing /
    malformed `RFM_HPC_SUBMIT_REDUCE_JOB_ID` marker, leaving
    `prev_reduce_job_id` stale; the next cascade stage would then
    chain onto an earlier stage's reduce and race against the
    current stage.
  - bsm `_parse_reduce_job_id` returned the FIRST marker, not the
    last; sparse re-submits print the marker more than once and
    only the last reflects the actually-submitted reduce.
  - bsm pullback + 04-collect used HPC stage name
    `empirical_null_screening` for both shard dirs AND artifact
    dirs, but the canonical post-reduce artifact dir written by
    `manuscript_pipeline_helpers` is `empirical_null_screen`
    (no `-ing`). Per-stage pullback therefore copied a nonexistent
    `empirical_null_screening` directory and the 04-collect
    completeness check would never find it in correctly-collected
    runs.
  - bsm `--dry-run --generate-only` still SSHed despite docs saying
    fully local.
  - bsm tests had zero coverage for the cascade chaining helpers.
- **CLOSED (round 24, rfm-pipeline c9dbc7e, bsm pending commit):**
  - New shared module `rfm_pipeline/hpc_cascade.py` exposes
    `parse_reduce_job_id` (returns LAST marker, skips malformed),
    `inject_dependency_flag` (idempotent), and
    `CascadeChainError`. Both orchestrators import them so behavior
    cannot drift.
  - rfm `tools/run_hpc_workflow.py` now mirrors the bsm cascade
    pattern (grouped builder + capture + chain) and raises
    `CascadeChainError` on missing marker.
  - rfm `hpc_submit.py` `_build_fresh_manifest` writes the manifest
    against `hpc_shards_<stage>` to match the per-stage layout.
  - rfm `_make_submit_all_script` reduce-only path submits the
    reduce directly with no stale `ARRAY_JOB_ID` reference; log
    glob `bsm_*` → `rfm_*`.
  - rfm `tools/hpc_bundle_manifest.py` scans
    `hpc_shards_interaction_discovery` (cascade) with legacy
    `hpc_shards` fallback; log glob accepts both `rfm_*` and
    `bsm_*`.
  - rfm `pixi.toml` `hpc-small-test` task removed; doc snippet
    replaced with an equivalent `hpc-workflow --generate-only
    --dry-run` invocation.
  - bsm orchestrator: deleted local parser; imports shared helpers;
    raises `CascadeChainError` on missing marker; honors
    `--dry-run --generate-only` by skipping SSH (`>>> [skip ssh:
    ...]` log line so the operator can still review the commands).
  - bsm pullback + 04-collect: two parallel lists distinguish HPC
    stage names (for shard dirs / SLURM logs) from canonical
    artifact dir names (for `${run_dir}/${artifact_dir}` copy and
    completeness check).
  - bsm `--dry-run` help text updated to document the local-only
    `--dry-run --generate-only` combination.
  - New `bsm tests/test_cascade_chaining.py` (6 cases) covers
    helper-import wiring, last-marker semantics, idempotent
    injection, and `CascadeChainError` semantics.
- **Tests:** rfm 473 pass / 11 skipped (added test_hpc_cascade.py);
  bsm 26 pass (added test_cascade_chaining.py).

______________________________________________________________________

## 2026-06-07 — Round 25: collect exit code, pullback hardening, provenance link

- **Severity:** MED.
- **Evidence:**
  - `scripts/publication-run/04_collect_publication_artifacts.sh`
    printed "⚠️ Some artifacts missing" and exited 0, so the
    master orchestrator's downstream "WORKFLOW COMPLETE" banner
    would fire on incomplete collection.
  - `docs/manuscript_feature_catalog_provenance.md:73` referenced
    `docs/manuscripts/manuscript_impact_log.md` without making
    clear that the file lives in the upstream `rfm-pipeline` repo
    (this repo has no `docs/manuscripts/` directory). A new reader
    auditing the catalog could not locate the impact log.
  - `scripts/kestrel/pull_hpc_artifacts_bundle.sh:430` parallel
    arrays `hpc_stages[]` and `artifact_dirs[]` had no length
    guard; a single-array edit could silently mis-map HPC stage
    names to writer dir names.
  - `scripts/kestrel/pull_hpc_artifacts_bundle.sh:478` duplicated
    the cascade stage list for the per-stage log copy loop,
    reintroducing drift risk.
- **CLOSED (round 25, bsm-public-rf pending commit):**
  - `04_collect_publication_artifacts.sh` now `exit 1`s after the
    missing-artifacts summary so the master orchestrator (set
    -euo pipefail) halts before the success banner.
  - `manuscript_feature_catalog_provenance.md` makes the upstream
    repo path explicit and links to the GitHub URL.
  - `pull_hpc_artifacts_bundle.sh` asserts
    `${#hpc_stages[@]} == ${#artifact_dirs[@]}` and exits 2 with a
    clear maintainer message on mismatch.
  - Log-copy loop iterates `${hpc_stages[@]}` so the canonical
    stage list is defined exactly once in `_per_stage_files_copy`.
- **Tests:** 26 pass; bash syntax checks pass for both modified
  scripts.

______________________________________________________________________

## 2026-06-07 — Round 26: multi-tier cascade chain + summarizer port + SSH safety

- **Severity:** HIGH (chaining bug, mirrors rfm r26).
- **Evidence:**
  - `scripts/hpc_workflow.py` chained the next cascade stage to only
    the LAST tier's reduce job id (same bug class as rfm r26#1).
  - `tools/hpc_bundle_manifest.py` was the pre-r25-followup version;
    cascade runs got `scripts_missing` rows because the summarizer
    only knew about `hpc_shards_interaction_discovery`.
  - `scripts/publication-run/04_collect_publication_artifacts.sh`:
    when `$EXTRACT_DIR/runs` was missing entirely (manifest-only
    bundle), all per-stage checks were skipped and the script
    reported "All critical artifacts present" purely on the
    strength of the manifest files.
  - `tools/hpc_bundle_manifest.py` `_collect_stage_metrics` only
    looked at `runs/<target>/run_artifacts/<stage>/`. The
    `reporting_bundle` pullback mode copies stages directly under
    `runs/<target>/<stage>/`, so stage-metric columns were dropped
    from bundles produced via that mode.
  - `scripts/kestrel/status_publication_full_dataset_distributed.sh`
    interpolated `${STUDY_ROOT}` directly into the remote SSH
    command string; spaces or shell metacharacters in
    `--study-root` could break the script or inject commands.
  - `scripts/kestrel/pull_hpc_artifacts_bundle.sh` array-length
    guard accepted equal-but-empty arrays (a maintainer edit that
    cleared both lists silently copied zero stage dirs/logs).
  - `scripts/kestrel/controller_publication_full_dataset_distributed.sh`
    had ten parallel per-stage resource arrays (`N_SHARDS`,
    `WALLTIME`, `MAX_CONCURRENT`, etc.) and no length guard —
    drift would silently misassign resources to wrong stages.
- **CLOSED (round 26, bsm-public-rf pending commit):**
  - Bumped rfm-pipeline pin → 25ef483 to pick up
    `parse_all_reduce_job_ids`, multi-id `inject_dependency_flag`,
    and the cascade-aware summarizer helpers.
  - `scripts/hpc_workflow.py` now collects one id per per-tier
    invocation and threads the FULL list into the next stage as a
    colon list. `CascadeChainError` fires on partial markers too.
  - `tools/hpc_bundle_manifest.py` replaced wholesale with the
    rfm-pipeline r26 version: `_discover_stages_in_run_dir`,
    `_stages_to_summarize`, `_stage_suffixed_manifest`,
    cascade-aware `_summarize_target` with `stage=` parameter,
    cascade-aware `_collect_stage_metrics` (run_artifacts/ nested
    OR flat reporting_bundle layout).
  - `04_collect_publication_artifacts.sh` now flips
    `ALL_PRESENT=false` AND prints an explicit "MISSING: runs/"
    line when no per-target stage dirs exist (so exit 1 from r25
    actually fires for manifest-only bundles).
  - `pull_hpc_artifacts_bundle.sh` array guard now also rejects
    empty arrays (length-> 0 check before length-equality check).
  - `status_publication_full_dataset_distributed.sh` rewritten to
    pass STUDY_ROOT / STUDY_ID as POSITIONAL args to `bash -s`
    via a quoted heredoc — no more inline interpolation, no more
    triple-backslash escaping; metacharacters in --study-root are
    inert.
  - `controller_publication_full_dataset_distributed.sh` asserts
    every per-stage resource array length matches STAGES length
    via a `declare -n` loop (bash 4.3+, Kestrel default).
- **Tests:** 26 pass; bash syntax checks pass on all four
  modified scripts.
