# Detached Arabic renderer prototype

From `C:\Dispatch_AR`:

```powershell
python -X utf8 tools/rtl_renderer_prototype/inspect_assets.py
python -X utf8 tools/rtl_renderer_prototype/build.py
```

Uses existing HarfBuzz/UBA code and installed packages, including PyMuPDF for PNGs.
No EXE, PAK, installer, game process or native module is used. Fixed outputs:
`reports/rtl_research/renderer_repair/`.

`renderer.py` freezes the complete visual layout into immutable glyphs and line
ranges. The controller changes only safe-unit alpha; foreground and shadow use
one mask. `build.py` uses the same 14 prior texts and 3 wrappers, both cluster and
word grouping, and emits JSON and synthetic SVG/PNG comparisons. The previous
timing POC is neither rebuilt nor retuned.

Preparing a final layout can involve several shaping calls for measuring and
wrapping. There are **no shaping or wrapping calls during reveal**. Only the
isolated rejected comparator reconstructs logical-order x. It generously retains
clusters and is not an exact emulator of shipped per-UTF16 slicing failures.

This is not an Unreal module. Style IDs are retained; native italic/size/outline
metrics, materials, atlas integration and RetainerBox blur are not modeled.
See `reports/rtl_research/renderer_repair/ARCHITECTURE.md` for the native design
and its unproven integration requirements.
