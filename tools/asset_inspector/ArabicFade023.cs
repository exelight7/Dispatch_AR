using System.Globalization;
using System.Text.Json.Nodes;
using UAssetAPI;
using UAssetAPI.ExportTypes;

// Round 024 (supervisor_reply_024, design report_023): display-only per-word fade on the round-019 WBP (the WBP of the Run 6 pak).
// Integer word boundaries stay on K2_SetTimer -> Arabic Clock Fired -> Advance Budget -> Step -> Set Threshold Arabic. The new
// "Arabic Fade Tick" (Blueprint Tick, after Arabic Paused Clock) only reads clock state and writes the two Border tints:
// tint B = ArabicFadeBase * (1 + 9.4 * alpha), alpha = FClamp((Elapsed - 0.025) / (Due - 0.025), 0, 1) for unit T+1.
static partial class ArabicStage1
{
    const string FadeName = "WBP_SubtitleBlock_AR_R8B_FADE_023";
    const string FadeTick = "Arabic Fade Tick";
    const string StyleFix021Dir = "builds/rtl_poc/r8b_stylefix_021";
    const string NativeEvidence023 = "reports/rtl_research/renderer_repair/r8b_fade_023/native_returns_023.json";
    const float FadeSlope = 9.4f, FadeLetter = 0.025f, FadeMinSpan = 0.001f;
    static readonly float FadeHidden = (float)(1 / 10.5);   // FadeBase at T = -1 (row u0 product 1/10.5: opacity 0)
    static readonly string[] FadeEdited = { "Set Threshold Arabic", "Tick" };
    static readonly string[] FadeLocals = { "Due", "Now", "Elapsed", "Span", "Alpha", "Blue" };
    static readonly (string Key, string[] Params)[] FadeNatives = { ("KismetMathLibrary.Divide_FloatFloat", new[] { "Float", "Float" }), ("KismetMathLibrary.FClamp", new[] { "Float", "Float", "Float" }) };
    static readonly string[] FadeAllowed = { "BooleanAND", "Not_PreBool", "Less_IntInt", "Add_IntInt", "GreaterEqual_FloatFloat", "Array_Get", "GetTimeSeconds",
        "GetUnpausedTimeSeconds", "Subtract_FloatFloat", "Add_FloatFloat", "Multiply_FloatFloat", "Divide_FloatFloat", "FClamp", "SetContentColorAndOpacity", "RequestRender" };
    static readonly string[] MarkupFunctions = { "Build Arabic Markup", "Build Arabic Timing", "Format As Arabic Plain", "AR Escape", "Arabic Apply Style", "Arabic Apply Wrap" };
    // Round-021 tables (the Run 6 pak payload); never regenerated here.
    static readonly Dictionary<string, string> Tables021 = new() {
        ["DT_AR_Fill.uasset"] = "ee1b723d69bb0ab7c8eb3bfd84a5886b863d813486b550b7017b90883f59f665", ["DT_AR_Fill.uexp"] = "caa039c46145580f21d48d83cc4333e69d379a3d846ff1ab66fa598b589f80af",
        ["DT_AR_Fill_Large.uasset"] = "0ac7c57ae8e092881e3b56fae1044599c8d0fd817786f74f1499f372977ed927", ["DT_AR_Fill_Large.uexp"] = "8182df2efc3eb59f4d17694f980caf6380b51418670e7d72ce52c1e0404c6262",
        ["DT_AR_Outline.uasset"] = "d81c10af086ba6f50e0b994dd90c570fcb3147c7a2ea4e2ed0dab5a801d9ab10", ["DT_AR_Outline.uexp"] = "427e3a49015aca862cf6ccdf21557b77535662d69c366a4f048d543274c10ce6",
        ["DT_AR_Outline_Large.uasset"] = "ce61830b6eb2151ff29ee3ba414c0d3d892b4acabd1d1f5e4185268d2c7c1b60", ["DT_AR_Outline_Large.uexp"] = "93620a8faeb88bdb895c9edadea192ceed7944208d66c7599fcffbd5aeb32801" };
    static string FadeWbp023(string dir) => Path.Combine(dir, FadeName + ".uasset");
    static string Repair019Wbp(string root) => RepairPath(Path.Combine(root, Repair019Dir));

    static void GateFade023(string root) {
        foreach (string ext in new[] { ".uasset", ".uexp" }) { string k = Repair019Dir + "/" + RepairName + ext; Require(HashFile(Path.Combine(root, k)).Equals(Inputs021[k], StringComparison.OrdinalIgnoreCase), "round-019/021 WBP hash mismatch " + k); }
        foreach (var (file, sha) in Tables021) Require(HashFile(Path.Combine(root, StyleFix021Dir, file)).Equals(sha, StringComparison.OrdinalIgnoreCase), "round-021 DT_AR hash mismatch " + file);
    }
    static JsonNode Natives023(string root) {
        var n = JsonNode.Parse(File.ReadAllText(Path.Combine(root, NativeEvidence023)))!;
        Require(Str(n["exe_sha256"]) == ExeSha && n["functions"] is JsonObject, "fade native evidence missing or for another EXE"); return n;
    }
    // Fail closed: both new natives must be the KismetMathLibrary float functions, exactly as the EXE UHT tables declare them.
    static List<string> FadeSignatures023(JsonNode natives) {
        var errors = new List<string>();
        foreach (var (key, ps) in FadeNatives) {
            var e = natives["functions"]?[key]; var c = (e?["candidates"] as JsonArray)?.Where(x => (x!["params"] as JsonArray)?.Count == ps.Length).ToArray();
            bool ok = e != null && Str(e["return"]) == "Float" && (e["params"] as JsonArray)?.Select(p => Str(p!["type"])).SequenceEqual(ps) == true && c is { Length: > 0 }
                && c.All(x => Str(x!["outer_rva"]) == "0x285ae80" && Str(x["return"]) == "Float" && Arr(x, "params").All(p => !p!["out"]!.GetValue<bool>() && !p["reference"]!.GetValue<bool>()));
            if (!ok) errors.Add("float native signature unresolved " + key);
        }
        return errors;
    }

    static Build2Context GenerateFade023(JsonObject baseline) {
        var c = new Build2Context(baseline); var a = c.Asset; var exports = Arr(a, "Exports");
        for (int i = 0; i < exports.Count; i++) if (Str(exports[i]!["$type"]).Contains("FunctionExport")) c.Functions[Str(exports[i]!["ObjectName"])] = i + 1;
        { int i = exports.Count + 1; var e = Copy(Export(a, "Stop Displaying Line")); e["ObjectName"] = FadeTick; exports.Add(e); Arr(a, "DependsMap").Add(new JsonArray()); c.Functions[FadeTick] = i; }
        // Hidden-state defaults (= Set Threshold Arabic(-1)); every line resets them through Set Threshold Arabic.
        c.State("Float", "ArabicFadeBase", JsonValue.Create(FadeHidden)!); c.State("Float", "ArabicLastBlue", JsonValue.Create(0f)!);
        GenerateFadeTick023(c); EditThreshold023(c, baseline); EditTick023(c, baseline);
        var cls = Export(a, "WBP_SubtitleBlock_C");
        Arr(cls, "FuncMap").Add(new JsonArray(FadeTick, c.Functions[FadeTick])); Arr(cls, "Children").Add(c.Functions[FadeTick]); AddDep(cls, DepKeys[1], c.Functions[FadeTick]);
        foreach (var p in c.Plans) exports[p.ExportIndex - 1]!["ScriptBytecode"] = new JsonArray(p.Cells.Select(x => (JsonNode)x.Code).ToArray());
        Names(a); Assemble2(c, baseline);
        foreach (var p in c.Plans) { var e = exports[p.ExportIndex - 1]!; foreach (int r in ScriptReferences2(e["ScriptBytecode"]).Concat(References(e["LoadedProperties"])).Where(x => x != 0 && x != 22 && x != p.ExportIndex).Distinct()) AddDep(e, DepKeys[1], r); }
        Names(a); return c;
    }

