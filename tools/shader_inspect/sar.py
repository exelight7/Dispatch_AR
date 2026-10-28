import struct,sys
def load(path):
    b=open(path,'rb').read()
    o=0
    def u32():
        nonlocal o; v=struct.unpack_from('<I',b,o)[0]; o+=4; return v
    ver=u32()
    n=u32(); smh=[b[o+20*i:o+20*i+20] for i in range(n)]; o+=20*n
    n=u32(); sh=[b[o+20*i:o+20*i+20] for i in range(n)]; o+=20*n
    n=u32(); sme=[]
    for i in range(n): sme.append(struct.unpack_from('<IIII',b,o)); o+=16
    n=u32(); se=[]
    for i in range(n): se.append(struct.unpack_from('<QIIB',b,o)); o+=17
    n=u32(); pe=[]
    for i in range(n): pe.append(struct.unpack_from('<qq',b,o)); o+=16
    n=u32(); idx=list(struct.unpack_from('<%dI'%n,b,o)); o+=4*n
    return dict(ver=ver,smh=smh,sh=sh,sme=sme,se=se,pe=pe,idx=idx,body=o,b=b)
if __name__=='__main__':
    a=load(sys.argv[1])
    print('ver',a['ver'],'maps',len(a['smh']),'shaders',len(a['sh']),'entries',len(a['se']),'body@',a['body'],'size',len(a['b']))
    comp=sum(1 for e in a['se'] if e[1]!=e[2]); print('compressed',comp)
    from collections import Counter; print('freq',Counter(e[3] for e in a['se']))
    print(a['se'][:3])
