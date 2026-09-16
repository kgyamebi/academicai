# Social login setup (Google + Microsoft)

AcademicCheck supports **Continue with Google**, **Continue with Microsoft**, and email/password.

Buttons appear only when the matching env vars are set.

## 1. Redirect URIs (required)

Use the **public site** API path (Caddy proxies `/api` → backend):

- `https://academiccheck.org/api/auth/oauth/google/callback`
- `https://academiccheck.org/api/auth/oauth/microsoft/callback`

Local:

- `http://localhost:8000/api/auth/oauth/google/callback`
- `http://localhost:8000/api/auth/oauth/microsoft/callback`

Set in production `.env`:

```bash
APP_WEB_URL=https://academiccheck.org
# If APP_API_URL is http://127.0.0.1:8000 (Docker internal), OAuth still uses APP_WEB_URL
# for redirect URIs automatically. Or set explicitly:
OAUTH_REDIRECT_BASE=https://academiccheck.org
APP_API_URL=https://academiccheck.org
```

## 2. Google Cloud Console

1. Create OAuth client (Web application)
2. Authorized JavaScript origins: `https://academiccheck.org`
3. Authorized redirect URIs: the Google callback above
4. Copy Client ID + Secret into:

```bash
GOOGLE_OAUTH_CLIENT_ID=...
GOOGLE_OAUTH_CLIENT_SECRET=...
```

## 3. Microsoft Entra (Azure AD)

1. App registration → Web redirect URI = Microsoft callback above
2. API permissions: Microsoft Graph `User.Read` (delegated), plus openid/email/profile
3. Create a client secret
4. Supported account types: **Accounts in any org + personal Microsoft accounts** (`common`)
5. Copy Application (client) ID + secret:

```bash
MICROSOFT_OAUTH_CLIENT_ID=...
MICROSOFT_OAUTH_CLIENT_SECRET=...
```

## 4. Deploy

```bash
cd ~/academicai
# add OAuth vars to .env
docker compose -f docker-compose.prod.yml exec api alembic upgrade head
# or recreate api after env change
docker compose -f docker-compose.prod.yml up -d --force-recreate api worker
cd frontend && npm ci && npm run build
sudo systemctl restart academiccheck-next
```

## Behaviour

- New social users: verified email (when IdP asserts it), free plan, redirect to `/onboarding`
- Existing email account: links provider and signs in (no duplicate user)
- OAuth-only users have no password (use social or password reset after setting one later)
