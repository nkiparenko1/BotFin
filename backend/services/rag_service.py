"""RAG vector search service."""

import uuid

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from models import KnowledgeChunk
from services.ai_service import ai_service


async def search_knowledge(
    db: AsyncSession,
    query: str,
    topic_prefix: str = "tax",
    limit: int = 5,
) -> list[str]:
    """Search knowledge chunks by semantic similarity."""
    try:
        embedding = await ai_service.get_embedding(query)
    except Exception:
        result = await db.execute(
            select(KnowledgeChunk.content)
            .where(KnowledgeChunk.topic.like(f"{topic_prefix}%"))
            .limit(limit)
        )
        return list(result.scalars().all())

    embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
    sql = text("""
        SELECT content FROM knowledge_chunks
        WHERE topic LIKE :topic
        ORDER BY embedding <=> :embedding::vector
        LIMIT :limit
    """)
    result = await db.execute(sql, {"topic": f"{topic_prefix}%", "embedding": embedding_str, "limit": limit})
    return [row[0] for row in result.fetchall()]
