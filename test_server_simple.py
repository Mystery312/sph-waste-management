#!/usr/bin/env python3
"""
Simple test to verify the Minecraft WebSocket server works.
"""

import taichi as ti
import numpy as np
import asyncio
import websockets
from sph_fluid_sim.config import *
from sph_fluid_sim.scenarios import load_scenario
from sph_fluid_sim.network.websocket_server import MinecraftDataServer
from sph_fluid_sim.analytics.metrics import ConcentrationMetrics

async def test_websocket_data():
    """Test WebSocket server data sending."""

    print("="*80)
    print("Testing Minecraft WebSocket Server")
    print("="*80)

    # Initialize Taichi
    ti.init(arch=ti.cpu)  # Use CPU for testing

    # Load scenario
    print("\n1. Loading scenario...")
    solver, concentration_tracker = load_scenario('oil_spill', num_particles=1000)
    print("   ✓ Scenario loaded")

    # Create server
    print("\n2. Creating WebSocket server...")
    ws_server = MinecraftDataServer(solver=solver, concentration_tracker=concentration_tracker)
    print("   ✓ Server created")

    # Create metrics
    metrics = ConcentrationMetrics()

    # Simulate a few steps and broadcast
    print("\n3. Running simulation steps...")
    for step in range(5):
        dt = solver.compute_timestep()
        solver.step(dt)
        concentration_tracker.step(
            solver.positions,
            solver.velocities,
            solver.masses,
            solver.densities,
            solver.neighbor_search,
            dt
        )

        # Compute metrics
        stats = metrics.compute_statistics(
            concentration_tracker.concentration,
            solver.masses,
            solver.positions,
            1000
        )

        # Create metrics dict
        metrics_dict = {
            'mean_concentration': float(stats[0]) if stats[0] == stats[0] else 0.0,
            'max_concentration': float(stats[1]) if stats[1] == stats[1] else 0.0,
            'min_concentration': float(stats[2]) if stats[2] == stats[2] else 0.0,
            'variance': float(stats[3]) if stats[3] == stats[3] else 0.0,
            'center_of_mass': [0.0, 0.0, 0.0],
            'total_waste_mass': float(stats[7]) if stats[7] == stats[7] else 0.0,
            'mixing_index': float(stats[8]) if stats[8] == stats[8] else 0.0
        }

        # Update server data
        print(f"   Step {step}: Updating server data...")
        try:
            positions_np = solver.positions.to_numpy()
            velocities_np = solver.velocities.to_numpy()
            densities_np = solver.densities.to_numpy()
            pressures_np = solver.pressures.to_numpy()
            concentrations_np = concentration_tracker.concentration.to_numpy()

            ws_server.update_simulation_data(
                time=float(step) * dt,
                step=step,
                positions=positions_np,
                velocities=velocities_np,
                densities=densities_np,
                pressures=pressures_np,
                concentrations=concentrations_np,
                metrics=metrics_dict,
                gradients=None
            )
            print(f"     ✓ Data updated (time={float(step)*dt:.3f}s)")
        except Exception as e:
            print(f"     ✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False

        # Try to encode JSON
        try:
            indices = np.arange(0, 1000, 1)
            message = ws_server._encode_json(indices)
            print(f"     ✓ JSON encoded ({len(message)} bytes)")
        except Exception as e:
            print(f"     ✗ Encoding failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    print("\n" + "="*80)
    print("✓ All tests passed!")
    print("="*80)
    return True

if __name__ == "__main__":
    result = asyncio.run(test_websocket_data())
    exit(0 if result else 1)
