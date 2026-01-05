"""
Boundary Conditions - Simple Box Collision

Implements boundary enforcement to prevent particles from leaving the simulation domain.
Uses simple collision detection with damping to simulate energy loss.
"""

import taichi as ti
from ..config import *


@ti.kernel
def enforce_boundary(
    positions: ti.template(),
    velocities: ti.template(),
    num_particles: int
):
    """
    Enforce box boundary conditions using collision detection.

    For each particle, check if it's outside the box bounds.
    If so, reflect position and reverse velocity with damping.

    Args:
        positions: Particle positions
        velocities: Particle velocities
        num_particles: Number of particles
    """
    for i in range(num_particles):
        pos = positions[i]
        vel = velocities[i]

        # Check and enforce X bounds
        if pos.x < BOX_MIN.x:
            pos.x = BOX_MIN.x
            vel.x = -BOUNDARY_DAMPING * ti.abs(vel.x)
        elif pos.x > BOX_MAX.x:
            pos.x = BOX_MAX.x
            vel.x = -BOUNDARY_DAMPING * ti.abs(vel.x)

        # Check and enforce Y bounds
        if pos.y < BOX_MIN.y:
            pos.y = BOX_MIN.y
            vel.y = -BOUNDARY_DAMPING * ti.abs(vel.y)
        elif pos.y > BOX_MAX.y:
            pos.y = BOX_MAX.y
            vel.y = -BOUNDARY_DAMPING * ti.abs(vel.y)

        # Check and enforce Z bounds
        if pos.z < BOX_MIN.z:
            pos.z = BOX_MIN.z
            vel.z = -BOUNDARY_DAMPING * ti.abs(vel.z)
        elif pos.z > BOX_MAX.z:
            pos.z = BOX_MAX.z
            vel.z = -BOUNDARY_DAMPING * ti.abs(vel.z)

        # Update particle state
        positions[i] = pos
        velocities[i] = vel
