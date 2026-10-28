using System.Text.Json.Nodes;
using UAssetAPI;
using UAssetAPI.ExportTypes;

// Round 012 clock adapter (report_012): AWP=false -> K2_SetTimer + GetTimeSeconds; AWP=true -> Tick + GetUnpausedTimeSeconds.
// Input is the frozen 011 pair; 011, Stage1 and Stage2 are never regenerated.
static partial class ArabicStage1
{
    const string ClockName = "WBP_SubtitleBlock_AR_REVEAL_CLOCK";
    const string Reveal011Dir = "builds/rtl_poc/reveal_control_011";
    const string Reveal011Uasset = "859FDBAD998E390A20271D021117DF3C3761FED67409784BAE9BFF0E07FC0ADC";
    const string Reveal011Uexp = "F3B73603A0C8750424B164E0767C208AAE12C69F2399F7E440CD15802BD85A34";
    const string ClockImportEvidence = "reports/rtl_research/renderer_repair/scheduler_012/clock_imports_012.json";
    const string ExeSha = "365637a77d4b74a61d198a9927e3dcd437bf3be2247b96fcbe5c2e851ac14923";
    const string TimerTarget = "Arabic Clock Fired";
    const string Awp = "Animate While Paused";
    static readonly string[] ClockFunctions = { "Arabic Arm Clock", TimerTarget, "Arabic Paused Clock", "Tick" };
    static readonly string[] ClockEdited = { "Arabic Begin Reveal", "Arabic Finish", "Arabic Cancel" };
    static readonly string[] ForbiddenClocks = { "Delay", "RetriggerableDelay", "DelayUntilNextTick", "GetRealTimeSeconds", "GetWorldDeltaSeconds", "GetAccurateRealTime", "K2_SetTimerDelegate" };
    static string ClockPath(string dir) => Path.Combine(dir, ClockName + ".uasset");
    static string Reveal011Path(string root) => Path.Combine(root, Reveal011Dir, RevealName + ".uasset");
    static string FadePath(string root) => Path.Combine(root, SourceDir, "WBP_SimpleFadeSwitcher.uasset");
    static JsonObject SelfR() => X("Self");
    static JsonObject ClockLiveR(Build2Context c) => c.And(c.And(StateR("bArabicActive"), StateR("ArabicSchedulerArmed")), c.Not(StateR("ArabicFinished")));
    static JsonObject TimerR(Build2Context c, string fn, params JsonNode[] rest) => c.C("KismetSystemLibrary", fn, new JsonNode[] { SelfR(), SC(TimerTarget) }.Concat(rest).ToArray());

    static Build2Context GenerateClock(JsonObject baseline, string root) {
        var c = new Build2Context(baseline); var a = c.Asset; var exports = Arr(a, "Exports");
        for (int i = 0; i < exports.Count; i++) if (Str(exports[i]!["$type"]).Contains("FunctionExport")) c.Functions[Str(exports[i]!["ObjectName"])] = i + 1;
        foreach (string h in ClockFunctions) { int i = exports.Count + 1; var e = Copy(Export(a, "Stop Displaying Line")); e["ObjectName"] = h; exports.Add(e); Arr(a, "DependsMap").Add(new JsonArray()); c.Functions[h] = i; }
        c.State("Float", "ArabicClockStamp", JsonValue.Create(0f)!); c.State("Float", "ArabicClockRemainder", JsonValue.Create(-1f)!); c.State("Int", "ArabicClockGeneration", V(0));
        // Dropping the serialized false restores the UUserWidget constructor default (true), as in shipped WBP_SimpleFadeSwitcher.
        var cdo = Arr(Export(a, "Default__WBP_SubtitleBlock_C"), "Data"); cdo.Remove(cdo.Single(x => Str(x!["Name"]) == "bHasScriptImplementedTick"));
        GenerateClockHelpersR(c); GenerateTickR(c, root); EditClockHelpersR(c, baseline);
        var cls = Export(a, "WBP_SubtitleBlock_C");
        foreach (string h in ClockFunctions) { Arr(cls, "FuncMap").Add(new JsonArray(h, c.Functions[h])); Arr(cls, "Children").Add(c.Functions[h]); AddDep(cls, DepKeys[1], c.Functions[h]); }
        foreach (var p in c.Plans) exports[p.ExportIndex - 1]!["ScriptBytecode"] = new JsonArray(p.Cells.Select(x => (JsonNode)x.Code).ToArray());
        Names(a); Assemble2(c, baseline);
        foreach (var p in c.Plans) { var e = exports[p.ExportIndex - 1]!; foreach (int r in ScriptReferences2(e["ScriptBytecode"]).Concat(References(e["LoadedProperties"])).Where(x => x != 0 && x != 22 && x != p.ExportIndex).Distinct()) AddDep(e, DepKeys[1], r); }
        Names(a); return c;
    }

