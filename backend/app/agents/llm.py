"""
Single entry point for LLM calls: Groq first, Gemini second, each under a hard
timeout. Returns the text together with which provider/model produced it so the
pipeline can record AI metadata. Raises LLMUnavailable when no provider answers;
callers then use the deterministic local analysis instead.
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Optional

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("app.ai.llm")


class LLMUnavailable(Exception):
    pass


@dataclass
class LLMResult:
    text: str
    provider: str
    model: str
    latency_ms: int


async def complete(prompt: str, system: Optional[str] = None, json_mode: bool = False,
                   temperature: float = 0.3, max_tokens: int = 1500, timeout: Optional[float] = None) -> LLMResult:
    from app.agents.gemini_client import gemini_generate
    from app.agents.groq_client import groq_client

    budget = timeout or get_settings().ai_timeout_seconds
    started = time.perf_counter()
    errors = []

    if groq_client.client is not None:
        try:
            result = await asyncio.wait_for(
                groq_client.generate_with_model(prompt, max_tokens=max_tokens, system=system,
                                                temperature=temperature, json_mode=json_mode),
                timeout=budget,
            )
            if result:
                text, model = result
                return LLMResult(text, "groq", model, int((time.perf_counter() - started) * 1000))
            errors.append("groq: no response")
        except asyncio.TimeoutError:
            errors.append("groq: timeout")
        except Exception as exc:  # provider SDK errors vary widely
            errors.append(f"groq: {type(exc).__name__}")

    remaining = max(3.0, budget - (time.perf_counter() - started))
    gemini_prompt = f"{system}\n\n{prompt}" if system else prompt
    if json_mode:
        gemini_prompt += "\n\nRespond with a single JSON object only."
    try:
        text, model = await asyncio.wait_for(gemini_generate(gemini_prompt), timeout=remaining)
        return LLMResult(text, "gemini", model, int((time.perf_counter() - started) * 1000))
    except asyncio.TimeoutError:
        errors.append("gemini: timeout")
    except Exception as exc:
        errors.append(f"gemini: {type(exc).__name__}")

    logger.warning("All LLM providers failed: %s", "; ".join(errors))
    raise LLMUnavailable("; ".join(errors))
