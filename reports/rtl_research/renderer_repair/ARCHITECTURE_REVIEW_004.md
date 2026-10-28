# Architecture gate review — round 004 (Opus 5.5)

```text
STOCK_ENGINE_REPAIR_ROUTE_IDENTIFIED   (identified at design level, NOT proven)

STOCK_RENDERER_ROUTE:        NOT_PROVEN
BLUEPRINT_ARABIC_BRANCH:     REQUIRES_UNSUPPORTED_EDIT   (with current UAssetAPI tooling)
EXISTING_NATIVE_CLASS_ROUTE: REJECTED
NATIVE_MODULE_LOADING:       NOT_FOUND   (NATIVE_MODULE_LOADING_NOT_FOUND)
CUSTOM_NATIVE_RENDERER:      BLOCKED_BY_DELIVERY

DYNAMIC_MARKUP_ROUTE:        REJECTED_AS_PRIMARY (per-step SetText relayout); geometry-stable in model only
GAME_NOT_RUN  STEAM_NOT_RUN  PACKAGE_NOT_INSTALLED  IN_GAME_RTL_NOT_PROVEN  tested_in_game=0  final=0
```

## 1. Verdict on round 003

Round 003's renderer logic is right: freeze the final shaped layout, then change only
per-unit visibility. Its **deployment vehicle** does not work. The preferred
`UArabicSubtitleRevealWidget` is a new native UClass. This shipping build has no way
to load one (section 9). Round 003 already called delivery "unresolved". This round
upgrades that to "not found, with evidence". The native-renderer recommendation is
withdrawn.

The replacement recommendation keeps round 003's model (final geometry, one mask,
two passes) but builds it from classes already in the EXE:

```text
stock URichTextBlock (final Slate layout, HarfBuzz + ICU BiDi, full shaping, RTL flow)
+ whitespace-only run boundaries (one rich run per word unit)
+ each unit's index encoded in its style row's colour (one row per unit, same metrics)
+ a new UI font material: visible iff unit index <= reveal threshold
+ the threshold stored in a tiny cooked render-target asset,
  written per step with stock ClearRenderTarget2D
=> text set ONCE per subtitle line; reveal steps never touch text, styles or layout
```

Everything native in this chain is shipped engine code. The new parts are only
**assets**: a material, material instances, render targets, generated DataTables, and
a modified WBP_SubtitleBlock. Section 4.3 lists what keeps the route at NOT_PROVEN.

Evidence labels: CONFIRMED_FROM_BINARY (hash-locked name/structure evidence in
`exe_names.json`; name presence only, not behaviour), CONFIRMED_FROM_ASSET,
DETACHED_MODEL_TESTED (`run_boundary.json`), ENGINE_SOURCE_RECALL (UE4.27 engine
behaviour from knowledge, not checked against 4.27 source this round),
DESIGN_INFERENCE, NOT_PROVEN.

## 2. Evidence base (new this round)

