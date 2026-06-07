"""AI command bar endpoints."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.assistant import orchestrator
from app.assistant.orchestrator import CommandResult
from app.config import settings
from app.google.services import get_user_email

router = APIRouter(prefix="/assistant", tags=["assistant"])

_DISABLED_REPLY = (
    "AI command bar is disabled — set ANTHROPIC_API_KEY in backend/.env to enable it."
)


class CommandRequest(BaseModel):
    text: str


class ConfirmRequest(BaseModel):
    tool: str
    input: dict


@router.get("/status")
def status():
    return {"available": bool(settings.anthropic_api_key)}


@router.post("/command", response_model=CommandResult)
def command(req: CommandRequest):
    if not settings.anthropic_api_key:
        return CommandResult(reply=_DISABLED_REPLY)
    try:
        email = get_user_email()
    except Exception:
        email = None
    return orchestrator.run_command(req.text, user_email=email)


@router.post("/confirm")
def confirm(req: ConfirmRequest):
    if not settings.anthropic_api_key:
        return {"executed": False, "error": _DISABLED_REPLY}
    result = orchestrator.confirm_action(req.tool, req.input)
    return {"executed": True, "tool": req.tool, "result": result}
