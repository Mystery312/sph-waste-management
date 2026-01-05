"""
Particle Initialization - Dam Break Scenario

Sets up initial particle positions and velocities for the dam break test case.
Particles are arranged in a regular grid in the corner of the domain.
"""

import taichi as ti
from ..config import *


@ti.kernel
def initialize_dam_break(
    positions: ti.template(),
    velocities: ti.template(),
    masses: ti.template(),
    num_particles: int
):
    """
    Initialize particles for dam break scenario.

    Creates a 20×20×20 grid of particles in the corner of the box.
    Dam dimensions: 40% width × 50% height × 40% depth

    Args:
        positions: Particle position field
        velocities: Particle velocity field
        masses: Particle mass field
        num_particles: Number of particles
    """
    # Dam break dimensions
    fluid_start = ti.math.vec3(0.0, 0.0, 0.0)
    fluid_dim = ti.math.vec3(0.4, 0.5, 0.4)  # 40% x 50% x 40%

    # Calculate particles per dimension for ~8000 particles
    particles_per_dim = int(ti.pow(num_particles, 1.0/3.0)) # ~20

    idx = 0
    for i in range(particles_per_dim):
        for j in range(particles_per_dim):
            for k in range(particles_per_dim):
                if idx < num_particles:
                    # Position with particle spacing
                    pos_x = fluid_start.x + (i + 0.5) * PARTICLE_SPACING
                    pos_y = fluid_start.y + (j + 0.5) * PARTICLE_SPACING
                    pos_z = fluid_start.z + (k + 0.5) * PARTICLE_SPACING

                    # Check if within fluid dimensions
                    if (pos_x <= fluid_start.x + fluid_dim.x and
                        pos_y <= fluid_start.y + fluid_dim.y and
                        pos_z <= fluid_start.z + fluid_dim.z):

                        positions[idx] = ti.math.vec3(pos_x, pos_y, pos_z)
                        velocities[idx] = ti.math.vec3(0.0, 0.0, 0.0)  # Initially at rest
                        masses[idx] = PARTICLE_MASS

                        idx += 1