    static void ClockConsumeR(Build2Context c, Asm2 p, int f, JsonObject elapsed) {
        // Generation is captured before the budget call; a synchronous Finish->pool reuse must not be re-armed with this line.
        p.Emit(Assign2(f, "Gen", StateR("ArabicGeneration"), "Int"));
        p.Emit(Assign2(f, "Delta", c.C("KismetMathLibrary", "FMax", StateR("ArabicClockRemainder"), elapsed), "Float"));
        p.Emit(Assign2(22, "ArabicClockRemainder", FC(-1), "Float", true));
        p.Emit(Call2(c.Functions["Arabic Advance Budget"], Var2(f, "Delta"), Var2(f, "Gen")));
        p.Jump("return", c.IntEq(Var2(f, "Gen"), StateR("ArabicGeneration"))); p.Emit(Call2(c.Functions["Arabic Arm Clock"]));
        p.Mark("return"); p.Emit(Return2()); p.Emit(X("EndOfScript"));
    }

    static void GenerateClockHelpersR(Build2Context c) {
        var p = c.Function("Arabic Arm Clock", null); int f = p.ExportIndex; c.Local(f, "Float", "Due");
        p.Jump("return", c.And(ClockLiveR(c), c.Less(c.Add(StateR("ArabicCurrentUnit"), 1), StateR("ArabicUnitCount"))));
        p.Emit(c.C("KismetArrayLibrary", "Array_Get", StateR("ArabicUnitDelays"), c.Add(StateR("ArabicCurrentUnit"), 1), Var2(f, "Due")));
        p.Emit(Assign2(22, "ArabicClockRemainder", c.C("KismetMathLibrary", "Subtract_FloatFloat", Var2(f, "Due"), StateR("ArabicElapsed")), "Float", true));
        p.Emit(Assign2(22, "ArabicClockGeneration", StateR("ArabicGeneration"), "Int", true));
        p.Jump("world", StateR(Awp));
        p.Emit(Assign2(22, "ArabicClockStamp", c.C("GameplayStatics", "GetUnpausedTimeSeconds", SelfR()), "Float", true)); p.Jump("return");
        p.Mark("world"); p.Emit(Assign2(22, "ArabicClockStamp", c.C("GameplayStatics", "GetTimeSeconds", SelfR()), "Float", true));
        p.Emit(TimerR(c, "K2_SetTimer", StateR("ArabicClockRemainder"), BC(false), FC(0), FC(0)));
        p.Mark("return"); p.Emit(Return2()); p.Emit(X("EndOfScript"));

        p = c.Function(TimerTarget, null); f = p.ExportIndex; c.Local(f, "Int", "Gen"); c.Local(f, "Float", "Delta");
        p.Jump("return", c.Not(StateR(Awp)));
        p.Jump("return", c.And(ClockLiveR(c), c.IntEq(StateR("ArabicClockGeneration"), StateR("ArabicGeneration"))));
        ClockConsumeR(c, p, f, c.C("KismetMathLibrary", "Subtract_FloatFloat", c.C("GameplayStatics", "GetTimeSeconds", SelfR()), StateR("ArabicClockStamp")));

        p = c.Function("Arabic Paused Clock", null); f = p.ExportIndex; c.Local(f, "Int", "Gen"); c.Local(f, "Float", "Delta"); c.Local(f, "Float", "El");
        p.Jump("return", c.And(c.And(c.And(StateR("bArabicActive"), StateR(Awp)), c.And(StateR("ArabicSchedulerArmed"), c.Not(StateR("ArabicFinished")))),
            c.C("KismetMathLibrary", "GreaterEqual_FloatFloat", StateR("ArabicClockRemainder"), FC(0))));
        p.Emit(Assign2(f, "El", c.C("KismetMathLibrary", "Subtract_FloatFloat", c.C("GameplayStatics", "GetUnpausedTimeSeconds", SelfR()), StateR("ArabicClockStamp")), "Float"));
        p.Jump("return", c.C("KismetMathLibrary", "GreaterEqual_FloatFloat", Var2(f, "El"), StateR("ArabicClockRemainder")));
        ClockConsumeR(c, p, f, Var2(f, "El"));
    }