    static void GenerateFadeTick023(Build2Context c) {
        var p = c.Function(FadeTick, null); int f = p.ExportIndex; foreach (string n in FadeLocals) c.Local(f, "Float", n);
        JsonObject L(string n) => Var2(f, n);
        JsonObject M(string fn, params JsonNode[] xs) => c.C("KismetMathLibrary", fn, xs);
        // Same live/next-unit guard as Arabic Arm Clock; Finish, Cancel, Stop, animation off and English all leave Remainder = -1.
        p.Jump("return", c.And(ClockLiveR(c), c.Less(c.Add(StateR("ArabicCurrentUnit"), 1), StateR("ArabicUnitCount"))));
        p.Jump("return", M("GreaterEqual_FloatFloat", StateR("ArabicClockRemainder"), FC(0)));
        p.Emit(c.C("KismetArrayLibrary", "Array_Get", StateR("ArabicUnitDelays"), c.Add(StateR("ArabicCurrentUnit"), 1), L("Due")));
        // The clock Arm Clock stamped with: GetUnpausedTimeSeconds for the AWP preview, GetTimeSeconds for gameplay.
        p.Jump("world", StateR(Awp)); p.Emit(Assign2(f, "Now", c.C("GameplayStatics", "GetUnpausedTimeSeconds", SelfR()), "Float")); p.Jump("elapsed");
        p.Mark("world"); p.Emit(Assign2(f, "Now", c.C("GameplayStatics", "GetTimeSeconds", SelfR()), "Float"));
        p.Mark("elapsed");
        p.Emit(Assign2(f, "Elapsed", M("Add_FloatFloat", M("Subtract_FloatFloat", L("Due"), StateR("ArabicClockRemainder")), M("Subtract_FloatFloat", L("Now"), StateR("ArabicClockStamp"))), "Float"));
        p.Emit(Assign2(f, "Span", M("Subtract_FloatFloat", L("Due"), FC(FadeLetter)), "Float"));
        p.Emit(Assign2(f, "Alpha", FC(0), "Float"));   // one-letter unit: no fade, the timer reveals it
        p.Jump("blue", M("GreaterEqual_FloatFloat", L("Span"), FC(FadeMinSpan)));
        p.Emit(Assign2(f, "Alpha", M("FClamp", M("Divide_FloatFloat", M("Subtract_FloatFloat", L("Elapsed"), FC(FadeLetter)), L("Span")), FC(0), FC(1)), "Float"));
        p.Mark("blue"); p.Emit(Assign2(f, "Blue", M("Multiply_FloatFloat", StateR("ArabicFadeBase"), M("Add_FloatFloat", FC(1), M("Multiply_FloatFloat", FC(FadeSlope), L("Alpha")))), "Float"));
        // Unchanged tint (pause, sub-step frame): no write and no shadow re-render.
        p.Jump("return", c.Not(c.And(M("GreaterEqual_FloatFloat", L("Blue"), StateR("ArabicLastBlue")), M("GreaterEqual_FloatFloat", StateR("ArabicLastBlue"), L("Blue")))));
        foreach (string w in new[] { Widgets[1], Widgets[5] }) p.Emit(Method2(w, c.N("Border", "SetContentColorAndOpacity"),
            X("StructConst", ("Struct", V(LinearColor023(c.Asset))), ("StructSize", V(16)), ("Value", new JsonArray(FC(1), FC(1), L("Blue"), FC(1))))));
        foreach (string w in new[] { Widgets[3], Widgets[4] }) p.Emit(Method2(w, c.N("RetainerBox", "RequestRender")));
        p.Emit(Assign2(22, "ArabicLastBlue", L("Blue"), "Float", true));
        p.Mark("return"); p.Emit(Return2()); p.Emit(X("EndOfScript"));
    }
    static int LinearColor023(JsonObject a) {
        var i = Arr(a, "Imports"); int k = i.Select((x, n) => (x, n)).Single(x => Str(x.x!["ObjectName"]) == "LinearColor" && Str(x.x!["ClassName"]) == "ScriptStruct").n;
        return -k - 1;
    }

    // After the existing integer Blue and ArabicThreshold: FadeBase = T < 0 ? 1/10.5 : Blue, LastBlue = Blue. Inserted after the
    // "apply" join so every path (T < 0, clamp, 0..36) passes through it; the tint/RequestRender tail is unchanged.
    static void EditThreshold023(Build2Context c, JsonObject baseline) {
        string name = Helpers2[5]; var code = Arr(Export(baseline, name), "ScriptBytecode"); int f = Index(baseline, name);
        var p = new Asm2 { ExportIndex = f, Original = code.DeepClone().AsArray() }; c.Plans.Add(p);
        var at = code.Select((x, i) => (x, i)).Where(x => IsAssignmentR(x.x!, "ArabicThreshold")).Select(x => x.i).ToArray();
        Require(at.Length == 1 && CallsR(baseline, code[at[0] + 1], "SetContentColorAndOpacity").Count == 1, "unexpected Set Threshold Arabic layout");
        for (int i = 0; i < code.Count; i++) {
            p.Old(i); if (i != at[0]) continue;
            p.Jump("fade_base", c.Less(Var2(f, "Threshold"), IC(0)));
            p.Emit(Assign2(22, "ArabicFadeBase", FC(FadeHidden), "Float", true)); p.Jump("fade_last");
            p.Mark("fade_base"); p.Emit(Assign2(22, "ArabicFadeBase", Var2(f, "Blue"), "Float", true));
            p.Mark("fade_last"); p.Emit(Assign2(22, "ArabicLastBlue", Var2(f, "Blue"), "Float", true));
        }
    }
    static void EditTick023(Build2Context c, JsonObject baseline) {
        var code = Arr(Export(baseline, "Tick"), "ScriptBytecode"); var p = new Asm2 { ExportIndex = Index(baseline, "Tick"), Original = code.DeepClone().AsArray() }; c.Plans.Add(p);
        Require(code.Count == 3 && CalleeR(baseline, code[0]) == "Arabic Paused Clock", "unexpected round-019 Tick");
        p.Old(0); p.Emit(Call2(c.Functions[FadeTick])); p.Old(1); p.Old(2);
    }

