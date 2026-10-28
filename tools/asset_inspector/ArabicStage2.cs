using System.Reflection;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json.Nodes;
using UAssetAPI;
using UAssetAPI.ExportTypes;
using UAssetAPI.Kismet.Bytecode;

// Shares the existing inspector's package/schema helpers; Stage1 generation is not rerun.
static partial class ArabicStage1
{
    const string Wbp2 = "WBP_SubtitleBlock_AR_STAGE2";
    static readonly string[] Helpers2 = { "Format As Arabic Plain", "AR Escape", "AR Is Separator", "AR Is Letter Code", "Build Arabic Markup", "Set Threshold Arabic" };
    static readonly string[] States2 = { "bArabic", "bArabicActive", "bArabicProtoSuppressed", "ArabicThreshold", "ArabicUnitCount", "ArabicSpeakerUnits" };
    static string Stage1Path(string root) => Path.Combine(root, "builds/rtl_poc/stage1", Wbp + ".uasset");
    static string Stage2Path(string dir) => Path.Combine(dir, Wbp2 + ".uasset");
    static JsonObject X(string op, params (string Key, JsonNode? Value)[] fields) {
        var x = new JsonObject { ["$type"] = "UAssetAPI.Kismet.Bytecode.Expressions.EX_" + op + ", UAssetAPI" };
        foreach (var (k, v) in fields) x[k] = v; return x;
    }
    static JsonNode V(int n) => JsonValue.Create(n)!;
    static JsonNode V(string s) => JsonValue.Create(s)!;
    static JsonObject IC(int n) => X("IntConst", ("Value", V(n)));
    static JsonObject FC(float n) => X("FloatConst", ("Value", JsonValue.Create(n)));
    static JsonObject SC(string s) => X(s.Any(c => c > 127) ? "UnicodeStringConst" : "StringConst", ("Value", V(s)));
    static JsonObject BC(bool b) => X(b ? "True" : "False");
    static JsonObject OC(int n) => X("ObjectConst", ("Value", V(n)));
    static JsonObject Ptr(int owner, string? name) => new() { ["$type"] = "UAssetAPI.Kismet.Bytecode.KismetPropertyPointer, UAssetAPI",
        ["New"] = new JsonObject { ["$type"] = "UAssetAPI.UnrealTypes.FFieldPath, UAssetAPI", ["Path"] = name == null ? new JsonArray() : new JsonArray(name), ["ResolvedOwner"] = owner } };
    static JsonObject Var2(int owner, string name, bool instance = false, bool output = false) => X(instance ? "InstanceVariable" : output ? "LocalOutVariable" : "LocalVariable", ("Variable", Ptr(owner, name)));
    static JsonObject Assign2(int owner, string name, JsonObject value, string type = "Str", bool instance = false) {
        if (type == "Bool" || type == "Object") return X(type == "Bool" ? "LetBool" : "LetObj", ("VariableExpression", Var2(owner, name, instance)), ("AssignmentExpression", value));
        return X("Let", ("Value", Ptr(owner, name)), ("Variable", Var2(owner, name, instance)), ("Expression", value));
    }
    static JsonObject Call2(int index, params JsonNode[] args) => X(index < 0 ? "CallMath" : "LocalFinalFunction", ("StackNode", V(index)), ("Parameters", new JsonArray(args)));
    static JsonObject Return2(JsonObject? value = null) => X("Return", ("ReturnExpression", value ?? X("Nothing")));
    static JsonObject Context2(JsonObject target, JsonObject body, JsonObject? resultPointer = null) => X("Context", ("ObjectExpression", target),
        ("Offset", V(0)), ("PropertyType", V(0)), ("RValuePointer", resultPointer ?? Ptr(0, null)), ("ContextExpression", body));
    static JsonObject Method2(string widget, int function, params JsonNode[] args) => Context2(Var2(22, widget, true),
        X("FinalFunction", ("StackNode", V(function)), ("Parameters", new JsonArray(args))));
    static JsonObject Visible2(string widget, int visibility) => Context2(Var2(22, widget, true),
        X("VirtualFunction", ("VirtualFunctionName", V("SetVisibility")), ("Parameters", new JsonArray(X("ByteConst", ("Value", V(visibility)))))));

    sealed class Cell2 {
        public required string Label;
        public required JsonObject Code;
        public int? OriginalIndex;
        public bool English;
    }
    sealed class Asm2 {
        public int ExportIndex;
        public int? SourceExportIndex;
        public readonly List<Cell2> Cells = new();
        public readonly List<(JsonObject Node, string Field, string Label)> Fixups = new();
        public readonly Dictionary<string, int> Marks = new();
        public JsonArray? Original;
        public void Mark(string name) { Require(!Marks.ContainsKey(name), "duplicate assembler label " + name); Marks.Add(name, Cells.Count); }
        public void Emit(JsonObject x, string? label = null) => Cells.Add(new Cell2 { Label = label ?? "new_" + Cells.Count, Code = x });
        public void Old(int i, bool english = true) { var x = Copy(Original![i]!); Cells.Add(new Cell2 { Label = (english ? "old_" : "ar_old_") + i, Code = x, OriginalIndex = i, English = english }); }
        public void Jump(string label, JsonObject? condition = null) {
            var x = condition == null ? X("Jump", ("CodeOffset", V(0))) : X("JumpIfNot", ("CodeOffset", V(0)), ("BooleanExpression", condition));
            Fixups.Add((x, "CodeOffset", label)); Emit(x);
        }
    }
    sealed class Build2Context {
        public readonly JsonObject Asset;
        public readonly List<Asm2> Plans = new();
        public readonly Dictionary<string, int> Functions = new();
        public readonly Dictionary<string, int> Native = new();
        public Build2Context(JsonObject baseline) { Asset = Copy(baseline); }
        public int N(string cls, string name) {
            string id = cls + "." + name;
            if (Native.TryGetValue(id, out int value)) return value;
            int owner = Import(Asset, cls, cls is "Border" or "RichTextBlock" or "RetainerBox" ? "/Script/UMG" : "/Script/Engine", "Class", "/Script/CoreUObject");
            return Native[id] = Import(Asset, name, "", "Function", "/Script/CoreUObject", owner);
        }
        public JsonObject C(string cls, string name, params JsonNode[] args) => Call2(N(cls, name), args);
        public JsonObject StrEq(JsonNode x, JsonNode y) => C("KismetStringLibrary", "EqualEqual_StrStr", x, y);
        public JsonObject IntEq(JsonNode x, JsonNode y) => C("KismetMathLibrary", "EqualEqual_IntInt", x, y);
        public JsonObject Less(JsonNode x, JsonNode y) => C("KismetMathLibrary", "Less_IntInt", x, y);
        public JsonObject And(JsonNode x, JsonNode y) => C("KismetMathLibrary", "BooleanAND", x, y);
        public JsonObject Or(JsonNode x, JsonNode y) => C("KismetMathLibrary", "BooleanOR", x, y);
        public JsonObject Not(JsonNode x) => C("KismetMathLibrary", "Not_PreBool", x);
        public JsonObject Cat(params JsonNode[] xs) { JsonNode value = xs[0]; foreach (var x in xs.Skip(1)) value = C("KismetStringLibrary", "Concat_StrStr", value, x); return value.AsObject(); }
        public JsonObject Add(JsonNode x, int y) => C("KismetMathLibrary", "Add_IntInt", x, IC(y));
        public JsonObject Field(string type, string name, string flags = "CPF_None") {
            var source = Arr(Export(Asset, "Format As Subtitle Text With Tags"), "LoadedProperties").First(x => Str(x!["SerializedType"]) == "StrProperty")!;
            JsonObject p;
            if (type == "Bool") p = Copy(Arr(Export(Asset, "Set Displayed Line"), "LoadedProperties").First(x => Str(x!["SerializedType"]) == "BoolProperty")!);
            else p = Copy(source);
            p["Name"] = name; p["SerializedType"] = type + "Property"; p["PropertyFlags"] = flags;
            p["ElementSize"] = type is "Int" or "Float" ? 4 : type == "Text" ? 24 : type == "Bool" ? 1 : 16;
            return p;
        }
        public void Local(int fn, string type, string name, string flags = "CPF_None") => Arr(Arr(Asset, "Exports")[fn - 1]!, "LoadedProperties").Add(Field(type, name, flags));
        public Asm2 Function(string name, string? ret, params (string Type, string Name)[] parameters) {
            int index = Functions[name]; var e = Copy(Export(Asset, "Stop Displaying Line"));
            e["ObjectName"] = name; e["LoadedProperties"] = new JsonArray(); e["ScriptBytecode"] = new JsonArray();
            e["FunctionFlags"] = "FUNC_Public, FUNC_HasDefaults, FUNC_BlueprintCallable, FUNC_BlueprintEvent" + (ret == null ? "" : ", FUNC_HasOutParms");
            Arr(Asset, "Exports")[index - 1] = e;
            foreach (var (t, n) in parameters) Local(index, t, n, "CPF_Parm");
            if (ret != null) Local(index, ret, "ReturnValue", "CPF_Parm, CPF_OutParm, CPF_ReturnParm");
            var p = new Asm2 { ExportIndex = index }; Plans.Add(p); return p;
        }
        public void State(string type, string name, JsonNode value) {
            Arr(Export(Asset, "WBP_SubtitleBlock_C"), "LoadedProperties").Add(Field(type, name, "CPF_BlueprintVisible, CPF_Transient"));
            Set(Export(Asset, "Default__WBP_SubtitleBlock_C"), P(type, name, value));
        }
    }

