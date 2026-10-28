# WBP_SubtitleBlock Arabic-branch patch plan (prepared round 006; production Blueprint not modified)

# Round 019 patch note — Build Arabic Timing is void

The R8b WBP adds one patch after round 012, made by `RepairTiming019` (`tools/asset_inspector/ArabicRepair019.cs`):
- `Build Arabic Timing` (export 66) drops `ReturnValue` and `FUNC_HasOutParms`.
- Its single `Return Local(Output)` becomes `Return Nothing`.

No other export changes (72/73 byte-identical to 012). The bare call at Set Displayed Line:66 is now a valid void statement.

Generator rule for every future patch: never emit a statement-level call to a function returning a non-trivial value
(FString, FText, TArray, non-POD struct). Bind it with `Let` to a local of the return type, or make the helper void.
`ReturnContractR` enforces this.
Artifact `builds/rtl_poc/r8b_repair_019/`; see `R8B_REPAIR_019.md`. Not installed, not runtime-tested.


# Round 009 authoritative implementation note

`R8B_WBP_STAGE1_PASS`: four Arabic R8b tables, seven named stock widgets, seven slots, seven widget FObjectProperties
and four DataTable FObjectProperties are generated/validated on a detached copy. Original Kismet remains byte-identical.
See `WBP_STAGE1_RESULT.md` for exact evidence and null CDO defaults. The Stage-2 map is now
`WBP_STAGE2_BYTECODE_MAP.md`; it supersedes old RT/new-material/raw-StartsWith("ar") proposals below.
Earlier claims that no widget-tree generator exists are historical. Runtime routing/timers/helpers are still absent.
NOT_INSTALLABLE / NOT_RUNTIME_TESTED. No stage-2 mutation performed.

---

Source facts: `reports/rtl_research/WBP_SubtitleBlock.json` (37 exports, 95 imports) and `subtitle_block_summary.txt`;
pooling from `WBP_SubtitlesWidget.json`. Route and gates: `ARCHITECTURE_REVIEW_004.md`, `NEXT_INTEGRATION_CHECKLIST.md`.
To be authored in a UE4.27 editor (stub project named Dispatch with header-only stubs for ProtoAnimatedText, AdHocUtils,
AdHocSubtitles, Dispatch settings classes), then cooked. Not authorable with the current UAssetAPI tooling
(BLUEPRINT_ARABIC_BRANCH: REQUIRES_UNSUPPORTED_EDIT).

## 1. Existing exports that remain unchanged (English path)

| Export | Role | Change |
|---|---|---|
| 33 `SubtitleProtoText` (ProtoRichTextBlock) | English foreground | none |
| 34 `SubtitleShadowProtoText` | English shadow | none |
| 35/36 `RetainerBox_Horiz/Vert` + MI_UI_TwoPassBlur_* | shadow blur | none (Arabic shadow gets its own pair, see 2) |
| 24 `Letterbox`, 25 `Overlay_0`, 26 `SubtitleOverlay`, 27–32 slots | layout | add children only |
| 13 `Format As Subtitle Text With Tags`, 16 `Apply Speaker Name if Needed`, 17 `Get Text Tag Opener` | English markup | none (Arabic has its own builder) |
| 18 `Setup Dynamic Material`, 15 `Update Text Color` | font MID + colour | extended to also create/update the Arabic MIDs |
| 2 Ubergraph: OnInitialized, OnPrintLetter, letterbox/colour setting callbacks, finish delegate | events | extended (see 4) |

## 2. New objects

