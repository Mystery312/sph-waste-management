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

    async def handler(self, websocket: websockets.WebSocketServerProtocol, path: str):
        """
        Handle client connections and messages.

        Args:
            websocket: WebSocket connection
            path: Connection path
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

    async def broadcast_data(self):
        """
        Broadcast current simulation data to all connected clients.
        This should be called periodically from the simulation loop.
        """
        if not self.clients:
            return

        # Apply decimation
        indices = np.arange(0, len(self.current_data['positions']), self.decimation_factor)

        if self.binary_mode:
            message = self._encode_binary(indices)
        else:
            message = self._encode_json(indices)

        # Broadcast to all clients
        if self.clients:  # Check again in case clients disconnected
            websockets.broadcast(self.clients, message)

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
        async with websockets.serve(self.handler, self.host, self.port):
            self.running = True
            print(f"[WebSocket] Server running - waiting for connections...")
            await asyncio.Future()  # Run forever

    def stop_server(self):
        """Stop the WebSocket server."""
        self.running = False
        print("[WebSocket] Server stopped")
