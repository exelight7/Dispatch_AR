# Video localization audit (round 006)

Status: STATIC_PASS for the inventory and classification. Nothing here is IN_GAME_PASS: no movie was played in the game.

Data: `reports/coverage/video_localization.json` (one row per movie). Evidence: `reports/coverage/evidence/video_probe_sample.json`.
Tools: `tools/coverage/video_probe.py` (streams + sampled-frame OCR), `tools/coverage/build_coverage_reports.py` (classification).

## Method

- Inventory: every `.webm`/`.mp4` path in `reports/all_asset_paths.json` (from the earlier pak listing): **3,436 movies** (3,435 VP9 WebM, 1 MP4 test clip).
- Sample: 32 movies were copied out of temporary extractions into `%TEMP%` (never read in place, never written back):
  all 15 credits movies, menu backdrops, the startup sting, the FTUE QTE clip, a ChoiceStats clip and cutscene shots from episodes 101 to 108 (including `_SB` and `_MA` variants).
- For each sampled movie: ffmpeg (bundled with imageio-ffmpeg) listed the streams; one frame every 6 s was extracted and OCR'd with RapidOCR.
- No movie was transcoded, re-encoded or replaced.

## Results

| Class | Movies | Meaning |
|---|---:|---|
| NO_BURNED_TEXT | 14 | sampled cutscene/menu clip: no subtitle stream, OCR found no text |
| NO_BURNED_TEXT_INFERRED | 3,385 | not sampled; cutscene shots from the same pipeline and folders as the sampled ones |
| BURNED_IN_TEXT | 15 | end credits (`10x_Credits`, `Credits_108_A`–`H`): English role titles and names burned into the frames |
| LANGUAGE_NEUTRAL | 14 | startup logo sting (4) and main-menu backdrops (10). The only OCR hits are in-world signage such as "OBSIDIAN INK" |
| NOT_RUNTIME | 8 | `AVSyncTest`, `TestClips`, `AudioGapTest` engineering clips |

- Subtitle streams in the sample: **0 of 32**. The game draws dialogue subtitles as UMG text from localized FText (the episode `Line` records). The Arabic subtitles therefore come from the `ar` locres that is already built, and they hit the same RTL rendering limit as all other UI text (`docs/KNOWN_ISSUES.md`).
- Audio stays English. No dubbing was attempted, and none is in scope.

## What would need Arabic

| Item | Difficulty | Priority | Recommendation |
|---|---|---|---|
| 15 credits movies (≈8–9 min each) | HIGH: the credits would have to be re-rendered from source or overlaid frame by frame; names are proper nouns | LOW | Keep them in English. Credits are usually left untranslated, and changing them carries legal and attribution risk |

No replacement movie exists in the project (`replacement_assets_present: 0`). The current package ships no movies.

## Limits

- 3,385 cutscene movies are classified by inference, not by OCR. A full OCR pass is feasible offline (about 3,400 movies × 1 frame / 6 s) but costly. The sample found no burned-in text in any cutscene.
- OCR only sees Latin text, and it can miss stylised or small lettering. Spot visual checks were made only on credits and menu frames.
