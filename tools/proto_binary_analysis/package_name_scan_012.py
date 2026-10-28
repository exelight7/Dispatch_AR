"""Round 012 read-only name-map scan of every shipped .uasset/.umap header (all PAKs).
Unpacks headers in batches of 200 into a caller-given scratch dir, scans, deletes; game files are only read.
The AES key is read in memory from tools/local_aes_key.txt (as scripts/investigate.py does), passed to the
repak child process, and never printed or written. Usage: python -I package_name_scan_012.py <scratch_dir> <new_result.json>"""
import subprocess, sys, json, shutil
from pathlib import Path
ROOT = Path(r"C:\Dispatch_AR")
PAKS = Path(r"D:\SteamLibrary\steamapps\common\Dispatch\Dispatch\Content\Paks")
TMP = Path(sys.argv[1]); OUTF = Path(sys.argv[2])
key = (ROOT / "tools/local_aes_key.txt").read_text().strip()
repak = ROOT / "tools/repak-v0.2.3/repak.exe"
needles = ["Animate While Paused", "AnimateWhilePaused", "WBP_SubtitleBlock", "On Finish Letter by Letter Print",
           "Stop Displaying Line", "Set Displayed Line", "Get Subtitle Block From Pool", "WBP_SubtitlesWidget"]
hits = {k: [] for k in needles}; n = 0
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
            for k in needles:
                if k.encode() in b: hits[k].append(f"{pak.name}:{p}")
    print(pak.name, "done", n, flush=True)
shutil.rmtree(TMP, ignore_errors=True)
OUTF.write_text(json.dumps({"packages_scanned": n, "hits": hits}, indent=1))
print("ALL_SCAN_DONE", n)
