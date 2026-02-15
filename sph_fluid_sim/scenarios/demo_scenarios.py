"""
Preset demo scenarios for classroom presentations.

This module provides predefined waste injection patterns for educational demonstrations
of multivariable calculus concepts (gradients, integrals, divergence, curl).

Each scenario sets up different waste distribution patterns to showcase specific
physics and mathematical behaviors.
"""

import numpy as np
import taichi as ti
from sph_fluid_sim.config import (
    NUM_PARTICLES, PARTICLE_TYPE_FLUID_WASTE, PARTICLE_TYPE_FLUID_CLEAN
)
from sph_fluid_sim.core.solver import WCSPHSolver
from sph_fluid_sim.tracking.concentration import ConcentrationTracker

2


class DemoScenario:
    """Base class for demo scenarios."""

    def __init__(self, num_particles: int = NUM_PARTICLES, name: str = "unnamed"):
        """
        Initialize demo scenario.

        Args:
            num_particles: Number of particles in simulation
            name: Scenario name for logging
        """
        self.num_particles = num_particles
        self.name = name
        self.solver = None
        self.tracker = None

    def setup(self):
        """
        Create solver and tracker with scenario-specific initialization.
        Must be implemented by subclasses.
        """
        raise NotImplementedError

    def get_scenario_info(self) -> dict:
        """
        Return information about the scenario for display.

        Returns:
            dict with keys: name, description, physics_concepts
        """
        raise NotImplementedError


class OilSpillScenario(DemoScenario):
    """
    Oil Spill Scenario: Waste floats upward

    Demonstrates:
    - Oil (lighter than water) rises due to buoyancy
    - Gradient field shows concentration spreading upward
    - Good for showing ∇C pointing upward in y-direction
    """

    def __init__(self, num_particles: int = NUM_PARTICLES):
        super().__init__(num_particles, name="oil_spill")

    def setup(self):
        """Initialize oil spill scenario - waste at bottom, floats upward."""
        # Create solver and tracker
        self.solver = WCSPHSolver(num_particles=self.num_particles)
        self.solver.initialize()

        self.tracker = ConcentrationTracker(num_particles=self.num_particles)
        self.tracker.initialize_clean_fluid()

        # Mark bottom 15% of particles as waste (oil)
        positions_np = self.solver.positions.to_numpy()
        y_positions = positions_np[:, 1]

        waste_count = int(0.15 * self.num_particles)
        waste_indices_np = np.argsort(y_positions)[:waste_count]  # Bottom 15%

        # Use a simpler approach: mark a contiguous range
        # For oil spill, we want the bottom particles, so use min to max of waste indices
        if len(waste_indices_np) > 0:
            min_idx = int(np.min(waste_indices_np))
            max_idx = int(np.max(waste_indices_np)) + 1
            self.tracker.initialize_waste_particles(min_idx, max_idx)

        return self.solver, self.tracker

    def get_scenario_info(self) -> dict:
        return {
            "name": "Oil Spill",
            "description": "Oil (density 900 kg/m³) injected at bottom, rises upward due to buoyancy",
            "physics_concepts": [
                "Buoyancy force",
                "Gradient of concentration (∇C points upward)",
                "Advection-diffusion with buoyant transport"
            ],
            "learning_objectives": [
                "Observe how ∇C changes as waste spreads",
                "See volume integral increase in top regions",
                "Understand directional derivatives in 3D"
            ]
        }


class HeavyContaminationScenario(DemoScenario):
    """
    Heavy Contamination Scenario: Waste sinks downward

    Demonstrates:
    - Heavy waste (denser than water) sinks
    - Opposite behavior from oil spill
    - Gradient field shows concentration spreading downward
    - Good for comparing opposite physics
    """

    def __init__(self, num_particles: int = NUM_PARTICLES):
        super().__init__(num_particles, name="heavy_contamination")

    def setup(self):
        """Initialize heavy contamination scenario - waste at top, sinks downward."""
        # Create solver and tracker
        self.solver = WCSPHSolver(num_particles=self.num_particles)
        self.solver.initialize()

        self.tracker = ConcentrationTracker(num_particles=self.num_particles)
        self.tracker.initialize_clean_fluid()

        # Mark top 15% of particles as waste (heavy, denser than water)
        positions_np = self.solver.positions.to_numpy()
        y_positions = positions_np[:, 1]

        waste_count = int(0.15 * self.num_particles)
        waste_indices_np = np.argsort(y_positions)[-waste_count:]  # Top 15%

        # Use a simpler approach: mark a contiguous range
        # For heavy contamination, we want the top particles, so use min to max of waste indices
        if len(waste_indices_np) > 0:
            min_idx = int(np.min(waste_indices_np))
            max_idx = int(np.max(waste_indices_np)) + 1
            self.tracker.initialize_waste_particles(min_idx, max_idx)

        return self.solver, self.tracker

    def get_scenario_info(self) -> dict:
        return {
            "name": "Heavy Contamination",
            "description": "Heavy waste (density 1100 kg/m³) injected at top, sinks due to gravity",
            "physics_concepts": [
                "Gravitational settling",
                "Gradient of concentration (∇C points downward)",
                "Negative divergence (sink behavior)"
            ],
            "learning_objectives": [
                "Compare with oil spill - opposite behavior",
                "Observe how ∇C reverses direction",
                "See volume integral increase in bottom regions"
            ]
        }


