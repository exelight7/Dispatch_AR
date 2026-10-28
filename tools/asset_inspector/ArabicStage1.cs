using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using UAssetAPI;
using UAssetAPI.ExportTypes;
using UAssetAPI.Kismet.Bytecode;
using UAssetAPI.UnrealTypes;

// Stage 1 only. Uses UAssetAPI's typed JSON bridge; no raw package/bytecode patching.
static partial class ArabicStage1
{
    const string Wbp = "WBP_SubtitleBlock_AR_STAGE1";
    const string SourceDir = "extracted/Dispatch/Content/Shared/Core/Widgets";
    const string SourceWbp = "WBP_SubtitleBlock";
    const string SourceTable = "DT_SubtitlesProtoRichText";
    static readonly string[] Tables = { "DT_AR_Fill", "DT_AR_Fill_Large", "DT_AR_Outline", "DT_AR_Outline_Large" };
    static readonly string[] Widgets = { "ArabicRoot", "ArabicForegroundBorder", "ArabicForegroundRichText",
        "ArabicShadowRetainerHorizontal", "ArabicShadowRetainerVertical", "ArabicShadowBorder", "ArabicShadowRichText" };
    static readonly string[] DepKeys = { "SerializationBeforeSerializationDependencies", "CreateBeforeSerializationDependencies",
        "SerializationBeforeCreateDependencies", "CreateBeforeCreateDependencies" };
    static readonly JsonSerializerOptions Pretty = new(JsonSerializerOptions.Default) { WriteIndented = true };
    static JsonArray Arr(JsonNode n, string k) => n[k]!.AsArray();
    static string Str(JsonNode? n) => n?.ToString() ?? "";
    static int Num(JsonNode? n) => n!.GetValue<int>();
    static JsonObject Obj(JsonNode n) => n.AsObject();
    static JsonObject Copy(JsonNode n) => n.DeepClone().AsObject();
    static JsonObject Export(JsonNode a, string name) => Arr(a, "Exports").Select(x => x!.AsObject()).Single(x => Str(x["ObjectName"]) == name);
    static int Index(JsonNode a, string name) => Arr(a, "Exports").Select((x, i) => (x, i)).Single(x => Str(x.x!["ObjectName"]) == name).i + 1;
    static JsonObject Prop(JsonNode n, string name, string field = "Data") => Arr(n, field).Select(x => x!.AsObject()).Single(x => Str(x["Name"]) == name);
    static JsonObject Child(JsonNode n, string name) => Prop(n, name, "Value");
    static JsonObject P(string type, string name, JsonNode? value) => new() {
        ["$type"] = $"UAssetAPI.PropertyTypes.Objects.{type}PropertyData, UAssetAPI", ["Name"] = name,
        ["ArrayIndex"] = 0, ["PropertyGuid"] = null, ["IsZero"] = false, ["PropertyTagFlags"] = "None",
        ["PropertyTypeName"] = null, ["PropertyTagExtensions"] = "NoExtension", ["Value"] = value };
    static JsonObject Ref(string name, int value) => P("Object", name, JsonValue.Create(value));
    static JsonObject S(string name, string type, params JsonNode[] fields) {
        var p = P("Struct", name, new JsonArray(fields));
        p["$type"] = "UAssetAPI.PropertyTypes.Structs.StructPropertyData, UAssetAPI";
        p["StructType"] = type; p["SerializeNone"] = true; p["StructGUID"] = "{00000000-0000-0000-0000-000000000000}";
        p["SerializationControl"] = "NoExtension"; p["Operation"] = "None"; return p;
    }
    static JsonObject Color(string name, float blue) {
        var leaf = P("LinearColor", name, new JsonObject { ["$type"] = "UAssetAPI.UnrealTypes.FLinearColor, UAssetAPI",
            ["R"] = 1f, ["G"] = 1f, ["B"] = blue, ["A"] = 1f });
        leaf["$type"] = "UAssetAPI.PropertyTypes.Structs.LinearColorPropertyData, UAssetAPI";
        return S(name, "LinearColor", leaf);
    }
    static JsonObject Slots(params int[] indices) {
        var p = P("Array", "Slots", new JsonArray(indices.Select((i, k) => (JsonNode)Ref(k.ToString(), i)).ToArray()));
        p["ArrayType"] = "ObjectProperty"; return p;
    }
    static JsonObject Visibility() {
        var p = P("Enum", "Visibility", JsonValue.Create("ESlateVisibility::Collapsed"));
        p["EnumType"] = "ESlateVisibility"; p["InnerType"] = null; return p;
    }
    static void Set(JsonNode e, JsonObject p) {
        var data = Arr(e, "Data"); int i = data.Select((x, k) => (x, k)).Where(x => Str(x.x!["Name"]) == Str(p["Name"]))
            .Select(x => x.k).DefaultIfEmpty(-1).Single();
        if (i < 0) data.Add(p); else data[i] = p;
    }
    static void Deps(JsonNode e, string key, params int[] values) => e[key] = new JsonArray(values.Distinct().Select(i => (JsonNode)JsonValue.Create(i)!).ToArray());
    static void AddDep(JsonNode e, string key, int value) { if (!Arr(e, key).Any(x => Num(x) == value)) Arr(e, key).Add(value); }
    static void Require(bool condition, string error) { if (!condition) throw new InvalidDataException(error); }
    static string Hash(byte[] b) => Convert.ToHexString(SHA256.HashData(b));
    static string HashFile(string p) => Hash(File.ReadAllBytes(p));
    static string HashNode(JsonNode? n) => Hash(Encoding.UTF8.GetBytes(n?.ToJsonString() ?? "null"));
    static UAsset Read(string p) => new(p, EngineVersion.VER_UE4_27);
    static JsonObject Model(UAsset a) => JsonNode.Parse(a.SerializeJson(false))!.AsObject();
    static string Source(string root, string name) => Path.Combine(root, SourceDir, name + ".uasset");
    static string Target(string dir, string name) => Path.Combine(dir, name == Wbp ? "" : "Dispatch/Content/ArabicReveal", name + ".uasset");
    static void SaveJson(string path, JsonNode n) => File.WriteAllText(path, n.ToJsonString(Pretty) + "\n", new UTF8Encoding(false));

