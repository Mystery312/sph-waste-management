"""
Equation of State - Tait EOS for Weakly Compressible SPH

Implements the Tait equation of state to relate fluid density to pressure.
This allows WCSPH to maintain near-incompressibility (~1% density variation)
while using explicit time integration.

Tait EOS: p = B * ((ρ/ρ₀)^γ - 1)

where:
    B = c_s² * ρ₀ / γ (stiffness parameter)
    γ = 7 (exponent for water)
    c_s = sound speed (~10× max velocity)
"""

import taichi as ti
from ..config import *
from ..core.kernel import cubic_spline_kernel


@ti.kernel
def compute_density(
    positions: ti.template(),
    velocities: ti.template(),
    masses: ti.template(),
    densities: ti.template(),
    neighbor_search: ti.template(),
    num_particles: int
):
    """
    Compute particle densities using SPH summation.

    Mathematical formula:
        ρᵢ = Σⱼ mⱼ W(|rᵢ - rⱼ|, h)

    Args:
        positions: Particle positions
        velocities: Particle velocities
        masses: Particle masses
        densities: Output density field
        neighbor_search: Neighbor search structure
        num_particles: Number of particles
    """
    for i in range(num_particles):
        density_sum = 0.0
        pos_i = positions[i]
        cell_idx = neighbor_search.particle_cell_index[i]

        # Decode 1D cell index to 3D coordinates
        grid_res = neighbor_search.grid_resolution
        cell_z = cell_idx // (grid_res * grid_res)
        temp = cell_idx % (grid_res * grid_res)
        cell_y = temp // grid_res
        cell_x = temp % grid_res

        # Search 3×3×3 stencil (27 cells including self)
        for offset_x in ti.static(range(-1, 2)):
            for offset_y in ti.static(range(-1, 2)):
                for offset_z in ti.static(range(-1, 2)):
                    # Neighbor cell coordinates
                    neighbor_cell_x = cell_x + offset_x
                    neighbor_cell_y = cell_y + offset_y
                    neighbor_cell_z = cell_z + offset_z

                    # Check if neighbor cell is within grid bounds
                    if (neighbor_cell_x >= 0 and neighbor_cell_x < grid_res and
                        neighbor_cell_y >= 0 and neighbor_cell_y < grid_res and
                        neighbor_cell_z >= 0 and neighbor_cell_z < grid_res):

                        # Convert to 1D index
                        neighbor_cell_idx = (neighbor_cell_x +
                                           neighbor_cell_y * grid_res +
                                           neighbor_cell_z * grid_res * grid_res)

                        # Iterate over particles in neighbor cell
                        num_particles_in_cell = neighbor_search.cell_particle_count[neighbor_cell_idx]

                        for k in range(num_particles_in_cell):
                            if k < neighbor_search.max_particles_per_cell:
                                j = neighbor_search.cell_particle_list[neighbor_cell_idx, k]

                                # Check if within support radius (2h)
                                r_ij = pos_i - positions[j]
                                dist = r_ij.norm()

                                if dist < 2.0 * SMOOTHING_LENGTH:
                                    # SPH kernel
                                    W = cubic_spline_kernel(r_ij, SMOOTHING_LENGTH)

                                    # Accumulate: ρᵢ = Σⱼ mⱼ W(rᵢⱼ, h)
                                    density_sum += masses[j] * W

        # Store density
        densities[i] = density_sum

        # Clamp density to prevent extreme values
        # This improves numerical stability
        densities[i] = ti.max(
            MIN_DENSITY_FACTOR * REST_DENSITY,
            ti.min(densities[i], MAX_DENSITY_FACTOR * REST_DENSITY)
        )


@ti.kernel
def compute_pressure(
    densities: ti.template(),
    pressures: ti.template(),
    num_particles: int
):
    """
    Compute particle pressures using Tait equation of state.

    Tait EOS:
        p = B * ((ρ/ρ₀)^γ - 1)

    where:
        B = c_s² * ρ₀ / γ  (stiffness parameter)
        γ = 7  (exponent for water)

    Args:
        densities: Particle densities
        pressures: Output pressure field
        num_particles: Number of particles
    """
    for i in range(num_particles):
        # Density ratio
        rho_ratio = densities[i] / REST_DENSITY

        # Tait equation: p = B * ((ρ/ρ₀)^γ - 1)
        pressure = STIFFNESS_B * (ti.pow(rho_ratio, GAMMA) - 1.0)

        # Clamp negative pressures to prevent tensile instability
        # Negative pressures can cause particle clustering artifacts
        pressures[i] = ti.max(0.0, pressure)
