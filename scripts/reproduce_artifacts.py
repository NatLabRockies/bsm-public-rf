"""Regenerate manuscript artifacts from committed final model artifacts.

Reads the committed CSVs in artifacts/ and regenerates figures and tables
using rfm_pipeline visualization utilities.
"""
from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Ensure RFM_STUDY_ROOT points to this repo root.
os.environ.setdefault("RFM_STUDY_ROOT", str(REPO_ROOT))

from rfm_pipeline.config import load_config  # noqa: E402
from rfm_pipeline.manuscript_stages import build_manuscript_notebook_context  # noqa: E402


def main() -> None:
    config_path = REPO_ROOT / "configs" / "manuscript_case_study.yml"
    cfg = load_config(str(config_path))
    context = build_manuscript_notebook_context(REPO_ROOT, cfg)
    print(f"Context loaded: {context}")
    print("Artifact regeneration: run the manuscript notebooks in rfm-pipeline/notebooks/manuscript/")


if __name__ == "__main__":
    main()
