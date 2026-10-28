using System.Globalization;
using System.Text.Json.Nodes;

// Round 021 (report_020): Run 5 drew no Arabic subtitle. Stock URichTextBlock::RebuildStyleInstance (EXE 0x1ec95e0) reads
// TextStyleSet rows only when RowStruct IsChildOf FRichTextStyleRow, and the round-009 DT_AR tables kept the sibling
// ProtoRichTextStyleRow of their DT_SubtitlesProtoRichText template. Only the four tables are rebuilt; the 019 WBP is reused byte for byte.
static partial class ArabicStage1
{
    const string Tables019Dir = "builds/rtl_poc/stage1/Dispatch/Content/ArabicReveal";
    const string Repair019Dir = "builds/rtl_poc/r8b_repair_019";
    const string StyleGateEvidence = "reports/rtl_research/renderer_repair/run5_020/style_gate_020.json";
    const string StockRow = "/Script/UMG.RichTextStyleRow", ProtoRow = "/Script/ProtoAnimatedText.ProtoRichTextStyleRow", BaseRow = "/Script/Engine.TableRowBase";
    const string StockRichText = "/Script/UMG.RichTextBlock", ProtoRichText = "/Script/ProtoAnimatedText.ProtoRichTextBlock", ChildOk = "CHILD_OF_RichTextStyleRow";
    static readonly string[] ProtoOnlyFields = { "PrintLetterAnimationTime", "PrintLetterInterval", "UseAdvancedPrintIntervals", "CommaInterval",
        "SentenceInterval", "EllipsisInterval", "MidWordDashInterval", "SpaceInterval" };
    // Round-019 inputs = the Run 5 pak payload: the WBP must stay byte-identical, the tables are the rejected Run 5 tables.
    static readonly Dictionary<string, string> Inputs021 = new() {
        [Repair019Dir + "/" + RepairName + ".uasset"] = "e4189ec226170f487ed232ebc0a4659fa559d91738a2aea6d59f892cd02b6f52",
        [Repair019Dir + "/" + RepairName + ".uexp"] = "9ab47d953df90f163689203abb356ccd81ce2828c7a4898ea762f49b4e24b0b4",
        [Tables019Dir + "/DT_AR_Fill.uasset"] = "564fd5ec21bf6019bc9370c7014b198e3e270468f02b6c07f433139c0d81b613",
        [Tables019Dir + "/DT_AR_Fill.uexp"] = "b9feeeb5b211c50d02866380568c2d49fcbe3e44f5ac65b586aa6e5ea05da2c7",
        [Tables019Dir + "/DT_AR_Fill_Large.uasset"] = "7ca693e2feac213ce646cf579f4ff839a44e8cd28e53e9f80e8431f60f4b96fd",
        [Tables019Dir + "/DT_AR_Fill_Large.uexp"] = "e0615b35fab7e37d6e206c32d701bd931a42af6aea85c25c040ac309bc6cbb1d",
        [Tables019Dir + "/DT_AR_Outline.uasset"] = "f70763c44a79955141d5bdb9b607c0a6f5247f3005bf901e58ab5903c0a78064",
        [Tables019Dir + "/DT_AR_Outline.uexp"] = "6e005ff57cf4d8fb16fe7e65b6fd8fd26d321c1fc13fc3ae3a9aa69630b87e87",
        [Tables019Dir + "/DT_AR_Outline_Large.uasset"] = "5bcd8f48843149de519fd93731258033d0f131d7c54cafb6d06e77e47e84a92e",
        [Tables019Dir + "/DT_AR_Outline_Large.uexp"] = "be845d56fa6e5f6089f81f8db5128cdd74c35eb5dee7f5a0570100f0cb949f84" };
    static string Old021(string root, string table) => Path.Combine(root, Tables019Dir, table + ".uasset");
    static string New021(string dir, string table) => Path.Combine(dir, table + ".uasset");
    static string TablePath021(string table) => "/Game/ArabicReveal/" + table + "." + table;
    static void GateInputs021(string root) {
        foreach (var (path, sha) in Inputs021) Require(HashFile(Path.Combine(root, path)).Equals(sha, StringComparison.OrdinalIgnoreCase), "round-019 input hash mismatch " + path);
    }
    // Struct parents from the EXE UHT FStructParams (style_gate_020.json): both rows derive directly from FTableRowBase.
    static Dictionary<string, string?> RowHierarchy021(string root) {
        var n = JsonNode.Parse(File.ReadAllText(Path.Combine(root, StyleGateEvidence)))!;
        Require(Str(n["exe_sha256"]) == ExeSha && Str(n["RichTextStyleRow"]?["super"]) == "TableRowBase" && Str(n["ProtoRichTextStyleRow"]?["super"]) == "TableRowBase"
            && Str(n["rebuild_style_instance"]?["function_rva"]) == "0x1ec95e0", "style gate evidence missing or for another EXE");
        return new() { [StockRow] = BaseRow, [ProtoRow] = BaseRow, [BaseRow] = null };
    }

