"""
Authentication API endpoints
Handles signup, login, session validation, logout.

Session tokens are delivered via:
  1. Bearer token in JSON response body  (backwards-compatible, used by current frontend)
  2. HttpOnly cookie  (more secure, prevents XSS token theft)

The backend accepts either mechanism for subsequent authenticated requests.
"""
from fastapi import APIRouter, HTTPException, Header, Response, Request
from pydantic import BaseModel
from typing import Optional
import logging

from app.core.config import settings
from app.services.auth_service import (
    create_user,
    authenticate_user,
    create_session,
    validate_session,
    delete_session,
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Cookie name used for HttpOnly session token
_SESSION_COOKIE = "lexra_session"


def _set_session_cookie(response: Response, token: str) -> None:
    """Attach an HttpOnly session cookie to the response."""
    response.set_cookie(
        key=_SESSION_COOKIE,
        value=token,
        httponly=True,
        samesite="lax",          # "none" required if frontend/backend are cross-origin over HTTPS
        secure=settings.COOKIE_SECURE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    """Delete the session cookie."""
    response.delete_cookie(key=_SESSION_COOKIE, path="/")


# ─── Request / Response Models ────────────────────────────────────

class SignUpRequest(BaseModel):
    email: str
    password: str
    full_name: str
    organization: Optional[str] = ""


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    token: str
    user: dict
    message: str


# ─── Endpoints ────────────────────────────────────────────────────

@router.post("/signup", response_model=AuthResponse)
async def signup(request: SignUpRequest, response: Response):
    """Register a new user account"""

    if len(request.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    if not request.email or "@" not in request.email:
        raise HTTPException(status_code=400, detail="A valid email address is required")

    if not request.full_name or not request.full_name.strip():
        raise HTTPException(status_code=400, detail="Full name is required")

    user = create_user(
        email=request.email,
        password=request.password,
        full_name=request.full_name,
        organization=request.organization or "",
    )

    if not user:
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    token = create_session(user["id"])
    _set_session_cookie(response, token)

    logger.info(f"New user registered: {request.email}")
    return AuthResponse(token=token, user=user, message="Account created successfully")


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest, response: Response):
    """Authenticate and return a session token"""

    user = authenticate_user(request.email, request.password)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_session(user["id"])
    _set_session_cookie(response, token)

    logger.info(f"User logged in: {request.email}")
    return AuthResponse(token=token, user=user, message="Login successful")


@router.get("/me")
async def get_current_user(
    request: Request,
    authorization: Optional[str] = Header(None),
):
    """Return the currently authenticated user.
    Accepts either Bearer token in Authorization header or HttpOnly cookie."""

    # Cookie takes priority; fall back to Authorization header
    token = request.cookies.get(_SESSION_COOKIE)
    if not token and authorization:
        token = authorization.replace("Bearer ", "").strip()

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = validate_session(token)
    if not user:
        raise HTTPException(status_code=401, detail="Session expired or invalid")

    return {"user": user}


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    authorization: Optional[str] = Header(None),
):
    """Invalidate the current session and clear the cookie."""

    token = request.cookies.get(_SESSION_COOKIE)
    if not token and authorization:
        token = authorization.replace("Bearer ", "").strip()

    if token:
        delete_session(token)
        logger.info("User logged out")

    _clear_session_cookie(response)
    return {"message": "Logged out successfully"}
