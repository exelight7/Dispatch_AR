import collections,json,re
from pathlib import Path

def unique_pairs(pairs):
    d={}
    for k,v in pairs:
        assert k not in d, f'duplicate JSON key {k}'
        d[k]=v
    return d

total=0
for target in ('104','105','106'):
    source=json.loads(Path(f'translation/source/{target}.json').read_text(encoding='utf-8'))
    dest=json.loads(Path(f'translation/arabic/{target}.json').read_text(encoding='utf-8'),object_pairs_hook=unique_pairs)
    assert set(dest)=={str(row['index']) for row in source}, target
    for row in source:
        original,translated=row['en'],dest[str(row['index'])]
        assert isinstance(translated,str) and translated, (target,row['index'],'empty/non-string')
        for marker in ('^','|','\r','\n'):
            assert original.count(marker)==translated.count(marker), (target,row['index'],repr(marker))
        for pattern in (r'<[^>]*>',r'\{[^{}]*\}'):
            assert collections.Counter(re.findall(pattern,original))==collections.Counter(re.findall(pattern,translated)), (target,row['index'],pattern)
        assert not re.search('[\u202a-\u202e\u2066-\u2069\ufb50-\ufdff\ufe70-\ufeff]',translated), (target,row['index'],'bidi or presentation forms')
    unchanged=[row['index'] for row in source if dest[str(row['index'])]==row['en']]
    print(f'{target}: {len(dest)}/{len(source)}; unchanged legitimate KEEP={len(unchanged)}; structural checks pass')
    total+=len(dest)
print(f'TOTAL {total}; status TRANSLATED only')
