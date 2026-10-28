"""Optional reversible installation of the experimental Arabic text pak only.

Does not launch Dispatch, change culture settings, overwrite original packages,
change save data, or install the detached renderer experiment.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "builds/arabic_texts_experimental"
if not PACKAGE.is_dir() and (ROOT / "manifest.json").is_file():
    PACKAGE = ROOT  # The standalone experimental ZIP keeps its manifest here.
PAK_NAME = "Dispatch_AR_Texts_P.pak"
STATE = ROOT / "backups/installation_state.json"
COMPAT = ROOT / "compatibility/game_build.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_compatibility(game, compat_path):
    """Refuse any install whose executable hash or pak sizes are not a verified supported build."""
    compat = json.loads(compat_path.read_text(encoding="utf-8"))
    executable = game / "Dispatch/Binaries/Win64/Dispatch-Win64-Shipping.exe"
    if not executable.is_file():
        raise ValueError("Not a Dispatch installation: shipping executable missing")
    exe_hash = sha(executable)
    key = "Dispatch/Binaries/Win64/Dispatch-Win64-Shipping.exe"
    for build in compat["supported_builds"]:
        if build["identity_files"][key]["sha256"] != exe_hash:
            continue
        for name, info in build["pak_files"].items():
            pak = game / "Dispatch/Content/Paks" / name
            if not pak.is_file() or pak.stat().st_size != info["bytes"]:
                raise ValueError(f"Original package {name} differs from the supported build")
        return build
    raise ValueError("Unsupported Dispatch build: executable hash is not in compatibility/game_build.json")


def change(package, game, state_path, uninstall=False, compat_path=COMPAT, dry_run=False):
    game = game.resolve()
    destination = game / "Dispatch/Content/Paks" / PAK_NAME
    previous = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else None
    if previous and previous.get("game_root") != str(game):
        raise ValueError("Install state belongs to a different game directory")
    if destination.exists():
        if not previous or not previous.get("installed") or sha(destination) != previous["pak_sha256"]:
            raise ValueError("Destination is not the unchanged package owned by this installer")
    if uninstall:
        if destination.exists():
            destination.unlink()  # Only the fixed, hash-verified additive mod file.
        if previous:
            previous["installed"] = False
            state_path.write_text(json.dumps(previous, indent=2) + "\n", encoding="utf-8")
        return "Experimental text pak removed; original game files were not changed"
    manifest = json.loads((package / "manifest.json").read_text(encoding="utf-8"))
    build = check_compatibility(game, compat_path)
    source = package / PAK_NAME
    if manifest["kind"] != "arabic-texts-experimental" or manifest["pak_name"] != PAK_NAME:
        raise ValueError("Wrong build kind or package filename")
    if sha(source) != manifest["pak_sha256"]:
        raise ValueError("Build checksum mismatch")
    executable = game / "Dispatch/Binaries/Win64/Dispatch-Win64-Shipping.exe"
    if not executable.is_file() or sha(executable) != manifest["game_executable_sha256"]:
        raise ValueError("Game executable differs from the investigated build")
    if not destination.parent.is_dir():
        raise ValueError("Installed game pak directory not found")
    if dry_run:
        return f"Dry run: compatible with {build['project_version']} / Steam build {build['steam_build_id']}; would add {destination.name}; nothing written"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and sha(destination) == manifest["pak_sha256"]:
        return "Same experimental text pak is already installed"
    if destination.exists():
        backup = state_path.parent / f"previous_ar_texts_{sha(destination)}.pak"
        if not backup.exists():
            shutil.copy2(destination, backup)
    with tempfile.NamedTemporaryFile(prefix="Dispatch_AR_", suffix=".tmp", dir=destination.parent, delete=False) as stream:
        temp = Path(stream.name)
        stream.write(source.read_bytes())
    try:
        if sha(temp) != manifest["pak_sha256"]:
            raise ValueError("Copied package checksum mismatch")
        temp.replace(destination)
    finally:
        if temp.exists():
            temp.unlink()
    state_path.write_text(json.dumps({"installed": True, "game_root": str(game),
        "pak_name": PAK_NAME, "pak_sha256": manifest["pak_sha256"],
        "installed_files": [destination.relative_to(game).as_posix()], "game_build": build["steam_build_id"],
        "runtime_tested": False, "rtl_typewriter_fixed": False}, indent=2) + "\n", encoding="utf-8")
    return "Experimental text pak installed; native Arabic progressive reveal remains unresolved"


def selftest():
    (ROOT / "tests").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="install-test-", dir=ROOT / "tests") as folder:
        folder = Path(folder).resolve()
        assert folder.is_relative_to((ROOT / "tests").resolve())
        package, game, state = folder / "package", folder / "game", folder / "state.json"
        package.mkdir()
        (game / "Dispatch/Content/Paks").mkdir(parents=True)
        executable = game / "Dispatch/Binaries/Win64/Dispatch-Win64-Shipping.exe"
        executable.parent.mkdir(parents=True)
        executable.write_bytes(b"fake test executable; never executed")
        original = game / "Dispatch/Content/Paks/original.pak"
        original.write_bytes(b"original sentinel")
        (package / PAK_NAME).write_bytes(b"test package")
        manifest = {"kind": "arabic-texts-experimental", "pak_name": PAK_NAME,
                    "pak_sha256": sha(package / PAK_NAME), "game_executable_sha256": sha(executable)}
        (package / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        compat = folder / "game_build.json"
        build = {"project_version": "test", "steam_build_id": "0", "pak_files": {"original.pak": {"bytes": original.stat().st_size}},
                 "identity_files": {"Dispatch/Binaries/Win64/Dispatch-Win64-Shipping.exe": {"sha256": sha(executable)}}}
        compat.write_text(json.dumps({"supported_builds": [build]}), encoding="utf-8")
        assert "Dry run" in change(package, game, state, compat_path=compat, dry_run=True)
        assert not (original.parent / PAK_NAME).exists() and not state.exists(), "dry run wrote files"
        bad = folder / "bad_build.json"
        bad.write_text(json.dumps({"supported_builds": [{**build, "identity_files": {"Dispatch/Binaries/Win64/Dispatch-Win64-Shipping.exe": {"sha256": "0" * 64}}}]}), encoding="utf-8")
        for wrong in [bad]:
            try:
                change(package, game, state, compat_path=wrong)
            except ValueError:
                pass
            else:
                raise AssertionError("Unsupported build accepted")
        resized = folder / "resized.json"
        resized.write_text(json.dumps({"supported_builds": [{**build, "pak_files": {"original.pak": {"bytes": 1}}}]}), encoding="utf-8")
        try:
            change(package, game, state, compat_path=resized)
        except ValueError:
            pass
        else:
            raise AssertionError("Changed original pak accepted")
        assert "installed" in change(package, game, state, compat_path=compat)
        assert json.loads(state.read_text(encoding="utf-8"))["installed_files"] == ["Dispatch/Content/Paks/" + PAK_NAME]
        assert "already installed" in change(package, game, state, compat_path=compat)
        installed = original.parent / PAK_NAME
        installed.write_bytes(b"foreign modification")
        try:
            change(package, game, state, uninstall=True)
        except ValueError:
            pass
        else:
            raise AssertionError("Modified foreign data was deleted")
        installed.write_bytes(b"test package")
        change(package, game, state, uninstall=True)
        assert not installed.exists() and original.read_bytes() == b"original sentinel"
    print("Install compatibility refusal, dry run, idempotency, foreign-file refusal and uninstall safety self-checks passed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experimental-text-only", action="store_true")
    parser.add_argument("--uninstall", action="store_true")
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="Check compatibility and target only; write nothing")
    parser.add_argument("--game-root", type=Path, help="Dispatch install folder, e.g. <Steam library>/steamapps/common/Dispatch")
    args = parser.parse_args()
    if args.selftest:
        selftest()
    elif (args.uninstall or args.experimental_text_only) and not args.game_root:
        parser.error("--game-root is required; no game path is assumed")
    elif args.uninstall or args.experimental_text_only:
        print(change(PACKAGE, args.game_root, STATE, uninstall=args.uninstall, dry_run=args.dry_run))
    else:
        parser.error("Choose --experimental-text-only or --uninstall. No game is launched.")
