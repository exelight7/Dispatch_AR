# Arabic reveal renderer — round 003

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


# Round 009 implementation status — offline Stage 1 passed

The round-008 R8b architecture is now represented by four detached tables and a serialized WBP subtree under
`builds/rtl_poc/stage1/`. This implements structure, named FObjectProperties, table references and dependencies only;
all seven Arabic widgets default Collapsed. No original bytecode or runtime reveal logic changed. The source BPGC/CDO
null widget-reference convention is retained; runtime binding has not been tested. See `WBP_STAGE1_RESULT.md`.
Stage-2 implementation sites and relocation/flow-stack constraints are in `WBP_STAGE2_BYTECODE_MAP.md`.
The design gate classes from round 008 and the outline VERSION_SENSITIVE limitation remain unchanged.
`DISPATCH_INTEGRATION_PROVEN=false; IN_GAME_RTL_PROVEN=false; tested_in_game=0; final=0`.

---

> **Round 004 note:** the native-widget deployment recommendation below is superseded.
> The build has no native module loading path. See `ARCHITECTURE_REVIEW_004.md`.
> The model sections (final geometry, safe units, one mask, two passes) remain valid.

```text
RENDERER_REPAIR_PROTOTYPE_BUILT
ARABIC_BRANCH_REQUIRES_NATIVE_INTEGRATION
secondary: ARABIC_BRANCH_REQUIRES_BLUEPRINT_CODE_CHANGE
ARABIC_ISOLATION_NOT_PROVEN
IN_GAME_RTL_NOT_PROVEN
tested_in_game=0
final=0
```

The working prototype is detached Python/SVG/PNG, not an Unreal module or an
installable mod. A clean native architecture is identified; loading it into this
monolithic game remains unresolved. The timing-only route stays closed.

## Evidence

Round 002 is authoritative for logical-pen paint and zero-delay batching. No EXE
analysis was repeated. This round inspected two existing asset JSONs, the earlier
layout/corpus, known engine installation locations and official APIs in SOURCES.md.

Evidence classes: CONFIRMED_FROM_BINARY = inherited round 002 only;
CONFIRMED_FROM_ASSET = serialized tree/types/calls; DETACHED_MODEL_TESTED = this
prototype's assertions; DESIGN_INFERENCE = native composition; NOT_PROVEN =
native compilation, integration, full styles/materials and actual-game behavior.

## Rendering primitive decision matrix

Y means supported by the proposed composition, not implemented in Dispatch.
Every native row requires a verified UE4.27 SDK/build. No row is compiled here.
All can avoid EXE byte edits in a source-integrated build; that does not establish
a loading path in the installed game. References resolve through SOURCES.md.

| Primitive | Final visual positions | Rich styles / wrapping | Cluster alpha | Existing WBP and English | Proto source? | Blueprint change? | Decision |
|---|---|---|---|---|---|---|---|
| Custom SRichTextBlock decorator/run | Y through block/context/shaped cache | Reuse marshaller and layout | New paint bridge needed | Requires registration and Arabic selection; Proto forced factory not assumed replaceable | No for independent run; in-place Proto replacement unproven | New class/routing, not just style data | Useful component [RUN, RICH] |
| Custom ISlateRun/text run | Y when consuming final block/sequence | Reuse FSlateTextRun measurement; avoid writing wrapping again | Y with custom paint | Must be inserted in Arabic layout | No | Native class and routing | Suitable run component [RUN, BLOCK, GLYPH] |
| Custom Slate widget | Y, owns FSlateTextLayout | Rich marshaller/style adapter required | Y over frozen visual geometry | Needs UMG bridge | No | UMG wrapper/branch required | Chosen layout owner [LAYOUT, LINES] |
| URichTextBlock-derived widget | Conditional on custom Slate rebuild | Existing style controls help | Subclass alone insufficient | Sibling class lacks Proto-specific functions/delegates | No for sibling; Proto subclass headers/ABI unavailable | Existing typed Proto references cannot be swapped blindly | Possible, but more inherited assumptions [RICH, WRAPPER] |
| UWidget wrapping Slate | Y through owned adapter | Explicit style/wrap/color bridge | Y | Separate Arabic child; original English objects retained | No | New UClass and explicit branch | Preferred shell [WRAPPER] |
| Custom layout/line-view path | Y: line blocks and glyph mapping | Retain engine line flow | Layout itself supplies no complete per-glyph tint API | Component inside Slate owner | No | Does not itself provide UMG routing | Reuse, do not replace engine layout [LINES, SEQUENCE] |

