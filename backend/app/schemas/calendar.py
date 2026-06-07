"""Pydantic schemas for Calendar requests/responses."""
from __future__ import annotations

from pydantic import BaseModel, Field


class Attendee(BaseModel):
    email: str
    response_status: str = ""  # needsAction/accepted/declined/tentative


class CalendarEvent(BaseModel):
    id: str
    summary: str = ""
    description: str = ""
    location: str = ""
    start: str = ""  # RFC3339 datetime or date
    end: str = ""
    all_day: bool = False
    attendees: list[Attendee] = Field(default_factory=list)
    html_link: str = ""


class EventListResponse(BaseModel):
    events: list[CalendarEvent]


class CreateEventRequest(BaseModel):
    summary: str
    start: str  # RFC3339, e.g. "2026-06-07T15:00:00-05:00", or date for all-day
    end: str
    description: str = ""
    location: str = ""
    attendees: list[str] = Field(default_factory=list)
    all_day: bool = False
    send_updates: bool = False  # email invites to attendees


class UpdateEventRequest(BaseModel):
    summary: str | None = None
    start: str | None = None
    end: str | None = None
    description: str | None = None
    location: str | None = None
    attendees: list[str] | None = None
    all_day: bool | None = None
    send_updates: bool = False


class FreeSlot(BaseModel):
    start: str
    end: str


class FreeSlotsResponse(BaseModel):
    busy: list[FreeSlot]
    free: list[FreeSlot]
