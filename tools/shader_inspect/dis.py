import ctypes,struct,sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import sar,lz4.block as L
d3d=ctypes.WinDLL('d3dcompiler_47.dll')
class Blob(ctypes.Structure): pass
def disasm(dx):
    p=ctypes.c_void_p()
    hr=d3d.D3DDisassemble(dx,len(dx),0,None,ctypes.byref(p))
    if hr!=0: return None
    vt=ctypes.cast(ctypes.cast(p,ctypes.POINTER(ctypes.c_void_p))[0],ctypes.POINTER(ctypes.c_void_p))
    GetPtr=ctypes.WINFUNCTYPE(ctypes.c_void_p,ctypes.c_void_p)(vt[3])
    GetSize=ctypes.WINFUNCTYPE(ctypes.c_size_t,ctypes.c_void_p)(vt[4])
    s=ctypes.string_at(GetPtr(p),GetSize(p)).decode('latin1')
    ctypes.WINFUNCTYPE(ctypes.c_ulong,ctypes.c_void_p)(vt[2])(p)
    return s
def shader(a,j):
    o,s,u,f=a['se'][j]; r=a['b'][a['body']+o:a['body']+o+s]
    c=r if s==u else L.decompress(r,uncompressed_size=u)
    k=c.find(b'DXBC'); n=struct.unpack_from('<I',c,k+24)[0]
    return f,c[k:k+n],c
if __name__=='__main__':
    a=sar.load(sys.argv[1]); m=int(sys.argv[2]); out=sys.argv[3]; os.makedirs(out,exist_ok=True)
    e=a['sme'][m]
    for n,j in enumerate(a['idx'][e[0]:e[0]+e[1]]):
        f,dx,c=shader(a,j); t=disasm(dx)
        open(os.path.join(out,'%02d_%s_%d.asm'%(n,'VS' if f==0 else 'PS' if f==3 else 'F%d'%f,j)),'w').write(t or 'FAIL')
        print(n,f,len(dx),'ok' if t else 'fail')
