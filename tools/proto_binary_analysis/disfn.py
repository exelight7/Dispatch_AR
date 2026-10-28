"""Disassemble one function (by any RVA inside it). Read-only. Usage: python disfn.py <rva hex> [max_insns]"""
import sys
from pe import Image

img = Image()


def show(rva, limit=400):
    f = img.func(rva) or (rva, rva + 0x200)
    print(f"; func {f[0]:#x}-{f[1]:#x} size {f[1]-f[0]:#x}")
    for ins in img.disasm(*f)[:limit]:
        r = ins.address - img.base
        note = ""
        if ins.mnemonic in ("call", "jmp") and ins.op_str.startswith("0x"):
            t = int(ins.op_str, 16) - img.base
            ft = img.func(t)
            note = f"  -> {t:#x}" + (f" (fn {ft[0]:#x} sz {ft[1]-ft[0]:#x})" if ft else "")
        elif "rip +" in ins.op_str or "rip -" in ins.op_str:
            t = ins.address + ins.size + ins.disp - img.base if hasattr(ins, "disp") else None
            for op in ins.operands:
                if op.type == 3 and op.mem.base == capstone_rip:
                    t = ins.address + ins.size + op.mem.disp - img.base
                    s = ""
                    try:
                        s = img.cstr(t, 60)
                    except Exception:
                        pass
                    note = f"  ; [{t:#x}] {s!r}" if s and s.isprintable() and len(s) > 2 else f"  ; [{t:#x}]"
        print(f"{r:#09x}  {ins.mnemonic:6} {ins.op_str}{note}")


import capstone.x86 as X
capstone_rip = X.X86_REG_RIP
if __name__ == "__main__":
    show(int(sys.argv[1], 16), int(sys.argv[2]) if len(sys.argv) > 2 else 400)
