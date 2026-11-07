"""Nebius Token Factory client for NVIDIA Nemotron models.

OPT-IN ONLY: this is the external "live" inference path. It is used
solely when MESHCFO_INFERENCE=live AND MESHCFO_ENABLE_EXTERNAL=1 AND a
Nebius key is configured. The default inference path is local
(see local_llm.py). Also hosts the shared JSON-payload parsing helpers.
"""

from __future__ import annotations

import json
import re
from typing import Any

from openai import OpenAI, AuthenticationError, APIError

from meshcfo_filing_radar.config import Settings

THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


class TokenFactoryError(RuntimeError):
    pass


def strip_think(text: str) -> str:
    return THINK_RE.sub("", text or "").strip()


def parse_json_payload(text: str) -> dict[str, Any]:
    cleaned = strip_think(text)
    m = FENCE_RE.search(cleaned)
    if m:
        cleaned = m.group(1).strip()
    # try direct
    try:
        direct = json.loads(cleaned)
        if isinstance(direct, dict):
            return direct
    except json.JSONDecodeError:
        pass
    # brace slice
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start >= 0 and end > start:
        sliced = json.loads(cleaned[start : end + 1])
        if isinstance(sliced, dict):
            return sliced
    raise TokenFactoryError(f"Could not parse JSON object from model output: {cleaned[:240]}")


class TokenFactoryClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        key = settings.resolved_nebius_key()
        if not key:
            raise TokenFactoryError("NEBIUS_API_KEY not set")
        self._client = OpenAI(base_url=settings.nebius_base_url, api_key=key)
        self.last_model = ""
        self.last_error: str | None = None

    def complete_json(
        self,
        *,
        model: str,
        system: str,
        user: str,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> dict[str, Any]:
        try:
            resp = self._client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                extra_body={"chat_template_kwargs": {"enable_thinking": False}},
            )
        except AuthenticationError as e:
            self.last_error = f"401 auth: {e}"
            raise TokenFactoryError(
                "Nebius Token Factory authentication failed (401). "
                "Rotate the API key in the Token Factory console and update "
                "NEBIUS_API_KEY / the key file."
            ) from e
        except APIError as e:
            self.last_error = str(e)
            raise TokenFactoryError(f"Token Factory API error: {e}") from e

        content = resp.choices[0].message.content or ""
        self.last_model = model
        return parse_json_payload(content)
