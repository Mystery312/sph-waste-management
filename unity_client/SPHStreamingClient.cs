using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using NativeWebSocket;  // Requires NativeWebSocket package

/// <summary>
/// SPH Simulation WebSocket Client for Unity
///
/// Connects to Python simulation server and receives real-time particle data.
/// Creates and updates particle visualization in Unity scene.
///
/// Installation:
/// 1. Install NativeWebSocket via Unity Package Manager
///    URL: https://github.com/endel/NativeWebSocket.git#upm
/// 2. Attach this script to a GameObject in your scene
/// 3. Configure WebSocket URL in inspector
/// 4. Run Python simulation with: python unity_streaming_main.py
/// </summary>
public class SPHStreamingClient : MonoBehaviour
{
    [Header("WebSocket Connection")]
    [Tooltip("WebSocket server URL (ws://localhost:8765)")]
    public string serverUrl = "ws://localhost:8765";

    [Header("Particle Visualization")]
    [Tooltip("Prefab for particle rendering (use Sphere)")]
    public GameObject particlePrefab;

    [Tooltip("Scale factor for particles")]
    public float particleScale = 0.02f;

    [Tooltip("Use GPU instancing for better performance")]
    public bool useGPUInstancing = true;

    [Header("Color Settings")]
    [Tooltip("Color for clean water (concentration = 0)")]
    public Color cleanColor = new Color(0, 0, 1);  // Blue

    [Tooltip("Color for mixed (concentration = 0.5)")]
    public Color mixedColor = new Color(1, 1, 0);  // Yellow

    [Tooltip("Color for pure waste (concentration = 1)")]
    public Color wasteColor = new Color(1, 0, 0);  // Red

    [Header("Performance")]
    [Tooltip("Maximum particles to render (for performance)")]
    public int maxParticles = 8000;

    [Header("UI Display")]
    [Tooltip("Display metrics on screen")]
    public bool showMetrics = true;

    // WebSocket
    private WebSocket websocket;

    // Particle data
    private List<GameObject> particleObjects = new List<GameObject>();
    private Vector3[] positions;
    private Vector3[] velocities;
    private float[] concentrations;
    private Vector3[] gradientVectors;

    // Public accessors for Phase 4 scripts
    public Vector3[] GradientVectors => gradientVectors;
    public Vector3[] Positions => positions;
    public float[] Concentrations => concentrations;
    public int ParticleCount => particleObjects.Count;

    // Metrics
    private SimulationMetrics currentMetrics = new SimulationMetrics();

    // Connection state
    private bool isConnected = false;
    private string statusMessage = "Disconnected";

    // Serializable data structures
    [Serializable]
    private class SimulationData
    {
        public string type;
        public float time;
        public int step;
        public int particle_count;
        public float[][] positions;
        public float[][] velocities;
        public float[] densities;
        public float[] pressures;
        public float[] concentrations;
        public float[][] gradients;
        public MetricsData metrics;
    }

    [Serializable]
    private class MetricsData
    {
        public float mean_concentration;
        public float max_concentration;
        public float min_concentration;
        public float variance;
        public float[] center_of_mass;
        public float total_waste_mass;
        public float mixing_index;
    }

    private class SimulationMetrics
    {
        public float time;
        public int step;
        public int particleCount;
        public float meanConcentration;
        public float mixingIndex;
        public Vector3 centerOfMass;
    }

    async void Start()
    {
        Debug.Log($"[SPH Client] Connecting to {serverUrl}");
        statusMessage = "Connecting...";

        // Create WebSocket connection
        websocket = new WebSocket(serverUrl);

        // Event handlers
        websocket.OnOpen += () =>
        {
            Debug.Log("[SPH Client] Connected to simulation server!");
            isConnected = true;
            statusMessage = "Connected";
        };

        websocket.OnError += (e) =>
        {
            Debug.LogError($"[SPH Client] WebSocket Error: {e}");
            statusMessage = $"Error: {e}";
        };

        websocket.OnClose += (e) =>
        {
            Debug.Log($"[SPH Client] Connection closed: {e}");
            isConnected = false;
            statusMessage = "Disconnected";
        };

        websocket.OnMessage += (bytes) =>
        {
            string message = System.Text.Encoding.UTF8.GetString(bytes);

            // Check if compressed (starts with 'C')
            if (message.StartsWith("C"))
            {
                Debug.LogWarning("[SPH Client] Compressed data not yet supported in C#");
                return;
            }

            // Parse JSON data
            try
            {
                SimulationData data = JsonUtility.FromJson<SimulationData>(message);

                if (data.type == "simulation_data")
                {
                    ProcessSimulationData(data);
                }
            }
            catch (Exception ex)
            {
                Debug.LogError($"[SPH Client] Failed to parse message: {ex.Message}");
            }
        };

        // Connect
        await websocket.Connect();
    }

    void Update()
    {
        // Process WebSocket messages
        #if !UNITY_WEBGL || UNITY_EDITOR
        websocket?.DispatchMessageQueue();
        #endif
    }

