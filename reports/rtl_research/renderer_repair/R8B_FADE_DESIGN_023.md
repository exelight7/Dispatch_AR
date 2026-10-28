# R8b per-word fade: design and offline proof (round 023)

2026-10-26. Design, model and offline validation only. Nothing was emitted, built or installed, and the game was not run.

- **Tool:** `tools/r8b_023/fade_model_023.py`
- **Evidence:** `run7_023/fade_model_023.json`
- **Base:** the round-012 adapter model (`clock_model_012.Arabic`). Round 022 cross-checked it against the **installed** bytecode: unit delays equal on 150/150 lines, reveal frames within 1 frame.

## 1. Root cause (from round 022)

Each word goes from opacity 0 to 0.999 in a single frame, at the moment native Proto would print its **last** letter.

| | Visible changes per second | Frames that change |
|---|---:|---:|
| Current R8b | 8.4 | 14% |
| Native Proto | 37.2 | 62% |

The timer and clock are not the cause: the line ends within ±1 frame of native, and no frame reveals two units.

## 2. Fractional threshold

All existing values stay as they are:
- rows: row B = 10.5^-i (u0..u36);
- `M_SubtitlePrinting`: opacity = sat((VC.b − 0.1) × 1.11);
- markup, tables and layout.

The new display state is written only to the two Border tints:

```text
tint B = FadeBase(T) × (1 + 9.4 × α)        FadeBase(T) = 10.5^T   (T = −1 → 1/10.5)
```

What each unit sees, with product = row B × tint B:

| Unit | Product | Opacity |
|---|---|---|
| i ≤ T | ≥ 10.5^(T−i) ≥ 1 | full (0.999) |
| T+1 | (1 + 9.4α)/10.5, from 0.0952 to 0.9905 | 0 → 0.989, monotone in α |
| ≥ T+2 | ≤ 0.9905/10.5 = 0.0943 | 0 |

- **α = 0** is exactly the current integer state for T. The `FadeBase` constants are the existing `Set Threshold Arabic` table.
- **α = 1** stops at sRGB code 254 (opacity 0.989). The last 1% arrives only when the timer advances T. So full opacity lands on the same frame as today, which is native ±1.
- **Why not 9.5:** 1 + 9.5α (top = the next integer threshold) already reaches code 255 at α ≈ 0.99. On the corpus that finished the last word 1–2 frames early (−2 on 2 lines). The first run of the tool measured this, and the slope was lowered to 9.4.
- **Why not 10.5^(T+f), the supervisor's variant:** it would need `MultiplyMultiply_FloatFloat`, which is present in the EXE. Its ramp is convex: 0.02 at f=0.1 and 0.23 at f=0.5, so the word stays near-invisible for its first half. The linear form needs no power function and gives a near-linear ramp: 0.094 at 0.1, 0.495 at 0.5, 0.893 at 0.9.

## 3. Quantization proof

The vertex colour path:
1. Slate multiplies the colours as `FLinearColor` (float32).
2. `ToFColor(true)` (4.27): clamp, then the sRGB curve, then floor(x·255.999).
3. The shipped VS decodes the sRGB exactly (round 008 shader map 34).
4. The PS applies the opacity code.

The check sweeps every T from −1 to 35 with 20,001 values of α each.

| | sRGB 8-bit (shipped path) | linear 8-bit (robustness) |
|---|---:|---:|
| Next-unit opacity monotone, all T | yes | yes |
| Distinct opacity levels | 166 | 229 |
| Largest level step | 0.0098 | 0.0044 |
| Unit T+2 maximum opacity | **0** | **0** |
| Revealed units' maximum deficit from full | **0** | **0** |

Float32 range is safe:
- largest tint is 10.5^35 × 10.4 = 5.8e36, below the 3.4e38 maximum;
- smallest row value is 10.5^-36 = 1.7e-37, above the smallest normal float (1.2e-38).

## 4. Fade timing

For unit T+1 with N letters, Due = 0.025·N, the unit's existing delay. The time since the unit started is:

```text
E = Due − ArabicClockRemainder + (Now − ArabicClockStamp)
```

Arm Clock already stores Remainder = Due − Elapsed and Stamp = Now. Then:

```text
α = FClamp((E − 0.025) / (Due − 0.025), 0, 1)        (α = 0 when Due − 0.025 < 0.001, a 1-letter unit)
```

