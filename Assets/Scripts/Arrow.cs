using System.Collections.Generic;
using UnityEngine;

/// <summary>Straight-flying arrow: damages the first IDamageable it touches, sticks into solid colliders.</summary>
[RequireComponent(typeof(SpriteRenderer))]
public class Arrow : MonoBehaviour
{
    private const float StuckLifetime = 1f;

    private SpriteRenderer spriteRenderer;
    private ICollection<Collider2D> ignore;
    private Vector2 direction;
    private Vector2 source;
    private float speed;
    private float rangeLeft;
    private int damage;
    private bool empowered;
    private float stuckTime = -1f;

    public static Arrow Spawn(Sprite sprite, Color color, Vector2 position, Vector2 direction, float speed, float range,
        int damage, bool empowered, Vector2 source, ICollection<Collider2D> ignore)
    {
        var go = new GameObject("Arrow");
        float angle = Mathf.Atan2(direction.y, direction.x) * Mathf.Rad2Deg;
        go.transform.SetPositionAndRotation(position, Quaternion.Euler(0f, 0f, angle));
        var sr = go.AddComponent<SpriteRenderer>();
        sr.sprite = sprite;
        sr.color = color;
        sr.sortingOrder = 2;
        var arrow = go.AddComponent<Arrow>();
        arrow.spriteRenderer = sr;
        arrow.direction = direction.normalized;
        arrow.speed = speed;
        arrow.rangeLeft = range;
        arrow.damage = damage;
        arrow.empowered = empowered;
        arrow.source = source;
        arrow.ignore = ignore;
        return arrow;
    }

    private void Update()
    {
        if (stuckTime >= 0f)
        {
            stuckTime += Time.deltaTime;
            var c = spriteRenderer.color;
            spriteRenderer.color = new Color(c.r, c.g, c.b, 1f - stuckTime / StuckLifetime);
            if (stuckTime >= StuckLifetime) Destroy(gameObject);
            return;
        }

        float step = Mathf.Min(speed * Time.deltaTime, rangeLeft);
        Vector2 pos = transform.position;
        foreach (var hit in Physics2D.RaycastAll(pos, direction, step))
        {
            if (ignore != null && ignore.Contains(hit.collider)) continue;
            var target = hit.collider.GetComponentInParent<IDamageable>();
            if (target != null)
            {
                target.TakeHit(damage, source, empowered);
                Destroy(gameObject);
                return;
            }
            if (!hit.collider.isTrigger)
            {
                transform.position = hit.point;
                stuckTime = 0f;
                return;
            }
        }

        transform.position = pos + direction * step;
        rangeLeft -= step;
        if (rangeLeft <= 0f) stuckTime = 0f;
    }
}
