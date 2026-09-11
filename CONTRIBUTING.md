# Contributing to bsm-public-rf

Thank you for your interest in contributing.

This repository is a **reproduction repository** for a published case study. It
contains configuration, committed model artifacts, and thin driver scripts. The
reduced-form modeling framework itself lives in
[`rfm-pipeline`](https://github.com/NatLabRockies/rfm-pipeline).

Please open framework changes (screening, interaction discovery, selection,
estimation) against `rfm-pipeline`, not here.

## Scope of changes accepted here

- Corrections to configuration, documentation, or metadata
- Fixes to the reproduction scripts under `scripts/`
- Additional tests that strengthen reproduction guarantees

Because the committed artifacts back a published manuscript, changes that alter
published numbers require an accompanying explanation of provenance and a
regenerated reproduction log.

## Getting started

1. Fork the repository and create a feature branch from `main`.
1. Install the environment (this repo is [Pixi](https://pixi.sh)-managed):
   ```bash
   git clone https://github.com/NatLabRockies/bsm-public-rf.git
   cd bsm-public-rf
   pixi install --locked
   ```
1. Run the test suite:
   ```bash
   pixi run pytest tests/ -q
   ```

Use `pixi run` for all project tooling. Do not invoke bare `python`, `pytest`,
or `pip`, as this bypasses the locked environment that reproduction depends on.

## Requirements for a pull request

- The full test suite passes.
- Tests are added for new behavior. Do not weaken, skip, or narrow existing
  tests to make a change pass.
- Documentation is updated when behavior or interfaces change.
- Commits are scoped and have descriptive messages.

## Data availability

Raw BSM simulator input data is not distributed with this repository. See the
README for access. Please do not commit raw simulator data, large binary blobs,
or credentials.

## Reporting problems

Open an issue describing the observed behavior, the expected behavior, and the
exact `pixi run` command used. For suspected security issues, see
[SECURITY.md](SECURITY.md).
