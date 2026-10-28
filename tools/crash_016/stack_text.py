import sys,io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
dmp=sys.argv[1]; sys.argv=['x',dmp,'3ea1b7d570']
src=open('dump_read.py').read()
exec(src)
print('=== utf16 view')
for a in range(0x3ea1b7d2b0,0x3ea1b7d700,0x20):
    b=rd(a,0x20)
    if not b: print(hex(a),'N/A'); continue
    t=b.decode('utf-16le',errors='replace')
    print(hex(a), b[:12].hex(), ascii(t) if False else ''.join(c if c.isprintable() else '.' for c in t))