| New object | Class | Notes |
|---|---|---|
| `ArabicText` | stock RichTextBlock (`/Script/UMG.RichTextBlock`, already imported as −24) | TextStyleSet = `DT_ArabicReveal`; AutoWrap at `Wrap Text Length` (1050); Justification Center (as English); ShapedTextOptions: FullShaping, flow Auto; Visibility Collapsed by default |
| `ArabicShadowText` | RichTextBlock | Same rows with shadow variant MICs; inside new `ArabicRetainer_Horiz/Vert` with the same blur MIs |
| `ArabicRetainer_Horiz`, `ArabicRetainer_Vert` | RetainerBox | Same settings as 35/36 (RenderOnInvalidation true) |
| Slots | OverlaySlot/PanelSlot | Arabic layer added to `Overlay_0` beside the English children, same alignment |
| `DT_ArabicReveal`, `DT_ArabicReveal_Large` | DataTable of FRichTextStyleRow | One row per (style variant × unit index 0..N−1); identical font/size/outline/spacing; ColorAndOpacity R = encoded unit index (G2 calibration) |
| `M_ArabicReveal` + MICs (fg, shadow, outline) | UI material | coverage × (unitIndex ≤ threshold); colour from vector param `SubtitleColor` |
| `RT_ArabicReveal_<slot>` | TextureRenderTarget2D 1×1 | threshold store; one per pooled block is created at runtime with `CreateRenderTarget2D` if cooked RTs cannot be shared |
| Variables | `bArabic` (bool), `ArabicUnitCount` (int), `ArabicUnitReadyTimes` (float array), `ArabicThreshold` (int), `ArabicTimer` (TimerHandle), `ArabicFgMID`, `ArabicShadowMID` (MID refs) | new BPGC properties |
| Function `Build Arabic Markup` | BP function | Splits the processed Arabic text at whitespace into units (no unit without a strong letter; speaker/donthide prefix = unit 0); emits `<s{variant}_u{i}>word </>`; returns unit ready times from the Proto cadence (0.025 s per counted character, `ready(U)=max` of its characters) |
| Function `Arabic Step` | BP function | ++threshold; `ClearRenderTarget2D(RT, (threshold/255,0,0,1))`; RequestRender on both Arabic retainers; on last unit clear timer and call the block's existing `On Finish Letter by Letter Print` delegate once |

New imports needed: `/Script/Engine.KismetInternationalizationLibrary:GetCurrentLanguage`,
`/Script/Engine.KismetRenderingLibrary:ClearRenderTarget2D` (and optionally `CreateRenderTarget2D`),
`/Script/Engine.KismetSystemLibrary:K2_SetTimer`/`K2_ClearAndInvalidateTimerHandle`, `KismetStringLibrary:ParseIntoArray`,
`/Script/UMG.RichTextBlock:SetText/SetTextStyleSet`, the new DataTables, material, MICs and RTs. All native names exist in
the EXE (`exe_names.json`).

## 3. Language query

In `Set Displayed Line`, once per line: `bArabic = StartsWith(GetCurrentLanguage(), "ar")` (covers `ar`, `ar-SA`). No
character-based detection. English (`en`, any other culture) leaves `bArabic=false` and runs the original nodes unchanged.

## 4. Function-by-function plan

**Set Displayed Line (export 11)** — after the existing censorship filter, `ProcessLocalizedTextWithCallback` and
`Apply Speaker Name if Needed` (shared, unchanged):

```
if !bArabic:                       # original path, byte-identical behaviour
    SubtitleShadowProtoText.SetText(T); SubtitleProtoText.SetText(T)
    letterbox nodes (unchanged)
    if TypewriterEnabled: PrintLetterByLetter() x2 else: ShowText() x2
    ArabicText/ArabicShadowText: Collapsed
else:
    Proto texts: SetText("") and Collapsed      # nothing English left visible
    letterbox nodes (unchanged)
    markup, readyTimes = Build Arabic Markup(T)
    ArabicShadowText.SetText(markup); ArabicText.SetText(markup)    # once per line
    ArabicText/ArabicShadowText: SelfHitTestInvisible
    if TypewriterEnabled: threshold=-1; ClearRT(threshold); K2_SetTimer(Arabic Step, 0.025, looping) driven by readyTimes
    else:                 threshold=last; ClearRT(threshold); fire finish delegate once (same as ShowText path)
```

**Stop Displaying Line (export 12)** — keep `SubtitleOverlay.SetVisibility(Hidden)`; add: clear `ArabicTimer`, set
threshold to −1 (`ClearRT`), Collapse Arabic layer. Applies to both paths, so a pooled block never re-shows stale units.

