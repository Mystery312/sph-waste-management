"""
Main Entry Point - 3D WCSPH Fluid Simulation

Dam break test case with real-time visualization and data export.
"""

import taichi as ti
from sph_fluid_sim.config import *
from sph_fluid_sim.core.solver import WCSPHSolver
from sph_fluid_sim.visualization.renderer import SPHRenderer
from sph_fluid_sim.utils.export import export_to_vtk


def main():
    # Initialize Taichi
    # Use CUDA for NVIDIA GPUs, cpu for CPU-only systems
    ti.init(arch=ti.cuda)  # Change to ti.cpu if no GPU available

    # Print configuration
    print_simulation_config()

    # Create solver
    print("\nInitializing WCSPH solver...")
    solver = WCSPHSolver(num_particles=NUM_PARTICLES)
    solver.initialize()

    # Create renderer
    print("Starting real-time visualization...")
    renderer = SPHRenderer(solver)

    # Simulation parameters
    target_time = 5.0  # Simulate 5 seconds
    export_interval = 0.05  # Export every 50ms
    print_interval = 10  # Print every 10 steps

    # Main simulation loop
    time = 0.0
    step = 0
    frame = 0
    next_export_time = 0.0

    print("\n" + "="*60)
    print("Starting simulation...")
    print("="*60)
    print("Controls: ESC to exit, Right-click + drag to rotate camera")
    print("="*60 + "\n")

    while time < target_time and not renderer.should_close():
        # Compute adaptive timestep
        dt = solver.compute_timestep()

        # Perform SPH step
        solver.step(dt)

        # Update time
        time += dt
        step += 1

        # Export frame if needed
        if time >= next_export_time:
            positions = solver.positions.to_numpy()
            velocities = solver.velocities.to_numpy()
            densities = solver.densities.to_numpy()
            pressures = solver.pressures.to_numpy()

            export_to_vtk(
                positions,
                velocities,
                densities,
                pressures,
                frame,
                OUTPUT_DIR
            )
            next_export_time += export_interval
            frame += 1

        # Render
        renderer.render()

        # Console output
        if step % print_interval == 0:
            densities_np = solver.densities.to_numpy()
            max_density = densities_np.max()
            min_density = densities_np.min()
            density_error = abs((max_density - REST_DENSITY) / REST_DENSITY) * 100

            print(f"Step {step:5d} | "
                  f"Time: {time:6.3f}s | "
                  f"dt: {dt*1000:5.2f}ms | "
                  f"Density error: {density_error:.2f}% | "
                  f"Frames: {frame}")

    print("\n" + "="*60)
    print(f"Simulation completed!")
    print(f"Total steps: {step}")
    print(f"Total time: {time:.2f}s")
    print(f"Frames exported: {frame}")
    print(f"Output directory: {OUTPUT_DIR}")
    print("="*60)


if __name__ == "__main__":
    main()
