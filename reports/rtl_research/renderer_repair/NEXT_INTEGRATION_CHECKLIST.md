# Stock-renderer integration checklist (prepared round 006; no gate executed)

# Round 019 checklist — repaired R8b ready for Run 5

- [x] Run 2 defect repaired: `Build Arabic Timing` is void (frame audit 16/16; return contract 1120 sites, 0 invalid).
- [x] Run 2 artifact rejected by the new validator at Set Displayed Line:66 (negative fixture on the real 012 pair).
- [x] Rebuilt from clean source; equals the repair of the frozen 012 pair; deterministic; roundtrip-exact.
- [x] Clock replay 500/500 frame-identical; 14 lifecycle cases; ledger equals canonical on 96 fixtures.
- [x] English path identical to the Run 1-proven 012 build; instruction 66 unreachable when `bArabic=false`.
- [x] Staging pak `Dispatch_AR_R8b_P.pak` `1058eac4…f988`: 10 files, same paths as Run 2's pak, deterministic, read back.
- [ ] Run 5 (approval needed): Texts + Fonts + R8b + `-culture=ar`, no Locmeta; T1–T15 in `builds/rtl_poc/r8b_runtime_staging_019/RUN5_READY.md`.
- [ ] Visual proof: right-side Arabic word reveal, no glyph movement, joining intact, shadow in sync.


# Round 009 current checklist

- [x] Four R8b tables, exact 38 rows, normal 28 / Large 36, shipped materials, float32 index codes.
- [x] Detached reachable Arabic widget subtree; every generated widget Collapsed; reciprocal slot ownership.
- [x] Named BPGC object fields and table handles; null widget CDO defaults, no guessed native offsets.
- [x] All four dependency arrays checked; create/serialize event graph acyclic.
- [x] 34 original export payloads identical; only BPGC/CDO/Overlay_0 changed as expected; unexpected=0.
- [x] All 21 original functions' serialized bytecode SHA256 and complete payloads preserved.
- [x] Five assets generated twice and reread/serialized with byte equality; ten negative fixtures detected.
- [x] Independent validator plus general project checks: STATIC_PASS 25/25.
- [x] Stage-2 bytecode map and future package/rollback plan prepared.
- [ ] Stage-2 Kismet generator: exact ar/ar- gate, Arabic helpers/state, label relocation and CFG validation.
- [ ] Runtime named-widget binding, outline propagation, timing/pause/finish/pooling and final rendered RTL.
- [ ] Later approved package/version/install/rollback acceptance; no installable package in this round.

Current result: `R8B_WBP_STAGE1_PASS` (offline only). See `WBP_STAGE1_RESULT.md` and `WBP_STAGE2_BYTECODE_MAP.md`.
Keep `DISPATCH_INTEGRATION_PROVEN=false; IN_GAME_RTL_PROVEN=false; tested_in_game=0; final=0`.

---

Route: `STOCK_ENGINE_REPAIR_ROUTE_IDENTIFIED` (round 004), **NOT_PROVEN**. This file lists what each gate must
produce once a UE4.27 editor is available. Nothing here is a gate result. G1–G3 were not repeated.

## Gate artifacts