**Setup Dynamic Material (18)** — also create `ArabicFgMID`/`ArabicShadowMID` from the Arabic MICs, bind the slot RT as
texture parameter, assign them to every row's font material at runtime only if G1 shows per-row MIC binding is not enough.

**Update Text Color (15)** — also `SetVectorParameterValue("SubtitleColor")` on the Arabic MIDs.

**ChangeTextToLarge (19)** — also `SetTextStyleSet(DT_ArabicReveal_Large)` on both Arabic texts, then invalidate layout.

**Set Has Outline (14)** — also toggle `SetRetainRendering` on the Arabic retainers and pick outline row variants.

**Set Wrap Text At (21) / PreConstruct** — also apply the wrap length to the Arabic texts (stock `SetAutoWrapText` + wrap width;
`AdHocUtils SetTextWrapAt` takes a ProtoRichTextBlock-compatible target — verify in editor).

**OnPrintLetter (Ubergraph)** — unchanged for English; the Arabic `Arabic Step` calls the retainer `RequestRender` itself.

## 5. Calls that remain English-only

`PrintLetterByLetter`, `ShowText`, `SetProtoTextStyleSet`, `OverrideFontMaterial` (M_SubtitlePrinting MID),
`Format As Subtitle Text With Tags`, `Get Text Tag Opener` (`<text style=… donthide=…>` markup is Proto-specific).

## 6. Shadow sync and pooling

One timer and one threshold RT per block drive both Arabic MIDs, so foreground and shadow cannot diverge. Pooled
blocks are reinitialized in `Set Displayed Line` and cleaned in `Stop Displaying Line`; `WBP_SubtitlesWidget` needs **no**
change (its pool only calls these two functions).

## 7. Acceptance once authored

English: binary-identical behaviour (same functions executed, same text, same timing). Arabic: right-anchored reveal by
whole words in reading order, final layout identical to the fully revealed line, finish delegate once, skip/finish
idempotent, pooled reuse clean. All require EDITOR_PASS then IN_GAME_PASS; none is claimed.


---

# Round 007 update: from real editor results (UE 5.8.4 isolated test; NOT 4.27, NOT DISPATCH)

Evidence: `ue427_gate_test/`. Everything below reflects behaviour measured in **UE 5.8.4**. It must be re-measured in a 4.27 editor before authoring. The production `WBP_SubtitleBlock` was **not** edited.

## R7.1 Changes forced by the measurements
| # | Change | Evidence |
|---|---|---|
| 1 | The material must **divide the output colour by VertexColor** (`Col / max(VC,1e-6)`), because Slate multiplies the font-material output by the run colour | G1 probes |
| 2 | Row colours are `(srgb_to_linear((i+1)/255), 1, 1, 1)`: index in R only, G=B=A=1. Unit i = byte i+1. The material decodes `round(linear_to_srgb(VC.r)*255)-1` | G2 sweep 256/256; naive i/255 gives 183/256 |
| 3 | Rows per table: `Default` + `u0..u254` (255 units; need 69) | G2 functional 255-unit pass |
| 4 | Opacity output is **not** multiplied by VC.A | G1/G5 RenderOpacity |
| 5 | Arabic retainers: `RequestRender` after **every** threshold write **and once on the frame after SetText**. The first retained capture after SetText can be empty | G3 retainer policy; long_wrap 22,998 px stale first capture |
| 6 | No RGB tint (`ColorAndOpacity`, `ContentColorAndOpacity`, colour animation tracks) on any ancestor of the Arabic layer. RenderOpacity is allowed | G5 parent: tint 2/4 wrong, opacity 0/4 |
| 7 | Texture parameter `RevealRT` must use SamplerType **Color** (5.8 compiler rejects LinearColor for the RT) | material compile error, round 007 |
| 8 | Shader delivery decision needed: shared cook puts the shadermap in the project archive; inline cook embeds it in `M_ArabicReveal.uexp` | G4 |

