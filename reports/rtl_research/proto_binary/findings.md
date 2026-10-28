# Findings — shipped Proto code, round 002

## Verdict and evidence classes

| Question | Result | Evidence |
|---|---|---|
| Placement during character-run paint | `PAINT_MODEL_LOGICAL_PEN` | `CONFIRMED_FROM_BINARY` |
| Exactly zero computed print interval | `ZERO_INTERVAL_BATCHES_CHARACTERS` | `CONFIRMED_FROM_BINARY` |
| Timing-only word reveal | `WORD_REVEAL_REJECTED` | Consequence of confirmed paint loop |
| Arabic-only resource redirection | `ARABIC_ISOLATION_NOT_PROVEN` | Not analyzed in this round |
| Correct actual-game Arabic | `IN_GAME_RTL_NOT_PROVEN` | No execution |

Confidence: HIGH for the two binary classifications on the hash-locked build.
Exact C++ method names and structure type names for non-reflected objects remain
`INFERRED`; numerical fields, calls, pointer links and control flow are observed.

## Reflection and field offsets

The `ProtoRichTextStyleRow` struct descriptor at RVA `0x400b3b0` includes:
name pointer `0x31cc228`, size `0x298`, alignment 8 and property-array pointer
`0x31cc120`. The latter contains nine property descriptors (base row plus eight
timing fields). Its ops factory `0x9a65c0` also writes size `0x298` / alignment 8.
`0x9a7460` references the struct descriptor at `0x400b3b0` and invokes the struct
construction helper. Its outer/package function is `0x9a6460`, which references
the generated package descriptor `0x31ccf50`. These are distinct struct/package
registration paths, not ordinary timing consumers.

| Field | Row offset | Descriptor RVA |
|---|---:|---:|
| PrintLetterAnimationTime | 0x278 | 0x31cbfd0 |
| PrintLetterInterval | 0x27c | 0x31cbff8 |
| UseAdvancedPrintIntervals | 0x280 | 0x31cc020 |
| CommaInterval | 0x284 | 0x31cc058 |
| SentenceInterval | 0x288 | 0x31cc080 |
| EllipsisInterval | 0x28c | 0x31cc0a8 |
| MidWordDashInterval | 0x290 | 0x31cc0d0 |
| SpaceInterval | 0x294 | 0x31cc0f8 |

Float offsets are explicit descriptor members at descriptor+0x24. The bool is
proved by the descriptor's setter pointer `0x8cdf60`, which writes byte [rcx+0x280]=1;
the bool descriptor's other numeric members must not be mistaken for an offset.
`results.json` records file offsets, referenced strings and confidence per field.

## Timing-field consumption chain

`0x9a4270..0x9a48b7` (row-to-timing-map alias) reads all eight fields together at
`0x9a4675..0x9a46dc`, places them contiguously on the stack, and inserts them into
the block's map at block+0x7f8. `0x99b280` is the map insertion helper; it copies
the 32-byte timing payload at map-entry+8 (48-byte map entries).

`0x9a1fd0..0x9a23a2` starts with the block default timing at +0x848/+0x858,
then resolves a run's style in that map (`0x9a225e..0x9a22b9` and the alternate
style branch through `0x9a2365`). It copies map-entry+8 into run-record+0x70/+0x80.
Thus the run record layout is:

```text
0x70 animation time       0x74 base letter interval
0x78 advanced bool       0x7c comma
0x80 sentence            0x84 ellipsis
0x88 midword dash        0x8c space
```

The live array is at block+0x7a8, stride 0xb0. `0x9a0880..0x9a09c8` consumes these
same fields and returns the chosen float without a minimum clamp. Block+0x681
and +0x684 implement an interval override, which takes precedence over run timing.
This connects reflected row fields to consumption, rather than relying on names.

## Block dispatch chain

Generated registration `0x9a7080` uses native-function table `0x31cda00` (12 entries).
Its `PrintLetterByLetter` name at `0x31cda80` maps to exec thunk `0x9a78f0`.
The thunk dispatches through vtable+0x308. The block constructor `0x99bbc0`
installs vtable `0x31ca898`, whose +0x308 resolves to `0x9a3ec0`.

Other resolved block slots:

```text
0x358 -> 0x9a3900  process reveal budget
0x368 -> 0x9a0880  select delay
0x388 -> 0x99cdd0  advance reveal index
0x390 -> 0x9a0cd0  classify special character (role inferred from comparisons)
```

The important virtual calls can therefore be resolved statically for this class;
stripped symbols did not prevent identifying this path. Runtime subclasses or
reentrant Blueprint callbacks are not proven by this analysis.

## Character paint provenance

1. Block rebuild `0x9a494a` calls `0x9a6630`.
2. That generated class initializer references wide `UProtoRichTextCharColorDecorator`
   (name body at `0x31cce72`) and object-constructor wrapper `0x9a6960`.
3. That constructor installs UObject vtable `0x31cd430`.
4. Slot +0x270 points to decorator factory `0x99e9f0`.
5. Its `0x99eaa0..0x99eaa7` installs decorator vtable `0x31cafe0`.
6. Slot +0x10 points to create-run function `0x99e130`.
7. Its call at `0x99e71f` reaches run factory `0x99d0e0`.
8. Run factory installs vtable `0x31caf38` at `0x99d143..0x99d14d`.
9. Slot +0x90 (`0x31cafc8`) points to the paint implementation `0x9a2bd0`.

This confirms the paint function belongs to the shipped Proto character decorator,
rather than inferring membership from adjacency or the public tutorial.

## Boundaries and limitations

`functions.json` gives every identified span's RVA, file offset, approximate bounds,
incoming references, outgoing calls and hash. Several functions are split across
multiple .pdata records with a shared prologue/epilogue; treating a single record
as the whole function hid important code in the previous helper output.

No public code was copied or treated as shipped evidence. Asset timing values from
round 001 remain `CONFIRMED_FROM_ASSET`; its HarfBuzz and mixed-BiDi harnesses
remain model evidence only. They were not rebuilt or rerun in this round.

The two requested code questions are resolved. Availability of plugin source is
not a blocker for these classifications. A working repair, Arabic isolation,
activation, full-layout drawing integration, and actual-game acceptance are still
unresolved and are outside the authorized static-only round.
