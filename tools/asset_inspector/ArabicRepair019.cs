using System.Text.Json.Nodes;
using UAssetAPI.ExportTypes;

// Round 019 (report_019): Build Arabic Timing becomes a void helper. Run 2 crashed because Set Displayed Line:66 called it as
// a bare statement while it still returned FString, so the VM copied the markup into its uninitialized scratch buffer.
// The repaired WBP is rebuilt from clean source (frozen 011 -> repair -> 012 clock generator) and must byte-equal the repair
// applied to the frozen 012 pair; 011/012 and earlier artifacts are never regenerated.
static partial class ArabicStage1
{
    const string RepairName = "WBP_SubtitleBlock_AR_R8B_REPAIR_019";
    const string Clock012Uasset = "29EDA3A7C8404DD4CE454590096F4ACC83267B6065CB32B3DA828286D20B4397";
    const string Clock012Uexp = "C6546290DB8678EB987A57ABCA17B17DA6E7B76DD706AB3F9BF4208ABE8260C5";
    const string NativeEvidence = "reports/rtl_research/renderer_repair/r8b_repair_019/native_returns_019.json";
    const string Timing = "Build Arabic Timing";
    static string RepairPath(string dir) => Path.Combine(dir, RepairName + ".uasset");
    static string Clock012Path(string root) => Path.Combine(root, "builds/rtl_poc/reveal_clock_012", ClockName + ".uasset");

    // Removes the FString ReturnValue (CPF_Parm|CPF_OutParm|CPF_ReturnParm) and FUNC_HasOutParms; Return Local(Output) -> Return Nothing.
    static JsonObject RepairTiming019(JsonObject source) {
        var c = new Build2Context(source); var a = c.Asset; int f = Index(a, Timing); var e = Export(a, Timing); var props = Arr(e, "LoadedProperties");
        var ret = props.Where(p => Str(p!["PropertyFlags"]).Contains("CPF_ReturnParm")).ToArray();
        Require(ret.Length == 1 && Str(ret[0]!["Name"]) == "ReturnValue" && Str(ret[0]!["SerializedType"]) == "StrProperty", "unexpected Build Arabic Timing return property");
        var code = Arr(e, "ScriptBytecode"); var returns = code.Select((x, i) => (x, i)).Where(x => IsOpR(x.x!, "Return")).ToArray();
        Require(returns.Length == 1 && returns[0].i == code.Count - 2 && IsOpR(code[^1]!, "EndOfScript") && IsOpR(code[returns[0].i]!["ReturnExpression"]!, "LocalVariable")
            && Str(code[returns[0].i]!["ReturnExpression"]!["Variable"]!["New"]!["Path"]![0]) == "Output", "unexpected Build Arabic Timing return statement");
        // The returned markup must be unused: the only call site is a top-level statement (the Run 2 site).
        Require(CallSites019(a, f).SequenceEqual(new[] { ("Set Displayed Line", true) }), "Build Arabic Timing return value has a consumer");
        props.Remove(ret[0]);
        Require(!props.Any(p => Str(p!["PropertyFlags"]).Contains("CPF_OutParm")), "Build Arabic Timing keeps an out parameter");
        e["FunctionFlags"] = string.Join(", ", Str(e["FunctionFlags"]).Split(", ").Where(x => x != "FUNC_HasOutParms"));
        var p = new Asm2 { ExportIndex = f, Original = code.DeepClone().AsArray() }; c.Plans.Add(p);
        for (int i = 0; i < code.Count; i++) if (i == returns[0].i) p.Emit(Return2()); else p.Old(i);
        e["ScriptBytecode"] = new JsonArray(p.Cells.Select(x => (JsonNode)x.Code).ToArray());
        Names(a); Assemble2(c, source); return a;
    }
    // (caller, top-level statement?) for every call of export f.
    static List<(string, bool)> CallSites019(JsonObject a, int f) {
        var result = new List<(string, bool)>(); string name = Str(Arr(a, "Exports")[f - 1]!["ObjectName"]);
        foreach (var e in Arr(a, "Exports").Where(x => x!["ScriptBytecode"] is JsonArray)) foreach (var ins in Arr(e!, "ScriptBytecode"))
            JsonWalk2(ins, "$", (o, path) => { if (o["StackNode"] is JsonValue v && Num(v) == f || Str(o["VirtualFunctionName"]) == name) result.Add((Str(e!["ObjectName"]), path == "$")); });
        return result;
    }