    // Import identity is the complete tuple, not just the leaf object name.
    static int Import(JsonNode a, string name, string package, string className, string classPackage) {
        int outer = 0;
        if (package != "") outer = Import(a, package, "", "Package", "/Script/CoreUObject");
        var imports = Arr(a, "Imports");
        for (int i = 0; i < imports.Count; i++) {
            var x = imports[i]!;
            if (Str(x["ObjectName"]) == name && Num(x["OuterIndex"]) == outer && Str(x["ClassName"]) == className && Str(x["ClassPackage"]) == classPackage) return -i - 1;
        }
        imports.Add(new JsonObject { ["$type"] = "UAssetAPI.Import, UAssetAPI", ["ObjectName"] = name, ["OuterIndex"] = outer,
            ["ClassPackage"] = classPackage, ["ClassName"] = className, ["PackageName"] = null, ["bImportOptional"] = false });
        return -imports.Count;
    }
    static int Class(JsonNode a, string name) => Import(a, name, "/Script/UMG", "Class", "/Script/CoreUObject");
    static int Cdo(JsonNode a, string name) => Import(a, "Default__" + name, "/Script/UMG", name, "/Script/UMG");
    static int TableImport(JsonNode a, string name) => Import(a, name, "/Game/ArabicReveal/" + name, "DataTable", "/Script/Engine");

    static void Names(JsonObject a) {
        // Complete FNames before deserialization, keeping the original prefix untouched.
        var map = Arr(a, "NameMap"); var seen = map.Select(Str).ToHashSet();
        void Add(string s) {
            if (s == "" || int.TryParse(s, out _)) return; // array element labels are not serialized FNames
            int underscore = s.LastIndexOf('_');
            if (underscore > 0 && uint.TryParse(s[(underscore + 1)..], out _) && seen.Contains(s[..underscore])) return;
            if (seen.Add(s)) map.Add(s);
        }
        void Visit(JsonNode? n) {
            if (n is JsonObject o) {
                foreach (var (key, value) in o.ToArray()) {
                    if (value is JsonValue && key is "Name" or "ObjectName" or "ClassPackage" or "ClassName" or "StructType" or "ArrayType" or "EnumType" or "EnumValue" or "SerializedType" or "RepNotifyFunc") Add(Str(value));
                    if (key == "Value" && value is JsonValue && (Str(o["$type"]).Contains("NamePropertyData") || Str(o["$type"]).Contains("EnumPropertyData"))) Add(Str(value));
                    Visit(value);
                }
            } else if (n is JsonArray xs) foreach (var x in xs) Visit(x);
        }
        Visit(a["Imports"]); Visit(a["Exports"]);
        a["NamesReferencedFromExportDataCount"] = map.Count;
        foreach (var g in Arr(a, "Generations")) { g!["ExportCount"] = Arr(a, "Exports").Count; g["NameCount"] = map.Count; }
    }

    static JsonObject MakeTable(JsonObject source, string name, JsonArray? changes = null) {
        var a = Copy(source); var e = Arr(a, "Exports").Single()!;
        bool large = name.EndsWith("_Large"), outline = name.Contains("Outline");
        string style = "Default" + (outline ? "_Outline" : "") + (large ? "_Large" : "");
        var template = Arr(e["Table"]!, "Data").Single(x => Str(x!["Name"]) == style)!;
        var rows = new JsonArray();
        for (int k = -1; k < 37; k++) {
            int unit = Math.Max(k, 0); float b = (float)Math.Pow(10.5, -unit);
            var row = Copy(template); row["Name"] = k < 0 ? "Default" : "u" + k;
            var text = Child(row, "TextStyle");
            var color = Child(Child(text, "ColorAndOpacity"), "SpecifiedColor")["Value"]![0]!["Value"]!;
            var old = color.DeepClone(); color["R"] = 1f; color["G"] = 1f; color["B"] = b; color["A"] = 1f;
            changes?.Add(new JsonObject { ["table"] = name, ["row"] = row["Name"]!.DeepClone(), ["templateRow"] = style,
                ["field"] = "TextStyle.ColorAndOpacity.SpecifiedColor", ["before"] = old, ["after"] = color.DeepClone() });
            if (outline) {
                var oc = Child(Child(Child(text, "Font"), "OutlineSettings"), "OutlineColor")["Value"]![0]!["Value"]!;
                var before = oc.DeepClone(); oc["R"] = 1f; oc["G"] = 1f; oc["B"] = b; oc["A"] = 1f;
                changes?.Add(new JsonObject { ["table"] = name, ["row"] = row["Name"]!.DeepClone(), ["templateRow"] = style,
                    ["field"] = "TextStyle.Font.OutlineSettings.OutlineColor", ["before"] = before, ["after"] = oc.DeepClone() });
            }
            rows.Add(row);
        }
        e["Table"]!["Data"] = rows; e["ObjectName"] = name;
        // Replace the asset's own package name only; font/material/script imports stay untouched.
        var map = Arr(a, "NameMap");
        for (int i = 0; i < map.Count; i++) {
            if (Str(map[i]) == SourceTable) map[i] = name;
            else if (Str(map[i]) == "/Game/Shared/Core/Widgets/" + SourceTable) map[i] = "/Game/ArabicReveal/" + name;
        }
        a["PackageGuid"] = GuidFrom(name);
        Names(a); return a;
    }
    static string GuidFrom(string s) => "{" + new Guid(SHA256.HashData(Encoding.UTF8.GetBytes("Dispatch_AR:stage1:" + s)).AsSpan(0, 16)).ToString().ToUpperInvariant() + "}";