    static string? ImportPath021(JsonObject a, int i) {
        var imports = Arr(a, "Imports"); if (i >= 0 || -i > imports.Count) return null;
        var x = imports[-i - 1]!; int o = Num(x["OuterIndex"]);
        return o == 0 ? Str(x["ObjectName"]) : ImportPath021(a, o) is string p ? p + "." + Str(x["ObjectName"]) : null;
    }
    // The serialized RowStruct of a cooked DataTable, as /Script/<Module>.<Struct>, or null with the reason.
    static string? RowStruct021(JsonObject table, out string why) {
        why = ""; var exports = Arr(table, "Exports"); var imports = Arr(table, "Imports");
        if (exports.Count != 1 || !Str(exports[0]!["$type"]).Contains("DataTableExport")) { why = "not a single-export DataTable package"; return null; }
        var rs = (exports[0]!["Data"] as JsonArray)?.FirstOrDefault(p => Str(p!["Name"]) == "RowStruct");
        int i = rs?["Value"] is JsonValue v ? Num(v) : 0;
        if (i >= 0 || -i > imports.Count) { why = "RowStruct missing or not an import"; return null; }
        var x = imports[-i - 1]!; int o = Num(x["OuterIndex"]);
        if (Str(x["ClassName"]) != "ScriptStruct" || Str(x["ClassPackage"]) != "/Script/CoreUObject" || o >= 0 || -o > imports.Count
            || Str(imports[-o - 1]!["ClassName"]) != "Package" || Num(imports[-o - 1]!["OuterIndex"]) != 0) { why = "RowStruct import is not a native ScriptStruct"; return null; }
        return Str(imports[-o - 1]!["ObjectName"]) + "." + Str(x["ObjectName"]);
    }
    static string RowVerdict021(string? row, Dictionary<string, string?> h) {
        if (row == null || !h.ContainsKey(row)) return "UNRESOLVED";
        for (string? s = row; s != null; s = h[s]) if (s == StockRow) return ChildOk;
        return row == BaseRow ? "TABLEROWBASE_ONLY" : "SIBLING_NOT_CHILD";
    }

    // The RowStruct import pair is renamed in place (same import and NameMap indices, so every TextStyle byte is unchanged);
    // the eight Proto-only row fields are dropped. Nothing else changes.
    static JsonObject StyleFixTable021(JsonObject old) {
        var a = Copy(old); var e = Arr(a, "Exports").Single()!; var imports = Arr(a, "Imports"); var names = Arr(a, "NameMap");
        Require(RowStruct021(a, out _) == ProtoRow, "input table RowStruct is not ProtoRichTextStyleRow");
        var row = imports[-Num(Prop(e, "RowStruct")["Value"]) - 1]!; int outer = Num(row["OuterIndex"]);
        Require(imports.Count(x => Num(x!["OuterIndex"]) == outer) == 1, "/Script/ProtoAnimatedText import has other users");
        row["ObjectName"] = "RichTextStyleRow"; imports[-outer - 1]!["ObjectName"] = "/Script/UMG";
        foreach (var (from, to) in new[] { ("ProtoRichTextStyleRow", "RichTextStyleRow"), ("/Script/ProtoAnimatedText", "/Script/UMG") }) {
            Require(names.Count(x => Str(x) == from) == 1 && !names.Any(x => Str(x) == to), "NameMap rename " + from);
            names[names.Select(Str).ToList().IndexOf(from)] = to;
        }
        foreach (var r in Arr(e["Table"]!, "Data")) {
            var props = Arr(r!, "Value");
            Require(Str(r!["StructType"]) == "ProtoRichTextStyleRow" && props.Select(p => Str(p!["Name"])).SequenceEqual(ProtoOnlyFields.Prepend("TextStyle")), "unexpected row layout " + Str(r["Name"]));
            r["StructType"] = "RichTextStyleRow"; r["Value"] = new JsonArray(props[0]!.DeepClone());
        }
        return a;
    }

