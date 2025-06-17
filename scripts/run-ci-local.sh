#!/usr/bin/env bash

set -e

echo "Ruff"
ruff format .
ruff check .

echo "Mypy"
mypy .

echo "Pytest"
pytest

echo "Biome"
npx @biomejs/biome format --write .
npx @biomejs/biome lint .
npx @biomejs/biome check --fix .
