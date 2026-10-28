"""Reproduce read-only Dispatch package discovery, extraction and integrity checks."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GAME = Path(r"D:\SteamLibrary\steamapps\common\Dispatch")


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def footer(path):
    with path.open("rb") as stream:
        stream.seek(-204, 2)
        data = stream.read()
    if data[:4] != bytes.fromhex("e1126f5a"):
        raise ValueError(f"Not the observed UE4.27 v11 footer: {path.name}")
    version, offset, size = struct.unpack_from("<Iqq", data, 4)
    if version != 11 or offset < 0 or offset + size > path.stat().st_size:
        raise ValueError(f"Unsupported package footer: {path.name}")
    return offset, size, data[24:44]


def find_local_key(executable, pak):
    from Crypto.Cipher import AES
    code = executable.read_bytes()
    offset, size, expected = footer(pak)
    with pak.open("rb") as stream:
        stream.seek(offset)
        encrypted = stream.read(size)
    # Collect immediate dword stores in a small instruction window, then verify
    # candidates against the complete decrypted index SHA1, not a text guess.
    patterns = [(rb"\xc7([\x40-\x47])(.)(.{4})", 1),
                (rb"\xc7\x44\x24(.)(.{4})", 2)]
    for pattern, form in patterns:
        hits = list(re.finditer(pattern, code, re.S))
        for i, match in enumerate(hits):
            base, disp, value = (match[1], match[2][0], match[3]) if form == 1 else (b"rsp", match[1][0], match[2])
            stores = {disp: value}
            for next_match in hits[i + 1:i + 20]:
                if next_match.start() - match.start() > 180:
                    break
                other_base, other_disp, other_value = (next_match[1], next_match[2][0], next_match[3]) if form == 1 else (b"rsp", next_match[1][0], next_match[2])
                if other_base == base:
                    stores.setdefault(other_disp, other_value)
            if not all(disp + 4 * j in stores for j in range(8)):
                continue
            key = b"".join(stores[disp + 4 * j] for j in range(8))
            prefix = AES.new(key, AES.MODE_ECB).decrypt(encrypted[:32])
            if not (0 < struct.unpack_from("<i", prefix)[0] < 256 and b"../" in prefix):
                continue
            plain = AES.new(key, AES.MODE_ECB).decrypt(encrypted)
            if hashlib.sha1(plain).digest() == expected:
                return key, match.start()
    raise ValueError("No index-verified local key found; no package was modified")


def selected(path):
    localization = "/Localization/" in path and ("/en/" in path or path.count("/") == 4)
    font = path.lower().endswith((".ufont", ".ttf", ".otf")) or ("/Fonts/" in path and path.endswith((".uasset", ".uexp")))
    ui = any(part in path for part in ["/Shared/Core/Widgets/", "/Shared/Story/Widgets/ChoiceUIs/",
             "/Shared/Menu/Widgets/SettingsMenu/", "/Plugins/ProtoAnimatedText/",
             "/Shared/Shifts/Gameplay/Widgets/Shift_Misc/WBP_RichText"])
    return localization or font or ui or path.endswith((".ini", ".uplugin"))


def inventory(game, extract=False):
    from Crypto.Cipher import AES
    reports = ROOT / "reports"
    repak = ROOT / "tools/repak-v0.2.3/repak.exe"
    executable = game / "Dispatch/Binaries/Win64/Dispatch-Win64-Shipping.exe"
    paks = sorted((game / "Dispatch/Content/Paks").glob("*.pak"))
    if not paks or not executable.is_file() or not repak.is_file():
        raise ValueError("Game executable, packages or verified repak tool missing")
    key, key_offset = find_local_key(executable, paks[0])
    (ROOT / "tools/local_aes_key.txt").write_text(key.hex() + "\n", encoding="ascii")
    entries, packages, extracted = [], [], []
    for pak in paks:
        offset, size, expected = footer(pak)
        with pak.open("rb") as stream:
            stream.seek(offset)
            plain = AES.new(key, AES.MODE_ECB).decrypt(stream.read(size))
        if hashlib.sha1(plain).digest() != expected:
            raise ValueError(f"Index digest failed: {pak.name}")
        info = subprocess.run([str(repak), "--aes-key", key.hex(), "info", str(pak)], capture_output=True, check=True, text=True).stdout
        paths = subprocess.run([str(repak), "--aes-key", key.hex(), "list", str(pak)], capture_output=True, check=True, text=True).stdout.splitlines()
        (reports / f"{pak.stem}_paths.txt").write_text("\n".join(paths) + "\n", encoding="utf-8")
        packages.append({"name": pak.name, "bytes": pak.stat().st_size,
            "file_count": len(paths), "index_sha1_verified": True, "info": info})
        entries.extend({"pak": pak.name, "path": path} for path in paths)
        chosen = [path for path in paths if selected(path)]
        if extract:
            for start in range(0, len(chosen), 60):
                command = [str(repak), "--aes-key", key.hex(), "unpack", str(pak),
                           "--output", str(ROOT / "extracted"), "--force", "--quiet"]
                for path in chosen[start:start + 60]:
                    command += ["--include", path]
                subprocess.run(command, capture_output=True, check=True)
            for path in chosen:
                file = ROOT / "extracted" / path
                extracted.append({"pak": pak.name, "path": path, "size": file.stat().st_size,
                                  "sha256": sha256(file)})
        print(f"{pak.name}: {len(paths)} entries, index digest verified", flush=True)
    summary = {"game_root": str(game.resolve()), "packages": len(packages),
        "indexed_entries": len(entries), "executable_sha256": sha256(executable),
        "key_executable_offset": key_offset, "game_files_modified": 0,
        "extensions": dict(Counter(Path(e["path"]).suffix for e in entries))}
    for name, data in [("pak_inventory", packages), ("all_asset_paths", entries), ("investigation", summary)]:
        (reports / f"{name}.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    if extract:
        (reports / "extraction_manifest.json").write_text(json.dumps(extracted, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


def baseline(game, verify=False):
    dest = ROOT / "backups/original_game_sha256.json"
    current = {p.relative_to(game).as_posix(): {"bytes": p.stat().st_size, "sha256": sha256(p)}
               for p in sorted(game.rglob("*")) if p.is_file()}
    if verify:
        previous = json.loads(dest.read_text(encoding="utf-8"))
        changed = [name for name in previous if previous[name] != current.get(name)]
        if changed:
            raise ValueError(f"Original game content changed: {changed}")
        added = sorted(set(current) - set(previous))
        print(f"Verified {len(previous)} original game files unchanged; added files: {added}")
    else:
        if dest.exists():
            raise FileExistsError("Original baseline already exists; use verify")
        dest.write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")
        print(f"Recorded SHA256 of {len(current)} original game files")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["inventory", "extract", "baseline", "verify"])
    parser.add_argument("--game-root", type=Path, default=DEFAULT_GAME)
    args = parser.parse_args()
    if args.command in ("baseline", "verify"):
        baseline(args.game_root, verify=args.command == "verify")
    else:
        inventory(args.game_root, extract=args.command == "extract")