## R7.2 Exact assets
| Asset | Type | Settings |
|---|---|---|
| `M_ArabicReveal` | Material | MD_UI, Translucent, Unlit. Custom node per `ue427_gate_test/materials/M_ArabicReveal.md`. Params `RevealRT` (Texture), `SubtitleColor` (Vector), `DecodeMode` (Scalar, calibration knob), `DebugMode` (Scalar, 0 in shipping) |
| `MI_ArabicReveal_FG`, `MI_ArabicReveal_Shadow`, `MI_ArabicReveal_Outline` (untested) | MaterialInstanceConstant | colours per English look; DecodeMode from the 4.27 calibration |
| `RT_ArabicReveal` (template) | TextureRenderTarget2D 1×1 RGBA16f, ClearColor (-1,0,0,1) | one per pooled block, created at runtime with **Create Render Target 2D** (cooked RT would be shared across blocks) |
| `DT_ArabicReveal`, `DT_ArabicReveal_Large` (+ outline variants) | DataTable FRichTextStyleRow | 256 rows each. Every row has the same font, size, outline and spacing; only `ColorAndOpacity.R` differs. **~1.37 MB cooked per table**: keep the number of tables minimal |
| Arabic font | Font (composite) | DISPATCH's own subtitle font chain, or the engine NotoNaskhArabicUI fallback (test used Roboto + NotoNaskhArabicUI) |

## R7.3 Blueprint nodes per function (WBP_SubtitleBlock)
| Feature | Nodes (all stock BlueprintCallable; names CONFIRMED_FROM_BINARY in round 004) |
|---|---|
| Language gate | `Get Current Language` → `Starts With ("ar")` → Branch. Once per line, stored in `bArabic` |
| Arabic foreground | `ArabicText` (RichTextBlock), TextStyleSet `DT_ArabicReveal`, AutoWrap, Justification as English |
| Arabic shadow | `ArabicShadowText` in `ArabicRetainer_Horiz/Vert` (same blur MIs), TextStyleSet shadow table |
| Per-block MIDs | `Create Dynamic Material Instance` (fg, shadow) → `Set Texture Parameter Value ("RevealRT", ArabicRT)`. Rows must reference these MIDs, so either per-block tables or a material that reads a per-block RT through a single MID. **Open design point:** DataTable rows reference a fixed material. Per-slot binding needs per-slot MICs/RTs cooked as assets, or one shared RT plus "one block reveals at a time". To be decided by the 4.27 test |
| Initial SetText | `Clear Render Target 2D (RT, (-1,0,0,1))` → `Set Text(ArabicShadowText)` → `Set Text(ArabicText)` → `Request Render` ×2 now and on next tick (`Delay 0`/`Set Timer for Next Tick`) |
| Threshold update | timer → `Clear Render Target 2D (RT, (t,0,0,1))` → `Request Render` (Horiz, Vert) |
| Skip | `Clear Render Target 2D (RT, (N-1,…))` + Request Render + finish delegate once |
| Finish | when t == N-1: `Clear and Invalidate Timer by Handle` + call existing `On Finish Letter by Letter Print` once |
| Stop Displaying Line | existing `SetVisibility(Hidden)` + clear timer + `Clear Render Target 2D (RT, -1)` + Request Render |
| Pool reset | Set Displayed Line always writes -1 **before** SetText (G5: 0 stale units across A/B/C) |
| Large text | `Set Text Style Set (DT_ArabicReveal_Large)` on both Arabic texts (init-time only, not during reveal) |
| Outline | outline row variants + `Set Retain Rendering` on Arabic retainers, mirroring `Set Has Outline` (outline material path **untested**) |
| Colour | `Set Vector Parameter Value ("SubtitleColor")` on the Arabic MIDs (never widget tint) |
| Wrap width | `Set Auto Wrap Text` / wrap-at as English (geometry stable in test) |
| Speaker formatting | speaker prefix = unit 0, revealed at the first step. In markup it is whitespace-split like other units |
| Censorship output | Arabic markup builder runs **after** the existing censorship/`ProcessLocalizedTextWithCallback`; it never re-reads raw text |
| English Proto path | unchanged nodes; Arabic layer Collapsed when `bArabic=false` |

