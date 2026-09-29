"""Run one self-contained prediction with the bundled BSM model."""

from __future__ import annotations

import pandas as pd

from bsm_public_rf import BSMReducedFormModel, load_model


def make_smoke_test_inputs(model: BSMReducedFormModel) -> pd.DataFrame:
    """Return one finite synthetic row for checking an installation.

    The values are intentionally simple and are not a scientifically meaningful
    BSM scenario. Use :meth:`BSMReducedFormModel.input_schema` to prepare real
    inputs and review their historical ranges.
    """
    return pd.DataFrame({name: [1.0] for name in model.required_input_names})


def main() -> None:
    """Load the bundle and print three predictions for a synthetic input row."""
    model = load_model()
    inputs = make_smoke_test_inputs(model)
    outputs = model.output_names[:3]
    predictions = model.predict(inputs, outputs=outputs)

    print(f"Loaded {len(model.feature_names)} features and {len(model.output_names)} outputs")
    print(predictions.to_string(index=False))


if __name__ == "__main__":
    main()
