"""Tax advisor API."""

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import get_current_user
from models import TaxCalculation, TaxProfile, User
from schemas import TaxAskRequest, TaxProfileOut
from services.ai_service import ai_service, load_prompt
from services.rag_service import search_knowledge
from services.tax_calculator import calculate_deductions

router = APIRouter(prefix="/api/tax", tags=["tax"])


async def _get_or_create_tax_profile(db: AsyncSession, user: User) -> TaxProfile:
    result = await db.execute(select(TaxProfile).where(TaxProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        profile = TaxProfile(user_id=user.id)
        db.add(profile)
        await db.flush()
    return profile


@router.get("/profile", response_model=TaxProfileOut)
async def get_tax_profile(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    profile = await _get_or_create_tax_profile(db, user)
    return profile


@router.post("/profile", response_model=TaxProfileOut)
async def save_tax_profile(
    data: dict,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_or_create_tax_profile(db, user)
    for key, value in data.items():
        if hasattr(profile, key):
            setattr(profile, key, value)
    await db.flush()
    return profile


@router.post("/calculate")
async def calculate_tax(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_or_create_tax_profile(db, user)
    deductions, total, documents = calculate_deductions(profile)
    calc = TaxCalculation(
        user_id=user.id,
        deductions=deductions,
        total_return=total,
        documents=documents,
    )
    db.add(calc)
    await db.flush()
    return {
        "calculation_id": calc.id,
        "deductions": deductions,
        "total_return": float(total),
        "documents": documents,
    }


@router.post("/ask")
async def ask_tax(
    body: TaxAskRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    calc = None
    if body.calculation_id:
        result = await db.execute(
            select(TaxCalculation).where(
                TaxCalculation.id == body.calculation_id,
                TaxCalculation.user_id == user.id,
            )
        )
        calc = result.scalar_one_or_none()
    else:
        result = await db.execute(
            select(TaxCalculation)
            .where(TaxCalculation.user_id == user.id)
            .order_by(TaxCalculation.created_at.desc())
            .limit(1)
        )
        calc = result.scalar_one_or_none()

    if not calc:
        raise HTTPException(status_code=400, detail="Сначала выполните расчёт вычетов")

    rag_chunks = await search_knowledge(db, body.question, topic_prefix="tax")
    rag_context = "\n\n".join(rag_chunks) if rag_chunks else "Нет дополнительного контекста."

    system = load_prompt("tax_agent.txt")
    system = system.replace("{deductions_json}", json.dumps(calc.deductions, ensure_ascii=False))
    system = system.replace("{total_return}", str(calc.total_return))
    system = system.replace("{rag_context}", rag_context)

    async def stream():
        total_tokens = 0
        async for chunk, tokens in ai_service.chat_stream(
            system, [{"role": "user", "content": body.question}]
        ):
            if chunk:
                yield f"data: {json.dumps({'type': 'text', 'content': chunk}, ensure_ascii=False)}\n\n"
            if tokens:
                total_tokens = tokens
        yield f"data: {json.dumps({'type': 'done', 'tokens': total_tokens}, ensure_ascii=False)}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")
