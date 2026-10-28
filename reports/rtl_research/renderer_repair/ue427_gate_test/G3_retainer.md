# G3: Threshold updates without relayout (RetainerBox, foreground/shadow)

**UE 5.8.4: G3_PASS_UE58. UE4.27: G3_NOT_PROVEN.**

## Setup per corpus line (12 lines, 82 units)
- **Foreground:** URichTextBlock with `DT_ArabicReveal` (no retainer).
- **Shadow:** URichTextBlock with `DT_ArabicReveal_Shadow` inside a URetainerBox (RenderOnInvalidation, as in WBP_SubtitleBlock).
- Both layers sample the same `RT_ArabicReveal`.
- `SetTextStyleSet` and `SetText` are called once at init. After that, only `ClearRenderTarget2D(RT, t)` runs, plus `RequestRender` on the retainer.
- Steps go from t = -1 to N-1. The final reference is t = 10000.

## Results
| Check | Result |
|---|---|
| foreground sequences passing (blank start, no pixel removed, revealed pixels bit-identical to final, every step adds, end = final, desired size unchanged) | **12/12** |
| shadow-in-retainer sequences passing | **12/12** |
| SetText calls after init | **0** |
| SetTextStyleSet calls after init | **0** |
| steps where foreground and shadow visible-unit sets differ | **0** |
| foreground steps whose visible set is not exactly units 0..t | **0** |
| desired-size changes during reveal | **0** |
| reading-order violations (centroids move right→left, then down) | **0** |
| independent PNG re-check (`compare_pngs.py`) | **24/24 layers pass** |

## RetainerBox behaviour (`G3_retainer_policy_*`)
| Retainer mode | Stale steps (speaker / long_wrap) | Finding |
|---|---|---|
| RenderOnInvalidation, **no** RequestRender | 3/3, 39/39 | A threshold change does not invalidate the retainer. **Stale until requested.** |
| RenderOnInvalidation + RequestRender each step | 0/3, 0/39 | Correct on the first paint after the write. No one-frame delay. |
| RenderOnInvalidation = false (phase rendering) | 3/3, 39/39 | **Inconclusive.** All harness paints happen inside one engine frame, so phase rendering never advances. This is a harness limit, not an engine result. |

Extra finding: the long_wrap retainer's first capture right after SetText was empty (22,998 px stale). The retainer consumed its request before the child's text and shader were ready. **The WBP must call RequestRender again on the frame after SetText** (or at every step, which also covers it).

## Not covered
- The real game-frame order. The harness writes the RT and paints in the same game-thread frame, and ClearRenderTarget2D is enqueued before the Slate draw, so there is no delay. Real-viewport behaviour and the 4.27 retainer implementation are NOT_PROVEN.
- The outline (`OutlineSettings.OutlineMaterial`) path was not tested.

Screenshots: `screenshots/lines/<id>/{fg,shadow_retainer}/tNNN.png`, `final.png`. Diffs: `pixel_diff/<id>/...` (grey = equals final, red = differs, black = hidden).