| Gate | Question | Needs | Pass artifact (exact) | Fail consequence |
|---|---|---|---|---|
| G1 | Does a UI-domain font material on a RichTextBlock run receive the run colour as `VertexColor` while glyph coverage is still applied? | UE4.27 editor (Launcher), blank project, stock RichTextBlock, test material | `tests/ue427_gates/G1/` : material `.uasset` + screenshot of 3 runs with R = 0.1/0.5/0.9 shown as distinct grey levels, glyph edges anti-aliased; `G1.json` with sampled pixel values per run | Route rejected → dynamic-markup fallback is a supervisor decision |
| G2 | How is vertex colour quantized (8-bit? sRGB?) and how many distinct unit indexes survive? | same | `G2.json`: table of written R byte → value read in material (0..255 step 1), colour-space note, chosen encoding (`index = round(R*255)` or sRGB-corrected), max units per line | Calibration knob in M_ArabicReveal; < 64 units/line → split long lines |
| G3 | Does a cooked render target sampled in the font material update after `ClearRenderTarget2D` inside RetainerBox-retained and normal paint, for both foreground and outline/shadow materials? | same + RetainerBox pair as in WBP_SubtitleBlock | `G3/` frame captures at threshold 0,1,2,…,N with RequestRender; `G3.json` latency (frames) and stale-frame count = 0; identical glyph positions across steps (pixel diff of fully revealed vs. final) | If retained paint does not refresh, drive retainers with `RequestRender` per step (already called by OnPrintLetter) or drop the retainer for Arabic |
| G4 | Can new material shaders be delivered to the shipped game? | Editor cook of the material/MICs/RT/DataTables for WindowsNoEditor with the project's settings | See G4 requirements below; `G4.json` listing every cooked file, its pak path and the shader library entries | Without shaders the material renders default/black → route blocked by delivery |
| G5 | Pooling, reset, ancestor tint, skip/finish | Static audit (done below) + editor PIE replay of pooled blocks | `G5.json`: pass/fail per item of the G5 checklist below | Per-item fixes in the WBP patch |

## G4 static requirements (shader delivery)

- `DefaultGame.ini`: `bShareMaterialShaderCode=True`, `bSharedMaterialNativeLibraries=True`, `bDeterministicShaderCodeOrder=False`,
  classic paks (`bUseIoStore=False`). The shipped shader code lives in the project's shared shader library inside pakchunk0
  (`ushaderbytecode` ×4 in the index). A new material's shaders are **not** in that library.
- Option A (preferred to test first): cook the mod content with **shared material shader code disabled for the mod cook**, so the
  new material carries inline shader maps inside its `.uexp` (works only if the engine accepts inline maps when the project
  uses a shared library — NOT_PROVEN).
- Option B: cook a separate shader code library for the mod (`ShaderArchive-<ModName>-PCD3D_SM5.ushaderbytecode` +
  `ShaderAssetInfo`) and place it in the mod pak at the path the engine scans for chunk/plugin libraries (`<Project>/Content/` /
  plugin content root). Requires the engine to open additional libraries on pak mount — NOT_PROVEN for this build.
- Material must be **UI domain**, unlit, translucent/masked as M_SubtitlePrinting, with `Used with UI`; shader permutations
  only for PCD3D_SM5 (the only shipped global shader cache is `GlobalShaderCache-PCD3D_SM5.bin`).
- Cook with the same engine version (4.27) and `FileVersionLicenseeUE=0`, unversioned packages, as observed.
- Pak placement: `Dispatch/Content/Paks/Dispatch_AR_Texts_P.pak` already mounts at `../../../`; new assets go to new paths
  (`/Game/ArabicReveal/...`) so no original asset is replaced except WBP_SubtitleBlock (see WBP_PATCH_PLAN). Priority `_P`.
- Evidence to keep: cook log, list of produced files, `repak list` of the mod pak, a check that no original-path asset other
  than the WBP is included.

## G5 static checklist

