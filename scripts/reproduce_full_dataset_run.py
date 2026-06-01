"""Reproduce the full BSM dataset run on Kestrel HPC.

This script drives the rfm_pipeline orchestration using the BSM publication configs.
It is intended to be run from the bsm-public-rf repo root.
"""
from __future__ import annotations

import os
from pathlib import Path

# Ensure RFM_STUDY_ROOT points to this repo
os.environ.setdefault("RFM_STUDY_ROOT", str(Path(__file__).parent))

from rfm_pipeline.config import load_config  # noqa: E402
from rfm_pipeline.workflow import run_workflow  # noqa: E402


def main() -> None:
    config_path = Path(__file__).parent / "configs" / "manuscript_case_study.yml"
    cfg = load_config(str(config_path))
    run_workflow(cfg)


if __name__ == "__main__":
    main()
