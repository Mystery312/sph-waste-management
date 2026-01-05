"""
GGUI Renderer - Real-time 3D visualization using Taichi's built-in GGUI.
"""

import taichi as ti
from ..config import *


class SPHRenderer:
    """Real-time GGUI renderer for SPH simulation."""

    def __init__(self, solver):
        """
        Initialize GGUI renderer.

        Args:
            solver: WCSPHSolver instance
        """
        self.solver = solver

        # Create window
        self.window = ti.ui.Window("SPH Fluid Simulation", (WINDOW_WIDTH, WINDOW_HEIGHT))
        self.canvas = self.window.get_canvas()
        self.scene = ti.ui.Scene()
        self.camera = ti.ui.Camera()

        # Camera setup
        self.camera.position(1.5, 1.0, 1.5)
        self.camera.lookat(0.5, 0.5, 0.5)
        self.camera.up(0, 1, 0)

    def render(self):
        """Render current simulation state."""
        self.camera.track_user_inputs(self.window, movement_speed=0.03, hold_key=ti.ui.RMB)
        self.scene.set_camera(self.camera)

        # Add ambient light
        self.scene.ambient_light((0.5, 0.5, 0.5))
        self.scene.point_light(pos=(0.5, 1.5, 0.5), color=(1, 1, 1))

        # Render fluid particles (blue water)
        self.scene.particles(
            self.solver.positions,
            radius=PARTICLE_RENDER_RADIUS,
            color=(0.2, 0.5, 0.8)
        )

        # Render canvas
        self.canvas.scene(self.scene)
        self.window.show()

    def should_close(self):
        """Check if window should close."""
        return self.window.is_pressed(ti.ui.ESCAPE) or not self.window.running
