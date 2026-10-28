"""Round 017 read-only cmap audit of every face reachable by DISPATCH's player-facing font chains, against the Arabic corpus.
python -X utf8 -I tools/font_017/cmap_chain_017.py <out.json>   (uses extracted/ font copies; fontTools)"""
import json, sys, unicodedata
from pathlib import Path
from fontTools.ttLib import TTFont, TTCollection
ROOT = Path(__file__).resolve().parents[2]; EX = ROOT / 'extracted'
U = 'Dispatch/Content/Shared/UI/Fonts/'; SH = 'Dispatch/Content/Shared/Shifts/Art/'
FACES = {
    'Montserrat-Medium': U + 'Montserrat/static/Montserrat-Medium.ufont', 'Montserrat-MediumItalic': U + 'Montserrat/static/Montserrat-MediumItalic.ufont',
    'Orbitron-Regular': U + 'Orbitron/Orbitron-Regular.ufont', 'Rajdhani-Medium': U + 'Rajdhani/Rajdhani-Medium.ufont',
    'NotoSansCJK-Medium': U + 'NotoSansCJK/NotoSansCJK-Medium.ufont', 'NotoSans-Regular': U + 'NotoSans/NotoSans-Regular.ufont',
    'NotoSansThai-Regular': U + 'NotoSansThai/NotoSansThai-Regular.ufont',
    'Tomorrow-Regular': SH + 'UI/Fonts/Tomorrow/Tomorrow-Regular.ufont', 'Roboto-Regular(game)': SH + 'Fonts/Roboto_Regular/Roboto-Regular.ufont',
    'Aktiv_Grotesk': SH + 'Fonts/Aktiv_Grotesk.ufont',
    'Slate/DroidSansFallback.ttf': 'Engine/Content/Slate/Fonts/DroidSansFallback.ttf', 'Slate/NotoNaskhArabicUI-Regular.ttf': 'Engine/Content/Slate/Fonts/NotoNaskhArabicUI-Regular.ttf',
}
def strings(x):
    if isinstance(x, str): yield x
    elif isinstance(x, dict):
        for v in x.values(): yield from strings(v)
    elif isinstance(x, list):
        for v in x: yield from strings(v)
corpus = set()
for f in sorted((ROOT / 'translation/arabic').glob('*.json')):
    for s in strings(json.load(open(f, encoding='utf-8'))): corpus.update(s)
arabic = sorted(c for c in corpus if 0x0600 <= ord(c) <= 0x06FF or 0xFB50 <= ord(c) <= 0xFEFF)
probe_punct = [c for c in '.,!?:«»"\'()-…' if c in corpus] + ['…']
def cmap(path):
    p = EX / path
    data = p.read_bytes()
    font = TTCollection(str(p)).fonts[0] if data[:4] == b'ttcf' else TTFont(str(p), lazy=True)
    return set(font.getBestCmap() or {})
out = {'corpusArabicCodepoints': ['U+%04X' % ord(c) for c in arabic], 'faces': {}}
for name, path in FACES.items():
    cm = cmap(path)
    out['faces'][name] = {'file': path, 'arabicCorpusCovered': sum(ord(c) in cm for c in arabic), 'arabicCorpusTotal': len(arabic),
                          'missingArabic': ['U+%04X' % ord(c) for c in arabic if ord(c) not in cm][:60],
                          'punctuationCovered': {c: ord(c) in cm for c in probe_punct}}
    print('%-36s Arabic %3d/%d  punct %s' % (name, out['faces'][name]['arabicCorpusCovered'], len(arabic), ''.join(c if ord(c) in cm else '_' for c in probe_punct)))
json.dump(out, open(sys.argv[1], 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
