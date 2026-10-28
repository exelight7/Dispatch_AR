# Font analysis

105 bundled font-face files were extracted and inspected: 91 `.ufont` files that contain standard font data and 14 `.ttf` files. Full per-file cmap, OpenType table/script and metric results: `reports/font_coverage.json`. Reproduce with `python scripts/analyze_fonts.py`.

Arabic cmap coverage is present in:

- `Dispatch/Content/Shared/Shifts/Art/Fonts/Aktiv_Grotesk.ufont`: Aktiv Grotesk Regular 6.000; 212 Arabic codepoints, 262 presentation forms; GSUB and GPOS; units/em 1000, ascent 997, descent -283.
- `Engine/Content/Slate/Fonts/NotoNaskhArabicUI-Regular.ttf`: 253 Arabic codepoints, 752 presentation forms; GSUB and GPOS; units/em 2048, ascent 2189, descent -600.

Default subtitle styles reference the Montserrat-Variable runtime composite font, with sizes 28/36 and typefaces Medium/Medium Italic. Its composite includes multiple script-specific fonts; the presence of a separate Arabic fallback face does not prove that this exact widget selects it correctly. See `reports/rtl_research/ASSET_INSPECTION.md` for actual references.

## Round 017: actual chain (runtime symptom explained)

The isolation run showed that, with Texts pak + `-culture=ar` and no R8b, Arabic letters are invisible while punctuation renders. The cause is that no font reachable by player UI has an Arabic glyph:

- The player-facing UI uses three runtime composites: `Montserrat-Variable` (subtitles, main menu, settings items, pause, dialogue choices via `WBP_RichText` → `DT_RichTextStyles`), `Rajdhani-Variable` (settings tabs, shift UI, shift choices, `TS_Shift_*`) and `Orbitron-Variable` (menu and settings headers, save menu). The scan covered all 27,365 packages: `reports/rtl_research/font_017/font_usage_017.json`.
- Each composite has a Latin default typeface and a **NotoSansCJK** fallback typeface (not Noto Sans as round 006 stated). Its sub-fonts cover CJK (zh-Hans), Thai, Bengali, Greek, Devanagari and Cyrillic. **None of them has an Arabic range.**
- Corpus Arabic coverage (46 code points) is 0/46 for every face in those chains: Montserrat, Orbitron, Rajdhani, NotoSansCJK, NotoSans, NotoSansThai, Tomorrow, Roboto, and the engine's DroidSansFallback. See `reports/rtl_research/font_017/cmap_chain_017.json`.
- The engine fallback is not reached:
  - The 4.27 EXE has no localized-fallback (`FallbackFont`) text key.
  - The last-resort face is `SlateDebug/Fonts/LastResort.ttf`, which is not in any pak.
  - The EXE references `NotoNaskhArabicUI-Regular.ttf` only inside the legacy default-font table, which UMG widgets with a `FontObject` never use.
- Result: composite lookup picks the default face, then the CJK fallback face, which has glyph index 0. With no last-resort face the glyph is dropped. Punctuation (`. , ! ? « »`) exists in the Latin or CJK faces, so it still renders.

Repair route (detached prototype `builds/rtl_poc/font_fix_017/`, static only): append one Arabic sub-typeface to each of the three composites. Its ranges are U+0600–06FF, 0750–077F, 08A0–08FF, FB50–FDFF and FE70–FEFF. It is a cooked `FFontData` that names the shipped `../../../Engine/Content/Slate/Fonts/NotoNaskhArabicUI-Regular.ttf` (46/46 corpus coverage, OFL), so it adds no new font file or asset. The English default and fallback typefaces are unchanged. Not installed and not runtime-tested.

No original font was replaced, no commercial bundled font is redistributed by the new text PAK, and no new font download was required. Existing Arabic cmap/GSUB/GPOS data is promising, but cannot prove joining, actual fallback choice, mark placement or clipping in the game.

## Round 018: packaged and installed; runtime pending

`builds/rtl_poc/font_runtime_018/Dispatch_AR_Fonts_P.pak` now overrides only the three composite packages at their exact original paths (3 uasset + 3 uexp). SHA256: `b8b22bcb0d6f4fd31963a2743c12c822273cc54cc983947e7a0997bda07db19f`; 62,412 bytes, V11, mount `../../../`. Two builds are byte-identical, both extracted payloads match the round-017 prototype, and the existing validator passes on the prototype and extracted data. English DefaultTypeface, fallback, original sub-fonts, imports and NameMap remain exactly unchanged.

The Fonts pak was installed with a verified temporary copy and atomic rename after supported-game hash checks and a hash-verified Config/SaveGames backup. Run 4 is Texts + Fonts + `-culture=ar`, with R8b and Locmeta absent. Dispatch has not been launched in this session. Arabic UI/subtitle screenshots, stability and the subsequent English regression are pending operator evidence; `ARABIC_GLYPH_RENDERING_PROVEN=false`, `IN_GAME_RTL_PROVEN=false`, `final=0`. Procedure and installation evidence: `builds/rtl_poc/font_runtime_018/RUN4_READY.md`.

Required visual checks remain: baseline/line height, ascenders/descenders, glyph padding, Arabic marks, ي ج ح خ م ع غ, multiline wrapping and large subtitle styles. No visual pass is recorded.
