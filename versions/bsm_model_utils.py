"""Loader and pipeline for versioned BSM reduced-form models in ``versions/``.

These models use a MathJSON feature-definition format and Parquet coefficients,
which differs from the packaged ``model/`` bundle loaded by ``bsm_public_rf``.
Output names are shared, so output metadata comes from ``model/output_metadata.json``.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------


def load_registry(data_dir: Path) -> dict:
    """Load the model-version registry from ``data_dir``."""
    with (Path(data_dir) / "model_registry.json").open(encoding="utf-8") as f:
        return json.load(f)


def load_feature_definitions(data_dir: Path, registry: dict | None = None) -> dict:
    """Load the active model's ordered MathJSON feature definitions."""
    if registry is None:
        registry = load_registry(data_dir)
    active_id = registry["active"]
    active = registry["models"][active_id]
    with (Path(data_dir) / active_id / active["feature_defs_file"]).open(encoding="utf-8") as f:
        return json.load(f)


def load_inputs(path: str | Path) -> pd.DataFrame:
    """Load raw inputs from a parquet or CSV file. Returns a DataFrame of shape (N, 62).

    Accepts parquet or CSV. Column names are preserved so that
    ``build_feature_vector`` can reorder them to match the metadata.
    """
    path = Path(path)
    if path.suffix == ".csv":
        df = pd.read_csv(path)
    else:
        df = pd.read_parquet(path)
    if "value" in df.columns:
        df = df["value"].to_frame().T.reset_index(drop=True)
    return df


def load_coefficients(data_dir: Path, registry: dict | None = None) -> pd.DataFrame:
    """Load the active model's coefficient matrix."""
    if registry is None:
        registry = load_registry(data_dir)
    active_id = registry["active"]
    active = registry["models"][active_id]
    return pd.read_parquet(Path(data_dir) / active_id / active["coef_file"])


def load_output_metadata(metadata_dir: Path | None = None) -> dict:
    """Load the shared output descriptions and dimension metadata."""
    if metadata_dir is None:
        metadata_dir = Path(__file__).parent.parent / "model"
    with (Path(metadata_dir) / "output_metadata.json").open(encoding="utf-8") as f:
        return json.load(f)


def _load_scale(data_dir: Path, filename: str) -> np.ndarray | None:
    """Load a scale vector from parquet, or return None if the file doesn't exist."""
    path = Path(data_dir) / filename
    if path.exists():
        return pd.read_parquet(path)["scale"].values
    return None


# ---------------------------------------------------------------------------
# Feature engineering
# ---------------------------------------------------------------------------


def _eval_mathjson(expr, inputs: dict):
    """Recursively evaluate a MathJSON expression against numpy arrays."""
    if isinstance(expr, str):
        return inputs[expr]
    if isinstance(expr, (int, float)):
        return float(expr)
    head, *args = expr
    vals = [_eval_mathjson(a, inputs) for a in args]
    if head == "Exp":
        return np.exp(vals[0])
    if head == "Ln":
        return np.log(vals[0])
    if head == "Divide":
        return vals[0] / vals[1]
    if head == "Multiply":
        return vals[0] * vals[1]
    if head == "Power":
        return vals[0] ** vals[1]
    if head == "Add":
        return vals[0] + vals[1]
    raise ValueError(f"Unknown MathJSON head: {head!r}")


