"""AI command bar endpoints."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.assistant import orchestrator
from app.assistant.orchestrator import CommandResult
from app.google.services import get_user_email

router = APIRouter(prefix="/assistant", tags=["assistant"])


class CommandRequest(BaseModel):
    text: str


class ConfirmRequest(BaseModel):
    tool: str
    input: dict


@router.post("/command", response_model=CommandResult)
def command(req: CommandRequest):
    try:
        email = get_user_email()
    except Exception:
        email = None
    return orchestrator.run_command(req.text, user_email=email)


@router.post("/confirm")
def confirm(req: ConfirmRequest):
    result = orchestrator.confirm_action(req.tool, req.input)
    return {"executed": True, "tool": req.tool, "result": result}
