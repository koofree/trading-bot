import json
import logging
from typing import Any, Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(tags=["websocket"])
logger = logging.getLogger(__name__)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time updates"""
    from api.main import manager, trading_system

    await manager.connect(websocket)

    try:
        while True:
            data = await websocket.receive_text()

            # Parse and handle WebSocket messages
            try:
                message = json.loads(data)
                await handle_websocket_message(message, websocket, trading_system)
            except json.JSONDecodeError:
                await websocket.send_text(
                    json.dumps({"type": "error", "message": "Invalid JSON"})
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def handle_websocket_message(
    message: Dict[str, Any], websocket: WebSocket, trading_system: Any
) -> None:
    """Handle incoming WebSocket messages"""
    msg_type = message.get("type")

    if msg_type == "subscribe":
        markets = message.get("markets", [])
        if markets:
            trading_system.monitored_markets = markets
            await websocket.send_text(
                json.dumps({"type": "subscribed", "markets": markets})
            )

    elif msg_type == "execute_trade":
        signal_data = message.get("signal")
        if signal_data:
            # Convert to TradingSignal object
            # Implementation depends on signal structure
            pass