    // Canonical text of an expression, for exact formula checks.
    static string Shape023(JsonObject a, JsonNode? n) {
        if (n is not JsonObject o) return "?";
        string op = Op019(o); string Args() => string.Join(",", Arr(o, "Parameters").Select(x => Shape023(a, x)));
        return op switch {
            "CallMath" or "FinalFunction" or "LocalFinalFunction" => CalleeR(a, o) + "(" + Args() + ")",
            "VirtualFunction" => Str(o["VirtualFunctionName"]) + "(" + Args() + ")",
            "InstanceVariable" => "@" + Str(o["Variable"]?["New"]?["Path"]?[0]),
            "LocalVariable" or "LocalOutVariable" => Str(o["Variable"]?["New"]?["Path"]?[0]),
            "FloatConst" => "f:" + FloatR(o["Value"]).ToString("R", CultureInfo.InvariantCulture),
            "IntConst" => "i:" + Str(o["Value"]), "Self" => "self", "True" => "true", "False" => "false",
            "StructConst" => "S(" + string.Join(",", Arr(o, "Value").Select(x => Shape023(a, x))) + ")",
            "Context" => Shape023(a, o["ObjectExpression"]) + "." + Shape023(a, o["ContextExpression"]),
            _ => "EX_" + op };
    }
    static string? Written023(JsonObject o) => Op019(o) switch {
        "Let" => Op019(o["Variable"]) == "InstanceVariable" ? Str(o["Variable"]!["Variable"]?["New"]?["Path"]?[0]) : null,
        "LetBool" or "LetObj" => Op019(o["VariableExpression"]) == "InstanceVariable" ? Str(o["VariableExpression"]!["Variable"]?["New"]?["Path"]?[0]) : null,
        "SetArray" => Str(o["AssigningProperty"]?["Variable"]?["New"]?["Path"]?[0]), _ => null };
    // ReadsR without the empty-path crash (Context r-value pointers carry an empty FFieldPath).
    static bool Reads023(JsonNode? n, string variable) { bool hit = false; JsonWalk2(n, "$", (o, _) => { if (Str(o["$type"]).Contains("FFieldPath") && o["Path"] is JsonArray p && p.Count > 0 && Str(p[0]) == variable) hit = true; }); return hit; }
    static int[] Offsets023(UAsset typed, int export) {
        var expr = ((StructExport)typed.Exports[export - 1]).ScriptBytecode!; var o = new int[expr.Length + 1];
        for (int i = 0; i < expr.Length; i++) o[i + 1] = o[i] + Size2(typed, expr[i]); return o;
    }

