# Feature: Google OAuth & Authentication

## Basic Flow

1. On first load the frontend detects `connected: false` from `/api/auth/status` and shows the **Connect Google** screen.
2. User clicks Connect → frontend calls `GET /api/auth/login` → backend returns a Google consent URL → browser redirects there.
3. After consent Google redirects to `http://localhost:8000/api/auth/callback?code=…` → backend exchanges the code for tokens and writes them to `token.json`.
4. Backend redirects the browser to `http://localhost:5173/?auth=success` → frontend detects the query param, shows a toast, re-fetches `/api/auth/status`, and unmounts the Connect screen.
5. On every subsequent backend request `credentials.py` loads `token.json` and auto-refreshes if the access token is expired (using the stored refresh token — no user action needed).
6. **Disconnect:** `POST /api/auth/logout` deletes `token.json`; the frontend drops all cached queries and shows the Connect screen again.

## Architecture

```
ConnectGate (frontend)
    │
    ├─ GET /api/auth/status  → connected: bool, email: string|null
    ├─ GET /api/auth/login   → { authorization_url }  (starts consent)
    └─ GET /api/auth/callback?code=  (Google redirects here)
           │
           oauth.py: Flow.fetch_token(code)
           credentials.py: save_credentials → token.json
           redirect → frontend /?auth=success
```

`require_credentials()` in `credentials.py` is called at the top of every service builder
(`google/services.py`). If `token.json` is absent or invalid it raises `NotAuthenticatedError`,
which `main.py` maps to an HTTP 401. The frontend can add a 401-interceptor if auto-logout is desired.

### Why `prompt=consent` on every login
`google-auth-oauthlib` only returns a `refresh_token` on the first consent or when
`prompt=consent` is forced. Without it, re-authorizations would silently omit the refresh
token and break persistent auth.

## Affected Files

| Path | Role |
|---|---|
| `backend/app/auth/oauth.py` | Builds the OAuth flow, generates consent URL, exchanges code |
| `backend/app/auth/credentials.py` | Load/save/refresh token, `require_credentials()` |
| `backend/app/routers/auth.py` | `/auth/login`, `/auth/callback`, `/auth/status`, `/auth/logout` |
| `backend/app/config.py` | `GOOGLE_SCOPES`, `client_secret_path`, `token_path` |
| `backend/app/google/services.py` | `oauth2_service()` → `get_user_email()` |
| `backend/.env` / `backend/client_secret.json` | Secrets (gitignored) |
| `frontend/src/components/ConnectGate.tsx` | Gate component, handles `?auth=` redirect param |
| `frontend/src/components/Sidebar.tsx` | Shows connected email + Disconnect button |
| `frontend/src/api/client.ts` | `api.authStatus`, `api.loginUrl`, `api.logout` |
| `frontend/src/api/types.ts` | `AuthStatus` interface |
