import os
import json
import httpx
from dataclasses import dataclass
from typing import AsyncGenerator, Optional
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "llm", ".env"))

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


@dataclass
class StreamChunk:
    content: str
    finished: bool
    usage: Optional[dict] = None


class OpenRouterClient:

    def __init__(self, model: str = "openrouter/owl-alpha"):
        self.api_key = os.getenv("API", "")
        self.model = model
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=5.0, read=60.0, write=5.0, pool=5.0),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )
        self.sync_client = httpx.Client(
            timeout=httpx.Timeout(connect=5.0, read=60.0, write=5.0, pool=5.0),
        )

    def _headers(self, stream: bool = False) -> dict:
        h = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if stream:
            h["Accept"] = "text/event-stream"
        return h

    def _payload(
        self, messages: list, stream: bool = False, max_tokens: int = 2048, temperature: float = 0.7
    ) -> dict:
        p = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "stream": stream,
            "temperature": temperature,
        }
        return p

    async def complete(
        self, messages: list, max_tokens: int = 2048, temperature: float = 0.7
    ) -> str:
        resp = await self.client.post(
            OPENROUTER_URL,
            headers=self._headers(),
            json=self._payload(messages, stream=False, max_tokens=max_tokens, temperature=temperature),
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    async def complete_json(
        self, messages: list, max_tokens: int = 2048, temperature: float = 0.7
    ) -> dict:
        resp = await self.client.post(
            OPENROUTER_URL,
            headers=self._headers(),
            json=self._payload(messages, stream=False, max_tokens=max_tokens, temperature=temperature),
        )
        resp.raise_for_status()
        return resp.json()

    def complete_sync(
        self, messages: list, max_tokens: int = 2048, temperature: float = 0.7
    ) -> str:
        resp = self.sync_client.post(
            OPENROUTER_URL,
            headers=self._headers(),
            json=self._payload(messages, stream=False, max_tokens=max_tokens, temperature=temperature),
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    def complete_json_sync(
        self, messages: list, max_tokens: int = 2048, temperature: float = 0.7
    ) -> dict:
        resp = self.sync_client.post(
            OPENROUTER_URL,
            headers=self._headers(),
            json=self._payload(messages, stream=False, max_tokens=max_tokens, temperature=temperature),
        )
        resp.raise_for_status()
        return resp.json()

    async def stream(
        self, messages: list, max_tokens: int = 2048, temperature: float = 0.7
    ) -> AsyncGenerator[StreamChunk, None]:
        async with self.client.stream(
            "POST",
            OPENROUTER_URL,
            headers=self._headers(stream=True),
            json=self._payload(messages, stream=True, max_tokens=max_tokens, temperature=temperature),
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.startswith("data: "):
                    continue
                payload = line[6:]
                if payload.strip() == "[DONE]":
                    yield StreamChunk(content="", finished=True)
                    return
                try:
                    chunk = json.loads(payload)
                    delta = chunk["choices"][0].get("delta", {})
                    content = delta.get("content", "")
                    finish = chunk["choices"][0].get("finish_reason")
                    usage = chunk.get("usage")
                    if content:
                        yield StreamChunk(
                            content=content,
                            finished=finish is not None,
                            usage=usage,
                        )
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue

    async def close(self):
        await self.client.aclose()
        self.sync_client.close()
