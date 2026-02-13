"""
Minecraft Entry Point - Real-Time Streaming for Calculus 3 Education

Specialized entry point for streaming SPH simulation data to Minecraft clients
for educational demonstrations of multivariable calculus concepts.

Features:
- Preset demo scenarios (oil_spill, heavy_contamination, point_source)
- Extended WebSocket data format with Minecraft-specific fields
- Volume integral pre-computation for preset regions
- Camera positioning suggestions
- Support for saving/loading simulation states

Usage:
    # Run oil spill scenario (default)
    python minecraft_streaming_main.py

    # Run specific scenario
    python minecraft_streaming_main.py --scenario heavy_contamination

    # List available scenarios
    python minecraft_streaming_main.py --list-scenarios

    # Custom parameters
    python minecraft_streaming_main.py --scenario point_source --particles 4000 --fps 20
"""

import taichi as ti
import numpy as np
import asyncio
import threading
import time
import argparse
import os
from pathlib import Path

from sph_fluid_sim.config import *
from sph_fluid_sim.scenarios import load_scenario, list_scenarios, get_scenario_descriptions
from sph_fluid_sim.network.websocket_server import MinecraftDataServer
from sph_fluid_sim.analytics.metrics import ConcentrationMetrics
from sph_fluid_sim.utils.export import export_to_vtk


