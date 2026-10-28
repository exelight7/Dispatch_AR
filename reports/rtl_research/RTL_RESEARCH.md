# Dispatch Arabic RTL and typewriter investigation

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


# Round 009 latest result — R8B_WBP_STAGE1_PASS (offline only)

Four R8b tables, 38 rows each, and the detached WBP's seven-widget/seven-slot hidden Arabic subtree are generated.
Named BPGC widget fields and four DataTable handles serialize/reread; widget CDO defaults are null, matching the source.
Original 21 function payloads/raw script bytes are unchanged; 34/37 original export payloads are identical, with only
BPGC/CDO/Overlay_0 structural changes. Independent validation, ten negative tests, deterministic generation and binary
reread/serialize pass. General project verification: STATIC_PASS 25/25. Evidence: `renderer_repair/WBP_STAGE1_RESULT.md`.
Next: the prepared `WBP_STAGE2_BYTECODE_MAP.md`. No Kismet mutation, installation or runtime proof in this round.
`DISPATCH_INTEGRATION_PROVEN=false; IN_GAME_RTL_PROVEN=false; tested_in_game=0; final=0`.

---

Status: research only, 2026-10-23. No game launch, asset modification, runtime probe, Arabic rendering result or typewriter result was performed by this research role. Only this folder is owned for writes. The engine version and actual Dispatch rendering path must be established by the coordinator.

## Native Arabic first

UE 4.27 documents native Arabic shaping: `FullShaping` handles complex RTL and bidirectional text; `KerningOnly` is unsuitable; `Auto` selects full shaping for RTL. This supports trying normal Arabic Unicode through the game's existing Slate/UMG renderer before considering preprocessing. It does not prove Dispatch uses this path or has left it enabled. [UE-SHAPE](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/TextShapingMethod.html?application_version=4.27)

Keep stored text in logical order. Bidirectional display order and contextual glyph shaping are separate operations. Reversing Arabic codepoints or replacing letters with presentation forms before passing them to a capable renderer risks double processing, broken numbers and punctuation. This recommendation follows Unicode's logical-order model and contextual shaping requirements. [UAX9](https://www.unicode.org/reports/tr9/)

For the first identified dialogue/menu text widget, inspect these candidates without assuming their cooked serialization names or offsets:

| Concern | Research target | Meaning |
|---|---|---|
| Complex rendering | TextBlock `simple_text_mode` | Must be disabled for Arabic; this optimization bypasses shaping, wrapping and justification. |
| Glyph shaping | `shaped_text_options.text_shaping_method` plus `override_text_shaping_method` | Use FullShaping for a controlled PoC, or verify working Auto behavior. |
| Paragraph direction | `text_flow_direction` plus `override_text_flow_direction` | RTL for a known Arabic paragraph; Auto needs testing with leading Latin labels/numbers. |
| Text alignment | `justification` | Right alignment controls text within its available area. |
| Widget geometry | Actual parent slot, size, anchors, offsets and alignment | Controls the text area's position and stability. |
| Bounds | Wrap width, margins, line height and clipping | Verify long dialogue and marks at the top/bottom of lines. |

These are documented engine properties, not proposed binary field patches. In 4.27 `TextFlowDirection` is Auto=0, LeftToRight=1, RightToLeft=2; the newer `Culture` enum option is absent from this pinned reference. Override flags matter: changing a value while leaving its override inactive can leave the default effective. [UE-OPTIONS](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/ShapedTextOptions.html?application_version=4.27), [UE-FLOW](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/TextFlowDirection?application_version=4.27), [UE-TEXT](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/TextBlock?application_version=4.27), [UE-LAYOUT](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/TextLayoutWidget?application_version=4.27)

Right justification is separate from right anchoring. If the actual parent is a CanvasPanel, inspect the slot's anchors, alignment and offsets. A fixed-width dialogue box can retain its existing geometry and use right-justified text. A content-sized box may need its right edge pinned, but selecting anchor/alignment values requires the actual layout. Avoid mirroring the whole HUD to repair one text paragraph. [UE-SLOT](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/CanvasPanelSlot?application_version=4.27)

