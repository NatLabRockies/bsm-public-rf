from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from bsm_public_rf import load_model

ROOT = Path(__file__).resolve().parents[1]
VERSIONS = ROOT / "versions"

pytest.importorskip("pyarrow")


@pytest.fixture(scope="module")
def utils():
    path = VERSIONS / "bsm_model_utils.py"
    spec = importlib.util.spec_from_file_location("bsm_model_utils", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def registry(utils) -> dict:
    return utils.load_registry(VERSIONS)


def test_archived_version_contract(utils, registry: dict) -> None:
    assert registry["active"] in registry["models"]
    for version, entry in registry["models"].items():
        folder = VERSIONS / version
        assert (folder / entry["coef_file"]).is_file()
        assert (folder / entry["feature_defs_file"]).is_file()

    entry = registry["models"][registry["active"]]
    coefficients = utils.load_coefficients(VERSIONS)
    features = utils.load_feature_definitions(VERSIONS)
    base_inputs = [name for name, spec in features.items() if isinstance(spec["derivation"], str)]

    assert coefficients.shape == (entry["n_outputs"], entry["n_features"] + 1)
    assert len(features) == entry["n_features"]
    assert len(base_inputs) == entry["n_inputs"]
    assert "const" in coefficients.columns
    assert [c for c in coefficients.columns if c != "const"] == list(features)
    assert coefficients.index.astype(str).tolist() == list(load_model().output_names)


def test_archived_metadata_contains_no_placeholders(registry: dict) -> None:
    inputs_metadata = json.loads(
        (VERSIONS / registry["active"] / "inputs_metadata.json").read_text(encoding="utf-8")
    )
    public_metadata = json.dumps({"registry": registry, "inputs": inputs_metadata}).lower()

    assert "tbd" not in public_metadata
    assert "placeholder" not in public_metadata


def test_run_model_aligns_intercept_by_name(utils, registry: dict) -> None:
    features = utils.load_feature_definitions(VERSIONS)
    coefficients = utils.load_coefficients(VERSIONS)
    base_inputs = [name for name, spec in features.items() if isinstance(spec["derivation"], str)]
    rng = np.random.default_rng(0)
    inputs = pd.DataFrame(rng.uniform(0.5, 1.5, (2, len(base_inputs))), columns=base_inputs)

    matrix = utils.build_feature_vector(features, inputs)
    predictions = utils.run_model(coefficients, matrix, list(features))

    named = pd.DataFrame(matrix[:, :-1], columns=list(features)).assign(const=1.0)
    expected = named[coefficients.columns].to_numpy() @ coefficients.to_numpy().T
    np.testing.assert_allclose(predictions, expected)


def test_run_pipeline_and_unpack(utils, registry: dict, tmp_path: Path) -> None:
    features = utils.load_feature_definitions(VERSIONS)
    base_inputs = [name for name, spec in features.items() if isinstance(spec["derivation"], str)]
    inputs_metadata = json.loads(
        (VERSIONS / "BSM_RFM_v1" / "inputs_metadata.json").read_text(encoding="utf-8")
    )
    assert set(inputs_metadata) == set(base_inputs)

    constraints = {name: inputs_metadata[name]["constraints"] for name in base_inputs}
    midpoints = {name: (c["min"] + c["max"]) / 2 for name, c in constraints.items()}
    path = tmp_path / "inputs.csv"
    pd.DataFrame([midpoints]).to_csv(path, index=False)

    predictions = utils.run_pipeline(path)
    unpacked = utils.unpack_outputs(predictions, utils.load_output_metadata())

    entry = registry["models"][registry["active"]]
    assert predictions.shape == (1, entry["n_outputs"])
    assert np.isfinite(predictions.to_numpy()).all()
    assert len(unpacked) > 0
    assert not unpacked[["sample", "variable", "pathway", "region", "product"]].duplicated().any()


def test_archived_feature_builder_rejects_missing_dataframe_inputs(utils, registry: dict) -> None:
    features = utils.load_feature_definitions(VERSIONS)
    base_inputs = [name for name, spec in features.items() if isinstance(spec["derivation"], str)]
    incomplete = pd.DataFrame({name: [1.0] for name in base_inputs[:-1]})

    with pytest.raises(ValueError, match="missing required base columns"):
        utils.build_feature_vector(features, incomplete)


def test_archived_feature_builder_rejects_nonfinite_inputs(utils, registry: dict) -> None:
    features = utils.load_feature_definitions(VERSIONS)
    base_inputs = [name for name, spec in features.items() if isinstance(spec["derivation"], str)]
    values = pd.DataFrame({name: [1.0] for name in base_inputs})
    values.loc[0, base_inputs[0]] = np.nan

    with pytest.raises(ValueError, match="finite"):
        utils.build_feature_vector(features, values)


def test_archived_input_loader_rejects_unknown_file_type(utils, tmp_path: Path) -> None:
    path = tmp_path / "inputs.txt"
    path.write_text("x\n1\n", encoding="utf-8")

    with pytest.raises(ValueError, match="CSV or Parquet"):
        utils.load_inputs(path)
