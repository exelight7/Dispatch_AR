# Run 5 failure analysis (round 020)

Result: **`R8B_RUN5_FAIL`**. `FRAME_CRASH_FIXED_RUNTIME=true`, `R8B_SUBTITLE_RENDERING_FAILED=true`, `IN_GAME_RTL_PROVEN=false`, `final=0`.

Configuration: Texts `0fa5792a…7235` + Fonts `b8b22bcb…b19f` + repaired R8b `1058eac4…f988` + `-culture=ar`, no Locmeta.
Evidence: operator statement and screenshots (relayed, not in the project), `POST_RUN5_HASHES.json` and
`PRE_POST_RUN5_COMPARISON.json` in `backups/runtime_run5_020_20261025_111003_531/`, and `run5_020/style_gate_020.json`
(`tools/r8b_020/style_gate_020.py`, EXE hash-gated, read-only).

## What the operator saw

- The game boots, the first cutscene plays without a crash, and Arabic UI text renders generally.
- The subtitle region is completely empty in the first cutscene: no Arabic, no punctuation, no reveal.
- Many settings option names are missing.

## Proven fault: the DT_AR tables are invisible to stock URichTextBlock

1. **Tables.** All four tables in the installed pak (`DT_AR_Fill`, `_Fill_Large`, `_Outline`, `_Outline_Large`) serialize
   RowStruct `/Script/ProtoAnimatedText.ProtoRichTextStyleRow`. Round 009 cloned them from `DT_SubtitlesProtoRichText`.
2. **Struct hierarchy (EXE UHT `FStructParams`).**
   - `ProtoRichTextStyleRow`: 664 B, 9 declared properties (`TextStyle` plus 8 Proto print-interval fields), super `TableRowBase`.
   - `RichTextStyleRow`: 632 B, 1 property (`TextStyle`), super `TableRowBase`.
   - They are siblings. `ProtoRichTextStyleRow` is **not** a child of `RichTextStyleRow`.
3. **Engine gate (EXE).** `URichTextBlock::RebuildStyleInstance` (RVA `0x1ec95e0`):
   - It builds `FSlateStyleSet("RichTextStyle")`.
   - It loads `TextStyleSet` (`this+0x140`) and its `RowStruct` (`+0x28`).
   - It calls `FRichTextStyleRow::StaticStruct` (`0x1f10390`, registered by `0x6dc7f0` as `/Script/UMG.RichTextStyleRow`).
   - It runs the inlined `FStructBaseChain` IsChildOf test (`[+0x30]`, `[+0x38]`, `chain[depth] == parent`).
   - If the test fails, the whole row loop is skipped.
4. **Effect.** `ArabicForegroundRichText` and `ArabicShadowRichText` end up with an empty style set:
   - no `Default` row and no `u0..u36` rows;
   - therefore no Montserrat composite with the Arabic sub-font, and no `M_SubtitlePrinting`;
   - every run falls back to the widget's default `FTextBlockStyle`.
   - The widget exports set no `DefaultTextStyleOverride`, so that default style has no font object.
   - With LastResort absent (round 017), no glyph can resolve. This matches a region with no punctuation at all, unlike Run 3, which showed punctuation.
   - The fallback step is DESIGN_INFERENCE from 4.27 engine behaviour. The rejection itself is CONFIRMED_FROM_BINARY plus CONFIRMED_FROM_ASSET.
5. **Why earlier rounds missed it.**
   - `WBP_PATCH_PLAN.md` said the shipped row type is "accepted by stock `SetTextStyleSet`". That holds only at the type level: any `UDataTable*` binds.
   - The UE 5.8.4 harness could not catch it, because it has no ProtoAnimatedText module and used `RichTextStyleRow`.

Classification of the empty subtitle: **receiving text with an invalid style.** The text arrives, but the style table is silently rejected.

## Boundary table

