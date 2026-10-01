using System.Collections.Generic;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEditor.U2D.Sprites;
using UnityEngine;

public static class TopDownSceneSetup
{
    private const string ScenePath = "Assets/Scenes/SampleScene.unity";
    private const string SpritePath = "Assets/Sprites/Square.png";
    private const string PlayerSpriteFolder = "Assets/Sprites/Swordsman";
    private const string PlayerSpritePrefix = "Swordsman";
    private const int FrameSize = 64;
    private const int PlayerPixelsPerUnit = 24;
    private const string ScarecrowSpritePath = "Assets/Sprites/Scarecrow/Scarecrow.png";
    private const string HorseSpriteFolder = "Assets/Sprites/Horse";
    private const string HorseSpritePrefix = "Horse";
    // Must match how far Tools/gen_horse.py expects the rider to sit above the ground.
    private const int HorseRiderLiftPixels = 9;

    // Row order in the craftpix sheets, top to bottom.
    private static readonly string[] SheetRows = { "down", "left", "right", "up" };

    [MenuItem("Tools/Top Down/Setup Sample Scene")]
    public static void Setup()
    {
        if (EditorApplication.isPlayingOrWillChangePlaymode)
        {
            EditorUtility.DisplayDialog("Top Down Setup", "Hãy thoát Play mode trước khi chạy Setup.", "OK");
            return;
        }

        AssetDatabase.Refresh();
        var sprite = CreateSquareSprite();
        var scene = EditorSceneManager.GetActiveScene();
        if (scene.path != ScenePath)
        {
            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
            scene = EditorSceneManager.OpenScene(ScenePath);
        }

        var idle = LoadSheet(PlayerSpriteFolder, PlayerSpritePrefix, "Idle");
        var walk = LoadSheet(PlayerSpriteFolder, PlayerSpritePrefix, "Walk");
        var run = LoadSheet(PlayerSpriteFolder, PlayerSpritePrefix, "Run");
        var attack = LoadSheet(PlayerSpriteFolder, PlayerSpritePrefix, "Attack");

        var player = GameObject.Find("Player") ?? new GameObject("Player");
        // Rider visuals live on the "Rider" child so they can be lifted onto the horse.
        var oldAnimator = player.GetComponent<PlayerSpriteAnimator>();
        if (oldAnimator != null) Object.DestroyImmediate(oldAnimator);
        var oldRenderer = player.GetComponent<SpriteRenderer>();
        if (oldRenderer != null) Object.DestroyImmediate(oldRenderer);

        var col = GetOrAdd<BoxCollider2D>(player);
        col.size = new Vector2(0.5f, 0.3f);
        col.offset = new Vector2(0f, -0.5f);
        var rb = GetOrAdd<Rigidbody2D>(player);
        rb.gravityScale = 0f;
        rb.freezeRotation = true;
        var controller = GetOrAdd<PlayerController>(player);
        GetOrAdd<PlayerSkills>(player);

        var pivot = player.transform.Find("FacingPivot");
        if (pivot != null) Object.DestroyImmediate(pivot.gameObject);

        var rider = GetOrCreateChild(player.transform, "Rider");
        var sr = GetOrAdd<SpriteRenderer>(rider.gameObject);
        sr.sprite = idle.TryGetValue("down", out var idleDown) && idleDown.Length > 0 ? idleDown[0] : sprite;
        sr.color = Color.white;
        sr.flipX = false;
        sr.sortingOrder = 1;

        var horse = SetupHorse(player.transform, controller);

        var animator = GetOrAdd<PlayerSpriteAnimator>(rider.gameObject);
        var animSo = new SerializedObject(animator);
        animSo.FindProperty("controller").objectReferenceValue = controller;
        animSo.FindProperty("horse").objectReferenceValue = horse;
        animSo.FindProperty("mountedLift").floatValue = HorseRiderLiftPixels / (float)PlayerPixelsPerUnit;
        AssignAnimation(animSo.FindProperty("idle"), idle, 8f, true);
        AssignAnimation(animSo.FindProperty("walk"), walk, 10f, true);
        AssignAnimation(animSo.FindProperty("run"), run, 12f, true);
        const float attackFps = 16f;
        AssignAnimation(animSo.FindProperty("attack"), attack, attackFps, false);
        AssignAnimation(animSo.FindProperty("mountedIdle"), LoadSheet(PlayerSpriteFolder, PlayerSpritePrefix, "Idle_Mounted"), 8f, true);
        AssignAnimation(animSo.FindProperty("mountedAttack"), LoadSheet(PlayerSpriteFolder, PlayerSpritePrefix, "Attack_Mounted"), attackFps, false);
        animSo.ApplyModifiedPropertiesWithoutUndo();

        int attackFrames = attack.TryGetValue("down", out var attackDown) ? attackDown.Length : 8;
        var controllerSo = new SerializedObject(controller);
        controllerSo.FindProperty("attackDuration").floatValue = attackFrames / attackFps;
        controllerSo.FindProperty("mountedColliderSize").vector2Value = new Vector2(1.2f, 0.4f);
        controllerSo.FindProperty("mountedColliderOffset").vector2Value = new Vector2(0f, -0.5f);
        controllerSo.ApplyModifiedPropertiesWithoutUndo();

        CreateScarecrow(new Vector2(3f, 0f));

        CreateWall("Wall_Top", sprite, new Vector2(0, 5), new Vector2(20, 1));
        CreateWall("Wall_Bottom", sprite, new Vector2(0, -5), new Vector2(20, 1));
        CreateWall("Wall_Left", sprite, new Vector2(-10, 0), new Vector2(1, 11));
        CreateWall("Wall_Right", sprite, new Vector2(10, 0), new Vector2(1, 11));

        var cam = Camera.main;
        if (cam != null)
        {
            cam.orthographic = true;
            cam.orthographicSize = 5f;
            var follow = GetOrAdd<CameraFollow>(cam.gameObject);
            follow.Target = player.transform;
        }

        EditorSceneManager.MarkSceneDirty(scene);
        EditorSceneManager.SaveScene(scene);
        AssetDatabase.SaveAssets();
    }

