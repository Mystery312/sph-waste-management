# Unity Client Setup Guide - Phase 3

This guide will help you set up the Unity3D client to visualize the SPH simulation in real-time.

## Prerequisites

- Unity 2021.3 LTS or newer
- Python simulation running ([unity_streaming_main.py](../unity_streaming_main.py))
- Basic Unity knowledge

## Quick Start (5 minutes)

### Step 1: Create Unity Project

1. Open Unity Hub
2. Click "New Project"
3. Select "3D Core" template
4. Name it "SPH Visualization"
5. Click "Create Project"

### Step 2: Install NativeWebSocket Package

1. In Unity, go to **Window → Package Manager**
2. Click the **+** button in top-left
3. Select **"Add package from git URL..."**
4. Enter: `https://github.com/endel/NativeWebSocket.git#upm`
5. Click **Add**
6. Wait for installation to complete

### Step 3: Setup Scene

1. In **Hierarchy**, create empty GameObject:
   - Right-click → Create Empty
   - Name it "SPH Simulation"

2. Create particle prefab:
   - GameObject → 3D Object → Sphere
   - Scale it to (0.02, 0.02, 0.02)
   - Drag it to Project window to create prefab
   - Delete the sphere from scene
   - Name prefab "ParticlePrefab"

3. Create material for particles:
   - Project window → Right-click → Create → Material
   - Name it "ParticleMaterial"
   - Set Rendering Mode → "Opaque"
   - Enable GPU Instancing checkbox

4. Apply material to prefab:
   - Select ParticlePrefab
   - Drag ParticleMaterial to it

### Step 4: Add Client Script

1. Copy [SPHStreamingClient.cs](SPHStreamingClient.cs) to your Unity project's `Assets/Scripts/` folder
2. Select "SPH Simulation" GameObject
3. Click **Add Component** in Inspector
4. Search for "SPH Streaming Client" and add it

### Step 5: Configure Script

In the Inspector, set:
- **Server URL**: `ws://localhost:8765`
- **Particle Prefab**: Drag your ParticlePrefab here
- **Particle Scale**: `0.02`
- **Use GPU Instancing**: ✓ (checked)
- **Show Metrics**: ✓ (checked)

Color settings (optional):
- **Clean Color**: Blue (0, 0, 255)
- **Mixed Color**: Yellow (255, 255, 0)
- **Waste Color**: Red (255, 0, 0)

### Step 6: Setup Camera

1. Select Main Camera
2. Set Position: (1.5, 1.0, 1.5)
3. Set Rotation: (20, -45, 0)
4. Or use this script for orbit camera:

```csharp
// Add to Main Camera for mouse orbit controls
using UnityEngine;

public class OrbitCamera : MonoBehaviour
{
    public Transform target;
    public float distance = 2.0f;
    public float xSpeed = 120.0f;
    public float ySpeed = 120.0f;

    private float x = 0.0f;
    private float y = 0.0f;

    void Start()
    {
        Vector3 angles = transform.eulerAngles;
        x = angles.y;
        y = angles.x;

        if (target == null)
        {
            target = GameObject.Find("SPH Simulation").transform;
        }
    }

    void LateUpdate()
    {
        if (Input.GetMouseButton(1))  // Right mouse button
        {
            x += Input.GetAxis("Mouse X") * xSpeed * 0.02f;
            y -= Input.GetAxis("Mouse Y") * ySpeed * 0.02f;
        }

        Quaternion rotation = Quaternion.Euler(y, x, 0);
        Vector3 position = rotation * new Vector3(0.0f, 0.0f, -distance) + target.position;

        transform.rotation = rotation;
        transform.position = position;
    }
}
```

### Step 7: Run Simulation

1. **Start Python simulation first:**
   ```bash
   cd "Waste Management"
   python unity_streaming_main.py
   ```

   Wait for message: "READY FOR UNITY CONNECTION"

2. **Press Play in Unity**
   - You should see "Connected" in the metrics display
   - Particles will start appearing and animating
   - Colors will show concentration levels

## Understanding the Visualization

### Color Coding

- **Blue particles**: Clean water (concentration = 0%)
- **Yellow particles**: Mixed (concentration ≈ 50%)
- **Red particles**: Pure waste (concentration = 100%)

### Metrics Display (Top-Left)

```
SPH Simulation - Phase 3
Status: Connected
Time: 2.345s                   ← Simulation time
Step: 1234                     ← Simulation timestep
Particles: 8000                ← Number of particles
Mean Concentration: 0.1234     ← Average concentration
Mixing Index: 0.5678           ← 0=unmixed, 1=fully mixed
Center of Mass: (0.5, 0.3, 0.5) ← Waste center position
```

