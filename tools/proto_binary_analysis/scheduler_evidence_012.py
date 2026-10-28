"""Read-only, build-locked excerpts for round 012 (paused-accumulator producer and stock clock routes).

Never runs the game and never reads the local AES key. Writes one NEW evidence file and refuses overwrite.
Labels are analyst names for behaviour; engine names are given only where the binary itself proves them
(an assert string, reflection data, or a match with the base-class vtable and its dispatcher).
"""
import hashlib
import json
import struct
import sys
from pathlib import Path

from pe import Image

ROOT = Path(__file__).resolve().parents[2]
EXPECTED = "365637a77d4b74a61d198a9927e3dcd437bf3be2247b96fcbe5c2e851ac14923"
SPANS = [
    ("block_ctor_tickable_base_and_fields", 0x99BBC0, 0x99BDC1),
    ("tickable_ctor_FTickableGameObject", 0x2730130, 0x27301A6),
    ("proto_Tick_accumulator_producer", 0x9A5B30, 0x9A5B6B),
    ("proto_IsTickable_and_IsTickableWhenPaused", 0x9A2BB0, 0x9A2BC2),
    ("proto_BeginDestroy_clears_tick_gate", 0x99CB10, 0x99CB1C),
    ("UObject_BeginDestroy_assert_path", 0x10FE5A0, 0x10FE5F6),
    ("TickObjects_entry_loop", 0x27424C0, 0x2742547),
    ("UWorld_Tick_time_update", 0x242BDC7, 0x242BE4F),
    ("UWorld_Tick_timer_then_tickables", 0x242C48A, 0x242C4CA),
    ("engine_loop_null_world_tickables", 0x2342A77, 0x2342A8D),
    ("process_reveal_budget", 0x9A3900, 0x9A3EB2),
    ("print_letter_by_letter", 0x9A3EC0, 0x9A4261),
    ("select_print_delay", 0x9A0880, 0x9A09C8),
    ("anim_time_override_getter", 0x9A0850, 0x9A0865),
    ("normal_finish", 0x9A07B0, 0x9A0848),
    ("show_text", 0x9A5710, 0x9A5771),
    ("stop_early", 0x9A5A30, 0x9A5AD4),
    ("proto_timer_callback", 0x798610, 0x798619),
    ("timer_manager_tick_once_per_frame_guard", 0x2741850, 0x2741888),
    ("GameplayStatics_GetTimeSeconds", 0x235EC10, 0x235EC3B),
    ("GameplayStatics_GetUnpausedTimeSeconds", 0x235EC70, 0x235EC9B),
    ("GameplayStatics_GetRealTimeSeconds", 0x235D9F0, 0x235DA1B),
    ("GameplayStatics_GetWorldDeltaSeconds", 0x235EE60, 0x235EE8B),
    ("K2_SetTimer_bind_by_name", 0x24047C0, 0x24048B9),
    ("K2_SetTimerDelegate_same_timer_manager", 0x2404AA1, 0x2404B1B),
    ("UUserWidget_NativeTick_no_pause_gate", 0x1EBC940, 0x1EBCA15),
    ("bHasScriptImplementedTick_setter", 0x1F18870, 0x1F18878),
    ("DelayUntilNextTick_latent_action", 0xCA52F0, 0xCA53B4),
]
VTABLES = [("proto_tickable_vtable", 0x31CAC38, 9), ("FTickableGameObject_base_vtable", 0x389AC78, 9)]
BLOCK_VTABLE = 0x31CA898
BLOCK_SLOTS = [0x80, 0x88, 0x308, 0x320, 0x350, 0x358, 0x360, 0x368, 0x370, 0x388, 0x390]
PROPERTY_NAMES = {0x31CCBB0: "AnimateWhilePaused", 0x31CCC10: "EndHoldTime", 0x31CCC70: "OnBeginLetterByLetterPrint",
                  0x31CCC90: "OnPrintLetter", 0x31CCCA0: "OnFinishLetterByLetterPrint",
                  0x31CCCC0: "OnPauseLetterByLetterPrint", 0x31CCCE0: "OnResumeLetterByLetterPrint",
                  0x31CCD00: "OnNewBlockLetterByLetterPrint"}


def main():
    output = ROOT / (sys.argv[1] if len(sys.argv) > 1 else
                     "reports/rtl_research/renderer_repair/scheduler_012/native_evidence_012.json")
    if output.exists():
        raise FileExistsError("Refusing to overwrite existing evidence")
    image = Image()
    digest = hashlib.sha256(image.data).hexdigest()
    assert digest == EXPECTED, "Unsupported executable build"
    q = lambda rva: struct.unpack_from("<Q", image.data, image.off(rva))[0]
    excerpts = []
    for label, start, end in SPANS:
        code = image.data[image.off(start):image.off(start) + end - start]
        excerpts.append({"label": label, "start_rva": hex(start), "end_rva_exclusive": hex(end),
                         "sha256": hashlib.sha256(code).hexdigest(),
                         "instructions": [{"rva": hex(i.address - image.base), "bytes": i.bytes.hex(),
                                           "instruction": f"{i.mnemonic} {i.op_str}"}
                                          for i in image.disasm(start, end)]})
    vtables = [{"label": label, "rva": hex(rva),
                "slots": [hex(q(rva + 8 * k) - image.base) for k in range(n)]} for label, rva, n in VTABLES]
    vtables.append({"label": "proto_block_primary_vtable", "rva": hex(BLOCK_VTABLE),
                    "slots": {hex(o): hex(q(BLOCK_VTABLE + o) - image.base) for o in BLOCK_SLOTS}})
    properties = []
    for name_rva, name in PROPERTY_NAMES.items():
        for desc in image.ptr_refs(name_rva):
            properties.append({"name": name, "descriptor_rva": hex(desc),
                               "offset_or_flag": hex(struct.unpack_from("<I", image.data, image.off(desc) + 0x24)[0])})
    report = {"exe_sha256": digest, "access": "READ_ONLY_STATIC_BYTES", "image_base": hex(image.base),
              "addresses": "RVA; instruction operands show original virtual addresses",
              "constants": {"set_timer_first_delay_0x31221a8":
                            struct.unpack_from("<f", image.data, image.off(0x31221A8))[0]},
              "paused_accumulator_writer_identified": True, "game_run": False, "installed": False,
              "excerpts": excerpts, "vtables": vtables, "reflected_properties": properties}
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2)
        file.write("\n")
    print(f"STATIC_EXCERPTS_SAVED: {output}")


if __name__ == "__main__":
    main()
