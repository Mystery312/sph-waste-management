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

# Run Phase 3: WebSocket streaming for Unity client (FIXED ✓)
python unity_streaming_main.py

# Run all tests
python test_all_phases.py

# Test WebSocket broadcasting (Phase 0 verification)
python test_websocket_broadcast.py

# Full end-to-end streaming test
python test_streaming_e2e.py
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

## Current Project Status

### ✓ COMPLETE
- **Phase 1 (Core SPH):** Full simulation with GGUI visualization
- **Phase 2 (Waste Tracking):** Concentration advection-diffusion solver with metrics
- **Phase 3 Backend (WebSocket):** Server infrastructure fully functional
  - Fixed critical broadcasting bug (commit 205df3b)
  - All clients now receive 30 FPS frame updates
  - JSON and binary encoding with compression support
  - Multi-client support with proper async handling

### ✓ READY FOR NEXT STEPS
- **Unity Client (85% complete):** SPHStreamingClient.cs production-ready
  - WebSocket connection management
  - Particle rendering with GPU instancing
  - Color-coded concentration visualization (blue→yellow→red)
  - Real-time metrics display
  - Existing implementation in `unity_client/`

### → PHASE 1 (NEXT): Unity Project Setup
**Objective:** Create Unity 2021.3 project and verify streaming pipeline
**Time:** 2-3 hours
**Guide:** See [PHASE_1_SETUP.md](PHASE_1_SETUP.md)

### → PHASE 2 (AFTER Phase 1): Gradient Arrow Visualization
**Objective:** Add ∇C (gradient of concentration) vector field visualization
**Time:** 6-8 hours
**Key Features:**
- 5×5×5 grid of gradient arrows
- Arrow length scaled by |∇C|
- Color coding by magnitude (green→yellow→red)
- Toggle with `G` key

### → PHASE 3 (AFTER Phase 2): Volume Integral Visualizer
**Objective:** Add ∭ C dV (triple integral) animated Riemann sum
**Time:** 4-6 hours
**Key Features:**
- Translucent bounding boxes for preset regions
- Sequential particle highlighting
- Running total display
- Three preset regions (top, bottom, center)

### → PHASE 4 (AFTER Phase 3): Camera & UI Polish
**Time:** 3-4 hours
**Key Features:**
- Cinemachine camera presets
- Keyboard shortcuts (G, 1-3, SPACE, TAB, H, R)
- Large-format presentation UI
- Professional visual polish

### → PHASE 5 (FINAL): Testing & Demo Rehearsal
**Time:** 2-3 hours
**Deliverables:** Ready-to-present Calculus 3 demonstration

**Total Timeline:** 20-26 hours for complete MVP

## Quick Start - Testing WebSocket

After making changes, verify streaming still works:

```bash
# Terminal 1: Start Python server
python unity_streaming_main.py

# Terminal 2: Run WebSocket test
python test_websocket_broadcast.py

# Expected output: ✓ SUCCESS: Received 5/5 frames!
```

## Debugging Tips

**WebSocket Broadcast Issues:**
- See [PHASE_0_COMPLETE.md](PHASE_0_COMPLETE.md) for fix details
- Check `sph_fluid_sim/network/websocket_server.py` line 202-217
- Verify asyncio.gather() properly awaits all client sends

**Streaming Simulation:**
- Monitor client connections: Lines 218-220 in websocket_server.py
- Check particle data updates: Lines 131-140 in unity_streaming_main.py
- Verify broadcast rate: target_time / frames_received