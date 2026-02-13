#!/usr/bin/env python3
"""
End-to-End Test of WebSocket Streaming Pipeline

This script:
1. Starts the streaming simulation (Python backend)
2. Connects a test client (simulating Unity)
3. Verifies data streaming works correctly
4. Logs performance metrics

Run with: python test_streaming_e2e.py
"""

import asyncio
import websockets
import json
import zlib
import time
import threading
from sph_fluid_sim.config import NUM_PARTICLES
import taichi as ti


async def run_test_client(duration=10):
    """
    Connect to WebSocket server and log received frames.

    Args:
        duration: How long to listen (seconds)

    Returns:
        Dictionary with test results
    """
    uri = "ws://localhost:8765"
    results = {
        'connected': False,
        'frames_received': 0,
        'total_bytes': 0,
        'errors': []
    }

    try:
        # Wait for server to start
        await asyncio.sleep(2)

        print("\n" + "=" * 80)
        print("TEST CLIENT: Connecting to WebSocket server...")
        print("=" * 80)

        async with websockets.connect(uri) as websocket:
            results['connected'] = True
            print(f"✓ Connected to {uri}")

            # Request config
            await websocket.send(json.dumps({"command": "get_config"}))
            config_msg = await websocket.recv()
            config = json.loads(config_msg)
            print(f"✓ Server config: compression={config['data']['compression']}, "
                  f"decimation={config['data']['decimation_factor']}")

            # Receive frames for specified duration
            start_time = time.time()
            frame_times = []

            print(f"\nListening for frames for {duration} seconds...")
            while time.time() - start_time < duration:
                try:
                    # Wait for data with timeout
                    data = await asyncio.wait_for(websocket.recv(), timeout=1.0)

                    frame_time = time.time() - start_time
                    frame_times.append(frame_time)
                    results['frames_received'] += 1
                    results['total_bytes'] += len(data) if isinstance(data, bytes) else len(data.encode())

                    # Parse first few frames in detail
                    if results['frames_received'] <= 3:
                        try:
                            if isinstance(data, str):
                                if data.startswith('C'):
                                    # Compressed JSON
                                    hex_data = data[1:]
                                    compressed = bytes.fromhex(hex_data)
                                    decompressed = zlib.decompress(compressed).decode('utf-8')
                                    msg = json.loads(decompressed)
                                else:
                                    msg = json.loads(data)

                                print(f"✓ Frame {results['frames_received']}: "
                                      f"time={msg.get('time'):.3f}s, step={msg.get('step')}, "
                                      f"particles={msg.get('particle_count')}")
                        except Exception as e:
                            print(f"✗ Frame {results['frames_received']}: Failed to parse: {e}")
                            results['errors'].append(str(e))

                except asyncio.TimeoutError:
                    # No frame received in 1 second
                    pass

    except ConnectionRefusedError:
        results['errors'].append(f"Connection refused: Is server running on {uri}?")
        print(f"✗ Connection refused on {uri}")
    except Exception as e:
        results['errors'].append(str(e))
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

    return results


def run_streaming_simulation(duration=10):
    """
    Run the streaming simulation for the specified duration.

    Args:
        duration: Simulation duration (seconds)
    """
    # Import here to avoid issues if called in background
    from unity_streaming_main import StreamingSimulation

    print("\n" + "=" * 80)
    print("STREAMING SIMULATION: Starting Phase 3 test")
    print("=" * 80)

    # Initialize Taichi on CPU for this test
    try:
        ti.init(arch=ti.cuda)
    except:
        print("CUDA not available, using CPU")
        ti.init(arch=ti.cpu)

    # Create simulation
    sim = StreamingSimulation(
        num_particles=min(NUM_PARTICLES, 2000),  # Use fewer particles for quick test
        host="localhost",
        port=8765,
        broadcast_fps=30
    )

    # Start WebSocket server
    sim.start_server()
    time.sleep(1)  # Give server time to start

    # Run simulation
    print(f"\nStarting simulation (duration={duration}s, {sim.num_particles} particles)...")
    print(f"Broadcasting at {sim.broadcast_fps} FPS")

    sim.run(target_time=duration, export_vtk=False)

    print("\nSimulation completed!")


async def main():
    """Run end-to-end test."""
    print("\n" + "=" * 80)
    print("END-TO-END STREAMING TEST")
    print("=" * 80)

    # Start simulation in background thread
    sim_thread = threading.Thread(
        target=run_streaming_simulation,
        args=(15,),  # 15 second simulation
        daemon=True
    )
    sim_thread.start()

    # Run test client
    results = await run_test_client(duration=12)

    # Print results
    print("\n" + "=" * 80)
    print("TEST RESULTS")
    print("=" * 80)
    print(f"Connected: {results['connected']}")
    print(f"Frames received: {results['frames_received']}")
    print(f"Total bytes received: {results['total_bytes']:,}")

    if results['frames_received'] > 0:
        print(f"Average bytes per frame: {results['total_bytes'] / results['frames_received']:.0f}")
        avg_fps = results['frames_received'] / 12.0
        print(f"Effective FPS: {avg_fps:.1f}")

    if results['errors']:
        print(f"\nErrors encountered:")
        for error in results['errors']:
            print(f"  - {error}")

    print("\n" + "=" * 80)
    if results['connected'] and results['frames_received'] > 5:
        print("✓ TEST PASSED: WebSocket streaming is working!")
        print("The fix resolved the broadcasting bug.")
    else:
        print("✗ TEST FAILED: Insufficient frames received")
    print("=" * 80 + "\n")

    # Wait for simulation thread to finish
    sim_thread.join(timeout=20)


if __name__ == "__main__":
    asyncio.run(main())
