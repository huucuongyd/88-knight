using System.Collections.Generic;
using UnityEngine;
using UnityEngine.InputSystem;

/// <summary>
/// Space: basic attack. Q: thrust toward the facing direction. W: 60° cone sweep.
/// E: burst + aura ring that doubles damage while it lasts.
/// Sizes are in sprite pixels (converted with pixelsPerUnit) so they match the pixel art scale.
/// </summary>
[RequireComponent(typeof(PlayerController))]
public class PlayerSkills : MonoBehaviour
{
    [SerializeField] private float pixelsPerUnit = 24f;
    [SerializeField] private Color effectColor = new Color(0.78f, 0.95f, 1f, 0.9f);

    [Header("Space - Basic attack")]
    [SerializeField] private float basicRadius = 28f;
    [SerializeField] private float basicAngle = 120f;
    [SerializeField] private int basicDamage = 1;

    [Header("Q - Thrust")]
    [SerializeField] private float thrustLength = 100f;
    [SerializeField] private float thrustWidth = 8f;
    [SerializeField] private float thrustCooldown = 1.5f;
    [SerializeField] private int thrustDamage = 3;

    [Header("W - Sweep")]
    [SerializeField] private float sweepRadius = 40f;
    [SerializeField] private float sweepAngle = 60f;
    [SerializeField] private float sweepCooldown = 1f;
    [SerializeField] private int sweepDamage = 2;

    [Header("E - Aura")]
    [SerializeField] private float auraRadius = 40f;
    [SerializeField] private float auraDuration = 20f;
    [SerializeField] private float auraCooldown = 20f;
    [SerializeField] private float auraDamageMultiplier = 2f;
    [SerializeField] private int auraBurstDamage = 2;
    [SerializeField] private Color auraColor = new Color(1f, 0.78f, 0.3f, 0.8f);

    private PlayerController controller;
    private readonly HashSet<Collider2D> ownColliders = new HashSet<Collider2D>();
    private Sprite thrustSprite, sweepSprite, auraBurstSprite;
    private SpriteRenderer auraRenderer;
    private float thrustReady, sweepReady, auraReady, auraEnd;

    public float ThrustCooldownLeft => Mathf.Max(0f, thrustReady - Time.time);
    public float SweepCooldownLeft => Mathf.Max(0f, sweepReady - Time.time);
    public float AuraCooldownLeft => Mathf.Max(0f, auraReady - Time.time);
    public float AuraTimeLeft => Mathf.Max(0f, auraEnd - Time.time);
    public bool AuraActive => Time.time < auraEnd;
    public float DamageMultiplier => AuraActive ? auraDamageMultiplier : 1f;

    private Vector2 Origin => transform.position;
    private float ToUnits(float px) => px / pixelsPerUnit;

    private void Awake()
    {
        controller = GetComponent<PlayerController>();
        foreach (var c in GetComponentsInChildren<Collider2D>()) ownColliders.Add(c);
        thrustSprite = SkillSprites.Thrust(Mathf.RoundToInt(thrustLength), Mathf.RoundToInt(thrustWidth), pixelsPerUnit);
        sweepSprite = SkillSprites.Cone(Mathf.RoundToInt(sweepRadius), sweepAngle, pixelsPerUnit);
        int auraPx = Mathf.RoundToInt(auraRadius);
        auraBurstSprite = SkillSprites.Ring(auraPx, pixelsPerUnit, 0.35f);

        var aura = new GameObject("DamageAura");
        aura.transform.SetParent(transform, false);
        auraRenderer = aura.AddComponent<SpriteRenderer>();
        auraRenderer.sprite = SkillSprites.Ring(auraPx, pixelsPerUnit, 0.08f);
        auraRenderer.sortingOrder = -1;
        auraRenderer.enabled = false;
    }

