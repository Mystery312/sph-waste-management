"""
Phase 2 Entry Point - Waste Tracking Simulation

Dam break scenario with waste particles (oil/pollutant) mixed in.
Demonstrates:
- Multi-phase particle tracking
- Advection-diffusion of concentration field
- Real-time color-coded visualization
- Contamination zone metrics
- Enhanced data export
"""

import taichi as ti
import numpy as np
from sph_fluid_sim.config import *
from sph_fluid_sim.core.solver import WCSPHSolver
from sph_fluid_sim.tracking.concentration import ConcentrationTracker
from sph_fluid_sim.analytics.metrics import ConcentrationMetrics
from sph_fluid_sim.visualization.waste_renderer import WasteTrackingRenderer
from sph_fluid_sim.utils.export import export_to_vtk
import os


def export_waste_data(positions, velocities, densities, pressures, concentration, frame, output_dir):
    """
    Export VTK file with concentration data included.

    Args:
        positions: Particle positions (numpy array)
        velocities: Particle velocities (numpy array)
        densities: Particle densities (numpy array)
        pressures: Particle pressures (numpy array)
        concentration: Concentration field (numpy array)
        frame: Frame number
        output_dir: Output directory path
    """
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"waste_particles_{frame:05d}.vtk")

    with open(filename, 'w') as f:
        # VTK header
        f.write("# vtk DataFile Version 3.0\n")
        f.write(f"SPH Waste Tracking - Frame {frame}\n")
        f.write("ASCII\n")
        f.write("DATASET POLYDATA\n")

        # Points
        num_particles = len(positions)
        f.write(f"POINTS {num_particles} float\n")
        for pos in positions:
            f.write(f"{pos[0]:.6f} {pos[1]:.6f} {pos[2]:.6f}\n")

        # Point data
        f.write(f"\nPOINT_DATA {num_particles}\n")

        # Velocity
        f.write("VECTORS velocity float\n")
        for vel in velocities:
            f.write(f"{vel[0]:.6f} {vel[1]:.6f} {vel[2]:.6f}\n")

        # Density
        f.write("\nSCALARS density float 1\n")
        f.write("LOOKUP_TABLE default\n")
        for rho in densities:
            f.write(f"{rho:.6f}\n")

        # Pressure
        f.write("\nSCALARS pressure float 1\n")
        f.write("LOOKUP_TABLE default\n")
        for p in pressures:
            f.write(f"{p:.6f}\n")

        # Concentration (NEW!)
        f.write("\nSCALARS concentration float 1\n")
        f.write("LOOKUP_TABLE default\n")
        for c in concentration:
            f.write(f"{c:.6f}\n")


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

    # Create concentration tracker
    print("Initializing concentration tracker...")
    concentration_tracker = ConcentrationTracker(num_particles=NUM_PARTICLES)
    concentration_tracker.initialize_clean_fluid()

    # Mark top 20% of particles as waste (oil floating on top initially)
    # In the dam break, these are the particles at the highest y-positions
    waste_particle_count = int(0.2 * NUM_PARTICLES)

    # Find particles with highest y-positions
    positions_np = solver.positions.to_numpy()
    y_positions = positions_np[:, 1]
    waste_indices = np.argsort(y_positions)[-waste_particle_count:]

    # Mark waste particles
    print(f"Marking {waste_particle_count} particles as waste (oil)...")
    for idx in waste_indices:
        concentration_tracker.concentration[idx] = 1.0
        concentration_tracker.particle_type[idx] = PARTICLE_TYPE_FLUID_WASTE

    # Create metrics tracker
    print("Initializing metrics tracker...")
    metrics = ConcentrationMetrics()

    # Create enhanced renderer
    print("Starting real-time waste tracking visualization...")
    renderer = WasteTrackingRenderer(solver, concentration_tracker)

    # Simulation parameters
    target_time = 5.0  # Simulate 5 seconds
    export_interval = 0.05  # Export every 50ms
    print_interval = 10  # Print every 10 steps
    metrics_interval = 50  # Compute metrics every 50 steps

    # Main simulation loop
    time = 0.0
    step = 0
    frame = 0
    next_export_time = 0.0

    print("\n" + "="*80)
    print("Starting Waste Tracking Simulation (Phase 2)")
    print("="*80)
    print("Controls: ESC to exit, Right-click + drag to rotate camera")
    print("Color Legend: Blue = Clean Water | Yellow = Mixed | Red = Pure Waste")
    print("="*80 + "\n")

    while time < target_time and not renderer.should_close():
        # Compute adaptive timestep
        dt = solver.compute_timestep()

        # Perform SPH step (fluid dynamics)
        solver.step(dt)

        # Perform concentration advection-diffusion step
        concentration_tracker.step(
            solver.positions,
            solver.velocities,
            solver.masses,
            solver.densities,
            solver.neighbor_search,
            dt
        )

        # Update time
        time += dt
        step += 1

        # Export frame if needed
        if time >= next_export_time:
            positions = solver.positions.to_numpy()
            velocities = solver.velocities.to_numpy()
            densities = solver.densities.to_numpy()
            pressures = solver.pressures.to_numpy()
            concentration = concentration_tracker.concentration.to_numpy()

            export_waste_data(
                positions,
                velocities,
                densities,
                pressures,
                concentration,
                frame,
                OUTPUT_DIR
            )
            next_export_time += export_interval
            frame += 1

        # Render with color-coded particles
        renderer.render()

        # Compute and print metrics
        if step % metrics_interval == 0:
            # Compute statistics
            stats = metrics.compute_statistics(
                concentration_tracker.concentration,
                solver.masses,
                solver.positions,
                NUM_PARTICLES
            )

            # Detect contamination zones
            metrics.detect_contamination_zones(
                concentration_tracker.concentration,
                NUM_PARTICLES
            )
            zones = metrics.get_zone_volumes()

            print(f"\n{'='*80}")
            print(f"Step {step} | Time: {time:.3f}s | Frame: {frame}")
            print(f"{'='*80}")
            print(f"Concentration Statistics:")
            print(f"  Mean:  {stats[0]:.4f} | Max: {stats[1]:.4f} | Min: {stats[2]:.4f}")
            print(f"  Variance: {stats[3]:.6f} | Mixing Index: {stats[8]:.4f}")
            print(f"Center of Mass: ({stats[4]:.3f}, {stats[5]:.3f}, {stats[6]:.3f})")
            print(f"Total Waste Mass: {stats[7]:.3f} kg")
            print(f"\nContamination Zones:")
            print(f"  Low (>10%):    {zones['low']['particle_count']:5d} particles "
                  f"({zones['low']['percentage']:5.2f}% of volume)")
            print(f"  Medium (>50%): {zones['medium']['particle_count']:5d} particles "
                  f"({zones['medium']['percentage']:5.2f}% of volume)")
            print(f"  High (>90%):   {zones['high']['particle_count']:5d} particles "
                  f"({zones['high']['percentage']:5.2f}% of volume)")
            print(f"{'='*80}\n")

        # Console output (brief)
        if step % print_interval == 0 and step % metrics_interval != 0:
            total_conc = concentration_tracker.compute_total_concentration()
            print(f"Step {step:5d} | "
                  f"Time: {time:6.3f}s | "
                  f"dt: {dt*1000:5.2f}ms | "
                  f"Total Conc: {total_conc:8.2f} | "
                  f"Frames: {frame}")

    print("\n" + "="*80)
    print(f"Waste Tracking Simulation Completed!")
    print("="*80)
    print(f"Total steps: {step}")
    print(f"Total time: {time:.2f}s")
    print(f"Frames exported: {frame}")
    print(f"Output directory: {OUTPUT_DIR}")
    print("\nNext Steps:")
    print("1. Open ParaView and load output/frames/waste_particles_*.vtk")
    print("2. Apply 'Glyph' filter to visualize particles as spheres")
    print("3. Color by 'concentration' field (0=blue/clean, 1=red/waste)")
    print("4. Play animation to see pollutant dispersion over time")
    print("="*80)


if __name__ == "__main__":
    main()
