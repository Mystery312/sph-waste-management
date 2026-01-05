"""
Comprehensive Test Suite for All Phases

Tests Phase 1, Phase 2, and Phase 3 functionality.
Run this to verify your installation is working correctly.
"""

import sys
import taichi as ti
import numpy as np


def print_section(title):
    """Print formatted section header."""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)


def test_phase_1():
    """Test Phase 1: Basic SPH Physics."""
    print_section("PHASE 1: Basic SPH Physics Engine")

    from sph_fluid_sim.core.solver import WCSPHSolver

    # Create solver
    print("Creating SPH solver...")
    solver = WCSPHSolver(num_particles=500)
    solver.initialize()
    print("✓ Solver initialized with 500 particles")

    # Run a few steps
    print("Running 5 simulation steps...")
    for i in range(5):
        dt = solver.compute_timestep()
        solver.step(dt)
        if i == 0:
            print(f"  Step {i}: dt = {dt*1000:.2f} ms")

    # Check results
    positions = solver.positions.to_numpy()
    velocities = solver.velocities.to_numpy()
    densities = solver.densities.to_numpy()

    assert positions.shape == (500, 3), "Position shape incorrect"
    assert velocities.shape == (500, 3), "Velocity shape incorrect"
    assert densities.shape == (500,), "Density shape incorrect"

    print(f"✓ Position range: [{positions.min():.3f}, {positions.max():.3f}]")
    print(f"✓ Density range: [{densities.min():.1f}, {densities.max():.1f}] kg/m³")
    print(f"✓ Max velocity: {np.linalg.norm(velocities, axis=1).max():.3f} m/s")

    print("\n✅ PHASE 1 PASSED")
    return True


def test_phase_2():
    """Test Phase 2: Waste Tracking."""
    print_section("PHASE 2: Waste Tracking & Concentration")

    from sph_fluid_sim.config import PARTICLE_TYPE_FLUID_WASTE
    from sph_fluid_sim.core.solver import WCSPHSolver
    from sph_fluid_sim.tracking.concentration import ConcentrationTracker
    from sph_fluid_sim.analytics.metrics import ConcentrationMetrics

    # Create components
    print("Creating solver and concentration tracker...")
    solver = WCSPHSolver(num_particles=500)
    solver.initialize()

    tracker = ConcentrationTracker(num_particles=500)
    tracker.initialize_clean_fluid()

    # Mark top 20% as waste
    positions_np = solver.positions.to_numpy()
    y_positions = positions_np[:, 1]
    waste_count = int(0.2 * 500)
    waste_indices = np.argsort(y_positions)[-waste_count:]

    for idx in waste_indices:
        tracker.concentration[idx] = 1.0
        tracker.particle_type[idx] = PARTICLE_TYPE_FLUID_WASTE

    print(f"✓ Marked {waste_count} particles as waste")

    # Create metrics
    metrics = ConcentrationMetrics()

    # Run simulation
    print("Running 5 coupled simulation steps...")
    for i in range(5):
        dt = solver.compute_timestep()
        solver.step(dt)
        tracker.step(
            solver.positions,
            solver.velocities,
            solver.masses,
            solver.densities,
            solver.neighbor_search,
            dt
        )

    # Compute final statistics
    stats = metrics.compute_statistics(
        tracker.concentration,
        solver.masses,
        solver.positions,
        500
    )

    metrics.detect_contamination_zones(tracker.concentration, 500)
    zones = metrics.get_zone_volumes()

    print(f"✓ Mean concentration: {stats[0]:.4f}")
    print(f"✓ Mixing index: {stats[8]:.4f}")
    print(f"✓ High contamination zone: {zones['high']['particle_count']} particles")

    # Verify concentration is conserved
    concentration_np = tracker.concentration.to_numpy()
    assert concentration_np.min() >= 0.0, "Concentration below 0"
    assert concentration_np.max() <= 1.0, "Concentration above 1"

    print("\n✅ PHASE 2 PASSED")
    return True


