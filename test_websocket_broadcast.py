"""
Direct test of WebSocket broadcast fix without full simulation.
Tests the broadcast mechanism in isolation.
"""

import asyncio
import websockets
import json
import zlib
import numpy as np
from sph_fluid_sim.network.websocket_server import SimulationDataServer


async def test_broadcast():
    """Test the broadcast fix directly."""
    print("Testing WebSocket broadcast fix...")
    print("=" * 80)

    # Create server
    server = SimulationDataServer(host="localhost", port=8765)

    # Create dummy data
    num_particles = 100
    positions = np.random.rand(num_particles, 3)
    velocities = np.random.rand(num_particles, 3)
    densities = np.ones(num_particles) * 1000.0
    pressures = np.random.rand(num_particles) * 1000.0
    concentrations = np.random.rand(num_particles)

    # Update server with dummy data
    server.update_simulation_data(
        time=0.0,
        step=0,
        positions=positions,
        velocities=velocities,
        densities=densities,
        pressures=pressures,
        concentrations=concentrations,
        metrics={'test': 'data'}
    )

    # Start server in background
    print("Starting WebSocket server...")
    server_task = asyncio.create_task(server.start_server())
    await asyncio.sleep(0.5)  # Give server time to start

    # Connect a test client
    print("Connecting test client...")
    uri = "ws://localhost:8765"
    frames_received = 0

    try:
        async with websockets.connect(uri) as websocket:
            print(f"✓ Connected to {uri}")

            # Send multiple frames
            for frame_num in range(5):
                # Update data
                server.update_simulation_data(
                    time=frame_num * 0.01,
                    step=frame_num,
                    positions=positions + frame_num * 0.001,
                    velocities=velocities,
                    densities=densities,
                    pressures=pressures,
                    concentrations=concentrations,
                    metrics={'frame': frame_num}
                )

                # Broadcast the frame
                print(f"Broadcasting frame {frame_num}...")
                await server.broadcast_data()

                # Try to receive
                try:
                    data = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    frames_received += 1

                    # Parse message
                    if isinstance(data, str):
                        if data.startswith('C'):
                            # Compressed
                            hex_data = data[1:]
                            compressed = bytes.fromhex(hex_data)
                            decompressed = zlib.decompress(compressed).decode('utf-8')
                            msg = json.loads(decompressed)
                        else:
                            msg = json.loads(data)

                        print(f"✓ Frame {frame_num}: {msg.get('type')}, "
                              f"step={msg.get('step')}, "
                              f"particles={msg.get('particle_count')}")
                    else:
                        print(f"✓ Frame {frame_num}: Received {len(data)} bytes (binary)")

                except asyncio.TimeoutError:
                    print(f"✗ Frame {frame_num}: Timeout waiting for data")

                await asyncio.sleep(0.1)

        print("\n" + "=" * 80)
        if frames_received > 0:
            print(f"✓ SUCCESS: Received {frames_received}/5 frames!")
            print("The broadcast fix is working correctly.")
        else:
            print("✗ FAILURE: No frames received!")
            print("The broadcast mechanism is still broken.")
        print("=" * 80)

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Cleanup
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    asyncio.run(test_broadcast())
