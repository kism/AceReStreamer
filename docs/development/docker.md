# Docker Build

```bash
docker buildx build --network=host --file docker/Dockerfile.combined . -t acerestreamer
```

## Separate Frontend and Backend Container

```bash
docker buildx build --file docker/Dockerfile.backend . -t acerestreamer-backend
docker buildx build --build-arg VITE_API_URL="https://api.example.com" --file docker/Dockerfile.frontend ./frontend -t acerestreamer-frontend
```