    void ProcessSimulationData(SimulationData data)
    {
        int particleCount = Mathf.Min(data.particle_count, maxParticles);

        // Update metrics
        currentMetrics.time = data.time;
        currentMetrics.step = data.step;
        currentMetrics.particleCount = particleCount;

        if (data.metrics != null)
        {
            currentMetrics.meanConcentration = data.metrics.mean_concentration;
            currentMetrics.mixingIndex = data.metrics.mixing_index;

            if (data.metrics.center_of_mass != null && data.metrics.center_of_mass.Length == 3)
            {
                currentMetrics.centerOfMass = new Vector3(
                    data.metrics.center_of_mass[0],
                    data.metrics.center_of_mass[1],
                    data.metrics.center_of_mass[2]
                );
            }
        }

        // Initialize particle objects if needed
        if (particleObjects.Count == 0)
        {
            InitializeParticles(particleCount);
        }

        // Cache arrays for Phase 4 script access
        if (positions == null || positions.Length != particleCount)
            positions = new Vector3[particleCount];
        if (concentrations == null || concentrations.Length != particleCount)
            concentrations = new float[particleCount];

        // Update particle positions and colors
        for (int i = 0; i < particleCount && i < particleObjects.Count; i++)
        {
            if (data.positions != null && i < data.positions.Length)
            {
                // Convert Python coordinates to Unity (Y-up)
                Vector3 pos = new Vector3(
                    data.positions[i][0],
                    data.positions[i][1],
                    data.positions[i][2]
                );
                particleObjects[i].transform.position = pos;
                positions[i] = pos;
            }

            // Update color based on concentration
            if (data.concentrations != null && i < data.concentrations.Length)
            {
                float concentration = data.concentrations[i];
                concentrations[i] = concentration;
                Color particleColor = GetConcentrationColor(concentration);

                Renderer renderer = particleObjects[i].GetComponent<Renderer>();
                if (renderer != null)
                {
                    renderer.material.color = particleColor;
                }
            }

            // Store gradient data
            if (data.gradients != null && i < data.gradients.Length && data.gradients[i] != null && data.gradients[i].Length == 3)
            {
                if (gradientVectors == null || gradientVectors.Length != particleCount)
                    gradientVectors = new Vector3[particleCount];

                gradientVectors[i] = new Vector3(
                    data.gradients[i][0],
                    data.gradients[i][1],
                    data.gradients[i][2]
                );
            }
        }
    }

    void InitializeParticles(int count)
    {
        Debug.Log($"[SPH Client] Initializing {count} particle objects");

        // Check if prefab is assigned
        if (particlePrefab == null)
        {
            Debug.LogWarning("[SPH Client] No particle prefab assigned, creating default spheres");
            particlePrefab = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        }

        // Create particle objects
        for (int i = 0; i < count; i++)
        {
            GameObject particle = Instantiate(particlePrefab, Vector3.zero, Quaternion.identity);
            particle.transform.localScale = Vector3.one * particleScale;
            particle.transform.parent = transform;
            particle.name = $"Particle_{i}";

            // Enable GPU instancing if available
            if (useGPUInstancing)
            {
                Renderer renderer = particle.GetComponent<Renderer>();
                if (renderer != null)
                {
                    renderer.material.enableInstancing = true;
                }
            }

            particleObjects.Add(particle);
        }
    }

    Color GetConcentrationColor(float concentration)
    {
        // Gradient: Blue (0) → Yellow (0.5) → Red (1)
        if (concentration < 0.5f)
        {
            // Blue to Yellow
            float t = concentration * 2.0f;
            return Color.Lerp(cleanColor, mixedColor, t);
        }
        else
        {
            // Yellow to Red
            float t = (concentration - 0.5f) * 2.0f;
            return Color.Lerp(mixedColor, wasteColor, t);
        }
    }

    void OnGUI()
    {
        if (!showMetrics) return;

        GUIStyle style = new GUIStyle();
        style.fontSize = 16;
        style.normal.textColor = Color.white;
        style.padding = new RectOffset(10, 10, 10, 10);

        GUILayout.BeginArea(new Rect(10, 10, 400, 300));
        GUILayout.BeginVertical("box");

        GUILayout.Label($"<b>SPH Simulation - Phase 3</b>", style);
        GUILayout.Label($"Status: {statusMessage}", style);

        if (isConnected)
        {
            GUILayout.Label($"Time: {currentMetrics.time:F3}s", style);
            GUILayout.Label($"Step: {currentMetrics.step}", style);
            GUILayout.Label($"Particles: {currentMetrics.particleCount}", style);
            GUILayout.Label($"Mean Concentration: {currentMetrics.meanConcentration:F4}", style);
            GUILayout.Label($"Mixing Index: {currentMetrics.mixingIndex:F4}", style);
            GUILayout.Label($"Center of Mass: {currentMetrics.centerOfMass}", style);
        }

        GUILayout.EndVertical();
        GUILayout.EndArea();
    }

    async void OnApplicationQuit()
    {
        if (websocket != null && websocket.State == WebSocketState.Open)
        {
            await websocket.Close();
        }
    }

    private void OnDestroy()
    {
        // Clean up particle objects
        foreach (GameObject particle in particleObjects)
        {
            if (particle != null)
            {
                Destroy(particle);
            }
        }
        particleObjects.Clear();
    }
}
