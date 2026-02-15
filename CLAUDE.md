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

### ✓ COMPLETE — Phases 0-3 (Python Backend)
- **Phase 0 (WebSocket Fix):** Critical broadcasting bug fixed (commit 205df3b)
- **Phase 1 (Core SPH):** Full simulation with GGUI visualization
- **Phase 2 (Waste Tracking):** Concentration advection-diffusion solver with metrics
- **Phase 3 (Unity Streaming):** WebSocket server at `ws://localhost:8765`, JSON/binary encoding, compression, multi-client support, 30 FPS
- **Python verified operational:** All 4 tests pass (`python test_all_phases.py`)

### ✓ CODE COMPLETE — Phase 4 (Camera & UI Polish)
All Phase 4 scripts written and committed. **Awaiting Unity testing.**

**New files created:**
- `unity_client/Assets/Scripts/CameraPresetManager.cs` — 4 camera presets (Overview, Close-Up, Side, Top-Down) cycled via TAB key
- `unity_client/Assets/Scripts/PresentationController.cs` — SPACE (pause/resume with yellow "⏸ PAUSED" indicator), H (UI toggle), R (reset)
- `unity_client/Assets/Scripts/PresentationUIManager.cs` — Adaptive font scaling (22-48px based on screen height / 1080 ratio), percentage-based panel layout

**Files modified:**
- `unity_client/SPHStreamingClient.cs` — Conditional compilation (`#if NATIVEWEBSOCKET_INSTALLED`), adaptive UI via PresentationUIManager, gradients field + position/concentration caching
- `unity_client/Assets/Scripts/GradientVisualizer.cs` — Fixed Vector3.Lerp type mismatch (now component-wise Mathf.Lerp), adaptive UI layout
- `unity_client/Assets/Scripts/VolumeIntegralCalculator.cs` — Adaptive UI layout via PresentationUIManager
- `unity_client/Assets/Scripts/SPHSetup.cs` — Auto-wires Phase 4 components via ConfigurePhase4Components()

**Keyboard shortcuts (full set):**
| Key | Action |
|-----|--------|
| TAB | Cycle camera presets (Overview → Close-Up → Side → Top-Down) |
| SPACE | Pause/resume simulation |
| H | Toggle UI panels visibility |
| R | Reset camera to default view |
| G | Toggle gradient arrow visualization |
| 1/2/3 | Volume integral preset regions (top/bottom/center) |

**Known issue:** NativeWebSocket package NOT yet installed in Unity. Must install via Package Manager → + button → git URL: `https://github.com/endel/NativeWebSocket.git#upm`. Code compiles without it due to conditional compilation directives, but WebSocket streaming won't function until installed.

### → NEXT: Phase 5 (Testing & Demo Rehearsal)
**Objective:** Verify all features end-to-end, rehearse Calculus 3 classroom demo
**Prerequisites:**
1. Install NativeWebSocket package in Unity
2. Verify zero compilation errors
3. Test Python→Unity streaming pipeline
4. Test all keyboard shortcuts
5. Verify UI readability at projector resolution (1080p-4K)

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

**Resolved Bugs (Phase 4 development):**
- `physics/__init__.py` was deleted from git — restored (required for Python module imports)
- `SPHStreamingClient.cs` missing `gradients` field in SimulationData — added (Python was sending gradient data but Unity ignored it)
- `GradientVisualizer.cs` line 109: `Vector3.Lerp` called with Vector3 as 3rd arg (requires float) — fixed with component-wise `Mathf.Lerp`
- Unity manifest.json: Removed invalid module references (`com.unity.modules.core`, `.lighting`, `.spriteanimation`, `.sprites`), restored `com.unity.modules.imgui` (required for OnGUI)
- NativeWebSocket not found: Wrapped all WebSocket code in `#if NATIVEWEBSOCKET_INSTALLED` conditional compilation

## Session Continuation Context

This project was developed across multiple Claude Code sessions. Key context:
- **User environment:** Python operational, Unity available but with limited testing capability
- **Purpose:** Calculus 3 classroom demonstration (SPH fluid sim with waste concentration tracking)
- **Current state:** Phase 4 code complete, needs NativeWebSocket install + Unity testing before Phase 5
- **User preference:** Pragmatic approach — conditional compilation to unblock development when dependencies unavailable