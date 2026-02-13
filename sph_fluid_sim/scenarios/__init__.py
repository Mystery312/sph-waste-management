"""
Scenarios module - Preset simulation scenarios for educational demonstrations.
"""

from .demo_scenarios import (
    load_scenario,
    list_scenarios,
    get_scenario_descriptions,
    SCENARIOS
)

__all__ = [
    'load_scenario',
    'list_scenarios',
    'get_scenario_descriptions',
    'SCENARIOS'
]