| Item | Static finding | What the patch must do | Runtime check |
|---|---|---|---|
| Pool reset | `WBP_SubtitlesWidget` keeps `UnusedSubtitleBlockPool`; `Get Subtitle Block From Pool` pops the last block or `Create`s one; `Release` appends it back; blocks are reused across lines | `Set Displayed Line` must fully reinitialize the Arabic layer: SetText, reset threshold to unit 0 (or −1), clear timer, recompute unit count | Two consecutive lines on the same pooled block show no carry-over |
| Foreground/shadow sync | Shadow is `SubtitleShadowProtoText` inside `RetainerBox_Horiz/Vert` (blur MIs); foreground is unretained; `OnPrintLetter` requests render on both retainers | Arabic foreground and shadow MIDs sample the **same** threshold RT; one timer writes it; call `RequestRender` on both retainers per step | Shadow never ahead/behind foreground |
| Ancestor tint | `WBP_SubtitlesWidget` animation `ExpandChoiceSpacing` animates a ScaleBox float only; no colour track found; letterbox opacity is on a separate Image; subtitle colour is a **material vector parameter** (`Update Text Color` → `SetVectorParameterValue` on the font MID), not a widget tint | Keep colour in a material parameter (vertex colour carries the unit index); copy `Update Text Color` to the Arabic MIDs; never use `ColorAndOpacity` RGB on ancestors | Per-character subtitle colour still applies to Arabic |
| RetainerBox | `RenderOnInvalidation=true`, `RenderOnPhase=false`; `Set Has Outline` toggles `SetRetainRendering` | Request render after every threshold write; respect `Has Outline` toggling | Outline on/off both reveal correctly |
| Stop Displaying Line | Only `SubtitleOverlay.SetVisibility(Hidden)` | Also stop the Arabic timer and set threshold to "hidden" so a re-shown pooled block cannot flash old text | Hide → reuse shows nothing stale |
| Skip | Typewriter setting `SubtitleTypewriterAnimationEnabled=false` → `ShowText()` | Arabic branch sets threshold = last unit immediately | No reveal animation when disabled |
| Finish | Proto fires `OnFinishLetterByLetterPrint` → block's `On Finish Letter by Letter Print` delegate | Arabic timer fires the **same** block delegate exactly once when the last unit is shown | Subtitle sequencing/timing unchanged |
| Reuse / large text | `ChangeTextToLarge` swaps style sets and invalidates layout | Arabic layer gets its own Large DataTable and the same call | Large subtitles reveal correctly |

None of these items is marked passed.

## Round 007 status

Evidence: `reports/rtl_research/renderer_repair/ue427_gate_test/` (engine used: **UE 5.8.4**, not 4.27; user chose "Use 5.8 only").

| Gate | UE 5.8.4 | UE4.27 |
|---|---|---|
| G1 | PASS_UE58 (VC = 8-bit sRGB run colour; coverage identical; output × VC compensated) | NOT_PROVEN |
| G2 | PASS_UE58 (256/256 bytes; 255-unit reveal; capacity 255, need 69) | NOT_PROVEN |
| G3 | PASS_UE58 (12/12 fg + retained shadow; RequestRender required) | NOT_PROVEN |
| G4 | EDITOR_COOK_PASS_UE58 (shared archive vs inline 33,861 B) | NOT_RUN |
| G5 | MODEL_PASS_UE58 (A/B/C reuse; tint corrupts, opacity safe) | NOT_RUN |

Next: rerun `tools/ue427_stock_reveal_test` on a real 4.27 editor (`UE=` root; UE4 API spellings), then decide per-block RT binding and shader delivery.

## Round 008 status (revision R8 / R8b; UE 5.8.4 harness + DISPATCH shader bytecode)

| Gate | UE4.27 / DISPATCH class (round 008) | Basis |
|---|---|---|
| G1 | G1_427_HIGH_CONFIDENCE | shipped M_SubtitlePrinting VS/PS: VC input, output×VC, `Color/VC` compensation (BIN) |
| G2 | G2_427_HIGH_CONFIDENCE | shipped VS exact sRGB decode (bit-exact constants); simulation 256/256 under both quantisers, margin 0.484 |
| G3 | G3_427_HIGH_CONFIDENCE (R8/R8b), outline VERSION_SENSITIVE | paint-only tint update; DISPATCH English already uses RenderOnInvalidation + RequestRender per step (ASSET) |
| G4 | R8: VERSION_SENSITIVE (inline map); R8b: no new shaders | per-map `bShareCode` (SRC58); shipped maps reused |
| G5 | HIGH_CONFIDENCE for isolation; timer/finish NOT_PROVEN | per-block tint; 5.8 concurrency 0 wrong px, pool 0 failures |

Pool-slot problem: solved by design (per-block Border tint). The G5 "same threshold RT" item above is superseded by "same Set Threshold Arabic call writes both Borders".

Next offline steps: build R8b DataTables by cloning; write a WBP mutation generator with a round-trip/validator; produce detached artifacts only. See report_008.
