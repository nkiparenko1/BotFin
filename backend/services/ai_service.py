"""DeepSeek API client."""

import json
from collections.abc import AsyncGenerator
from pathlib import Path

import httpx

from config import settings

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def load_prompt(name: str) -> str:
    """Load prompt template from file."""
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")


class AIService:
    """DeepSeek chat and embedding client."""

    def __init__(self) -> None:
        self.api_key = settings.deepseek_api_key
        self.base_url = settings.deepseek_base_url.rstrip("/")
        self.chat_model = settings.deepseek_chat_model

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def chat_stream(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
    ) -> AsyncGenerator[tuple[str, int | None], None]:
        """Stream chat completion tokens. Yields (content_chunk, total_tokens_on_done)."""
        payload = {
            "model": self.chat_model,
            "messages": [{"role": "system", "content": system_prompt}, *messages],
            "stream": True,
        }
        total_tokens = None
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/v1/chat/completions",
                headers=self._headers(),
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    chunk = json.loads(data)
                    delta = chunk["choices"][0].get("delta", {})
                    if content := delta.get("content"):
                        yield content, None
                    if usage := chunk.get("usage"):
                        total_tokens = usage.get("total_tokens")
        yield "", total_tokens

    async def chat_complete(self, system_prompt: str, messages: list[dict[str, str]]) -> tuple[str, int]:
        """Non-streaming chat completion."""
        payload = {
            "model": self.chat_model,
            "messages": [{"role": "system", "content": system_prompt}, *messages],
            "stream": False,
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/v1/chat/completions",
                headers=self._headers(),
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            tokens = data.get("usage", {}).get("total_tokens", 0)
            return content, tokens

    async def get_embedding(self, text: str) -> list[float]:
        """Get text embedding vector."""
        payload = {"model": settings.deepseek_embedding_model, "input": text}
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/v1/embeddings",
                headers=self._headers(),
                json=payload,
            )
            response.raise_for_status()
            return response.json()["data"][0]["embedding"]


ai_service = AIService()
