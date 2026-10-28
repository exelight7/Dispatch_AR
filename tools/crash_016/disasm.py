import pefile,capstone,sys
exe=r'D:\SteamLibrary\steamapps\common\Dispatch\Dispatch\Binaries\Win64\Dispatch-Win64-Shipping.exe'
pe=pefile.PE(exe,fast_load=True); print('exe ts %#x'%pe.FILE_HEADER.TimeDateStamp,'imagebase %#x'%pe.OPTIONAL_HEADER.ImageBase)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64); 
def dis(rva,before,after):
    off=pe.get_offset_from_rva(rva-before); data=pe.__data__[off:off+before+after]
    for i in md.disasm(data,rva-before): print('%#x  %-8s %s%s'%(i.address,i.mnemonic,i.op_str,'   <== FAULT' if i.address==rva else ''))
for a in sys.argv[1:]:
    r=int(a,16); print('---',a); dis(r,0x60,0x30)
