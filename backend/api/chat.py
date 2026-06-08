"""Chat API with SSE streaming."""

import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import async_session, get_db
from dependencies import get_current_user
from models import ChatSession, ChatUsage, Message, Profile, User
from schemas import ChatMessageRequest, ChatSessionOut, MessageOut
from services.ai_service import ai_service, load_prompt
from services.scoring import calculate_health_score

router = APIRouter(prefix="/api/chat", tags=["chat"])

CHAT_LIMIT = 50


def _profile_context(profile: Profile | None, user: User) -> str:
    if not profile:
        return f"Имя: {user.name or 'Пользователь'}. Профиль не заполнен."
    return (
        f"Имя: {user.name}\n"
        f"Возраст: {profile.age}, регион: {profile.region}, семья: {profile.family_status}\n"
        f"Доход: {profile.monthly_income} ₽/мес, расходы: "
        f"{(profile.fixed_expenses or 0) + (profile.variable_expenses or 0)} ₽/мес\n"
        f"Накопления: {profile.savings} ₽\n"
        f"Цель: {profile.main_goal}, срок: {profile.goal_years} лет\n"
        f"Риск-профиль: {profile.risk_level}\n"
        f"Financial Health Score: {profile.health_score or calculate_health_score(profile)}/100"
    )


async def _check_usage(db: AsyncSession, user_id: uuid.UUID) -> None:
    ym = datetime.now(timezone.utc).strftime("%Y-%m")
    result = await db.execute(
        select(ChatUsage).where(ChatUsage.user_id == user_id, ChatUsage.year_month == ym)
    )
    usage = result.scalar_one_or_none()
    if not usage:
        usage = ChatUsage(user_id=user_id, year_month=ym, count=0)
        db.add(usage)
        await db.flush()
    if usage.count >= CHAT_LIMIT:
        raise HTTPException(status_code=429, detail=f"Лимит {CHAT_LIMIT} сообщений в месяц исчерпан")


@router.get("/sessions", response_model=list[ChatSessionOut])
async def list_sessions(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ChatSession).where(ChatSession.user_id == user.id).order_by(ChatSession.created_at.desc())
    )
    return result.scalars().all()


@router.post("/sessions")
async def create_session(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    session = ChatSession(user_id=user.id, title="Новый чат")
    db.add(session)
    await db.flush()
    return {"session_id": session.id}


@router.get("/sessions/{session_id}/messages", response_model=list[MessageOut])
async def get_messages(
    session_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Session not found")
    msgs = await db.execute(
        select(Message).where(Message.session_id == session_id).order_by(Message.created_at)
    )
    return msgs.scalars().all()


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(
    session_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    await db.delete(session)


@router.post("/message")
async def send_message(
    body: ChatMessageRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send chat message and stream AI response via SSE."""
    result = await db.execute(
        select(ChatSession).where(ChatSession.id == body.session_id, ChatSession.user_id == user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    await _check_usage(db, user.id)

    session_id = session.id
    user_id = user.id
    user_message = body.message
    ym = datetime.now(timezone.utc).strftime("%Y-%m")

    async def event_stream():
        async with async_session() as stream_db:
            usage_result = await stream_db.execute(
                select(ChatUsage).where(ChatUsage.user_id == user_id, ChatUsage.year_month == ym)
            )
            stream_usage = usage_result.scalar_one()
            profile_result = await stream_db.execute(select(Profile).where(Profile.user_id == user_id))
            stream_profile = profile_result.scalar_one_or_none()
            user_result = await stream_db.execute(select(User).where(User.id == user_id))
            stream_user = user_result.scalar_one()

            user_msg = Message(session_id=session_id, role="user", content=user_message)
            stream_db.add(user_msg)
            sess_result = await stream_db.execute(select(ChatSession).where(ChatSession.id == session_id))
            stream_session = sess_result.scalar_one()
            if not stream_session.title or stream_session.title == "Новый чат":
                stream_session.title = user_message[:50]
            await stream_db.flush()

            history_result = await stream_db.execute(
                select(Message).where(Message.session_id == session_id).order_by(Message.created_at.desc()).limit(20)
            )
            history = list(reversed(history_result.scalars().all()))
            messages = [{"role": m.role, "content": m.content} for m in history]

            system_template = load_prompt("finance_assistant.txt")
            system_prompt = system_template.replace(
                "{profile_context}", _profile_context(stream_profile, stream_user)
            )

            full_content = ""
            total_tokens = 0
            async for chunk, tokens in ai_service.chat_stream(system_prompt, messages):
                if chunk:
                    full_content += chunk
                    yield f"data: {json.dumps({'type': 'text', 'content': chunk}, ensure_ascii=False)}\n\n"
                if tokens:
                    total_tokens = tokens

            assistant_msg = Message(
                session_id=session_id,
                role="assistant",
                content=full_content,
                tokens=total_tokens or None,
            )
            stream_db.add(assistant_msg)
            stream_usage.count += 1
            await stream_db.commit()
            yield f"data: {json.dumps({'type': 'done', 'message_id': str(assistant_msg.id), 'tokens': total_tokens}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