| Fact | Evidence | Class |
|---|---|---|
| Stock UMG classes compiled in: URichTextBlock, URichTextBlockDecorator, URichTextBlockImageDecorator, UTextBlock, URetainerBox, UInvalidationBox, UOverlay, UCanvasPanel, UWidgetSwitcher, UImage | wide registration names, e.g. `URichTextBlock` @0x35bc910 | CONFIRMED_FROM_BINARY |
| FRichTextStyleRow, FTextBlockStyle, FSlateFontInfo.FontMaterial, FFontOutlineSettings.OutlineMaterial, ShapedTextOptions, ETextFlowDirection::RightToLeft, ETextShapingMethod::FullShaping | narrow reflected names | CONFIRMED_FROM_BINARY |
| URichTextBlock BP API: SetText, SetTextStyleSet, SetDefaultTextStyle/Font/ColorAndOpacity/ShadowColorAndOpacity, ClearAllDefaultStyleOverrides, GetDecoratorByClass, SetAutoWrapText, SetMinDesiredWidth, SetJustification, SetTextTransformPolicy | contiguous names @0x35bb7f0..0x35bb8f8 | CONFIRMED_FROM_BINARY |
| No per-run/per-range visibility or colour setter; no SetDefaultMaterial / SetFontMaterial | absent as reflected names | CONFIRMED_FROM_BINARY (name absence) |
| UKismetInternationalizationLibrary with GetCurrentLanguage, GetCurrentCulture, GetCurrentLocale, GetNativeCulture, GetSuitableCulture, SetCurrentLanguage | names @0x395d6d0..0x395d7b0 + class name | CONFIRMED_FROM_BINARY |
| UDispatchLanguageSetting + `OnLanguageSettingValueChanged` + "Language" settings row | wide/narrow names @0x32f2480, 0x32f2030, 0x32e15b0 | CONFIRMED_FROM_BINARY |
| UKismetRenderingLibrary: ClearRenderTarget2D, CreateRenderTarget2D, DrawMaterialToRenderTarget; UTextureRenderTarget2D; K2_SetTimer, ParseIntoArray, Delay | names | CONFIRMED_FROM_BINARY |
| **ProtoRichTextBlock derives from URichTextBlock** | WBP export 19 calls `/Script/UMG:RichTextBlock:SetTextStyleSet` on SubtitleProtoText / SubtitleShadowProtoText | CONFIRMED_FROM_ASSET |
| Blueprints are bytecode, not nativized; classic paks; shared shader code | DefaultGame.ini: BlueprintNativizationMethod=Disabled, bUseIoStore=False, bShareMaterialShaderCode=True | CONFIRMED_FROM_ASSET (config) |
| Cooked packages use stock serialization flags | FileVersionLicenseeUE=0, unversioned, event-driven loader (WBP, DT, material) | CONFIRMED_FROM_ASSET |
| Monolithic EXE; no engine C++ exports | FStaticallyLinkedModuleRegistrant RTTI ×2; 269 PE exports = libpng/AMD AGS/driver hints, 0 mangled C++ | CONFIRMED_FROM_BINARY |
| No game/plugin module DLLs or `.modules` manifests; only third-party DLLs | install listing in exe_names.json | CONFIRMED_FROM_INSTALL_LISTING |
| No script runtime (UE4SS/UnLua/Python runtime names absent) | exe_names.json | CONFIRMED_FROM_BINARY (name absence) |
| Custom engine tree at `E:\DispatchBuilder\Storyboard_Mode\Game\UnrealEngine` | source-path strings in EXE | CONFIRMED_FROM_BINARY |

Reproduce: `python -X utf8 tools/rtl_renderer_prototype/exe_names.py` (refuses any
other EXE hash) and `python -X utf8 tools/rtl_renderer_prototype/run_boundary.py`.

## 3. Stock renderer investigation

| Shipped type | Can it supply final shaped Arabic layout? | Can it change per-unit visibility without relayout? | Role |
|---|---|---|---|
| URichTextBlock / SRichTextBlock | Yes: stock FSlateTextRun paint of the final layout; FullShaping and RTL flow are reflected options (ENGINE_SOURCE_RECALL for the paint path) | No direct API. Only through a material channel (4.3) | **Arabic layout owner** |
| UTextBlock / STextBlock | Yes for one style | One colour for the whole text; no per-unit channel | Rejected (no per-unit identity) |
| Per-word UTextBlock in a WrapBox/CanvasPanel | Each word shapes correctly | Yes (per-widget opacity) | **Rejected**: re-implements BiDi word ordering and wrapping outside the engine. "SDN 250 XP" inside an RTL line would need UBA reordering that depends on line breaks |
| URetainerBox (+ effect material) | No (container) | Effect material sees only retained pixels. It has no glyph or unit identity | Shadow blur stays here (existing MI_UI_TwoPassBlur_*). Needs RequestRender per step |
| UInvalidationBox | No | No; caching only | Optional performance only |
| UOverlay | — | — | Holds the Arabic layer beside the English one |
| UWidgetSwitcher | — | — | Optional language switch (visibility toggling is enough) |
| Existing text material M_SubtitlePrinting | — | Driven by ProtoRichText_Data per-character data written by Proto's logical-pen paint loop | Rejected (tied to the defective paint path) |
| RichText decorators present: URichTextBlockImageDecorator, Proto Image/Widget/CharColor decorators | — | The image decorator only handles images. Proto decorators run inside Proto's paint path | Rejected |

