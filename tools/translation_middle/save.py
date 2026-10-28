import json,sys
from pathlib import Path
t,start=sys.argv[1],int(sys.argv[2])
src=json.loads(Path(f'translation/source/{t}.json').read_text(encoding='utf-8'))
p=Path(f'translation/arabic/{t}.json')
out=json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}
rows=Path('tools/translation_middle/batch.txt').read_text(encoding='utf-8-sig').splitlines()
for i,s in enumerate(rows,start):
    if s=='<KEEP>': s=src[i]['en']
    else: s=s.replace('\\r','\r').replace('\\n','\n')
    out[str(i)]=s
p.parent.mkdir(exist_ok=True,parents=True)
p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(t,start,len(rows),'total',len(out))
