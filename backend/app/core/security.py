"""Security primitives: password hashing, JWT, cookies, and HTML sanitization.

Pure functions with no database or model dependencies — the request-scoped auth
dependencies live in app/deps.py.
"""
from datetime import datetime, timedelta, timezone

import bleach
import jwt
from fastapi import Response
from passlib.context import CryptContext

from . import config

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
JWT_ALGORITHM = "HS256"


# --- Passwords ---------------------------------------------------------------
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


# --- JWT ---------------------------------------------------------------------
def create_access_token(user_id: int) -> str:
    """Issue a signed HS256 JWT with standard sub/iat/exp claims."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(seconds=config.SESSION_MAX_AGE),
    }
    return jwt.encode(payload, config.SESSION_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, config.SESSION_SECRET, algorithms=[JWT_ALGORITHM])


# --- Cookies -----------------------------------------------------------------
def set_auth_cookie(response: Response, token: str) -> None:
    """Deliver the JWT as an HTTP-only cookie so browser clients stay XSS-safe."""
    response.set_cookie(
        key=config.COOKIE_NAME,
        value=token,
        max_age=config.SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=config.COOKIE_SECURE,
        path="/",
    )


def clear_auth_cookie(response: Response) -> None:
    response.delete_cookie(config.COOKIE_NAME, path="/")


# --- HTML sanitization -------------------------------------------------------
# Document HTML is stored and re-rendered in the editor and the PDF-export iframe,
# so we sanitize server-side against a strict allow-list matching the editor schema.
ALLOWED_TAGS = [
    "p", "br", "hr",
    "h1", "h2", "h3",
    "strong", "em", "u", "s", "code", "pre", "blockquote",
    "ul", "ol", "li",
    "a",
]
ALLOWED_ATTRIBUTES = {"a": ["href", "title"]}
ALLOWED_PROTOCOLS = ["http", "https", "mailto"]


def sanitize_html(html: str) -> str:
    """Strip anything outside the allow-list (scripts, on* handlers, img, etc.)."""
    if not html:
        return ""
    return bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )
