# Engine functions used by the gate harness and their Blueprint nodes (UE 5.8.4 isolated test)

The harness is written in C++ so that it can run unattended. Every reveal-relevant call is a stock `UFUNCTION(BlueprintCallable)`. These are the same nodes the WBP patch would use.

| Purpose | Harness call | Blueprint node | When |
|---|---|---|---|
| style table | `URichTextBlock::SetTextStyleSet(DT)` | Set Text Style Set | once per widget (init) |
| line text | `URichTextBlock::SetText(markup)` | Set Text (Rich Text Block) | once per subtitle line |
| threshold | `UKismetRenderingLibrary::ClearRenderTarget2D(World, RT_ArabicReveal, (t,0,0,1))` | Clear Render Target 2D | every reveal step, and on skip, finish, reset and stop |
| retained shadow refresh | `URetainerBox::RequestRender()` | Request Render | every threshold write, **plus once on the frame after SetText** |
| wrap / justify | `SetAutoWrapText(true)`, `SetJustification(Center)` | Set Auto Wrap Text, Set Justification | init |
| language gate | `UKismetInternationalizationLibrary::GetCurrentLanguage()` | Get Current Language | once per line |
| parent opacity | `UWidget::SetRenderOpacity` | Set Render Opacity | allowed (alpha only, index intact) |
| parent RGB tint | `UBorder::SetContentColorAndOpacity` | (none) | **forbidden** above the Arabic layer: it corrupts the index (2 of 4 steps wrong) |

Not used at all: per-step SetText, SetTextStyleSet, the SetDefault* overrides, and Material Parameter Collections.

Measured post-init call counts were 0 for SetText and 0 for SetTextStyleSet, across all 12 corpus lines and the 255-unit stress line.
