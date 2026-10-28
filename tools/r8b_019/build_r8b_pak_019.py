"""Round 019: staging-only Dispatch_AR_R8b_P.pak with only the repaired R8b assets (never installs anything).

Contents = the 014 layout: the validated r8b_repair_019 WBP renamed to the shipped WBP_SubtitleBlock path plus the four
unchanged stage1 DT_AR tables. No Texts, Fonts or Locmeta. repak 0.2.3, V11, mount ../../../, seed 0, RAYON_NUM_THREADS=1,
built twice and read back. python -X utf8 -I tools/r8b_019/build_r8b_pak_019.py
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'builds/rtl_poc/r8b_repair_019'
STAGE = ROOT / 'builds/rtl_poc/r8b_runtime_staging_019'
OLD = ROOT / 'builds/rtl_poc/runtime_staging_014/tree'
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
    report = json.loads((SRC / 'repair_verification.json').read_text(encoding='utf-8'))
    assert report['status'] == 'R8B_REPAIR_019_GENERATED' and report['validator_errors'] == 0 and report['return_contract_invalid'] == 0
    assert report['deterministic'] and report['roundtrip'] and report['cross_check_equals_repair_of_012']
    sources = {WBP + ext: SRC / ('WBP_SubtitleBlock_AR_R8B_REPAIR_019' + ext) for ext in ('.uasset', '.uexp')}
    assert sha(sources[WBP + '.uasset']).upper() == report['uasset_sha256'] and sha(sources[WBP + '.uexp']).upper() == report['uexp_sha256']
    for t in TABLES:
        for ext in ('.uasset', '.uexp'): sources[f'Dispatch/Content/ArabicReveal/{t}{ext}'] = ROOT / f'builds/rtl_poc/stage1/Dispatch/Content/ArabicReveal/{t}{ext}'
    expected = {k: sha(v) for k, v in sources.items()}
    old = members(OLD)
    assert set(expected) == set(old), 'virtual paths differ from the 014 layout'
    assert all(expected[k] == old[k] for k in expected if '/ArabicReveal/' in k), 'DT_AR tables changed since 014'
    assert all(expected[k] != old[k] for k in expected if k.startswith(WBP)), 'WBP not repaired'
    shipped = set((ROOT / 'reports/pakchunk0-WindowsNoEditor_paths.txt').read_text(encoding='utf-8').split())
    assert WBP + '.uasset' in shipped and WBP + '.uexp' in shipped, 'WBP path is not the shipped virtual path'
    assert not any(k.endswith(('.locres', '.locmeta')) or '/UI/Fonts/' in k or k.endswith('.ttf') for k in expected), 'Texts/Fonts must stay out'

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
    assert set(listing.split()) == set(expected) and len(listing.split()) == 10
    info = run([REPAK, 'info', first], 'pak_info.log'); (STAGE / 'pak_info.txt').write_text(info, encoding='utf-8')
    assert 'version: V11' in info and 'mount point: ../../../' in info and 'compression: None' in info and 'encrypted index: false' in info
    old_listing = run([REPAK, 'list', ROOT / 'builds/rtl_poc/runtime_staging_014/STAGING_ONLY_R8b_014.pak'], 'pak_list_014.log')
    assert set(old_listing.split()) == set(listing.split()), 'path set differs from the installed-in-Run-2 R8b pak'
    readback = {}
    for i, target in enumerate((first, second), 1):
        out = STAGE / f'work/unpacked_{i}'
        run([REPAK, 'unpack', target, '--output', out, '--quiet'], f'unpack_{i}.log')
        readback[f'build_{i}'] = members(out); assert readback[f'build_{i}'] == expected, 'readback differs'
    font = sha(FONT_PAK)
    assert font == 'b8b22bcb0d6f4fd31963a2743c12c822273cc54cc983947e7a0997bda07db19f', 'font pak changed'
    save('determinism.json', {'PAK_BUILD_1_SHA256': sha(first), 'PAK_BUILD_2_SHA256': sha(second), 'byte_equal': True, 'RAYON_NUM_THREADS': '1',
                              'repak_sha256': sha(REPAK), 'format': 'V11', 'mount': '../../../', 'path_hash_seed': 0, 'compressed': False, 'encrypted': False})
    save('readback_hashes.json', {'source': expected, **readback, 'all_hash_equal': True})
    save('manifest.json', {
        'status': 'R8B_STAGING_PAK_READY_NOT_INSTALLED', 'labels': ['OFFLINE_VALIDATED', 'STAGING_ONLY', 'NOT_INSTALLED', 'NOT_RUNTIME_TESTED'],
        'pak': first.name, 'size': first.stat().st_size, 'sha256': sha(first), 'files': expected, 'file_count': 10,
        'source_artifact': 'builds/rtl_poc/r8b_repair_019', 'repair_uasset_sha256': report['uasset_sha256'], 'repair_uexp_sha256': report['uexp_sha256'],
        'differs_from_014_only_in': [WBP + '.uasset', WBP + '.uexp'], 'pak_014_sha256': sha(ROOT / 'builds/rtl_poc/runtime_staging_014/STAGING_ONLY_R8b_014.pak'),
        'excluded': ['Dispatch_AR_Texts_P.pak content', 'Dispatch_AR_Fonts_P.pak content', 'Dispatch_AR_Locmeta_P.pak'],
        'font_pak_sha256_unchanged': font, 'future_runtime_set': ['Dispatch_AR_Texts_P.pak', 'Dispatch_AR_Fonts_P.pak', 'Dispatch_AR_R8b_P.pak', '-culture=ar'],
        'installed': False, 'tested_in_game': 0, 'final': 0, 'R8B_FIXED': True, 'IN_GAME_RTL_PROVEN': False})
    (STAGE / 'STAGING_ONLY_NOT_INSTALLED.txt').write_text(
        'STAGING ONLY (round 019). Repaired R8b: Build Arabic Timing is void. OFFLINE_VALIDATED, NOT_INSTALLED, NOT_RUNTIME_TESTED.\n'
        'Install only after a separate supervisor approval of the Run 5 procedure (report_019). final=0\n', encoding='utf-8')
    print('R8B_STAGING_PAK_READY', sha(first), first.stat().st_size)


if __name__ == '__main__':
    main()