    // RichTextStyleGate (permanent, round 021). Every DataTable bound to a stock /Script/UMG.RichTextBlock, as a widget TextStyleSet
    // default or as a SetTextStyleSet argument, must have a RowStruct that IsChildOf /Script/UMG.RichTextStyleRow: EXE 0x1ec95e0 skips
    // every row otherwise. Fail closed: an unresolved widget, argument, table or RowStruct is an error. Shipped ProtoRichTextBlock
    // targets are listed but exempt: they draw from ProtoTextStyleSet.
    static JsonArray RichTextStyleGate(JsonObject wbp, Func<string, JsonObject?> load, Dictionary<string, string?> h, Action<bool, string> T) {
        var audit = new JsonArray(); var exports = Arr(wbp, "Exports").Select(x => x!.AsObject()).ToArray(); var imports = Arr(wbp, "Imports");
        var cls = exports.Single(x => Str(x["$type"]).Contains("ClassExport")); var cdo = exports.Single(x => Num(x["ClassIndex"]) == Array.IndexOf(exports, cls) + 1);
        void Bind(string site, int index) {
            string? path = ImportPath021(wbp, index);
            var table = path != null && Str(imports[-index - 1]!["ClassName"]) == "DataTable" ? load(path) : null;
            string why = "table unresolved"; string? row = table == null ? null : RowStruct021(table, out why); string verdict = RowVerdict021(row, h);
            T(verdict == ChildOk, $"RichTextStyleGate {site}: {path ?? "index " + index} RowStruct {row ?? "unresolved (" + why + ")"} is {verdict}, not a child of {StockRow}");
            audit.Add(new JsonObject { ["site"] = site, ["widget_class"] = StockRichText, ["table"] = path ?? "index " + index, ["row_struct"] = row, ["verdict"] = verdict });
        }
        foreach (var w in exports.Where(x => ImportPath021(wbp, Num(x["ClassIndex"])) == StockRichText)) {
            var p = (w["Data"] as JsonArray)?.FirstOrDefault(x => Str(x!["Name"]) == "TextStyleSet");
            if (p != null) Bind(Str(w["ObjectName"]) + " TextStyleSet (widget default)", Num(p["Value"]));
            else audit.Add(new JsonObject { ["site"] = Str(w["ObjectName"]) + " TextStyleSet (widget default)", ["widget_class"] = StockRichText, ["verdict"] = "NO_DEFAULT_TABLE" });
        }
        bool IsSetStyle(JsonObject o) => CallOps.Contains(Op019(o)) && (o["StackNode"] is JsonValue s && ImportPath021(wbp, Num(s)) == StockRichText + ".SetTextStyleSet" || Str(o["VirtualFunctionName"]) == "SetTextStyleSet");
        foreach (var f in exports.Where(x => x["ScriptBytecode"] is JsonArray)) {
            var code = Arr(f, "ScriptBytecode"); string fn = Str(f["ObjectName"]); int calls = 0, bound = 0;
            for (int idx = 0; idx < code.Count; idx++) JsonWalk2(code[idx], "$", (o, _) => {
                if (IsSetStyle(o)) calls++;
                if (Op019(o) is not ("Context" or "Context_FailSilent") || o["ContextExpression"] is not JsonObject call || !IsSetStyle(call)) return;
                bound++; string site = fn + ":" + idx + " SetTextStyleSet"; var target = o["ObjectExpression"];
                string? targetClass = Op019(target) == "InstanceVariable" && target!["Variable"]?["New"]?["Path"] is JsonArray tp && tp.Count == 1
                    ? (cls["LoadedProperties"] as JsonArray)?.Where(p => Str(p!["Name"]) == Str(tp[0])).Select(p => ImportPath021(wbp, Num(p!["PropertyClass"]))).FirstOrDefault() : null;
                if (targetClass == ProtoRichText) { audit.Add(new JsonObject { ["site"] = site, ["widget_class"] = targetClass, ["verdict"] = "EXEMPT_PROTO_WIDGET" }); return; }
                T(targetClass == StockRichText, "RichTextStyleGate " + site + ": target unresolved (" + (targetClass ?? "EX_" + Op019(target)) + ")");
                var args = Arr(call, "Parameters"); var values = targetClass == StockRichText && args.Count == 1 ? TableValues021(args[0], f, cdo, 0) : null;
                if (targetClass == StockRichText && values == null) {
                    T(false, "RichTextStyleGate " + site + ": argument unresolved (" + (args.Count == 1 ? "EX_" + Op019(args[0]) : args.Count + " arguments") + ")");
                    audit.Add(new JsonObject { ["site"] = site, ["widget_class"] = targetClass, ["verdict"] = "UNRESOLVED_ARGUMENT" });
                }
                foreach (int v in values?.Distinct() ?? Enumerable.Empty<int>()) Bind(site, v);
            });
            T(calls == bound, "RichTextStyleGate " + fn + ": SetTextStyleSet call outside a widget context");
        }
        return audit;
    }
    // Every object a SetTextStyleSet argument can hold: constants, CDO defaults of instance variables, and every Let/LetObj into a
    // local. Parameters, out-parameter writes and any other expression are unresolved.
    static List<int>? TableValues021(JsonNode? x, JsonObject f, JsonObject cdo, int depth) {
        string? name = x?["Variable"]?["New"]?["Path"] is JsonArray p && p.Count == 1 ? Str(p[0]) : null;
        switch (Op019(x)) {
            case "ObjectConst": return new() { Num(x!["Value"]) };
            case "InstanceVariable": return (cdo["Data"] as JsonArray)?.FirstOrDefault(q => Str(q!["Name"]) == name)?["Value"] is JsonValue v ? new() { Num(v) } : null;
            case "LocalVariable" when depth < 8:
                if (Arr(f, "LoadedProperties").Any(q => Str(q!["Name"]) == name && Str(q!["PropertyFlags"]).Contains("CPF_Parm"))) return null;
                bool outWrite = false; JsonWalk2(f["ScriptBytecode"], "$", (o, _) => outWrite |= Op019(o) == "LocalOutVariable" && Str(o["Variable"]?["New"]?["Path"]?[0]) == name);
                if (outWrite) return null;
                var result = new List<int>();
                foreach (var ins in Arr(f, "ScriptBytecode")) {
                    var (dst, src) = Op019(ins) switch { "LetObj" => (ins!["VariableExpression"], ins["AssignmentExpression"]), "Let" => (ins!["Variable"], ins["Expression"]), _ => (null, null) };
                    if (Op019(dst) != "LocalVariable" || Str(dst!["Variable"]?["New"]?["Path"]?[0]) != name) continue;
                    if (TableValues021(src, f, cdo, depth + 1) is not List<int> vs) return null;
                    result.AddRange(vs);
                }
                return result.Count > 0 ? result : null;
            default: return null;
        }
    }