## 4. RichTextBlock investigation

### 4.1 What URichTextBlock can and cannot do at runtime

All shipped URichTextBlock mutators either replace the text (SetText → re-marshal,
reparse, relayout) or replace or override styles. That means SetTextStyleSet → style
rebuild + refresh, and the SetDefault* overrides → new default style + layout
invalidation (ENGINE_SOURCE_RECALL). None of them changes one run's alpha in place.
So a pure-widget reveal on a stock URichTextBlock **always relayouts per step**.

### 4.2 Dynamic markup route (classified separately)

Moving the tag boundary each step, e.g. `<visible>مرحبا</><hidden> بالعالم</>` →
`<visible>مرحبا بالعالم</>`:

- Causes per step: SetText, reparse, new runs, relayout and rewrap. Reshaping is
  likely; whether the shaped-text cache hits is NOT_PROVEN.
- Geometry (detached model): if every boundary is at whitespace, intermediate and
  final layouts are identical (40/40 below). A boundary at a non-space position is
  **not** identical (kerning and script itemization change, below). The naive
  `<visible>/<hidden>` markup above is safe only because its boundary is a space.
- Fixed segmentation (each word always its own run; only the row name changes from
  hidden to visible) keeps the run structure identical at every step. It still does
  a full SetText or style-set relayout per step.

Classification: **REJECTED_AS_PRIMARY**. It breaks the "layout stays stable during
reveal" requirement through per-step relayout. Geometric identity holds in the
detached model only, not in Slate. Keep it as a documented fallback for the
supervisor to decide on if the material channel (4.3) fails gate G1–G3.

### 4.3 Proposed: index-encoded colour + reveal material (no per-step relayout)

```text
per subtitle line, once:
  Arabic markup = stock RichText tags, one tag per word unit:  <s0_Default_u7>كلمة </>
  ArabicText.SetText(markup)           (foreground URichTextBlock)
  ArabicShadowText.SetText(markup)     (shadow URichTextBlock in its own RetainerBox pair)
per reveal step:
  ClearRenderTarget2D(RT_ArabicReveal_S0, (threshold, 0, 0, 1)); RequestRender on retainers
```

- **Rows**: generated FRichTextStyleRow DataTables (DT_ArabicReveal, _Large). One row
  per (pool slot × style variant × unit index). All rows share font, typeface, size,
  outline width and letter spacing, so they share metrics. They differ only in
  ColorAndOpacity (and OutlineColor), whose R byte encodes the unit index, and in
  which material instance they use.
- **Material**: new UI-domain font material M_ArabicReveal. It samples the slot's
  render target and outputs coverage only when unitIndex <= threshold. Colour comes
  from a material parameter or a global colour RT, not from the vertex colour.
  Static MICs per slot and per foreground/shadow mean foreground and shadow read
  **the same RT**. That gives one mask and two passes by construction, never two
  clocks.
- **Units**: whitespace-delimited words. A token with no strong letter (a standalone
  "—" or "...") merges into a neighbour. Speaker or donthide text is unit 0, always
  visible. No boundary inside a word, so no shaping cluster, ligature, mark or
  kerning pair can be split.
- **Timing**: a Blueprint timer advances at Proto's 0.025 s cadence per counted
  character. A unit becomes visible when its last character is due, which is round
  003's `ready(U) = max(native ready times)`. Finish/skip set threshold = last unit
  and fire the existing finish delegate once.
- **English**: untouched Proto foreground/shadow objects and calls. The Arabic layer
  stays Collapsed unless the language gate passes.

Forbidden techniques avoided: no Reverse(), Presentation Forms, prefix shaping,
logical pen, per-letter substring, horizontal clip, partial-word reshaping,
cluster splitting or English change.

**Gating unknowns (each can reject the route):**