    // Same tuple identity as Stage1, with an explicit class Outer for function imports.
    static int Import(JsonNode a, string name, string unused, string className, string classPackage, int outer) {
        var imports = Arr(a, "Imports");
        for (int k = 0; k < imports.Count; k++) { var i = imports[k]!;
            if (Str(i["ObjectName"]) == name && Num(i["OuterIndex"]) == outer && Str(i["ClassName"]) == className && Str(i["ClassPackage"]) == classPackage) return -k - 1;
        }
        imports.Add(new JsonObject { ["$type"] = "UAssetAPI.Import, UAssetAPI", ["ObjectName"] = name, ["OuterIndex"] = outer,
            ["ClassName"] = className, ["ClassPackage"] = classPackage, ["PackageName"] = null, ["bImportOptional"] = false }); return -imports.Count;
    }

    static Build2Context Generate2(JsonObject baseline) {
        var c = new Build2Context(baseline); var a = c.Asset; var exports = Arr(a, "Exports");
        foreach (string name in Helpers2) { int id = exports.Count + 1; c.Functions[name] = id; var reserved = Copy(Export(a, "Stop Displaying Line")); reserved["ObjectName"] = name; exports.Add(reserved); Arr(a, "DependsMap").Add(new JsonArray()); }
        foreach (string name in States2) c.State(name.StartsWith("b") ? "Bool" : "Int", name, name.StartsWith("b") ? JsonValue.Create(false)! : V(name == "ArabicThreshold" ? -1 : 0));
        GenerateStringHelpers2(c); GenerateMarkup2(c); GenerateThreshold2(c); GenerateDisplayedLine2(c); GenerateStop2(c);
        var cls = Export(a, "WBP_SubtitleBlock_C");
        foreach (string name in Helpers2) { Arr(cls, "FuncMap").Add(new JsonArray(name, c.Functions[name])); Arr(cls, "Children").Add(c.Functions[name]); AddDep(cls, DepKeys[1], c.Functions[name]); }
        foreach (var p in c.Plans) Arr(a, "Exports")[p.ExportIndex - 1]!["ScriptBytecode"] = new JsonArray(p.Cells.Select(x => (JsonNode)x.Code).ToArray());
        Names(a); Assemble2(c, baseline);
        foreach (var p in c.Plans) {
            var e = Arr(a, "Exports")[p.ExportIndex - 1]!;
            var refs = ScriptReferences2(e["ScriptBytecode"]).Concat(References(e["LoadedProperties"])).Where(i => i != 0).Distinct().ToArray();
            foreach (int r in refs) if (r != 22 && r != p.ExportIndex) AddDep(e, DepKeys[1], r);
        }
        Names(a); return c;
    }

    static void GenerateStringHelpers2(Build2Context c) {
        var p = c.Function(Helpers2[0], "Str", ("Str", "string")); int f = p.ExportIndex;
        Arr(c.Asset,"Exports")[f-1]!["LoadedProperties"] = new JsonArray(Arr(Export(c.Asset,"Format As Subtitle Text With Tags"),"LoadedProperties").Take(2).Select(x=>x!.DeepClone()).ToArray());
        p.Emit(Return2(c.C("KismetStringLibrary", "Replace", c.C("KismetStringLibrary", "Replace", Var2(f, "string"), SC("<Italic>"), SC(""), X("ByteConst", ("Value", V(0)))), SC("</>"), SC(""), X("ByteConst", ("Value", V(0)))))); p.Emit(X("EndOfScript"));
        p = c.Function(Helpers2[1], "Str", ("Str", "Input")); f = p.ExportIndex; JsonObject value = Var2(f, "Input");
        foreach (var (from, to) in new[] { ("&", "&amp;"), ("<", "&lt;"), (">", "&gt;"), ("\"", "&quot;") }) value = c.C("KismetStringLibrary", "Replace", value, SC(from), SC(to), X("ByteConst", ("Value", V(0))));
        p.Emit(Return2(value)); p.Emit(X("EndOfScript"));
        p = c.Function(Helpers2[2], "Bool", ("Str", "Character")); f = p.ExportIndex;
        value = c.StrEq(Var2(f, "Character"), SC(" "));
        foreach (string s in new[] { "\t", "\n", "\r" }) value = c.Or(value, c.StrEq(Var2(f, "Character"), SC(s)));
        p.Emit(Return2(value)); p.Emit(X("EndOfScript"));
        p = c.Function(Helpers2[3], "Bool", ("Int", "Code")); f = p.ExportIndex; JsonObject? letter = null;
        foreach (var (lo, hi) in new[] { (0x41,0x5A), (0x61,0x7A), (0x620,0x64A), (0x66E,0x6D3), (0x750,0x77F), (0xFB50,0xFDFF), (0xFE70,0xFEFC) }) {
            var test = c.And(c.C("KismetMathLibrary", "GreaterEqual_IntInt", Var2(f, "Code"), IC(lo)), c.C("KismetMathLibrary", "LessEqual_IntInt", Var2(f, "Code"), IC(hi)));
            letter = letter == null ? test : c.Or(letter, test);
        }
        p.Emit(Return2(letter!)); p.Emit(X("EndOfScript"));
    }

