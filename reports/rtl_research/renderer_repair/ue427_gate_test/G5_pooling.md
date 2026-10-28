# G5: Pooling / reset / parent tint (isolated model)

**UE 5.8.4: G5_MODEL_PASS_UE58. UE4.27: G5_NOT_RUN.**

## Pooled block model
One foreground RichTextBlock, one shadow RichTextBlock in a RetainerBox, and one threshold RT, reused for three lines.
- SetText happens only at "Set Displayed Line", always after writing threshold -1.
- Skip, finish, reset and stop only write the threshold. RequestRender is called on every write.

| Step | Threshold | fg px | shadow px | fg px outside the current line's final | ok |
|---|---|---|---|---|---|
| A set | -1 | 0 | 0 | 0 | ✓ |
| A reveal | 1 | 1295 | 1295 | 0 | ✓ |
| A skip | 4 (last) | 2604 | 2604 | 0 (equals final) | ✓ |
| A finish | 4 | 2604 | 2604 | 0 | ✓ |
| A reset | -1 | 0 | 0 | 0 | ✓ |
| B set | -1 | 0 | 0 | 0 | ✓ |
| B reveal | 1 | 1825 | 1825 | 0 | ✓ |
| B reset | -1 | 0 | 0 | 0 | ✓ |
| C reveal | 0 | 192 | 192 | 0 | ✓ |
| C finish | 3 | 1168 | 1168 | 0 (equals final) | ✓ |
| C Stop Displaying Line | -1 | 0 | 0 | 0 | ✓ |

failed_checks = 0. No stale units carried over between lines.

## Parent tint / opacity (speaker line, 4 steps)
| Parent | Wrong visible-unit steps | Max pixel at final |
|---|---|---|
| UBorder ContentColorAndOpacity (0.5, 0.5, 0.5, 1) | **2 of 4** | (1, 1, 1, 1) |
| UBorder RenderOpacity 0.5 | 0 of 4 | (0.752, 0.752, 0.752, 0.752) |

- **RGB tint on any ancestor corrupts the unit index.** The colour division hides the tint, but the decode breaks.
- **RenderOpacity is safe.** It affects alpha only.
- Round 004's static audit found no colour tracks on WBP_SubtitlesWidget ancestors. That remains a static finding; DISPATCH in-game behaviour is NOT_PROVEN.
- The observed alpha of 0.752 for opacity 0.5 was not analysed further. It is offscreen output with gamma off, and it does not affect the index.

Not covered: real timer-driven skip/finish (the threshold values are written directly), the finish delegate, `ChangeTextToLarge`, outline toggling.

Screenshots: `screenshots/G5/`.
