using UnityEngine;

/// <summary>Scarecrow that never dies: shows damage numbers, wobbles and flashes when hit.</summary>
public class TrainingDummy : MonoBehaviour, IDamageable
{
    [SerializeField] private Transform visual;
    [SerializeField] private float numberHeight = 1.8f;
    [SerializeField] private Color normalColor = Color.white;
    [SerializeField] private Color empoweredColor = new Color(1f, 0.75f, 0.2f);
    [SerializeField] private float wobbleAngle = 12f;
    [SerializeField] private float wobbleTime = 0.35f;

    private SpriteRenderer spriteRenderer;
    private float wobbleTimer;
    private float wobbleSign = 1f;

    public int TotalDamage { get; private set; }
    public int HitCount { get; private set; }

    private void Awake()
    {
        if (visual == null) visual = transform;
        spriteRenderer = visual.GetComponent<SpriteRenderer>();
    }

    public void TakeHit(int damage, Vector2 sourcePosition, bool empowered)
    {
        TotalDamage += damage;
        HitCount++;

        var jitter = new Vector3(Random.Range(-0.25f, 0.25f), Random.Range(0f, 0.2f), 0f);
        DamageNumber.Spawn(damage, transform.position + Vector3.up * numberHeight + jitter,
            empowered ? empoweredColor : normalColor, scale: empowered ? 2 : 1);

        // Lean away from the attacker.
        wobbleSign = sourcePosition.x <= transform.position.x ? -1f : 1f;
        wobbleTimer = wobbleTime;
    }

    private void Update()
    {
        if (wobbleTimer <= 0f) return;
        wobbleTimer = Mathf.Max(0f, wobbleTimer - Time.deltaTime);
        float t = 1f - wobbleTimer / wobbleTime;
        float angle = wobbleSign * wobbleAngle * Mathf.Sin(t * Mathf.PI * 3f) * (1f - t);
        visual.localRotation = Quaternion.Euler(0f, 0f, angle);
        if (spriteRenderer != null)
            spriteRenderer.color = Color.Lerp(new Color(1f, 0.55f, 0.55f), Color.white, t);
    }
}
