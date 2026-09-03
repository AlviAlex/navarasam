"""Translation and semantic emoji sequence planning pipeline."""

import json
import re
from typing import Any, Optional

from ai_provider import AIProvider, AIProviderError
from emoji_lut import LUTService
from emoji_pack import filter_supported_emojis

EMOJI_RE = re.compile(
    r"[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U00002B00-\U00002BFF\U00002300-\U000023FF\U00002000-\U000020FF\U0000FE00-\U0000FE0F\u20E3\u3030\u00A9\u00AE]"
)

FORWARD_SCHEMA = {
    "type": "object",
    "properties": {
        "emojis": {
            "type": "string",
            "description": "Space-separated sequence of Apple iOS emojis representing the decoded semantic concepts and relationships."
        },
        "concepts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "role": {
                        "type": "string",
                        "description": "Semantic role: entity, action, relation, context, modifier, negation, or intent"
                    },
                    "name": {"type": "string", "description": "English meaning of the concept or relationship"},
                    "emoji": {"type": "string", "description": "Single matching Apple iOS emoji from the supported pack"}
                },
                "required": ["name", "emoji"]
            },
            "description": "Deconstructed semantic concepts and relationships in planned order."
        },
        "emotion": {
            "type": ["string", "null"],
            "description": "Explicit emotional state expressed by user, or null"
        },
        "explanation": {
            "type": "string",
            "description": "Brief explanation of the semantic interpretation and relationship mapping."
        }
    },
    "required": ["emojis", "concepts", "explanation"],
    "additionalProperties": False,
}


