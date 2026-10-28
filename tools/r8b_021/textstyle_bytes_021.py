"""Round 021: independent byte-level proof for the rebuilt DT_AR tables (no UAssetAPI).

Parses the UE4.27 cooked .uasset header (NameMap, ImportMap, ExportMap) and the DataTable export in .uexp (tagged
properties, NumRows, rows of tagged properties) for the round-019 and round-021 tables, then requires:
- RowStruct resolves to /Script/UMG.RichTextStyleRow (021) and /Script/ProtoAnimatedText.ProtoRichTextStyleRow (019);
- NameMap differs only by the two in-place renames and the ImportMap bytes are identical;
- every 021 row holds exactly the TextStyle tag, byte-identical to the 019 row's TextStyle tag;
- the 021 export equals the 019 export with the eight Proto-only row tags cut out, byte for byte.
python -X utf8 -I tools/r8b_021/textstyle_bytes_021.py <stylefix_dir> <out.json>
"""
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OLD = ROOT / "builds/rtl_poc/stage1/Dispatch/Content/ArabicReveal"
TABLES = ["DT_AR_Fill", "DT_AR_Fill_Large", "DT_AR_Outline", "DT_AR_Outline_Large"]
PROTO_ONLY = ["PrintLetterAnimationTime", "PrintLetterInterval", "UseAdvancedPrintIntervals", "CommaInterval",
              "SentenceInterval", "EllipsisInterval", "MidWordDashInterval", "SpaceInterval"]
RENAMES = {("ProtoRichTextStyleRow", "RichTextStyleRow"), ("/Script/ProtoAnimatedText", "/Script/UMG")}


class Package:
    def __init__(self, uasset):
        h = uasset.read_bytes(); self.uexp = uasset.with_suffix(".uexp").read_bytes()
        i32 = lambda o: struct.unpack_from("<i", h, o)[0]
        assert struct.unpack_from("<I", h, 0)[0] == 0x9E2A83C1 and i32(4) == -7, "not a UE4.27 package"
        o = 20 + 4 + 20 * i32(20)                                     # tag, legacy, UE3, UE4, licensee, custom versions
        header_size = i32(o); o += 4
        o = self.fstring(h, o)[1]                                     # FolderName
        flags = struct.unpack_from("<I", h, o)[0]; o += 4
        assert flags & 0x80000000, "expected a cooked (FilterEditorOnly) package"
        name_count, name_offset = i32(o), i32(o + 4); o += 8 + 8      # names, gatherable text
        export_count, export_offset, import_count, import_offset = (i32(o + 4 * k) for k in range(4))
        assert len(h) == header_size and export_count == 1
        self.names, p = [], name_offset
        for _ in range(name_count):
            s, p = self.fstring(h, p); self.names.append(s); p += 4   # two serialized hashes
        self.import_bytes = h[import_offset:import_offset + 28 * import_count]
        self.imports = [struct.unpack_from("<iiiiiii", h, import_offset + 28 * k) for k in range(import_count)]
        size, offset = struct.unpack_from("<qq", h, export_offset + 28)
        assert offset == header_size and offset - header_size + size + 4 == len(self.uexp) and self.uexp[-4:] == h[:4]
        self.export = self.uexp[:size]

    @staticmethod
    def fstring(b, o):
        n = struct.unpack_from("<i", b, o)[0]; o += 4
        if n >= 0: return b[o:o + n].rstrip(b"\0").decode("ascii"), o + n
        return b[o:o - 2 * n].decode("utf-16-le").rstrip("\0"), o - 2 * n

    def name(self, b, o):
        index, number = struct.unpack_from("<ii", b, o)
        return self.names[index] + ("" if number == 0 else "_%d" % (number - 1))

    def tags(self, o):
        """Tagged properties from o up to and including None: [(name, raw bytes)], end offset."""
        b, out = self.export, []
        while True:
            start, name = o, self.name(b, o); o += 8
            if name == "None": return out, o
            kind = self.name(b, o); size = struct.unpack_from("<i", b, o + 8)[0]; o += 16
            o += {"StructProperty": 24, "BoolProperty": 1, "ByteProperty": 8, "EnumProperty": 8, "ArrayProperty": 8, "SetProperty": 8, "MapProperty": 16}.get(kind, 0)
            o += 1 + (16 if b[o] else 0)
            o += size; out.append((name, b[start:o]))

    def table(self):
        props, o = self.tags(0)
        assert [n for n, _ in props] == ["RowStruct"]
        row_struct = struct.unpack_from("<i", props[0][1], len(props[0][1]) - 4)[0]
        assert struct.unpack_from("<i", self.export, o)[0] == 0; o += 4          # no object GUID
        count = struct.unpack_from("<i", self.export, o)[0]; o += 4
        self.rows_start, rows = o, []
        for _ in range(count):
            row = self.name(self.export, o); o += 8
            tags, end = self.tags(o); rows.append((row, self.export[o - 8:o], tags, self.export[end - 8:end])); o = end
        assert o == len(self.export), "trailing export bytes"
        _, _, cls, _, outer, obj, _ = self.imports[-row_struct - 1]
        package = self.imports[-outer - 1]
        return self.names[package[5]] + "." + self.names[obj], self.names[cls], rows