## Performance Optimization

### For Slow Computers

1. **Reduce particle count** in Python:
   - Edit [config.py](../sph_fluid_sim/config.py)
   - Set `NUM_PARTICLES = 2000`

2. **Enable decimation** in Python:
   - Edit [unity_streaming_main.py](../unity_streaming_main.py)
   - In `SimulationDataServer.__init__()`:
   ```python
   self.decimation_factor = 2  # Send every 2nd particle
   ```

3. **Lower broadcast rate**:
   - In [unity_streaming_main.py](../unity_streaming_main.py):
   ```python
   broadcast_fps=15  # Reduce from 30
   ```

4. **In Unity**:
   - Set **Max Particles** to lower value (e.g., 4000)
   - Disable **Show Metrics** for slight performance boost

### For High-End Systems

1. **Increase particle count** in Python:
   ```python
   NUM_PARTICLES = 16000
   ```

2. **Higher quality rendering** in Unity:
   - Use higher poly sphere prefab
   - Add reflective/metallic materials
   - Enable post-processing effects

## Advanced Features

### Multiple Camera Views

Create multiple cameras for different perspectives:

```csharp
// Add Picture-in-Picture view
Camera mainCam = Camera.main;
Camera pipCam = new GameObject("PIP Camera").AddComponent<Camera>();
pipCam.transform.position = new Vector3(0.5f, 2.0f, 0.5f);
pipCam.transform.LookAt(Vector3.one * 0.5f);
pipCam.rect = new Rect(0.75f, 0.75f, 0.2f, 0.2f);
pipCam.depth = mainCam.depth + 1;
```

### Recording Video

1. Install Unity Recorder:
   - Window → Package Manager
   - Search "Recorder"
   - Install

2. Configure recording:
   - Window → General → Recorder → Recorder Window
   - Add Recorder → Movie
   - Set output path and quality

### Custom Shaders

Create a shader that visualizes concentration with transparency:

```glsl
Shader "Custom/ParticleConcentration"
{
    Properties
    {
        _Concentration ("Concentration", Range(0,1)) = 0
    }
    SubShader
    {
        Tags { "Queue"="Transparent" "RenderType"="Transparent" }
        Blend SrcAlpha OneMinusSrcAlpha

        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"

            float _Concentration;

            struct appdata
            {
                float4 vertex : POSITION;
            };

            struct v2f
            {
                float4 vertex : SV_POSITION;
            };

            v2f vert (appdata v)
            {
                v2f o;
                o.vertex = UnityObjectToClipPos(v.vertex);
                return o;
            }

            fixed4 frag (v2f i) : SV_Target
            {
                // Blue → Yellow → Red
                fixed4 col;
                if (_Concentration < 0.5)
                {
                    float t = _Concentration * 2.0;
                    col = lerp(fixed4(0,0,1,0.5), fixed4(1,1,0,0.7), t);
                }
                else
                {
                    float t = (_Concentration - 0.5) * 2.0;
                    col = lerp(fixed4(1,1,0,0.7), fixed4(1,0,0,1), t);
                }
                return col;
            }
            ENDCG
        }
    }
}
```

## Troubleshooting

### "Connection failed" or "Disconnected"

1. **Check Python is running:**
   ```bash
   # You should see this message:
   [WebSocket] Server running - waiting for connections...
   ```

2. **Check firewall**: Allow port 8765

3. **Wrong URL**: Verify `ws://localhost:8765` in Unity Inspector

### No particles appearing

1. **Check particle prefab**: Must be assigned in Inspector
2. **Check scale**: Particles might be too small
3. **Check camera position**: Move camera back to see particles

### Poor performance / Low FPS

1. **Reduce particle count** in Python config
2. **Enable GPU instancing** in Unity
3. **Use simpler particle prefab** (fewer polygons)
4. **Lower broadcast rate** to 15 FPS

### Particles appear as white

- Material not assigned to prefab
- Shader compilation error (check Console)

## Next Steps

- Add particle trails for flow visualization
- Implement heatmap overlay for concentration
- Add contamination zone boundaries
- Create time-series graphs of metrics
- Implement manual camera waypoints
- Add export functionality for screenshots/videos

## Support

- Unity Documentation: https://docs.unity3d.com/
- NativeWebSocket: https://github.com/endel/NativeWebSocket
- Project Issues: See main [README.md](../README.md)
