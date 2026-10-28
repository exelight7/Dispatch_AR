# Arabic image production queue (round 008, static)

Machine-readable: `image_queue.json` (180 entries, generated from `image_localization.json` and the pak indexes). No image was redrawn.

| Priority | Group | Count | Format / size | Replacement mechanism | Notes |
|---|---|---:|---|---|---|
| P1 | Chaotic censor overlay "RESTRICTED / Please contact your supervisor" | 2 | DXT5, 1024² (POT) | NORMAL_COOKED_TEXTURE (same format and dims) | In the `MediaPlayer` folder: material dependency UNKNOWN (referencers not inspected). Visible in normal play when Chaotic censorship is chosen |
| P2 | Hero-database dossier stills "[UNAVAILABLE]" | 8 | BC7, 2560×1080 (non-POT) | SPECIAL_COMPRESSION (BC7 encode) | Visible in normal play |
| P3 | Tutorial screenshots with English UI | 3 | DXT1, 1920×1080 | NORMAL_COOKED_TEXTURE | Usage unverified ("TutorialTempImages"); needs a re-shoot with Arabic UI, so it depends on in-game work |
| P4 | Deluxe comic pages/covers | 61 | 59 DXT1, 1 DXT5, 1 BGRA8; up to 4124×6300 | NORMAL_COOKED_TEXTURE, NON_POT, LARGE | Extras only; re-lettering |
| P5 | Deluxe artbook pages | 106 | DXT1; up to 6668×3752 | NORMAL_COOKED_TEXTURE, NON_POT, LARGE | Extras only |

Common facts:
- **Mip storage:** no `.ubulk` exists for any of the 180, so mips are stored inline in `.uexp` and none is a streamed-bulk case.
- **Atlases:** no atlas was identified.
- **Writer:** every entry needs a 4.27-compatible cooked-texture writer, either a 4.27 cooker or a validated UAssetAPI-level texture injector. Neither exists in this project: NOT_PROVEN.
- **Delivery:** an `L10N/ar` copy needs the AssetRegistry change described in `reports/arabic_activation/L10N_AR.md`. An original-path override would change English too.

Order of work: P1 first (2 small DXT5 files; check referencers), then P2.
