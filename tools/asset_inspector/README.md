# Minimal UE4.27 asset inspector

## R8b style tables (round 021)

```powershell
dotnet tools/asset_inspector/bin/Release/net8.0/asset_inspector.dll --arabic-stylefix-021 . builds/rtl_poc/new-stylefix-run
python -X utf8 -I tools/r8b_021/textstyle_bytes_021.py builds/rtl_poc/new-stylefix-run builds/rtl_poc/new-stylefix-run/textstyle_bytes_021.json
python -X utf8 tools/asset_inspector/test_stylefix_021.py
python -X utf8 -I tools/r8b_021/build_r8b_pak_021.py
```

Stock `URichTextBlock` uses a TextStyleSet only when its RowStruct is a child of `/Script/UMG.RichTextStyleRow` (EXE 0x1ec95e0).
The generator rebuilds only the four DT_AR tables. The RowStruct import pair `ProtoAnimatedText.ProtoRichTextStyleRow` is renamed in
place to `UMG.RichTextStyleRow`, and the eight Proto-only row fields are dropped. `TextStyle` stays byte-identical, and the round-019 WBP is
reused unchanged. `RichTextStyleGate` is the permanent rule. Every table bound to a stock `RichTextBlock` must have a RowStruct that is
a child of `RichTextStyleRow`; the bindings are widget `TextStyleSet` defaults and `SetTextStyleSet` arguments, resolved through
constants, CDO defaults and locals. Anything unresolved fails. The accepted output is `builds/rtl_poc/r8b_stylefix_021/` (NOT_INSTALLED).

## R8b repair (round 019)

```powershell
python -X utf8 -I tools/r8b_019/native_returns_019.py builds/rtl_poc/reveal_clock_012/WBP_SubtitleBlock_AR_REVEAL_CLOCK.json builds/rtl_poc/stage1/original_wbp_baseline.json <new evidence.json>
dotnet tools/asset_inspector/bin/Release/net8.0/asset_inspector.dll --arabic-wbp-repair-019 . builds/rtl_poc/new-repair-run
python -X utf8 tools/asset_inspector/test_repair_019.py builds/rtl_poc/r8b_repair_019
python -X utf8 -I tools/r8b_019/build_r8b_pak_019.py
```

`RepairTiming019` makes `Build Arabic Timing` void: it drops the FString ReturnValue and FUNC_HasOutParms, and turns
`Return Local(Output)` into `Return Nothing`. The output is `GenerateClock(RepairTiming019(frozen 011))` and must byte-equal
`RepairTiming019(frozen 012)`; both inputs are hash-gated. `ReturnContractR` is the permanent return-contract rule: no
statement-level call may return anything but void, a scalar or a thunk-proven plainly stored struct, and every call result,
variable or constant must land in storage of a compatible type. Native signatures come from
`reports/rtl_research/renderer_repair/r8b_repair_019/native_returns_019.json` (EXE UHT tables). The accepted output is
`builds/rtl_poc/r8b_repair_019/` (OFFLINE, NOT_INSTALLABLE, NOT_RUNTIME_TESTED); `r8b_repair_019_dev01` is a byte-identical dev run.

## Arabic font sub-typeface prototype (round 017)

```powershell
dotnet tools/asset_inspector/bin/Release/net8.0/asset_inspector.dll --font-fix-017 builds/rtl_poc/font_017_input builds/rtl_poc/new-font-run
python -X utf8 -I tools/font_017/validate_font_fix_017.py <scratch_dir> <new_result.json>
```

The command appends one Arabic sub-typeface to each of `Montserrat-Variable`, `Orbitron-Variable` and `Rajdhani-Variable`. The inputs are the hash-gated originals from pakchunk0. The sub-font is cloned from the culture-neutral Thai entry and points at `../../../Engine/Content/Slate/Fonts/NotoNaskhArabicUI-Regular.ttf` by cooked FFontData filename. The accepted output is `builds/rtl_poc/font_fix_017/`, which is NOT_INSTALLABLE and not runtime-tested.

## R8b clock adapter (round 012)

```powershell
dotnet restore tools/asset_inspector/asset_inspector.csproj --packages tools/asset_inspector/.packages --source tools/asset_inspector/.packages
dotnet build tools/asset_inspector/asset_inspector.csproj -c Release --no-restore
python -I tools/proto_binary_analysis/clock_imports_012.py reports/rtl_research/renderer_repair/scheduler_012/clock_imports_012.json
dotnet tools/asset_inspector/bin/Release/net8.0/asset_inspector.dll --arabic-wbp-clock . builds/rtl_poc/new-clock-run
python -X utf8 tools/asset_inspector/test_clock.py builds/rtl_poc/reveal_clock_012
```

