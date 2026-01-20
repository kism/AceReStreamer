# Development

## Backend (FastAPI)

### Generate SDK and clinent

```bash
./scripts/generate-client.sh
```

### Run

Run development server

```bash
fastapi dev --reload --port 5100 --entrypoint acere.main:app
```

To be accessable from other hosts:

```bash
fastapi dev --reload  --host 0.0.0.0 --port 5100 --entrypoint acere.main:app
```

## Frontend (Vite + React)

Open a new vscode window in the `frontend/` folder:

```bash
code frontend/
```

```bash
bun install
```

Run development server, you can use a `.env` file if desired. The variable will affect builds, not just the dev server.

```bash
export VITE_BACKEND_URL="http://localhost:5100"  # Adjust if your backend is running elsewhere
bun run dev
```

## Docker Build

Build a combined container with both frontend and backend:

```bash
docker buildx build --network=host --file docker/Dockerfile.combined . -t acerestreamer
```

### Separate Frontend and Backend Container

Build the backend and frontend containers separately:

```bash
docker buildx build --file docker/Dockerfile.backend . -t acerestreamer-backend
docker buildx build --build-arg VITE_API_URL="https://api.example.com" --file docker/Dockerfile.frontend ./frontend -t acerestreamer-frontend
```