| Gate | Question | How to settle (no game run needed) |
|---|---|---|
| G1 | Does a UI font material on a rich-text run receive the run colour as VertexColor, and is glyph coverage still applied? | UE4.27 editor, UMG designer/PIE, stock RichTextBlock |
| G2 | Vertex colour quantization: 8-bit, sRGB-encoded or linear in the material? | Same editor test; result sets a calibration switch in M_ArabicReveal (keep the knob) |
| G3 | Does a cooked RT sampled in a font material update per ClearRenderTarget2D inside RetainerBox-retained and normal paint? Does the outline material path behave the same? | Same editor test |
| G4 | New material shaders under bShareMaterialShaderCode=True: a mod-side shader library, or cook with inline shader code | Cook test + static pak inspection; in-game proof stays NOT_PROVEN |
| G5 | Pool slots: how many WBP_SubtitleBlock instances can reveal at once? Does any ancestor tint RGB, which would corrupt the index? (RenderOpacity is alpha-only) | Static BP audit of WBP_SubtitlesWidget + animation tracks |

Material Parameter Collections are a second threshold channel. Whether Slate's
material view binds the world's MPC buffer in 4.27 is NOT_PROVEN (suspected not).
The render-target channel is preferred.

## 5. Run-boundary shaping results (detached HarfBuzz + UBA model)

Each run is shaped separately, as Slate does per rich-text run. Two variants were
run: with HarfBuzz pre/post context and fully isolated, because Slate 4.27's choice
is not verified. The model uses the fonts from the existing oracle: Montserrat-Medium
(.ufont) and the engine's NotoNaskhArabicUI.

| Cut placement | Comparisons | Identical geometry (glyph ids, clusters, x/y, advances, line ranges) |
|---|---|---|
| word start (after whitespace) | 10 cases × 2 context modes | **20/20** |
| word end (before whitespace) | 10 × 2 | **20/20** |
| word + punctuation (cuts at letter/punct edges too) | 10 × 2 | 10/20. Fails: mixed_test42, version, multiline, punctuation, long_wrap |
| NEG: mid-word cut (control) | 10 × 2 | defect detected: 10/10 isolated, 5/10 with context |

Cases: السلام عليكم · السَّلَامُ عَلَيْكُمْ · لا إله إلا الله · مرحبا TEST-42 بالعالم ·
الإصدار v1.02 متاح الآن · السعر 50 USD اليوم · multiline (explicit newline) · speaker
prefix · Arabic/Latin punctuation and brackets · long multi-line wrap.

Diagnosed failures: Latin kerning lost across `T|-` (20.683 → 21.915 px) and `1|.`
(8.027 → 8.475 px). Punctuation-only runs also get a different script, which gives a
different glyph (`.`/`!` gid 5/4 → 1517/1516, 7.67 → 10.0 px). Line ranges were
identical in every case, including the failing ones.

Rule: **rich-run boundaries only at whitespace**, and every unit must contain a
strong letter. This preserves joining, lam-alef and other ligatures, marks,
kerning, mixed BiDi and wrapping in the model. Slate/ICU parity is NOT_PROVEN.

## 6. Blueprint edit feasibility (WBP_SubtitleBlock, cooked, not modified)

| Edit kind | Needed for Arabic branch | Current UAssetAPI 1.1.0 tooling status |
|---|---|---|
| Property edit on existing export | Yes (Arabic layer visibility defaults) | **Proven**: round-trip in `--layout-prototype` (5 exports changed, 32 byte-identical) |
| Widget-tree structural edit (new widget + slot exports, re-parenting) | Yes (2 RichTextBlocks, Overlay slots, 2 RetainerBoxes) | Serializable in principle. Not exercised; no validator for WidgetTree/BPGC consistency |
| New object export | Yes | Same as above |
| New class/function/struct import | Yes: RichTextBlock class is already imported (-24); also GetCurrentLanguage, ClearRenderTarget2D, K2_SetTimer, string helpers, new DataTables/RTs | Appending imports is supported by the library. Not exercised |
| New BPGC property (FProperty) for the new widget variables | Yes | Not exercised |
| Kismet bytecode edit / new function | Yes: language branch, markup build, timer, finish/skip | Library reads and writes bytecode. **No compiler**: jump offsets, ubergraph frame layout and persistent-frame properties would be hand-authored, with no semantic check |

