"""Scan cooked UE4.27 packages for serialized FText and check them against the translated locres identities.

python -X utf8 tools/coverage/cooked_text_scan.py <folder with extracted .uexp/.uasset> [--out reports/coverage/cooked_text_scan.json]

Two exact FText layouts are recognised (cooked, unversioned UE4.27):
  * culture-invariant:  uint32 flags with bit 1 (CultureInvariant) | int8 -1 (no history) | uint32 1 | FString
  * localizable base:   uint32 flags | int8 0 (Base history) | FString namespace | FString key (32 hex) | FString source
Culture-invariant text can never be localized through locres; localizable text must have a locres identity.
The input folder must hold copies outside the game installation. Nothing is written except the report.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import re
import struct

ROOT = Path(__file__).resolve().parents[2]
INVARIANT = re.compile(rb"([\x00-\xff]{4})\xff\x01\x00\x00\x00")
KEY = re.compile(rb"\x21\x00\x00\x00([0-9A-F]{32})\x00")


def fstring(data, pos):
    if pos + 4 > len(data):
        return None, pos
    n = struct.unpack_from("<i", data, pos)[0]
    pos += 4
    if n == 0:
        return "", pos
    size = n if n > 0 else -2 * n
    if not 0 < abs(n) <= 4096 or pos + size > len(data):
        return None, pos
    raw = data[pos:pos + size]
    try:
        text = raw[:-1].decode("ascii") if n > 0 else raw[:-2].decode("utf-16le")
    except UnicodeDecodeError:
        return None, pos
    if raw[-1:] != b"\0":
        return None, pos
    return text, pos + size


def scan(data):
    invariant, localizable = [], []
    for m in INVARIANT.finditer(data):
        flags = struct.unpack("<I", m[1])[0]
        if flags & 2 and flags < 0x100:
            text, _ = fstring(data, m.end())
            if text:
                invariant.append(text)
    for m in KEY.finditer(data):
        key = m[1].decode()
        source, _ = fstring(data, m.end())
        # Walk back over the namespace FString to the Base history byte.
        for ns_len in range(0, 200):
            start = m.start() - 4 - ns_len
            if start < 1:
                break
            ns, end = fstring(data, start)
            if ns is not None and end == m.start() and data[start - 1] == 0:
                if source is not None:
                    localizable.append((ns, key, source))
                break
    return invariant, localizable


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("--out", type=Path, default=ROOT / "reports/coverage/cooked_text_scan.json")
    args = parser.parse_args()
    folder = args.folder.resolve()
    if "steamapps" in str(folder).lower():
        raise SystemExit("Scan copies only, never the game installation")
    identities = {}
    for path in sorted((ROOT / "translation/source").glob("*.json")):
        for row in json.loads(path.read_text(encoding="utf-8")):
            identities[(row["namespace"], row["key"])] = row["target"]
    manifest_only = {(r["namespace"], r["key"]) for r in json.loads((ROOT / "reports/manifest_only_keys.json").read_text(encoding="utf-8"))}
    inv, loc = defaultdict(set), defaultdict(set)
    files = 0
    for path in sorted(folder.rglob("*")):
        if path.suffix not in (".uexp", ".uasset", ".umap"):
            continue
        files += 1
        name = path.relative_to(folder).as_posix()
        a, b = scan(path.read_bytes())
        for text in a:
            inv[text].add(name)
        if "/ST_" in "/" + name:
            continue  # string tables store FString key/value pairs, not FText; verified per table instead
        for ns, key, source in b:
            loc[(ns, key, source)].add(name)
    localizable = []
    for (ns, key, source), where in sorted(loc.items()):
        target = identities.get((ns, key))
        localizable.append({"namespace": ns, "key": key, "en": source, "files": sorted(where),
                            "translated_target": target,
                            "status": "LOCALIZED_ALREADY" if target else
                            ("SOURCE_ONLY_MANIFEST" if (ns, key) in manifest_only else "NO_LOCRES_IDENTITY")})
    report = {"folder_files_scanned": files,
              "culture_invariant_texts": [{"en": t, "files": sorted(w)} for t, w in sorted(inv.items())],
              "localizable_texts": localizable,
              "summary": {"culture_invariant_unique": len(inv), "localizable_unique": len(localizable),
                          "localizable_with_translated_identity": sum(r["status"] == "LOCALIZED_ALREADY" for r in localizable),
                          "localizable_without_identity": sum(r["status"] == "NO_LOCRES_IDENTITY" for r in localizable)}}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
