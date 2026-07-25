"""In-memory WebSocket room manager for per-document presence and live sync.

Single-process (fits the single-service deploy). Each document is a "room"; every
open editor is a connection. We broadcast presence changes and relay content
updates between participants. Persistence still flows through the REST autosave —
this layer only propagates live state.
"""
import asyncio

from fastapi import WebSocket


class RealtimeManager:
    def __init__(self) -> None:
        self._rooms: dict[int, dict[int, tuple[WebSocket, dict]]] = {}
        self._counter = 0
        self._lock = asyncio.Lock()

    async def join(self, document_id: int, ws: WebSocket, user: dict) -> int:
        async with self._lock:
            self._counter += 1
            client_id = self._counter
            self._rooms.setdefault(document_id, {})[client_id] = (ws, user)
        return client_id

    async def leave(self, document_id: int, client_id: int) -> None:
        async with self._lock:
            room = self._rooms.get(document_id)
            if room and client_id in room:
                del room[client_id]
                if not room:
                    self._rooms.pop(document_id, None)

    def presence(self, document_id: int) -> list[dict]:
        """Unique users currently in the room (one entry per user)."""
        room = self._rooms.get(document_id, {})
        by_user: dict[int, dict] = {}
        for _ws, user in room.values():
            by_user[user["id"]] = user
        return list(by_user.values())

    async def broadcast(self, document_id: int, message: dict, exclude: int | None = None) -> None:
        room = dict(self._rooms.get(document_id, {}))
        dead: list[int] = []
        for client_id, (ws, _user) in room.items():
            if client_id == exclude:
                continue
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(client_id)
        for client_id in dead:
            await self.leave(document_id, client_id)


manager = RealtimeManager()
