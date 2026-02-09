#!/usr/bin/env bash

set -e

ACERE_FIRST_SUPERUSER_USERNAME="admin"
ACERE_FIRST_SUPERUSER_PASSWORD="$(openssl rand -base64 16)"
DOTENV_FILE="$(pwd)/frontend/.env_playwright"
VITE_API_URL="http://acerestreamer-backend-playwright:5101"

echo "ACERE_FIRST_SUPERUSER_USERNAME=${ACERE_FIRST_SUPERUSER_USERNAME}" >"${DOTENV_FILE}"
echo "ACERE_FIRST_SUPERUSER_PASSWORD=${ACERE_FIRST_SUPERUSER_PASSWORD}" >>"${DOTENV_FILE}"
echo "VITE_API_URL=${VITE_API_URL}" >>"${DOTENV_FILE}"

# Backend
docker buildx build --file docker/Dockerfile.backend . -t acerestreamer-backend:latest
docker buildx build --file docker/Dockerfile.frontend --build-arg VITE_API_URL=${VITE_API_URL} . -t acerestreamer-frontend:latest

docker compose -f frontend/docker-compose.playwright.yml --env-file "${DOTENV_FILE}" up --build --abort-on-container-exit

docker logs acerestreamer-playwright-tests