## Integration options matrix

| Route | Technical viability | Arabic isolation | Proto source | Game source | EXE byte edit | Hook | Detached now | Risk / recommendation |
|---|---|---|---|---|---|---|---|---|
| A. Modify Proto source | Direct paint repair; deployment unresolved | Native language gate | Yes for this route | Needed for clean monolithic rebuild unless another supported entry exists | Not inherently | Not inherently | Model only | Smaller WBP impact, not a prerequisite for B |
| B. New native Slate/UMG renderer | Concrete design below; game compatibility unproven | Language branch, English original | No | Not for standalone UE test; installed-game delivery still unresolved | No by design | No in clean supported integration | Working independent harness, no UE module | Preferred architecture |
| C. Blueprint branch to alternate widget | Structurally expressible; current tree has no replacement renderer | Explicit language gate | No | Not necessarily, but cooking/integration unproven | No | No by design | Metadata audit only | Required companion to B; insufficient alone |
| D. Data-only localized override | Styles/fonts/timing cannot repair proven placement | Data redirection still unproven | No | No | No | No | Prior POC exists; not rebuilt | Reject as reveal repair |
| E. Runtime hook/injection | Analysis-only possibility; compatibility unproven | Would need verified gate | Not necessarily | Not necessarily | Implementation-dependent | Yes | Not attempted | High risk; outside authorization |

No route is currently a proven buildable/installable native mod for this game.
A new UClass is not registered by placing a name, source or DLL in a PAK.
Blueprint bytecode cannot be localized by assuming an L10N/ar copy will run.

## Integration points found

Reproducer: `tools/rtl_renderer_prototype/inspect_assets.py`.
Evidence/hashes: `integration_points.json`.

- Block: 37 exports. WidgetTree 37 -> SubtitleOverlay 26 -> Overlay_0 25.
  Slot 28 holds foreground Proto 33; slot 29 holds RetainerBox_Horiz 35 ->
  RetainerBox_Vert 36 -> shadow Proto 34. Letterbox 24 occupies the other branch.
- Both text fields are FObjectProperty typed as imported ProtoRichTextBlock (-18).
  An unrelated UWidget/URichTextBlock lacks existing PrintLetterByLetter/ShowText,
  Proto style setters and delegate bindings. A default class-reference swap alone
  cannot preserve this contract.
- Set Displayed Line export 11 is the seam after profanity/localized callback and
  speaker formatting. Keep that preprocessing, then route the complete text.
- PreConstruct 3, Set Wrap Text At 21, ChangeTextToLarge 19, color/outline handlers,
  Stop Displaying Line 12 and print/finish delegates are update/reset seams.
  A wrapper needs explicit equivalent methods; AdHoc's wrap helper is not assumed
  compatible with an unrelated new widget.
- Static visibility on both text objects is Visible. Whole-overlay visibility and
  outline/retainer settings are not language gates. No WidgetSwitcher, spare
  ordinary RichTextBlock/TextBlock child or culture/language name appears in the
  two inspected exports. RichTextBlock in NameMap is not an unused child widget.
- Parent WBP_SubtitlesWidget has 43 exports and typed WBP_SubtitleBlock pooling.
  Adding an Arabic child inside that block preserves the pool's outer type;
  replacing the pooled block with an unrelated class does not.
- bHasScriptImplementedTick/Paint are false on the block CDO. There is no ready
  Blueprint paint handler that can be enabled just by changing data.

Strongest classification: ARABIC_BRANCH_REQUIRES_NATIVE_INTEGRATION, with
ARABIC_BRANCH_REQUIRES_BLUEPRINT_CODE_CHANGE for the preferred replacement-widget
route. A native culture-aware Proto repair could avoid the BP branch, but is a
different route. Absence claims are limited to these exports; inherited behavior
and all other game assets were not exhaustively scanned. Original BP unchanged.

## Preferred architecture

Conceptual names, not implemented native classes:

```text
WBP_SubtitleBlock's complete processed logical FText
  current localization language is ar?
    no -> existing SubtitleProtoText + SubtitleShadowProtoText, original calls
    yes -> UArabicSubtitleRevealWidget wrapping SArabicSubtitleReveal
             rich parser/style adapter -> FSlateTextLayout -> final line views
             -> visual shaped glyphs + UTF-16 source identities
             -> frozen glyph geometry + safe-unit IDs
             -> one reveal mask -> foreground and shadow draw passes
```

