# Run 6 result (round 022): R8b subtitle visible, RTL direction correct, reveal not smooth

2026-10-26. **`R8B_RUN6_PARTIAL`**. Operator run; the session never launched the game.

- **Configuration:** Texts `0fa5792a…7235` + Fonts `b8b22bcb…b19f` + round-021 R8b `a3402118…e916` + `-culture=ar`. No Locmeta, 23 paks.
- **Install:** `r8b_runtime_staging_021/work/install_run6.ps1`. Receipt and backup in `backups/runtime_run6_022_20261026_002031_875/`.
- **Post-run:** `post_run6.ps1` found identity, originals and all three mod paks unchanged, 0 new crashes and 0 Application events.

## Operator observation (Run 6A, animation ON)

The operator reported:
- the game boots, and there is no crash;
- the Arabic subtitle is visible;
- the first unit appears on the right;
- later text appears toward the left;
- **the reveal animation is noticeably less smooth than the original subtitle animation.**

Not explicitly observed:
- joining;
- stationary glyphs;
- punctuation stability;
- shadow sync;
- T13–T18.

Run 6B was not needed.

## What the run proves

| Flag | Basis |
|---|---|
| `ARABIC_SUBTITLE_VISIBLE=true` | Observed. Run 5 used the byte-identical WBP with `ProtoRichTextStyleRow` tables and was empty. The RowStruct is the only change, so the round-021 fix works at runtime. |
| `R8B_THRESHOLD_RUNTIME_PROVEN=true` | A progressive reveal is only possible if units not yet revealed are hidden by `M_SubtitlePrinting` (tint B = 10.5^t, row B = 10.5^-i). |
| `R8B_CLOCK_RUNTIME_PROVEN=true` (gameplay route, AWP=false) | Every content unit has delay ≥ 0.025 s. On the AWP=false route, `Arabic Begin Reveal` consumes only zero-delay units. After that, the only way to advance is `K2_SetTimer` → `Arabic Clock Fired` (`WBP_CLOCK_RESULT_012.md`). Progress was seen, so the timer fired. The AWP=true preview route (Tick) was not observed. |
| `RTL_DIRECTION_RUNTIME_PROVEN=true` | Observed: the first unit is on the right, and the reveal grows leftward. |
| `IN_GAME_RTL_PROVEN=false` | Stationary glyphs, joining stability, punctuation and shadow sync were not explicitly observed. |

## Smoothness isolation

Tool: `tools/r8b_022/cadence_022.py`. Evidence: `run6_022/cadence_022.json`.
- **What it compares:** the **installed** bytecode (the JSON dump of WBP uasset `e4189ec2…`) against native per-letter Proto, both at a fixed 60 fps.
- **Inputs:** all 7,488 Arabic subtitles, content only. Speaker names were off in CloudSettings.
- **Native reference:** the shipped Proto rows. `PrintLetterInterval 0.025`, `PrintLetterAnimationTime 0`, `UseAdvancedPrintIntervals false` and `SpaceInterval 0` in every row of `DT_SubtitlesProtoRichText(_Large)`. So English prints one letter every 25 ms with no fade.
- **Cross-check, every 50th line through the emitted VM:**
  - unit delays equal the reference on 150/150 lines;
  - reveal frames equal the adapter model on 147/150, and are within 1 frame on all of them.
  - The three 1-frame cases are float32 tie-breaks: 0.025 s is 1.5 frames, so every second boundary lands exactly on a frame.

| Measure (60 fps) | R8b word units | Native Proto letters |
|---|---:|---:|
| Visible changes per second | **8.4** | **37.2** |
| Frames with a visible change | 14% | 62% |
| Gap between changes: median, p10–p90, max (frames) | 6, 3–11, 220 | 2, 1–2, 2 |
| Gaps ≥ 10 frames (≥ 167 ms) | 15% | 0 |
| Gap coefficient of variation | 0.49 | 0.33 |
| Characters appearing per change: mean, p90, max | 4.59, 7, 147 | 1.04, 1, 2 |
| First visible frame: median, p90 | 7, 10 | 3, 3 |
| Line end compared with native | −1: 645, 0: 5,927, +1: 916 | reference |
| Frames revealing more than one unit | 0 | n/a |

