"""Round 021: staging-only Dispatch_AR_R8b_P.pak = round-019 repaired WBP (unchanged) + round-021 DT_AR tables (RowStruct
/Script/UMG.RichTextStyleRow). Never installs anything. Same workflow as round 019: repak 0.2.3, V11, mount ../../../, seed 0,
uncompressed, RAYON_NUM_THREADS=1, built twice, both unpacked and hash-compared with the sources.
python -X utf8 -I tools/r8b_021/build_r8b_pak_021.py
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
WBP_SRC = ROOT / 'builds/rtl_poc/r8b_repair_019/WBP_SubtitleBlock_AR_R8B_REPAIR_019'
TABLE_SRC = ROOT / 'builds/rtl_poc/r8b_stylefix_021'
STAGE = ROOT / 'builds/rtl_poc/r8b_runtime_staging_021'
PAK_019 = ROOT / 'builds/rtl_poc/r8b_runtime_staging_019/Dispatch_AR_R8b_P.pak'
FONT_PAK = ROOT / 'builds/rtl_poc/font_runtime_018/Dispatch_AR_Fonts_P.pak'
REPAK = ROOT / 'tools/repak-v0.2.3/repak.exe'
WBP = 'Dispatch/Content/Shared/Core/Widgets/WBP_SubtitleBlock'
TABLES = ['DT_AR_Fill', 'DT_AR_Fill_Large', 'DT_AR_Outline', 'DT_AR_Outline_Large']
WBP_019 = {'.uasset': 'e4189ec226170f487ed232ebc0a4659fa559d91738a2aea6d59f892cd02b6f52', '.uexp': '9ab47d953df90f163689203abb356ccd81ce2828c7a4898ea762f49b4e24b0b4'}
PAK_019_SHA = '1058eac436c2844f44b0ca60d625dfad832296214aea9dca676d401279f1f988'


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def members(d): return {p.relative_to(d).as_posix(): sha(p) for p in sorted(d.rglob('*')) if p.is_file()}
def save(name, data): (STAGE / name).write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')


def run(args, log, env=None):
    r = subprocess.run([str(x) for x in args], capture_output=True, text=True, encoding='utf-8', env=env)
    (STAGE / 'work' / log).write_text(r.stdout + r.stderr, encoding='utf-8')
    assert r.returncode == 0, f'{log}: exit {r.returncode}'
    return r.stdout


def main():
    assert not STAGE.exists(), 'refusing existing staging directory'
    report = json.loads((TABLE_SRC / 'validation.json').read_text(encoding='utf-8'))
    assert report['status'] == 'R8B_STYLEFIX_021_GENERATED' and report['validator_errors'] == 0 and report['RichTextStyleGate'] == 'PASS'
    assert report['row_struct'] == '/Script/UMG.RichTextStyleRow' and report['textstyle_equal_rows'] == report['textstyle_rows_compared'] == 152
    assert json.loads((TABLE_SRC / 'textstyle_bytes_021.json').read_text(encoding='utf-8'))['status'] == 'TEXTSTYLE_BYTES_IDENTICAL'
    sources = {WBP + ext: WBP_SRC.with_suffix(ext) for ext in ('.uasset', '.uexp')}
    assert all(sha(sources[WBP + ext]) == h for ext, h in WBP_019.items()), 'round-019 WBP changed'
    for t in TABLES:
        for ext in ('.uasset', '.uexp'):
            sources[f'Dispatch/Content/ArabicReveal/{t}{ext}'] = src = TABLE_SRC / f'{t}{ext}'
            assert sha(src) == report['files'][src.name], f'{src.name} differs from validation.json'
    expected = {k: sha(v) for k, v in sources.items()}
    assert sha(PAK_019) == PAK_019_SHA
    old = members(ROOT / 'builds/rtl_poc/r8b_runtime_staging_019/work/unpacked_1')
    assert set(expected) == set(old), 'virtual paths differ from the 019 pak'
    assert all(expected[k] == old[k] for k in expected if k.startswith(WBP)), 'WBP differs from the 019 pak'
    assert all(expected[k] != old[k] for k in expected if '/ArabicReveal/' in k), 'DT_AR tables not replaced'
    shipped = set((ROOT / 'reports/pakchunk0-WindowsNoEditor_paths.txt').read_text(encoding='utf-8').split())
    assert WBP + '.uasset' in shipped and WBP + '.uexp' in shipped, 'WBP path is not the shipped virtual path'
    assert not any(k.lower().endswith(('.locres', '.locmeta', '.ttf', '.otf', '.exe', '.dll', '.bin')) or '/UI/Fonts/' in k or 'AssetRegistry' in k
                   or '/Localization/' in k for k in expected), 'Texts/Fonts/Locmeta/TTF/EXE/DLL/AssetRegistry must stay out'

    (STAGE / 'work').mkdir(parents=True); payload = STAGE / 'payload'
    for k, v in sources.items():
        (payload / k).parent.mkdir(parents=True, exist_ok=True); (payload / k).write_bytes(v.read_bytes())
    assert members(payload) == expected
    first, second = STAGE / 'Dispatch_AR_R8b_P.pak', STAGE / 'work/build_2.pak'
    env = {**os.environ, 'RAYON_NUM_THREADS': '1'}
    for i, target in enumerate((first, second), 1):
        run([REPAK, 'pack', payload, target, '--version', 'V11', '--mount-point', '../../../', '--path-hash-seed', '0', '--quiet'], f'pack_{i}.log', env)
    assert first.read_bytes() == second.read_bytes(), 'non-deterministic pak'
    listing = run([REPAK, 'list', first], 'pak_list.log'); (STAGE / 'pak_file_list.txt').write_text(listing, encoding='utf-8')
    assert sorted(listing.split()) == sorted(expected) and len(listing.split()) == 10
    info = run([REPAK, 'info', first], 'pak_info.log'); (STAGE / 'pak_info.txt').write_text(info, encoding='utf-8')
    assert 'version: V11' in info and 'mount point: ../../../' in info and 'compression: None' in info and 'encrypted index: false' in info
    readback = {}
    for i, target in enumerate((first, second), 1):
        out = STAGE / f'work/unpacked_{i}'
        run([REPAK, 'unpack', target, '--output', out, '--quiet'], f'unpack_{i}.log')
        readback[f'build_{i}'] = members(out); assert readback[f'build_{i}'] == expected, 'readback differs or extra files'
    font = sha(FONT_PAK)
    assert font == 'b8b22bcb0d6f4fd31963a2743c12c822273cc54cc983947e7a0997bda07db19f', 'font pak changed'
    save('determinism.json', {'PAK_BUILD_1_SHA256': sha(first), 'PAK_BUILD_2_SHA256': sha(second), 'byte_equal': True, 'RAYON_NUM_THREADS': '1',
                              'repak_sha256': sha(REPAK), 'format': 'V11', 'mount': '../../../', 'path_hash_seed': 0, 'compressed': False, 'encrypted': False})
    save('readback_hashes.json', {'source': expected, **readback, 'all_hash_equal': True, 'extra_files': 0})
    save('manifest.json', {
        'status': 'R8B_STYLEFIX_STAGING_PAK_READY_NOT_INSTALLED', 'labels': ['OFFLINE_VALIDATED', 'STAGING_ONLY', 'NOT_INSTALLED', 'NOT_RUNTIME_TESTED'],
        'pak': first.name, 'size': first.stat().st_size, 'sha256': sha(first), 'files': expected, 'file_count': 10,
        'wbp_source': 'builds/rtl_poc/r8b_repair_019 (unchanged)', 'wbp_sha256': WBP_019, 'tables_source': 'builds/rtl_poc/r8b_stylefix_021',
        'table_row_struct': '/Script/UMG.RichTextStyleRow', 'differs_from_019_pak_only_in': [f'Dispatch/Content/ArabicReveal/{t}{e}' for t in TABLES for e in ('.uasset', '.uexp')],
        'pak_019_sha256': PAK_019_SHA,
        'excluded': ['Dispatch_AR_Texts_P.pak content', 'Dispatch_AR_Fonts_P.pak content', 'Dispatch_AR_Locmeta_P.pak', 'TTF', 'EXE', 'DLL', 'AssetRegistry'],
        'font_pak_sha256_unchanged': font, 'future_runtime_set': ['Dispatch_AR_Texts_P.pak', 'Dispatch_AR_Fonts_P.pak', 'Dispatch_AR_R8b_P.pak', '-culture=ar'],
        'installed': False, 'tested_in_game': 0, 'final': 0, 'R8B_STYLEFIX_READY': True, 'IN_GAME_RTL_PROVEN': False})
    (STAGE / 'STAGING_ONLY_NOT_INSTALLED.txt').write_text(
        'STAGING ONLY (round 021). R8b = round-019 WBP + DT_AR tables with RowStruct /Script/UMG.RichTextStyleRow.\n'
        'OFFLINE_VALIDATED, NOT_INSTALLED, NOT_RUNTIME_TESTED. Install only after supervisor approval of RUN6_READY.md. final=0\n', encoding='utf-8')
    print('R8B_STYLEFIX_STAGING_PAK_READY', sha(first), first.stat().st_size)


if __name__ == '__main__':
    main()
