# Package layout

## Current experimental package (exists)

`builds/Dispatch_AR_Texts_EXPERIMENTAL.zip` — labels `STATIC / EXPERIMENTAL / NOT_INSTALL_TESTED / NO_RTL_FIX`
(in `manifest.json` and the first lines of `README_AR.txt`). Deterministic: fixed ZIP entry timestamps (1980-01-01),
fixed attributes, single-threaded repak (`RAYON_NUM_THREADS=1`).

```
Dispatch_AR_Texts_EXPERIMENTAL.zip
├── Dispatch_AR_Texts_P.pak          # 14 ar locres only, mount ../../../, uncompressed, unencrypted, V11
├── manifest.json                    # kind, labels, versions, payload hashes, validation, runtime state
├── README_AR.txt                    # Arabic notes + install/uninstall commands
├── scripts/install.py               # checked installer (dry run, compatibility refusal, scoped uninstall)
├── docs/INSTALL.md
└── compatibility/game_build.json    # supported build: 1.0.19512 / Steam 25637711 (hashes, sizes; no secrets)
```

PAK content (all additive culture `ar`; no English or original asset path):

```
Dispatch/Content/Localization/{101..108,OtherContent,Shared}/ar/<target>.locres
Engine/Content/Localization/Engine/ar/Engine.locres                      # sparse: 464 identities
Engine/Plugins/Online/OnlineSubsystem{,Steam,Utils}/Content/Localization/<target>/ar/<target>.locres
```

## Intended final distribution (not built; not a release)

```
Dispatch_Arabic_<version>.zip
├── README_AR.md / README_EN.md      # what it is, requirements, known issues, how to select Arabic
├── INSTALL.md / UNINSTALL.md
├── CHANGELOG.md
├── KNOWN_ISSUES.md
├── CREDITS.md                       # translators/reviewers, tools (repak, UAssetAPI, HarfBuzz, fontTools)
├── LICENSES/                        # third-party notices for anything redistributed (nothing of the game)
├── compatibility/game_build.json
├── manifest.json                    # file list + SHA256 of every member
├── SHA256SUMS.txt
├── install.py
└── paks/
    └── Dispatch_AR_P.pak            # text locres + (if gates pass) Arabic reveal assets + WBP_SubtitleBlock + locmeta overrides
```

Rules: no AES key, no original game file or extracted asset, no EXE/DLL, no reports or source dumps, no absolute local
paths, no temporary files; every member listed with SHA256 in `manifest.json`. Enforced by `scripts/verify_project.py`
(package audit section).
