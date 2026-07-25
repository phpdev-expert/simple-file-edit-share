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
    # Set per-request after validation; "owner", "editor" or "viewer".
    role: str = ""


class DocumentListResponse(BaseModel):
    owned: list[DocumentSummary]
    shared: list[DocumentSummary]


class DocumentUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=255)
    content: Optional[str] = None


class ShareCreate(BaseModel):
    email: EmailStr
    role: Literal["editor", "viewer"] = "editor"


class ShareOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user: UserOut
    role: str
