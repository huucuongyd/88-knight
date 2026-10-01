using System.Collections.Generic;
using System.Linq;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

/// <summary>
/// Builds a sample forest map from the sprites cut out of map.png by Tools/gen_map_assets.py:
/// tiled grass, a ring of trees along the walls and scattered props inside.
/// World objects are Y-sorted (Renderer2D custom axis) at sorting order 1.
/// </summary>
public static class TopDownMapSetup
{
    private const string MapFolder = "Assets/Sprites/Map";
    private const string GrassPath = MapFolder + "/Ground/Grass.png";
    private const string Renderer2DPath = "Assets/Settings/Renderer2D.asset";
    private const int GrassPixelsPerUnit = 48;
    private const int WorldSortingOrder = 1;
    private const int Seed = 1234;
    // The Player pivot is 0.5 units above its feet; props sort from the same height above their base.
    public const float SortHeight = 0.5f;
    public const int WorldSortingOrderValue = WorldSortingOrder;

    private class Category
    {
        public string Name;
        public int PixelsPerUnit;
        public int Count;
        public float Spacing;
        // Collider as a fraction of the sprite size; zero width means walk-through.
        public Vector2 Collider;
    }

    private static readonly Category[] Categories =
    {
        new Category { Name = "Trees", PixelsPerUnit = 56, Count = 14, Spacing = 2.2f, Collider = new Vector2(0.22f, 0.08f) },
        new Category { Name = "SmallTrees", PixelsPerUnit = 56, Count = 8, Spacing = 1.2f, Collider = new Vector2(0.2f, 0.08f) },
        new Category { Name = "Bushes", PixelsPerUnit = 64, Count = 12, Spacing = 1.2f, Collider = new Vector2(0.7f, 0.3f) },
        new Category { Name = "Rocks", PixelsPerUnit = 64, Count = 6, Spacing = 1.2f, Collider = new Vector2(0.8f, 0.4f) },
        new Category { Name = "Logs", PixelsPerUnit = 64, Count = 6, Spacing = 1.4f, Collider = new Vector2(0.9f, 0.35f) },
        new Category { Name = "Plants", PixelsPerUnit = 96, Count = 30, Spacing = 0.6f },
        new Category { Name = "Flowers", PixelsPerUnit = 110, Count = 36, Spacing = 0.5f },
        new Category { Name = "Mushrooms", PixelsPerUnit = 110, Count = 10, Spacing = 0.5f },
        new Category { Name = "Pebbles", PixelsPerUnit = 96, Count = 6, Spacing = 0.6f },
    };

    /// <summary>Builds the map inside a play area of +-halfSize. Areas in keepClear stay empty.</summary>
    public static void Build(Vector2 halfSize, Rect[] keepClear)
    {
        if (!AssetDatabase.IsValidFolder(MapFolder))
        {
            Debug.LogWarning($"Missing {MapFolder}; run Tools/gen_map_assets.py first.");
            return;
        }

        EnableYSorting();

        var old = GameObject.Find("Map");
        if (old != null) Object.DestroyImmediate(old);
        var root = new GameObject("Map").transform;

        CreateGround(root, halfSize);

        var rng = new System.Random(Seed);
        var placed = new List<(Vector2 pos, float radius)>();
        foreach (var r in keepClear)
            placed.Add((r.center, Mathf.Max(r.width, r.height) * 0.5f));

        var trees = LoadCategory(Categories[0]);
        if (trees.Length > 0)
            PlaceBorder(root, Categories[0], trees, halfSize, rng, placed);

        foreach (var cat in Categories)
        {
            var sprites = LoadCategory(cat);
            if (sprites.Length == 0) continue;
            var parent = new GameObject(cat.Name).transform;
            parent.SetParent(root, false);
            for (int i = 0; i < cat.Count; i++)
            {
                if (!TryFindSpot(halfSize - Vector2.one * 0.8f, cat.Spacing, keepClear, placed, rng, out var pos)) break;
                placed.Add((pos, cat.Spacing * 0.5f));
                CreateProp(parent, cat, sprites[rng.Next(sprites.Length)], pos, rng.NextDouble() < 0.5);
            }
        }
    }

    /// <summary>Makes sprites with the same sorting order draw lower-on-screen in front.</summary>
    private static void EnableYSorting()
    {
        var data = AssetDatabase.LoadAssetAtPath<Renderer2DData>(Renderer2DPath);
        if (data == null)
        {
            Debug.LogWarning($"Missing {Renderer2DPath}; props will not be Y-sorted.");
            return;
        }
        var so = new SerializedObject(data);
        so.FindProperty("m_TransparencySortMode").intValue = (int)TransparencySortMode.CustomAxis;
        so.FindProperty("m_TransparencySortAxis").vector3Value = Vector3.up;
        so.ApplyModifiedPropertiesWithoutUndo();
        EditorUtility.SetDirty(data);
    }

    private static void CreateGround(Transform root, Vector2 halfSize)
    {
        var importer = AssetImporter.GetAtPath(GrassPath) as TextureImporter;
        if (importer == null)
        {
            Debug.LogWarning($"Missing {GrassPath}");
            return;
        }
        importer.textureType = TextureImporterType.Sprite;
        importer.spriteImportMode = SpriteImportMode.Single;
        importer.spritePixelsPerUnit = GrassPixelsPerUnit;
        importer.filterMode = FilterMode.Point;
        importer.wrapMode = TextureWrapMode.Repeat;
        importer.textureCompression = TextureImporterCompression.Uncompressed;
        importer.mipmapEnabled = false;
        var settings = new TextureImporterSettings();
        importer.ReadTextureSettings(settings);
        settings.spriteMeshType = SpriteMeshType.FullRect;
        importer.SetTextureSettings(settings);
        importer.SaveAndReimport();

        var ground = new GameObject("Ground");
        ground.transform.SetParent(root, false);
        var sr = ground.AddComponent<SpriteRenderer>();
        sr.sprite = AssetDatabase.LoadAssetAtPath<Sprite>(GrassPath);
        sr.drawMode = SpriteDrawMode.Tiled;
        // Extra margin so the camera never sees past the grass at the walls.
        sr.size = (halfSize + new Vector2(12f, 8f)) * 2f;
        sr.sortingOrder = -100;
    }

