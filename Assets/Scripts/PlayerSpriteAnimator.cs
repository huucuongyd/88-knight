using UnityEngine;

[System.Serializable]
public class DirectionalAnimation
{
    public float fps = 10f;
    public bool loop = true;
    public Sprite[] down;
    public Sprite[] left;
    public Sprite[] right;
    public Sprite[] up;

    public Sprite[] Get(Vector2 dir)
    {
        if (Mathf.Abs(dir.x) > Mathf.Abs(dir.y))
            return dir.x < 0f ? left : right;
        return dir.y > 0f ? up : down;
    }
}

[RequireComponent(typeof(SpriteRenderer))]
public class PlayerSpriteAnimator : MonoBehaviour
{
    [SerializeField] private PlayerController controller;
    [SerializeField] private DirectionalAnimation idle = new DirectionalAnimation { fps = 8f };
    [SerializeField] private DirectionalAnimation walk = new DirectionalAnimation { fps = 10f };
    [SerializeField] private DirectionalAnimation run = new DirectionalAnimation { fps = 12f };
    [SerializeField] private DirectionalAnimation attack = new DirectionalAnimation { fps = 16f, loop = false };

    [Header("Horse")]
    [SerializeField] private HorseAnimator horse;
    [Tooltip("How far the rider is raised onto the saddle, in world units.")]
    [SerializeField] private float mountedLift = 9f / 24f;
    [Tooltip("Leg-less versions of idle/attack used while riding (Tools/gen_mounted_rider.py).")]
    [SerializeField] private DirectionalAnimation mountedIdle = new DirectionalAnimation { fps = 8f };
    [SerializeField] private DirectionalAnimation mountedAttack = new DirectionalAnimation { fps = 16f, loop = false };

    [Header("Bow (Tools/gen_bow.py)")]
    [SerializeField] private DirectionalAnimation bowIdle = new DirectionalAnimation { fps = 8f };
    [SerializeField] private DirectionalAnimation bowWalk = new DirectionalAnimation { fps = 10f };
    [SerializeField] private DirectionalAnimation bowRun = new DirectionalAnimation { fps = 12f };
    [SerializeField] private DirectionalAnimation bowAttack = new DirectionalAnimation { fps = 12f, loop = false };
    [SerializeField] private DirectionalAnimation bowMountedIdle = new DirectionalAnimation { fps = 8f };
    [SerializeField] private DirectionalAnimation bowMountedAttack = new DirectionalAnimation { fps = 12f, loop = false };

    [Header("Sword (Tools/gen_sword.py)")]
    [SerializeField] private DirectionalAnimation swordIdle = new DirectionalAnimation { fps = 8f };
    [SerializeField] private DirectionalAnimation swordWalk = new DirectionalAnimation { fps = 10f };
    [SerializeField] private DirectionalAnimation swordRun = new DirectionalAnimation { fps = 12f };
    [SerializeField] private DirectionalAnimation swordAttack = new DirectionalAnimation { fps = 16f, loop = false };
    [SerializeField] private DirectionalAnimation swordMountedIdle = new DirectionalAnimation { fps = 8f };
    [SerializeField] private DirectionalAnimation swordMountedAttack = new DirectionalAnimation { fps = 16f, loop = false };

    private SpriteRenderer spriteRenderer;
    private DirectionalAnimation current;
    private bool wasAttacking;
    private float time;

    public DirectionalAnimation Attack => attack;

    private void Awake()
    {
        spriteRenderer = GetComponent<SpriteRenderer>();
        if (controller == null) controller = GetComponentInParent<PlayerController>();
    }

    private void Update()
    {
        if (controller == null) return;

        var weapon = controller.CurrentWeapon;
        DirectionalAnimation Pick(DirectionalAnimation glaive, DirectionalAnimation bowAnim, DirectionalAnimation swordAnim) =>
            weapon == PlayerController.Weapon.Bow ? OrFallback(bowAnim, glaive)
            : weapon == PlayerController.Weapon.Sword ? OrFallback(swordAnim, glaive)
            : glaive;

        var anim = controller.IsMounted
                ? (controller.IsAttacking
                    ? OrFallback(Pick(mountedAttack, bowMountedAttack, swordMountedAttack), Pick(attack, bowAttack, swordAttack))
                    : OrFallback(Pick(mountedIdle, bowMountedIdle, swordMountedIdle), Pick(idle, bowIdle, swordIdle)))
            : controller.IsAttacking ? Pick(attack, bowAttack, swordAttack)
            : !controller.IsMoving ? Pick(idle, bowIdle, swordIdle)
            : controller.IsRunning ? Pick(run, bowRun, swordRun)
            : Pick(walk, bowWalk, swordWalk);

        bool attackStarted = controller.IsAttacking && !wasAttacking;
        wasAttacking = controller.IsAttacking;
        if (anim != current || attackStarted)
        {
            current = anim;
            time = 0f;
        }
        time += Time.deltaTime;

        var frames = anim.Get(controller.FacingDirection);
        if (frames == null || frames.Length == 0) return;

        int index = (int)(time * anim.fps);
        index = anim.loop ? index % frames.Length : Mathf.Min(index, frames.Length - 1);
        spriteRenderer.flipX = false;
        spriteRenderer.sprite = frames[index];
    }

    private static DirectionalAnimation OrFallback(DirectionalAnimation preferred, DirectionalAnimation fallback)
    {
        return preferred.down != null && preferred.down.Length > 0 ? preferred : fallback;
    }

    private void LateUpdate()
    {
        if (controller == null || transform == controller.transform) return;
        float y = controller.IsMounted ? mountedLift + (horse != null ? horse.SaddleBob : 0f) : 0f;
        transform.localPosition = new Vector3(0f, y, 0f);
    }
}