- The fade starts at the unit's first native letter and is complete at its last.
- The integer boundaries still come from `K2_SetTimer`, so the total duration is unchanged by construction.
- `Now` is `GetTimeSeconds` when AWP=false (gameplay) and `GetUnpausedTimeSeconds` when AWP=true (preview). These are the same clocks the stamps were taken with.

## 5. All 7,488 subtitles at 60 fps

| | Native Proto | Current R8b | **Proposed fade** |
|---|---:|---:|---:|
| Frames with a visible change | 62.05% | 14.0% | **87.35%** (linear 8-bit: 87.38%) |
| Visible changes per second | 37.2 | 8.4 | 52.4 |
| Line completion vs native (frames) | — | −1: 645, 0: 5,927, +1: 916 | **identical: −1: 645, 0: 5,927, +1: 916** |

Per line, the p10 share of changing frames is 81.8%.

Violations, each counted over every frame of every line, in both quantizations:

| Check | Count |
|---|---:|
| Threshold regressions (T and T+α) | 0 |
| Unit opacity regressions | 0 |
| T+2 ghost frames | 0 |
| Revealed units not full | 0 |

Visible changes per frame, in round 022's terms: a changed frame differs from the previous one in at least one unit's quantized opacity. The denominator is the same per-line frame span for all three columns.

## 6. Scheduling: architecture A

**Decision:** keep `K2_SetTimer` → `Arabic Clock Fired` → `Advance Budget` → `Step` → `Set Threshold Arabic` for the word boundaries. Add a display-only `Arabic Fade Tick` to the existing Blueprint `Tick`.

**Why not B:**
- A's boundary path is the one proven at runtime in Run 6. It is frame-identical to native in the round-012 model (4000/4000).
- B would re-derive timing, pause and skip semantics, and throw away that proof.
- In A, the `Tick` only *reads* clock state and writes the tint. It never advances `ArabicCurrentUnit`, so it cannot break timing, generation or finish semantics.
- `Tick` is already compiled in: `bHasScriptImplementedTick` is set, and `Tick` calls `Arabic Paused Clock`. So the change adds one call and one function.

Frame order:
1. World tick: `FTimerManager` → `Clock Fired` → `Step` → integer `Set Threshold`.
2. Slate paint of the block: `Tick` → `Arabic Paused Clock` (AWP only) → `Arabic Fade Tick`.
3. Children paint: the foreground Border, then the shadow retainers. They use the new tint in the same frame.

### Arabic Fade Tick, in stock Kismet

```text
if !(bArabicActive && ArabicSchedulerArmed && !ArabicFinished) return
if !(ArabicClockRemainder >= 0) return                           // disarmed: Finish/Cancel set −1
Next = ArabicCurrentUnit + 1; if !(Next < ArabicUnitCount) return
Due  = Array_Get(ArabicUnitDelays, Next)
Now  = Animate While Paused ? GetUnpausedTimeSeconds() : GetTimeSeconds()
E    = (Due − ArabicClockRemainder) + (Now − ArabicClockStamp)
Span = Due − 0.025
Alpha = Span >= 0.001 ? FClamp(Divide_FloatFloat(E − 0.025, Span), 0, 1) : 0
Blue = ArabicFadeBase × (1 + 9.4 × Alpha)
if Blue >= ArabicLastBlue && ArabicLastBlue >= Blue return       // unchanged (pause, gaps): no write
ArabicForegroundBorder.SetContentColorAndOpacity((1,1,Blue,1))
ArabicShadowBorder.SetContentColorAndOpacity((1,1,Blue,1))
ArabicShadowRetainerHorizontal.RequestRender(); ArabicShadowRetainerVertical.RequestRender()
ArabicLastBlue = Blue
```

**New natives:** `Divide_FloatFloat` and `FClamp`.
- Both are in the shipped EXE, with UHT FFunctionParams `(float,float)→float` and `(float,float,float)→float`, OuterFunc `0x285ae80` (KismetMathLibrary). They were read with `native_returns_019.candidates`.
- Both are scalar returns, so they satisfy `ReturnContractR` when used inside a Let.
- Every other node is already imported in the WBP.

**New fields:** `ArabicFadeBase` and `ArabicLastBlue` (float).

**One edit to `Set Threshold Arabic`:** after it picks Blue, it also sets `ArabicFadeBase = (T < 0 ? 1/10.5 : Blue)` and `ArabicLastBlue = Blue`. The integer path stays the single owner of boundary state.

## 7. Lifecycle

These were modelled on 3,000 random lines: random 25–144 fps, random pause windows, 20% cancels, 30% skips, 10% animation off, and 20% AWP=true. Totals: 2,709 animated lines, 537 cancelled, 848 skipped, 291 with animation off.

