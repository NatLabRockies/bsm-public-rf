# BSM Reduced-Form Model

`bsm-public-rf` distributes a portable reduced-form surrogate for the Biomass
Scenario Model (BSM). Clone this repository to inspect the model inputs and
outputs, load the existing coefficient bundle, and generate predictions
without rerunning the publication workflow.

This repository is deliberately model-focused. The generic modeling workflow
and the complete manuscript case study live in
[`rfm-pipeline`](https://github.com/NatLabRockies/rfm-pipeline/tree/main/examples/bsm-manuscript).
The article source and submission files live in
[`bsm-public-rf-manuscript`](https://github.com/NatLabRockies/bsm-public-rf-manuscript).

## Current release status

The checked-in `model/` directory contains the existing BSM model artifact:

- 23,495 named outputs;
- 245 selected engineered features derived from 65 required base inputs;
- raw-scale and standardized coefficient matrices;
- per-output intercepts and input/output scaling metadata; and
- feature names, transformations, units, ranges, and descriptions.

This is the current legacy export, made available now so the model is usable.
A separately developed metadata-to-release-matrix conversion will replace or
augment it when that work is ready. Until then, the bundle must not be
described as evidence from a newer analysis method or a future publication
run.

## Install

With [Pixi](https://pixi.sh):

```bash
git clone https://github.com/NatLabRockies/bsm-public-rf.git
cd bsm-public-rf
pixi install --locked
```

Or install the complete model distribution into an existing Python 3.10+
environment:

```bash
python -m pip install .
```

The wheel includes the model CSVs and `load_model()` discovers them
automatically. A source checkout continues to use its top-level `model/`
directory. To use a separately downloaded or updated bundle, pass its path to
`load_model(...)` or set `BSM_PUBLIC_RF_MODEL_DIR`.

## Predict

The loader accepts a `pandas.DataFrame` containing the 65 base inputs used by
the selected support. It materializes identity, quadratic, square-root,
log1p, inverse, and pairwise-interaction features in the exact coefficient
column order.

```python
import pandas as pd

from bsm_public_rf import load_model

model = load_model()
print(model.required_input_names)
print(model.input_schema())

inputs = pd.read_csv("my_bsm_inputs.csv")
predictions = model.predict(
    inputs,
    outputs=["AHC.MFSPMetric[HEFA, A]_2030"],
)
predictions.to_csv("predictions.csv", index=False)
```

For command-line use after either installation method:

```bash
bsm-rf-predict my_bsm_inputs.csv predictions.csv \
  --output 'AHC.MFSPMetric[HEFA, A]_2030'
```

Inside the Pixi environment, `pixi run predict -- ...` is equivalent.

The API rejects missing columns, non-finite values, invalid transformation
domains, artifact-order drift, and unknown output names. It reports but does
not enforce the historical input ranges; predictions outside those ranges are
extrapolations.

## Model equation

For output `i` and input row `r`:

```text
y_hat[i, r] = intercept[i]
            + sum_j coefficient[i, j] * (feature[r, j] - training_mean[j])
```

See [`model/README.md`](model/README.md) for the artifact contract and file
descriptions.

## Validate

```bash
./test_repo.sh --check
```

The release bundle's recorded SHA-256 digests are in
[`model/SHA256SUMS`](model/SHA256SUMS).

## Data scope

Raw BSM simulator runs are not distributed here. They are not required for
inference with the committed coefficient bundle. The workflow example explains
the controlled-data requirements for full scientific reproduction.

## License and citation

The software is released under the [MIT License](LICENSE). Citation metadata
is available in [`CITATION.cff`](CITATION.cff). See
[`CHANGELOG.md`](CHANGELOG.md) for release history.
