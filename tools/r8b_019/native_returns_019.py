"""Round 019: signature evidence for every native callee of an R8b WBP, read from the shipped EXE (read-only).

Decoder as tools/proto_binary_analysis/clock_imports_012.py: FFunctionParams OuterFunc +0, NameUTF8 +0x10, StructureSize
+0x28, PropertyArray +0x30, NumProperties +0x38, FunctionFlags +0x40; FPropertyParamsBase NameUTF8 +0, PropertyFlags +0x10,
GenFlags +0x18 (type = low 5 bits). Entries without CPF_Parm are container inners, not parameters.
Resolution order: EXE candidates with the call-site argument count -> same OuterFunc as another uniquely resolved function of
the same owner class -> the binding the shipped compiler used in the original WBP (Let type / LetBool / LetObj / bare = void).
Struct returns are checked in the native thunk: the RESULT_PARAM register may only receive plain stores (trivial copy).
python -X utf8 -I tools/r8b_019/native_returns_019.py <wbp.json> <original_wbp.json> <out.json>
"""
import hashlib
import json
import re
import struct
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "proto_binary_analysis"))
from pe import Image, EXE  # noqa: E402

EXE_SHA = "365637a77d4b74a61d198a9927e3dcd437bf3be2247b96fcbe5c2e851ac14923"
GEN = ["Byte", "Int8", "Int16", "Int", "Int64", "UInt16", "UInt32", "UInt64", "UnsizedInt", "UnsizedUInt", "Float", "Double",
       "Bool", "SoftClass", "WeakObject", "LazyObject", "SoftObject", "Class", "Object", "Interface", "Name", "Str", "Array",
       "Map", "Set", "Struct", "Delegate", "InlineMulticastDelegate", "SparseMulticastDelegate", "Text", "Enum", "FieldPath"]
CPF_PARM, CPF_OUT, CPF_RETURN, CPF_REFERENCE = 0x80, 0x100, 0x400, 0x8000000
IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
CALLS = ("EX_LocalFinalFunction,", "EX_FinalFunction,", "EX_CallMath,", "EX_VirtualFunction,", "EX_LocalVirtualFunction,")


def sites(wbp):
    """key -> [(argument count, compiler destination)] per native call; destination is a property type or VOID."""
    E, I = wbp["Exports"], wbp["Imports"]
    local = {e["ObjectName"] for e in E if "FunctionExport" in e["$type"]}

    def ptype(ptr):
        f = ptr.get("New", ptr); o = f.get("ResolvedOwner", 0)
        if not (isinstance(o, int) and o > 0 and f.get("Path")): return None
        p = next((p for p in E[o - 1].get("LoadedProperties") or [] if p["Name"] == f["Path"][0]), None)
        return p["SerializedType"][:-8] if p else None
    out = defaultdict(list)

    def walk(x, dest):
        if isinstance(x, list):
            for y in x: walk(y, dest)
            return
        if not isinstance(x, dict): return
        t = x.get("$type", ""); s = x.get("StackNode"); key = None
        if any(c in t for c in CALLS):
            if isinstance(s, int) and s < 0:
                imp = I[-s - 1]; o = imp["OuterIndex"]; key = (I[-o - 1]["ObjectName"] + "." if o < 0 else "") + imp["ObjectName"]
            elif "VirtualFunctionName" in x and x["VirtualFunctionName"] not in local:
                key = x["VirtualFunctionName"]
        if key: out[key].append((len(x["Parameters"]), dest))
        for k, v in x.items():
            if k == "$type": continue
            if "EX_Let," in t: d = ptype(x["Value"]) if k == "Expression" else "LVALUE"
            elif "EX_LetBool," in t: d = "Bool" if k == "AssignmentExpression" else "LVALUE"
            elif "EX_LetObj," in t: d = "Object" if k == "AssignmentExpression" else "LVALUE"
            elif "EX_JumpIfNot," in t: d = "Bool"
            elif "EX_Context" in t and k == "ContextExpression": d = dest
            else: d = "ARG"
            walk(v, d)
    for e in E:
        for ins in e.get("ScriptBytecode") or []: walk(ins, "VOID")
    return out


def candidates(img, name):
    q = lambda rva: struct.unpack_from("<Q", img.data, img.off(rva))[0]
    text = img.secs[".text"]; t0, t1 = text.VirtualAddress, text.VirtualAddress + text.Misc_VirtualSize
    found = []
    for s in img.find(name.encode() + b"\0"):
        if img.data[img.off(s) - 1] != 0: continue
        for ref in img.ptr_refs(s):
            base = ref - 0x10
            try:
                outer = q(base) - img.base
                count = struct.unpack_from("<i", img.data, img.off(base + 0x38))[0]
                if not (t0 <= outer < t1 and 0 <= count <= 32): continue
                size = q(base + 0x28); fflags = struct.unpack_from("<I", img.data, img.off(base + 0x40))[0]
                array = q(base + 0x30) - img.base if count else 0
                params = []
                for k in range(count):
                    prop = q(array + 8 * k) - img.base
                    pname = img.cstr(q(prop) - img.base)
                    if not IDENT.match(pname): raise ValueError(pname)
                    params.append((pname, GEN[img.data[img.off(prop + 0x18)] & 0x1F], q(prop + 0x10)))
                if not 0 <= size < 0x10000: continue
            except Exception:
                continue
            parms = [p for p in params if p[2] & CPF_PARM]
            ret = [p[1] for p in parms if p[2] & CPF_RETURN]
            found.append({"params_rva": hex(base), "outer_rva": hex(outer), "function_flags": hex(fflags), "parms_size": size,
                          "params": [{"name": n, "type": t, "out": bool(f & CPF_OUT), "reference": bool(f & CPF_REFERENCE)}
                                     for n, t, f in parms if not f & CPF_RETURN],
                          "return": ret[0] if ret else None})
    return found