Verify the exact Font/FontFace chain, style names, Arabic coverage and metrics. Runtime composite fonts can select sub-font families by character range. Font availability alone does not establish shaping success; contextual substitutions and mark positioning depend on shaping data and the renderer. Also inspect packaged ICU data before relying on Arabic culture selection. [UE-FONT](https://dev.epicgames.com/documentation/unreal-engine/font-asset-and-editor?application_version=4.27), [HB-SHAPE](https://harfbuzz.github.io/what-is-harfbuzz.html), [UE-I18N](https://dev.epicgames.com/documentation/unreal-engine/localization-overview?application_version=4.27)

## Typewriter: preserve the complete layout

Engineering recommendation, not a verified Dispatch implementation: shape and wrap the complete final paragraph once at the final width, then reveal its existing glyph groups. Keep final line breaks, advances, alignment and positions while changing visibility. Replacing the text with successively longer prefixes can change the last Arabic letter's contextual form, its advance, joining, and wrapping. Fixed outer box width alone does not prevent this. The reason is contextual shaping; line width must be measured from shaped glyphs. [UAX9](https://www.unicode.org/reports/tr9/)

Reveal units need two mappings:

1. Segment logical source text at extended grapheme boundaries so a combining mark is not independently revealed or a surrogate sequence split. Raw byte, UTF-16-unit or codepoint counts are insufficient as general user-perceived character counts. [UAX29](https://www.unicode.org/reports/tr29/)
2. Map those source ranges to complete shaped clusters. Multiple graphemes can become one ligature, such as a lam-alef form. Do not paint half that cluster. A conservative policy delays a merged cluster until all its source graphemes are due; document this timing choice. HarfBuzz cluster IDs track source-to-glyph grouping, and RTL visual output order is not source-index order. [HB-CLUSTERS](https://harfbuzz.github.io/clusters.html), [HB-MAPPING](https://harfbuzz.github.io/working-with-harfbuzz-clusters.html)

For mixed Arabic, Latin and numbers, logical reveal may correspond to disjoint visible regions. A single rectangle moving from right to left is therefore not a complete general solution. Per-cluster paint visibility or equivalent masks over the final layout are candidates only if the actual renderer exposes enough control. Adding rich-text color spans or replacing hidden glyphs with spaces may alter shaping/run boundaries and needs its own proof. Whole-word reveal is a possible fallback only if the agreed requirement allows it; it does not demonstrate character reveal.

Inspect the existing typewriter implementation before choosing a patch route: source-prefix substring updates, per-letter widgets, rich text decorators, material masking, or native painting have different failure modes. Preserve timing, skip-to-end behavior, pause cues and dialogue progression. An opportunistic `SetText` runtime call can remove the original property binding; account for that if the final implementation uses it. [UE-TEXT](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/TextBlock?application_version=4.27)

## Cooked asset versus runtime boundary

Inspection can identify exported widget properties, font references, asset dependencies and whatever executable Blueprint bytecode survives cooking. It cannot establish the live native call path from defaults alone. Epic documents cooked content as read-only in normal editor workflows, with Blueprint limitations and dependent `.uexp`/`.ubulk` files. Exported JSON is diagnostic data, not a recookable source project. A default property may also be overwritten by runtime bindings. [UE-COOKED](https://dev.epicgames.com/documentation/en-us/unreal-engine/working-with-cooked-content-in-the-editor?application_version=4.27)

The Python API pages above document engine schema. They are not a way to execute Python inside the shipped game: Epic restricts that environment to the editor. Likewise, a new custom C++/Slate renderer cannot be made active merely by placing source code into a pak. A verified native extension/hook route, an existing game extension point, or matching source/build integration would be required. This is an implementation constraint, not evidence that a particular runtime tool is compatible. [UE-PYTHON](https://dev.epicgames.com/documentation/en-us/unreal-engine/scripting-the-editor-using-python?application_version=4.27)

## Minimum actual-game acceptance evidence

Run a deliberately tiny, identified test set only after reversible packaging and integrity checks are ready. Suggested probe strings are test data, not full translation:

| Probe | Text | Observe |
|---|---|---|
| Joining | `مرحبا بالعالم` | Connected contextual forms, right start, natural spacing. |
| Ligature/marks | `لا لَا مُهِمّ` | No isolated marks, broken joining or partial lam-alef. |
| Mixed direction | `اتصل بـ Robert على 123، الآن!` | Latin name/number order and punctuation. |
| Leading Latin | `SDN: المهمة جاهزة (12/30).` | Stable paragraph direction and brackets. |
| Wrap | A long Arabic sentence at actual dialogue width | Stable final wrapping throughout reveal. |

Capture real game frames at start, several reveal steps, first line wrap and completion, plus short video if possible. Check menu/static text separately from animated dialogue; passing one does not pass the other. Check skip, next line, rich text and inline icons using the game's real syntax. Full translation remains gated on visible Arabic, stable right anchoring, joined shapes, correct mixed text and acceptable typewriter behavior. No screenshot, synthetic preview, or static asset report alone proves all these conditions.

## Limited exe string scan (2026-10-23, read-only)

Historical round 001 section. The later round 002 below supersedes its "no disassembly" statement; the string-presence results remain valid.

`Dispatch-Win64-Shipping.exe` (73,869,896 bytes) contains the reflected names of the ProtoRichTextStyleRow timing fields. They match the DataTable serialization exactly. It also contains the `EProtoRichTextSpecialCharacter::PRT_{NONE,SPACE,COMMA,MIDWORDDASH,ENDOFSENTENCE,ELLIPSIS}` enum, and the adjacent UTF-16 literals `donthide`, `style`, `s`, `,`, `!`, `?` next to the UProtoRichTextBlock handlers. CONFIRMED_FROM_BINARY as strings only. Their use (classifier set, donthide counting) is not proven. Native names `PlayNextLetter`, `CurrentCharacterIndex`, `CharPrintPercent`: NOT_FOUND. No disassembly was done.

## Round 002 — focused read-only binary analysis

Both requested questions are resolved for executable SHA256 `365637a77d4b74a61d198a9927e3dcd437bf3be2247b96fcbe5c2e851ac14923`:

- `PAINT_MODEL_LOGICAL_PEN`: confirmed from the char-color decorator factory/run/vtable chain and the one-unit shaped-slice paint loop at RVA `0x9a2bd0..0x9a368c`.
- `ZERO_INTERVAL_BATCHES_CHARACTERS`: confirmed from interval selection, synchronous zero-entry branch, advancing reveal-budget loop and subsequent scheduling boundary.
- `WORD_REVEAL_REJECTED` for the timing-only approach. Zero batching does not repair accumulated logical-order x placement.

The evidence pack `proto_binary/` records exact RVAs, file offsets, 21 logical function spans, xrefs, all eight row-field offsets, limited disassembly and a hash-locked Python reproducer. Public tutorial code remains `PUBLIC_REFERENCE_ONLY`; this verdict does not rely on it being identical to the shipped implementation.

There is no classification blocker requiring source. No native fix/integration was built; Arabic isolation and actual-game results remain unproven. No game/Steam execution, debugger, hooks, DLLs, executable edits or PAK installation. `tested_in_game=0`, `final=0`.

## Round 003 — detached renderer repair prototype

Result: `RENDERER_REPAIR_PROTOTYPE_BUILT`, detached Python/SVG/PNG only. Existing binary evidence remains unchanged. Two WBP exports show typed Proto foreground/shadow fields, no ready culture gate, no WidgetSwitcher and no spare ordinary text child. The proposed new-renderer route requires native integration plus Blueprint routing; Arabic isolation remains unproven.

Architecture and UE primitive/route matrices: `renderer_repair/ARCHITECTURE.md`; primary references/version caveats: `renderer_repair/SOURCES.md`; reproducible asset findings: `renderer_repair/integration_points.json`. Model validation: 42 placement cases, 84 plans, 2,908 frames; zero cluster splits or layout/shadow drift. Exact native atlas/material/timing integration and engine build remain unproven. No original game file was read this round; prior integrity evidence reused. `tested_in_game=0`, `final=0`.

## Round 004 — architecture gate review

`STOCK_ENGINE_REPAIR_ROUTE_IDENTIFIED` (design level, NOT proven). Native module loading: NOT_FOUND (monolithic, 0 engine exports, content-only plugin discovery), so the round-003 native widget is BLOCKED_BY_DELIVERY. Recommended route: stock URichTextBlock with whitespace-only runs, index-encoded style colours and a render-target-thresholded font material. No per-step relayout. Shipped-class evidence: `renderer_repair/exe_names.json`. Run-boundary model: `renderer_repair/run_boundary.json` (whitespace cuts 40/40 identical; punctuation cuts drift). Review and decision tree: `renderer_repair/ARCHITECTURE_REVIEW_004.md`. `tested_in_game=0`, `final=0`.

## Round 006 additions (static evidence)

- Culture list in the shipping EXE: `system, de, es, es-419, fr, it, ja, ko, pt-BR, ru, uk, th, tr, pl, zh-Hans, zh-Hant` (UTF-16 literals at 0x32e5090 beside settings literals); no `ar`. 17 cultures are actually shipped (locmeta CompiledCultures), contrary to `CulturesToStage=en` in DefaultGame.ini.
- Compiled RTL-related cvars: `Slate.EnableLayoutLocalization`, `Slate.ShouldFollowCultureByDefault`. `ETextJustify::InvariantLeft` is absent (4.27 enum; Left/Right flip for RTL lines per ENGINE_SOURCE_RECALL).
- Font fallback: `CompositeFallbackFont` and `NotoNaskhArabicUI-Regular.ttf` are referenced by the EXE; the subtitle composite font has no Arabic sub-typeface.
- Asset localization: the shipped AssetRegistry lists only `/Game/L10N/en/FMOD` packages; mod L10N/ar packages need a registry change (`reports/arabic_activation/L10N_AR.md`).
- Culture-invariant FText (`ETextFlag::CultureInvariant`) exists in 240 widget texts; 91 look user-facing and cannot be localized through locres (`reports/coverage/NON_LOCRES_TEXT.md`).

## Round 007: stock-renderer gate test (UE 5.8.4 isolated, non-authoritative for 4.27)

Evidence: `reports/rtl_research/renderer_repair/ue427_gate_test/` (engine used: **UE 5.8.4**, not 4.27; user chose "Use 5.8 only").

- **G1–G5 on 5.8.4:** all pass. The per-gate details are in `ue427_gate_test/README.md`.
- **UE4.27:** G1–G3 NOT_PROVEN, G4/G5 NOT_RUN, so the 4.27 classification is `STOCK_RENDERER_GATE_TEST_BLOCKED`.
- **Real Slate (5.8) shaping parity:**
  - Whitespace-unit markup is pixel-identical to plain text on 11/12 lines; the 12th differs by ≤6e-8.
  - The `TEST|-42` cut changes output.
  - Arabic mid-word and `v1|.02` cuts did not change output in 5.8, unlike the detached model.
  - The whitespace-only rule stays.
- **Design corrections:**
  - The material divides the output colour by VertexColor, because Slate multiplies it.
  - The index is stored as sRGB byte i+1 in R.
  - The retainer needs RequestRender per write and once after SetText.
  - No RGB tint is allowed on ancestors.

## Round 008: compatibility audit and revision R8 (no UE4.27, no game run)

DISPATCH's shipped shader library (Chunk0, LZ4 DXBC, disassembled read-only) shows the following for the subtitle font material `M_SubtitlePrinting`:
- the VS decodes the vertex colour with exact sRGB (floor 6.1e-5);
- the PS computes `Color / VertexColor`;
- Slate multiplies the material colour by VertexColor and the A8 coverage.

This is the round-007 G1/G2 mechanism, proven on DISPATCH's own engine build. The render-target threshold is replaced by a per-block Border tint (R8). R8 passes on the UE 5.8.4 harness:
- 12 lines × fg/shadow/outline;
- concurrent blocks;
- pool reuse;
- per-line colour through a retainer effect MID.

Variant R8b reuses the shipped material (no new shaders, ≤ 37 units). Evidence and classes: `renderer_repair/COMPATIBILITY_AUDIT_008.md`.
