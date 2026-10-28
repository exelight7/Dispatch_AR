"""Round 012 adapter: verify every new import against the shipped EXE's UHT reflection tables (read-only).

Decodes UE4.27 UECodeGen_Private::FFunctionParams (NameUTF8 at +0x10, PropertyArray +0x30, NumProperties +0x38,
FunctionFlags +0x40) and FPropertyParamsBase (NameUTF8 +0, PropertyFlags +0x10, GenFlags +0x18, type mask 0x1F).
Geometry is additionally checked in the shipped WBP_SimpleFadeSwitcher import table (the Tick template).
Run: python -I tools/proto_binary_analysis/clock_imports_012.py <out.json>
"""
import hashlib
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pe import Image, EXE  # noqa: E402

EXE_SHA = "365637a77d4b74a61d198a9927e3dcd437bf3be2247b96fcbe5c2e851ac14923"
GEN = {0x0A: "Float", 0x0C: "Bool", 0x12: "Object", 0x15: "Str", 0x19: "Struct"}
FUNC_FINAL, FUNC_NATIVE, FUNC_STATIC, FUNC_EVENT, FUNC_BP_EVENT = 0x1, 0x400, 0x2000, 0x800, 0x8000000
EXPECTED = {  # function -> (required flags, [(param, gen type)]) ; return values included
    "K2_SetTimer": (FUNC_FINAL | FUNC_NATIVE | FUNC_STATIC, [("Object", "Object"), ("FunctionName", "Str"), ("Time", "Float"),
                    ("bLooping", "Bool"), ("InitialStartDelay", "Float"), ("InitialStartDelayVariance", "Float"), ("ReturnValue", "Struct")]),
    "K2_ClearTimer": (FUNC_FINAL | FUNC_NATIVE | FUNC_STATIC, [("Object", "Object"), ("FunctionName", "Str")]),
    "GetTimeSeconds": (FUNC_FINAL | FUNC_NATIVE | FUNC_STATIC, [("WorldContextObject", "Object"), ("ReturnValue", "Float")]),
    "GetUnpausedTimeSeconds": (FUNC_FINAL | FUNC_NATIVE | FUNC_STATIC, [("WorldContextObject", "Object"), ("ReturnValue", "Float")]),
    "FMax": (FUNC_FINAL | FUNC_NATIVE | FUNC_STATIC, [("A", "Float"), ("B", "Float"), ("ReturnValue", "Float")]),
    "Tick": (FUNC_EVENT | FUNC_BP_EVENT, [("MyGeometry", "Struct"), ("InDeltaTime", "Float")]),
}


def main(out):
    assert hashlib.sha256(EXE.read_bytes()).hexdigest() == EXE_SHA, "unexpected EXE build"
    img = Image()
    q = lambda rva: struct.unpack_from("<Q", img.data, img.off(rva))[0]
    result = {"exe_sha256": EXE_SHA, "functions": {}}
    for name, (flags, params) in EXPECTED.items():
        matches = []
        for s in img.find(name.encode() + b"\0"):
            if img.data[img.off(s) - 1] != 0:
                continue  # suffix of a longer string
            for ref in img.ptr_refs(s):
                base = ref - 0x10
                try:
                    count = struct.unpack_from("<i", img.data, img.off(base + 0x38))[0]
                    fflags = struct.unpack_from("<I", img.data, img.off(base + 0x40))[0]
                    array = q(base + 0x30) - img.base
                    if not 0 <= count <= 16 or (count and not 0 < array < len(img.data) * 2):
                        continue
                    got = []
                    for k in range(count):
                        prop = q(array + 8 * k) - img.base
                        gen = img.data[img.off(prop + 0x18)] & 0x1F  # 0x20 = NativeBool modifier
                        got.append((img.cstr(q(prop) - img.base), GEN.get(gen, hex(gen))))
                except Exception:
                    continue
                if sorted(got) == sorted(params) and fflags & flags == flags:
                    matches.append({"params_rva": hex(base), "function_flags": hex(fflags), "params": got})
        assert len(matches) == 1, (name, matches)
        result["functions"][name] = matches[0]
    fade = Path(__file__).resolve().parents[2] / "extracted/Dispatch/Content/Shared/Core/Widgets/WBP_SimpleFadeSwitcher.uasset"
    raw = fade.read_bytes()
    assert b"/Script/SlateCore\0" in raw and b"Geometry\0" in raw, "shipped Geometry import absent"
    result["geometry_import"] = {"package": "/Script/SlateCore", "shipped_in": "WBP_SimpleFadeSwitcher.uasset",
                                 "sha256": hashlib.sha256(raw).hexdigest()}
    Path(out).write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    print("CLOCK_IMPORTS_VERIFIED", ", ".join(result["functions"]))


if __name__ == "__main__":
    main(sys.argv[1])
