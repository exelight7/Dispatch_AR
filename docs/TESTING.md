# Testing and acceptance

## Round 019 — repaired R8b

| Command | What it checks |
|---|---|
| `python -X utf8 tools/asset_inspector/test_repair_019.py` | Void-helper ledger vs the canonical segmenter (96 fixtures), the 012 clock replay on the repair (500+500 seeds, 14 lifecycle cases), then `--validate-arabic-wbp-repair-019`: full 012 clock validator, return-contract rule (1120 sites), repair invariants, 27 negative fixtures including the real Run 2 artifact, frozen-input hashes, cross-check, determinism and roundtrip copies |
| `python -X utf8 -I tools/r8b_019/frame_audit_019.py …` | Independent layout/metadata before/after record and call-site audit; see `scripts/verify_project.py` for the arguments |
| `python -X utf8 -I tools/r8b_019/native_returns_019.py <wbp.json> <original.json> <out.json>` | Read-only EXE UHT signature evidence plus thunk store check; negative controls Concat_StrStr and Conv_StringToText must be non-trivial |
| `python -X utf8 -I tools/r8b_019/build_r8b_pak_019.py` | Staging pak: double build byte-equal, 10 paths equal to the 014 pak, readback hash-equal, font pak unchanged |

All of these are offline. The runtime acceptance set (NO CRASH, RIGHT-SIDE ARABIC REVEAL, NO GLYPH MOVEMENT, NO SHAPING
BREAKAGE) needs Run 5 video evidence.


## Round 011 — emitted reveal-control model

`python -X utf8 tools/asset_inspector/test_reveal.py` checks `builds/rtl_poc/reveal_control_011/`:19 lifecycle cases,
six negative mutations, original payload/script preservation, frozen input hashes, deterministic pairs and binary
roundtrip. It executes reread helper instructions and the generated animation-setting predicate with native-call stubs.
The pause/unpause case injects world/paused deltas; **it does not bind/prove Proto's paused clock**. Result remains
R8B_WBP_STAGE2_REVEAL_PARTIAL. No timer delegate exists to validate; scheduler integration is incomplete.
`scripts/verify_project.py` includes this check alongside the unchanged Stage1/Stage2 tests.
`tools/proto_binary_analysis/scheduler_evidence.py` reproduces read-only timing excerpts (new output path on rerun).

## Round 010: Stage-2 initialization

`python -X utf8 tools/asset_inspector/test_stage2.py` evaluates the emitted helper instructions against the canonical
segmenter (96 cases), exhausts 39 threshold inputs and evaluates the emitted language predicate. It also runs the
standalone C# validator, including six specific negative fixtures, source hashes, bytecode/diff/CFG/relocation checks
and binary determinism evidence. This test is now included in `scripts/verify_project.py` alongside Stage 1.
It is an offline model test, not execution in Unreal or the game. No timer/reveal-finish runtime result is claimed.

# Round 009 offline Stage-1 checks

Run `python -X utf8 tools/asset_inspector/test_stage1.py`, or the independently callable C# command
`dotnet tools/asset_inspector/bin/Release/net8.0/asset_inspector.dll --validate-arabic-wbp-stage1 . builds/rtl_poc/stage1`.
The C# validator rereads five binary pairs, checks exact cloned table styles, ownership/visibility/BPGC/CDO/imports,
all dependency arrays and event-graph cycles, preserves original function bytes, and checks deterministic binary copies.
Ten negative variants of the reread models cover malformed slots/parents/duplicates/imports/rows/visibility/bytecode/
references/dependencies/field types. The Python integration test also imports the canonical segmentation implementation
at capacity 37 and checks text/timing/markup and the ar/ar-/arn language boundary.
`python -X utf8 scripts/verify_project.py` includes this check; latest result STATIC_PASS 25/25.
These tests do not run an editor, Dispatch or Steam. Runtime evidence remains absent; tested_in_game=0; final=0.

---

## Automated data checks

- All 20 encrypted index SHA1 values verified against locally derived data.
- Original game files fingerprinted in `backups/original_game_sha256.json`.
- English locres export/recompile semantic equality and compiler idempotency; per-resource byte equality recorded.
- UTF-16 FString boundaries, Unicode roundtrip, malformed/truncated input rejection.
- Missing/duplicate/extra IDs, source English retention, empty Arabic, placeholder/tag multisets, slice/caret/newline/tab counts, corrupt/control/presentation-form text and untranslated candidates.
- URLs and email addresses retained exactly.
- Three data-only PoC resources: one semantic change each, archive byte readback and deterministic packing.
- Optional installer: fake-file copy, repeat install, foreign modification refusal, scoped uninstall.
- Font cmap, OpenType and metric inventory, with probe-character coverage.
- `python -X utf8 tools/rtl_reveal/test_reveal.py`: offline HarfBuzz/UBA reveal oracle. It checks clusters, lam-alef, marks, mixed BiDi, wrap, right anchor, timing, events, skip and the culture gate. PASS covers the model only and is not game evidence.

