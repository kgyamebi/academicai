# Launch in the next hour — operator card

## Status: READY for free public launch (local stack green)

Billing stays **disabled**.

### Running now

| Service | URL / note |
| --- | --- |
| Frontend | http://localhost:3001 |
| API | http://localhost:8000 |
| Ready | http://127.0.0.1:8000/api/ready → redis + workers ≥ 1 |
| Postgres | localhost:5432 |
| Redis | localhost:6379 (Invoice App redis-server 5.x; client uses protocol=2) |
| Worker | RQ SimpleWorker (Windows) |

### Smoke proven

Register → paste draft → analysis queued → **report completed**.

### Before you tweet / share a public link

1. **HTTPS** in front of web+API (required).  
2. Update `.env` / `backend/.env`: `APP_WEB_URL`, `APP_API_URL`, `APP_CORS_ORIGINS` to your domain.  
3. `COOKIE_SECURE=true` once on HTTPS.  
4. Real SMTP for verification email (console = logs only).  
5. Paste Sentry DSN if you have one; restart API + worker.

### Restart commands (if needed)

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
.\.venv\Scripts\python.exe -m app.workers.rq_worker
cd ..\frontend
npm run start   # or next start -p 3001
```

### Do not

- Enable Stripe/Paystack  
- Expose HTTP ports raw to the internet  
- Claim WCAG/pentest certificates without deployed evidence  