    static void GenerateMarkup2(Build2Context c) {
        var p = c.Function(Helpers2[4], "Str", ("Str", "Content"), ("Str", "Speaker")); int f = p.ExportIndex;
        foreach (string s in new[] { "Input", "Lead", "Token", "Gap", "Pending", "PendingGap", "Output", "Character" }) c.Local(f, "Str", s);
        foreach (string s in new[] { "Phase", "Cursor", "Length", "Scan", "Count", "RawCount", "SpeakerCount" }) c.Local(f, "Int", s);
        foreach (string s in new[] { "PreviousInSegment", "HasLetter" }) c.Local(f, "Bool", s);
        JsonObject L(string n) => Var2(f, n);
        void A(string n, JsonObject value, string type = "Str") => p.Emit(Assign2(f, n, value, type));
        JsonObject Char() => c.C("KismetStringLibrary", "GetSubstring", L("Input"), L("Cursor"), IC(1));
        JsonObject Sep(JsonNode x) => Call2(c.Functions[Helpers2[2]], x);
        void Inc(string n) => A(n, c.Add(L(n), 1), "Int");
        JsonObject Tagged() => c.Cat(SC("<u"), c.C("KismetStringLibrary", "Conv_IntToString", c.C("KismetMathLibrary", "Subtract_IntInt", L("Count"), IC(1))), SC(">"), Call2(c.Functions[Helpers2[1]], L("Pending")), SC("</>"), L("PendingGap"));
        foreach (string n in new[] { "Lead", "Token", "Gap", "Pending", "PendingGap", "Output" }) A(n, SC(""));
        foreach (string n in new[] { "Count", "RawCount", "SpeakerCount", "Phase" }) A(n, IC(0), "Int");
        p.Jump("content_first", c.Not(c.StrEq(L("Speaker"), SC("")))); A("Input", c.Cat(L("Speaker"), SC(":"))); p.Jump("segment");
        p.Mark("content_first"); A("Phase", IC(1), "Int"); A("Input", L("Content"));
        p.Mark("segment"); A("Cursor", IC(0), "Int"); A("Lead", SC("")); A("PreviousInSegment", BC(false), "Bool"); A("Length", c.C("KismetStringLibrary", "Len", L("Input")), "Int");
        p.Mark("lead_loop"); p.Jump("lead_done", c.Less(L("Cursor"), L("Length"))); p.Jump("lead_done", Sep(Char())); A("Lead", c.Cat(L("Lead"), Char())); Inc("Cursor"); p.Jump("lead_loop");
        p.Mark("lead_done"); p.Jump("ignore_content_lead", c.Or(c.IntEq(L("Phase"), IC(0)), c.StrEq(L("Speaker"), SC("")))); A("Output", c.Cat(L("Output"), L("Lead")));
        p.Mark("ignore_content_lead");
        p.Mark("token_start"); p.Jump("segment_done", c.Less(L("Cursor"), L("Length"))); A("Token", SC("")); A("Gap", SC(""));
        p.Mark("token_loop"); p.Jump("gap_loop", c.Less(L("Cursor"), L("Length"))); p.Jump("token_char", Sep(Char())); p.Jump("gap_loop");
        p.Mark("token_char"); A("Token", c.Cat(L("Token"), Char())); Inc("Cursor"); p.Jump("token_loop");
        p.Mark("gap_loop"); p.Jump("classify", c.Less(L("Cursor"), L("Length"))); p.Jump("classify", Sep(Char())); A("Gap", c.Cat(L("Gap"), Char())); Inc("Cursor"); p.Jump("gap_loop");
        p.Mark("classify"); A("HasLetter", BC(false), "Bool"); A("Scan", IC(0), "Int");
        p.Mark("letter_loop"); p.Jump("classified", c.Less(L("Scan"), c.C("KismetStringLibrary", "Len", L("Token"))));
        p.Jump("letter_next", Call2(c.Functions[Helpers2[3]], c.C("KismetStringLibrary", "GetCharacterAsNumber", L("Token"), L("Scan")))); A("HasLetter", BC(true), "Bool"); p.Jump("classified");
        p.Mark("letter_next"); Inc("Scan"); p.Jump("letter_loop");
        p.Mark("classified");
        p.Jump("new_unit", c.And(c.And(c.Not(L("HasLetter")), L("PreviousInSegment")), c.Not(c.C("KismetStringLibrary", "Contains", L("PendingGap"), SC("\n"), BC(true), BC(false)))));
        A("Pending", c.Cat(L("Pending"), L("PendingGap"), L("Token"))); A("PendingGap", L("Gap")); p.Jump("token_done");
        p.Mark("new_unit"); Inc("RawCount"); p.Jump("overflow", c.Less(L("Count"), IC(37)));
        p.Jump("first_unit", c.C("KismetMathLibrary", "GreaterEqual_IntInt", L("Count"), IC(1))); A("Output", c.Cat(L("Output"), Tagged()));
        p.Mark("first_unit"); Inc("Count"); A("Pending", L("Token")); A("PendingGap", L("Gap")); p.Jump("token_done");
        p.Mark("overflow"); A("Pending", c.Cat(L("Pending"), L("PendingGap"), L("Token"))); A("PendingGap", L("Gap"));
        p.Mark("token_done"); A("PreviousInSegment", BC(true), "Bool"); p.Jump("token_start");
        p.Mark("segment_done"); p.Jump("finish", c.IntEq(L("Phase"), IC(0))); A("SpeakerCount", L("RawCount"), "Int"); A("PendingGap", SC(" ")); A("Phase", IC(1), "Int"); A("Input", L("Content")); p.Jump("segment");
        p.Mark("finish"); p.Jump("empty", c.C("KismetMathLibrary", "GreaterEqual_IntInt", L("Count"), IC(1))); A("Output", c.Cat(L("Output"), Tagged()));
        p.Mark("empty"); p.Emit(Assign2(22, "ArabicUnitCount", L("Count"), "Int", true)); p.Emit(Assign2(22, "ArabicSpeakerUnits", L("SpeakerCount"), "Int", true));
        p.Emit(Return2(L("Output"))); p.Emit(X("EndOfScript"));
    }

    static void GenerateThreshold2(Build2Context c) {
        var p = c.Function(Helpers2[5], null, ("Int", "Threshold")); int f = p.ExportIndex;
        c.Local(f, "Float", "Blue");
        p.Jump("nonnegative", c.Less(Var2(f, "Threshold"), IC(0))); p.Emit(Assign2(f, "Blue", FC(0), "Float")); p.Jump("apply");
        p.Mark("nonnegative"); p.Jump("clamped", c.C("KismetMathLibrary", "GreaterEqual_IntInt", Var2(f, "Threshold"), IC(37))); p.Emit(Assign2(f, "Threshold", IC(36), "Int"));
        p.Mark("clamped");
        // Exact float32 powers; no accumulated multiply error or engine-version pow signature guess.
        for (int i=0;i<37;i++) {
            p.Jump("power_next_"+i,c.IntEq(Var2(f,"Threshold"),IC(i)));
            p.Emit(Assign2(f,"Blue",FC((float)Math.Pow(10.5,i)),"Float")); p.Jump("apply"); p.Mark("power_next_"+i);
        }
        p.Emit(Assign2(f,"Blue",FC(0),"Float")); // unreachable after clamp; validator exhausts the domain
        p.Mark("apply"); p.Emit(Assign2(22, "ArabicThreshold", Var2(f, "Threshold"), "Int", true));
        foreach (string widget in new[] { Widgets[1], Widgets[5] }) p.Emit(Method2(widget, c.N("Border", "SetContentColorAndOpacity"),
            X("StructConst", ("Struct", V(-90)), ("StructSize", V(16)), ("Value", new JsonArray(FC(1), FC(1), Var2(f, "Blue"), FC(1))))));
        foreach (string widget in new[] { Widgets[3], Widgets[4] }) p.Emit(Method2(widget, c.N("RetainerBox", "RequestRender")));
        p.Emit(Return2()); p.Emit(X("EndOfScript"));
    }

