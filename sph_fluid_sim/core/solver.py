"""
Main WCSPH Solver - Orchestrates the entire simulation pipeline.

This is the main solver class that coordinates all SPH computation modules:
- Neighbor search
- Density and pressure computation
- Force calculations
- Time integration
- Boundary enforcement
"""

import taichi as ti
from ..config import *
from ..core.neighbor_search import NeighborSearch
from ..physics.equation_of_state import compute_density, compute_pressure
from ..physics.forces import compute_pressure_force, compute_viscosity_force, compute_total_acceleration
from ..physics.boundary import enforce_boundary
from ..core.integrator import integrate_step, compute_adaptive_timestep
from ..utils.initialization import initialize_dam_break


class WCSPHSolver:
    """Weakly Compressible SPH Solver for 3D fluid simulation."""

    def __init__(self, num_particles=NUM_PARTICLES):
        """
        Initialize WCSPH solver.

        Args:
            num_particles: Number of fluid particles
        """
        self.num_particles = num_particles

        # Taichi fields - Structure of Arrays for GPU optimization
        self.positions = ti.Vector.field(3, dtype=ti.f32, shape=num_particles)
        self.velocities = ti.Vector.field(3, dtype=ti.f32, shape=num_particles)
        self.accelerations = ti.Vector.field(3, dtype=ti.f32, shape=num_particles)

        self.masses = ti.field(dtype=ti.f32, shape=num_particles)
        self.densities = ti.field(dtype=ti.f32, shape=num_particles)
        self.pressures = ti.field(dtype=ti.f32, shape=num_particles)

        self.pressure_accelerations = ti.Vector.field(3, dtype=ti.f32, shape=num_particles)
        self.viscosity_accelerations = ti.Vector.field(3, dtype=ti.f32, shape=num_particles)

        # Neighbor search
        self.neighbor_search = NeighborSearch(num_particles, GRID_RESOLUTION)

        # Simulation time
        self.current_time = 0.0

    def initialize(self):
        """Initialize particle positions and velocities for dam break."""
        initialize_dam_break(
            self.positions,
            self.velocities,
            self.masses,
            self.num_particles
        )

    def step(self, dt: float):
        """
        Perform one simulation timestep.

        Pipeline:
        1. Update neighbor grid
        2. Compute density
        3. Compute pressure (Tait EOS)
        4. Compute pressure forces
        5. Compute viscosity forces
        6. Combine forces
        7. Integrate (update positions and velocities)
        8. Enforce boundaries

        Args:
            dt: Timestep
        """
        # 1. Update spatial hash grid for neighbor finding
        self.neighbor_search.build_grid(self.positions)

        # 2. Compute densities using SPH summation
        compute_density(
            self.positions,
            self.velocities,
            self.masses,
            self.densities,
            self.neighbor_search,
            self.num_particles
        )

        # 3. Compute pressures using Tait EOS
        compute_pressure(
            self.densities,
            self.pressures,
            self.num_particles
        )

        # 4. Compute pressure forces
        compute_pressure_force(
            self.positions,
            self.velocities,
            self.masses,
            self.densities,
            self.pressures,
            self.pressure_accelerations,
            self.neighbor_search,
            self.num_particles
        )

        # 5. Compute viscosity forces
        compute_viscosity_force(
            self.positions,
            self.velocities,
            self.masses,
            self.densities,
            self.viscosity_accelerations,
            self.neighbor_search,
            self.num_particles
        )

        # 6. Combine all forces
        # Note: Buoyancy field may not exist in Phase 1 simulations
        # Pass dummy field and flag=0 to disable buoyancy
        compute_total_acceleration(
            self.pressure_accelerations,
            self.viscosity_accelerations,
            self.pressure_accelerations,  # Dummy field (not used when flag=0)
            self.accelerations,
            self.num_particles,
            0  # include_buoyancy = 0 (disabled)
        )

        # 7. Time integration (symplectic Euler)
        integrate_step(
            self.positions,
            self.velocities,
            self.accelerations,
            self.num_particles,
            dt
        )

        # 8. Enforce boundary conditions
        enforce_boundary(
            self.positions,
            self.velocities,
            self.num_particles
        )

        # Update simulation time
        self.current_time += dt

    def compute_timestep(self) -> float:
        """
        Compute adaptive timestep using CFL condition.

        Returns:
            Adaptive timestep
        """
        return compute_adaptive_timestep(
            self.velocities,
            self.accelerations,
            self.num_particles
        )
