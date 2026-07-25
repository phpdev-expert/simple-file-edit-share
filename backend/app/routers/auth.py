"""Authentication routes: login, logout, and current-user lookup (JWT-based)."""
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.security import (
    clear_auth_cookie,
    create_access_token,
    set_auth_cookie,
    verify_password,
)
from ..deps import get_current_user
from ..models import User
from ..schemas import LoginRequest, LoginResponse, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")

    token = create_access_token(user.id)
    # HTTP-only cookie for the browser SPA; also returned in the body for API clients.
    set_auth_cookie(response, token)
    return LoginResponse(access_token=token, user=user)


@router.post("/logout")
def logout(response: Response):
    clear_auth_cookie(response)
    return {"ok": True}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
