# Stock-renderer gate test (round 007): UE ISOLATED TEST, NOT DISPATCH

> **Engine actually used: Unreal Engine 5.8.4** (`D:\EPIC\UE_5.8`, CL 58902052). UE4.27 was **not** installed. The Launcher install produced 5.8, and the user chose "Use 5.8 only" for this round. Every result here is **non-authoritative for UE4.27 and for DISPATCH's custom 4.27 branch**. For 4.27, G1–G3 remain `NOT_PROVEN` and G4/G5 are `NOT_RUN`. The folder keeps the requested name `ue427_gate_test` for continuity.

## Summary (`results.json`)

| Gate | UE 5.8.4 result | UE4.27 status |
|---|---|---|
| G1 VertexColor + coverage | **G1_PASS_UE58**. The row colour reaches the font material as 8-bit sRGB VertexColor; the coverage mask is identical to no-material. **Slate multiplies output by VC**, so the material divides it back. | G1_NOT_PROVEN |
| G2 precision | **G2_PASS_UE58**. sRGB-byte encoding is lossless (256/256). 255-unit functional reveal passed. SAFE_UNIT_CAPACITY_UE58 = 255 (need 69). | G2_NOT_PROVEN |
| G3 threshold without relayout | **G3_PASS_UE58**. 12/12 lines, foreground and retained shadow, 0 SetText/SetTextStyleSet after init, 0 fg/shadow mismatches. RetainerBox needs RequestRender per write and once after SetText. | G3_NOT_PROVEN |
| G4 cook | **G4_EDITOR_COOK_PASS_UE58**. Shared cook puts the material in the project shader archive; inline cook embeds it (33,861 B). | G4_NOT_RUN |
| G5 pooling | **G5_MODEL_PASS_UE58**. A/B/C reuse with 0 failures. RGB tint on a parent corrupts the index; RenderOpacity is safe. | G5_NOT_RUN |

Classification: **STOCK_RENDERER_GATE_TEST_BLOCKED** for UE4.27 (no 4.27 editor). On 5.8 only: STOCK_RENDERER_GATES_G1_G3_PASS_ON_UE58 (non-authoritative). Not claimed: `STOCK_RENDERER_GATES_G1_G3_PASS`, `STOCK_RENDERER_EDITOR_PROTOTYPE_VALIDATED`, `DISPATCH_INTEGRATION_PROVEN`.

## Layout invariance and shaping (real Slate 5.8, not the detached model)
- **Positive cases.** For the 12 corpus lines, plain untagged text was compared with whitespace-unit markup at full reveal. 11 are pixel-identical. long_wrap differs at 4,633 px by at most **5.96e-8** (float rounding of the colour division; the 8-bit PNGs are identical), so the geometry is identical.
- **During reveal.** Every revealed pixel is bit-identical to the final reference on all lines. Desired size never changed. Wrapping and line ranges are unchanged (identical pixels).
- **Negative controls:**
  - `TEST|-42` cut: 2,842 px differ (max 1.0). Slate shapes per run there, which matches the round-004 model's Latin kerning failure.
  - Mid-word Arabic cut `مرح|با`: **0 px differ**.
  - `v1|.02` cut: **0 px differ**.

  So in 5.8 Slate an Arabic mid-word run cut did *not* break joining, unlike the detached model. The whitespace-only rule stays: the Latin case proves cuts can change output, and 4.27 is unverified.
- **Visual check** (screenshots): lam-alef (لا، إلا، الله), harakat (السَّلَامُ عَلَيْكُمْ), joining, `TEST-42`, `v1.02`, `(TEST-42)`, `50 USD`, «…», ؟، !, explicit newline, multiple spaces and a 2-line wrap all render in correct RTL order. Partial reveals keep their final positions (centre-justified lines do not re-centre).

## Culture API (generic engine behaviour, editor 5.8; not DISPATCH)
| Input | SetCurrentCulture ok | GetCurrentLanguage | GetCurrentCulture | GetCurrentLocale |
|---|---|---|---|---|
| ar | true | ar | ar | ar |
| ar-SA | true | ar-SA | ar-SA | ar-SA |
| en | true | en | en | en |
| en-US | true | en-US | en-US | en-US |
| `-culture=ar` on the command line | n/a | ar | ar | ar |
| `-culture=ar-SA` on the command line | n/a | **ar** | **ar** | ar-SA |

`StartsWith(GetCurrentLanguage(), "ar")` is true in all ar cases. With `-culture=ar-SA` the editor resolved language/culture to `ar` (its available localization) and kept the locale `ar-SA`. Under `-culture=ar` the editor printed 30 "Condition failed" lines from its own startup self-checks, before any test ran.

## Files
- `results.json`: gate summary. `harness_results.json`: raw harness output. `pixel_check.json`: PNG re-check.
- `environment.json`, `project_settings.json`, `G1_vertex_color.md` … `G5_pooling.md`
- `materials/M_ArabicReveal.md`, `blueprint_nodes/NODES.md`, `cook/`
- `screenshots/` (264 PNGs) and `pixel_diff/` (188 PNGs). Every image carries a burned-in 28-px label "UE ISOLATED TEST (UE 5.8.4, NOT 4.27) - NOT DISPATCH".

## Reproduce
```sh
sh tools/ue427_stock_reveal_test/run_gates.sh                    # build + RevealGate.All
python -I tools/ue427_stock_reveal_test/compare_pngs.py tools/ue427_stock_reveal_test/Saved/RevealGate
sh tools/ue427_stock_reveal_test/run_gates.sh RevealGate.Culture -culture=ar
```
Set `UE=` to another engine root (e.g. a future 4.27 install) to rerun. The 4.27 port needs the UE4 API spellings (`Material->Expressions`, `UPackage::SavePackage` flags, `FImageUtils::CompressImageArray`, `RenderOnInvalidation` direct), which the first draft of the harness used.