    static JsonObject MakeWbp(JsonObject source) {
        var a = Copy(source); var exports = Arr(a, "Exports");
        int tree = Index(a, "WidgetTree"), parent = Index(a, "Overlay_0");
        var cls = Export(a, "WBP_SubtitleBlock_C"); var cdo = Export(a, "Default__WBP_SubtitleBlock_C");
        var referenceField = Arr(cls, "LoadedProperties").Single(x => Str(x!["Name"]) == "SubtitleProtoText")!;
        var overlay = Export(a, "SubtitleOverlay"); var retH = Export(a, "RetainerBox_Horiz"); var retV = Export(a, "RetainerBox_Vert");
        var baseText = Export(a, "SubtitleProtoText");
        var indices = Widgets.Select((s, k) => (s, i: exports.Count + k + 1)).ToDictionary(x => x.s, x => x.i);
        string[] classes = { "Overlay", "Border", "RichTextBlock", "RetainerBox", "RetainerBox", "Border", "RichTextBlock" };
        for (int k = 0; k < Widgets.Length; k++) {
            string name = Widgets[k], type = classes[k];
            JsonObject e = Copy(type == "RetainerBox" ? (k == 3 ? retH : retV) : overlay);
            e["ObjectName"] = name; e["ClassIndex"] = Class(a, type); e["TemplateIndex"] = Cdo(a, type); e["OuterIndex"] = tree;
            e["Data"] = new JsonArray(P("Bool", "bIsVariable", JsonValue.Create(true)), Visibility());
            if (type == "RetainerBox") foreach (var p in Arr(k == 3 ? retH : retV, "Data"))
                if (Str(p!["Name"]) is "RenderOnInvalidation" or "RenderOnPhase" or "EffectMaterial" or "RenderTransform") Arr(e, "Data").Add(p.DeepClone());
            if (type == "Border") {
                Arr(e, "Data").Add(Color("ContentColorAndOpacity", 0f)); // canonical R8b t<0 sentinel; neutral R/G/A
                // A Border must not paint a background over its children.
                Arr(e, "Data").Add(S("BrushColor", "LinearColor", new JsonObject {
                    ["$type"] = "UAssetAPI.PropertyTypes.Structs.LinearColorPropertyData, UAssetAPI", ["Name"] = "BrushColor",
                    ["ArrayIndex"] = 0, ["PropertyGuid"] = null, ["IsZero"] = false, ["PropertyTagFlags"] = "None",
                    ["PropertyTypeName"] = null, ["PropertyTagExtensions"] = "NoExtension", ["Value"] = new JsonObject {
                        ["$type"] = "UAssetAPI.UnrealTypes.FLinearColor, UAssetAPI", ["R"] = 1f, ["G"] = 1f, ["B"] = 1f, ["A"] = 0f } }));
                Arr(e, "Data").Add(S("Padding", "Margin", new[] { "Left", "Top", "Right", "Bottom" }.Select(s => (JsonNode)P("Float", s, JsonValue.Create(0f))).ToArray()));
            }
            if (type == "RichTextBlock") {
                Arr(e, "Data").Add(Ref("TextStyleSet", TableImport(a, Tables[0])));
                foreach (string field in new[] { "Text", "Justification", "WrapTextAt", "Margin" }) {
                    var p = Copy(Prop(baseText, field)); if (field == "Text") p["CultureInvariantString"] = null; Arr(e, "Data").Add(p);
                }
                Arr(e, "Data").Add(S("ShapedTextOptions", "ShapedTextOptions",
                    P("Bool", "bOverride_TextShapingMethod", JsonValue.Create(true)), P("Bool", "bOverride_TextFlowDirection", JsonValue.Create(true)),
                    new JsonObject { ["$type"] = "UAssetAPI.PropertyTypes.Objects.EnumPropertyData, UAssetAPI", ["Name"] = "TextShapingMethod", ["EnumType"] = "ETextShapingMethod", ["Value"] = "ETextShapingMethod::FullShaping" },
                    new JsonObject { ["$type"] = "UAssetAPI.PropertyTypes.Objects.EnumPropertyData, UAssetAPI", ["Name"] = "TextFlowDirection", ["EnumType"] = "ETextFlowDirection", ["Value"] = "ETextFlowDirection::Auto" }));
            }
            foreach (string key in DepKeys) Deps(e, key);
            exports.Add(e); Arr(a, "DependsMap").Add(new JsonArray());
            var f = Copy(referenceField); f["Name"] = name; f["PropertyClass"] = Class(a, type); Arr(cls, "LoadedProperties").Add(f);
            // Match the source's null widget CDO defaults. Name binding during engine initialization remains runtime-unproven.
            Arr(cdo, "Data").Add(Ref(name, 0)); AddDep(cls, DepKeys[1], Class(a, type));
        }
        // DataTable handles make all four switches available without executing runtime logic in Stage 1.
        foreach (string name in Tables) {
            int ti = TableImport(a, name);
            var f = Copy(referenceField); f["Name"] = name; f["PropertyClass"] = Import(a, "DataTable", "/Script/Engine", "Class", "/Script/CoreUObject");
            f["PropertyFlags"] = "CPF_BlueprintVisible"; Arr(cls, "LoadedProperties").Add(f);
            Arr(cdo, "Data").Add(Ref(name, ti)); AddDep(cdo, DepKeys[1], ti); AddDep(cls, DepKeys[1], Num(f["PropertyClass"]));
        }
        // Shadow precedes foreground for correct overlay paint order.
        (string? parentName, string child, string slotClass)[] links = {
            (null, Widgets[0], "OverlaySlot"), (Widgets[0], Widgets[3], "OverlaySlot"), (Widgets[0], Widgets[1], "OverlaySlot"),
            (Widgets[1], Widgets[2], "BorderSlot"), (Widgets[3], Widgets[4], "PanelSlot"),
            (Widgets[4], Widgets[5], "PanelSlot"), (Widgets[5], Widgets[6], "BorderSlot") };
        foreach (var (pn, cn, sc) in links) {
            int pi = pn == null ? parent : indices[pn], ci = indices[cn]; int si = exports.Count + 1;
            var slot = Copy(Export(a, sc == "OverlaySlot" ? "OverlaySlot_1" : "PanelSlot_0", pi: false));
            slot["ObjectName"] = "ArabicSlot_" + cn; slot["ClassIndex"] = Class(a, sc); slot["TemplateIndex"] = Cdo(a, sc); slot["OuterIndex"] = pi;
            slot["Data"] = new JsonArray(Ref("Parent", pi), Ref("Content", ci));
            if (sc != "PanelSlot") foreach (string axis in new[] { "Horizontal", "Vertical" }) {
                var align = Copy(Prop(Export(a, "OverlaySlot_1"), axis + "Alignment")); align["EnumValue"] = axis == "Horizontal" ? "HAlign_Fill" : "VAlign_Fill";
                Arr(slot, "Data").Add(align);
            }
            if (sc == "BorderSlot") Arr(slot, "Data").Add(S("Padding", "Margin",
                new[] { "Left", "Top", "Right", "Bottom" }.Select(s => (JsonNode)P("Float", s, JsonValue.Create(0f))).ToArray()));
            foreach (string key in DepKeys) Deps(slot, key);
            Deps(slot, DepKeys[1], pi, ci); Deps(slot, DepKeys[2], Num(slot["ClassIndex"]), Num(slot["TemplateIndex"])); Deps(slot, DepKeys[3], pi);
            exports.Add(slot); Arr(a, "DependsMap").Add(new JsonArray());
            var pe = exports[pi - 1]!; var ce = exports[ci - 1]!;
            var existing = Arr(pe, "Data").SingleOrDefault(x => Str(x!["Name"]) == "Slots");
            if (existing == null) Set(pe, Slots(si)); else Arr(existing, "Value").Add(Ref(Arr(existing, "Value").Count.ToString(), si));
            Set(ce, Ref("Slot", si)); AddDep(pe, DepKeys[1], si);
        }
        foreach (string name in Widgets) {
            var e = Export(a, name); Deps(e, DepKeys[0]);
            Deps(e, DepKeys[1], References(e["Data"]).Where(x => x != 0).ToArray());
            Deps(e, DepKeys[2], Num(e["ClassIndex"]), Num(e["TemplateIndex"])); Deps(e, DepKeys[3], tree);
        }
        Names(a); return a;
    }
    // Two PanelSlot_0 exports exist under distinct Outers. Use the first only as a metadata template.
    static JsonObject Export(JsonNode a, string name, bool pi) => Arr(a, "Exports").First(x => Str(x!["ObjectName"]) == name)!.AsObject();

