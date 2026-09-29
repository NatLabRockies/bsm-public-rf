# BSM Reduced-Form Model

`bsm-public-rf` is the ready-to-use Biomass Scenario Model (BSM)
reduced-form surrogate. The model bundle, Python loader, and command-line
predictor are included; the original simulator runs are not required.

## Choose the right repository

| I want to... | Go to... |
| --- | --- |
| Predict BSM outputs with the released model | **This repository** |
| Fit or adapt a reduced-form modeling workflow | [`rfm-pipeline`](https://github.com/NatLabRockies/rfm-pipeline) |
| Inspect the complete BSM workflow case study | [`rfm-pipeline/examples/bsm-manuscript`](https://github.com/NatLabRockies/rfm-pipeline/tree/main/examples/bsm-manuscript) |

## Install

Python 3.10–3.12 is supported.

```bash
git clone https://github.com/NatLabRockies/bsm-public-rf.git
cd bsm-public-rf
python -m pip install .
```

For a locked development environment, install
[Pixi](https://pixi.sh) and run `pixi install --locked` instead.

## Predict in Python

The model expects a pandas DataFrame containing its 65 named base inputs. It
constructs the selected transformations and interactions automatically.

```python
import pandas as pd

from bsm_public_rf import load_model

model = load_model()

# Discover the exact input and output names before preparing data.
model.input_schema().reset_index().to_csv("bsm_input_schema.csv", index=False)
model.output_schema().reset_index().to_csv("bsm_output_schema.csv", index=False)

inputs = pd.read_csv("my_bsm_inputs.csv")
predictions = model.predict(
    inputs,
    outputs=["AHC.MFSPMetric[HEFA, A]_2030"],
)
predictions.to_csv("predictions.csv", index=False)
```

Omit `outputs` to predict all 23,495 outputs. Extra input columns are allowed;
missing or invalid required inputs are rejected with a clear error.

## Predict from the command line

```bash
bsm-rf-predict my_bsm_inputs.csv predictions.csv \
  --output 'AHC.MFSPMetric[HEFA, A]_2030'
```

Repeat `--output` to select more outputs, or omit it to predict all outputs.
Run `bsm-rf-predict --help` for all options. In the Pixi environment, use
`pixi run predict -- ...`.

## What is included

The versioned `model/` bundle contains:

- 23,495 named outputs;
- 245 selected engineered features built from 65 required base inputs;
- raw-scale and standardized coefficient matrices;
- one intercept per output;
- feature and output scaling metadata; and
- feature transformations, input ranges, units, and descriptions.

The loader validates file presence, schemas, row and column order, duplicate
names, finite values, and transformation domains before prediction. Historical
input ranges are descriptive rather than enforced; values outside them are
extrapolations.

See [`model/README.md`](model/README.md) for the file contract and prediction
equation. SHA-256 digests for every released CSV are recorded in
[`model/SHA256SUMS`](model/SHA256SUMS).

## Model status and scope

This release packages the existing validated coefficient export so it is
usable independently of the research workflow. A future metadata-derived
matrix may update the artifact, but it must preserve the same fail-closed
alignment and provenance requirements.

Raw BSM simulator runs, workflow configurations, diagnostics, and publication
figures are intentionally not stored here. The BSM case study in
`rfm-pipeline` is their canonical home.

## Develop, cite, and report issues

- Validate a checkout with `pixi run gate`.
- See [`CONTRIBUTING.md`](CONTRIBUTING.md) for repository boundaries.
- Cite the software using [`CITATION.cff`](CITATION.cff).
- See [`CHANGELOG.md`](CHANGELOG.md) for release history.
- Report defects through [GitHub Issues](https://github.com/NatLabRockies/bsm-public-rf/issues).

Licensed under the [MIT License](LICENSE).