def trivial_store(img, name):
    """Thunk evidence for a struct return: every use of the saved RESULT_PARAM register is a plain store."""
    q = lambda rva: struct.unpack_from("<Q", img.data, img.off(rva))[0]
    text = img.secs[".text"]; t0, t1 = text.VirtualAddress, text.VirtualAddress + text.Misc_VirtualSize
    thunks = set()
    for s in img.find(name.encode() + b"\0"):
        if img.data[img.off(s) - 1] != 0: continue
        for ref in img.ptr_refs(s):   # FNameNativePtrPair {NameUTF8, Pointer}
            fn = q(ref + 8) - img.base
            if t0 <= fn < t1 and img.func(fn) and img.func(fn)[0] == fn: thunks.add(fn)
    results = []
    for fn in sorted(thunks):   # a DECLARE_FUNCTION thunk saves RESULT_PARAM (r8); other pairs are not thunks
        reg, stores, other, extent = None, [], [], 0
        for ins in img.disasm(*img.func(fn)):
            text_ = "%x %s %s" % (ins.address - img.base, ins.mnemonic, ins.op_str)
            if reg is None:
                if ins.mnemonic == "mov" and ins.op_str.endswith(", r8"): reg = ins.op_str.split(",")[0]
                continue
            if not re.search(r"\b%s\b" % reg, ins.op_str): continue
            if ins.op_str.split(",")[0] == reg: break   # pop/overwrite: the pointer is dead from here
            m = re.match(r"(qword|dword|xmmword) ptr \[%s(?: \+ (0x[0-9a-f]+|\d+))?\], [a-z0-9]+$" % reg, ins.op_str)
            if m and ins.mnemonic in ("mov", "movups", "movaps", "movsd", "movss", "movq", "movdqu"):
                stores.append(text_); extent = max(extent, int(m.group(2) or "0", 0) + {"qword": 8, "dword": 4, "xmmword": 16}[m.group(1)])
            else: other.append(text_)
        if reg: results.append({"thunk_rva": hex(fn), "result_register": reg, "stores": stores, "other_uses": other,
                                "store_extent_bytes": extent, "trivial": bool(stores) and not other and extent <= 64})
    return {"thunks": results, "trivial": bool(results) and all(r["trivial"] for r in results)}


def main(src, original, out):
    assert hashlib.sha256(EXE.read_bytes()).hexdigest() == EXE_SHA, "unexpected EXE build"
    img = Image()
    used, shipped = sites(json.load(open(src, encoding="utf-8"))), sites(json.load(open(original, encoding="utf-8")))
    raw = {k: candidates(img, k.split(".")[-1]) for k in used}

    def narrowed(key):
        counts = {n for n, _ in used[key]}
        return [x for x in raw[key] if len(x["params"]) in counts] if len(counts) == 1 else raw[key]
    stage = {k: narrowed(k) for k in used}
    anchors = defaultdict(set)   # owner class -> OuterFunc of its uniquely resolved functions
    for k, c in stage.items():
        if "." in k and len(c) == 1: anchors[k.split(".")[0]].add(c[0]["outer_rva"])
    result = {"exe_sha256": EXE_SHA, "source": Path(src).name, "original": Path(original).name, "functions": {}}
    for key in sorted(used):
        c, evidence = stage[key], "EXE_UNIQUE"
        if len({str(x["return"]) for x in c}) > 1 and "." in key:
            c, evidence = [x for x in c if x["outer_rva"] in anchors[key.split(".")[0]]], "EXE_OWNER_ANCHOR"
        entry = {"candidates": raw[key], "argument_counts": sorted(Counter(n for n, _ in used[key]).items())}
        if c and len({str(x["return"]) for x in c}) == 1:
            ret = c[0]["return"]; params = c[0]["params"] if len({json.dumps(x["params"]) for x in c}) == 1 else None
            if len(c) > 1: evidence = "EXE_ALL_CANDIDATES_AGREE"
        else:
            bound = {d for _, d in shipped.get(key, []) if d not in ("ARG", "LVALUE", None)}
            ret, params, evidence = "UNRESOLVED", None, "UNRESOLVED"
            if len(bound) == 1:
                b = next(iter(bound)); r = None if b == "VOID" else b
                if not raw[key] or r in {x["return"] for x in stage[key]}:
                    ret, evidence = r, "COMPILER_BARE_STATEMENT" if b == "VOID" else "COMPILER_BINDING"
                    same = [x for x in stage[key] if x["return"] == r]
                    params = same[0]["params"] if same and len({json.dumps(x["params"]) for x in same}) == 1 else None
        entry.update({"return": ret, "params": params, "evidence": evidence,
                      "wildcard": key.startswith("KismetArrayLibrary.")})  # CustomThunk generic array functions
        if ret == "Struct": entry["trivial_store"] = trivial_store(img, key.split(".")[-1])
        result["functions"][key] = entry
    # Negative controls: FString/FText results are assigned (read/released), never plain-stored.
    result["negative_controls"] = {f: trivial_store(img, f) for f in ("Concat_StrStr", "Conv_StringToText")}
    assert not any(v["trivial"] for v in result["negative_controls"].values()), "thunk classifier accepted a non-trivial return"
    Path(out).write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    for k, v in result["functions"].items():
        print("%-62s %-10s %-26s %s" % (k, v["return"], v["evidence"], "trivial_store=%s" % v["trivial_store"]["trivial"] if "trivial_store" in v else ""))
    print("UNRESOLVED:", [k for k, v in result["functions"].items() if v["return"] == "UNRESOLVED"])


if __name__ == "__main__":
    main(*sys.argv[1:4])
