"""Comprehensive Whitebox Testing Suite for Emojify.

Covers internal branch logic, edge cases, error handlers, boundary conditions,
and state machines across all modules:
- emoji_pack.py
- emoji_lut.py
- room_manager.py
- gemini_provider.py
- ollama_provider.py
- translator.py
- app.py (REST & Socket.IO WebSockets)
"""

import io
import json
import time
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

import pytest

import emoji_lut
import emoji_pack
from ai_provider import AIProvider, AIProviderError
from app import create_app, socketio
from config import Config
from emoji_lut import LUTService
from gemini_provider import GeminiProvider
from ollama_provider import OllamaProvider
from room_manager import RoomManager
from translator import TranslationService


# ============================================================================
# 1. WHITEBOX TESTS: emoji_pack.py
# ============================================================================
class TestEmojiPackWhitebox:
    def test_parse_ttf_missing_file(self):
        cps = emoji_pack._parse_ttf_cmap_codepoints("non_existent_font.ttf")
        assert cps == set()

    def test_parse_ttf_corrupt_file(self, tmp_path):
        bad_file = tmp_path / "corrupt.ttf"
        bad_file.write_bytes(b"short")
        cps = emoji_pack._parse_ttf_cmap_codepoints(str(bad_file))
        assert cps == set()

    def test_get_supported_codepoints_cached(self):
        cps = emoji_pack.get_supported_codepoints()
        assert len(cps) > 1000
        # Codepoints of standard emojis
        assert ord("🍕") in cps
        assert ord("☕") in cps

    def test_is_emoji_supported_variations(self):
        assert emoji_pack.is_emoji_supported("🍕")
        assert emoji_pack.is_emoji_supported("☕")
        assert emoji_pack.is_emoji_supported("🏖️")  # with variation selector
        assert emoji_pack.is_emoji_supported("🧑‍🤝‍🧑")  # with ZWJ
        assert emoji_pack.is_emoji_supported("   ")  # whitespace allowed

    def test_filter_supported_emojis(self):
        filtered = emoji_pack.filter_supported_emojis("🍕 ☕")
        assert "🍕" in filtered and "☕" in filtered


# ============================================================================
# 2. WHITEBOX TESTS: emoji_lut.py
# ============================================================================
class TestEmojiLUTWhitebox:
    @pytest.fixture
    def lut(self):
        return LUTService()

    def test_lut_initialization_and_counts(self, lut):
        entries = lut.get_all_entries()
        assert len(entries) >= 1000
        assert len(lut.keyword_index) > 500

    def test_lru_cache_hit_and_eviction(self, lut):
        lut.cache_limit = 2
        lut.put_cache("test1", {"emojis": "🍕"})
        lut.put_cache("test2", {"emojis": "☕"})
        assert lut.get_cached("test1")["emojis"] == "🍕"
        # Adding a 3rd should evict test2 (since test1 was accessed recently)
        lut.put_cache("test3", {"emojis": "🏖️"})
        assert lut.get_cached("test2") is None
        assert lut.get_cached("test1") is not None
        assert lut.get_cached("test3") is not None

    def test_exact_phrase_lookup_variations(self, lut):
        res1 = lut.lookup("i love pizza")
        assert res1 is not None and res1["emojis"] == "🍕 ❤️"

        res2 = lut.lookup("where is the pizza?")
        assert res2 is not None and "❓" in res2["emojis"]

        res3 = lut.lookup("stop the car right now!")
        assert res3 is not None and "❗" in res3["emojis"]

        res4 = lut.lookup("i love pizza?!")
        assert res4 is not None and "⁉️" in res4["emojis"]

    def test_single_word_lookup(self, lut):
        res = lut.lookup("coffee")
        assert res is not None and "☕" in res["emojis"]

        res_q = lut.lookup("coffee?")
        assert res_q is not None and "❓" in res_q["emojis"]

    def test_ngram_and_negation_extraction(self, lut):
        res = lut.lookup("i do not want coffee")
        assert res is not None
        assert "☕" in res["emojis"]
        assert "🚫" in res["emojis"]

    def test_unmatched_returns_none(self, lut):
        res = lut.lookup("The epistemological dichotomy oscillates infinitely")
        assert res is None


