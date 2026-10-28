# Text-bearing images (round 006)

Machine-readable: `image_localization.json`; raw evidence in `evidence/texture_probe_*.json`.

## Method

All 995 `Dispatch/**/T_*` textures were copied out of the paks to a temporary folder and decoded with the installed
`texture2ddecoder` (BC1/BC3/BC4/BC7/BGRA8/G8, largest present mip) — `tools/coverage/texture_probe.py`. OCR (installed
RapidOCR) ran on the 835 non-extras textures and on a 16-page sample of the Deluxe extras; no OCR over videos or other
assets. Path rules + OCR + spot visual checks (contact sheets of menu art, dossier, crime art, censor overlays) assign the
class. Thumbnails stayed in the temporary folder and are not distributed. **No replacement image exists**: nothing is
claimed translated.

## Summary

| Class | Textures |
|---|---:|
| NO_TEXT (OCR-negative; not every image inspected by eye) | 466 |
| LANGUAGE_NEUTRAL (key legends, logos, product box/album art, diegetic signage, signatures) | 332 |
| NEEDS_ARABIC | 180 |
| NOT_RUNTIME (sandbox/debug/placeholder/render targets) | 14 |
| UNREADABLE (render-target assets without pixel data) | 3 |
| ALREADY_LOCALIZED | 0 |

The game localizes **no** image for any of its 16 non-English cultures (only `/Game/L10N/en/FMOD` audio exists).

## NEEDS_ARABIC detail

| Group | Count | Example asset | Size / format | Screen | Difficulty | Priority |
|---|---:|---|---|---|---|---|
| Chaotic censor overlay "RESTRICTED / Please contact your supervisor" | 2 | `AdHocPlugin/Story/MediaPlayer/ChaoticCensorTextures/T_ChaoticCensor_SDN-Restricted_01` | 1024² BC | Chaotic censorship mode during cinematics | LOW (flat UI art) | MEDIUM |
| Dossier still "[UNAVAILABLE]" | 8 | `Shared/Shifts/Art/UI/T_UI/Heroes/Dossier_StillFrame/T_UI_Dossier_Still_*` | 2560×1080 | Hero database before reveal | MEDIUM | LOW |
| Tutorial screenshots with English UI (`TutorialTempImages`) | 3 | `T_UI_TutorialTemp_Dispatch` | 1920×1080 | Tutorial popups (usage unverified; "Temp") | HIGH (re-shoot in Arabic UI) | LOW |
| Deluxe comic pages/covers (lettering) | 61 | `DispatchEp102/Extras/Comic/Splash/T_01a_Splash_Pg01_Master` | 4124×6300 DXT1 | Extras → Comic Books | VERY_HIGH (re-lettering) | LOW |
| Deluxe artbook pages (annotations; sampled) | 106 | `DispatchSpecialEditionUncensored/T_DispatchArtBook-Ch4-9-UNCENSORED` | up to 6668×3752 | Extras → Art of Dispatch | VERY_HIGH | LOW |

Delivery of any replacement image as `L10N/ar` needs the AssetRegistry change described in
`reports/arabic_activation/L10N_AR.md`; an original-path override would change English too.
