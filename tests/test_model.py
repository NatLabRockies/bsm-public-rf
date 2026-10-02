from __future__ import annotations

import csv
from pathlib import Path, PurePosixPath

import numpy as np
import pandas as pd
import pytest

import bsm_public_rf.model as model_module
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


def test_predict_rejects_empty_or_scalar_output_selection(artifact_dir: Path) -> None:
    model = BSMReducedFormModel.from_artifact_dir(artifact_dir)
    inputs = pd.DataFrame({"x": [1.0], "z": [2.0]})

    with pytest.raises(ValueError, match="at least one"):
        model.predict(inputs, outputs=[])
    with pytest.raises(TypeError, match="iterable.*not a string"):
        model.predict(inputs, outputs="out_a")


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
        ({"x": [1e308], "z": [1.0]}, "transformed features.*finite"),
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


def test_transform_rejects_duplicate_input_columns(artifact_dir: Path) -> None:
    model = BSMReducedFormModel.from_artifact_dir(artifact_dir)
    inputs = pd.DataFrame([[1.0, 2.0, 3.0]], columns=["x", "x", "z"])

    with pytest.raises(ValueError, match="duplicate column names"):
        model.transform_inputs(inputs)


def test_loader_rejects_artifact_order_drift(artifact_dir: Path) -> None:
    standardization = pd.read_csv(artifact_dir / "x_standardization.csv")
    standardization.loc[0, "feature_name"] = "wrong"
    standardization.to_csv(artifact_dir / "x_standardization.csv", index=False)

    with pytest.raises(ModelArtifactError, match="feature order"):
        BSMReducedFormModel.from_artifact_dir(artifact_dir)


def test_loader_rejects_interaction_without_second_input(artifact_dir: Path) -> None:
    metadata = pd.read_csv(artifact_dir / "coefficient_column_metadata.csv")
    metadata.loc[metadata["transformation"] == "interaction", "base_input_2"] = ""
    metadata.to_csv(artifact_dir / "coefficient_column_metadata.csv", index=False)

    with pytest.raises(ModelArtifactError, match="interaction.*base_input_2"):
        BSMReducedFormModel.from_artifact_dir(artifact_dir)


def test_loader_accepts_float_serialization_roundoff(artifact_dir: Path) -> None:
    intercepts = pd.read_csv(artifact_dir / "per_output_intercepts.csv")
    outputs = pd.read_csv(artifact_dir / "y_standardization.csv")
    intercepts.loc[0, "intercept"] = 10_000_000_000.000002
    outputs.loc[0, "mean"] = 10_000_000_000.0
    intercepts.to_csv(artifact_dir / "per_output_intercepts.csv", index=False)
    outputs.to_csv(artifact_dir / "y_standardization.csv", index=False)

    model = BSMReducedFormModel.from_artifact_dir(artifact_dir)

    assert model.output_names == ("out_a", "out_b")


def test_loader_rejects_material_output_mean_mismatch(artifact_dir: Path) -> None:
    outputs = pd.read_csv(artifact_dir / "y_standardization.csv")
    outputs.loc[0, "mean"] = 10.01
    outputs.to_csv(artifact_dir / "y_standardization.csv", index=False)

    with pytest.raises(ModelArtifactError, match="output means"):
        BSMReducedFormModel.from_artifact_dir(artifact_dir)


def test_released_model_predicts_from_its_declared_schema() -> None:
    model = load_model()
    schema = model.input_schema()
    assert schema.index.tolist() == list(model.required_input_names)
    assert not schema.index.has_duplicates
    assert schema.loc["SE.initial indices of Commercial Maturity[Jet]", "unit"] == "unitless"
    assert model.feature_names
    assert model.output_names

    values = {}
    for name, row in schema.iterrows():
        minimum = row["minimum"]
        maximum = row["maximum"]
        values[name] = (minimum + maximum) / 2 if np.isfinite([minimum, maximum]).all() else 1.0
    inputs = pd.DataFrame([values], index=["scenario"])
    output_name = model.output_names[0]

    predictions = model.predict(inputs, outputs=[output_name])

    assert predictions.index.tolist() == ["scenario"]
    assert predictions.columns.tolist() == [output_name]
    assert predictions.shape == (1, 1)
    assert np.isfinite(predictions.iloc[0, 0])


def test_default_model_dir_falls_back_to_installed_distribution(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    installed_root = tmp_path / "installed"
    installed_model = installed_root / "share" / "bsm-public-rf" / "model"
    installed_model.mkdir(parents=True)

    class Distribution:
        files = None

        def locate_file(self, path: str) -> Path:
            return installed_root / path

    monkeypatch.delenv("BSM_PUBLIC_RF_MODEL_DIR", raising=False)
    monkeypatch.setattr(
        model_module,
        "__file__",
        str(tmp_path / "site-packages" / "bsm_public_rf" / "model.py"),
    )
    monkeypatch.setattr(
        model_module.metadata,
        "distribution",
        lambda name: Distribution(),
    )

    assert model_module.default_model_dir() == installed_model


def test_default_model_dir_follows_installed_record_outside_site_packages(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    site_packages = tmp_path / "venv" / "Lib" / "site-packages"
    installed_model = tmp_path / "venv" / "share" / "bsm-public-rf" / "model"
    installed_model.mkdir(parents=True)
    record_entry = PurePosixPath("../../share/bsm-public-rf/model/x_standardization.csv")

    class Distribution:
        files = [PurePosixPath("bsm_public_rf/model.py"), record_entry]

        def locate_file(self, path: PurePosixPath | str) -> Path:
            return site_packages / path

    monkeypatch.delenv("BSM_PUBLIC_RF_MODEL_DIR", raising=False)
    monkeypatch.setattr(model_module, "__file__", str(site_packages / "bsm_public_rf" / "model.py"))
    monkeypatch.setattr(model_module.metadata, "distribution", lambda name: Distribution())

    assert model_module.default_model_dir() == installed_model.resolve()