class MinecraftStreamingSimulation:
    """
    Simulation with Minecraft-optimized WebSocket streaming capability.
    """

    def __init__(
        self,
        scenario: str = "oil_spill",
        num_particles: int = NUM_PARTICLES,
        host: str = "localhost",
        port: int = 8765,
        broadcast_fps: int = 30,
        auto_inject: bool = True
    ):
        """
        Initialize Minecraft streaming simulation.

        Args:
            scenario: Scenario name ('oil_spill', 'heavy_contamination', 'point_source')
            num_particles: Number of particles
            host: WebSocket server host
            port: WebSocket server port
            broadcast_fps: Target broadcast frames per second
            auto_inject: Automatically inject waste at start (scenario-dependent)
        """
        self.scenario_name = scenario
        self.num_particles = num_particles
        self.broadcast_fps = broadcast_fps
        self.broadcast_interval = 1.0 / broadcast_fps
        self.auto_inject = auto_inject

        # Load scenario
        print(f"\n{'='*80}")
        print(f"Initializing Minecraft Streaming Simulation")
        print(f"{'='*80}")
        print(f"Scenario: {scenario}")
        print(f"Particles: {num_particles}")
        print(f"Broadcast rate: {broadcast_fps} FPS")
        print(f"{'='*80}\n")

        try:
            self.solver, self.concentration_tracker = load_scenario(scenario, num_particles)
        except ValueError as e:
            print(f"ERROR: {e}")
            print(f"\nAvailable scenarios: {', '.join(list_scenarios())}")
            raise

        # Create metrics
        self.metrics = ConcentrationMetrics()

        # Create Minecraft-optimized WebSocket server
        print(f"Initializing Minecraft WebSocket server on {host}:{port}...")
        self.ws_server = MinecraftDataServer(
            host=host,
            port=port,
            solver=self.solver,
            concentration_tracker=self.concentration_tracker
        )

        # Server thread
        self.server_thread = None
        self.server_loop = None

        # Simulation state
        self.running = False
        self.time = 0.0
        self.step = 0
        self.last_broadcast_time = -float('inf')  # Force first broadcast immediately

    def start_server(self):
        """Start WebSocket server in separate thread."""
        def run_server():
            import sys
            sys.stdout.flush()
            print("[Minecraft] Server thread started, initializing asyncio loop...")
            sys.stdout.flush()

            self.server_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.server_loop)
            print("[Minecraft] Asyncio loop created")
            sys.stdout.flush()

            try:
                print("[Minecraft] Calling start_server()...")
                sys.stdout.flush()
                self.server_loop.run_until_complete(self.ws_server.start_server())
            except OSError as e:
                if e.errno == 48:  # Address in use
                    print(f"[ERROR] Port {self.ws_server.port} is still in use")
                    print(f"[ERROR] Try: lsof -i :{self.ws_server.port} | grep LISTEN")
                    print(f"[ERROR] Or wait a few seconds and try again")
                else:
                    print(f"[ERROR] Failed to start WebSocket server: {e}")
            except Exception as e:
                print(f"[ERROR] Unexpected error in WebSocket server: {e}")
                import traceback
                traceback.print_exc()
            finally:
                print("[Minecraft] Server thread exiting")
                sys.stdout.flush()

        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        print("[Minecraft] WebSocket server started in background thread")
        time.sleep(2.0)  # Give server time to start and bind port

    def broadcast_if_ready(self):
        """Broadcast data to clients if enough time has passed."""
        if self.time - self.last_broadcast_time >= self.broadcast_interval:
            if self.step % 50 == 0:
                print(f"[Broadcast] Time: {self.time:.4f}s, Last broadcast: {self.last_broadcast_time:.4f}s, Interval: {self.broadcast_interval:.4f}s")
            try:
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

                # Safely convert stats to floats, replacing NaN/Inf with defaults
                def safe_float(val, default=0.0):
                    """Convert to float, replacing NaN/Inf with default."""
                    f = float(val)
                    return default if (f != f or f == float('inf') or f == float('-inf')) else f

                metrics_dict = {
                    'mean_concentration': safe_float(stats[0], 0.0),
                    'max_concentration': safe_float(stats[1], 0.0),
                    'min_concentration': safe_float(stats[2], 0.0),
                    'variance': safe_float(stats[3], 0.0),
                    'center_of_mass': [safe_float(stats[4], 0.0), safe_float(stats[5], 0.0), safe_float(stats[6], 0.0)],
                    'total_waste_mass': safe_float(stats[7], 0.0),
                    'mixing_index': safe_float(stats[8], 0.0)
                }

                # Update Minecraft-optimized server data (including gradients)
                gradients = None  # TODO: Compute gradients for visualization
                self.ws_server.update_simulation_data(
                    time=self.time,
                    step=self.step,
                    positions=positions,
                    velocities=velocities,
                    densities=densities,
                    pressures=pressures,
                    concentrations=concentrations,
                    metrics=metrics_dict,
                    gradients=gradients
                )

                # Broadcast asynchronously
                if self.server_loop:
                    asyncio.run_coroutine_threadsafe(
                        self.ws_server.broadcast_data(),
                        self.server_loop
                    )

                self.last_broadcast_time = self.time
            except Exception as e:
                print(f"[ERROR] Failed to broadcast data: {e}")
                import traceback
                traceback.print_exc()

    def run(
        self,
        target_time: float = 10.0,
        export_vtk: bool = False,
        export_interval: float = 0.05
    ):
        """
        Run simulation with Minecraft streaming.

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
        print("Starting Minecraft Streaming Simulation")
        print("="*80)
        print(f"WebSocket: ws://{self.ws_server.host}:{self.ws_server.port}")
        print(f"Broadcast rate: {self.broadcast_fps} FPS")
        print(f"Target duration: {target_time}s")
        print(f"Scenario: {self.scenario_name}")
        print("="*80)
        print("\nWaiting for Minecraft clients to connect...")
        print("In Minecraft, connect to: ws://localhost:8765\n")
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

            # Broadcast to Minecraft clients
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
    """Main entry point with command-line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Minecraft SPH Waste Management Simulation for Calculus 3 Education",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run default oil spill scenario
  python minecraft_streaming_main.py

  # Run heavy contamination scenario
  python minecraft_streaming_main.py --scenario heavy_contamination

  # List all available scenarios
  python minecraft_streaming_main.py --list-scenarios

  # Custom simulation with different parameters
  python minecraft_streaming_main.py --scenario point_source --particles 4000 --fps 20 --duration 15
        """
    )

    parser.add_argument(
        '--scenario',
        default='oil_spill',
        choices=['oil_spill', 'heavy_contamination', 'point_source'],
        help='Demo scenario to run (default: oil_spill)'
    )

    parser.add_argument(
        '--particles',
        type=int,
        default=NUM_PARTICLES,
        help=f'Number of particles (default: {NUM_PARTICLES})'
    )

    parser.add_argument(
        '--fps',
        type=int,
        default=30,
        help='Broadcast FPS for Minecraft clients (default: 30)'
    )

    parser.add_argument(
        '--duration',
        type=float,
        default=10.0,
        help='Simulation duration in seconds (default: 10.0)'
    )

    parser.add_argument(
        '--host',
        default='localhost',
        help='WebSocket server host (default: localhost)'
    )

    parser.add_argument(
        '--port',
        type=int,
        default=8765,
        help='WebSocket server port (default: 8765)'
    )

    parser.add_argument(
        '--list-scenarios',
        action='store_true',
        help='List all available scenarios with descriptions'
    )

    parser.add_argument(
        '--export-vtk',
        action='store_true',
        help='Export VTK files during simulation'
    )

    args = parser.parse_args()

    # List scenarios if requested
    if args.list_scenarios:
        print("\n" + "="*80)
        print("Available Scenarios")
        print("="*80)
        descriptions = get_scenario_descriptions()
        for scenario_name, info in descriptions.items():
            print(f"\n{info['name']} ({scenario_name})")
            print(f"  {info['description']}")
            print(f"  Physics: {', '.join(info['physics_concepts'])}")
        print("\n" + "="*80)
        return

    # Initialize Taichi
    print("[Taichi] Initializing GPU acceleration...")
    ti.init(arch=ti.cuda)  # Change to ti.cpu if no GPU

    # Print configuration
    print_simulation_config()

    # Create simulation
    sim = MinecraftStreamingSimulation(
        scenario=args.scenario,
        num_particles=args.particles,
        host=args.host,
        port=args.port,
        broadcast_fps=args.fps
    )

    # Start server
    sim.start_server()

    try:
        # Run simulation
        sim.run(
            target_time=args.duration,
            export_vtk=args.export_vtk,
            export_interval=0.1
        )
    except KeyboardInterrupt:
        print("\n\nSimulation interrupted by user")
    finally:
        print("\nServer will continue running for 5 seconds...")
        print("(Allows Minecraft clients to disconnect gracefully)")
        time.sleep(5)


if __name__ == "__main__":
    main()
