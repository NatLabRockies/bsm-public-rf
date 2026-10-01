"""Predict one released BSM output for the bundled example scenarios."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from bsm_public_rf import load_model

EXAMPLE_INPUTS = Path(__file__).with_name("example_inputs.csv")
EXAMPLE_OUTPUT = "AHC.MFSPMetric[HEFA, A]_2030"


def main() -> None:
    """Load the model and print labelled predictions for the example inputs."""
    model = load_model()
    inputs = pd.read_csv(EXAMPLE_INPUTS, index_col="scenario")
    predictions = model.predict(inputs, outputs=[EXAMPLE_OUTPUT])

    print(f"Loaded {len(model.feature_names)} features and {len(model.output_names)} outputs")
    print(predictions.to_string())


if __name__ == "__main__":
    main()
