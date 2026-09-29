"""Command-line prediction interface for the released BSM model."""

from __future__ import annotations

import argparse

import pandas as pd

from .model import load_model


def main() -> None:
    """Load base inputs from CSV and write reduced-form predictions."""
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
        help="Override the bundled model artifact directory",
    )
    args = parser.parse_args()

    model = load_model(args.model_dir)
    inputs = pd.read_csv(args.inputs)
    model.predict(inputs, outputs=args.outputs).to_csv(args.predictions, index=False)


if __name__ == "__main__":
    main()
