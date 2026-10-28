# R8 tint-threshold test (UE ISOLATED TEST, UE 5.8.4, NOT 4.27, NOT DISPATCH)

- **Run:** `sh tools/ue427_stock_reveal_test/run_gates.sh RevealGate.Tint`. Source: `RevealGateTest.cpp`, `RunTint()`.
- **Design under test:** row colour R = unit index; per-block Border tint G = threshold; custom UI font material; shadow Border inside a RetainerBox; outline rows; foreground colourize retainer (effect MID).
- **Results:** `results.json` (`R8_all_pass: true`) and `pixel_check.json` (36/36 layers, 8-bit).
- **Simulations:** `sim_427_vertex_path.json` (DISPATCH VS constants replay) and `segmentation_stats.json` (7,488 subtitles).
- **Known deviation:** `long_wrap` revealed pixels differ from the final by 5.96e-8 (one float ULP) in G only, and are identical at 8 bits.
