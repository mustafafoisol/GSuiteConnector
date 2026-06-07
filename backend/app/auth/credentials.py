"""Load and refresh the single user's Google OAuth credentials."""
from __future__ import annotations

import json
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from app.config import GOOGLE_SCOPES, settings


class NotAuthenticatedError(RuntimeError):
    """Raised when no valid Google credentials are available."""


def save_credentials(creds: Credentials) -> None:
    settings.token_path.write_text(creds.to_json(), encoding="utf-8")


def load_credentials() -> Credentials | None:
    """Return cached credentials (refreshing if needed), or None if absent."""
    token_path: Path = settings.token_path
    if not token_path.exists():
        return None

    data = json.loads(token_path.read_text(encoding="utf-8"))
    creds = Credentials.from_authorized_user_info(data, GOOGLE_SCOPES)

    if creds.valid:
        return creds

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        save_credentials(creds)
        return creds

    return None


def require_credentials() -> Credentials:
    creds = load_credentials()
    if creds is None:
        raise NotAuthenticatedError(
            "Not connected to Google. Visit /api/auth/login to authorize."
        )
    return creds