| Boundary | Status | Evidence |
|---|---|---|
| Language-gated control flow | PASSES | Proto texts were hidden, and only the Arabic branch hides them (Set Displayed Line:39–40). Run 2 proved `-culture=ar` reaches the branch. |
| Repaired `Build Arabic Timing` call | PASSES at runtime | Execution passed instruction 66, the Run 2 crash site, with no crash, no new `Saved\Crashes` entry and no Application events. |
| SetText | EXECUTED | Instructions 37–38 precede 66 on the only path. Run 2's dump showed 72-unit markup in `ARText`. |
| SetTextStyleSet | EXECUTES, **TABLE REJECTED** | `style_gate_020.json` |
| ArabicRoot and subtree visibility | Set Visible (instructions 42–48) | Names match the class `FObjectProperty`s and all seven are slotted under `Overlay_0` slot 3, so name binding is statically satisfied. Not proven at runtime. |
| Border ContentColorAndOpacity | Cannot hide anything now | Tint (1,1,B,1) keeps A=1. B only matters through `M_SubtitlePrinting`, which comes from the rejected rows. Brush alpha is 0. |
| Threshold sentinel and updates | MASKED | t=−1 at instructions 35 and 65 (speaker names off, so SpeakerUnits=0). Without the rows there is no material to read VC.b. |
| Material threshold encoding (4.27 vertex colour) | MASKED, not proven | Needs the rows. |
| RetainerBox capture | Shadow only | The foreground is not inside a retainer, so it would draw regardless. |
| UnitCount, Begin Reveal, clock | MASKED | Statically OK: `Arabic Clock Fired` is in the serialized FuncMap and has no `CPF_Parm` locals, so `K2_SetTimer` accepts it. Not proven at runtime. |

Excluded this round:
- **Missing FuncMap entries:** all 22 new functions are present, including `Arabic Clock Fired` and `Tick`.
- **Clock parameters:** they would make `K2_SetTimer` refuse the function, but the clock functions have none.
- **Subtitles disabled:** `SubtitlesEnabled=true` before and after the run.
- **Missing DT imports:** they resolve to `/Game/ArabicReveal/…`, inside the pak's mount.

## Settings labels

- R8b's footprint is `WBP_SubtitleBlock` plus four new tables. The round-012 scan of all 27,365 packages finds `WBP_SubtitleBlock`
  referenced only by `WBP_SubtitlesWidget` (gameplay) and `WBP_SubtitlePreview` (the settings preview).
- The preview text shares the fault above.
- Settings option-name widgets are not reachable from R8b, so **attribution to R8b is not established**. Run 4 already logged UI overlap (backlog B02).
- Needed: the same settings page photographed with and without R8b.

## Confounds left by the run (game-written, not edited by the session)

`CloudSettings.sav` changed during Run 5:
- DialogueBoost 0→1;
- MonoAudio 0→1;
- **ColorblindnessSetting NormalVision→Tritanope**, at intensity 1.0.

Language `system`, SubtitlesEnabled, SubtitleAnimationEnabled=1, speaker names 0, colours 1, letterbox 0 and large 0 are unchanged.
The operator should set colour blindness back to Normal in-game before the next screenshots.

## Next task

Rebuild only the four DT_AR tables with RowStruct `/Script/UMG.RichTextStyleRow`:
- Keep `Default`, `u0..u36` and every `TextStyle` value identical (font, size, `M_SubtitlePrinting`/`MI_SubtitlePrinting_Bold`, colour codes).
- Drop the 8 Proto-only fields.
- The WBP stays byte-identical.

Add a permanent validator rule: every table bound to a UMG `RichTextBlock` (widget default `TextStyleSet` and every
`SetTextStyleSet` argument) must have a RowStruct that is a child of `RichTextStyleRow`, citing the EXE gate. The 019 tables are the negative fixture.

Then rebuild the staging pak and prepare Run 6 with a built-in discriminator:
1. Typewriter on (clock route).
2. If the subtitle is still empty, turn subtitle animation off in-game. That route is `Arabic Finish`: threshold = UnitCount−1, no clock.

Text visible with animation off but not with it on isolates the clock. Empty in both points to the material, encoding or binding.
