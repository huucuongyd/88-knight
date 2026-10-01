using UnityEngine;

[RequireComponent(typeof(SpriteRenderer))]
public class HorseAnimator : MonoBehaviour
{
    [SerializeField] private PlayerController controller;
    [SerializeField] private float pixelsPerUnit = 24f;

    [SerializeField] private DirectionalAnimation idle = new DirectionalAnimation { fps = 5f };
    [SerializeField] private DirectionalAnimation walk = new DirectionalAnimation { fps = 10f };
    [SerializeField] private DirectionalAnimation run = new DirectionalAnimation { fps = 14f };

    [Tooltip("Body bob per gallop frame in pixels (negative = up). Must match Tools/gen_horse.py RUN_BOB.")]
    [SerializeField] private int[] runBob = { 1, 0, -1, -1, 0, 1 };

    private SpriteRenderer spriteRenderer;
    private DirectionalAnimation current;
    private float time;

    /// <summary>Vertical offset (world units) of the saddle caused by the gallop bob.</summary>
    public float SaddleBob { get; private set; }

    private void Awake()
    {
        spriteRenderer = GetComponent<SpriteRenderer>();
        if (controller == null) controller = GetComponentInParent<PlayerController>();
    }

    private void Update()
    {
        bool visible = controller != null && controller.IsMounted;
        spriteRenderer.enabled = visible;
        SaddleBob = 0f;
        if (!visible)
        {
            current = null;
            return;
        }

        var anim = !controller.IsMoving ? idle
            : controller.IsRunning ? run
            : walk;

        if (anim != current)
        {
            current = anim;
            time = 0f;
        }
        time += Time.deltaTime;

        var frames = anim.Get(controller.FacingDirection);
        if (frames == null || frames.Length == 0) return;
        int index = (int)(time * anim.fps) % frames.Length;
        spriteRenderer.sprite = frames[index];

        if (anim == run && runBob != null && runBob.Length > 0)
            SaddleBob = -runBob[index % runBob.Length] / pixelsPerUnit;
    }
}