    private void Update()
    {
        var keyboard = Keyboard.current;
        var mouse = Mouse.current;
        var gamepad = Gamepad.current;
        bool basic = (keyboard != null && keyboard.spaceKey.wasPressedThisFrame)
            || (mouse != null && mouse.leftButton.wasPressedThisFrame)
            || (gamepad != null && gamepad.buttonWest.wasPressedThisFrame);
        bool q = (keyboard != null && keyboard.qKey.wasPressedThisFrame) || (gamepad != null && gamepad.leftShoulder.wasPressedThisFrame);
        bool w = (keyboard != null && keyboard.wKey.wasPressedThisFrame) || (gamepad != null && gamepad.rightShoulder.wasPressedThisFrame);
        bool e = (keyboard != null && keyboard.eKey.wasPressedThisFrame) || (gamepad != null && gamepad.buttonEast.wasPressedThisFrame);

        if (q && Time.time >= thrustReady && controller.TryBeginAttack())
        {
            thrustReady = Time.time + thrustCooldown;
            CastThrust();
        }
        else if (w && Time.time >= sweepReady && controller.TryBeginAttack())
        {
            sweepReady = Time.time + sweepCooldown;
            CastSweep();
        }
        else if (e && Time.time >= auraReady && controller.TryBeginAttack())
        {
            auraReady = Time.time + auraCooldown;
            CastAura();
        }
        else if (basic && controller.TryBeginAttack())
        {
            CastBasic();
        }

        UpdateAura();
    }

    private void CastBasic()
    {
        Vector2 dir = controller.FacingDirection;
        var hits = Physics2D.OverlapCircleAll(Origin, ToUnits(basicRadius));
        Damage(hits, basicDamage, c => InCone(c, dir, basicAngle));
    }

    private void CastThrust()
    {
        Vector2 dir = controller.FacingDirection;
        float angle = Mathf.Atan2(dir.y, dir.x) * Mathf.Rad2Deg;
        float length = ToUnits(thrustLength);
        var hits = Physics2D.OverlapBoxAll(Origin + dir * (length * 0.5f), new Vector2(length, ToUnits(thrustWidth)), angle);
        Damage(hits, thrustDamage, _ => true);
        SkillEffect.Spawn(thrustSprite, CurrentEffectColor, Origin, angle, 0.25f);
    }

    private void CastSweep()
    {
        Vector2 dir = controller.FacingDirection;
        float angle = Mathf.Atan2(dir.y, dir.x) * Mathf.Rad2Deg;
        var hits = Physics2D.OverlapCircleAll(Origin, ToUnits(sweepRadius));
        Damage(hits, sweepDamage, c => InCone(c, dir, sweepAngle));
        SkillEffect.Spawn(sweepSprite, CurrentEffectColor, Origin, angle, 0.25f, 0.7f);
    }

    private void CastAura()
    {
        var hits = Physics2D.OverlapCircleAll(Origin, ToUnits(auraRadius));
        Damage(hits, auraBurstDamage, _ => true);
        SkillEffect.Spawn(auraBurstSprite, auraColor, Origin, 0f, 0.35f, 0.3f);
        auraEnd = Time.time + auraDuration;
    }

    private void UpdateAura()
    {
        float left = AuraTimeLeft;
        auraRenderer.enabled = left > 0f;
        if (left <= 0f) return;
        // Blink during the last 3 seconds so the player knows the buff is ending.
        float pulse = left > 3f ? 0.75f + 0.25f * Mathf.Sin(Time.time * 4f) : (Mathf.Repeat(Time.time * 6f, 1f) < 0.5f ? 1f : 0.3f);
        auraRenderer.color = new Color(auraColor.r, auraColor.g, auraColor.b, auraColor.a * pulse);
    }

    private Color CurrentEffectColor => AuraActive ? auraColor : effectColor;

    private bool InCone(Collider2D c, Vector2 dir, float angle)
    {
        Vector2 to = c.ClosestPoint(Origin) - Origin;
        return to.sqrMagnitude < 0.0001f || Vector2.Angle(dir, to) <= angle * 0.5f;
    }

    private void Damage(Collider2D[] hits, int baseDamage, System.Predicate<Collider2D> filter)
    {
        bool empowered = AuraActive;
        int damage = Mathf.RoundToInt(baseDamage * DamageMultiplier);
        var done = new HashSet<IDamageable>();
        foreach (var c in hits)
        {
            if (ownColliders.Contains(c) || !filter(c)) continue;
            var target = c.GetComponentInParent<IDamageable>();
            if (target != null && done.Add(target))
                target.TakeHit(damage, Origin, empowered);
        }
    }