class TranslationService:
    def __init__(self, provider: AIProvider, max_input_length: int = 600, max_concepts: int = 8, lut_service: Optional[LUTService] = None) -> None:
        self.provider = provider
        self.max_input_length = max_input_length
        self.max_concepts = max_concepts
        self.lut_service = lut_service or LUTService()

    def translate(self, text: str) -> dict[str, Any]:
        clean_text = self._validate_input(text)

        # 1. Test Look-Up Table (LUT) for exact idioms or phrases (<0.1ms)
        lut_result = self.lut_service.lookup(clean_text)
        if lut_result is not None:
            return self._validate_result(lut_result)

        # 2. For multi-word complex statements, invoke the Semantic Decoder
        try:
            messages = self._build_messages(clean_text)
            result = self.provider.chat(messages, FORWARD_SCHEMA)
            validated = self._validate_result(result)
        except AIProviderError:
            fallback_res = self.lut_service.fallback_extract(clean_text)
            validated = self._validate_result(fallback_res)

        # Cache planned result in memory
        self.lut_service.put_cache(clean_text.lower(), validated)
        return validated

    def _validate_input(self, text: Any) -> str:
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Write something first — even a tiny thought counts.")
        clean_text = " ".join(text.split())
        if len(clean_text) > self.max_input_length:
            raise ValueError(f"Keep it under {self.max_input_length} characters so the AI can focus.")
        return clean_text

    def _build_messages(self, text: str) -> list[dict[str, str]]:
        system = (
            "You are Emojify, a hyper-rational semantic emoji translator and Cognitive Semantic Decoder.\n\n"
            "### CORE PHILOSOPHY & THINKING PROCESS:\n"
            "You must behave as a SEMANTIC DECODER, NOT as a word-to-emoji dictionary.\n"
            "Follow this internal cognitive process:\n"
            "Natural Language Input → Understand complete sentence → Extract semantic concepts & entities → "
            "Extract relationships between concepts (e.g. inside, with, without, under, above, to, from) → "
            "Identify actions / context / modifiers / negation / intent → Map meaningful concepts to emojis → "
            "Produce final emoji sequence.\n\n"
            "### STRICT RULES:\n"
            "1. LINGUISTIC FORM VS SEMANTIC MEANING:\n"
            "   - Do NOT translate every word independently. Do NOT assign arbitrary emojis to grammatical filler words (e.g. 'are', 'the', 'is', 'a').\n"
            "   - Treat input as: sentence → meaning → semantic concepts/relationships → emojis.\n\n"
            "2. PRESERVE SEMANTIC RELATIONSHIPS:\n"
            "   - When a sentence expresses a spatial or logical relation between entities, preserve that relationship:\n"
            "     * 'in' / 'inside' / 'into' → 📥 (in/inside/inbox)\n"
            "     * 'with' → 🧑‍🤝‍🧑 / 🤝\n"
            "     * 'without' / 'no' / 'not' → 🚫\n"
            "     * 'to' / 'from' / 'toward' / 'then' → ➡️\n"
            "     * 'under' / 'below' → ⬇️\n"
            "     * 'above' / 'over' → ⬆️\n"
            "   - Example: 'bring the beer in the bag' contains entities (beer, bag) and relation (inside: beer in bag). "
            "Output must represent beer + inside + bag: '🍺 📥 👜'. The relation 'in' must NEVER disappear into just '🍺 👜'.\n\n"
            "3. QUESTION SEMANTICS & INTENT:\n"
            "   - Question words ('where', 'why', 'when', 'how') contribute to question semantics, not independent object emojis.\n"
            "   - Example: 'where are you?' → entity: person/you (🧑), intent: question (❓) → '🧑 ❓'. Do NOT translate 'where', 'are', 'you' independently.\n\n"
            "4. CONTEXTUAL EMOJI SELECTION (NO BLIND MAPPING):\n"
            "   - Understand context before selecting emojis:\n"
            "     * 'I went to school' describes the place/building → '🏫' (not graduation 🎓)\n"
            "     * 'I graduated from school' describes graduation → '🎓' (or '🧑 🎓 🏫')\n\n"
            "5. NEGATION CONVENTION:\n"
            "   - For negated actions/preferences, place 🚫 directly after the negated entity/action:\n"
            "     * 'I don't like coffee' → '☕ 🚫'\n\n"
            "6. Direct & Literal Accuracy:\n"
            "   - Map each core entity to its single most direct emoji from standard Apple iOS emoji sets. "
            "   - Never use slang, trendy metaphors, or loose associations.\n\n"
            "7. NUMERIC & TEMPORAL QUANTITIES:\n"
            "   - When numbers or quantities are given, use numeric emojis: 0️⃣, 1️⃣, 2️⃣, 3️⃣, 4️⃣, 5️⃣, 6️⃣, 7️⃣, 8️⃣, 9️⃣, 🔟, 💯\n"
            "   - Time concepts: 'tonight' / 'night' / 'midnight' → 🌙; 'tomorrow' / 'yesterday' / 'date' → 📅; 'morning' → 🌅; 'evening' → 🌇\n\n"
            "8. TERMINAL PUNCTUATION RULES:\n"
            "   - Question or Interrogation ('Where are you?', 'Are we meeting tomorrow?') → Always end with ❓\n"
            "   - Exclamation, Alert or Command ('Hurry up!', 'Watch out for the train!') → Always end with ❗\n"
            "   - Shocked question / Interrobang ('What happened to the car?!') → Always end with ⁉️\n\n"
            "9. Zero Decorative Vibe & DO NOT INVENT INFORMATION:\n"
            "   - NEVER include decorative filler emojis (like ✨, 🔥, 💀, 🚀, 😎, 😂, ❤️) unless explicitly expressed in the sentence.\n"
            "   - Do not invent actions or contexts not stated (e.g. 'bring' does not mean running 🏃; 'beer' does not mean party 🎉).\n\n"
            "### EXAMPLES OF SEMANTIC DECODING:\n"
            "- 'bring the beer in the bag' → emojis: '🍺 📥 👜', concepts: [{'name': 'beer', 'emoji': '🍺'}, {'name': 'inside/in', 'emoji': '📥'}, {'name': 'bag', 'emoji': '👜'}]\n"
            "- 'where are you?' → emojis: '🧑 ❓', concepts: [{'name': 'you', 'emoji': '🧑'}, {'name': 'question', 'emoji': '❓'}]\n"
            "- 'I don\\'t like coffee' → emojis: '☕ 🚫', concepts: [{'name': 'coffee', 'emoji': '☕'}, {'name': 'negation', 'emoji': '🚫'}]\n"
            "- 'I am going to college tomorrow' → emojis: '🧑 🚶 🏫 📅', concepts: [{'name': 'person', 'emoji': '🧑'}, {'name': 'go/walk', 'emoji': '🚶'}, {'name': 'college', 'emoji': '🏫'}, {'name': 'tomorrow', 'emoji': '📅'}]\n"
            "- 'I went to school' → emojis: '🧑 🚶 🏫', concepts: [{'name': 'person', 'emoji': '🧑'}, {'name': 'went', 'emoji': '🚶'}, {'name': 'school', 'emoji': '🏫'}]\n"
            "- 'I graduated from school' → emojis: '🧑 🎓 🏫', concepts: [{'name': 'person', 'emoji': '🧑'}, {'name': 'graduated', 'emoji': '🎓'}, {'name': 'school', 'emoji': '🏫'}]\n"
            "- 'I have 3 cats and 2 dogs tonight' → emojis: '🧑 3️⃣ 🐱 2️⃣ 🐶 🌙', concepts: [{'name': 'I', 'emoji': '🧑'}, {'name': '3', 'emoji': '3️⃣'}, {'name': 'cats', 'emoji': '🐱'}, {'name': '2', 'emoji': '2️⃣'}, {'name': 'dogs', 'emoji': '🐶'}, {'name': 'tonight', 'emoji': '🌙'}]\n\n"
            "Output strictly conforming JSON without markdown fences."
        )
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": f"Sentence to semantically decode: \"{text}\"\nJSON Schema: {json.dumps(FORWARD_SCHEMA)}"},
        ]

    def _validate_result(self, result: dict[str, Any]) -> dict[str, Any]:
        main_value = result.get("emojis")
        concepts = result.get("concepts")
        emotion = result.get("emotion")
        explanation = result.get("explanation")
        if not isinstance(main_value, str) or not main_value.strip() or len(main_value) > 500:
            raise AIProviderError("The model produced an unusable result. Please try again.")
        if not EMOJI_RE.search(main_value):
            raise AIProviderError("The model did not return emojis. Please try again.")

        # Ensure emojis are supported in the iOS emoji font pack
        clean_emojis = filter_supported_emojis(main_value.strip())
        if not clean_emojis or not EMOJI_RE.search(clean_emojis):
            clean_emojis = main_value.strip()

        if not isinstance(concepts, list) or len(concepts) > self.max_concepts:
            raise AIProviderError("The model returned invalid concepts. Please try again.")
        safe_concepts = []
        for concept in concepts:
            if not isinstance(concept, dict):
                raise AIProviderError("The model returned invalid concepts. Please try again.")
            name, emoji = concept.get("name"), concept.get("emoji")
            if not isinstance(name, str) or not isinstance(emoji, str) or not name.strip() or not emoji.strip():
                raise AIProviderError("The model returned invalid concepts. Please try again.")
            safe_concepts.append({"name": name.strip()[:60], "emoji": emoji.strip()[:24]})

        if emotion is not None and (not isinstance(emotion, str) or len(emotion) > 80):
            emotion = None
        if not isinstance(explanation, str):
            explanation = "A local AI rationally mapped the core ideas to emojis."
        return {
            "emojis": clean_emojis,
            "concepts": safe_concepts,
            "emotion": emotion.strip() if isinstance(emotion, str) and emotion.strip() else None,
            "explanation": explanation.strip()[:1000] or "A local AI rationally mapped the core ideas to emojis.",
        }