Use GetCurrentLanguage's language code [LANGUAGE], snapshotted per subtitle.
GetCurrentCulture is a legacy equivalent; number/date locale and character
detection are not reliable UI-language selectors. `ar`, `ar-SA`, `ar_EG` select
Arabic; English language always keeps Proto, even for mixed input. Under Arabic
language, an all-Latin `SDN 250 XP` line still uses the new renderer. An explicit
localization-language flag could work, but none is connected in the current block.

### Final geometry and masking

Prepare complete rich text and normal engine wrapping before reveal. Retain line
offsets, block geometry, visual glyph sequences and source coverage. Source identity
must include line-model/paragraph identity plus logical UTF-16 offset; local
SourceIndex values from separate paragraphs must not collide.

The adapter resolves shaped glyph atlas data [ATLAS] and freezes each glyph's
visual position once. During that preparation, advances follow the already-shaped
**visual** sequence. During reveal there is no pen, source slicing or reflow.
Change per-unit alpha on positioned glyph geometry. A single moving rectangle is
insufficient for mixed runs; source-prefix shaping changes layout and is rejected.

MakeCustomVerts [VERTS] is a custom-geometry carrier candidate, not a verified
drop-in font batcher. Atlas resource handles, font shader/material behavior,
clipping, outlines, lifetime and atlas invalidation require an actual engine
adapter. Proto's packed vertex payload/font material must not be reused blindly.
An alternative full-sequence copy with bIsVisible masking must first prove the
batcher retains hidden advances; that optimization is not assumed here.

Width/DPI/font/style/language changes create a new full snapshot before painting,
carrying readiness by logical source identity. No partially visible prefix is
used as the layout input.

### Safe units and styles

Union grapheme ranges with every overlapping shaping cluster. Ligatures can span
several graphemes; marks can produce several glyphs or zero-character glyph
entries. Such entries are not independent reveal units. Word mode merges only
after closure. Never split at a style boundary just to expose a partial glyph.

Native runs retain actual font, typeface, size, material, outline, speaker and
donthide metadata from the processed text/style table. The detached model retains
style IDs and synthetic colors, but uses the earlier fixed-size fallback metrics.
It does not prove native italic/large/outline rendering or unknown decorators.

### Timing, events, skip and shadow

Renderer input is an authoritative TimingTrace: one ready timestamp per source
UTF-16 unit and the native finish deadline. For each safe unit U:

```text
ready(U) = max(native ready times covered by U)
```

Thus no half-cluster is shown, and final completion time is retained. Punctuation,
space waits, overrides, pause handling, exempt ranges and EndHold belong in the
future timing adapter. No ready-index feed has been proven; no exact native
timing adapter is built. Do not substitute the rejected 0/space-0.16 POC tuning.

Design API:

```text
StartReveal(snapshot, trace): reset old generation and mask
AdvanceRevealUnit(clock): consume due units, commit one mask
CompleteReveal(): all visible; finish once
SkipToEnd(): idempotent CompleteReveal
OnMaskChanged: invalidate foreground and shadow
OnRevealFinished: forward block completion once
```

The harness tests equivalent methods, zero-delay timestamps, a positive gap and
completion hold. Its default trace uses a fixture 0.025 cadence; donthide/newline
are excluded by an explicit unverified assumption. A mixed exempt/timed cluster
waits for its last timed position. Exact speaker, ShowText, skip event counts,
reentrancy and pooling cancellation remain integration tests. A stale callback
must not finish the next pooled subtitle generation.

Shadow design: **one immutable mask, two draw passes**, never two clocks. The
prototype uses offset shadow/foreground with identical glyph IDs and alpha.
Actual horizontal/vertical RetainerBox effects must refresh from the same mask
generation. Blur, outlines and M_SubtitlePrinting are not reproduced by an SVG
drop shadow and remain explicit native integration work.

## Detached prototype and validation

The new harness reuses existing HarfBuzz and full UBA via python-bidi/unicode-bidi
(not ICU), plus 14 saved prior corpus texts under 3 wrappers. Preparing one final
layout transaction can shape for measurements and final lines multiple times;
tests forbid any shaping during reveal.

