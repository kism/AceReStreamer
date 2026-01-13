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
export ACERE_FIRST_SUPERUSER_USERNAME="admin"
export ACERE_FIRST_SUPERUSER_PASSWORD="" # This will only set the password on first run, if empty a random password will be generated and printed in the logs
uvicorn --workers 1 acere.main:app --host 0.0.0.0 --port 5100
```