    static IEnumerable<int> References(JsonNode? n) {
        if (n is JsonObject o) {
            if (Str(o["$type"]).Contains("ObjectPropertyData") && o["Value"] is JsonValue) yield return Num(o["Value"]);
            foreach (var (k, v) in o) {
                if (v is JsonValue && k is "OuterIndex" or "ClassIndex" or "SuperIndex" or "TemplateIndex" or "PropertyClass" or "Struct" or "SuperStruct" or "ClassWithin" or "ClassGeneratedBy" or "ClassDefaultObject") yield return Num(v);
                if (v is JsonArray xs && DepKeys.Contains(k)) foreach (var x in xs) yield return Num(x);
                else foreach (int i in References(v)) yield return i;
            }
        } else if (n is JsonArray xs) foreach (var x in xs) foreach (int i in References(x)) yield return i;
    }

    static List<string> Check(JsonObject a, JsonObject baseline, bool wbp) {
        var errors = new List<string>(); void Test(bool ok, string why) { if (!ok) errors.Add(why); }
        int ne = Arr(a, "Exports").Count, ni = Arr(a, "Imports").Count;
        foreach (int i in References(a["Exports"]).Concat(References(a["Imports"]))) Test(i >= -ni && i <= ne, "invalid package index " + i);
        Test(Arr(a, "DependsMap").Count == ne, "DependsMap cardinality");
        foreach (var e in Arr(a, "Exports")) foreach (string key in DepKeys) {
            var d = Arr(e!, key).Select(Num).ToArray(); Test(d.Distinct().Count() == d.Length, "duplicate dependency"); Test(!d.Contains(0), "null dependency");
        }
        if (!wbp) {
            var table = Arr(a, "Exports").Single()!; string name = Str(table["ObjectName"]);
            var rows = Arr(table["Table"]!, "Data");
            Test(rows.Select(x => Str(x!["Name"])).SequenceEqual(new[] { "Default" }.Concat(Enumerable.Range(0, 37).Select(i => "u" + i))), "row count/names must be Default,u0..u36");
            float previous = float.PositiveInfinity;
            foreach (var row in rows.Where(x => Str(x!["Name"]) != "Default")) {
                int unit = int.Parse(Str(row!["Name"])[1..]); var style = Child(row!, "TextStyle"); var font = Child(style, "Font");
                float b = float.Parse(Str(Child(Child(style, "ColorAndOpacity"), "SpecifiedColor")["Value"]![0]!["Value"]!["B"]), System.Globalization.CultureInfo.InvariantCulture);
                Test(b > 0 && float.IsFinite(b) && b < previous && b == (float)Math.Pow(10.5, -unit), "row encoding " + unit); previous = b;
                Test(Num(Child(font, "Size")["Value"]) == (name.EndsWith("_Large") ? 36 : 28), "font size");
                Test(Num(Child(Child(font, "OutlineSettings"), "OutlineSize")["Value"]) == (name.Contains("Outline") ? 2 : 0), "outline size");
            }
            // Exact expected clone catches all unrelated style/timing/material changes, not just selected fields.
            Test(JsonNode.DeepEquals(Projection(a), Projection(Normalize(MakeTable(baseline, name)))), "table differs from exact template transformation");
            return errors;
        }
        int originalCount = Arr(baseline, "Exports").Count;
        Test(ne == originalCount + 14, "new subtree export count");
        Test(Arr(a, "NameMap").Take(Arr(baseline, "NameMap").Count).Select(Str).SequenceEqual(Arr(baseline, "NameMap").Select(Str)), "original name indices changed");
        Test(JsonNode.DeepEquals(new JsonArray(Arr(a, "Imports").Take(Arr(baseline, "Imports").Count).Select(x => x!.DeepClone()).ToArray()), baseline["Imports"]), "original imports changed");
        foreach (string name in Widgets) {
            var matches = Arr(a, "Exports").Where(x => Str(x!["ObjectName"]) == name).ToArray(); Test(matches.Length == 1, "widget occurrence " + name);
            if (matches.Length == 1) Test(Str(Prop(matches[0]!, "Visibility")["Value"]) == "ESlateVisibility::Collapsed", "Arabic widget visible " + name);
        }
        var visited = new HashSet<int>(); var active = new HashSet<int>(); var ownedSlots = new HashSet<int>();
        void Walk(int i) {
            if (i < 1 || i > ne) { errors.Add("dangling widget " + i); return; }
            if (!active.Add(i)) { errors.Add("widget cycle " + i); return; }
            if (!visited.Add(i)) { errors.Add("duplicate widget ownership " + i); active.Remove(i); return; }
            var widget = Arr(a, "Exports")[i - 1]!;
            var slots = Arr(widget, "Data").SingleOrDefault(x => Str(x!["Name"]) == "Slots");
            if (slots != null) foreach (int si in Arr(slots, "Value").Select(x => Num(x!["Value"]))) {
                if (si < 1 || si > ne) { errors.Add("dangling slot " + si); continue; }
                Test(ownedSlots.Add(si), "duplicate slot ownership " + si); var slot = Arr(a, "Exports")[si - 1]!;
                Test(Num(slot["OuterIndex"]) == i && Num(Prop(slot, "Parent")["Value"]) == i, "slot parent/Outer mismatch " + si);
                int ci = Num(Prop(slot, "Content")["Value"]);
                if (ci < 1 || ci > ne) { errors.Add("dangling content " + ci); continue; }
                var child = Arr(a, "Exports")[ci - 1]!;
                Test(Num(Prop(child, "Slot")["Value"]) == si, "child slot reciprocal mismatch " + ci); Walk(ci);
            }
            active.Remove(i);
        }
        Walk(Num(Prop(Export(a, "WidgetTree"), "RootWidget")["Value"]));
        foreach (string name in Widgets) if (Arr(a, "Exports").Count(x => Str(x!["ObjectName"]) == name) == 1) Test(visited.Contains(Index(a, name)), "unreachable widget " + name);
        Test(ownedSlots.Count == 13 && visited.Count == 14, "reachable widget/slot count");
        // Exact schema comparison also validates field flags/types/CDO defaults, table handles, hierarchy and all dependency arrays.
        var expected = Normalize(MakeWbp(baseline));
        Test(JsonNode.DeepEquals(Projection(a), Projection(expected)), "WBP differs from exact Stage1 schema (including bytecode/dependencies)");
        foreach (var e in Arr(baseline, "Exports").Where(x => x!["ScriptBytecode"] != null)) {
            string name = Str(e!["ObjectName"]); Test(JsonNode.DeepEquals(e["ScriptBytecode"], Export(a, name)["ScriptBytecode"]), "original bytecode changed " + name);
            Test(JsonNode.DeepEquals(e["ScriptBytecodeRaw"], Export(a, name)["ScriptBytecodeRaw"]), "original raw bytecode changed " + name);
        }
        DependencyCycles(a, errors);
        return errors;
    }

