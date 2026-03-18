from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict
import asyncio
import redis.asyncio as redis
import os
import contextlib

router = APIRouter()

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

class ConnectionManager:
    def __init__(self):
        # Maps race_id to a list of active WebSocket connections
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Maps race_id to a boolean indicating if a Redis listener is already running
        self.listeners: Dict[str, bool] = {}

    async def connect(self, websocket: WebSocket, race_id: str):
        await websocket.accept()
        if race_id not in self.active_connections:
            self.active_connections[race_id] = []
        self.active_connections[race_id].append(websocket)
        
        # Start a Redis listener for this race_id if not already running
        if not self.listeners.get(race_id, False):
            self.listeners[race_id] = True
            asyncio.create_task(self.listen_to_redis(race_id))

    def disconnect(self, websocket: WebSocket, race_id: str):
        if race_id in self.active_connections:
            self.active_connections[race_id].remove(websocket)
            if len(self.active_connections[race_id]) == 0:
                del self.active_connections[race_id]
                self.listeners[race_id] = False

    async def broadcast(self, message: str, race_id: str):
        if race_id in self.active_connections:
            for connection in self.active_connections[race_id]:
                try:
                    await connection.send_text(message)
                except Exception:
                    # Ignore dead connections
                    pass

    async def listen_to_redis(self, race_id: str):
        """
        Background task: connects to Redis, subscribes to the channel, 
        and broadcasts messages continuously.
        """
        try:
            r = redis.from_url(REDIS_URL, decode_responses=True)
            async with r.pubsub() as pubsub:
                channel_name = f"race:{race_id}:live"
                await pubsub.subscribe(channel_name)
                print(f"[WebSocket] Subscribed to Redis channel: {channel_name}")
                
                async for message in pubsub.listen():
                    # Stop if no longer needed
                    if not self.listeners.get(race_id, False):
                        break

                    if message["type"] == "message":
                        data = message["data"]
                        await self.broadcast(data, race_id)
        except asyncio.CancelledError:
            print(f"[WebSocket] Redis listener for {race_id} cancelled.")
        except Exception as e:
            print(f"[WebSocket] Redis listener for {race_id} failed: {e}")
            self.listeners[race_id] = False


manager = ConnectionManager()


@router.websocket("/ws/race/{race_id}")
async def race_websocket(websocket: WebSocket, race_id: str):
    await manager.connect(websocket, race_id)
    try:
        while True:
            # We don't expect messages from the client in this one-way stream, 
            # but we need to keep the connection open and receive to detect disconnects.
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, race_id)


@router.websocket("/ws/race")
async def race_control_websocket(websocket: WebSocket):
    """
    Lightweight control socket kept for backwards compatibility with existing tests
    and clients that expect init/start/pause commands.
    """
    await websocket.accept()
    race_state = {
        "track_id": "monaco",
        "lap": 0,
        "speed": 1.0,
        "running": False,
    }
    update_task = None

    async def stream_updates():
        while race_state["running"]:
            race_state["lap"] += 1
            await websocket.send_json(
                {
                    "type": "update",
                    "track_id": race_state["track_id"],
                    "lap": race_state["lap"],
                }
            )
            interval = max(0.03, 0.2 / max(0.1, float(race_state["speed"])))
            await asyncio.sleep(interval)

    try:
        while True:
            payload = await websocket.receive_json()
            command = payload.get("command")

            if command == "init":
                race_state["track_id"] = payload.get("track_id", "monaco")
                race_state["lap"] = 0
                await websocket.send_json(
                    {"type": "init", "track_id": race_state["track_id"]}
                )
            elif command == "start":
                race_state["speed"] = float(payload.get("speed", 1.0) or 1.0)
                race_state["running"] = True
                if update_task is None or update_task.done():
                    update_task = asyncio.create_task(stream_updates())
            elif command == "pause":
                race_state["running"] = False
                if update_task and not update_task.done():
                    update_task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await update_task
                await websocket.send_json({"type": "paused", "lap": race_state["lap"]})
            else:
                await websocket.send_json(
                    {"type": "error", "message": f"Unknown command: {command}"}
                )
    except WebSocketDisconnect:
        pass
    finally:
        race_state["running"] = False
        if update_task and not update_task.done():
            update_task.cancel()