    static void GenerateTickR(Build2Context c, string root) {
        var template = Export(Model(Read(FadePath(root))), "Tick");
        Require(Str(template["FunctionFlags"]) == "FUNC_BlueprintCosmetic, FUNC_Event, FUNC_Public, FUNC_BlueprintEvent"
            && Arr(template, "LoadedProperties").Select(x => Str(x!["Name"]) + ":" + Str(x!["SerializedType"])).SequenceEqual(new[] { "MyGeometry:StructProperty", "InDeltaTime:FloatProperty" }), "shipped Tick template changed");
        var p = c.Function("Tick", null); int f = p.ExportIndex; var e = Arr(c.Asset, "Exports")[f - 1]!;
        int super = Import(c.Asset, "Tick", "", "Function", "/Script/CoreUObject", Class(c.Asset, "UserWidget"));
        int geometry = Import(c.Asset, "Geometry", "/Script/SlateCore", "ScriptStruct", "/Script/CoreUObject");
        e["FunctionFlags"] = template["FunctionFlags"]!.DeepClone(); e["SuperStruct"] = super; e["SuperIndex"] = super;
        var props = Arr(template, "LoadedProperties").DeepClone().AsArray(); props[0]!["Struct"] = geometry; e["LoadedProperties"] = props;
        AddDep(e, DepKeys[0], super); AddDep(e, DepKeys[0], geometry); AddDep(e, DepKeys[3], super);
        // Preview-only paused clock driver. InDeltaTime (Slate delta) is deliberately never read.
        p.Emit(Call2(c.Functions["Arabic Paused Clock"])); p.Emit(Return2()); p.Emit(X("EndOfScript"));
    }

    static void EditClockHelpersR(Build2Context c, JsonObject baseline) {
        foreach (string name in ClockEdited) {
            var code = Arr(Export(baseline, name), "ScriptBytecode"); var p = new Asm2 { ExportIndex = Index(baseline, name), Original = code.DeepClone().AsArray() }; c.Plans.Add(p);
            for (int i = 0; i < code.Count; i++) {
                if (name == "Arabic Finish" && IsOpR(code[i]!, "CallMulticastDelegate")) {  // broadcast stays last
                    p.Emit(TimerR(c, "K2_ClearTimer")); p.Emit(Assign2(22, "ArabicClockRemainder", FC(-1), "Float", true));
                }
                if (name == "Arabic Cancel" && IsOpR(code[i]!, "Return")) {
                    p.Emit(TimerR(c, "K2_ClearTimer")); p.Emit(Assign2(22, "ArabicClockRemainder", FC(-1), "Float", true)); p.Emit(Assign2(22, "ArabicClockStamp", FC(0), "Float", true));
                }
                p.Old(i);
                if (name == "Arabic Begin Reveal" && Num(code[i]!["StackNode"] ?? V(0)) == c.Functions["Arabic Advance Budget"]) p.Emit(Call2(c.Functions["Arabic Arm Clock"]));
            }
        }
    }

    // The JSON bridge writes some floats as strings ("+0").
    static float FloatR(JsonNode? n) => float.Parse(Str(n), System.Globalization.CultureInfo.InvariantCulture);
    static string CalleeR(JsonObject a, JsonNode? n) {
        if (n?["StackNode"] is not JsonValue v) return "";
        int s = v.GetValue<int>(); var imports = Arr(a, "Imports"); var exports = Arr(a, "Exports");
        return s < 0 && -s <= imports.Count ? Str(imports[-s - 1]!["ObjectName"]) : s > 0 && s <= exports.Count ? Str(exports[s - 1]!["ObjectName"]) : "";
    }
    static List<JsonObject> CallsR(JsonObject a, JsonNode? n, string callee) { var r = new List<JsonObject>(); JsonWalk2(n, "$", (o, _) => { if (CalleeR(a, o) == callee) r.Add(o); }); return r; }
    static bool ReadsR(JsonNode? n, string variable) { bool hit = false; JsonWalk2(n, "$", (o, _) => { if (Str(o["$type"]).Contains("FFieldPath") && Str(o["Path"]?[0]) == variable) hit = true; }); return hit; }
    // True when the variable is read outside any Not_PreBool (a positive guard term).
    static bool PositiveR(JsonObject a, JsonNode? n, string variable) {
        if (n is JsonObject o) { if (CalleeR(a, o) == "Not_PreBool") return false; if (IsOpR(o, "InstanceVariable") && Str(o["Variable"]?["New"]?["Path"]?[0]) == variable) return true; return o.Any(kv => PositiveR(a, kv.Value, variable)); }
        return n is JsonArray xs && xs.Any(x => PositiveR(a, x, variable));
    }
    static bool IsAwpR(JsonNode? n) => n is JsonObject o && IsOpR(o, "InstanceVariable") && Str(o["Variable"]?["New"]?["Path"]?[0]) == Awp;
    static HashSet<int> ReachableR(JsonArray code, int[] offsets, bool awp) {
        var seen = new HashSet<int>(); var todo = new Stack<int>(); todo.Push(0);
        while (todo.Count > 0) {
            int pc = todo.Pop(); if (pc < 0 || pc >= code.Count || !seen.Add(pc)) continue; var n = code[pc]!;
            if (IsOpR(n, "Jump")) { todo.Push(Array.IndexOf(offsets, Num(n["CodeOffset"]))); continue; }
            if (IsOpR(n, "JumpIfNot")) { bool? d = IsAwpR(n["BooleanExpression"]) ? awp : null; if (d != true) todo.Push(Array.IndexOf(offsets, Num(n["CodeOffset"]))); if (d != false) todo.Push(pc + 1); continue; }
            if (!IsOpR(n, "Return") && !IsOpR(n, "EndOfScript")) todo.Push(pc + 1);
        }
        return seen;
    }

