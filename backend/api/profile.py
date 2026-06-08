"""Profile and onboarding API routes."""

from decimal import Decimal

from fastapi import APIRouter, Body, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import get_current_user
from models import Profile, User
from schemas import OnboardingRequest, OnboardingResponse, ProfileOut, ProfileResponse
from services.scoring import build_action_plan, calculate_health_score

router = APIRouter(prefix="/api/profile", tags=["profile"])

FIELD_MAP = {
    "name": None,
    "age": "age",
    "region": "region",
    "family_status": "family_status",
    "monthly_income": "monthly_income",
    "fixed_expenses": "fixed_expenses",
    "variable_expenses": "variable_expenses",
    "savings": "savings",
    "has_mortgage": "has_mortgage",
    "mortgage_payment": "mortgage_payment",
    "has_loans": "has_loans",
    "loan_payment": "loan_payment",
    "investment_exp": "investment_exp",
    "risk_level": "risk_level",
    "main_goal": "main_goal",
    "goal_years": "goal_years",
}


async def _get_or_create_profile(db: AsyncSession, user: User) -> Profile:
    result = await db.execute(select(Profile).where(Profile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        profile = Profile(user_id=user.id)
        db.add(profile)
        await db.flush()
    return profile


def _apply_data(profile: Profile, user: User, data: dict) -> None:
    if name := data.get("name"):
        user.name = name
    for key, attr in FIELD_MAP.items():
        if key == "name" or attr is None:
            continue
        if key in data:
            value = data[key]
            if attr in ("monthly_income", "fixed_expenses", "variable_expenses", "savings", "mortgage_payment", "loan_payment"):
                value = Decimal(str(value)) if value is not None else None
            setattr(profile, attr, value)


@router.post("/onboarding", response_model=OnboardingResponse)
async def save_onboarding(
    body: OnboardingRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OnboardingResponse:
    """Save onboarding step data."""
    profile = await _get_or_create_profile(db, user)
    _apply_data(profile, user, body.data)

    plan = None
    if body.step >= 3:
        profile.onboarding_done = True
        profile.health_score = calculate_health_score(profile)
        plan = build_action_plan(profile)
    else:
        profile.health_score = calculate_health_score(profile)

    await db.flush()
    return OnboardingResponse(
        profile=ProfileOut.model_validate(profile),
        health_score=profile.health_score or 0,
        plan=plan,
    )


@router.get("", response_model=ProfileResponse)
async def get_profile(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> ProfileResponse:
    """Get user profile."""
    result = await db.execute(select(Profile).where(Profile.user_id == user.id))
    profile = result.scalar_one_or_none()
    return ProfileResponse(
        profile=ProfileOut.model_validate(profile) if profile else None,
        health_score=profile.health_score if profile else None,
    )


@router.patch("", response_model=ProfileResponse)
async def update_profile(
    data: dict = Body(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    """Update profile fields."""
    profile = await _get_or_create_profile(db, user)
    _apply_data(profile, user, data)
    profile.health_score = calculate_health_score(profile)
    await db.flush()
    return ProfileResponse(profile=ProfileOut.model_validate(profile), health_score=profile.health_score)