    static void DependencyCycles(JsonNode a, List<string> errors) {
        int count = Arr(a, "Exports").Count; var edges = Enumerable.Range(0, count * 2).Select(_ => new HashSet<int>()).ToArray();
        for (int i = 1; i <= count; i++) {
            int c = 2 * (i - 1), s = c + 1; edges[s].Add(c);
            for (int k = 0; k < 4; k++) foreach (int d in Arr(Arr(a, "Exports")[i - 1]!, DepKeys[k]).Select(Num).Where(x => x > 0 && x <= count))
                edges[k < 2 ? s : c].Add(2 * (d - 1) + (k is 0 or 2 ? 1 : 0));
        }
        var state = new int[count * 2];
        bool Visit(int n) { if (state[n] == 1) return false; if (state[n] == 2) return true; state[n] = 1;
            foreach (int d in edges[n]) if (!Visit(d)) return false; state[n] = 2; return true; }
        if (Enumerable.Range(0, edges.Length).Any(n => !Visit(n))) errors.Add("EDL create/serialize dependency cycle");
    }

    static JsonObject Projection(JsonObject a) {
        var p = Copy(a);
        foreach (var e in Arr(p, "Exports")) { e!["SerialOffset"] = 0; e["SerialSize"] = 0; }
        // These are package layout offsets regenerated by UAssetAPI; not semantic data.
        foreach (string key in new[] { "AssetRegistryDependencyDataOffset", "SoftObjectPathsOffset", "SearchableNamesOffset", "ThumbnailTableOffset", "ImportTypeHierarchiesOffset", "PayloadTocOffset", "DataResourceOffset" }) p[key] = 0;
        // The JSON bridge materializes null optional FPackageIndex fields as index 0.
        // UE4.27 omits these legacy fields. Binary export equality is checked separately.
        void OptionalIndices(JsonNode? n) {
            if (n is JsonObject o) foreach (var (k, v) in o.ToArray()) {
                if (k is "Next" or "ArrayInnerProp" or "StringTableAsset" && v is JsonValue && Num(v) == 0) o[k] = null;
                else OptionalIndices(v);
            } else if (n is JsonArray xs) foreach (var x in xs) OptionalIndices(x);
        }
        OptionalIndices(p);
        return p;
    }
    static JsonObject Normalize(JsonObject a) => Model(UAsset.DeserializeJson(a.ToJsonString()));

