from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

from bsm_public_rf import load_model
from bsm_public_rf.cli import main

ROOT = Path(__file__).resolve().parents[1]


def test_cli_predicts_selected_output(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    inputs = pd.read_csv(ROOT / "examples" / "example_inputs.csv").head(2)
    input_path = tmp_path / "inputs.csv"
    prediction_path = tmp_path / "predictions.csv"
    inputs.to_csv(input_path, index=False)

    output_name = load_model().output_names[0]
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "bsm-rf-predict",
            str(input_path),
            str(prediction_path),
            "--output",
            output_name,
        ],
    )

    main()

    predictions = pd.read_csv(prediction_path)
    assert predictions.columns.tolist() == [output_name]
    assert len(predictions) == len(inputs)
    assert predictions[output_name].notna().all()


def test_cli_can_preserve_a_named_scenario_column(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    inputs = pd.read_csv(ROOT / "examples" / "example_inputs.csv").head(2)
    input_path = tmp_path / "inputs.csv"
    prediction_path = tmp_path / "predictions.csv"
    inputs.to_csv(input_path, index=False)

    output_name = load_model().output_names[0]
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "bsm-rf-predict",
            str(input_path),
            str(prediction_path),
            "--index-column",
            "scenario",
            "--output",
            output_name,
        ],
    )

    main()

    predictions = pd.read_csv(prediction_path)
    assert predictions["scenario"].tolist() == inputs["scenario"].tolist()
