"""Expose the shared action layer as Claude tools.

Read-only tools run immediately inside the tool loop. Tools in CONFIRM_TOOLS are
outbound/destructive — the orchestrator never runs them automatically; it returns
a pending action for the user to confirm in the UI, which then hits /assistant/confirm.
"""
from __future__ import annotations

from typing import Any, Callable

from app.actions import calendar_actions as ca
from app.actions import gmail_actions as ga
from app.schemas.calendar import CreateEventRequest, UpdateEventRequest


# ---------- dispatch wrappers (uniform: kwargs in, JSON-able out) ----------

def _list_messages(query: str = "", max_results: int = 15) -> Any:
    return ga.list_messages(query=query, max_results=max_results).model_dump()


def _get_message(message_id: str) -> Any:
    return ga.get_message(message_id).model_dump()


def _send_email(to: list[str], subject: str, body: str, cc: list[str] | None = None) -> Any:
    return ga.send_email(to=to, subject=subject, body=body, cc=cc).model_dump()


def _create_draft(to: list[str], subject: str, body: str, cc: list[str] | None = None) -> Any:
    return ga.create_draft(to=to, subject=subject, body=body, cc=cc).model_dump()


def _reply(thread_id: str, body: str, to: list[str] | None = None) -> Any:
    return ga.reply(thread_id=thread_id, body=body, to=to).model_dump()


def _archive(message_id: str) -> Any:
    return ga.archive(message_id).model_dump()


def _list_events(
    time_min: str | None = None,
    time_max: str | None = None,
    query: str | None = None,
    max_results: int = 25,
) -> Any:
    return ca.list_events(
        time_min=time_min, time_max=time_max, query=query, max_results=max_results
    ).model_dump()


def _create_event(
    summary: str,
    start: str,
    end: str,
    description: str = "",
    location: str = "",
    attendees: list[str] | None = None,
    all_day: bool = False,
    send_updates: bool = False,
) -> Any:
    return ca.create_event(
        CreateEventRequest(
            summary=summary,
            start=start,
            end=end,
            description=description,
            location=location,
            attendees=attendees or [],
            all_day=all_day,
            send_updates=send_updates,
        )
    ).model_dump()


def _update_event(event_id: str, **kwargs: Any) -> Any:
    return ca.update_event(event_id, UpdateEventRequest(**kwargs)).model_dump()


def _delete_event(event_id: str, send_updates: bool = False) -> Any:
    ca.delete_event(event_id, send_updates=send_updates)
    return {"deleted": True, "id": event_id}


def _find_free(time_min: str, time_max: str, slot_minutes: int = 30) -> Any:
    return ca.find_free_slots(time_min, time_max, slot_minutes=slot_minutes).model_dump()


TOOL_FUNCTIONS: dict[str, Callable[..., Any]] = {
    "list_messages": _list_messages,
    "get_message": _get_message,
    "send_email": _send_email,
    "create_draft": _create_draft,
    "reply": _reply,
    "archive": _archive,
    "list_events": _list_events,
    "create_event": _create_event,
    "update_event": _update_event,
    "delete_event": _delete_event,
    "find_free_slots": _find_free,
}

# Outbound/destructive — require explicit user confirmation before running.
CONFIRM_TOOLS: set[str] = {
    "send_email",
    "reply",
    "create_event",
    "update_event",
    "delete_event",
}


