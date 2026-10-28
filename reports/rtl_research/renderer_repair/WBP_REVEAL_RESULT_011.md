# R8b Stage 2 continuation — reveal control partial

2026-10-25. **R8B_WBP_STAGE2_REVEAL_PARTIAL**. OFFLINE / NOT_INSTALLABLE / NOT_RUNTIME_TESTED.
The control helpers are generated; **the real engine clock/scheduler callback is unbound**. The artifact cannot
advance timed subtitles by itself. There is no timer delegate to validate; pause scheduling is not passed.

## Artifact and preservation

Offline review pair: `builds/rtl_poc/reveal_control_011/WBP_SubtitleBlock_AR_REVEAL_PARTIAL.{uasset,uexp}`.
Internal original package/class identity is retained. This is not an installed language override.
69 exports, 137 imports, 413 names. Twelve new helpers and six state fields extend the frozen Stage2 input.
All 79 Stage1/Stage2 files remain SHA256-identical; neither initialization stage was regenerated.
49/57 input payloads and all 21 untouched function scripts/payloads are byte-identical. Intentional changes:
exports 4,11,12,14,19,21,22,23 (old Proto completion, display, Stop, outline, size, wrap, BPGC, CDO).
Unexpected original changes: zero. Name/import prefixes remain fixed. Cloned original instructions retain meaning
except measured address relocation and explicit additions. English runtime equivalence remains untested.

| File | Bytes | SHA256 |
|---|---:|---|
| .uasset | 25,099 | 859FDBAD998E390A20271D021117DF3C3761FED67409784BAE9BFF0E07FC0ADC |
| .uexp | 66,948 | F3B73603A0C8750424B164E0767C208AAE12C69F2399F7E440CD15802BD85A34 |

`reveal_dev01`, `reveal_dev02`, `reveal_control`, `reveal_control_final` are superseded development outputs.
The latter two preceded completion of the emitted animation-branch check. None may be installed.

## Generated behaviour

- Step advances logical units bounded to 0..36 through frozen Set Threshold Arabic, pairing foreground/shadow and
  requesting both retainers. No reveal-time SetText/SetTextStyleSet occurs.
- Build Arabic Timing instruments a clone of frozen Build Arabic Markup; the original helper stays byte-identical.
  Ledger units, speaker delays and merged tail match the canonical reference. See SCHEDULER_TIMING_011.md.
- Begin Reveal starts from the speaker threshold and consumes zero-delay units. Advance Budget/Clocks consume
  supplied deltas. These are unbound ports, not engine timers.
- Finish guards active/finished, clears scheduler/active before effects, sets the final threshold and broadcasts the
  original finished delegate exactly once. No state mutation follows broadcast, protecting synchronous pool reuse.
  Skip calls Finish(true); animation-disabled initialization reaches Finish. Arabic never calls Proto ShowText.
  Skip is directly tested; additional callers outside this WBP are not bound/proven here.
- Cancel increments generation and clears scheduler, active, finished, current/count/speaker, elapsed, delay array
  and threshold, then collapses all seven widgets. Stop calls Cancel even after completion. Suppression remains
  available for the frozen English restoration path. Stale/reentrant budgets reject old generations.
- Old native Proto completion is suppressed while Arabic owns the block. The original English callback body remains
  behind the ownership guard. This prevents late native completion releasing a new Arabic line in the model.
- Outline/large handlers append selection of Fill/Outline and normal/Large; shadow uses corresponding Fill. Wrap
  appends the shipped UTextLayoutWidget utility for both widgets. Original English instructions remain present.

## Checks

Release build: 0 warnings/errors. Independent validator: 0 errors. Two-generation and reread/save pairs are byte-identical.
`reveal_verification.json` records 79 frozen hashes, six negative cases and per-export raw/script diffs.
`instruction_inventory.json` records VM/serialized offsets; `independent_validation.json` is saved separately.

`test_reveal.py` executes reread helper Kismet and the emitted animation-branch predicate, instead of mirroring its
intended setting. Nineteen lifecycle cases pass: 1 unit, speaker-only, speaker+1, 37, overflow 80→37, combining/emoji,
zero-delay unit, skip at start/half, Stop during/after finish, pool A→B→C, animation disabled, injected pause/unpause,
stale generation, reentrant finish/pool, late Proto completion, all four style variants, paired wrap. Finish twice and
paired thresholds are asserted throughout. This bounded evaluator stubs native calls; it is not Unreal execution
or a complete main-graph runtime test. Injected-clock success does not prove native pause equivalence.

Six negative fixtures require specific diagnostics: duplicate finish broadcast, missing scheduler clear, bad scheduler
jump, unpaired shadow threshold, SetText in Step and missing pool reset. Validator also checks exact source-derived
schema, references, root branch/push boundaries, context lengths, script sizes, original instructions, untouched
bytecode and dependency event DAG. Exact comparison does not validate an absent engine delegate. Aggregate checks
retain Stage1/Stage2 tests and add the partial control test: **STATIC_PASS 27/27** (2026-10-25).

## Boundary

Single smallest blocker: certify the driver of Proto's paused accumulator(+0x86c), then bind an equivalent clock/
dispatch adapter including native completion cadence. Ordinary timer behaviour alone does not prove paused behaviour.
Named-widget binding, UE4.27 render/outline/layout/capture and all in-game lifecycle behaviour remain untested.
No new PAK/ZIP, install, game/Steam run or game-directory write. New tools do not read AES; the existing aggregate
package-leak audit uses the local key only in memory and never prints it.

DISPATCH_INTEGRATION_PROVEN=false; IN_GAME_RTL_PROVEN=false; tested_in_game=0; final=0.
