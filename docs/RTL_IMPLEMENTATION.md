# RTL implementation — native reveal unresolved

## Round 019 — R8B_REPAIR_READY (offline; not installed, not run)

Run 2's frame bug is repaired. `Build Arabic Timing` is now a void helper:
- ReturnValue FStrProperty removed, FUNC_HasOutParms cleared, `Return Local(Output)` replaced by `Return Nothing`.
- Before → after: PropertiesSize 216→200, ParmsSize 48→32, ReturnValueOffset 32→MAX_uint16.
- The only call (Set Displayed Line:66, a bare statement) consumed nothing, so semantics are unchanged: the delay ledger
  equals the canonical segmenter on 96 fixtures.

Build and validation:
- Rebuilt from clean source (011 → repair → 012 clock generator). Byte-identical to the repair applied to the frozen 012
  pair; deterministic; roundtrip-exact.
- 72/73 exports byte-identical to the installed 014 build.
- New permanent return-contract validator: 1120 call sites, 0 invalid. It rejects the real Run 2 artifact at exactly
  `Set Displayed Line:66 Build Arabic Timing -> Str`. Native signatures and the K2_SetTimer trivially-stored struct come from EXE evidence.
- Clock replay: 500/500 frame-identical.

Staging pak `builds/rtl_poc/r8b_runtime_staging_019/Dispatch_AR_R8b_P.pak` (`1058eac4…f988`) is NOT installed; the Run 5
procedure is `RUN5_READY.md`.

Run 4 (operator, relayed): Arabic glyphs visible across the UI and subtitles, but stock Proto reveals left to right and
overlaps, so stock Proto is rejected. Details: `reports/rtl_research/renderer_repair/R8B_REPAIR_019.md`.
`ARABIC_GLYPH_RENDERING_PROVEN=true; ARABIC_FONT_RUNTIME_PARTIAL=true; STOCK_PROTO_RTL_REJECTED=true; R8B_FIXED=true; IN_GAME_RTL_PROVEN=false; final=0`.


## Round 011 latest: detached reveal control generated, clock unbound

`R8B_WBP_STAGE2_REVEAL_PARTIAL`: twelve helpers implement the unit delay ledger, Step, idempotent Finish, skip,
generation-safe cancellation/pooling and live outline/size/wrap. Nineteen offline lifecycle cases and six negative
cases pass; all79 frozen inputs remain unchanged. No engine timer/tick adapter is connected. Pause equivalence
and completion cadence remain unproven. Next blocker: certify the native+0x86c accumulator driver and bind the
equivalent clock/dispatch adapter. Evidence: `reports/rtl_research/renderer_repair/WBP_REVEAL_RESULT_011.md`
and `SCHEDULER_TIMING_011.md`. NOT_INSTALLABLE/NOT_RUNTIME_TESTED; tested_in_game=0; final=0.

## Round 010: Arabic initialization generated offline

`R8B_WBP_STAGE2_PASS` for the authorized initialization subset: language gate, full word-unit markup, styles,
hidden threshold reset, SetText once per Arabic layer and cleanup. Nineteen untouched functions remain byte-identical;
Set Displayed Line and Stop Displaying Line intentionally change. See `reports/rtl_research/renderer_repair/WBP_STAGE2_RESULT.md`.
Timer/step/finish are absent; NOT_INSTALLABLE / NOT_RUNTIME_TESTED; tested_in_game=0; final=0.

# Round 009: detached R8b structure implemented

Current offline result: `R8B_WBP_STAGE1_PASS`. Four tables and a seven-widget Arabic layer now exist in
`builds/rtl_poc/stage1/`, with strict UAssetAPI validation, deterministic binary output and original bytecode hashes.
The layer is Collapsed by default; no runtime text/timer/language branches are implemented. Named widget CDO defaults
are null as in the original class; engine name binding remains untested. No installation occurred.
Details: `reports/rtl_research/renderer_repair/WBP_STAGE1_RESULT.md`; next implementation:
`WBP_STAGE2_BYTECODE_MAP.md`. `IN_GAME_RTL_PROVEN=false; tested_in_game=0; final=0`.

