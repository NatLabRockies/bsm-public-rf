"""Reproduce the full BSM dataset run on HPC.

This script drives the rfm_pipeline orchestration using the BSM publication configs.
It is intended to be run from the bsm-public-rf repo root.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "configs" / "hpc" / "kestrel_publication_full_dataset.yml"
RUNNER_PATH = REPO_ROOT / "scripts" / "run_manuscript_pipeline.py"

# Ensure RFM_STUDY_ROOT points to this repo root.
os.environ.setdefault("RFM_STUDY_ROOT", str(REPO_ROOT))

from rfm_pipeline.config import load_config  # noqa: E402
from rfm_pipeline.workflow import run_canonical_workflow as _rfm_run_canonical_workflow  # noqa: F401,E402


def run_canonical_workflow(cfg: object) -> None:
    if not RUNNER_PATH.is_file():
        raise FileNotFoundError(f"Pipeline runner not found: {RUNNER_PATH}")
    subprocess.run([sys.executable, str(RUNNER_PATH), str(CONFIG_PATH)], check=True)


def main() -> None:
    cfg = load_config(str(CONFIG_PATH))
    run_canonical_workflow(cfg)


if __name__ == "__main__":
    main()
