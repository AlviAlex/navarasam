"""Flask and Flask-SocketIO entry point for Emojify Real-Time Chat & Translator."""

from flask import Flask, jsonify, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room

from ai_provider import AIProviderError
from config import Config
from gemini_provider import GeminiProvider
from ollama_provider import OllamaProvider
from room_manager import RoomManager
from translator import TranslationService

room_manager = RoomManager()
socketio = SocketIO(cors_allowed_origins="*", async_mode="threading")


def create_app(provider=None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    if provider:
        active_provider = provider
    elif app.config.get("GEMINI_API_KEY"):
        active_provider = GeminiProvider(
            app.config["GEMINI_API_KEY"],
            app.config["GEMINI_MODEL"],
            app.config["GEMINI_TIMEOUT_SECONDS"],
        )
    else:
        # Automatically use local Ollama cognitive model
        active_provider = OllamaProvider(
            app.config["OLLAMA_BASE_URL"],
            app.config.get("OLLAMA_MODEL", "qwen3:8b"),
            app.config["OLLAMA_TIMEOUT_SECONDS"],
        )

    service = TranslationService(active_provider, app.config["MAX_INPUT_LENGTH"], app.config["MAX_CONCEPTS"])
    app.translation_service = service
    socketio.init_app(app)

    def _get_lan_ip():
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    @app.get("/")
    def index():
        provider_badge = "Gemini Flash" if app.config.get("AI_PROVIDER") != "ollama" else "Local Ollama"
        return render_template(
            "landing.html",
            max_length=app.config["MAX_INPUT_LENGTH"],
            provider_badge=provider_badge,
            network_ip=_get_lan_ip(),
        )

    @app.get("/app")
    def app_page():
        provider_badge = "Gemini Flash" if app.config.get("AI_PROVIDER") != "ollama" else "Local Ollama"
        return render_template(
            "index.html",
            max_length=app.config["MAX_INPUT_LENGTH"],
            provider_badge=provider_badge,
            initial_room_id="",
            network_ip=_get_lan_ip(),
        )

    @app.get("/room/<room_id>")
    def room_page(room_id):
        provider_badge = "Gemini Flash" if app.config.get("AI_PROVIDER") != "ollama" else "Local Ollama"
        return render_template(
            "index.html",
            max_length=app.config["MAX_INPUT_LENGTH"],
            provider_badge=provider_badge,
            initial_room_id=room_id.strip().lower(),
            network_ip=_get_lan_ip(),
        )

    @app.get("/api/network-info")
    def get_network_info():
        import socket
        local_ip = "127.0.0.1"
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except Exception:
            pass
        return jsonify({"local_ip": local_ip, "port": 5000})

    @app.post("/api/rooms")
    def create_new_room():
        data = request.get_json(silent=True) or {}
        custom_id = data.get("room_id")
        created_id = room_manager.create_room(custom_id)
        return jsonify({"room_id": created_id, "url": f"/room/{created_id}"})

    @app.get("/api/rooms/<room_id>")
    def get_room_status(room_id):
        room = room_manager.get_room(room_id)
        if not room:
            return jsonify({"exists": False, "participant_count": 0}), 404
        return jsonify({
            "exists": True,
            "room_id": room_id,
            "participant_count": len(room["participants"]),
            "messages": room["messages"],
        })

    @app.get("/api/lut")
    def get_lut():
        return jsonify(service.lut_service.get_all_entries())

    @app.post("/api/translate")
    def translate():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify(error="Send a valid request and try again."), 400
        try:
            output = service.translate(data.get("text"))
            return jsonify(output)
        except ValueError as exc:
            return jsonify(error=str(exc)), 400
        except AIProviderError as exc:
            return jsonify(error=str(exc)), 503
        except Exception:
            app.logger.exception("Unexpected translation failure")
            return jsonify(error="Something unexpected happened. Please try again."), 500

    # ---------------- WebSocket Events ----------------
    @socketio.on("join_room")
    def handle_join(data):
        room_id = (data.get("room_id") or "").strip().lower()
        if not room_id:
            emit("error", {"message": "Invalid room ID."})
            return

        sid = request.sid
        room_manager.join_room(room_id, sid)
        join_room(room_id)
        room = room_manager.get_room(room_id)
        count = len(room["participants"]) if room else 1

        emit("room_joined", {
            "room_id": room_id,
            "participant_count": count,
            "messages": room["messages"] if room else [],
        })
        emit("peer_joined", {"participant_count": count}, to=room_id, include_self=False)

    @socketio.on("send_message")
    def handle_send_message(data):
        room_id = (data.get("room_id") or "").strip().lower()
        text = (data.get("text") or "").strip()
        if not room_id or not text:
            emit("error", {"message": "Empty message or missing room."})
            return

        sid = request.sid
        try:
            translated = service.translate(text)
            msg = room_manager.add_message(
                room_id=room_id,
                sender_sid=sid,
                original_text=text,
                emojis=translated["emojis"],
                concepts=translated.get("concepts", []),
                emotion=translated.get("emotion"),
                explanation=translated.get("explanation", ""),
            )

            # Sender receives their raw text + translated emojis
            emit("message_sent", {
                "id": msg["id"],
                "is_self": True,
                "original_text": text,
                "emojis": translated["emojis"],
                "concepts": translated.get("concepts", []),
                "emotion": translated.get("emotion"),
                "timestamp": msg["timestamp"],
            })

            # Receiver in the room receives ONLY the translated emojis!
            emit("message_received", {
                "id": msg["id"],
                "is_self": False,
                "emojis": translated["emojis"],
                "concepts": translated.get("concepts", []),
                "emotion": translated.get("emotion"),
                "timestamp": msg["timestamp"],
            }, to=room_id, include_self=False)

        except Exception as exc:
            emit("error", {"message": str(exc)})

    @socketio.on("disconnect")
    def handle_disconnect():
        sid = request.sid
        affected_rooms = room_manager.remove_sid(sid)
        for r_id in affected_rooms:
            room = room_manager.get_room(r_id)
            count = len(room["participants"]) if room else 0
            emit("peer_left", {"participant_count": count}, to=r_id)

    return app


if __name__ == "__main__":
    app_instance = create_app()
    socketio.run(app_instance, host="0.0.0.0", port=5000, debug=False, allow_unsafe_werkzeug=True)
