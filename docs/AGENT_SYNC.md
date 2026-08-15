# Agent Sync

## SESSION STATE — 2026-08-11 — G11-HPC-S1 paired sync note (uncommitted)

- This BSM worktree remains dispatch-blocked for G11:
  `scheduler_submission_permitted: false`.
- Historical 16,000-AU/15,152-AU package claim is superseded. The live paired
  full provisional package reports 175,449 requested AUs before pilot
  telemetry; production remains locked until pilot-selected resources produce
  a regenerated envelope that fits the same-day remaining allocation.
- Paired RFM slice `/Users/dhetting/src/rfm-pipeline-g11-integration`
  generated a content-addressed NO-SUBMIT Kestrel package only. No BSM
  execution, artifact regeneration, `sbatch`, commit, or push occurred here.
- The BSM pre-HPC suite does not require five future authoritative release
  figure PDFs. `scripts/reproduce_artifacts.py --validate-only` retains the
  strict later-release check for all five PDFs, including missing and
  truncated-file rejection. No stale figures were generated or promoted.

## SESSION STATE — 2026-08-12 — G11 integration implementation (NO-SUBMIT)

- Current branch: `g11-integration-reconcile`; changes are uncommitted and no
  scheduler command, commit, or push occurred.
- `configs/g11_campaign_contract.toml` records the publication G11-v9 contract,
  including the 6,400-record null/strong/stress inventory, 158 continuous plus
  two binary predictors, B-screen=3,199, initial B-interaction=999, 20
  resolution records, fixed-family supplement, comparators, retry policy, and
  2,000 bootstrap draws.
- `scripts/g11_campaign_adapter.py` executes manifest-bound resolution,
  Gate-B/fixed-family, Gate-C, and applied stages through the pinned RFM path.
  It validates the phase authorization and resource freeze and emits
  content-addressed terminal/scientific artifacts. Gate C reuses Gate-B strong
  records and adds only the four stress regimes.
- `scripts/prepare_g11_applied_data.py` prepares the 30,000-row split with a
  sealed 1,500-row holdout and records 160 inputs (158 continuous, two binary)
  plus 23,495 outputs. Adaptive jobs receive training bytes only; the existing
  holdout is not described as previously contaminated. The preparer rejects
  X/Y/assignment row-order drift and non-0/1 scenario values, and the prepared
  manifest binds the exact preparer bytes.
- Legacy publication submission entry points and scheduler defaults are
  fail-closed against G11 so they cannot silently run the superseded B=201/
  B=31/100-bootstrap route. The old method contract is preserved under
  `configs/rejected_history/`.
- Validation: the complete BSM test suite passes (`75 passed`); Ruff format and
  lint pass on the G11 adapter, splitter, driver, and tests; guarded shell
  entrypoints pass `bash -n`; `git diff --check` passes.
- Paired hashes in RFM `configs/hpc/g11_kestrel_campaign.yml` currently match
  the adapter, recovery driver, DGP contract, and applied config bytes. The
  adapter requires comparators only for strong/stress recovery records and
  validates schema-v2 run/source/lock/inventory-bound authorization before
  every scientific operation.
- Still blocked before any HPC submission: commit and install exact clean RFM/
  BSM checkouts, prepare and hash the real applied-data manifest, record
  same-day allocation/storage/inode evidence, run exact `sbatch --test-only`,
  and obtain separate user authorization for scheduler submission.

## SESSION STATE — 2026-08-14 — final execution/release closure (uncommitted)

- The accepted sizing pilot `g11-pilot-final-sizing-20260814f` completed;
  none of the changes in this section has altered its source-bound RFM commit,
  submitted another scientific phase, or changed its evidence root.
- `scripts/g11_final_execution.py` now provides one restartable controller for
  accepted-pilot accounting, development resolution, fresh confirmatory
  packaging, 25,000-AU certification, Gate B, Gate P, Gate C, and bounded
  publication compilation. Every submission requires literal `--execute`;
  same-day preflight occurs immediately before submission; existing completion
  records, reducer bytes, and budget certificates are revalidated on restart.
- `advance` and `watch` accept a fresh invocation-level `--remaining-au` so a
  later phase never depends on the initialization-day allocation snapshot. A
  changed `aus_report` value stops before preflight; restarting with the fresh
  integer continues the same immutable campaign without resubmitting work.
