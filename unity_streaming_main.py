"""
Phase 3 Entry Point - Real-Time Streaming to Unity

Combines Phase 2 waste tracking with WebSocket server for live streaming to Unity.
Demonstrates:
- Real-time data streaming over WebSocket
- Configurable broadcast rate
- Multiple client support
- Performance metrics
- Optional VTK export
"""

import taichi as ti
import numpy as np
import asyncio
import threading
from sph_fluid_sim.config import *
from sph_fluid_sim.core.solver import WCSPHSolver
from sph_fluid_sim.tracking.concentration import ConcentrationTracker
from sph_fluid_sim.analytics.metrics import ConcentrationMetrics
from sph_fluid_sim.network.websocket_server import SimulationDataServer
from sph_fluid_sim.utils.export import export_to_vtk
import time
import os


class StreamingSimulation:
    """
    Simulation with real-time WebSocket streaming capability.
    """

    def __init__(
        self,
        num_particles: int = NUM_PARTICLES,
        host: str = "localhost",
        port: int = 8765,
        broadcast_fps: int = 30
    ):
        """
        Initialize streaming simulation.

        Args:
            num_particles: Number of particles
            host: WebSocket server host
            port: WebSocket server port
            broadcast_fps: Target broadcast frames per second
        """
        self.num_particles = num_particles
        self.broadcast_fps = broadcast_fps
        self.broadcast_interval = 1.0 / broadcast_fps

        # Create SPH solver
        print("Initializing WCSPH solver...")
        self.solver = WCSPHSolver(num_particles=num_particles)
        self.solver.initialize()

        # Create concentration tracker
        print("Initializing concentration tracker...")
        self.concentration_tracker = ConcentrationTracker(num_particles=num_particles)
        self.concentration_tracker.initialize_clean_fluid()

        # Mark top 20% as waste
        positions_np = self.solver.positions.to_numpy()
        y_positions = positions_np[:, 1]
        waste_count = int(0.2 * num_particles)
        waste_indices = np.argsort(y_positions)[-waste_count:]

        print(f"Marking {waste_count} particles as waste...")
        for idx in waste_indices:
            self.concentration_tracker.concentration[idx] = 1.0
            self.concentration_tracker.particle_type[idx] = PARTICLE_TYPE_FLUID_WASTE

        # Create metrics
        self.metrics = ConcentrationMetrics()

        # Create WebSocket server
        print(f"Initializing WebSocket server on {host}:{port}...")
        self.ws_server = SimulationDataServer(host=host, port=port)

        # Server thread
        self.server_thread = None
        self.server_loop = None

        # Simulation state
        self.running = False
        self.time = 0.0
        self.step = 0
        self.last_broadcast_time = 0.0

    def start_server(self):
        """Start WebSocket server in separate thread."""
        def run_server():
            self.server_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.server_loop)
            self.server_loop.run_until_complete(self.ws_server.start_server())

        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        print("WebSocket server started in background thread")
        time.sleep(0.5)  # Give server time to start

    def broadcast_if_ready(self):
        """Broadcast data to clients if enough time has passed."""
        if self.time - self.last_broadcast_time >= self.broadcast_interval:
            # Get current data
            positions = self.solver.positions.to_numpy()
            velocities = self.solver.velocities.to_numpy()
            densities = self.solver.densities.to_numpy()
            pressures = self.solver.pressures.to_numpy()
            concentrations = self.concentration_tracker.concentration.to_numpy()

            # Compute metrics
            stats = self.metrics.compute_statistics(
                self.concentration_tracker.concentration,
                self.solver.masses,
                self.solver.positions,
                self.num_particles
            )

            metrics_dict = {
                'mean_concentration': float(stats[0]),
                'max_concentration': float(stats[1]),
                'min_concentration': float(stats[2]),
                'variance': float(stats[3]),
                'center_of_mass': [float(stats[4]), float(stats[5]), float(stats[6])],
                'total_waste_mass': float(stats[7]),
                'mixing_index': float(stats[8])
            }

            # Update server data
            self.ws_server.update_simulation_data(
                time=self.time,
                step=self.step,
                positions=positions,
                velocities=velocities,
                densities=densities,
                pressures=pressures,
                concentrations=concentrations,
                metrics=metrics_dict
            )

            # Broadcast asynchronously
            if self.server_loop:
                asyncio.run_coroutine_threadsafe(
                    self.ws_server.broadcast_data(),
                    self.server_loop
                )

            self.last_broadcast_time = self.time

    def run(
        self,
        target_time: float = 5.0,
        export_vtk: bool = False,
        export_interval: float = 0.05
    ):
        """
        Run simulation with real-time streaming.

        Args:
            target_time: Total simulation time
            export_vtk: Whether to export VTK files
            export_interval: VTK export interval
        """
        self.running = True
        next_export_time = 0.0
        frame = 0
        print_interval = 50

        print("\n" + "="*80)
        print("Starting Real-Time Streaming Simulation (Phase 3)")
        print("="*80)
        print(f"WebSocket: ws://{self.ws_server.host}:{self.ws_server.port}")
        print(f"Broadcast rate: {self.broadcast_fps} FPS")
        print(f"Particle count: {self.num_particles}")
        print("="*80 + "\n")

        while self.time < target_time and self.running:
            # Compute timestep
            dt = self.solver.compute_timestep()

            # SPH step
            self.solver.step(dt)

            # Concentration step
            self.concentration_tracker.step(
                self.solver.positions,
                self.solver.velocities,
                self.solver.masses,
                self.solver.densities,
                self.solver.neighbor_search,
                dt
            )

            # Update time
            self.time += dt
            self.step += 1

            # Broadcast to WebSocket clients
            self.broadcast_if_ready()

            # Export VTK if enabled
            if export_vtk and self.time >= next_export_time:
                positions = self.solver.positions.to_numpy()
                velocities = self.solver.velocities.to_numpy()
                densities = self.solver.densities.to_numpy()
                pressures = self.solver.pressures.to_numpy()
                export_to_vtk(positions, velocities, densities, pressures, frame, OUTPUT_DIR)
                next_export_time += export_interval
                frame += 1

            # Console output
            if self.step % print_interval == 0:
                total_conc = self.concentration_tracker.compute_total_concentration()
                client_count = len(self.ws_server.clients)
                print(f"Step {self.step:5d} | "
                      f"Time: {self.time:6.3f}s | "
                      f"dt: {dt*1000:5.2f}ms | "
                      f"Clients: {client_count} | "
                      f"Total Conc: {total_conc:8.2f}")

        print("\n" + "="*80)
        print("Simulation Completed!")
        print("="*80)
        print(f"Total steps: {self.step}")
        print(f"Total time: {self.time:.2f}s")
        if export_vtk:
            print(f"Frames exported: {frame}")
        print("="*80)


def main():
    # Initialize Taichi
    ti.init(arch=ti.cuda)  # Change to ti.cpu if no GPU

    # Print configuration
    print_simulation_config()

    # Create streaming simulation
    sim = StreamingSimulation(
        num_particles=NUM_PARTICLES,
        host="localhost",
        port=8765,
        broadcast_fps=30  # 30 updates per second to Unity
    )

    # Start WebSocket server
    sim.start_server()

    print("\n" + "="*80)
    print("READY FOR UNITY CONNECTION")
    print("="*80)
    print("In Unity, connect to: ws://localhost:8765")
    print("Press Ctrl+C to stop the simulation")
    print("="*80 + "\n")

    try:
        # Run simulation
        sim.run(
            target_time=10.0,  # 10 seconds
            export_vtk=False,  # Disable VTK for performance
            export_interval=0.1
        )
    except KeyboardInterrupt:
        print("\n\nSimulation interrupted by user")

    print("\nServer will continue running for 5 seconds...")
    print("(Allows Unity clients to disconnect gracefully)")
    time.sleep(5)


if __name__ == "__main__":
    main()