    // Frame-safety rule (round 019). A call writes its return value through RESULT_PARAM, so every call must sit where the VM
    // provides constructed storage of the callee's return type. A top-level statement receives ProcessLocalScriptFunction's
    // uninitialized 64-byte scratch buffer: only void, scalars or a struct whose native thunk plainly stores it may land there.
    // Script out-parameters are evaluated with a null RESULT_PARAM. Native signatures come from the EXE evidence JSON.
    static readonly string[] ScratchSafe = { "Bool", "Byte", "Int8", "Int16", "Int", "Int64", "UInt16", "UInt32", "UInt64", "Float", "Double", "Name", "Object", "Class", "Enum" };
    static readonly string[] CallOps = { "LocalFinalFunction", "FinalFunction", "CallMath", "VirtualFunction", "LocalVirtualFunction", "CallMulticastDelegate" };
    static readonly string[] StatementOps = { "Let", "LetBool", "LetObj", "LetWeakObjPtr", "LetDelegate", "LetMulticastDelegate", "LetValueOnPersistentFrame", "Jump",
        "JumpIfNot", "Return", "EndOfScript", "PushExecutionFlow", "PopExecutionFlow", "PopExecutionFlowIfNot", "ComputedJump", "SetArray", "SetSet", "SetMap",
        "BindDelegate", "AddMulticastDelegate", "RemoveMulticastDelegate", "ClearMulticastDelegate", "Nothing", "Tracepoint", "WireTracepoint", "Context", "Context_FailSilent" };
    sealed record Sig019(string Key, string? Ret, string[]? Params, bool[]? NullArgs, bool TrivialStore, bool Wildcard);
    static string Op019(JsonNode? n) { string t = Str(n?["$type"]); int i = t.IndexOf(".EX_"); return i < 0 ? "" : t[(i + 4)..t.IndexOf(',')]; }
    static string Type019(JsonNode p) => Str(p["SerializedType"]).Replace("Property", "");
    static bool Compatible019(string value, string slot) => value == slot || new[] { value, slot }.All(x => x is "Object" or "Class") || new[] { value, slot }.All(x => x is "Byte" or "Enum");
    static string? PtrType019(JsonObject a, JsonNode? ptr) {
        var f = ptr?["New"] ?? ptr; if (f?["ResolvedOwner"] is not JsonValue v || Num(v) <= 0 || f["Path"] is not JsonArray path || path.Count == 0) return null;
        var p = (Arr(a, "Exports")[Num(v) - 1]!["LoadedProperties"] as JsonArray)?.FirstOrDefault(x => Str(x!["Name"]) == Str(path[0]));
        return p == null ? null : Type019(p);
    }
    static Sig019? Signature019(JsonObject a, JsonObject call, JsonNode natives) {
        var exports = Arr(a, "Exports"); var imports = Arr(a, "Imports"); int s = call["StackNode"] is JsonValue v ? Num(v) : 0; string name = Str(call["VirtualFunctionName"]);
        int local = s > 0 ? s : name == "" ? 0 : exports.Select((x, i) => (x, i)).Where(x => Str(x.x!["$type"]).Contains("FunctionExport") && Str(x.x!["ObjectName"]) == name).Select(x => x.i + 1).FirstOrDefault();
        if (local > 0) {
            var parms = Arr(exports[local - 1]!, "LoadedProperties").Where(p => Str(p!["PropertyFlags"]).Contains("CPF_Parm")).ToArray();
            var args = parms.Where(p => !Str(p!["PropertyFlags"]).Contains("CPF_ReturnParm")).ToArray(); var ret = parms.FirstOrDefault(p => Str(p!["PropertyFlags"]).Contains("CPF_ReturnParm"));
            return new(Str(exports[local - 1]!["ObjectName"]), ret == null ? null : Type019(ret), args.Select(p => Type019(p!)).ToArray(), args.Select(p => Str(p!["PropertyFlags"]).Contains("CPF_OutParm")).ToArray(), false, false);
        }
        string key = name;
        if (s < 0) { var imp = imports[-s - 1]!; int o = Num(imp["OuterIndex"]); key = (o < 0 ? Str(imports[-o - 1]!["ObjectName"]) + "." : "") + Str(imp["ObjectName"]); }
        var e = natives["functions"]?[key]; if (e == null || Str(e["return"]) == "UNRESOLVED") return null;
        var ps = e["params"] as JsonArray;
        return new(key, e["return"] is JsonValue r ? r.ToString() : null, ps?.Select(p => Str(p!["type"])).ToArray(), ps?.Select(_ => false).ToArray(),
            e["trivial_store"]?["trivial"]?.GetValue<bool>() == true, e["wildcard"]?.GetValue<bool>() == true);
    }
    static JsonArray ReturnContractR(JsonObject a, JsonNode natives, Action<bool, string> T) {
        var audit = new JsonArray(); var exports = Arr(a, "Exports");
        for (int fi = 0; fi < exports.Count; fi++) {
            if (exports[fi]!["ScriptBytecode"] is not JsonArray code) continue;
            string fn = Str(exports[fi]!["ObjectName"]);
            var retProp = (exports[fi]!["LoadedProperties"] as JsonArray)?.FirstOrDefault(p => Str(p!["PropertyFlags"]).Contains("CPF_ReturnParm"));
            string fnRet = retProp == null ? "VOIDRET" : "T:" + Type019(retProp);
            for (int idx = 0; idx < code.Count; idx++) {
                string where = fn + ":" + idx, top = Op019(code[idx]);
                T(StatementOps.Contains(top) || CallOps.Contains(top), "value expression at statement level " + where + " EX_" + top);
                Walk(code[idx], "SCRATCH", where);
            }
            void Walk(JsonNode? n, string dest, string where) {
                if (n is JsonArray xs) { foreach (var x in xs) Walk(x, dest, where); return; }
                if (n is not JsonObject o) return;
                string op = Op019(o);
                void W(string field, string d) => Walk(o[field], d, where);
                if (CallOps.Contains(op)) {
                    var sig = Signature019(a, o, natives); if (op == "CallMulticastDelegate") W("Delegate", "NULL");
                    string callee = sig?.Key ?? Str(o["VirtualFunctionName"]) + Str(o["StackNode"]);
                    var row = new JsonObject { ["site"] = where, ["opcode"] = "EX_" + op, ["callee"] = callee, ["return"] = sig == null ? "UNRESOLVED" : sig.Ret ?? "void", ["destination"] = dest };
                    if (sig == null) { T(false, "unresolved callee signature " + where + " " + callee); row["verdict"] = "INVALID"; audit.Add(row); foreach (var x in Arr(o, "Parameters")) Walk(x, "UNKNOWN_PARAM", where); return; }
                    string what = where + " " + sig.Key + " -> " + (sig.Ret ?? "void");
                    bool ok = dest switch {
                        "SCRATCH" => sig.Ret == null || ScratchSafe.Contains(sig.Ret) || sig.Ret == "Struct" && sig.TrivialStore,
                        "ANY" => sig.Ret != null,
                        _ when dest.StartsWith("T:") => sig.Ret != null && Compatible019(sig.Ret, dest[2..]),
                        _ => false };
                    if (!ok) T(false, (dest == "SCRATCH" ? "unsafe statement-level non-trivial return " : dest.StartsWith("T:") || dest == "ANY" ? "invalid result destination " : "call result into " + dest + " destination ") + what + (dest.StartsWith("T:") ? " into " + dest[2..] : ""));
                    row["verdict"] = ok ? "VALID" : "INVALID"; audit.Add(row);
                    var args = Arr(o, "Parameters");
                    if (sig.Params != null) T(args.Count == sig.Params.Length, "argument count mismatch " + what);
                    for (int i = 0; i < args.Count; i++)
                        Walk(args[i], sig.Params == null || i >= sig.Params.Length ? "UNKNOWN_PARAM" : sig.NullArgs![i] ? "NULL" : sig.Wildcard ? "ANY" : "T:" + sig.Params[i], where);
                    return;
                }
                // Variables and constants copy their own type into the destination (CopyCompleteValueToScriptVM / *(T*)RESULT_PARAM).
                string? value = op switch {
                    "LocalVariable" or "InstanceVariable" or "LocalOutVariable" or "DefaultVariable" => PtrType019(a, o["Variable"]),
                    "IntConst" or "IntConstByte" or "IntZero" or "IntOne" => "Int", "FloatConst" => "Float", "StringConst" or "UnicodeStringConst" => "Str",
                    "TextConst" => "Text", "NameConst" => "Name", "ByteConst" => "Byte", "True" or "False" => "Bool", "ObjectConst" or "NoObject" or "Self" => "Object", _ => null };
                if (value != null && dest.StartsWith("T:")) T(Compatible019(value, dest[2..]), "invalid value destination " + where + " EX_" + op + " " + value + " into " + dest[2..]);
                switch (op) {
                    case "Let": W("Variable", "NULL"); W("Expression", PtrType019(a, o["Value"]) is string t ? "T:" + t : "ANY"); return;
                    case "LetBool": W("VariableExpression", "NULL"); W("AssignmentExpression", "T:Bool"); return;
                    case "LetObj": W("VariableExpression", "NULL"); W("AssignmentExpression", "T:Object"); return;
                    case "LetValueOnPersistentFrame": W("AssignmentExpression", PtrType019(a, o["DestinationProperty"]) is string pt ? "T:" + pt : "ANY"); return;
                    case "JumpIfNot": W("BooleanExpression", "T:Bool"); return;
                    case "ComputedJump": W("CodeOffsetExpression", "T:Int"); return;
                    case "Return": if (fnRet == "VOIDRET") T(Op019(o["ReturnExpression"]) == "Nothing", "value returned from void function " + where); else W("ReturnExpression", fnRet); return;
                    case "Context" or "Context_FailSilent" or "ClassContext":
                        W("ObjectExpression", "T:Object");
                        bool rvNull = o["RValuePointer"]?["New"]?["Path"] is JsonArray rp && rp.Count == 0; string? rv = PtrType019(a, o["RValuePointer"]);
                        if (!rvNull && dest == "SCRATCH") T(rv != null && ScratchSafe.Contains(rv), "unsafe statement-level context r-value " + where);
                        if (!rvNull && dest.StartsWith("T:") && rv != null) T(Compatible019(rv, dest[2..]), "context r-value type mismatch " + where);
                        W("ContextExpression", dest); return;
                    case "SwitchValue": W("IndexTerm", "NULL"); foreach (var k in Arr(o, "Cases")) { Walk(k!["CaseIndexValueTerm"], "ANY", where); Walk(k["CaseTerm"], dest, where); } W("DefaultTerm", dest); return;
                    case "StructMemberContext": W("StructExpression", "NULL"); return;
                    case "SetArray": W("AssigningProperty", "NULL"); W("Elements", "ANY"); return;
                    case "StructConst": W("Value", "ANY"); return;
                    case "BindDelegate": W("Delegate", "NULL"); W("ObjectTerm", "T:Object"); return;
                    case "AddMulticastDelegate" or "RemoveMulticastDelegate": W("Delegate", "NULL"); W("DelegateToAdd", "ANY"); return;
                }
                foreach (var (k, v) in o) if (k != "$type") Walk(v, "UNMODELED", where);
            }
        }
        return audit;
    }

