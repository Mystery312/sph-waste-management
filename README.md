# 3D Fluid Dynamics Simulation - Waste Management System

A modular Python project implementing a 3D Weakly Compressible SPH (Smoothed Particle Hydrodynamics) simulation using Taichi Lang for GPU acceleration. Designed as a waste management particle concentration tracker for monitoring pollutant dispersion in water.

## Features

### Phase 1: Base Physics Engine ✅
- ✅ GPU-accelerated 3D fluid simulation with 8,000 particles
- ✅ Weakly Compressible SPH (WCSPH) with Tait equation of state
- ✅ Real Navier-Stokes equations (pressure + viscosity forces)
- ✅ Adaptive CFL timestep for stability
- ✅ Dam break scenario
- ✅ Real-time GGUI visualization
- ✅ VTK export for ParaView post-processing

### Phase 2: Waste Tracking ✅
- ✅ Multi-density particle tracking (oil/heavy waste)
- ✅ Concentration field computation
- ✅ Advection-diffusion for pollutants
- ✅ Contamination zone detection
- ✅ Color-coded visualization (Blue→Yellow→Red)
- ✅ Real-time metrics (mean, variance, mixing index)
- ✅ Center of mass tracking
- ⏳ Buoyancy forces (planned for Phase 2.5)

### Phase 3: Unity Frontend & Real-Time Streaming ✅
- ✅ WebSocket server for real-time data streaming
- ✅ Unity client with C# scripts
- ✅ 30 FPS real-time visualization
- ✅ Multi-client support
- ✅ Configurable compression and decimation
- ✅ JSON and binary streaming modes
- ⏳ Advanced metrics (heatmaps, flow statistics) - In Progress
- ⏳ Time-series data tracking - Planned
- ⏳ Contamination alerts - Planned

## Installation

### Requirements
- Python 3.10+
- NVIDIA GPU with CUDA support (or CPU fallback)

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run Phase 1 simulation
python main.py
```

## Usage

### Phase 1: Running the Base Simulation

```bash
python main.py
```

**Controls:**
- **ESC**: Exit simulation
- **Right-click + drag**: Rotate camera
- **Mouse wheel**: Zoom

**Output:**
- Real-time 3D visualization window
- VTK files exported to `output/frames/` every 50ms
- Console progress indicators

### Phase 2: Running Waste Tracking Simulation

```bash
python waste_tracking_main.py
```

**New Features:**
- Color-coded particles: Blue (clean) → Yellow (mixed) → Red (waste)
- Real-time concentration metrics printed to console
- Contamination zone analysis (low/medium/high thresholds)
- Enhanced VTK export with concentration field data

**Console Output:**
- Concentration statistics (mean, max, min, variance)
- Mixing index (0 = unmixed, 1 = perfectly mixed)
- Center of mass tracking
- Contamination zone volumes and percentages

### Phase 3: Real-Time Unity Streaming

```bash
python unity_streaming_main.py
```

**New Features:**
- WebSocket server streaming at 30 FPS
- Unity3D client for interactive visualization
- Multi-client support (connect multiple Unity instances)
- Configurable data compression and decimation
- Real-time metrics overlay

**Setup Unity Client:**
See [unity_client/README_Unity.md](unity_client/README_Unity.md) for complete Unity setup instructions.

### Viewing Results in ParaView

**For Phase 1 (Basic Simulation):**
1. Open ParaView
2. File → Open → Select `output/frames/particles_*.vtk`
3. Apply
4. Use "Glyph" filter to visualize particles as spheres
5. Color by "density" or "pressure"
6. Play animation to see time evolution

**For Phase 2 (Waste Tracking):**
1. Open ParaView
2. File → Open → Select `output/frames/waste_particles_*.vtk`
3. Apply
4. Use "Glyph" filter to visualize particles as spheres
5. Color by "concentration" field (0.0 = clean, 1.0 = pure waste)
6. Play animation to see pollutant dispersion and mixing
7. Optional: Apply "Threshold" filter to isolate contaminated regions

## Project Structure

```
Waste Management/
├── sph_fluid_sim/           # Main package
│   ├── config.py            # Physical constants
│   ├── core/                # Core SPH algorithms
│   │   ├── kernel.py        # Cubic spline kernel
│   │   ├── solver.py        # Main WCSPH solver
│   │   ├── neighbor_search.py  # Spatial hashing
│   │   └── integrator.py    # Time integration
│   ├── physics/             # Physics modules
│   │   ├── equation_of_state.py  # Tait EOS
│   │   ├── forces.py        # Pressure & viscosity
│   │   └── boundary.py      # Boundary conditions
│   ├── tracking/            # Waste tracking (Phase 2)
│   │   ├── concentration.py # Advection-diffusion solver
│   │   └── __init__.py
│   ├── analytics/           # Metrics and analysis (Phase 2)
│   │   ├── metrics.py       # Contamination zone detection
│   │   └── __init__.py
│   ├── network/             # Real-time streaming (Phase 3) ✨NEW✨
│   │   ├── websocket_server.py # WebSocket server
│   │   └── __init__.py
│   ├── utils/               # Utilities
│   │   ├── initialization.py  # Dam break setup
│   │   └── export.py        # VTK/CSV export
│   └── visualization/       # Visualization
│       ├── renderer.py      # GGUI renderer (Phase 1)
│       └── waste_renderer.py # Color-coded renderer (Phase 2)
├── unity_client/            # Unity3D client (Phase 3) ✨NEW✨
│   ├── SPHStreamingClient.cs # Unity C# client script
│   └── README_Unity.md      # Unity setup guide
├── main.py                  # Phase 1 entry point
├── waste_tracking_main.py   # Phase 2 entry point
├── unity_streaming_main.py  # Phase 3 entry point ✨NEW✨
├── requirements.txt         # Dependencies
├── QUICKSTART.md            # Quick start guide ✨NEW✨
└── output/                  # Simulation output
    ├── frames/              # VTK files
    └── logs/                # Logs