    // Exact display-only constraints of Arabic Fade Tick, its Tick call and the Set Threshold Arabic fade state.
    static void FadeSemantics023(JsonObject a, Action<bool, string> T) {
        var exports = Arr(a, "Exports"); int fi = exports.Select((x, i) => (x, i)).Where(x => Str(x.x!["ObjectName"]) == FadeTick).Select(x => x.i + 1).DefaultIfEmpty(0).First();
        if (fi == 0) { T(false, "Arabic Fade Tick missing"); return; }
        var fe = exports[fi - 1]!; var code = Arr(fe, "ScriptBytecode");
        T(!Arr(fe, "LoadedProperties").Any(p => Str(p!["PropertyFlags"]).Contains("CPF_Parm")), "Fade Tick has parameters");
        T(Arr(Export(a, "WBP_SubtitleBlock_C"), "FuncMap").Count(x => Str(x![0]) == FadeTick) == 1, "Fade Tick not in FuncMap");
        // Everything Fade Tick can execute, including any local function it would call.
        var reach = new List<int> { fi };
        for (int k = 0; k < reach.Count; k++) JsonWalk2(exports[reach[k] - 1]!["ScriptBytecode"], "$", (o, _) => {
            if (o["StackNode"] is JsonValue v && Num(v) > 0 && !reach.Contains(Num(v))) reach.Add(Num(v)); });
        foreach (int r in reach) {
            string fn = Str(exports[r - 1]!["ObjectName"]);
            JsonWalk2(exports[r - 1]!["ScriptBytecode"], "$", (o, _) => {
                string op = Op019(o), callee = CalleeR(a, o);
                if (CallOps.Contains(op) && o["StackNode"] is JsonValue s && Num(s) > 0) {
                    T(false, "Fade Tick calls local function " + callee);
                    if (MarkupFunctions.Contains(callee)) T(false, "Fade Tick modifies markup (" + callee + ")");
                }
                if (callee == "SetText") T(false, "Fade Tick calls SetText (" + fn + ")");
                if (callee == "SetTextStyleSet") T(false, "Fade Tick calls SetTextStyleSet (" + fn + ")");
                if (callee is "K2_SetTimer" or "K2_ClearTimer") T(false, "Fade Tick calls " + callee + " (" + fn + ")");
                if (op == "CallMulticastDelegate") T(false, "Fade Tick broadcasts finish (" + fn + ")");
                if (callee is "Concat_StrStr" or "Conv_StringToText" or "Replace" or "GetSubstring" or "Conv_IntToString") T(false, "Fade Tick modifies markup (" + callee + ")");
                if (callee.StartsWith("Array_") && callee != "Array_Get") T(false, "Fade Tick modifies unit arrays (" + callee + ")");
                if (op == "VirtualFunction" || callee is "SetVisibility" or "SetRetainRendering" or "SetTextWrapAt" or "SetWrapTextAt") T(false, "Fade Tick mutates layout (" + (callee == "" ? Str(o["VirtualFunctionName"]) : callee) + ")");
                if (CallOps.Contains(op) && o["StackNode"] is JsonValue n && Num(n) < 0 && !FadeAllowed.Contains(callee)) T(false, "Fade Tick calls non-whitelisted native " + callee);
                if (Written023(o) is string w && w != "ArabicLastBlue")
                    T(false, w == "ArabicUnitDelays" ? "Fade Tick modifies unit arrays (ArabicUnitDelays)" : "Fade Tick writes " + w);
            });
            T(!Reads023(exports[r - 1]!["ScriptBytecode"], "InDeltaTime") && !Reads023(exports[r - 1]!["ScriptBytecode"], "MyGeometry"), "Fade Tick uses InDeltaTime (" + fn + ")");
        }
        var tick = Arr(Export(a, "Tick"), "ScriptBytecode");
        T(tick.Count == 4 && CalleeR(a, tick[0]) == "Arabic Paused Clock" && CalleeR(a, tick[1]) == FadeTick && Arr(tick[1]!, "Parameters").Count == 0 && IsOpR(tick[2]!, "Return") && IsOpR(tick[3]!, "EndOfScript"),
            "Tick does not call Paused Clock then Fade Tick");
        T(!Reads023(tick, "InDeltaTime") && !Reads023(tick, "MyGeometry"), "Tick reads InDeltaTime");
        if (code.Count < 4) { T(false, "Fade Tick body too short"); return; }
        var typed = UAsset.DeserializeJson(a.ToJsonString()); var offsets = Offsets023(typed, fi);
        int ret = code.Select((x, i) => (x, i)).Where(x => IsOpR(x.x!, "Return")).Select(x => x.i).DefaultIfEmpty(-1).Last();
        bool Exits(JsonNode n) => IsOpR(n, "JumpIfNot") && ret >= 0 && ret < offsets.Length && Num(n["CodeOffset"]) == offsets[ret];
        var g0 = IsOpR(code[0]!, "JumpIfNot") ? code[0]!["BooleanExpression"] : null;
        T(g0 != null && Exits(code[0]!) && PositiveR(a, g0, "bArabicActive") && PositiveR(a, g0, "ArabicSchedulerArmed") && ReadsR(g0, "ArabicFinished") && !PositiveR(a, g0, "ArabicFinished")
            && ReadsR(g0, "ArabicCurrentUnit") && ReadsR(g0, "ArabicUnitCount"), "Fade Tick live guard incomplete");
        T(Exits(code[1]!) && Shape023(a, code[1]!["BooleanExpression"]) == "GreaterEqual_FloatFloat(@ArabicClockRemainder,f:0)", "Remainder guard missing");
        var awp = ReachableR(code, offsets, true); var world = ReachableR(code, offsets, false);
        bool Calls(HashSet<int> path, string fn) => path.Any(i => CallsR(a, code[i], fn).Count > 0);
        T(Calls(awp, "GetUnpausedTimeSeconds") && !Calls(awp, "GetTimeSeconds") && Calls(world, "GetTimeSeconds") && !Calls(world, "GetUnpausedTimeSeconds"), "Fade Tick wrong clock source");
        JsonObject[] Lets(string local) => code.Select(x => x!.AsObject()).Where(x => IsOpR(x, "Let") && Op019(x["Variable"]) == "LocalVariable" && Str(x["Variable"]!["Variable"]?["New"]?["Path"]?[0]) == local).ToArray();
        string One(string local) { var l = Lets(local); return l.Length == 1 ? Shape023(a, l[0]["Expression"]) : "count " + l.Length; }
        T(code.Any(x => Shape023(a, x) == "Array_Get(@ArabicUnitDelays,Add_IntInt(@ArabicCurrentUnit,i:1),Due)"), "Fade Tick does not read Due of unit T+1");
        T(One("Elapsed") == "Add_FloatFloat(Subtract_FloatFloat(Due,@ArabicClockRemainder),Subtract_FloatFloat(Now,@ArabicClockStamp))", "Fade Tick elapsed formula " + One("Elapsed"));
        T(One("Span") == "Subtract_FloatFloat(Due,f:0.025)", "Fade Tick span formula " + One("Span"));
        var alpha = Lets("Alpha").Select(x => Shape023(a, x["Expression"])).ToArray();
        T(alpha.SequenceEqual(new[] { "f:0", "FClamp(Divide_FloatFloat(Subtract_FloatFloat(Elapsed,f:0.025),Span),f:0,f:1)" })
            && code.Any(x => IsOpR(x!, "JumpIfNot") && Shape023(a, x!["BooleanExpression"]) == "GreaterEqual_FloatFloat(Span,f:0.001)"), "Fade Tick alpha formula " + string.Join(" | ", alpha));
        var blue = Lets("Blue"); var slope = blue.Length == 1 ? blue[0]["Expression"]?["Parameters"]?[1]?["Parameters"]?[1]?["Parameters"]?[0] : null;
        float s = slope is JsonObject so && IsOpR(so, "FloatConst") ? FloatR(so["Value"]) : float.NaN;
        T(blue.Length == 1 && Shape023(a, blue[0]["Expression"]) == "Multiply_FloatFloat(@ArabicFadeBase,Add_FloatFloat(f:1,Multiply_FloatFloat(f:" + s.ToString("R", CultureInfo.InvariantCulture) + ",Alpha)))",
            "Fade Tick blue formula " + One("Blue"));
        T(s < 9.5f, "slope >= 9.5 (" + s.ToString("R", CultureInfo.InvariantCulture) + ")"); T(s == FadeSlope, "slope is not the approved 9.4");
        int change = code.Select((x, i) => (x, i)).Where(x => IsOpR(x.x!, "JumpIfNot") && Exits(x.x!) && Shape023(a, x.x!["BooleanExpression"])
            == "Not_PreBool(BooleanAND(GreaterEqual_FloatFloat(Blue,@ArabicLastBlue),GreaterEqual_FloatFloat(@ArabicLastBlue,Blue)))").Select(x => x.i).DefaultIfEmpty(-1).First();
        T(change > 0, "Fade Tick missing unchanged-tint guard");
        var tints = code.Select((x, i) => (x, i)).Where(x => CallsR(a, x.x, "SetContentColorAndOpacity").Count > 0).ToArray();
        var renders = code.Select((x, i) => (x, i)).Where(x => CallsR(a, x.x, "RequestRender").Count > 0).ToArray();
        string Target(JsonNode n) => Shape023(a, n["ObjectExpression"]);
        T(tints.Select(x => Target(x.x!)).OrderBy(x => x, StringComparer.Ordinal).SequenceEqual(new[] { "@" + Widgets[1], "@" + Widgets[5] }), "only one Border updated or extra tint target: " + string.Join(",", tints.Select(x => Target(x.x!))));
        T(tints.All(x => Shape023(a, x.x!["ContextExpression"]) == "SetContentColorAndOpacity(S(f:1,f:1,Blue,f:1))"), "Fade Tick tint is not (1,1,Blue,1)");
        T(renders.Select(x => Target(x.x!)).OrderBy(x => x, StringComparer.Ordinal).SequenceEqual(new[] { "@" + Widgets[3], "@" + Widgets[4] }), "only one shadow retainer refreshed or extra render target: " + string.Join(",", renders.Select(x => Target(x.x!))));
        var last = code.Select((x, i) => (x, i)).Where(x => Written023(x.x!.AsObject()) == "ArabicLastBlue").ToArray();
        T(last.Length == 1 && Shape023(a, last[0].x!["Expression"]) == "Blue", "Fade Tick LastBlue update missing");
        T(change > 0 && tints.Concat(renders).Concat(last).All(x => x.i > change && x.i < ret), "Fade Tick writes outside the unchanged-tint guard");
        // Set Threshold Arabic keeps its integer path and records the fade state after it.
        var th = Arr(Export(a, Helpers2[5]), "ScriptBytecode"); int at = th.Select((x, i) => (x, i)).Where(x => IsAssignmentR(x.x!, "ArabicThreshold")).Select(x => x.i).DefaultIfEmpty(-9).First();
        string Sh(int i) => i >= 0 && i < th.Count ? Shape023(a, th[i]) : "";
        bool thresholdOk = at >= 0 && at + 7 < th.Count && IsOpR(th[at + 1]!, "JumpIfNot") && Shape023(a, th[at + 1]!["BooleanExpression"]) == "Less_IntInt(Threshold,i:0)"
            && Shape023(a, th[at + 2]!["Expression"]) == "f:" + FadeHidden.ToString("R", CultureInfo.InvariantCulture) && Written023(th[at + 2]!.AsObject()) == "ArabicFadeBase" && IsOpR(th[at + 3]!, "Jump")
            && Written023(th[at + 4]!.AsObject()) == "ArabicFadeBase" && Shape023(a, th[at + 4]!["Expression"]) == "Blue" && Written023(th[at + 5]!.AsObject()) == "ArabicLastBlue" && Shape023(a, th[at + 5]!["Expression"]) == "Blue"
            && Sh(at + 6).StartsWith("@" + Widgets[1] + ".SetContentColorAndOpacity");
        T(thresholdOk, "Set Threshold Arabic fade-state assignments missing or misplaced");
        foreach (string fn in new[] { "Arabic Cancel", "Arabic Finish", "Stop Displaying Line" })
            T(Arr(Export(a, fn), "ScriptBytecode").Any(x => CalleeR(a, x) == Helpers2[5]), "fade fields not reset by " + fn);
    }

