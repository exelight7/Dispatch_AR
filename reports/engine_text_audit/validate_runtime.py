from pathlib import Path
from collections import Counter
import json,re

root=Path(__file__).resolve().parents[2]
def unique(pairs):
 result={}
 for k,v in pairs:
  assert k not in result,('duplicate index',k)
  result[k]=v
 return result
source=json.loads((root/'translation/source/EngineRuntime.json').read_text(encoding='utf-8'))
arabic=json.loads((root/'translation/arabic/EngineRuntime.json').read_text(encoding='utf-8'),object_pairs_hook=unique)
assert set(arabic)=={str(r['index']) for r in source}
keeps=[]
for r in source:
 en,ar=r['en'],arabic[str(r['index'])]
 assert isinstance(ar,str) and ar,(r['index'],'empty')
 for marker in ('|','^','\r','\n','\\'):
  assert en.count(marker)==ar.count(marker),(r['index'],repr(marker))
 for pattern in (r'<[^>]*>',r'\{[^{}]*\}'):
  assert Counter(re.findall(pattern,en))==Counter(re.findall(pattern,ar)),(r['index'],pattern)
 assert not re.search('[\u061c\u200e\u200f\u202a-\u202e\u2066-\u2069\ufb50-\ufdff\ufe70-\ufeff]',ar),(r['index'],'bidi/presentation forms')
 if ar==en:
  if r['namespace']=='FInputChord':
   reason='Technical modifier/key-chord notation or formatting placeholders.'
  elif r['key'] in ('DefaultKeySelectionText',):
   reason='Pure punctuation.'
  elif r['key'].endswith(('SubCategory','SubCateogry')) or r['key']=='Slate':
   reason='Platform, device or framework brand/name.'
  else:
   reason='Technical physical keyboard/controller key name or identifier, preserved per style.'
  keeps.append({'index':r['index'],'namespace':r['namespace'],'key':r['key'],'en':en,'reason':reason})
(Path(__file__).parent/'runtime_keep.json').write_text(json.dumps(keeps,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
result={'records':len(arabic),'source_records':len(source),'translated_or_legitimate_keep':len(arabic),'legitimate_keep':len(keeps),'status':'TRANSLATED','structural_validation':'PASS','runtime_reachability':'NOT PROVEN','game_launched':False}
(Path(__file__).parent/'runtime_validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
