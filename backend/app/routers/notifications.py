"""In-app notification routes."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..deps import get_current_user
from ..models import User
from ..schemas import NotificationList
from ..services import notifications as svc

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("", response_model=NotificationList)
def list_notifications(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return NotificationList(
        items=svc.list_for_user(db, user.id),
        unread=svc.unread_count(db, user.id),
    )


@router.post("/read")
def mark_read(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    svc.mark_all_read(db, user.id)
    return {"ok": True}
