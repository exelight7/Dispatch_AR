"""Round 024: staging-only Dispatch_AR_R8b_P.pak = round-024 fade WBP + round-021 DT_AR tables (unchanged). Never installs anything.
Same workflow as rounds 019/021: repak 0.2.3, V11, mount ../../../, seed 0, uncompressed, RAYON_NUM_THREADS=1, built twice, both
unpacked and hash-compared with the sources. Refuses to run unless the fade validation and the emitted-bytecode replay passed.
python -X utf8 -I tools/r8b_023/build_r8b_pak_023.py
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
FADE = ROOT / 'builds/rtl_poc/r8b_fade_023'
WBP_SRC = FADE / 'WBP_SubtitleBlock_AR_R8B_FADE_023'
TABLE_SRC = ROOT / 'builds/rtl_poc/r8b_stylefix_021'
STAGE = ROOT / 'builds/rtl_poc/r8b_runtime_staging_023'
PAK_021 = ROOT / 'builds/rtl_poc/r8b_runtime_staging_021'
PAK_021_SHA = 'a3402118a351a09b4ae544493f437203c28ce2df8081d24aad729faf3321e916'   # installed in Run 6
FONT_PAK = ROOT / 'builds/rtl_poc/font_runtime_018/Dispatch_AR_Fonts_P.pak'
REPAK = ROOT / 'tools/repak-v0.2.3/repak.exe'
WBP = 'Dispatch/Content/Shared/Core/Widgets/WBP_SubtitleBlock'
TABLES = ['DT_AR_Fill', 'DT_AR_Fill_Large', 'DT_AR_Outline', 'DT_AR_Outline_Large']


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
    report = json.loads((FADE / 'validation.json').read_text(encoding='utf-8'))
    assert report['status'] == 'R8B_FADE_023_GENERATED' and report['validator_errors'] == 0 and report['unexpected_changes'] == 0
    assert report['deterministic'] and report['roundtrip'] and report['return_contract']['invalid'] == 0 and report['RichTextStyleGate']['bindings'] == 14
    assert json.loads((FADE / 'fade_replay.json').read_text(encoding='utf-8'))['verdict'] == 'BYTECODE_REPLAY_PASS', 'emitted-bytecode replay not passed'
    sources = {WBP + ext: WBP_SRC.with_suffix(ext) for ext in ('.uasset', '.uexp')}
    assert sha(sources[WBP + '.uasset']) == report['uasset_sha256'] and sha(sources[WBP + '.uexp']) == report['uexp_sha256'], 'fade WBP differs from validation.json'
    for t in TABLES:
        for ext in ('.uasset', '.uexp'):
            sources[f'Dispatch/Content/ArabicReveal/{t}{ext}'] = src = TABLE_SRC / f'{t}{ext}'
            assert sha(src) == report['dt_ar_tables_round_021_unchanged'][src.name], f'{src.name} changed since round 021'
    expected = {k: sha(v) for k, v in sources.items()}
    assert sha(PAK_021 / 'Dispatch_AR_R8b_P.pak') == PAK_021_SHA
    old = members(PAK_021 / 'work/unpacked_1')
    assert set(expected) == set(old), 'virtual paths differ from the Run 6 pak'
    assert all(expected[k] == old[k] for k in expected if '/ArabicReveal/' in k), 'DT_AR tables differ from the Run 6 pak'
    assert all(expected[k] != old[k] for k in expected if k.startswith(WBP)), 'WBP not replaced'
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
        'status': 'R8B_FADE_STAGING_PAK_READY_NOT_INSTALLED', 'labels': ['STAGING_ONLY', 'NOT_INSTALLED', 'NOT_RUNTIME_TESTED'],
        'pak': first.name, 'size': first.stat().st_size, 'sha256': sha(first), 'files': expected, 'file_count': 10,
        'wbp_source': 'builds/rtl_poc/r8b_fade_023', 'wbp_sha256': {'.uasset': report['uasset_sha256'], '.uexp': report['uexp_sha256']},
        'tables_source': 'builds/rtl_poc/r8b_stylefix_021 (unchanged, byte-identical to the Run 6 pak)',
        'differs_from_run6_pak_only_in': [WBP + '.uasset', WBP + '.uexp'], 'run6_pak_sha256': PAK_021_SHA,
        'excluded': ['Dispatch_AR_Texts_P.pak content', 'Dispatch_AR_Fonts_P.pak content', 'Dispatch_AR_Locmeta_P.pak', 'TTF', 'EXE', 'DLL', 'AssetRegistry'],
        'font_pak_sha256_unchanged': font, 'future_runtime_set': ['Dispatch_AR_Texts_P.pak', 'Dispatch_AR_Fonts_P.pak', 'Dispatch_AR_R8b_P.pak (this file)', '-culture=ar'],
        'installed': False, 'tested_in_game': 0, 'final': 0, 'IN_GAME_RTL_PROVEN': False})
    (STAGE / 'STAGING_ONLY_NOT_INSTALLED.txt').write_text(
        'STAGING_ONLY NOT_INSTALLED NOT_RUNTIME_TESTED (round 024).\nR8b = round-024 fade WBP (Arabic Fade Tick) + round-021 DT_AR tables (unchanged).\n'
        'The Run 6 pak (a3402118...e916) stays installed. Install only after supervisor approval of RUN7_READY.md. final=0\n', encoding='utf-8')
    print('R8B_FADE_STAGING_PAK_READY', sha(first), first.stat().st_size)


if __name__ == '__main__':
    main()
