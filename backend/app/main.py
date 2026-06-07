"""FastAPI application entry point."""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from googleapiclient.errors import HttpError

from app.auth.credentials import NotAuthenticatedError
from app.config import settings
from app.routers import assistant, auth, calendar, gmail

app = FastAPI(title="GSuiteConnector", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(NotAuthenticatedError)
async def _not_authed(_: Request, exc: NotAuthenticatedError):
    return JSONResponse(status_code=401, content={"detail": str(exc)})


@app.exception_handler(HttpError)
async def _google_error(_: Request, exc: HttpError):
    status = getattr(exc, "status_code", None) or 502
    return JSONResponse(status_code=status, content={"detail": f"Google API error: {exc}"})


@app.get("/api/health")
def health():
    return {"status": "ok"}


api_routers = [auth.router, gmail.router, calendar.router, assistant.router]
for r in api_routers:
    app.include_router(r, prefix="/api")