    static void ClockSemanticsR(JsonObject a, Action<bool, string> T) {
        var typed = UAsset.DeserializeJson(a.ToJsonString());
        JsonArray Code(string name) => Arr(Export(a, name), "ScriptBytecode");
        int[] Offsets(string name) { var expr = ((StructExport)typed.Exports[Index(a, name) - 1]).ScriptBytecode!; var o = new int[expr.Length + 1]; for (int i = 0; i < expr.Length; i++) o[i + 1] = o[i] + Size2(typed, expr[i]); return o; }
        bool Top(JsonNode? n, string callee) => CalleeR(a, n) == callee;
        bool SetsR(JsonNode? n, string variable, float value) => n is JsonObject o && IsAssignmentR(o, variable) && IsOpR(o["Expression"]!, "FloatConst") && FloatR(o["Expression"]!["Value"]) == value;
        bool funcMap = Arr(Export(a, "WBP_SubtitleBlock_C"), "FuncMap").Any(x => Str(x![0]) == TimerTarget);
        foreach (var e in Arr(a, "Exports").Where(x => x!["ScriptBytecode"] != null)) {
            foreach (string fn in new[] { "K2_SetTimer", "K2_ClearTimer" }) foreach (var call in CallsR(a, e!["ScriptBytecode"], fn)) {
                var ps = Arr(call, "Parameters");
                T(funcMap && ps.Count >= 2 && IsOpR(ps[0]!, "Self") && IsOpR(ps[1]!, "StringConst") && Str(ps[1]!["Value"]) == TimerTarget, "timer function name mismatch");
                if (fn == "K2_SetTimer") T(ps.Count == 6 && ReadsR(ps[2], "ArabicClockRemainder") && IsOpR(ps[3]!, "False") && ps.Skip(4).All(x => IsOpR(x!, "FloatConst") && FloatR(x!["Value"]) == 0), "bad K2_SetTimer arguments");
            }
            foreach (string fn in ForbiddenClocks) T(CallsR(a, e!["ScriptBytecode"], fn).Count == 0, "forbidden clock source " + fn);
            T(CallsR(a, e!["ScriptBytecode"], "Arabic Advance Clocks").Count == 0, "unused Advance Clocks referenced");
        }
        var finish = Code("Arabic Finish"); int broadcast = finish.Select((x, i) => (x, i)).Where(x => IsOpR(x.x!, "CallMulticastDelegate")).Select(x => x.i).DefaultIfEmpty(-1).First();
        int clear = finish.Select((x, i) => (x, i)).Where(x => Top(x.x, "K2_ClearTimer")).Select(x => x.i).DefaultIfEmpty(-1).First();
        T(clear >= 0 && clear < broadcast, "Finish missing ClearTimer");
        T(finish.Take(Math.Max(broadcast, 0)).Any(x => SetsR(x, "ArabicClockRemainder", -1)), "Finish missing clock disarm");
        T(broadcast >= 0 && broadcast + 1 < finish.Count && IsOpR(finish[broadcast + 1]!, "Return"), "Finish broadcast not last");
        var cancel = Code("Arabic Cancel"); T(cancel.Any(x => Top(x, "K2_ClearTimer")), "Cancel missing ClearTimer");
        T(cancel.Any(x => SetsR(x, "ArabicClockRemainder", -1)) && cancel.Any(x => SetsR(x, "ArabicClockStamp", 0)), "Cancel missing clock reset");
        var begin = Code("Arabic Begin Reveal"); int budget = begin.Select((x, i) => (x, i)).Where(x => Top(x.x, "Arabic Advance Budget")).Select(x => x.i).DefaultIfEmpty(-2).First();
        T(budget >= 0 && budget + 1 < begin.Count && Top(begin[budget + 1], "Arabic Arm Clock"), "Begin Reveal does not arm clock");
        var fired = Export(a, TimerTarget); T(!Arr(fired, "LoadedProperties").Any(x => Str(x!["PropertyFlags"]).Contains("CPF_Parm")), "Clock Fired has parameters");
        var fc = Code(TimerTarget); T(fc.Count > 1 && IsOpR(fc[0]!, "JumpIfNot") && Top(fc[0]!["BooleanExpression"], "Not_PreBool") && IsAwpR(fc[0]!["BooleanExpression"]!["Parameters"]![0]), "Clock Fired missing AWP reject");
        T(fc.Count > 1 && ReadsR(fc[1]!["BooleanExpression"], "ArabicClockGeneration") && ReadsR(fc[1]!["BooleanExpression"], "ArabicGeneration"), "Clock Fired missing generation guard");
        var pc = Code("Arabic Paused Clock"); var guard = pc.Count > 0 && IsOpR(pc[0]!, "JumpIfNot") ? pc[0]!["BooleanExpression"] : null;
        T(guard != null && PositiveR(a, guard, Awp) && PositiveR(a, guard, "bArabicActive") && PositiveR(a, guard, "ArabicSchedulerArmed") && ReadsR(guard, "ArabicFinished") && ReadsR(guard, "ArabicClockRemainder"), "Paused Clock missing AWP guard");
        foreach (var (name, code) in new[] { (TimerTarget, fc), ("Arabic Paused Clock", pc) }) T(CallsR(a, code, "FMax").Count == 1, "missing FMax " + name);
        T(CallsR(a, fc, "GetTimeSeconds").Count == 1 && CallsR(a, fc, "GetUnpausedTimeSeconds").Count == 0 && CallsR(a, pc, "GetUnpausedTimeSeconds").Count == 1 && CallsR(a, pc, "GetTimeSeconds").Count == 0, "wrong clock source");
        T(CallsR(a, pc, "K2_SetTimer").Count == 0, "Paused Clock starts timer");
        var arm = Code("Arabic Arm Clock"); var armOffsets = Offsets("Arabic Arm Clock");
        var paused = ReachableR(arm, armOffsets, true); var world = ReachableR(arm, armOffsets, false);
        T(!paused.Any(i => CallsR(a, arm[i], "K2_SetTimer").Count > 0) && paused.Any(i => CallsR(a, arm[i], "GetUnpausedTimeSeconds").Count > 0), "Arm Clock starts timer in AWP mode");
        T(world.Any(i => CallsR(a, arm[i], "K2_SetTimer").Count > 0) && world.Any(i => CallsR(a, arm[i], "GetTimeSeconds").Count > 0), "Arm Clock missing gameplay timer");
        var armGuard = arm.Count > 0 && IsOpR(arm[0]!, "JumpIfNot") ? arm[0]!["BooleanExpression"] : null;
        T(new[] { "bArabicActive", "ArabicSchedulerArmed", "ArabicFinished", "ArabicCurrentUnit", "ArabicUnitCount" }.All(v => ReadsR(armGuard, v)), "Arm Clock guard incomplete");
        var cdo = Arr(Export(a, "Default__WBP_SubtitleBlock_C"), "Data");
        bool tickOff = cdo.Any(x => Str(x!["Name"]) == "bHasScriptImplementedTick" && x!["Value"]?.GetValue<bool>() != true);
        T(!tickOff && Arr(Export(a, "WBP_SubtitleBlock_C"), "FuncMap").Any(x => Str(x![0]) == "Tick"), "Blueprint Tick disabled");
        var tick = Export(a, "Tick"); int super = Num(tick["SuperStruct"]); var imports = Arr(a, "Imports");
        bool signature = super < 0 && Str(imports[-super - 1]!["ObjectName"]) == "Tick" && Num(imports[-super - 1]!["OuterIndex"]) is int o && o < 0 && Str(imports[-o - 1]!["ObjectName"]) == "UserWidget"
            && Str(tick["FunctionFlags"]).Contains("FUNC_Event") && Arr(tick, "LoadedProperties").Select(x => Str(x!["Name"])).SequenceEqual(new[] { "MyGeometry", "InDeltaTime" })
            && Num(Arr(tick, "LoadedProperties")[0]!["Struct"]) is int g && g < 0 && Str(imports[-g - 1]!["ObjectName"]) == "Geometry";
        T(signature, "Tick signature differs from UserWidget:Tick");
        var tc = Arr(tick, "ScriptBytecode"); T(tc.Count == 3 && Top(tc[0], "Arabic Paused Clock") && Arr(tc[0]!, "Parameters").Count == 0, "Tick does not only call Paused Clock");
        T(!ReadsR(tc, "InDeltaTime") && !ReadsR(tc, "MyGeometry"), "Tick reads InDeltaTime");
    }

