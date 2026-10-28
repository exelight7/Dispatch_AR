# Round 011 — native timing evidence and the unbound clock

2026-10-25, Asia/Riyadh. Static read-only inspection of the shipped executable and cooked Blueprint.
**Pause equivalence is NOT_PROVEN. No timer/tick/latent callback is bound in the continuation artifact.**

## Sources

Executable SHA256: `365637a77d4b74a61d198a9927e3dcd437bf3be2247b96fcbe5c2e851ac14923`.
Addresses below are RVAs; image base is 0x140000000. Labels describe behaviour, not recovered symbols.
`tools/proto_binary_analysis/scheduler_evidence.py` reproduces selected excerpts into a NEW output path,
refuses overwrite and checks this hash before decoding. It never runs or modifies the executable.
Evidence: `scheduler_011/native_evidence.json`, `pause_functions.asm`, `pause_field_xrefs.json`.
The global candidate-xref list includes unrelated objects/stack operands; it does not prove a Proto writer.
Explicit excerpt ranges may include padding/neighbouring instructions. A .pdata fragment is not treated as
a whole logical C++ function. Earlier logical-span evidence remains in `../proto_binary/`.

## Original behaviour established by the files

- Original WBP Ubergraph instructions 1/2 copy class `Animate While Paused` into both Proto widgets' native
  `AnimateWhilePaused` property. PrintLetterByLetter and ShowText are parameterless; the pause flag is a property.
  The CDO does not override the flag. Runtime state remains editable.
- The main Blueprint reads `SubtitleTypewriterAnimationEnabled`: enabled invokes PrintLetterByLetter; disabled
  invokes ShowText. The continuation reuses the same option-read instructions and calls Arabic Finish for immediate display.
- In native budget processing, 0x9a392f selects the pause mode at block+0x680. The true branch at 0x9a393b reads
  block+0x86c. The other branch at 0x9a3945..0x9a3956 obtains the world and subtracts block+0x7e0 from world+0x5a0.
  Remaining delay is accounted for in the budget. These are distinct clock paths.
- At0x9a3bf6..0x9a3c1f, the paused branch stores remaining delay at block+0x870 and resets block+0x86c.
  It bypasses the ordinary scheduling call at 0x9a3d96 to helper0x2739fa0. This has the timer-manager shape;
  a recovered engine function symbol is not claimed.
- The producer accumulating block+0x86c and its Tick/Paint/pause dispatch ordering remain unidentified.
  Reading/resetting that accumulator does not establish an equivalent Blueprint clock.
- Normal completion 0x9a07b0..0x9a0847 clears its timer handle and active state, then broadcasts StoppedEarly=false
  (0x9a0838). ShowText 0x9a5710..0x9a5770 takes the active-print stop path; target 0x9a5a30..0x9a5ad3 clears
  timer/active and broadcasts StoppedEarly=true unless notification is suppressed. Generated Finish accepts this
  Boolean delegate argument: false for normal completion, true for explicit skip/immediate completion. Argument
  meaning does not establish final-frame or last-character completion cadence.

## Implemented delay contract and limits

All four frozen R8b tables have PrintLetterInterval=0.025 and UseAdvancedPrintIntervals=false; the generator checks
these preconditions. The ledger follows the authorized `segment_units.py` reference: 0.025 seconds per content
unit nonseparator, noncombining code point; zero delay for immediately visible speaker units. Digits/punctuation/
symbols count under that reference's actual `letters()` function. UTF-16 surrogate pairs are decoded; combining
ranges are frozen to Unicode 15.0.0. Overflow merges full tail content/delay into unit 36. This is the unit-level
reference contract, not proof of every native character-event timing detail.

Arabic Advance Budget consumes an injected delta and generation. Arabic Advance Clocks selects injected WorldDelta/
PausedDelta by the original flag. **Neither receives engine time.** The pause test proves selection/accumulation
only. A generic real-time timer, world timer or widget tick was not substituted for the unknown native driver.
Native last-character/hold/completion cadence also needs certification when binding the adapter.

## Shipped wrap utility

The existing AdHocUtilsBlueprintLibrary.SetTextWrapAt import accepts UTextLayoutWidget, not only ProtoRichTextBlock.
Descriptor 0x4018330 references parameter array 0x32760e8. TextWidget descriptor 0x3276090 links getter 0x1f13a60,
then 0x1f0c270, then 0x1f15260. The latter registers TextLayoutWidget in /Script/UMG (name reference 0x1f1529d).
Thunk 0xcaae80 calls 0xca7bb0, which writes WrapTextAt at+0x110 and dispatches virtual+0x2a8.
This static type/implementation evidence supports reuse for stock RichTextBlock. Generated code calls the shipped
utility for both Arabic widgets; it emits no raw memory writes. Runtime dispatch/layout/capture remain untested.

## Smallest implementation blocker

Identify/certify the writer and driver of Proto's paused accumulation at block+0x86c; bind an equivalent clock/dispatch
adapter for ordinary and paused budgets, including completion cadence. Until then:
`R8B_WBP_STAGE2_REVEAL_PARTIAL`; clock_adapter_bound=false; pause_equivalence_proven=false.

DISPATCH_INTEGRATION_PROVEN=false; IN_GAME_RTL_PROVEN=false; tested_in_game=0; final=0.
