"""Read/write UE4.27 .locmeta (FTextLocalizationMetaDataResource, version 1) and build a detached
prototype that adds the 'ar' culture to CompiledCultures. Nothing is installed or packed.

python -X utf8 tools/arabic_activation/locmeta.py selftest
python -X utf8 tools/arabic_activation/locmeta.py prototype
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from localization import Reader, fstring  # noqa: E402

MAGIC = bytes.fromhex("4fee4ca1684855836c4c46bd70da507c")
OUT = ROOT / "reports/arabic_activation/prototype"


def read(data: bytes):
    r = Reader(data)
    if r.take(16) != MAGIC:
        raise ValueError("Not a locmeta file")
    version = r.number("<B")
    if version != 1:
        raise ValueError("Only locmeta version 1 is supported")
    native, native_res = r.string(), r.string()
    cultures = [r.string() for _ in range(r.number("<i"))]
    if r.pos != len(data):
        raise ValueError("Trailing locmeta data")
    return {"version": version, "native_culture": native, "native_locres": native_res, "compiled_cultures": cultures}


def write(meta) -> bytes:
    out = MAGIC + bytes([meta["version"]]) + fstring(meta["native_culture"]) + fstring(meta["native_locres"])
    out += struct.pack("<i", len(meta["compiled_cultures"]))
    for culture in meta["compiled_cultures"]:
        out += fstring(culture)
    return out


def originals():
    return sorted((ROOT / "extracted").rglob("*.locmeta"))


def selftest():
    files = originals()
    assert files, "no extracted locmeta"
    for path in files:
        data = path.read_bytes()
        assert write(read(data)) == data, path
    meta = read(files[0].read_bytes())
    added = {**meta, "compiled_cultures": sorted(set(meta["compiled_cultures"]) | {"ar"}, key=str.lower)}
    assert read(write(added))["compiled_cultures"].count("ar") == 1
    try:
        read(b"bad" * 10)
    except ValueError:
        pass
    else:
        raise AssertionError("bad magic accepted")
    print(f"locmeta byte round-trip passed for {len(files)} files")


def prototype():
    selftest()
    records = []
    for path in originals():
        rel = path.relative_to(ROOT / "extracted")
        if not rel.as_posix().startswith("Dispatch/"):
            continue  # Engine/plugin targets only matter for engine text; the game list is what the engine validates first
        meta = read(path.read_bytes())
        cultures = sorted(set(meta["compiled_cultures"]) | {"ar"}, key=str.lower)
        data = write({**meta, "compiled_cultures": cultures})
        dest = OUT / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        records.append({"file": rel.as_posix(), "original_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                        "prototype_sha256": hashlib.sha256(data).hexdigest(), "original_cultures": meta["compiled_cultures"],
                        "prototype_cultures": cultures})
    (OUT / "locmeta_prototype.json").write_text(json.dumps({
        "status": "DETACHED_PROTOTYPE_NOT_INSTALLED_NOT_PACKED", "files": records,
        "purpose": "Adds 'ar' to CompiledCultures so the engine's available-culture list (read from <Target>.locmeta) can contain ar.",
        "effect_on_other_cultures": "Only the culture list gains one entry; native culture, native locres path and all other entries are unchanged.",
        "runtime": "NOT_PROVEN"}, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(records)} prototype locmeta files under {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    {"selftest": selftest, "prototype": prototype}[sys.argv[1]]()
