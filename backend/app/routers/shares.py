"""Sharing routes: grant, list, and revoke document access by email."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import get_current_user, get_document_for_user
from ..database import get_db
from ..models import Share, User
from ..schemas import ShareCreate, ShareOut

router = APIRouter(prefix="/api/documents/{document_id}/shares", tags=["shares"])


def _require_owner(document_id: int, db: Session, user: User):
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
    _require_owner(document_id, db, user)

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
    if share:  # idempotent: update role instead of duplicating
        share.role = payload.role
    else:
        share = Share(document_id=document_id, user_id=target.id, role=payload.role)
        db.add(share)
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
