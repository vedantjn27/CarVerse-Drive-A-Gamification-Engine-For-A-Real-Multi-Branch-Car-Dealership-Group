"""Optional Mistral-first/Gemini-fallback text generation; never controls scoring."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import AICache


class AIProvider:
    """A cache-backed text-only gateway with a deterministic caller supplied fallback."""

    async def generate(self, session: AsyncSession, *, feature: str, system_prompt: str, user_prompt: str, fallback: str) -> dict[str, str]:
        payload = json.dumps({"feature": feature, "system": system_prompt, "user": user_prompt}, sort_keys=True, separators=(",", ":"))
        key = hashlib.sha256(payload.encode()).hexdigest()
        now = datetime.now(UTC).replace(tzinfo=None)
        cached = await session.get(AICache, key)
        if cached is not None and cached.expires_at > now:
            return {"text": cached.response_text, "provider": cached.provider, "cached": "true"}
        provider, text = await self._request(system_prompt, user_prompt, fallback)
        expires_at = now + timedelta(seconds=settings.ai_cache_ttl_seconds)
        statement = sqlite_insert(AICache)
        excluded = statement.excluded
        await session.execute(statement.on_conflict_do_update(index_elements=["cache_key"], set_={"provider": excluded.provider, "response_text": excluded.response_text, "created_at": excluded.created_at, "expires_at": excluded.expires_at}), [{"cache_key": key, "feature": feature, "provider": provider, "response_text": text, "created_at": now, "expires_at": expires_at}])
        await session.commit()
        return {"text": text, "provider": provider, "cached": "false"}

    async def _request(self, system_prompt: str, user_prompt: str, fallback: str) -> tuple[str, str]:
        timeout = httpx.Timeout(settings.ai_timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout) as client:
            if settings.mistral_api_key is not None:
                try:
                    response = await client.post("https://api.mistral.ai/v1/chat/completions", headers={"Authorization": f"Bearer {settings.mistral_api_key.get_secret_value()}"}, json={"model": settings.mistral_model, "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], "temperature": 0.4, "max_tokens": 220})
                    response.raise_for_status()
                    content = response.json()["choices"][0]["message"]["content"]
                    if isinstance(content, str) and content.strip():
                        return "mistral", content.strip()
                except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError):
                    pass
            if settings.gemini_api_key is not None:
                try:
                    response = await client.post(f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent", headers={"x-goog-api-key": settings.gemini_api_key.get_secret_value()}, json={"system_instruction": {"parts": [{"text": system_prompt}]}, "contents": [{"parts": [{"text": user_prompt}]}], "generationConfig": {"temperature": 0.4, "maxOutputTokens": 220}})
                    response.raise_for_status()
                    content = response.json()["candidates"][0]["content"]["parts"][0]["text"]
                    if isinstance(content, str) and content.strip():
                        return "gemini", content.strip()
                except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError):
                    pass
        return "deterministic", fallback


ai_provider = AIProvider()
