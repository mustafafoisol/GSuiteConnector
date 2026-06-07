"""Gmail REST endpoints — thin wrappers over app.actions.gmail_actions."""
from __future__ import annotations

from fastapi import APIRouter

from app.actions import gmail_actions as ga
from app.schemas.gmail import (
    EmailDetail,
    EmailListResponse,
    MessageRef,
    ModifyLabelsRequest,
    ReplyRequest,
    SendEmailRequest,
)

router = APIRouter(prefix="/gmail", tags=["gmail"])


@router.get("/messages", response_model=EmailListResponse)
def list_messages(q: str = "", max_results: int = 25, page_token: str | None = None):
    return ga.list_messages(query=q, max_results=max_results, page_token=page_token)


@router.get("/messages/{message_id}", response_model=EmailDetail)
def get_message(message_id: str):
    return ga.get_message(message_id)


@router.post("/messages/send", response_model=MessageRef)
def send_email(req: SendEmailRequest):
    return ga.send_email(
        to=[str(x) for x in req.to],
        subject=req.subject,
        body=req.body,
        cc=[str(x) for x in req.cc],
        bcc=[str(x) for x in req.bcc],
    )


@router.post("/drafts", response_model=MessageRef)
def create_draft(req: SendEmailRequest):
    return ga.create_draft(
        to=[str(x) for x in req.to],
        subject=req.subject,
        body=req.body,
        cc=[str(x) for x in req.cc],
    )


@router.post("/messages/reply", response_model=MessageRef)
def reply(req: ReplyRequest):
    return ga.reply(
        thread_id=req.thread_id,
        body=req.body,
        to=[str(x) for x in req.to] or None,
        subject=req.subject,
    )


@router.post("/messages/{message_id}/labels", response_model=MessageRef)
def modify_labels(message_id: str, req: ModifyLabelsRequest):
    return ga.modify_labels(message_id, add=req.add, remove=req.remove)


@router.post("/messages/{message_id}/archive", response_model=MessageRef)
def archive(message_id: str):
    return ga.archive(message_id)


@router.post("/messages/{message_id}/read", response_model=MessageRef)
def mark_read(message_id: str):
    return ga.mark_read(message_id)
