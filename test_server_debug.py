#!/usr/bin/env python3
"""
Debug test for Minecraft streaming server.
"""

import sys
print("1. Starting imports...")
sys.stdout.flush()

import taichi as ti
print("2. Taichi imported")
sys.stdout.flush()

import asyncio
print("3. Asyncio imported")
sys.stdout.flush()

from sph_fluid_sim.config import *
print("4. Config imported")
sys.stdout.flush()

from sph_fluid_sim.scenarios import load_scenario
print("5. Scenarios imported")
sys.stdout.flush()

from sph_fluid_sim.network.websocket_server import MinecraftDataServer
print("6. WebSocket server imported")
sys.stdout.flush()

from sph_fluid_sim.analytics.metrics import ConcentrationMetrics
print("7. Metrics imported")
sys.stdout.flush()

from minecraft_streaming_main import MinecraftStreamingSimulation
print("8. MinecraftStreamingSimulation imported")
sys.stdout.flush()

print("\n9. Initializing Taichi...")
ti.init(arch=ti.cpu)
print("10. Taichi initialized")
sys.stdout.flush()

print("\n11. Creating simulation...")
sim = MinecraftStreamingSimulation(
    scenario='oil_spill',
    num_particles=1000,
    broadcast_fps=30
)
print("12. Simulation created")
sys.stdout.flush()

print("\n13. Starting server...")
sim.start_server()
print("14. Server thread started")
sys.stdout.flush()

print("\n15. Waiting 2 seconds...")
import time
time.sleep(2)
print("16. Running single step...")

# Single step
dt = sim.solver.compute_timestep()
sim.solver.step(dt)
sim.concentration_tracker.step(
    sim.solver.positions,
    sim.solver.velocities,
    sim.solver.masses,
    sim.solver.densities,
    sim.solver.neighbor_search,
    dt
)

sim.time += dt
sim.step += 1
print(f"17. Step completed (time={sim.time:.4f}s)")
sys.stdout.flush()

print("\n18. Checking server status...")
print(f"    Server loop: {sim.server_loop}")
print(f"    Server thread: {sim.server_thread}")
print(f"    Clients: {len(sim.ws_server.clients)}")
sys.stdout.flush()

print("\n19. Done!")