    [MenuItem("Tools/Top Down/Setup Sample Scene", true)]
    private static bool ValidateSetup() => !EditorApplication.isPlayingOrWillChangePlaymode;

    private static HorseAnimator SetupHorse(Transform player, PlayerController controller)
    {
        var horse = GetOrCreateChild(player, "Horse");
        horse.localPosition = Vector3.zero;
        var backSr = GetOrAdd<SpriteRenderer>(horse.gameObject);
        backSr.sortingOrder = 0;
        backSr.enabled = false;

        var front = horse.Find("HorseFront");
        if (front != null) Object.DestroyImmediate(front.gameObject);

        var horseAnimator = GetOrAdd<HorseAnimator>(horse.gameObject);
        var so = new SerializedObject(horseAnimator);
        so.FindProperty("controller").objectReferenceValue = controller;
        so.FindProperty("pixelsPerUnit").floatValue = PlayerPixelsPerUnit;
        foreach (var (anim, fps) in new[] { ("Idle", 5f), ("Walk", 10f), ("Run", 14f) })
            AssignAnimation(so.FindProperty(anim.ToLowerInvariant()), LoadSheet(HorseSpriteFolder, HorseSpritePrefix, anim), fps, true);
        so.ApplyModifiedPropertiesWithoutUndo();
        return horseAnimator;
    }

