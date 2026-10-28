import json,sys
from pathlib import Path
root=Path(__file__).resolve().parents[2]
src=json.loads((root/'translation/source/EngineRuntime.json').read_text(encoding='utf-8'))
p=root/'translation/arabic/EngineRuntime.json'
out=json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}
rows=(Path(__file__).parent/'runtime_batch.txt').read_text(encoding='utf-8-sig').splitlines()
for i,s in enumerate(rows,int(sys.argv[1])):
 s=src[i]['en'] if s=='<KEEP>' else s.replace('\\r','\r').replace('\\n','\n')
 for marker in ('|','^','\r','\n'):
  assert src[i]['en'].count(marker)==s.count(marker),(i,marker)
 out[str(i)]=s
p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(len(rows),'saved; total',len(out))
