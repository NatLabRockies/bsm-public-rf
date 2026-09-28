from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_repository_contains_only_public_model_surfaces() -> None:
    forbidden = ["configs", "docs", "figures", "scripts", ".slice-runner.toml"]
    assert not [name for name in forbidden if (ROOT / name).exists()]


def test_model_bundle_contains_required_release_files() -> None:
    model_root = ROOT / "model"
    required = {
        "README.md",
        "coefficient_column_metadata.csv",
        "coefficient_matrix_raw_scale.csv",
        "coefficient_matrix_standardized.csv",
        "final_support_features.csv",
        "per_output_intercepts.csv",
        "x_standardization.csv",
        "y_standardization.csv",
    }
    assert required <= {path.name for path in model_root.iterdir()}
