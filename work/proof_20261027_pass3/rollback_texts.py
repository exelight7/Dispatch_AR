"""Restore only the verified text package saved before the third review installation."""
import json

from install_texts import BACKUP, GAME, PAK_NAME, RECEIPT, ROOT, STATE, change, inventory, require_game_closed, sha


def main():
    require_game_closed()
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    target = GAME / "Dispatch/Content/Paks" / PAK_NAME
    if str(GAME) != receipt["game_root"] or sha(target) != receipt["new_pak_sha256"]:
        raise RuntimeError("Refusing rollback of a different or modified installation")
    package = BACKUP / "builds/arabic_texts_experimental"
    manifest = json.loads((package / "manifest.json").read_text(encoding="utf-8"))
    if sha(package / PAK_NAME) != manifest["pak_sha256"] or manifest["pak_sha256"] != receipt["old_pak_sha256"]:
        raise RuntimeError("Previous package backup checksum mismatch")
    before = inventory()
    result = change(package, GAME, STATE, compat_path=ROOT / "compatibility/game_build.json")
    after = inventory()
    if sha(target) != receipt["old_pak_sha256"] or set(before) != set(after):
        raise RuntimeError("Rollback verification failed")
    if any(after[n] != before[n] for n in before if n != PAK_NAME):
        raise RuntimeError("Another package changed during rollback")
    output = BACKUP / "rollback_receipt.json"
    with output.open("x", encoding="utf-8") as file:
        json.dump({"restored_sha256": sha(target), "other_paks_unchanged": True,
                   "installer_result": result, "game_launched": False}, file, indent=2)
    print("Previous text package restored and verified")


if __name__ == "__main__":
    main()