    static void WritePackage(JsonObject model, string path) {
        Require(!File.Exists(path) && !File.Exists(Path.ChangeExtension(path, ".uexp")), "Refusing existing output " + path);
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        var a = UAsset.DeserializeJson(model.ToJsonString());
        SaveJson(Path.ChangeExtension(path, ".schema.json"), Model(a)); a.Write(path);
        var reread = Read(path); Require(reread.VerifyBinaryEquality(), "binary reread roundtrip failed " + path);
        SaveJson(Path.ChangeExtension(path, ".json"), Model(reread));
    }

    static JsonArray ValidateFiles(string root, string dir, JsonObject source, JsonObject table) {
        var result = new JsonArray();
        foreach (string name in Tables.Concat(new[] { Wbp })) {
            string path = Target(dir, name); var asset = Read(path); var a = Model(asset);
            var errors = Check(a, name == Wbp ? source : table, name == Wbp);
            Require(asset.VerifyBinaryEquality(), "roundtrip " + name);
            Require(errors.Count == 0, name + ": " + string.Join("; ", errors.Take(12)));
            result.Add(new JsonObject { ["asset"] = name, ["errors"] = 0, ["roundtripBinaryEqual"] = true,
                ["uasset_sha256"] = HashFile(path), ["uexp_sha256"] = HashFile(Path.ChangeExtension(path, ".uexp")) });
        }
        return result;
    }

    public static int Validate(string rootPath, string directory) {
        try {
            string root = Path.GetFullPath(rootPath), dir = Path.GetFullPath(directory);
            var manifest = JsonNode.Parse(File.ReadAllText(Path.Combine(dir, "stage1_verification.json")))!;
            Require(Str(manifest["status"]) == "R8B_WBP_STAGE1_PASS", "missing Stage1 pass manifest");
            foreach (var entry in Arr(manifest, "sourceHashes"))
                Require(HashFile(Path.Combine(root, Str(entry!["path"]))) == Str(entry["sha256"]), "protected source hash mismatch");
            var source = Model(Read(Source(root, SourceWbp))); var table = Model(Read(Source(root, SourceTable)));
            var result = ValidateFiles(root, dir, source, table);
            var original = OriginalDiff(Source(root, SourceWbp), Target(dir, Wbp), source);
            var negative = NegativeTests(Model(Read(Target(dir, Wbp))), Model(Read(Target(dir, Tables[0]))), source, table);
            foreach (string name in Tables.Concat(new[] { Wbp })) foreach (string ext in new[] { ".uasset", ".uexp" }) {
                var bytes = File.ReadAllBytes(Path.ChangeExtension(Target(dir, name), ext));
                Require(bytes.SequenceEqual(File.ReadAllBytes(Path.ChangeExtension(Target(Path.Combine(dir, "determinism"), name), ext))), "determinism evidence mismatch " + name);
                Require(bytes.SequenceEqual(File.ReadAllBytes(Path.ChangeExtension(Target(Path.Combine(dir, "roundtrip"), name), ext))), "roundtrip evidence mismatch " + name);
            }
            Console.WriteLine(new JsonObject { ["status"] = "STAGE1_OFFLINE_VALIDATION_PASS", ["assets"] = result,
                ["negativeTests"] = negative, ["originalExports"] = original, ["determinismEvidenceMatches"] = true }.ToJsonString(Pretty));
            return 0;
        } catch (Exception ex) { Console.Error.WriteLine(ex.ToString()); return 1; }
    }