Results live in `reports/validation.json`, `reports/text_sources.json`, `reports/poc_data_checks.json`, `reports/font_coverage.json` and the final build manifest. Do not equate these checks with a complete literary review.

## Runtime checks — NOT RUN

The user explicitly prohibited launching the game. No Arabic screenshot or motion sequence exists; `tests/screenshots/` is reserved for future real evidence.

Required screens: short/long dialogue, two/three-line subtitles, choices in hover/selected/disabled states, settings, notifications, tutorial, names, mixed English/numbers/punctuation, small/large font sizes, skip/finish behavior, original English regression, culture selection.

Critical animated acceptance: first visible grapheme begins at the fixed right anchor, later clusters extend left in reading order, marks and lam-alef do not split, wrapping remains stable, mixed runs retain order, timing/events stay original. An eventual complete right-aligned subtitle does not prove an earlier left-starting reveal passed.

`NOT_RUN` is not PASS or FAIL. The existing plugin's documented limitation and unimplemented shared renderer fix remain separately recorded as unresolved.

`python -X utf8 tools/rtl_reveal/test_word_timing.py [--json reports/rtl_research/word_reveal_model.json]` checks the word-timing hypothesis. For every frame it asserts that each HarfBuzz shaping cluster is all hidden or all visible; a failure is reported as WORD_REVEAL_REJECTED. It also checks words revealed in one frame, logical reveal order, donthide skip/count and wait before/after, multiple spaces, newline, wrap, a word split across style runs, and the English per-character control. PASS is model-only.

## Round 002 — shipped binary checks

`python -X utf8 tools/proto_binary_analysis/evidence.py` locks the executable SHA256 and verifies 8 reflected field offsets, 8 pointer links, 21 decoded logical function spans and 13 decisive instructions. Output: `reports/rtl_research/proto_binary/`. It reads the EXE and never executes or modifies it. Selected excerpts are filtered from disassembly at known function entries; .pdata fragments are not mistaken for full C++ functions. Function aliases are descriptive, not recovered symbols.

Results: `PAINT_MODEL_LOGICAL_PEN`, `ZERO_INTERVAL_BATCHES_CHARACTERS`, therefore `WORD_REVEAL_REJECTED` for timing-only changes. Existing Word-Reveal/HarfBuzz/mixed-BiDi tests and DataTable POCs were not rerun or rebuilt. The evidence generator's checks reproduce the conclusions on this exact build; they are not a general classifier.

A fresh full SHA256 verification matches all 97 original installation files (22.8 GiB), with no added or missing files: `proto_binary/integrity.json`. Runtime remains NOT_RUN; `tested_in_game=0`, `final=0`.

## Round 003 — detached renderer repair prototype

Commands:

```powershell
python -X utf8 tools/rtl_renderer_prototype/inspect_assets.py
python -X utf8 tools/rtl_renderer_prototype/build.py
```

Reuses the 14 saved texts under 3 wrappers, without rebuilding the timing POC. 42 placement cases, 84 cluster/word plans, 2,908 boundary/adjacent frames: zero shaping-cluster splits, stable final geometry/wrap, matching foreground/shadow masks. Correct placement passes 42/42; rejected logical-pen abstraction fails 42/42. During reveal, HarfBuzz is replaced with a failing stub to catch accidental reshaping. Tests cover source UTF-16 mapping, invalid timing input, zero-delay batches, hold completion, skip/finish idempotence, culture routing and split-alpha negative control.

Ten JSON/SVG/PNG artifacts were byte-identical over repeated builds (`reports/rtl_research/renderer_repair/verification.json`). Mixed/lam-alef/long-wrap/punctuation images are labeled SYNTHETIC. Actual native typography, shader/material/retainer behavior, exact timing events and loading compatibility are NOT_PROVEN. No game file hash recomputation: round 002 integrity reused and no game files accessed. `tested_in_game=0`, `final=0`.

## Round 004 — architecture gate review

```powershell
python -X utf8 tools/rtl_renderer_prototype/run_boundary.py
python -X utf8 tools/rtl_renderer_prototype/exe_names.py
```

