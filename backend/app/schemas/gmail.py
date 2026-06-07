"""Pydantic schemas for Gmail requests/responses."""
from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class EmailSummary(BaseModel):
    id: str
    thread_id: str
    sender: str = ""
    to: str = ""
    subject: str = ""
    snippet: str = ""
    date: str = ""
    unread: bool = False
    labels: list[str] = Field(default_factory=list)


class EmailDetail(EmailSummary):
    body: str = ""  # plain-text body


class EmailListResponse(BaseModel):
    messages: list[EmailSummary]
    next_page_token: str | None = None


class SendEmailRequest(BaseModel):
    to: list[EmailStr]
    subject: str
    body: str
    cc: list[EmailStr] = Field(default_factory=list)
    bcc: list[EmailStr] = Field(default_factory=list)


class ReplyRequest(BaseModel):
    thread_id: str
    body: str
    to: list[EmailStr] = Field(default_factory=list)
    subject: str | None = None


class ModifyLabelsRequest(BaseModel):
    add: list[str] = Field(default_factory=list)
    remove: list[str] = Field(default_factory=list)


class MessageRef(BaseModel):
    id: str
    thread_id: str
