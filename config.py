"""Runtime configuration for Emojify."""

import os
from pathlib import Path


# Automatically load .env file if it exists in the workspace
def _load_env_file():
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("'\"")
                    if key and key not in os.environ:
                        os.environ[key] = val


_load_env_file()


class Config:
    MAX_INPUT_LENGTH = int(os.getenv("EMOJIFY_MAX_INPUT_LENGTH", "600"))

    # Provider selection: "gemini" (default) or "ollama"
    AI_PROVIDER = os.getenv("EMOJIFY_PROVIDER", "gemini").lower()

    # Gemini settings
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    GEMINI_TIMEOUT_SECONDS = int(os.getenv("GEMINI_TIMEOUT_SECONDS", "30"))

    # Ollama settings (fallback)
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    OLLAMA_MODEL = os.getenv("EMOJIFY_MODEL", "qwen3:4b-instruct")
    OLLAMA_TIMEOUT_SECONDS = int(os.getenv("EMOJIFY_TIMEOUT_SECONDS", "45"))

    MAX_CONCEPTS = 8
