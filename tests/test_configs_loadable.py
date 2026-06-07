"""Smoke test: every standalone HPC YAML must load against the pinned rfm-pipeline.

Catches drift between this repo's configs and renames/removals in the pinned
rfm-pipeline (e.g. round-3 ``lasso_alpha_percentile -> lasso_alpha_grid_size``
and round-4 ``transform_families`` rejection). Partial / template configs that
are merged at runtime are intentionally excluded.
"""

from __future__ import annotations

import glob
from pathlib import Path

import pytest

from rfm_pipeline.config import load_config

REPO_ROOT = Path(__file__).resolve().parent.parent

STANDALONE_CONFIGS = [
    "configs/hpc/kestrel_publication_full_dataset.yml",
    "configs/hpc/kestrel_publication_full_dataset_distributed_base.yml",
    *sorted(
        p
        for p in glob.glob(str(REPO_ROOT / "configs/hpc/dev/kestrel_*.yml"))
        # ``workflow_*`` YAMLs are partial overlays consumed by the orchestrator,
        # not standalone WorkflowConfig payloads.
        if "workflow_" not in Path(p).name
    ),
]


@pytest.mark.parametrize("path", STANDALONE_CONFIGS)
def test_config_loads(path: str) -> None:
    load_config(str(REPO_ROOT / path) if not Path(path).is_absolute() else path)
