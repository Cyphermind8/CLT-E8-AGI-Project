import asyncio
import websockets
import json

LOG_STORAGE = []

async def log_server(websocket, path):
    """Handle incoming WebSocket connections and store logs."""
    async for message in websocket:
        log_entry = json.loads(message)
        LOG_STORAGE.append(log_entry)
        print(f"📥 AI Log Received: {log_entry}")

async def main():
    """Start WebSocket server without blocking the event loop."""
    server = await websockets.serve(log_server, "localhost", 8765)
    await server.wait_closed()

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