    static void GenerateDisplayedLine2(Build2Context c) {
        var a = c.Asset; var fn = Export(a, "Set Displayed Line"); int f = Index(a, "Set Displayed Line");
        var p = new Asm2 { ExportIndex = f, Original = Arr(fn, "ScriptBytecode").DeepClone().AsArray() }; c.Plans.Add(p);
        foreach (string n in new[] { "ARLanguage", "ARPlain", "ARSpeaker", "ARMarkup" }) c.Local(f, "Str", n);
        c.Local(f, "Bool", "ARLarge"); c.Local(f, "Text", "ARText");
        var tf = Copy(Arr(Export(a, "WBP_SubtitleBlock_C"), "LoadedProperties").Single(x => Str(x!["Name"]) == Tables[0])!); tf["Name"] = "ARForegroundStyle"; tf["PropertyFlags"] = "CPF_None"; Arr(fn, "LoadedProperties").Add(tf);
        JsonObject L(string n) => Var2(f, n);
        for (int i = 2; i <= 6; i++) p.Old(i);
        p.Emit(Assign2(f, "ARLanguage", c.C("KismetInternationalizationLibrary", "GetCurrentLanguage")));
        p.Emit(Assign2(22, "bArabic", c.Or(c.StrEq(L("ARLanguage"), SC("ar")), c.C("KismetStringLibrary", "StartsWith", L("ARLanguage"), SC("ar-"), X("ByteConst", ("Value", V(0))))), "Bool", true));
        p.Jump("english", Var2(22, "bArabic", true));
        // Arabic branch owns no original execution-flow stack entries.
        var bind = Copy(p.Original[7]!); bind["FunctionName"] = Helpers2[0]; p.Emit(bind, "arabic_begin"); p.Old(8, false);
        p.Emit(Assign2(f, "ARPlain", c.C("KismetTextLibrary", "Conv_TextToString", L("CallFunc_ProcessLocalizedTextWithCallback_ReturnValue"))));
        p.Emit(Assign2(f, "ARSpeaker", SC("")));
        var speaker = Export(a, "Apply Speaker Name if Needed");
        string[] speakerNames = { "CallFunc_GetGameInstanceSubsystem_ReturnValue", "CallFunc_GetCloudSettings_ReturnValue", "CallFunc_GetOptionValue_ReturnValue" };
        foreach (string n in speakerNames) { var field = Copy(Arr(speaker, "LoadedProperties").Single(x => Str(x!["Name"]) == n)!); field["Name"] = "ARSpeaker_" + n; Arr(fn, "LoadedProperties").Add(field); }
        foreach (int i in new[] { 0, 1, 4 }) { var code = Copy(Arr(speaker, "ScriptBytecode")[i]!); Rebind2(code, 16, f, n => "ARSpeaker_" + n); p.Emit(code); }
        p.Jump("speaker_done", L("ARSpeaker_CallFunc_GetOptionValue_ReturnValue"));
        p.Emit(Assign2(f, "ARSpeaker", c.C("KismetTextLibrary", "Conv_TextToString", p.Original[9]!["Parameters"]![1]!.DeepClone())));
        p.Mark("speaker_done"); p.Emit(Assign2(f, "ARMarkup", Call2(c.Functions[Helpers2[4]], L("ARPlain"), L("ARSpeaker"))));
        var protoStyle = Context2(Var2(22, "SubtitleProtoText", true), Var2(-18, "ProtoTextStyleSet", true), Ptr(-18, "ProtoTextStyleSet"));
        p.Emit(Assign2(f, "ARLarge", c.C("KismetMathLibrary", "EqualEqual_ObjectObject", protoStyle, OC(-30)), "Bool"));
        p.Jump("fill", Var2(22, "Has Outline", true));
        p.Jump("outline_normal", L("ARLarge")); p.Emit(Assign2(f, "ARForegroundStyle", Var2(22, Tables[3], true), "Object")); p.Jump("styles");
        p.Mark("outline_normal"); p.Emit(Assign2(f, "ARForegroundStyle", Var2(22, Tables[2], true), "Object")); p.Jump("styles");
        p.Mark("fill"); p.Jump("fill_normal", L("ARLarge")); p.Emit(Assign2(f, "ARForegroundStyle", Var2(22, Tables[1], true), "Object")); p.Jump("styles");
        p.Mark("fill_normal"); p.Emit(Assign2(f, "ARForegroundStyle", Var2(22, Tables[0], true), "Object"));
        p.Mark("styles"); p.Emit(Method2(Widgets[2], c.N("RichTextBlock", "SetTextStyleSet"), L("ARForegroundStyle")));
        p.Jump("shadow_normal", L("ARLarge")); p.Emit(Method2(Widgets[6], c.N("RichTextBlock", "SetTextStyleSet"), Var2(22, Tables[1], true))); p.Jump("text_init");
        p.Mark("shadow_normal"); p.Emit(Method2(Widgets[6], c.N("RichTextBlock", "SetTextStyleSet"), Var2(22, Tables[0], true)));
        p.Mark("text_init"); p.Emit(Call2(c.Functions[Helpers2[5]], IC(-1))); p.Emit(Assign2(f, "ARText", c.C("KismetTextLibrary", "Conv_StringToText", L("ARMarkup")), "Text"));
        foreach (string w in new[] { Widgets[2], Widgets[6] }) p.Emit(Method2(w, c.N("RichTextBlock", "SetText"), L("ARText")));
        foreach (string w in new[] { "SubtitleProtoText", "RetainerBox_Horiz" }) p.Emit(Visible2(w, 1));
        p.Emit(Assign2(22, "bArabicProtoSuppressed", BC(true), "Bool", true));
        foreach (string w in Widgets) p.Emit(Visible2(w, 0));
        foreach (string w in new[] { Widgets[3], Widgets[4] }) p.Emit(Method2(w, c.N("RetainerBox", "SetRetainRendering"), c.Not(Var2(22, "Has Outline", true))));
        p.Jump("no_outline_hide", Var2(22, "Has Outline", true)); p.Emit(Visible2(Widgets[3], 2)); p.Mark("no_outline_hide");
        // Preserve the same per-line letterbox settings, with all old local owners unchanged.
        for (int i = 12; i <= 22; i++) p.Old(i, false);
        p.Emit(Assign2(22, "bArabicActive", BC(true), "Bool", true));
        p.Emit(Call2(c.Functions[Helpers2[5]], c.C("KismetMathLibrary", "Subtract_IntInt", Var2(22, "ArabicSpeakerUnits", true), IC(1))));
        p.Jump("old_36");
        p.Mark("english"); p.Jump("english_original", Var2(22, "bArabicProtoSuppressed", true));
        p.Emit(Visible2(Widgets[0], 1)); p.Emit(Visible2("SubtitleProtoText", 0)); p.Emit(Visible2("SubtitleShadowProtoText", 0));
        p.Jump("english_shadow_visible", Var2(22, "Has Outline", true)); p.Emit(Visible2("RetainerBox_Horiz", 2)); p.Jump("english_restored");
        p.Mark("english_shadow_visible"); p.Emit(Visible2("RetainerBox_Horiz", 0)); p.Mark("english_restored");
        p.Emit(Assign2(22, "bArabicProtoSuppressed", BC(false), "Bool", true)); p.Emit(Assign2(22, "bArabicActive", BC(false), "Bool", true));
        p.Mark("english_original"); p.Old(0); p.Old(1); for (int i = 7; i < p.Original.Count; i++) p.Old(i);
    }

