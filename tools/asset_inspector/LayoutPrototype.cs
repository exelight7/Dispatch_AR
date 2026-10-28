using System.Security.Cryptography;
using System.Text.Json;
using UAssetAPI;
using UAssetAPI.ExportTypes;
using UAssetAPI.PropertyTypes.Objects;
using UAssetAPI.PropertyTypes.Structs;
using UAssetAPI.UnrealTypes;

static class LayoutPrototype
{
    // Detached layout experiment only: it retains Proto's unsupported Arabic typewriter.
    public static int Build(string sourcePath, string outputPath)
    {
        try
        {
            string source = Path.GetFullPath(sourcePath);
            string output = Path.GetFullPath(outputPath);
            if (Path.GetFileName(source) != "WBP_SubtitleBlock.uasset" || Path.GetFileName(output) != "WBP_SubtitleBlock.uasset")
                throw new ArgumentException("This prototype accepts only WBP_SubtitleBlock.uasset.");
            if (output.Contains("\\L10N\\", StringComparison.OrdinalIgnoreCase))
                throw new ArgumentException("UE4.27 does not support L10N replacement of bytecode Blueprints.");
            foreach (string extension in new[] { ".uasset", ".uexp", ".json", ".verification.json" })
                if (File.Exists(Path.ChangeExtension(output, extension))) throw new IOException("Prototype output already exists.");
            string[] originals = { source, Path.ChangeExtension(source, ".uexp") };
            string[] beforeHashes = originals.Select(Hash).ToArray();
            if (beforeHashes[0] != "5B11CA427CC9BC990000E6C4FFA147E07D305E21C15132045FF18CB927D8D8A5" ||
                beforeHashes[1] != "5CC987CF5190E3153A8B6B77E4444E3CB79FED419453175F22A80C2595FBA64F")
                throw new InvalidDataException("Unexpected source build; inspect it before changing this prototype.");
            byte[] originalCombined = Combine(originals);
            var asset = new UAsset(source, EngineVersion.VER_UE4_27);
            if (!asset.VerifyBinaryEquality()) throw new InvalidDataException("Source does not roundtrip byte-identically.");
            var ranges = asset.Exports.Select(x => (x.SerialOffset, x.SerialSize)).ToArray();
            var changed = new HashSet<int>();
            for (int index = 0; index < asset.Exports.Count; index++)
            {
                if (asset.Exports[index] is not NormalExport export) continue;
                string name = export.ObjectName.ToString();
                if (name is "SubtitleProtoText" or "SubtitleShadowProtoText")
                {
                    ((BytePropertyData)export.Data.Single(x => x.Name.ToString() == "Justification")).EnumValue = new FName(asset, "ETextJustify::Right");
                    if (export.Data.Any(x => x.Name.ToString() == "ShapedTextOptions"))
                        throw new InvalidDataException("Unexpected existing shaped-text override.");
                    export.Data.Add(new StructPropertyData(new FName(asset, "ShapedTextOptions"), new FName(asset, "ShapedTextOptions"))
                    {
                        Value = new List<PropertyData>
                        {
                            new BoolPropertyData(new FName(asset, "bOverride_TextShapingMethod")) { Value = true },
                            new BoolPropertyData(new FName(asset, "bOverride_TextFlowDirection")) { Value = true },
                            new EnumPropertyData(new FName(asset, "TextShapingMethod")) { EnumType = new FName(asset, "ETextShapingMethod"), Value = new FName(asset, "ETextShapingMethod::FullShaping") },
                            new EnumPropertyData(new FName(asset, "TextFlowDirection")) { EnumType = new FName(asset, "ETextFlowDirection"), Value = new FName(asset, "ETextFlowDirection::RightToLeft") }
                        }
                    });
                    changed.Add(index);
                }
                if (name is "OverlaySlot_1" or "OverlaySlot_3" or "OverlaySlot_4")
                {
                    ((BytePropertyData)export.Data.Single(x => x.Name.ToString() == "HorizontalAlignment")).EnumValue = new FName(asset, "HAlign_Fill");
                    changed.Add(index);
                }
            }
            if (changed.Count != 5) throw new InvalidDataException("Expected exactly five layout exports.");
            Directory.CreateDirectory(Path.GetDirectoryName(output)!);
            asset.Write(output);
            var reread = new UAsset(output, EngineVersion.VER_UE4_27);
            if (!reread.VerifyBinaryEquality()) throw new InvalidDataException("Prototype roundtrip failed.");
            byte[] outputCombined = Combine(new[] { output, Path.ChangeExtension(output, ".uexp") });
            int unchangedCount = 0;
            for (int index = 0; index < asset.Exports.Count; index++)
            {
                if (changed.Contains(index)) continue;
                var old = ranges[index];
                var current = reread.Exports[index];
                if (!originalCombined.AsSpan((int)old.SerialOffset, (int)old.SerialSize).SequenceEqual(outputCombined.AsSpan((int)current.SerialOffset, (int)current.SerialSize)))
                    throw new InvalidDataException($"Unexpected export payload change: {index + 1}.");
                unchangedCount++;
            }
            if (!beforeHashes.SequenceEqual(originals.Select(Hash))) throw new IOException("Source hash changed.");
            File.WriteAllText(Path.ChangeExtension(output, ".json"), reread.SerializeJson(true));
            string report = JsonSerializer.Serialize(new { status = "UNVERIFIED_LAYOUT_PROTOTYPE", output,
                sourceHashesUnchanged = true, binaryRoundtripEqual = true, unchangedExportPayloads = unchangedCount,
                changedExports = changed.Select(x => new { index = x + 1, name = reread.Exports[x].ObjectName.ToString() }),
                typewriter = "ORIGINAL_UNMODIFIED_UNSUPPORTED_RTL", cultureScope = "INSTALL_TIME_ARABIC_ONLY_ORIGINAL_ASSET_PATH_REQUIRED",
                sha256 = new[] { output, Path.ChangeExtension(output, ".uexp") }.Select(path => new { path, hash = Hash(path) }) });
            File.WriteAllText(Path.ChangeExtension(output, ".verification.json"), report);
            Console.WriteLine(report);
            return 0;
        }
        catch (Exception error)
        {
            Console.Error.WriteLine($"{error.GetType().Name}: {error.Message}");
            return 1;
        }
    }

    static byte[] Combine(IEnumerable<string> paths) => paths.SelectMany(File.ReadAllBytes).ToArray();
    static string Hash(string path) => Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path)));
}
