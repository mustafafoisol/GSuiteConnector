"""Application configuration (env-driven via pydantic-settings)."""
from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/ directory (this file is backend/app/config.py)
BASE_DIR = Path(__file__).resolve().parent.parent

# OAuth scopes for Gmail (read/search/send/draft/modify) + Calendar.
GOOGLE_SCOPES: list[str] = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Claude
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"

    # Google OAuth
    google_client_secret_file: str = "client_secret.json"
    token_file: str = "token.json"
    oauth_redirect_uri: str = "http://localhost:8000/api/auth/callback"

    # App
    frontend_origin: str = "http://localhost:5173"

    @property
    def client_secret_path(self) -> Path:
        p = Path(self.google_client_secret_file)
        return p if p.is_absolute() else BASE_DIR / p

    @property
    def token_path(self) -> Path:
        p = Path(self.token_file)
        return p if p.is_absolute() else BASE_DIR / p


settings = Settings()
