"""Index RAG documents into knowledge_chunks."""

import argparse
import asyncio
import uuid
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from config import settings
from models import KnowledgeChunk
from database import Base
from services.ai_service import ai_service

TOPIC_MAP = {
    "nk_rf_excerpts.md": "tax_deduction",
    "tax_deductions.md": "tax_deduction",
    "fns_instructions.md": "tax_fns",
    "iis_guide.md": "tax_iis",
    "mortgage_deduction.md": "tax_mortgage",
}


def chunk_text(text_content: str, size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks."""
    words = text_content.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i : i + size])
        if chunk.strip():
            chunks.append(chunk)
        i += size - overlap
    return chunks or [text_content]


async def ingest(source_dir: Path) -> None:
    """Load documents and store embeddings."""
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as db:
        for path in source_dir.glob("*.md"):
            content = path.read_text(encoding="utf-8")
            topic = TOPIC_MAP.get(path.name, "tax_general")
            for piece in chunk_text(content):
                try:
                    embedding = await ai_service.get_embedding(piece)
                except Exception:
                    embedding = [0.0] * 1536
                db.add(
                    KnowledgeChunk(
                        id=uuid.uuid4(),
                        source=path.stem,
                        topic=topic,
                        content=piece,
                        embedding=embedding,
                    )
                )
        await db.commit()
    await engine.dispose()
    print("Ingestion complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="rag/documents/")
    args = parser.parse_args()
    asyncio.run(ingest(Path(args.source)))
