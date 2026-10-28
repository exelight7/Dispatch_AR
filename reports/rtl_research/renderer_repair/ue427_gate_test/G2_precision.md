# G2: Index precision

**UE 5.8.4: G2_PASS_UE58. UE4.27: G2_NOT_PROVEN.**

## Byte sweep
Rows with R written by two encodings, for i = 0..255. Each row was read back at full coverage with DebugMode 2, so the pixel equals VC.

| Encoding (row R) | Decoding in material | Correct of 256 | Distinct |
|---|---|---|---|
| linear i/255 | round(r·255) | 183 | 183 |
| linear i/255 | round(linear_to_srgb(r)·255) | 2 | 183 |
| **srgb_to_linear(i/255)** | **round(linear_to_srgb(r)·255)** | **256** | **256** |
| srgb_to_linear(i/255) | round(r·255) | 2 | 183 |

Slate packs the vertex colour as an 8-bit **sRGB** byte and linearises it in the shader. Writing the byte through `srgb_to_linear(b/255)` gives a lossless 8-bit channel. Naive linear `i/255` loses 73 values to collisions at the top of the range.

## Functional test (255 units)
- One RichTextBlock holds 255 whitespace units ("كلمة" × 255) at 1600×900.
- The threshold is stepped from -1 to 254 with ClearRenderTarget2D only.
- Result: start blank, every step adds pixels, no pixel removed, every revealed pixel equals the final reference exactly, the last step equals the final, desired size unchanged, 0 reading-order violations, 0 SetText calls during reveal. **pass = true.**

## Capacity
- **SAFE_UNIT_CAPACITY (UE 5.8.4) = 255** units per line. Unit i uses byte i+1; byte 0 is reserved so the colour division never divides by 0.
- Need: the longest Arabic subtitle in `translation/records` has 68 whitespace units, plus 1 speaker unit = 69. p99 = 26, p99.9 = 49. Rows: DT_ArabicReveal has u0..u254.
- Extension if ever needed: a second byte in G (×256). It is not needed and was not tested.

## Other factors
- **Interpolation.** All vertices of a glyph quad carry the same colour, so there is no interpolation error. Measured decode was exact for all 256 bytes.
- **RetainerBox.** The index is decoded inside the font material while the child is drawn into the retainer target, before any 8-bit storage. Retainer precision cannot alias indices. Shadow-in-retainer passed all 12 lines.
- **Linear/sRGB.** Covered by the encoding above. Whether 4.27 packs vertex colours as sRGB the same way is NOT_PROVEN. The `DecodeMode` parameter is kept as the calibration knob (0 = linear, 1 = sRGB, 2 = inverse).