    static List<string> CheckClock(JsonObject actual, JsonObject baseline, string root) {
        var errors = new List<string>(); void T(bool ok, string why) { if (!ok) errors.Add(why); }
        var expected = GenerateClock(baseline, root);
        T(JsonNode.DeepEquals(Projection(actual), Projection(Normalize(expected.Asset))), "unexpected clock schema change");
        T(Arr(actual, "NameMap").Take(Arr(baseline, "NameMap").Count).Select(Str).SequenceEqual(Arr(baseline, "NameMap").Select(Str)), "frozen name indices changed");
        T(JsonNode.DeepEquals(new JsonArray(Arr(actual, "Imports").Take(Arr(baseline, "Imports").Count).Select(x => x!.DeepClone()).ToArray()), baseline["Imports"]), "frozen imports changed");
        var paced = new[] { "Arabic Step", "Arabic Advance Budget", "Arabic Advance Clocks", "Arabic Finish" }.Concat(ClockFunctions);
        if (RevealInvariantsR(actual, baseline, expected.Functions, paced, T)) return errors;
        // Jump/context/size certificates cover every function, not only the edited ones (011 fixtures stay exact).
        var planned = expected.Plans.Select(p => p.ExportIndex).ToHashSet();
        var everyFunction = Arr(actual, "Exports").Select((x, i) => (x, i: i + 1)).Where(x => x.x!["ScriptBytecode"] is JsonArray && !planned.Contains(x.i)).Select(x => new Asm2 { ExportIndex = x.i });
        RevealBytecodeR(actual, baseline, expected.Plans.Concat(everyFunction).ToList(), T);
        foreach (var old in Arr(baseline, "Exports").Where(x => Str(x!["$type"]).Contains("FunctionExport")))
            if (!ClockEdited.Contains(Str(old!["ObjectName"]))) T(JsonNode.DeepEquals(old["ScriptBytecode"], Export(actual, Str(old["ObjectName"]))["ScriptBytecode"]), "untouched function changed " + Str(old["ObjectName"]));
        try { ClockSemanticsR(actual, T); } catch (Exception ex) { errors.Add("malformed clock adapter: " + ex.Message); }
        DependencyCycles(actual, errors); return errors;
    }

