# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GPU-accelerated 3D SPH (Smoothed Particle Hydrodynamics) fluid simulation for waste management, built with Python and Taichi Lang. The system has three phases: core fluid physics, waste concentration tracking, and real-time Unity streaming via WebSocket.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run Phase 1: Basic SPH fluid simulation (GGUI window + VTK export)
python main.py

# Run Phase 2: Waste concentration tracking with metrics
python waste_tracking_main.py

# Run Phase 3: WebSocket streaming for Unity client
python unity_streaming_main.py

# Run all tests
python test_all_phases.py
```

## Architecture

### Three-Phase Pipeline

**Phase 1 — Core SPH Engine** (`main.py`): Dam-break initialization → neighbor search (spatial hashing) → density summation → Tait EOS pressure → symmetric pressure forces + Morris viscosity → adaptive CFL timestep integration → boundary enforcement → GGUI rendering + VTK export.

**Phase 2 — Waste Tracking** (`waste_tracking_main.py`): Extends Phase 1 with advection-diffusion concentration solver (`∂C/∂t + v·∇C = D∇²C`), contamination zone detection, and statistical metrics (mixing index, variance, center of mass). Color-coded visualization (blue→yellow→red).

**Phase 3 — Unity Streaming** (`unity_streaming_main.py`): Adds WebSocket server (`ws://localhost:8765`) with JSON/binary encoding, compression, decimation, and multi-client support. Unity C# client in `unity_client/`.

### Module Layout

- `sph_fluid_sim/config.py` — All simulation parameters and physical constants (particle count, spacing, viscosity, sound speed, timestep, diffusion coefficient, domain size). This is the single source of truth for tuning the simulation.
- `sph_fluid_sim/core/` — SPH solver orchestrator (`solver.py`), cubic spline kernel (`kernel.py`), spatial hash neighbor search (`neighbor_search.py`), symplectic Euler integrator with CFL (`integrator.py`)
- `sph_fluid_sim/physics/` — Tait equation of state (`equation_of_state.py`), pressure and viscosity force computation (`forces.py`), box boundary conditions (`boundary.py`)
- `sph_fluid_sim/tracking/` — Advection-diffusion concentration solver (`concentration.py`)
- `sph_fluid_sim/analytics/` — Contamination metrics and zone detection (`metrics.py`)
- `sph_fluid_sim/network/` — WebSocket streaming server (`websocket_server.py`)
- `sph_fluid_sim/visualization/` — Phase 1 GGUI renderer (`renderer.py`), Phase 2 color-coded renderer (`waste_renderer.py`)
- `sph_fluid_sim/utils/` — Dam-break particle initialization (`initialization.py`), VTK ASCII export (`export.py`)

### Key Design Patterns

- All GPU-parallel computation uses Taichi `@ti.kernel` and `@ti.func` decorators. Taichi fields (not NumPy arrays) are the primary data structures for particle state.
- The solver pipeline in `WCSPHSolver.step()` orchestrates the full timestep by calling each module in sequence.
- VTK files export to `output/frames/` for ParaView post-processing.

## Dependencies

- `taichi>=1.6.0` — GPU compute framework (kernels, fields, GGUI)
- `numpy>=1.24.0` — Data transfer between Taichi and Python
- `websockets>=11.0` — Phase 3 streaming server
