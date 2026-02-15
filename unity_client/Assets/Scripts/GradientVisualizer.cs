using UnityEngine;

/// <summary>
/// Visualizes concentration gradient vector field (nabla C).
/// Displays a 5x5x5 grid of arrows showing gradient direction and magnitude.
/// Toggle with G key. Arrow color: green (low) -> yellow (mid) -> red (high).
/// </summary>
public class GradientVisualizer : MonoBehaviour
{
    [Header("References")]
    public SPHStreamingClient streamingClient;

    [Header("Grid Settings")]
    [Tooltip("Number of sample points per axis")]
    public int gridResolution = 5;

    [Header("Arrow Appearance")]
    [Tooltip("Base scale for arrow length")]
    public float arrowScale = 2.0f;

    [Tooltip("Minimum arrow length to display")]
    public float minMagnitude = 0.001f;

    [Tooltip("Maximum arrow length clamp")]
    public float maxArrowLength = 0.5f;

    [Header("Domain")]
    public Vector3 domainMin = Vector3.zero;
    public Vector3 domainMax = new Vector3(1f, 0.6f, 1f);

    // State
    private bool isVisible = false;
    private GameObject[] arrowObjects;
    private Vector3[] gridPositions;
    private int totalGridPoints;

    public bool IsVisible => isVisible;

    void Start()
    {
        totalGridPoints = gridResolution * gridResolution * gridResolution;
        CreateGrid();
        SetArrowsActive(false);
    }

    void Update()
    {
        if (!isVisible || streamingClient == null) return;

        UpdateArrows();
    }

    public void ToggleVisibility()
    {
        isVisible = !isVisible;
        SetArrowsActive(isVisible);
        Debug.Log($"[GradientViz] Arrows {(isVisible ? "shown" : "hidden")}");
    }

    private void CreateGrid()
    {
        gridPositions = new Vector3[totalGridPoints];
        arrowObjects = new GameObject[totalGridPoints];

        int idx = 0;
        Vector3 step = new Vector3(
            (domainMax.x - domainMin.x) / (gridResolution - 1),
            (domainMax.y - domainMin.y) / (gridResolution - 1),
            (domainMax.z - domainMin.z) / (gridResolution - 1)
        );

        for (int ix = 0; ix < gridResolution; ix++)
        {
            for (int iy = 0; iy < gridResolution; iy++)
            {
                for (int iz = 0; iz < gridResolution; iz++)
                {
                    Vector3 pos = domainMin + new Vector3(ix * step.x, iy * step.y, iz * step.z);
                    gridPositions[idx] = pos;

                    // Create arrow as a stretched cube (simple representation)
                    GameObject arrow = GameObject.CreatePrimitive(PrimitiveType.Cube);
                    arrow.name = $"GradientArrow_{idx}";
                    arrow.transform.parent = transform;
                    arrow.transform.position = pos;
                    arrow.transform.localScale = new Vector3(0.005f, 0.005f, 0.02f);

                    // Remove collider for performance
                    Collider col = arrow.GetComponent<Collider>();
                    if (col != null) Destroy(col);

                    // Set material
                    Renderer rend = arrow.GetComponent<Renderer>();
                    if (rend != null)
                    {
                        rend.material = new Material(Shader.Find("Standard"));
                        rend.material.enableInstancing = true;
                    }

                    arrowObjects[idx] = arrow;
                    idx++;
                }
            }
        }
    }

    private void UpdateArrows()
    {
        Vector3[] gradients = streamingClient.GradientVectors;
        Vector3[] positions = streamingClient.Positions;

        if (gradients == null || positions == null) return;

        int particleCount = streamingClient.ParticleCount;

        for (int i = 0; i < totalGridPoints; i++)
        {
            // Interpolate gradient at grid position from nearby particles
            Vector3 interpGradient = InterpolateGradient(gridPositions[i], positions, gradients, particleCount);

            float magnitude = interpGradient.magnitude;

            if (magnitude < minMagnitude)
            {
                arrowObjects[i].SetActive(false);
                continue;
            }

            arrowObjects[i].SetActive(true);

            // Clamp arrow length
            float arrowLength = Mathf.Min(magnitude * arrowScale, maxArrowLength);

            // Orient arrow along gradient direction
            Vector3 direction = interpGradient.normalized;
            arrowObjects[i].transform.rotation = Quaternion.LookRotation(direction);
            arrowObjects[i].transform.localScale = new Vector3(0.005f, 0.005f, arrowLength);

            // Color by magnitude: green -> yellow -> red
            Color arrowColor = GetMagnitudeColor(magnitude);
            Renderer rend = arrowObjects[i].GetComponent<Renderer>();
            if (rend != null)
                rend.material.color = arrowColor;
        }
    }

    private Vector3 InterpolateGradient(Vector3 samplePos, Vector3[] positions, Vector3[] gradients, int count)
    {
        // Simple inverse-distance weighted interpolation from nearby particles
        float influenceRadius = 0.15f;
        float influenceRadiusSq = influenceRadius * influenceRadius;
        Vector3 weightedSum = Vector3.zero;
        float totalWeight = 0f;

        for (int i = 0; i < count && i < positions.Length && i < gradients.Length; i++)
        {
            float distSq = (positions[i] - samplePos).sqrMagnitude;
            if (distSq < influenceRadiusSq && distSq > 0.0001f)
            {
                float weight = 1.0f / distSq;
                weightedSum += gradients[i] * weight;
                totalWeight += weight;
            }
        }

        if (totalWeight > 0f)
            return weightedSum / totalWeight;

        return Vector3.zero;
    }

    private Color GetMagnitudeColor(float magnitude)
    {
        // Normalize magnitude to [0, 1] range
        float maxExpected = 10.0f;
        float t = Mathf.Clamp01(magnitude / maxExpected);

        if (t < 0.5f)
        {
            // Green to Yellow
            float s = t * 2f;
            return new Color(
                Mathf.Lerp(0f, 1f, s),
                1f,
                0f
            );
        }
        else
        {
            // Yellow to Red
            float s = (t - 0.5f) * 2f;
            return new Color(
                1f,
                Mathf.Lerp(1f, 0f, s),
                0f
            );
        }
    }

    private void SetArrowsActive(bool active)
    {
        if (arrowObjects == null) return;
        for (int i = 0; i < arrowObjects.Length; i++)
        {
            if (arrowObjects[i] != null)
                arrowObjects[i].SetActive(active);
        }
    }

    void OnDestroy()
    {
        if (arrowObjects != null)
        {
            for (int i = 0; i < arrowObjects.Length; i++)
            {
                if (arrowObjects[i] != null)
                    Destroy(arrowObjects[i]);
            }
        }
    }
}
