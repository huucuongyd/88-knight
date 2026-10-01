using UnityEngine;

/// <summary>Short-lived sprite that fades out (and optionally grows) then destroys itself.</summary>
[RequireComponent(typeof(SpriteRenderer))]
public class SkillEffect : MonoBehaviour
{
    private SpriteRenderer spriteRenderer;
    private float lifetime;
    private float age;
    private float startScale;
    private Color color;

    public static SkillEffect Spawn(Sprite sprite, Color color, Vector2 position, float angle, float lifetime, float startScale = 1f)
    {
        var go = new GameObject($"FX_{sprite.name}");
        go.transform.SetPositionAndRotation(position, Quaternion.Euler(0f, 0f, angle));
        var sr = go.AddComponent<SpriteRenderer>();
        sr.sprite = sprite;
        sr.color = color;
        sr.sortingOrder = 3;
        var fx = go.AddComponent<SkillEffect>();
        fx.spriteRenderer = sr;
        fx.color = color;
        fx.lifetime = Mathf.Max(lifetime, 0.01f);
        fx.startScale = startScale;
        go.transform.localScale = Vector3.one * startScale;
        return fx;
    }

    private void Update()
    {
        age += Time.deltaTime;
        float t = age / lifetime;
        if (t >= 1f)
        {
            Destroy(gameObject);
            return;
        }
        transform.localScale = Vector3.one * Mathf.Lerp(startScale, 1f, Mathf.Sqrt(t));
        spriteRenderer.color = new Color(color.r, color.g, color.b, color.a * (1f - t * t));
    }
}