def build_feature_vector(
    feature_definitions: dict, raw_inputs: pd.DataFrame | np.ndarray
) -> np.ndarray:
    """Build the full feature matrix from raw base inputs.

    Parameters
    ----------
    feature_definitions : dict
        Feature definitions (346 entries) with MathJSON derivations.
    raw_inputs : pd.DataFrame or np.ndarray, shape (N, 62)

    Returns
    -------
    np.ndarray, shape (N, n_features + 1)
        All derived features plus a trailing column of 1.0 (intercept).
    """
    # Identity features (derivation is a plain string) are the base inputs
    base_names = [
        name for name, entry in feature_definitions.items() if isinstance(entry["derivation"], str)
    ]

    # Convert to named numpy arrays
    if isinstance(raw_inputs, np.ndarray):
        if raw_inputs.ndim == 1:
            raw_inputs = raw_inputs.reshape(1, -1)
        if raw_inputs.shape[1] != len(base_names):
            raise ValueError(f"Expected {len(base_names)} columns, got {raw_inputs.shape[1]}")
        input_arrays = {name: raw_inputs[:, i] for i, name in enumerate(base_names)}
    else:
        # DataFrame — reorder to canonical order if columns match
        if set(raw_inputs.columns) == set(base_names):
            raw_inputs = raw_inputs[base_names]
        input_arrays = {col: raw_inputs[col].values for col in raw_inputs.columns}

    n_rows = next(iter(input_arrays.values())).shape[0] if input_arrays else 0
    n_features = len(feature_definitions)

    # Evaluate all derivations into a contiguous array
    result = np.empty((n_rows, n_features + 1), dtype=np.float64)
    for i, (_name, entry) in enumerate(feature_definitions.items()):
        result[:, i] = _eval_mathjson(entry["derivation"], input_arrays)
    result[:, -1] = 1.0  # intercept
    return result


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------


def run_model(
    coefficients: pd.DataFrame, feature_matrix: np.ndarray, feature_names: list[str] | None = None
) -> np.ndarray:
    """Compute predictions: (N, 347) @ (347, 23495) -> (N, 23495).

    Parameters
    ----------
    coefficients : pd.DataFrame
        Coefficient matrix loaded from parquet (includes a ``const`` column).
    feature_matrix : np.ndarray, shape (N, n_features + 1)
        Output of build_feature_vector (intercept column last).
    feature_names : list of str, optional
        Feature order used to build ``feature_matrix`` (the keys of the feature
        definitions). Defaults to the non-``const`` coefficient columns in order.

    Returns
    -------
    np.ndarray, shape (N, n_outputs)
    """
    # Align coefficient columns to the feature matrix by name. The parquet stores
    # ``const`` first, while build_feature_vector appends the intercept last.
    if feature_names is None:
        feature_names = [c for c in coefficients.columns if c != "const"]
    ordered = coefficients[[*feature_names, "const"]]
    if ordered.shape[1] != feature_matrix.shape[1]:
        raise ValueError(
            f"feature matrix has {feature_matrix.shape[1]} columns, "
            f"coefficients expect {ordered.shape[1]}"
        )
    return feature_matrix @ ordered.values.T


# ---------------------------------------------------------------------------
# Output unpacking
# ---------------------------------------------------------------------------


def _parse_output_column(col: str):
    """Split a flat output column name into (base_variable, dim_values, year).

    Column names follow ``BASE_VARIABLE[dim1, dim2, ...]_YEAR`` (bracket omitted
    when the variable has no dimensions), per the ``name_format`` documented in
    ``metadata/output_metadata.json``.
    """
    base_and_dims, year = col.rsplit("_", 1)
    if "[" in base_and_dims:
        base, bracket = base_and_dims[:-1].split("[", 1)
        values = tuple(v.strip() for v in bracket.split(","))
    else:
        base, values = base_and_dims, ()
    return base.rstrip(), values, int(year)