    // Repair-specific invariants plus the full 012 clock validator against the repaired 011 baseline.
    static List<string> CheckRepair019(JsonObject actual, JsonObject repaired011, JsonNode natives, string root, out JsonArray audit) {
        var errors = CheckClock(actual, repaired011, root); void T(bool ok, string why) { if (!ok) errors.Add(why); }
        audit = ReturnContractR(actual, natives, T);
        var e = Export(actual, Timing); var code = Arr(e, "ScriptBytecode");
        T(!Arr(e, "LoadedProperties").Any(p => Str(p!["PropertyFlags"]) is var fl && (fl.Contains("CPF_ReturnParm") || fl.Contains("CPF_OutParm"))) && !Str(e["FunctionFlags"]).Contains("FUNC_HasOutParms"), "Build Arabic Timing still returns a value");
        T(code.Count(x => IsOpR(x!, "Return")) == 1 && code.Where(x => IsOpR(x!, "Return")).All(x => Op019(x!["ReturnExpression"]) == "Nothing"), "Build Arabic Timing return is not Return Nothing");
        T(CallSites019(actual, Index(actual, Timing)).SequenceEqual(new[] { ("Set Displayed Line", true) }), "Build Arabic Timing call sites changed");
        return errors;
    }

    static JsonArray DiffRepair019(string sourcePath, string generatedPath) {
        var original = Read(sourcePath); var generated = Read(generatedPath); var result = new JsonArray();
        Require(original.Exports.Count == generated.Exports.Count && original.Imports.Count == generated.Imports.Count, "repair changed export/import count");
        Require(JsonNode.DeepEquals(Model(original)["NameMap"], Model(generated)["NameMap"]) && JsonNode.DeepEquals(Model(original)["Imports"], Model(generated)["Imports"]), "repair changed names/imports");
        var old = File.ReadAllBytes(sourcePath).Concat(File.ReadAllBytes(Path.ChangeExtension(sourcePath, ".uexp"))).ToArray(); var now = File.ReadAllBytes(generatedPath).Concat(File.ReadAllBytes(Path.ChangeExtension(generatedPath, ".uexp"))).ToArray();
        for (int i = 0; i < original.Exports.Count; i++) {
            var o = original.Exports[i]; var n = generated.Exports[i]; string name = o.ObjectName.ToString();
            var before = old.AsSpan((int)o.SerialOffset, (int)o.SerialSize).ToArray(); var after = now.AsSpan((int)n.SerialOffset, (int)n.SerialSize).ToArray(); bool same = before.SequenceEqual(after);
            Require(same || name == Timing, "unexpected repair export change " + (i + 1) + " " + name);
            var item = new JsonObject { ["export"] = i + 1, ["name"] = name, ["classification"] = same ? "BYTE_IDENTICAL" : "EXPECTED_R8B_REPAIR_019", ["source_payload_sha256"] = Hash(before), ["generated_payload_sha256"] = Hash(after), ["source_serial_size"] = o.SerialSize, ["generated_serial_size"] = n.SerialSize };
            if (o is FunctionExport of && n is FunctionExport nf) { var b = Bytecode(original, of, out _); var c = Bytecode(generated, nf, out _); item["bytecode_unchanged"] = b.SequenceEqual(c); item["bytecode_size"] = new JsonArray(b.Length, c.Length); }
            result.Add(item);
        }
        return result;
    }