    sealed record FadeContext023(string Root, JsonObject Baseline, JsonObject Expected, List<Asm2> Plans, JsonNode Natives, Dictionary<string, JsonObject> Tables, Dictionary<string, string?> Rows);
    static FadeContext023 FadeContext(string root, JsonNode natives) {
        var baseline = Model(Read(Repair019Wbp(root))); var expected = GenerateFade023(baseline);
        var tables = Tables.ToDictionary(TablePath021, t => Model(Read(New021(Path.Combine(root, StyleFix021Dir), t))));
        return new(root, baseline, Projection(Normalize(expected.Asset)), expected.Plans, natives, tables, RowHierarchy021(root));
    }

    static List<string> CheckFade023(JsonObject actual, FadeContext023 x, out JsonArray contract, out JsonArray style) {
        var errors = FadeSignatures023(x.Natives); void T(bool ok, string why) { if (!ok) errors.Add(why); }
        contract = new JsonArray(); style = new JsonArray(); var b = x.Baseline;
        T(JsonNode.DeepEquals(Projection(actual), x.Expected), "unexpected fade schema change");
        T(Arr(actual, "NameMap").Take(Arr(b, "NameMap").Count).Select(Str).SequenceEqual(Arr(b, "NameMap").Select(Str)), "frozen name indices changed");
        T(JsonNode.DeepEquals(new JsonArray(Arr(actual, "Imports").Take(Arr(b, "Imports").Count).Select(n => n!.DeepClone()).ToArray()), b["Imports"]), "frozen imports changed");
        var added = Arr(actual, "Imports").Skip(Arr(b, "Imports").Count).Select(n => Str(n!["ObjectName"])).ToArray();
        T(added.SequenceEqual(new[] { "Divide_FloatFloat", "FClamp" }), "unexpected new imports " + string.Join(",", added));
        int ni = Arr(actual, "Imports").Count, ne = Arr(actual, "Exports").Count;
        if (References(actual["Exports"]).Concat(References(actual["Imports"])).Concat(ScriptReferences2(actual["Exports"])).Any(r => r < -ni || r > ne)) { T(false, "dangling fade reference"); return errors; }
        // Every other round-019 function is unchanged (reveal, clock, markup, timing, style, English paths).
        foreach (var old in Arr(b, "Exports").Where(n => Str(n!["$type"]).Contains("FunctionExport"))) {
            string name = Str(old!["ObjectName"]); if (FadeEdited.Contains(name)) continue;
            var now = Export(actual, name); T(new[] { "ScriptBytecode", "LoadedProperties", "FunctionFlags" }.All(k => JsonNode.DeepEquals(old[k], now[k])), "untouched function changed " + name);
        }
        var planned = x.Plans.Select(p => p.ExportIndex).ToHashSet();
        RevealBytecodeR(actual, b, x.Plans.Concat(Arr(actual, "Exports").Select((n, i) => (n, i: i + 1)).Where(n => n.n!["ScriptBytecode"] is JsonArray && !planned.Contains(n.i)).Select(n => new Asm2 { ExportIndex = n.i })).ToList(), T);
        // Round-012/019 clock semantics on the same package with only the new Tick call masked.
        var masked = Copy(actual); var tick = Arr(Export(masked, "Tick"), "ScriptBytecode");
        foreach (var n in tick.Where(n => CalleeR(masked, n) == FadeTick).ToArray()) tick.Remove(n);
        try { ClockSemanticsR(masked, T); } catch (Exception ex) { errors.Add("malformed clock adapter: " + ex.Message); }
        try { FadeSemantics023(actual, T); } catch (Exception ex) { errors.Add("malformed fade tick: " + ex.Message); }
        contract = ReturnContractR(actual, x.Natives, T);
        style = RichTextStyleGate(actual, p => x.Tables.GetValueOrDefault(p), x.Rows, T);
        T(style.Count(n => Str(n!["verdict"]) == ChildOk) == 14, "RichTextStyleGate must cover all four tables (14 bindings)");
        DependencyCycles(actual, errors); return errors;
    }

