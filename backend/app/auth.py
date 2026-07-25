"""Password hashing, JWT issuing/verification, and access-control helpers."""
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, Request, Response, status
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from . import config
from .database import get_db
from .models import Document, Share, User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

JWT_ALGORITHM = "HS256"


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


def _extract_token(request: Request) -> str | None:
    """Prefer an Authorization: Bearer header, fall back to the cookie."""
    authz = request.headers.get("Authorization", "")
    if authz.lower().startswith("bearer "):
        return authz[7:].strip()
    return request.cookies.get(config.COOKIE_NAME)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Resolve the JWT (header or cookie) to a User, or raise 401."""
    token = _extract_token(request)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    try:
        payload = decode_access_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")

    user = db.get(User, int(payload.get("sub", 0)))
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session user not found")
    return user


# --- Document access control -------------------------------------------------
def resolve_role(db: Session, document: Document, user: User) -> str | None:
    """Return the user's access level for a document, or None if no access."""
    if document.owner_id == user.id:
        return "owner"
    share = (
        db.query(Share)
        .filter(Share.document_id == document.id, Share.user_id == user.id)
        .first()
    )
    return share.role if share else None


def get_document_for_user(
    document_id: int, db: Session, user: User, *, need_edit: bool = False
) -> tuple[Document, str]:
    """Fetch a document the user may access; enforce 404/403 uniformly.

    Returns (document, role). need_edit=True rejects viewers with 403.
    """
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")

    role = resolve_role(db, document, user)
    if role is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You do not have access to this document")
    if need_edit and role == "viewer":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You have view-only access")
    return document, role
