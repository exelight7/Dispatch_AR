# Zero interval: ZERO_INTERVAL_BATCHES_CHARACTERS

Evidence: `CONFIRMED_FROM_BINARY`, HIGH confidence for the base class path.
The field-to-run mapping is documented in findings.md. No inference from Unreal
documentation is needed for this result.

## Delay selector

`0x9a0880..0x9a09c8` returns block override +0x684 when enabled by +0x681.
Otherwise it indexes the run-record array at block+0x7a8 (stride 0xb0).
When advanced intervals are enabled and category is nonzero, it selects:

```text
category 1: record+0x8c (space)
category 2: record+0x7c (comma)
category 3: record+0x88 (midword dash)
category 4: record+0x80 (sentence)
category 5: record+0x84 (ellipsis)
otherwise: record+0x74 (PrintLetterInterval)
```

There is no zero check or minimum clamp between these loads and returning the
chosen scalar. Setting the row's letter interval to zero produces a zero base
delay when no overriding interval is active.

## Initial entry

`PrintLetterByLetter`, `0x9a3ec0..0x9a4261`, resolves the selected interval and
stores it at block+0x7e4. At `0x9a3fe3` it makes a floating zero; `0x9a3fee`
compares the selected interval with it. `jbe 0x9a4222` handles zero immediately.
`0x9a4228` calls vtable+0x358, which is `0x9a3900` in the block constructor's
vtable. Thus an initial zero delay is processed synchronously in this entry call.

## Budget loop

`0x9a3900..0x9a3eb2` computes a nonnegative time budget and compares it to the
current remaining delay. The main loop:

```text
while budget >= remaining_delay:
    if end reached: finish; exit loop
    advance reveal state
    update the relevant run's character animation state
    budget -= remaining_delay
    category = classify current position
    remaining_delay = select_delay(run, category)
```

Decisive addresses:

- `0x9a3a0d..0x9a3a29`: checks end and calls advance-index slot +0x388.
- `0x99ce5f..0x99ce6d`: increments per-run and total reveal indices.
- `0x9a3b1d`: subtracts the old delay from the budget.
- `0x9a3b3f..0x9a3b55`: calls selector slot +0x368 and stores the new delay.
- `0x9a3b95..0x9a3b9d`: loops while budget >= delay, including equality at zero.
- `0x9a3b7f..0x9a3b87`: end path invokes completion slot +0x360, stopping finite text.

For consecutive ordinary text characters with zero letter interval and zero
animation time, the delay does not consume budget, but the index advances.
Consequently multiple characters are processed in one callback. A positive space
interval can end that batch once it exceeds the remaining budget. A large elapsed
budget can consume more than one word; exactly one word per frame is not promised.

## Scheduling boundary

After the loop stops for lack of budget, `0x9a3bf6..0x9a3c0b` subtracts budget
from remaining delay. In the ordinary non-paused path the remaining positive
delay is passed in xmm3 to scheduler helper `0x2739fa0` at `0x9a3d96`.
The same helper itself compares its rate against zero at `0x273a03f..0x273a042`,
but the decisive fact is that Proto consumes zero-delay characters before reaching
that scheduling branch. The helper is consistent with FTimerManager SetTimer;
its exact C++ symbol is not recovered and is unnecessary for this classification.

There is also an AnimateWhilePaused path using block+0x86c/+0x870 accumulation;
the same budget-processing loop still handles zero intervals. Its full Tick/Paint
ordering was not certified in this round.

## Limits

This proves batching in shipped control flow, not runtime animation correctness,
guaranteed Paint ordering, safety under reentrant callbacks, or Arabic isolation.
The paint result independently rejects the timing-only approach. The prior concern
that a zero letter interval necessarily invalidates the timer is not the behavior
of the ordinary path recovered here.