Example: «أيمكنك توصيلي يا ميكا مان؟», units of 6/6/2/4/4 letters.
- **R8b:** changes at frames 10, 19, 21, 27 and 33. The gaps are 9, 2, 6 and 6 frames.
- **Native:** 21 single-letter changes from frame 3 to frame 33.

| Supervisor candidate | Verdict | Why |
|---|---|---|
| Whole-word reveal granularity | **PRIMARY** | 4.4× fewer visible changes. Each change adds a whole word (4.6 characters on average) instead of one letter. The gaps vary with word length, from 3 to 11 frames. Splitting inside a word is forbidden, because units cut only at whitespace to keep shaping and joining intact (`segment_units.py` rule 2, `ARCHITECTURE.md:180-183`). |
| Threshold stepping | **CONTRIBUTING** | Each unit goes from opacity 0 to 0.999 in one frame. Native letters also pop (`PrintLetterAnimationTime` 0), but one letter at a time. At word size, the pop is about 4.6× larger. |
| ArabicUnitDelays | **CONTRIBUTING (phase), values correct** | Delay = 0.025 × letters, equal to the reference on 150/150 lines. By design, ready(U) is the time of the unit's **last** letter (`WBP_PATCH_PLAN.md:58`). So each word appears only once native would have finished typing it. The first word shows at frame 7 (median), where native shows its first letter at frame 3. |
| Original Proto timing parity vs R8b word timing | **Total duration matches; distribution does not** | The line ends within ±1 frame of native on every line. The intermediate cadence is per word, not per letter. |
| `K2_SetTimer` cadence | **Not the cause** | One non-looping timer per unit. Reveal frames are within 1 frame of the model, and there is no drift (line-end parity above). |
| `Arabic Clock Fired` scheduling | **Not the cause** | Δ = FMax(Remainder, now − Stamp). The overshoot is carried in Elapsed and re-armed with Due − Elapsed, so no lag accumulates. |
| Multiple units revealed in the same frame | **Not the cause at 60 fps** | 0 frames. The smallest content delay (25 ms) is longer than a frame (16.7 ms). Below 40 fps, units of 1–2 letters (12.5% of units) could share a frame. |
| Zero or very small delay accumulation | **Not the cause, with one exception** | Zero delays exist only for speaker units, and speaker names are off. The exception is overflow: 17 of 7,488 lines have more than 37 units, and the tail merges into u36. That gives a 66–220-frame (1.1–3.7 s) stall, then one large pop. |

**Not measurable offline:**
- the operator's real frame rate;
- any per-step frame cost: the Border tint, and `RequestRender` on two retainers.

The Arabic shadow retainers use `RenderOnInvalidation=true` and `RenderOnPhase=false`, the same as the shipped English retainers, so no phase throttle is configured.

## Lever that keeps RTL, layout and joining (DESIGN_INFERENCE, not tested)

The shipped opacity code already supports a per-unit fade, with no change to rows, markup or layout.
- **Mechanism:** use a fractional threshold, tint B = 10.5^(T+f) with 0 ≤ f < 1.
- **What it does** (`fractional_threshold_ramp_DESIGN_INFERENCE` in the JSON):
  - only unit T+1 fades, through 167 monotone 8-bit sRGB levels, with a largest step of 0.0099;
  - unit T+2 stays at opacity 0, so nothing ghosts;
  - revealed units stay at 0.999.
- **Untested assumptions:**
  - that Slate quantizes the tinted vertex colour to 8-bit sRGB (HC427). The integer endpoints of this path are now proven in game; intermediate values are not;
  - that a per-frame driver can run for gameplay blocks. Today `Tick` acts only when AWP=true.

## Settings labels (separate issue)

`SETTINGS_LABELS_MISSING=true`. The problem persists from Run 5 and is tracked independently of the subtitle renderer.
- R8b's static footprint is `WBP_SubtitleBlock` (reached from `WBP_SubtitlesWidget` and `WBP_SubtitlePreview` only) plus the four DT_AR tables.
- Attribution to R8b is **not established**.
- Run 4 (without R8b) reported Arabic glyphs visible in settings, but did not check the labels on a specific page. Only an A/B comparison of the same page can separate the causes.

DISPATCH_INTEGRATION: subtitle path visible. IN_GAME_RTL_PROVEN=false. tested_in_game=1 (Run 6). final=0.
