import pefile,capstone,sys
exe=r'D:\SteamLibrary\steamapps\common\Dispatch\Dispatch\Binaries\Win64\Dispatch-Win64-Shipping.exe'
pe=pefile.PE(exe,fast_load=True); md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64); md.detail=False
def start(rva):
    # walk back to a 0xCC/ret padding boundary
    off=pe.get_offset_from_rva(rva); b=pe.__data__
    i=off
    while i>off-0x1200 and not (b[i-1]==0xCC and b[i]!=0xCC): i-=1
    return rva-(off-i)
for a in sys.argv[1:]:
    r=int(a,16); s=start(r); print('=== ret %#x  fn start ~%#x (size back %#x)'%(r,s,r-s))
    off=pe.get_offset_from_rva(s); n=0
    for ins in md.disasm(pe.__data__[off:off+0x120],s):
        if ins.address>r+0x20 and n>6: break
        mark='  <== RET' if ins.address==r else ''
        print('  %#x %-6s %s%s'%(ins.address,ins.mnemonic,ins.op_str,mark)); n+=1
