#!/usr/bin/env python3
"""
Test script to verify metrics computation works correctly.
"""

import taichi as ti
import numpy as np
from sph_fluid_sim.config import *
from sph_fluid_sim.analytics.metrics import ConcentrationMetrics
from sph_fluid_sim.scenarios import load_scenario

print("Testing metrics computation...")
print("="*80)

# Initialize Taichi
print("[Taichi] Initializing GPU acceleration...")
ti.init(arch=ti.cuda)

# Load a scenario
print("Loading oil_spill scenario...")
solver, concentration_tracker = load_scenario('oil_spill', num_particles=1000)

# Create metrics
metrics = ConcentrationMetrics()

# Run a few simulation steps
print("\nRunning simulation steps...")
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

    # Try to compute metrics
    try:
        print(f"\nStep {step}:")
        print(f"  Computing statistics...")
        stats = metrics.compute_statistics(
            concentration_tracker.concentration,
            solver.masses,
            solver.positions,
            1000
        )

        print(f"  Stats type: {type(stats)}")
        print(f"  Stats: {stats}")

        # Try to access individual values
        print(f"  Mean concentration: {float(stats[0]):.6f}")
        print(f"  Max concentration: {float(stats[1]):.6f}")
        print(f"  Min concentration: {float(stats[2]):.6f}")
        print(f"  Variance: {float(stats[3]):.6f}")
        print(f"  Mixing index: {float(stats[8]):.6f}")

    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "="*80)
print("Metrics test completed!")