    static JsonArray DiffClock(string originalPath, string generatedPath) {
        var original = Read(originalPath); var generated = Read(generatedPath); var result = new JsonArray();
        var allowed = ClockEdited.Concat(new[] { "WBP_SubtitleBlock_C", "Default__WBP_SubtitleBlock_C" }).ToArray();
        var old = File.ReadAllBytes(originalPath).Concat(File.ReadAllBytes(Path.ChangeExtension(originalPath, ".uexp"))).ToArray(); var now = File.ReadAllBytes(generatedPath).Concat(File.ReadAllBytes(Path.ChangeExtension(generatedPath, ".uexp"))).ToArray();
        for (int i = 0; i < original.Exports.Count; i++) {
            var o = original.Exports[i]; var n = generated.Exports[i]; string name = o.ObjectName.ToString(); var before = old.AsSpan((int)o.SerialOffset, (int)o.SerialSize).ToArray(); var after = now.AsSpan((int)n.SerialOffset, (int)n.SerialSize).ToArray();
            bool same = before.SequenceEqual(after); Require(same || allowed.Contains(name), "unexpected clock export change " + (i + 1) + " " + name);
            var item = new JsonObject { ["export"] = i + 1, ["name"] = name, ["classification"] = same ? "BYTE_IDENTICAL" : "EXPECTED_CLOCK_ADAPTER_CHANGE", ["source_payload_sha256"] = Hash(before), ["generated_payload_sha256"] = Hash(after) };
            if (o is FunctionExport of && n is FunctionExport nf) { var b = Bytecode(original, of, out _); var c = Bytecode(generated, nf, out _); item["bytecode_unchanged"] = b.SequenceEqual(c); if (!ClockEdited.Contains(name)) Require(b.SequenceEqual(c), "untouched clock function changed " + name); }
            result.Add(item);
        }
        return result;
    }

