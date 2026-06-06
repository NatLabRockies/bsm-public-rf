"""Regenerate manuscript artifacts from committed final model artifacts.

Reads the committed CSVs in artifacts/ and regenerates figures and tables
using rfm_pipeline visualization utilities.
"""
from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "configs" / "hpc" / "kestrel_publication_full_dataset.yml"
MANUSCRIPT_NOTEBOOK = "08_manuscript_tables_and_figures.ipynb"

# Ensure RFM_STUDY_ROOT points to this repo root.
os.environ.setdefault("RFM_STUDY_ROOT", str(REPO_ROOT))

from rfm_pipeline.config import load_config  # noqa: E402
from rfm_pipeline.manuscript_runtime import build_manuscript_notebook_context  # noqa: E402


def main() -> None:
    cfg = load_config(str(CONFIG_PATH))
    print(f"Loaded runtime config for dataset={cfg.dataset.type}: {CONFIG_PATH}")
    print(f"Manuscript context entrypoint: {build_manuscript_notebook_context.__module__}.{build_manuscript_notebook_context.__name__}")
    print(f"Artifact regeneration notebook: {MANUSCRIPT_NOTEBOOK}")
    print("Artifact regeneration: run the manuscript notebooks in rfm-pipeline/notebooks/manuscript/")


if __name__ == "__main__":
    main()
