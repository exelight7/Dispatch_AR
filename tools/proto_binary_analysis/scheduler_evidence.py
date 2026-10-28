"""Read-only, build-locked excerpts for round 011; never runs the game or reads the local AES key.

Writes a new evidence file only. Fragment boundaries below are explicit excerpt ranges,
not a claim that each .pdata record is a whole logical C++ function.
"""
import hashlib
import json
import sys
from pathlib import Path

from pe import Image

ROOT = Path(__file__).resolve().parents[2]
EXPECTED = "365637a77d4b74a61d198a9927e3dcd437bf3be2247b96fcbe5c2e851ac14923"
SPANS = [
    ("native_budget_and_rearm", 0x9A3900, 0x9A3EB2),
    ("normal_finish", 0x9A07B0, 0x9A0848),
    ("show_text", 0x9A5710, 0x9A5772),
    ("stop_early", 0x9A5A30, 0x9A5B20),
    ("exec_ShowText", 0x9A7A30, 0x9A7A60),
    ("wrap_native_thunk", 0xCAAE80, 0xCAAF39),
    ("wrap_implementation", 0xCA7BB0, 0xCA7C00),
    ("wrap_parameter_class_getter", 0x1F13A60, 0x1F13A70),
    ("text_layout_class_getter", 0x1F0C270, 0x1F0C290),
    ("text_layout_class_constructor", 0x1F15260, 0x1F15340),
]


def main():
    output = ROOT / (sys.argv[1] if len(sys.argv) > 1 else
                     "reports/rtl_research/renderer_repair/scheduler_011/native_evidence.json")
    if output.exists():
        raise FileExistsError("Refusing to overwrite existing evidence")
    image = Image()
    digest = hashlib.sha256(image.data).hexdigest()
    assert digest == EXPECTED, "Unsupported executable build"
    excerpts = []
    for label, start, end in SPANS:
        code = image.data[image.off(start):image.off(start) + end-start]
        excerpts.append({"label": label, "start_rva": hex(start), "end_rva_exclusive": hex(end),
                         "sha256": hashlib.sha256(code).hexdigest(),
                         "instructions": [{"rva": hex(i.address-image.base), "bytes": i.bytes.hex(),
                                           "instruction": f"{i.mnemonic} {i.op_str}"}
                                          for i in image.disasm(start, end)]})
    metadata = []
    for label, rva, length in [("wrap_function_descriptor", 0x4018330, 64),
                               ("wrap_parameter_pointer_array", 0x32760E8, 16),
                               ("wrap_TextWidget_property_descriptor", 0x3276090, 64)]:
        metadata.append({"label": label, "rva": hex(rva),
                         "bytes": image.data[image.off(rva):image.off(rva)+length].hex()})
    report = {"exe_sha256": digest, "access": "READ_ONLY_STATIC_BYTES",
              "image_base": hex(image.base), "addresses": "RVA; instruction operands show original virtual addresses",
              "native_paused_accumulator_writer_identified": False,
              "pause_equivalence_proven": False, "clock_adapter_bound": False,
              "excerpts": excerpts, "metadata": metadata,
              "game_run": False, "installed": False}
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2)
        file.write("\n")
    print(f"STATIC_EXCERPTS_SAVED; PAUSE_CLOCK_UNPROVEN: {output}")


if __name__ == "__main__":
    main()
