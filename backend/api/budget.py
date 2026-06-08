"""Budget and transactions API."""

import json
import uuid
from collections import defaultdict
from datetime import date, datetime

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import extract, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import get_current_user
from models import Profile, Transaction, User
from schemas import ImportConfirmRequest, TransactionCreate, TransactionOut, TransactionUpdate, BudgetAnalyzeRequest
from services.ai_service import ai_service, load_prompt
from services.csv_parser import detect_and_parse

router = APIRouter(prefix="/api/budget", tags=["budget"])

CATEGORIES = ["food", "transport", "housing", "subscriptions", "entertainment", "health", "other"]


async def _categorize_batch(descriptions: list[str]) -> list[str]:
    """AI-categorize transaction descriptions."""
    if not descriptions:
        return []
    prompt = (
        "Классифицируй каждую транзакцию в одну категорию: "
        + ", ".join(CATEGORIES)
        + ". Ответь JSON-массивом категорий в том же порядке."
    )
    items = "\n".join(f"{i+1}. {d}" for i, d in enumerate(descriptions))
    try:
        content, _ = await ai_service.chat_complete(prompt, [{"role": "user", "content": items}])
        import re
        match = re.search(r"\[.*\]", content, re.DOTALL)
        if match:
            cats = json.loads(match.group())
            return [c if c in CATEGORIES else "other" for c in cats]
    except Exception:
        pass
    return ["other"] * len(descriptions)


@router.get("/transactions", response_model=list[TransactionOut])
async def list_transactions(
    month: str | None = Query(None),
    category: str | None = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(Transaction).where(Transaction.user_id == user.id)
    if month:
        year, mon = map(int, month.split("-"))
        q = q.where(extract("year", Transaction.date) == year, extract("month", Transaction.date) == mon)
    if category:
        q = q.where(Transaction.category == category)
    q = q.order_by(Transaction.date.desc())
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/transactions", response_model=TransactionOut)
async def create_transaction(
    body: TransactionCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tx = Transaction(
        user_id=user.id,
        amount=body.amount,
        category=body.category,
        date=body.date,
        description=body.description,
    )
    db.add(tx)
    await db.flush()
    return tx


@router.patch("/transactions/{tx_id}", response_model=TransactionOut)
async def update_transaction(
    tx_id: uuid.UUID,
    body: TransactionUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Transaction).where(Transaction.id == tx_id, Transaction.user_id == user.id))
    tx = result.scalar_one_or_none()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(tx, field, value)
    await db.flush()
    return tx


@router.delete("/transactions/{tx_id}", status_code=204)
async def delete_transaction(
    tx_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Transaction).where(Transaction.id == tx_id, Transaction.user_id == user.id))
    tx = result.scalar_one_or_none()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    await db.delete(tx)


@router.post("/import-csv")
async def import_csv(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    content = (await file.read()).decode("utf-8-sig")
    rows = detect_and_parse(content, file.filename or "export.csv")
    descriptions = [r["description"] for r in rows]
    categories = await _categorize_batch(descriptions[:50])
    preview = []
    for i, row in enumerate(rows):
        cat = categories[i] if i < len(categories) else "other"
        preview.append({**row, "category": cat})
    return {"preview": preview}


@router.post("/import-csv/confirm")
async def confirm_import(
    body: ImportConfirmRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count = 0
    for item in body.transactions:
        tx = Transaction(
            user_id=user.id,
            amount=item["amount"],
            category=item.get("category", "other"),
            description=item.get("description"),
            date=date.fromisoformat(item["date"]),
            source="csv_import",
        )
        db.add(tx)
        count += 1
    await db.flush()
    return {"imported_count": count}


@router.post("/analyze")
async def analyze_budget(
    body: BudgetAnalyzeRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Stream AI budget analysis."""
    month = body.month or datetime.now().strftime("%Y-%m")
    year, mon = map(int, month.split("-"))
    result = await db.execute(
        select(Transaction).where(
            Transaction.user_id == user.id,
            extract("year", Transaction.date) == year,
            extract("month", Transaction.date) == mon,
        )
    )
    transactions = result.scalars().all()
    by_category: dict[str, float] = defaultdict(float)
    for tx in transactions:
        by_category[tx.category or "other"] += float(tx.amount)

    profile_result = await db.execute(select(Profile).where(Profile.user_id == user.id))
    profile = profile_result.scalar_one_or_none()
    income = float(profile.monthly_income or 0) if profile else 0

    system = load_prompt("budget_agent.txt")
    system = system.replace("{monthly_income}", str(income))
    system = system.replace("{month}", month)
    system = system.replace("{category_breakdown_json}", json.dumps(dict(by_category), ensure_ascii=False))

    async def stream():
        total_tokens = 0
        async for chunk, tokens in ai_service.chat_stream(system, [{"role": "user", "content": "Проанализируй мой бюджет."}]):
            if chunk:
                yield f"data: {json.dumps({'type': 'text', 'content': chunk}, ensure_ascii=False)}\n\n"
            if tokens:
                total_tokens = tokens
        yield f"data: {json.dumps({'type': 'done', 'tokens': total_tokens}, ensure_ascii=False)}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")
