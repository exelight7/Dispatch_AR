# Round 012: Proto scheduler audit and the Arabic clock adapter

2026-10-25. Static, read-only. EXE SHA256 `365637a7…4ac14923` (hash-checked by every script). RVAs, base 0x140000000.
`PAUSED_ACCUMULATOR_DRIVER = IDENTIFIED`. `ARABIC_CLOCK_ADAPTER = STOCK_BLUEPRINT_ROUTE_FOUND`.
For all gameplay subtitles (`Animate While Paused = false`) the route is exact. For the settings preview (`true`)
it is a safe approximation. Nothing is installed or run. DISPATCH_INTEGRATION_PROVEN=false; tested_in_game=0; final=0.

Evidence:
- `scheduler_012/native_evidence_012.json` comes from `tools/proto_binary_analysis/scheduler_evidence_012.py`.
- `scheduler_012/package_name_scan_012.json` comes from `package_name_scan_012.py` (27,365 packages).
- `scheduler_012/preview_instance_override_012.json`.
- Model check: `tools/proto_binary_analysis/clock_model_012.py`.

## 1. Producer of block+0x86c

`UProtoRichTextBlock` multiply inherits `FTickableGameObject` at block+0x678.
- The ctor (`0x99bbd2`) calls `0x2730130`. That routine is UE4.27 `FTickableGameObject()`: it reads the statics `0x2736140`, locks, and adds to NewTickableObjects.
- The ctor then installs vtable `0x31cac38`. Base vtable `0x389ac78` has purecalls in slots 0 and 4.

| slot | base | Proto | meaning, proven by dispatcher `0x27421f0` |
|---|---|---|---|
| 0 | purecall | `0x9a5b30` | `Tick(float)` (called via `[rax]`, xmm1 = DeltaSeconds) |
| 1 | false | false | `GetTickableTickType` = Conditional (`cmp al,2` = Never) |
| 2 | true | `0x9a2bb0` | `IsTickable` (`+0x10`) |
| 3 | true | true | default-true gate (`+0x18`) |
| 6 | false | `0x9a2bb0` | `IsTickableWhenPaused` (`+0x30`, called only when bIsPaused) |
| 8 | null | `0x9a1840` | `GetTickableGameObjectWorld` (`+0x40`, compared to World) = UObject::GetWorld |

`0x9a5b30`, with `this` = block+0x678:
```
acc(+0x86c) += DeltaSeconds
if rem(+0x870) >= 0 && acc >= rem: block->vfunc[0x358]()      // process_reveal_budget 0x9a3900
```
`0x9a2bb0` returns `AnimateWhilePaused(+0x680) && +0x868`. +0x868 is set to 1 by the ctor. It is cleared only by the
Proto `BeginDestroy` override `0x99cb10` (block vtable slot +0x80, tail-calls the parent). The grandparent is
`0x10fe5a0`, proven to be UObject::BeginDestroy by its assert string at `0x3363eb0`. No other writer exists: a linear
sweep of 0x990000..0x9b0000 found only the ctor, `0x9a3c16/0x9a3c1f` and `0x9a4000/0x9a4008`.

The dispatcher is `FTickableGameObject::TickObjects(World, TickType, bIsPaused, DeltaSeconds)` at `0x27421f0`, a shipping build
with the editor branch removed. Callers:
- `UWorld::Tick` `0x242c4c5`. It runs after `FTimerManager::Tick 0x2741850`, and only when `TickType != TimeOnly && !bIsPaused`. Both get the same xmm6.
- The engine loop `0x2342a88` with World = nullptr. That call never matches a Proto block that has a world.

The `UWorld::Tick` time update (`0x242bdc7..0x242be47`) is exact UE4.27:
`RealTime(+0x5a8)+=raw`; `if !paused Audio(+0x5ac)+=raw`;
`dt=FixupDeltaSeconds(raw*EffectiveTimeDilation)` (WorldSettings vfuncs 0x648/0x650); `DeltaTimeSeconds(+0x5b0)=dt`;
`UnpausedTimeSeconds(+0x5a4)+=dt`; `if !paused TimeSeconds(+0x5a0)+=dt`.

## 2. Clock paths

- **AnimateWhilePaused = false.** Proto is never ticked. It schedules with `InternalSetTimer 0x2739fa0` on
  `World->OwningGameInstance(+0x180)->TimerManager(+0xd0)`, or on `World+0x368` when there is no game instance.
  The call uses rate = remainder, bLoop = 0 and FirstDelay = −1.0 (`0x31221a8`). The delegate `0x798610` is `jmp [vtbl+0x358]`.
  The stamp is `+0x7e0 = World.TimeSeconds`, and on a fire `elapsed = TimeSeconds − stamp`. The clock is gated by pause and dilated.
- **AnimateWhilePaused = true.** The clock is `acc` (Σ world dt over TickObjects calls, paused or not). The re-arm path stores
  `+0x870 = remainder` and `acc = 0`, and it does not set a timer.
- Common budget (`0x9a3900`):
  - `budget = max(pending(+0x7e4), elapsed)`.
  - Loop: if `idx+1 >= count`, call finish (`0x9a07b0`). Otherwise advance the index, `budget -= pending`, and set `pending = select_delay(class of the char just revealed)`. Repeat while `budget >= pending`.
  - After the loop, `pending -= budget` (always > 0), then re-arm.
  - `OnPrintLetter(+0x6c8)` is broadcast once per call. `OnPause/OnResume LetterByLetterPrint (+0x6e8/+0x6f8)` describe text pacing, not game pause.
