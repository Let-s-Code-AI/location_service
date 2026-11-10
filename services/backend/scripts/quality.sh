#!/usr/bin/env bash
# Quality gate for the backend: lint, formatting check and tests with coverage.
# Run from any directory; it changes into services/backend itself.
#
#   ./scripts/quality.sh
#
# Prefers the project venv (venv/bin) when it exists, so local runs use the
# pinned tool versions even if another ruff/pytest is on PATH. CI has no venv:
# the tools are installed into the system interpreter and found on PATH.
# The ruff rule set and the coverage threshold (fail_under) live in
# pyproject.toml. Writes coverage.xml, which CI feeds to diff-cover.

set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

if [ -x venv/bin/ruff ]; then
    PATH="$PWD/venv/bin:$PATH"
fi

echo "▶ Lint: ruff check"
ruff check .

echo "▶ Formatowanie: ruff format --check"
ruff format --check .

echo "▶ Testy z pokryciem: pytest --cov"
pytest -q --cov --cov-report=term-missing --cov-report=xml

echo "✅ Quality gate backendu: OK"