42 placement cases, 84 cluster/word plans, 2,908 event-boundary/adjacent frames:
0 cluster splits, 0 geometry/wrap drift, 0 shadow drift and 0 correct-model
mixed-BiDi placement failures. The logical-pen abstraction fails 42/42 checks.
It retains all shaped glyphs generously and is not a shipped-code emulator.

Synthetic SVG/PNG outputs cover mixed text, marked lam-alef, punctuation and long
wrapping. Tests include UTF-16 non-BMP mapping, bad timing input, split-alpha
mutation, skip/completion idempotence and culture gating. Repeated-output byte
comparison is recorded in verification.json. Stable wrapping is a model property:
breaks are whitespace-only and fallback is simplified; this is not Slate/ICU parity.

## Native build/deployment boundary

No UE4.27 headers/UnrealBuildTool were found in the checked known/registered roots;
Epic Launcher's manifest lists no UE_* installs. Bounded discovery, not a full
disk search. No SDK installation was attempted.

Missing: actual engine layout/atlas/style adapter, native timing feed, new UClass
registration, BP language routing/cooking and supported game loading path. Proto
source is not mandatory for this independent design. No Blueprint/EXE edits,
DLLs, hooks, installation or runtime execution occurred.

Next: supervisor review of architecture and native build/deployment prerequisites,
then a separately scoped UE4.27 standalone adapter build against supplied headers.
Do not repeat binary classification or the timing-only POC.

## Round 007 note: gate results (UE 5.8.4 only)

Evidence: `reports/rtl_research/renderer_repair/ue427_gate_test/` (engine used: **UE 5.8.4**, not 4.27; user chose "Use 5.8 only").

The stock route (URichTextBlock, whitespace units, index in the run colour, UI font material, threshold in a 1×1 RT written with ClearRenderTarget2D) behaved as designed on 5.8.4:
- The final layout was frozen.
- There were 0 SetText or SetTextStyleSet calls after init.
- Foreground and retained shadow stayed synchronised.

Three corrections to round 004's material design:
1. Output colour = `SubtitleColor / VertexColor` (Slate multiplies the font-material output by the run colour).
2. Encode the index as sRGB byte i+1 in R with G=B=A=1. Linear i/255 aliases 73 of 256 values.
3. Do not multiply opacity by VertexColor.A.

Retainers need RequestRender per write and once after SetText. A 4.27 rerun is required before integration.

## Round 008: canonical integration architecture (supersedes the round-007 RT threshold)

Decision: `EDITOR_RENDERER_ROUTE_NEEDS_REVISION`.
- The revision R8 (per-block tint threshold) is implemented and passes on UE 5.8.4 only.
- Full audit and evidence classes are in `COMPATIBILITY_AUDIT_008.md`.
- Evidence directories: `r8_tint_test/`, `r8b_printing_test/`, `dispatch_shader_evidence/`.

Two material back-ends share one widget and Blueprint design:
- **R8b (canonical for offline work, no new shaders):** rows use DISPATCH's shipped `M_SubtitlePrinting` (fill and shadow) and `MI_SubtitlePrinting_Bold` (outline). Reveal code in VertexColor.B is `10.5^(t-i)`, max 37 units.
- **R8 (upgrade, needs a 4.27 shader compile):** new `M_ArabicReveal`, with the index in R and the threshold in G. Max 128 units, plus a colourize retainer for per-line colour.

