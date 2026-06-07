"""Gmail action layer — shared by REST routers and the Claude tool loop.

Every Gmail operation lives here exactly once.
"""
from __future__ import annotations

import base64
from email.message import EmailMessage

from app.google.services import gmail_service
from app.schemas.gmail import (
    EmailDetail,
    EmailListResponse,
    EmailSummary,
    MessageRef,
)


# ---------- helpers ----------

def _header(headers: list[dict], name: str) -> str:
    name = name.lower()
    for h in headers:
        if h.get("name", "").lower() == name:
            return h.get("value", "")
    return ""


def _decode_part(data: str) -> str:
    return base64.urlsafe_b64decode(data.encode("utf-8")).decode("utf-8", "replace")


def _extract_plain_body(payload: dict) -> str:
    """Walk the MIME tree and return the best plain-text body."""
    mime = payload.get("mimeType", "")
    body = payload.get("body", {})
    if mime == "text/plain" and body.get("data"):
        return _decode_part(body["data"])

    parts = payload.get("parts", [])
    # Prefer text/plain, fall back to stripped text/html.
    for part in parts:
        if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
            return _decode_part(part["body"]["data"])
    for part in parts:
        text = _extract_plain_body(part)
        if text:
            return text
    if mime == "text/html" and body.get("data"):
        return _decode_part(body["data"])
    return ""


def _to_summary(msg: dict) -> EmailSummary:
    headers = msg.get("payload", {}).get("headers", [])
    labels = msg.get("labelIds", [])
    return EmailSummary(
        id=msg["id"],
        thread_id=msg.get("threadId", ""),
        sender=_header(headers, "From"),
        to=_header(headers, "To"),
        subject=_header(headers, "Subject"),
        snippet=msg.get("snippet", ""),
        date=_header(headers, "Date"),
        unread="UNREAD" in labels,
        labels=labels,
    )


def _build_mime(
    to: list[str],
    subject: str,
    body: str,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    headers: dict[str, str] | None = None,
) -> str:
    msg = EmailMessage()
    msg["To"] = ", ".join(to)
    if cc:
        msg["Cc"] = ", ".join(cc)
    if bcc:
        msg["Bcc"] = ", ".join(bcc)
    msg["Subject"] = subject
    for k, v in (headers or {}).items():
        msg[k] = v
    msg.set_content(body)
    return base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")


# ---------- read / search ----------

def list_messages(
    query: str = "",
    max_results: int = 25,
    page_token: str | None = None,
) -> EmailListResponse:
    """List/search messages. `query` uses Gmail search syntax (e.g. 'is:unread')."""
    svc = gmail_service()
    listing = (
        svc.users()
        .messages()
        .list(userId="me", q=query, maxResults=max_results, pageToken=page_token)
        .execute()
    )
    summaries: list[EmailSummary] = []
    for ref in listing.get("messages", []):
        msg = (
            svc.users()
            .messages()
            .get(
                userId="me",
                id=ref["id"],
                format="metadata",
                metadataHeaders=["From", "To", "Subject", "Date"],
            )
            .execute()
        )
        summaries.append(_to_summary(msg))
    return EmailListResponse(
        messages=summaries, next_page_token=listing.get("nextPageToken")
    )


def get_message(message_id: str) -> EmailDetail:
    svc = gmail_service()
    msg = (
        svc.users().messages().get(userId="me", id=message_id, format="full").execute()
    )
    summary = _to_summary(msg)
    return EmailDetail(
        **summary.model_dump(),
        body=_extract_plain_body(msg.get("payload", {})),
    )


# ---------- compose / send ----------

def send_email(
    to: list[str],
    subject: str,
    body: str,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
) -> MessageRef:
    svc = gmail_service()
    raw = _build_mime(to, subject, body, cc, bcc)
    sent = svc.users().messages().send(userId="me", body={"raw": raw}).execute()
    return MessageRef(id=sent["id"], thread_id=sent.get("threadId", ""))


def create_draft(
    to: list[str],
    subject: str,
    body: str,
    cc: list[str] | None = None,
) -> MessageRef:
    svc = gmail_service()
    raw = _build_mime(to, subject, body, cc)
    draft = (
        svc.users()
        .drafts()
        .create(userId="me", body={"message": {"raw": raw}})
        .execute()
    )
    m = draft.get("message", {})
    return MessageRef(id=draft["id"], thread_id=m.get("threadId", ""))


def reply(
    thread_id: str,
    body: str,
    to: list[str] | None = None,
    subject: str | None = None,
) -> MessageRef:
    """Reply within an existing thread. Resolves recipient/subject if omitted."""
    svc = gmail_service()
    thread = svc.users().threads().get(userId="me", id=thread_id, format="metadata").execute()
    msgs = thread.get("messages", [])
    last = msgs[-1] if msgs else {}
    headers = last.get("payload", {}).get("headers", [])

    if not to:
        reply_to = _header(headers, "Reply-To") or _header(headers, "From")
        to = [reply_to] if reply_to else []
    if subject is None:
        subj = _header(headers, "Subject")
        subject = subj if subj.lower().startswith("re:") else f"Re: {subj}"

    msg_id_hdr = _header(headers, "Message-ID")
    extra = {}
    if msg_id_hdr:
        extra = {"In-Reply-To": msg_id_hdr, "References": msg_id_hdr}

    raw = _build_mime(to, subject, body, headers=extra)
    sent = (
        svc.users()
        .messages()
        .send(userId="me", body={"raw": raw, "threadId": thread_id})
        .execute()
    )
    return MessageRef(id=sent["id"], thread_id=sent.get("threadId", ""))


# ---------- modify ----------

def modify_labels(
    message_id: str, add: list[str] | None = None, remove: list[str] | None = None
) -> MessageRef:
    svc = gmail_service()
    msg = (
        svc.users()
        .messages()
        .modify(
            userId="me",
            id=message_id,
            body={"addLabelIds": add or [], "removeLabelIds": remove or []},
        )
        .execute()
    )
    return MessageRef(id=msg["id"], thread_id=msg.get("threadId", ""))


def archive(message_id: str) -> MessageRef:
    return modify_labels(message_id, remove=["INBOX"])


def mark_read(message_id: str) -> MessageRef:
    return modify_labels(message_id, remove=["UNREAD"])


def mark_unread(message_id: str) -> MessageRef:
    return modify_labels(message_id, add=["UNREAD"])