## R7.4 Still blocking authoring
1. No UE4.27 editor: G1–G5 must be repeated on 4.27 (harness: `tools/ue427_stock_reveal_test`, set `UE=`).
2. Per-pooled-block material binding (R7.3, "Per-block MIDs").
3. Stub project for the cooked WBP's script dependencies (unchanged from round 006).
4. Shader delivery for DISPATCH (shared vs inline) — NOT_PROVEN in game.


---

# Round 008 update: revision R8 / R8b (supersedes the RT parts of R7.1–R7.4)

Sources: `COMPATIBILITY_AUDIT_008.md` (§5 pool, §11 segmentation, §12 seam, §15 mutation map) and `ARCHITECTURE.md` (round-008 diagram). The production WBP was **not** edited.

## R8.1 What is withdrawn from R7
- `RT_ArabicReveal`, `ClearRenderTarget2D`, `CreateRenderTarget2D`, the RT texture parameter and SamplerType note. The per-block threshold is now a Border tint.
- The separate shadow DataTable and shadow MIC. The shipped blur keeps only the retained alpha, so the fg table serves both layers.
- `Update Text Color` writing a vector parameter on "the Arabic MIDs". Stock rows cannot reference a per-block MID. For R8 the colour goes on the fg colourize-retainer effect MID; R8b stays white.
- "255 rows". The new sizes are 129 rows (R8) or 38 rows (R8b).

## R8.2 Assets
| Asset | R8b (offline-producible) | R8 (needs 4.27 shader compile) |
|---|---|---|
| Fill / Fill_Large / Outline / Outline_Large tables | clone `DT_SubtitlesProtoRichText`; RowStruct stays the shipped row type (accepted by stock `SetTextStyleSet`, ASSET) or `/Script/UMG.RichTextStyleRow`; rows `Default`, `u0..u36`; colour (1,1,10.5^-i,1); FontMaterial `M_SubtitlePrinting`; outline rows OutlineMaterial `MI_SubtitlePrinting_Bold`, OutlineColor = row colour | rows `Default`, `u0..u127`; colour (srgb_to_linear((i+1)/255),1,1,1); FontMaterial `MI_ArabicReveal_FG`; outline `MI_ArabicReveal_Outline` |
| Material | none (shipped) | `M_ArabicReveal` (index R, threshold G), `M_ArabicColorize` (retainer effect) |
| Font | shipped `Montserrat-Variable` | same |

## R8.3 Function bodies (pseudo-Blueprint)
```
Set Threshold Arabic(int t):
    tint = R8b ? MakeColor(1,1, t<0 ? 0 : Pow(10.5, Min(t,36)), 1) : MakeColor(1, SrgbToLin((t+1)/255), 1, 1)
    ArabicFgBorder.SetContentColorAndOpacity(tint); ArabicShadowBorder.SetContentColorAndOpacity(tint)
    ArabicRetainer_H.RequestRender(); ArabicRetainer_V.RequestRender()          [R8: + fg colour retainer]
Arabic Step():   ArabicThreshold += 1; Set Threshold Arabic(ArabicThreshold)
                 if ArabicThreshold >= ArabicUnitCount-1: Arabic Finish() else K2_SetTimerDelegate(Arabic Step, ArabicDelays[ArabicThreshold+1], false)
Arabic Finish(): if bArabicFinished: return; bArabicFinished = true; K2_ClearAndInvalidateTimerHandle(ArabicTimer)
                 Set Threshold Arabic(ArabicUnitCount-1); call On Finish Letter by Letter Print (existing delegate)
```
`SrgbToLin` is a pure helper: `x <= 0.04045 ? x/12.92 : Pow((x+0.055)/1.055, 2.4)`. All nodes are stock (KismetMathLibrary). It is not needed for R8b.

## R8.4 Still blocking authoring
1. No WBP generator: the widget-tree, variable and bytecode mutations in audit §15 are POSSIBLE_BUT_UNPROVEN with UAssetAPI 1.1.0, and stub authoring is NOT_VIABLE without a 4.27 editor.
2. Outline tint propagation on 4.27 (VERSION_SENSITIVE). Fallback: outline off in Arabic.
3. Runtime: language gate under `-culture=ar`, real frame order, timer/finish delegate. All need the game.
