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
- `configs/g11_campaign_contract.toml` now mirrors the RFM G11-v9 contract,
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
