"""Linear disassembly from an RVA for N instructions (ignores .pdata chunking). Read-only.
Usage: python lin.py <rva hex> [n]"""
import sys
import capstone.x86 as X
from pe import Image

img = Image()


def lin(rva, n=80):
    code = img.data[img.off(rva):img.off(rva) + n * 15]
    for k, ins in enumerate(img.cs.disasm(code, img.base + rva)):
        if k >= n:
            break
        note = ""
        if ins.mnemonic in ("call", "jmp") or ins.mnemonic.startswith("j"):
            if ins.op_str.startswith("0x"):
                note = f"  -> {int(ins.op_str, 16) - img.base:#x}"
        for op in ins.operands:
            if op.type == X.X86_OP_MEM and op.mem.base == X.X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp - img.base
                s = ""
                try:
                    s = img.cstr(t, 60)
                except Exception:
                    pass
                note = f"  ; [{t:#x}]" + (f" {s!r}" if s.isprintable() and len(s) > 3 else "")
        print(f"{ins.address - img.base:#09x}  {ins.mnemonic:7} {ins.op_str}{note}")
        if ins.mnemonic == "int3":
            break


if __name__ == "__main__":
    lin(int(sys.argv[1], 16), int(sys.argv[2]) if len(sys.argv) > 2 else 80)