- Phase submission writes and fsyncs an append-only scheduler journal after
  every `sbatch` response so a partial submission cannot lose returned job IDs
  or silently resubmit. Exact terminal acceptance requires `COMPLETED/0:0` for
  every non-array job and every expected array task; an optional synthetic
  array-parent row may not substitute for task coverage.
- Whole-campaign accounting now reserves 5 AUs for a final one-CPU,
  30-minute, 8-GB `shared` publication-compilation job. That job creates the
  compact publication bundle on Kestrel while all immutable package/result
  paths remain available; all subsequent work is local and consumes no AUs.

## SESSION STATE — 2026-08-15 — fixed-family publication amendment (uncommitted)

- The successfully completed accepted pilot is
  `g11-pilot-final-sizing-20260814f`; its 63 steps and original 1,000-count
  pilot-base contract remain immutable evidence. Prior rejected attempts cost
  exactly 192.55 AUs, and the accepted pilot cost 90.36944444444445 AUs.
- Before confirmatory execution, one hashed amendment changes only
  `fixed_family_replicates` from 1,000 to 200. The five primary null regimes
  remain at 1,000 each. The 10/100/1,000-pair nested supplement uses all 200
  precommitted identities, one-sided 95% Wilson upper-bound <=0.09, and largest
  passing event count 11. No interim test, optional stopping, or incremental
  standby extension is permitted.
- The final package and budget certificate bind the amendment hash. Package
  creation replaces completed pilot/resolution estimates with exact observed
  AUs, applies the shared 20% reserve only to unexecuted work, and remains
  fail-closed above 25,000 AUs after prior rejected attempts and the bounded
  5-AU publication job. The retained B=999 projection reserves 24,301 AUs for
  remaining confirmatory work and leaves at most 411.0805555555562 AUs for
  actual resolution. The B=1,998 branch requests 48,499 AUs for remaining work
  and is therefore an unconditional pre-confirmatory stop. No scheduler job was
  submitted by this amendment work.
- Scaling the accepted 6,342-second interaction pilot by the resolution's
  measured pair-draw ratio forecasts about 223 AUs including reducer allowance,
  below the 411.08-AU B=999 limit; admission still uses exact post-resolution
  `sacct`, never that forecast.
- Each confirmatory phase now receives an immutable rolling budget guard that
  substitutes observed AUs for completed phases and requires the current
  phase's complete scheduler-requested walltime charge to fit under the cap.
  This prevents an overrun in one phase from leaking into a later submission.
- `scripts/build_g11_publication_artifacts.py` compiles all publication tables,
  23,495-output ledgers, coefficient products, 11 figure-data surfaces,
  generated manuscript values/tables, and provenance. Every reducer artifact
  and raw recovery terminal record is hash-bound to its packaged reducer and
  worker result before use.
- `scripts/audit_g11_publication_artifacts.py`,
  `scripts/install_g11_manuscript_artifacts.py`, and
  `scripts/finalize_g11_manuscript_release.py` provide an independent audit,
  atomic manuscript installation, deterministic figure build, and local
  `manuscript.pdf`/`coverpage.pdf` release gate. The terminal local token is
  `JDS_RELEASE_BUILD_PASS`.
- Full operator commands, acceptance criteria, transfer instructions, and the
  zero-AU local finish are recorded in `docs/G11_FINAL_EXECUTION.md`.
- Validation currently passes: all 105 BSM repository tests, scoped Ruff
  lint/format, direct CLI entry-point smoke checks, all 266 manuscript
  repository tests, and successful 21-page manuscript plus one-page cover
  compilation with no unresolved citations or references.
  The release audit independently recomputes the raw-scale coefficient and
  intercept algebra from the frozen model, and the final artifact submission
  fsyncs its returned scheduler ID before writing the submission record. Final
  local success also requires deterministic, validated JDS source and
  publication-supplement archives. Final scientific values remain generated
  surfaces until the confirmatory campaign completes.
- The local reproduction layer now applies two tested text-only corrections
  after the pilot-bound RFM renderer returns: the per-output CDF uses a compact
  in-frame maximum annotation, and the module heatmap is titled `Interaction
  endpoint counts`. Plot geometry and scientific values are unchanged, and no
  RFM source/pin used by the active pilot was modified.
