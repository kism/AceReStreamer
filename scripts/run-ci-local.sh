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

if [ -d ~/.nvm ]; then
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
    [ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion
fi


nvm use

print_heading "npm lint"
npm run lint

print_heading "npm typecheck"
npm run typecheck
