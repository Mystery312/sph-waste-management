"""
Concentration Metrics and Contamination Zone Detection

Computes statistical metrics for waste concentration tracking:
- Mean, max, min concentration
- Concentration variance and mixing index
- Center of mass
- Contamination zone volumes (low/medium/high thresholds)
"""

import taichi as ti
from ..config import *


@ti.data_oriented
class ConcentrationMetrics:
    """
    Computes comprehensive metrics for concentration analysis.
    """

    def __init__(self):
        """Initialize metrics storage."""
        # Contamination zone particle counts
        self.zone_counts = ti.field(dtype=ti.i32, shape=3)  # [low, medium, high]

    @ti.kernel
    def compute_statistics(
        self,
        concentration: ti.template(),
        masses: ti.template(),
        positions: ti.template(),
        num_particles: int
    ) -> ti.types.vector(10, float):
        """
        Compute all concentration statistics in single kernel.

        Returns vector containing:
            [0] mean_concentration
            [1] max_concentration
            [2] min_concentration
            [3] variance
            [4] center_of_mass_x
            [5] center_of_mass_y
            [6] center_of_mass_z
            [7] total_waste_mass
            [8] mixing_index (0=unmixed, 1=perfect mixing)
            [9] reserved

        Args:
            concentration: Concentration field
            masses: Particle masses
            positions: Particle positions
            num_particles: Number of particles

        Returns:
            Statistics vector
        """
        mean_conc = 0.0
        max_conc = 0.0
        min_conc = 1.0
        total_waste_mass = 0.0
        center_of_mass = ti.math.vec3(0.0, 0.0, 0.0)

        # First pass: mean, extrema, center of mass
        for i in range(num_particles):
            c = concentration[i]
            m = masses[i]

            mean_conc += c
            max_conc = ti.max(max_conc, c)
            min_conc = ti.min(min_conc, c)

            total_waste_mass += c * m
            center_of_mass += c * m * positions[i]

        mean_conc /= num_particles

        # Normalize center of mass
        if total_waste_mass > 1e-10:
            center_of_mass /= total_waste_mass

        # Second pass: variance
        variance = 0.0
        for i in range(num_particles):
            deviation = concentration[i] - mean_conc
            variance += deviation * deviation
        variance /= num_particles

        # Mixing index: 0 = unmixed, 1 = perfectly mixed
        # For binary system (0 or 1), maximum variance is 0.25
        variance_unmixed = 0.25
        mixing_index = 1.0 - ti.sqrt(variance / (variance_unmixed + 1e-10))

        return ti.Vector([
            mean_conc,
            max_conc,
            min_conc,
            variance,
            center_of_mass.x,
            center_of_mass.y,
            center_of_mass.z,
            total_waste_mass,
            mixing_index,
            0.0  # Reserved slot
        ])

    @ti.kernel
    def detect_contamination_zones(
        self,
        concentration: ti.template(),
        num_particles: int
    ):
        """
        Count particles in each contamination zone.

        Thresholds:
        - Low: concentration >= 0.1 (10%)
        - Medium: concentration >= 0.5 (50%)
        - High: concentration >= 0.9 (90%)

        Args:
            concentration: Concentration field
            num_particles: Number of particles
        """
        # Reset counts
        for i in range(3):
            self.zone_counts[i] = 0

        # Count particles in each zone
        for i in range(num_particles):
            c = concentration[i]

            # High contamination (>= 90%)
            if c >= CONTAMINATION_THRESHOLD_HIGH:
                ti.atomic_add(self.zone_counts[2], 1)

            # Medium contamination (>= 50%)
            if c >= CONTAMINATION_THRESHOLD_MEDIUM:
                ti.atomic_add(self.zone_counts[1], 1)

            # Low contamination (>= 10%)
            if c >= CONTAMINATION_THRESHOLD_LOW:
                ti.atomic_add(self.zone_counts[0], 1)

    def get_zone_volumes(self):
        """
        Calculate contamination zone volumes from particle counts.

        Returns:
            Dictionary with low, medium, high zone volumes and percentages
        """
        particle_volume = PARTICLE_SPACING ** 3
        total_volume = (BOX_MAX.x - BOX_MIN.x) * (BOX_MAX.y - BOX_MIN.y) * (BOX_MAX.z - BOX_MIN.z)

        zone_counts_np = self.zone_counts.to_numpy()

        volumes = {
            'low': {
                'threshold': CONTAMINATION_THRESHOLD_LOW,
                'particle_count': int(zone_counts_np[0]),
                'volume': float(zone_counts_np[0] * particle_volume),
                'percentage': float((zone_counts_np[0] * particle_volume / total_volume) * 100)
            },
            'medium': {
                'threshold': CONTAMINATION_THRESHOLD_MEDIUM,
                'particle_count': int(zone_counts_np[1]),
                'volume': float(zone_counts_np[1] * particle_volume),
                'percentage': float((zone_counts_np[1] * particle_volume / total_volume) * 100)
            },
            'high': {
                'threshold': CONTAMINATION_THRESHOLD_HIGH,
                'particle_count': int(zone_counts_np[2]),
                'volume': float(zone_counts_np[2] * particle_volume),
                'percentage': float((zone_counts_np[2] * particle_volume / total_volume) * 100)
            }
        }

        return volumes
