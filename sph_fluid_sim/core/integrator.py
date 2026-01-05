"""
Time Integration - Symplectic Euler

Implements explicit symplectic Euler time integration with adaptive CFL timestep.
This scheme is simple, stable for WCSPH, and energy-conserving.
"""

import taichi as ti
from ..config import *


@ti.kernel
def integrate_step(
    positions: ti.template(),
    velocities: ti.template(),
    accelerations: ti.template(),
    num_particles: int,
    dt: float
):
    """
    Perform one symplectic Euler integration step.

    Algorithm:
        v(t+Δt) = v(t) + a(t) * Δt
        x(t+Δt) = x(t) + v(t+Δt) * Δt

    Args:
        positions: Particle positions
        velocities: Particle velocities
        accelerations: Particle accelerations
        num_particles: Number of particles
        dt: Timestep
    """
    for i in range(num_particles):
        # Update velocity: v(t+Δt) = v(t) + a(t) * Δt
        velocities[i] += accelerations[i] * dt

        # Update position: x(t+Δt) = x(t) + v(t+Δt) * Δt
        positions[i] += velocities[i] * dt


@ti.kernel
def compute_max_velocity(velocities: ti.template(), num_particles: int) -> float:
    """Compute maximum velocity magnitude."""
    max_v = 0.0
    for i in range(num_particles):
        v_mag = velocities[i].norm()
        max_v = ti.max(max_v, v_mag)
    return max_v


@ti.kernel
def compute_max_acceleration(accelerations: ti.template(), num_particles: int) -> float:
    """Compute maximum acceleration magnitude."""
    max_a = 0.0
    for i in range(num_particles):
        a_mag = accelerations[i].norm()
        max_a = ti.max(max_a, a_mag)
    return max_a


def compute_adaptive_timestep(velocities, accelerations, num_particles):
    """
    Compute adaptive timestep using CFL condition.

    CFL criteria:
        dt = min(dt_cfl, dt_force, dt_visc)

    where:
        dt_cfl = 0.25 * h / c_s        (Courant condition)
        dt_force = 0.25 * sqrt(h / a_max)  (Force condition)
        dt_visc = 0.125 * h² / ν       (Viscous diffusion)

    Returns:
        Adaptive timestep
    """
    max_v = compute_max_velocity(velocities, num_particles)
    max_a = compute_max_acceleration(accelerations, num_particles)

    # CFL condition (based on sound speed)
    dt_cfl = CFL_COEFFICIENT * SMOOTHING_LENGTH / (SOUND_SPEED + max_v + 1e-6)

    # Force condition
    dt_force = CFL_COEFFICIENT * ti.sqrt(SMOOTHING_LENGTH / (max_a + 1e-6))

    # Viscous diffusion condition
    dt_visc = 0.125 * SMOOTHING_LENGTH * SMOOTHING_LENGTH / (KINEMATIC_VISCOSITY + 1e-6)

    # Take minimum
    dt = min(dt_cfl, dt_force, dt_visc)

    # Clamp to bounds
    dt = max(MIN_TIMESTEP, min(dt, MAX_TIMESTEP))

    return dt
