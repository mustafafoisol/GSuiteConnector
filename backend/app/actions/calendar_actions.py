"""Calendar action layer — shared by REST routers and the Claude tool loop."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.google.services import calendar_service
from app.schemas.calendar import (
    Attendee,
    CalendarEvent,
    CreateEventRequest,
    EventListResponse,
    FreeSlot,
    FreeSlotsResponse,
    UpdateEventRequest,
)

CAL_ID = "primary"


def _to_event(item: dict) -> CalendarEvent:
    start = item.get("start", {})
    end = item.get("end", {})
    all_day = "date" in start
    return CalendarEvent(
        id=item["id"],
        summary=item.get("summary", ""),
        description=item.get("description", ""),
        location=item.get("location", ""),
        start=start.get("dateTime") or start.get("date", ""),
        end=end.get("dateTime") or end.get("date", ""),
        all_day=all_day,
        attendees=[
            Attendee(
                email=a.get("email", ""),
                response_status=a.get("responseStatus", ""),
            )
            for a in item.get("attendees", [])
        ],
        html_link=item.get("htmlLink", ""),
    )


def _time_bounds(start: str, end: str, all_day: bool) -> tuple[dict, dict]:
    key = "date" if all_day else "dateTime"
    s = {key: start}
    e = {key: end}
    if not all_day:
        # Let Google interpret offset in the string; include tz only if absent.
        pass
    return s, e


def list_events(
    time_min: str | None = None,
    time_max: str | None = None,
    max_results: int = 50,
    query: str | None = None,
) -> EventListResponse:
    """List events in [time_min, time_max] (RFC3339). Defaults to next 7 days."""
    svc = calendar_service()
    now = datetime.now(timezone.utc)
    tmin = time_min or now.isoformat()
    tmax = time_max or (now + timedelta(days=7)).isoformat()
    result = (
        svc.events()
        .list(
            calendarId=CAL_ID,
            timeMin=tmin,
            timeMax=tmax,
            singleEvents=True,
            orderBy="startTime",
            maxResults=max_results,
            q=query,
        )
        .execute()
    )
    return EventListResponse(
        events=[_to_event(i) for i in result.get("items", [])]
    )


def get_event(event_id: str) -> CalendarEvent:
    svc = calendar_service()
    item = svc.events().get(calendarId=CAL_ID, eventId=event_id).execute()
    return _to_event(item)


def create_event(req: CreateEventRequest) -> CalendarEvent:
    svc = calendar_service()
    start, end = _time_bounds(req.start, req.end, req.all_day)
    body: dict = {
        "summary": req.summary,
        "description": req.description,
        "location": req.location,
        "start": start,
        "end": end,
    }
    if req.attendees:
        body["attendees"] = [{"email": e} for e in req.attendees]
    created = (
        svc.events()
        .insert(
            calendarId=CAL_ID,
            body=body,
            sendUpdates="all" if req.send_updates else "none",
        )
        .execute()
    )
    return _to_event(created)


def update_event(event_id: str, req: UpdateEventRequest) -> CalendarEvent:
    svc = calendar_service()
    existing = svc.events().get(calendarId=CAL_ID, eventId=event_id).execute()
    all_day = req.all_day if req.all_day is not None else ("date" in existing.get("start", {}))

    if req.summary is not None:
        existing["summary"] = req.summary
    if req.description is not None:
        existing["description"] = req.description
    if req.location is not None:
        existing["location"] = req.location
    if req.start is not None:
        existing["start"], _ = _time_bounds(req.start, req.start, all_day)
    if req.end is not None:
        _, existing["end"] = _time_bounds(req.end, req.end, all_day)
    if req.attendees is not None:
        existing["attendees"] = [{"email": e} for e in req.attendees]

    updated = (
        svc.events()
        .update(
            calendarId=CAL_ID,
            eventId=event_id,
            body=existing,
            sendUpdates="all" if req.send_updates else "none",
        )
        .execute()
    )
    return _to_event(updated)


def delete_event(event_id: str, send_updates: bool = False) -> None:
    svc = calendar_service()
    svc.events().delete(
        calendarId=CAL_ID,
        eventId=event_id,
        sendUpdates="all" if send_updates else "none",
    ).execute()


def find_free_slots(
    time_min: str,
    time_max: str,
    slot_minutes: int = 30,
) -> FreeSlotsResponse:
    """Return busy blocks and free gaps within [time_min, time_max]."""
    svc = calendar_service()
    fb = (
        svc.freebusy()
        .query(
            body={
                "timeMin": time_min,
                "timeMax": time_max,
                "items": [{"id": CAL_ID}],
            }
        )
        .execute()
    )
    busy_raw = fb["calendars"][CAL_ID].get("busy", [])
    busy = [FreeSlot(start=b["start"], end=b["end"]) for b in busy_raw]

    # Compute free gaps between busy blocks.
    free: list[FreeSlot] = []
    cursor = datetime.fromisoformat(time_min)
    end_bound = datetime.fromisoformat(time_max)
    min_delta = timedelta(minutes=slot_minutes)
    for b in busy:
        b_start = datetime.fromisoformat(b.start)
        if b_start - cursor >= min_delta:
            free.append(FreeSlot(start=cursor.isoformat(), end=b_start.isoformat()))
        b_end = datetime.fromisoformat(b.end)
        if b_end > cursor:
            cursor = b_end
    if end_bound - cursor >= min_delta:
        free.append(FreeSlot(start=cursor.isoformat(), end=end_bound.isoformat()))

    return FreeSlotsResponse(busy=busy, free=free)
