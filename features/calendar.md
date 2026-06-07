# Feature: Google Calendar

Covers viewing upcoming events, creating, editing, and deleting events, and finding free time.

## Basic Flow

### Viewing events (agenda list)
1. `CalendarView` mounts and fetches `GET /api/calendar/events?time_min=…&time_max=…`.
2. The user can switch between **Today / Next 7 days / Next 30 days** via a dropdown;
   changing it updates `time_max` and re-fetches.
3. Events are grouped by day (derived from each event's `start` datetime) and rendered
   as an agenda list (no grid). All-day events show "All day" instead of a time range.

### Creating an event
1. Click **+ New event** → `EventDialog` opens with pre-filled start/end (now + 1 hr / +1.5 hr).
2. `datetime-local` inputs are converted to RFC3339-with-offset by `toRFC3339()` before posting.
3. `POST /api/calendar/events` → `calendar_actions.create_event()` → `events.insert`.
4. On success, TanStack Query key `["events"]` is invalidated → agenda refreshes.

### Editing an event
1. Click any event row → `EventDialog` opens pre-filled with that event's data.
2. `toLocalInput()` converts the stored RFC3339 string back to a `datetime-local` value.
3. `PATCH /api/calendar/events/:id` → `calendar_actions.update_event()` fetches the existing
   event from Google (to avoid overwriting unedited fields), patches changed fields, and calls
   `events.update`.

### Deleting an event
- Delete button inside `EventDialog` → `DELETE /api/calendar/events/:id`.
- `send_updates=false` by default (no cancellation emails to attendees).

### Free/busy query (used by AI command bar)
- `GET /api/calendar/free?time_min=…&time_max=…&slot_minutes=30`
- `calendar_actions.find_free_slots()` calls the `freebusy.query` API, then computes
  contiguous free gaps by walking the busy blocks chronologically.

## Architecture

```
CalendarView + EventDialog (React)
        │
        api/client.ts
        │
        /api/calendar/events  CRUD  (routers/calendar.py — thin wrappers)
        /api/calendar/free           (routers/calendar.py)
        │
        actions/calendar_actions.py  ← all Calendar logic
        │
        google/services.py → calendar_service() → Calendar REST v3
```

### Datetime conventions
All datetimes sent to Google must be RFC3339 **with an explicit timezone offset**
(e.g. `2026-06-07T15:00:00-05:00`). Two conversion helpers exist:
- Frontend: `toRFC3339(localInputStr)` in `EventDialog.tsx` — reads the browser's local offset at call time.
- Backend system prompt: the orchestrator injects the current local offset so Claude generates
  correct timestamps for the AI command bar path.

For all-day events, `start`/`end` use the `date` key (`YYYY-MM-DD`) instead of `dateTime`.
`_time_bounds()` in `calendar_actions.py` selects the correct key based on `all_day`.

### `events.update` vs `events.patch`
The backend uses `events.update` (full replacement), not `events.patch`, because it first
fetches the current resource and merges only the fields the caller provided. This avoids
the need to send the entire event body from the frontend.

## Affected Files

| Path | Role |
|---|---|
| `backend/app/actions/calendar_actions.py` | All Calendar operations |
| `backend/app/routers/calendar.py` | REST endpoints |
| `backend/app/google/services.py` | `calendar_service()` builder |
| `backend/app/schemas/calendar.py` | `CalendarEvent`, `CreateEventRequest`, `UpdateEventRequest`, `FreeSlotsResponse` |
| `frontend/src/views/CalendarView.tsx` | Agenda list, day grouping, range selector |
| `frontend/src/views/EventDialog.tsx` | Create/edit/delete modal, RFC3339 conversion helpers |
| `frontend/src/api/client.ts` | `api.listEvents`, `api.createEvent`, `api.updateEvent`, `api.deleteEvent` |
| `frontend/src/api/types.ts` | `CalendarEvent`, `CreateEventRequest`, `Attendee` |