- A true local release rehearsal also passes using a production-sized synthetic
  23,495-output bundle and the real compiler, figure renderer, independent
  numerical audit, installer, LaTeX toolchain, and archive writer. It produced
  44 checksummed artifacts, 11 SVGs, a 20-page synthetic-result manuscript, a
  one-page cover, and internally valid source/supplement ZIPs. The supplement
  now carries its own reproduction guide and license so it remains usable when
  separated from this repository.
- Live no-submit initialization exposed and closed two related environment
  hazards: the older BSM Pixi environment imported a stale installed RFM
  package, while the accepted scientific checkout intentionally predates the
  non-scientific pilot-accounting schedule-hash repair. The final controller
  now binds and hashes a separate `5d1ff14` controller checkout while package
  source hashing and worker execution remain bound to the accepted `fd12fd5`
  scientific checkout. The runbook supplies that separation explicitly and
  the controller rejects a changed or wrongly imported controller module. The
  controller import path changes only in-process; every real Slurm submission
  strips `PYTHONPATH`/`PYTHONHOME`, so workers remain bound to the accepted
  scientific checkout. The manifest records clean Git revisions and complete
  RFM-controller/BSM-script tree hashes. Recomputed pilot evidence must match
  the accepted freeze in every scientific and numeric field; the sole
  permitted difference is newer explanatory `accounting_rule` prose, in which
  case the accepted self-hashed freeze bytes remain authoritative. The
  publication job uses
  the scientific RFM Python environment rather than the stale BSM environment.
  A partial multi-`sbatch` failure cancels every returned job ID and writes a
  self-hashed abort record. Because `nationalpfa` is valid in Slurm but omitted
  from `aus_report` for this non-lead user, live smoke uses the configured
  25,000 ceiling while the separate campaign certificate and rolling guards
  subtract all sunk and observed AUs. No scheduler job was submitted by either
  rejected initialization.

## SESSION STATE — 2026-08-15 — final-submission adversarial hardening

- Scientific submission remains frozen while the exact final controller bytes
  complete local and Kestrel no-submit validation. No final scientific job was
  submitted by this review.
- Development package generation is now structurally resolution-only. Its
  immutable admission guard requires the complete resolution walltime request,
  the accepted pilot, all rejected attempts, the 5-AU publication reserve, and
  the full B=999 confirmatory reserve to fit below 25,000 AUs before resolution
  can be authorized.
- The 65-CPU, 6-GiB resolution workers retain their pilot-sized 2:43:33
  walltime but use Kestrel's 104-core `shared` nodes. This removes billing for
  the unused 39 cores and makes the full resolution walltime request fit while
  leaving the scientific computation and resource envelope unchanged.
- Generated worker/audit/reducer scripts use package-local precreated Slurm log
  directories, clear Python import overrides, and bind their SHA-256 values in
  the submission plan. Same-day preflight and authorization bind the exact plan
  hash, and the submitter rehashes every script before its first `sbatch`.
- Post-pilot arrays are accepted and charged from every expected task row;
  missing, extra, failed, or nonzero-exit tasks stop downstream work. Shared
  jobs use their request-bound node-equivalent fraction rather than charging a
  full node solely because `AllocNodes` reports one.
- The publication compiler has its own same-day `sbatch --test-only` evidence,
  binds that evidence into its submission record, journals the returned job ID,
  and refuses stale or partial evidence on restart.
- Focused controller tests pass (28), the complete BSM suite passes (112), and
  all 112 tests also pass under the scientific RFM Pixi interpreter with
  `PYTHONPATH`/`PYTHONHOME` removed and user-site imports disabled. The complete
  RFM repository gate also passes; fresh Kestrel replay remains required before
  submission.
- A prospective B=999 confirmatory-package audit then exposed a blocking
  mismatch between the generic package gate and the later exact budget
  certificate: the generic gate re-reserved estimates for already completed
  pilot and resolution work and rejected a 25,215-AU aggregate before the
  24,929.82-AU exact certificate could be built. No scheduler job was
  submitted. Confirmatory admission now uses immutable observed AUs for
  completed work, reserves 20% only on unexecuted confirmatory stages, and
  counts the separate 5-AU postprocessing reserve. The controller supplies the
  accepted-pilot, rejected-attempt, and observed-development charges from the
  resource freeze and retained accounting. Full validation plus fresh B=999
  acceptance, B=1,998 rejection, and every-script Kestrel `sbatch --test-only`
  remain mandatory before the execution flag may be used.