    static JsonArray OriginalDiff(string sourcePath, string generatedPath, JsonObject baseline) {
        var original = Read(sourcePath); var current = Read(generatedPath); var actual = Model(current); var expected = Normalize(MakeWbp(baseline));
        byte[] oldBytes = File.ReadAllBytes(sourcePath).Concat(File.ReadAllBytes(Path.ChangeExtension(sourcePath, ".uexp"))).ToArray();
        byte[] newBytes = File.ReadAllBytes(generatedPath).Concat(File.ReadAllBytes(Path.ChangeExtension(generatedPath, ".uexp"))).ToArray();
        var report = new JsonArray();
        for (int k = 0; k < original.Exports.Count; k++) {
            var o = original.Exports[k]; var n = current.Exports[k];
            byte[] ob = oldBytes.AsSpan((int)o.SerialOffset, (int)o.SerialSize).ToArray(), nb = newBytes.AsSpan((int)n.SerialOffset, (int)n.SerialSize).ToArray();
            string name = o.ObjectName.ToString(); bool identical = ob.SequenceEqual(nb);
            bool allowed = name is "Overlay_0" or "WBP_SubtitleBlock_C" or "Default__WBP_SubtitleBlock_C";
            bool schema = JsonNode.DeepEquals(Projection(actual)["Exports"]![k], Projection(expected)["Exports"]![k]);
            Require(identical || (allowed && schema), "UNEXPECTED_CHANGE export " + name);
            var e = new JsonObject { ["index"] = k + 1, ["name"] = name, ["classification"] = identical ? "BYTE_IDENTICAL" : "EXPECTED_STRUCTURAL_CHANGE",
                ["originalPayloadSha256"] = Hash(ob), ["generatedPayloadSha256"] = Hash(nb) };
            if (baseline["Exports"]![k]!["ScriptBytecode"] != null) {
                string oldScript = HashNode(baseline["Exports"]![k]!["ScriptBytecode"]), newScript = HashNode(actual["Exports"]![k]!["ScriptBytecode"]);
                Require(oldScript == newScript, "bytecode semantic hash changed " + name);
                Require(identical || name == "WBP_SubtitleBlock_C", "function serialized bytes changed " + name);
                e["originalBytecodeJsonSha256"] = oldScript; e["generatedBytecodeJsonSha256"] = newScript;
                e["wholeFunctionPayloadIdentical"] = identical;
            }
            if (o is FunctionExport of && n is FunctionExport nf) {
                byte[] oldCode = Bytecode(original, of, out _), newCode = Bytecode(current, nf, out _);
                Require(oldCode.SequenceEqual(newCode), "raw bytecode changed " + name);
                Require(oldCode.Length == 0 || ob.AsSpan().IndexOf(oldCode) >= 0, "original serialized script not found in export " + name);
                Require(newCode.Length == 0 || nb.AsSpan().IndexOf(newCode) >= 0, "generated serialized script not found in export " + name);
                e["originalBytecodeSha256"] = Hash(oldCode); e["generatedBytecodeSha256"] = Hash(newCode); e["serializedBytecodeBytes"] = oldCode.Length;
            }
            report.Add(e);
        }
        return report;
    }

    static byte[] Bytecode(UAsset asset, StructExport e, out JsonArray instructions) {
        instructions = new JsonArray();
        Require(e.ScriptBytecode != null, "opaque bytecode unsupported: " + e.ObjectName);
        using var stream = new MemoryStream(); using var writer = new AssetBinaryWriter(stream, Encoding.UTF8, true, asset);
        int logical = 0, index = 0;
        foreach (var instruction in e.ScriptBytecode!) {
            long start = stream.Position; int size = ExpressionSerializer.WriteExpression(instruction, writer);
            instructions.Add(new JsonObject { ["instruction"] = index++, ["logicalOffset"] = logical, ["logicalSize"] = size,
                ["serializedOffset"] = start, ["serializedSize"] = stream.Position - start, ["opcode"] = instruction.GetType().Name });
            logical += size;
        }
        writer.Flush(); return stream.ToArray();
    }

    static JsonArray InstructionInventory(UAsset source) {
        var result = new JsonArray();
        for (int k = 0; k < source.Exports.Count; k++) if (source.Exports[k] is FunctionExport f) {
            byte[] bytes = Bytecode(source, f, out var instructions);
            result.Add(new JsonObject { ["export"] = k + 1, ["function"] = f.ObjectName.ToString(), ["bytecodeSha256"] = Hash(bytes), ["instructions"] = instructions });
        }
        return result;
    }

    static JsonArray NegativeTests(JsonObject goodWbp, JsonObject goodTable, JsonObject source, JsonObject table) {
        var results = new JsonArray();
        void Run(string name, bool wbp, Action<JsonObject> mutate, string expected) {
            var bad = Copy(wbp ? goodWbp : goodTable); mutate(bad); List<string> errors;
            try { errors = Check(bad, wbp ? source : table, wbp); }
            catch (Exception ex) { errors = new() { "malformed schema: " + ex.GetType().Name }; }
            Require(errors.Count > 0 && errors.Any(e => e.Contains(expected)), "Negative fixture missed intended invariant: " + name + " / " + string.Join(";", errors));
            results.Add(new JsonObject { ["fixture"] = name, ["detected"] = true, ["diagnostics"] = new JsonArray(errors.Take(8).Select(e => (JsonNode)JsonValue.Create(e)!).ToArray()) });
        }
        Run("missing Border child slot", true, a => Arr(Prop(Export(a, Widgets[1]), "Slots"), "Value").Clear(), "count");
        Run("wrong parent", true, a => Prop(Export(a, "ArabicSlot_" + Widgets[2]), "Parent")["Value"] = Index(a, Widgets[5]), "parent");
        Run("duplicate widget", true, a => Arr(Prop(Export(a, Widgets[0]), "Slots"), "Value").Add(Ref("2", Index(a, "ArabicSlot_" + Widgets[1]))), "duplicate");
        Run("invalid import", true, a => Export(a, Widgets[1])["ClassIndex"] = -9999, "invalid package index");
        Run("wrong DataTable row count", false, a => Arr(Arr(a, "Exports")[0]!["Table"]!, "Data").RemoveAt(37), "row count");
        Run("Arabic root visible", true, a => Prop(Export(a, Widgets[0]), "Visibility")["Value"] = "ESlateVisibility::Visible", "visible");
        Run("modified original bytecode", true, a => Export(a, "Set Displayed Line")["ScriptBytecode"]![0]!["$type"] = "MODIFIED", "original bytecode changed");
        Run("dangling package index", true, a => Prop(Export(a, Widgets[2]), "TextStyleSet")["Value"] = 9999, "invalid package index");
        Run("missing dependency", true, a => Arr(Export(a, Widgets[1]), DepKeys[1]).Clear(), "dependencies");
        Run("wrong BPGC type", true, a => Arr(Export(a, "WBP_SubtitleBlock_C"), "LoadedProperties").Single(x => Str(x!["Name"]) == Widgets[1])!["PropertyClass"] = -24, "schema");
        return results;
    }

