"""Notification helpers — thin data-access layer over the Notification model."""
from sqlalchemy.orm import Session

from .. import models


def notify(db: Session, user_id: int, message: str, document_id: int | None = None):
    n = models.Notification(user_id=user_id, message=message, document_id=document_id)
    db.add(n)
    return n


def list_for_user(db: Session, user_id: int, limit: int = 50):
    return (
        db.query(models.Notification)
        .filter(models.Notification.user_id == user_id)
        .order_by(models.Notification.created_at.desc())
        .limit(limit)
        .all()
    )


def unread_count(db: Session, user_id: int) -> int:
    return (
        db.query(models.Notification)
        .filter(models.Notification.user_id == user_id, models.Notification.read == False)  # noqa: E712
        .count()
    )


def mark_all_read(db: Session, user_id: int) -> None:
    db.query(models.Notification).filter(
        models.Notification.user_id == user_id, models.Notification.read == False  # noqa: E712
    ).update({"read": True})
    db.commit()
