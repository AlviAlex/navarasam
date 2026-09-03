import pytest

from ai_provider import AIProvider, AIProviderError
from app import create_app
import emoji_pack


class FakeProvider(AIProvider):
    def __init__(self, response=None, error=None):
        self.response = response or {
            "emojis": "🍕 ❤️",
            "concepts": [{"name": "pizza", "emoji": "🍕"}, {"name": "love", "emoji": "❤️"}],
            "emotion": "love",
            "explanation": "Direct mapping of pizza and affection.",
        }
        self.error = error
        self.calls = []

    def chat(self, messages, schema):
        self.calls.append((messages, schema))
        if self.error:
            raise self.error
        return self.response


@pytest.fixture
def provider():
    return FakeProvider()


@pytest.fixture
def client(provider):
    return create_app(provider).test_client()


@pytest.mark.parametrize(
    "sentence",
    [
        "Epistemological dialectics oscillate transcendentally.",
        "A quantum algorithm optimizes neural network weights in parallel.",
    ],
)
def test_complex_text_is_sent_to_provider(client, provider, sentence):
    response = client.post("/api/translate", json={"text": sentence})
    assert response.status_code == 200
    assert response.json["emojis"] == "🍕 ❤️"
    prompt = provider.calls[-1][0][0]["content"]
    assert "hyper-rational semantic emoji translator" in prompt
    assert "Direct & Literal Accuracy" in prompt
    assert "Zero Decorative Vibe" in prompt


def test_lut_matches_instantly_without_ai(client, provider):
    response = client.post("/api/translate", json={"text": "i love pizza"})
    assert response.status_code == 200
    assert response.json["emojis"] == "🍕 ❤️"
    assert "Look-Up Table" in response.json["explanation"]
    # Provider was NOT called because LUT resolved it
    assert len(provider.calls) == 0


def test_lut_single_word_and_punctuation(client, provider):
    response = client.post("/api/translate", json={"text": "pizza?"})
    assert response.status_code == 200
    assert response.json["emojis"] == "🍕 ❓"
    assert len(provider.calls) == 0


def test_api_lut_returns_knowledge_base(client):
    response = client.get("/api/lut")
    assert response.status_code == 200
    data = response.json
    assert isinstance(data, list)
    assert len(data) > 30
    pizza_entry = next((item for item in data if item["emoji"] == "🍕"), None)
    assert pizza_entry is not None
    assert "pizza" in pizza_entry["keywords"]
    assert "hungry" in pizza_entry["emotions"]


def test_empty_input_is_friendly(client):
    response = client.post("/api/translate", json={"text": ""})
    assert response.status_code == 400 and "Write something" in response.json["error"]


def test_long_input_is_rejected(client):
    response = client.post("/api/translate", json={"text": "a" * 601})
    assert response.status_code == 400 and "600" in response.json["error"]


def test_invalid_model_response_fallback(client, provider):
    provider.response = {"emojis": "words only", "concepts": [], "emotion": None, "explanation": "x"}
    # Use unmatched text so it tries provider, fails, and falls back gracefully
    response = client.post("/api/translate", json={"text": "quantum entanglement observation test"})
    assert response.status_code == 200
    assert len(response.json["emojis"]) > 0


def test_provider_error_falls_back():
    client = create_app(
        FakeProvider(error=AIProviderError("Gemini API is temporarily busy."))
    ).test_client()
    response = client.post("/api/translate", json={"text": "quantum entanglement observation test"})
    assert response.status_code == 200
    assert len(response.json["emojis"]) > 0


def test_page_has_copy_control_and_font(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "ios_emoji.ttf" in response.text or "IOSEmoji" in response.text

    response_app = client.get("/app")
    assert response_app.status_code == 200
    assert 'id="message-input"' in response_app.text or 'id="composer-form"' in response_app.text


def test_emoji_pack_supports_common_emojis():
    assert emoji_pack.is_emoji_supported("🍕")
    assert emoji_pack.is_emoji_supported("☕")
    assert emoji_pack.is_emoji_supported("🏖️")
    assert emoji_pack.is_emoji_supported("🚫")
    assert emoji_pack.is_emoji_supported("❤️")
    assert emoji_pack.is_emoji_supported("❓")
    assert emoji_pack.is_emoji_supported("❗")
    assert emoji_pack.is_emoji_supported("⁉️")


def test_gemini_missing_api_key_raises():
    from gemini_provider import GeminiProvider

    provider = GeminiProvider(api_key="")
    with pytest.raises(AIProviderError) as exc_info:
        provider.chat([{"role": "user", "content": "hello"}], {})
    assert "Gemini API key is missing" in str(exc_info.value)


def test_room_manager_lifecycle():
    from room_manager import RoomManager

    rm = RoomManager()
    room_id = rm.create_room("testroom")
    assert room_id == "testroom"
    assert rm.get_room("testroom") is not None
    assert rm.join_room("testroom", "socket_1") is True
    assert rm.join_room("testroom", "socket_2") is True
    assert len(rm.get_room("testroom")["participants"]) == 2

    msg = rm.add_message("testroom", "socket_1", "hello", "👋", [], None, "greeting")
    assert msg["emojis"] == "👋"
    assert len(rm.get_room("testroom")["messages"]) == 1


def test_semantic_decoding_acceptance_cases(client):
    # 1. Relation preservation: bring the beer in the bag
    r1 = client.post("/api/translate", json={"text": "bring the beer in the bag"})
    assert r1.status_code == 200
    assert "🍺" in r1.json["emojis"]
    assert "📥" in r1.json["emojis"] or "📦" in r1.json["emojis"]
    assert "👜" in r1.json["emojis"]

    # 2. Question semantics: where are you?
    r2 = client.post("/api/translate", json={"text": "where are you?"})
    assert r2.status_code == 200
    assert "🧑" in r2.json["emojis"] and "❓" in r2.json["emojis"]

    # 3. Negation: I don't like coffee
    r3 = client.post("/api/translate", json={"text": "I don't like coffee"})
    assert r3.status_code == 200
    assert r3.json["emojis"] == "☕ 🚫"

    # 4. Contextual school vs graduation
    r4 = client.post("/api/translate", json={"text": "I went to school"})
    assert r4.status_code == 200
    assert "🏫" in r4.json["emojis"]
    assert "🎓" not in r4.json["emojis"]

    r5 = client.post("/api/translate", json={"text": "I graduated from school"})
    assert r5.status_code == 200
    assert "🎓" in r5.json["emojis"]






