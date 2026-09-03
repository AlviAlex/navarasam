# Navarasam — Cognitive Semantic Emoji Translation SaaS

> **Talk in Thoughts. Chat in Pure Emojis.**  
> Navarasam is an AI-powered cognitive semantic emoji translation engine and real-time 2-person chat platform that decodes human syntax, spatial relations (`inside`, `with`, `under`), negation (`🚫`), and event sequences into native Apple iOS emojis.

---

## 🌐 Live SaaS Platform

**🚀 Live Website:** [https://navarasam.onrender.com/](https://navarasam.onrender.com/)  
**💬 Instant Chat App:** [https://navarasam.onrender.com/app](https://navarasam.onrender.com/app)

---

## ✨ Key Features

- **🧠 Cognitive Semantic Decoder**: Analyzes whole sentence meaning instead of word-to-word dictionary lookup. Preserves spatial containment (`bring the beer in the bag` $\to$ `🍺 📥 👜`) and question intent (`where are you?` $\to$ `🧑 ❓`).
- **💬 Real-Time 2-Person Rooms**: Instant P2P synchronized chat with 1-click global share links.
- **⚡ Sub-Millisecond Speed**: Multi-tier architecture (<0.05ms memory Look-Up Table + Google Gemini 2.5 Flash).
- **🍎 Pure Apple iOS Font Fidelity**: Bundled `ios_emoji.ttf` (1,485 validated glyphs) guarantees identical Cupertino emoji rendering across Windows, Mac, Linux, and Android.
- **🚫 Strict Non-Hallucination**: Eliminates decorative random vibe noise (`✨`, `🔥`, `💀`, `🚀`) unless explicitly stated.
- **🔌 Developer REST API**: High-throughput `/api/translate` and `/api/rooms` endpoints for bots and integrations.

---

## 🏗️ Architecture

```text
User Natural Language Input
       │
       ├─── 1. In-Memory Look-Up Table (LUT) ───[ Match Found (<0.05ms) ]───► Instant Apple Emojis
       │
       └─── 2. Cognitive AI Planner (Gemini 2.5 Flash)
                     │
                     ├─ Extract Entities & Actions
                     ├─ Preserve Spatial / Logical Relations (in 📥, with 🤝, under ⬇️)
                     ├─ Context Disambiguation (School 🏫 vs Graduation 🎓)
                     └─ Order by Chronological & Grammatical SVO Flow
                                 │
                                 ▼
                     iOS Font Glyph Pack Validation
                                 │
                                 ▼
                     Real-Time WebSocket Sync (Socket.IO)
```

---

## 🚀 Quick Start (Local Setup)

### 1. Clone the repository
```bash
git clone https://github.com/AlviAlex/navarasam.git
cd navarasam
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure your API key
Create a `.env` file in the project root:
```ini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

### 4. Run the server
```bash
python app.py
```
Open **`http://127.0.0.1:5000`** in your browser.

---

## 🧪 Running Tests

```bash
python -m pytest
```
*38 of 38 unit, integration, and whitebox tests covering all edge cases, relationship mappings, and WebSocket handlers.*

---

## 📡 API Reference

### Semantic Translation Endpoint

```bash
curl -X POST https://navarasam.onrender.com/api/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "bring the beer in the bag"}'
```

**Response (200 OK):**
```json
{
  "emojis": "🍺 📥 👜",
  "concepts": [
    {"name": "beer", "emoji": "🍺"},
    {"name": "inside/in", "emoji": "📥"},
    {"name": "bag", "emoji": "👜"}
  ],
  "explanation": "Semantic relation: beer located inside the bag."
}
```

---

## 📄 License

MIT License © 2026 Navarasam. Built with Google Gemini and Apple iOS Font Pack.