    static void Rebind2(JsonNode? n, int oldOwner, int newOwner, Func<string,string> rename) {
        if (n is JsonObject o) {
            if (Str(o["$type"]).Contains("FFieldPath") && Num(o["ResolvedOwner"]) == oldOwner) { o["ResolvedOwner"] = newOwner; for (int i = 0; i < Arr(o,"Path").Count; i++) Arr(o,"Path")[i] = rename(Str(Arr(o,"Path")[i])); }
            foreach (var (_,v) in o.ToArray()) Rebind2(v, oldOwner, newOwner, rename);
        } else if (n is JsonArray xs) foreach (var x in xs) Rebind2(x, oldOwner, newOwner, rename);
    }
    static void GenerateStop2(Build2Context c) {
        var fn = Export(c.Asset, "Stop Displaying Line"); var p = new Asm2 { ExportIndex = 12, Original = Arr(fn,"ScriptBytecode").DeepClone().AsArray() }; c.Plans.Add(p);
        p.Old(0); p.Jump("old_1", Var2(22,"bArabicActive",true)); p.Emit(Call2(c.Functions[Helpers2[5]], IC(-1)));
        p.Emit(Visible2(Widgets[0],1)); p.Emit(Assign2(22,"bArabicActive",BC(false),"Bool",true)); p.Old(1); p.Old(2);
    }

    static int Size2(UAsset a, KismetExpression x) { using var s = new MemoryStream(); using var w = new AssetBinaryWriter(s, Encoding.UTF8, true, a); return ExpressionSerializer.WriteExpression(x,w); }
    static void TypedWalk2(object? n, string path, Dictionary<string,KismetExpression> result) {
        if (n is KismetExpression expression) {
            result[path] = expression;
            foreach (var field in n.GetType().GetFields(BindingFlags.Public|BindingFlags.Instance)) {
                var value = field.GetValue(n);
                if (value is KismetExpression) TypedWalk2(value, path+"."+field.Name, result);
                else if (value is Array xs) for (int i=0;i<xs.Length;i++) TypedWalk2(xs.GetValue(i), path+"."+field.Name+"["+i+"]", result);
                else if (value != null && value.GetType().Name == "FKismetSwitchCase") TypedWalk2(value,path+"."+field.Name,result);
            }
        } else if (n != null && n.GetType().Name == "FKismetSwitchCase") foreach(var f in n.GetType().GetFields()) TypedWalk2(f.GetValue(n),path+"."+f.Name,result);
    }
    static void JsonWalk2(JsonNode? n, string path, Action<JsonObject,string> visit) {
        if (n is JsonObject o) { visit(o,path); foreach(var (k,v) in o.ToArray()) JsonWalk2(v,path+"."+k,visit); }
        else if(n is JsonArray xs) for(int i=0;i<xs.Count;i++) JsonWalk2(xs[i],path+"["+i+"]",visit);
    }
    static void Assemble2(Build2Context c, JsonObject baseline) {
        Names(c.Asset); var typed=UAsset.DeserializeJson(c.Asset.ToJsonString()); var original=UAsset.DeserializeJson(baseline.ToJsonString());
        foreach(var p in c.Plans) {
            var expressions=((StructExport)typed.Exports[p.ExportIndex-1]).ScriptBytecode!;
            var offsets=new int[expressions.Length+1]; for(int i=0;i<expressions.Length;i++) offsets[i+1]=offsets[i]+Size2(typed,expressions[i]);
            var labels=p.Cells.Select((x,i)=>(x.Label,i)).ToDictionary(x=>x.Label,x=>offsets[x.i]); foreach(var (label,index) in p.Marks) labels.Add(label,offsets[index]);
            int[]? oldOffsets=null;
            if(p.Original!=null) { var old=((StructExport)original.Exports[(p.SourceExportIndex??p.ExportIndex)-1]).ScriptBytecode!; oldOffsets=new int[old.Length+1]; for(int i=0;i<old.Length;i++) oldOffsets[i+1]=oldOffsets[i]+Size2(original,old[i]); }
            for(int i=0;i<p.Cells.Count;i++) {
                var cell=p.Cells[i]; var typedNodes=new Dictionary<string,KismetExpression>(); TypedWalk2(expressions[i],"$",typedNodes);
                JsonWalk2(cell.Code,"$",(node,path)=> {
                    if(Str(node["$type"]).EndsWith(".EX_Context, UAssetAPI")) {
                        Require(typedNodes.ContainsKey(path+".ContextExpression"),"Context measurement path "+path);
                        node["Offset"]=Size2(typed,typedNodes[path+".ContextExpression"]);
                    }
                    if(cell.OriginalIndex is int oi) foreach(string k in new[]{"CodeOffset","PushingAddress","EndGotoOffset","NextOffset","SkipOffset"}) if(node[k] is JsonValue) {
                        int old=Num(node[k]);
                        if(old>=oldOffsets![oi] && old<=oldOffsets[oi+1]) node[k]=offsets[i]+old-oldOffsets[oi];
                        else { int target=Array.FindIndex(oldOffsets!, x=>x==old); Require(target>=0 && labels.ContainsKey("old_"+target),"unresolved original destination "+old); node[k]=labels["old_"+target]; }
                    }
                });
            }
            foreach(var (node,key,label) in p.Fixups) { Require(labels.ContainsKey(label),"undefined label "+label); node[key]=labels[label]; }
            Arr(c.Asset,"Exports")[p.ExportIndex-1]!["ScriptBytecodeSize"] = offsets[^1];
        }
    }

    static IEnumerable<int> ScriptReferences2(JsonNode? n) {
        if(n is JsonObject o) {
            string t=Str(o["$type"]);
            if(t.Contains("EX_ObjectConst") && o["Value"]!=null) yield return Num(o["Value"]);
            foreach(var (k,v) in o) {
                if(v is JsonValue && k is "StackNode" or "ResolvedOwner" or "Struct") yield return Num(v);
                foreach(int r in ScriptReferences2(v)) yield return r;
            }
        } else if(n is JsonArray xs) foreach(var x in xs) foreach(int r in ScriptReferences2(x)) yield return r;
    }