    static JsonArray NegativeRepair019(JsonObject good, JsonObject repaired011, JsonNode natives, string root) {
        var results = new JsonArray();
        void Contract(string name, JsonObject asset, JsonNode evidence, string diagnostic, bool expected = true) {
            var errors = new List<string>(); ReturnContractR(asset, evidence, (ok, why) => { if (!ok) errors.Add(why); });
            bool hit = errors.Any(x => x.Contains(diagnostic));
            Require(hit == expected, (expected ? "negative fixture missed " : "positive control rejected ") + name + " / " + string.Join(";", errors.Take(6)));
            results.Add(new JsonObject { ["fixture"] = name, ["detected"] = hit, ["expected_detection"] = expected, ["diagnostics"] = new JsonArray(errors.Take(5).Select(x => (JsonNode)V(x)).ToArray()) });
        }
        JsonObject WithReturn(string type, string? structName = null) {
            var bad = Copy(good); var p = Copy(Arr(Export(bad, Timing), "LoadedProperties")[0]!); p["Name"] = "ReturnValue"; p["PropertyFlags"] = "CPF_Parm, CPF_OutParm, CPF_ReturnParm"; p["SerializedType"] = type + "Property";
            Arr(Export(bad, Timing), "LoadedProperties").Insert(2, p); return bad;
        }
        // The real Run 2 artifact must be rejected by the complete validator, at the exact site.
        var frozen = Model(Read(Clock012Path(root))); var full = CheckRepair019(frozen, repaired011, natives, root, out _);
        string run2 = "unsafe statement-level non-trivial return Set Displayed Line:66 Build Arabic Timing -> Str";
        Require(full.Any(x => x.Contains(run2)), "Run 2 artifact not rejected: " + string.Join(";", full.Take(6)));
        results.Add(new JsonObject { ["fixture"] = "Run 2 artifact (frozen reveal_clock_012 = installed R8b 014)", ["detected"] = true, ["expected_detection"] = true, ["diagnostics"] = new JsonArray(full.Where(x => x.Contains("Build Arabic Timing")).Select(x => (JsonNode)V(x)).ToArray()) });
        Contract("bare call, FString return restored", WithReturn("Str"), natives, run2);
        Contract("bare call, FText return", WithReturn("Text"), natives, "Set Displayed Line:66 Build Arabic Timing -> Text");
        Contract("bare call, TArray return", WithReturn("Array"), natives, "Set Displayed Line:66 Build Arabic Timing -> Array");
        Contract("bare call, struct return", WithReturn("Struct"), natives, "Set Displayed Line:66 Build Arabic Timing -> Struct");
        Contract("bare call, bool return (POD control)", WithReturn("Bool"), natives, "unsafe statement-level", expected: false);
        var bareNative = Copy(good); Arr(Export(bareNative, "Arabic Step"), "ScriptBytecode").Insert(0, Call2(-Arr(good, "Imports").Select((x, i) => (x, i)).First(x => Str(x.x!["ObjectName"]) == "Concat_StrStr").i - 1, SC("a"), SC("b")));
        Contract("bare native FString return", bareNative, natives, "unsafe statement-level non-trivial return Arabic Step:0 KismetStringLibrary.Concat_StrStr -> Str");
        var noThunk = natives.DeepClone(); noThunk["functions"]!["KismetSystemLibrary.K2_SetTimer"]!["trivial_store"]!["trivial"] = false;
        Contract("struct return without thunk evidence", good, noThunk, "KismetSystemLibrary.K2_SetTimer -> Struct");
        var wrongLet = Copy(good); var len = Arr(Export(wrongLet, "AR Timing Characters"), "ScriptBytecode").First(x => IsAssignmentR(x!, "Length"))!;
        len["Value"]!["New"]!["Path"]![0] = "Input"; len["Variable"]!["Variable"]!["New"]!["Path"]![0] = "Input";
        Contract("Let destination type mismatch", wrongLet, natives, "invalid result destination AR Timing Characters:2 KismetStringLibrary.Len -> Int into Str");
        var bareValue = Copy(good); Arr(Export(bareValue, Timing), "ScriptBytecode").Insert(1, Var2(Index(good, Timing), "Output"));
        Contract("value expression at statement level", bareValue, natives, "value expression at statement level Build Arabic Timing:1 EX_LocalVariable");
        var wrongArg = Copy(good); Arr(Arr(Export(wrongArg, "Set Displayed Line"), "ScriptBytecode")[66]!, "Parameters")[1] = Var2(Index(good, "Set Displayed Line"), "ARLarge");
        Contract("argument type mismatch", wrongArg, natives, "invalid value destination Set Displayed Line:66 EX_LocalVariable Bool into Str");
        var unknown = natives.DeepClone(); unknown["functions"]!.AsObject().Remove("KismetStringLibrary.Concat_StrStr");
        Contract("native without signature evidence", good, unknown, "unresolved callee signature");
        return results;
    }

