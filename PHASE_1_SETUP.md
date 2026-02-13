# Phase 1: Unity Project Setup & Testing ✓ READY TO START

## Overview

Phase 1 establishes the working foundation for all subsequent educational features:
- **Existing Client:** 85% complete (SPHStreamingClient.cs, 335 lines)
- **Fixed Backend:** Phase 0 WebSocket broadcasting now works ✓
- **Goal:** Create Unity project and verify full pipeline end-to-end

**Estimated Time:** 2-3 hours (hands-on with Unity)

## Pre-Phase 1 Checklist

Before starting, verify:

- [ ] Python environment set up with dependencies
- [ ] WebSocket server tested successfully (Phase 0 ✓)
- [ ] Unity 2021.3 LTS or newer installed
- [ ] Git repository clean (no uncommitted changes)

## Phase 1 Implementation Steps

### Step 1: Create Unity Project (15 minutes)

**Objective:** Create base Unity project with correct settings

```bash
# 1. Open Unity Hub
# 2. New Project → 3D Core template
#    - Version: 2021.3 LTS (or 2022 LTS)
#    - Project Name: "SPH-Visualization"
#    - Location: Anywhere except Desktop/Waste Management
```

**Verification:**
- [ ] Project opens without errors
- [ ] Scene has Main Camera (default)
- [ ] Can press Play and see empty blue scene

### Step 2: Install NativeWebSocket Package (5 minutes)

**Objective:** Add WebSocket capability to Unity

```
In Unity Editor:
1. Window → Package Manager
2. Click [+] button (top-left of Package Manager window)
3. "Add package from git URL..."
4. Paste: https://github.com/endel/NativeWebSocket.git#upm
5. Click [Add]
6. Wait for "Installing" to complete
```

**Verification:**
- [ ] No errors in Console
- [ ] NativeWebSocket appears in Package Manager
- [ ] No red error messages

### Step 3: Setup Scene Structure (10 minutes)

**Objective:** Create game objects for SPH simulation

**Create SPH Container:**
```
Hierarchy → Right-click → Create Empty
- Name: "SPH Simulation"
- Position: (0, 0, 0)
- Scale: (1, 1, 1)
```

**Create Particle Prefab:**
```
1. GameObject → 3D Object → Sphere
   - Name: "ParticlePrefab"
   - Position: (0, 0, 0)
   - Scale: (0.02, 0.02, 0.02)

2. Drag ParticlePrefab from Hierarchy to Project/Prefabs/
   (Create Prefabs folder if needed)

3. Delete ParticlePrefab from Hierarchy

4. Select ParticlePrefab asset in Project
```

**Create Particle Material:**
```
1. Project → Right-click → Create → Material
   - Name: "ParticleMaterial"

2. Inspector settings:
   - Shader: Standard
   - Rendering Mode: Opaque
   - Enable "GPU Instancing" checkbox ✓

3. Color: Leave as default white (will be overridden by script)
```

**Apply Material to Prefab:**
```
1. Select ParticlePrefab asset
2. Drag ParticleMaterial onto Particle Renderer in Inspector
3. Verify material is assigned
```

**Verification:**
- [ ] "SPH Simulation" empty GameObject in scene
- [ ] ParticlePrefab in Project/Prefabs/
- [ ] Material assigned to ParticlePrefab
- [ ] No materials errors in Console

### Step 4: Add SPHStreamingClient Script (10 minutes)

**Objective:** Copy and attach the WebSocket client

**Copy Script:**
```
1. Create folder: Assets/Scripts/
2. Copy SPHStreamingClient.cs from:
   /Users/yeonjune.kim.27/Desktop/Waste\ Management/unity_client/SPHStreamingClient.cs

3. Paste into: Assets/Scripts/SPHStreamingClient.cs
```

**Attach to Scene:**
```
1. Select "SPH Simulation" GameObject in Hierarchy
2. Inspector → Add Component
3. Search for "SPH Streaming Client"
4. Click to add
```

**Verification:**
- [ ] Script added successfully (no compile errors)
- [ ] Component shows in Inspector for "SPH Simulation"
- [ ] Console shows no red error messages

### Step 5: Configure Script Parameters (5 minutes)

**Objective:** Set up WebSocket connection and rendering options

**In Inspector for SPHStreamingClient:**

```
WebSocket Connection:
- Server Url: ws://localhost:8765

Particle Visualization:
- Particle Prefab: [Drag ParticlePrefab here]
- Particle Scale: 0.02
- Use GPU Instancing: ✓ (checked)
- Max Particles: 8000

Color Settings:
- Clean Color: (0, 0, 1) - Blue
- Mixed Color: (1, 1, 0) - Yellow
- Waste Color: (1, 0, 0) - Red

UI Display:
- Show Metrics: ✓ (checked)
```