The input is the frozen 011 pair (hash-gated). The generator adds Arm Clock, Clock Fired (K2_SetTimer target) and Paused Clock, plus a Tick cloned from the shipped WBP_SimpleFadeSwitcher.Tick. It edits only Begin Reveal, Finish and Cancel, and leaves `Arabic Advance Clocks` unused. A plain `dotnet build` (with restore) breaks `obj/` because UAssetAPI is only in `.packages`; use the restore line above. The accepted output is `builds/rtl_poc/reveal_clock_012/`, which is NOT_INSTALLABLE; `reveal_clock_dev01` is a byte-identical development run.

## R8b Stage 2 initialization (round 010)

```powershell
dotnet build tools/asset_inspector/asset_inspector.csproj -c Release --no-restore
dotnet tools/asset_inspector/bin/Release/net8.0/asset_inspector.dll --arabic-wbp-stage2 . builds/rtl_poc/new-stage2-run
dotnet tools/asset_inspector/bin/Release/net8.0/asset_inspector.dll --validate-arabic-wbp-stage2 . builds/rtl_poc/stage2
python -X utf8 tools/asset_inspector/test_stage2.py
```

The accepted detached artifact is `builds/rtl_poc/stage2/`; Stage 1 is an immutable input and is not regenerated.
Stage 2 adds the ar/ar- gate after original instruction6, an Arabic initialization CFG, six state fields and six helpers.
The emitted markup helper is evaluated against the canonical segmenter on 96 fixtures; all 39 threshold cases use exact
float32 powers. This is an offline instruction evaluator, **not** execution in Unreal or DISPATCH. No render/reveal runtime proof.

The validator checks the exact intended patch, branch/context-skip bounds, source-relative nested relocation certificates,
FFieldPath/import/function references, both continuation reachability and English traces with the typewriter on/off.
All generated CFGs are acyclic except the explicitly bounded segmentation loops; English flow-stack continuations are
checked separately. Six malformed variants must trigger specific diagnostics. Nineteen untouched function payloads/script
hashes are identical; Set Displayed Line and Stop Displaying Line intentionally change. Two-generation and reread/save
binary equality are mandatory. Runtime binding/native dispatch still require a later runtime test.

This is an **initialization subset**: speaker units appear immediately, remaining units stay hidden until the future
Arabic Step scheduler. No timer, per-unit delay ledger, Arabic Finish, pause-compatible scheduling, next-layout-tick
capture or live outline/size/wrap update extension is generated. Never install it. See `WBP_STAGE2_RESULT.md`.

## R8b reveal-control continuation (round 011)

```powershell
dotnet build tools/asset_inspector/asset_inspector.csproj -c Release --no-restore
dotnet tools/asset_inspector/bin/Release/net8.0/asset_inspector.dll --arabic-wbp-reveal . builds/rtl_poc/new-reveal-run
dotnet tools/asset_inspector/bin/Release/net8.0/asset_inspector.dll --validate-arabic-wbp-reveal . builds/rtl_poc/reveal_control_011
python -X utf8 tools/asset_inspector/test_reveal.py
python -X utf8 scripts/verify_project.py
```

Review artifact: `builds/rtl_poc/reveal_control_011/`. **R8B_WBP_STAGE2_REVEAL_PARTIAL**: Step, Finish, Skip,
reset, delay ledger and live style/wrap helpers are generated. Advance Budget/Clocks accept injected inputs only;
no engine callback is bound, and native pause equivalence is unproven. Never install this artifact.
Stage1/Stage2 are immutable inputs (79 files). Generation refuses existing output directories.
The reread-bytecode evaluator covers19 lifecycle cases plus six negative fixtures and checks the generated immediate
display branch. See `WBP_REVEAL_RESULT_011.md` and `SCHEDULER_TIMING_011.md` in renderer_repair reports.

## R8b WBP Stage 1 (round 009)

```powershell
dotnet build tools/asset_inspector/asset_inspector.csproj -c Release --no-restore
dotnet tools/asset_inspector/bin/Release/net8.0/asset_inspector.dll --arabic-wbp-stage1 . builds/rtl_poc/new-stage1-run
dotnet tools/asset_inspector/bin/Release/net8.0/asset_inspector.dll --validate-arabic-wbp-stage1 . builds/rtl_poc/stage1
python -X utf8 tools/asset_inspector/test_stage1.py
python -X utf8 scripts/verify_project.py
```

