"""Reproduce the bounded Proto 1.02 analysis; read EXE bytes, never execute/modify them.

Usage: python -X utf8 tools/proto_binary_analysis/evidence.py
Only writes JSON and short disassembly excerpts under reports/rtl_research/proto_binary.
Descriptive aliases are analyst labels, not recovered C++ symbols.
"""
import hashlib
import json
import struct
from pathlib import Path

import capstone.x86 as X

from pe import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "reports/rtl_research/proto_binary"
EXPECTED_SHA256 = "365637a77d4b74a61d198a9927e3dcd437bf3be2247b96fcbe5c2e851ac14923"

# Logical spans recovered from entry, cross-chunk branches and epilogues. A single
# .pdata entry is often only one fragment, not the bounds of a C++ function.
FUNCTIONS = [
    ("proto_package_registration", 0x9A6460, 0x9A648F),
    ("style_struct_registration", 0x9A7460, 0x9A748F),
    ("style_struct_ops", 0x9A65C0, 0x9A65F5),
    ("block_class_registration", 0x9A61C0, 0x9A6272),
    ("block_constructor", 0x99BBC0, 0x99BDC1),
    ("char_decorator_class_registration", 0x9A6630, 0x9A66E2),
    ("char_decorator_object_constructor", 0x9A6960, 0x9A6989),
    ("char_decorator_factory", 0x99E9F0, 0x99EBB9),
    ("char_decorator_create_run", 0x99E130, 0x99E8CC),
    ("char_run_factory", 0x99D0E0, 0x99D39D),
    ("char_run_paint", 0x9A2BD0, 0x9A368C),
    ("style_row_to_timing_map", 0x9A4270, 0x9A48B7),
    ("style_timing_to_run_record", 0x9A1FD0, 0x9A23A2),
    ("select_print_delay", 0x9A0880, 0x9A09C8),
    ("advance_reveal_index", 0x99CDD0, 0x99CED3),
    ("process_reveal_budget", 0x9A3900, 0x9A3EB2),
    ("print_letter_by_letter", 0x9A3EC0, 0x9A4261),
    ("exec_PrintLetterByLetter", 0x9A78F0, 0x9A790F),
    ("rebuild_widget", 0x9A48C0, 0x9A50FF),
    ("shaped_range_helper", 0x132EC90, 0x132F096),
    ("slice_advance_scalar", 0x9CE980, 0x9CE984),
]

FIELDS = {
    "PrintLetterAnimationTime": (0x31CBFD0, 0x278),
    "PrintLetterInterval": (0x31CBFF8, 0x27C),
    "UseAdvancedPrintIntervals": (0x31CC020, 0x280),
    "CommaInterval": (0x31CC058, 0x284),
    "SentenceInterval": (0x31CC080, 0x288),
    "EllipsisInterval": (0x31CC0A8, 0x28C),
    "MidWordDashInterval": (0x31CC0D0, 0x290),
    "SpaceInterval": (0x31CC0F8, 0x294),
}

# Select only the instructions used by the written conclusions. These windows
# are filtered from decoding at the known function entry (never mid-instruction).
WINDOWS = {
    "style_struct_registration": [(0x9A7470, 0x9A7483)],
    "char_decorator_class_registration": [(0x9A666D, 0x9A669C)],
    "char_decorator_object_constructor": [(0x9A6979, 0x9A6983)],
    "char_decorator_factory": [(0x99EAA0, 0x99EAAA)],
    "char_decorator_create_run": [(0x99E6E3, 0x99E724)],
    "char_run_factory": [(0x99D13E, 0x99D150)],
    "char_run_paint": [
        (0x9A2D6F, 0x9A2DA3), (0x9A2DD2, 0x9A2DFC),
        (0x9A2F9C, 0x9A2FC2), (0x9A33E3, 0x9A341A),
        (0x9A353B, 0x9A3567), (0x9A3591, 0x9A35BB),
    ],
    "style_row_to_timing_map": [(0x9A4675, 0x9A46E7)],
    "style_timing_to_run_record": [(0x9A2278, 0x9A22C0)],
    "select_print_delay": [(0x9A089F, 0x9A08BC), (0x9A08EA, 0x9A097B)],
    "advance_reveal_index": [(0x99CE5F, 0x99CE8C)],
    "process_reveal_budget": [
        (0x9A39A8, 0x9A39C6), (0x9A3A0D, 0x9A3A30),
        (0x9A3B11, 0x9A3B7F), (0x9A3B95, 0x9A3BA3),
        (0x9A3D62, 0x9A3D9B),
    ],
    "print_letter_by_letter": [(0x9A3FD6, 0x9A3FF7), (0x9A4222, 0x9A422E)],
    "exec_PrintLetterByLetter": [(0x9A7905, 0x9A790F)],
    "shaped_range_helper": [(0x132ED34, 0x132ED48), (0x132EE66, 0x132EE85)],
    "slice_advance_scalar": [(0x9CE980, 0x9CE984)],
}