TOOLS: list[dict] = [
    {
        "name": "list_messages",
        "description": "List/search Gmail messages. `query` uses Gmail search syntax "
        "(e.g. 'is:unread', 'from:alice newer_than:7d').",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Gmail search query."},
                "max_results": {"type": "integer", "default": 15},
            },
        },
    },
    {
        "name": "get_message",
        "description": "Get the full plain-text body and headers of one email by id.",
        "input_schema": {
            "type": "object",
            "properties": {"message_id": {"type": "string"}},
            "required": ["message_id"],
        },
    },
    {
        "name": "send_email",
        "description": "Send a new email. Requires user confirmation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "to": {"type": "array", "items": {"type": "string"}},
                "subject": {"type": "string"},
                "body": {"type": "string"},
                "cc": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["to", "subject", "body"],
        },
    },
    {
        "name": "create_draft",
        "description": "Create a Gmail draft (not sent). Safe; does not require confirmation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "to": {"type": "array", "items": {"type": "string"}},
                "subject": {"type": "string"},
                "body": {"type": "string"},
                "cc": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["to", "subject", "body"],
        },
    },
    {
        "name": "reply",
        "description": "Reply within an existing email thread. Requires user confirmation. "
        "Recipient/subject are auto-resolved from the thread if omitted.",
        "input_schema": {
            "type": "object",
            "properties": {
                "thread_id": {"type": "string"},
                "body": {"type": "string"},
                "to": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["thread_id", "body"],
        },
    },
    {
        "name": "archive",
        "description": "Archive an email (remove from inbox). Safe.",
        "input_schema": {
            "type": "object",
            "properties": {"message_id": {"type": "string"}},
            "required": ["message_id"],
        },
    },
    {
        "name": "list_events",
        "description": "List/search calendar events between RFC3339 timestamps "
        "(e.g. 2026-06-07T00:00:00-05:00). Defaults to the next 7 days.",
        "input_schema": {
            "type": "object",
            "properties": {
                "time_min": {"type": "string"},
                "time_max": {"type": "string"},
                "query": {"type": "string"},
                "max_results": {"type": "integer", "default": 25},
            },
        },
    },
    {
        "name": "create_event",
        "description": "Create a calendar event. Requires user confirmation. Use RFC3339 "
        "datetimes WITH timezone offset for `start`/`end`, or YYYY-MM-DD with all_day=true.",
        "input_schema": {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "start": {"type": "string"},
                "end": {"type": "string"},
                "description": {"type": "string"},
                "location": {"type": "string"},
                "attendees": {"type": "array", "items": {"type": "string"}},
                "all_day": {"type": "boolean", "default": False},
            },
            "required": ["summary", "start", "end"],
        },
    },
    {
        "name": "update_event",
        "description": "Update fields of an existing event. Requires user confirmation. "
        "Only pass fields to change.",
        "input_schema": {
            "type": "object",
            "properties": {
                "event_id": {"type": "string"},
                "summary": {"type": "string"},
                "start": {"type": "string"},
                "end": {"type": "string"},
                "description": {"type": "string"},
                "location": {"type": "string"},
                "attendees": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["event_id"],
        },
    },
    {
        "name": "delete_event",
        "description": "Delete a calendar event by id. Requires user confirmation.",
        "input_schema": {
            "type": "object",
            "properties": {"event_id": {"type": "string"}},
            "required": ["event_id"],
        },
    },
    {
        "name": "find_free_slots",
        "description": "Find free/busy time within an RFC3339 window. Useful before scheduling.",
        "input_schema": {
            "type": "object",
            "properties": {
                "time_min": {"type": "string"},
                "time_max": {"type": "string"},
                "slot_minutes": {"type": "integer", "default": 30},
            },
            "required": ["time_min", "time_max"],
        },
    },
]


def human_summary(tool_name: str, tool_input: dict) -> str:
    """Short human-readable description of a pending action for the confirm UI."""
    if tool_name == "send_email":
        return f"Send email to {', '.join(tool_input.get('to', []))} — “{tool_input.get('subject', '')}”"
    if tool_name == "reply":
        return "Send reply in thread"
    if tool_name == "create_event":
        return f"Create event “{tool_input.get('summary', '')}” at {tool_input.get('start', '')}"
    if tool_name == "update_event":
        return f"Update event {tool_input.get('event_id', '')}"
    if tool_name == "delete_event":
        return f"Delete event {tool_input.get('event_id', '')}"
    return tool_name
