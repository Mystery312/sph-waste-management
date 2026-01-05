"""
Physical constants and simulation parameters for WCSPH fluid dynamics simulation.

This module contains all physical constants, numerical parameters, and configuration
settings for the 3D fluid simulation and waste tracking system.
"""

import taichi as ti
import math

# ============================================================================
# Physical Constants
# ============================================================================

# Gravity vector (m/s²)
GRAVITY = ti.math.vec3(0.0, -9.81, 0.0)

# Fluid properties (water at 20°C)
REST_DENSITY = 1000.0  # kg/m³
DYNAMIC_VISCOSITY = 0.001  # Pa·s (1 mPa·s for water)
KINEMATIC_VISCOSITY = DYNAMIC_VISCOSITY / REST_DENSITY  # m²/s

# ============================================================================
# Tait Equation of State Parameters
# ============================================================================

# Exponent for water in Tait EOS
GAMMA = 7.0

# Maximum expected velocity (for sound speed calculation)
MAX_VELOCITY_ESTIMATE = 10.0  # m/s

# Sound speed: c_s = 10 * v_max ensures ~1% compressibility
# This prevents excessive density variations while maintaining stability
SOUND_SPEED = 10.0 * MAX_VELOCITY_ESTIMATE  # 100 m/s

# Stiffness parameter: B = c_s² * ρ₀ / γ
# Used in Tait EOS: p = B * ((ρ/ρ₀)^γ - 1)
STIFFNESS_B = (SOUND_SPEED**2 * REST_DENSITY) / GAMMA

# ============================================================================
# Particle Parameters
# ============================================================================

# Number of fluid particles
NUM_PARTICLES = 8000

# Particle spacing (m) - determines resolution
PARTICLE_SPACING = 0.05  # 5 cm spacing

# Smoothing length: h = 1.2 * particle_spacing
# This is the characteristic length scale for SPH kernel support
SMOOTHING_LENGTH = 1.2 * PARTICLE_SPACING  # 0.06 m

# Particle mass (kg) - calculated from rest density and particle volume
PARTICLE_MASS = REST_DENSITY * (PARTICLE_SPACING**3)

# ============================================================================
# Time Integration Parameters
# ============================================================================

# CFL coefficient for adaptive timestep (safety factor)
CFL_COEFFICIENT = 0.25

# Maximum allowed timestep (s)
MAX_TIMESTEP = 0.001  # 1 ms

# Minimum timestep (s) - numerical floor to prevent stalling
MIN_TIMESTEP = 1e-6  # 1 microsecond

# ============================================================================
# Simulation Domain (Box Container)
# ============================================================================

# Box minimum corner (m)
BOX_MIN = ti.math.vec3(0.0, 0.0, 0.0)

# Box maximum corner (m) - 1m cube
BOX_MAX = ti.math.vec3(1.0, 1.0, 1.0)

# ============================================================================
# Spatial Hashing Grid Parameters
# ============================================================================

# Grid cell size: 2 * smoothing_length (kernel support radius)
# This ensures each particle only needs to search adjacent cells
CELL_SIZE = 2.0 * SMOOTHING_LENGTH  # 0.12 m

# Grid resolution (number of cells per dimension)
# Calculated to cover the entire simulation domain
GRID_RESOLUTION = int(math.ceil((BOX_MAX.x - BOX_MIN.x) / CELL_SIZE))

# Total number of grid cells
NUM_GRID_CELLS = GRID_RESOLUTION**3

# ============================================================================
# Visualization Parameters
# ============================================================================

# Window dimensions for GGUI
WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768

# Particle render radius for visualization
PARTICLE_RENDER_RADIUS = 0.01  # 1 cm

# ============================================================================
# Data Export Parameters
# ============================================================================

# Export interval (s) - save data every 10ms
EXPORT_INTERVAL = 0.01

# Export format: "vtk" or "csv"
EXPORT_FORMAT = "vtk"

# Output directory
OUTPUT_DIR = "output/frames"

# ============================================================================
# Waste Tracking Parameters (Phase 2)
# ============================================================================

# Waste density (kg/m³)
# For oil (lighter than water): 900 kg/m³
# For heavy waste (denser than water): 1100 kg/m³
WASTE_DENSITY = 900.0  # Default to oil

# Diffusion coefficient for dissolved pollutants (m²/s)
DIFFUSION_COEFFICIENT = 1e-9  # Molecular diffusion in water

# Particle type constants
PARTICLE_TYPE_FLUID_CLEAN = 0
PARTICLE_TYPE_FLUID_WASTE = 1
PARTICLE_TYPE_BOUNDARY = 2

# Contamination thresholds for zone detection
CONTAMINATION_THRESHOLD_LOW = 0.1  # 10% concentration
CONTAMINATION_THRESHOLD_MEDIUM = 0.5  # 50% concentration
CONTAMINATION_THRESHOLD_HIGH = 0.9  # 90% concentration

# ============================================================================
# Numerical Stability Parameters
# ============================================================================

# Epsilon for preventing division by zero in viscosity calculation
EPSILON_VISCOSITY = 0.01 * SMOOTHING_LENGTH

# Density clamping bounds (prevent extreme values)
MIN_DENSITY_FACTOR = 0.5  # 50% of rest density
MAX_DENSITY_FACTOR = 2.0  # 200% of rest density

# Boundary collision damping factor
BOUNDARY_DAMPING = 0.5  # 50% energy loss on collision

# ============================================================================
# Helper Functions
# ============================================================================

def print_simulation_config():
    """Print simulation configuration for debugging."""
    print("=" * 60)
    print("3D WCSPH Fluid Simulation Configuration")
    print("=" * 60)
    print(f"Particles: {NUM_PARTICLES}")
    print(f"Particle spacing: {PARTICLE_SPACING * 1000:.1f} mm")
    print(f"Smoothing length: {SMOOTHING_LENGTH * 1000:.1f} mm")
    print(f"Domain: ({BOX_MIN.x}, {BOX_MIN.y}, {BOX_MIN.z}) to ({BOX_MAX.x}, {BOX_MAX.y}, {BOX_MAX.z}) m")
    print(f"Grid resolution: {GRID_RESOLUTION}³ = {NUM_GRID_CELLS} cells")
    print(f"Sound speed: {SOUND_SPEED} m/s")
    print(f"Max timestep: {MAX_TIMESTEP * 1000:.3f} ms")
    print(f"Viscosity: {DYNAMIC_VISCOSITY * 1000:.3f} mPa·s")
    print("=" * 60)
