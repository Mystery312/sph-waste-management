using UnityEngine;

/// <summary>
/// Animated Riemann sum volume integral visualizer.
/// Computes triple integral of C dV over preset regions.
/// Keys 1-3 select regions: top, bottom, center.
/// </summary>
public class VolumeIntegralCalculator : MonoBehaviour
{
    [Header("References")]
    public SPHStreamingClient streamingClient;

    [Header("Visualization")]
    [Tooltip("Material for translucent bounding boxes")]
    public Color regionColor = new Color(0.2f, 0.5f, 1f, 0.15f);

    [Tooltip("Color for highlighted particles inside region")]
    public Color highlightColor = new Color(1f, 1f, 0f, 0.8f);

    // Region definitions
    private struct IntegralRegion
    {
        public string name;
        public Vector3 min;
        public Vector3 max;

        public IntegralRegion(string name, Vector3 min, Vector3 max)
        {
            this.name = name;
            this.min = min;
            this.max = max;
        }
    }

    private IntegralRegion[] regions = new IntegralRegion[]
    {
        new IntegralRegion("Top Region",    new Vector3(0.1f, 0.35f, 0.1f), new Vector3(0.9f, 0.55f, 0.9f)),
        new IntegralRegion("Bottom Region", new Vector3(0.1f, 0.0f, 0.1f),  new Vector3(0.9f, 0.2f, 0.9f)),
        new IntegralRegion("Center Region", new Vector3(0.25f, 0.1f, 0.25f), new Vector3(0.75f, 0.45f, 0.75f))
    };

    private int currentRegion = -1;
    private bool isActive = false;
    private float integralValue = 0f;
    private int particlesInRegion = 0;
    private GameObject boundingBox;
    private Material boxMaterial;

    // Public accessors
    public bool IsActive => isActive;
    public string CurrentRegionName => currentRegion >= 0 ? regions[currentRegion].name : "None";
    public float CurrentIntegralValue => integralValue;
    public int ParticlesInRegion => particlesInRegion;

    void Update()
    {
        if (!isActive || streamingClient == null || currentRegion < 0) return;

        ComputeIntegral();
    }

    public void SelectRegion(int regionIndex)
    {
        if (regionIndex < 0 || regionIndex >= regions.Length) return;

        // Toggle off if same region selected again
        if (regionIndex == currentRegion && isActive)
        {
            Deactivate();
            return;
        }

        currentRegion = regionIndex;
        isActive = true;
        UpdateBoundingBox();
        Debug.Log($"[VolumeIntegral] Region: {regions[currentRegion].name}");
    }

    private void ComputeIntegral()
    {
        Vector3[] positions = streamingClient.Positions;
        float[] concentrations = streamingClient.Concentrations;

        if (positions == null || concentrations == null) return;

        IntegralRegion region = regions[currentRegion];
        float sum = 0f;
        int count = 0;
        int particleCount = streamingClient.ParticleCount;

        // Approximate particle volume (domain volume / particle count)
        float domainVolume = 1.0f * 0.6f * 1.0f;
        float particleVolume = domainVolume / Mathf.Max(particleCount, 1);

        for (int i = 0; i < particleCount && i < positions.Length && i < concentrations.Length; i++)
        {
            Vector3 pos = positions[i];
            if (pos.x >= region.min.x && pos.x <= region.max.x &&
                pos.y >= region.min.y && pos.y <= region.max.y &&
                pos.z >= region.min.z && pos.z <= region.max.z)
            {
                sum += concentrations[i] * particleVolume;
                count++;
            }
        }

        integralValue = sum;
        particlesInRegion = count;
    }

    private void UpdateBoundingBox()
    {
        if (boundingBox != null)
            Destroy(boundingBox);

        if (currentRegion < 0) return;

        IntegralRegion region = regions[currentRegion];
        Vector3 center = (region.min + region.max) * 0.5f;
        Vector3 size = region.max - region.min;

        boundingBox = GameObject.CreatePrimitive(PrimitiveType.Cube);
        boundingBox.name = "IntegralRegionBox";
        boundingBox.transform.parent = transform;
        boundingBox.transform.position = center;
        boundingBox.transform.localScale = size;

        // Remove collider
        Collider col = boundingBox.GetComponent<Collider>();
        if (col != null) Destroy(col);

        // Translucent material
        Renderer rend = boundingBox.GetComponent<Renderer>();
        if (rend != null)
        {
            boxMaterial = new Material(Shader.Find("Standard"));
            boxMaterial.SetFloat("_Mode", 3); // Transparent
            boxMaterial.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
            boxMaterial.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
            boxMaterial.SetInt("_ZWrite", 0);
            boxMaterial.DisableKeyword("_ALPHATEST_ON");
            boxMaterial.EnableKeyword("_ALPHABLEND_ON");
            boxMaterial.DisableKeyword("_ALPHAPREMULTIPLY_ON");
            boxMaterial.renderQueue = 3000;
            boxMaterial.color = regionColor;
            rend.material = boxMaterial;
        }
    }

    private void Deactivate()
    {
        isActive = false;
        currentRegion = -1;
        integralValue = 0f;
        particlesInRegion = 0;

        if (boundingBox != null)
        {
            Destroy(boundingBox);
            boundingBox = null;
        }
    }

    void OnDestroy()
    {
        if (boundingBox != null)
            Destroy(boundingBox);
    }
}
