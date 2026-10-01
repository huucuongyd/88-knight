using UnityEngine;

/// <summary>Floating pixel-font damage number. Rendered into a tiny texture so it matches the pixel art.</summary>
[RequireComponent(typeof(SpriteRenderer))]
public class DamageNumber : MonoBehaviour
{
    // 3x5 glyphs, rows top to bottom.
    private static readonly string[] Glyphs =
    {
        "111101101101111", "010110010010111", "111001111100111", "111001111001111", "101101111001001",
        "111100111001111", "111100111101111", "111001010010010", "111101111101111", "111101111001111",
    };

    private const float Lifetime = 0.8f;
    private const float RiseDistance = 0.6f;

    private SpriteRenderer spriteRenderer;
    private Texture2D texture;
    private Color color;
    private Vector3 start;
    private float age;

    public static void Spawn(int value, Vector3 position, Color color, float pixelsPerUnit = 24f, int scale = 1)
    {
        var go = new GameObject($"Damage_{value}");
        go.transform.position = position;
        var sr = go.AddComponent<SpriteRenderer>();
        sr.sortingOrder = 10;
        var number = go.AddComponent<DamageNumber>();
        number.spriteRenderer = sr;
        number.color = color;
        number.start = position;
        number.texture = Render(Mathf.Max(0, value).ToString());
        sr.sprite = Sprite.Create(number.texture, new Rect(0, 0, number.texture.width, number.texture.height),
            new Vector2(0.5f, 0f), pixelsPerUnit / scale);
    }

    private static Texture2D Render(string digits)
    {
        int w = digits.Length * 4 + 1, h = 7;
        var tex = new Texture2D(w, h, TextureFormat.RGBA32, false) { filterMode = FilterMode.Point };
        var pixels = new Color32[w * h];
        var outline = new Color32(30, 20, 24, 255);
        var fill = new Color32(255, 255, 255, 255);
        for (int pass = 0; pass < 2; pass++)
        {
            for (int i = 0; i < digits.Length; i++)
            {
                string g = Glyphs[digits[i] - '0'];
                for (int gy = 0; gy < 5; gy++)
                for (int gx = 0; gx < 3; gx++)
                {
                    if (g[gy * 3 + gx] != '1') continue;
                    int x = 1 + i * 4 + gx, y = h - 2 - gy;
                    if (pass == 1)
                    {
                        pixels[y * w + x] = fill;
                        continue;
                    }
                    for (int oy = -1; oy <= 1; oy++)
                    for (int ox = -1; ox <= 1; ox++)
                        pixels[(y + oy) * w + x + ox] = outline;
                }
            }
        }
        tex.SetPixels32(pixels);
        tex.Apply();
        return tex;
    }

    private void Update()
    {
        age += Time.deltaTime;
        float t = age / Lifetime;
        if (t >= 1f)
        {
            Destroy(gameObject);
            return;
        }
        float rise = 1f - (1f - t) * (1f - t);
        transform.position = start + Vector3.up * (rise * RiseDistance);
        spriteRenderer.color = new Color(color.r, color.g, color.b, t < 0.6f ? 1f : 1f - (t - 0.6f) / 0.4f);
    }

    private void OnDestroy()
    {
        if (spriteRenderer != null && spriteRenderer.sprite != null) Destroy(spriteRenderer.sprite);
        if (texture != null) Destroy(texture);
    }
}
