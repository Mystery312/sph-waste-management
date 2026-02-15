using UnityEngine;

/// <summary>
/// Adaptive UI manager for classroom presentations.
/// Scales fonts and layout based on screen resolution.
/// Base resolution: 1080p.
/// </summary>
public class PresentationUIManager : MonoBehaviour
{
    [Header("References")]
    public SPHStreamingClient streamingClient;
    public CameraPresetManager cameraManager;
    public PresentationController presentationController;
    public GradientVisualizer gradientVisualizer;
    public VolumeIntegralCalculator volumeCalculator;

    [Header("UI Settings")]
    public bool showControls = true;

    // Font sizes at 1080p baseline
    private const float BASE_RESOLUTION = 1080f;
    private const int TITLE_SIZE_BASE = 42;
    private const int HEADING_SIZE_BASE = 32;
    private const int BODY_SIZE_BASE = 28;
    private const int SMALL_SIZE_BASE = 22;

    private float scaleFactor = 1f;
    private bool visible = true;

    // Computed font sizes
    private int titleSize;
    private int headingSize;
    private int bodySize;
    private int smallSize;

    // Styles
    private GUIStyle titleStyle;
    private GUIStyle headingStyle;
    private GUIStyle bodyStyle;
    private GUIStyle smallStyle;
    private GUIStyle boxStyle;
    private bool stylesInitialized = false;

    void Update()
    {
        float newScale = Screen.height / BASE_RESOLUTION;
        if (Mathf.Abs(newScale - scaleFactor) > 0.01f)
        {
            scaleFactor = newScale;
            UpdateFontSizes();
            stylesInitialized = false;
        }
    }

    private void UpdateFontSizes()
    {
        titleSize = Mathf.RoundToInt(TITLE_SIZE_BASE * scaleFactor);
        headingSize = Mathf.RoundToInt(HEADING_SIZE_BASE * scaleFactor);
        bodySize = Mathf.RoundToInt(BODY_SIZE_BASE * scaleFactor);
        smallSize = Mathf.RoundToInt(SMALL_SIZE_BASE * scaleFactor);
    }

    private void InitStyles()
    {
        UpdateFontSizes();

        titleStyle = new GUIStyle(GUI.skin.label);
        titleStyle.fontSize = titleSize;
        titleStyle.fontStyle = FontStyle.Bold;
        titleStyle.normal.textColor = Color.white;
        titleStyle.richText = true;

        headingStyle = new GUIStyle(GUI.skin.label);
        headingStyle.fontSize = headingSize;
        headingStyle.fontStyle = FontStyle.Bold;
        headingStyle.normal.textColor = new Color(0.9f, 0.9f, 1f);
        headingStyle.richText = true;

        bodyStyle = new GUIStyle(GUI.skin.label);
        bodyStyle.fontSize = bodySize;
        bodyStyle.normal.textColor = Color.white;
        bodyStyle.richText = true;

        smallStyle = new GUIStyle(GUI.skin.label);
        smallStyle.fontSize = smallSize;
        smallStyle.normal.textColor = new Color(0.7f, 0.7f, 0.7f);
        smallStyle.richText = true;

        boxStyle = new GUIStyle(GUI.skin.box);
        boxStyle.normal.background = MakeTexture(2, 2, new Color(0, 0, 0, 0.7f));

        stylesInitialized = true;
    }

    public void SetVisible(bool isVisible)
    {
        visible = isVisible;
    }

    void OnGUI()
    {
        if (!visible) return;
        if (!stylesInitialized) InitStyles();

        float panelWidth = Screen.width * 0.25f;
        float panelHeight = Screen.height * 0.5f;
        float margin = Screen.width * 0.01f;

        // Main info panel (top-left)
        GUILayout.BeginArea(new Rect(margin, margin, panelWidth, panelHeight), boxStyle);
        GUILayout.Space(10);

        GUILayout.Label("SPH Waste Simulation", titleStyle);
        GUILayout.Label("Calculus 3 Demo", headingStyle);
        GUILayout.Space(10);

        if (cameraManager != null)
            GUILayout.Label($"Camera: {cameraManager.CurrentPresetName}", bodyStyle);

        if (presentationController != null)
            GUILayout.Label(presentationController.IsPaused ? "STATUS: PAUSED" : "STATUS: Running", bodyStyle);

        GUILayout.Space(10);

        // Controls help
        if (showControls)
        {
            GUILayout.Label("Controls", headingStyle);
            GUILayout.Label("TAB  - Cycle camera", smallStyle);
            GUILayout.Label("SPACE - Pause/Resume", smallStyle);
            GUILayout.Label("G    - Toggle gradients", smallStyle);
            GUILayout.Label("1-3  - Volume regions", smallStyle);
            GUILayout.Label("H    - Toggle UI", smallStyle);
            GUILayout.Label("R    - Reset camera", smallStyle);
        }

        GUILayout.EndArea();

        // Volume integral panel (bottom-left)
        if (volumeCalculator != null && volumeCalculator.IsActive)
        {
            float bottomPanelY = Screen.height - panelHeight * 0.4f - margin;
            GUILayout.BeginArea(new Rect(margin, bottomPanelY, panelWidth, panelHeight * 0.4f), boxStyle);
            GUILayout.Space(5);
            GUILayout.Label("Volume Integral", headingStyle);
            GUILayout.Label($"Region: {volumeCalculator.CurrentRegionName}", bodyStyle);
            GUILayout.Label($"\u222D C dV = {volumeCalculator.CurrentIntegralValue:F4}", bodyStyle);
            GUILayout.Label($"Particles in region: {volumeCalculator.ParticlesInRegion}", smallStyle);
            GUILayout.EndArea();
        }
    }

    private Texture2D MakeTexture(int width, int height, Color color)
    {
        Color[] pixels = new Color[width * height];
        for (int i = 0; i < pixels.Length; i++)
            pixels[i] = color;

        Texture2D texture = new Texture2D(width, height);
        texture.SetPixels(pixels);
        texture.Apply();
        return texture;
    }
}
