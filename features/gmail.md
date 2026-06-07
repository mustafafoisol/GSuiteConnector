# Feature: Gmail

Covers reading, searching, composing, sending, drafting, replying, and archiving email.

## Basic Flow

### Inbox
1. `Inbox` view mounts → TanStack Query fetches `GET /api/gmail/messages?q=&max_results=30`.
2. The backend calls `gmail_actions.list_messages()` which issues a Gmail API `messages.list`,
   then fetches each message's metadata (From/To/Subject/Date headers only — lightweight).
3. Clicking a row navigates to `/inbox/:id` → `EmailDetail` fetches the full message
   (`format=full`) and extracts a plain-text body from the MIME tree.

### Search & filters
- The search bar submits a Gmail query string directly to the API (native syntax: `from:alice`, `is:unread`, `newer_than:7d`, etc.).
- The **Unread only** checkbox appends `is:unread` to the active query.

### Compose / Send
1. Compose view collects To/Cc/Subject/Body.
2. **Send:** `POST /api/gmail/messages/send` → `gmail_actions.send_email()` builds a MIME
   `EmailMessage`, base64url-encodes it, and calls `messages.send`.
3. **Save draft:** `POST /api/gmail/drafts` → same MIME build, calls `drafts.create`.

### Reply
1. `EmailDetail` shows a Reply textarea when the Reply button is clicked.
2. `POST /api/gmail/messages/reply` → `gmail_actions.reply()`:
   - Fetches the thread to resolve the last message's From/Reply-To headers (auto-fills recipient and `Re:` subject if caller omits them).
   - Adds `In-Reply-To` / `References` MIME headers so it threads correctly in Gmail.
   - Posts to `messages.send` with `threadId` to keep it in the thread.

### Archive / Mark read
- `POST /api/gmail/messages/:id/archive` → removes the `INBOX` label.
- `POST /api/gmail/messages/:id/read` → removes the `UNREAD` label.
- Both call `messages.modify` with `addLabelIds` / `removeLabelIds`.

## Architecture

```
Inbox / EmailDetail / Compose (React views)
        │
        api/client.ts (typed axios wrappers)
        │
        GET/POST /api/gmail/*   (routers/gmail.py — thin wrappers)
        │
        actions/gmail_actions.py  ← all Gmail logic lives here
        │
        google/services.py → gmail_service() → Gmail REST v1
```

### MIME handling
`gmail_actions._build_mime()` uses the stdlib `email.EmailMessage` and `base64.urlsafe_b64encode`.
`_extract_plain_body()` walks the MIME payload tree recursively: it prefers `text/plain` parts,
falls back through nested multipart, and finally falls back to `text/html` if that's all that exists.

### Unread state
The `unread` flag on `EmailSummary` is derived from the presence of `"UNREAD"` in the message's
`labelIds` array — no separate API call needed.

## Affected Files

| Path | Role |
|---|---|
| `backend/app/actions/gmail_actions.py` | All Gmail operations (the source of truth) |
| `backend/app/routers/gmail.py` | REST endpoints — delegates to `gmail_actions` |
| `backend/app/google/services.py` | `gmail_service()` builder |
| `backend/app/schemas/gmail.py` | `EmailSummary`, `EmailDetail`, `SendEmailRequest`, etc. |
| `frontend/src/views/Inbox.tsx` | Message list, search bar, unread filter |
| `frontend/src/views/EmailDetail.tsx` | Full message, inline reply, archive |
| `frontend/src/views/Compose.tsx` | Compose form, send/draft |
| `frontend/src/api/client.ts` | `api.listMessages`, `api.getMessage`, `api.sendEmail`, etc. |
| `frontend/src/api/types.ts` | `EmailSummary`, `EmailDetail`, `SendEmailRequest`, `ReplyRequest` |