    private static void PlaceBorder(Transform root, Category cat, Sprite[] sprites, Vector2 halfSize,
        System.Random rng, List<(Vector2 pos, float radius)> placed)
    {
        var parent = new GameObject("BorderTrees").transform;
        parent.SetParent(root, false);
        const float step = 1.7f;
        // Two staggered rows just outside the walls, so the play area is framed by forest.
        for (int row = 0; row < 2; row++)
        {
            float inset = 0.6f + row * 1.1f;
            float offset = row * step * 0.5f;
            for (float x = -halfSize.x - 1f + offset; x <= halfSize.x + 1f; x += step)
            {
                AddBorderTree(new Vector2(x, halfSize.y + inset));
                AddBorderTree(new Vector2(x, -halfSize.y - inset));
            }
            for (float y = -halfSize.y + offset; y <= halfSize.y; y += step)
            {
                AddBorderTree(new Vector2(-halfSize.x - inset, y));
                AddBorderTree(new Vector2(halfSize.x + inset, y));
            }
        }

        void AddBorderTree(Vector2 pos)
        {
            pos += new Vector2((float)(rng.NextDouble() - 0.5) * 0.6f, (float)(rng.NextDouble() - 0.5) * 0.4f);
            placed.Add((pos, cat.Spacing * 0.5f));
            CreateProp(parent, cat, sprites[rng.Next(sprites.Length)], pos, rng.NextDouble() < 0.5);
        }
    }

    private static bool TryFindSpot(Vector2 half, float spacing, Rect[] keepClear,
        List<(Vector2 pos, float radius)> placed, System.Random rng, out Vector2 pos)
    {
        for (int attempt = 0; attempt < 60; attempt++)
        {
            pos = new Vector2((float)(rng.NextDouble() * 2 - 1) * half.x, (float)(rng.NextDouble() * 2 - 1) * half.y);
            var p = pos;
            if (keepClear.Any(r => r.Contains(p))) continue;
            if (placed.Any(o => Vector2.Distance(o.pos, p) < o.radius + spacing * 0.5f)) continue;
            return true;
        }
        pos = default;
        return false;
    }

    /// <summary>pos is where the prop touches the ground.</summary>
    private static void CreateProp(Transform parent, Category cat, Sprite sprite, Vector2 pos, bool flip)
    {
        var go = new GameObject(sprite.name);
        go.transform.SetParent(parent, false);
        go.transform.position = pos + Vector2.up * SortHeight;
        var sr = go.AddComponent<SpriteRenderer>();
        sr.sprite = sprite;
        sr.flipX = flip;
        sr.sortingOrder = WorldSortingOrder;
        sr.spriteSortPoint = SpriteSortPoint.Pivot;

        if (cat.Collider.x <= 0f) return;
        var size = sprite.bounds.size;
        var col = go.AddComponent<BoxCollider2D>();
        col.size = new Vector2(size.x * cat.Collider.x, size.y * cat.Collider.y);
        col.offset = new Vector2(0f, -SortHeight + col.size.y * 0.5f);
    }

    private static Sprite[] LoadCategory(Category cat)
    {
        string folder = $"{MapFolder}/{cat.Name}";
        if (!AssetDatabase.IsValidFolder(folder)) return new Sprite[0];
        var sprites = new List<Sprite>();
        foreach (var guid in AssetDatabase.FindAssets("t:Texture2D", new[] { folder }))
        {
            string path = AssetDatabase.GUIDToAssetPath(guid);
            ImportProp(path, cat.PixelsPerUnit);
            var sprite = AssetDatabase.LoadAssetAtPath<Sprite>(path);
            if (sprite != null) sprites.Add(sprite);
        }
        return sprites.OrderBy(s => s.name).ToArray();
    }

    /// <summary>Pivot sits SortHeight above the bottom edge so sprites sort like the Player.</summary>
    private static void ImportProp(string path, int ppu)
    {
        var importer = (TextureImporter)AssetImporter.GetAtPath(path);
        importer.GetSourceTextureWidthAndHeight(out _, out int height);
        var pivot = new Vector2(0.5f, SortHeight * ppu / height);

        var settings = new TextureImporterSettings();
        importer.ReadTextureSettings(settings);
        bool upToDate = importer.textureType == TextureImporterType.Sprite
            && importer.spriteImportMode == SpriteImportMode.Single
            && Mathf.Approximately(importer.spritePixelsPerUnit, ppu)
            && settings.spriteAlignment == (int)SpriteAlignment.Custom
            && Vector2.Distance(settings.spritePivot, pivot) < 0.0001f
            && importer.filterMode == FilterMode.Point;
        if (upToDate) return;

        importer.textureType = TextureImporterType.Sprite;
        importer.spriteImportMode = SpriteImportMode.Single;
        importer.spritePixelsPerUnit = ppu;
        importer.filterMode = FilterMode.Point;
        importer.textureCompression = TextureImporterCompression.Uncompressed;
        importer.mipmapEnabled = false;
        importer.ReadTextureSettings(settings);
        settings.spriteAlignment = (int)SpriteAlignment.Custom;
        settings.spritePivot = pivot;
        importer.SetTextureSettings(settings);
        importer.SaveAndReimport();
    }
}
