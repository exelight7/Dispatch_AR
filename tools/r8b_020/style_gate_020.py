"""Round 020: why Run 5 shows no Arabic subtitle. Read-only evidence from the shipped EXE and the installed R8b pak payload.

1. UHT FStructParams (UE4.27: SuperFunc +8, NameUTF8 +0x18, SizeOf +0x20, PropertyArray +0x30, NumProperties +0x38) for
   ProtoRichTextStyleRow and RichTextStyleRow: their super structs and declared properties.
2. URichTextBlock::RebuildStyleInstance (the function building FSlateStyleSet(TEXT("RichTextStyle"))): it reads
   TextStyleSet->RowStruct, calls FRichTextStyleRow::StaticStruct and runs the inlined FStructBaseChain IsChildOf test
   before the row loop; a failed test skips every row.
3. The RowStruct names serialized in the four DT_AR tables of the staging payload (byte-equal to the installed pak).
python -X utf8 -I tools/r8b_020/style_gate_020.py <out.json>
"""
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/proto_binary_analysis"))
from pe import Image, EXE  # noqa: E402

EXE_SHA = "365637a77d4b74a61d198a9927e3dcd437bf3be2247b96fcbe5c2e851ac14923"
PAYLOAD = ROOT / "builds/rtl_poc/r8b_runtime_staging_019/payload/Dispatch/Content/ArabicReveal"
TABLES = ["DT_AR_Fill", "DT_AR_Fill_Large", "DT_AR_Outline", "DT_AR_Outline_Large"]


def main(out):
    assert hashlib.sha256(EXE.read_bytes()).hexdigest() == EXE_SHA, "unsupported EXE"
    img = Image()
    q = lambda rva: struct.unpack_from("<Q", img.data, img.off(rva))[0]
    i32 = lambda rva: struct.unpack_from("<i", img.data, img.off(rva))[0]
    cstr = lambda va: img.cstr(va - img.base)

    def rip(ins):
        return ins.address + ins.size + int(ins.op_str.split("rip")[1].split("]")[0].replace(" ", ""), 16) - img.base

    def struct_params(name):
        hits = [p - 0x18 for s in img.find(b"\0" + name.encode() + b"\0") for p in img.ptr_refs(s + 1)]
        assert len(hits) == 1, (name, hits)
        p = hits[0]
        props = [cstr(q(q(q(p + 0x30) - img.base + 8 * k) - img.base)) for k in range(i32(p + 0x38))]
        f = img.func(q(p + 8) - img.base)
        supers = [cstr(q(rip(i) + 0x18)) for i in img.disasm(*f) if i.mnemonic == "lea" and "rip" in i.op_str and img.off(rip(i))
                  and 0 < q(rip(i) + 0x18) - img.base < len(img.data)]
        return {"params_rva": hex(p), "size_of": q(p + 0x20), "properties": props, "super_func_rva": hex(f[0]), "super": supers[0]}

    proto, stock = struct_params("ProtoRichTextStyleRow"), struct_params("RichTextStyleRow")
    assert proto["super"] == stock["super"] == "TableRowBase" and "TextStyle" in proto["properties"]

    def wide_exact(s):
        return [r for r in img.find(s + "\0", wide=True) if img.data[img.off(r) - 2:img.off(r)] == b"\0\0"]
    (style_set,), (row_name,) = wide_exact("RichTextStyle"), wide_exact("RichTextStyleRow")
    code = img.rip_refs([style_set, row_name])
    (rebuild,) = {img.func(c) for c in code[style_set]}
    static_struct = {img.func(c)[0] for c in code[row_name]}
    # The struct registrar passes the StaticStruct body as its construct callback (lea rcx, [fn]).
    callbacks = {rip(i): f for f in static_struct for i in img.disasm(*img.func(f)) if i.mnemonic == "lea" and "rip" in i.op_str}
    gate, registrar = [], None
    listing = img.disasm(*rebuild)
    for n, ins in enumerate(listing):
        if ins.mnemonic == "call" and ins.op_str.startswith("0x") and int(ins.op_str, 16) - img.base in callbacks:
            registrar = callbacks[int(ins.op_str, 16) - img.base]
            gate = ["%x %s %s" % (i.address - img.base, i.mnemonic, i.op_str) for i in listing[n - 4:n + 13]]
    text = " | ".join(gate)
    assert "qword ptr [r13 + 0x140]" in text and "[rax + 0x28]" in text, "TextStyleSet->RowStruct load not found"
    assert "lea rdx, [rax + 0x30]" in text and "dword ptr [rax + 0x38]" in text and "rcx*8" in text, "IsChildOf chain test not found"

    tables = {}
    for t in TABLES:
        b = (PAYLOAD / (t + ".uasset")).read_bytes()
        tables[t] = {"ProtoRichTextStyleRow": b"ProtoRichTextStyleRow\0" in b, "/Script/ProtoAnimatedText": b"/Script/ProtoAnimatedText\0" in b,
                     "exact RichTextStyleRow name": b"\x11\x00\x00\x00RichTextStyleRow\0" in b, "/Script/UMG": b"/Script/UMG\0" in b}
        assert tables[t]["ProtoRichTextStyleRow"] and not tables[t]["exact RichTextStyleRow name"]

    result = {
        "status": "R8B_STYLE_TABLE_REJECTED_BY_URICHTEXTBLOCK",
        "exe_sha256": EXE_SHA,
        "ProtoRichTextStyleRow": proto, "RichTextStyleRow": stock,
        "rebuild_style_instance": {"function_rva": hex(rebuild[0]), "size": rebuild[1] - rebuild[0],
                                   "RichTextStyleRow_registrar_rva": hex(registrar), "gate_instructions": gate},
        "installed_tables_row_struct": tables,
        "conclusion": "Both row structs derive directly from FTableRowBase, so DT_AR_* (ProtoRichTextStyleRow) fail "
                      "IsChildOf(FRichTextStyleRow); URichTextBlock keeps an empty style set: no Default and no u0..u36 rows.",
    }
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(result["status"], proto["super"], proto["size_of"], stock["size_of"], hex(rebuild[0]))


if __name__ == "__main__":
    main(sys.argv[1])
