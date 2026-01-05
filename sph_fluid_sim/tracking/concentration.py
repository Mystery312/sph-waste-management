"""
Concentration Field Tracking and Advection-Diffusion

Implements passive scalar transport for waste particle concentration:
- Advection: Concentration moves with fluid velocity
- Diffusion: Molecular/turbulent diffusion spreads concentration
- Mass conservation: Total concentration is conserved

Mathematical formulation:
    dC/dt + v·∇C = D∇²C

where:
    C = concentration (0 = clean, 1 = pure waste)
    v = fluid velocity
    D = diffusion coefficient
"""

import taichi as ti
from ..config import *
from ..core.kernel import cubic_spline_kernel, cubic_spline_gradient


@ti.data_oriented
class ConcentrationTracker:
    """
    Tracks waste particle concentration using advection-diffusion.
    """

    def __init__(self, num_particles: int):
        """
        Initialize concentration tracker.

        Args:
            num_particles: Total number of particles
        """
        self.num_particles = num_particles

        # Concentration field (0.0 = clean, 1.0 = pure waste)
        self.concentration = ti.field(dtype=ti.f32, shape=num_particles)

        # Particle type field
        self.particle_type = ti.field(dtype=ti.i32, shape=num_particles)

        # Concentration gradient (for advection term)
        self.concentration_gradient = ti.Vector.field(3, dtype=ti.f32, shape=num_particles)

        # Concentration Laplacian (for diffusion term)
        self.concentration_laplacian = ti.field(dtype=ti.f32, shape=num_particles)

    @ti.kernel
    def initialize_clean_fluid(self):
        """Initialize all particles as clean water."""
        for i in range(self.num_particles):
            self.concentration[i] = 0.0
            self.particle_type[i] = PARTICLE_TYPE_FLUID_CLEAN

    @ti.kernel
    def initialize_waste_particles(self, start_idx: int, end_idx: int):
        """
        Mark particles as waste (concentration = 1.0).

        Args:
            start_idx: Starting particle index
            end_idx: Ending particle index (exclusive)
        """
        for i in range(start_idx, end_idx):
            if i < self.num_particles:
                self.concentration[i] = 1.0
                self.particle_type[i] = PARTICLE_TYPE_FLUID_WASTE

    @ti.kernel
    def compute_concentration_gradient(
        self,
        positions: ti.template(),
        masses: ti.template(),
        densities: ti.template(),
        neighbor_search: ti.template()
    ):
        """
        Compute concentration gradient using SPH formulation.

        Mathematical formula:
            ∇Cᵢ = ρᵢ Σⱼ mⱼ (Cⱼ - Cᵢ)/ρⱼ² ∇W(rᵢⱼ, h)

        Args:
            positions: Particle positions
            masses: Particle masses
            densities: Particle densities
            neighbor_search: Neighbor search structure
        """
        for i in range(self.num_particles):
            grad = ti.math.vec3(0.0, 0.0, 0.0)
            pos_i = positions[i]
            C_i = self.concentration[i]
            rho_i = densities[i]
            cell_idx = neighbor_search.particle_cell_index[i]

            # Decode 1D cell index to 3D coordinates
            grid_res = neighbor_search.grid_resolution
            cell_z = cell_idx // (grid_res * grid_res)
            temp = cell_idx % (grid_res * grid_res)
            cell_y = temp // grid_res
            cell_x = temp % grid_res

            # Search 3×3×3 stencil
            for offset_x in ti.static(range(-1, 2)):
                for offset_y in ti.static(range(-1, 2)):
                    for offset_z in ti.static(range(-1, 2)):
                        neighbor_cell_x = cell_x + offset_x
                        neighbor_cell_y = cell_y + offset_y
                        neighbor_cell_z = cell_z + offset_z

                        if (neighbor_cell_x >= 0 and neighbor_cell_x < grid_res and
                            neighbor_cell_y >= 0 and neighbor_cell_y < grid_res and
                            neighbor_cell_z >= 0 and neighbor_cell_z < grid_res):

                            neighbor_cell_idx = (neighbor_cell_x +
                                               neighbor_cell_y * grid_res +
                                               neighbor_cell_z * grid_res * grid_res)

                            num_particles_in_cell = neighbor_search.cell_particle_count[neighbor_cell_idx]

                            for k in range(num_particles_in_cell):
                                if k < neighbor_search.max_particles_per_cell:
                                    j = neighbor_search.cell_particle_list[neighbor_cell_idx, k]

                                    if i != j:
                                        r_ij = pos_i - positions[j]
                                        dist = r_ij.norm()

                                        if dist < 2.0 * SMOOTHING_LENGTH:
                                            # Kernel gradient
                                            grad_W = cubic_spline_gradient(r_ij, SMOOTHING_LENGTH)

                                            # Concentration difference
                                            C_j = self.concentration[j]
                                            rho_j = densities[j]

                                            # SPH gradient approximation
                                            grad += rho_i * masses[j] * (C_j - C_i) / (rho_j * rho_j) * grad_W

            self.concentration_gradient[i] = grad

    @ti.kernel
    def compute_concentration_laplacian(
        self,
        positions: ti.template(),
        masses: ti.template(),
        densities: ti.template(),
        neighbor_search: ti.template()
    ):
        """
        Compute concentration Laplacian using Morris formulation.

        Mathematical formula:
            ∇²Cᵢ = 2 Σⱼ mⱼ/ρⱼ (Cⱼ - Cᵢ) (rᵢⱼ·∇W)/(|rᵢⱼ|² + ε²)

        Args:
            positions: Particle positions
            masses: Particle masses
            densities: Particle densities
            neighbor_search: Neighbor search structure
        """
        epsilon_sq = EPSILON_VISCOSITY * EPSILON_VISCOSITY

        for i in range(self.num_particles):
            laplacian = 0.0
            pos_i = positions[i]
            C_i = self.concentration[i]
            cell_idx = neighbor_search.particle_cell_index[i]

            # Decode 1D cell index to 3D coordinates
            grid_res = neighbor_search.grid_resolution
            cell_z = cell_idx // (grid_res * grid_res)
            temp = cell_idx % (grid_res * grid_res)
            cell_y = temp // grid_res
            cell_x = temp % grid_res

            # Search 3×3×3 stencil
            for offset_x in ti.static(range(-1, 2)):
                for offset_y in ti.static(range(-1, 2)):
                    for offset_z in ti.static(range(-1, 2)):
                        neighbor_cell_x = cell_x + offset_x
                        neighbor_cell_y = cell_y + offset_y
                        neighbor_cell_z = cell_z + offset_z

                        if (neighbor_cell_x >= 0 and neighbor_cell_x < grid_res and
                            neighbor_cell_y >= 0 and neighbor_cell_y < grid_res and
                            neighbor_cell_z >= 0 and neighbor_cell_z < grid_res):

                            neighbor_cell_idx = (neighbor_cell_x +
                                               neighbor_cell_y * grid_res +
                                               neighbor_cell_z * grid_res * grid_res)

                            num_particles_in_cell = neighbor_search.cell_particle_count[neighbor_cell_idx]

                            for k in range(num_particles_in_cell):
                                if k < neighbor_search.max_particles_per_cell:
                                    j = neighbor_search.cell_particle_list[neighbor_cell_idx, k]

                                    if i != j:
                                        r_ij = pos_i - positions[j]
                                        dist = r_ij.norm()

                                        if dist < 2.0 * SMOOTHING_LENGTH:
                                            # Kernel gradient
                                            grad_W = cubic_spline_gradient(r_ij, SMOOTHING_LENGTH)

                                            # Concentration difference
                                            C_j = self.concentration[j]
                                            rho_j = densities[j]

                                            # Morris Laplacian formula
                                            r_dot_grad = r_ij.dot(grad_W)
                                            r_norm_sq = r_ij.norm_sqr() + epsilon_sq

                                            laplacian += 2.0 * (masses[j] / rho_j) * (C_j - C_i) * r_dot_grad / r_norm_sq

            self.concentration_laplacian[i] = laplacian

    @ti.kernel
    def update_concentration(
        self,
        velocities: ti.template(),
        dt: float
    ):
        """
        Update concentration using advection-diffusion equation.

        Transport equation:
            dC/dt = -v·∇C + D∇²C

        Args:
            velocities: Particle velocities
            dt: Timestep
        """
        for i in range(self.num_particles):
            # Advection term: -v·∇C (concentration moves with fluid)
            advection = -velocities[i].dot(self.concentration_gradient[i])

            # Diffusion term: D∇²C (concentration spreads)
            diffusion = DIFFUSION_COEFFICIENT * self.concentration_laplacian[i]

            # Time integration (explicit Euler)
            dC_dt = advection + diffusion

            # Update concentration
            new_concentration = self.concentration[i] + dC_dt * dt

            # Clamp to [0, 1] range
            self.concentration[i] = ti.max(0.0, ti.min(1.0, new_concentration))

    def step(
        self,
        positions: ti.template(),
        velocities: ti.template(),
        masses: ti.template(),
        densities: ti.template(),
        neighbor_search: ti.template(),
        dt: float
    ):
        """
        Perform one timestep of concentration advection-diffusion.

        Args:
            positions: Particle positions
            velocities: Particle velocities
            masses: Particle masses
            densities: Particle densities
            neighbor_search: Neighbor search structure
            dt: Timestep
        """
        # Compute spatial derivatives
        self.compute_concentration_gradient(positions, masses, densities, neighbor_search)
        self.compute_concentration_laplacian(positions, masses, densities, neighbor_search)

        # Update concentration field
        self.update_concentration(velocities, dt)

    @ti.kernel
    def compute_total_concentration(self) -> float:
        """
        Compute total concentration for mass conservation check.

        Returns:
            Sum of all particle concentrations
        """
        total = 0.0
        for i in range(self.num_particles):
            total += self.concentration[i]
        return total