    static readonly string[] TagFields021 = { "$type", "Name", "ArrayIndex", "PropertyGuid", "IsZero", "PropertyTagFlags", "PropertyTypeName", "PropertyTagExtensions" };
    // Field-by-field view of a property tree; object references are resolved to their import paths.
    static void Leaves021(JsonObject a, JsonNode p, string path, JsonObject leaves) {
        string name = path + Str(p["Name"]) + (Num(p["ArrayIndex"]) != 0 ? "[" + Num(p["ArrayIndex"]) + "]" : "");
        if (p["Value"] is JsonArray xs && xs.All(x => x is JsonObject o && o["Name"] != null)) { foreach (var x in xs) Leaves021(a, x!, name + ".", leaves); return; }
        var rest = new JsonObject(); foreach (var (k, v) in p.AsObject()) if (!TagFields021.Contains(k)) rest[k] = v?.DeepClone();
        if (Str(p["$type"]).Contains("ObjectPropertyData")) rest["Value"] = Num(p["Value"]) == 0 ? "null" : ImportPath021(a, Num(p["Value"])) ?? "export " + Num(p["Value"]);
        leaves[name] = rest.Count == 1 && rest.ContainsKey("Value") ? rest["Value"]?.DeepClone() : rest;
    }
    static float Blue021(JsonNode style, params string[] path) {
        JsonNode n = style; foreach (string s in path) n = Child(n, s);
        return float.Parse(Str(n["Value"]![0]!["Value"]!["B"]), CultureInfo.InvariantCulture);
    }