# ============================================================================
# 3. WHITEBOX TESTS: room_manager.py
# ============================================================================
class TestRoomManagerWhitebox:
    @pytest.fixture
    def rm(self):
        return RoomManager(room_ttl_seconds=10)

    def test_room_lifecycle_and_ttl(self, rm):
        r_id = rm.create_room("my_room")
        assert r_id == "my_room"
        assert rm.get_room("my_room") is not None

        # Expire room manually
        rm.rooms["my_room"]["last_active"] = time.time() - 20
        assert rm.get_room("my_room") is None

    def test_join_leave_and_disconnect_cleanup(self, rm):
        rm.join_room("room_a", "sid_1")
        rm.join_room("room_b", "sid_1")
        rm.join_room("room_a", "sid_2")

        assert len(rm.get_room("room_a")["participants"]) == 2
        remaining = rm.leave_room("room_a", "sid_2")
        assert remaining == 1

        # Remove socket from all rooms on disconnect
        affected = rm.remove_sid("sid_1")
        assert "room_a" in affected and "room_b" in affected
        assert len(rm.get_room("room_a")["participants"]) == 0

    def test_message_history_bounds(self, rm):
        rm.create_room("chat_room")
        for i in range(55):
            rm.add_message("chat_room", "sid_1", f"text_{i}", f"emoji_{i}", [], None, "exp")

        room = rm.get_room("chat_room")
        # Max history should be capped at 50
        assert len(room["messages"]) == 50
        assert room["messages"][-1]["original_text"] == "text_54"

    def test_add_message_invalid_room_raises(self, rm):
        with pytest.raises(ValueError):
            rm.add_message("ghost_room", "sid_1", "hi", "👋", [], None, "")


# ============================================================================
# 4. WHITEBOX TESTS: gemini_provider.py
# ============================================================================
class TestGeminiProviderWhitebox:
    def test_missing_api_key(self):
        provider = GeminiProvider(api_key="")
        with pytest.raises(AIProviderError) as exc:
            provider.chat([{"role": "user", "content": "hi"}], {})
        assert "Gemini API key is missing" in str(exc.value)

    @patch("gemini_provider.urlopen")
    def test_successful_chat_with_markdown_strip(self, mock_urlopen):
        raw_json = json.dumps({
            "candidates": [{
                "content": {
                    "parts": [{"text": "```json\n{\"emojis\": \"🍕\", \"concepts\": [], \"emotion\": null, \"explanation\": \"pizza\"}\n```"}]
                }
            }]
        }).encode("utf-8")

        mock_resp = MagicMock()
        mock_resp.read.return_value = raw_json
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        provider = GeminiProvider(api_key="dummy_key")
        result = provider.chat([
            {"role": "system", "content": "system instruction"},
            {"role": "user", "content": "hello"}
        ], {})
        assert result["emojis"] == "🍕"

    @patch("gemini_provider.urlopen")
    def test_http_error_handling(self, mock_urlopen):
        # 400 Error
        err_stream = io.BytesIO(json.dumps({"error": {"message": "Bad API Key"}}).encode("utf-8"))
        mock_urlopen.side_effect = HTTPError("url", 400, "Bad Request", {}, err_stream)

        provider = GeminiProvider(api_key="bad_key")
        with pytest.raises(AIProviderError) as exc:
            provider.chat([{"role": "user", "content": "hi"}], {})
        assert "Gemini API error (400)" in str(exc.value)

    @patch("gemini_provider.urlopen")
    def test_network_and_malformed_json_errors(self, mock_urlopen):
        mock_urlopen.side_effect = URLError("DNS Failed")
        provider = GeminiProvider(api_key="key")
        with pytest.raises(AIProviderError) as exc:
            provider.chat([{"role": "user", "content": "hi"}], {})
        assert "Could not reach Google Gemini API" in str(exc.value)


# ============================================================================
# 5. WHITEBOX TESTS: ollama_provider.py
# ============================================================================
class TestOllamaProviderWhitebox:
    @patch("ollama_provider.urlopen")
    def test_successful_chat(self, mock_urlopen):
        raw_json = json.dumps({
            "message": {
                "content": "{\"emojis\": \"☕ 🚫\", \"concepts\": [], \"emotion\": null, \"explanation\": \"coffee dislike\"}"
            }
        }).encode("utf-8")

        mock_resp = MagicMock()
        mock_resp.read.return_value = raw_json
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        provider = OllamaProvider("http://localhost:11434", "qwen3:4b-instruct", 30)
        result = provider.chat([{"role": "user", "content": "I don't like coffee"}], {})
        assert result["emojis"] == "☕ 🚫"

    @patch("ollama_provider.urlopen")
    def test_ollama_unavailable(self, mock_urlopen):
        mock_urlopen.side_effect = URLError("Connection refused")
        provider = OllamaProvider("http://localhost:11434", "qwen3:4b-instruct", 30)
        with pytest.raises(AIProviderError) as exc:
            provider.chat([{"role": "user", "content": "hi"}], {})
        assert "Ollama is not available" in str(exc.value)