    private void OnDrawGizmosSelected()
    {
        var pc = GetComponent<PlayerController>();
        Vector2 dir = pc != null && Application.isPlaying ? pc.FacingDirection : Vector2.down;
        Vector3 o = transform.position;

        Gizmos.color = Color.cyan;
        Gizmos.DrawLine(o, o + (Vector3)(dir * ToUnits(thrustLength)));

        Gizmos.color = Color.yellow;
        float r = ToUnits(sweepRadius);
        Vector3 prev = o;
        for (int i = 0; i <= 12; i++)
        {
            float a = -sweepAngle * 0.5f + sweepAngle * i / 12f;
            Vector3 p = o + Quaternion.Euler(0f, 0f, a) * (Vector3)(dir * r);
            Gizmos.DrawLine(prev, p);
            prev = p;
        }
        Gizmos.DrawLine(prev, o);

        Gizmos.color = Color.magenta;
        Gizmos.DrawWireSphere(o, ToUnits(auraRadius));
        Gizmos.color = Color.white;
        Gizmos.DrawWireSphere(o, ToUnits(basicRadius));
    }
}

/// <summary>Builds pixel-art effect sprites at runtime.</summary>
public static class SkillSprites
{
    public static Sprite Thrust(int length, int width, float ppu)
    {
        int h = width | 1;
        int mid = h / 2;
        int tip = Mathf.Min(12, length / 3);
        var tex = NewTexture(length, h);
        for (int x = 0; x < length; x++)
        {
            float half = x < length - tip ? mid : mid * (length - x) / (float)tip;
            float fade = 0.35f + 0.65f * x / length;
            for (int y = 0; y < h; y++)
            {
                float d = Mathf.Abs(y - mid);
                if (d > half + 0.01f) continue;
                float a = d <= 0.5f ? 1f : 1f - d / (half + 1f);
                tex.SetPixel(x, y, new Color(1f, 1f, 1f, a * fade));
            }
        }
        return Finish(tex, "Thrust", new Vector2(0f, 0.5f), ppu);
    }

    public static Sprite Cone(int radius, float angle, float ppu)
    {
        float half = angle * 0.5f;
        int cy = Mathf.CeilToInt(radius * Mathf.Sin(half * Mathf.Deg2Rad));
        int w = radius + 1, h = cy * 2 + 1;
        var tex = NewTexture(w, h);
        for (int x = 0; x < w; x++)
        for (int y = 0; y < h; y++)
        {
            float dx = x, dy = y - cy;
            float d = Mathf.Sqrt(dx * dx + dy * dy);
            float a = Mathf.Abs(Mathf.Atan2(dy, dx) * Mathf.Rad2Deg);
            if (d > radius || a > half) continue;
            bool edge = d > radius - 2f || a > half - 3f;
            float alpha = edge ? 1f : 0.15f + 0.6f * (d / radius) * (d / radius);
            tex.SetPixel(x, y, new Color(1f, 1f, 1f, alpha));
        }
        return Finish(tex, "Sweep", new Vector2(0.5f / w, (cy + 0.5f) / h), ppu);
    }

    public static Sprite Ring(int radius, float ppu, float fillAlpha = 0.35f)
    {
        int size = radius * 2 + 1;
        var tex = NewTexture(size, size);
        for (int x = 0; x < size; x++)
        for (int y = 0; y < size; y++)
        {
            float d = Vector2.Distance(new Vector2(x, y), new Vector2(radius, radius));
            if (d > radius + 0.3f) continue;
            float alpha = d >= radius - 1.5f ? 1f : fillAlpha * (0.3f + 0.7f * d / radius);
            tex.SetPixel(x, y, new Color(1f, 1f, 1f, alpha));
        }
        return Finish(tex, "Burst", new Vector2(0.5f, 0.5f), ppu);
    }

    private static Texture2D NewTexture(int w, int h)
    {
        var tex = new Texture2D(w, h, TextureFormat.RGBA32, false) { filterMode = FilterMode.Point, wrapMode = TextureWrapMode.Clamp };
        tex.SetPixels32(new Color32[w * h]);
        return tex;
    }

    private static Sprite Finish(Texture2D tex, string name, Vector2 pivot, float ppu)
    {
        tex.Apply();
        var sprite = Sprite.Create(tex, new Rect(0, 0, tex.width, tex.height), pivot, ppu);
        sprite.name = name;
        return sprite;
    }
}