The generator refuses an existing output directory and accepts outputs only beneath the project's `builds/rtl_poc/`.
The accepted round-009 artifact directory is `builds/rtl_poc/stage1/`. It contains the four `/Game/ArabicReveal/`
tables and the detached WBP pair, typed JSON/schema snapshots, original baseline, per-row change log,
instruction offset inventory, SHA256/export/bytecode evidence, and identical `determinism/` and `roundtrip/` copies.

The validator independently reparses all five assets, checks indices, the actual reachable WidgetTree, reciprocal slots,
the exact appended BPGC/CDO schema, all dependency arrays and the create/serialize event DAG. It compares original
export payload bytes and hashes serialized Kismet bytes for all 21 original functions. Ten negative tests mutate
models read from the real generated binaries; they do not modify the accepted binaries. Validation also verifies the
stored source hashes and the binary determinism evidence. The Python integration test reuses `segment_units.py`
at capacity 37, checks overflow text/timing and markup preservation, and invokes the independent binary validator.

The typed JSON comparison normalizes layout offsets and three optional legacy package-index fields (`Next`,
`ArrayInnerProp`, `StringTableAsset`): the JSON bridge materializes null as 0, while UE4.27 rereading returns null.
This does **not** waive byte checks: every binary pair survives reread/serialize with zero differing bytes, and
34/37 original export payloads remain identical. Only BPGC fields, CDO defaults and Overlay_0's child list change.

Widget fields have null CDO defaults, matching the original named widget fields. Correct runtime name binding is
not established by serialization. Stage 1 changes no original Kismet or runtime calls. All Arabic widgets are Collapsed.
**STAGE1 / OFFLINE / NOT_INSTALLABLE / NOT_RUNTIME_TESTED.** See `WBP_STAGE1_RESULT.md` and `WBP_STAGE2_BYTECODE_MAP.md`.

Requires existing .NET SDK/runtime 8. UAssetAPI 1.1.0 comes from [the author's official NuGet package](https://www.nuget.org/packages/UAssetAPI/1.1.0). API reference: [UAsset](https://atenfyr.github.io/UAssetAPI/api/uassetapi.uasset.html).

```powershell
dotnet build tools/asset_inspector/asset_inspector.csproj -c Release --no-restore
dotnet tools/asset_inspector/bin/Release/net8.0/asset_inspector.dll --self-check
dotnet tools/asset_inspector/bin/Release/net8.0/asset_inspector.dll extracted/Dispatch/Content/Shared/Core/Widgets/WBP_SubtitleBlock.uasset reports/rtl_research/new-export.json
python tools/asset_inspector/summarize.py reports/rtl_research/new-export.json
```

Keep `.uexp` and `.ubulk` beside input `.uasset` where present. Inspection writes only a new JSON file, refuses overwrite, reports in-memory binary roundtrip equality, and checks source hashes before/after. JSON export success is not proof that opaque native data was fully interpreted. No mappings file was needed for these tagged UE4.27 assets.

`--layout-prototype <source WBP_SubtitleBlock.uasset> <new WBP_SubtitleBlock.uasset>` creates a detached, exact-source-hash-gated experiment. It changes five layout exports, keeps 32 remaining export payloads byte-identical, and retains the original typewriter. It emits JSON and a verification file beside the new pair. **Keep `prototype/` out of distributables.** Its original-path override would affect English too; UE4.27 does not support normal L10N replacement of bytecode Blueprints. This is not an Arabic typewriter fix or a tested game patch.

Serena's C# server required an unavailable .NET10 runtime. The coordinator explicitly authorized ordinary file edits with installed SDK8; no runtime was installed. Release build and selfcheck passed with SDK8.

`--word-reveal-prototype <DT_SubtitlesProtoRichText[_Large].uasset> <new same-name .uasset> <SpaceInterval>` writes a detached timing experiment. It sets letter and anim to 0, advanced to true, the given space value, and the punctuation waits to 0 in every row. It refuses `steamapps`/`L10N` outputs and existing files. It also does a reread with binary roundtrip and a full JSON structured diff, failing on any change outside those values, and writes `.verification.json` with SHA256 values and a byte diff. Original package path: installing it would change English. **Not installed, not distributable.**
