"""Offline evaluator of the emitted helper instructions, compared to the canonical segmenter.

This evaluates the reread Kismet JSON, not the generator's source algorithm. It is not Unreal runtime execution.
python -X utf8 tools/asset_inspector/test_stage2.py [builds/rtl_poc/stage2]
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def opname(node):
    return node["$type"].split(".")[-1].split(",")[0]


def float32(n):
    return struct.unpack("<f", struct.pack("<f", float(n)))[0]


class VM:
    def __init__(self, asset, inventory):
        self.asset = asset
        self.exports = asset["Exports"]
        self.functions = {e["ObjectName"]: i + 1 for i, e in enumerate(self.exports) if "FunctionExport" in e["$type"]}
        self.inventory = {e["export"]: e["instructions"] for e in inventory}
        self.state = {}
        self.effects = []
        self.calls_with_targets = []
        self.native_properties = {}
        cls = next(e for e in self.exports if e["ObjectName"] == "WBP_SubtitleBlock_C")
        widget_fields = set()
        for field in cls["LoadedProperties"]:
            kind = field["SerializedType"]
            self.state[field["Name"]] = False if kind == "BoolProperty" else 0 if kind in ("IntProperty", "FloatProperty") else [] if kind == "ArrayProperty" else ""
            if kind == "ObjectProperty" and field.get("PropertyClass", 0) < 0:
                native_type = asset["Imports"][-field["PropertyClass"] - 1]["ObjectName"]
                if native_type in ("Border", "Overlay", "RichTextBlock", "ProtoRichTextBlock", "RetainerBox", "Image"):
                    self.state[field["Name"]] = field["Name"]
                    widget_fields.add(field["Name"])
        cdo = next(e for e in self.exports if e["ObjectName"] == "Default__WBP_SubtitleBlock_C")
        for prop in cdo["Data"]:
            if prop["Name"] in self.state and prop["Name"] not in widget_fields:
                self.state[prop["Name"]] = prop.get("Value", self.state[prop["Name"]])
                if "FloatPropertyData" in prop["$type"]: self.state[prop["Name"]] = float32(float(self.state[prop["Name"]]))  # JSON may store "+0"

    def native(self, index, args):
        name = self.asset["Imports"][-index - 1]["ObjectName"]
        if name == "Concat_StrStr": return args[0] + args[1]
        if name == "Replace": return args[0].replace(args[1], args[2])
        if name == "EqualEqual_StrStr": return args[0] == args[1]
        if name == "StartsWith": return args[0].startswith(args[1])
        if name == "BooleanOR": return args[0] or args[1]
        if name == "BooleanAND": return args[0] and args[1]
        if name == "Not_PreBool": return not args[0]
        if name == "EqualEqual_IntInt": return args[0] == args[1]
        if name == "Less_IntInt": return args[0] < args[1]
        if name == "LessEqual_IntInt": return args[0] <= args[1]
        if name == "GreaterEqual_IntInt": return args[0] >= args[1]
        if name == "EqualEqual_ObjectObject": return args[0] == args[1]
        if name == "Add_IntInt": return args[0] + args[1]
        if name == "Subtract_IntInt": return args[0] - args[1]
        if name == "Multiply_IntInt": return args[0] * args[1]
        if name == "Conv_IntToFloat": return float32(args[0])
        if name == "Multiply_FloatFloat": return float32(args[0] * args[1])
        if name == "Add_FloatFloat": return float32(args[0] + args[1])
        if name == "Subtract_FloatFloat": return float32(args[0] - args[1])
        if name == "GreaterEqual_FloatFloat": return args[0] >= args[1]
        if name == "FMax": return float32(args[0] if args[0] >= args[1] else args[1])  # FMath::Max
        if name == "Array_Add":
            args[0].append(args[1])
            return len(args[0]) - 1
        if name == "Conv_IntToString": return str(args[0])
        if name in ("Conv_TextToString", "Conv_StringToText"): return args[0]
        if name == "Len": return len(args[0].encode("utf-16-le", errors="surrogatepass")) // 2
        if name == "GetSubstring":
            return args[0].encode("utf-16-le", errors="surrogatepass")[2 * args[1]:2 * (args[1] + args[2])].decode("utf-16-le", errors="surrogatepass")
        if name == "GetCharacterAsNumber":
            raw = args[0].encode("utf-16-le", errors="surrogatepass")
            return struct.unpack("<H", raw[2 * args[1]:2 * args[1] + 2])[0]
        if name == "Contains": return args[1] in args[0]
        if name in ("SetContentColorAndOpacity", "RequestRender", "SetTextStyleSet", "SetText", "SetRetainRendering", "SetTextWrapAt"):
            self.effects.append((name, args))
            self.calls_with_targets.append((name, getattr(self, "_context_value", None), args))
            return None
        engine = getattr(self, "engine", None)  # optional world/timer stub (test_clock.py)
        if engine is not None and name in engine.natives: return engine.natives[name](*args)
        raise AssertionError("Unmodelled native call: " + name)

    def run(self, name, args=()):
        index = self.functions[name]
        fn = self.exports[index - 1]
        fields = fn["LoadedProperties"]
        local = {f["Name"]: False if f["SerializedType"] == "BoolProperty" else 0 if f["SerializedType"] in ("IntProperty", "FloatProperty") else "" for f in fields}
        inputs = [f for f in fields if "CPF_Parm" in f["PropertyFlags"] and "CPF_ReturnParm" not in f["PropertyFlags"] and "CPF_OutParm" not in f["PropertyFlags"]]
        assert len(inputs) == len(args), (name, len(inputs), args)
        local.update((f["Name"], v) for f, v in zip(inputs, args))

        def pointer(p):
            field = p["New"]
            return (self.state if field["ResolvedOwner"] == 22 else local), field["Path"][0]

        def expr(n):
            op = opname(n)
            if op in ("EX_LocalVariable", "EX_LocalOutVariable", "EX_InstanceVariable"):
                store, key = pointer(n["Variable"])
                if n["Variable"]["New"]["ResolvedOwner"] < 0:
                    return self.native_properties.get((getattr(self, "_context_value", None), key), store.get(key, key))
                return store.get(key, key if op == "EX_InstanceVariable" else "")
            if op in ("EX_IntConst", "EX_ByteConst", "EX_StringConst", "EX_UnicodeStringConst", "EX_ObjectConst"): return n["Value"]
            if op == "EX_FloatConst": return float32(n["Value"])
            if op == "EX_True": return True
            if op == "EX_False": return False
            if op == "EX_Nothing": return None
            if op == "EX_Self": return "self"
            if op in ("EX_LetBool", "EX_LetObj", "EX_Let"):
                target = n["Variable"] if op == "EX_Let" else n["VariableExpression"]
                value = expr(n["Expression"] if op == "EX_Let" else n["AssignmentExpression"])
                store, key = pointer(target["Variable"])
                store[key] = value
                return value
            if op == "EX_SetArray":
                store, key = pointer(n["AssigningProperty"]["Variable"])
                store[key] = [expr(x) for x in n["Elements"]]
                return None
            if op == "EX_CallMulticastDelegate":
                values = [expr(x) for x in n["Parameters"]]
                self.effects.append(("Broadcast", values))
                callback = getattr(self, "on_finish", None)
                if callback: callback()
                return None
            if op in ("EX_CallMath", "EX_FinalFunction", "EX_LocalFinalFunction"):
                if n["StackNode"] < 0 and self.asset["Imports"][-n["StackNode"] - 1]["ObjectName"] == "Array_Get":
                    values, index = expr(n["Parameters"][0]), expr(n["Parameters"][1])
                    store, key = pointer(n["Parameters"][2]["Variable"])
                    store[key] = values[index]
                    return None
                values = [expr(p) for p in n["Parameters"]]
                if n["StackNode"] < 0: return self.native(n["StackNode"], values)
                return self.run(self.exports[n["StackNode"] - 1]["ObjectName"], values)
            if op == "EX_Context":
                target = expr(n["ObjectExpression"])
                previous = getattr(self, "_context_value", None)
                self._context_value = target
                try: return expr(n["ContextExpression"])
                finally: self._context_value = previous
            if op == "EX_VirtualFunction" and n["VirtualFunctionName"] == "SetVisibility":
                values = [expr(x) for x in n["Parameters"]]
                self.effects.append(("SetVisibility", values))
                self.calls_with_targets.append(("SetVisibility", getattr(self, "_context_value", None), values))
                return None
            if op == "EX_StructConst": return tuple(expr(v) for v in n["Value"])
            raise AssertionError((name, "Unmodelled expression", op))

        script = fn["ScriptBytecode"]
        offsets = {e["logicalOffset"]: i for i, e in enumerate(self.inventory[index])}
        pc = 0
        for _ in range(250000):
            ins = script[pc]
            op = opname(ins)
            if op == "EX_Return": return expr(ins["ReturnExpression"])
            if op == "EX_Jump": pc = offsets[ins["CodeOffset"]]; continue
            if op == "EX_JumpIfNot" and not expr(ins["BooleanExpression"]): pc = offsets[ins["CodeOffset"]]; continue
            if op != "EX_JumpIfNot": expr(ins)
            pc += 1
        raise AssertionError("Helper exceeded its bounded execution budget: " + name)


def main():
    directory = ROOT / (sys.argv[1] if len(sys.argv) > 1 else "builds/rtl_poc/stage2")
    asset = json.loads((directory / "WBP_SubtitleBlock_AR_STAGE2.json").read_text())
    inventory = json.loads((directory / "stage2_instruction_inventory.json").read_text())
    vm = VM(asset, inventory)
    spec = importlib.util.spec_from_file_location("canonical", ROOT / "tools/ue427_stock_reveal_test/segment_units.py")
    canonical = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(canonical)
    canonical.MAX_UNITS = 37
    canonical.self_check()
    fixtures = [("مرحبا (TEST-42) بالعالم", "المحقق"), ("السعر 50 USD اليوم", ""), ("أ\n50 ب", ""),
                ('a<b & "c"', ""), (" ".join(["كلمة"] * 200), "المحقق"), ("السَّلَامُ", ""), ("", ""),
                (" ", ""), ("  أ", "المحقق"), ("أ\r50 ب", ""), ("أ\u00a0ب ج\u202fد", ""),
                ("أ\u200dب أ\u200cب أ\u200bب", ""), ("", " ".join(["اسم"] * 40)), ("   ", "المحقق"), ("مرحبا 😀 50 اليوم", "اسم"), ("don't <b> & \"c\"", "")]
    rng = random.Random(10)
    words = ["مرحبا", "كَلمة", "50", "!", "TEST-42", "a<b", "&", '"c"', "أ\u00a0ب", "أ\u200dب", "سـلام"]
    gaps = [" ", "\t", "\n", "\r", "  ", "\n "]
    for _ in range(80):
        content = "".join(rng.choice(words) + rng.choice(gaps) for _ in range(rng.randrange(1, 75)))
        fixtures.append((content, rng.choice(["", "المحقق", "اسم طويل"])))
    for content, speaker in fixtures:
        expected = canonical.build_markup(content, speaker)
        actual = vm.run("Build Arabic Markup", (content, speaker))
        actual = actual.encode("utf-16-le", errors="surrogatepass").decode("utf-16-le")
        assert (actual, vm.state["ArabicUnitCount"], vm.state["ArabicSpeakerUnits"]) == expected[:3], (repr(content), speaker, actual, expected[:3])
    assert vm.run("Format As Arabic Plain", ("أ<Italic>ب</>",)) == "أب"
    for threshold in [-1] + list(range(37)) + [99]:
        vm.effects.clear()
        vm.run("Set Threshold Arabic", (threshold,))
        colors = [args[0] for name, args in vm.effects if name == "SetContentColorAndOpacity"]
        b = 0.0 if threshold < 0 else float32(10.5**min(threshold, 36))
        assert colors == [(1.0, 1.0, b, 1.0)] * 2
        assert sum(name == "RequestRender" for name, _ in vm.effects) == 2
    main_script = asset["Exports"][10]["ScriptBytecode"]
    gate = next(n for n in main_script if opname(n) == "EX_LetBool" and n["VariableExpression"].get("Variable", {}).get("New", {}).get("Path") == ["bArabic"])["AssignmentExpression"]
    def evaluate_gate(n, language):
        op = opname(n)
        if op == "EX_LocalVariable":
            assert n["Variable"]["New"]["Path"] == ["ARLanguage"]
            return language
        if op in ("EX_StringConst", "EX_ByteConst"): return n["Value"]
        assert op == "EX_CallMath"
        return vm.native(n["StackNode"], [evaluate_gate(x, language) for x in n["Parameters"]])
    for language, expected in [("ar", True), ("ar-SA", True), ("ar-EG", True), ("arn", False), ("en", False), ("AR", False)]:
        assert evaluate_gate(gate, language) == expected
    proc = subprocess.run(["dotnet", str(ROOT / "tools/asset_inspector/bin/Release/net8.0/asset_inspector.dll"),
                           "--validate-arabic-wbp-stage2", str(ROOT), str(directory)], capture_output=True, text=True, encoding="utf-8")
    assert proc.returncode == 0, proc.stderr[-3000:]
    independent = json.loads(proc.stdout)
    assert independent["status"] == "STAGE2_OFFLINE_VALIDATION_PASS" and len(independent["negativeTests"]) >= 6
    report = json.loads((directory / "stage2_verification.json").read_text())
    assert report["status"] == "R8B_WBP_STAGE2_PASS" and report["validatorErrors"] == report["unexpectedChanges"] == 0
    assert report["deterministicBinaryEqual"] and report["roundtripBinaryEqual"]
    for ext in ("uasset", "uexp"):
        assert hashlib.sha256((directory / ("WBP_SubtitleBlock_AR_STAGE2." + ext)).read_bytes()).hexdigest().upper() == report[ext + "Sha256"]
    print(f"PASS: Stage2 independent validator + 6 negatives; emitted helper evaluator matched canonical on {len(fixtures)} fixtures; 39 exact threshold cases; no Unreal/game execution")


if __name__ == "__main__":
    main()
