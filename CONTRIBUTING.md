# Contributing to bsm-public-rf

This repository is the public distribution surface for the BSM reduced-form
model.

Appropriate changes include:

- loader and prediction correctness fixes;
- stronger artifact schema and alignment validation;
- clearer input/output documentation and usage examples; and
- reviewed updates to the released model bundle.

Generic workflow implementation changes belong in
[`rfm-pipeline`](https://github.com/NatLabRockies/rfm-pipeline). Study-specific
reproduction material is outside this distribution repository.

## Development

```bash
git clone https://github.com/NatLabRockies/bsm-public-rf.git
cd bsm-public-rf
pixi install --locked
pixi run gate
```

Before proposing a release, also build the wheel and verify that a clean
installation can load the bundled model without `BSM_PUBLIC_RF_MODEL_DIR`.

Use a feature branch and add tests before changing behavior. Do not alter model
rows, columns, values, or metadata without documenting provenance and testing
all cross-file alignment contracts.

Do not commit raw simulator data, credentials, local paths, generated caches,
or workflow outputs unrelated to the released model.