```

## Physics

### SPH Formulations

**Density (summation):**
```
ρᵢ = Σⱼ mⱼ W(|rᵢ - rⱼ|, h)
```

**Tait Equation of State:**
```
p = B * ((ρ/ρ₀)^γ - 1)
where B = c_s² * ρ₀ / γ, γ = 7
```

**Pressure Force (symmetric):**
```
aᵢ = -Σⱼ mⱼ (pᵢ/ρᵢ² + pⱼ/ρⱼ²) ∇W(rᵢⱼ, h)
```

**Viscosity Force (Morris et al.):**
```
aᵢ = μ Σⱼ (mⱼ/ρⱼ) (vⱼ - vᵢ) · [2(rᵢⱼ · ∇W) / (|rᵢⱼ|² + ε²)]
```

### Parameters

- **Fluid:** Water at 20°C
- **Rest Density:** 1000 kg/m³
- **Dynamic Viscosity:** 0.001 Pa·s
- **Gravity:** -9.81 m/s²
- **Sound Speed:** 100 m/s (10× max velocity)
- **Particle Count:** 8,000
- **Particle Spacing:** 0.05 m
- **Smoothing Length:** 0.06 m
- **Domain:** 1m × 1m × 1m box

## Performance

- **GPU (NVIDIA RTX):** ~60 FPS @ 8,000 particles
- **CPU:** ~10 FPS @ 8,000 particles
- **Memory:** ~100 MB GPU memory

## Configuration

Edit `sph_fluid_sim/config.py` to modify:
- Particle count
- Physical constants (density, viscosity)
- Domain size
- Simulation parameters

## Troubleshooting

**"No module named taichi"**
```bash
pip install taichi>=1.6.0
```

**"CUDA not available"**
Change `ti.init(arch=ti.cuda)` to `ti.init(arch=ti.cpu)` in `main.py`

**Particles exploding**
- Reduce timestep: Increase `CFL_COEFFICIENT` in config.py
- Increase sound speed: Modify `SOUND_SPEED` in config.py

**Slow performance**
- Reduce particle count: Modify `NUM_PARTICLES` in config.py
- Use GPU: Ensure `ti.init(arch=ti.cuda)`

## Next Steps

### Phase 2: Waste Tracking
Run after Phase 1 is working:
```bash
python waste_tracking_main.py  # (To be implemented)
```

### Phase 3: Unity Frontend
1. Setup Unity project (see `unity_client/README_Unity.md`)
2. Start Python WebSocket server
3. Connect Unity client for real-time visualization

## License

MIT License - Feel free to extend for research and industrial applications.

## Citation

If you use this code in research, please cite:
```
@software{sph_waste_management_2024,
  title={3D SPH Fluid Simulation for Waste Management},
  author={Your Name},
  year={2024},
  url={https://github.com/yourusername/waste-management-sph}
}
```

## References

- Monaghan, J. J. (2005). Smoothed particle hydrodynamics
- Becker & Teschner (2007). Weakly compressible SPH for free surface flows
- Morris et al. (1997). Modeling low Reynolds number incompressible flows

## Contact

For questions or collaborations, please open an issue or contact [your email].