    // Exact checks of the generated tables: RowStruct, rows, encoding, exact transformation, TextStyle equality and the gate.
    static List<string> CheckStyleFix021(string root, string dir, Dictionary<string, string?> h, out JsonObject comparison, out JsonObject rowAudit) {
        var errors = new List<string>(); void T(bool ok, string why) { if (!ok) errors.Add(why); }
        var tablesOut = new JsonArray(); var auditTables = new JsonArray(); var now = new Dictionary<string, JsonObject>(); var old = new Dictionary<string, JsonObject>();
        int rowsTotal = 0, rowsEqual = 0;
        foreach (string t in Tables) {
            var asset = Read(New021(dir, t)); T(asset.VerifyBinaryEquality(), "binary roundtrip " + t);
            var a = Model(asset); var o = Model(Read(Old021(root, t))); now[t] = a; old[t] = o;
            string? row = RowStruct021(a, out string why), oldRow = RowStruct021(o, out _);
            T(row == StockRow && RowVerdict021(row, h) == ChildOk, t + " RowStruct " + (row ?? why));
            var e = Arr(a, "Exports")[0]!; var rows = Arr(e["Table"]!, "Data"); var oldRows = Arr(Arr(o, "Exports")[0]!["Table"]!, "Data");
            T(rows.Select(x => Str(x!["Name"])).SequenceEqual(Enumerable.Range(0, 37).Select(i => "u" + i).Prepend("Default")), t + " rows must be Default,u0..u36");
            T(rows.All(x => Str(x!["StructType"]) == "RichTextStyleRow" && Arr(x, "Value").Select(p => Str(p!["Name"])).SequenceEqual(new[] { "TextStyle" })), t + " rows must hold only TextStyle");
            T(JsonNode.DeepEquals(Projection(a), Projection(Normalize(StyleFixTable021(o)))), t + " differs from the exact RowStruct/field transformation");
            var ni = Arr(a, "Imports"); var oi = Arr(o, "Imports"); int ri = -Num(Prop(e, "RowStruct")["Value"]) - 1, pi = -Num(ni[ri]!["OuterIndex"]) - 1;
            T(ni.Count == oi.Count && Enumerable.Range(0, ni.Count).All(i => i == ri || i == pi || JsonNode.DeepEquals(ni[i], oi[i])), t + " imports other than the RowStruct pair changed");
            var nn = Arr(a, "NameMap").Select(Str).ToArray(); var on = Arr(o, "NameMap").Select(Str).ToArray();
            T(nn.Length == on.Length && Enumerable.Range(0, nn.Length).Count(i => nn[i] != on[i]) == 2, t + " NameMap changes other than the RowStruct pair");
            var rowsJson = new JsonArray(); var materials = new SortedSet<string>(StringComparer.Ordinal); var fonts = new SortedSet<string>(StringComparer.Ordinal);
            for (int k = 0; k < rows.Count && k < oldRows.Count; k++) {
                string name = Str(rows[k]!["Name"]); var ts = Child(rows[k]!, "TextStyle"); var ots = Child(oldRows[k]!, "TextStyle");
                var leaves = new JsonObject(); var oldLeaves = new JsonObject(); Leaves021(a, ts, "", leaves); Leaves021(o, ots, "", oldLeaves);
                bool equal = Str(oldRows[k]!["Name"]) == name && JsonNode.DeepEquals(ts, ots) && JsonNode.DeepEquals(leaves, oldLeaves);
                T(equal, t + " " + name + " TextStyle changed"); rowsTotal++; if (equal) rowsEqual++;
                int unit = name == "Default" ? 0 : int.Parse(name[1..]); float b = (float)Math.Pow(10.5, -unit);
                T(Blue021(ts, "ColorAndOpacity", "SpecifiedColor") == b && (!t.Contains("Outline") || Blue021(ts, "Font", "OutlineSettings", "OutlineColor") == b), t + " " + name + " unit colour encoding");
                materials.Add(Str(leaves["TextStyle.Font.FontMaterial"])); materials.Add(Str(leaves["TextStyle.Font.OutlineSettings.OutlineMaterial"])); fonts.Add(Str(leaves["TextStyle.Font.FontObject"]) + " / " + Str(leaves["TextStyle.Font.TypefaceFontName"]));
                var dropped = new JsonObject(); foreach (var p in Arr(oldRows[k]!, "Value").Skip(1)) dropped[Str(p!["Name"])] = p["Value"]?.DeepClone();
                rowsJson.Add(new JsonObject { ["row"] = name, ["textstyle_equal"] = equal, ["old_textstyle_json_sha256"] = HashNode(ots), ["new_textstyle_json_sha256"] = HashNode(ts),
                    ["unit_blue"] = b, ["leaf_count"] = leaves.Count, ["dropped_proto_fields"] = dropped, ["textstyle_fields"] = leaves });
            }
            tablesOut.Add(new JsonObject { ["table"] = t, ["rows"] = rows.Count, ["textstyle_equal_rows"] = rowsJson.Count(x => x!["textstyle_equal"]!.GetValue<bool>()),
                ["font"] = new JsonArray(fonts.Select(x => (JsonNode)V(x)).ToArray()), ["materials"] = new JsonArray(materials.Select(x => (JsonNode)V(x)).ToArray()), ["row_comparison"] = rowsJson });
            auditTables.Add(new JsonObject { ["table"] = t, ["package"] = TablePath021(t), ["row_struct_round_019"] = oldRow, ["verdict_round_019"] = RowVerdict021(oldRow, h),
                ["row_struct_round_021"] = row, ["verdict_round_021"] = RowVerdict021(row, h), ["import_round_021"] = ni[ri]!.DeepClone(), ["package_import_round_021"] = ni[pi]!.DeepClone(),
                ["rows"] = rows.Count, ["row_properties_round_021"] = new JsonArray("TextStyle"), ["row_properties_round_019"] = new JsonArray(ProtoOnlyFields.Prepend("TextStyle").Select(x => (JsonNode)V(x)).ToArray()),
                ["uasset_sha256"] = HashFile(New021(dir, t)), ["uexp_sha256"] = HashFile(Path.ChangeExtension(New021(dir, t), ".uexp")) });
        }
        T(rowsTotal == 152 && rowsEqual == 152, "TextStyle equality " + rowsEqual + "/" + rowsTotal);
        var wbp = Model(Read(RepairPath(Path.Combine(root, Repair019Dir))));
        var gate = RichTextStyleGate(wbp, p => Tables.Where(t => TablePath021(t) == p).Select(t => now[t]).FirstOrDefault(), h, T);
        var gated = gate.Where(x => Str(x!["verdict"]) == ChildOk).Select(x => Str(x!["table"])).ToHashSet();
        T(Tables.All(t => gated.Contains(TablePath021(t))) && gate.Count(x => Str(x!["verdict"]) == ChildOk) == 14, "RichTextStyleGate must cover all four tables (14 bindings)");
        var run5Errors = new List<string>(); var run5 = RichTextStyleGate(wbp, p => Tables.Where(t => TablePath021(t) == p).Select(t => old[t]).FirstOrDefault(), h, (ok, why) => { if (!ok) run5Errors.Add(why); });
        T(run5Errors.Count == 14 && run5.Count(x => Str(x!["verdict"]) == "SIBLING_NOT_CHILD") == 14, "Run 5 tables not rejected by RichTextStyleGate");
        comparison = new JsonObject { ["rule"] = "for every table and row: round-019 TextStyle == round-021 TextStyle (UAssetAPI property tree with the same import indices, and resolved field-by-field)",
            ["rows_compared"] = rowsTotal, ["rows_equal"] = rowsEqual, ["textstyle_equality_percent"] = rowsTotal == 0 ? 0 : 100.0 * rowsEqual / rowsTotal,
            ["ignored_fields_outside_TextStyle"] = new JsonArray(ProtoOnlyFields.Select(x => (JsonNode)V(x)).ToArray()), ["byte_level_check"] = "textstyle_bytes_021.json (tools/r8b_021/textstyle_bytes_021.py)", ["tables"] = tablesOut };
        rowAudit = new JsonObject { ["required_row_struct"] = StockRow, ["engine_gate"] = "URichTextBlock::RebuildStyleInstance EXE RVA 0x1ec95e0 (style_gate_020.json)",
            ["struct_parents"] = new JsonObject { [StockRow] = BaseRow, [ProtoRow] = BaseRow, [BaseRow] = null }, ["tables"] = auditTables,
            ["RichTextStyleGate_round_021"] = new JsonObject { ["errors"] = errors.Count(x => x.StartsWith("RichTextStyleGate")), ["bindings"] = gate },
            ["RichTextStyleGate_round_019_run5_tables"] = new JsonObject { ["errors"] = run5Errors.Count, ["diagnostics"] = new JsonArray(run5Errors.Select(x => (JsonNode)V(x)).ToArray()), ["bindings"] = run5 } };
        return errors;
    }

