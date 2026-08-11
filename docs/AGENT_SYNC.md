# Agent Sync

## SESSION STATE — 2026-08-11 — G11-HPC-S1 paired sync note (uncommitted)

- This BSM worktree remains dispatch-blocked for G11:
  `scheduler_submission_permitted: false`.
- The paired RFM package uses the approved 16,000-AU Kestrel node-hour
  allocation ceiling; its conservative campaign envelope is 15,152 AUs.
- Paired RFM slice `/Users/dhetting/src/rfm-pipeline-g11-integration`
  generated a content-addressed NO-SUBMIT Kestrel package only. No BSM
  execution, artifact regeneration, `sbatch`, commit, or push occurred here.
- The BSM pre-HPC suite does not require five future authoritative release
  figure PDFs. `scripts/reproduce_artifacts.py --validate-only` retains the
  strict later-release check for all five PDFs, including missing and
  truncated-file rejection. No stale figures were generated or promoted.