**Verification:**
- [ ] All fields populated correctly
- [ ] Particle Prefab is assigned
- [ ] No warnings in Inspector

### Step 6: Setup Camera (5 minutes)

**Objective:** Position camera for visualization

**Select Main Camera** (in Hierarchy)

**Option A - Manual Setup:**
```
Inspector Properties:
- Position: (1.5, 1.0, 1.5)
- Rotation: (20, -45, 0)
- Field of View: 60
```

**Option B - Orbit Camera (Advanced):**
```
Create Assets/Scripts/OrbitCamera.cs:
[Use the OrbitCamera script from README_Unity.md lines 81-122]

Then:
1. Select Main Camera
2. Add Component → Script → OrbitCamera
3. Drag "SPH Simulation" to Target field
4. Right-click + drag to rotate view while testing
```

**Verification:**
- [ ] Camera can see simulation area (0,0,0) to (1,1,1)
- [ ] Camera not inside particles
- [ ] Reasonable viewing angle

## Phase 1 Testing

### Test 1: Compilation Check

```bash
# In Unity Console, verify no compilation errors
# File → Build Settings → (should show no errors)
```

**Result:** ✓ Script compiles cleanly

### Test 2: WebSocket Connection

**Terminal 1 - Start Python Server:**
```bash
cd /Users/yeonjune.kim.27/Desktop/Waste\ Management
python unity_streaming_main.py
```

**Expected output:**
```
[WebSocket] Starting server on localhost:8765
[WebSocket] Server running - waiting for connections...
READY FOR UNITY CONNECTION
```

**Terminal 2 - (Optional) Monitor Connection:**
```bash
python test_streaming_debug.py
```

**In Unity:**
1. Press Play button
2. Check Console for:
   ```
   [SPH Client] Connecting to ws://localhost:8765
   [SPH Client] Connected to simulation server!
   ```

**Verification:**
- [ ] "Connected to simulation server!" appears in Console
- [ ] No "Connection refused" errors
- [ ] Metrics display shows "Connected" in top-left

### Test 3: Particle Rendering

**While Play mode is active:**

```
Expected behavior:
- Blue/red particles appear in viewport
- Particles move smoothly
- Colors change based on concentration (blue → yellow → red)
- FPS stays at 60 (check Stats window: Window → Analysis → Profiler)
```

**Verification:**
- [ ] Particles visible in Game view
- [ ] Motion is smooth (no stuttering)
- [ ] Colors change realistically
- [ ] Console shows no errors
- [ ] FPS ≥ 60

### Test 4: Metrics Display

**In Game view (top-left corner):**

```
Expected display:
SPH Simulation - Phase 3
Status: Connected
Time: 0.123s
Step: 45
Particles: 2000  (or 8000 if using full particles)
Mean Concentration: 0.234
Mixing Index: 0.567
Center of Mass: (0.5, 0.2, 0.5)
```

**Verification:**
- [ ] All metrics display
- [ ] Values update every frame
- [ ] Time increases linearly
- [ ] Metrics readable (not overlapped)

### Full End-to-End Test Checklist

```
Pre-Flight:
- [ ] Python server running on ws://localhost:8765
- [ ] Test WebSocket client passes (5/5 frames)
- [ ] Unity project created and NativeWebSocket installed
- [ ] SPHStreamingClient.cs attached to scene
- [ ] All Inspector values configured

During Test:
- [ ] Press Play in Unity
- [ ] [SPH Client] Connected message appears
- [ ] Particles appear in viewport within 2 seconds
- [ ] Particles animate smoothly (30 FPS from server)
- [ ] Colors show concentration gradient
- [ ] Metrics display updates in real-time

Post-Test:
- [ ] Simulation runs for 10 seconds without errors
- [ ] Stop Python server (Ctrl+C)
- [ ] Press Stop in Unity
- [ ] Check Console for any errors (should be none)
```

## Troubleshooting

### Issue: "Connection refused" error

**Cause:** Python server not running or wrong URL

**Solution:**
```bash
# Terminal 1: Start Python server
python unity_streaming_main.py

# Verify output includes:
# [WebSocket] Server running - waiting for connections...
```

**Then in Unity:**
- Check Inspector: Server Url = `ws://localhost:8765`
- Press Play again

### Issue: No particles appearing

**Possible causes:**

