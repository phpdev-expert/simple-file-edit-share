"""File import: turn an uploaded .txt/.md file into a new editable document."""
import io
import os
from html import escape

import mammoth
import markdown as md
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from ..core import config
from ..core.database import get_db
from ..core.security import sanitize_html
from ..deps import get_current_user
from ..models import Document, User
from ..schemas import DocumentDetail

router = APIRouter(prefix="/api/uploads", tags=["uploads"])


def _txt_to_html(text: str) -> str:
    """Wrap plain-text lines in paragraphs, preserving blank-line breaks."""
    paragraphs = [p.strip() for p in text.split("\n\n")]
    html = "".join(
        f"<p>{escape(p).replace(chr(10), '<br>')}</p>" for p in paragraphs if p
    )
    return html or "<p></p>"


@router.post("", response_model=DocumentDetail, status_code=status.HTTP_201_CREATED)
async def import_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in config.ALLOWED_UPLOAD_EXTS:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Unsupported file type '{ext or 'unknown'}'. Allowed: .txt, .md, .docx",
        )

    # Read at most limit+1 bytes so an oversized upload can't balloon memory.
    raw = await file.read(config.MAX_UPLOAD_BYTES + 1)
    if len(raw) > config.MAX_UPLOAD_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "File exceeds 5 MB limit")

    if ext == ".docx":
        # .docx is a binary (zip) format; mammoth maps its styles to semantic HTML.
        try:
            content = mammoth.convert_to_html(io.BytesIO(raw)).value or "<p></p>"
        except Exception:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Could not read .docx file")
    else:
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "File must be UTF-8 text")
        if ext == ".md":
            content = md.markdown(text, extensions=["extra", "sane_lists"])
        else:
            content = _txt_to_html(text)

    # .md and .docx can carry raw HTML/scripting; sanitize before persisting.
    content = sanitize_html(content)

    title = os.path.splitext(os.path.basename(file.filename or "Imported"))[0] or "Imported"
    doc = Document(title=title[:255], content=content, owner_id=user.id)
    db.add(doc)
    db.commit()
    db.refresh(doc)

    detail = DocumentDetail.model_validate(doc)
    detail.role = "owner"
    return detail
