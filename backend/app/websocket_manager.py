import logging
import json
from typing import List
from fastapi import WebSocket

logger = logging.getLogger("backend.websocket")

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Remaining active connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.warning(f"Error sending message to WebSocket client: {e}")
            self.disconnect(websocket)

    async def broadcast_json(self, data: dict):
        if not self.active_connections:
            return
        
        message = json.dumps(data)
        logger.info(f"Broadcasting alert via WebSocket to {len(self.active_connections)} client(s)...")
        
        disconnected_clients = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning(f"Failed to broadcast message to connection, marking for disconnect: {e}")
                disconnected_clients.append(connection)
                
        for dead_client in disconnected_clients:
            self.disconnect(dead_client)

manager = ConnectionManager()