    static JsonArray NegativeFade023(JsonObject good, FadeContext023 x) {
        var results = new JsonArray(); int fi = Index(good, FadeTick), ti = Index(good, "Tick");
        void Run(string name, Action<JsonObject> mutate, string diagnostic, JsonNode? natives = null) {
            var bad = Copy(good); mutate(bad); Names(bad); List<string> errors;
            try { errors = CheckFade023(bad, natives == null ? x : x with { Natives = natives }, out _, out _); } catch (Exception ex) { errors = new() { "malformed: " + ex.Message }; }
            Require(errors.Any(e => e.Contains(diagnostic)), "negative fixture missed " + name + " / " + string.Join(";", errors.Take(6)));
            results.Add(new JsonObject { ["fixture"] = name, ["expected"] = "REJECT", ["result"] = "REJECT", ["diagnostic"] = diagnostic, ["errors"] = errors.Count, ["diagnostics"] = new JsonArray(errors.Take(5).Select(e => (JsonNode)V(e)).ToArray()) });
        }
        JsonArray Code(JsonObject a, string n = FadeTick) => Arr(Export(a, n), "ScriptBytecode");
        void Insert(JsonObject a, JsonNode n, string fn = FadeTick) { var s = Code(a, fn); s.Insert(s.Count - 2, n); }   // before Return
        int Imp(JsonObject a, string name, string owner) => -Arr(a, "Imports").Select((n, i) => (n, i)).Single(n => Str(n.n!["ObjectName"]) == name && Str(Arr(a, "Imports")[-Num(n.n["OuterIndex"]) - 1]!["ObjectName"]) == owner).i - 1;
        JsonNode Find(JsonObject a, string fn, Func<JsonNode, bool> p) => Code(a, fn).First(n => p(n!))!;
        Run("Fade Tick calls SetText", a => Insert(a, Method2(Widgets[2], Imp(a, "SetText", "RichTextBlock"), SC("x"))), "Fade Tick calls SetText");
        Run("Fade Tick calls SetTextStyleSet", a => Insert(a, Method2(Widgets[2], Imp(a, "SetTextStyleSet", "RichTextBlock"), Var2(22, Tables[0], true))), "Fade Tick calls SetTextStyleSet");
        Run("Fade Tick writes ArabicCurrentUnit", a => Insert(a, Assign2(22, "ArabicCurrentUnit", Call2(Imp(a, "Add_IntInt", "KismetMathLibrary"), StateR("ArabicCurrentUnit"), IC(1)), "Int", true)), "Fade Tick writes ArabicCurrentUnit");
        Run("Fade Tick writes ArabicThreshold", a => Insert(a, Assign2(22, "ArabicThreshold", IC(0), "Int", true)), "Fade Tick writes ArabicThreshold");
        Run("Fade Tick calls K2_SetTimer", a => Insert(a, CallsR(a, Code(a, "Arabic Arm Clock"), "K2_SetTimer")[0].DeepClone()), "Fade Tick calls K2_SetTimer");
        Run("Fade Tick calls K2_ClearTimer", a => Insert(a, Find(a, "Arabic Cancel", n => CalleeR(a, n) == "K2_ClearTimer").DeepClone()), "Fade Tick calls K2_ClearTimer");
        Run("Remainder guard missing", a => Code(a).RemoveAt(1), "Remainder guard missing");
        Run("Remainder guard reads Elapsed instead", a => Code(a)[1]!["BooleanExpression"]!["Parameters"]![0] = StateR("ArabicElapsed"), "Remainder guard missing");
        Run("live guard without bArabicActive", a => JsonWalk2(Code(a)[0], "$", (o, _) => { if (IsOpR(o, "InstanceVariable") && Str(o["Variable"]?["New"]?["Path"]?[0]) == "bArabicActive") o["Variable"]!["New"]!["Path"]![0] = "bArabic"; }), "Fade Tick live guard incomplete");
        Run("slope >= 9.5", a => JsonWalk2(Code(a), "$", (o, _) => { if (IsOpR(o, "FloatConst") && FloatR(o["Value"]) == FadeSlope) o["Value"] = 9.5f; }), "slope >= 9.5");
        Run("only one Border updated", a => Code(a).Remove(Find(a, FadeTick, n => Shape023(a, n).StartsWith("@" + Widgets[5]))), "only one Border updated");
        Run("only one shadow retainer refreshed", a => Code(a).Remove(Find(a, FadeTick, n => Shape023(a, n).StartsWith("@" + Widgets[4]))), "only one shadow retainer refreshed");
        Run("tint alpha not 1", a => Find(a, FadeTick, n => Shape023(a, n).StartsWith("@" + Widgets[1]))["ContextExpression"]!["Parameters"]![0]!["Value"]![3] = FC(0.5f), "Fade Tick tint is not (1,1,Blue,1)");
        Run("Fade Tick uses InDeltaTime", a => Insert(a, Assign2(Index(a, FadeTick), "Blue", Var2(ti, "InDeltaTime"), "Float")), "Fade Tick uses InDeltaTime");
        Run("Tick reads InDeltaTime", a => Code(a, "Tick").Insert(0, Assign2(ti, "InDeltaTime", Var2(ti, "InDeltaTime"), "Float")), "Tick reads InDeltaTime");
        Run("Tick without Fade Tick call", a => Code(a, "Tick").RemoveAt(1), "Tick does not call Paused Clock then Fade Tick");
        Run("Fade Tick broadcasts finish", a => Insert(a, Find(a, "Arabic Finish", n => IsOpR(n, "CallMulticastDelegate")).DeepClone()), "Fade Tick broadcasts finish");
        Run("Fade Tick calls Arabic Finish (transitive broadcast)", a => Insert(a, Call2(Index(a, "Arabic Finish"), BC(true))), "Fade Tick broadcasts finish (Arabic Finish)");
        Run("Fade Tick modifies unit arrays", a => Insert(a, Find(a, "Arabic Cancel", n => IsOpR(n, "SetArray")).DeepClone()), "Fade Tick modifies unit arrays");
        Run("Fade Tick modifies markup", a => Insert(a, Call2(Index(a, "Build Arabic Timing"), SC(""), SC(""))), "Fade Tick modifies markup");
        Run("Fade Tick mutates layout", a => Insert(a, Visible2(Widgets[0], 1)), "Fade Tick mutates layout");
        Run("Fade Tick writes without unchanged-tint guard", a => Code(a).Remove(Find(a, FadeTick, n => IsOpR(n, "JumpIfNot") && Shape023(a, n["BooleanExpression"]).StartsWith("Not_PreBool"))), "Fade Tick missing unchanged-tint guard");
        Run("Fade Tick gameplay clock = GetUnpausedTimeSeconds", a => JsonWalk2(Code(a), "$", (o, _) => { if (CalleeR(a, o) == "GetTimeSeconds") o["StackNode"] = Imp(a, "GetUnpausedTimeSeconds", "GameplayStatics"); }), "Fade Tick wrong clock source");
        Run("alpha without FClamp", a => { var l = Code(a).Last(n => IsOpR(n!, "Let") && Str(n!["Variable"]!["Variable"]?["New"]?["Path"]?[0]) == "Alpha")!; l["Expression"] = l["Expression"]!["Parameters"]![0]!.DeepClone(); }, "Fade Tick alpha formula");
        Run("Set Threshold without LastBlue reset", a => Code(a, Helpers2[5]).Remove(Code(a, Helpers2[5]).First(n => Written023(n!.AsObject()) == "ArabicLastBlue")), "Set Threshold Arabic fade-state assignments missing or misplaced");
        Run("float result into Int destination", a => { var e = Export(a, FadeTick); var p = Copy(Arr(e, "LoadedProperties")[0]!); p["Name"] = "Probe"; p["SerializedType"] = "IntProperty"; Arr(e, "LoadedProperties").Add(p);
            var l = Code(a).Last(n => IsOpR(n!, "Let") && Str(n!["Variable"]!["Variable"]?["New"]?["Path"]?[0]) == "Alpha")!; l["Value"]!["New"]!["Path"]![0] = "Probe"; l["Variable"]!["Variable"]!["New"]!["Path"]![0] = "Probe"; },
            "invalid result destination Arabic Fade Tick:");
        var noClamp = x.Natives.DeepClone(); noClamp["functions"]!.AsObject().Remove("KismetMathLibrary.FClamp");
        Run("float native signature unresolved (FClamp evidence absent)", _ => { }, "float native signature unresolved KismetMathLibrary.FClamp", noClamp);
        var badDivide = x.Natives.DeepClone(); badDivide["functions"]!["KismetMathLibrary.Divide_FloatFloat"]!["candidates"]![0]!["outer_rva"] = "0x1000";
        Run("float native signature mismatch (Divide_FloatFloat not KismetMathLibrary)", _ => { }, "float native signature unresolved KismetMathLibrary.Divide_FloatFloat", badDivide);
        // RichTextStyleGate on the fade WBP: the Run 5 tables (round-019 DT_AR) must still be rejected.
        var run5 = Tables.ToDictionary(TablePath021, t => Model(Read(Old021(x.Root, t))));
        var run5Errors = new List<string>(); RichTextStyleGate(good, p => run5.GetValueOrDefault(p), x.Rows, (ok, why) => { if (!ok) run5Errors.Add(why); });
        Require(run5Errors.Count == 14, "fade WBP accepted the Run 5 tables");
        results.Add(new JsonObject { ["fixture"] = "Run 5 tables bound to the fade WBP (RichTextStyleGate)", ["expected"] = "REJECT", ["result"] = "REJECT", ["errors"] = run5Errors.Count, ["diagnostics"] = new JsonArray(run5Errors.Take(2).Select(e => (JsonNode)V(e)).ToArray()) });
        return results;
    }