    static JsonArray NegativeStyleGate021(string root, string dir, Dictionary<string, string?> h) {
        var results = new JsonArray(); var wbp = Model(Read(RepairPath(Path.Combine(root, Repair019Dir))));
        var good = Tables.ToDictionary(TablePath021, t => Model(Read(New021(dir, t)))); var run5 = Tables.ToDictionary(TablePath021, t => Model(Read(Old021(root, t))));
        foreach (string s in new[] { SourceTable, SourceTable + "_Large" }) run5["/Game/Shared/Core/Widgets/" + s + "." + s] = good["/Game/Shared/Core/Widgets/" + s + "." + s] = Model(Read(Source(root, s)));
        int Shipped(string s) => -Arr(wbp, "Imports").Select((x, i) => (x, i)).Single(x => Str(x.x!["ObjectName"]) == s && Str(x.x!["ClassName"]) == "DataTable").i - 1;
        void Run(string name, JsonObject w, Dictionary<string, JsonObject> tables, string diagnostic, bool expected = true) {
            var errors = new List<string>(); RichTextStyleGate(w, p => tables.GetValueOrDefault(p), h, (ok, why) => { if (!ok) errors.Add(why); });
            bool hit = expected ? errors.Any(x => x.Contains(diagnostic)) : errors.Count == 0;
            Require(hit, (expected ? "negative fixture missed " : "positive control rejected ") + name + " / " + string.Join(";", errors.Take(4)));
            results.Add(new JsonObject { ["fixture"] = name, ["expected"] = expected ? "REJECT" : "ACCEPT", ["result"] = errors.Count == 0 ? "ACCEPT" : "REJECT", ["errors"] = errors.Count,
                ["diagnostics"] = new JsonArray(errors.Take(4).Select(x => (JsonNode)V(x)).ToArray()) });
        }
        Dictionary<string, JsonObject> With(string t, Action<JsonObject> mutate) {
            var copy = good.ToDictionary(x => x.Key, x => x.Value); var a = Copy(copy[TablePath021(t)]); mutate(a); copy[TablePath021(t)] = a; return copy;
        }
        void Rename(JsonObject a, string package, string row, string cls = "ScriptStruct") {
            var imports = Arr(a, "Imports"); var r = imports[-Num(Prop(Arr(a, "Exports")[0]!, "RowStruct")["Value"]) - 1]!;
            r["ObjectName"] = row; r["ClassName"] = cls; imports[-Num(r["OuterIndex"]) - 1]!["ObjectName"] = package;
        }
        JsonObject Mutate(Action<JsonObject> m) { var w = Copy(wbp); m(w); return w; }
        JsonNode Ins(JsonObject w, string f, int i) => Arr(Export(w, f), "ScriptBytecode")[i]!;
        Run("Run 5 tables (round-019 DT_AR, ProtoRichTextStyleRow) -> reject", wbp, run5, "RowStruct " + ProtoRow + " is SIBLING_NOT_CHILD");
        Run("ProtoRichTextStyleRow table -> reject", wbp, With("DT_AR_Fill", a => Rename(a, "/Script/ProtoAnimatedText", "ProtoRichTextStyleRow")), "DT_AR_Fill RowStruct " + ProtoRow + " is SIBLING_NOT_CHILD");
        Run("TableRowBase table -> reject", wbp, With("DT_AR_Outline", a => Rename(a, "/Script/Engine", "TableRowBase")), "DT_AR_Outline RowStruct " + BaseRow + " is TABLEROWBASE_ONLY");
        Run("unresolved RowStruct (unknown native struct) -> reject", wbp, With("DT_AR_Fill_Large", a => Rename(a, "/Script/UMG", "NoSuchStyleRow")), "/Script/UMG.NoSuchStyleRow is UNRESOLVED");
        Run("custom clone (user struct named RichTextStyleRow) -> reject", wbp, With("DT_AR_Fill_Large", a => Rename(a, "/Game/ArabicReveal/RichTextStyleRow", "RichTextStyleRow", "UserDefinedStruct")), "RowStruct import is not a native ScriptStruct");
        Run("custom clone (RichTextStyleRow in another module) -> reject", wbp, With("DT_AR_Fill", a => Rename(a, "/Script/ArabicReveal", "RichTextStyleRow")), "/Script/ArabicReveal.RichTextStyleRow is UNRESOLVED");
        Run("unresolved RowStruct (property missing) -> reject", wbp, With("DT_AR_Outline_Large", a => Arr(Arr(a, "Exports")[0]!, "Data").Clear()), "RowStruct missing or not an import");
        Run("unresolved RowStruct (export index) -> reject", wbp, With("DT_AR_Outline_Large", a => Prop(Arr(a, "Exports")[0]!, "RowStruct")["Value"] = 1), "RowStruct missing or not an import");
        Run("unresolved table (package absent) -> reject", wbp, good.Where(x => x.Key != TablePath021("DT_AR_Outline_Large")).ToDictionary(x => x.Key, x => x.Value), "table unresolved");
        Run("one Run 5 table behind the ARForegroundStyle local -> reject", wbp, With("DT_AR_Outline_Large", a => Rename(a, "/Script/ProtoAnimatedText", "ProtoRichTextStyleRow")), "Set Displayed Line:30 SetTextStyleSet: /Game/ArabicReveal/DT_AR_Outline_Large");
        Run("widget default bound to shipped Proto table -> reject", Mutate(w => Prop(Export(w, "ArabicShadowRichText"), "TextStyleSet")["Value"] = Shipped(SourceTable)), good, "ArabicShadowRichText TextStyleSet (widget default): /Game/Shared/Core/Widgets/DT_SubtitlesProtoRichText");
        Run("SetTextStyleSet constant shipped Proto table -> reject", Mutate(w => Arr(Ins(w, "Arabic Apply Style", 15)["ContextExpression"]!, "Parameters")[0] =OC(Shipped(SourceTable + "_Large"))), good, "Arabic Apply Style:15 SetTextStyleSet: /Game/Shared/Core/Widgets/DT_SubtitlesProtoRichText_Large");
        Run("local assigned shipped Proto table -> reject", Mutate(w => Ins(w, "Set Displayed Line", 29)["AssignmentExpression"] = OC(Shipped(SourceTable))), good, "Set Displayed Line:30 SetTextStyleSet: /Game/Shared/Core/Widgets/DT_SubtitlesProtoRichText");
        Run("unresolved SetTextStyleSet argument -> reject", Mutate(w => Arr(Ins(w, "Arabic Apply Style", 13)["ContextExpression"]!, "Parameters")[0] = X("NoObject")), good, "Arabic Apply Style:13 SetTextStyleSet: argument unresolved");
        Run("unresolved SetTextStyleSet target -> reject", Mutate(w => Ins(w, "Arabic Apply Style", 15)["ObjectExpression"] = X("Self")), good, "Arabic Apply Style:15 SetTextStyleSet: target unresolved");
        Run("correct RichTextStyleRow tables (round 021) -> accept", wbp, good, "", expected: false);
        return results;
    }

