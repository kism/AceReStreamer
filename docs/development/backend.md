# Development Tools

## Generate SDK and clinent

```bash
./scripts/generate-client.sh
```

## Run

Run development server

```bash
fastapi dev --reload --port 5100 --entrypoint acere.main:app
```

To be accessable from other hosts:

```bash
fastapi dev --reload  --host 0.0.0.0 --port 5100 --entrypoint acere.main:app
```
