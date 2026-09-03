"""Ollama implementation of the AI provider contract."""

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ai_provider import AIProvider, AIProviderError


class OllamaProvider(AIProvider):
    def __init__(self, base_url: str, model: str, timeout_seconds: int) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def chat(self, messages: list[dict[str, str]], schema: dict[str, Any]) -> dict[str, Any]:
        payload = json.dumps(
            {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "format": schema,
                "options": {"temperature": 0.0, "top_p": 0.9, "num_predict": 512},
            }
        ).encode("utf-8")
        request = Request(
            f"{self.base_url}/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                raw_response = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = "The selected model is unavailable." if exc.code == 404 else "Ollama could not complete this request."
            raise AIProviderError(detail) from exc
        except (URLError, TimeoutError) as exc:
            raise AIProviderError("Ollama is not available. Start Ollama and try again.") from exc
        except json.JSONDecodeError as exc:
            raise AIProviderError("Ollama returned an unreadable response.") from exc

        content = raw_response.get("message", {}).get("content")
        if not isinstance(content, str):
            raise AIProviderError("Ollama returned an incomplete response.")
        clean_content = content.strip()
        if clean_content.startswith("```"):
            clean_content = clean_content.strip("`")
            if clean_content.lower().startswith("json"):
                clean_content = clean_content[4:].strip()
        try:
            decoded = json.loads(clean_content)
        except json.JSONDecodeError as exc:
            raise AIProviderError("The local model returned invalid structured data. Please try again.") from exc
        if not isinstance(decoded, dict):
            raise AIProviderError("The local model returned an unexpected response.")
        return decoded
