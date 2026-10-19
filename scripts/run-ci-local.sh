#!/usr/bin/env bash

set -euo pipefail

function print_heading() {
    echo
    echo "=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-="
    echo "$1 >>>"
}

source .venv/bin/activate

print_heading "ty"
ty check

print_heading "ruff"
ruff format
ruff check --fix

print_heading "PyTest"
pytest -q --tb=short

print_heading "docs"
sphinx-build --fail-on-warning -b html docs docs_out

cd frontend

print_heading "pnpm lint"
pnpm run lint

print_heading "pnpm typecheck"
pnpm run typecheck
