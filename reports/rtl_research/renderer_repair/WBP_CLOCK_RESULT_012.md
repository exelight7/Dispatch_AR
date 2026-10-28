# R8b clock adapter — result (round 012 implementation)

2026-10-25. **R8B_WBP_CLOCK_ADAPTER_PASS** (offline). OFFLINE / NOT_INSTALLABLE / NOT_RUNTIME_TESTED.
This is the adapter specified in `SCHEDULER_AUDIT_012.md` / report_012, emitted into a new detached asset.

## Artifact

`builds/rtl_poc/reveal_clock_012/WBP_SubtitleBlock_AR_REVEAL_CLOCK.{uasset,uexp}`: 73 exports, 146 imports, 433 names.

| File | Bytes | SHA256 |
|---|---:|---|
| .uasset | 26,412 | 29EDA3A7C8404DD4CE454590096F4ACC83267B6065CB32B3DA828286D20B4397 |
| .uexp | 69,364 | C6546290DB8678EB987A57ABCA17B17DA6E7B76DD706AB3F9BF4208ABE8260C5 |

- **Source:** the frozen 011 pair (`859FDBAD…0ADC` / `F3B73603…5A34`). The generator refuses any other hash, and the 011 pair is unchanged.
- **Byte-identical:** 64 of the 69 original exports.
- **Changed, all intended:** class (22), CDO (23), `Arabic Finish` (58), `Arabic Cancel` (62) and `Arabic Begin Reveal` (69).
- **Preserved:** all other function bytecode is byte-identical, and the original name and import prefixes are unchanged.
- **Frozen inputs:** 93 files across stage1, stage2 and 011 keep their hashes.

## What was added

- **State** (with the flags of the 011 fields): `ArabicClockStamp` float 0, `ArabicClockRemainder` float (CDO −1), `ArabicClockGeneration` int 0.
- **Imports:**
  - `GameplayStatics.GetTimeSeconds` and `GetUnpausedTimeSeconds`;
  - `KismetSystemLibrary.K2_SetTimer` and `K2_ClearTimer`;
  - `KismetMathLibrary.FMax`;
  - `UserWidget:Tick` (super);
  - `/Script/SlateCore.Geometry`.
- **Import check:** each function is matched uniquely against the shipped EXE's UHT `FFunctionParams` tables, by parameter names, types and flags (`clock_imports_012.py` → `scheduler_012/clock_imports_012.json`). Geometry is checked against the shipped `WBP_SimpleFadeSwitcher` import table.
- **`Arabic Arm Clock`:**
  - guard: `Active && Armed && !Finished && Current+1 < Count`;
  - sets `Remainder = Delays[Current+1] − Elapsed` and `ClockGeneration = Generation`;
  - AWP=true: `Stamp = GetUnpausedTimeSeconds(self)`, with no timer;
  - AWP=false: `Stamp = GetTimeSeconds(self)`, then `K2_SetTimer(self,"Arabic Clock Fired",Remainder,false,0,0)`.
- **`Arabic Clock Fired`:**
  - takes zero parameters;
  - rejects AWP first;
  - guard: `Active && Armed && !Finished && ClockGeneration == Generation`;
  - captures `Gen`, computes `Δ = FMax(Remainder, GetTimeSeconds − Stamp)` and sets `Remainder = −1`;
  - calls `Advance Budget(Δ, Gen)`, then re-arms only if `Gen == Generation`.
- **`Arabic Paused Clock`:**
  - first instruction is the guard `Active && AWP && Armed && !Finished && Remainder ≥ 0`;
  - computes `El = GetUnpausedTimeSeconds − Stamp`, and returns while `El < Remainder`;
  - then consumes exactly as Clock Fired does.
- **`Tick(MyGeometry, InDeltaTime)`:**
  - its flags, parameters and super are cloned from the shipped `WBP_SimpleFadeSwitcher.Tick`;
  - its body is only `Arabic Paused Clock()`, and `InDeltaTime` is never read;
  - Blueprint Tick is enabled: the serialized `bHasScriptImplementedTick=false` is dropped from the CDO, which restores the UUserWidget default (true), as in the shipped template.
