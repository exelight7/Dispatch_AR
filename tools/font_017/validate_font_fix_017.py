"""Round 017 validator for builds/rtl_poc/font_fix_017 (detached; reads only project files and extracted copies).
python -X utf8 -I tools/font_017/validate_font_fix_017.py <scratch_dir> <new_result.json>
Re-dumps every input/output with asset_inspector (binary roundtrip), then checks: English fields preserved, exactly one
appended Arabic sub-typeface, ranges/overlaps, FFontData target exists in the shipped pak and covers the corpus, Latin
untouched, imports resolvable, determinism, minimal byte delta. Negative fixtures must each be detected."""
import copy, difflib, hashlib, json, struct, subprocess, sys
from pathlib import Path
from fontTools.ttLib import TTFont
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'builds/rtl_poc/font_fix_017'; INP = ROOT / 'builds/rtl_poc/font_017_input'
TMP = Path(sys.argv[1]); RESULT = Path(sys.argv[2])
INSPECTOR = ROOT / 'tools/asset_inspector/bin/Release/net8.0/asset_inspector.dll'
NAMES = ['Montserrat-Variable', 'Orbitron-Variable', 'Rajdhani-Variable']
REL = 'Dispatch/Content/Shared/UI/Fonts/'
NASKH = '../../../Engine/Content/Slate/Fonts/NotoNaskhArabicUI-Regular.ttf'
RANGES = [(0x0600, 0x06FF), (0x0750, 0x077F), (0x08A0, 0x08FF), (0xFB50, 0xFDFF), (0xFE70, 0xFEFF)]
PAK0 = set((ROOT / 'reports/pakchunk0-WindowsNoEditor_paths.txt').read_text(encoding='utf-8').split())
ALLPAK = set().union(*[set(p.read_text(encoding='utf-8').split()) for p in (ROOT / 'reports').glob('pakchunk*_paths.txt')])
VOLATILE = {'SerialSize', 'SerialOffset', 'ScriptSerializationStartOffset', 'ScriptSerializationEndOffset'}
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()

