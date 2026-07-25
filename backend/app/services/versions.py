"""Document version-history helpers: throttled snapshots + restore."""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from .. import models

# Don't snapshot on every debounced autosave; keep at most one per window.
THROTTLE_SECONDS = 45
MAX_VERSIONS = 30


def _age_seconds(dt: datetime) -> float:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - dt).total_seconds()


def snapshot(db: Session, document: models.Document, author: models.User | None) -> None:
    """Unconditionally record the current document state as a version."""
    db.add(
        models.DocumentVersion(
            document_id=document.id,
            title=document.title,
            content=document.content,
            author_id=author.id if author else None,
            author_name=author.name if author else "",
        )
    )
    db.flush()
    _prune(db, document.id)


def maybe_snapshot(db: Session, document: models.Document, author: models.User | None) -> None:
    """Record the current document state as a version, throttled by time.

    Call this AFTER updating the document, when the content actually changed.
    """
    latest = (
        db.query(models.DocumentVersion)
        .filter(models.DocumentVersion.document_id == document.id)
        .order_by(models.DocumentVersion.created_at.desc())
        .first()
    )
    if latest is not None and _age_seconds(latest.created_at) < THROTTLE_SECONDS:
        return
    snapshot(db, document, author)


def _prune(db: Session, document_id: int) -> None:
    """Keep only the most recent MAX_VERSIONS snapshots."""
    ids = [
        v.id
        for v in db.query(models.DocumentVersion.id)
        .filter(models.DocumentVersion.document_id == document_id)
        .order_by(models.DocumentVersion.created_at.desc())
        .offset(MAX_VERSIONS)
        .all()
    ]
    if ids:
        db.query(models.DocumentVersion).filter(
            models.DocumentVersion.id.in_(ids)
        ).delete(synchronize_session=False)


def list_for_document(db: Session, document_id: int):
    return (
        db.query(models.DocumentVersion)
        .filter(models.DocumentVersion.document_id == document_id)
        .order_by(models.DocumentVersion.created_at.desc())
        .all()
    )
