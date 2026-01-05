"""
Data Export - VTK and CSV formats

Exports particle data for post-processing in ParaView and plotting tools.
"""

import numpy as np
import os


def export_to_vtk(positions, velocities, densities, pressures, frame_num, output_dir):
    """
    Export particle data to VTK format for ParaView visualization.

    Args:
        positions: Particle positions (N×3 array)
        velocities: Particle velocities (N×3 array)
        densities: Particle densities (N array)
        pressures: Particle pressures (N array)
        frame_num: Frame number
        output_dir: Output directory
    """
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"particles_{frame_num:06d}.vtk")

    num_particles = len(positions)

    with open(filename, 'w') as f:
        # VTK header
        f.write("# vtk DataFile Version 3.0\n")
        f.write("SPH Fluid Simulation\n")
        f.write("ASCII\n")
        f.write("DATASET POLYDATA\n")

        # Write positions
        f.write(f"POINTS {num_particles} float\n")
        for pos in positions:
            f.write(f"{pos[0]} {pos[1]} {pos[2]}\n")

        # Write point data
        f.write(f"\nPOINT_DATA {num_particles}\n")

        # Density
        f.write("SCALARS density float 1\n")
        f.write("LOOKUP_TABLE default\n")
        for rho in densities:
            f.write(f"{rho}\n")

        # Pressure
        f.write("\nSCALARS pressure float 1\n")
        f.write("LOOKUP_TABLE default\n")
        for p in pressures:
            f.write(f"{p}\n")

        # Velocity
        f.write("\nVECTORS velocity float\n")
        for vel in velocities:
            f.write(f"{vel[0]} {vel[1]} {vel[2]}\n")


def export_to_csv(positions, frame_num, output_dir):
    """
    Export particle positions to CSV format.

    Args:
        positions: Particle positions (N×3 array)
        frame_num: Frame number
        output_dir: Output directory
    """
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"positions_{frame_num:06d}.csv")

    with open(filename, 'w') as f:
        f.write("x,y,z\n")
        for pos in positions:
            f.write(f"{pos[0]},{pos[1]},{pos[2]}\n")