Classification: **REQUIRES_UNSUPPORTED_EDIT** for the current tooling. A route that
could work is to author the modified WBP in a stock UE4.27 editor (Launcher build).
It would need a stub project named Dispatch, with header-only stub UCLASSes matching
the reflected names and signatures this BP uses:
ProtoAnimatedText (or the licensed Marketplace plugin), Dispatch, AdHocUtils and
AdHocSubtitles types. That route is NOT_PROVEN and is not attempted here. Cooked
packages are unversioned with LicenseeUE=0, which favours stock-cook
compatibility; the custom engine tree means this is not guaranteed.

A large part of the markup work can move out of Blueprint. A build-time tool can
write unit-tagged stock RichText markup into the Arabic locres only. English locres
and English bytecode never see it. Censorship/callback and speaker formatting in Set
Displayed Line still need an Arabic-side equivalent. That is integration work.

## 7. Language gate

`UKismetInternationalizationLibrary::GetCurrentLanguage` is a shipped static
BlueprintPure function (name evidence above). A cooked BP can call it through a new
import with no new native code, and test the prefix `ar` (covers `ar`, `ar-SA`)
against `en` / `en-US`. The game also ships its own `UDispatchLanguageSetting` with an
`OnLanguageSettingValueChanged` delegate. That is the in-game language option, so
the stock culture should follow it (NOT_PROVEN in-game). Whether an `ar` culture can be
selected at all is still NOT_PROVEN (CulturesToStage=en only; ICU preset All). Per
subtitle, snapshot the language once. Character detection is not used.

## 8. Existing renderer/class search (narrow)

Searched: WBP import tables (`WBP_SubtitleBlock`: 95, `WBP_SubtitlesWidget`: 125),
plugin descriptors in the pak index, and reflected class names `U*TextBlock`,
`U*Decorator`, `U*RichText*`. Found game/plugin text classes: UProtoRichTextBlock,
UProtoRichTextCharColorDecorator, UProtoRichTextImageDecorator,
UProtoRichTextWidgetDecorator, UCommonRichTextBlock, UCommonTextBlock, UCommonTextStyle.

- Proto*: the character paint is the proven logical pen (round 002). Rejected for
  Arabic reveal.
- CommonUI text: reflected setters are layout/case/scroll only (SetTextCase,
  SetWrapTextWidth). No per-run opacity or reveal API. Rejected.

No shipped widget combines final layout, rich text, per-run opacity and BP access.
**EXISTING_NATIVE_CLASS_ROUTE: REJECTED** within this scope. The stock route uses
generic engine classes. It does not repurpose a reveal class.

## 9. Native class loading gate (UArabicSubtitleRevealWidget)

| Requirement | Finding |
|---|---|
| Compile | UE4.27 headers + UnrealBuildTool + UnrealHeaderTool + MSVC v142 (VS2019) + Windows SDK. None discovered locally (round 003 inventory) |
| ABI | Must match the exact custom engine build (`E:\DispatchBuilder\...\UnrealEngine`). The EXE exports **0** engine C++ symbols, so an external module has nothing to link against |
| UClass registration | Needs the module's static registrants to run in-process followed by UObject processing. That happens only through module load or static link |
| Module loading | Monolithic build (FStaticallyLinkedModuleRegistrant RTTI). The UE4.27 monolithic FModuleManager resolves only statically linked initializers (ENGINE_SOURCE_RECALL). No module DLLs or `.modules` manifests exist |
| Plugin discovery | Present: `Mods/`, `PLUGIN=`, `EnablePlugins=`, `AdditionalPluginDirectories`, `.upluginmanifest`, plugin `*.pak` scanning. It brings descriptors/content only. A code module in a discovered plugin hits "PluginModuleNotFound" (string present) |
| Asset cooking | A WBP that imports `/Script/<NewModule>.ArabicSubtitleRevealWidget` can be cooked in an editor that has the module. In game, the import cannot resolve |
| Blueprint reference resolution | Missing /Script class, so the widget is null or the package fails to load. Both are unacceptable |

