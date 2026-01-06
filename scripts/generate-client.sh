#! /usr/bin/env bash

set -e
set -x

export IN_OPEN_API_MODE=true

ORIGINAL_PWD=$(pwd)

if [ -z "$VIRTUAL_ENV" ]; then
    echo "Please run this script inside the virtual environment."
    exit 1
fi

if [ ! -f "$ORIGINAL_PWD/acere/main.py" ]; then
    echo "Please run this script from the root of the AceReStreamer repository."
    exit 1
fi

cd "$ORIGINAL_PWD"
# Generate OpenAPI spec for frontend
python -c "import acere.main; import json; print(json.dumps(acere.main.app.openapi()))" > "$ORIGINAL_PWD/frontend/openapi.json"
cd "$ORIGINAL_PWD/frontend"
npm run generate-client

# Generate frontend paths to help fastapi serve them when in all-in-one mode
cd "$ORIGINAL_PWD/frontend"
npx vite-node scripts/generate_frontend_route_list.ts "$ORIGINAL_PWD/acere/api/routes_frontend/generated_frontend_paths.json"
