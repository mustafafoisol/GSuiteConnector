"""Build authenticated Google API service clients."""
from __future__ import annotations

from googleapiclient.discovery import build

from app.auth.credentials import require_credentials


def gmail_service():
    return build("gmail", "v1", credentials=require_credentials(), cache_discovery=False)


def calendar_service():
    return build("calendar", "v3", credentials=require_credentials(), cache_discovery=False)


def oauth2_service():
    return build("oauth2", "v2", credentials=require_credentials(), cache_discovery=False)


def get_user_email() -> str:
    info = oauth2_service().userinfo().get().execute()
    return info.get("email", "")