    static string[] FrozenRepairInputs(string root) => new[] { "builds/rtl_poc/stage1", "builds/rtl_poc/stage2", Reveal011Dir, "builds/rtl_poc/reveal_clock_012" }
        .SelectMany(d => Directory.GetFiles(Path.Combine(root, d), "*", SearchOption.AllDirectories)).Append(Path.Combine(root, NativeEvidence)).OrderBy(x => x, StringComparer.Ordinal).ToArray();
    static JsonNode Natives019(string root) {
        var n = JsonNode.Parse(File.ReadAllText(Path.Combine(root, NativeEvidence)))!;
        Require(Str(n["exe_sha256"]) == ExeSha && n["functions"] is JsonObject, "native signature evidence missing or for another EXE"); return n;
    }
    static void GateRepairInputs019(string root) {
        string a = Reveal011Path(root), b = Clock012Path(root);
        Require(HashFile(a) == Reveal011Uasset && HashFile(Path.ChangeExtension(a, ".uexp")) == Reveal011Uexp, "011 frozen pair hash mismatch");
        Require(HashFile(b) == Clock012Uasset && HashFile(Path.ChangeExtension(b, ".uexp")) == Clock012Uexp, "012 frozen pair hash mismatch");
    }

    public static int BuildRepair019(string rootPath, string outputDirectory) {
        try {
            string root = Path.GetFullPath(rootPath), dir = Path.GetFullPath(outputDirectory);
            Require(dir.StartsWith(Path.GetFullPath(Path.Combine(root, "builds/rtl_poc")) + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase), "detached output required"); Require(!Directory.Exists(dir), "refusing existing files");
            GateRepairInputs019(root); var natives = Natives019(root);
            var frozen = FrozenRepairInputs(root); var hashes = frozen.Select(HashFile).ToArray(); string fadeHash = HashFile(FadePath(root));
            var src011 = Read(Reveal011Path(root)); Require(src011.VerifyBinaryEquality(), "011 source roundtrip"); var repaired011 = RepairTiming019(Model(src011));
            var src012 = Read(Clock012Path(root)); Require(src012.VerifyBinaryEquality(), "012 source roundtrip");
            Directory.CreateDirectory(dir); File.WriteAllText(Path.Combine(dir, "NOT_INSTALLABLE.txt"), "R8B REPAIR 019 OFFLINE NOT_INSTALLABLE NOT_RUNTIME_TESTED\nBuild Arabic Timing is void; rebuilt from 011 through the 012 clock generator. Not tested in Unreal or in game.\n");
            WritePackage(GenerateClock(repaired011, root).Asset, RepairPath(dir));
            string cross = Path.Combine(dir, "cross_check_from_012"), repeat = Path.Combine(dir, "determinism"), roundtrip = Path.Combine(dir, "roundtrip");
            WritePackage(RepairTiming019(Model(src012)), RepairPath(cross));
            WritePackage(GenerateClock(RepairTiming019(Model(Read(Reveal011Path(root)))), root).Asset, RepairPath(repeat));
            Directory.CreateDirectory(roundtrip); Read(RepairPath(dir)).Write(RepairPath(roundtrip));
            foreach (string ext in new[] { ".uasset", ".uexp" }) foreach (string target in new[] { cross, repeat, roundtrip })
                Require(File.ReadAllBytes(Path.ChangeExtension(RepairPath(dir), ext)).SequenceEqual(File.ReadAllBytes(Path.ChangeExtension(RepairPath(target), ext))), "repair cross-check/determinism/roundtrip " + Path.GetFileName(target) + ext);
            var a = Model(Read(RepairPath(dir)));
            var errors = CheckRepair019(a, repaired011, natives, root, out var audit); Require(errors.Count == 0, string.Join(";", errors.Take(12)));
            SaveJson(Path.Combine(dir, "instruction_inventory.json"), InstructionInventory(Read(RepairPath(dir))));
            SaveJson(Path.Combine(dir, "return_contract_019.json"), new JsonObject { ["rule"] = "statement-level calls may only return void, scalars or thunk-proven plainly stored structs; every other call result, variable or constant needs constructed storage of a compatible type",
                ["call_sites"] = audit.Count, ["invalid"] = audit.Count(x => Str(x!["verdict"]) != "VALID"), ["statement_level"] = audit.Count(x => Str(x!["destination"]) == "SCRATCH"), ["sites"] = audit });
            var diff = DiffRepair019(Clock012Path(root), RepairPath(dir)); var negatives = NegativeClock(a, repaired011, root); foreach (var x in NegativeRepair019(a, repaired011, natives, root)) negatives.Add(x!.DeepClone());
            Require(hashes.SequenceEqual(frozen.Select(HashFile)) && HashFile(FadePath(root)) == fadeHash, "frozen inputs changed");
            SaveJson(Path.Combine(dir, "repair_verification.json"), new JsonObject {
                ["status"] = "R8B_REPAIR_019_GENERATED", ["labels"] = new JsonArray("OFFLINE", "NOT_INSTALLABLE", "NOT_RUNTIME_TESTED"), ["replay"] = "tools/asset_inspector/test_repair_019.py",
                ["repair"] = "Build Arabic Timing: ReturnValue (StrProperty, CPF_Parm|CPF_OutParm|CPF_ReturnParm) removed, FUNC_HasOutParms cleared, Return Local(Output) -> Return Nothing",
                ["validator_errors"] = 0, ["unexpected_changes"] = 0, ["return_contract_invalid"] = 0, ["return_contract_call_sites"] = audit.Count,
                ["source_011"] = new JsonObject { ["uasset_sha256"] = Reveal011Uasset, ["uexp_sha256"] = Reveal011Uexp }, ["source_012"] = new JsonObject { ["uasset_sha256"] = Clock012Uasset, ["uexp_sha256"] = Clock012Uexp },
                ["cross_check_equals_repair_of_012"] = true, ["native_evidence"] = NativeEvidence, ["negative_tests"] = negatives, ["export_diff_vs_012"] = diff,
                ["frozen_inputs"] = new JsonArray(frozen.Select((p, i) => (JsonNode)new JsonObject { ["path"] = Path.GetRelativePath(root, p).Replace('\\', '/'), ["sha256"] = hashes[i] }).ToArray()),
                ["deterministic"] = true, ["roundtrip"] = true, ["uasset_sha256"] = HashFile(RepairPath(dir)), ["uexp_sha256"] = HashFile(Path.ChangeExtension(RepairPath(dir), ".uexp")),
                ["DISPATCH_INTEGRATION_PROVEN"] = false, ["IN_GAME_RTL_PROVEN"] = false, ["tested_in_game"] = 0, ["final"] = 0 });
            Console.WriteLine("R8B_REPAIR_019_GENERATED: " + audit.Count + " call sites valid, " + negatives.Count + " negative fixtures, cross-check/deterministic/roundtrip. " + dir); return 0;
        } catch (Exception ex) { Console.Error.WriteLine(ex.ToString()); return 1; }
    }
    public static int ValidateRepair019(string rootPath, string directory) {
        try {
            string root = Path.GetFullPath(rootPath), dir = Path.GetFullPath(directory); GateRepairInputs019(root); var natives = Natives019(root);
            var repaired011 = RepairTiming019(Model(Read(Reveal011Path(root)))); var asset = Read(RepairPath(dir)); Require(asset.VerifyBinaryEquality(), "repair binary roundtrip");
            var a = Model(asset); var errors = CheckRepair019(a, repaired011, natives, root, out var audit); Require(errors.Count == 0, string.Join(";", errors));
            var report = JsonNode.Parse(File.ReadAllText(Path.Combine(dir, "repair_verification.json")))!;
            foreach (var entry in Arr(report, "frozen_inputs")) Require(HashFile(Path.Combine(root, Str(entry!["path"]))) == Str(entry["sha256"]), "frozen input hash changed");
            foreach (string ext in new[] { ".uasset", ".uexp" }) foreach (string copy in new[] { "cross_check_from_012", "determinism", "roundtrip" })
                Require(File.ReadAllBytes(Path.ChangeExtension(RepairPath(dir), ext)).SequenceEqual(File.ReadAllBytes(Path.ChangeExtension(RepairPath(Path.Combine(dir, copy)), ext))), "repair binary evidence mismatch");
            var negatives = NegativeClock(a, repaired011, root); foreach (var x in NegativeRepair019(a, repaired011, natives, root)) negatives.Add(x!.DeepClone());
            Console.WriteLine(new JsonObject { ["status"] = "R8B_REPAIR_019_STRUCTURE_PASS", ["errors"] = 0, ["return_contract_call_sites"] = audit.Count, ["negative_tests"] = negatives, ["original_export_diff"] = DiffRepair019(Clock012Path(root), RepairPath(dir)) }.ToJsonString(Pretty));
            return 0;
        } catch (Exception ex) { Console.Error.WriteLine(ex.ToString()); return 1; }
    }
}
