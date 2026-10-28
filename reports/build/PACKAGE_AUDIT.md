# Package audit (round 006)

Status: **STATIC_PASS**. The package has never been installed, and the game was not run, so nothing here is INSTALL_PASS or IN_GAME_PASS.
Machine check: `python -X utf8 scripts/verify_project.py` → `reports/STATIC_VERIFICATION.json` (package checks section).

## Artefact

| Item | Value |
|---|---|
| Archive | `builds/Dispatch_AR_Texts_EXPERIMENTAL.zip` |
| Archive SHA-256 | `190497af4a35e407a5a879103bf965d1c32594a78ce3085a4d39258ea5917aba` |
| Pak | `Dispatch_AR_Texts_P.pak` (1,463,653 bytes) |
| Pak SHA-256 | `0fa5792af8a7c63ef132d47e765c0aeb64fca1f9c6fe0bfc84ddefcd65b97235` |
| manifest.json SHA-256 | `fb3f346d09cd23c476a26893834422d3510a7562c9055a4cdac7fafefcd90aa2` |
| README_AR.txt SHA-256 | `8135651e09c71a1f8edee8a8b527062ab53403f39a343379f707ffeb60ad3a9a` |
| Labels (manifest, README, archive name) | STATIC, EXPERIMENTAL, NOT_INSTALL_TESTED, NO_RTL_FIX |
| Target game | Dispatch 1.0.19512, Steam build 25637711, EXE SHA-256 `365637a7…4ac14923` (`compatibility/game_build.json`) |
| Strings | 12,973 in 14 `ar` locres targets (101–108, EngineRuntime, OnlineSubsystem, OnlineSubsystemSteam, OnlineSubsystemUtils, OtherContent, Shared) |

The previous package (zip `bcbcc5a1…`, pak `3155fa9e…`) is preserved in `backups/session_006/builds/`. It was not renamed or promoted.

## Archive members (allow-list)

| Member | Purpose |
|---|---|
| `Dispatch_AR_Texts_P.pak` | additive pak; holds only `Dispatch/Content/Localization/*/ar/*.locres` |
| `manifest.json` | hashes, labels, per-target counts, compatibility hash |
| `README_AR.txt` | Arabic/English notice with labels and `--game-root` commands |
| `scripts/install.py` | installer: refuses on an EXE hash or pak size mismatch, has `--dry-run`, keeps an uninstall state |
| `docs/INSTALL.md` | install/uninstall instructions |
| `compatibility/game_build.json` | identity of the build the package was made for (no secrets) |

Every ZIP entry carries the fixed timestamp 1980-01-01 00:00:00.

## Exclusion checks

| Check | Result |
|---|---|
| AES key (raw, hex, upper-hex and UTF-16 forms), `tools/local_aes_key.txt` | not present (the key itself is never printed) |
| Original game paks, EXE, `.sig`, `.utoc/.ucas` | not present |
| Extracted English assets or source dumps | not present (the pak holds only `ar` locres; no English resource is overridden, `english_resources_overridden: false`) |
| Developer reports, temp files | not present |
| Absolute local paths (`<drive>:\Users`, `filessss`, `SteamLibrary`) | not present in any member |
| Hard-coded game path in the installer | removed; `--game-root` is required |

## Reproducibility

Two independent builds into separate scratch folders produced byte-identical outputs: ZIP `190497af…`, pak `0fa5792a…`, README `8135651e…` and manifest `fb3f346d…`. A third build into `builds/` matched both.
The pak is packed with repak V11 with `RAYON_NUM_THREADS=1`, mount point `../../../`. Locres compile → decode → recompile round-trips byte-for-byte for every target.

## What this audit cannot show

- That the game mounts the pak, or that it selects the `ar` culture. The culture is not in the EXE language list; launching with `-culture=ar` is the minimum route, and the menu entry would need an EXE change, which is out of scope.
- That Arabic renders right-to-left. It will not: `NO_RTL_FIX`, see `docs/KNOWN_ISSUES.md`.
- Install or uninstall behaviour on the real installation. Only the installer selftest ran, on a temporary fake game root.
