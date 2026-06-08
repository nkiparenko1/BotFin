"""Authentication API routes."""

import uuid

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from config import settings
from database import get_db
from dependencies import get_current_user
from models import Profile, User
from schemas import (
    AuthResponse,
    GoogleAuthRequest,
    LoginRequest,
    MeResponse,
    ProfileOut,
    RegisterRequest,
    UserOut,
)
from services.auth_utils import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _auth_response(user: User) -> AuthResponse:
    return AuthResponse(
        user=UserOut.model_validate(user),
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/register", response_model=AuthResponse)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)) -> AuthResponse:
    """Register new user with email and password."""
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(email=body.email, name=body.name, password_hash=hash_password(body.password))
    db.add(user)
    await db.flush()
    db.add(Profile(user_id=user.id))
    await db.flush()
    return _auth_response(user)


@router.post("/guest", response_model=AuthResponse)
async def guest_login(db: AsyncSession = Depends(get_db)) -> AuthResponse:
    """Create anonymous guest session for chat without registration."""
    guest_id = uuid.uuid4()
    user = User(
        email=f"guest-{guest_id}@guest.local",
        name="Гость",
        provider="guest",
    )
    db.add(user)
    await db.flush()
    db.add(Profile(user_id=user.id))
    await db.flush()
    return _auth_response(user)


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)) -> AuthResponse:
    """Login with email and password."""
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not user.password_hash or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return _auth_response(user)


@router.post("/google", response_model=AuthResponse)
async def google_auth(body: GoogleAuthRequest, db: AsyncSession = Depends(get_db)) -> AuthResponse:
    """Exchange Google OAuth code for JWT."""
    if not settings.google_oauth_client_id:
        raise HTTPException(status_code=501, detail="Google OAuth not configured")

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": body.code,
                "client_id": settings.google_oauth_client_id,
                "client_secret": settings.google_oauth_client_secret,
                "redirect_uri": settings.google_oauth_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if token_resp.status_code != 200:
            raise HTTPException(status_code=401, detail="Google auth failed")
        access = token_resp.json().get("access_token")
        user_resp = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access}"},
        )
        if user_resp.status_code != 200:
            raise HTTPException(status_code=401, detail="Failed to get Google profile")
        info = user_resp.json()

    email = info["email"]
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        user = User(
            email=email,
            name=info.get("name"),
            avatar_url=info.get("picture"),
            provider="google",
        )
        db.add(user)
        await db.flush()
        db.add(Profile(user_id=user.id))
        await db.flush()
    return _auth_response(user)


@router.post("/refresh")
async def refresh_token(body: dict) -> dict:
    """Refresh access token."""
    refresh_token = body.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token required")
    try:
        user_id = decode_token(refresh_token, "refresh")
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from exc
    return {"access_token": create_access_token(user_id)}


@router.post("/logout", status_code=204)
async def logout() -> None:
    """Logout user."""
    return None


@router.get("/me", response_model=MeResponse)
async def me(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> MeResponse:
    """Get current user and profile."""
    result = await db.execute(select(Profile).where(Profile.user_id == user.id))
    profile = result.scalar_one_or_none()
    return MeResponse(
        user=UserOut.model_validate(user),
        profile=ProfileOut.model_validate(profile) if profile else None,
    )


@router.delete("/me", status_code=204)
async def delete_account(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> None:
    """Delete user account and all related data."""
    await db.delete(user)
