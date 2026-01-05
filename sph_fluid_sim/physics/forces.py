"""
SPH Force Calculations

Implements pressure and viscosity forces using SPH formulations:
1. Pressure force: Symmetric gradient formulation (conserves momentum)
2. Viscosity force: Morris et al. formulation (ensures proper dissipation)
3. External forces: Gravity

These forces are combined to solve the Navier-Stokes equations in Lagrangian form.
"""

import taichi as ti
from ..config import *
from ..core.kernel import cubic_spline_gradient


@ti.kernel
def compute_pressure_force(
    positions: ti.template(),
    velocities: ti.template(),
    masses: ti.template(),
    densities: ti.template(),
    pressures: ti.template(),
    pressure_accelerations: ti.template(),
    neighbor_search: ti.template(),
    num_particles: int
):
    """
    Compute pressure force using symmetric SPH formulation.

    Mathematical formula (symmetric form - conserves momentum):
        aᵢ_pressure = -(1/ρᵢ) Σⱼ mⱼ (pᵢ/ρᵢ² + pⱼ/ρⱼ²) ∇W(rᵢⱼ, h)

    This formulation ensures exact momentum conservation and prevents
    spurious pressure oscillations.

    Args:
        positions: Particle positions
        velocities: Particle velocities
        masses: Particle masses
        densities: Particle densities
        pressures: Particle pressures
        pressure_accelerations: Output acceleration from pressure
        neighbor_search: Neighbor search structure
        num_particles: Number of particles
    """
    for i in range(num_particles):
        acc = ti.math.vec3(0.0, 0.0, 0.0)
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

                                if i != j:  # Skip self-interaction
                                    # Check if within support radius (2h)
                                    r_ij = pos_i - positions[j]
                                    dist = r_ij.norm()

                                    if dist < 2.0 * SMOOTHING_LENGTH:
                                        # Kernel gradient
                                        grad_W = cubic_spline_gradient(r_ij, SMOOTHING_LENGTH)

                                        # Symmetric pressure term: (pᵢ/ρᵢ² + pⱼ/ρⱼ²)
                                        pressure_term = (pressures[i] / (densities[i] * densities[i]) +
                                                        pressures[j] / (densities[j] * densities[j]))

                                        # Pressure force contribution
                                        acc += -masses[j] * pressure_term * grad_W

        # Store pressure acceleration
        pressure_accelerations[i] = acc


@ti.kernel
def compute_viscosity_force(
    positions: ti.template(),
    velocities: ti.template(),
    masses: ti.template(),
    densities: ti.template(),
    viscosity_accelerations: ti.template(),
    neighbor_search: ti.template(),
    num_particles: int
):
    """
    Compute viscosity force using Morris et al. formulation.

    Mathematical formula:
        aᵢ_viscosity = μ Σⱼ (mⱼ/ρⱼ) (vⱼ - vᵢ) · [2(rᵢⱼ · ∇W) / (|rᵢⱼ|² + ε²)]

    where ε = 0.01h prevents division by zero.

    This formulation ensures proper viscous dissipation without introducing
    artificial damping.

    Args:
        positions: Particle positions
        velocities: Particle velocities
        masses: Particle masses
        densities: Particle densities
        viscosity_accelerations: Output acceleration from viscosity
        neighbor_search: Neighbor search structure
        num_particles: Number of particles
    """
    epsilon_sq = EPSILON_VISCOSITY * EPSILON_VISCOSITY

    for i in range(num_particles):
        acc = ti.math.vec3(0.0, 0.0, 0.0)
        pos_i = positions[i]
        vel_i = velocities[i]
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

                                if i != j:  # Skip self-interaction
                                    # Check if within support radius (2h)
                                    r_ij = pos_i - positions[j]
                                    dist = r_ij.norm()

                                    if dist < 2.0 * SMOOTHING_LENGTH:
                                        # Velocity difference
                                        v_ij = velocities[j] - vel_i

                                        # Kernel gradient
                                        grad_W = cubic_spline_gradient(r_ij, SMOOTHING_LENGTH)

                                        # Morris viscosity formula
                                        r_dot_grad = r_ij.dot(grad_W)
                                        r_norm_sq = r_ij.norm_sqr() + epsilon_sq

                                        # Viscosity term
                                        visc_term = 2.0 * (masses[j] / densities[j]) * r_dot_grad / r_norm_sq

                                        # Viscosity force contribution
                                        acc += DYNAMIC_VISCOSITY * visc_term * v_ij

        # Store viscosity acceleration
        viscosity_accelerations[i] = acc


@ti.kernel
def compute_buoyancy_force(
    positions: ti.template(),
    masses: ti.template(),
    densities: ti.template(),
    particle_types: ti.template(),
    buoyancy_accelerations: ti.template(),
    neighbor_search: ti.template(),
    num_particles: int,
    waste_density: float
):
    """
    Compute buoyancy force for multi-density particles.

    Mathematical formula:
        F_buoyancy = (ρ_local - ρ_particle) * g * V

    where:
        ρ_local = local fluid density (from SPH summation of neighbors)
        ρ_particle = particle's own density (WASTE_DENSITY or REST_DENSITY)
        V = particle volume = m/ρ_particle

    This force causes:
    - Oil particles (ρ_waste < ρ_water) to rise (positive buoyancy)
    - Heavy waste (ρ_waste > ρ_water) to sink (negative buoyancy)

    Args:
        positions: Particle positions
        masses: Particle masses
        densities: Particle densities
        particle_types: Particle type field (clean/waste)
        buoyancy_accelerations: Output acceleration from buoyancy
        neighbor_search: Neighbor search structure
        num_particles: Number of particles
        waste_density: Density of waste particles
    """
    for i in range(num_particles):
        acc = ti.math.vec3(0.0, 0.0, 0.0)

        # Only apply buoyancy to waste particles (multi-density)
        if particle_types[i] == PARTICLE_TYPE_FLUID_WASTE:
            # Local fluid density (from neighbors, represents ambient fluid)
            local_density = densities[i]

            # Particle's intrinsic density
            particle_density = waste_density

            # Particle volume
            volume = masses[i] / particle_density

            # Buoyancy force: F = (ρ_fluid - ρ_particle) * g * V
            density_difference = local_density - particle_density

            # Buoyancy acceleration: a = F/m = (ρ_fluid - ρ_particle) * g * V / m
            acc = density_difference * GRAVITY * volume / masses[i]

        buoyancy_accelerations[i] = acc


@ti.kernel
def compute_total_acceleration(
    pressure_accelerations: ti.template(),
    viscosity_accelerations: ti.template(),
    buoyancy_accelerations: ti.template(),
    total_accelerations: ti.template(),
    num_particles: int,
    include_buoyancy: int
):
    """
    Combine all forces to compute total acceleration.

    Total acceleration:
        a_total = a_pressure + a_viscosity + a_buoyancy + g

    Args:
        pressure_accelerations: Acceleration from pressure
        viscosity_accelerations: Acceleration from viscosity
        buoyancy_accelerations: Acceleration from buoyancy
        total_accelerations: Output total acceleration
        num_particles: Number of particles
        include_buoyancy: Flag to include buoyancy (1=yes, 0=no)
    """
    for i in range(num_particles):
        # Sum all accelerations
        total_acc = (
            pressure_accelerations[i] +
            viscosity_accelerations[i] +
            GRAVITY  # External force (gravity)
        )

        # Add buoyancy if enabled
        if include_buoyancy == 1:
            total_acc += buoyancy_accelerations[i]

        total_accelerations[i] = total_acc
