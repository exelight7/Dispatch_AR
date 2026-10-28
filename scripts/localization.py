"""Read Dispatch's v1/v3 locres resources and maintain lossless translation records.

All commands operate inside this workspace; original game packages are read-only.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import struct

ROOT = Path(__file__).resolve().parents[1]
MAGIC = bytes.fromhex("0e147475674a03fc4a15909dc3377f1b")


class Reader:
    def __init__(self, data: bytes):
        self.data, self.pos = data, 0

    def take(self, size: int) -> bytes:
        if size < 0 or self.pos + size > len(self.data):
            raise ValueError("Truncated resource")
        value = self.data[self.pos:self.pos + size]
        self.pos += size
        return value

    def number(self, fmt="<I"):
        return struct.unpack(fmt, self.take(struct.calcsize(fmt)))[0]

    def string(self) -> str:
        count = self.number("<i")
        if count == 0:
            return ""
        raw = self.take(abs(count) * (2 if count < 0 else 1))
        null = b"\0\0" if count < 0 else b"\0"
        if not raw.endswith(null):
            raise ValueError("Unterminated FString")
        return raw[:-len(null)].decode("utf-16le" if count < 0 else "utf-8")

    def key(self, version=3):
        start = self.pos
        if version == 3:
            self.number()
        text = self.string()
        return text, self.data[start:self.pos]


def fstring(text: str) -> bytes:
    if "\0" in text:
        raise ValueError("Embedded NUL")
    if text.isascii():
        raw = text.encode("ascii") + b"\0"
        return struct.pack("<i", len(raw)) + raw
    raw = text.encode("utf-16le") + b"\0\0"
    return struct.pack("<i", -len(raw) // 2) + raw


def read_locres(data: bytes):
    r = Reader(data)
    if r.take(16) != MAGIC:
        raise ValueError("Invalid localization resource magic")
    version = r.number("<B")
    if version not in (1, 3):
        raise ValueError("Only confirmed Dispatch locres versions 1 and 3 are supported")
    strings_offset = r.number("<q")
    total = r.number() if version == 3 else None
    namespace_count = r.number()
    groups, rows = [], []
    for _ in range(namespace_count):
        namespace, raw_namespace = r.key(version)
        group = {"namespace": namespace, "raw_key": raw_namespace, "rows": []}
        for _ in range(r.number()):
            key, raw_key = r.key(version)
            row = {"namespace": namespace, "key": key, "raw_key": raw_key,
                   "source_hash": r.number(), "string_index": r.number()}
            group["rows"].append(row)
            rows.append(row)
        groups.append(group)
    if r.pos != strings_offset or (total is not None and len(rows) != total):
        raise ValueError("Resource index length/count mismatch")
    strings = [(r.string(), r.number("<i") if version == 3 else None) for _ in range(r.number())]
    if r.pos != len(data):
        raise ValueError("Unexpected resource trailing data")
    references = Counter(row["string_index"] for row in rows)
    for i, (_, count) in enumerate(strings):
        if count is not None and references[i] != count:
            raise ValueError("String reference count mismatch")
    for row in rows:
        row["text"] = strings[row["string_index"]][0]
    return {"groups": groups, "rows": rows, "data": data, "version": version}


def compile_locres(resource, translations: dict[tuple[str, str], str]) -> bytes:
    # Preserve serialized namespace/key hashes and source hashes exactly.
    entries, pool, indexes, refs = bytearray(), [], {}, Counter()
    for group in resource["groups"]:
        entries += group["raw_key"] + struct.pack("<I", len(group["rows"]))
        for row in group["rows"]:
            text = translations.get((row["namespace"], row["key"]), row["text"])
            if text not in indexes:
                indexes[text] = len(pool)
                pool.append(text)
            index = indexes[text]
            refs[index] += 1
            entries += row["raw_key"] + struct.pack("<II", row["source_hash"], index)
    version = resource["version"]
    offset = (33 if version == 3 else 29) + len(entries)
    header = MAGIC + bytes([version]) + struct.pack("<q", offset)
    if version == 3:
        header += struct.pack("<I", len(resource["rows"]))
    out = bytearray(header + struct.pack("<I", len(resource["groups"]))) + entries
    out += struct.pack("<I", len(pool))
    for i, text in enumerate(pool):
        out += fstring(text)
        if version == 3:
            out += struct.pack("<i", refs[i])
    result = bytes(out)
    verify = read_locres(result)
    assert [(r["namespace"], r["key"], r["source_hash"]) for r in verify["rows"]] == [
        (r["namespace"], r["key"], r["source_hash"]) for r in resource["rows"]]
    return result


def select_resource(resource, identities):
    """Build an explicit native-runtime subset without copying editor strings."""
    available = {(row["namespace"], row["key"]) for row in resource["rows"]}
    if not identities <= available:
        raise ValueError("Selected localization identities are missing from original resource")
    groups = []
    for group in resource["groups"]:
        rows = [r for r in group["rows"] if (r["namespace"], r["key"]) in identities]
        if rows:
            groups.append({**group, "rows": rows})
    return {**resource, "groups": groups, "rows": [r for g in groups for r in g["rows"]]}


def json_tree(node, parent=""):
    namespace = ".".join(x for x in [parent, node.get("Namespace", "")] if x)
    for child in node.get("Children", []):
        yield namespace, child
    for sub in node.get("Subnamespaces", []):
        yield from json_tree(sub, namespace)


def category(namespace, paths):
    if re.search(r"^(Online|NetworkErrors|EPartyReservation)", namespace):
        return "System Messages"
    if re.search(r"^(Input|FInputChord|SlateAccessibility|UICommands|EditableText)", namespace):
        return "Controls/Accessibility"
    text = " ".join([namespace] + paths).lower()
    for pattern, label in [("line_", "Dialogue/Subtitles"), ("choice", "Choices"),
            ("tutorial|ftue", "Tutorials"), ("notif", "Notifications"),
            ("characters", "Character Names"), ("settings", "Settings"),
            ("objective|mission", "Objectives"), ("credits", "Credits"),
            ("hero.*database", "Descriptions"), ("menu", "Menus"),
            ("hacking", "Phone / Computer UI")]:
        if re.search(pattern, text):
            return label
    return "UI/Other (review context)"


def export_sources():
    out = ROOT / "translation" / "source"
    out.mkdir(exist_ok=True)
    stats = []
    paths = list((ROOT / "extracted/Dispatch/Content/Localization").glob("*/en/*.locres"))
    paths += list((ROOT / "extracted/Engine/Plugins/Online").glob("*/Content/Localization/*/en/*.locres"))
    scope_path = ROOT / "translation/engine_scope.json"
    scope = json.loads(scope_path.read_text(encoding="utf-8")) if scope_path.exists() else None
    if scope:
        paths.append(ROOT / "extracted" / scope["source_file"])
    for path in sorted(paths):
        target = path.stem
        resource = read_locres(path.read_bytes())
        full_resource_count = len(resource["rows"])
        if scope and path.relative_to(ROOT / "extracted").as_posix() == scope["source_file"]:
            target = "EngineRuntime"
            resource = select_resource(resource, {(r["namespace"], r["key"]) for r in scope["identities"]})
        manifest_path = path.parent.parent / f"{target}.manifest"
        manifest = json.loads(manifest_path.read_text(encoding="utf-16")) if manifest_path.exists() else {}
        contexts = {}
        for ns, child in json_tree(manifest):
            for entry in child.get("Keys", []):
                contexts.setdefault((ns, entry["Key"]), []).append(entry.get("Path", ""))
        rows = []
        for i, row in enumerate(resource["rows"]):
            paths = contexts.get((row["namespace"], row["key"]), [])
            speaker = ""
            for source_path in paths:
                match = re.search(r"/Line_([^/.]+)_[^/._]+\.", source_path)
                if match:
                    speaker = match[1].replace("_", " ")
                    break
            rows.append({"id": f"{target}:{row['namespace']}:{row['key']}",
                "index": i, "target": target, "namespace": row["namespace"],
                "key": row["key"], "source_hash": row["source_hash"],
                "source_file": path.relative_to(ROOT / "extracted").as_posix(),
                "context": paths, "speaker": speaker,
                "category": category(row["namespace"], paths),
                "en": row["text"], "ar": "", "status": "TODO", "notes": ""})
        temporary = out / f"{target}.json.tmp"
        temporary.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(out / f"{target}.json")
        # Semantic roundtrip permits pool reorder; byte equality is also recorded.
        rebuilt = compile_locres(resource, {})
        assert [r["text"] for r in read_locres(rebuilt)["rows"]] == [r["text"] for r in resource["rows"]]
        assert compile_locres(read_locres(rebuilt), {}) == rebuilt
        stats.append({"target": target, "strings": len(rows),
            "original_resource_rows": full_resource_count,
            "words": sum(len(r["en"].split()) for r in rows),
            "manifest_keys": len(contexts), "unmapped_runtime_keys": sum(not r["context"] for r in rows),
            "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "semantic_roundtrip": True, "compile_idempotent": True,
            "byte_roundtrip": rebuilt == path.read_bytes(),
            "categories": dict(Counter(r["category"] for r in rows))})
    (ROOT / "reports/text_sources.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"targets": len(stats), "strings": sum(s["strings"] for s in stats),
                      "words": sum(s["words"] for s in stats)}, indent=2))


def selftest():
    for text in ["", "plain", "مرحبًا", "مُ", "اضغط E: 250 XP.", "emoji \U0001f600"]:
        r = Reader(fstring(text))
        assert r.string() == text and r.pos == len(r.data)
    try:
        Reader(b"\x10\0\0\0x").string()
    except ValueError:
        pass
    else:
        raise AssertionError("Truncation accepted")
    print("FString Unicode and bounds self-check passed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["export", "selftest"])
    args = parser.parse_args()
    selftest() if args.command == "selftest" else export_sources()
