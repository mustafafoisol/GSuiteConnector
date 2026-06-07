"""Claude tool-use loop for the AI command bar."""
from __future__ import annotations

import json
from datetime import datetime

from anthropic import Anthropic
from pydantic import BaseModel

from app.assistant import tools as T
from app.config import settings

MAX_TURNS = 8


class PendingAction(BaseModel):
    tool: str
    input: dict
    summary: str


class CommandResult(BaseModel):
    reply: str
    actions_taken: list[str] = []
    pending: PendingAction | None = None


def _system_prompt(user_email: str | None) -> str:
    now = datetime.now().astimezone()
    return (
        "You are a helpful assistant embedded in a personal Gmail + Google Calendar app. "
        f"The user's email is {user_email or 'unknown'}. "
        f"The current local date/time is {now.isoformat()} "
        f"(timezone offset {now.strftime('%z')}). "
        "Use the provided tools to read and manage the user's email and calendar. "
        "When creating or updating events, always include an explicit timezone offset in "
        "RFC3339 datetimes, using the user's local offset above unless told otherwise. "
        "Outbound or destructive actions (sending email, replying, creating/updating/deleting "
        "events) will be confirmed by the user through the UI — propose them via the tools and "
        "do not ask for confirmation in text. Be concise."
    )


def _client() -> Anthropic:
    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set in backend/.env")
    return Anthropic(api_key=settings.anthropic_api_key)


def run_command(text: str, user_email: str | None = None) -> CommandResult:
    client = _client()
    messages: list[dict] = [{"role": "user", "content": text}]
    actions_taken: list[str] = []
    final_text_parts: list[str] = []

    for _ in range(MAX_TURNS):
        resp = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=2048,
            system=_system_prompt(user_email),
            tools=T.TOOLS,
            messages=messages,
        )

        text_this_turn = "".join(
            b.text for b in resp.content if b.type == "text"
        ).strip()
        if text_this_turn:
            final_text_parts.append(text_this_turn)

        if resp.stop_reason != "tool_use":
            return CommandResult(
                reply="\n\n".join(final_text_parts).strip(),
                actions_taken=actions_taken,
            )

        tool_uses = [b for b in resp.content if b.type == "tool_use"]

        # If any requested tool needs confirmation, stop and surface it.
        for block in tool_uses:
            if block.name in T.CONFIRM_TOOLS:
                return CommandResult(
                    reply="\n\n".join(final_text_parts).strip(),
                    actions_taken=actions_taken,
                    pending=PendingAction(
                        tool=block.name,
                        input=dict(block.input),
                        summary=T.human_summary(block.name, dict(block.input)),
                    ),
                )

        # Otherwise execute all read-only tools and continue the loop.
        messages.append({"role": "assistant", "content": resp.content})
        tool_results = []
        for block in tool_uses:
            try:
                result = T.TOOL_FUNCTIONS[block.name](**dict(block.input))
                content = json.dumps(result, default=str)
                actions_taken.append(block.name)
            except Exception as e:  # surface tool errors back to Claude
                content = json.dumps({"error": str(e)})
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": content,
                }
            )
        messages.append({"role": "user", "content": tool_results})

    return CommandResult(
        reply="\n\n".join(final_text_parts).strip()
        or "Stopped after too many steps.",
        actions_taken=actions_taken,
    )


def confirm_action(tool: str, tool_input: dict) -> dict:
    """Execute a previously-proposed confirmed action."""
    if tool not in T.CONFIRM_TOOLS:
        raise ValueError(f"'{tool}' is not a confirmable action")
    return T.TOOL_FUNCTIONS[tool](**tool_input)
