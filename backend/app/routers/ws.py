"""WebSocket endpoint for live presence + content sync on a document."""
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from .. import models
from ..core import config
from ..core.database import SessionLocal
from ..deps import resolve_role, user_from_token
from ..realtime import manager

router = APIRouter()


@router.websocket("/ws/documents/{document_id}")
async def ws_document(
    websocket: WebSocket, document_id: int, token: str | None = Query(default=None)
):
    # Authenticate + authorize with a short-lived session (JWT via query or cookie).
    db = SessionLocal()
    try:
        raw = token or websocket.cookies.get(config.COOKIE_NAME)
        user = user_from_token(raw, db)
        if user is None:
            await websocket.close(code=4401)
            return
        document = db.get(models.Document, document_id)
        if document is None:
            await websocket.close(code=4404)
            return
        role = resolve_role(db, document, user)
        if role is None:
            await websocket.close(code=4403)
            return
        user_info = {"id": user.id, "name": user.name, "role": role}
    finally:
        db.close()

    await websocket.accept()
    client_id = await manager.join(document_id, websocket, user_info)
    await _announce(document_id)
    try:
        while True:
            data = await websocket.receive_json()
            # Only editors/owners may push content; viewers are receive-only.
            if data.get("type") == "update" and role != "viewer":
                await manager.broadcast(
                    document_id,
                    {"type": "update", "html": data.get("html", ""), "from": user_info["id"]},
                    exclude=client_id,
                )
    except WebSocketDisconnect:
        pass
    finally:
        await manager.leave(document_id, client_id)
        await _announce(document_id)


async def _announce(document_id: int) -> None:
    await manager.broadcast(
        document_id, {"type": "presence", "users": manager.presence(document_id)}
    )
