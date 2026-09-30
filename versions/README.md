# Archived model versions

This directory keeps earlier BSM reduced-form model fits alongside the released
bundle in [`model/`](../model/README.md). `load_model()` and the installed package
always use `model/`; nothing here is shipped in the wheel.

| Version | Inputs | Features | Outputs | Format |
| --- | --- | --- | --- | --- |
| `model/` (released, default) | 65 | 245 | 23,495 | CSV, loaded by `bsm_public_rf` |
| `BSM_RFM_v1` | 62 | 346 | 23,495 | Parquet + MathJSON, loaded by `bsm_model_utils.py` |

All versions predict the same 23,495 outputs in the same order, so
`model/output_metadata.json` and `bsm_public_rf.unpack_outputs` apply to each.
They differ in which base inputs they use and which engineered features they keep.

## Layout

```
versions/
├── model_registry.json        # version id -> files and counts; "active" is used by bsm_model_utils
├── bsm_model_utils.py         # loader, MathJSON feature builder, pipeline, unpacking
└── BSM_RFM_v1/
    ├── coefficients.parquet   # 23,495 outputs x ("const" + 346 features)
    ├── feature_definitions.json  # MathJSON derivation for each feature
    └── inputs_metadata.json   # descriptions, units, and ranges for the 62 inputs
```

## Usage

```python
import sys

sys.path.insert(0, "versions")
from bsm_model_utils import run_pipeline, unpack_outputs, load_output_metadata

predictions = run_pipeline("my_62_inputs.csv")  # uses the "active" registry entry
series = unpack_outputs(predictions, load_output_metadata())
```

Reading Parquet requires `pyarrow` (included in the Pixi environment).

## Feature definitions

Each entry in `feature_definitions.json` maps a feature name to a MathJSON
`derivation` and its `base_inputs`. Identity features (a plain string derivation)
are the base inputs. Other forms are `["Multiply", a, b]`, `["Power", x, 2]`, and
`["Divide", 1, x]`. Predictions are `coefficients @ [features..., 1.0]`, with the
`const` coefficient column matched to the trailing 1.0 by name.

## Adding a version

1. Create `versions/<VERSION_ID>/` with the coefficient and feature-definition files.
2. Add an entry to `model_registry.json` with file names and input/feature/output counts.
3. Run `pixi run gate`; `tests/test_versions.py` checks the registry against the files.
