"""
SPH Kernel Functions - Cubic Spline (M4 B-spline)

This module implements the cubic spline kernel and its gradient for 3D SPH simulations.
The cubic spline kernel is widely used in SPH due to its good balance between
computational efficiency and numerical accuracy.

Mathematical Background:
- Support radius: 2h (compact support)
- Normalization factor (3D): σ₃ = 8/(πh³)
- Ensures partition of unity: ∫W(r,h)dV = 1
"""

import taichi as ti
import math

# ============================================================================
# Kernel Functions
# ============================================================================

@ti.func
def cubic_spline_kernel(r: ti.math.vec3, h: float) -> float:
    """
    Cubic spline kernel function (M4 B-spline) for 3D SPH.

    Mathematical formulation:
        W(r, h) = σ₃ * f(q)

    where:
        q = |r| / h  (normalized distance)
        σ₃ = 8/(πh³)  (normalization factor for 3D)

        f(q) = {
            (2/3 - q² + q³/2)      if 0 ≤ q < 1
            (1/6)(2 - q)³          if 1 ≤ q < 2
            0                      if q ≥ 2
        }

    Args:
        r: Vector from particle j to particle i (r_ij = r_i - r_j)
        h: Smoothing length

    Returns:
        Kernel value W(|r|, h)

    Note:
        The normalization factor σ₃ = 8/(πh³) ensures that the kernel
        integrates to unity: ∫W(r,h)dV = 1
    """
    # Compute distance
    r_norm = r.norm()

    # Normalized distance q = |r| / h
    q = r_norm / h

    # Normalization factor for 3D: σ₃ = 8/(πh³)
    sigma_3 = 8.0 / (math.pi * h * h * h)

    # Kernel value
    kernel_value = 0.0

    if q < 1.0:
        # Region 1: 0 ≤ q < 1
        # W = σ₃ * (2/3 - q² + q³/2)
        kernel_value = sigma_3 * (2.0/3.0 - q*q + 0.5*q*q*q)
    elif q < 2.0:
        # Region 2: 1 ≤ q < 2
        # W = σ₃ * (1/6)(2-q)³
        temp = 2.0 - q
        kernel_value = sigma_3 * (1.0/6.0) * temp * temp * temp
    # else: q ≥ 2, kernel_value = 0 (outside support radius)

    return kernel_value


@ti.func
def cubic_spline_gradient(r: ti.math.vec3, h: float) -> ti.math.vec3:
    """
    Gradient of the cubic spline kernel function.

    Mathematical formulation:
        ∇W(r, h) = (r/|r|) * (dW/dr)

    where:
        dW/dr = (σ₃/h) * df/dq

        df/dq = {
            -2q + (3/2)q²         if 0 ≤ q < 1
            -(1/2)(2-q)²          if 1 ≤ q < 2
            0                     if q ≥ 2
        }

    Args:
        r: Vector from particle j to particle i (r_ij = r_i - r_j)
        h: Smoothing length

    Returns:
        Gradient vector ∇W(r, h)

    Note:
        This is used in SPH approximations of spatial derivatives:
        - Pressure gradient: ∇p = ρᵢ Σⱼ mⱼ (pⱼ/ρⱼ² + pᵢ/ρᵢ²) ∇W
        - Viscosity Laplacian: Uses r·∇W in Morris formulation
    """
    # Compute distance
    r_norm = r.norm()

    # Initialize gradient to zero
    gradient = ti.math.vec3(0.0, 0.0, 0.0)

    # Handle singularity at r = 0 (gradient is zero)
    # Only compute if r_norm is non-zero
    if r_norm >= 1e-6:
        # Normalized distance q = |r| / h
        q = r_norm / h

        # Normalization factor
        sigma_3 = 8.0 / (math.pi * h * h * h)

        # Derivative of kernel with respect to q
        dW_dq = 0.0

        if q < 1.0:
            # Region 1: 0 ≤ q < 1
            # df/dq = -2q + (3/2)q²
            dW_dq = -2.0*q + 1.5*q*q
        elif q < 2.0:
            # Region 2: 1 ≤ q < 2
            # df/dq = -(1/2)(2-q)²
            temp = 2.0 - q
            dW_dq = -0.5 * temp * temp
        # else: q ≥ 2, dW_dq = 0

        # Convert to derivative with respect to r
        # dW/dr = (dW/dq) * (dq/dr) = (dW/dq) / h
        dW_dr = (sigma_3 / h) * dW_dq

        # Gradient: ∇W = (r/|r|) * (dW/dr)
        gradient = (r / r_norm) * dW_dr

    return gradient


# ============================================================================
# Helper Functions
# ============================================================================

@ti.func
def kernel_support_radius(h: float) -> float:
    """
    Return the support radius of the cubic spline kernel.

    Args:
        h: Smoothing length

    Returns:
        Support radius (2h for cubic spline)
    """
    return 2.0 * h


@ti.func
def is_within_support(r: ti.math.vec3, h: float) -> bool:
    """
    Check if a point is within the kernel support radius.

    Args:
        r: Distance vector
        h: Smoothing length

    Returns:
        True if |r| < 2h, False otherwise
    """
    return r.norm() < kernel_support_radius(h)