    public static int Build(string rootPath, string outputDirectory) {
        try {
            string root = Path.GetFullPath(rootPath), dir = Path.GetFullPath(outputDirectory);
            string allowed = Path.GetFullPath(Path.Combine(root, "builds/rtl_poc")) + Path.DirectorySeparatorChar;
            Require(dir.StartsWith(allowed, StringComparison.OrdinalIgnoreCase), "Output must be under project builds/rtl_poc/");
            Require(!Directory.Exists(dir), "Refusing existing directory; choose a fresh run directory.");
            var paths = new[] { Source(root, SourceWbp), Source(root, SourceTable), Source(root, SourceTable + "_Large") };
            var protectedPaths = paths.SelectMany(p => new[] { p, Path.ChangeExtension(p, ".uexp") }).ToArray();
            var before = protectedPaths.Select(HashFile).ToArray();
            foreach (string path in paths) Require(Read(path).VerifyBinaryEquality(), "source roundtrip " + path);
            var source = Model(Read(paths[0])); var table = Model(Read(paths[1]));
            Require(Arr(source, "Exports").Count == 37 && before[0] == "5B11CA427CC9BC990000E6C4FFA147E07D305E21C15132045FF18CB927D8D8A5" && before[1] == "5CC987CF5190E3153A8B6B77E4444E3CB79FED419453175F22A80C2595FBA64F", "unsupported source WBP build");
            Directory.CreateDirectory(dir); SaveJson(Path.Combine(dir, "original_wbp_baseline.json"), source);
            SaveJson(Path.Combine(dir, "stage2_instruction_inventory.json"), InstructionInventory(Read(paths[0])));
            var changes = new JsonArray();
            foreach (string name in Tables) WritePackage(MakeTable(table, name, changes), Target(dir, name));
            WritePackage(MakeWbp(source), Target(dir, Wbp));
            SaveJson(Path.Combine(dir, "table_intentional_changes.json"), changes);
            var validation = ValidateFiles(root, dir, source, table);
            string repeat = Path.Combine(dir, "determinism"), roundtrip = Path.Combine(dir, "roundtrip");
            var determinism = new JsonArray();
            foreach (string name in Tables.Concat(new[] { Wbp })) {
                WritePackage(name == Wbp ? MakeWbp(source) : MakeTable(table, name), Target(repeat, name));
                string first = Target(dir, name), second = Target(repeat, name), third = Target(roundtrip, name);
                Directory.CreateDirectory(Path.GetDirectoryName(third)!); Read(first).Write(third);
                foreach (string ext in new[] { ".uasset", ".uexp" }) {
                    Require(File.ReadAllBytes(Path.ChangeExtension(first, ext)).SequenceEqual(File.ReadAllBytes(Path.ChangeExtension(second, ext))), "nondeterministic generation " + name + ext);
                    Require(File.ReadAllBytes(Path.ChangeExtension(first, ext)).SequenceEqual(File.ReadAllBytes(Path.ChangeExtension(third, ext))), "roundtrip bytes changed " + name + ext);
                }
                determinism.Add(new JsonObject { ["asset"] = name, ["doubleGenerationByteEqual"] = true, ["rereadSerializeByteEqual"] = true });
            }
            var diff = OriginalDiff(paths[0], Target(dir, Wbp), source);
            var negative = NegativeTests(Model(Read(Target(dir, Wbp))), Model(Read(Target(dir, Tables[0]))), source, table);
            Require(before.SequenceEqual(protectedPaths.Select(HashFile)), "protected extracted source changed");
            var result = new JsonObject { ["status"] = "R8B_WBP_STAGE1_PASS", ["labels"] = new JsonArray("STAGE1", "OFFLINE", "NOT_INSTALLABLE", "NOT_RUNTIME_TESTED"),
                ["validation"] = validation, ["originalExportDiff"] = diff, ["unexpectedOriginalExportChanges"] = 0,
                ["negativeTests"] = negative, ["determinism"] = determinism, ["sourceHashesUnchanged"] = true,
                ["sourceHashes"] = new JsonArray(protectedPaths.Select((p, i) => (JsonNode)new JsonObject { ["path"] = Path.GetRelativePath(root, p), ["sha256"] = before[i] }).ToArray()),
                ["ENGLISH_BYTECODE_UNCHANGED"] = true, ["DISPATCH_INTEGRATION_PROVEN"] = false, ["IN_GAME_RTL_PROVEN"] = false, ["tested_in_game"] = 0, ["final"] = 0 };
            SaveJson(Path.Combine(dir, "stage1_verification.json"), result);
            File.WriteAllText(Path.Combine(dir, "NOT_INSTALLABLE.txt"), "STAGE1 OFFLINE NOT_INSTALLABLE NOT_RUNTIME_TESTED\nDo not pack or install. Stage2 runtime routing is absent. Arabic layer defaults Collapsed.\n");
            Console.WriteLine("R8B_WBP_STAGE1_PASS: four tables, 14 new exports, exact source/function preservation, deterministic binaries, " + negative.Count + " negative tests. " + dir);
            return 0;
        } catch (Exception ex) { Console.Error.WriteLine(ex.ToString()); return 1; }
    }
}
