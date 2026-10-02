# Model bundle reference

This directory is the versioned BSM reduced-form model. `load_model()` checks
the cross-file schema and ordering contracts before exposing it for inference.
The installed wheel carries the same files under
`share/bsm-public-rf/model/`.

## Required inference files

| File                               | Contents                                                    |
| ---------------------------------- | ----------------------------------------------------------- |
| `coefficient_matrix_raw_scale.csv` | 23,495 output rows by 245 engineered-feature columns        |
| `per_output_intercepts.csv`        | One aligned intercept per output                            |
| `x_standardization.csv`            | Engineered-feature order, training means, and scales        |
| `coefficient_column_metadata.csv`  | Rules for constructing the 245 features from 65 base inputs |
| `y_standardization.csv`            | Output order, training means, and scales                    |

Additional release files are:

| File                                  | Contents                                                                    |
| ------------------------------------- | --------------------------------------------------------------------------- |
| `coefficient_matrix_standardized.csv` | Coefficients on the standardized feature scale                              |
| `final_support_features.csv`          | Selection metadata for the 245 retained features                            |
| `output_metadata.json`                | Output variable descriptions, units, dimensions, and region/product legends |
| `SHA256SUMS`                          | SHA-256 digest for every released CSV and JSON file                         |

## Prediction contract

For output `i` and input row `r`:

```text
y_hat[i, r] = intercept[i]
            + sum_j coefficient_raw[i, j]
                    * (engineered_feature[r, j] - training_mean[j])
```

The loader supports six transformations declared in
`coefficient_column_metadata.csv`:

| Name          | Definition   |
| ------------- | ------------ |
| `identity`    | `x`          |
| `quadratic`   | `x**2`       |
| `sqrt`        | `sqrt(x)`    |
| `log1p`       | `log(1 + x)` |
| `inverse`     | `1 / x`      |
| `interaction` | `x1 * x2`    |

Square-root inputs must be nonnegative, log1p inputs must exceed `-1`,
inverse inputs must be nonzero, and all values must be finite. Coefficient
columns, feature metadata, and feature-standardization rows must have
identical order; output rows, intercepts, and output metadata must also align.
`input_schema()` reports every required base input and includes units, ranges,
pathways, and descriptions where those fields are present in the bundle.

## Loading a different bundle

Pass a directory explicitly:

```python
from bsm_public_rf import load_model

model = load_model("/path/to/model")
```

Or set `BSM_PUBLIC_RF_MODEL_DIR`. An explicit argument takes precedence over
the checkout or installed default.

## Provenance

These files are byte-identical to the retained model output produced with
`rfm-pipeline` commit `618357705949c9c3ab418c5eaa5a363cb9d864f5`.
Training data, workflow diagnostics, and reporting artifacts are not part of
this prediction-focused distribution.