1. **Particle Prefab not assigned:**
   - Select "SPH Simulation" in Hierarchy
   - Check Inspector: "Particle Prefab" field
   - Should show "ParticlePrefab (GameObject)"
   - If empty, drag ParticlePrefab from Project here

2. **Camera not positioned correctly:**
   - Main Camera Position: (1.5, 1.0, 1.5)
   - Should see 1m³ cube centered at origin
   - Zoom out if needed (increase distance)

3. **Particles too small:**
   - Inspector: Particle Scale = 0.02
   - Temporary test: Change to 0.1
   - If particles appear, scale is the issue

### Issue: Poor performance / Low FPS

**Solution 1: Reduce particle count in Python**
```bash
# Edit unity_streaming_main.py line 244:
# broadcast_fps=30  → broadcast_fps=15

# Or in config.py:
# NUM_PARTICLES = 8000  → NUM_PARTICLES = 2000
```

**Solution 2: Reduce particles in Unity**
- Inspector: Max Particles = 4000

**Solution 3: Disable metrics**
- Inspector: Show Metrics = ☐ (unchecked)

### Issue: White/grey particles instead of colored

**Cause:** Material not assigned to prefab

**Solution:**
1. Select ParticlePrefab in Project
2. Drag ParticleMaterial onto it
3. Verify "Material" field is filled

## Success Criteria - Phase 1 Complete

✓ **Technical Success:**
- [ ] Python server broadcasts data successfully
- [ ] Unity client connects without errors
- [ ] 8000 particles render smoothly (60 FPS)
- [ ] Color gradient displays correctly
- [ ] Metrics update in real-time
- [ ] Simulation runs for 10+ minutes without crashes

✓ **Visual Success:**
- [ ] Particles clearly visible
- [ ] Blue → Yellow → Red gradient obvious
- [ ] Smooth motion (no jitter)
- [ ] Colors match concentration physically

✓ **Educational Success:**
- [ ] Particles simulate waste diffusion realistically
- [ ] Metrics match Python backend values
- [ ] Visualization conveys Calculus 3 concepts

## Moving to Phase 2

Once Phase 1 is complete:

1. **Save Phase 1 checkpoint:**
   ```bash
   git add .
   git commit -m "Phase 1 Complete: Unity project setup and streaming verified"
   ```

2. **Next phase objective:** Add gradient arrow visualization
   - Will add new GradientArrowRenderer.cs script
   - Sample 5×5×5 grid points
   - Render arrows scaled by |∇C|
   - Toggle with `G` key

3. **Time estimate:** Phase 2 = 6-8 hours

## Reference Files

**Original Implementations:**
- `unity_client/SPHStreamingClient.cs` - WebSocket client (335 lines) ✓ DONE
- `unity_client/README_Unity.md` - Setup guide (335 lines)
- `unity_streaming_main.py` - Python server (273 lines)
- `sph_fluid_sim/network/websocket_server.py` - Core WebSocket (317 lines)

**Test Files:**
- `test_websocket_broadcast.py` - Broadcast fix verification ✓ PASSED
- `test_streaming_e2e.py` - Full end-to-end test
- `test_streaming_debug.py` - Connection diagnostics

**Configuration:**
- `sph_fluid_sim/config.py` - All parameters (physics constants, particle count, etc.)

## Quick Reference Commands

```bash
# Start Python server (WebSocket on localhost:8765)
python unity_streaming_main.py

# Test WebSocket broadcast (if you want to verify the fix)
python test_websocket_broadcast.py

# Run end-to-end test (Python + Unity client simulation)
python test_streaming_e2e.py

# In Unity Editor:
# File → Build Settings → Scenes in Build
# Make sure "Scenes/Main" or your scene is listed
```

---

## Phase 1 Completion Checklist

**Before moving to Phase 2, verify:**

- [ ] Unity project created (2021.3+ LTS)
- [ ] NativeWebSocket package installed
- [ ] Scene structure: SPH Simulation, ParticlePrefab, ParticleMaterial
- [ ] SPHStreamingClient.cs attached and configured
- [ ] Python server runs successfully
- [ ] Unity connects to server (see "Connected" message)
- [ ] Particles render with color gradient
- [ ] Metrics display updates in real-time
- [ ] No Console errors
- [ ] 60 FPS maintained
- [ ] Simulation stable for 10+ seconds
- [ ] Changes committed to git

**Phase 1 Estimated Duration:** 2-3 hours
**Phase 1 Status:** READY TO START ✓

---

*Next: Phase 2 - Gradient Visualization (6-8 hours)*
