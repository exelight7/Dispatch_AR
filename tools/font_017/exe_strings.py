"""Read-only: find UTF-16 string literals in the shipped EXE and their RIP-relative code references.
python -I tools/font_017/exe_strings.py <out.json>"""
import json, sys
import numpy as np, pefile, capstone
EXE = r'D:\SteamLibrary\steamapps\common\Dispatch\Dispatch\Binaries\Win64\Dispatch-Win64-Shipping.exe'
WANT = ["FallbackFont", "DroidSansFallback", "Slate/Fonts/", "SlateDebug/Fonts/LastResort.ttf", "LastResort",
        "NotoNaskhArabicUI-Regular.ttf", "FF_LocalizedFallback", "FF_LastResortFallback", "Could not find Glyph Index"]
pe = pefile.PE(EXE, fast_load=True)
data = pe.__data__
text = next(s for s in pe.sections if s.Name.startswith(b'.text'))
t0, tsz = text.VirtualAddress, text.Misc_VirtualSize
tbytes = np.frombuffer(data[text.PointerToRawData:text.PointerToRawData + tsz], dtype=np.uint8)
rel = np.lib.stride_tricks.sliding_window_view(tbytes, 4).copy().view('<i4').ravel() if False else None
# rel32 at every byte offset i: int32 little endian of tbytes[i:i+4]
b = tbytes.astype(np.int64)
r32 = (b[:-3] | (b[1:-2] << 8) | (b[2:-1] << 16) | (b[3:] << 24))
r32 = np.where(r32 >= 2**31, r32 - 2**32, r32)
end_rva = t0 + np.arange(len(r32)) + 4
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
out = {}
for w in WANT:
    hits = []
    for enc, tag in ((w.encode('utf-16-le') + b'\0\0', 'utf16'), (w.encode() + b'\0', 'ascii')):
        start = 0
        while True:
            off = data.find(enc, start)
            if off < 0: break
            start = off + 1
            rva = pe.get_rva_from_offset(off)
            if rva is None: continue
            refs = []
            for i in np.nonzero(end_rva + r32 == rva)[0][:8]:
                # confirm with capstone: an instruction ending at i+4 (or i+4+imm) referencing rva
                for back in range(3, 8):
                    ins = next(md.disasm(data[text.PointerToRawData + i - back + 4 - 4:][:16], t0 + i - back), None)
                    if ins and ins.address + ins.size >= t0 + i + 4 and hex(rva) in ins.op_str:
                        refs.append({'insn_rva': hex(ins.address), 'insn': f'{ins.mnemonic} {ins.op_str}'}); break
            hits.append({'enc': tag, 'rva': hex(rva), 'code_refs': refs})
    out[w] = hits
json.dump(out, open(sys.argv[1], 'w'), indent=1)
for k, v in out.items():
    print(k, [(h['enc'], h['rva'], len(h['code_refs']), [r['insn_rva'] for r in h['code_refs']]) for h in v])
