# Release plan (no release has been made)

Current state: experimental text package only. `tested_in_game=0`, `final=0`. The steps below are the path to a
first public Arabic release; each step names its gate and evidence. Nothing here is complete unless marked.

| Step | Content | Gate / evidence | Status |
|---|---|---|---|
| 1 | Text resources (12,973 records) | `scripts/validate_translation.py`, `tools/translation_qa/qa.py`, build determinism | STATIC_PASS / BUILD_PASS / ROUNDTRIP_PASS |
| 2 | Literary review of all Arabic records | `translation/review/review_log.json` covers 12,487 records | PARTIAL (see progress.json `reviewed`) |
| 3 | Culture activation without the menu (`-culture=ar` + locmeta) | runtime observation | NOT_PROVEN (needs game) |
| 4 | Font chain and clipping | in-game screenshots at 28/32/36 pt, outline on/off | NOT_PROVEN |
| 5 | Stock-renderer reveal G1–G3 | UE4.27 editor tests (`NEXT_INTEGRATION_CHECKLIST.md`) | NOT_PROVEN (editor missing) |
| 6 | Cook and deliver Arabic reveal assets (G4) | cook log + shader library evidence | NOT_PROVEN |
| 7 | WBP_SubtitleBlock Arabic branch (G5) | `WBP_PATCH_PLAN.md`, editor PIE then game | NOT_PROVEN |
| 8 | In-game acceptance suite (`docs/TESTING.md` runtime list) | screenshots/video in `tests/screenshots/` | NOT_RUN |
| 9 | English regression | same scenes in `en`, compared with baseline | NOT_RUN |
| 10 | Package + checksums + docs (`PACKAGE_LAYOUT.md`) | `scripts/verify_project.py` package audit | layout defined; final package not built |
| 11 | Release notes: version compatibility 1.0.19512 / 25637711 only | `compatibility/game_build.json` | metadata ready |

## Release contents (when allowed)

README (Arabic + English), install / uninstall instructions (`install.py --dry-run` first), compatibility statement
(single verified build; installer refuses others), known issues (from `docs/KNOWN_ISSUES.md`), credits, third-party
license notices (only for redistributed tools/fonts — none of the game's), `manifest.json` + `SHA256SUMS.txt`.

## Must not happen

Renaming the experimental ZIP to final; claiming RTL reveal without in-game evidence; shipping English overrides;
shipping any game asset, AES key or EXE patch.