    public static int BuildStage2(string rootPath,string outputDirectory) {
        try {
            string root=Path.GetFullPath(rootPath),dir=Path.GetFullPath(outputDirectory);
            Require(dir.StartsWith(Path.GetFullPath(Path.Combine(root,"builds/rtl_poc"))+Path.DirectorySeparatorChar,StringComparison.OrdinalIgnoreCase),"Detached output required");
            Require(!Directory.Exists(dir),"Refusing existing Stage2 output");
            var source=Read(Stage1Path(root)); Require(source.VerifyBinaryEquality(),"Stage1 source roundtrip"); var baseline=Model(source);
            string stage1dir=Path.GetDirectoryName(Stage1Path(root))!;
            string[] protectedFiles=Directory.GetFiles(stage1dir,"*",SearchOption.AllDirectories).OrderBy(x=>x,StringComparer.Ordinal).ToArray();
            string[] before=protectedFiles.Select(HashFile).ToArray();
            Directory.CreateDirectory(dir); File.WriteAllText(Path.Combine(dir,"NOT_INSTALLABLE.txt"),"STAGE2 OFFLINE NOT_INSTALLABLE NOT_RUNTIME_TESTED — timer/step/finish deferred\n");
            var c=Generate2(baseline); WritePackage(c.Asset,Stage2Path(dir));
            SaveJson(Path.Combine(dir,"insertion_map.json"),new JsonArray(c.Plans.Select(p=>(JsonNode)new JsonObject { ["export"]=p.ExportIndex,["cells"]=new JsonArray(p.Cells.Select(x=>(JsonNode)new JsonObject{["label"]=x.Label,["original"]=x.OriginalIndex,["english"]=x.English}).ToArray()) }).ToArray()));
            var actual=Read(Stage2Path(dir)); var errors=CheckStage2(actual,baseline); Require(errors.Count==0,string.Join("; ",errors.Take(15)));
            var originalDiff=DiffStage2(Stage1Path(root),Stage2Path(dir));
            var repeat=Path.Combine(dir,"determinism"); var roundtrip=Path.Combine(dir,"roundtrip");
            WritePackage(Generate2(baseline).Asset,Stage2Path(repeat)); Directory.CreateDirectory(roundtrip); actual.Write(Stage2Path(roundtrip));
            foreach(string ext in new[]{".uasset",".uexp"}) {
                var bytes=File.ReadAllBytes(Path.ChangeExtension(Stage2Path(dir),ext));
                Require(bytes.SequenceEqual(File.ReadAllBytes(Path.ChangeExtension(Stage2Path(repeat),ext))),"Stage2 nondeterminism "+ext);
                Require(bytes.SequenceEqual(File.ReadAllBytes(Path.ChangeExtension(Stage2Path(roundtrip),ext))),"Stage2 roundtrip bytes "+ext);
            }
            var negatives=NegativeStage2(Model(actual),baseline);
            Require(before.SequenceEqual(protectedFiles.Select(HashFile)),"Stage1 files changed");
            SaveJson(Path.Combine(dir,"stage2_instruction_inventory.json"),InstructionInventory(actual));
            SaveJson(Path.Combine(dir,"stage2_verification.json"),new JsonObject { ["status"]="R8B_WBP_STAGE2_PASS",["scope"]="ARABIC_INITIALIZATION_ONLY_TIMER_STEP_FINISH_DEFERRED",
                ["labels"]=new JsonArray("STAGE2","OFFLINE","NOT_INSTALLABLE","NOT_RUNTIME_TESTED"),["validatorErrors"]=0,["unexpectedChanges"]=0,
                ["originalExportDiff"]=originalDiff,["negativeTests"]=negatives,["deterministicBinaryEqual"]=true,["roundtripBinaryEqual"]=true,
                ["stage1FilesUnchanged"]=true,["stage1Hashes"]=new JsonArray(protectedFiles.Select((x,i)=>(JsonNode)new JsonObject{["path"]=Path.GetRelativePath(root,x),["sha256"]=before[i]}).ToArray()),
                ["uassetSha256"]=HashFile(Stage2Path(dir)),["uexpSha256"]=HashFile(Path.ChangeExtension(Stage2Path(dir),".uexp")),
                ["DISPATCH_INTEGRATION_PROVEN"]=false,["IN_GAME_RTL_PROVEN"]=false,["tested_in_game"]=0,["final"]=0 });
            Console.WriteLine("R8B_WBP_STAGE2_PASS (initialization subset): CFG/English/relocation checks, "+negatives.Count+" negatives, deterministic binary and roundtrip. "+dir); return 0;
        } catch(Exception ex) {Console.Error.WriteLine(ex.ToString());return 1;}
    }
    public static int ValidateStage2(string rootPath,string directory) {
        try {
            string root=Path.GetFullPath(rootPath),dir=Path.GetFullPath(directory); var asset=Read(Stage2Path(dir)); Require(asset.VerifyBinaryEquality(),"Stage2 binary roundtrip");
            var baseline=Model(Read(Stage1Path(root))); var errors=CheckStage2(asset,baseline); Require(errors.Count==0,string.Join("; ",errors.Take(20)));
            var diff=DiffStage2(Stage1Path(root),Stage2Path(dir)); var report=JsonNode.Parse(File.ReadAllText(Path.Combine(dir,"stage2_verification.json")))!;
            foreach(var entry in Arr(report,"stage1Hashes")) Require(HashFile(Path.Combine(root,Str(entry!["path"])))==Str(entry["sha256"]),"Stage1 hash changed");
            foreach(string ext in new[]{".uasset",".uexp"}) foreach(string copy in new[]{"determinism","roundtrip"}) Require(File.ReadAllBytes(Path.ChangeExtension(Stage2Path(dir),ext)).SequenceEqual(File.ReadAllBytes(Path.ChangeExtension(Stage2Path(Path.Combine(dir,copy)),ext))),"binary evidence mismatch");
            Console.WriteLine(new JsonObject{["status"]="STAGE2_OFFLINE_VALIDATION_PASS",["errors"]=0,["negativeTests"]=NegativeStage2(Model(asset),baseline),["originalExportDiff"]=diff}.ToJsonString(Pretty));return 0;
        }
        catch(Exception ex) {Console.Error.WriteLine(ex.ToString());return 1;}
    }

