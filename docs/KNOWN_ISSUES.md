# Known issues

## Round 019 current boundary

- Stock Proto with the font fix is **rejected** for Arabic subtitles. Run 4 (relayed) showed a left-to-right reveal,
  overlapping or interleaving glyphs and an unstable layout during the reveal.
- The repaired R8b (`Build Arabic Timing` void) passes every offline check, but its in-game behaviour is unproven:
  - right-side word reveal, stationary glyphs and joining;
  - shadow sync and RetainerBox/outline on 4.27;
  - widget binding and K2_SetTimer firing.
- The R8b reveal unit is a whole word (whitespace-safe), not a letter. Lines above 37 units merge their tail (20 corpus lines).
- The font route is functional but partial: possible tashkeel clipping, Naskh Regular next to Montserrat Medium, and no
  Arabic italic. Tomorrow and Roboto UI paths are not patched.
- UI and translation items are tracked in `reports/TRANSLATION_UI_BACKLOG_019.md` (overlap, alignment, mixed bidi, wording).
  Nothing was edited this round.


## Round 011 current boundary

Step/Finish/Skip/reset and live Arabic style/wrap helpers are generated, superseding their absence below.
REVEAL_PARTIAL: budget/clock functions have no bound engine driver. Native paused accumulation(+0x86c) and completion
cadence remain uncertified. Injected-clock tests do not prove equivalence. The artifact cannot progress timed lines
by itself and must not be installed. Widget binding, retainer layout/capture, UE4.27 rendering and game behaviour
remain untested. See WBP_REVEAL_RESULT_011.md and SCHEDULER_TIMING_011.md.

## Round 010 historical boundary

The detached Arabic initialization CFG and helpers are generated/validated. This does not complete reveal:
Arabic Step/Finish and pause-compatible scheduling are missing, so the initial speaker threshold does not progress
through the remaining units. Post-layout retainer capture and live style/wrap changes also remain unimplemented.
Native/widget binding, 4.27 outline behaviour and all game runtime results are unproven. Do not install Stage2.

# Round 009 current integration limits

The detached WBP structural generator now passes offline checks; round-008's "patch not generated" limitation below
is superseded for Stage 1. Runtime Kismet routing, Arabic helpers, timers/finish/pooling, widget name binding and 4.27
outline propagation remain unproven. R8b is white, with a 37-unit limit handled by tail merging. It is not a playable fix.
All generated Arabic widgets are Collapsed. No original script changes or installable PAK are included.
`DISPATCH_INTEGRATION_PROVEN=false; IN_GAME_RTL_PROVEN=false; tested_in_game=0; final=0`.

---

**Round 002 correction:** timing-only word reveal is `WORD_REVEAL_REJECTED`, superseding item 9's historical blocked status. The binary proves `PAINT_MODEL_LOGICAL_PEN` and `ZERO_INTERVAL_BATCHES_CHARACTERS`. Multiple zero-delay characters are processed in one callback, but their paint positions still accumulate in ascending source-index order. The prior concern that zero necessarily invalidates the timer is not the recovered ordinary path. No repair was installed. See `reports/rtl_research/proto_binary/`.

1. **Native RTL progressive reveal unresolved.** The original ProtoAnimatedText path is retained. Round 002 identified and classified its native decorator paint function. The offline reference model exists in `tools/rtl_reveal/`; no repair has been integrated. Arabic isolation, a proven integration route and runtime acceptance remain unresolved. Source is not a prerequisite for the completed classification.
2. **No runtime/visual testing.** User prohibited game launch. Font fallback, joining, clipping, wrapping, mixed punctuation, choices and timing cannot be declared correct.
3. **Original UI alignment remains.** The detached right-layout prototype is excluded because an unconditional shared Blueprint override would also change English and still leave native reveal unresolved.
4. **Arabic culture selection unverified.** Text PAK adds culture ar; no Arabic item has been added to game settings. A future user-selected `-culture=ar` may be required and has not been tested.
5. **Engine catalogue is mixed and larger than game tables.** Engine.locres has 20,282 editor/runtime entries; 460 explicit system/input/accessibility candidates are translated as a sparse resource. The remaining 19,822 entries are outside that subset; they are not all asserted editor-only. Static presence does not prove runtime reachability. See `reports/engine_text_audit/`.
6. **Text embedded in images/movies is not covered by locres.** Package paths include images and thousands of video clips; no claim of complete OCR/video-art localization is made. Other hardcoded/nonlocalized text remains a coverage audit item.
7. **Context limits.** Three episode108 runtime keys lack current manifest context. Speaker names are inferred from asset paths, not voice recognition. Draft translations require scene-level literary review.
8. **Plural/ordinal output requires native testing.** Logical parameter identities and format keywords are retained, but Arabic grammar and runtime formatter behavior must be checked in context.

No shortcut such as manual string reversal, presentation-form preprocessing, disabling typewriter while claiming success, or hiding missing translations with English fallback is used to label the project complete.

9. **Timing-only word reveal rejected (2026-10-23, round 002).** The detached POC remains uninstalled. Zero interval does batch characters, but the shipped character run paints successive `[i,i+1)` shaped slices using accumulated x advances. Timing changes cannot repair that ordering. Arabic isolation via `L10N/ar` remains NOT_PROVEN. Exact addresses and provenance are in `reports/rtl_research/proto_binary/`. No in-game pixels were observed.

## Round 003 — detached renderer repair prototype

