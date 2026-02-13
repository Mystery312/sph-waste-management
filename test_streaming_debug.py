"""
Simple WebSocket client to test streaming connection.
Run this while unity_streaming_main.py is running to diagnose broadcast issues.
"""

import asyncio
import websockets
import json
import zlib

async def test_connection():
    uri = "ws://localhost:8765"
    print(f"Connecting to {uri}...")

    try:
        async with websockets.connect(uri) as websocket:
            print(f"✓ Connected to {uri}")

            # Request config
            await websocket.send(json.dumps({"command": "get_config"}))
            config_msg = await websocket.recv()
            print(f"✓ Received config: {config_msg[:100]}...")

            # Try to receive data frames
            print("\nWaiting for data frames (timeout: 5 seconds)...")
            frame_count = 0
            start_time = asyncio.get_event_loop().time()

            try:
                while asyncio.get_event_loop().time() - start_time < 5.0:
                    data = await asyncio.wait_for(websocket.recv(), timeout=0.5)
                    frame_count += 1

                    # Try to parse the message
                    try:
                        if isinstance(data, str):
                            if data.startswith('C'):
                                # Compressed message
                                hex_data = data[1:]
                                compressed = bytes.fromhex(hex_data)
                                decompressed = zlib.decompress(compressed).decode('utf-8')
                                msg = json.loads(decompressed)
                            else:
                                msg = json.loads(data)

                            if msg.get('type') == 'simulation_data':
                                print(f"✓ Frame {frame_count}: step={msg.get('step')}, "
                                      f"particles={msg.get('particle_count')}, "
                                      f"time={msg.get('time'):.3f}s")
                        else:
                            print(f"✓ Frame {frame_count}: Received {len(data)} bytes (binary)")
                    except json.JSONDecodeError as e:
                        print(f"✗ Frame {frame_count}: Failed to parse JSON: {e}")

            except asyncio.TimeoutError:
                pass

            if frame_count == 0:
                print("✗ No frames received! This indicates the broadcast bug.")
                print("  The server might not be calling broadcast_data() or")
                print("  websockets.broadcast() might not be working properly.")
            else:
                print(f"\n✓ Successfully received {frame_count} frames!")

    except ConnectionRefusedError:
        print(f"✗ Connection refused. Is the server running on {uri}?")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_connection())
