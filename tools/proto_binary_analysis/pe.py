"""Read-only static helpers for Dispatch-Win64-Shipping.exe (opens the file 'rb' only; never writes or runs it).

Addresses are RVAs (image base 0x140000000 is only used to decode absolute pointers).
Usage as a library: from pe import Image; img = Image()
"""
import bisect
import struct
from pathlib import Path

import capstone
import numpy as np
import pefile

EXE = Path(r"D:\SteamLibrary\steamapps\common\Dispatch\Dispatch\Binaries\Win64\Dispatch-Win64-Shipping.exe")


class Image:
    def __init__(self, path=EXE):
        self.data = Path(path).read_bytes()
        self.pe = pefile.PE(data=self.data, fast_load=True)
        self.base = self.pe.OPTIONAL_HEADER.ImageBase
        self.secs = {s.Name.rstrip(b"\0").decode(): s for s in self.pe.sections}
        p = self.secs[".pdata"]
        raw = np.frombuffer(self.data, dtype="<u4", count=p.Misc_VirtualSize // 4, offset=p.PointerToRawData)
        rf = raw[: len(raw) // 3 * 3].reshape(-1, 3)
        rf = rf[rf[:, 0] != 0]
        self.fstart, self.fend = rf[:, 0].tolist(), rf[:, 1].tolist()
        self.cs = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
        self.cs.detail = True

    def off(self, rva):
        return self.pe.get_offset_from_rva(rva)

    def rva(self, off):
        return self.pe.get_rva_from_offset(off)

    def sec_bytes(self, name):
        s = self.secs[name]
        return s.VirtualAddress, self.data[s.PointerToRawData:s.PointerToRawData + s.SizeOfRawData]

    def find(self, needle, wide=False):
        if isinstance(needle, str):
            needle = needle.encode("utf-16-le" if wide else "ascii")
        out, i = [], self.data.find(needle)
        while i >= 0:
            out.append(self.rva(i))
            i = self.data.find(needle, i + 1)
        return out

    def cstr(self, rva, n=200):
        b = self.data[self.off(rva):self.off(rva) + n]
        return b.split(b"\0")[0].decode("latin1")

    def ptr_refs(self, target_rva, sections=(".rdata", ".data")):
        """RVAs of 8-byte absolute pointers equal to target."""
        va = struct.pack("<Q", self.base + target_rva)
        out = []
        for name in sections:
            s0, b = self.sec_bytes(name)
            i = b.find(va)
            while i >= 0:
                if i % 8 == 0:
                    out.append(s0 + i)
                i = b.find(va, i + 1)
        return out

    def rip_refs(self, targets):
        """Code RVAs whose rip-relative disp32 (ending the instruction) resolves to any target.
        ponytail: assumes disp32 is the last operand bytes; misses forms with an imm after the disp."""
        s0, b = self.sec_bytes(".text")
        arr = np.frombuffer(b, dtype=np.uint8)
        hits = {}
        for t in targets:
            hits[t] = []
        tset = np.array(sorted(targets), dtype=np.int64)
        for k in range(4):
            n = (len(arr) - k) // 4
            d = np.frombuffer(b, dtype="<i4", count=n, offset=k).astype(np.int64)
            pos = s0 + k + 4 * np.arange(n, dtype=np.int64)
            dest = pos + 4 + d
            m = np.isin(dest, tset)
            for p, t in zip(pos[m], dest[m]):
                hits[int(t)].append(int(p))
        return hits

    def func(self, rva):
        i = bisect.bisect_right(self.fstart, rva) - 1
        if i >= 0 and self.fstart[i] <= rva < self.fend[i]:
            return self.fstart[i], self.fend[i]
        return None

    def disasm(self, start, end):
        return list(self.cs.disasm(self.data[self.off(start):self.off(start) + (end - start)], self.base + start))
