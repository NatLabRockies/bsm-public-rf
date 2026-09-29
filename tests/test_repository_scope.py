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


def test_ci_uses_the_repository_gate() -> None:
    pixi = (ROOT / "pixi.toml").read_text(encoding="utf-8")
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    assert 'gate = "pytest -q && ruff check src tests examples' in pixi
    assert "pixi run gate" in workflow


def test_internal_policy_files_are_not_part_of_the_public_repository() -> None:
    forbidden = ["AGENTS.md", "CODE_OF_CONDUCT.md", "SECURITY.md", "test_repo.sh"]
    assert not [name for name in forbidden if (ROOT / name).exists()]
