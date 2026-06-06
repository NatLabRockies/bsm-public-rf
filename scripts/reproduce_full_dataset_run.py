"""Reproduce the full BSM dataset run on HPC.

This script drives the rfm_pipeline orchestration using the BSM publication configs.
It is intended to be run from the bsm-public-rf repo root.
"""
from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Ensure RFM_STUDY_ROOT points to this repo root.
os.environ.setdefault("RFM_STUDY_ROOT", str(REPO_ROOT))

from rfm_pipeline.config import load_config  # noqa: E402
from rfm_pipeline.workflow import run_workflow  # noqa: E402


def main() -> None:
    config_path = REPO_ROOT / "configs" / "manuscript_case_study.yml"
    cfg = load_config(str(config_path))
    run_workflow(cfg)


if __name__ == "__main__":
    main()