- `select_delay 0x9a0880`. An override (+0x681 → +0x684) wins. With `UseAdvancedPrintIntervals` false (run+0x78), every class
  returns the base interval (run+0x74). `EndHoldTime (+0x690)` is written only by the ctor and read by no native code
  and by no shipped package.

## 3. What "Animate While Paused" guarantees in this build

When the flag is true, the reveal advances with world dt on every world tick of the owning game world, paused or not, and
whether the widget is visible or not. Time dilation and FixupDeltaSeconds still apply; it is not real time. The timer manager
is not used.

It does **not** guarantee clean lifecycle. Tick and IsTickable never test `bPrinting (+0x7ea)`, and finish, ShowText and
stop-early never reset `+0x870`. This produces three native quirks: (a) after completion, normal finish (OnFinish false)
re-runs on every world tick until the next print; (b) after ShowText, reveal processing continues; (c) a reused block whose
first delay is 0 starts with a stale `acc` and catches up instantly (`0x9a3ff1 → 0x9a4222` skips the `acc = 0` store).

Shipped usage, from all 27,365 package headers: the flag is overridden only in `WBP_SubtitlePreview` (settings menu, true).
Gameplay blocks come from `WidgetBlueprintLibrary::Create` in `WBP_SubtitlesWidget`. The variable is
`CPF_Edit|BlueprintVisible|BlueprintReadOnly`, not ExposeOnSpawn, and its class default is false. The only native
`AnimateWhilePaused` string is the reflection name.

## 4. Stock routes certified in this binary

| BP function | impl | reads / calls |
|---|---|---|
| GameplayStatics.GetTimeSeconds | `0x235ec10` | World+0x5a0 (same field as Proto) |
| GameplayStatics.GetUnpausedTimeSeconds | `0x235ec70` | World+0x5a4 |
| GameplayStatics.GetRealTimeSeconds / GetWorldDeltaSeconds | `0x235d9f0` / `0x235ee60` | +0x5a8 / +0x5b0 |
| KismetSystemLibrary.K2_SetTimer(Object, FunctionName, Time, bLooping, InitialStartDelay, Variance) | `0x24047c0` → `0x24048c0` | same TimerManager selection → `K2_FindDynamicTimerHandle 0x273a600` → `InternalSetTimer 0x2739fa0`, FirstDelay = Time + InitialStartDelay |
| KismetSystemLibrary.K2_ClearTimer(Object, FunctionName) | reflected | clears by bound function |
| UUserWidget::NativeTick | `0x1ebc940` | animations → `ProcessLatentActions(this,dt)` → `if bHasScriptImplementedTick (+0x1e4 bit 3) Tick()`; **no pause gate** |
| UUserWidget::UpdateCanTick fragment | `0x1ef8f81` | CanTick = ClassRequiresNativeTick ∣ bHasScriptImplementedTick ∣ latent actions ∣ sequence players |
| AdHocUtils.DelayUntilNextTick | `0xca52f0` | latent action (`FDelayUntilNextTickAction`, vtable `0x3274fd0`): no stronger than a widget tick; rejected |

## 5. Adapter decision

- `AWP=false` (EXACT_EQUIVALENCE). `K2_SetTimer(self,"Arabic Clock Fired",remainder,false,0,0)` with
  `stamp = GetTimeSeconds`. It uses the same timer manager object, the same `InternalSetTimer`, the same world-tick phase, the same pause gate and dilation, and the
  same `max(pending, elapsed)` rule. Model: 4000/4000 random lines (pauses, dilation, 0.1–0.4 s spikes) give frame-identical reveals.
- `AWP=true` (SAFE_APPROXIMATION, preview only). WBP Event Tick (Slate, later in the same frame) polls
  `GetUnpausedTimeSeconds − stamp`, which equals Σ world dt. Model, visible every frame: 3999/4000 lines identical, with 1 item in 76,002
  off by one frame because of an f32 tie. While hidden, Proto keeps going but the Arabic reveal waits for the next tick and then catches up.
  The three native quirks are deliberately not reproduced.
- NOT_ACCEPTABLE:
  - a world timer for AWP=true, because the reveal freezes in the paused menu;
  - Slate `InDeltaTime`, because it is real time, undilated, and skips hidden frames;
  - immediate display for the preview without supervisor approval;
  - any native hook.

## 6. Completion cadence (native vs Arabic)

**Native.** `OnBegin` fires synchronously after arming. Char i is revealed at the first eligible frame where elapsed ≥ D_i,
with D_0 = d(c0) and D_{i+1} = D_i + d(c_i). `OnFinish(false)` fires in the call where elapsed ≥ D_N = D_{N−1} + d(c_{N−1}),
which is one interval after the last char and is quantized to the frame. Catch-up allows several chars, and the finish, in one call.

**Arabic (011 ledger).** `Finish(false)` fires in the same step as the last unit, so there is no trailing interval.
Spaces and combining marks are not counted, but natively every char takes the base interval when advanced intervals are off.

**Consumers.** The block's own dispatcher has no binder in any shipped package. The visible end state is the same.
This is a SAFE_APPROXIMATION and is not changed.