class PointSourceScenario(DemoScenario):
    """
    Point Source Scenario: Waste injected from center

    Demonstrates:
    - Radial spreading from a central point
    - Spherical gradient field (radial symmetry)
    - Good for showing ∇C as radial vectors pointing outward
    """

    def __init__(self, num_particles: int = NUM_PARTICLES):
        super().__init__(num_particles, name="point_source")

    def setup(self):
        """Initialize point source scenario - waste injected from center."""
        # Create solver and tracker
        self.solver = WCSPHSolver(num_particles=self.num_particles)
        self.solver.initialize()

        self.tracker = ConcentrationTracker(num_particles=self.num_particles)
        self.tracker.initialize_clean_fluid()

        # Mark particles near center (0.5, 0.5, 0.5) as waste
        positions_np = self.solver.positions.to_numpy()
        center = np.array([0.5, 0.5, 0.5])
        distances = np.linalg.norm(positions_np - center, axis=1)

        # Mark particles within 0.25m of center (innermost region)
        waste_indices_np = np.where(distances < 0.25)[0]

        # Use a simpler approach: mark a contiguous range
        # For point source, we want particles near center, so use min to max of waste indices
        if len(waste_indices_np) > 0:
            min_idx = int(np.min(waste_indices_np))
            max_idx = int(np.max(waste_indices_np)) + 1
            self.tracker.initialize_waste_particles(min_idx, max_idx)

        return self.solver, self.tracker

    def get_scenario_info(self) -> dict:
        return {
            "name": "Point Source",
            "description": "Contamination injected from center point (0.5, 0.5, 0.5), spreads radially",
            "physics_concepts": [
                "Radial diffusion from point source",
                "Spherically symmetric gradient field",
                "Radial symmetry in ∇C vectors"
            ],
            "learning_objectives": [
                "See radial spreading pattern",
                "Observe radial gradient vectors (∇C ∝ r̂)",
                "Understand spherical coordinates concept"
            ]
        }


# Scenario registry for easy access
SCENARIOS = {
    'oil_spill': OilSpillScenario,
    'heavy_contamination': HeavyContaminationScenario,
    'point_source': PointSourceScenario,
}


def load_scenario(scenario_name: str, num_particles: int = NUM_PARTICLES):
    """
    Load a preset scenario by name.

    Args:
        scenario_name: Name of scenario ('oil_spill', 'heavy_contamination', 'point_source')
        num_particles: Number of particles in simulation

    Returns:
        tuple: (solver, concentration_tracker)

    Raises:
        ValueError: If scenario_name is not recognized
    """
    if scenario_name not in SCENARIOS:
        available = ', '.join(SCENARIOS.keys())
        raise ValueError(f"Unknown scenario '{scenario_name}'. Available: {available}")

    scenario_class = SCENARIOS[scenario_name]
    scenario = scenario_class(num_particles=num_particles)
    solver, tracker = scenario.setup()

    print(f"\n{'='*60}")
    print(f"Loaded Scenario: {scenario.get_scenario_info()['name']}")
    print(f"{'='*60}")
    print(f"Description: {scenario.get_scenario_info()['description']}")
    print(f"\nPhysics Concepts:")
    for concept in scenario.get_scenario_info()['physics_concepts']:
        print(f"  • {concept}")
    print(f"\nLearning Objectives:")
    for obj in scenario.get_scenario_info()['learning_objectives']:
        print(f"  • {obj}")
    print(f"{'='*60}\n")

    return solver, tracker


def list_scenarios() -> list:
    """
    List all available scenarios.

    Returns:
        list: Names of available scenarios
    """
    return list(SCENARIOS.keys())


def get_scenario_descriptions() -> dict:
    """
    Get descriptions of all available scenarios.

    Returns:
        dict: Scenario information keyed by name
    """
    descriptions = {}
    for name, scenario_class in SCENARIOS.items():
        scenario = scenario_class()
        descriptions[name] = scenario.get_scenario_info()
    return descriptions
