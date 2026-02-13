"""
Test script for Minecraft WebSocket server.

This script tests the Python streaming server with various scenarios
and provides real-time feedback on data being sent to clients.
"""

import asyncio
import websockets
import json
import zlib
import time
from pathlib import Path


class MinecraftClientSimulator:
    """Simulates a Minecraft client connecting to the WebSocket server."""

    def __init__(self, host: str = "localhost", port: int = 8765):
        self.uri = f"ws://{host}:{port}"
        self.connected = False
        self.frames_received = 0
        self.last_frame_time = None
        self.fps = 0
        self.total_particles = 0
        self.total_bytes = 0

    async def connect(self):
        """Connect to WebSocket server."""
        try:
            self.websocket = await websockets.connect(self.uri)
            self.connected = True
            print(f"✓ Connected to {self.uri}\n")
            return True
        except Exception as e:
            print(f"✗ Failed to connect: {e}")
            print(f"  Make sure the server is running:")
            print(f"  python minecraft_streaming_main.py")
            return False

    async def receive_frames(self, duration: int = 10):
        """Receive and analyze frames for specified duration."""
        if not self.connected:
            return

        print(f"Receiving data for {duration} seconds...\n")
        print("="*80)
        print("FRAME ANALYSIS")
        print("="*80)

        start_time = time.time()
        last_stats_time = start_time

        while time.time() - start_time < duration:
            try:
                # Set timeout for receive
                message = await asyncio.wait_for(
                    self.websocket.recv(),
                    timeout=1.0
                )

                self.frames_received += 1
                current_time = time.time()
                self.total_bytes += len(message)

                # Calculate FPS
                if self.last_frame_time:
                    frame_interval = current_time - self.last_frame_time
                    if frame_interval > 0:
                        self.fps = 1.0 / frame_interval
                self.last_frame_time = current_time

                # Parse message
                try:
                    # Check if compressed
                    if isinstance(message, str) and message.startswith('C'):
                        # Decompress
                        compressed_hex = message[1:]
                        compressed_data = bytes.fromhex(compressed_hex)
                        decompressed = zlib.decompress(compressed_data)
                        data = json.loads(decompressed.decode('utf-8'))
                        compression = "yes"
                    elif isinstance(message, str):
                        data = json.loads(message)
                        compression = "no"
                    else:
                        # Binary format (not fully parsed here)
                        print(f"Frame {self.frames_received}: Binary format (size: {len(message)} bytes)")
                        continue

                    self.total_particles += data.get('particle_count', 0)

                    # Print frame info every 3 frames
                    if self.frames_received % 3 == 1:
                        self._print_frame_info(data, compression)

                    # Print stats every 10 frames
                    if self.frames_received % 10 == 0:
                        elapsed = current_time - start_time
                        throughput = self.total_bytes / elapsed / 1024  # KB/s
                        print(f"\n[Stats] Frames: {self.frames_received} | "
                              f"FPS: {self.fps:.1f} | "
                              f"Throughput: {throughput:.1f} KB/s | "
                              f"Avg particles/frame: {self.total_particles / self.frames_received:.0f}\n")

                except json.JSONDecodeError as e:
                    print(f"✗ Failed to parse JSON: {e}")
                    print(f"  Message type: {type(message)}")
                    print(f"  Message size: {len(message)}")

            except asyncio.TimeoutError:
                # No message received (server might be waiting for clients)
                pass
            except Exception as e:
                print(f"Error receiving frame: {e}")
                break

        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"Frames received: {self.frames_received}")
        print(f"Average FPS: {self.fps:.1f}")
        print(f"Total bytes received: {self.total_bytes / 1024:.1f} KB")
        print(f"Average throughput: {(self.total_bytes / (time.time() - start_time)) / 1024:.1f} KB/s")
        print(f"Total particles streamed: {self.total_particles}")
        print(f"Average particles per frame: {self.total_particles / max(1, self.frames_received):.0f}")
        print("="*80 + "\n")

    def _print_frame_info(self, data: dict, compression: str):
        """Print detailed info about a frame."""
        print(f"\nFrame {self.frames_received}:")
        print(f"  Time: {data.get('time', 'N/A'):.3f}s")
        print(f"  Step: {data.get('step', 'N/A')}")
        print(f"  Particles: {data.get('particle_count', 'N/A')}")
        print(f"  Compressed: {compression}")

        # Metrics
        if 'metrics' in data:
            metrics = data['metrics']
            print(f"  Mean concentration: {metrics.get('mean_concentration', 'N/A'):.4f}")
            print(f"  Max concentration: {metrics.get('max_concentration', 'N/A'):.4f}")
            print(f"  Mixing index: {metrics.get('mixing_index', 'N/A'):.4f}")

        # Minecraft data
        if 'minecraft_data' in data:
            mc_data = data['minecraft_data']
            print(f"  Voxel resolution: {mc_data.get('voxel_resolution', 'N/A')}")

            # Volume integrals
            if 'preset_regions' in mc_data:
                regions = mc_data['preset_regions']
                print(f"  Volume integrals:")
                for region_name, region_data in regions.items():
                    print(f"    - {region_data.get('name', region_name)}: "
                          f"{region_data.get('value', 'N/A'):.4f} kg "
                          f"({region_data.get('particle_count', 0)} particles)")

            # Camera presets
            if 'camera_presets' in mc_data:
                print(f"  Camera presets available: {list(mc_data['camera_presets'].keys())}")

    async def disconnect(self):
        """Disconnect from server."""
        if self.connected:
            await self.websocket.close()
            print("Disconnected from server")


async def test_server(scenario: str = "oil_spill", duration: int = 10):
    """Test the server by connecting and receiving frames."""
    print("\n" + "="*80)
    print(f"Testing Minecraft WebSocket Server - {scenario.upper()} scenario")
    print("="*80 + "\n")

    client = MinecraftClientSimulator()

    # Try to connect
    if not await client.connect():
        print("\n⚠️  Server is not running!")
        print("\nStart the server in another terminal:")
        print(f"  python minecraft_streaming_main.py --scenario {scenario}\n")
        return

    # Receive frames
    try:
        await client.receive_frames(duration=duration)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    finally:
        await client.disconnect()


def main():
    """Main test entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Test Minecraft WebSocket server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test default oil spill scenario
  python test_minecraft_server.py

  # Test heavy contamination for 20 seconds
  python test_minecraft_server.py --scenario heavy_contamination --duration 20

  # Test point source for 5 seconds
  python test_minecraft_server.py --scenario point_source --duration 5

Note: Make sure to run the server in another terminal before running this test:
  python minecraft_streaming_main.py --scenario oil_spill
        """
    )

    parser.add_argument(
        '--scenario',
        default='oil_spill',
        choices=['oil_spill', 'heavy_contamination', 'point_source'],
        help='Scenario to test (default: oil_spill)'
    )

    parser.add_argument(
        '--duration',
        type=int,
        default=10,
        help='Test duration in seconds (default: 10)'
    )

    args = parser.parse_args()

    # Run async test
    asyncio.run(test_server(scenario=args.scenario, duration=args.duration))


if __name__ == "__main__":
    main()
