from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_prediction_example_runs_from_source_checkout() -> None:
    root = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(root / "src")

    result = subprocess.run(
        [sys.executable, str(root / "examples" / "predict.py")],
        cwd=root,
        env=env,
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert "Loaded 245 features and 23495 outputs" in result.stdout