- **Edits to the 011 helpers:**
  - Begin Reveal: `Arm Clock()` right after `Advance Budget(0, Generation)`.
  - Finish: `K2_ClearTimer` and `Remainder = −1` before the broadcast, which stays last.
  - Cancel: `K2_ClearTimer`, `Remainder = −1` and `Stamp = 0`.
  - `Arabic Advance Clocks` is untouched and unused; the validator rejects any reference to it.
- **Call shape:**
  - `K2_SetTimer`, `K2_ClearTimer` and the getters use `EX_CallMath`. That matches the shipped calls to the static non-pure `SetTextWrapAt` and `CreateDynamicMaterialInstance` in this WBP.
  - The `FTimerHandle` result of `K2_SetTimer` is discarded at statement level. That needs an 8-byte return buffer, which fits the VM's 64-byte simple-return buffer.

## Verification

| Check | Result |
|---|---|
| Release build | 0 warnings / 0 errors |
| Clock validator | 0 errors |
| Unexpected changes | 0 |
| Two-generation binary | identical (plus a third run, `reveal_clock_dev01`, also identical) |
| Reread/save binary | identical |
| Emitted-bytecode replay, AWP=false, seeds 0–499 | 500/500 frame-identical to `NativeProto`, and identical to the 012 adapter model |
| Emitted-bytecode replay, AWP=true, seeds 0–499 | 500/500 identical (max difference 0 frames; ≤1 allowed); never starts a world timer |
| AWP=true with 30% hidden frames, 100 seeds | converges; never more than 1 frame early |
| Lifecycle cases | 14 |
| Negative fixtures | 15 detected with the specific diagnostic |
| Aggregate | STATIC_PASS 28/28 |

- **Lifecycle cases:**
  - normal reveal (== NativeProto);
  - finish once over 300 extra frames;
  - finish twice (one broadcast);
  - a 37-unit line and overflow 80→37 (== NativeProto);
  - pause freezes and resume continues (== NativeProto);
  - AWP reveal while paused (≤1 frame, no timer);
  - skip halfway (timer cleared, single finish);
  - Stop / Cancel during reveal (timer cleared, no late finish);
  - pool A→B: the same object+function replaces the stale timer, and B == NativeProto;
  - reentrant finish leading to pool reuse inside the timer callback (the stale line does not re-arm);
  - animation disabled;
  - zero-delay leading units (a combining-only line and a speaker prefix);
  - English or inactive Tick is a no-op (state, effects and timers unchanged).
- **The 8 required negative fixtures:**
  - Finish without ClearTimer;
  - Cancel without ClearTimer;
  - wrong timer function-name string;
  - Clock Fired with parameters;
  - Paused Clock without the AWP guard;
  - Arm Clock starting a timer in AWP mode;
  - missing FMax;
  - Blueprint Tick disabled.
- **The other 7 negative fixtures:** Tick reading InDeltaTime, and the six 011 control fixtures.
- **Validator carry-over:** the 011 invariant and bytecode checks became shared helpers, so the 011 validator is unchanged in behaviour (test_reveal.py still passes). The jump, context and size certificates now cover every function export, not only the edited ones.

## Boundary

- **The replay is an offline evaluator** of the reread Kismet, against a ported engine stub (`clock_model_012.World`). It is not Unreal execution.
- **Not proven in game:** that UE4.27 loads the Tick override and `bHasScriptImplementedTick`, that ListView/invalidation ticks the preview block, and the FTimerManager `>` vs `≥` rule. The equivalence holds for the same routine either way.
- **Inherited from 011:** `Array_Get` is called through `EX_CallMath`, while shipped bytecode calls KismetArrayLibrary through a Default__ context. The VM handler is generic, but this is not runtime-proven.

DISPATCH_INTEGRATION_PROVEN=false; IN_GAME_RTL_PROVEN=false; tested_in_game=0; final=0.
