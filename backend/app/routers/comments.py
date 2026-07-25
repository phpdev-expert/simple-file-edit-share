"""Comments and edit-suggestions anchored to a quoted span of a document."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..deps import get_current_user, get_document_for_user
from ..models import Comment, User
from ..schemas import CommentCreate, CommentOut
from ..services import notifications as notif_svc

router = APIRouter(prefix="/api/documents/{document_id}/comments", tags=["comments"])


def _get_comment(document_id: int, comment_id: int, db: Session) -> Comment:
    comment = db.get(Comment, comment_id)
    if comment is None or comment.document_id != document_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Comment not found")
    return comment


@router.get("", response_model=list[CommentOut])
def list_comments(
    document_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    get_document_for_user(document_id, db, user)  # access check
    return (
        db.query(Comment)
        .filter(Comment.document_id == document_id)
        .order_by(Comment.resolved.asc(), Comment.created_at.desc())
        .all()
    )


@router.post("", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def create_comment(
    document_id: int,
    payload: CommentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Anyone with access may comment or suggest (including view-only collaborators).
    doc, _role = get_document_for_user(document_id, db, user)
    if payload.kind == "suggestion" and not (payload.suggested_text or "").strip():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "A suggestion needs replacement text")

    comment = Comment(
        document_id=document_id,
        author_id=user.id,
        author_name=user.name,
        kind=payload.kind,
        quote=payload.quote,
        body=payload.body,
        suggested_text=payload.suggested_text,
    )
    db.add(comment)

    # Let the owner know someone weighed in (unless they did it themselves).
    if doc.owner_id != user.id:
        verb = "suggested an edit on" if payload.kind == "suggestion" else "commented on"
        notif_svc.notify(db, doc.owner_id, f'{user.name} {verb} "{doc.title}"', document_id=document_id)

    db.commit()
    db.refresh(comment)
    return comment


@router.post("/{comment_id}/resolve", response_model=CommentOut)
def resolve_comment(
    document_id: int,
    comment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Editors/owners, or the comment's author, may resolve it.
    doc, role = get_document_for_user(document_id, db, user)
    comment = _get_comment(document_id, comment_id, db)
    if role == "viewer" and comment.author_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not allowed to resolve this")
    comment.resolved = True
    db.commit()
    db.refresh(comment)
    return comment


@router.post("/{comment_id}/accept", response_model=CommentOut)
def accept_suggestion(
    document_id: int,
    comment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Accepting applies a text change, so it requires edit access. The actual
    # find-and-replace happens client-side in the editor; here we just record it.
    get_document_for_user(document_id, db, user, need_edit=True)
    comment = _get_comment(document_id, comment_id, db)
    if comment.kind != "suggestion":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Only suggestions can be accepted")
    comment.resolved = True
    db.commit()
    db.refresh(comment)
    return comment
