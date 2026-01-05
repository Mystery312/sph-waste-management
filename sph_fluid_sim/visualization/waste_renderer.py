"""
Enhanced Renderer for Waste Tracking Visualization

Renders particles with color-coding based on concentration:
- Blue: Clean water (concentration = 0.0)
- Yellow: Mixed (concentration = 0.5)
- Red: High waste (concentration = 1.0)
"""

import taichi as ti
from ..config import *


@ti.data_oriented
class WasteTrackingRenderer:
    """
    Real-time GGUI renderer with concentration-based coloring.
    """

    def __init__(self, solver, concentration_tracker):
        """
        Initialize waste tracking renderer.

        Args:
            solver: WCSPHSolver instance
            concentration_tracker: ConcentrationTracker instance
        """
        self.solver = solver
        self.concentration_tracker = concentration_tracker

        # Create GGUI window
        self.window = ti.ui.Window(
            "3D Waste Tracking Simulation",
            (WINDOW_WIDTH, WINDOW_HEIGHT),
            vsync=True
        )

        # Create 3D canvas
        self.canvas = self.window.get_canvas()
        self.scene = ti.ui.Scene()

        # Setup camera
        self.camera = ti.ui.Camera()
        self.camera.position(1.5, 1.0, 1.5)
        self.camera.lookat(0.5, 0.5, 0.5)
        self.camera.up(0, 1, 0)

        # Color field for particles
        self.particle_colors = ti.Vector.field(3, dtype=ti.f32, shape=solver.num_particles)

    @ti.kernel
    def compute_particle_colors(self):
        """
        Compute particle colors based on concentration.

        Color mapping:
        - concentration = 0.0 → Blue (0, 0, 1)    Clean water
        - concentration = 0.5 → Yellow (1, 1, 0)  Mixed
        - concentration = 1.0 → Red (1, 0, 0)     Pure waste
        """
        for i in range(self.solver.num_particles):
            c = self.concentration_tracker.concentration[i]

            # Initialize color variable
            color = ti.math.vec3(0.0, 0.0, 1.0)  # Default blue

            # Gradient from blue → yellow → red
            if c < 0.5:
                # Blue (0,0,1) to Yellow (1,1,0)
                # Increase red and green, decrease blue
                t = c * 2.0  # Map [0, 0.5] to [0, 1]
                color = ti.math.vec3(t, t, 1.0 - t)
            else:
                # Yellow (1,1,0) to Red (1,0,0)
                # Keep red=1, decrease green
                t = (c - 0.5) * 2.0  # Map [0.5, 1.0] to [0, 1]
                color = ti.math.vec3(1.0, 1.0 - t, 0.0)

            self.particle_colors[i] = color

    def render(self):
        """Render one frame with concentration-colored particles."""
        # Update camera
        self.camera.track_user_inputs(self.window, movement_speed=0.03, hold_key=ti.ui.RMB)
        self.scene.set_camera(self.camera)

        # Set lighting
        self.scene.ambient_light((0.8, 0.8, 0.8))
        self.scene.point_light(pos=(1.5, 2.0, 1.5), color=(1, 1, 1))

        # Compute particle colors
        self.compute_particle_colors()

        # Render particles with color
        self.scene.particles(
            self.solver.positions,
            radius=PARTICLE_RENDER_RADIUS,
            per_vertex_color=self.particle_colors
        )

        # Draw box boundaries
        self.draw_box()

        # Render scene
        self.canvas.scene(self.scene)
        self.window.show()

    def draw_box(self):
        """Draw visualization of the simulation domain boundaries."""
        # Box vertices (8 corners)
        corners = [
            [BOX_MIN.x, BOX_MIN.y, BOX_MIN.z],
            [BOX_MAX.x, BOX_MIN.y, BOX_MIN.z],
            [BOX_MAX.x, BOX_MAX.y, BOX_MIN.z],
            [BOX_MIN.x, BOX_MAX.y, BOX_MIN.z],
            [BOX_MIN.x, BOX_MIN.y, BOX_MAX.z],
            [BOX_MAX.x, BOX_MIN.y, BOX_MAX.z],
            [BOX_MAX.x, BOX_MAX.y, BOX_MAX.z],
            [BOX_MIN.x, BOX_MAX.y, BOX_MAX.z],
        ]

        # Box edges (12 lines)
        edges = [
            (0, 1), (1, 2), (2, 3), (3, 0),  # Bottom face
            (4, 5), (5, 6), (6, 7), (7, 4),  # Top face
            (0, 4), (1, 5), (2, 6), (3, 7),  # Vertical edges
        ]

        # Draw edges as lines
        for start_idx, end_idx in edges:
            self.scene.lines(
                ti.Vector.field(3, dtype=ti.f32, shape=2),
                width=2.0,
                color=(0.5, 0.5, 0.5)
            )

    def should_close(self):
        """Check if window should close (ESC pressed)."""
        return not self.window.running
