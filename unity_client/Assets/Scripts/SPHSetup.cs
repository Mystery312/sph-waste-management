using UnityEngine;

/// <summary>
/// Scene setup script that initializes and wires all Phase 4 components.
/// Attach to a root GameObject in the scene.
/// </summary>
public class SPHSetup : MonoBehaviour
{
    [Header("Auto-Setup")]
    [Tooltip("Automatically find and wire components on Start")]
    public bool autoSetup = true;

    // Component references
    private SPHStreamingClient streamingClient;
    private CameraPresetManager cameraManager;
    private PresentationController presentationController;
    private PresentationUIManager uiManager;
    private GradientVisualizer gradientVisualizer;
    private VolumeIntegralCalculator volumeCalculator;

    void Start()
    {
        if (autoSetup)
            SetupComponents();
    }

    public void SetupComponents()
    {
        // Find or create SPHStreamingClient
        streamingClient = FindObjectOfType<SPHStreamingClient>();
        if (streamingClient == null)
        {
            Debug.LogError("[SPHSetup] SPHStreamingClient not found in scene!");
            return;
        }

        // Find or add CameraPresetManager
        cameraManager = FindObjectOfType<CameraPresetManager>();
        if (cameraManager == null)
        {
            cameraManager = gameObject.AddComponent<CameraPresetManager>();
            Debug.Log("[SPHSetup] Added CameraPresetManager");
        }

        // Find or add GradientVisualizer
        gradientVisualizer = FindObjectOfType<GradientVisualizer>();
        if (gradientVisualizer == null)
        {
            gradientVisualizer = gameObject.AddComponent<GradientVisualizer>();
            Debug.Log("[SPHSetup] Added GradientVisualizer");
        }
        gradientVisualizer.streamingClient = streamingClient;

        // Find or add VolumeIntegralCalculator
        volumeCalculator = FindObjectOfType<VolumeIntegralCalculator>();
        if (volumeCalculator == null)
        {
            volumeCalculator = gameObject.AddComponent<VolumeIntegralCalculator>();
            Debug.Log("[SPHSetup] Added VolumeIntegralCalculator");
        }
        volumeCalculator.streamingClient = streamingClient;

        // Find or add PresentationUIManager
        uiManager = FindObjectOfType<PresentationUIManager>();
        if (uiManager == null)
        {
            uiManager = gameObject.AddComponent<PresentationUIManager>();
            Debug.Log("[SPHSetup] Added PresentationUIManager");
        }
        uiManager.streamingClient = streamingClient;
        uiManager.cameraManager = cameraManager;
        uiManager.volumeCalculator = volumeCalculator;

        // Find or add PresentationController
        presentationController = FindObjectOfType<PresentationController>();
        if (presentationController == null)
        {
            presentationController = gameObject.AddComponent<PresentationController>();
            Debug.Log("[SPHSetup] Added PresentationController");
        }
        presentationController.streamingClient = streamingClient;
        presentationController.cameraManager = cameraManager;
        presentationController.uiManager = uiManager;
        presentationController.gradientVisualizer = gradientVisualizer;
        presentationController.volumeCalculator = volumeCalculator;

        // Wire UI manager's presentation controller reference
        uiManager.presentationController = presentationController;

        Debug.Log("[SPHSetup] All Phase 4 components initialized and wired!");
    }
}
