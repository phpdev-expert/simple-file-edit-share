"""Folder CRUD plus the folder-as-knowledge-base RAG chat endpoint."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..core import config
from ..core.database import get_db
from ..deps import get_current_user
from ..models import Document, Folder, User
from ..schemas import ChatRequest, ChatResponse, FolderCreate, FolderOut
from ..services import rag

router = APIRouter(prefix="/api/folders", tags=["folders"])


def _owned_folder(folder_id: int, db: Session, user: User) -> Folder:
    folder = db.get(Folder, folder_id)
    if folder is None or folder.owner_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Folder not found")
    return folder


@router.get("", response_model=list[FolderOut])
def list_folders(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    counts = dict(
        db.query(Document.folder_id, func.count(Document.id))
        .filter(Document.owner_id == user.id, Document.folder_id.isnot(None))
        .group_by(Document.folder_id)
        .all()
    )
    folders = (
        db.query(Folder)
        .filter(Folder.owner_id == user.id)
        .order_by(Folder.created_at.desc())
        .all()
    )
    return [FolderOut(id=f.id, name=f.name, doc_count=counts.get(f.id, 0)) for f in folders]


@router.post("", response_model=FolderOut, status_code=status.HTTP_201_CREATED)
def create_folder(
    payload: FolderCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    folder = Folder(name=payload.name.strip(), owner_id=user.id)
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return FolderOut(id=folder.id, name=folder.name, doc_count=0)


@router.delete("/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_folder(
    folder_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    folder = _owned_folder(folder_id, db, user)
    # Detach documents (don't delete them), then remove the folder.
    db.query(Document).filter(Document.folder_id == folder_id).update({"folder_id": None})
    db.delete(folder)
    db.commit()


@router.post("/{folder_id}/chat", response_model=ChatResponse)
def chat_with_folder(
    folder_id: int,
    payload: ChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    folder = _owned_folder(folder_id, db, user)

    docs = (
        db.query(Document)
        .filter(Document.folder_id == folder_id, Document.owner_id == user.id)
        .all()
    )
    if not docs:
        return ChatResponse(
            answer="This folder has no documents yet. Add some documents to chat with them.",
            sources=[],
        )
    if not config.LLM_ENABLED:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "AI chat is not configured on this server (set OPENROUTER_API_KEY).",
        )

    try:
        answer, sources = rag.chat(folder.name, docs, payload.message, payload.history)
    except rag.LLMError as e:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"AI service error: {e}")
    return ChatResponse(answer=answer, sources=sources)
