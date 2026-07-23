import logging

import requests

from .base import AIProvider

logger = logging.getLogger("bohlale")


class OpenAICompatibleProvider(AIProvider):
    """
    Works with any OpenAI Chat Completions–compatible HTTP endpoint —
    OpenAI itself, Azure OpenAI (compatible mode), or a Qwen-compatible
    endpoint such as DashScope's OpenAI-compatible mode. Point
    AI_API_BASE at the relevant endpoint; the wire protocol is the same
    shape either way, which is why one adapter class serves both
    branches of the §37 architecture diagram.
    """

    name = "openai_compatible"

    def __init__(self, base_url, api_key, model):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    def complete(self, *, system_prompt, user_prompt, purpose="general", max_tokens=1200):
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "max_tokens": max_tokens,
                    "temperature": 0.4,
                },
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception:
            logger.exception("AI provider request failed (purpose=%s)", purpose)
            return (
                "[AI generation unavailable — the configured AI provider could not be "
                "reached. Please draft this content manually or try again later.]"
            )
