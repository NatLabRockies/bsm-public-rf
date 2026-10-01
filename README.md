# BSM Reduced-Form Model

`bsm-public-rf` provides the released Biomass Scenario Model (BSM)
reduced-form model, a Python prediction API, and a command-line predictor. You
do not need the original simulator runs to use it.

## Start here

| Goal                                 | Start with                                                      |
| ------------------------------------ | --------------------------------------------------------------- |
| Verify the model and see predictions | [`examples/predict.py`](examples/predict.py)                    |
| Follow a notebook walkthrough        | [`examples/quickstart.ipynb`](examples/quickstart.ipynb)        |
| Inspect the model files and equation | [`model/README.md`](model/README.md)                            |
| Fit a new reduced-form model         | [`rfm-pipeline`](https://github.com/NatLabRockies/rfm-pipeline) |

## Install

Python 3.10–3.12 is supported.

```bash
git clone https://github.com/NatLabRockies/bsm-public-rf.git
cd bsm-public-rf
python -m pip install .
```

Run the included example:

```bash
python examples/predict.py
```

For a locked development environment, install [Pixi](https://pixi.sh), run
`pixi install --locked`, and prefix Python commands with `pixi run`.

## Predict in Python

The model expects one row per scenario and one column per required BSM input.
It constructs the selected transformations and interactions automatically.

```python
import pandas as pd

from bsm_public_rf import load_model

model = load_model()
inputs = pd.read_csv("my_bsm_inputs.csv")

predictions = model.predict(
    inputs,
    outputs=["AHC.MFSPMetric[HEFA, A]_2030"],
)
predictions.to_csv("predictions.csv", index=False)
```

Use the model metadata to prepare inputs and choose outputs:

```python
from bsm_public_rf import output_catalog

input_schema = model.input_schema()          # names, units, ranges, descriptions
catalog = output_catalog(model.output_names) # dimensions, years, units, descriptions
```

The model requires the 65 columns listed by `input_schema`. Extra columns are
allowed. Missing, non-finite, or transformation-invalid inputs raise an error.
The documented ranges describe the model's training data; predictions outside
them are extrapolations.

Omit `outputs` to predict every released output. To select a complete time
series from the catalog and reshape it into year columns:

```python
from bsm_public_rf import unpack_outputs

names = catalog.query(
    "variable == 'AHC.MFSPMetric' and pathway == 'HEFA' and region == 'A'"
).index.tolist()
predictions = model.predict(inputs, outputs=names)
series = unpack_outputs(predictions)
```

Output names follow `VARIABLE[pathway, region, product]_YEAR`; dimensions that
do not apply to a variable are omitted.

## Predict from the command line

This command predicts one output for the bundled example inputs:

```bash
bsm-rf-predict examples/example_inputs.csv predictions.csv \
  --output 'AHC.MFSPMetric[HEFA, A]_2030'
```

Repeat `--output` to select more outputs, or omit it to predict all outputs.
Prediction rows retain the input row order. Run `bsm-rf-predict --help` for all
options. In the Pixi environment, use `pixi run predict -- ...`.

## Model bundle

The released bundle contains 23,495 outputs, 245 engineered features, and the
metadata needed to construct those features from 65 base inputs. It includes
raw-scale and standardized coefficients, intercepts, scaling parameters, input
descriptions and ranges, and output descriptions and units.

`load_model()` validates file presence, schemas, ordering, duplicate names, and
finite values before prediction. See [`model/README.md`](model/README.md) for
the file contract and prediction equation. File digests are recorded in
[`model/SHA256SUMS`](model/SHA256SUMS).

Earlier fits are retained in [`versions/`](versions/README.md) for comparison;
they are not used by `load_model()` or included in the installed package.

## Cite, contribute, and report issues

- Cite the software using [`CITATION.cff`](CITATION.cff).
- See [`CONTRIBUTING.md`](CONTRIBUTING.md) for development instructions.
- See [`CHANGELOG.md`](CHANGELOG.md) for release history.
- Report defects through [GitHub Issues](https://github.com/NatLabRockies/bsm-public-rf/issues).

Licensed under the [MIT License](LICENSE).