def main(directory, out):
    result, ok = {"rule": __doc__.splitlines()[0], "tables": {}}, True
    for t in TABLES:
        old, new = Package(OLD / (t + ".uasset")), Package(Path(directory) / (t + ".uasset"))
        old_struct, old_cls, old_rows = old.table(); new_struct, new_cls, new_rows = new.table()
        renames = {(a, b) for a, b in zip(old.names, new.names) if a != b}
        # The 019 export with each row cut down to FName + TextStyle tag + None (name indices are shared after in-place renames).
        rebuilt = old.export[:old.rows_start] + b"".join(name + tags[0][1] + none for _, name, tags, none in old_rows)
        rows_ok = [n == m and [x for x, _ in a] == ["TextStyle"] + PROTO_ONLY and [x for x, _ in b] == ["TextStyle"] and a[0][1] == b[0][1]
                   for (n, _, a, _), (m, _, b, _) in zip(old_rows, new_rows)]
        checks = {
            "row_struct_019": old_struct, "row_struct_021": new_struct, "row_struct_class": new_cls,
            "row_struct_021_is_stock": new_struct == "/Script/UMG.RichTextStyleRow" and new_cls == "ScriptStruct",
            "row_struct_019_is_proto": old_struct == "/Script/ProtoAnimatedText.ProtoRichTextStyleRow",
            "rows": [r[0] for r in new_rows], "row_count": len(new_rows),
            "rows_textstyle_bytes_identical": sum(rows_ok),
            "namemap_only_renames": len(old.names) == len(new.names) and renames == RENAMES,
            "import_map_bytes_identical": old.import_bytes == new.import_bytes,
            "export_equals_019_minus_proto_tags": rebuilt == new.export,
            "old_export_sha256": hashlib.sha256(old.export).hexdigest(), "new_export_sha256": hashlib.sha256(new.export).hexdigest(),
            "textstyle_sha256_by_row": {r[0]: hashlib.sha256(r[2][0][1]).hexdigest() for r in new_rows},
        }
        good = (checks["row_struct_021_is_stock"] and checks["row_struct_019_is_proto"] and len(new_rows) == 38 and all(rows_ok)
                and checks["rows"] == ["Default"] + ["u%d" % k for k in range(37)] and checks["namemap_only_renames"]
                and checks["import_map_bytes_identical"] and checks["export_equals_019_minus_proto_tags"])
        checks["status"] = "PASS" if good else "FAIL"; ok &= good
        result["tables"][t] = checks
    result["status"] = "TEXTSTYLE_BYTES_IDENTICAL" if ok else "FAIL"
    Path(out).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(result["status"], {t: (v["row_struct_021"], v["rows_textstyle_bytes_identical"]) for t, v in result["tables"].items()})
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