def analyze():
    im = Image()  # Path.read_bytes() in pe.py is the only EXE access.
    digest = hashlib.sha256(im.data).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError("Unknown executable hash; build-specific addresses are unsafe to interpret")

    def u64(rva):
        return struct.unpack_from("<Q", im.data, im.off(rva))[0]

    def pointer(rva):
        return u64(rva) - im.base

    decoded = {}
    ins_at = {}
    functions = []
    for alias, start, end in FUNCTIONS:
        ins = im.disasm(start, end)
        assert ins and ins[-1].address + ins[-1].size == im.base + end, alias
        decoded[alias] = ins
        ins_at.update({i.address - im.base: i for i in ins})
        calls = []
        for i in ins:
            if i.mnemonic == "call":
                calls.append({"rva": hex(i.address - im.base), "operand": i.op_str,
                              "target_rva": hex(i.operands[0].imm - im.base)
                              if i.operands[0].type == X.X86_OP_IMM else None})
        chunks = [{"start_rva": hex(s), "end_rva": hex(e)}
                  for s, e in zip(im.fstart, im.fend) if start <= s < end]
        functions.append({"alias": alias, "symbol_name_recovered": False,
                          "rva": hex(start), "file_offset": hex(im.off(start)),
                          "approximate_end_rva_exclusive": hex(end),
                          "span_sha256": hashlib.sha256(im.data[im.off(start):im.off(start) + end-start]).hexdigest(),
                          "evidence": "CONFIRMED_FROM_BINARY", "confidence": "HIGH",
                          "bounds_note": "logical entry-to-epilogue span; pdata may split it",
                          "pdata_fragments": chunks, "outgoing_calls": calls,
                          "incoming_pointer_references": list(map(hex, im.ptr_refs(start)))})

    fields = []
    for name, (descriptor, offset) in FIELDS.items():
        name_rva = pointer(descriptor)
        assert im.cstr(name_rva) == name
        if name == "UseAdvancedPrintIntervals":
            setter = pointer(descriptor + 0x30)
            inst = next(im.cs.disasm(im.data[im.off(setter):im.off(setter)+8], im.base+setter))
            assert inst.mnemonic == "mov" and inst.operands[0].mem.disp == offset
        else:
            setter = None
            assert struct.unpack_from("<I", im.data, im.off(descriptor)+0x24)[0] == offset
        fields.append({"field": name, "row_offset": hex(offset), "descriptor_rva": hex(descriptor),
                       "file_offset": hex(im.off(descriptor)), "string_rva": hex(name_rva),
                       "bool_setter_rva": hex(setter) if setter else None,
                       "evidence": "CONFIRMED_FROM_BINARY", "confidence": "HIGH"})

    links = [
        ("block PrintLetterByLetter slot 0x308", 0x31CABA0, 0x9A3EC0),
        ("block process-budget slot 0x358", 0x31CABF0, 0x9A3900),
        ("block delay slot 0x368", 0x31CAC00, 0x9A0880),
        ("block index slot 0x388", 0x31CAC20, 0x99CDD0),
        ("char decorator factory slot 0x270", 0x31CD6A0, 0x99E9F0),
        ("decorator create-run slot 0x10", 0x31CAFF0, 0x99E130),
        ("char run paint slot 0x90", 0x31CAFC8, 0x9A2BD0),
        ("PrintLetterByLetter native registration thunk", 0x31CDA88, 0x9A78F0),
    ]
    xrefs = []
    for label, location, target in links:
        assert pointer(location) == target, label
        xrefs.append({"kind": "absolute_pointer", "label": label, "rva": hex(location),
                      "file_offset": hex(im.off(location)), "target_rva": hex(target),
                      "evidence": "CONFIRMED_FROM_BINARY", "confidence": "HIGH"})
    targets = {s for _, s, _ in FUNCTIONS}
    for alias, ins in decoded.items():
        for i in ins:
            rva = i.address - im.base
            if i.mnemonic == "call" and i.operands[0].type == X.X86_OP_IMM:
                target = i.operands[0].imm - im.base
                if target in targets:
                    xrefs.append({"kind": "direct_call", "from_alias": alias,
                                  "rva": hex(rva), "file_offset": hex(im.off(rva)),
                                  "target_rva": hex(target), "evidence": "CONFIRMED_FROM_BINARY"})
            for o in i.operands:
                if o.type == X.X86_OP_MEM and o.mem.base == X.X86_REG_RIP:
                    target = rva + i.size + o.mem.disp
                    if target in [0x31CAF38, 0x31CAFE0, 0x31CD430, 0x31CCE72, 0x31CA898,
                                  0x400B3B0, 0x31CCF50]:
                        xrefs.append({"kind": "rip_memory", "from_alias": alias,
                                      "rva": hex(rva), "file_offset": hex(im.off(rva)),
                                      "target_rva": hex(target), "evidence": "CONFIRMED_FROM_BINARY"})

    # Evidence guards: check the decisive instructions/branch targets, not just strings.
    expected = {
        0x9A2DD2: ("lea", "eax, [rsi + 1]"),
        0x9A2DD9: ("mov", "dword ptr [rsp + 0x64], eax"),
        0x9A3406: ("addss", "xmm10, dword ptr [rsp + 0x58]"),
        0x9A3544: ("call", "0x1409ce980"),
        0x9A355D: ("addss", "xmm2, xmm0"),
        0x9A3591: ("inc", "esi"),
        0x9A35B5: ("jl", "0x1409a2dd2"),
        0x9A3FEE: ("comiss", "xmm0, xmm1"),
        0x9A3FF1: ("jbe", "0x1409a4222"),
        0x9A4228: ("call", "qword ptr [rax + 0x358]"),
        0x9A3B55: ("movss", "dword ptr [r14 + 0x7e4], xmm0"),
        0x9A3B95: ("comiss", "xmm7, dword ptr [r14 + 0x7e4]"),
        0x9A3B9D: ("jae", "0x1409a39f0"),
    }
    for rva, pair in expected.items():
        i = ins_at[rva]
        assert (i.mnemonic, i.op_str) == pair, hex(rva)

    excerpts = ["# Minimal binary excerpts", "", "RVAs, build hash locked. Analyst aliases, not symbols.", ""]
    for alias, windows in WINDOWS.items():
        excerpts.extend(["## " + alias, "", "```asm"])
        for a, b in windows:
            excerpts.append(f"; {a:#x}..{b:#x}")
            for i in decoded[alias]:
                rva = i.address - im.base
                if a <= rva < b:
                    excerpts.append(f"{rva:08x}  {i.mnemonic:8} {i.op_str}")
        excerpts.extend(["```", ""])

    for fn in functions:
        fn["important_incoming_xrefs"] = [x for x in xrefs if x["target_rva"] == fn["rva"]]
        fn["purpose"] = fn["alias"].replace("_", " ")
        fn["related_fields"] = list(FIELDS) if fn["alias"] in {
            "style_row_to_timing_map", "style_timing_to_run_record", "select_print_delay"} else []

    OUT.mkdir(parents=True, exist_ok=True)
    results = {
        "exe_sha256": digest, "image_base": hex(im.base),
        "paint_model": "PAINT_MODEL_LOGICAL_PEN",
        "zero_interval": "ZERO_INTERVAL_BATCHES_CHARACTERS",
        "timing_only_word_reveal": "WORD_REVEAL_REJECTED",
        "arabic_isolation": "ARABIC_ISOLATION_NOT_PROVEN",
        "runtime": "NOT_RUN", "tested_in_game": 0, "final": 0,
        "evidence_instruction_guards": len(expected), "reflection_fields_verified": len(fields),
        "function_spans_decoded": len(functions), "fields": fields,
        "limitations": ["No execution/emulation of the game", "No exact C++ symbol names recovered",
                        "Batching proves control flow; does not certify Paint ordering or reentrant callbacks",
                        "Word-reveal rejected for timing-only approach; other implementations not assessed"],
    }
    for name, obj in [("functions.json", functions), ("xrefs.json", xrefs), ("results.json", results)]:
        (OUT / name).write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")
    (OUT / "excerpts.md").write_text("\n".join(excerpts), encoding="utf-8")
    print(json.dumps({k: v for k, v in results.items() if k not in ["fields", "limitations"]}, indent=2))


if __name__ == "__main__":
    analyze()
