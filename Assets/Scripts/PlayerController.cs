using UnityEngine;
using UnityEngine.InputSystem;

[RequireComponent(typeof(Rigidbody2D))]
public class PlayerController : MonoBehaviour
{
    public enum FacingMode
    {
        MoveDirection,
        Mouse
    }

    public enum Weapon
    {
        Glaive,
        Bow,
        Sword
    }

    private const int WeaponCount = 3;

    [SerializeField] private float moveSpeed = 4f;
    [SerializeField] private float runSpeed = 7f;

    [Header("Facing")]
    [SerializeField] private FacingMode facingMode = FacingMode.MoveDirection;

    [Header("Attack")]
    [SerializeField] private float attackDuration = 0.5f;
    [SerializeField] private float bowAttackDuration = 0.5f;
    [SerializeField] private float attackMoveMultiplier = 0f;

    [Header("Weapon")]
    [SerializeField] private Weapon startingWeapon = Weapon.Glaive;

    [Header("Horse")]
    [SerializeField] private float mountedMoveSpeed = 6f;
    [SerializeField] private float mountedRunSpeed = 10f;
    [SerializeField] private float mountedAttackMoveMultiplier = 0.6f;
    [SerializeField] private Vector2 mountedColliderSize = new Vector2(1.2f, 0.4f);
    [SerializeField] private Vector2 mountedColliderOffset = new Vector2(0f, -0.5f);

    private Rigidbody2D rb;
    private BoxCollider2D box;
    private Vector2 standingColliderSize;
    private Vector2 standingColliderOffset;
    private Vector2 moveInput;
    private bool runHeld;
    private float attackTimer;

    public Vector2 FacingDirection { get; private set; } = Vector2.down;
    public bool IsMoving => moveInput.sqrMagnitude > 0.01f;
    public bool IsRunning => IsMoving && runHeld;
    public bool IsAttacking => attackTimer > 0f;
    public bool IsMounted { get; private set; }
    public Weapon CurrentWeapon { get; private set; }

    private void Awake()
    {
        CurrentWeapon = startingWeapon;
        rb = GetComponent<Rigidbody2D>();
        rb.gravityScale = 0f;
        rb.freezeRotation = true;
        rb.interpolation = RigidbodyInterpolation2D.Interpolate;

        box = GetComponent<BoxCollider2D>();
        if (box != null)
        {
            standingColliderSize = box.size;
            standingColliderOffset = box.offset;
        }
    }

    private void Update()
    {
        ReadMoveInput();

        if (attackTimer > 0f)
            attackTimer -= Time.deltaTime;
        else
            UpdateFacing();

        if (!IsAttacking && MountPressed())
            SetMounted(!IsMounted);

        if (!IsAttacking)
            ReadWeaponSwitch();
    }

    /// <summary>Starts the attack animation/lock. Returns false if an attack is already playing.</summary>
    public bool TryBeginAttack()
    {
        if (IsAttacking) return false;
        attackTimer = CurrentWeapon == Weapon.Bow ? bowAttackDuration : attackDuration;
        return true;
    }

    private void ReadWeaponSwitch()
    {
        var keyboard = Keyboard.current;
        var gamepad = Gamepad.current;
        if (keyboard != null && keyboard.digit1Key.wasPressedThisFrame)
            CurrentWeapon = Weapon.Glaive;
        else if (keyboard != null && keyboard.digit2Key.wasPressedThisFrame)
            CurrentWeapon = Weapon.Bow;
        else if (keyboard != null && keyboard.digit3Key.wasPressedThisFrame)
            CurrentWeapon = Weapon.Sword;
        else if ((keyboard != null && keyboard.cKey.wasPressedThisFrame)
                 || (gamepad != null && gamepad.dpad.up.wasPressedThisFrame))
            CurrentWeapon = (Weapon)(((int)CurrentWeapon + 1) % WeaponCount);
    }

    private void FixedUpdate()
    {
        float speed = IsMounted
            ? (IsRunning ? mountedRunSpeed : mountedMoveSpeed)
            : (IsRunning ? runSpeed : moveSpeed);
        if (IsAttacking) speed *= IsMounted ? mountedAttackMoveMultiplier : attackMoveMultiplier;
        rb.linearVelocity = moveInput * speed;
    }

    public void SetMounted(bool mounted)
    {
        IsMounted = mounted;
        if (box == null) return;
        box.size = mounted ? mountedColliderSize : standingColliderSize;
        box.offset = mounted ? mountedColliderOffset : standingColliderOffset;
    }

    private void ReadMoveInput()
    {
        moveInput = Vector2.zero;
        runHeld = false;

        var keyboard = Keyboard.current;
        if (keyboard != null)
        {
            if (keyboard.upArrowKey.isPressed) moveInput.y += 1;
            if (keyboard.downArrowKey.isPressed) moveInput.y -= 1;
            if (keyboard.rightArrowKey.isPressed) moveInput.x += 1;
            if (keyboard.leftArrowKey.isPressed) moveInput.x -= 1;
            runHeld = keyboard.leftShiftKey.isPressed || keyboard.rightShiftKey.isPressed;
        }

        var gamepad = Gamepad.current;
        if (gamepad != null)
        {
            if (moveInput == Vector2.zero)
                moveInput = gamepad.leftStick.ReadValue();
            runHeld |= gamepad.leftStickButton.isPressed || gamepad.rightTrigger.isPressed;
        }

        moveInput = Vector2.ClampMagnitude(moveInput, 1f);
    }

    private bool MountPressed()
    {
        var keyboard = Keyboard.current;
        var gamepad = Gamepad.current;
        return (keyboard != null && keyboard.bKey.wasPressedThisFrame)
            || (gamepad != null && gamepad.buttonNorth.wasPressedThisFrame);
    }

    private void UpdateFacing()
    {
        if (facingMode == FacingMode.Mouse && Mouse.current != null && Camera.main != null)
        {
            Vector2 mouseWorld = Camera.main.ScreenToWorldPoint(Mouse.current.position.ReadValue());
            var toMouse = mouseWorld - (Vector2)transform.position;
            if (toMouse.sqrMagnitude > 0.0001f)
                FacingDirection = toMouse.normalized;
        }
        else if (moveInput.sqrMagnitude > 0.01f)
        {
            FacingDirection = moveInput.normalized;
        }
    }
}