def unpack_outputs(predictions: pd.DataFrame, output_metadata: dict) -> pd.DataFrame:
    """Unpack the flat predictions DataFrame into one combined DataFrame across all outputs.

    Parameters
    ----------
    predictions : pd.DataFrame, shape (N, n_outputs)
        Output of ``run_model``/``run_pipeline``. Columns are the fully expanded
        output names (e.g. ``"AHC.MFSPMetric[HEFA, A]_2015"``).
    output_metadata : dict
        Parsed ``metadata/output_metadata.json`` (see ``load_output_metadata``).

    Returns
    -------
    pd.DataFrame
        Flat table (default row numbers), sorted by ``sample``, with ``sample``,
        ``variable``, ``pathway``, ``region``, ``product`` as regular columns,
        followed by one column per year. ``variable`` is the base output variable
        name (the 17 keys of ``output_metadata["variables"]``). Not every variable
        has every dimension (e.g. most don't have ``product``) -- dimensions that
        don't apply to a given variable are filled with ``""``. ``region`` values
        are expanded to their full names (e.g. ``"A"`` -> ``"Atlantic"``) via
        ``output_metadata["region_legend"]``. One row per output
        time series per sample (635 distinct (variable, pathway, region, product)
        series x N samples), each row holding all 37 years (2015-2051) as columns.
        Select a specific series with boolean
        filtering, e.g. ``df[(df["variable"] == "AHC.MFSPMetric") & (df["sample"] == 0)
        & (df["pathway"] == "HEFA") & (df["region"] == "Atlantic")]``. Use bracket indexing
        (``df["sample"]``, ``df["product"]``), not attribute access -- ``sample`` and
        ``product`` are also built-in DataFrame method names, so ``df.sample``/
        ``df.product`` silently return the method, not the column.
    """
    col_meta = {col: _parse_output_column(col) for col in predictions.columns}
    dim_names = ("pathway", "region", "product")

    frames = []
    for base, spec in output_metadata["variables"].items():
        dims = spec["dimensions"]
        cols = [c for c, (b, _, _) in col_meta.items() if b == base]

        sub = predictions[cols].copy()
        sub.index.name = "sample"

        if dims:
            tuples = [(*col_meta[c][1], col_meta[c][2]) for c in cols]
            sub.columns = pd.MultiIndex.from_tuples(tuples, names=[*dims, "year"])
            sub = sub.stack(level=list(range(len(dims))))
        else:
            sub.columns = pd.Index([col_meta[c][2] for c in cols], name="year")

        sub = sub.reset_index()
        for d in dim_names:
            if d not in sub.columns:
                sub[d] = ""
        sub["variable"] = base
        frames.append(sub)

    combined = pd.concat(frames, ignore_index=True)
    combined["region"] = combined["region"].replace(output_metadata["region_legend"])
    year_cols = sorted(c for c in combined.columns if c not in ("variable", "sample", *dim_names))
    combined = combined.sort_values(["sample", "variable", *dim_names], ignore_index=True)
    return combined[["sample", "variable", *dim_names, *year_cols]]


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


def run_pipeline(input_data_path: str | Path, data_dir: Path | None = None) -> pd.DataFrame:
    """Run the full BSM model pipeline from raw inputs to final predictions.

    Parameters
    ----------
    input_data_path : str or Path
        Path to the input Parquet or CSV file.
    data_dir : Path, optional
        Directory containing ``model_registry.json`` and the version folders.
        Defaults to the directory containing this script.

    Returns
    -------
    pd.DataFrame, shape (N, n_outputs)
        Final predictions. Columns are output variable names.
    """
    input_data_path = Path(input_data_path)
    if data_dir is None:
        data_dir = Path(__file__).parent
    data_dir = Path(data_dir)

    feature_defs = load_feature_definitions(data_dir)
    raw_inputs = load_inputs(input_data_path)
    coefficients = load_coefficients(data_dir)

    feature_matrix = build_feature_vector(feature_defs, raw_inputs)

    # Apply feature scaling if scale file exists
    feature_scale = _load_scale(data_dir, "feature_scale.parquet")
    if feature_scale is not None:
        feature_matrix = feature_matrix / feature_scale

    predictions = run_model(coefficients, feature_matrix, list(feature_defs))

    # Apply output scaling if scale file exists
    output_scale = _load_scale(data_dir, "output_scale.parquet")
    if output_scale is not None:
        predictions = predictions * output_scale

    return pd.DataFrame(predictions, columns=coefficients.index)
