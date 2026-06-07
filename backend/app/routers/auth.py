"""OAuth endpoints: login, callback, status, logout."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from app.auth import oauth
from app.auth.credentials import load_credentials, save_credentials
from app.config import settings
from app.google.services import get_user_email

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
def login():
    """Return the Google consent URL for the frontend to redirect to."""
    try:
        return {"authorization_url": oauth.build_authorization_url()}
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/callback")
def callback(code: str | None = None, error: str | None = None):
    """Google redirects here after consent; exchange code and persist token."""
    if error:
        return RedirectResponse(f"{settings.frontend_origin}/?auth=error")
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")
    creds = oauth.exchange_code(code)
    save_credentials(creds)
    return RedirectResponse(f"{settings.frontend_origin}/?auth=success")


@router.get("/status")
def status():
    creds = load_credentials()
    if creds is None:
        return {"connected": False, "email": None}
    try:
        return {"connected": True, "email": get_user_email()}
    except Exception:
        return {"connected": True, "email": None}


@router.post("/logout")
def logout():
    if settings.token_path.exists():
        settings.token_path.unlink()
    return {"connected": False}
