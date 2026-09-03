# Emojify

**Say less. Emoji more.** Emojify is a hyper-rational semantic emoji translator featuring a deterministic **Emoji Look-Up Table (LUT)** first-tier engine with **AI Fallback** (Google Gemini API / Ollama) and native **Apple iOS Emoji Font Pack (`ios_emoji.ttf`)** rendering.

## Architecture

```text
User Input → Translator Service
                │
                ├─── 1. Check Emoji Look-Up Table (LUT) ───[ Match Found ]───► Instant Validated Output
                │
                └─── 2. If Not in LUT (Complex/Novel) ────► AI Engine (Gemini / Ollama)
                                                                 │
                                                                 ▼
                                                        Structured JSON Output
                                                                 │
                                                                 ▼
                                                    Browser (@font-face IOSEmoji)
```

1. **Deterministic Look-Up Table (LUT)**: Fast, zero-token semantic knowledge base (`emoji_lut.py`) matching common phrases, entities, and feelings (with question `❓` and exclamation `❗` punctuation handling).
2. **AI Fallback Engine**: Complex or unmatched phrases are dynamically routed to **Google Gemini API** (`gemini-2.5-flash`) or local **Ollama** with strict literal rationality.
3. **iOS Emoji Font Pack (`ios_emoji.ttf`)**: Emojis are validated on the backend against 1,485 font codepoints and rendered in the browser with bundled `@font-face`.
4. **Emoji Knowledge Base API (`GET /api/lut`)**: Returns the full dictionary of emojis with all their possible meanings, keywords, emotions, and feelings.

## Configuration

Set your Gemini API key in an environment variable or create a `.env` file in the project root:

```ini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
EMOJIFY_PROVIDER=gemini
```

*(To use local Ollama instead, set `EMOJIFY_PROVIDER=ollama` in `.env`)*

## Setup and Run

```powershell
python app.py
```

Open **http://127.0.0.1:5000** in your browser.

## Running Tests

```powershell
python -m pytest
```
