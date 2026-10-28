# Round 008: deep compatibility audit and revised integration architecture

Scope: can the round-007 stock-renderer route reach DISPATCH's shipped UE4.27 branch with content, asset and Blueprint
changes only? The constraints are no UE4.27 editor, no game run, no hooks, injection, EXE patch or Proto logical pen.

**Decision: `EDITOR_RENDERER_ROUTE_NEEDS_REVISION`.**
- The render-target threshold store (round 007) is replaced by a per-block threshold carried in a widget tint (R8).
- The revision is specified, implemented in the harness and passes on UE 5.8.4.
- New evidence from DISPATCH's own shipped shader bytecode lifts the core vertex-colour path to HIGH_CONFIDENCE for 4.27.
- Without a 4.27 shader compiler, only the R8b variant (it reuses DISPATCH's shipped M_SubtitlePrinting) can be produced fully offline.
- Runtime proof is still absent: `IN_GAME_RTL_PROVEN=false`, `tested_in_game=0`, `final=0`.

Evidence labels used below:

| Label | Meaning |
|---|---|
| **BIN** | PROVEN_FROM_DISPATCH_BINARY: shipped EXE or shipped shader bytecode, read-only |
| **ASSET** | PROVEN_FROM_DISPATCH_ASSETS |
| **SRC58** | PROVEN_FROM_UE_SOURCE, read in the local UE 5.8.4 install. **No UE4.27 source was accessible** (EpicGames/UnrealEngine is private to this machine's credentials) |
| **UE58** | PROVEN_ON_UE58_ONLY (harness) |
| **HC427** | HIGH_CONFIDENCE_427_COMPATIBLE |
| **VS** | VERSION_SENSITIVE |
| **NP** | NOT_PROVEN |
| **REJ** | REJECTED |

---

## 1. New primary evidence: DISPATCH's own compiled Slate shaders

The shipped shader library was extracted to the session scratchpad. The original paks were read only; the AES key was read from the local key file and never printed.
- **Archive:** `ShaderArchive-Dispatch_Chunk0-PCD3D_SM5.ushaderbytecode`, version 2, 388 shader maps, 4,360 shaders.
- **Compression:** LZ4 per shader.
- **Format:** DXBC `vs_5_0` / `ps_5_0`.
- **Tools:** `tools/shader_inspect/sar.py` (archive header) and `dis.py` (LZ4 + `D3DDisassemble` from the Windows `d3dcompiler_47.dll`).
- **Disassembly:** `dispatch_shader_evidence/M_SubtitlePrinting_map34/`.

`M_SubtitlePrinting.uexp` references shader map **34** (hash `3210ff19e5ed652129248fd4af82dbadec2c953b`, 20 shaders). This is the UI font material DISPATCH's subtitles use today.

**Vertex shader (#3, Slate material VS):** the decode is exact sRGB. Immediates are read with hex printing.

```
max  r0.xyz, v3.xyzx, 0x38800006            ; VC = max(VC, 6.1035e-5)
mad  r1.xyz, r0, 0x3f72a76e, 0x3d558919     ; (VC + 0.055) / 1.055
log/mul 0x4019999a/exp                      ; ^2.4
lt   0x3d25aee6 (0.04045) / mul 1/12.92 / movc
mov  o1.xyz, r0.xyz   ; Color interpolant = linearised VC
mov  o1.w, v3.w       ; alpha passed unchanged (linear)
```

**Grayscale-font pixel shader (#12):** this is the A8 atlas sample `t0.wxyz → .x`, alpha only.

```
div  r0.xyz, cb1[2].xyz, v1.xyz              ; Color / VertexColor   (Proto "ColorCompensation")
mad  ... lerp, max 0                          ; emissive
add/mul_sat r0.w, (v1.z - 0.1) * 1.11         ; opacity from VertexColor.B  (Proto "print" progress)
mul  r1, r0, v1                               ; Slate: material colour x VertexColor (all 4 channels)
sample r0.x, v4.xy, t0.wxyz                   ; font atlas coverage
mul  o0.w, r0.x, r1.w                         ; alpha = coverage x opacity x VC.a
```

The shipped asset `ProtoRichText_Data` describes itself as: *"Helper node to get extra data passed to font materials by ProtoRichTextBlocks. This is a wrapper for vertex color."*

So on DISPATCH's own engine, a UI-domain font material receives the vertex colour, Slate multiplies its output by that colour, and production compensates with `Color / VertexColor`. That is the exact G1 mechanism, in full float with no `min16float` (**BIN + ASSET**).

Also extracted:
- **Blur material** M_UI_TwoPassBlur (shader map 35, PS `933`): RGB is a flat `Color` parameter, and alpha is a 7-tap blur of the retained alpha × 0.538.
- **EXE reflection names**, null-terminated ASCII (**BIN**, names only, not behaviour): `SetContentColorAndOpacity`, `GetEffectMaterial`, `SetEffectMaterial`, `SetBrushColor`, `GetCurrentLanguage`, `StartsWith`, `EqualEqual_StrStr`, `RequestRender`, `SetTextStyleSet`, `K2_SetTimerDelegate`, `ParseIntoArray`, `GetCharacterArrayFromString`, `SetRetainRendering`, `SetAutoWrapText`, `ProcessLocalizedTextWithCallback`.
- **Shader-library strings** in the EXE (**BIN**): `ShaderArchive-%s-` and `%s_Chunk%d`.

## 2. Harness re-audit (round 007, re-derived from `harness_results.json` and the source)

| Gate | Verdict | Why |
|---|---|---|
| G1 | **VALID** | Probe drawn with debug mode 2 (constant white) shows pixel = VertexColor (0.0999, 0.5029, 0.8963) for row colour (0.1, 0.5, 0.9), i.e. 8-bit sRGB. Mode 1 shows VC² (0.0100, 0.2529, 0.8033), which independently proves the output × VC multiply. Coverage mask: 0/76,800 pixels differ vs. the no-material reference (2,888 visible, 864 partial). Not vacuous |
| G2 | **VALID** | 256 separate draws, one byte each. Readback normalised by alpha at the max-coverage pixel (A = 1). `srgb_to_linear` encode with `linear_to_srgb` decode gives 256/256 distinct and correct. The 255-unit functional run passes with 0 removed pixels, 0 empty steps, 0 order violations and 0 SetText |
| G3 | **VALID_WITH_CAVEAT** | Fg and shadow sequences pass with bit-exact revealed pixels. Caveats: (a) `steps_fg_not_exact_prefix` is **tautological**, because the unit map comes from the same widget's own sequence. Unit-to-word correctness rests on monotonicity, one-unit-per-step, "every step adds" and the right-to-left centroid check, and those do pass. (b) `desired_size_changes=0` is near-vacuous, since nothing can relayout without SetText; the real proof is 0 SetText/SetTextStyleSet. (c) Everything is painted offscreen inside one engine frame. "RenderOnInvalidation=false" therefore stays stale 3/3 and 39/39, as expected: phase/frame counters do not advance. That mode is untestable here. (d) The "second RequestRender after SetText" may be a same-frame artefact; cheap to keep |
| G4 | **VALID_WITH_CAVEAT** | Proves a UE5 cook of both shader routes only. The packages are UE5 and unusable by DISPATCH |
| G5 | **VALID_WITH_CAVEAT** | Pool model (A/B/C) passes. The shadow check is only "visible px > 0 / = 0" per step, not per-unit, but the G3 sync check covers per-unit shadow content. Timer, delegate and real frame order are not modelled. Tint/opacity findings are valid |

Other checks:
- **Warm-up:** first-paint warm-up (3 paints + `FinishShaders`) is a harness need: shaders compile on first use in an editor. A cooked game has precompiled shaders, but a pooled block's first paint may still be one frame late. The hidden state at SetText makes this harmless.
- **Regression:** after this round's harness edits, `RevealGate.All` reproduces `harness_results.json` **field for field** (`identical_to_round007: True`).

## 3. UE4.27 compatibility matrix (only items the route depends on)

| Feature | UE4.27 (DISPATCH) | UE5.8 | Route depends on | Class |
|---|---|---|---|---|
| UI font material receives run colour as VertexColor | Shipped Slate material VS/PS above | same (SlateVertexShader.usf `SOURCE_IN_LINEAR_SPACE`) | yes | **BIN** |
| Output × VertexColor (font path) | `mul r1, r0, v1` then alpha × A8 coverage | `GetFontElementColor: OutColor = VC * MaterialColor` | yes (compensation) | **BIN** |
| Vertex colour 8-bit/channel, sRGB decoded in VS | `max(v,6.1e-5)` + exact sRGB, alpha linear | `sRGBToLinear` without max | yes | **BIN** |
| CPU packing FLinearColor→FColor sRGB | inferred: shipped VS decodes sRGB unconditionally, so CPU must encode sRGB (`bSRGBVertexColor = !IsVertexColorInLinearSpace()`, false in RHI policy); 4.x quantiser `floor(x*255.999)` (recall) | stb table, round-to-nearest | yes | **HC427** (both quantisers simulated 256/256) |
| FSlateTextRun: run colour × widget tint → glyph VC | not readable (no 4.27 source); fundamental since UE4.0 | `InWidgetStyle.GetColorAndOpacityTint() * Style.ColorAndOpacity` | yes (R8 threshold) | **HC427** |
| Outline glyph VC = tint × OutlineColor; OutlineMaterial applied to outline geometry | outline rows exist in DISPATCH data (size 2, `MI_SubtitlePrinting_Bold`, black) | `BuildFontGeometry(OutlineSettings, PackVertexColor(GetOutlineTint()), OutlineFontMaterial…)` | yes (outline layer) | **VS**: the tint factor on the outline colour is the single 4.27 behaviour this audit cannot pin down |
| FRichTextStyleRow / FTextBlockStyle layout | DISPATCH tables: FontObject, FontMaterial, OutlineSettings{OutlineSize, bSeparateFillAlpha, bApplyOutlineToDropShadows, OutlineMaterial, OutlineColor}, TypefaceFontName, Size, LetterSpacing, ColorAndOpacity, Shadow*, Highlight/Strike/Underline brushes | superset | yes | **ASSET** |
| Stock RichTextBlock accepts DISPATCH's row tables | `ChangeTextToLarge` calls `/Script/UMG:RichTextBlock:SetTextStyleSet` with `DT_SubtitlesProtoRichText_Large` | — | cloning DISPATCH tables | **ASSET** |
| Rich-text escapes `&amp; &quot; &lt; &gt;` | writer/parser pair since 4.x (recall) | `FDefaultRichTextMarkupWriter::EscapeText` + `HandleEscapeSequences` | 33 subtitles contain `& < > "` | **HC427** |
| URetainerBox RenderOnInvalidation + RequestRender | DISPATCH English path: both retainers `RenderOnInvalidation=true`, `RenderOnPhase=false`, `RequestRender` on every `OnPrintLetter` | `bRenderRequested` path, child invalidation re-render | yes | **ASSET** (same pattern already live) |
| Retainer paints children with incoming widget style; retained image tinted again | not readable | SRetainerWidget: `Context.WidgetStyle` passed to children; box tint = style × ColorAndOpacity | threshold Border must be *inside* the retainer | **VS** (design avoids the question) |
| URetainerBox effect MID per instance (`GetEffectMaterial`) | name in EXE | per-instance MID once Slate widget exists | R8 colour only | **BIN** (name) / **UE58** |
| ClearRenderTarget2D, RGBA16f RT, RT sampled in UI material | names in EXE | works | **not needed by R8** | **HC427** (moot) |
| UMaterialInstanceDynamic / UI domain / font material binding | Proto `OverrideFontMaterial` with `CreateDynamicMaterialInstance` | same | R8 colour; not row binding | **ASSET** |
| Shader map inline vs shared | archive strings present; per-map `bShareCode` flag | `FShaderMapBase` serialises `bShareCode` then inline code or hash | shader delivery (R8 only) | **HC427** for loader; **NP** in game |
| `GetCurrentLanguage` | name in EXE | ar, ar-SA → `ar`/`ar-SA` | language gate | **BIN** (name) / **UE58** |

## 4. Gate compatibility

### G1: `G1_427 = G1_427_HIGH_CONFIDENCE`

What is proven from DISPATCH's own binary:
- the font-material path, the VertexColor input, the output × VC multiply, and the full-float math;
- production already uses the `Color / VertexColor` compensation (Proto's `ColorCompensation`).

The one link not visible in bytecode is stock FSlateTextRun putting the *rich-run* colour into the vertex. That has been basic Slate behaviour since UE4.0, and the shader the run feeds is the same one.

Numerical safety:
- **Byte 0:** VS floor 6.1e-5, so linear 4.72e-6 and 1/VC = 211,681.
- **Byte 1:** linear 3.035e-4, so 1/VC = 3,294.6.
- **Round-trip:** `(1/VC)·VC` round-trip error 0.0 in float32 for both bytes.
- **Range:** no fp16 anywhere (no min16 in the DXBC), and 2e5 is within fp16 anyway.
- **R8 G channel:** the threshold G changes per step, so `Col.g/VC.g·VC.g` can round by **one ULP** (5.96e-8, measured on `long_wrap`). That is invisible at 8 bits: the PNG check is 36/36 identical.

### G2: `G2_427 = G2_427_HIGH_CONFIDENCE`

The index path `i → byte i+1 → sRGB encode → FColor → VS decode → material decode` was replayed in float32 by `tools/ue427_stock_reveal_test/sim_427_vertex_path.py`:
- it uses the **bit-exact DISPATCH VS constants**;
- under both the 4.x `floor(x·255.999)` and the round-to-nearest quantiser;
- with GPU log2/exp2 perturbed ±1e-5 relative (≈20× the D3D11 spec) and the interpolant ±4 ULP.

Result: **256/256 bytes, worst decode margin 0.484 byte**.

Capacity:
- **Proven capacity:** 255 indices plus 255 thresholds.
- **Design capacity:** 128 units (rows u0..u127), against a measured need of **69** (7,488 Arabic subtitles: p50 6, p99 27, max 69).

### G3: `G3_427 = G3_427_HIGH_CONFIDENCE` (for the revised route R8; the outline layer stays VERSION_SENSITIVE)

R8 removes the RT, so the update is a paint-only property change (`SetContentColorAndOpacity`): no SetText, no SetTextStyleSet, no layout mutation.

The retainer contract is identical to DISPATCH's live English path (RenderOnInvalidation=true + RequestRender per step). The Arabic design adds:
- one extra RequestRender on the tick after SetText;
- a RequestRender on every threshold write.

Phase rendering is not used (DISPATCH: RenderOnPhase=false).

The round-007 RT pipeline would also be HC427, but it fails the pooling requirement (section 5).

### G4: shader delivery, see section 14

`G4_427 = VERSION_SENSITIVE` for R8: a new material needs a 4.27 shader compile and inline map acceptance.

For R8b there are **no new shaders**; it reuses the shipped M_SubtitlePrinting / MI_SubtitlePrinting_Bold / MI_UI_TwoPassBlur shader maps.

### G5: `G5_427 = HIGH_CONFIDENCE` for state isolation, `NOT_PROVEN` for timer/finish

The threshold is per-widget state, so pooled and concurrent blocks are independent by construction. Tested on 5.8:
- two blocks at different thresholds in one paint: 0 wrong pixels in 5 cases;
- pool A/B/C reuse: 0 failed checks.

The Blueprint timer, skip and finish logic does not exist yet.

## 5. Pool-slot threshold architecture

Static facts:
- `WBP_SubtitlesWidget` keeps `SubtitleBlocksByHandle` (Map) and adds each block to the `SubtitleBlocksList` VerticalBox.
- `Get Subtitle Block From Pool` pops from `UnusedSubtitleBlockPool` or **creates** a new block.
- So the pool is **unbounded**, and several blocks can be visible at once (**ASSET**).

Separately, DataTable rows bind a *fixed* material, and the English per-line subtitle colour is a **per-block MID** (`Setup Dynamic Material` → `OverrideFontMaterial`; `Update Text Color` → `SetVectorParameterValue`).

| Option | Correctness | Memory/assets | BP complexity | Pool safety | Shadow sync | Cook | Version sensitivity | Verdict |
|---|---|---|---|---|---|---|---|---|
| A: RT+MIC+DT per slot | correct up to N slots; block N+1 breaks | N×(RT+2–4 MIC+4 DT); ≥0.46 MB per DT | needs slot index from the pool (not available in the block) | **unsafe** (pool unbounded) | shared RT per slot | many assets | RT path | REJ |
| B: one active block, shared RT | wrong whenever two subtitles overlap | 1 set | low | **not guaranteed** (VerticalBox + handle map) | ok | low | RT path | REJ |
| C: one texture, slot ID + unit ID | slot ID must reach the shader per block: only possible through a widget tint (→ E). Per-texel writes need Canvas drawing (ClearRenderTarget2D clears the whole RT) | 1 RT | high | ok if slot IDs managed | ok | low | Canvas + RT | REJ (dominated by E) |
| D: MPC | global; same slot-ID problem; MPC binding in Slate UI materials NP | 1 MPC | medium | as C | ok | low | NP | REJ |
| **E (R8): threshold in VertexColor.G from a per-block Border tint** | **exact; tested 5.8** | 0 RT, 1 material, shared tables | low: one `SetContentColorAndOpacity` per layer per step | **safe by construction** | one BP function writes both borders; 0 sync differences | 1 new material | tint path HC427 | **SELECTED (needs 4.27 shader compile)** |
| **E' (R8b): exponential code in VertexColor.B, reuse shipped M_SubtitlePrinting** | exact for ≤ 37 units; tail merge above; tested 5.8 on a mirror of the shipped math | 0 new materials/shaders | same as E | safe | same | **no new shaders** | relies on shipped shader (BIN) | **SELECTED for offline integration** |

`POOL_SLOT_ARCHITECTURE = PER_BLOCK_TINT_THRESHOLD`: option E, with material back-end R8 or R8b.

## 6. Revision R8: what changed and how it was tested

| Component | Round 007 | R8 |
|---|---|---|
| Threshold store | 1×1 RGBA16f RT, ClearRenderTarget2D | Border `ContentColorAndOpacity` = (1, srgb_to_linear((t+1)/255), 1, 1) per block and layer |
| Material | `idx(R) <= Thr(RT.r)` | `idx(R) <= thr(G)`; both sRGB-decoded; `Col / max(VC,1e-6)` |
| Shadow | own MIC + table | **same table as fg** (the shipped blur discards RGB, see §1); Border *inside* the retainer pair |
| Outline | untested | per-row `OutlineColor` = the same index colour; outline material = black variant; **tested 5.8** |
| Per-line colour | unresolved (rows cannot reference a per-block MID) | fg in its own RetainerBox whose per-instance effect MID multiplies by `SubtitleColor`; **tested 5.8** (exact colour at full coverage; AA edges differ by ≤ 0.227 vs a direct coloured material: gamma-space retention) |

R8b uses the same widgets and Blueprint, but the reveal code is in B:
- row B = 10.5^-i, tint B = 10.5^t;
- shipped opacity = sat((B−0.1)·1.11): revealed B = 1 gives 0.999 (English's own maximum), hidden gives 0;
- capacity 37 units, since 10.5^36 < FLT_MAX; 20 of 7,488 subtitles (0.27%) exceed it, and their tail reveals as one final unit;
- outline via shipped `MI_SubtitlePrinting_Bold` (Color black, mask clip 0.333);
- shipped VS print-scale offset at the revealed state is `lerp(−10, 0, 0.999)·(Ut−pivot)` ≤ 0.01 px with stock run UVs in [0, 1] (SRC58 `BuildFontGeometry`), and identical for every revealed glyph.

Harness (`tools/ue427_stock_reveal_test`, UE 5.8.4 only):
- **`RevealGate.Tint` (R8):** G-byte sweep 256/256 with R index unchanged 256/256. 12 lines × (fg, shadow-in-retainer, outline) pass within 1e-6. 11 lines are bit-exact; `long_wrap` has a 1-ULP G jitter. Layout parity 0 px against untagged text, fg/shadow sync 0. Concurrent blocks: 0 wrong pixels in 5 cases. Pool reuse 0 failures. Colourize 3/3. PNG re-check 36/36.
- **`RevealGate.TintB` (R8b):** 12 lines × 3 layers bit-exact; `long_wrap` merged 39→37 units. Concurrency 0 wrong; pool 0 failures; PNG 36/36.
- **`RevealGate.All`:** unchanged, identical to round 007.

Evidence: `r8_tint_test/`, `r8b_printing_test/`, `r8_tint_test/sim_427_vertex_path.json`, `r8_tint_test/segmentation_stats.json`.

## 7. DataTable size

DISPATCH packages have an unversioned *summary* but **tagged** properties (`HasUnversionedProperties=false`; no mappings file needed). Every row therefore repeats property tags for FTextBlockStyle's three FSlateBrushes and the font/outline structs:
- **DISPATCH (4.27):** `DT_SubtitlesProtoRichText.uexp` is 28,505 B for 8 rows, i.e. **≈3.56 KB/row**.
- **UE 5.8 (round 007):** 5.37 KB/row.

Design:

| Item | Size |
|---|---|
| R8: `Default + u0..u127` = 129 rows | ≈0.46 MB per table in 4.27 form |
| R8: tables Fill, Fill_Large, Outline, Outline_Large (shadow reuses Fill) | ≈1.8 MB total (round-007 plan: ≥6 tables of 256 rows) |
| R8b: 38 rows | ≈0.14 MB per table |

At runtime each RichTextBlock copies every row into its style set, roughly 0.6 KB/row. Fewer rows also helps there.

255 rows are not needed. 96 rows would cover all data today, but 128 keeps a ×1.85 margin at a cost of about 0.1 MB.

## 8. Parent tint audit (WBP_SubtitleBlock and WBP_SubtitlesWidget, static)

| Element | Class |
|---|---|
| WBP_SubtitlesWidget: no ColorAndOpacity / ContentColorAndOpacity / RenderOpacity / ForegroundColor serialised; only animation `ExpandChoiceSpacing` animates `ChoiceSpacingScalebox.UserSpecifiedScale` (not an ancestor of the blocks) | NOT_USED |
| WBP_SubtitleBlock: ColorAndOpacity only on `Letterbox` (sibling Image); `Image:SetOpacity` on Letterbox; no widget animations; no SetColorAndOpacity/RenderOpacity calls | SAFE (not an ancestor) |
| SubtitleOverlay / RootVBox visibility | SAFE |
| Text-style drop shadow (ShadowOffset 0 in all rows) | NOT_USED |
| ForegroundColor (rows use Specified colour) | NOT_USED |
| RenderOpacity anywhere | SAFE (alpha only; UE58 G5; the R8/R8b codes live in RGB) |
| Retainer effect materials (blur, colourize) | SAFE (applied after the index is resolved) |
| Any RGB tint above the threshold Border | INDEX_CORRUPTING |
| Ancestors above WBP_SubtitlesWidget (HUD host created natively by AdHocSubtitles) | NOT_PROVEN |
| Outline tint propagation on 4.27 | NOT_PROVEN (VS) |

Normal subtitle colour, keeping the index intact:
- **R8:** the foreground retainer's effect MID (`SubtitleColor`).
- **R8b:**
  - white, which matches the default (`SubtitlesColorEnabled` off);
  - colour candidate: a foreground retainer with the *shipped* `MI_UI_TwoPassBlur` (Radius 0, `Color` = subtitle colour). Its RGB output is not premultiplied, so there is an edge-halo risk: NOT_PROVEN.

## 9. Outline path

DISPATCH outline is real font outline geometry (rows `*_Outline`: OutlineSize 2, OutlineMaterial `MI_SubtitlePrinting_Bold`, OutlineColor black) (**ASSET**).

Stock Slate draws the outline as a separate glyph pass:
- vertex colour = tint × OutlineColor;
- material = OutlineMaterial;
- the fill pass is drawn on top (**SRC58**).

Design:
- the same RichTextBlock and the same rows;
- `OutlineColor` = the row's index colour;
- outline material = black reveal variant (R8) or `MI_SubtitlePrinting_Bold` (R8b);
- fill and outline reveal together from one threshold, with no separate widget (UE58: 12/12 lines).

Outline mode, mirroring English `Set Has Outline`:
- switch the Arabic fg table to the Outline table;
- turn shadow retention off and hide the shadow pair, as English does.

Risk **VS:** if 4.27's FSlateTextRun did not multiply OutlineColor by the widget tint, the R8/R8b outline would show unrevealed words (fill would still be right). That is detectable on the first runtime check. The fallback is to disable outline in Arabic (shadow mode only).

## 10. Shadow architecture

Keep the second RichTextBlock inside its own RetainerBox_Horiz → RetainerBox_Vert pair, with the same blur MIs as English. Then:
- put the threshold Border *between* the inner retainer and the text;
- use the same markup string, set in the same Blueprint call;
- use the same table as the foreground;
- write the same threshold value in the same function as the foreground Border;
- call RequestRender on both retainers per write and once on the tick after SetText.

There is no independent reveal state (UE58: 0 sync differences across 12 lines).

## 11. Segmentation (implementation-ready)

Reference implementation: `tools/ue427_stock_reveal_test/segment_units.py` (self-check + full corpus).
1. **Input:** the final logical text after censorship and `ProcessLocalizedTextWithCallback`, with the game's `<Italic>` and `</>` markers removed (Arabic has no italic face). The speaker prefix is `SpeakerName + ":"` when English would show a speaker.
2. **Split characters:** exactly U+0020, U+0009, U+000A and U+000D. These never split: NBSP, U+202F, ZWSP, ZWJ, ZWNJ, harakat, tatweel, punctuation.
3. **Tokens:** a token is a maximal run of non-split characters. A token with no Arabic or Latin letter joins the previous unit together with its gap, unless that gap holds a newline or there is no previous unit.
4. **Speaker:** speaker units come first and are visible from the start (English shows the speaker at once).
5. **Overflow:** units beyond MAX (128 for R8, 37 for R8b) merge into the last unit.
6. **Markup:** leading gap + `<u{k}>` + escaped unit + `</>` + gap. Gaps stay outside tags (Default row = index 0). Escape `& " < >`.
7. **Delay:** unit delay = 0.025 s × its letters excluding combining marks. DISPATCH rows use PrintLetterInterval 0.025, UseAdvancedPrintIntervals=false, SpaceInterval 0.

Cases:

| Case | Example | Units |
|---|---|---|
| Arabic + punctuation | `حقاً؟`, `«اقتباس` | one unit each |
| Latin + punctuation, version strings | `(TEST-42)`, `v1.02` | one unit each |
| Number then unit | `50 USD` | `50` joins the preceding word, `USD` stands alone |
| lam-alef, harakat | — | never split, because cuts only happen at whitespace |

Corpus results:
- 7,488 subtitles, 0 round-trip failures, max 69 units, max 4 speaker units;
- 33 lines need escaping;
- round-007 negative controls (`TEST|-42` changed 2,842 px) justify never cutting inside a token.

## 12. Speaker formatting and censorship: where the Arabic input is taken

`Set Displayed Line(SubtitleDisplayInfo)` does the following (**ASSET**):
1. `SubtitleColor` / `Update Text Color`;
2. `Dispatch Filter Text Profanity`, which gives `Potentially_Censored_Text`;
3. `ProcessLocalizedTextWithCallback(text, delegate → Format As Subtitle Text With Tags(string)->string)`;
4. `Apply Speaker Name if Needed(text, SpeakerName)`, which returns `{OpeningSpeakerTag}{SpeakerName}: </>{SubtitleContent}`;
5. `SetText` ×2 and `PrintLetterByLetter` / `ShowText`.

The Arabic branch reuses step 2 unchanged.

For step 3 it passes a **new Arabic callback**, `Format As Arabic Plain(string)->string`, which only removes `<Italic>` and `</>`. It does not call the English callback, because that injects Proto `<text style=…>` tags.

For step 4 it reads the same `SubtitleSpeakerNamesEnabled` setting and `TextIsEmpty(SpeakerName)` test, then builds the plain prefix.

Steps 6 and 7 of the segmentation then run once on the complete string. Arabic locres pre-tagging is rejected for two reasons:
- subtitle sources are `LocalizeableSlicedText` split at `|` natively;
- some text is reused in other widgets (e.g. `VOTranscription`).

## 13. Language gate

- **Rule:** `L = GetCurrentLanguage(); bArabic = (L == "ar") || StartsWith(L, "ar-")`. A bare `StartsWith("ar")` would also match `arn` (Mapudungun). The rule is evaluated once per `Set Displayed Line` and held for that line.
- **Generic engine capability:** UE58 (ar, ar-SA, `-culture=ar`) and **BIN** (name).
- **Why this source:** `GetCurrentLanguage` is the same engine state that selects the locres, so "Arabic renderer if and only if Arabic text is shown" holds by construction. A missing key falls back to English source text, which still renders correctly through the Arabic path.
- **DISPATCH's own state:** the `UDispatchLanguageSetting` option list has no `ar` (**BIN**), so it cannot be used.
- **Runtime-only uncertainty:** whether `-culture=ar` is honoured, and whether a saved Language setting overrides it. Both are NP.

## 14. Shader delivery

Static facts:
- **Shipped libraries:** Chunk0, Chunk8, Chunk16 and Global, plus GlobalShaderCache and AssetRegistry.bin.
- **Inline maps:** no shipped material checked carries an inline map (no DXBC in the extracted `.uexp`s).
- **EXE:** contains `ShaderArchive-%s-` and `%s_Chunk%d`; chunk libraries are opened by name (**BIN**).

| Route | For | Against |
|---|---|---|
| A: inline shader map | self-contained `.uexp`; loader reads a per-map `bShareCode` flag (SRC58; same scheme since 4.26, HC427); no naming or mount-order dependency | needs a 4.27 shader compile matching DISPATCH's custom branch uniform-buffer layouts (NP) |
| B: separate archive | mirrors shipped layout | depends on pak chunk ID / library name being opened at mount (strings present, behaviour NP); mount order |
| R8b: none | reuses shipped maps; nothing to deliver | 37-unit cap; colour feature reduced |

`SHADER_DELIVERY_ROUTE = NO_NEW_SHADERS_R8B` for offline integration. `ROUTE_A_INLINE` is the preferred route if R8 is ever cooked.

## 15. Blueprint integration (WBP_SubtitleBlock, metadata only, not edited)

| Mutation | Kind | UAssetAPI 1.1.0 |
|---|---|---|
| Arabic fg: Overlay_0 → OverlaySlot → [R8: RetainerBox(colourize) →] Border → BorderSlot → RichTextBlock | WIDGET_TREE_CHANGE (4–6 new exports) | POSSIBLE_BUT_UNPROVEN |
| Arabic shadow: OverlaySlot → RetainerBox_H → PanelSlot → RetainerBox_V → PanelSlot → Border → BorderSlot → RichTextBlock | WIDGET_TREE_CHANGE (≈8 exports) | POSSIBLE_BUT_UNPROVEN |
| Properties on new widgets: TextStyleSet, Justification Center, AutoWrapText / WrapTextAt 1050, Visibility Collapsed, EffectMaterial (existing blur MIs) | PROPERTY_ONLY | SUPPORTED (property edits proven round 004) |
| Imports: `/Script/UMG.Border`, `BorderSlot`, `Default__Border`, functions in §1, new/cloned DataTables | NEW_IMPORT / NEW_ASSET_REFERENCE | SUPPORTED (append) / unexercised |
| BPGC variables: ArabicText, ArabicShadowText, ArabicFgBorder, ArabicShadowBorder, ArabicRetainer_H/V, bArabic, ArabicThreshold, ArabicUnitCount, ArabicSpeakerUnits, ArabicDelays (float[]), ArabicTimer (TimerHandle) | NEW_VARIABLE (FProperty + CDO) | POSSIBLE_BUT_UNPROVEN |
| Set Displayed Line: branch after step 2 | KISMET_BYTECODE_CHANGE | POSSIBLE_BUT_UNPROVEN (hand-computed jump offsets, no compiler) |
| New functions: Format As Arabic Plain, Build Arabic Markup (loop over GetCharacterArrayFromString), Arabic Set Threshold, Arabic Step (timer), Arabic Finish | NEW_FUNCTION_CALL + new UFunction exports | POSSIBLE_BUT_UNPROVEN (largest risk) |
| Stop Displaying Line, Set Has Outline, ChangeTextToLarge, Set Wrap Text At: append Arabic calls | KISMET_BYTECODE_CHANGE | POSSIBLE_BUT_UNPROVEN |
| Timer: `K2_SetTimerDelegate` (EX_BindDelegate to Arabic Step) | NEW_FUNCTION_CALL | POSSIBLE_BUT_UNPROVEN |

`BLUEPRINT_PATCH_FEASIBILITY = POSSIBLE_BUT_UNPROVEN`. No mutation needs a primitive UAssetAPI cannot serialise. None has been exercised, and there is no validator for WidgetTree/BPGC consistency or bytecode semantics. Round 004's `REQUIRES_UNSUPPORTED_EDIT` described the *current tooling without a generator*; this round maps each mutation.

Assets producible offline for R8b:
- **DataTables:** cloned from `DT_SubtitlesProtoRichText`, property edits only.
- **MICs:** none new are needed; the rows reference shipped M_SubtitlePrinting and MI_SubtitlePrinting_Bold.
- **Font:** shipped `Montserrat-Variable`.

## 16. Stub authoring

`STUB_AUTHORING = STUB_AUTHORING_NOT_VIABLE` while no UE4.27 editor exists:
- a header-only stub project needs a 4.27 UHT/editor;
- UE 5.8 cannot write 4.27 packages (FileVersionUE5, different summary).

Should a 4.27 editor ever be used, the route becomes STUB_AUTHORING_HIGH_RISK:
- it needs matching /Script paths for ProtoAnimatedText, AdHocUtils, AdHocSubtitles and Dispatch;
- tagged properties tolerate layout drift better than unversioned would;
- LicenseeUE 0;
- the custom branch is still unknown.

## 17. Image queue and NEEDS_CONTEXT

These are kept in `reports/coverage/IMAGE_QUEUE.md` and `reports/validation/NEEDS_CONTEXT_008.md`.

## 18. Canonical architecture

See `ARCHITECTURE.md`, section "Round 008: canonical integration architecture".
