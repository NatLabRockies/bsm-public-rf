#!/usr/bin/env bash
set -euo pipefail

MODE="${1:---check}"
PIXI_BIN="${PIXI_BIN:-pixi}"

usage() {
  cat <<'USAGE'
Usage:
  ./test_repo.sh [--check|--check-only|--ci]
  ./test_repo.sh --fix
  ./test_repo.sh --clean
USAGE
}

if [[ "${MODE}" == "--help" || "${MODE}" == "-h" ]]; then
  usage
  exit 0
fi

if ! command -v "${PIXI_BIN}" >/dev/null 2>&1; then
  echo "error: pixi executable not found: ${PIXI_BIN}" >&2
  exit 1
fi

if [[ "${MODE}" == "--clean" ]]; then
  rm -rf .pytest_cache .ruff_cache build dist src/*.egg-info
  find . -path ./.pixi -prune -o -type d -name __pycache__ -exec rm -rf {} +
  MODE="--check"
fi

if [[ "${MODE}" == "--fix" ]]; then
  "${PIXI_BIN}" run format
  MODE="--check"
fi

if [[ "${MODE}" == "--check-only" || "${MODE}" == "--ci" ]]; then
  MODE="--check"
fi

if [[ "${MODE}" != "--check" ]]; then
  echo "error: unknown mode: ${MODE}" >&2
  usage >&2
  exit 2
fi

"${PIXI_BIN}" run test
"${PIXI_BIN}" run lint
"${PIXI_BIN}" run format-check
git diff --check
