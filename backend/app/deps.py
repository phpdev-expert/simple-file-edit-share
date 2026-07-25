"""FastAPI dependencies: current-user resolution and document access control."""
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from . import models
from .core import config
from .core.database import get_db
from .core.security import decode_access_token
import jwt


def _extract_token(request: Request) -> str | None:
    """Prefer an Authorization: Bearer header, fall back to the cookie."""
    authz = request.headers.get("Authorization", "")
    if authz.lower().startswith("bearer "):
        return authz[7:].strip()
    return request.cookies.get(config.COOKIE_NAME)


def user_from_token(token: str | None, db: Session) -> models.User | None:
    """Resolve a raw JWT to a User, or None. Shared by HTTP and WebSocket auth."""
    if not token:
        return None
    try:
        payload = decode_access_token(token)
    except jwt.InvalidTokenError:
        return None
    return db.get(models.User, int(payload.get("sub", 0)))


def get_current_user(request: Request, db: Session = Depends(get_db)) -> models.User:
    """Resolve the JWT (header or cookie) to a User, or raise 401."""
    user = user_from_token(_extract_token(request), db)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    return user


def resolve_role(db: Session, document: models.Document, user: models.User) -> str | None:
    """Return the user's access level for a document, or None if no access."""
    if document.owner_id == user.id:
        return "owner"
    share = (
        db.query(models.Share)
        .filter(models.Share.document_id == document.id, models.Share.user_id == user.id)
        .first()
    )
    return share.role if share else None


def get_document_for_user(
    document_id: int, db: Session, user: models.User, *, need_edit: bool = False
) -> tuple[models.Document, str]:
    """Fetch a document the user may access; enforce 404/403 uniformly.

    Returns (document, role). need_edit=True rejects viewers with 403.
    """
    document = db.get(models.Document, document_id)
    if document is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")

    role = resolve_role(db, document, user)
    if role is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You do not have access to this document")
    if need_edit and role == "viewer":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You have view-only access")
    return document, role