```text
SubtitleDisplayInfo (native AdHocSubtitles; text already sliced at '|')
  |
Set Displayed Line
  |- SubtitleColor / Update Text Color ............................ shared, unchanged
  |- Dispatch Filter Text Profanity -> censored text ............... shared, unchanged
  |- LANGUAGE GATE: L = GetCurrentLanguage(); bArabic = L=="ar" || StartsWith(L,"ar-")   (once per line)
  |
  |-- bArabic == false: ORIGINAL PROTO PATH, byte-identical bytecode
  |     ProcessLocalizedTextWithCallback(Format As Subtitle Text With Tags) -> Apply Speaker Name if Needed
  |     -> SetText x2 -> PrintLetterByLetter x2 | ShowText x2 ; OnPrintLetter -> RequestRender x2 ; finish delegate
  |     Arabic layer: Collapsed
  |
  `-- bArabic == true: ARABIC PATH
        ProcessLocalizedTextWithCallback(Format As Arabic Plain: strip <Italic>, </>)
        speaker prefix = SpeakerName + ":" if SubtitleSpeakerNamesEnabled && !TextIsEmpty(SpeakerName)
        SEGMENTATION (segment_units.py rules): whitespace-only cuts, letterless tokens join previous,
          speaker units first, overflow tail-merge (37 | 128), escape & " < >
          -> markup "<u0>..</> <u1>..</> ..", UnitCount, SpeakerUnits, per-unit delays (0.025 s x letters)
        Proto texts: SetText("") + Collapsed
        ArabicThreshold = -1 -> SetThreshold   (BEFORE SetText: pooled block never flashes old text)
        ArabicShadowText.SetText(markup); ArabicText.SetText(markup)   (ONLY layout mutation of the line)
        FINAL LAYOUT: stock URichTextBlock, Justification Center, AutoWrap 1050, full shaping, BiDi auto
        Arabic layer SelfHitTestInvisible; RequestRender x2 now and on next tick
        typewriter on : ArabicThreshold = SpeakerUnits-1 ; K2_SetTimerDelegate(Arabic Step, delay[next])
        typewriter off: ArabicThreshold = UnitCount-1 ; Arabic Finish

  SetThreshold(t)  (single writer for every layer of the block)
        R8b: tint = (1, 1, t<0 ? 0 : 10.5^min(t,36), 1)     R8: tint = (1, srgb_to_linear((t+1)/255), 1, 1)
        ArabicFgBorder.SetContentColorAndOpacity(tint); ArabicShadowBorder.SetContentColorAndOpacity(tint)
        ArabicRetainer_H/V.RequestRender() [+ fg colour retainer in R8]

  Arabic Step: ++t; SetThreshold(t); if t == UnitCount-1 -> Arabic Finish else re-arm timer with delay[t+1]
  Arabic Finish (idempotent; guard flag): clear timer; SetThreshold(UnitCount-1); call existing
        "On Finish Letter by Letter Print" delegate once
  Skip (typewriter disabled or external skip) = Arabic Finish
  Stop Displaying Line: existing SubtitleOverlay Hidden + clear timer + SetThreshold(-1) + Arabic layer Collapsed
  Pool reuse: everything above is per-block state; Set Displayed Line always resets to -1 first

WIDGETS (inside Overlay_0, beside the English children; no ancestor RGB tint)
  fg:     [R8 only: RetainerBox(EffectMaterial=M_ArabicColorize MID, SubtitleColor)] -> ArabicFgBorder -> ArabicText
  shadow: ArabicRetainer_H(MI_UI_TwoPassBlur_Horiz) -> ArabicRetainer_V(MI_UI_TwoPassBlur_Vert)
          -> ArabicShadowBorder -> ArabicShadowText        (Border INSIDE the retainers)

ROWS (one table serves fg and shadow; the shipped blur keeps only the retained alpha)
  Default (index 0) + u0..u(N-1); identical font (Montserrat-Variable, Medium, 28 | 36 Large), size, spacing
  colour: R8b (1,1,10.5^-i,1)   R8 (srgb_to_linear((i+1)/255),1,1,1)
  outline tables: OutlineSize 2, OutlineMaterial (R8b MI_SubtitlePrinting_Bold | R8 black reveal MIC), OutlineColor = row colour
  tables: Fill, Fill_Large, Outline, Outline_Large   (R8b 38 rows ~0.14 MB each; R8 129 rows ~0.46 MB each)

MATERIAL / INDEX CHANNEL
  R8b: shipped M_SubtitlePrinting: emissive = Color/VC (x VC by Slate), opacity = sat((VC.b-0.1)*1.11)
  R8 : idx = round(linear_to_srgb(VC.r)*255)-1, thr = round(linear_to_srgb(VC.g)*255)-1, vis = idx<=thr,
       out = (SubtitleColor/max(VC,1e-6), vis)
OUTLINE: same widget, same rows, outline geometry carries the same code (4.27 tint factor: VERSION_SENSITIVE)
SHADOW : second RichTextBlock, same markup, same threshold writer, inside the existing blur retainer pair
MODES  : Set Has Outline -> Arabic fg table Outline/Fill + shadow retain/visibility as English;
         ChangeTextToLarge -> *_Large tables (init time only, never during reveal)
```

English isolation: no English export, function, delegate or animation is changed. The Arabic code runs only behind `bArabic`, which is evaluated after the shared profanity call. The shared parts are the profanity filter, `Update Text Color` and the letterbox nodes, and these execute exactly as before.
