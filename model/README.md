# Model artifact contract

This directory contains the existing BSM reduced-form model export. The public
loader validates the row and column relationships before using it.

## Runtime files

| File | Purpose |
| --- | --- |
| `coefficient_matrix_raw_scale.csv` | Raw-output-scale coefficients; rows are 23,495 outputs and columns are 245 engineered features. |
| `per_output_intercepts.csv` | Intercept for every coefficient-matrix output row. |
| `x_standardization.csv` | Feature order plus the training mean and scale. The raw-scale equation uses the mean for centering. |
| `coefficient_column_metadata.csv` | Transformation and base-input metadata used to construct the 245 features from 65 inputs. |

## Additional existing export files

| File | Purpose |
| --- | --- |
| `coefficient_matrix_standardized.csv` | Coefficients on the train-standardized feature scale. |
| `y_standardization.csv` | Output order and per-output training mean/scale. |
| `final_support_features.csv` | Selection and feature-type metadata for the 245 columns. |

The diagnostic tables, publication figure inputs, workflow configurations,
and reproduction scripts are maintained with the canonical example at
`rfm-pipeline/examples/bsm-manuscript/`.

## Feature construction

`coefficient_column_metadata.csv` defines six transformations:

- `identity`: `x`
- `quadratic`: `x**2`
- `sqrt`: `sqrt(x)`
- `log1p`: `log(1 + x)`
- `inverse`: `1 / x`
- `interaction`: `x1 * x2`

The loader rejects square-root values below zero, log1p values at or below
`-1`, inverse values equal to zero, and any non-finite input.

## Prediction equation

For output `i` and case `r`:

```text
y_hat[i, r] = intercept[i]
            + sum_j coefficient_raw[i, j]
                    * (engineered_feature[r, j] - feature_mean[j])
```

Coefficient columns, feature metadata rows, and `x_standardization.csv` rows
must remain in exactly the same order. Output rows and intercept rows must also
remain aligned.

## Release note

This is the existing model artifact requested for immediate public use. It is
not the planned metadata-derived release matrix. That future conversion should
arrive as a separately reviewed artifact update with the same fail-closed
alignment guarantees.
