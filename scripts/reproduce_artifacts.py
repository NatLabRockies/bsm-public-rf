"""Regenerate manuscript artifacts from committed final model artifacts.

Reads the committed CSVs in artifacts/ and regenerates figures and tables
using rfm_pipeline visualization utilities.
"""
from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("RFM_STUDY_ROOT", str(Path(__file__).parent))

from rfm_pipeline.config import load_config  # noqa: E402
from rfm_pipeline.manuscript_stages import build_manuscript_notebook_context  # noqa: E402


def main() -> None:
    config_path = Path(__file__).parent / "configs" / "manuscript_case_study.yml"
    cfg = load_config(str(config_path))
    context = build_manuscript_notebook_context(Path(__file__).parent, cfg)
    print(f"Context loaded: {context}")
    print("Artifact regeneration: run the manuscript notebooks in rfm-pipeline/notebooks/manuscript/")


if __name__ == "__main__":
    main()
