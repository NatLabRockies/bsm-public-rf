from __future__ import annotations

import hashlib
from pathlib import Path

import tomllib

from bsm_public_rf import __version__

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ARTIFACTS = {
    "coefficient_column_metadata.csv",
    "coefficient_matrix_raw_scale.csv",
    "per_output_intercepts.csv",
    "x_standardization.csv",
    "y_standardization.csv",
}


def test_wheel_declares_runtime_model_bundle_and_cli() -> None:
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = config["project"]
    data_files = config["tool"]["setuptools"]["data-files"]

    assert project["scripts"]["bsm-rf-predict"] == "bsm_public_rf.cli:main"
    packaged = {Path(path).name for path in data_files["share/bsm-public-rf/model"]}
    assert RUNTIME_ARTIFACTS <= packaged


def test_release_version_is_consistent() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

    assert __version__ == project["version"]
    assert f"version: {__version__}" in citation
    assert f"## {__version__}" in changelog


def test_model_checksum_manifest_covers_release_artifacts() -> None:
    model_dir = ROOT / "model"
    lines = (model_dir / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
    recorded = {}
    for line in lines:
        digest, filename = line.split("  ", maxsplit=1)
        recorded[filename] = digest

    expected = {path.name for path in [*model_dir.glob("*.csv"), *model_dir.glob("*.json")]}
    assert set(recorded) == expected
    for filename, expected_digest in recorded.items():
        actual = hashlib.sha256((model_dir / filename).read_bytes()).hexdigest()
        assert actual == expected_digest
