# read-only minidump parse: exception record, thread ctx regs, modules, stack bytes
import struct,sys
d=open(sys.argv[1],'rb').read()
n,=struct.unpack_from('<I',d,8); rva,=struct.unpack_from('<I',d,12)
S={}
for i in range(n):
    t,sz,r=struct.unpack_from('<III',d,rva+12*i); S[t]=(sz,r)
print('streams',sorted(S))
sz,r=S[6]; tid,=struct.unpack_from('<I',d,r)
code,fl,rec,addr,nparam=struct.unpack_from('<IIQQI',d,r+8)
params=struct.unpack_from('<15Q',d,r+32)
print('exc tid',tid,'code %#x'%code,'addr %#x'%addr,'params',[hex(p) for p in params[:nparam]])
csz,crva=struct.unpack_from('<II',d,r+8+4+4+8+8+4+4+15*8)
c=d[crva:crva+csz]
names=['P1','P2','P3','P4','P5','P6']
off=0x78
rn=['Rax','Rcx','Rdx','Rbx','Rsp','Rbp','Rsi','Rdi']+['R%d'%i for i in range(8,16)]+['Rip']
vals=struct.unpack_from('<17Q',c,0x78)
for k,v in zip(rn,vals): print(k,'%#x'%v)
# modules
sz,r=S[4]; cnt,=struct.unpack_from('<I',d,r)
for i in range(cnt):
    b,sz2,cs,ts,nr=struct.unpack_from('<QIIII',d,r+4+108*i)
    l,=struct.unpack_from('<I',d,nr); nm=d[nr+4:nr+4+l].decode('utf-16le')
    if 'Dispatch' in nm or 'ntdll' in nm: print('mod %#x size %#x ts %#x %s'%(b,sz2,ts,nm))

# --- memory ranges (MemoryListStream=5, Memory64=9)
def mem():
    out=[]
    if 5 in S:
        sz,r=S[5]; k,=struct.unpack_from('<I',d,r)
        for i in range(k):
            st,ds,rv=struct.unpack_from('<QII',d,r+4+16*i); out.append((st,ds,rv))
    if 9 in S:
        sz,r=S[9]; k,base=struct.unpack_from('<QQ',d,r); o=base
        for i in range(k):
            st,ds=struct.unpack_from('<QQ',d,r+16+16*i); out.append((st,ds,o)); o+=ds
    return out
M=mem()
def rd(a,n):
    for st,ds,rv in M:
        if st<=a and a+n<=st+ds: return d[rv+a-st:rv+a-st+n]
if len(sys.argv)>2:
    base=0x7ff795a50000
    print('ranges',[(hex(s),hex(z)) for s,z,_ in M][:20])
    f=int(sys.argv[2],16); b=rd(f,0x60)
    if b:
        q=struct.unpack('<12Q',b); print('FFrame@%#x'%f,[hex(x) for x in q])
        print(' Node=%#x Object=%#x Code=%#x Locals=%#x'%(q[2],q[3],q[4],q[5]))
    # stack words that look like exe return addrs
    sp=vals[4]; w=rd(sp,0x700)
    print('stack scan:')
    for i in range(0,len(w),8):
        v,=struct.unpack_from('<Q',w,i)
        if base<=v<base+0x4913000: print('  rsp+%#x  RVA %#x'%(i,v-base))
