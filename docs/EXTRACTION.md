# Extraction

Original game packages are read-only. `scripts/investigate.py`:

1. Checks the observed v11 footer and bounds.
2. Finds immediate-store key candidates in the installed executable; accepts only a complete AES-decrypted-index SHA1 match.
3. Rechecks all 20 index digests.
4. Runs verified repak to inventory all virtual paths.
5. Optionally extracts English localization/source companions, configuration, plugin descriptors, font faces/objects and selected shared UI assets into `extracted/`.
6. Records extracted byte sizes, SHA256 and source PAK paths.

```powershell
python scripts/investigate.py inventory
python scripts/investigate.py extract
python scripts/localization.py export
```

`extracted/` is an unchanged source baseline, never the patch staging area. Original archives remain in the game installation. New PAKs are built separately.

The original installation fingerprint is in `backups/original_game_sha256.json` (97 original files). To recheck:

```powershell
python scripts/investigate.py verify
```

repak 0.2.3 was downloaded from [its official release](https://github.com/trumank/repak/releases/tag/v0.2.3). Verified release ZIP SHA256: `6720d602144d75df477a99d5bedb6ea780997546afc335901d4937cafeaa73fa`. Tool licenses are preserved under `tools/repak-v0.2.3/`.

No whole-game decrypt/repack or original-file overwrite is required for the text package. No signed-package enforcement or Arabic-culture activation has been verified inside the running game.
