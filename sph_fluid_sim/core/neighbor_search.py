"""
Grid-Based Neighbor Search for SPH

This module implements efficient spatial hashing for finding particle neighbors.
Uses a uniform grid where each cell has size = 2h (kernel support radius).

Algorithm:
1. Assign each particle to a grid cell based on position
2. For neighbor queries, search the particle's cell and 26 adjacent cells (3×3×3 stencil)
3. Check distance to determine if particles are within support radius

Complexity: O(N) expected time for uniform particle distribution
"""

import taichi as ti
from ..config import *


@ti.data_oriented
class NeighborSearch:
    """
    Grid-based spatial hashing for efficient neighbor finding in SPH.
    """

    def __init__(self, num_particles: int, grid_resolution: int):
        """
        Initialize neighbor search data structures.

        Args:
            num_particles: Total number of particles
            grid_resolution: Number of grid cells per dimension
        """
        self.num_particles = num_particles
        self.grid_resolution = grid_resolution
        self.num_cells = grid_resolution ** 3

        # Grid data structures
        # For each particle, store which cell it belongs to
        self.particle_cell_index = ti.field(dtype=ti.i32, shape=num_particles)

        # For each cell, store count of particles
        self.cell_particle_count = ti.field(dtype=ti.i32, shape=self.num_cells)

        # For each cell, store list of particle indices
        # Conservative estimate: max 64 particles per cell
        self.max_particles_per_cell = 64
        self.cell_particle_list = ti.field(
            dtype=ti.i32,
            shape=(self.num_cells, self.max_particles_per_cell)
        )

    @ti.func
    def compute_cell_index(self, pos: ti.math.vec3) -> int:
        """
        Compute 1D cell index from 3D position.

        Args:
            pos: Particle position

        Returns:
            1D cell index in range [0, num_cells)
        """
        # Compute 3D grid coordinates
        cell_x = int(ti.floor((pos.x - BOX_MIN.x) / CELL_SIZE))
        cell_y = int(ti.floor((pos.y - BOX_MIN.y) / CELL_SIZE))
        cell_z = int(ti.floor((pos.z - BOX_MIN.z) / CELL_SIZE))

        # Clamp to grid bounds
        cell_x = ti.max(0, ti.min(cell_x, self.grid_resolution - 1))
        cell_y = ti.max(0, ti.min(cell_y, self.grid_resolution - 1))
        cell_z = ti.max(0, ti.min(cell_z, self.grid_resolution - 1))

        # Convert 3D to 1D index
        cell_index = cell_x + cell_y * self.grid_resolution + \
                     cell_z * self.grid_resolution * self.grid_resolution

        return cell_index

    @ti.kernel
    def build_grid(self, positions: ti.template()):
        """
        Build spatial hash grid from particle positions.

        Args:
            positions: Particle position field
        """
        # Clear cell counts
        for i in range(self.num_cells):
            self.cell_particle_count[i] = 0

        # Assign particles to cells
        for i in range(self.num_particles):
            cell_idx = self.compute_cell_index(positions[i])
            self.particle_cell_index[i] = cell_idx

            # Atomically increment cell count and get slot
            slot = ti.atomic_add(self.cell_particle_count[cell_idx], 1)

            # Store particle index in cell list (if space available)
            if slot < self.max_particles_per_cell:
                self.cell_particle_list[cell_idx, slot] = i

    @ti.func
    def for_all_neighbors(
        self,
        particle_idx: int,
        positions: ti.template(),
        callback: ti.template()
    ):
        """
        Iterate over all neighbors within support radius and apply callback.

        This function searches the 3×3×3 = 27 cell stencil around the particle's cell.

        Args:
            particle_idx: Index of the particle to find neighbors for
            positions: Particle position field
            callback: Function to call for each neighbor (takes neighbor_idx as argument)
        """
        pos_i = positions[particle_idx]
        cell_idx = self.particle_cell_index[particle_idx]

        # Decode 1D cell index to 3D coordinates
        cell_z = cell_idx // (self.grid_resolution * self.grid_resolution)
        temp = cell_idx % (self.grid_resolution * self.grid_resolution)
        cell_y = temp // self.grid_resolution
        cell_x = temp % self.grid_resolution

        # Search 3×3×3 stencil (27 cells including self)
        for offset_x in ti.static(range(-1, 2)):
            for offset_y in ti.static(range(-1, 2)):
                for offset_z in ti.static(range(-1, 2)):
                    # Neighbor cell coordinates
                    neighbor_cell_x = cell_x + offset_x
                    neighbor_cell_y = cell_y + offset_y
                    neighbor_cell_z = cell_z + offset_z

                    # Check if neighbor cell is within grid bounds
                    if (neighbor_cell_x >= 0 and neighbor_cell_x < self.grid_resolution and
                        neighbor_cell_y >= 0 and neighbor_cell_y < self.grid_resolution and
                        neighbor_cell_z >= 0 and neighbor_cell_z < self.grid_resolution):

                        # Convert to 1D index
                        neighbor_cell_idx = (neighbor_cell_x +
                                           neighbor_cell_y * self.grid_resolution +
                                           neighbor_cell_z * self.grid_resolution * self.grid_resolution)

                        # Iterate over particles in neighbor cell
                        num_particles_in_cell = self.cell_particle_count[neighbor_cell_idx]

                        for k in range(num_particles_in_cell):
                            if k < self.max_particles_per_cell:
                                neighbor_idx = self.cell_particle_list[neighbor_cell_idx, k]

                                # Check if within support radius (2h)
                                r_ij = pos_i - positions[neighbor_idx]
                                dist = r_ij.norm()

                                if dist < 2.0 * SMOOTHING_LENGTH:
                                    # Apply callback function
                                    callback(neighbor_idx)
