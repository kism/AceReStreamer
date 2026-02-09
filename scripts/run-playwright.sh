#!/usr/bin/env bash

# BACKEND_DOTENV_FILE="$(pwd)/.env"
# FRONTEND_DOTENV_FILE="$(pwd)/frontend/.env"


ACERE_FIRST_SUPERUSER_USERNAME="admin"
ACERE_FIRST_SUPERUSER_PASSWORD="$(openssl rand -base64 16)"
BACKEND_PORT=5101

# Backend
docker buildx build --file docker/Dockerfile.backend . -t acerestreamer-backend:latest

docker stop AceReBackendPlaywright > /dev/null 2>&1 || true
docker rm AceReBackendPlaywright > /dev/null 2>&1 || true

docker run \
    --rm \
    -d \
    --name AceReBackendPlaywright \
    -p ${BACKEND_PORT}:5100 \
    --mount type=bind,source="$(pwd)"/instance_test,target=/app/instance \
    -e ACERE_FIRST_SUPERUSER_USERNAME="${ACERE_FIRST_SUPERUSER_USERNAME}" \
    -e ACERE_FIRST_SUPERUSER_PASSWORD="${ACERE_FIRST_SUPERUSER_PASSWORD}" \
    -e ACERE_EXTERNAL_URL="http://localhost:${BACKEND_PORT}" \
    acerestreamer-backend:latest

docker ps -a --filter "name=AceReBackendPlaywright" --format "table {{.Names}}\t{{.Status}}"

bun run --cwd frontend test:e2e

