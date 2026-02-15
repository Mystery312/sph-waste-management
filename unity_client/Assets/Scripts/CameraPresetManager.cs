using UnityEngine;

/// <summary>
/// Camera preset manager for classroom presentation.
/// Cycles through 4 camera presets with TAB key.
/// Reset to default with R key.
/// </summary>
public class CameraPresetManager : MonoBehaviour
{
    [Header("Camera Reference")]
    [Tooltip("Main camera to control. Auto-finds if null.")]
    public Camera targetCamera;

    [Header("Orbit Settings")]
    [Tooltip("Point the camera orbits around")]
    public Vector3 orbitCenter = new Vector3(0.5f, 0.3f, 0.5f);

    [Tooltip("Transition speed between presets")]
    public float transitionSpeed = 3.0f;

    // Camera preset definitions
    private struct CameraPreset
    {
        public string name;
        public float elevation;  // degrees
        public float azimuth;    // degrees
        public float distance;   // meters

        public CameraPreset(string name, float elevation, float azimuth, float distance)
        {
            this.name = name;
            this.elevation = elevation;
            this.azimuth = azimuth;
            this.distance = distance;
        }
    }

    private CameraPreset[] presets = new CameraPreset[]
    {
        new CameraPreset("Overview",   45f, 45f,  15f),
        new CameraPreset("Close-Up",   30f, 0f,   5f),
        new CameraPreset("Side View",  0f,  90f,  10f),
        new CameraPreset("Top-Down",   89f, 0f,   12f)
    };

    private int currentPreset = 0;
    private Vector3 targetPosition;
    private Quaternion targetRotation;
    private bool isTransitioning = false;

    // Public accessor for UI display
    public string CurrentPresetName => presets[currentPreset].name;
    public int CurrentPresetIndex => currentPreset;
    public int PresetCount => presets.Length;

    void Start()
    {
        if (targetCamera == null)
            targetCamera = Camera.main;

        if (targetCamera == null)
        {
            Debug.LogError("[CameraPresets] No camera found!");
            return;
        }

        ApplyPresetImmediate(0);
    }

    void Update()
    {
        if (targetCamera == null) return;

        // TAB to cycle presets
        if (Input.GetKeyDown(KeyCode.Tab))
        {
            CyclePreset();
        }

        // R to reset to overview
        if (Input.GetKeyDown(KeyCode.R))
        {
            SetPreset(0);
        }

        // Smooth transition
        if (isTransitioning)
        {
            targetCamera.transform.position = Vector3.Lerp(
                targetCamera.transform.position, targetPosition, Time.deltaTime * transitionSpeed);
            targetCamera.transform.rotation = Quaternion.Slerp(
                targetCamera.transform.rotation, targetRotation, Time.deltaTime * transitionSpeed);

            if (Vector3.Distance(targetCamera.transform.position, targetPosition) < 0.01f)
            {
                targetCamera.transform.position = targetPosition;
                targetCamera.transform.rotation = targetRotation;
                isTransitioning = false;
            }
        }
    }

    public void CyclePreset()
    {
        currentPreset = (currentPreset + 1) % presets.Length;
        ApplyPresetSmooth(currentPreset);
        Debug.Log($"[CameraPresets] Switched to: {presets[currentPreset].name}");
    }

    public void SetPreset(int index)
    {
        if (index < 0 || index >= presets.Length) return;
        currentPreset = index;
        ApplyPresetSmooth(currentPreset);
    }

    private void ApplyPresetSmooth(int index)
    {
        ComputePresetTransform(presets[index], out targetPosition, out targetRotation);
        isTransitioning = true;
    }

    private void ApplyPresetImmediate(int index)
    {
        ComputePresetTransform(presets[index], out targetPosition, out targetRotation);
        targetCamera.transform.position = targetPosition;
        targetCamera.transform.rotation = targetRotation;
        isTransitioning = false;
    }

    private void ComputePresetTransform(CameraPreset preset, out Vector3 pos, out Quaternion rot)
    {
        float elevRad = preset.elevation * Mathf.Deg2Rad;
        float azimRad = preset.azimuth * Mathf.Deg2Rad;

        float x = preset.distance * Mathf.Cos(elevRad) * Mathf.Sin(azimRad);
        float y = preset.distance * Mathf.Sin(elevRad);
        float z = preset.distance * Mathf.Cos(elevRad) * Mathf.Cos(azimRad);

        pos = orbitCenter + new Vector3(x, y, z);
        rot = Quaternion.LookRotation(orbitCenter - pos, Vector3.up);
    }
}
