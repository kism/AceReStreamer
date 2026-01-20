#!/usr/bin/env bash

set -euo pipefail

function print_heading() {
    echo
    echo "=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-="
    echo "$1 >>>"
    echo
}

source .venv/bin/activate

print_heading "PyTest"
pytest -q --tb=short

print_heading "mypy"
mypy

print_heading "tc"
ty check

print_heading "ruff"
ruff check

cd frontend

export BUN_INSTALL="$HOME/.bun"
export PATH="$BUN_INSTALL/bin:$PATH"

print_heading "bun lint"
bun run lint

print_heading "bun typecheck"
bun run typecheck
