# Build

```powershell
python scripts/verify_project.py          # aggregate static checks -> reports/STATIC_VERIFICATION.json
python scripts/localization.py selftest
python scripts/validate_translation.py --selftest
python scripts/install.py --selftest
python scripts/validate_translation.py
python scripts/build.py
```

Pipeline: extract baseline -> export runtime identities/context -> translate -> validate -> compile native locres -> deterministic v11 PAK -> read back every PAK byte -> optional install -> future runtime testing.

The compiler preserves original namespace/key serialization and source hashes. Different dialogue translations may get distinct string-pool entries even when English was shared. It verifies counts, string references, identity/hash preservation and idempotent compilation. Unchanged English resource roundtrips were byte-identical for the 10 project resources; plugin v1 resources are checked separately in `reports/text_sources.json`.

The build only adds `ar/<target>.locres` under each original project/engine-plugin localization mount path, plus a sparse Engine/ar/Engine.locres with 460 explicitly selected identities from `translation/engine_scope.json`. The unselected Engine catalogue is not copied as English fallback into this resource. No English resources, timing assets, original fonts, Blueprint prototype, executable or AES key is included.

repak's parallel writer produced different physical payload ordering during the initial full build. The pipeline now sets RAYON_NUM_THREADS=1 for its pack subprocesses, then verifies two byte-identical PAK outputs. This is local to the build command and changes no system setting.

The build refuses missing/invalid authoring. It packs twice and compares bytes, unpacks into a temporary workspace and compares all members with the staged files. Output: `builds/arabic_texts_experimental/` plus `builds/Dispatch_AR_Texts_EXPERIMENTAL.zip`.

The build manifest explicitly records experimental status, game version, all payload hashes, validation results, unresolved native RTL reveal and absence of runtime testing. Successful data compilation is not production readiness.

For three single-key data probes only: `python scripts/build.py --poc`. Results: `reports/poc_data_checks.json`. These probes were not installed or run.

## Round 006 changes

- `python scripts/build.py --output-root <dir>` builds into a detached folder; used to build twice and compare (identical PAK, manifest, README and ZIP SHA256; unpacked contents identical).
- ZIP entries use a fixed 1980-01-01 timestamp and fixed attributes, so the archive itself is deterministic. repak still runs with `RAYON_NUM_THREADS=1` (set inside `pack_verified`, no system change).
- The manifest carries `labels: STATIC, EXPERIMENTAL, NOT_INSTALL_TESTED, NO_RTL_FIX` and the hash of `compatibility/game_build.json`, which is shipped inside the ZIP for the installer.
- Engine scope is 464 identities (4 RUNTIME_CONFIRMED records added from `reports/coverage/engine_classification.json`).
- Package audit (members allow-list, AES absence, absolute paths, labels, pak hash, pak contents) runs in `scripts/verify_project.py`; report `reports/build/PACKAGE_AUDIT.md`.
