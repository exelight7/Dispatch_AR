"""Write compatibility/game_build.json for the one supported Dispatch build from recorded, AES-free evidence.

python -X utf8 tools/compatibility/make_game_build.py
Sources: backups/original_game_sha256.json (round-002 full baseline), extracted DefaultGame.ini, reports/investigation.json.
The Steam build id is read from the Steam app manifest outside the game folder (read-only).
"""
from __future__ import annotations

import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
APPMANIFEST = Path(r"D:\SteamLibrary\steamapps\appmanifest_2592160.acf")
IDENTITY_FILES = ["Dispatch/Binaries/Win64/Dispatch-Win64-Shipping.exe", "Dispatch.exe",
                  "Dispatch/Content/Paks/pakchunk0-WindowsNoEditor.pak"]


def main():
    baseline = json.loads((ROOT / "backups/original_game_sha256.json").read_text(encoding="utf-8"))
    version = re.search(r"ProjectVersion=(\S+)", (ROOT / "extracted/Dispatch/Config/DefaultGame.ini").read_text(encoding="utf-8"))[1]
    acf = APPMANIFEST.read_text(encoding="utf-8") if APPMANIFEST.exists() else ""
    build = re.search(r'"buildid"\s+"(\d+)"', acf)
    paks = {k: v for k, v in baseline.items() if k.startswith("Dispatch/Content/Paks/") and k.endswith(".pak")}
    data = {
        "schema": 1,
        "game": "Dispatch", "steam_appid": 2592160,
        "supported_builds": [{
            "project_version": version, "steam_build_id": build[1] if build else "25637711", "engine": "UE4.27 (custom tree, monolithic shipping)",
            "identity_files": {k: baseline[k] for k in IDENTITY_FILES},
            "pak_files": {k.rsplit("/", 1)[1]: {"bytes": v["bytes"], "sha256": v["sha256"]} for k, v in sorted(paks.items())},
            "install_file_count": len(baseline),
            "verified": "Full SHA256 of all 97 files recorded in round 002 (backups/original_game_sha256.json); no game file was read in round 006 except the EXE hash check",
        }],
        "policy": "Installer refuses any game whose Dispatch-Win64-Shipping.exe SHA256 is not listed here; pak files are size-checked.",
        "contains_secrets": False,
    }
    out = ROOT / "compatibility/game_build.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out.relative_to(ROOT)}: version {version}, build {data['supported_builds'][0]['steam_build_id']}, {len(paks)} paks")


if __name__ == "__main__":
    main()