def dump(uasset, tag):
    out = TMP / (tag + '.json'); out.unlink(missing_ok=True)
    r = subprocess.run(['dotnet', str(INSPECTOR), str(uasset), str(out)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    meta = json.loads(r.stdout); return json.load(open(out, encoding='utf-8')), meta['binaryRoundtripEqual']
def field(s, n): return next(x for x in s['Value'] if x['Name'] == n)
def bound(r, n): return next(x for x in field(r, n)['Value'] if x['Name'] == 'Value')['Value']
def composite(a): return next(p for p in a['Exports'][0]['Data'] if p['Name'] == 'CompositeFont')
def subs(a): return field(composite(a), 'SubTypefaces')['Value']
def ranges(s): return [(bound(r, 'LowerBound'), bound(r, 'UpperBound')) for r in field(s, 'CharacterRanges')['Value']]
def strip(x):
    if isinstance(x, dict): return {k: strip(v) for k, v in x.items() if k not in VOLATILE}
    if isinstance(x, list): return [strip(v) for v in x]
    return x
def import_ok(a, i):
    if i == 0: return True
    if i > 0: return i <= len(a['Exports'])
    if -i > len(a['Imports']): return False
    imp = a['Imports'][-i - 1]
    if imp['OuterIndex'] == 0:  # package
        n = imp['ObjectName']
        return n.startswith('/Script/') or (n.startswith('/Game/') and 'Dispatch/Content/' + n[6:] + '.uasset' in ALLPAK) or \
            (n.startswith('/Engine/') and 'Engine/Content/' + n[8:] + '.uasset' in ALLPAK)
    return import_ok(a, imp['OuterIndex'])

corpus = json.load(open(ROOT / 'reports/rtl_research/font_017/cmap_chain_017.json', encoding='utf-8'))['corpusArabicCodepoints']
corpus = [int(c[2:], 16) for c in corpus]
naskh_file = ROOT / 'extracted/Engine/Content/Slate/Fonts/NotoNaskhArabicUI-Regular.ttf'
naskh_cmap = set(TTFont(str(naskh_file), lazy=True).getBestCmap())

def check(orig, new, name):
    e = []
    T = lambda ok, why: ok or e.append(why)
    T(new['Imports'] == orig['Imports'], 'imports changed')
    T(new['NameMap'][:len(orig['NameMap'])] == orig['NameMap'], 'name map prefix changed')
    T(len(new['Exports']) == len(orig['Exports']), 'export count changed')
    co, cn = composite(orig), composite(new)
    for k in ('DefaultTypeface', 'FallbackTypeface'):
        T(strip(field(co, k)) == strip(field(cn, k)), 'English %s changed' % k)
    so, sn = subs(orig), subs(new)
    T(len(sn) == len(so) + 1, 'expected exactly one appended sub-typeface')
    T(strip(sn[:len(so)]) == strip(so), 'original sub-typefaces changed')
    rest_o = [p for p in orig['Exports'][0]['Data'] if p['Name'] != 'CompositeFont']
    rest_n = [p for p in new['Exports'][0]['Data'] if p['Name'] != 'CompositeFont']
    T(strip(rest_o) == strip(rest_n), 'other font properties changed')
    if len(sn) != len(so) + 1: return e
    ar = sn[-1]; rg = ranges(ar)
    T(rg == RANGES, 'Arabic ranges differ: %s' % rg)
    other = [r for s in so for r in ranges(s)]
    T(not any(lo <= ohi and olo <= hi for lo, hi in rg for olo, ohi in other), 'Arabic range overlaps an existing sub-font')
    T(not any(lo <= c <= hi for lo, hi in rg for c in range(0x20, 0x250)), 'Arabic range covers Latin/Latin-1/Ext-A/B')
    T(all(any(lo <= c <= hi for lo, hi in rg) for c in corpus), 'corpus Arabic code point outside new ranges')
    T(field(ar, 'Cultures')['Value'] is None, 'Arabic sub-font is culture-restricted')
    fonts = next(x for x in field(ar, 'Typeface')['Value'] if x['Name'] == 'Fonts')['Value']
    T(len(fonts) >= 1, 'empty Arabic typeface')
    for f in fonts:
        fd = field(f, 'Font')['Value'][0]['Value']
        T(fd['bIsCooked'] is True, 'FFontData not cooked')
        if fd['LocalFontFaceAsset'] == 0:
            T(fd['FontFilename'] == NASKH, 'unexpected font filename %r' % fd['FontFilename'])
            T(fd['FontFilename'].replace('../../../', '') in PAK0, 'font file not shipped in pakchunk0: %r' % fd['FontFilename'])
            T(fd['LoadingPolicy'] == 'LazyLoad', 'loading policy %s' % fd['LoadingPolicy'])
        else:
            T(import_ok(new, fd['LocalFontFaceAsset']), 'FontFace import does not resolve to a shipped package')
    def refs(x):
        if isinstance(x, dict):
            if 'LocalFontFaceAsset' in x: yield x['LocalFontFaceAsset']
            for v in x.values(): yield from refs(v)
        elif isinstance(x, list):
            for v in x: yield from refs(v)
    T(all(import_ok(new, i) for i in refs(new['Exports'])), 'dangling/missing FontFace import')
    T(all(import_ok(new, -k - 1) for k in range(len(new['Imports']))), 'import package missing from pak inventory')
    return e

report = {'status': None, 'fonts': {}, 'negativeFixtures': []}
errors = []
for n in NAMES:
    o, rto = dump(INP / (REL + n + '.uasset'), 'in_' + n)
    a, rtn = dump(OUT / (REL + n + '.uasset'), 'out_' + n)
    errs = check(o, a, n)
    if not (rto and rtn): errs.append('binary roundtrip failed')
    det = all((OUT / (REL + n + ext)).read_bytes() == (OUT / 'determinism' / (REL + n + ext)).read_bytes() for ext in ('.uasset', '.uexp'))
    if not det: errs.append('nondeterministic output')
    ob, nb = (INP / (REL + n + '.uexp')).read_bytes(), (OUT / (REL + n + '.uexp')).read_bytes()
    ops = [o for o in difflib.SequenceMatcher(None, ob, nb, autojunk=False).get_opcodes() if o[0] != 'equal']
    inserts = [o for o in ops if o[0] == 'insert']; edits = [o for o in ops if o[0] != 'insert']
    # Every non-insert edit must sit inside an int32 that grew by exactly the inserted size or by one array element.
    grown = []
    for _, i1, i2, j1, j2 in edits:
        for start in range(max(0, i1 - 3), i1 + 1):
            if start + 4 >= i2 and start + 4 <= len(ob):
                a_, b_ = struct.unpack_from('<i', ob, start)[0], struct.unpack_from('<i', nb, start - i1 + j1)[0]
                if b_ - a_ in (len(nb) - len(ob), 1): grown.append((start, a_, b_)); break
    if len(inserts) != 1 or sum(o[4] - o[3] for o in inserts) != len(nb) - len(ob) or len(grown) != len(edits):
        errs.append('uexp delta is not one insertion plus size/count fields: %s' % ops[:8])
    report['fonts'][n] = {'errors': errs, 'binaryRoundtrip': rto and rtn, 'deterministic': det,
                          'inputSha256': {'uasset': sha(INP / (REL + n + '.uasset')), 'uexp': sha(INP / (REL + n + '.uexp'))},
                          'outputSha256': {'uasset': sha(OUT / (REL + n + '.uasset')), 'uexp': sha(OUT / (REL + n + '.uexp'))},
                          'uexpBytes': [len(ob), len(nb)], 'insertedBytes': len(nb) - len(ob), 'insertions': len(inserts),
                          'sizeFieldEdits': [{'uexpOffset': g[0], 'old': g[1], 'new': g[2]} for g in grown],
                          'subTypefaces': [len(subs(o)), len(subs(a))], 'arabicRanges': ['U+%04X-U+%04X' % r for r in ranges(subs(a)[-1])]}
    errors += [n + ': ' + x for x in errs]
    if n == NAMES[0]:
        base_o, base_a = o, a
report['arabicFace'] = {'file': NASKH, 'shippedIn': 'pakchunk0', 'extractedSha256': sha(naskh_file),
                        'corpusArabicCovered': sum(c in naskh_cmap for c in corpus), 'corpusArabicTotal': len(corpus)}
if report['arabicFace']['corpusArabicCovered'] != len(corpus): errors.append('Naskh does not cover the corpus')
def neg(label, mutate, expect):
    bad = copy.deepcopy(base_a); mutate(bad); errs = check(base_o, bad, 'neg')
    ok = any(expect in x for x in errs); report['negativeFixtures'].append({'fixture': label, 'detected': ok, 'diagnostics': errs[:3]})
    if not ok: errors.append('negative not detected: ' + label)
neg('English default typeface changed', lambda a: field(composite(a), 'DefaultTypeface')['Value'][0]['Value'][0]['Value'].__setitem__(0, field(composite(a), 'DefaultTypeface')['Value'][0]['Value'][1]['Value'][0]), 'English DefaultTypeface changed')
neg('range covers Latin', lambda a: next(x for x in field(subs(a)[-1], 'CharacterRanges')['Value'][0]['Value'] if x['Name'] == 'LowerBound')['Value'][1].__setitem__('Value', 0x41), 'Latin')
neg('font file not shipped', lambda a: next(x for x in field(subs(a)[-1], 'Typeface')['Value'] if x['Name'] == 'Fonts')['Value'][0]['Value'][1]['Value'][0]['Value'].__setitem__('FontFilename', '../../../Engine/Content/Slate/Fonts/Missing.ttf'), 'not shipped')
neg('dangling FontFace import', lambda a: next(x for x in field(subs(a)[-1], 'Typeface')['Value'] if x['Name'] == 'Fonts')['Value'][0]['Value'][1]['Value'][0]['Value'].__setitem__('LocalFontFaceAsset', -9999), 'import')
neg('original sub-font removed', lambda a: subs(a).pop(0), 'exactly one appended')
report['errors'] = errors
report['status'] = 'FONT_FIX_017_STATIC_PASS' if not errors else 'FONT_FIX_017_STATIC_FAIL'
report.update({'installed': False, 'tested_in_game': 0, 'final': 0, 'ARABIC_GLYPH_RENDERING_PROVEN': False})
RESULT.write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding='utf-8')
print(report['status'], 'errors', len(errors))
for n, f in report['fonts'].items(): print(' ', n, f['subTypefaces'], 'roundtrip', f['binaryRoundtrip'], 'det', f['deterministic'], 'uexp', f['uexpBytes'], '+%d' % f['insertedBytes'], 'insertions', f['insertions'], 'size edits', [(g['old'], g['new']) for g in f['sizeFieldEdits']])
for x in report['negativeFixtures']: print('  negative', x['fixture'], x['detected'])
for x in errors: print('  ERR', x)
