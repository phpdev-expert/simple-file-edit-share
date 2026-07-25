"""Document CRUD, the owned/shared dashboard listing, and version history."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.security import sanitize_html
from ..deps import get_current_user, get_document_for_user
from ..models import Document, DocumentVersion, Share, User
from ..schemas import (
    DocumentDetail,
    DocumentListResponse,
    DocumentSummary,
    DocumentUpdate,
    VersionSummary,
)
from ..services import versions as versions_svc

router = APIRouter(prefix="/api/documents", tags=["documents"])


def _summary(doc: Document, role: str) -> DocumentSummary:
    s = DocumentSummary.model_validate(doc)
    s.role = role
    return s


def _detail(doc: Document, role: str) -> DocumentDetail:
    detail = DocumentDetail.model_validate(doc)
    detail.role = role
    return detail


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

    content_changed = False
    if payload.content is not None:
        new_content = sanitize_html(payload.content)
        content_changed = new_content != doc.content
        doc.content = new_content

    db.commit()
    db.refresh(doc)

    # Record a throttled version snapshot when the body actually changed.
    if content_changed:
        versions_svc.maybe_snapshot(db, doc, user)
        db.commit()
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


# --- Version history --------------------------------------------------------
@router.get("/{document_id}/versions", response_model=list[VersionSummary])
def list_versions(
    document_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    get_document_for_user(document_id, db, user)  # access check
    return versions_svc.list_for_document(db, document_id)


@router.post("/{document_id}/versions/{version_id}/restore", response_model=DocumentDetail)
def restore_version(
    document_id: int,
    version_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    doc, role = get_document_for_user(document_id, db, user, need_edit=True)
    version = db.get(DocumentVersion, version_id)
    if version is None or version.document_id != document_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Version not found")

    # Snapshot the current state first so a restore is itself reversible.
    versions_svc.snapshot(db, doc, user)
    doc.title = version.title
    doc.content = version.content
    db.commit()
    db.refresh(doc)
    return _detail(doc, role)