`run_boundary.py`: 10 cases (including marks, lam-alef, Latin/digits, multiline, speaker prefix, punctuation, long wrap). Plain shaping is compared against the same text cut into style runs at word start, word end, and word+punctuation positions, each with and without HarfBuzz context. Result: 40/40 whitespace comparisons identical, word+punctuation 10/20. The negative mid-word control is detected 10/10 isolated and 5/10 with context, and the script asserts both detections. Output `reports/rtl_research/renderer_repair/run_boundary.json`.

`exe_names.py`: reads the hash-locked EXE bytes only and asserts presence of required stock class/function/struct names and absence of names expected absent. Also lists install binaries/descriptors. Output `exe_names.json`. Name presence is not behaviour. Runtime NOT_RUN; `tested_in_game=0`, `final=0`.

## Round 006 — static completion sweep

```powershell
python scripts/verify_project.py                                   # aggregate STATIC_PASS report
python -X utf8 tools/translation_qa/qa.py                          # translation QA + Unicode safety
python -X utf8 tools/translation_qa/review_queue.py                # review queue (merges review_log.json)
python -X utf8 tools/font_analysis/coverage.py                     # font coverage, corpus shaping, clipping metrics
python -X utf8 tools/arabic_activation/locmeta.py selftest         # locmeta byte round-trip
python -X utf8 tools/coverage/engine_audit.py --engine-assets DIR  # Engine runtime relevance (reads EXE, hash-locked)
python -X utf8 tools/coverage/cooked_text_scan.py DIR              # FText in cooked copies vs translated identities
python -X utf8 tools/coverage/texture_probe.py DIR THUMBS --out F  # decode texture copies (+ --ocr, targeted)
python -X utf8 tools/coverage/video_probe.py DIR FRAMES --out F    # streams + sampled-frame OCR of movie copies
python -X utf8 scripts/install.py --selftest                       # now also compatibility refusal and dry run
```

`DIR` folders are temporary copies extracted from the paks; the tools refuse a path inside `steamapps`. All results are
STATIC_PASS at most. Literary review status is tracked in `translation/review/review_log.json` (REVIEWED_OK,
CHANGED_AFTER_REVIEW, NEEDS_CONTEXT, BLOCKED); `progress.json` `reviewed` counts only REVIEWED_OK + CHANGED_AFTER_REVIEW.
Runtime tests remain NOT_RUN; `tested_in_game=0`, `final=0`.

End-of-round-006 state: `review_log.json` has a verdict for all 12,973 records: REVIEWED_OK 12,493, CHANGED_AFTER_REVIEW 462, NEEDS_CONTEXT 18 (`reviewed=12955`).
The review was a static AI pass. No human native-speaker review has been done.
The package was built twice in scratch folders and once into `builds/`, and all three are byte-identical (`reports/build/PACKAGE_AUDIT.md`).

## Round 007: editor gate harness (isolated, UE 5.8.4)

- Build and run: `sh tools/ue427_stock_reveal_test/run_gates.sh`. This runs the `RevealGate.All` automation test: offscreen FWidgetRenderer, RGBA32f readback and pixel diffs.
- Independent PNG re-check: `python -I tools/ue427_stock_reveal_test/compare_pngs.py tools/ue427_stock_reveal_test/Saved/RevealGate` (24/24 pass).
- Culture probe: `sh tools/ue427_stock_reveal_test/run_gates.sh RevealGate.Culture -culture=ar`.
- These checks are EDITOR (5.8) evidence only. They are not EDITOR_PASS on 4.27 and not IN_GAME_PASS.

## Round 008: compatibility checks (isolated UE 5.8.4 + offline)

- **`sh tools/ue427_stock_reveal_test/run_gates.sh RevealGate.Tint`:** runs R8 and R8b. The prefix match also runs `RevealGate.TintB`. Outputs go to `Saved/RevealGateTint[B]/results.json`, and `R8_all_pass` must be true.
- **`python -I tools/ue427_stock_reveal_test/compare_pngs.py tools/ue427_stock_reveal_test/Saved/RevealGateTint[B]`:** must report 36/36.
- **`python -I tools/ue427_stock_reveal_test/sim_427_vertex_path.py`:** float32 replay of DISPATCH's shipped VS constants; must report 256/256 and the R8b check passing.
- **`python -I tools/ue427_stock_reveal_test/segment_units.py translation/records`:** segmentation self-check plus the full corpus; 0 round-trip failures and 0 lines over 128 units.
- **`RevealGate.All`:** must stay identical to `reports/rtl_research/renderer_repair/ue427_gate_test/harness_results.json`.
- **Shader evidence:** `tools/shader_inspect/{sar.py,dis.py}` take an extracted `.ushaderbytecode` and a shader-map index. They are read-only.

These are NOT game evidence. `tested_in_game=0`.
