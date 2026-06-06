# Per-output OLS intercepts

The released coefficient matrices (`coefficient_matrix_raw_scale.csv` and
`coefficient_matrix_standardized.csv`) deliberately omit a free intercept
column because all candidate features in the final design are mean-centred
(scaled by `x_standardization.csv`). The per-output intercept therefore
collapses to the per-output training-set mean of the response.

To make the prediction equation fully self-contained, the same vector is
exported as `per_output_intercepts.csv` for downstream consumers that prefer
an explicit intercept term. The values are identical to the `mean` column of
`y_standardization.csv` and the `scale` column of that file is `1.0` for every
output (responses are recovered on the raw scale).

The full prediction rule is

```
y_hat[output i, row r] = intercept[i]
                       + sum_j  coef_raw_scale[i, j] * (X_raw[r, j] - mean_x[j])
                                                       / scale_x[j]
```

where `coef_raw_scale` is read from `coefficient_matrix_raw_scale.csv` and
`mean_x`, `scale_x` are read from `x_standardization.csv`.
