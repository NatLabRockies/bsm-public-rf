from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from bsm_public_rf import BSMReducedFormModel, ModelArtifactError, load_model


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


@pytest.fixture
def artifact_dir(tmp_path: Path) -> Path:
    features = ["x", "x_sq", "x_sqrt", "x_log1p", "z_inv", "x:z"]
    metadata_fields = [
        "coefficient_column_index",
        "feature_name",
        "feature_type",
        "transformation",
        "base_input_1",
        "base_input_1_unit",
        "base_input_1_min",
        "base_input_1_max",
        "base_input_1_pathway",
        "base_input_1_description",
        "base_input_2",
        "base_input_2_unit",
        "n_outputs_nonzero",
        "stability_selection_frequency",
        "hc3_retained",
        "delta_nrmse_if_removed",
    ]
    transformations = [
        ("numeric", "identity", "x", ""),
        ("transformation", "quadratic", "x", ""),
        ("transformation", "sqrt", "x", ""),
        ("transformation", "log1p", "x", ""),
        ("transformation", "inverse", "z", ""),
        ("interaction", "interaction", "x", "z"),
    ]
    rows = []
    for index, (feature, (feature_type, transform, base_1, base_2)) in enumerate(
        zip(features, transformations, strict=True)
    ):
        rows.append(
            {
                "coefficient_column_index": index,
                "feature_name": feature,
                "feature_type": feature_type,
                "transformation": transform,
                "base_input_1": base_1,
                "base_input_1_unit": "unitless",
                "base_input_1_min": 0,
                "base_input_1_max": 10,
                "base_input_1_pathway": "fixture",
                "base_input_1_description": "fixture input",
                "base_input_2": base_2,
                "base_input_2_unit": "unitless" if base_2 else "",
                "n_outputs_nonzero": 2,
                "stability_selection_frequency": 1,
                "hc3_retained": True,
                "delta_nrmse_if_removed": 0,
            }
        )
    _write_csv(tmp_path / "coefficient_column_metadata.csv", metadata_fields, rows)

    pd.DataFrame(
        {
            "original_position": range(len(features)),
            "mean": np.zeros(len(features)),
            "scale": np.ones(len(features)),
        },
        index=pd.Index(features, name="feature_name"),
    ).to_csv(tmp_path / "x_standardization.csv")
    pd.DataFrame(
        [[1, 1, 1, 1, 1, 1], [2, 0, 0, 0, -1, 0.5]],
        index=pd.Index(["out_a", "out_b"], name="output_name"),
        columns=features,
    ).to_csv(tmp_path / "coefficient_matrix_raw_scale.csv")
    pd.DataFrame(
        {"intercept": [10.0, -3.0]},
        index=pd.Index(["out_a", "out_b"], name="output_name"),
    ).to_csv(tmp_path / "per_output_intercepts.csv")
    pd.DataFrame(
        {
            "original_position": [0, 1],
            "mean": [10.0, -3.0],
            "scale": [1.0, 1.0],
        },
        index=pd.Index(["out_a", "out_b"], name="output_name"),
    ).to_csv(tmp_path / "y_standardization.csv")
    return tmp_path


def test_transform_and_predict_from_base_inputs(artifact_dir: Path) -> None:
    model = BSMReducedFormModel.from_artifact_dir(artifact_dir)
    inputs = pd.DataFrame({"x": [4.0], "z": [2.0]}, index=["case-1"])

    features = model.transform_inputs(inputs)
    expected_features = np.array([4.0, 16.0, 2.0, np.log1p(4.0), 0.5, 8.0])
    np.testing.assert_allclose(features.iloc[0].to_numpy(), expected_features)

    predictions = model.predict(inputs)
    assert predictions.index.tolist() == ["case-1"]
    np.testing.assert_allclose(predictions.loc["case-1", "out_a"], 10 + expected_features.sum())
    np.testing.assert_allclose(
        predictions.loc["case-1", "out_b"],
        -3 + 2 * expected_features[0] - expected_features[4] + 0.5 * expected_features[5],
    )


def test_predict_can_select_outputs_and_accept_precomputed_features(artifact_dir: Path) -> None:
    model = BSMReducedFormModel.from_artifact_dir(artifact_dir)
    features = model.transform_inputs(pd.DataFrame({"x": [1.0, 2.0], "z": [2.0, 4.0]}))

    predictions = model.predict_features(features, outputs=["out_b"])

    assert predictions.columns.tolist() == ["out_b"]
    assert predictions.shape == (2, 1)


def test_model_exposes_input_and_output_schemas(artifact_dir: Path) -> None:
    model = BSMReducedFormModel.from_artifact_dir(artifact_dir)

    assert model.input_schema().index.tolist() == ["x", "z"]
    assert model.output_schema().index.tolist() == ["out_a", "out_b"]
    assert model.output_schema().loc["out_a", "mean"] == 10.0


@pytest.mark.parametrize(
    ("inputs", "message"),
    [
        ({"x": [-1.0], "z": [1.0]}, "square-root"),
        ({"x": [-2.0], "z": [1.0]}, "log1p"),
        ({"x": [1.0], "z": [0.0]}, "inverse"),
        ({"x": [np.nan], "z": [1.0]}, "finite"),
    ],
)
def test_transform_rejects_invalid_inputs(
    artifact_dir: Path, inputs: dict[str, list[float]], message: str
) -> None:
    model = BSMReducedFormModel.from_artifact_dir(artifact_dir)

    with pytest.raises(ValueError, match=message):
        model.transform_inputs(pd.DataFrame(inputs))


def test_transform_rejects_missing_base_input(artifact_dir: Path) -> None:
    model = BSMReducedFormModel.from_artifact_dir(artifact_dir)

    with pytest.raises(ValueError, match="z"):
        model.transform_inputs(pd.DataFrame({"x": [1.0]}))


def test_loader_rejects_artifact_order_drift(artifact_dir: Path) -> None:
    standardization = pd.read_csv(artifact_dir / "x_standardization.csv")
    standardization.loc[0, "feature_name"] = "wrong"
    standardization.to_csv(artifact_dir / "x_standardization.csv", index=False)

    with pytest.raises(ModelArtifactError, match="feature order"):
        BSMReducedFormModel.from_artifact_dir(artifact_dir)


def test_repository_model_bundle_loads() -> None:
    model = load_model()

    assert len(model.feature_names) == 245
    assert len(model.output_names) == 23_495
    assert len(model.required_input_names) == 65


def test_repository_model_predicts_from_required_base_inputs() -> None:
    model = load_model()
    inputs = pd.DataFrame({name: [1.0] for name in model.required_input_names})

    predictions = model.predict(inputs, outputs=[model.output_names[0]])

    assert predictions.shape == (1, 1)
    assert np.isfinite(predictions.iloc[0, 0])