    static JsonArray NegativeClock(JsonObject good, JsonObject baseline, string root) {
        var results = new JsonArray();
        void Run(string name, Action<JsonObject> mutate, string diagnostic) { var bad = Copy(good); mutate(bad); var errors = CheckClock(bad, baseline, root); Require(errors.Any(x => x.Contains(diagnostic)), "negative fixture missed " + name + " / " + string.Join(";", errors.Take(6))); results.Add(new JsonObject { ["fixture"] = name, ["detected"] = true, ["diagnostics"] = new JsonArray(errors.Take(5).Select(x => (JsonNode)V(x)).ToArray()) }); }
        JsonArray Code(JsonObject a, string n) => Arr(Export(a, n), "ScriptBytecode");
        JsonNode TopCall(JsonObject a, string fn, string callee) => Code(a, fn).First(x => CalleeR(a, x) == callee)!;
        Run("Finish without ClearTimer", a => Code(a, "Arabic Finish").Remove(TopCall(a, "Arabic Finish", "K2_ClearTimer")), "Finish missing ClearTimer");
        Run("Cancel without ClearTimer", a => Code(a, "Arabic Cancel").Remove(TopCall(a, "Arabic Cancel", "K2_ClearTimer")), "Cancel missing ClearTimer");
        Run("wrong timer function-name string", a => CallsR(a, Code(a, "Arabic Arm Clock"), "K2_SetTimer")[0]["Parameters"]![1]!["Value"] = "Arabic Clock Fire", "timer function name mismatch");
        Run("Clock Fired with parameters", a => Arr(Export(a, TimerTarget), "LoadedProperties").First(x => Str(x!["Name"]) == "Gen")!["PropertyFlags"] = "CPF_Parm", "Clock Fired has parameters");
        Run("Paused Clock without AWP guard", a => JsonWalk2(Code(a, "Arabic Paused Clock")[0], "$", (o, _) => { if (IsAwpR(o)) o["Variable"]!["New"]!["Path"]![0] = "bArabicActive"; }), "Paused Clock missing AWP guard");
        Run("Arm Clock starting timer in AWP mode", a => { var s = Code(a, "Arabic Arm Clock"); int i = s.Select((x, k) => (x, k)).First(x => CallsR(a, x.x, "GetUnpausedTimeSeconds").Count > 0).k; s.Insert(i + 1, TopCall(a, "Arabic Arm Clock", "K2_SetTimer").DeepClone()); }, "Arm Clock starts timer in AWP mode");
        Run("missing FMax", a => { var n = Code(a, TimerTarget).First(x => CallsR(a, x, "FMax").Count > 0)!; n["Expression"] = StateR("ArabicClockRemainder"); }, "missing FMax");
        Run("Blueprint Tick disabled", a => Arr(Export(a, "Default__WBP_SubtitleBlock_C"), "Data").Add(P("Bool", "bHasScriptImplementedTick", JsonValue.Create(false))), "Blueprint Tick disabled");
        Run("Tick reads InDeltaTime", a => Code(a, "Tick").Insert(0, Assign2(Index(a, "Tick"), "InDeltaTime", Var2(Index(a, "Tick"), "InDeltaTime"), "Float")), "Tick reads InDeltaTime");
        // The six 011 control fixtures still have to be caught by the clock validator.
        Run("double-finish broadcast", a => { var s = Code(a, "Arabic Finish"); s.Insert(s.Count - 2, s.Single(x => IsOpR(x!, "CallMulticastDelegate"))!.DeepClone()); }, "double finish broadcast");
        Run("missing scheduler clear", a => Code(a, "Arabic Cancel").Single(x => IsAssignmentR(x!, "ArabicSchedulerArmed"))!["AssignmentExpression"] = BC(true), "missing scheduler clear");
        Run("bad scheduler jump", a => Code(a, "Arabic Advance Budget").First(x => IsOpR(x!, "JumpIfNot"))!["CodeOffset"] = 3, "bad scheduler jump");
        Run("unpaired shadow update", a => { var s = Code(a, Helpers2[5]); s.Remove(s.First(x => Str(x).Contains("ArabicShadowBorder"))); }, "unpaired shadow threshold update");
        Run("SetText inside Arabic Step", a => Code(a, "Arabic Step").Insert(0, Method2(Widgets[2], -128, SC("bad"))), "reveal-time SetText/style mutation");
        Run("missing pool reset", a => { var s = Code(a, "Arabic Cancel"); s.Remove(s.Single(x => IsAssignmentR(x!, "ArabicUnitCount"))); }, "missing pool reset ArabicUnitCount");
        return results;
    }

    static string[] FrozenClockInputs(string root) => new[] { "builds/rtl_poc/stage1", "builds/rtl_poc/stage2", Reveal011Dir }
        .SelectMany(d => Directory.GetFiles(Path.Combine(root, d), "*", SearchOption.AllDirectories)).OrderBy(x => x, StringComparer.Ordinal).ToArray();

