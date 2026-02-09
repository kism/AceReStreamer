#!/usr/bin/env bash

set -e

export ACERE_FIRST_SUPERUSER_USERNAME="admin"
ACERE_FIRST_SUPERUSER_PASSWORD="$(openssl rand -base64 16)"
export ACERE_FIRST_SUPERUSER_PASSWORD
export VITE_API_URL="http://acerestreamer-backend-playwright:5100"

# Backend
docker buildx build --file docker/Dockerfile.backend . -t acerestreamer-backend:latest
docker buildx build --file docker/Dockerfile.frontend --build-arg VITE_API_URL=${VITE_API_URL} . -t acerestreamer-frontend:latest

docker compose -f frontend/docker-compose.playwright.yml down --volumes --remove-orphans
docker compose -f frontend/docker-compose.playwright.yml up --build --abort-on-container-exit

docker logs acerestreamer-playwright-tests
