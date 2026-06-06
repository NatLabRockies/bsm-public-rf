"""Regenerate manuscript figures from committed final model artifacts.

Reads the committed CSVs in artifacts/ and writes publication-ready figures
to figures/. No raw BSM data or HPC infrastructure required.

Usage
-----
    pixi run reproduce-artifacts
    python scripts/reproduce_artifacts.py [--output-dir figures/]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Delegate to the dedicated figure generation module.
_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR))

from generate_manuscript_figures import generate_all  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--output-dir", default=None, help="Output directory (default: figures/)"
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir) if args.output_dir else None
    try:
        generate_all(output_dir=output_dir)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
