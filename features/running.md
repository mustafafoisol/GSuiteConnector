# Running & Testing GSuiteConnector

## Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.13 | Use `py -3.13`; the `python` on PATH is 3.9 (too old) |
| Node.js 18+ | `node --version` to confirm |
| `backend/client_secret.json` | Download from Google Cloud Console (see below) |
| `backend/.env` | Copy from `backend/.env.example`, fill in `ANTHROPIC_API_KEY` |

## One-time Google Cloud setup

1. Create a project at <https://console.cloud.google.com>.
2. **APIs & Services → Library** — enable **Gmail API** and **Google Calendar API**.
3. **OAuth consent screen** — User type: **External**, publishing status: **Testing**, add your Gmail address as a test user.
4. **Credentials → Create credentials → OAuth client ID**:
   - Type: **Web application**
   - Authorized redirect URI: `http://localhost:8000/api/auth/callback`
   - Download the JSON → save as `backend/client_secret.json`

## Backend

```powershell
cd backend

# First time only
py -3.13 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env          # then set ANTHROPIC_API_KEY in .env

# Run (from backend/)
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

The backend is ready when you see `Application startup complete`.

## Frontend

```powershell
cd frontend

# First time only
npm install

# Run (from frontend/)
npm run dev
```

Open <http://localhost:5173>. The dev server proxies `/api/*` to the backend on port 8000.

## Connecting Google

1. Click **Connect Google** on the landing screen.
2. Complete the consent flow (you'll see an "unverified app" warning — expected in testing mode; click "Continue").
3. On success you land back at the app with your email shown in the sidebar.

Token is saved to `backend/token.json` (gitignored). After the first consent you won't need
to re-authorize unless you delete the file or revoke access.

## Verifying each feature manually

### Auth
- `/api/auth/status` returns `{"connected": true, "email": "..."}` after consent.
- Restart the backend — still connected (token persists). `POST /api/auth/logout` disconnects.

### Gmail
- Inbox loads your real messages.
- Search with `is:unread` or `from:someone` — results update.
- Open an email → full body visible.
- Compose → send a test email to yourself → verify it arrives.
- Reply to a thread → verify it appears in the thread in Gmail.
- Archive → email removed from Inbox label.

### Calendar
- Events for the next 7 days appear in the agenda list.
- Create an event → appears immediately.
- Click an event → edit the title or time → save → changes reflected.
- Delete an event → removed from the list.

### AI command bar
Try these inputs:
- `"Summarize my 5 most recent unread emails"` — should list summaries.
- `"Who sent me email today?"` — should name senders.
- `"Schedule a 30-minute meeting tomorrow at 2pm titled Test sync"` — confirm prompt appears → click Confirm → event appears in Calendar.
- `"Draft a reply to the last email from <someone>"` — draft created (no confirm needed).
- `"Delete the Test sync event"` — confirm prompt appears → click Cancel → nothing deleted.

## Smoke-test backend imports (no credentials needed)

```powershell
cd backend
.venv\Scripts\python.exe -c "from app.main import app; print([r.path for r in app.routes])"
```

Should print all 18 API routes with no errors.

## Frontend type-check / build

```powershell
cd frontend
npm run build    # runs tsc -b then vite build — exits 0 if no type errors
```

There is no automated test suite. The above manual steps are the verification path for each feature.

## Common issues

| Symptom | Likely cause |
|---|---|
| `FileNotFoundError: client_secret.json` | File missing from `backend/` — download from Google Cloud Console |
| `NotAuthenticatedError` (401) | `token.json` absent — visit `/api/auth/login` flow |
| `Invalid redirect URI` on Google consent page | Redirect URI in Google Cloud Console doesn't match `http://localhost:8000/api/auth/callback` exactly |
| AI command bar returns "ANTHROPIC_API_KEY is not set" | Add key to `backend/.env` and restart the backend |
| Frontend shows "Failed to load" | Backend is not running on port 8000, or CORS mismatch |
