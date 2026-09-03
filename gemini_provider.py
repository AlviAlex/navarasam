"""Cloud AI implementation supporting Google Gemini API and Groq API."""

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ai_provider import AIProvider, AIProviderError


class GeminiProvider(AIProvider):
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash", timeout_seconds: int = 30) -> None:
        self.api_key = api_key.strip() if api_key else ""
        self.model = model or "gemini-2.5-flash"
        self.timeout_seconds = timeout_seconds

    def chat(self, messages: list[dict[str, str]], schema: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            raise AIProviderError(
                "Gemini API key is missing. Set GEMINI_API_KEY in your .env or environment variable."
            )

        # 1. Automatic Groq support if user provides a Groq key (starts with 'gsk_')
        if self.api_key.startswith("gsk_"):
            return self._call_groq(messages)

        # 2. Google Gemini API
        return self._call_gemini(messages)

    def _call_gemini(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        system_instruction = None
        contents = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                system_instruction = {"parts": [{"text": content}]}
            else:
                gemini_role = "user" if role == "user" else "model"
                contents.append({"role": gemini_role, "parts": [{"text": content}]})

        payload_dict: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.0,
                "maxOutputTokens": 300,
                "responseMimeType": "application/json",
            },
        }
        if system_instruction:
            payload_dict["systemInstruction"] = system_instruction

        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = json.dumps(payload_dict).encode("utf-8")
        request = Request(
            endpoint,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Connection": "keep-alive",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                raw_response = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            try:
                err_body = json.loads(exc.read().decode("utf-8"))
                msg = err_body.get("error", {}).get("message", "")
            except Exception:
                msg = ""

            if exc.code == 400 or exc.code == 403:
                detail = f"Gemini API error ({exc.code}): {msg}" if msg else "Gemini API key is invalid or lacks access."
            elif exc.code == 404:
                detail = f"Gemini model '{self.model}' was not found. Try 'gemini-1.5-flash' or 'gemini-2.5-flash'."
            elif exc.code == 429:
                detail = "Gemini API rate limit reached. Please wait a moment and try again."
            else:
                detail = f"Gemini API error ({exc.code}): {msg or 'Request failed.'}"
            raise AIProviderError(detail) from exc
        except (URLError, TimeoutError) as exc:
            raise AIProviderError("Could not reach Google Gemini API. Check your internet connection.") from exc
        except json.JSONDecodeError as exc:
            raise AIProviderError("Gemini returned an unreadable response.") from exc

        candidates = raw_response.get("candidates", [])
        if not candidates:
            raise AIProviderError("Gemini returned an empty response.")

        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts or "text" not in parts[0]:
            raise AIProviderError("Gemini returned an incomplete response structure.")

        return self._decode_json_text(parts[0]["text"])

    def _call_groq(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        """High-speed Groq API integration (Llama 3.3 70B Versatile)."""
        endpoint = "https://api.groq.com/openai/v1/chat/completions"
        payload_dict = {
            "model": "llama-3.3-70b-versatile",
            "messages": messages,
            "temperature": 0.0,
            "max_tokens": 300,
            "response_format": {"type": "json_object"},
        }
        payload = json.dumps(payload_dict).encode("utf-8")
        request = Request(
            endpoint,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                raw_response = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            try:
                err_body = json.loads(exc.read().decode("utf-8"))
                msg = err_body.get("error", {}).get("message", "")
            except Exception:
                msg = ""
            raise AIProviderError(f"Groq API error ({exc.code}): {msg or 'Authentication / request failed.'}") from exc
        except (URLError, TimeoutError) as exc:
            raise AIProviderError("Could not reach Groq API. Check your network connection.") from exc
        except json.JSONDecodeError as exc:
            raise AIProviderError("Groq returned an unreadable response.") from exc

        choices = raw_response.get("choices", [])
        if not choices:
            raise AIProviderError("Groq returned an empty response.")

        content = choices[0].get("message", {}).get("content", "")
        return self._decode_json_text(content)

    def _decode_json_text(self, text: str) -> dict[str, Any]:
        raw_text = text.strip()
        if raw_text.startswith("```"):
            raw_text = raw_text.strip("`")
            if raw_text.lower().startswith("json"):
                raw_text = raw_text[4:].strip()

        try:
            decoded = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise AIProviderError("Model returned malformed JSON data. Please try again.") from exc

        if not isinstance(decoded, dict):
            raise AIProviderError("Model returned an unexpected JSON structure.")

        return decoded
