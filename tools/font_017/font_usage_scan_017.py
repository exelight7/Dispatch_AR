"""Round 017 read-only scan: which shipped packages import which font objects (all PAKs).
Same batching as tools/proto_binary_analysis/package_name_scan_012.py; the AES key is read in memory and only passed
to the repak child process. Usage: python -I font_usage_scan_017.py <scratch_dir> <new_result.json>"""
import subprocess, sys, json, shutil
from pathlib import Path
ROOT = Path(r"C:\Dispatch_AR")
PAKS = Path(r"D:\SteamLibrary\steamapps\common\Dispatch\Dispatch\Content\Paks")
TMP = Path(sys.argv[1]); OUTF = Path(sys.argv[2])
key = (ROOT / "tools/local_aes_key.txt").read_text().strip()
repak = ROOT / "tools/repak-v0.2.3/repak.exe"
# Font objects (UFont) a widget/style can reference, plus the legacy-name marker.
FONTS = ["/Game/Shared/UI/Fonts/Montserrat-Variable", "/Game/Shared/UI/Fonts/Orbitron-Variable",
         "/Game/Shared/UI/Fonts/Rajdhani-Variable", "/Game/Shared/Shifts/Art/Fonts/Aktiv_Grotesk_Font",
         "/Game/Shared/Shifts/Art/UI/Fonts/Tomorrow/", "/Game/Shared/Shifts/Art/Fonts/Roboto_Regular/",
         "/Game/Shared/Shifts/Art/Fonts/Roboto_Mono/", "/Game/Shared/Shifts/Art/Fonts/Input/",
         "/Game/Shared/Shifts/Art/Fonts/SourceCodePro/", "/Game/Shared/Shifts/Art/Fonts/schaboxcondensed/",
         "/Game/Shared/Shifts/Art/Fonts/ChiKareGo/", "/Game/Shared/Core/Art/UI/ButtonPrompts/KeyboardMouse/Font_Keycap",
         "/Game/Shared/UI/Fonts/Barlow/", "/Engine/EngineFonts/Roboto", "/Engine/EngineFonts/RobotoDistanceField",
         "/Game/Shared/UI/Fonts/Montserrat/static/", "/Game/Shared/UI/Fonts/NotoSans"]
hits = {}; n = 0
for lst in sorted((ROOT / "reports").glob("pakchunk*_paths.txt")):
    pak = PAKS / lst.name.replace("_paths.txt", ".pak")
    paths = [p for p in lst.read_text(encoding="utf-8").split() if p.endswith((".uasset", ".umap"))]
    for i in range(0, len(paths), 200):
        if TMP.exists(): shutil.rmtree(TMP)
        TMP.mkdir(parents=True)
        cmd = [str(repak), "--aes-key", key, "unpack", str(pak), "--output", str(TMP), "--quiet"]
        for p in paths[i:i+200]: cmd += ["--include", p]
        r = subprocess.run(cmd, capture_output=True)
        if r.returncode: print("repak failed", pak.name, i, r.stderr[-300:]); sys.exit(1)
        for p in paths[i:i+200]:
            b = (TMP / p).read_bytes(); n += 1
            f = [k for k in FONTS if k.encode() in b]
            if f or b"FontObject" in b or b"SlateFontInfo" in b:
                hits[f"{pak.name}:{p}"] = {"fonts": f, "FontObject": b"FontObject" in b, "SlateFontInfo": b"SlateFontInfo" in b,
                                           "FontFallback": b"FontFallback" in b}
    print(pak.name, "done", n, flush=True)
shutil.rmtree(TMP, ignore_errors=True)
OUTF.write_text(json.dumps({"packages_scanned": n, "hits": hits}, indent=1))
print("ALL_SCAN_DONE", n)