# ============================================================================
# 6. WHITEBOX TESTS: translator.py
# ============================================================================
class TestTranslatorWhitebox:
    class DummyProvider(AIProvider):
        def __init__(self, output=None):
            self.output = output or {"emojis": "🍕 ❤️", "concepts": [{"name": "pizza", "emoji": "🍕"}], "emotion": "love", "explanation": "test"}

        def chat(self, messages, schema):
            return self.output

    def test_input_validation(self):
        svc = TranslationService(self.DummyProvider(), max_input_length=10)
        with pytest.raises(ValueError) as exc1:
            svc.translate("")
        assert "Write something first" in str(exc1.value)

        with pytest.raises(ValueError) as exc2:
            svc.translate("a" * 15)
        assert "Keep it under 10 characters" in str(exc2.value)

    def test_lut_cache_bypass(self):
        provider = MagicMock()
        svc = TranslationService(provider)
        res = svc.translate("i love pizza")
        assert res["emojis"] == "🍕 ❤️"
        # Provider should NOT have been called
        provider.chat.assert_not_called()

    def test_invalid_model_response_handling(self):
        svc = TranslationService(self.DummyProvider())
        # Missing emojis
        with pytest.raises(AIProviderError) as exc:
            svc._validate_result({"emojis": "no emojis here", "concepts": [], "emotion": None, "explanation": "x"})
        assert "did not return emojis" in str(exc.value)

        # Invalid concepts format
        with pytest.raises(AIProviderError):
            svc._validate_result({"emojis": "🍕", "concepts": "not a list", "emotion": None, "explanation": "x"})

        # Long emotion trimming and default explanation
        res = svc._validate_result({"emojis": "🍕", "concepts": [{"name": "pizza", "emoji": "🍕"}], "emotion": "x" * 100, "explanation": 123})
        assert res["emotion"] is None
        assert "A local AI" in res["explanation"]



# ============================================================================
# 7. WHITEBOX TESTS: app.py REST & WebSockets
# ============================================================================
class TestAppWhitebox:
    @pytest.fixture
    def app(self):
        fake_provider = TestTranslatorWhitebox.DummyProvider()
        return create_app(fake_provider)

    @pytest.fixture
    def client(self, app):
        return app.test_client()

    def test_routes(self, client):
        res = client.get("/")
        assert res.status_code == 200
        assert "Navarasam" in res.text

        # GET /room/testroom
        res_room = client.get("/room/testroom")
        assert res_room.status_code == 200
        assert res_room.status_code == 200

        # POST /api/rooms
        res_create = client.post("/api/rooms", json={"room_id": "alpha"})
        assert res_create.status_code == 200
        assert res_create.json["room_id"] == "alpha"

        # GET /api/rooms/alpha
        res_status = client.get("/api/rooms/alpha")
        assert res_status.status_code == 200
        assert res_status.json["exists"] is True

        # GET /api/rooms/missing
        res_missing = client.get("/api/rooms/missing")
        assert res_missing.status_code == 404

        # GET /api/lut
        res_lut = client.get("/api/lut")
        assert res_lut.status_code == 200
        assert len(res_lut.json) > 100

        # POST /api/translate valid
        res_t = client.post("/api/translate", json={"text": "pizza?"})
        assert res_t.status_code == 200
        assert res_t.json["emojis"] == "🍕 ❓"

        # POST /api/translate invalid payload
        res_invalid = client.post("/api/translate", data="not json", content_type="text/plain")
        assert res_invalid.status_code == 400

    def test_socketio_events(self, app):
        socketio_client = socketio.test_client(app)
        assert socketio_client.is_connected()

        # Join room
        socketio_client.emit("join_room", {"room_id": "lobby"})
        received = socketio_client.get_received()
        assert any(event["name"] == "room_joined" for event in received)

        # Send message
        socketio_client.emit("send_message", {"room_id": "lobby", "text": "hello pizza"})
        received_msg = socketio_client.get_received()
        assert any(event["name"] == "message_sent" for event in received_msg)

        socketio_client.disconnect()
