"""Document CRUD plus the owned/shared dashboard listing."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import get_current_user, get_document_for_user
from ..database import get_db
from ..models import Document, Share, User
from ..security import sanitize_html
from ..schemas import (
    DocumentDetail,
    DocumentListResponse,
    DocumentSummary,
    DocumentUpdate,
)

router = APIRouter(prefix="/api/documents", tags=["documents"])


def _summary(doc: Document, role: str) -> DocumentSummary:
    s = DocumentSummary.model_validate(doc)
    s.role = role
    return s


@router.get("", response_model=DocumentListResponse)
def list_documents(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    owned = (
        db.query(Document)
        .filter(Document.owner_id == user.id)
        .order_by(Document.updated_at.desc())
        .all()
    )
    shared_rows = (
        db.query(Document, Share.role)
        .join(Share, Share.document_id == Document.id)
        .filter(Share.user_id == user.id)
        .order_by(Document.updated_at.desc())
        .all()
    )
    return DocumentListResponse(
        owned=[_summary(d, "owner") for d in owned],
        shared=[_summary(d, role) for d, role in shared_rows],
    )


@router.post("", response_model=DocumentDetail, status_code=status.HTTP_201_CREATED)
def create_document(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    doc = Document(title="Untitled", content="", owner_id=user.id)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return _detail(doc, "owner")


@router.get("/{document_id}", response_model=DocumentDetail)
def get_document(
    document_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    doc, role = get_document_for_user(document_id, db, user)
    return _detail(doc, role)


@router.put("/{document_id}", response_model=DocumentDetail)
def update_document(
    document_id: int,
    payload: DocumentUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    doc, role = get_document_for_user(document_id, db, user, need_edit=True)
    if payload.title is not None:
        title = payload.title.strip()
        doc.title = title or "Untitled"
    if payload.content is not None:
        doc.content = sanitize_html(payload.content)
    db.commit()
    db.refresh(doc)
    return _detail(doc, role)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    doc, role = get_document_for_user(document_id, db, user)
    if role != "owner":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only the owner can delete a document")
    db.delete(doc)
    db.commit()


def _detail(doc: Document, role: str) -> DocumentDetail:
    detail = DocumentDetail.model_validate(doc)
    detail.role = role
    return detail
