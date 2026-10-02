"""Load and evaluate the released BSM reduced-form coefficient bundle."""

from __future__ import annotations

import os
from collections.abc import Iterable
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path

import numpy as np
import pandas as pd


class ModelArtifactError(ValueError):
    """Raised when the files in a model bundle are missing or inconsistent."""


_REQUIRED_FILES = (
    "coefficient_column_metadata.csv",
    "coefficient_matrix_raw_scale.csv",
    "per_output_intercepts.csv",
    "x_standardization.csv",
    "y_standardization.csv",
)
_SUPPORTED_TRANSFORMS = {
    "identity",
    "interaction",
    "inverse",
    "log1p",
    "quadratic",
    "sqrt",
}


def default_model_dir() -> Path:
    """Return the released model directory.

    ``BSM_PUBLIC_RF_MODEL_DIR`` takes precedence. Source checkouts use their
    top-level ``model/`` directory, while installed distributions use the
    bundle installed under ``share/bsm-public-rf/model``.
    """
    configured = os.environ.get("BSM_PUBLIC_RF_MODEL_DIR")
    if configured:
        return Path(configured).expanduser().resolve()
    checkout_model_dir = Path(__file__).resolve().parents[2] / "model"
    if checkout_model_dir.is_dir():
        return checkout_model_dir
    try:
        distribution = metadata.distribution("bsm-public-rf")
    except metadata.PackageNotFoundError:
        return checkout_model_dir
    # Data files install under the environment prefix, not site-packages, so use
    # the installed RECORD (e.g. ``../../share/bsm-public-rf/model/...``).
    for file in distribution.files or ():
        if file.parts[-3:] == ("bsm-public-rf", "model", "x_standardization.csv"):
            return Path(distribution.locate_file(file)).resolve().parent
    return Path(distribution.locate_file("share/bsm-public-rf/model")).resolve()


def _require_columns(frame: pd.DataFrame, columns: set[str], *, source: Path) -> None:
    missing = sorted(columns.difference(frame.columns))
    if missing:
        raise ModelArtifactError(f"{source.name} is missing required columns: {missing}")


