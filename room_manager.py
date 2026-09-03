"""Room and session management for 2-person real-time emoji chat rooms."""

import time
import uuid
from typing import Any, Dict, List, Optional


class RoomManager:
    def __init__(self, room_ttl_seconds: int = 3600) -> None:
        self.rooms: Dict[str, Dict[str, Any]] = {}
        self.room_ttl_seconds = room_ttl_seconds

    def create_room(self, custom_id: Optional[str] = None) -> str:
        """Create a new chat room and return its room_id."""
        room_id = custom_id.strip().lower() if custom_id else uuid.uuid4().hex[:8]
        now = time.time()
        self.rooms[room_id] = {
            "room_id": room_id,
            "created_at": now,
            "last_active": now,
            "participants": set(),  # Set of socket IDs
            "messages": [],
        }
        return room_id

    def get_room(self, room_id: str) -> Optional[Dict[str, Any]]:
        """Get room data if it exists and has not expired."""
        room = self.rooms.get(room_id.strip().lower())
        if not room:
            return None
        # Check TTL
        if time.time() - room["last_active"] > self.room_ttl_seconds:
            self.remove_room(room_id)
            return None
        return room

    def join_room(self, room_id: str, sid: str) -> bool:
        """Add a socket participant to a room. Max 2 active chatters per room."""
        room = self.get_room(room_id)
        if not room:
            self.create_room(room_id)
            room = self.get_room(room_id)

        room["participants"].add(sid)
        room["last_active"] = time.time()
        return True

    def leave_room(self, room_id: str, sid: str) -> int:
        """Remove a participant from a room and return remaining participant count."""
        room = self.rooms.get(room_id.strip().lower())
        if not room:
            return 0
        room["participants"].discard(sid)
        room["last_active"] = time.time()
        return len(room["participants"])

    def remove_sid(self, sid: str) -> List[str]:
        """Remove a disconnected socket ID from all rooms and return affected room IDs."""
        affected = []
        for room_id, room in list(self.rooms.items()):
            if sid in room["participants"]:
                room["participants"].discard(sid)
                room["last_active"] = time.time()
                affected.append(room_id)
        return affected

    def add_message(self, room_id: str, sender_sid: str, original_text: str, emojis: str, concepts: list, emotion: Optional[str], explanation: str) -> Dict[str, Any]:
        """Record a translated message in the room history."""
        room = self.get_room(room_id)
        if not room:
            raise ValueError("Room does not exist.")

        msg = {
            "id": uuid.uuid4().hex[:10],
            "room_id": room_id,
            "sender_sid": sender_sid,
            "original_text": original_text,
            "emojis": emojis,
            "concepts": concepts,
            "emotion": emotion,
            "explanation": explanation,
            "timestamp": time.time(),
        }
        room["messages"].append(msg)
        room["last_active"] = time.time()
        # Keep last 50 messages per room
        if len(room["messages"]) > 50:
            room["messages"].pop(0)
        return msg

    def remove_room(self, room_id: str) -> None:
        """Delete a room from active memory."""
        self.rooms.pop(room_id.strip().lower(), None)