    static JsonObject DiffFade023(string sourcePath, string generatedPath) {
        var original = Read(sourcePath); var generated = Read(generatedPath); var exports = new JsonArray();
        var old = File.ReadAllBytes(sourcePath).Concat(File.ReadAllBytes(Path.ChangeExtension(sourcePath, ".uexp"))).ToArray(); var now = File.ReadAllBytes(generatedPath).Concat(File.ReadAllBytes(Path.ChangeExtension(generatedPath, ".uexp"))).ToArray();
        var expected = new Dictionary<string, string> { ["Set Threshold Arabic"] = "EXPECTED_THRESHOLD_FADE_STATE_ASSIGNMENTS", ["Tick"] = "EXPECTED_TICK_CALLS_FADE_TICK",
            ["WBP_SubtitleBlock_C"] = "EXPECTED_CLASS_2_FLOAT_FIELDS_AND_FUNCMAP", ["Default__WBP_SubtitleBlock_C"] = "EXPECTED_CDO_2_FLOAT_DEFAULTS" };
        Require(generated.Exports.Count == original.Exports.Count + 1 && generated.Exports[^1].ObjectName.ToString() == FadeTick, "fade must append exactly one export");
        for (int i = 0; i < generated.Exports.Count; i++) {
            var n = generated.Exports[i]; string name = n.ObjectName.ToString(); var after = now.AsSpan((int)n.SerialOffset, (int)n.SerialSize).ToArray();
            var item = new JsonObject { ["export"] = i + 1, ["name"] = name, ["generated_payload_sha256"] = Hash(after), ["generated_serial_size"] = n.SerialSize };
            if (i < original.Exports.Count) {
                var o = original.Exports[i]; var before = old.AsSpan((int)o.SerialOffset, (int)o.SerialSize).ToArray(); bool same = before.SequenceEqual(after);
                Require(o.ObjectName.ToString() == name && (same || expected.ContainsKey(name)), "unexpected fade export change " + (i + 1) + " " + name);
                item["classification"] = same ? "BYTE_IDENTICAL" : expected[name]; item["source_payload_sha256"] = Hash(before); item["source_serial_size"] = o.SerialSize;
                if (o is FunctionExport of && n is FunctionExport nf) { var bc = Bytecode(original, of, out _); var gc = Bytecode(generated, nf, out _); item["bytecode_unchanged"] = bc.SequenceEqual(gc); item["bytecode_size"] = new JsonArray(bc.Length, gc.Length); }
            } else { item["classification"] = "EXPECTED_NEW_FADE_TICK_HELPER"; if (n is FunctionExport nf) item["bytecode_size"] = Bytecode(generated, nf, out _).Length; }
            exports.Add(item);
        }
        var oi = original.Imports.Select(x => x.ObjectName.ToString()).ToArray(); var gi = generated.Imports.Select(x => x.ObjectName.ToString()).ToArray();
        var on = original.GetNameMapIndexList().Select(x => x.ToString()).ToArray(); var gn = generated.GetNameMapIndexList().Select(x => x.ToString()).ToArray();
        Require(gi.Take(oi.Length).SequenceEqual(oi) && gn.Take(on.Length).SequenceEqual(on), "fade changed existing imports/names");
        return new JsonObject { ["source"] = "round-019 " + RepairName + " (Run 6 pak WBP)", ["exports_source"] = original.Exports.Count, ["exports_generated"] = generated.Exports.Count,
            ["changed_exports"] = new JsonArray(exports.Where(e => Str(e!["classification"]) != "BYTE_IDENTICAL").Select(e => (JsonNode)V(Str(e!["name"]) + ": " + Str(e!["classification"]))).ToArray()),
            ["byte_identical_exports"] = exports.Count(e => Str(e!["classification"]) == "BYTE_IDENTICAL"), ["unexplained_changes"] = 0,
            ["added_imports"] = new JsonArray(gi.Skip(oi.Length).Select(s => (JsonNode)V("KismetMathLibrary." + s)).ToArray()),
            ["added_names"] = new JsonArray(gn.Skip(on.Length).Select(s => (JsonNode)V(s)).ToArray()), ["exports"] = exports };
    }

    static string[] FrozenFadeInputs(string root) => Directory.GetFiles(Path.Combine(root, Repair019Dir), "*", SearchOption.AllDirectories)
        .Concat(Directory.GetFiles(Path.Combine(root, StyleFix021Dir), "*", SearchOption.AllDirectories)).Append(Path.Combine(root, NativeEvidence023)).OrderBy(p => p, StringComparer.Ordinal).ToArray();
    static void SameFadeBytes(string dir) {
        foreach (string ext in new[] { ".uasset", ".uexp" }) foreach (string copy in new[] { "determinism", "roundtrip" })
            Require(File.ReadAllBytes(Path.ChangeExtension(FadeWbp023(dir), ext)).SequenceEqual(File.ReadAllBytes(Path.ChangeExtension(FadeWbp023(Path.Combine(dir, copy)), ext))), copy + " bytes differ " + ext);
    }