**NATIVE_MODULE_LOADING_NOT_FOUND**: no way to load a new native module without
modifying the EXE, a proxy DLL, UE4SS or injection, all of which are outside the
current constraints.

## 10. UE4.27 SDK — exact dependency list (for an isolated renderer test only)

- Modules: Core, CoreUObject, ApplicationCore, InputCore. SlateCore
  (FSlateDrawElement, FSlateFontCache, FShapedGlyphSequence, FSlateFontInfo, font
  atlas/shader resources, MakeCustomVerts). Slate (FTextLayout, FSlateTextLayout,
  FSlateTextRun, ISlateRun, FRichTextLayoutMarshaller, SRichTextBlock). UMG (UWidget,
  UTextLayoutWidget, URichTextBlock, FRichTextStyleRow). Engine (UMaterialInterface for
  font materials, UDataTable, UFont/UFontFace). RenderCore/RHI only for custom
  vertex/material work.
- ThirdParty: HarfBuzz, ICU 64 (the EXE carries `icu_64` RTTI), FreeType2.
- Tools: UBT, UHT, MSVC v142, Windows 10 SDK. A standalone Program target needs a
  source engine. A Launcher engine can only build game/editor modules.
- The **stock route needs no C++ at all**. It needs a Launcher UE4.27 editor to
  compile/cook one material, MICs, RTs, DataTables and the edited WBP. Stub UCLASS
  headers are needed only if the WBP is re-authored in the editor.

## 11. Game delivery

- Content: `_P.pak` priority override (string present). No `.sig` files ship, so no
  pak-signing evidence was found. This is the existing route of the project's
  ar-only text PAK (not installed). Cooked BP/material/DataTable/RT assets can be
  delivered this way (NOT_PROVEN in-game).
- Native code: none (section 9).

## 12. Proto-source route

Even with ProtoAnimatedText source, a fix must be compiled into the monolithic
Dispatch-Win64-Shipping.exe. The plugin has no DLL; its uplugin declares a Runtime
module that is statically linked. That means **rebuilding Dispatch from the
developer's game source and custom engine**, which only the developer can do. It is
not a mod-side route. It stays the cleanest *upstream* fix (report to the developer).

## 13. Decision tree

```text
Can stock shipped classes implement correct reveal?
  Layout: YES — URichTextBlock final Slate layout (classes CONFIRMED_FROM_BINARY;
          paint path ENGINE_SOURCE_RECALL; whitespace runs geometry-neutral in model)
  Per-unit visibility without relayout: ONLY via index-colour + reveal material + RT
          (all native pieces shipped; behaviour gates G1–G3 NOT_PROVEN)
  => YES at design level -> blueprint/data integration route  [SELECTED, NOT_PROVEN]
       requires: UE4.27 editor cook of new assets (G4) + WBP Arabic branch
                 (REQUIRES_UNSUPPORTED_EDIT with current tooling)
     if G1–G3 fail -> dynamic-markup fallback (per-step relayout) is a supervisor
                      policy decision, else fall through:
Can an existing shipped native class be repurposed?
  NO — Proto (logical pen, CONFIRMED_FROM_BINARY), CommonUI (no reveal API)
Can the shipping build load a new legitimate native module?
  NO — monolithic, 0 engine exports, no module DLL/.modules, plugin discovery
       is content-only (NATIVE_MODULE_LOADING_NOT_FOUND)
Otherwise requires: game/source rebuild by the developer, an approved runtime loader,
  or binary intervention — all outside current constraints.
```

## 14. What remains unproven

G1–G5. Slate's per-run shaping context and ICU breaking versus the model. Stock-cook
compatibility with the custom engine tree. Arabic culture selection in game. The
Arabic-side censorship/speaker equivalent. Blueprint authoring and pooling. Any
in-game rendering. Nothing was installed, cooked or run.
