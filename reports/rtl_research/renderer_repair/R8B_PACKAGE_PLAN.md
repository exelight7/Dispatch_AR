# R8b package and rollback plan — future only

2026-10-25. Current artifacts: STAGE1 / OFFLINE / NOT_INSTALLABLE / NOT_RUNTIME_TESTED.
No PAK is created by the Stage-1 generator. The original game directory stays read-only.

## Future contents (only after Stage 2 and separate approval)

| Virtual content | Source/ownership |
|---|---|
| `/Game/ArabicReveal/DT_AR_Fill`, `_Fill_Large`, `_Outline`, `_Outline_Large` | Four generated tables, each .uasset + .uexp; normal 28/Large 36; 38 rows |
| `/Game/Shared/Core/Widgets/WBP_SubtitleBlock` | Future Stage-2 validated override; must retain the original English path and branch only for `ar`/`ar-` |
| Arabic game/engine `.locres` targets | Existing validated Arabic record pipeline; no pretagged subtitle translations |
| Required Arabic `.locmeta`/culture metadata | Follow the existing culture-activation analysis; verify paths and supported cultures before packaging |
| Arabic image overrides, later | Only inventoried/approved translations; separate later scope |
| Mod-owned manifest/version/ownership list | Exact filenames, hashes, labels and supported source build |

The table binaries are in `builds/rtl_poc/stage1/Dispatch/Content/ArabicReveal/`. The detached filename
`WBP_SubtitleBlock_AR_STAGE1.uasset` is a review label; its internal BPGC/package identity intentionally retains the
original name. It must **not** be packed as the final override. Stage 1 has no runtime branch and remains inert/hidden.

R8b references shipped `M_SubtitlePrinting`, `MI_SubtitlePrinting_Bold`, and horizontal/vertical blur MIs.
Do not package copies or modifications of those assets, a new material, a shader library, shader cache, EXE, DLL,
UE4SS or editor output. No new shader compilation/delivery route is needed for R8b.

## Version and preinstallation gate

Supported baseline: Dispatch project 1.0.19512, Steam build 25637711. Verify the supported EXE/source-asset hashes
recorded in `compatibility/game_build.json` and Stage-1 source evidence before any future installation; fail closed on
mismatch. This round checks only the extracted source pairs and does not repeat a large game-directory scan.
Future evidence must include Stage-2 CFG/variable/bytecode checks, package path allow-list, source hashes, culture
metadata, deterministic pack/list/readback and separate runtime acceptance. Outline propagation on 4.27 and widget
name binding remain unproven. Per-speaker RGB is an unresolved R8b limitation; do not advertise parity.

## Footprint, owned files and rollback

Proposed future package: one uniquely named mod-owned `Dispatch_AR_R8b_P.pak` under the already supported Paks
mount directory, with a manifest beside it or outside the game directory. The exact directory/priority must be verified
before installation. Keep this separate from the existing experimental text-only package; the future installer must
detect conflicts and refuse competing WBP/locres overrides. Do not install both silently.

Record the exact destination and SHA256 in an ownership receipt. Refuse to overwrite an unknown preexisting file.
Use a temporary mod-owned filename and atomically rename only after pack readback/version checks. A failed install
removes only its own newly created temporary files. It must never edit original pakchunk files or the EXE.

Uninstall/rollback: stop any future game use through the human's normal workflow, verify the ownership receipt and
hash, then delete only the exact mod-owned PAK/receipt or restore the previous **mod-owned** package backup.
No wildcards, no original-asset restoration and no deletion of save/config/cache directories. If a culture preference
was explicitly changed later, restore only the recorded setting after checking for intervening user edits. Retain the
manifest and source version record outside the game directory for reproducible rollback.

Nothing in this plan executes installation. GAME_NOT_RUN; STEAM_NOT_RUN; PACKAGE_NOT_INSTALLED;
DISPATCH_INTEGRATION_PROVEN=false; IN_GAME_RTL_PROVEN=false; tested_in_game=0; final=0.