The detached final-layout renderer model now passes its corpus checks (`RENDERER_REPAIR_PROTOTYPE_BUILT`), but no native repair is integrated. The new-widget design needs native registration/loading, Blueprint language routing and a verified style/font/atlas/timing adapter. The asset audit found no ready Arabic branch or spare ordinary text child in the two inspected WBPs. No UE4.27 SDK/UBT was discovered in the bounded registered/known-root check.

Model limits include simplified wrapping/fallback and unmodeled italic/size/outline/font-material/retainer behavior. See `reports/rtl_research/renderer_repair/ARCHITECTURE.md`. No game execution or installation; `ARABIC_ISOLATION_NOT_PROVEN`, `tested_in_game=0`, `final=0`.

## Round 004 — architecture gate review

10. **No native module loading path.** Monolithic shipping EXE: 0 engine C++ exports, no module DLLs or `.modules` manifests, content-only plugin discovery. A new native renderer class cannot be delivered without an EXE change, proxy DLL, UE4SS or injection. Fixing Proto source would require the developer to rebuild Dispatch.
11. **Rich-run boundaries must be at whitespace.** Detached model: cuts at punctuation lose Latin kerning (`T|-`, `1|.`) and change the script of punctuation-only runs. Whitespace cuts are geometry-neutral (40/40). Slate parity is NOT_PROVEN.
12. **Stock route gates untested (G1–G5).** Font-material vertex colour and coverage, colour quantization, render-target update under RetainerBox, new-material shader delivery with shared shader code, and pooling/ancestor tint. Each can reject the route. Current UAssetAPI tooling has not exercised new exports, imports or bytecode.

## Round 006 — static completion sweep

13. **Arabic cannot appear in the in-game Language menu.** The option list is a literal culture list in the shipping EXE (no `ar`). Arabic must be requested at launch (`-culture=ar`) or via user config, and the game's saved Language setting may override it (runtime NOT_PROVEN). A locmeta override adding `ar` to `CompiledCultures` is prototyped but not packaged. See `reports/arabic_activation/ARABIC_CULTURE.md`.
14. **Culture-invariant widget text.** 91 shipping-widget FTexts are flagged CultureInvariant and can never be localized through locres; whether they are visible or overwritten at runtime is unknown (same English in all 16 shipped cultures). A visible case needs a WBP edit.
15. **Images and videos.** 180 textures carry English text (13 small runtime overlays/stamps, 3 tutorial screenshots, 167 Deluxe comic/artbook pages); no replacement exists. Credits are videos with burned-in text (see `reports/coverage/VIDEO_LOCALIZATION.md`). Subtitles of cinematics come from locres and are translated.
16. **No Arabic profanity list.** The subtitle profanity filter has DataTables for 16 languages and none for Arabic.
17. **Font fallback and clipping.** The subtitle composite font has no Arabic face; Arabic relies on the engine fallback Noto Naskh Arabic UI Regular (no italic, lighter weight). Stacked marks exceed the line box by ~3–6 px statically; real clipping needs the game.
18. **Real-person names stay Latin.** Commentary speaker names (cast/crew) have no locres identity in any culture and are kept in Latin by policy.
19. **Installer now requires `--game-root`** and refuses any build other than Dispatch 1.0.19512 / Steam 25637711 (`compatibility/game_build.json`); `--dry-run` writes nothing. Not run against the real game.
20. **Literary review is partial.** `translation/progress.json` `reviewed` counts records actually reviewed this round (high-risk categories first); the rest are TRANSLATED only.

## Round 007 additions

- **No UE4.27 editor yet.** The gate tests ran on UE 5.8.4 only and are not authoritative for DISPATCH's 4.27 branch.
- **Colour pollution.** Slate multiplies font-material output by the run colour. Without the material division, the Arabic text would be tinted by its own unit index.
- **Retained shadow goes stale.** A RetainerBox with RenderOnInvalidation does not refresh on a threshold write; it needs RequestRender. The first retained capture after SetText can be empty.
- **Ancestor tint.** An RGB tint on any ancestor of the Arabic layer corrupts reveal indices.
- **Shared shader code.** The new material's shaders go to the project shader archive. Delivery to DISPATCH (mod archive or inline) is unproven.
- **Per-block render targets.** DataTable rows bind a fixed material, so per-pooled-block RTs need a design decision.

Evidence: `reports/rtl_research/renderer_repair/ue427_gate_test/` (engine used: **UE 5.8.4**, not 4.27; user chose "Use 5.8 only").

## Round 008 additions
1. **Pool:** the round-007 RT threshold cannot serve an unbounded subtitle pool. It is superseded by the per-block tint threshold (R8/R8b).
2. **R8b unit cap:** R8b caps reveal at 37 units per line. 20 of 7,488 Arabic subtitles reveal their tail as one final step.
3. **R8b colour:** R8b shows subtitles in white. The per-speaker colour option (`SubtitlesColorEnabled`) needs R8 (new material) or the unproven blur-MI colour route.
4. **Outline on 4.27:** if 4.27 does not multiply the outline colour by the widget tint, the outline would show before its word. This is detectable on the first runtime check; the fallback is outline off for Arabic.
5. **WBP patch not generated:** the WBP patch is mapped mutation by mutation but not generated (no 4.27 editor; UAssetAPI widget-tree, variable and bytecode edits POSSIBLE_BUT_UNPROVEN).
6. **NEEDS_CONTEXT:** 9 of the 18 entries are resolvable from bullet-point order (pending sign-off); 9 remain.
