using UnityEngine;

public interface IDamageable
{
    /// <param name="empowered">True when the attacker's damage buff was active.</param>
    void TakeHit(int damage, Vector2 sourcePosition, bool empowered);
}