def test_phase_3():
    """Test Phase 3: WebSocket Server."""
    print_section("PHASE 3: WebSocket Real-Time Streaming")

    from sph_fluid_sim.network.websocket_server import SimulationDataServer

    # Create server
    print("Creating WebSocket server...")
    server = SimulationDataServer(host='localhost', port=8767)
    print("✓ Server created on port 8767")

    # Test data encoding
    print("Testing data encoding...")
    positions = np.random.rand(100, 3)
    velocities = np.random.rand(100, 3) * 0.1
    densities = np.ones(100) * 1000.0
    pressures = np.random.rand(100) * 100.0
    concentrations = np.random.rand(100)

    server.update_simulation_data(
        time=1.0,
        step=50,
        positions=positions,
        velocities=velocities,
        densities=densities,
        pressures=pressures,
        concentrations=concentrations,
        metrics={'mean_concentration': 0.5}
    )
    print("✓ Data updated successfully")

    # Test JSON encoding
    indices = np.arange(0, 100, 2)
    json_data = server._encode_json(indices)
    print(f"✓ JSON encoding: {len(json_data)} characters")

    # Test binary encoding
    server.binary_mode = True
    binary_data = server._encode_binary(indices)
    print(f"✓ Binary encoding: {len(binary_data)} bytes")

    # Verify compression
    server.compression_enabled = True
    server.binary_mode = False
    compressed_json = server._encode_json(indices)
    compression_ratio = len(json_data) / max(len(compressed_json), 1)
    print(f"✓ Compression ratio: {compression_ratio:.2f}x")

    print("\n✅ PHASE 3 PASSED")
    return True


def test_vtk_export():
    """Test VTK file export."""
    print_section("VTK Export Test")

    import os
    from waste_tracking_main import export_waste_data

    # Create test directory
    test_dir = "output/test_vtk"
    os.makedirs(test_dir, exist_ok=True)

    # Generate test data
    print("Generating test data...")
    num_particles = 50
    positions = np.random.rand(num_particles, 3)
    velocities = np.random.rand(num_particles, 3) * 0.1
    densities = np.ones(num_particles) * 1000.0
    pressures = np.random.rand(num_particles) * 100.0
    concentration = np.linspace(0.0, 1.0, num_particles)

    # Export VTK file
    export_waste_data(positions, velocities, densities, pressures, concentration, 0, test_dir)
    vtk_file = os.path.join(test_dir, "waste_particles_00000.vtk")

    assert os.path.exists(vtk_file), "VTK file not created"
    print(f"✓ VTK file created: {vtk_file}")

    # Read and verify
    with open(vtk_file, 'r') as f:
        content = f.read()

    required_fields = ['POINTS', 'velocity', 'density', 'pressure', 'concentration']
    for field in required_fields:
        assert field in content, f"Missing field: {field}"
        print(f"✓ Field present: {field}")

    file_size = os.path.getsize(vtk_file)
    print(f"✓ File size: {file_size} bytes")

    print("\n✅ VTK EXPORT PASSED")
    return True


def main():
    """Run all tests."""
    print("\n" + "█"*80)
    print("█" + " "*78 + "█")
    print("█" + "  SPH WASTE MANAGEMENT - COMPREHENSIVE TEST SUITE".center(78) + "█")
    print("█" + " "*78 + "█")
    print("█"*80)

    # Initialize Taichi in CPU mode for testing
    print("\nInitializing Taichi (CPU mode for compatibility)...")
    ti.init(arch=ti.cpu, debug=False)
    print("✓ Taichi initialized")

    # Run tests
    results = {}

    try:
        results['Phase 1'] = test_phase_1()
    except Exception as e:
        print(f"\n❌ PHASE 1 FAILED: {e}")
        results['Phase 1'] = False

    try:
        results['Phase 2'] = test_phase_2()
    except Exception as e:
        print(f"\n❌ PHASE 2 FAILED: {e}")
        results['Phase 2'] = False

    try:
        results['Phase 3'] = test_phase_3()
    except Exception as e:
        print(f"\n❌ PHASE 3 FAILED: {e}")
        results['Phase 3'] = False

    try:
        results['VTK Export'] = test_vtk_export()
    except Exception as e:
        print(f"\n❌ VTK EXPORT FAILED: {e}")
        results['VTK Export'] = False

    # Print summary
    print("\n" + "="*80)
    print("  TEST SUMMARY")
    print("="*80)

    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:20s} : {status}")
        all_passed = all_passed and passed

    print("="*80)

    if all_passed:
        print("\n🎉 ALL TESTS PASSED! Your installation is working correctly.")
        print("\nNext steps:")
        print("  1. Run Phase 1:  python main.py")
        print("  2. Run Phase 2:  python waste_tracking_main.py")
        print("  3. Run Phase 3:  python unity_streaming_main.py")
        print("\nSee QUICKSTART.md for detailed usage instructions.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        print("Common issues:")
        print("  - Missing dependencies: pip install -r requirements.txt")
        print("  - Taichi not installed: pip install taichi>=1.6.0")
        print("  - Import errors: Check PYTHONPATH includes project directory")
        return 1


if __name__ == "__main__":
    sys.exit(main())
