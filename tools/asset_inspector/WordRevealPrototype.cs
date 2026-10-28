using System.Security.Cryptography;
using System.Text.Json;
using System.Text.Json.Nodes;
using UAssetAPI;
using UAssetAPI.ExportTypes;
using UAssetAPI.PropertyTypes.Objects;
using UAssetAPI.UnrealTypes;

static class WordRevealPrototype
{
    // Detached timing experiment. Original package path: installing it would change English too.
    public static int Build(string sourcePath, string outputPath, string spaceText)
    {
        try
        {
            string source = Path.GetFullPath(sourcePath);
            string output = Path.GetFullPath(outputPath);
            string name = Path.GetFileName(source);
            if (name is not ("DT_SubtitlesProtoRichText.uasset" or "DT_SubtitlesProtoRichText_Large.uasset") || Path.GetFileName(output) != name)
                throw new ArgumentException("Accepts only DT_SubtitlesProtoRichText[_Large].uasset with the same output file name.");
            float space = float.Parse(spaceText, System.Globalization.CultureInfo.InvariantCulture);
            if (!(space > 0f)) throw new ArgumentException("SpaceInterval must be positive.");
            if (output.Contains("\\steamapps\\", StringComparison.OrdinalIgnoreCase) || output.Contains("\\L10N\\", StringComparison.OrdinalIgnoreCase))
                throw new ArgumentException("Prototype output must stay detached: no game install path, no L10N path.");
            foreach (string extension in new[] { ".uasset", ".uexp", ".json", ".verification.json" })
                if (File.Exists(Path.ChangeExtension(output, extension))) throw new IOException("Prototype output already exists.");
            string[] originals = { source, Path.ChangeExtension(source, ".uexp") };
            string[] beforeHashes = originals.Select(Hash).ToArray();

            var targets = new (string Field, object Value)[]
            {
                ("PrintLetterInterval", 0f), ("PrintLetterAnimationTime", 0f), ("UseAdvancedPrintIntervals", true),
                ("SpaceInterval", space), ("CommaInterval", 0f), ("SentenceInterval", 0f),
                ("EllipsisInterval", 0f), ("MidWordDashInterval", 0f),
            };
            var asset = new UAsset(source, EngineVersion.VER_UE4_27);
            if (!asset.VerifyBinaryEquality()) throw new InvalidDataException("Source does not roundtrip byte-identically.");
            var originalJson = JsonNode.Parse(asset.SerializeJson(false))!;
            var table = asset.Exports.OfType<DataTableExport>().Single();
            var changes = new List<object>();
            foreach (var row in table.Table.Data)
                foreach (var (field, value) in targets)
                {
                    var prop = row.Value.Single(x => x.Name.ToString() == field);
                    object original = prop switch
                    {
                        FloatPropertyData f => f.Value,
                        BoolPropertyData b => b.Value,
                        _ => throw new InvalidDataException($"{row.Name}.{field}: unexpected {prop.GetType().Name}")
                    };
                    if (prop is FloatPropertyData fp) fp.Value = (float)value; else ((BoolPropertyData)prop).Value = (bool)value;
                    changes.Add(new { row = row.Name.ToString(), field, type = prop.PropertyType.ToString(), original, prototype = value,
                        changed = !original.Equals(value) });
                }

            Directory.CreateDirectory(Path.GetDirectoryName(output)!);
            asset.Write(output);
            var reread = new UAsset(output, EngineVersion.VER_UE4_27);
            if (!reread.VerifyBinaryEquality()) throw new InvalidDataException("Prototype roundtrip failed.");
            foreach (var row in reread.Exports.OfType<DataTableExport>().Single().Table.Data)
                foreach (var (field, value) in targets)
                {
                    var prop = row.Value.Single(x => x.Name.ToString() == field);
                    object now = prop is FloatPropertyData f ? f.Value : ((BoolPropertyData)prop).Value;
                    if (!now.Equals(value)) throw new InvalidDataException($"Reread mismatch {row.Name}.{field}.");
                }
            // Structured diff over the whole reread asset: every differing leaf must be the Value of a target field.
            var diff = new List<(string Path, string Field, string Original, string Prototype)>();
            Diff(originalJson, JsonNode.Parse(reread.SerializeJson(false)), "$", null, diff);
            var stray = diff.Where(d => !d.Path.EndsWith(".Value") || !targets.Any(t => t.Field == d.Field)).ToList();
            if (stray.Count > 0) throw new InvalidDataException($"Unintended change: {stray[0].Path}");
            if (!beforeHashes.SequenceEqual(originals.Select(Hash))) throw new IOException("Source hash changed.");
            string[] outputs = { output, Path.ChangeExtension(output, ".uexp") };
            var byteDiff = originals.Zip(outputs, (a, b) => (A: File.ReadAllBytes(a), B: File.ReadAllBytes(b)))
                .Select((p, i) => new { file = Path.GetFileName(outputs[i]), sameLength = p.A.Length == p.B.Length,
                    differingBytes = p.A.Length == p.B.Length ? p.A.Zip(p.B).Count(x => x.First != x.Second) : -1 }).ToArray();
            File.WriteAllText(Path.ChangeExtension(output, ".json"), reread.SerializeJson(true));
            string report = JsonSerializer.Serialize(new
            {
                status = "UNVERIFIED_TIMING_PROTOTYPE_NOT_INSTALLED", cultureScope = "ARABIC_ISOLATION_NOT_PROVEN_ORIGINAL_PACKAGE_PATH",
                sourceHashesUnchanged = true, binaryRoundtripEqual = true, rows = table.Table.Data.Count, changes,
                structuredDiff = diff.Select(d => new { path = d.Path, field = d.Field, original = d.Original, prototype = d.Prototype }),
                unintendedDiffs = 0, byteDiff,
                sha256Original = originals.Select((path, i) => new { path, hash = beforeHashes[i] }),
                sha256Prototype = outputs.Select(path => new { path, hash = Hash(path) })
            }, new JsonSerializerOptions { WriteIndented = true });
            File.WriteAllText(Path.ChangeExtension(output, ".verification.json"), report);
            Console.WriteLine($"OK {name}: {table.Table.Data.Count} rows, {changes.Count} target fields; see verification.json");
            return 0;
        }
        catch (Exception error)
        {
            Console.Error.WriteLine($"{error.GetType().Name}: {error.Message}");
            return 1;
        }
    }

    static void Diff(JsonNode? a, JsonNode? b, string path, string? field, List<(string, string, string, string)> diff)
    {
        if (a is JsonObject oa && b is JsonObject ob)
        {
            field = oa["Name"]?.ToString() ?? field;
            foreach (string key in oa.Select(x => x.Key).Union(ob.Select(x => x.Key)))
                Diff(oa[key], ob[key], $"{path}.{key}", field, diff);
        }
        else if (a is JsonArray xa && b is JsonArray xb && xa.Count == xb.Count)
            for (int i = 0; i < xa.Count; i++) Diff(xa[i], xb[i], $"{path}[{i}]", field, diff);
        else if (a?.ToJsonString() != b?.ToJsonString())
            diff.Add((path, field ?? "", a?.ToJsonString() ?? "null", b?.ToJsonString() ?? "null"));
    }

    static string Hash(string path) => Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path)));
}
