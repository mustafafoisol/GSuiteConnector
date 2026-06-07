# GSuiteConnector

A personal, local webapp that connects to **your** Gmail + Google Calendar with a
**hybrid** interface: classic Inbox/Compose/Calendar views **plus** an AI command
bar (powered by Claude) where you type natural language and it performs actions.

- **Backend:** Python + FastAPI (`backend/`)
- **Frontend:** React + Vite + TypeScript (`frontend/`)
- **Single user, local only.** Your Google app stays in *testing* mode — no app
  verification required.

---

## Architecture

One **shared action layer** (`backend/app/actions/`) holds every Google operation
exactly once. Two consumers call it:

- **REST routers** (`backend/app/routers/`) drive the traditional UI.
- **Claude tool loop** (`backend/app/assistant/`) drives the AI command bar.

```
React UI ─┬─► /api/gmail, /api/calendar ─┐
          └─► /api/assistant (Claude) ───┤
                                         ▼
                          actions/ (gmail_actions, calendar_actions)
                                         ▼
                          Google Gmail v1 / Calendar v3 APIs
```

Outbound/destructive AI actions (send email, reply, create/update/delete event)
are **never executed automatically** — Claude proposes them and you confirm in the
UI before they run.

---

## 1. Google Cloud setup (one time)

1. Go to <https://console.cloud.google.com> → create a project.
2. **APIs & Services → Library** → enable **Gmail API** and **Google Calendar API**.
3. **APIs & Services → OAuth consent screen**:
   - User type: **External**, publishing status: **Testing**.
   - Add your own Google account under **Test users**.
4. **APIs & Services → Credentials → Create credentials → OAuth client ID**:
   - Application type: **Web application**.
   - **Authorized redirect URIs:** add `http://localhost:8000/api/auth/callback`.
   - Download the JSON and save it as `backend/client_secret.json`.

## 2. Backend setup

```powershell
cd backend
py -3.13 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env      # then edit .env
```

Edit `backend/.env`:
- `ANTHROPIC_API_KEY` — your Claude API key (for the command bar).
- `ANTHROPIC_MODEL` — defaults to `claude-sonnet-4-6` (use `claude-opus-4-8` for
  the most capable model).

Run it:
```powershell
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

## 3. Frontend setup

```powershell
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173>.

## 4. Connect & use

1. Click **Connect Google**, complete consent (you'll see an "unverified app"
   warning — expected in testing mode; continue).
2. **Inbox:** search (Gmail syntax), open, reply, archive.
3. **Compose:** send or save a draft.
4. **Calendar:** view upcoming, create/edit/delete events.
5. **Command bar** (bottom): try
   - "Summarize my 5 most recent unread emails"
   - "Draft a reply to the latest email from <someone>"
   - "Schedule a 30-minute meeting tomorrow at 3pm titled Sync" → **Confirm**.

---

## Privacy

`client_secret.json`, `token.json`, and `.env` are gitignored and never leave your
machine. Email/calendar content is sent to the Claude API **only** when you use the
command bar; the traditional UI talks to Google directly.

## OAuth scopes

`gmail.readonly`, `gmail.send`, `gmail.compose`, `gmail.modify`, `calendar`,
plus `openid`/`userinfo.email` to show which account is connected.

## Out of scope (v1)

Multi-user/hosted deploy + Google verification, persistent chat history, Drive/Docs,
push notifications, calendar grid view (agenda list is provided).
