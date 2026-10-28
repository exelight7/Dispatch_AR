"""Install only the reviewed text pak through the existing guarded installer."""
import csv
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from install import STATE, change, check_compatibility

GAME = Path(r"D:\SteamLibrary\steamapps\common\Dispatch")
BACKUP = ROOT / "backups/proofread_20261027_pass3"
PACKAGE = ROOT / "builds/arabic_texts_experimental"
PAK_NAME = "Dispatch_AR_Texts_P.pak"
RECEIPT = BACKUP / "installation_receipt.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_game_closed():
    proc = subprocess.run(["tasklist", "/FO", "CSV", "/NH"], check=True,
                          capture_output=True, text=True, errors="replace")
    names = {row[0].lower() for row in csv.reader(proc.stdout.splitlines()) if row}
    if names & {"dispatch.exe", "dispatch-win64-shipping.exe"}:
        raise RuntimeError("Close Dispatch before updating the text package")


def inventory():
    directory = GAME / "Dispatch/Content/Paks"
    return {p.name: {"size": p.stat().st_size, "mtime_ns": p.stat().st_mtime_ns,
                     "sha256": sha(p) if p.name.startswith("Dispatch_AR") else None}
            for p in directory.glob("*.pak")}


def main():
    if RECEIPT.exists():
        raise FileExistsError("Installation receipt already exists; refusing a new transaction")
    require_game_closed()
    previous = json.loads((BACKUP / "game_before/snapshot.json").read_text(encoding="utf-8"))
    old_manifest = json.loads((BACKUP / "builds/arabic_texts_experimental/manifest.json").read_text(encoding="utf-8"))
    manifest = json.loads((PACKAGE / "manifest.json").read_text(encoding="utf-8"))
    target = GAME / "Dispatch/Content/Paks" / PAK_NAME
    if sha(target) != previous["text_sha256"] or sha(target) != old_manifest["pak_sha256"]:
        raise RuntimeError("Installed text package changed after backup")
    if sha(PACKAGE / PAK_NAME) != manifest["pak_sha256"]:
        raise RuntimeError("Reviewed package checksum mismatch")
    before = inventory()
    for entry in previous["paks"]:
        if entry["name"] != PAK_NAME:
            actual = before.get(entry["name"])
            expected = {k: entry[k] for k in ("size", "mtime_ns", "sha256")}
            if actual != expected:
                raise RuntimeError("Other game package changed after backup: " + entry["name"])
    compat = ROOT / "compatibility/game_build.json"
    build = check_compatibility(GAME, compat)
    identities = {}
    for relative, info in build["identity_files"].items():
        actual = sha(GAME / relative)
        if actual != info["sha256"]:
            raise RuntimeError("Unsupported game identity: " + relative)
        identities[relative] = actual
    if set(before) != {p["name"] for p in previous["paks"]}:
        raise RuntimeError("Game package set changed after backup")
    adopted = not STATE.exists()
    if adopted:
        # The existing package is known by both its build manifest and verified backup.
        state = {"installed": True, "game_root": str(GAME.resolve()), "pak_name": PAK_NAME,
                 "pak_sha256": previous["text_sha256"],
                 "provenance": "adopted_existing_package_matching_prior_build_manifest"}
        with STATE.open("x", encoding="utf-8") as file:
            json.dump(state, file, indent=2)
    else:
        shutil.copy2(STATE, BACKUP / "installation_state_before.json")
    dry_run = change(PACKAGE, GAME, STATE, compat_path=compat, dry_run=True)
    require_game_closed()
    installed = change(PACKAGE, GAME, STATE, compat_path=compat)
    if sha(target) != manifest["pak_sha256"]:
        raise RuntimeError("Installed package differs from reviewed build")
    repeat = change(PACKAGE, GAME, STATE, compat_path=compat)
    if "already installed" not in repeat:
        raise RuntimeError("Installer repeat was not idempotent")
    after = inventory()
    if set(after) != set(before):
        raise RuntimeError("Unexpected game package addition or removal")
    for name in before:
        if name != PAK_NAME and after[name] != before[name]:
            raise RuntimeError("Unexpected change to another package: " + name)
    for relative, expected in identities.items():
        if sha(GAME / relative) != expected:
            raise RuntimeError("Original game identity changed: " + relative)
    receipt = {"installed_at_utc": datetime.now(timezone.utc).isoformat(),
               "game_root": str(GAME), "installed_file": str(target),
               "old_pak_sha256": previous["text_sha256"],
               "new_pak_sha256": manifest["pak_sha256"], "new_pak_bytes": target.stat().st_size,
               "previous_package_backup": str(BACKUP / "game_before" / PAK_NAME),
               "adopted_verified_existing_installation": adopted,
               "dry_run": dry_run, "installer_result": installed, "idempotent_repeat": True,
               "original_identity_sha256_unchanged": identities,
               "other_paks_unchanged": True, "pak_inventory_before": before,
               "pak_inventory_after": after, "game_launched": False, "runtime_tested": False}
    with RECEIPT.open("x", encoding="utf-8") as file:
        json.dump(receipt, file, indent=2)
        file.write("\n")
    print("REVIEWED_TEXTS_INSTALLED_SHA256_VERIFIED " + manifest["pak_sha256"])
    print("Receipt: " + str(RECEIPT))


if __name__ == "__main__":
    main()
