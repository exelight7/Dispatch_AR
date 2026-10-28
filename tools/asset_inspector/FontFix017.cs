using System.Text.Json.Nodes;

// Round 017 detached font prototype: append one Arabic sub-typeface to each shipped runtime composite font.
// The sub-font names the engine's own shipped Slate face by cooked FFontData filename, so no new font asset or file is added.
static partial class ArabicStage1
{
    const string NaskhPath = "../../../Engine/Content/Slate/Fonts/NotoNaskhArabicUI-Regular.ttf";
    static readonly (int Lo, int Hi)[] ArabicRanges = { (0x0600, 0x06FF), (0x0750, 0x077F), (0x08A0, 0x08FF), (0xFB50, 0xFDFF), (0xFE70, 0xFEFF) };
    static readonly (string Name, string Uasset, string Uexp)[] FontInputs = {
        ("Montserrat-Variable", "1F89A5AEF053323AD71A6D815F4088CC630B7D758D1CDF88A3A90FCB4B3B456B", "0A6811E6241573B77682458048A466097E3A8E012C3AB0876F21E772BED1C6EB"),
        ("Orbitron-Variable", "7B41D9682F11120ECA90E94C7BEE33DDD475A21C23C1BEA2FC9012270B183524", "BED3D528F4577E330E2C4447E5A51430B07843C36490333B5F95F7B926020E1C"),
        ("Rajdhani-Variable", "7C726E48EEFD2B74804C328CB75DA6205EAD08043788633C721C8B54CA0804D2", "A8E2DFB8EAAEB2318224E53CCA8273002C3B89439D9E21FBA78103C615F1048D") };
    static string FontRel(string name) => Path.Combine("Dispatch/Content/Shared/UI/Fonts", name + ".uasset");

    static JsonObject ArabicFontModel(JsonObject model) {
        var a = Copy(model);
        var composite = Arr(Arr(a, "Exports")[0]!, "Data").Single(x => Str(x!["Name"]) == "CompositeFont")!;
        var subs = Arr(composite, "Value").Single(x => Str(x!["Name"]) == "SubTypefaces")!["Value"]!.AsArray();
        JsonNode Field(JsonNode s, string n) => Arr(s, "Value").Single(x => Str(x!["Name"]) == n)!;
        int Bound(JsonNode r, string n) => Num(Arr(Field(r, n), "Value").Single(x => Str(x!["Name"]) == "Value")!["Value"]);
        // Template: the existing culture-neutral Thai sub-font (one range U+0E00-0E7F); every field is reused as serialized.
        var thai = subs.Single(s => Arr(Field(s!, "CharacterRanges"), "Value") is var r && r.Count == 1 && Bound(r[0]!, "LowerBound") == 0x0E00 && Bound(r[0]!, "UpperBound") == 0x0E7F)!;
        Require(Field(thai, "Cultures")["Value"] == null, "template sub-font is culture-restricted");
        var arabic = Copy(thai); var ranges = Arr(Field(arabic, "CharacterRanges"), "Value"); var range = Copy(ranges[0]!); ranges.Clear();
        foreach (var (lo, hi) in ArabicRanges) {
            var r = Copy(range);
            Arr(Field(r, "LowerBound"), "Value").Single(x => Str(x!["Name"]) == "Value")!["Value"] = lo;
            Arr(Field(r, "UpperBound"), "Value").Single(x => Str(x!["Name"]) == "Value")!["Value"] = hi;
            ranges.Add(r);
        }
        var fonts = Arr(Arr(Field(arabic, "Typeface"), "Value").Single(x => Str(x!["Name"]) == "Fonts")!, "Value");
        var entry = Copy(fonts[0]!); fonts.Clear(); fonts.Add(entry);
        Require(Str(Field(entry, "Name")["Value"]) == "Default", "template first typeface entry is not Default");
        var data = Arr(Field(entry, "Font"), "Value")[0]!["Value"]!.AsObject();
        data["LocalFontFaceAsset"] = 0; data["FontFilename"] = NaskhPath; data["Hinting"] = "Default"; data["LoadingPolicy"] = "LazyLoad"; data["SubFaceIndex"] = 0;
        Require(data["bIsCooked"]!.GetValue<bool>(), "template FFontData is not cooked");
        subs.Add(arabic);
        return a;
    }

    public static int BuildFontFix017(string inputRoot, string outputDirectory) {
        try {
            string input = Path.GetFullPath(inputRoot), dir = Path.GetFullPath(outputDirectory);
            Require(!Directory.Exists(dir), "Refusing existing font_fix output");
            foreach (var (name, ua, ue) in FontInputs) {
                string src = Path.Combine(input, FontRel(name));
                Require(HashFile(src) == ua && HashFile(Path.ChangeExtension(src, ".uexp")) == ue, "input hash mismatch " + name);
            }
            var hashes = new JsonArray();
            foreach (string run in new[] { "", "determinism" })
                foreach (var (name, _, _) in FontInputs) {
                    var source = Read(Path.Combine(input, FontRel(name))); Require(source.VerifyBinaryEquality(), "input roundtrip " + name);
                    string target = Path.Combine(dir, run, FontRel(name)); WritePackage(ArabicFontModel(Model(source)), target);
                    if (run == "") hashes.Add(new JsonObject { ["path"] = FontRel(name).Replace('\\', '/'), ["uasset"] = HashFile(target), ["uexp"] = HashFile(Path.ChangeExtension(target, ".uexp")) });
                }
            foreach (var (name, _, _) in FontInputs) foreach (string ext in new[] { ".uasset", ".uexp" })
                Require(File.ReadAllBytes(Path.ChangeExtension(Path.Combine(dir, FontRel(name)), ext)).SequenceEqual(File.ReadAllBytes(Path.ChangeExtension(Path.Combine(dir, "determinism", FontRel(name)), ext))), "nondeterministic " + name + ext);
            File.WriteAllText(Path.Combine(dir, "NOT_INSTALLABLE.txt"), "FONT_FIX_017 DETACHED PROTOTYPE - NOT_INSTALLED - NOT_RUNTIME_TESTED\n");
            SaveJson(Path.Combine(dir, "font_fix_017_manifest.json"), new JsonObject { ["status"] = "FONT_FIX_017_GENERATED", ["arabicFace"] = NaskhPath,
                ["ranges"] = new JsonArray(ArabicRanges.Select(r => (JsonNode)$"U+{r.Lo:X4}-U+{r.Hi:X4}").ToArray()), ["outputs"] = hashes,
                ["deterministicBinaryEqual"] = true, ["installed"] = false, ["tested_in_game"] = 0, ["final"] = 0 });
            Console.WriteLine("FONT_FIX_017_GENERATED " + dir); return 0;
        } catch (Exception ex) { Console.Error.WriteLine(ex.ToString()); return 1; }
    }
}
