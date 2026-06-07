# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A **local, single-user** webapp connecting the owner's Gmail + Google Calendar, with a
**hybrid** interface: classic REST-driven UI views (Inbox/Compose/Calendar) **plus** a
Claude-powered AI command bar. The Google OAuth app stays in **testing mode** — no
verification flow. Backend = FastAPI (`backend/`), frontend = React/Vite/TS (`frontend/`).

## Commands

Use the `py -3.13` launcher — the `python` on PATH is 3.9 and too old.

```powershell
# Backend (from backend/)
py -3.13 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000

# Frontend (from frontend/)
npm install
npm run dev      # Vite on :5173, proxies /api -> :8000
npm run build    # tsc -b && vite build  — use this to type-check
```

There is no test suite or linter configured. `npm run build` is the type-check gate for
the frontend. To smoke-test the backend without credentials:
`.venv\Scripts\python.exe -c "from app.main import app"`.

### Running live requires two secrets (gitignored, not in repo)
- `backend/client_secret.json` — Google OAuth **Web** client; authorized redirect URI must
  be exactly `http://localhost:8000/api/auth/callback`.
- `backend/.env` (copy from `.env.example`) with `ANTHROPIC_API_KEY` for the command bar.

## Architecture — the one idea that matters

**One shared action layer, two consumers.** Every Google operation is written exactly once
in `backend/app/actions/{gmail_actions,calendar_actions}.py`. Two independent callers use it:

1. **REST routers** (`backend/app/routers/`) — thin wrappers, drive the traditional UI.
2. **Claude tool loop** (`backend/app/assistant/`) — drives the AI command bar.

When adding a Gmail/Calendar capability, add the function to the action layer first, then
expose it through *both* a router endpoint and (if the assistant should use it) a tool in
`assistant/tools.py`. Never put Google API calls directly in a router or the orchestrator.

```
React UI ─┬─► /api/gmail, /api/calendar (routers/) ─┐
          └─► /api/assistant (assistant/) ──────────┤
                                                     ▼
                          actions/  ── google/services.py ──► Gmail v1 / Calendar v3
```

### Assistant tool loop & the confirmation guard
`assistant/orchestrator.py` runs Claude with the tools from `assistant/tools.py`. Tools
listed in `tools.CONFIRM_TOOLS` (send/reply/create/update/delete) are **outbound/destructive
and never auto-executed**. When Claude requests one, the orchestrator stops the loop and
returns a `PendingAction`; the frontend `CommandBar` shows a Confirm button that calls
`POST /api/assistant/confirm`, which runs the action directly (bypassing Claude). Read-only
tools execute inline within the loop. Preserve this guard when touching the assistant.

### Auth & credentials
`auth/oauth.py` runs the consent flow; `auth/credentials.py` loads/refreshes the cached
`token.json`. `google/services.py` builds authenticated clients via `require_credentials()`,
which raises `NotAuthenticatedError` (mapped to HTTP 401 in `main.py`) when no token exists.
Everything is single-user — there are no sessions or per-user state.

### Schemas are shared contracts
Pydantic models in `backend/app/schemas/` are reused by the action layer, the routers
(`response_model=`), and mirrored by hand in `frontend/src/api/types.ts`. Changing a
backend schema means updating `types.ts` to match.

### Frontend conventions
- Server state goes through TanStack Query. Query keys `["messages"]` and `["events"]` are
  invalidated after mutations and after the command bar acts — reuse these exact keys so
  views refresh consistently.
- All HTTP goes through `frontend/src/api/client.ts` (the typed `api` object). Don't call
  axios/fetch directly from components.
- Plain CSS in `src/styles.css` (no Tailwind). The calendar is an agenda list, not a grid.

## Conventions
- Datetimes to Google must be RFC3339 **with an explicit timezone offset**. The frontend
  converts `datetime-local` inputs in `EventDialog.tsx` (`toRFC3339`); the assistant is told
  the local offset in the orchestrator's system prompt.
- Gmail search uses native Gmail query syntax (e.g. `is:unread`, `from:x newer_than:7d`),
  passed straight through to the API.