    private static void CreateScarecrow(Vector2 position)
    {
        var importer = AssetImporter.GetAtPath(ScarecrowSpritePath) as TextureImporter;
        if (importer == null)
        {
            Debug.LogWarning($"Missing sprite: {ScarecrowSpritePath}");
            return;
        }
        importer.textureType = TextureImporterType.Sprite;
        importer.spriteImportMode = SpriteImportMode.Single;
        importer.spritePixelsPerUnit = PlayerPixelsPerUnit;
        importer.filterMode = FilterMode.Point;
        importer.textureCompression = TextureImporterCompression.Uncompressed;
        importer.mipmapEnabled = false;
        var settings = new TextureImporterSettings();
        importer.ReadTextureSettings(settings);
        settings.spriteAlignment = (int)SpriteAlignment.BottomCenter;
        importer.SetTextureSettings(settings);
        importer.SaveAndReimport();

        var scarecrow = GameObject.Find("Scarecrow") ?? new GameObject("Scarecrow");
        scarecrow.transform.position = position;

        var visual = GetOrCreateChild(scarecrow.transform, "Visual");
        visual.localPosition = Vector3.zero;
        var sr = GetOrAdd<SpriteRenderer>(visual.gameObject);
        sr.sprite = AssetDatabase.LoadAssetAtPath<Sprite>(ScarecrowSpritePath);
        sr.sortingOrder = 1;

        // Solid base so the player bumps into the pole.
        var solid = GetOrAdd<BoxCollider2D>(scarecrow);
        solid.size = new Vector2(0.35f, 0.2f);
        solid.offset = new Vector2(0f, 0.12f);

        // Trigger covering the body so attacks aimed at chest height still connect.
        var hurtbox = GetOrCreateChild(scarecrow.transform, "Hurtbox");
        hurtbox.localPosition = Vector3.zero;
        var hurtCol = GetOrAdd<BoxCollider2D>(hurtbox.gameObject);
        hurtCol.isTrigger = true;
        hurtCol.size = new Vector2(1f, 1.5f);
        hurtCol.offset = new Vector2(0f, 0.9f);

        var dummy = GetOrAdd<TrainingDummy>(scarecrow);
        var so = new SerializedObject(dummy);
        so.FindProperty("visual").objectReferenceValue = visual;
        so.FindProperty("numberHeight").floatValue = 1.9f;
        so.ApplyModifiedPropertiesWithoutUndo();
    }

    private static Transform GetOrCreateChild(Transform parent, string name)
    {
        var child = parent.Find(name);
        if (child != null) return child;
        child = new GameObject(name).transform;
        child.SetParent(parent, false);
        return child;
    }

    private static Dictionary<string, Sprite[]> LoadSheet(string folder, string prefix, string animName)
    {
        string path = $"{folder}/{prefix}_{animName}.png";
        var result = new Dictionary<string, Sprite[]>();
        var importer = AssetImporter.GetAtPath(path) as TextureImporter;
        if (importer == null)
        {
            Debug.LogWarning($"Missing sprite sheet: {path}");
            return result;
        }

        importer.textureType = TextureImporterType.Sprite;
        importer.spriteImportMode = SpriteImportMode.Multiple;
        importer.spritePixelsPerUnit = PlayerPixelsPerUnit;
        importer.filterMode = FilterMode.Point;
        importer.textureCompression = TextureImporterCompression.Uncompressed;
        importer.mipmapEnabled = false;
        importer.SaveAndReimport();

        var texture = AssetDatabase.LoadAssetAtPath<Texture2D>(path);
        int columns = texture.width / FrameSize;
        int rows = texture.height / FrameSize;

        var factory = new SpriteDataProviderFactories();
        factory.Init();
        var provider = factory.GetSpriteEditorDataProviderFromObject(importer);
        provider.InitSpriteEditorDataProvider();

        // Rows may have fewer frames than the sheet is wide; empty cells would show as blank frames.
        var pixels = new Texture2D(2, 2);
        pixels.LoadImage(System.IO.File.ReadAllBytes(path));

        var rects = new List<SpriteRect>();
        for (int row = 0; row < rows && row < SheetRows.Length; row++)
        {
            for (int c = 0; c < columns; c++)
            {
                var cell = new RectInt(c * FrameSize, texture.height - (row + 1) * FrameSize, FrameSize, FrameSize);
                if (IsEmpty(pixels, cell)) continue;
                rects.Add(new SpriteRect
                {
                    name = $"{prefix}_{animName}_{SheetRows[row]}_{c}",
                    rect = new Rect(cell.x, cell.y, cell.width, cell.height),
                    alignment = SpriteAlignment.Center,
                    pivot = new Vector2(0.5f, 0.5f),
                    spriteID = GUID.Generate()
                });
            }
        }

        Object.DestroyImmediate(pixels);

        provider.SetSpriteRects(rects.ToArray());
        var nameIds = provider.GetDataProvider<ISpriteNameFileIdDataProvider>();
        nameIds?.SetNameFileIdPairs(rects.Select(r => new SpriteNameFileIdPair(r.name, r.spriteID)));
        provider.Apply();
        importer.SaveAndReimport();

        var sprites = AssetDatabase.LoadAllAssetsAtPath(path).OfType<Sprite>().ToList();
        foreach (var dir in SheetRows)
        {
            string namePrefix = $"{prefix}_{animName}_{dir}_";
            result[dir] = sprites
                .Where(s => s.name.StartsWith(namePrefix))
                .OrderBy(s => int.Parse(s.name.Substring(namePrefix.Length)))
                .ToArray();
        }
        return result;
    }

