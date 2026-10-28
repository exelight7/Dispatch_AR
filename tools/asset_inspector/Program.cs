using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using UAssetAPI;
using UAssetAPI.UnrealTypes;

if (args.Length == 3 && args[0] == "--arabic-fade-023")
    return ArabicStage1.BuildFade023(args[1], args[2]);
if (args.Length == 3 && args[0] == "--validate-arabic-fade-023")
    return ArabicStage1.ValidateFade023(args[1], args[2]);

if (args.Length == 3 && args[0] == "--arabic-stylefix-021")
    return ArabicStage1.BuildStyleFix021(args[1], args[2]);
if (args.Length == 3 && args[0] == "--validate-arabic-stylefix-021")
    return ArabicStage1.ValidateStyleFix021(args[1], args[2]);

if (args.Length == 3 && args[0] == "--arabic-wbp-repair-019")
    return ArabicStage1.BuildRepair019(args[1], args[2]);
if (args.Length == 3 && args[0] == "--validate-arabic-wbp-repair-019")
    return ArabicStage1.ValidateRepair019(args[1], args[2]);

if (args.Length == 3 && args[0] == "--font-fix-017")
    return ArabicStage1.BuildFontFix017(args[1], args[2]);

if (args.Length == 3 && args[0] == "--arabic-wbp-clock")
    return ArabicStage1.BuildClock(args[1], args[2]);
if (args.Length == 3 && args[0] == "--validate-arabic-wbp-clock")
    return ArabicStage1.ValidateClock(args[1], args[2]);

if (args.Length == 3 && args[0] == "--arabic-wbp-reveal")
    return ArabicStage1.BuildReveal(args[1], args[2]);
if (args.Length == 3 && args[0] == "--validate-arabic-wbp-reveal")
    return ArabicStage1.ValidateReveal(args[1], args[2]);

if (args.Length == 3 && args[0] == "--arabic-wbp-stage2")
    return ArabicStage1.BuildStage2(args[1], args[2]);
if (args.Length == 3 && args[0] == "--validate-arabic-wbp-stage2")
    return ArabicStage1.ValidateStage2(args[1], args[2]);

if (args.Length == 3 && args[0] == "--arabic-wbp-stage1")
    return ArabicStage1.Build(args[1], args[2]);
if (args.Length == 3 && args[0] == "--validate-arabic-wbp-stage1")
    return ArabicStage1.Validate(args[1], args[2]);

if (args.Length == 3 && args[0] == "--layout-prototype")
    return LayoutPrototype.Build(args[1], args[2]);
if (args.Length == 4 && args[0] == "--word-reveal-prototype")
    return WordRevealPrototype.Build(args[1], args[2], args[3]);

if (args.Length == 1 && args[0] == "--self-check")
{
    if ((int)EngineVersion.VER_UE4_27 != 29 || !SamePath("a.uasset", "./a.uasset") || SamePath("a.uasset", "a.json"))
        throw new InvalidOperationException("Argument/path self-check failed.");
    Console.WriteLine("PASS: UE4.27 selection and normalized path collision checks.");
    return 0;
}

if (args.Length != 2)
{
    Console.Error.WriteLine("Usage: asset_inspector <input.uasset> <new-output.json> | --self-check | --layout-prototype <WBP_SubtitleBlock.uasset> <new-output.uasset> | --word-reveal-prototype <DT_SubtitlesProtoRichText[_Large].uasset> <new-output.uasset> <SpaceInterval>");
    return 2;
}

try
{
    string input = Path.GetFullPath(args[0]);
    string output = Path.GetFullPath(args[1]);
    if (!string.Equals(Path.GetExtension(input), ".uasset", StringComparison.OrdinalIgnoreCase) || !File.Exists(input))
        throw new ArgumentException("Input must be an existing .uasset file; keep its .uexp adjacent.");
    if (!string.Equals(Path.GetExtension(output), ".json", StringComparison.OrdinalIgnoreCase) || SamePath(input, output))
        throw new ArgumentException("Output must be a distinct .json path.");
    if (File.Exists(output)) throw new IOException("Output already exists; choose a new filename.");

    string[] sourceFiles = new[] { input, Path.ChangeExtension(input, ".uexp"), Path.ChangeExtension(input, ".ubulk") }
        .Where(File.Exists).ToArray();
    string[] before = sourceFiles.Select(Hash).ToArray();
    var asset = new UAsset(input, EngineVersion.VER_UE4_27);
    string json = asset.SerializeJson(true);
    using var parsed = JsonDocument.Parse(json);
    if (parsed.RootElement.ValueKind != JsonValueKind.Object) throw new InvalidDataException("Expected asset JSON object.");
    bool binaryEqual = asset.VerifyBinaryEquality();
    if (!before.SequenceEqual(sourceFiles.Select(Hash))) throw new IOException("Input hash changed during inspection.");
    Directory.CreateDirectory(Path.GetDirectoryName(output)!);
    using (var stream = new FileStream(output, FileMode.CreateNew, FileAccess.Write))
    using (var writer = new StreamWriter(stream, new UTF8Encoding(false))) writer.Write(json);
    Console.WriteLine(JsonSerializer.Serialize(new { input, output, engine = "UE4.27", exports = asset.Exports.Count,
        imports = asset.Imports.Count, binaryRoundtripEqual = binaryEqual, sourceHashesUnchanged = true,
        sha256 = sourceFiles.Select((path, index) => new { path, hash = before[index] }) }));
    return 0;
}
catch (Exception error)
{
    Console.Error.WriteLine($"{error.GetType().Name}: {error.Message}");
    return 1;
}

static string Hash(string path) => Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path)));
static bool SamePath(string left, string right) => string.Equals(Path.GetFullPath(left), Path.GetFullPath(right), StringComparison.OrdinalIgnoreCase);