    public static int BuildFade023(string rootPath, string outputDirectory) {
        try {
            string root = Path.GetFullPath(rootPath), dir = Path.GetFullPath(outputDirectory);
            Require(dir.StartsWith(Path.GetFullPath(Path.Combine(root, "builds/rtl_poc")) + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase), "detached output required"); Require(!Directory.Exists(dir), "refusing existing files");
            GateFade023(root); var natives = Natives023(root); var sig = FadeSignatures023(natives); Require(sig.Count == 0, string.Join(";", sig));
            var frozen = FrozenFadeInputs(root); var hashes = frozen.Select(HashFile).ToArray();
            var src = Read(Repair019Wbp(root)); Require(src.VerifyBinaryEquality(), "019 source roundtrip");
            Directory.CreateDirectory(dir);
            File.WriteAllText(Path.Combine(dir, "NOT_INSTALLED.txt"), "R8B FADE 023 OFFLINE STAGING_ONLY NOT_INSTALLED NOT_RUNTIME_TESTED\nRound-019 WBP + Arabic Fade Tick (display-only per-word fade). Not tested in Unreal or in game. The Run 6 pak stays installed until Run 7 is approved.\n");
            WritePackage(GenerateFade023(Model(src)).Asset, FadeWbp023(dir));
            WritePackage(GenerateFade023(Model(Read(Repair019Wbp(root)))).Asset, FadeWbp023(Path.Combine(dir, "determinism")));
            Directory.CreateDirectory(Path.Combine(dir, "roundtrip")); Read(FadeWbp023(dir)).Write(FadeWbp023(Path.Combine(dir, "roundtrip")));
            SameFadeBytes(dir);
            var x = FadeContext(root, natives); var a = Model(Read(FadeWbp023(dir)));
            var errors = CheckFade023(a, x, out var contract, out var style); Require(errors.Count == 0, string.Join(";", errors.Take(12)));
            var negatives = NegativeFade023(a, x);
            // The round-019 ReturnContractR fixtures, re-run against the fade WBP with the round-024 evidence.
            GateRepairInputs019(root); var repaired011 = RepairTiming019(Model(Read(Reveal011Path(root))));
            var contractFixtures = NegativeRepair019(a, repaired011, natives, root);
            SaveJson(Path.Combine(dir, "instruction_inventory.json"), InstructionInventory(Read(FadeWbp023(dir))));
            var diff = DiffFade023(Repair019Wbp(root), FadeWbp023(dir)); SaveJson(Path.Combine(dir, "function_diff.json"), diff);
            Require(hashes.SequenceEqual(frozen.Select(HashFile)), "frozen inputs changed"); GateFade023(root);
            string ua = HashFile(FadeWbp023(dir)).ToLowerInvariant(), ue = HashFile(Path.ChangeExtension(FadeWbp023(dir), ".uexp")).ToLowerInvariant();
            SaveJson(Path.Combine(dir, "validation.json"), new JsonObject {
                ["status"] = "R8B_FADE_023_GENERATED", ["labels"] = new JsonArray("OFFLINE", "STAGING_ONLY", "NOT_INSTALLED", "NOT_RUNTIME_TESTED"), ["validator"] = "asset_inspector --validate-arabic-fade-023",
                ["validator_errors"] = 0, ["unexpected_changes"] = 0, ["fade_negative_fixtures"] = negatives, ["return_contract_fixtures"] = contractFixtures,
                ["return_contract"] = new JsonObject { ["call_sites"] = contract.Count, ["invalid"] = contract.Count(n => Str(n!["verdict"]) != "VALID"),
                    ["fade_tick_sites"] = new JsonArray(contract.Where(n => Str(n!["site"]).StartsWith(FadeTick + ":") || Str(n!["site"]).StartsWith(Helpers2[5] + ":") && Str(n!["callee"]).Contains("Less_IntInt")).Select(n => n!.DeepClone()).ToArray()) },
                ["RichTextStyleGate"] = new JsonObject { ["verdict"] = "PASS", ["bindings"] = style.Count(n => Str(n!["verdict"]) == ChildOk), ["sites"] = style },
                ["native_evidence"] = NativeEvidence023, ["fade_natives"] = new JsonArray(FadeNatives.Select(n => (JsonNode)V(n.Key + "(" + string.Join(",", n.Params) + ")->Float")).ToArray()),
                ["design"] = new JsonObject { ["tint_B"] = "ArabicFadeBase*(1+9.4*Alpha)", ["alpha"] = "FClamp((Due-Remainder+(Now-Stamp)-0.025)/(Due-0.025),0,1), 0 when Due-0.025<0.001",
                    ["fade_base"] = "Set Threshold Arabic: T<0 ? 1/10.5 : Blue", ["now"] = "AWP ? GetUnpausedTimeSeconds : GetTimeSeconds", ["writes_per_changed_frame"] = "2 SetContentColorAndOpacity + 2 RequestRender + ArabicLastBlue" },
                ["source_wbp"] = new JsonObject { ["path"] = Repair019Dir + "/" + RepairName, ["uasset_sha256"] = Inputs021[Repair019Dir + "/" + RepairName + ".uasset"], ["uexp_sha256"] = Inputs021[Repair019Dir + "/" + RepairName + ".uexp"] },
                ["dt_ar_tables_round_021_unchanged"] = new JsonObject(Tables021.Select(t => KeyValuePair.Create(t.Key, (JsonNode?)V(t.Value)))),
                ["frozen_inputs"] = new JsonArray(frozen.Select((p, i) => (JsonNode)new JsonObject { ["path"] = Path.GetRelativePath(root, p).Replace('\\', '/'), ["sha256"] = hashes[i] }).ToArray()),
                ["deterministic"] = true, ["roundtrip"] = true, ["uasset_sha256"] = ua, ["uexp_sha256"] = ue, ["IN_GAME_RTL_PROVEN"] = false, ["installed"] = false, ["tested_in_game"] = 0, ["final"] = 0 });
            Console.WriteLine("R8B_FADE_023_GENERATED: " + contract.Count + " call sites valid, " + negatives.Count + " fade fixtures + " + contractFixtures.Count + " return-contract fixtures, RichTextStyleGate 14, deterministic/roundtrip. " + dir); return 0;
        } catch (Exception ex) { Console.Error.WriteLine(ex.ToString()); return 1; }
    }

    public static int ValidateFade023(string rootPath, string directory) {
        try {
            string root = Path.GetFullPath(rootPath), dir = Path.GetFullPath(directory); GateFade023(root); var natives = Natives023(root);
            var report = JsonNode.Parse(File.ReadAllText(Path.Combine(dir, "validation.json")))!; Require(Str(report["status"]) == "R8B_FADE_023_GENERATED", "missing round-024 validation report");
            Require(HashFile(FadeWbp023(dir)).Equals(Str(report["uasset_sha256"]), StringComparison.OrdinalIgnoreCase) && HashFile(Path.ChangeExtension(FadeWbp023(dir), ".uexp")).Equals(Str(report["uexp_sha256"]), StringComparison.OrdinalIgnoreCase), "artifact hash changed");
            foreach (var entry in Arr(report, "frozen_inputs")) Require(HashFile(Path.Combine(root, Str(entry!["path"]))) == Str(entry["sha256"]), "frozen input hash changed " + Str(entry!["path"]));
            var asset = Read(FadeWbp023(dir)); Require(asset.VerifyBinaryEquality(), "fade binary roundtrip"); SameFadeBytes(dir);
            var x = FadeContext(root, natives); var a = Model(asset);
            var errors = CheckFade023(a, x, out var contract, out var style); Require(errors.Count == 0, string.Join(";", errors));
            var negatives = NegativeFade023(a, x);
            GateRepairInputs019(root); var contractFixtures = NegativeRepair019(a, RepairTiming019(Model(Read(Reveal011Path(root)))), natives, root);
            Console.WriteLine(new JsonObject { ["status"] = "R8B_FADE_023_PASS", ["errors"] = 0, ["return_contract_call_sites"] = contract.Count, ["return_contract_invalid"] = 0,
                ["RichTextStyleGate_bindings"] = style.Count(n => Str(n!["verdict"]) == ChildOk), ["negative_tests"] = negatives, ["return_contract_fixtures"] = contractFixtures,
                ["function_diff"] = DiffFade023(Repair019Wbp(root), FadeWbp023(dir)) }.ToJsonString(Pretty));
            return 0;
        } catch (Exception ex) { Console.Error.WriteLine(ex.ToString()); return 1; }
    }
}
