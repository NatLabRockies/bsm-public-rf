from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from bsm_public_rf import (
    load_model,
    load_output_metadata,
    output_catalog,
    parse_output_name,
    unpack_outputs,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def metadata() -> dict:
    return load_output_metadata()


def test_output_metadata_describes_every_released_output(metadata: dict) -> None:
    model = load_model()

    catalog = output_catalog(model.output_names, metadata)

    assert catalog.index.tolist() == list(model.output_names)
    assert not catalog.index.has_duplicates
    assert set(catalog["variable"]) == set(metadata["variables"])
    assert (
        catalog["year"]
        .between(metadata["year_range"]["start"], metadata["year_range"]["end"])
        .all()
    )


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        (
            "AHC.MFSPMetric[HEFA, A]_2030",
            {"variable": "AHC.MFSPMetric", "pathway": "HEFA", "region": "A", "product": ""},
        ),
        (
            "OI.annual total HCBN prodn_2051",
            {"variable": "OI.annual total HCBN prodn", "pathway": "", "region": "", "product": ""},
        ),
    ],
)
def test_parse_output_name(metadata: dict, name: str, expected: dict) -> None:
    parsed = parse_output_name(name, metadata)

    assert {key: parsed[key] for key in expected} == expected
    assert parsed["year"] == int(name.rsplit("_", 1)[1])


@pytest.mark.parametrize(
    "name",
    [
        "Unknown.Var_2030",
        "AHC.MFSPMetric[HEFA]_2030",
        "AHC.MFSPMetric[XX, A]_2030",
        "AHC.MFSPMetric[HEFA, A_2030",
        "AHC.MFSPMetric[HEFA, A]_2100",
    ],
)
def test_parse_output_name_rejects_unknown_names(metadata: dict, name: str) -> None:
    with pytest.raises(ValueError):
        parse_output_name(name, metadata)


def test_unpack_outputs_round_trips_example_predictions(metadata: dict) -> None:
    model = load_model()
    inputs = pd.read_csv(ROOT / "examples" / "example_inputs.csv", index_col="scenario")
    predictions = model.predict(inputs)

    unpacked = unpack_outputs(predictions, metadata)

    series_columns = ["sample", "variable", "pathway", "region", "product"]
    catalog = output_catalog(model.output_names, metadata).reset_index()
    years = sorted(catalog["year"].unique())
    series_count = len(catalog[["variable", "pathway", "region", "product"]].drop_duplicates())
    assert unpacked.shape == (series_count * len(inputs), len(series_columns) + len(years))
    assert unpacked.columns.tolist() == [*series_columns, *years]
    assert set(unpacked["region"]) - {""} <= set(metadata["region_legend"].values())

    sample = inputs.index[0]
    output_name = predictions.columns[0]
    parsed = parse_output_name(output_name, metadata)
    region = metadata["region_legend"].get(parsed["region"], parsed["region"])
    row = unpacked[
        (unpacked["sample"] == sample)
        & (unpacked["variable"] == parsed["variable"])
        & (unpacked["pathway"] == parsed["pathway"])
        & (unpacked["region"] == region)
        & (unpacked["product"] == parsed["product"])
    ]
    assert len(row) == 1
    np.testing.assert_allclose(row[parsed["year"]].iloc[0], predictions.loc[sample, output_name])


def test_unpack_outputs_rejects_duplicate_output_columns(metadata: dict) -> None:
    name = "AHC.MFSPMetric[HEFA, A]_2030"
    predictions = pd.DataFrame([[1.0, 2.0]], columns=[name, name])

    with pytest.raises(ValueError, match="duplicate column names"):
        unpack_outputs(predictions, metadata)


def test_example_inputs_cover_required_inputs_within_documented_ranges() -> None:
    model = load_model()
    inputs = pd.read_csv(ROOT / "examples" / "example_inputs.csv", index_col="scenario")
    schema = model.input_schema().dropna(subset=["minimum", "maximum"])

    assert list(inputs.columns) == list(model.required_input_names)
    assert (inputs[schema.index] >= schema["minimum"]).all().all()
    assert (inputs[schema.index] <= schema["maximum"]).all().all()
