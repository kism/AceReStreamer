# Non-Docker Deployment

Build frontend to be served by fastapi

```bash
cd frontend
npm run build-aio
```

Run production server, you can use a `.env` file if you desire

```bash
export ACERE_ENVIRONMENT=production
export ACERE_APP__ACE_ADDRESS="http://localhost:6878"
export ACERE_FRONTEND_HOST="example.com"  # Set to your domain
uvicorn --workers 1 acere.main:app --host 0.0.0.0 --port 5100
```
