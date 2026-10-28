# R8b test: reuse of DISPATCH's M_SubtitlePrinting math (UE ISOLATED TEST, UE 5.8.4, NOT 4.27, NOT DISPATCH)

- **Run:** `sh tools/ue427_stock_reveal_test/run_gates.sh RevealGate.TintB`.
- **Material:** a mirror of the shipped pixel math read from DXBC (`dispatch_shader_evidence/M_SubtitlePrinting_map34/12_PS_924.asm`): `emissive = Color/VC`, `opacity = saturate((VC.b-0.1)*1.11)`. The shipped VS print-scale offset is not mirrored; it is ≤ 0.01 px at the revealed state (audit §6).
- **Code:** row B = 10.5^-i; Border tint B = 10.5^t; maximum 37 units (`long_wrap` 39 → 37).
- **Results:** `results.json` (`R8_all_pass: true`), `pixel_check.json` (36/36).