    static string[] Paths021(string dir) => Tables.SelectMany(t => new[] { New021(dir, t), Path.ChangeExtension(New021(dir, t), ".uexp") }).ToArray();
    static void SameBytes021(string dir) {
        foreach (string copy in new[] { "determinism", "roundtrip" }) foreach (string p in Paths021(dir))
            Require(File.ReadAllBytes(p).SequenceEqual(File.ReadAllBytes(Path.Combine(dir, copy, Path.GetFileName(p)))), copy + " bytes differ " + Path.GetFileName(p));
    }

    public static int BuildStyleFix021(string rootPath, string outputDirectory) {
        try {
            string root = Path.GetFullPath(rootPath), dir = Path.GetFullPath(outputDirectory);
            Require(dir.StartsWith(Path.GetFullPath(Path.Combine(root, "builds/rtl_poc")) + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase), "detached output required"); Require(!Directory.Exists(dir), "refusing existing files");
            GateInputs021(root); var h = RowHierarchy021(root);
            foreach (string t in Tables) Require(Read(Old021(root, t)).VerifyBinaryEquality(), "round-019 table roundtrip " + t);
            Directory.CreateDirectory(dir);
            File.WriteAllText(Path.Combine(dir, "NOT_INSTALLED.txt"), "R8B STYLEFIX 021 OFFLINE NOT_INSTALLED NOT_RUNTIME_TESTED\nFour DT_AR tables with RowStruct /Script/UMG.RichTextStyleRow; the round-019 WBP is reused unchanged. Install only through the approved Run 6 procedure.\n");
            foreach (string t in Tables) {
                WritePackage(StyleFixTable021(Model(Read(Old021(root, t)))), New021(dir, t));
                WritePackage(StyleFixTable021(Model(Read(Old021(root, t)))), New021(Path.Combine(dir, "determinism"), t));
                Directory.CreateDirectory(Path.Combine(dir, "roundtrip")); Read(New021(dir, t)).Write(New021(Path.Combine(dir, "roundtrip"), t));
            }
            SameBytes021(dir);
            var errors = CheckStyleFix021(root, dir, h, out var comparison, out var rowAudit); Require(errors.Count == 0, string.Join(";", errors.Take(12)));
            var negatives = NegativeStyleGate021(root, dir, h); GateInputs021(root);
            SaveJson(Path.Combine(dir, "textstyle_comparison.json"), comparison); SaveJson(Path.Combine(dir, "rowstruct_audit.json"), rowAudit);
            var files = new JsonObject(); foreach (string p in Paths021(dir)) files[Path.GetFileName(p)] = HashFile(p).ToLowerInvariant();
            SaveJson(Path.Combine(dir, "validation.json"), new JsonObject {
                ["status"] = "R8B_STYLEFIX_021_GENERATED", ["labels"] = new JsonArray("OFFLINE", "NOT_INSTALLED", "NOT_RUNTIME_TESTED"), ["validator_errors"] = 0,
                ["RichTextStyleGate"] = "PASS", ["RichTextStyleGate_bindings"] = 14, ["run5_tables_rejected"] = Arr(rowAudit["RichTextStyleGate_round_019_run5_tables"]!, "diagnostics").Count,
                ["row_struct"] = StockRow, ["tables"] = 4, ["rows_per_table"] = 38, ["textstyle_equal_rows"] = comparison["rows_equal"]!.DeepClone(), ["textstyle_rows_compared"] = comparison["rows_compared"]!.DeepClone(),
                ["exact_transformation"] = "RowStruct import pair renamed in place (ProtoRichTextStyleRow -> RichTextStyleRow, /Script/ProtoAnimatedText -> /Script/UMG); 8 Proto-only row fields dropped; nothing else",
                ["negative_tests"] = negatives, ["deterministic"] = true, ["roundtrip"] = true,
                ["wbp_round_019_unchanged"] = new JsonObject { ["uasset_sha256"] = Inputs021[Repair019Dir + "/" + RepairName + ".uasset"], ["uexp_sha256"] = Inputs021[Repair019Dir + "/" + RepairName + ".uexp"] },
                ["inputs"] = new JsonObject(Inputs021.Select(x => KeyValuePair.Create(x.Key, (JsonNode?)V(x.Value)))), ["files"] = files,
                ["IN_GAME_RTL_PROVEN"] = false, ["tested_in_game"] = 0, ["final"] = 0 });
            SaveJson(Path.Combine(dir, "manifest.json"), new JsonObject {
                ["status"] = "R8B_STYLEFIX_021_ASSETS_NOT_INSTALLED", ["labels"] = new JsonArray("OFFLINE_VALIDATED", "NOT_INSTALLED", "NOT_RUNTIME_TESTED"),
                ["assets"] = files.DeepClone(), ["pak_virtual_dir"] = "Dispatch/Content/ArabicReveal/", ["row_struct"] = StockRow,
                ["wbp"] = "round-019 " + RepairName + " reused unchanged (not part of this folder)",
                ["evidence"] = new JsonArray("validation.json", "textstyle_comparison.json", "rowstruct_audit.json", "textstyle_bytes_021.json"),
                ["generator"] = "asset_inspector --arabic-stylefix-021", ["validator"] = "asset_inspector --validate-arabic-stylefix-021", ["installed"] = false, ["final"] = 0 });
            Console.WriteLine("R8B_STYLEFIX_021_GENERATED: 4 tables RowStruct " + StockRow + ", 152/152 TextStyle equal, RichTextStyleGate 14 bindings PASS, Run 5 tables rejected, " + negatives.Count + " fixtures. " + dir);
            return 0;
        } catch (Exception ex) { Console.Error.WriteLine(ex.ToString()); return 1; }
    }
    public static int ValidateStyleFix021(string rootPath, string directory) {
        try {
            string root = Path.GetFullPath(rootPath), dir = Path.GetFullPath(directory); GateInputs021(root); var h = RowHierarchy021(root);
            var report = JsonNode.Parse(File.ReadAllText(Path.Combine(dir, "validation.json")))!;
            Require(Str(report["status"]) == "R8B_STYLEFIX_021_GENERATED", "missing round-021 validation report");
            foreach (var (name, sha) in report["files"]!.AsObject()) Require(HashFile(Path.Combine(dir, name)).Equals(Str(sha), StringComparison.OrdinalIgnoreCase), "artifact hash changed " + name);
            SameBytes021(dir);
            var errors = CheckStyleFix021(root, dir, h, out var comparison, out var rowAudit); Require(errors.Count == 0, string.Join(";", errors));
            var negatives = NegativeStyleGate021(root, dir, h);
            Console.WriteLine(new JsonObject { ["status"] = "R8B_STYLEFIX_021_PASS", ["errors"] = 0, ["RichTextStyleGate"] = "PASS", ["row_struct"] = StockRow,
                ["textstyle_equal_rows"] = comparison["rows_equal"]!.DeepClone(), ["run5_tables_rejected"] = Arr(rowAudit["RichTextStyleGate_round_019_run5_tables"]!, "diagnostics").Count,
                ["negative_tests"] = negatives }.ToJsonString(Pretty));
            return 0;
        } catch (Exception ex) { Console.Error.WriteLine(ex.ToString()); return 1; }
    }
}
