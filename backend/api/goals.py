"""Financial goals API."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import get_current_user
from models import Goal, User
from schemas import GoalCreate, GoalOut, GoalUpdate
from services.goals_service import calculate_monthly_deposit, goal_scenarios

router = APIRouter(prefix="/api/goals", tags=["goals"])

GOAL_LIMIT = 1


def _goal_calculations(goal: Goal) -> dict:
    deposit = calculate_monthly_deposit(
        goal.target_amount, goal.current_amount, goal.deadline_months, goal.expected_return
    )
    goal.monthly_deposit = deposit
    scenarios = goal_scenarios(
        goal.target_amount, goal.current_amount, goal.deadline_months, goal.expected_return, deposit
    )
    progress = float(goal.current_amount / goal.target_amount * 100) if goal.target_amount else 0
    return {
        "monthly_deposit": float(deposit),
        "progress_pct": min(progress, 100),
        "scenarios": scenarios,
    }


@router.get("")
async def list_goals(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Goal).where(Goal.user_id == user.id).order_by(Goal.created_at.desc()))
    goals = result.scalars().all()
    return [{"goal": GoalOut.model_validate(g), "calculations": _goal_calculations(g)} for g in goals]


@router.post("")
async def create_goal(
    body: GoalCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    active_count = await db.execute(
        select(func.count()).select_from(Goal).where(Goal.user_id == user.id, Goal.status == "active")
    )
    if (active_count.scalar() or 0) >= GOAL_LIMIT:
        raise HTTPException(status_code=400, detail=f"Лимит Free: {GOAL_LIMIT} активная цель")

    goal = Goal(
        user_id=user.id,
        name=body.name,
        target_amount=body.target_amount,
        current_amount=body.current_amount,
        expected_return=body.expected_return,
        deadline_months=body.deadline_months,
    )
    db.add(goal)
    await db.flush()
    calcs = _goal_calculations(goal)
    await db.flush()
    return {"goal": GoalOut.model_validate(goal), "calculations": calcs}


@router.get("/{goal_id}")
async def get_goal(
    goal_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Goal).where(Goal.id == goal_id, Goal.user_id == user.id))
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return {"goal": GoalOut.model_validate(goal), "calculations": _goal_calculations(goal)}


@router.patch("/{goal_id}")
async def update_goal(
    goal_id: uuid.UUID,
    body: GoalUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Goal).where(Goal.id == goal_id, Goal.user_id == user.id))
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(goal, field, value)
    await db.flush()
    return {"goal": GoalOut.model_validate(goal), "calculations": _goal_calculations(goal)}


@router.delete("/{goal_id}", status_code=204)
async def delete_goal(
    goal_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Goal).where(Goal.id == goal_id, Goal.user_id == user.id))
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    await db.delete(goal)