---

## Observed original implementation

The shared subtitle block has foreground and shadow ProtoRichTextBlock objects, centered justification, wrapping at 1050, and 2-unit margins. Blueprint formats speaker names and `<text ...>` markup, assigns the complete processed subtitle and invokes native PrintLetterByLetter or ShowText. Per-letter events update shadow retainers and completion delegates. This is a shared route across subtitle lines.

## Confirmed engine capabilities and remaining gap

Slate supports bidirectional shaping; Unreal uses ICU for culture/boundary/BiDi work. Arabic should remain in logical Unicode order, use native full shaping, RTL paragraph flow, a stable right-side layout and appropriate fallback fonts. [Epic's localization overview](https://dev.epicgames.com/documentation/unreal-engine/localization-overview?application_version=4.27) describes ICU support.

The [ProtoAnimatedText author's known issues](https://protowlf.com/protoanimatedtext/knownissues/) state that Arabic/RTL letter printing is unsupported. The shipped plugin is 1.02; the local shared call path is independently decoded. Its decorators pack animation data into glyph vertex colors. A right-alignment setting or material mask alone does not establish correct shaping clusters or logical-to-visual reveal order.

No cluster-safe native renderer replacement has been implemented. Therefore **RTL progressive reveal is unresolved**, not passed or merely assumed to work.

## Detached experiment

An isolated UAssetAPI prototype changes three subtitle OverlaySlots from Center to Fill and both text objects to Right justification with FullShaping/RightToLeft overrides. It reparses and preserves the other 32 export payloads, including Blueprint bytecode. It leaves the original native reveal unchanged. It is excluded from distribution because it would affect English and does not solve the reveal requirement.

Cooked Blueprints cannot be made culture-scoped simply by copying them under L10N/ar; [Epic explicitly excludes bytecode assets from asset localization](https://dev.epicgames.com/documentation/unreal-engine/asset-localization?application_version=4.27). Culture-specific Font/DataTable candidates do not by themselves fix anchoring/reveal.

## Required shared renderer behavior

- Retain complete text and final wrapped layout throughout reveal.
- Map logical Unicode graphemes to native shaped glyph clusters; lam-alef and combining marks must remain indivisible where shaping merges them.
- Reveal clusters/words in reading order, retaining the right anchor. Never reverse characters, glyph strings, English or numbers.
- Preserve BiDi within English/number runs and punctuation. A single screen-space right-to-left rectangle is insufficient for arbitrary mixed runs and multiple lines.
- Keep original voice/line/slice timing and events, foreground/shadow consistency, skip/finish behavior and original English behavior.
- Compare character and whole-word modes in the actual game; use whole-word reveal if it avoids join/mark/layout instability.

This is an implementation specification, **not working game code**. Native source access or a verified runtime extension is still needed. User currently prohibits launching the game, so no visual acceptance can be recorded.

## Selected control point (2026-10-23)

Evidence: Blueprint passes the complete processed text and calls native `PrintLetterByLetter`/`ShowText` (ASSET_INSPECTION.md). The [technical overview](https://protowlf.com/protoanimatedtext/technicaloverview/) says `ProtoRichTextCharColorDecorator` packs per-glyph animation data in vertex colours and sets alpha on print. The author's [public tutorial](https://protowlf.com/unreal/printing-text-in-unreal/) paints each UTF-16 index as its own `MakeShapedText` slice. It cuts each slice out of the shaped line and moves `characterOffset.X` left to right in logical order. This explains the [documented RTL limitation](https://protowlf.com/protoanimatedtext/knownissues/): joining forms survive because the whole line is shaped, but Arabic slices land in reverse order and the alef of lam-alef has no glyph of its own. The tutorial is conceptual. Shipped 1.02 source has not been seen.

Rejected routes and why:
- DataTable, material, locres or markup edits. None of them can change the glyph positions the run paints. Markup opt-out and ShowText are static fallbacks, not reveal.
- WBP override. It would also change English, and L10N/ar cannot replace bytecode assets.
- Screen-space clip. The tests show that one right-to-left rectangle cannot express logical reveal for `... 250 XP`.

Chosen point: **the decorator run's native paint**. The shared counter, timing, `OnPrintLetter`/finish delegates, shadow retainers and Blueprint stay unchanged. Only two things change:
1. Each glyph is drawn at its position in the block's final shaped, visual-order glyph sequence: accumulate `XAdvance` over `GlyphsToRender`, as stock `FSlateTextRun::OnPaint` does. It is not drawn at a logical-order pen.
2. Each glyph takes the alpha (and R/B data) of the **last code unit of its reveal unit**. A reveal unit is the set of extended grapheme clusters closed under shaping clusters. UE 4.27 exposes `SourceIndex`, `NumCharactersInGlyph` and `NumGraphemeClustersInGlyph` per [FShapedGlyphEntry](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/SlateCore/Fonts/FShapedGlyphEntry?application_version=4.27).

The per-UTF-16 counter is untouched, so total duration, event count, skip/finish and English (gated on culture `ar`) are unchanged.

## Reference model: `tools/rtl_reveal/` (offline oracle, not game code)

`reveal.py` uses the extracted Montserrat-Medium plus the engine's NotoNaskhArabicUI fallback and HarfBuzz shaping. BiDi comes from the full UBA in python-bidi 0.6.11 / unicode-bidi. The model runs: parse Proto markup (`donthide` → visible at t=0) → per-paragraph levels with RTL base → per-line run itemisation (level, font) → shaping with context → greedy wrap at 1050 → L1/L2 visual order → right anchor. It then forms reveal units (grapheme ∪ shaping cluster, or word mode) and gives each unit the due time of its last UTF-16 unit at 0.025 s. It returns `None` for any non-`ar` culture, which means the original path.

```powershell
python -X utf8 tools/rtl_reveal/test_reveal.py
python -X utf8 tools/rtl_reveal/reveal.py "<text>...</>" --json out.json --svg out.svg [--mode word]
```

The self-check covers all 9 `tests/rtl_cases.json` probes, bare and wrapped by the speaker formatter, in cluster and word mode. It checks:
- no split graphemes or shaping clusters; lam-alef = one unit and one glyph; marks stay with their base
- every frame is a subset of the final layout and frames only grow
- right anchor; wrap ≤1050; lines revealed in order
- digits and Latin in LTR order inside RTL
- original total duration; one print per unit and one finish; skip finishes once
- `en`/`fr` return no plan; foreground and shadow plans are identical

Two controls are also asserted:
- Prefix reshaping changes the newest letter's form at 7 of 12 steps.
- The tutorial's slicing model reverses Arabic but matches English.

Five injected faults are all killed: no cluster merge, per-codepoint units, no L2, per-unit timing and a double finish.

Synthetic evidence lives in `reports/rtl_research/reveal_model/` (plans, SVG and PNG frames labelled SYNTHETIC). It proves the algorithm only. It does not prove that the game's fonts, fallback, ICU line breaking or Proto 1.02 behave the same.

Model limits:
- Line breaks only after whitespace (UE uses ICU UAX#14).
- Font choice is a simplified per-codepoint fallback.
- `donthide` timing exclusion is assumed.
- Python indices are codepoints; native code uses UTF-16 `SourceIndex`.

## Blocker for in-game implementation

1. **No renderer repair has been integrated.** Round 002 recovered and classified the shipped paint loop from the binary. Licensed ProtoAnimatedText 1.02 source is absent and could help implement a repair, but it is no longer required for the completed behavior classification. Its necessity for integration has not been established.
2. **A code-loading route into `Dispatch-Win64-Shipping.exe`.** The build is monolithic, with no plugin DLL, no PDB, and no UE4SS or proxy DLL installed. A rebuilt plugin cannot be dropped in. A hook (e.g. proxy DLL + vtable/AOB patch of the run's `OnPaint`) would need RE of this exact build and runtime proof of compatibility.
3. **Runtime acceptance.** Running the game is currently prohibited.

## Data probes

`tests/rtl_cases.json` contains the requested Arabic/mixed/long/diacritic/punctuation cases. `python scripts/build.py --poc` builds three alternate data-only resources using the real SettingsSubtitlePreview:TestSubtitle identity. It verifies exactly one semantic text change, logical codepoint preservation, binary readback, archive readback and deterministic packing. It does not test the live dialogue renderer or substitute for an animated PoC.

Detailed primary-source research and concrete asset inspection: `reports/rtl_research/`.

## Word-reveal timing route (round 001, historical) — WORD_REVEAL_BLOCKED

Superseded by round 002 below: timing-only word reveal is now rejected from shipped binary evidence. The following records the earlier POC and its then-unresolved questions.


Hypothesis: `PrintLetterInterval=0`, `PrintLetterAnimationTime=0`, `UseAdvancedPrintIntervals=true`, `SpaceInterval>0`, so every letter of a word is printed inside one timer callback and becomes visible in the same paint.

- Asset facts (CONFIRMED_FROM_ASSET): both Proto widgets in WBP_SubtitleBlock use `/Game/Shared/Core/Widgets/DT_SubtitlesProtoRichText` (row struct `/Script/ProtoAnimatedText.ProtoRichTextStyleRow`). `ChangeTextToLarge` swaps in `DT_SubtitlesProtoRichText_Large`. The row is picked by the markup `style="..."` from `Get Text Tag Opener`. All rows ship with letter 0.025, anim 0, advanced=false and space 0. Comma, sentence, ellipsis and dash are 0.045/0.045/0.045/0.05, or 0.3/0.5/0.2/0.05 on the `*_Outline*` rows. These punctuation values are inactive because advanced=false.
- Model (`tools/rtl_reveal/word_timing.py`, `test_word_timing.py`): 14 texts × 3 wrappers × 2 donthide models × 2 wait models. 0 partly-visible HarfBuzz shaping clusters at every frame; the shipped per-letter timing control does split clusters. Stock-position BiDi passes 42/42. **The published tutorial paint model (logical-order UTF-16 pen) fails 42/42**: timing cannot move glyphs.
- POC: `asset_inspector --word-reveal-prototype` writes detached tables under `tools/asset_inspector/prototype/word_reveal/`. The only changes are the target values, verified by a full JSON diff and byte diff, with the `.uasset` byte-identical. SpaceInterval 0.16 = 0.025 × 251,023 UTF-16 units / 39,470 spaces over 7,237 Arabic subtitle lines, which keeps the corpus's total reveal time. Punctuation waits are set to 0 because the shipped rows never apply them, and a dash/comma wait would split words. **Not installed, not distributable.**
- Arabic isolation: NOT_PROVEN. The DataTables carry no bytecode (one DataTableExport each), so the UE4.27 bytecode exclusion does not apply. The build also ships `Content/L10N/en/` packages. Unproven: whether a mod-added `L10N/ar` package is discovered (cooked FPackageLocalizationCache relies on the AssetRegistry; AssetRegistry.bin is in pakchunk0), and whether the WBP's hard import is redirected. An original-path override changes English.
- Exe strings (CONFIRMED_FROM_BINARY, names only): the 8 row field names, `PRT_NONE/SPACE/COMMA/MIDWORDDASH/ENDOFSENTENCE/ELLIPSIS`, and wide literals `donthide`, `style`, `,`, `!`, `?`. NOT_FOUND: `PlayNextLetter`, `CurrentCharacterIndex`, `CharPrintPercent`. Their semantics are not proven.
- Blocker: shipped 1.02 paint placement (stock visual positions vs. tutorial logical pen) and zero-interval timer behaviour are unproven. Without them word reveal cannot be called viable, and with the tutorial model it is rejected.

## Round 002 — shipped binary classification

The hash-locked static investigation resolved both questions without plugin source. Evidence: `reports/rtl_research/proto_binary/` (functions, xrefs, selected excerpts, offsets and a reproducer).

- `PAINT_MODEL_LOGICAL_PEN` (`CONFIRMED_FROM_BINARY`): the char-color decorator's registration/factory chain resolves its run paint to RVA `0x9a2bd0..0x9a368c`. Each iteration constructs `[i,i+1)`, retrieves a shaped slice, draws it with accumulated x, then adds that slice's advance and increments the logical index. Reusing shaping does not preserve final visual positions.
- `ZERO_INTERVAL_BATCHES_CHARACTERS` (`CONFIRMED_FROM_BINARY`): selector `0x9a0880..0x9a09c8` returns the chosen scalar without a minimum clamp. Print entry `0x9a3ec0..0x9a4261` routes zero immediately to budget loop `0x9a3900..0x9a3eb2`. The loop advances while budget >= remaining delay. Positive space delays can stop a batch; a large time budget can consume multiple words. Subsequent ordinary scheduling receives the remaining wait.
- Decision: **WORD_REVEAL_REJECTED for timing-only changes.** The POC was not rebuilt or installed. Arabic isolation, native repair/integration, Paint ordering and actual-game acceptance remain unproven. Public tutorials remain `PUBLIC_REFERENCE_ONLY`.
- Source absence did not block these classifications. The two binary questions must not be reopened merely because symbols are stripped. A source/integration requirement for an actual repair is a separate question.
- `GAME_NOT_RUN`, `STEAM_NOT_RUN`, `PACKAGE_NOT_INSTALLED`, `IN_GAME_RTL_NOT_PROVEN`, `tested_in_game=0`, `final=0`.

## Round 003 — detached renderer repair prototype

Preferred architecture: a new Arabic UWidget wrapping custom Slate, using retained FSlateTextLayout line/block/glyph positions and one safe-unit alpha mask shared by foreground and shadow. Non-Arabic localization language keeps the existing Proto path. New native registration and Blueprint routing are required; none is implemented.

The detached prototype consumes full logical text, prepares final visual geometry, then changes visibility only. Safe units close graphemes under shaping clusters; word mode merges afterward. TimingTrace supplies authoritative per-UTF16 readiness and native finish time. Its actual game adapter, donthide/hold semantics, materials and RetainerBox effects remain unverified. Ten outputs are deterministic across repeated builds; this is not an Unreal module.

See `reports/rtl_research/renderer_repair/ARCHITECTURE.md` for six primitive candidates, five integration routes, API contracts and precise native build/deployment gaps. `RENDERER_REPAIR_PROTOTYPE_BUILT` is model-only. Arabic isolation and in-game behavior remain unproven; `tested_in_game=0`, `final=0`.

## Round 004 — architecture gate review (supersedes round-003 recommendation)

The native `UArabicSubtitleRevealWidget` cannot be delivered. This build has no supported native module loading path (`NATIVE_MODULE_LOADING_NOT_FOUND`). The proposed stock-engine route keeps round 003's model: final geometry, one mask, foreground and shadow passes.

1. Arabic layer inside WBP_SubtitleBlock: stock URichTextBlock foreground plus shadow (own RetainerBox pair with the existing blur MIs), ShapedTextOptions RTL + FullShaping. English Proto objects and calls are untouched, and the Arabic layer stays Collapsed unless `GetCurrentLanguage` starts with `ar`.
2. Markup set once per line: one stock RichText tag per whitespace word unit (row `s<slot>_<variant>_u<k>`). Speaker/donthide is unit 0. Tokens without a strong letter merge into a neighbour. Never cut inside a word or at punctuation.
3. Generated DataTables: rows share font/size/outline metrics and differ only in colour (R byte = unit index) and material instance.
4. New font material M_ArabicReveal (+ static MICs per slot and per foreground/shadow) samples the slot's cooked render target: coverage only if index <= threshold. Calibration switch for vertex-colour space (gate G2).
5. Per step: ClearRenderTarget2D(threshold) and RequestRender on the retainers. A unit is visible when its last character is due at Proto's cadence. Finish/skip set the last unit and fire the finish delegate once.

Not implemented. Gates G1–G5 are listed in `reports/rtl_research/renderer_repair/ARCHITECTURE_REVIEW_004.md`. Blueprint authoring needs a UE4.27 editor workflow; current UAssetAPI tooling has only proven property edits. `tested_in_game=0`, `final=0`.

## Round 006 — static preparation (no gate executed)

- Exact authoring plan for the Arabic branch of `WBP_SubtitleBlock`: `reports/rtl_research/renderer_repair/WBP_PATCH_PLAN.md` (exports kept, new objects/imports, language query `StartsWith(GetCurrentLanguage(),"ar")`, Set/Stop Displaying Line branches, shadow sync, pool reset, colour via material parameter).
- Gate artifacts and G4/G5 static requirements: `reports/rtl_research/renderer_repair/NEXT_INTEGRATION_CHECKLIST.md`. Subtitle colour is a material vector parameter (`Update Text Color`), so vertex colour is free for the unit index; no ancestor colour animation was found.
- Arabic activation: the in-game Language list is a literal list in the EXE without `ar` (menu entry impossible without an EXE change); menu-independent route = ar locres + locmeta `CompiledCultures` + launch culture (`reports/arabic_activation/`).
- Font: subtitles' composite font has no Arabic face; Arabic falls to the engine fallback Noto Naskh Arabic UI (0 missing glyphs, 0 `.notdef` over the corpus, static clipping risk +3–6 px) — `reports/fonts/FONT_READINESS.md`.
- Status unchanged: STOCK_RENDERER_ROUTE NOT_PROVEN, G1–G5 NOT_PROVEN, IN_GAME_RTL_NOT_PROVEN.

## Round 007: stock renderer gates (UE 5.8.4 isolated test)

Evidence: `reports/rtl_research/renderer_repair/ue427_gate_test/` (engine used: **UE 5.8.4**, not 4.27; user chose "Use 5.8 only").

On UE 5.8.4 the stock-route prototype revealed Arabic by whole words with the final shaped RTL layout frozen. It used one SetText per line and only threshold writes after that. The 4.27 behaviour is not proven, and nothing was integrated into DISPATCH. The required material and Blueprint changes are in `reports/rtl_research/renderer_repair/WBP_PATCH_PLAN.md` (Round 007 update).

## Round 008: revised integration architecture (R8 / R8b)

- **Threshold:** per subtitle block, a stock Border's `ContentColorAndOpacity` carries the threshold. There is no render target, so pooled and simultaneous blocks are independent.
- **R8:** a new material with the index in R and the threshold in G (128 units). It needs a UE4.27 shader compile.
- **R8b:** reuses DISPATCH's shipped `M_SubtitlePrinting`, whose compiled pixel shader computes opacity from VertexColor.B. The code is `10.5^(t-i)` (37 units). No new shaders are needed, and every asset can be cloned from shipped ones.
- **Shadow:** the same table and markup inside the existing blur retainer pair, with the Border inside the retainers.
- **Outline:** per-row OutlineColor carries the code. 4.27 tint propagation is VERSION_SENSITIVE.
- **Segmentation reference:** `tools/ue427_stock_reveal_test/segment_units.py`.
- **Language gate:** `L == "ar" || StartsWith(L, "ar-")` on `GetCurrentLanguage()`.
- **Design and evidence:** `reports/rtl_research/renderer_repair/ARCHITECTURE.md` (round 008) and `COMPATIBILITY_AUDIT_008.md`.
