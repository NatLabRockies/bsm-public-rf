# Changelog

All notable changes to the public BSM reduced-form model distribution are
documented in this file.

## 0.1.0

Initial public release candidate.

### Added

- `model/output_metadata.json` with descriptions, units, dimensions, and region and
  product legends for all 17 output variables (635 series).
- `output_catalog`, `parse_output_name`, and `unpack_outputs` for labelling and
  reshaping predictions.
- `examples/quickstart.ipynb` and `examples/example_inputs.csv`.
- `versions/BSM_RFM_v1`, an archived 346-feature, 62-input model fit with its loader
  `versions/bsm_model_utils.py`.
- `win-64` Pixi platform and an optional `notebook` environment.
- The existing 23,495-output, 245-feature BSM coefficient bundle.
- Fail-closed artifact alignment and numeric validation.
- Base-input feature construction and selected-output prediction.
- An installable `bsm-rf-predict` command.
- Model SHA-256 checksums.
- Source-checkout and installed-wheel model discovery.

### Fixed

- installed wheels now find the bundled model: data files install under the
  environment prefix (`<prefix>/share/...`), not `site-packages/share/...`, so
  `default_model_dir()` follows the installed RECORD.
- `.gitattributes` keeps model files byte-identical on Windows so `SHA256SUMS`
  verifies after checkout.
- `input_schema()` includes inputs that appear only as the second operand of an
  interaction.
- The command-line predictor can preserve a named scenario column.

### Notes

- This release contains the retained model export; no new model fit was performed.
- Raw BSM simulator runs are not distributed and are not needed for inference.
