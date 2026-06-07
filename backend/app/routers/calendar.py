"""Calendar REST endpoints — thin wrappers over app.actions.calendar_actions."""
from __future__ import annotations

from fastapi import APIRouter

from app.actions import calendar_actions as ca
from app.schemas.calendar import (
    CalendarEvent,
    CreateEventRequest,
    EventListResponse,
    FreeSlotsResponse,
    UpdateEventRequest,
)

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/events", response_model=EventListResponse)
def list_events(
    time_min: str | None = None,
    time_max: str | None = None,
    q: str | None = None,
    max_results: int = 50,
):
    return ca.list_events(
        time_min=time_min, time_max=time_max, query=q, max_results=max_results
    )


@router.get("/events/{event_id}", response_model=CalendarEvent)
def get_event(event_id: str):
    return ca.get_event(event_id)


@router.post("/events", response_model=CalendarEvent)
def create_event(req: CreateEventRequest):
    return ca.create_event(req)


@router.patch("/events/{event_id}", response_model=CalendarEvent)
def update_event(event_id: str, req: UpdateEventRequest):
    return ca.update_event(event_id, req)


@router.delete("/events/{event_id}")
def delete_event(event_id: str, send_updates: bool = False):
    ca.delete_event(event_id, send_updates=send_updates)
    return {"deleted": True, "id": event_id}


@router.get("/free", response_model=FreeSlotsResponse)
def find_free(time_min: str, time_max: str, slot_minutes: int = 30):
    return ca.find_free_slots(time_min, time_max, slot_minutes=slot_minutes)
