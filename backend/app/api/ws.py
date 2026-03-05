from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict
import asyncio
import redis.asyncio as redis
import os

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
