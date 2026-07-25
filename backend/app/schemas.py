"""Pydantic request/response models."""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class DocumentSummary(BaseModel):
    """Lightweight shape for dashboard lists (no content payload)."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    owner: UserOut
    updated_at: datetime
    folder_id: Optional[int] = None
    # Populated per-request: the caller's access level for this doc.
    role: Optional[str] = None


class DocumentDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    content: str
    owner: UserOut
    created_at: datetime
    updated_at: datetime
    folder_id: Optional[int] = None
    # Set per-request after validation; "owner", "editor" or "viewer".
    role: str = ""


class DocumentListResponse(BaseModel):
    owned: list[DocumentSummary]
    shared: list[DocumentSummary]


class DocumentUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=255)
    content: Optional[str] = None
    # Presence of this key (even as null) moves the doc; absence leaves it.
    folder_id: Optional[int] = None


class ShareCreate(BaseModel):
    email: EmailStr
    role: Literal["editor", "viewer"] = "editor"


class ShareOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user: UserOut
    role: str


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    message: str
    document_id: Optional[int] = None
    read: bool
    created_at: datetime


class NotificationList(BaseModel):
    items: list[NotificationOut]
    unread: int


class VersionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    author_name: str
    created_at: datetime


class CommentCreate(BaseModel):
    kind: Literal["comment", "suggestion"] = "comment"
    quote: str = Field(default="", max_length=4000)
    body: str = Field(default="", max_length=4000)
    suggested_text: Optional[str] = Field(default=None, max_length=4000)


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    kind: str
    quote: str
    body: str
    suggested_text: Optional[str] = None
    author_name: str
    resolved: bool
    created_at: datetime


class FolderCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class FolderOut(BaseModel):
    id: int
    name: str
    doc_count: int


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    history: list[ChatMessage] = []


class ChatResponse(BaseModel):
    answer: str
    sources: list[str] = []
