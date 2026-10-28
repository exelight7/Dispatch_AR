# Paint model: PAINT_MODEL_LOGICAL_PEN

Evidence: `CONFIRMED_FROM_BINARY`, HIGH confidence, hash locked in README.
Descriptive function alias: char_run_paint, RVA `0x9a2bd0..0x9a368c`.
Its linkage to UProtoRichTextCharColorDecorator is documented in findings.md.

## Decisive data and control flow

1. At `0x9a2cb1..0x9a2cc9`, the function obtains the layout block's range/context
   through its virtual interface. At `0x9a2d6f..0x9a2d9e` it computes end-start,
   initializes a zero horizontal accumulator, and retains the range's starting index.
2. Each iteration constructs a range `[esi, esi+1)` at `0x9a2dd2..0x9a2dd9`.
   `esi` starts at the logical range start and increments at `0x9a3591`.
   It does not iterate a visual glyph-position array.
3. The function indexes per-character animation/color data at run+0x308 with
   32-byte stride (`0x9a2ddd..0x9a2df6`), using range start and run+0x304.
4. The one-unit range is passed to helper `0x132ec90` at `0x9a2fbd` (and for an
   alternate styled outline sequence at `0x9a3180`). That helper compares the
   requested range with the full cache-key range at `0x132ed34..0x132ed42`, and
   on a miss passes requested begin/end to `0x11d74b0` at `0x132ee79..0x132ee80`.
   Its role as a shaped-range/subsequence helper is inferred from the cached
   sequence/range flow; its exact C++ symbol is not recovered.
5. The slice is passed into a Slate draw-element construction call at `0x9a353b`
   (same target `0x1237880` as the alternate shadow/outline draw at `0x9a3397`).
   Geometry x includes the accumulator at `0x9a3406`.
6. After drawing, `0x9a3544` calls `0x9ce980`, a getter returning dword [sequence+0x40].
   Its integer result is converted to float and ADDED to the accumulator at
   `0x9a3556..0x9a3561`. This is the advance-width role in this call path.
7. Both index counters increase. `0x9a35b5` branches back to the next one-unit range.

Approximate behavioral pseudocode (analyst reconstruction, not source):

```text
pen_x = 0
for source_index from block_begin to block_end - 1:
    slice = shaped_range(source_index, source_index + 1)
    tint = animation_data[source_index - run_begin]
    draw(slice, block_geometry_offset_x + pen_x, tint)
    pen_x += slice_advance(slice)
```

This code can reuse shaping data, but it reconstructs placement by accumulating
slice advances in ascending source-index order. Reusing a shaped subsequence is
not the same as reusing each glyph's final BiDi visual position. No timing value
changes the source-index progression or horizontal accumulator.

## Consequence

`PAINT_MODEL_FINAL_LAYOUT` is rejected for this character-run implementation.
Even when a complete word's alpha changes in one callback, its painted slices
still use this placement loop. The timing-only word-reveal POC is therefore
`WORD_REVEAL_REJECTED` under the supervisor's Case B.

This is a code-path conclusion, not a claim that actual-game Arabic frames were
observed. Exact clipping, font fallback, ligature loss, and which pixels a given
Arabic string produces remain untested. The public tutorial is still only
`PUBLIC_REFERENCE_ONLY`; matching it is unnecessary for this classification.