    private static bool IsEmpty(Texture2D texture, RectInt cell)
    {
        return texture.GetPixels(cell.x, cell.y, cell.width, cell.height).All(c => c.a <= 0f);
    }

    private static void AssignAnimation(SerializedProperty prop, Dictionary<string, Sprite[]> frames, float fps, bool loop)
    {
        prop.FindPropertyRelative("fps").floatValue = fps;
        prop.FindPropertyRelative("loop").boolValue = loop;
        foreach (var dir in SheetRows)
        {
            var arr = prop.FindPropertyRelative(dir);
            var sprites = frames.TryGetValue(dir, out var s) ? s : new Sprite[0];
            arr.arraySize = sprites.Length;
            for (int i = 0; i < sprites.Length; i++)
                arr.GetArrayElementAtIndex(i).objectReferenceValue = sprites[i];
        }
    }

    private static T GetOrAdd<T>(GameObject go) where T : Component
    {
        var c = go.GetComponent<T>();
        return c != null ? c : go.AddComponent<T>();
    }

    private static void CreateWall(string name, Sprite sprite, Vector2 position, Vector2 size)
    {
        var wall = GameObject.Find(name) ?? new GameObject(name);
        wall.transform.position = position;
        wall.transform.localScale = new Vector3(size.x, size.y, 1);
        var sr = GetOrAdd<SpriteRenderer>(wall);
        sr.sprite = sprite;
        sr.color = new Color(0.35f, 0.35f, 0.35f);
        if (!wall.GetComponent<BoxCollider2D>()) wall.AddComponent<BoxCollider2D>();
    }

    private static Sprite CreateSquareSprite()
    {
        var existing = AssetDatabase.LoadAssetAtPath<Sprite>(SpritePath);
        if (existing != null) return existing;

        System.IO.Directory.CreateDirectory("Assets/Sprites");
        var tex = new Texture2D(32, 32);
        var pixels = new Color[32 * 32];
        for (int i = 0; i < pixels.Length; i++) pixels[i] = Color.white;
        tex.SetPixels(pixels);
        System.IO.File.WriteAllBytes(SpritePath, tex.EncodeToPNG());
        Object.DestroyImmediate(tex);
        AssetDatabase.ImportAsset(SpritePath);

        var importer = (TextureImporter)AssetImporter.GetAtPath(SpritePath);
        importer.textureType = TextureImporterType.Sprite;
        importer.spritePixelsPerUnit = 32;
        importer.filterMode = FilterMode.Point;
        importer.SaveAndReimport();

        return AssetDatabase.LoadAssetAtPath<Sprite>(SpritePath);
    }
}