    static JsonNode? Semantic2(JsonNode? n) {
        var result=n?.DeepClone(); JsonWalk2(result,"$",(o,_)=> {
            foreach(string k in new[]{"CodeOffset","PushingAddress","EndGotoOffset","NextOffset","SkipOffset"}) if(o[k]!=null)o[k]=0;
            if(Str(o["$type"]).Contains("EX_Context"))o["Offset"]=0;
        }); return result;
    }
    static List<string> CheckStage2(UAsset actual,JsonObject baseline) => CheckStage2Model(Model(actual),baseline,actual);
    static List<string> CheckStage2Model(JsonObject a,JsonObject baseline,UAsset? typed=null) {
        var errors=new List<string>(); void T(bool ok,string why){if(!ok)errors.Add(why);}
        var expected=Generate2(baseline); var expectedModel=Normalize(expected.Asset);
        T(JsonNode.DeepEquals(Projection(a),Projection(expectedModel)),"unexpected Stage2 schema change");
        T(Arr(a,"NameMap").Take(Arr(baseline,"NameMap").Count).Select(Str).SequenceEqual(Arr(baseline,"NameMap").Select(Str)),"name prefix changed");
        T(JsonNode.DeepEquals(new JsonArray(Arr(a,"Imports").Take(Arr(baseline,"Imports").Count).Select(x=>x!.DeepClone()).ToArray()),baseline["Imports"]),"original imports changed");
        int ne=Arr(a,"Exports").Count,ni=Arr(a,"Imports").Count;
        foreach(int i in References(a["Exports"]).Concat(References(a["Imports"])).Concat(ScriptReferences2(a["Exports"]))) T(i>=-ni&&i<=ne,"dangling FPackageIndex "+i);
        var map=Arr(Export(a,"WBP_SubtitleBlock_C"),"FuncMap");
        foreach(string h in Helpers2)T(map.Count(x=>Str(x![0])==h)==1,"missing helper function "+h);
        foreach(var e in Arr(a,"Exports").Where(x=>x!["ScriptBytecode"]!=null)) JsonWalk2(e!["ScriptBytecode"],"$",(o,path)=>{
            string type=Str(o["$type"]);
            if(type.Contains("FFieldPath") && Num(o["ResolvedOwner"])>0){int owner=Num(o["ResolvedOwner"]); if(owner<=ne)foreach(var name in Arr(o,"Path").Take(1))T(Arr(Arr(a,"Exports")[owner-1]!,"LoadedProperties").Any(p=>Str(p!["Name"])==Str(name)),"missing variable "+Str(name));}
            if(o["StackNode"] is JsonValue) {int index=Num(o["StackNode"]); if(index<0&&-index<=ni) T(Str(Arr(a,"Imports")[-index-1]!["ClassName"])=="Function","missing function import "+index);else if(index>0&&index<=ne)T(Str(Arr(a,"Exports")[index-1]!["$type"]).Contains("FunctionExport"),"invalid local function "+index);}
        });
        foreach(var e in Arr(baseline,"Exports").Where(x=>Str(x!["$type"]).Contains("FunctionExport") && Str(x["ObjectName"]) is not ("Set Displayed Line" or "Stop Displaying Line")))
            T(JsonNode.DeepEquals(e!["ScriptBytecode"],Export(a,Str(e["ObjectName"]))["ScriptBytecode"]),"modified unrelated function "+Str(e["ObjectName"]));
        // Invalid indices/cardinalities cannot be safely traversed. Other defects still exercise the specific CFG gates.
        if(errors.Any(x=>x.StartsWith("dangling FPackageIndex")) || expected.Plans.Any(p=>Arr(Arr(a,"Exports")[p.ExportIndex-1]!,"ScriptBytecode").Count!=p.Cells.Count))return errors;
        typed??=UAsset.DeserializeJson(a.ToJsonString());
        foreach(var plan in expected.Plans) {
            int f=plan.ExportIndex; var code=Arr(Arr(a,"Exports")[f-1]!,"ScriptBytecode"); var expr=((StructExport)typed.Exports[f-1]).ScriptBytecode!;
            int[] offsets=new int[expr.Length+1];for(int i=0;i<expr.Length;i++)offsets[i+1]=offsets[i]+Size2(typed,expr[i]);
            T(Num(Arr(a,"Exports")[f-1]!["ScriptBytecodeSize"])==offsets[^1],"wrong logical bytecode size");
            if(plan.Original!=null) {
                // Independent relocation certificate: unchanged nested bodies retain valid source-relative boundaries.
                var sourceTyped=UAsset.DeserializeJson(baseline.ToJsonString());var old=((StructExport)sourceTyped.Exports[f-1]).ScriptBytecode!;
                var oldOffsets=new int[old.Length+1];for(int j=0;j<old.Length;j++)oldOffsets[j+1]=oldOffsets[j]+Size2(sourceTyped,old[j]);
                for(int j=0;j<plan.Cells.Count;j++)if(plan.Cells[j].OriginalIndex is int oi) {
                    var sourceNodes=new Dictionary<string,JsonObject>();JsonWalk2(plan.Original[oi],"$",(node,path)=>sourceNodes[path]=node);
                    JsonWalk2(code[j],"$",(node,path)=>{
                        foreach(string field in new[]{"CodeOffset","PushingAddress","EndGotoOffset","NextOffset","SkipOffset"})if(node[field]!=null) {
                            int originalTarget=Num(sourceNodes[path][field]),target;
                            if(originalTarget>=oldOffsets[oi]&&originalTarget<=oldOffsets[oi+1])target=offsets[j]+originalTarget-oldOffsets[oi];
                            else {int origin=Array.IndexOf(oldOffsets,originalTarget);int location=plan.Cells.FindIndex(x=>x.English&&x.OriginalIndex==origin);Require(location>=0,"source relocation destination absent");target=offsets[location];}
                            T(Num(node[field])==target,"relocation certificate mismatch "+f+":"+j+" "+path+"."+field);
                        }
                    });
                }
            }
            for(int i=0;i<code.Count;i++) {
                var nodes=new Dictionary<string,KismetExpression>();TypedWalk2(expr[i],"$",nodes);
                JsonWalk2(code[i],"$",(node,path)=>{
                    string op=Str(node["$type"]);
                    if(op.Contains("EX_Context")) T(Num(node["Offset"])==Size2(typed,nodes[path+".ContextExpression"]),"bad context skip "+f+":"+i);
                    if(op.Contains("EX_Jump,")||op.Contains("EX_JumpIfNot,")||op.Contains("EX_PushExecutionFlow,")) {
                        int target=Num(node[op.Contains("PushExecutionFlow")?"PushingAddress":"CodeOffset"]);T(Array.IndexOf(offsets,target)>=0&&target<offsets[^1],"bad jump target "+f+":"+i);
                    }
                });
            }
            if(f!=expected.Functions[Helpers2[4]]) {
                var colors=new int[code.Count];
                bool Acyclic(int pc) {
                    if(pc<0||pc>=code.Count)return true;
                    if(colors[pc]==1)return false;if(colors[pc]==2)return true;colors[pc]=1;
                    var n=code[pc]!;string op=Str(n["$type"]);var next=new List<int>();
                    if(op.Contains("EX_Jump,"))next.Add(Array.IndexOf(offsets,Num(n["CodeOffset"])));
                    else if(op.Contains("EX_JumpIfNot")){next.Add(pc+1);next.Add(Array.IndexOf(offsets,Num(n["CodeOffset"])));}
                    else if(!op.Contains("EX_Return")&&!op.Contains("EX_EndOfScript")&&!op.Contains("EX_PopExecutionFlow"))next.Add(pc+1);
                    if(next.Any(x=>!Acyclic(x)))return false;colors[pc]=2;return true;
                }
                T(Enumerable.Range(0,code.Count).All(Acyclic),"accidental CFG cycle "+f);
            }
            if(f==11) {
                var old=Arr(Export(baseline,"Set Displayed Line"),"ScriptBytecode");
                T(plan.Cells.Where(x=>x.English&&x.OriginalIndex!=null).Select(x=>x.OriginalIndex!.Value).OrderBy(x=>x).SequenceEqual(Enumerable.Range(0,old.Count)),"English sequence inventory changed");
                for(int i=0;i<plan.Cells.Count;i++)if(plan.Cells[i].English&&plan.Cells[i].OriginalIndex is int oi)T(JsonNode.DeepEquals(Semantic2(code[i]),Semantic2(old[oi])),"English instruction modified "+oi);
                var firstGate=code.First(x=>Str(x!["$type"]).Contains("EX_JumpIfNot"))!;
                var expectedGate=Arr(Export(expectedModel,"Set Displayed Line"),"ScriptBytecode").First(x=>Str(x!["$type"]).Contains("EX_JumpIfNot"))!;
                T(Num(firstGate["CodeOffset"])==Num(expectedGate["CodeOffset"]),"wrong English continuation");
                foreach(bool animate in new[]{false,true}) {
                    try {T(EnglishTrace2(code,plan,offsets,animate).SequenceEqual(OriginalTrace2(old,baseline,animate)),"wrong English continuation / flow stack");}
                    catch(Exception ex){errors.Add("wrong English continuation / "+ex.Message);}
                }
                T(plan.Cells.Any(x=>x.Label=="arabic_begin")&&plan.Cells.Any(x=>x.Label=="old_7"),"Arabic/English reachability");
                var reachable=new HashSet<int>();var pending=new Stack<int>();pending.Push(0);
                var returns=code.Where(x=>Str(x!["$type"]).Contains("EX_PushExecutionFlow")).Select(x=>Array.IndexOf(offsets,Num(x!["PushingAddress"]))).ToArray();
                while(pending.Count>0){int pc=pending.Pop();if(pc<0||pc>=code.Count||!reachable.Add(pc))continue;var node=code[pc]!;string op=Str(node["$type"]);
                    if(op.Contains("EX_Jump,")||op.Contains("EX_JumpIfNot"))pending.Push(Array.IndexOf(offsets,Num(node["CodeOffset"])));
                    if(op.Contains("EX_PopExecutionFlow")){foreach(int r in returns)pending.Push(r);continue;}
                    if(!op.Contains("EX_Jump,")&&!op.Contains("EX_Return")&&!op.Contains("EX_EndOfScript"))pending.Push(pc+1);
                }
                T(reachable.Contains(plan.Cells.FindIndex(x=>x.Label=="arabic_begin"))&&reachable.Contains(plan.Cells.FindIndex(x=>x.Label=="old_7")),"Arabic/English continuation unreachable");
            }
        }
        DependencyCycles(a,errors);return errors;
    }

