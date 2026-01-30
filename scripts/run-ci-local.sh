#!/usr/bin/env bash

set -euo pipefail

function print_heading() {
    echo
    echo "=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-="
    echo "$1 >>>"
}

source .venv/bin/activate

print_heading "mypy"
mypy

print_heading "ty"
ty check

print_heading "ruff"
ruff format
ruff check --fix

print_heading "PyTest"
pytest -q --tb=short

print_heading "docs"
sphinx-build -M html docs docs_out

cd frontend

export BUN_INSTALL="$HOME/.bun"
export PATH="$BUN_INSTALL/bin:$PATH"

print_heading "bun lint"
bun run lint

print_heading "bun typecheck"
bun run typecheck