def _require_finite(frame: pd.DataFrame, *, label: str) -> None:
    try:
        values = frame.to_numpy(dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must contain numeric values") from exc
    if not np.isfinite(values).all():
        raise ValueError(f"{label} must contain only finite values")


@dataclass(frozen=True)
class BSMReducedFormModel:
    """In-memory representation of the released linear surrogate.

    The coefficient matrix is on the raw output scale. Prediction centers each
    engineered input feature by its training mean, multiplies by the matching
    coefficient row, and adds the per-output intercept.
    """

    artifact_dir: Path
    coefficients: pd.DataFrame
    intercepts: pd.Series
    feature_metadata: pd.DataFrame
    feature_means: pd.Series
    output_metadata: pd.DataFrame

    @classmethod
    def from_artifact_dir(cls, artifact_dir: str | Path) -> BSMReducedFormModel:
        """Load a model bundle and fail closed on schema or ordering drift."""
        root = Path(artifact_dir).expanduser().resolve()
        missing_files = [name for name in _REQUIRED_FILES if not (root / name).is_file()]
        if missing_files:
            raise ModelArtifactError(
                f"model bundle {root} is missing required files: {missing_files}"
            )

        metadata_path = root / "coefficient_column_metadata.csv"
        metadata = pd.read_csv(metadata_path)
        _require_columns(
            metadata,
            {
                "coefficient_column_index",
                "feature_name",
                "transformation",
                "base_input_1",
                "base_input_2",
            },
            source=metadata_path,
        )
        if metadata["feature_name"].duplicated().any():
            raise ModelArtifactError("coefficient metadata contains duplicate feature names")
        expected_positions = np.arange(len(metadata))
        if not np.array_equal(metadata["coefficient_column_index"].to_numpy(), expected_positions):
            raise ModelArtifactError("coefficient metadata positions are not contiguous")
        unsupported = sorted(set(metadata["transformation"]) - _SUPPORTED_TRANSFORMS)
        if unsupported:
            raise ModelArtifactError(f"unsupported feature transformations: {unsupported}")

        coefficients = pd.read_csv(
            root / "coefficient_matrix_raw_scale.csv", index_col="output_name"
        )
        if coefficients.index.has_duplicates:
            raise ModelArtifactError("coefficient matrix contains duplicate output names")

        standardization_path = root / "x_standardization.csv"
        standardization = pd.read_csv(standardization_path)
        _require_columns(
            standardization,
            {"feature_name", "original_position", "mean", "scale"},
            source=standardization_path,
        )

        feature_names = metadata["feature_name"].astype(str).tolist()
        if feature_names != coefficients.columns.astype(str).tolist():
            raise ModelArtifactError(
                "coefficient matrix feature order does not match coefficient metadata"
            )
        if feature_names != standardization["feature_name"].astype(str).tolist():
            raise ModelArtifactError(
                "x_standardization feature order does not match coefficient metadata"
            )
        if not np.array_equal(standardization["original_position"].to_numpy(), expected_positions):
            raise ModelArtifactError("x_standardization positions are not contiguous")

        intercept_path = root / "per_output_intercepts.csv"
        intercept_frame = pd.read_csv(intercept_path)
        _require_columns(intercept_frame, {"output_name", "intercept"}, source=intercept_path)
        if intercept_frame["output_name"].duplicated().any():
            raise ModelArtifactError("intercept vector contains duplicate output names")
        intercepts = intercept_frame.set_index("output_name")["intercept"]
        if coefficients.index.astype(str).tolist() != intercepts.index.astype(str).tolist():
            raise ModelArtifactError(
                "intercept output order does not match coefficient matrix output order"
            )

        output_path = root / "y_standardization.csv"
        output_metadata = pd.read_csv(output_path)
        _require_columns(
            output_metadata,
            {"output_name", "original_position", "mean", "scale"},
            source=output_path,
        )
        if (
            coefficients.index.astype(str).tolist()
            != output_metadata["output_name"].astype(str).tolist()
        ):
            raise ModelArtifactError(
                "y_standardization output order does not match coefficient matrix"
            )
        if not np.array_equal(
            output_metadata["original_position"].to_numpy(),
            np.arange(len(output_metadata)),
        ):
            raise ModelArtifactError("y_standardization positions are not contiguous")

        _require_finite(coefficients, label="coefficient matrix")
        _require_finite(intercepts.to_frame(), label="intercept vector")
        _require_finite(standardization[["mean", "scale"]], label="feature scaling")
        _require_finite(output_metadata[["mean", "scale"]], label="output scaling")
        if (standardization["scale"] <= 0).any():
            raise ModelArtifactError("feature scales must be positive")
        if (output_metadata["scale"] <= 0).any():
            raise ModelArtifactError("output scales must be positive")
        if not np.allclose(
            intercepts.to_numpy(dtype=float),
            output_metadata["mean"].to_numpy(dtype=float),
            rtol=8 * np.finfo(float).eps,
            atol=1e-12,
        ):
            raise ModelArtifactError("output means do not match the intercept vector")

        return cls(
            artifact_dir=root,
            coefficients=coefficients,
            intercepts=intercepts,
            feature_metadata=metadata,
            feature_means=standardization.set_index("feature_name")["mean"],
            output_metadata=output_metadata.set_index("output_name"),
        )

    @property
    def feature_names(self) -> tuple[str, ...]:
        """Engineered feature names in coefficient-column order."""
        return tuple(self.coefficients.columns.astype(str))

    @property
    def output_names(self) -> tuple[str, ...]:
        """Output names in coefficient-row order."""
        return tuple(self.coefficients.index.astype(str))

    @property
    def required_input_names(self) -> tuple[str, ...]:
        """Base BSM inputs needed to materialize the selected feature support."""
        names: list[str] = []
        for row in self.feature_metadata.itertuples(index=False):
            for name in (str(row.base_input_1), str(row.base_input_2)):
                if name and name != "nan" and name not in names:
                    names.append(name)
        return tuple(names)

    def input_schema(self) -> pd.DataFrame:
        """Return one metadata row for each base input used by the model."""
        primary_columns = [
            "base_input_1",
            "base_input_1_unit",
            "base_input_1_min",
            "base_input_1_max",
            "base_input_1_pathway",
            "base_input_1_description",
        ]
        available = [name for name in primary_columns if name in self.feature_metadata.columns]
        primary = self.feature_metadata[available].drop_duplicates("base_input_1")
        primary = primary.rename(
            columns={
                "base_input_1": "input_name",
                "base_input_1_unit": "unit",
                "base_input_1_min": "minimum",
                "base_input_1_max": "maximum",
                "base_input_1_pathway": "pathway",
                "base_input_1_description": "description",
            }
        )

        secondary_columns = [
            name
            for name in ("base_input_2", "base_input_2_unit")
            if name in self.feature_metadata.columns
        ]
        secondary = self.feature_metadata[secondary_columns].copy()
        secondary = secondary.loc[secondary["base_input_2"].notna()]
        secondary = secondary.loc[secondary["base_input_2"].astype(str).str.len() > 0]
        secondary = secondary.rename(
            columns={"base_input_2": "input_name", "base_input_2_unit": "unit"}
        ).drop_duplicates("input_name")
        for column in ("minimum", "maximum", "pathway", "description"):
            secondary[column] = pd.NA

        schema = pd.concat([primary, secondary], ignore_index=True)
        schema = schema.drop_duplicates("input_name").set_index("input_name")
        return schema.reindex(self.required_input_names)

    def output_schema(self) -> pd.DataFrame:
        """Return output names, positions, training means, and scales."""
        return self.output_metadata.copy()

    def transform_inputs(self, inputs: pd.DataFrame) -> pd.DataFrame:
        """Materialize the released 245-feature support from base BSM inputs."""
        if not isinstance(inputs, pd.DataFrame):
            raise TypeError("inputs must be a pandas DataFrame")
        if inputs.columns.has_duplicates:
            raise ValueError("inputs must not contain duplicate column names")
        missing = [name for name in self.required_input_names if name not in inputs.columns]
        if missing:
            raise ValueError(f"inputs are missing required base columns: {missing}")
        raw = inputs.loc[:, self.required_input_names]
        _require_finite(raw, label="inputs")

        invalid: list[str] = []
        for row in self.feature_metadata.itertuples(index=False):
            values = raw[str(row.base_input_1)].to_numpy(dtype=float)
            transform = str(row.transformation)
            if transform == "sqrt" and (values < 0).any():
                invalid.append(f"square-root feature {row.feature_name} received values below zero")
            elif transform == "log1p" and (values <= -1).any():
                invalid.append(f"log1p feature {row.feature_name} received values at or below -1")
            elif transform == "inverse" and (values == 0).any():
                invalid.append(f"inverse feature {row.feature_name} received zero")
        if invalid:
            raise ValueError("; ".join(invalid))

        transformed: dict[str, np.ndarray] = {}
        for row in self.feature_metadata.itertuples(index=False):
            first = raw[str(row.base_input_1)].to_numpy(dtype=float)
            transform = str(row.transformation)
            if transform == "identity":
                values = first
            elif transform == "quadratic":
                values = np.square(first)
            elif transform == "sqrt":
                values = np.sqrt(first)
            elif transform == "log1p":
                values = np.log1p(first)
            elif transform == "inverse":
                values = np.reciprocal(first)
            elif transform == "interaction":
                second = raw[str(row.base_input_2)].to_numpy(dtype=float)
                values = first * second
            else:  # guarded during load; retained as a fail-closed boundary
                raise ModelArtifactError(f"unsupported transformation: {transform}")
            transformed[str(row.feature_name)] = values

        return pd.DataFrame(transformed, index=inputs.index).loc[:, self.feature_names]

    def predict(
        self, inputs: pd.DataFrame, *, outputs: Iterable[str] | None = None
    ) -> pd.DataFrame:
        """Predict BSM outputs from base input columns."""
        return self.predict_features(self.transform_inputs(inputs), outputs=outputs)

    def predict_features(
        self, features: pd.DataFrame, *, outputs: Iterable[str] | None = None
    ) -> pd.DataFrame:
        """Predict from a precomputed engineered-feature matrix."""
        if not isinstance(features, pd.DataFrame):
            raise TypeError("features must be a pandas DataFrame")
        if features.columns.has_duplicates:
            raise ValueError("features must not contain duplicate column names")
        missing = [name for name in self.feature_names if name not in features.columns]
        if missing:
            raise ValueError(f"features are missing required columns: {missing}")
        aligned = features.loc[:, self.feature_names]
        _require_finite(aligned, label="features")

        if outputs is None:
            selected_outputs = list(self.output_names)
        else:
            selected_outputs = list(outputs)
            if len(selected_outputs) != len(set(selected_outputs)):
                raise ValueError("outputs contains duplicate names")
            unknown = [name for name in selected_outputs if name not in self.coefficients.index]
            if unknown:
                raise ValueError(f"unknown output names: {unknown}")

        centered = aligned.to_numpy(dtype=float) - self.feature_means.loc[
            list(self.feature_names)
        ].to_numpy(dtype=float)
        coefficients = self.coefficients.loc[selected_outputs].to_numpy(dtype=float)
        predictions = centered @ coefficients.T
        predictions += self.intercepts.loc[selected_outputs].to_numpy(dtype=float)
        return pd.DataFrame(predictions, index=features.index, columns=selected_outputs)


def load_model(artifact_dir: str | Path | None = None) -> BSMReducedFormModel:
    """Load the released model from ``artifact_dir`` or the checkout default."""
    return BSMReducedFormModel.from_artifact_dir(
        default_model_dir() if artifact_dir is None else artifact_dir
    )