    static List<int> OriginalTrace2(JsonArray script,JsonObject baseline,bool animate) {
        var typed=UAsset.DeserializeJson(baseline.ToJsonString());var expr=((StructExport)typed.Exports[10]).ScriptBytecode!;var offsets=new int[expr.Length+1];for(int k=0;k<expr.Length;k++)offsets[k+1]=offsets[k]+Size2(typed,expr[k]);
        var dummy=new Asm2();for(int k=0;k<script.Count;k++)dummy.Cells.Add(new Cell2{Label="old_"+k,Code=Copy(script[k]!),English=true,OriginalIndex=k});
        return EnglishTrace2(script,dummy,offsets,animate);
    }
    static List<int> EnglishTrace2(JsonArray script,Asm2 plan,int[] offsets,bool animate) {
        var stack=new Stack<int>();var trace=new List<int>();int pc=0,budget=2000;
        while(pc>=0&&pc<script.Count&&--budget>0) {
            var e=script[pc]!;string op=Str(e["$type"]);var cell=plan.Cells[pc];
            if(op.Contains("EX_Return")){Require(stack.Count==0,"English flow stack not empty at return");return trace;}
            if(op.Contains("EX_PushExecutionFlow")){stack.Push(Array.IndexOf(offsets,Num(e["PushingAddress"])));pc++;continue;}
            if(op.Contains("EX_PopExecutionFlow")){Require(stack.Count>0,"flow stack underflow");pc=stack.Pop();continue;}
            if(op.Contains("EX_Jump,")){pc=Array.IndexOf(offsets,Num(e["CodeOffset"]));continue;}
            if(op.Contains("EX_JumpIfNot")){
                bool condition=cell.OriginalIndex==26?animate:false; // new English path: Arabic=false, ProtoSuppressed=false
                pc=condition?pc+1:Array.IndexOf(offsets,Num(e["CodeOffset"]));continue;
            }
            if(cell.English&&cell.OriginalIndex is int oi)trace.Add(oi);pc++;
        }
        throw new InvalidDataException("nonterminating/unreachable English CFG");
    }

    static JsonArray DiffStage2(string sourcePath,string outputPath) {
        var original=Read(sourcePath);var generated=Read(outputPath);var baseline=Model(original);var current=Model(generated);var result=new JsonArray();
        byte[] old=File.ReadAllBytes(sourcePath).Concat(File.ReadAllBytes(Path.ChangeExtension(sourcePath,".uexp"))).ToArray();
        byte[] now=File.ReadAllBytes(outputPath).Concat(File.ReadAllBytes(Path.ChangeExtension(outputPath,".uexp"))).ToArray();
        for(int i=0;i<original.Exports.Count;i++) {
            var o=original.Exports[i];var n=generated.Exports[i];byte[] ob=old.AsSpan((int)o.SerialOffset,(int)o.SerialSize).ToArray(),nb=now.AsSpan((int)n.SerialOffset,(int)n.SerialSize).ToArray();
            bool same=ob.SequenceEqual(nb),allowed=i is 10 or 11 or 21 or 22;Require(same||allowed,"modified unrelated export "+(i+1));
            var entry=new JsonObject{["export"]=i+1,["name"]=o.ObjectName.ToString(),["classification"]=same?"BYTE_IDENTICAL":"EXPECTED_STAGE2_CHANGE",["originalPayloadSha256"]=Hash(ob),["stage2PayloadSha256"]=Hash(nb)};
            if(o is FunctionExport of&&n is FunctionExport nf) {
                byte[] oc=Bytecode(original,of,out _),nc=Bytecode(generated,nf,out _);if(i is not (10 or 11))Require(oc.SequenceEqual(nc),"modified unrelated function bytecode "+(i+1));
                entry["originalBytecodeSha256"]=Hash(oc);entry["stage2BytecodeSha256"]=Hash(nc);entry["bytecodeUnchanged"]=oc.SequenceEqual(nc);
            }
            result.Add(entry);
        }
        return result;
    }
    static JsonArray NegativeStage2(JsonObject good,JsonObject baseline) {
        var result=new JsonArray();
        void Run(string name,Action<JsonObject> mutate,string diagnostic) {
            var bad=Copy(good);mutate(bad);var errors=CheckStage2Model(bad,baseline);
            Require(errors.Any(x=>x.Contains(diagnostic)),"negative not detected: "+name);
            result.Add(new JsonObject{["fixture"]=name,["detected"]=true,["diagnostics"]=new JsonArray(errors.Take(4).Select(x=>(JsonNode)V(x)).ToArray())});
        }
        Run("bad jump target",a=>Arr(Export(a,"Set Displayed Line"),"ScriptBytecode").First(x=>Str(x!["$type"]).Contains("EX_JumpIfNot"))!["CodeOffset"]=3,"bad jump target");
        Run("bad context skip",a=>Arr(Export(a,"Set Displayed Line"),"ScriptBytecode").First(x=>Str(x!["$type"]).Contains("EX_Context"))!["Offset"]=1,"bad context skip");
        Run("missing function import",a=>Arr(a,"Imports").First(x=>Str(x!["ObjectName"])=="GetCurrentLanguage")!["ClassName"]="Object","missing function import");
        Run("missing variable",a=>{var p=Arr(Export(a,"WBP_SubtitleBlock_C"),"LoadedProperties");p.Remove(p.Single(x=>Str(x!["Name"])=="bArabic"));},"missing variable");
        Run("wrong English continuation",a=>Arr(Export(a,"Set Displayed Line"),"ScriptBytecode").First(x=>Str(x!["$type"]).Contains("EX_JumpIfNot"))!["CodeOffset"]=0,"wrong English continuation");
        Run("modified unrelated function",a=>Arr(Export(a,"ChangeTextToLarge"),"ScriptBytecode")[0]!["Offset"]=99,"modified unrelated function");
        return result;
    }
}
