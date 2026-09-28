"""Predict selected BSM outputs from a CSV of base input values."""

from __future__ import annotations

import argparse

import pandas as pd

from bsm_public_rf import load_model


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", help="CSV containing one row per case and the required inputs")
    parser.add_argument("predictions", help="Destination CSV for predictions")
    parser.add_argument(
        "--output",
        action="append",
        dest="outputs",
        help="Output name to predict; repeat to select multiple outputs (default: all)",
    )
    parser.add_argument(
        "--model-dir",
        default=None,
        help=(
            "Model artifact directory (default: BSM_PUBLIC_RF_MODEL_DIR or the checkout's ./model)"
        ),
    )
    args = parser.parse_args()

    model = load_model(args.model_dir)
    inputs = pd.read_csv(args.inputs)
    model.predict(inputs, outputs=args.outputs).to_csv(args.predictions, index=False)


if __name__ == "__main__":
    main()
