"""Smoke tests for committed manuscript reproduction artifacts.

These tests validate that the artifact bundle shipped in
``artifacts/`` is internally consistent and matches the values cited
in the manuscript (JDS v22). They run without HPC access or BSM
input data and exist so reviewers can verify the release bundle
before attempting a full reproduction run.

Run with::

    pixi run pytest tests/

or, if pixi is not installed locally::

    python -m pytest tests/
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = REPO_ROOT / "artifacts"

# Manuscript v22 (JDS submission) reference values.
MANUSCRIPT_TABLE2 = {
    "n_retained_outputs": 23495,
    "n_variance_filtered_outputs": 9954,
    "n_prefilter_features": 172,
    "n_final_features": 132,
    "n_pruning_removed_features": 40,
}
MANUSCRIPT_HOLDOUT_NRMSE = 0.0721
MANUSCRIPT_NULL_NRMSE = 0.1653


def _read_csv(rel: str) -> pd.DataFrame:
    path = ARTIFACTS / rel
    if not path.exists():
        pytest.fail(f"required artifact missing: {rel}")
    return pd.read_csv(path)


def test_final_ols_summary_matches_manuscript():
    df = _read_csv("final_model/final_ols_summary.csv")
    assert len(df) == 1
    row = df.iloc[0]
    for col, expected in MANUSCRIPT_TABLE2.items():
        assert int(row[col]) == expected, (
            f"final_ols_summary[{col}]={row[col]} != manuscript v22 {expected}"
        )
    assert row["final_ols_holdout_nrmse"] == pytest.approx(
        MANUSCRIPT_HOLDOUT_NRMSE, abs=5e-4
    )
    assert row["null_mean_holdout_nrmse"] == pytest.approx(
        MANUSCRIPT_NULL_NRMSE, abs=5e-4
    )
    assert row["manuscript_final_predictor_count_reference"] == 132
    assert row["manuscript_final_ols_holdout_nrmse_reference"] == pytest.approx(0.0721)


def test_ablation_table_matches_manuscript():
    df = _read_csv("tables/ablation_table.csv")
    by_model = {row["model_name"]: row for _, row in df.iterrows()}
    expected = {
        "null_mean": 0.1653,
        "main_effects_ols": 0.0812,
        "screened_ols": 0.0812,
        "penalized_ols": 0.0709,
        "final_ols": 0.0721,
    }
    for model, target in expected.items():
        assert model in by_model, f"missing ablation model: {model}"
        observed = float(by_model[model]["nrmse"])
        assert observed == pytest.approx(target, abs=5e-4), (
            f"ablation[{model}]={observed} != manuscript {target}"
        )


def test_workflow_stage_summary_matches_manuscript():
    df = _read_csv("tables/workflow_stage_summary.csv")
    rows = df.set_index(["stage", "primary_quantity"])["recomputed_value"]
    assert int(rows[("output_conditioning", "retained_scalar_outputs")]) == 9954
    assert int(rows[("output_conditioning", "retained_pca_components")]) == 20
    assert int(rows[("empirical_null_screening", "retained_terms")]) == 69
    assert int(rows[("interaction_discovery", "retained_pairs")]) == 62
    assert int(rows[("nonlinear_discovery", "retained_transformations")]) == 41
    assert int(rows[("sparse_selection_and_stability", "final_stable_support_terms")]) == 172
    assert int(rows[("final_inferential_filter", "hc3_retained_terms")]) == 172
    assert int(rows[("feature_pruning", "removed_terms_after_hc3")]) == 40
    assert float(rows[("final_ols", "holdout_nrmse")]) == pytest.approx(0.0721, abs=5e-4)


def test_final_support_features_count():
    df = _read_csv("final_model/final_support_features.csv")
    assert len(df) == 132, f"expected 132 final support features, got {len(df)}"


def test_prefilter_support_features_count():
    df = _read_csv("final_model/prefilter_support_features.csv")
    assert len(df) == 172, f"expected 172 enriched features, got {len(df)}"


def test_coefficient_matrix_shape():
    df = _read_csv("final_model/coefficient_matrix_raw_scale.csv")
    # Either 23495 rows × (132 + id col) or 132 rows × (23495 + id col)
    # depending on orientation. Accept both and just sanity-check.
    n_outputs = 23495
    n_features = 132
    rows, cols = df.shape
    feature_axis = cols - 1
    output_axis = rows
    assert (output_axis == n_outputs and feature_axis == n_features) or (
        output_axis == n_features and feature_axis == n_outputs
    ), f"coefficient_matrix shape {df.shape} matches neither orientation"


def test_intercept_vector_matches_y_standardization():
    intercepts = _read_csv("final_model/per_output_intercepts.csv")
    y_std = _read_csv("final_model/y_standardization.csv")
    merged = intercepts.merge(y_std, on=intercepts.columns[0], how="inner")
    # intercept must equal y_standardization.mean (the per-output training mean).
    diff = (merged["intercept"] - merged["mean"]).abs().max()
    assert diff < 1e-9, f"intercept and y_standardization.mean diverge by {diff}"
