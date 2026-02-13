"""
WebSocket Server for Real-Time Simulation Data Streaming

Streams SPH simulation data to Unity or other clients over WebSocket protocol.
Supports multiple simultaneous clients with configurable data rates.

Data Protocol:
- JSON messages with particle positions, velocities, concentrations
- Binary mode for high-performance streaming (optional)
- Compression for reduced bandwidth
"""

import asyncio
import websockets
import json
import struct
import zlib
from typing import Set, Optional
import numpy as np


class SimulationDataServer:
    """
    WebSocket server for streaming simulation data to clients.
    """

    def __init__(self, host: str = "localhost", port: int = 8765):
        """
        Initialize WebSocket server.

        Args:
            host: Server host address
            port: Server port number
        """
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.running = False

        # Current simulation state (updated externally)
        self.current_data = {
            'time': 0.0,
            'step': 0,
            'positions': None,
            'velocities': None,
            'densities': None,
            'pressures': None,
            'concentrations': None,
            'metrics': {}
        }

        # Configuration
        self.compression_enabled = True
        self.binary_mode = False  # JSON by default, binary for performance
        self.decimation_factor = 1  # Send every Nth particle for bandwidth reduction

    async def register(self, websocket: websockets.WebSocketServerProtocol):
        """Register a new client connection."""
        self.clients.add(websocket)
        print(f"[WebSocket] Client connected from {websocket.remote_address}")
        print(f"[WebSocket] Total clients: {len(self.clients)}")

    async def unregister(self, websocket: websockets.WebSocketServerProtocol):
        """Unregister a disconnected client."""
        self.clients.remove(websocket)
        print(f"[WebSocket] Client disconnected from {websocket.remote_address}")
        print(f"[WebSocket] Total clients: {len(self.clients)}")

    async def handler(self, websocket: websockets.WebSocketServerProtocol):
        """
        Handle client connections and messages.

        Args:
            websocket: WebSocket connection
        """
        await self.register(websocket)
        try:
            async for message in websocket:
                # Handle client commands
                await self.handle_command(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister(websocket)

    async def handle_command(self, websocket: websockets.WebSocketServerProtocol, message: str):
        """
        Handle commands from clients.

        Supported commands:
        - {"command": "get_config"} - Returns server configuration
        - {"command": "set_decimation", "factor": N} - Set particle decimation
        - {"command": "set_compression", "enabled": true/false}
        - {"command": "set_binary_mode", "enabled": true/false}

        Args:
            websocket: Client connection
            message: Command message
        """
        try:
            data = json.loads(message)
            command = data.get('command')

            if command == 'get_config':
                config = {
                    'compression': self.compression_enabled,
                    'binary_mode': self.binary_mode,
                    'decimation_factor': self.decimation_factor,
                    'server_version': '1.0.0'
                }
                await websocket.send(json.dumps({'type': 'config', 'data': config}))

            elif command == 'set_decimation':
                self.decimation_factor = max(1, int(data.get('factor', 1)))
                await websocket.send(json.dumps({
                    'type': 'ack',
                    'message': f'Decimation set to {self.decimation_factor}'
                }))

            elif command == 'set_compression':
                self.compression_enabled = bool(data.get('enabled', True))
                await websocket.send(json.dumps({
                    'type': 'ack',
                    'message': f'Compression {"enabled" if self.compression_enabled else "disabled"}'
                }))

            elif command == 'set_binary_mode':
                self.binary_mode = bool(data.get('enabled', False))
                await websocket.send(json.dumps({
                    'type': 'ack',
                    'message': f'Binary mode {"enabled" if self.binary_mode else "disabled"}'
                }))

        except json.JSONDecodeError:
            await websocket.send(json.dumps({
                'type': 'error',
                'message': 'Invalid JSON command'
            }))

    def update_simulation_data(
        self,
        time: float,
        step: int,
        positions: np.ndarray,
        velocities: np.ndarray,
        densities: np.ndarray,
        pressures: np.ndarray,
        concentrations: Optional[np.ndarray] = None,
        metrics: Optional[dict] = None
    ):
        """
        Update current simulation state (called from main simulation loop).

        Args:
            time: Simulation time
            step: Current timestep
            positions: Particle positions [N, 3]
            velocities: Particle velocities [N, 3]
            densities: Particle densities [N]
            pressures: Particle pressures [N]
            concentrations: Particle concentrations [N] (optional)
            metrics: Additional metrics dictionary (optional)
        """
        self.current_data = {
            'time': float(time),
            'step': int(step),
            'positions': positions,
            'velocities': velocities,
            'densities': densities,
            'pressures': pressures,
            'concentrations': concentrations,
            'metrics': metrics or {}
        }

        # Debug logging for first data update
        if step % 50 == 0:
            print(f"[WebSocket] Updated data: step={step}, time={time:.3f}s, particles={len(positions)}")

    async def broadcast_data(self):
        """
        Broadcast current simulation data to all connected clients.
        This should be called periodically from the simulation loop.
        """
        try:
            if not self.clients:
                #print(f"[Broadcast] No clients connected")
                return

            # Check if current_data is initialized
            if self.current_data['positions'] is None:
                print(f"[Broadcast] No position data yet")
                return

            # Apply decimation
            indices = np.arange(0, len(self.current_data['positions']), self.decimation_factor)

            if self.binary_mode:
                message = self._encode_binary(indices)
            else:
                message = self._encode_json(indices)

            # Broadcast to all clients
            if self.clients:  # Check again in case clients disconnected
                print(f"[Broadcast] Sending {len(message)} bytes to {len(self.clients)} client(s)")
                websockets.broadcast(self.clients, message)
        except Exception as e:
            print(f"[ERROR] Broadcast failed: {e}")
            import traceback
            traceback.print_exc()

    def _encode_json(self, indices: np.ndarray) -> str:
        """
        Encode data as JSON message.

        Args:
            indices: Particle indices to include

        Returns:
            JSON string
        """
        data = {
            'type': 'simulation_data',
            'time': self.current_data['time'],
            'step': self.current_data['step'],
            'particle_count': len(indices),
            'positions': self.current_data['positions'][indices].tolist(),
            'velocities': self.current_data['velocities'][indices].tolist(),
            'densities': self.current_data['densities'][indices].tolist(),
            'pressures': self.current_data['pressures'][indices].tolist(),
        }

        # Add concentration if available
        if self.current_data['concentrations'] is not None:
            data['concentrations'] = self.current_data['concentrations'][indices].tolist()

        # Add metrics
        if self.current_data['metrics']:
            data['metrics'] = self.current_data['metrics']

        json_str = json.dumps(data)

        # Compress if enabled
        if self.compression_enabled:
            compressed = zlib.compress(json_str.encode('utf-8'))
            # Prefix with 'C' to indicate compression
            return 'C' + compressed.hex()
        else:
            return json_str

    def _encode_binary(self, indices: np.ndarray) -> bytes:
        """
        Encode data as binary message for higher performance.

        Binary format:
        - Header: 'SPHD' (4 bytes magic)
        - Version: 1 (1 byte)
        - Flags: compression bit (1 byte)
        - Time: float64 (8 bytes)
        - Step: int32 (4 bytes)
        - Particle count: int32 (4 bytes)
        - Positions: float32[N, 3]
        - Velocities: float32[N, 3]
        - Densities: float32[N]
        - Pressures: float32[N]
        - Concentrations: float32[N] (optional)

        Args:
            indices: Particle indices to include

        Returns:
            Binary data
        """
        # Header
        data = b'SPHD'  # Magic number
        data += struct.pack('B', 1)  # Version
        flags = 0x01 if self.current_data['concentrations'] is not None else 0x00
        data += struct.pack('B', flags)
        data += struct.pack('d', self.current_data['time'])
        data += struct.pack('i', self.current_data['step'])
        data += struct.pack('i', len(indices))

        # Particle data
        data += self.current_data['positions'][indices].astype(np.float32).tobytes()
        data += self.current_data['velocities'][indices].astype(np.float32).tobytes()
        data += self.current_data['densities'][indices].astype(np.float32).tobytes()
        data += self.current_data['pressures'][indices].astype(np.float32).tobytes()

        if self.current_data['concentrations'] is not None:
            data += self.current_data['concentrations'][indices].astype(np.float32).tobytes()

        # Compress if enabled
        if self.compression_enabled:
            data = zlib.compress(data)

        return data

    async def start_server(self):
        """Start the WebSocket server."""
        print(f"[WebSocket] Starting server on {self.host}:{self.port}")
        try:
            # Try with reuse_port if available (for faster rebinding)
            async with websockets.serve(self.handler, self.host, self.port, reuse_port=True):
                self.running = True
                print(f"[WebSocket] Server running - waiting for connections...")
                await asyncio.Future()  # Run forever
        except TypeError:
            # Older websockets version doesn't support reuse_port
            async with websockets.serve(self.handler, self.host, self.port):
                self.running = True
                print(f"[WebSocket] Server running - waiting for connections...")
                await asyncio.Future()  # Run forever

    def stop_server(self):
        """Stop the WebSocket server."""
        self.running = False
        print("[WebSocket] Server stopped")


class MinecraftDataServer(SimulationDataServer):
    """
    WebSocket server optimized for Minecraft client streaming.

    Extends SimulationDataServer with Minecraft-specific data formats and features:
    - Extended JSON format with gradients, integrals, and metadata
    - Pre-computed volume integral results for preset regions
    - Camera positioning suggestions
    - Voxel grid bounds and density information
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8765,
        solver=None,
        concentration_tracker=None
    ):
        """
        Initialize Minecraft-optimized WebSocket server.

        Args:
            host: Server host address
            port: Server port number
            solver: WCSPHSolver instance (for gradient computation)
            concentration_tracker: ConcentrationTracker instance
        """
        super().__init__(host=host, port=port)
        self.solver = solver
        self.concentration_tracker = concentration_tracker

        # Minecraft-specific configuration
        self.voxel_resolution = 20  # 20×20×20 grid for 1m³ domain
        self.voxel_size = 1.0 / self.voxel_resolution  # Size of each voxel in meters

        # Preset regions for volume integrals (bounds in simulation space: 0-1)
        self.preset_regions = {
            'top_half': {
                'bounds': [[0, 0.5, 0], [1, 1, 1]],
                'name': 'Top Half',
                'description': 'Upper half of simulation domain'
            },
            'bottom_half': {
                'bounds': [[0, 0, 0], [1, 0.5, 1]],
                'name': 'Bottom Half',
                'description': 'Lower half of simulation domain'
            },
            'high_contamination': {
                'bounds': [[0.25, 0.25, 0.25], [0.75, 0.75, 0.75]],
                'name': 'High Contamination Zone',
                'description': 'Central region of domain'
            }
        }

        # Camera presets (in Minecraft coordinates: 0-20 blocks)
        self.camera_presets = {
            'overview': {
                'position': [10, 12, 10],
                'look_at': [10, 10, 10],
                'fov': 70
            },
            'close_up': {
                'position': [12, 10, 12],
                'look_at': [10, 10, 10],
                'fov': 45
            },
            'side': {
                'position': [20, 10, 10],
                'look_at': [10, 10, 10],
                'fov': 60
            },
            'top_down': {
                'position': [10, 20, 10],
                'look_at': [10, 10, 10],
                'fov': 60
            }
        }

    def update_simulation_data(
        self,
        time: float,
        step: int,
        positions: np.ndarray,
        velocities: np.ndarray,
        densities: np.ndarray,
        pressures: np.ndarray,
        concentrations: Optional[np.ndarray] = None,
        metrics: Optional[dict] = None,
        gradients: Optional[np.ndarray] = None
    ):
        """
        Update current simulation state with Minecraft-specific data.

        Args:
            time: Simulation time
            step: Current timestep
            positions: Particle positions [N, 3]
            velocities: Particle velocities [N, 3]
            densities: Particle densities [N]
            pressures: Particle pressures [N]
            concentrations: Particle concentrations [N] (optional)
            metrics: Additional metrics dictionary (optional)
            gradients: Gradient vectors for particles [N, 3] (optional)
        """
        super().update_simulation_data(
            time=time,
            step=step,
            positions=positions,
            velocities=velocities,
            densities=densities,
            pressures=pressures,
            concentrations=concentrations,
            metrics=metrics
        )

        # Store Minecraft-specific data
        self.current_data['gradients'] = gradients

    def _compute_volume_integrals(self) -> dict:
        """
        Compute volume integrals for preset regions.

        Returns:
            dict: Volume integral results for each preset region
        """
        if self.current_data['concentrations'] is None:
            return {}

        try:
            concentrations = self.current_data['concentrations']
            positions = self.current_data['positions']
            voxel_volume = self.voxel_size ** 3

            integrals = {}

            for region_key, region_info in self.preset_regions.items():
                bounds = region_info['bounds']
                min_bound = np.array(bounds[0])
                max_bound = np.array(bounds[1])

                # Find particles within bounds
                within_bounds = np.all(
                    (positions >= min_bound) & (positions <= max_bound),
                    axis=1
                )

                if np.any(within_bounds):
                    # Compute Riemann sum: ∭ C dV ≈ Σ C_i * ΔV
                    integral = np.sum(concentrations[within_bounds]) * voxel_volume
                    particle_count = np.sum(within_bounds)
                else:
                    integral = 0.0
                    particle_count = 0

                # Ensure values are finite
                if integral != integral or integral == float('inf') or integral == float('-inf'):
                    integral = 0.0

                integrals[region_key] = {
                    'value': float(integral),
                    'particle_count': int(particle_count),
                    'bounds': bounds,
                    'name': region_info['name']
                }

            return integrals
        except Exception as e:
            print(f"[ERROR] Failed to compute volume integrals: {e}")
            # Return empty dict on error
            return {}

    def _encode_json(self, indices: np.ndarray) -> str:
        """
        Encode data as Minecraft-optimized JSON message.

        Extends base JSON with:
        - Minecraft-specific data fields
        - Volume integral calculations
        - Camera position suggestions
        - Gradient data (if available)

        Args:
            indices: Particle indices to include

        Returns:
            JSON string
        """
        try:
            data = {
                'type': 'simulation_data',
                'time': float(self.current_data['time']),
                'step': int(self.current_data['step']),
                'particle_count': len(indices),
                'positions': self.current_data['positions'][indices].tolist(),
                'velocities': self.current_data['velocities'][indices].tolist(),
                'densities': self.current_data['densities'][indices].tolist(),
                'pressures': self.current_data['pressures'][indices].tolist(),
            }

            # Add concentration if available
            if self.current_data['concentrations'] is not None:
                data['concentrations'] = self.current_data['concentrations'][indices].tolist()

            # Add gradients if available (for vector field visualization)
            if self.current_data.get('gradients') is not None:
                data['gradients'] = self.current_data['gradients'][indices].tolist()

            # Add metrics with safety checks
            if self.current_data['metrics']:
                # Ensure all metric values are JSON-serializable (no NaN/Inf)
                safe_metrics = {}
                for key, value in self.current_data['metrics'].items():
                    if isinstance(value, list):
                        safe_metrics[key] = [0.0 if (v != v or v == float('inf') or v == float('-inf')) else v for v in value]
                    else:
                        val = float(value) if not isinstance(value, str) else value
                        safe_metrics[key] = 0.0 if (val != val or val == float('inf') or val == float('-inf')) else val
                data['metrics'] = safe_metrics

            # Add Minecraft-specific data
            minecraft_data = {
                'preset_regions': self._compute_volume_integrals(),
                'camera_presets': self.camera_presets,
                'voxel_resolution': self.voxel_resolution,
                'voxel_size': float(self.voxel_size),
                'coordinate_scale': 20  # 20 Minecraft blocks per 1m simulation unit
            }
            data['minecraft_data'] = minecraft_data

            json_str = json.dumps(data)

            # Compress if enabled
            if self.compression_enabled:
                compressed = zlib.compress(json_str.encode('utf-8'))
                # Prefix with 'C' to indicate compression
                return 'C' + compressed.hex()
            else:
                return json_str
        except Exception as e:
            print(f"[ERROR] Failed to encode JSON: {e}")
            import traceback
            traceback.print_exc()
            # Return minimal valid JSON on error
            return json.dumps({'type': 'error', 'message': str(e)})
