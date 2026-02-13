#!/usr/bin/env python3
"""Minimal test - server sends one message when client connects."""

import asyncio
import websockets
import json

async def handler(websocket):
    """Handle incoming WebSocket connection."""
    print("[Server] Client connected")
    message = json.dumps({
        "type": "test",
        "data": "Hello from server!"
    })
    await websocket.send(message)
    print("[Server] Message sent")
    await websocket.wait_closed()

async def run_server():
    """Run minimal server."""
    print("[Server] Starting on localhost:9876...")
    async with websockets.serve(handler, "localhost", 9876):
        print("[Server] Waiting for connections...")
        await asyncio.Future()  # Run forever

async def test_client():
    """Test client."""
    print("[Client] Connecting to ws://localhost:9876...")
    try:
        async with websockets.connect("ws://localhost:9876") as websocket:
            print("[Client] Connected")
            message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
            print(f"[Client] Received: {message}")
            return True
    except asyncio.TimeoutError:
        print("[Client] Timeout waiting for message")
        return False
    except Exception as e:
        print(f"[Client] Error: {e}")
        return False

async def main():
    """Run server and test."""
    # Start server in background
    server_task = asyncio.create_task(run_server())

    # Give server time to start
    await asyncio.sleep(1)

    # Run test client
    result = await test_client()

    # Cancel server
    server_task.cancel()
    try:
        await server_task
    except asyncio.CancelledError:
        pass

    print(f"\n{'✓' if result else '✗'} Test {'passed' if result else 'failed'}")
    return result

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
