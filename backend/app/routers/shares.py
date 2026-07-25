"""Sharing routes: grant, list, and revoke document access by email."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..deps import get_current_user, get_document_for_user
from ..models import Document, Share, User
from ..schemas import ShareCreate, ShareOut
from ..services import notifications as notif_svc

router = APIRouter(prefix="/api/documents/{document_id}/shares", tags=["shares"])


def _require_owner(document_id: int, db: Session, user: User) -> Document:
    doc, role = get_document_for_user(document_id, db, user)
    if role != "owner":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only the owner can manage sharing")
    return doc


@router.get("", response_model=list[ShareOut])
def list_shares(
    document_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    _require_owner(document_id, db, user)
    return db.query(Share).filter(Share.document_id == document_id).all()


@router.post("", response_model=ShareOut, status_code=status.HTTP_201_CREATED)
def create_share(
    document_id: int,
    payload: ShareCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    doc = _require_owner(document_id, db, user)

    target = db.query(User).filter(User.email == payload.email.lower()).first()
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No user with that email")
    if target.id == user.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You already own this document")

    share = (
        db.query(Share)
        .filter(Share.document_id == document_id, Share.user_id == target.id)
        .first()
    )
    is_new = share is None
    if share:  # idempotent: update role instead of duplicating
        share.role = payload.role
    else:
        share = Share(document_id=document_id, user_id=target.id, role=payload.role)
        db.add(share)

    # Notify the recipient (only on a fresh share, not a role change).
    if is_new:
        access = "edit" if payload.role == "editor" else "view"
        notif_svc.notify(
            db,
            target.id,
            f'{user.name} shared "{doc.title}" with you ({access} access)',
            document_id=document_id,
        )

    db.commit()
    db.refresh(share)
    return share


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_share(
    document_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _require_owner(document_id, db, user)
    share = (
        db.query(Share)
        .filter(Share.document_id == document_id, Share.user_id == user_id)
        .first()
    )
    if share:
        db.delete(share)
        db.commit()
