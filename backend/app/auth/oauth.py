"""OAuth 2.0 web flow helpers (single-user, local)."""
from __future__ import annotations

from google_auth_oauthlib.flow import Flow

from app.config import GOOGLE_SCOPES, settings


def _build_flow() -> Flow:
    if not settings.client_secret_path.exists():
        raise FileNotFoundError(
            f"OAuth client file not found at {settings.client_secret_path}. "
            "Download it from Google Cloud Console (see README)."
        )
    return Flow.from_client_secrets_file(
        str(settings.client_secret_path),
        scopes=GOOGLE_SCOPES,
        redirect_uri=settings.oauth_redirect_uri,
    )


def build_authorization_url() -> str:
    """URL the browser is sent to for consent."""
    flow = _build_flow()
    url, _state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",  # force refresh_token on every consent
    )
    return url


def exchange_code(code: str):
    """Exchange the callback authorization code for credentials."""
    flow = _build_flow()
    flow.fetch_token(code=code)
    return flow.credentials
