#!/usr/bin/env bash

# BACKEND_DOTENV_FILE="$(pwd)/.env"
# FRONTEND_DOTENV_FILE="$(pwd)/frontend/.env"


ACERE_FIRST_SUPERUSER_USERNAME="admin"
ACERE_FIRST_SUPERUSER_PASSWORD="$(openssl rand -base64 16)"
BACKEND_PORT=5101

# Export credentials for Playwright tests
export FIRST_SUPERUSER="${ACERE_FIRST_SUPERUSER_USERNAME}"
export FIRST_SUPERUSER_PASSWORD="${ACERE_FIRST_SUPERUSER_PASSWORD}"
export VITE_API_URL="http://localhost:${BACKEND_PORT}"

echo "Using credentials: ${FIRST_SUPERUSER} / ${FIRST_SUPERUSER_PASSWORD}"

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

# Wait for backend to be healthy
echo "Waiting for backend to be ready..."
for i in {1..30}; do
    if curl -f -s "http://localhost:${BACKEND_PORT}/api/v1/health" > /dev/null 2>&1; then
        echo "Backend is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "Backend failed to start within 30 seconds"
        docker logs AceReBackendPlaywright
        exit 1
    fi
    sleep 1
done

docker ps -a --filter "name=AceReBackendPlaywright" --format "table {{.Names}}\t{{.Status}}"

bun run --cwd frontend test:e2e

# Cleanup
echo "Stopping backend container..."
docker stop AceReBackendPlaywright > /dev/null 2>&1 || true