    public static int BuildClock(string rootPath, string outputDirectory) {
        try {
            string root = Path.GetFullPath(rootPath), dir = Path.GetFullPath(outputDirectory);
            Require(dir.StartsWith(Path.GetFullPath(Path.Combine(root, "builds/rtl_poc")) + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase), "detached output required"); Require(!Directory.Exists(dir), "refusing existing files");
            string source = Reveal011Path(root);
            Require(HashFile(source) == Reveal011Uasset && HashFile(Path.ChangeExtension(source, ".uexp")) == Reveal011Uexp, "011 frozen pair hash mismatch");
            var evidence = JsonNode.Parse(File.ReadAllText(Path.Combine(root, ClockImportEvidence)))!;
            Require(Str(evidence["exe_sha256"]) == ExeSha && new[] { "K2_SetTimer", "K2_ClearTimer", "GetTimeSeconds", "GetUnpausedTimeSeconds", "FMax", "Tick" }.All(f => evidence["functions"]?[f] != null) && evidence["geometry_import"] != null, "shipped reflection evidence missing");
            var frozen = FrozenClockInputs(root); var hashes = frozen.Select(HashFile).ToArray(); string fadeHash = HashFile(FadePath(root));
            var src = Read(source); Require(src.VerifyBinaryEquality(), "011 source roundtrip"); var baseline = Model(src);
            Directory.CreateDirectory(dir); File.WriteAllText(Path.Combine(dir, "NOT_INSTALLABLE.txt"), "REVEAL CLOCK ADAPTER OFFLINE NOT_INSTALLABLE NOT_RUNTIME_TESTED\nAWP=false K2_SetTimer+GetTimeSeconds; AWP=true Tick+GetUnpausedTimeSeconds. Not tested in Unreal or in game.\n");
            WritePackage(GenerateClock(baseline, root).Asset, ClockPath(dir)); var a = Model(Read(ClockPath(dir)));
            var errors = CheckClock(a, baseline, root); Require(errors.Count == 0, string.Join(";", errors.Take(12)));
            string repeat = Path.Combine(dir, "determinism"), roundtrip = Path.Combine(dir, "roundtrip");
            WritePackage(GenerateClock(baseline, root).Asset, ClockPath(repeat)); Directory.CreateDirectory(roundtrip); Read(ClockPath(dir)).Write(ClockPath(roundtrip));
            foreach (string ext in new[] { ".uasset", ".uexp" }) foreach (string target in new[] { repeat, roundtrip })
                Require(File.ReadAllBytes(Path.ChangeExtension(ClockPath(dir), ext)).SequenceEqual(File.ReadAllBytes(Path.ChangeExtension(ClockPath(target), ext))), "clock determinism/roundtrip " + ext);
            SaveJson(Path.Combine(dir, "instruction_inventory.json"), InstructionInventory(Read(ClockPath(dir))));
            var diff = DiffClock(source, ClockPath(dir)); var negatives = NegativeClock(a, baseline, root);
            Require(hashes.SequenceEqual(frozen.Select(HashFile)) && HashFile(FadePath(root)) == fadeHash, "frozen inputs changed");
            SaveJson(Path.Combine(dir, "clock_verification.json"), new JsonObject {
                ["status"] = "R8B_WBP_CLOCK_ADAPTER_GENERATED", ["replay"] = "tools/asset_inspector/test_clock.py", ["validator_errors"] = 0, ["unexpected_changes"] = 0,
                ["source_011"] = new JsonObject { ["uasset_sha256"] = Reveal011Uasset, ["uexp_sha256"] = Reveal011Uexp }, ["tick_template"] = new JsonObject { ["path"] = Path.GetRelativePath(root, FadePath(root)), ["sha256"] = fadeHash },
                ["import_evidence"] = ClockImportEvidence, ["unused_helpers"] = new JsonArray("Arabic Advance Clocks"),
                ["timing_policy"] = new JsonObject { ["AnimateWhilePaused_false"] = "K2_SetTimer + GetTimeSeconds (canonical gameplay path)", ["AnimateWhilePaused_true"] = "Blueprint Tick + GetUnpausedTimeSeconds (preview only)" },
                ["negative_tests"] = negatives, ["original_export_diff"] = diff,
                ["frozen_inputs"] = new JsonArray(frozen.Select((p, i) => (JsonNode)new JsonObject { ["path"] = Path.GetRelativePath(root, p), ["sha256"] = hashes[i] }).ToArray()),
                ["deterministic"] = true, ["roundtrip"] = true, ["uasset_sha256"] = HashFile(ClockPath(dir)), ["uexp_sha256"] = HashFile(Path.ChangeExtension(ClockPath(dir), ".uexp")),
                ["DISPATCH_INTEGRATION_PROVEN"] = false, ["IN_GAME_RTL_PROVEN"] = false, ["tested_in_game"] = 0, ["final"] = 0 });
            Console.WriteLine("R8B_WBP_CLOCK_ADAPTER_GENERATED: " + negatives.Count + " negative fixtures, deterministic, roundtrip. " + dir); return 0;
        } catch (Exception ex) { Console.Error.WriteLine(ex.ToString()); return 1; }
    }
    public static int ValidateClock(string rootPath, string directory) {
        try {
            string root = Path.GetFullPath(rootPath), dir = Path.GetFullPath(directory); string source = Reveal011Path(root);
            Require(HashFile(source) == Reveal011Uasset && HashFile(Path.ChangeExtension(source, ".uexp")) == Reveal011Uexp, "011 frozen pair hash mismatch");
            var baseline = Model(Read(source)); var a = Read(ClockPath(dir)); Require(a.VerifyBinaryEquality(), "clock binary roundtrip");
            var errors = CheckClock(Model(a), baseline, root); Require(errors.Count == 0, string.Join(";", errors));
            var report = JsonNode.Parse(File.ReadAllText(Path.Combine(dir, "clock_verification.json")))!;
            foreach (var entry in Arr(report, "frozen_inputs")) Require(HashFile(Path.Combine(root, Str(entry!["path"]))) == Str(entry["sha256"]), "frozen input hash changed");
            foreach (string ext in new[] { ".uasset", ".uexp" }) foreach (string copy in new[] { "determinism", "roundtrip" })
                Require(File.ReadAllBytes(Path.ChangeExtension(ClockPath(dir), ext)).SequenceEqual(File.ReadAllBytes(Path.ChangeExtension(ClockPath(Path.Combine(dir, copy)), ext))), "clock binary evidence mismatch");
            Console.WriteLine(new JsonObject { ["status"] = "CLOCK_ADAPTER_STRUCTURE_PASS", ["errors"] = 0, ["negative_tests"] = NegativeClock(Model(a), baseline, root), ["original_export_diff"] = DiffClock(source, ClockPath(dir)) }.ToJsonString(Pretty));
            return 0;
        } catch (Exception ex) { Console.Error.WriteLine(ex.ToString()); return 1; }
    }
}
