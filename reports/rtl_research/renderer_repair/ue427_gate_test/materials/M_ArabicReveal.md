# M_ArabicReveal (UE 5.8.4 isolated test, not 4.27, not DISPATCH)

Domain UI, blend Translucent, shading Unlit. Built by `RevealGateTest.cpp::MakeMaterial`.

```text
VertexColor (RGB) ─────────────────────────────→ VC
VertexColor (A) ───────────────────────────────→ VA (connected; not used by the final code)
Constant2(0.5,0.5) → TextureSampleParameter2D "RevealRT" (RT_ArabicReveal, SamplerType Color) (R) → Thr
ScalarParameter "DebugMode" → Dbg
ScalarParameter "DecodeMode" → Dec
VectorParameter "SubtitleColor" (RGB) → Col
                         ↓
           Custom "ArabicReveal" (float4)
           ├─ ComponentMask RGB → Emissive Color
           └─ ComponentMask A   → Opacity
```

Custom node HLSL (final):

```hlsl
float r = VC.r;
float s = (r <= 0.0031308) ? r * 12.92 : 1.055 * pow(r, 1.0 / 2.4) - 0.055;
float l = (r <= 0.04045) ? r / 12.92 : pow((r + 0.055) / 1.055, 2.4);
float v = (Dec < 0.5) ? r : ((Dec < 1.5) ? s : l);
float idx = floor(v * 255.0 + 0.5) - 1.0;
if (Dbg > 1.5) return float4(1.0, 1.0, 1.0, 1.0);   // pixel = Slate vertex colour
if (Dbg > 0.5) return float4(VC, 1.0);              // pixel = VertexColor^2
float vis = (idx <= Thr + 0.25) ? 1.0 : 0.0;
return float4(Col / max(VC, 1e-6), vis);            // undo Slate's output x VertexColor
```

## Measured in UE 5.8.4 (`results.json` G1/G2)

- **VertexColor input.** Slate passes the run's `ColorAndOpacity` to the font material as VertexColor. It is quantised to 8-bit sRGB and converted back to linear in the shader.
- **Output multiplied by vertex colour.** Slate multiplies the material output by the vertex colour. A constant white output rendered as (0.0999, 0.5029, 0.8963) for row colour (0.1, 0.5, 0.9). The colour is therefore divided back. Rows use G=B=1, so only R carries the index and needs compensation. With the compensation, `SubtitleColor` (0.2, 0.4, 0.6) rendered exactly as (0.2, 0.4, 0.6).
- **Glyph coverage.** Coverage is still applied: the alpha mask matches the no-material reference exactly, with 0 differing pixels and 864 partial-coverage pixels.
- **Index encoding.** R byte = i+1 (`srgb_to_linear((i+1)/255)`). That gives 255 unit IDs (0..254). Byte 0 is unused, so the division stays finite.
  - Naive linear `i/255` encoding decodes only 183 of 256 bytes correctly.
- **Threshold.** `RT_ArabicReveal.R` (RGBA16f float). -1 = nothing visible, 10000 = everything visible.
- **Sampler type.** `SamplerType` must be `Color`. The 5.8 material compiler rejects `LinearColor` for this RT with "Sampler type is Linear Color, should be Color".
- **Opacity.** Opacity is not multiplied by `VertexColor.A`, because Slate applies vertex alpha itself. RenderOpacity 0.5 on a parent changed alpha only and left the index intact.