| Event | Behaviour | Modelled result |
|---|---|---|
| Set Displayed Line | `Arabic Cancel` → markup → `Set Threshold(−1)`, which also sets FadeBase = 1/10.5 → `Begin Reveal` | unchanged path |
| Begin Reveal | zero-delay units consumed; Arm Clock stamps | the fade starts on the next Tick |
| Tick | reads state, writes the tint only when Blue changes | 0 regressions, 0 ghosts |
| Clock Fired / Advance Budget | unchanged; `Step` → integer `Set Threshold(T+1)`, so the fade restarts at α=0 | boundary frames identical to current |
| Finish (normal or skip) | ClearTimer, Remainder = −1, `Set Threshold(count−1)`; Tick guard fails | skip: full on the same frame (507 frames, 0 not full); 0 fade writes after finish |
| Skip | → Finish(True) | as above |
| Cancel, Stop Displaying | generation +1, ClearTimer, Remainder = −1, `Set Threshold(−1)` | 0 fade writes after cancel |
| Pause / resume | `GetTimeSeconds` and the timer both stop, so Blue is constant and nothing is written | 0 tint writes in 60 paused frames; resume continues the ramp |
| Pool reuse | `Cancel` resets everything; `Set Threshold(−1)` resets FadeBase and LastBlue | no stale fade (generation is not needed, because Tick is synchronous) |
| Animation disabled | `Set Displayed Line` → `Arabic Finish(True)` before any Tick | full immediately (291/291); 0 fade writes |
| AWP=true (preview) | Paused Clock advances, then Fade Tick uses `GetUnpausedTimeSeconds` | included in the 3,000; 0 violations |

Finish broadcasts more than once: 0.

## 8. Foreground and shadow

Per changed frame the change does exactly four calls: `SetContentColorAndOpacity` on both Borders and `RequestRender` on both retainers. This is the same set `Set Threshold Arabic` already issues per step, and it runs before the children paint.
- **No shadow lag:** the retainers render on invalidation, so they re-render in the same paint.
- **Paint only:** `UBorder::SetContentColorAndOpacity` → `SBorder::SetColorAndOpacity` invalidates paint, not layout.
- **No text mutation:** in the model, the only effect names are `SetContentColorAndOpacity` and `RequestRender`. `SetText`, `SetTextStyleSet`, substring creation and layout calls during the reveal: 0.

## 9. Performance (estimate)

- **Idle block (no active reveal):** about 4 bytecode nodes (the guard) per visible block per frame.
- **Active reveal:**
  - about 22 nodes, including 1 time read, 1 `Array_Get`, 7 float ops, 1 divide and 1 clamp;
  - plus 4 widget calls when Blue changed, on 87% of frames.
  - At the usual 0.1–0.5 µs per Kismet node that is roughly 5–15 µs of CPU per active subtitle per frame. No `Pow` call.
- **Main cost:** the two shadow retainer re-renders, on the GPU, at about 52 per second instead of today's 8.4. English already re-renders its retainers on every printed letter, about 37 per second, so the cost is of the same order.
- Not measurable offline.

## 10. Overflow (more than 37 units: 17 of 7,488 lines)

- The merged tail in u36 (11–147 letters) no longer pops after a 1.1–3.7 s stall. It fades linearly over 15–219 frames.
- Completion vs native: 0 or +1 frames on all 17 lines.
- Changing-frame share on these lines: 0.82–0.94.
- **Remaining issue:** the tail fades as one block of up to 147 letters, not word by word. Fixing that needs the unit limit redesign, which is out of scope.

## 11. Representative examples (complete frame tables in the JSON `examples`)

| Example | Units (raw) | Native last letter | Current last unit | Proposed full | Frames changed: native / current / proposed |
|---|---:|---:|---:|---:|---|
| 2 words | 2 | 16 | 16 | 16 | 9 / 2 / 15 |
| «أيمكنك توصيلي يا ميكا مان؟» | 5 | 33 | 33 | 33 | 21 / 5 / 30 |
| Long (30 units) | 30 | 253 | 253 | 253 | 167 / 30 / 239 |
| Explicit newline (only `\n` line in the corpus) | 4 | 32 | 32 | 32 | 20 / 4 / 29 |
| Exactly 37 units | 37 | 251 | 251 | 251 | 166 / 37 / 227 |
| Overflow (68 raw units) | 37 (68) | 473 | 473 | 473 | 314 / 37 / 388 |

