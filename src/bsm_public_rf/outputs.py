"""Describe and reshape the flat BSM output names using the bundled output metadata."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from .model import default_model_dir

OUTPUT_METADATA_FILE = "output_metadata.json"
DIMENSIONS = ("pathway", "region", "product")


def load_output_metadata(artifact_dir: str | Path | None = None) -> dict[str, Any]:
    """Load ``output_metadata.json`` from ``artifact_dir`` or the default model bundle."""
    root = default_model_dir() if artifact_dir is None else Path(artifact_dir)
    with (root / OUTPUT_METADATA_FILE).open(encoding="utf-8") as stream:
        return json.load(stream)


def parse_output_name(name: str, output_metadata: dict[str, Any]) -> dict[str, Any]:
    """Split a flat output name into its variable, dimensions, and year.

    Names follow ``BASE_VARIABLE[dim1, dim2, ...]_YEAR``; the bracket is omitted
    for variables without dimensions. Dimensions a variable lacks are ``""``.
    """
    if not isinstance(name, str):
        raise TypeError("output name must be a string")
    try:
        base_and_dims, year_text = name.rsplit("_", 1)
        year = int(year_text)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"output {name!r} does not end with a numeric year") from exc
    if "[" in base_and_dims:
        if not base_and_dims.endswith("]") or base_and_dims.count("[") != 1:
            raise ValueError(f"output {name!r} has malformed dimension brackets")
        base, bracket = base_and_dims.rstrip("]").split("[", 1)
        values = [value.strip() for value in bracket.split(",")]
    else:
        base, values = base_and_dims, []
    base = base.rstrip()

    spec = output_metadata["variables"].get(base)
    if spec is None:
        raise ValueError(f"output {name!r} has unknown variable {base!r}")
    if len(values) != len(spec["dimensions"]):
        raise ValueError(f"output {name!r} does not match dimensions {spec['dimensions']}")
    parsed: dict[str, Any] = {"variable": base, **dict.fromkeys(DIMENSIONS, "")}
    for dimension, value in zip(spec["dimensions"], values, strict=True):
        if value not in spec[f"{dimension}_values"]:
            raise ValueError(f"output {name!r} has unknown {dimension} {value!r}")
        parsed[dimension] = value
    year_range = output_metadata.get("year_range", {})
    if not year_range.get("start", year) <= year <= year_range.get("end", year):
        raise ValueError(f"output {name!r} has a year outside the declared range")
    parsed["year"] = year
    return parsed


def output_catalog(
    output_names: list[str] | tuple[str, ...], output_metadata: dict[str, Any] | None = None
) -> pd.DataFrame:
    """Return one row per output name with its variable, dimensions, year, and units."""
    metadata = load_output_metadata() if output_metadata is None else output_metadata
    rows = []
    for name in output_names:
        parsed = parse_output_name(name, metadata)
        spec = metadata["variables"][parsed["variable"]]
        rows.append(
            {
                "output_name": name,
                **parsed,
                "unit": spec["unit"],
                "description": spec["description"],
            }
        )
    return pd.DataFrame(rows).set_index("output_name")


def unpack_outputs(
    predictions: pd.DataFrame, output_metadata: dict[str, Any] | None = None
) -> pd.DataFrame:
    """Reshape flat predictions into one row per sample and output series.

    The result has ``sample``, ``variable``, ``pathway``, ``region``, and
    ``product`` columns followed by one column per year. ``sample`` holds the
    row labels of ``predictions``; region codes are expanded to full names.
    Use bracket indexing (``df["sample"]``) because ``sample`` and ``product``
    are also DataFrame method names.
    """
    if not isinstance(predictions, pd.DataFrame):
        raise TypeError("predictions must be a pandas DataFrame")
    if predictions.index.has_duplicates:
        raise ValueError("predictions index must not contain duplicate labels")
    if predictions.columns.has_duplicates:
        raise ValueError("predictions must not contain duplicate column names")
    metadata = load_output_metadata() if output_metadata is None else output_metadata
    keys = output_catalog(list(predictions.columns.astype(str)), metadata)
    keys = keys[["variable", *DIMENSIONS, "year"]]

    long = pd.DataFrame(
        predictions.to_numpy(dtype=float).T,
        index=pd.MultiIndex.from_frame(keys),
        columns=pd.Index(predictions.index, name="sample"),
    ).melt(ignore_index=False, value_name="value")
    series = ["sample", "variable", *DIMENSIONS]
    wide = long.reset_index().pivot(index=series, columns="year", values="value")
    wide = wide.reset_index()
    wide.columns.name = None
    wide["region"] = wide["region"].replace(metadata["region_legend"])
    return wide
