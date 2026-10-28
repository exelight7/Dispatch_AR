# G1: VertexColor and glyph coverage

**UE 5.8.4: G1_PASS_UE58. UE4.27: G1_NOT_PROVEN** (no 4.27 editor this round).

## Test
- Stock URichTextBlock, text `<u0>ااا ممم</>`, size 64, `F_ArabicReveal`.
- The row colour is (0.1, 0.5, 0.9, 1). The font material is `M_ArabicReveal` in its debug modes.
- The threshold RT is set to "all visible".
- The reference is the same text and row with no font material.

## Results (`harness_results.json` → `G1`, `G1_probes`)

| Probe | Pixel at full coverage | Meaning |
|---|---|---|
| DebugMode 2 (output = constant 1) | (0.099899, 0.502886, 0.896269, 1) | Slate multiplies the output by the vertex colour. VC is the row colour after 8-bit sRGB quantisation (0.5 → byte 188 → 0.502886). |
| DebugMode 1 (output = VC) | (0.009980, 0.252895, 0.803299, 1) | = VC², which confirms the VertexColor node receives the row colour |
| DebugMode 0, SubtitleColor (0.2, 0.4, 0.6), with `Col / VC` compensation | (0.2, 0.4, 0.6, 1) | The compensation is exact |
| Coverage | alpha mask vs no-material: **0** px differ; 864 partial-coverage (anti-aliased) px; 2,888 visible px both | Glyph mask preserved |

## Consequences for the design
1. The index can travel in the run colour. G and B must stay at 1, so the index lives in R only.
2. The material must divide the visible colour by VC, because the stock Slate font-material path multiplies output by the vertex colour.
3. The material must not multiply opacity by VC.A.
4. Round 004 said "colour comes from a material parameter, not from the vertex colour". That is right, but it is not sufficient: without the division the text is tinted by its own index.

## Harness caveat (recorded)
The first paint of a new widget that uses the font material was empty or different in 5 of 590 first paints. A shader compile on first use finished before the next paint. All measurements use the second paint. In a game, the first frame after SetText is normally at threshold -1 anyway, but this has not been checked in 4.27.

Screenshots: `screenshots/G1/`.

Note: the probe file `probe_MIC_Debug_DebugMode1.png` and the JSON label `MIC_Debug_DebugMode1` are stale names. The final `MI_ArabicReveal_Debug` uses DebugMode **2**, and its pixel equals the DebugMode-2 MID result.
