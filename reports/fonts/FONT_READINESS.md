# Arabic font readiness — static (round 006)

> **Round 017 correction (runtime-contradicted):** the fallback typeface of `Montserrat-Variable` is NotoSansCJK, not Noto Sans. Arabic code points do **not** reach a global Slate fallback in this 4.27 build: there is no localized-fallback key, and `SlateDebug/Fonts/LastResort.ttf` is not shipped. The "proposed chain" below therefore did not exist at runtime, which is why Arabic letters were invisible in the isolation run. See `docs/FONT_ANALYSIS.md` (round 017) and `builds/rtl_poc/font_fix_017/`.

Harness: `python -X utf8 tools/font_analysis/coverage.py` (installed fontTools 4.65 + uharfbuzz 0.56, extracted font
copies only). Output: `font_coverage.json`. Nothing here is an in-game or Slate result.

## Font structure used by subtitles

`/Game/Shared/UI/Fonts/Montserrat-Variable` is a Runtime **CompositeFont** (UAssetAPI export):

- Default typeface: 18 Montserrat faces (Medium / Medium Italic are used by the subtitle rows).
- Fallback typeface: Noto Sans faces.
- Sub-typefaces by character range: CJK (culture `zh-Hans`), Thai U+0E00–0E7F, Bengali U+0980–09FF, Greek U+0370–03FF,
  Devanagari U+0900–097F, Cyrillic ranges.
- **No Arabic range and no Arabic face.**

Arabic code points therefore reach Slate's global composite fallback. The shipping EXE references
`CompositeFallbackFont` and `NotoNaskhArabicUI-Regular.ttf`, and that file ships at
`Engine/Content/Slate/Fonts/` (CONFIRMED_FROM_BINARY / ASSET). That the fallback is selected for these runs is
ENGINE_SOURCE_RECALL — **NOT_PROVEN** in game.

Proposed final chain (no new asset, no cook): Montserrat Medium → Noto Sans Medium → engine fallback Noto Naskh Arabic UI
Regular. Alternative chain for the shift UI: `Aktiv_Grotesk` has its own Arabic (212 Arabic code points, GSUB/GPOS
`arab`) and covers every code point of the corpus.

## Coverage

| Face | Arabic Basic | Supplement | Ext-A | PF-A | PF-B | Latin (95) | Corpus code points missing |
|---|---:|---:|---:|---:|---:|---:|---:|
| Montserrat Medium | 0 | 0 | 0 | 0 | 0 | 95 | 52 (all Arabic) |
| Noto Sans Medium | 0 | 0 | 0 | 0 | 1 | 95 | 46 |
| **Noto Naskh Arabic UI** | 253 | 48 | 39 | 611 | 141 | 15 | 87 (all Latin/punctuation, covered by Montserrat) |
| Aktiv Grotesk | 212 | 30 | 2 | 136 | 126 | 95 | **0** |
| Roboto Regular | 0 | 0 | 0 | 0 | 1 | 95 | 46 |

The corpus (all 12,973 records) uses 153 distinct code points, 46 of them Arabic (letters, U+0640 tatweel, the
tanween/harakat U+064B–0651, ، ؛ ؟). Required-set checks for Naskh: Arabic letters 41/41, combining marks 9/9, Arabic
punctuation 7/7, Arabic-Indic digits 10/10, Western digits 10/10.

**Missing glyphs for the proposed chain: 0.** Presentation-form code points in the translated text: **0** (logical
Unicode only; presentation forms exist in the font for its own GSUB, which is correct).

## Shaping

All 66,632 Arabic runs of the corpus were shaped with HarfBuzz on Noto Naskh Arabic UI: **0 `.notdef` glyphs**; the
lam-alef probe shapes to a single ligature glyph. Joining, marks and lam-alef are supported by the face (GSUB/GPOS
`arab`). Slate's own run splitting and shaping are not exercised here.

## Static clipping risk

Slate size in points at 96 DPI. Ink = highest/lowest shaped Arabic outline in the corpus including mark offsets
(top 2,344 / bottom −555 font units, UPEM 2048); outline rows add 2 px.

| Style | px | Montserrat ascent | Naskh ascent | Arabic ink top | Over line box (top) | Over line box (bottom) | Class |
|---|---:|---:|---:|---:|---:|---:|---|
| Default 28 | 37.3 | 36.1 | 39.9 | 42.7 | +2.8 | −0.8 | STATIC_RISK_FOUND |
| Default_Outline 28 | 37.3 | 36.1 | 39.9 | 44.7 | +4.8 | +1.2 | STATIC_RISK_FOUND |
| _Large table 32 | 42.7 | 41.3 | 45.6 | 48.8 | +3.2 | −0.9 | STATIC_RISK_FOUND |
| _Large table outline 32 | 42.7 | 41.3 | 45.6 | 50.8 | +5.2 | +1.1 | STATIC_RISK_FOUND |
| Default_Large 36 | 48.0 | 46.5 | 51.3 | 54.9 | +3.6 | −1.1 | STATIC_RISK_FOUND |
| Default_Outline_Large 36 | 48.0 | 46.5 | 51.3 | 56.9 | +5.6 | +1.0 | STATIC_RISK_FOUND |

Stacked marks (e.g. shadda + fatha on tall letters) rise ~3–6 px above the larger (Naskh) ascent; the subtitle text
widgets have 2 px margins and sit inside RetainerBoxes. Whether Slate grows the line height for the fallback face and
whether the retainer clips is **IN_GAME_REQUIRED**. Mitigations available without code: avoid stacked tashkeel in
subtitles (already rare: the corpus uses harakat sparingly), or add vertical margin in the Arabic branch layout.

## Other limits

- No Arabic italic: Italic subtitle rows (Medium Italic) will show upright Naskh; Slate does not synthesize italics.
- Weight mismatch: Naskh Regular next to Montserrat Medium.
- Atlas padding, distance-field fonts and font materials (M_SubtitlePrinting / the proposed reveal material) are not
  modelled.