Five-word line, frames 0–20: α is the fade of unit T+1, op is its opacity, nat is the number of native letters visible.

| Frame | T | Unit | α | op | nat | Current T |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | −1 | 0 | 0 | 0 | 0 | −1 |
| 2 | −1 | 0 | 0.067 | 0.062 | 0 | −1 |
| 3 | −1 | 0 | 0.200 | 0.194 | 2 | −1 |
| 5 | −1 | 0 | 0.467 | 0.461 | 3 | −1 |
| 7 | −1 | 0 | 0.733 | 0.725 | 4 | −1 |
| 9 | −1 | 0 | 1.000 | 0.989 | 6 | −1 |
| 10 | 0 | 1 | 0 | 0 | 6 | 0 |
| 12 | 0 | 1 | 0.200 | 0.194 | 8 | 0 |
| 18 | 0 | 1 | 1.000 | 0.989 | 12 | 0 |
| 19 | 1 | 2 | 0 | 0 | 12 | 1 |
| 20 | 1 | 2 | 0.333 | 0.329 | 13 | 1 |

Native Proto's first letter appears at frame 3, and the fade starts at frame 2. This is within one frame, and comes from how the native port schedules the frame of its first item.

## 12. Proof checklist

| # | Requirement | Result |
|---|---|---|
| 1 | RTL unit order unchanged | Markup and rows are untouched, and the fade only reads the existing `u<i>` order |
| 2 | Arabic word boundaries unchanged | `Build Arabic Markup`/`Timing` are untouched; units come from the same `segment_units` |
| 3 | Threshold monotone | 0 regressions: corpus plus lifecycle |
| 4 | Next word fades monotonically | 0 opacity regressions; monotone over the whole α domain for every T |
| 5 | T+2 never ghosts | maximum opacity 0, analytically and in replay |
| 6 | Revealed words stay full | 0 deficit |
| 7 | Final timing native ±1 frame | −1/0/+1 only, identical to the current R8b |
| 8 | No SetText during reveal | effect set = {tint, RequestRender} |
| 9 | Final layout unchanged | no text, style or wrap call; the final state is `Set Threshold(count−1)` as today |
| 10 | Smoothness approaches native | 87.35% of frames change, against native 62.05% |

## 13. Implementation plan (next round)

1. `tools/asset_inspector/ArabicFade023.cs` (`--arabic-fade-023`), with input = the round-021 stylefix WBP pair:
   - add the fields `ArabicFadeBase` and `ArabicLastBlue`;
   - add the imports `Divide_FloatFloat` and `FClamp` (KismetMathLibrary, `CallMath`);
   - add two `Let`s to `Set Threshold Arabic`;
   - generate `Arabic Fade Tick` as in §6;
   - insert one call to it in `Tick` after `Arabic Paused Clock`.
2. A validator (`--validate-arabic-fade-023`) with negative fixtures:
   - Fade Tick calls `SetText` or `SetTextStyleSet`;
   - Fade Tick advances `ArabicCurrentUnit` or `ArabicThreshold`;
   - Fade Tick calls `K2_SetTimer`;
   - the Remainder guard is missing;
   - slope ≥ 9.5;
   - only one Border is written;
   - `Tick` reads `InDeltaTime`.
   - It also runs `ReturnContractR` and `RichTextStyleGate`.
3. `tools/asset_inspector/test_fade_023.py`: replay the emitted bytecode in the round-012 VM against `fade_model_023.Block`, frame-identical tint B on every 50th line plus the 3,000 lifecycle seeds. Add it to `verify_project.py`.
4. A staging-only pak, then Run 7 with the operator: smoothness, stationary glyphs, joining, shadow sync, skip, pause.

## 14. Remaining risks

- **The Blueprint `Tick` route is not proven at runtime.** Run 6 proved only the K2_SetTimer route; the Tick only acted in the settings preview. If `Tick` never fires for gameplay blocks (for example under global invalidation), the reveal falls back to today's word pops. It degrades gracefully, with no hang, because the boundaries never depend on Tick.
- **Intermediate opacities are unproven.** Only the integer endpoints of the sRGB vertex-colour path are runtime-proven, so the in-between levels need to be seen on screen. The linear-8-bit variant passes all the same checks.
- **Outline mode** (`MI_SubtitlePrinting_Bold`) is assumed to use the same opacity code.
- **Overflow tails** fade as one block (§10).
- **Frame rate:** below about 40 fps a 1-letter unit can share a frame, as today. The fade stays monotone (the lifecycle test ran down to 25 fps).
