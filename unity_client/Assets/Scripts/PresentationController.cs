using UnityEngine;

/// <summary>
/// Presentation controller for classroom demos.
/// SPACE = pause/resume, H = toggle UI, R = reset camera.
/// </summary>
public class PresentationController : MonoBehaviour
{
    [Header("References")]
    public SPHStreamingClient streamingClient;
    public CameraPresetManager cameraManager;
    public PresentationUIManager uiManager;
    public GradientVisualizer gradientVisualizer;
    public VolumeIntegralCalculator volumeCalculator;

    // State
    private bool isPaused = false;
    private bool uiVisible = true;

    public bool IsPaused => isPaused;
    public bool UIVisible => uiVisible;

    void Update()
    {
        // SPACE - Pause / Resume
        if (Input.GetKeyDown(KeyCode.Space))
        {
            TogglePause();
        }

        // H - Toggle UI
        if (Input.GetKeyDown(KeyCode.H))
        {
            ToggleUI();
        }

        // G - Toggle gradient arrows
        if (Input.GetKeyDown(KeyCode.G))
        {
            ToggleGradients();
        }

        // 1, 2, 3 - Volume integral preset regions
        if (Input.GetKeyDown(KeyCode.Alpha1))
            SelectVolumeRegion(0);
        if (Input.GetKeyDown(KeyCode.Alpha2))
            SelectVolumeRegion(1);
        if (Input.GetKeyDown(KeyCode.Alpha3))
            SelectVolumeRegion(2);
    }

    public void TogglePause()
    {
        isPaused = !isPaused;
        Time.timeScale = isPaused ? 0f : 1f;
        Debug.Log($"[Presentation] {(isPaused ? "PAUSED" : "RESUMED")}");
    }

    public void ToggleUI()
    {
        uiVisible = !uiVisible;

        if (streamingClient != null)
            streamingClient.showMetrics = uiVisible;

        if (uiManager != null)
            uiManager.SetVisible(uiVisible);

        Debug.Log($"[Presentation] UI {(uiVisible ? "shown" : "hidden")}");
    }

    public void ToggleGradients()
    {
        if (gradientVisualizer != null)
        {
            gradientVisualizer.ToggleVisibility();
            Debug.Log($"[Presentation] Gradients toggled");
        }
    }

    public void SelectVolumeRegion(int regionIndex)
    {
        if (volumeCalculator != null)
        {
            volumeCalculator.SelectRegion(regionIndex);
            Debug.Log($"[Presentation] Volume region {regionIndex + 1} selected");
        }
    }
}
