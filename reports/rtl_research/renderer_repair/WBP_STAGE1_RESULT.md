# WBP Stage-1 result — R8B_WBP_STAGE1_PASS

2026-10-25, Asia/Riyadh. **STAGE1 / OFFLINE / NOT_INSTALLABLE / NOT_RUNTIME_TESTED.**

## Session result

Four Arabic R8b table pairs and a detached WBP pair generated and validated. Validator errors=0;
unexpected original export changes=0; all 21 original function bytecode SHA256 values and entire payloads unchanged.
Generation twice and reread/serialize produce identical .uasset and .uexp bytes for all five assets.
General project verification: STATIC_PASS 25/25. Runtime integration is not implemented or proven.

## Supervisor task summary

Implemented Supervisor Reply 008: clone shipped styles, add a hidden stock-widget subtree and named object properties,
validate the cooked package structure, preserve original script, prepare Stage-2 mutation sites and future rollback.
The exact instruction is saved as `lastnews/supervisor_reply_008.md`. This round ends at the Stage-1 boundary.

## R8b DataTable generation

Location: `builds/rtl_poc/stage1/Dispatch/Content/ArabicReveal/`, virtual `/Game/ArabicReveal/`.
Four assets: DT_AR_Fill, DT_AR_Fill_Large, DT_AR_Outline, DT_AR_Outline_Large. Each has Default,u0..u36 (38 rows).
Default uses index0. Unit i uses float32 B=10.5^-i, R=G=A=1. Codes are finite, positive and strictly decreasing.

The template is the original normal table's Default/Default_Large/Default_Outline/Default_Outline_Large style as appropriate.
These already have the required 28/36 sizes and outline 0/2. The separately named shipped Large table is size32;
it is inspected/hash-protected, not used as a size36 template. ProtoRichTextStyleRow remains the shipped row struct
(compatible inherited rich-text style); no new struct or native type is invented. Extra Proto timing fields are retained.

Fill FontMaterial points to shipped M_SubtitlePrinting; outline rows also retain shipped MI_SubtitlePrinting_Bold and
outline size2, with OutlineColor changed to the same index code. Shadow reuses Fill/Fill_Large. No shadow tables.
Font face, Medium typeface, spacing, shadow settings, transforms and all unrelated source fields are preserved.
Every colour edit is recorded before/after in `table_intentional_changes.json` (228 field entries). Asset identity,
row expansion and style-selection transformations are in `table_asset_changes.json`; exact typed snapshots are adjacent.
Each clone receives a deterministic SHA256-derived GUID; package identity moves only to the intended Arabic path.

## DataTable validation

Checks exact row names/order/count, no duplicates, required fields through the full template comparison, correct font
sizes/materials/outline, float32 codes and all unchanged properties. Reparse and VerifyBinaryEquality pass. Explicit
second serialization and independent second generation have **zero differing bytes**, so no serializer-metadata byte
exceptions are needed. The typed JSON bridge canonicalizes single precision, default metadata and optional null indices;
these are not accepted binary differences.

## Original WBP baseline

Read-only extracted pair: `extracted/Dispatch/Content/Shared/Core/Widgets/WBP_SubtitleBlock.{uasset,uexp}`.
Actual baseline: 37 exports, 95 imports, 276 names. Full UAssetAPI package summary, names/imports/exports, offsets,
all four dependency arrays, DependsMap and metadata are in `original_wbp_baseline.json`; source hashes are recorded
in `stage1_verification.json`. Supported source hashes are gated by the generator. All six relevant extracted files
(WBP and both table pairs) are unchanged after generation; independent validation rechecks those hashes.

## Stage-1 widget subtree and WidgetTree

Detached pair: `builds/rtl_poc/stage1/WBP_SubtitleBlock_AR_STAGE1.{uasset,uexp}`.
The filename is a review label; original internal WBP/BPGC names remain. There are 51 exports, 109 imports and 317 names.

```text
WidgetTree(37) -> SubtitleOverlay(26) -> Overlay_0(25)
  [all original children unchanged]
  ArabicSlot_ArabicRoot(45) -> ArabicRoot(38, Overlay)
    ArabicSlot_ArabicShadowRetainerHorizontal(46) -> ArabicShadowRetainerHorizontal(41)
      ArabicSlot_ArabicShadowRetainerVertical(49) -> ArabicShadowRetainerVertical(42)
        ArabicSlot_ArabicShadowBorder(50) -> ArabicShadowBorder(43)
          ArabicSlot_ArabicShadowRichText(51) -> ArabicShadowRichText(44)
    ArabicSlot_ArabicForegroundBorder(47) -> ArabicForegroundBorder(39)
      ArabicSlot_ArabicForegroundRichText(48) -> ArabicForegroundRichText(40)
```

Shadow is earlier in the overlay paint order. All seven new widgets explicitly default Collapsed; all Text is empty.
Every generated widget Outer is WidgetTree37; every slot Outer equals its parent. Parent Slots, child Slot and slot
Parent/Content are reciprocal. Full-tree traversal reaches 14 widgets and 13 slots (7 new widgets + 7 new slots),
with no duplicate ownership, cycles, dangling references or orphans. The actual RootWidget is unchanged, not bypassed.

Borders have ContentColorAndOpacity=(1,1,0,1), the canonical t<0 hidden sentinel, and transparent background/zero
padding. A -1 exponent would also be below the shader's .1 cutoff (10.5^-1=.095238...), but the canonical architecture
explicitly uses zero for t<0. No RGB parent tint is added. BorderSlot padding is zero too. Shadow Border is inside both
retainers; both retainers retain the source blur MI and render settings. RichTextBlock is stock, Center/wrap1050,
FullShaping/Auto flow, initial DT_AR_Fill. No SetText/reveal/timer calls are added.

## BPGC variables

Seven widget FObjectProperties plus four DataTable FObjectProperties are appended; all original fields remain.
The full metadata and CDO audit is `variable_audit.json`.

| Field | Class | CDO value | Reason |
|---|---|---|---|
| ArabicRoot | Overlay | 0 | named access for future helper calls |
| ArabicForegroundBorder | Border | 0 | named access for future helper calls |
| ArabicForegroundRichText | RichTextBlock | 0 | named access for future helper calls |
| ArabicShadowRetainerHorizontal | RetainerBox | 0 | named access for future helper calls |
| ArabicShadowRetainerVertical | RetainerBox | 0 | named access for future helper calls |
| ArabicShadowBorder | Border | 0 | named access for future helper calls |
| ArabicShadowRichText | RichTextBlock | 0 | named access for future helper calls |
| DT_AR_Fill | DataTable | -100 | future foreground/shadow style switch |
| DT_AR_Fill_Large | DataTable | -103 | future foreground/shadow style switch |
| DT_AR_Outline | DataTable | -105 | future foreground/shadow style switch |
| DT_AR_Outline_Large | DataTable | -107 | future foreground/shadow style switch |

Widget property flags are copied exactly from source SubtitleProtoText:
CPF_BlueprintVisible, CPF_ExportObject, CPF_InstancedReference, CPF_RepSkip, CPF_PersistentInstance.
Table handles use CPF_BlueprintVisible and the imported stock DataTable class. All have ElementSize8;
ArrayDim is the source UAssetAPI enum TArray, whose serialized numeric value is **1** (scalar array dimension,
not a newly introduced dynamic array). Field flags are RF_Public,RF_LoadCompleted; RepNotifyFunc None and original
replication metadata are retained.

Offset strategy: no native offset is guessed or serialized. The actual source FObjectProperty representation has
name/type/flags/array dimension but no offset member to fill. Metadata is cloned and only name/class are changed.
Widget CDO references are explicitly null(0), matching the original class's absent/null widget defaults; pointing them
at WidgetTree templates would change the convention and risk sharing templates across instances. The named tree
objects provide future binding targets. Engine linking/name binding is **NOT_RUNTIME_TESTED**; offline field coherence
passes. Four non-null CDO table references are valid imports. STAGE1_VARIABLE_BLOCKED does not apply to serialization.

## Imports

All original imports remain exact; only 14 necessary imports are appended. Existing RichTextBlock/RetainerBox/Overlay/
OverlaySlot/PanelSlot classes, archetypes, blur MIs and their packages are reused. Each added import is referenced by
an export/property/dependency or a required imported object's Outer; no speculative runtime functions are imported.

| Index | Object | Outer | Purpose |
|---|---|---|---|
| -96 | Border | -85 | stock class or required archetype |
| -97 | Default__Border | -85 | stock class or required archetype |
| -98 | Default__RichTextBlock | -85 | stock class or required archetype |
| -99 | /Game/ArabicReveal/DT_AR_Fill | 0 | Arabic table package/object |
| -100 | DT_AR_Fill | -99 | Arabic table package/object |
| -101 | DataTable | -83 | stock class or required archetype |
| -102 | /Game/ArabicReveal/DT_AR_Fill_Large | 0 | Arabic table package/object |
| -103 | DT_AR_Fill_Large | -102 | Arabic table package/object |
| -104 | /Game/ArabicReveal/DT_AR_Outline | 0 | Arabic table package/object |
| -105 | DT_AR_Outline | -104 | Arabic table package/object |
| -106 | /Game/ArabicReveal/DT_AR_Outline_Large | 0 | Arabic table package/object |
| -107 | DT_AR_Outline_Large | -106 | Arabic table package/object |
| -108 | BorderSlot | -85 | stock class or required archetype |
| -109 | Default__BorderSlot | -85 | stock class or required archetype |

## Dependencies

`dependency_audit.json` records all four arrays for every export before/after. Generated widgets/slots require their
class/archetype serialized before creation and their Outer created before creation. Referenced slot/content/material/
table objects are created before serialization. BPGC adds required property classes; CDO adds table imports;
Overlay_0 adds only the new root slot. Existing dependency lists are preserved outside necessary appends.
DependsMap has 51 entries, with the original 37 unchanged and empty entries following the source EDL convention.
The validator checks every index, no duplicate/null dependencies, exact intended arrays, and an acyclic two-event
(create/serialize) dependency graph. Cross-file external table/material loading remains a runtime consideration.

## Original-export diff

34 BYTE_IDENTICAL, 3 EXPECTED_STRUCTURAL_CHANGE, **0 UNEXPECTED_CHANGE**. The three changes are BPGC22,
CDO23 and Overlay_0(25). Exact expected-schema comparison restricts the changes; an allowed export name alone is
insufficient. Full original/generated payload SHA256 for every export is in `original_export_diff.json`.

| Original export | Name | Classification |
|---|---|---|
| 1 | On Finish Letter by Letter Print__DelegateSignature | BYTE_IDENTICAL |
| 2 | ExecuteUbergraph_WBP_SubtitleBlock | BYTE_IDENTICAL |
| 3 | PreConstruct | BYTE_IDENTICAL |
| 4 | On Text Finished Letter by Letter Print | BYTE_IDENTICAL |
| 5 | On Subtitle Color Enabled Changed | BYTE_IDENTICAL |
| 6 | Letterbox Enabled Changed | BYTE_IDENTICAL |
| 7 | Letterbox Opacity Changed | BYTE_IDENTICAL |
| 8 | On Print Letter | BYTE_IDENTICAL |
| 9 | OnInitialized | BYTE_IDENTICAL |
| 10 | Construct | BYTE_IDENTICAL |
| 11 | Set Displayed Line | BYTE_IDENTICAL |
| 12 | Stop Displaying Line | BYTE_IDENTICAL |
| 13 | Format As Subtitle Text With Tags | BYTE_IDENTICAL |
| 14 | Set Has Outline | BYTE_IDENTICAL |
| 15 | Update Text Color | BYTE_IDENTICAL |
| 16 | Apply Speaker Name if Needed | BYTE_IDENTICAL |
| 17 | Get Text Tag Opener | BYTE_IDENTICAL |
| 18 | Setup Dynamic Material | BYTE_IDENTICAL |
| 19 | ChangeTextToLarge | BYTE_IDENTICAL |
| 20 | WBP_SubtitleBlock_AutoGenFunc | BYTE_IDENTICAL |
| 21 | Set Wrap Text At | BYTE_IDENTICAL |
| 22 | WBP_SubtitleBlock_C | EXPECTED_STRUCTURAL_CHANGE |
| 23 | Default__WBP_SubtitleBlock_C | EXPECTED_STRUCTURAL_CHANGE |
| 24 | Letterbox | BYTE_IDENTICAL |
| 25 | Overlay_0 | EXPECTED_STRUCTURAL_CHANGE |
| 26 | SubtitleOverlay | BYTE_IDENTICAL |
| 27 | OverlaySlot_0 | BYTE_IDENTICAL |
| 28 | OverlaySlot_1 | BYTE_IDENTICAL |
| 29 | OverlaySlot_3 | BYTE_IDENTICAL |
| 30 | OverlaySlot_4 | BYTE_IDENTICAL |
| 31 | PanelSlot_0 | BYTE_IDENTICAL |
| 32 | PanelSlot_0 | BYTE_IDENTICAL |
| 33 | SubtitleProtoText | BYTE_IDENTICAL |
| 34 | SubtitleShadowProtoText | BYTE_IDENTICAL |
| 35 | RetainerBox_Horiz | BYTE_IDENTICAL |
| 36 | RetainerBox_Vert | BYTE_IDENTICAL |
| 37 | WidgetTree | BYTE_IDENTICAL |

## Bytecode preservation

All 21 FunctionExports are serialized with UAssetAPI ExpressionSerializer, hashed, compared, and their script bytes
located within the actual original/generated export payloads. Complete function payload equality provides a second,
stronger guard. Raw bytecode SHA256 and byte lengths are in `bytecode_preservation.json`; semantic JSON hashes
are separate and are not mislabelled as raw byte hashes. BPGC's empty script is also preserved.
**ENGLISH_BYTECODE_UNCHANGED=true. ENGLISH_RUNTIME_BEHAVIOUR_PROVEN is not claimed.**

## Validator

Existing `tools/asset_inspector` extended with `ArabicStage1.cs` and two CLI commands. Validation is independently
callable, reparses real binaries, compares exact source-derived schema and property metadata, verifies reachability,
slots/Outer/default visibility, all table styles, imports and original name indices, dependencies, original bytecode/export
bytes, source hashes and stored binary determinism evidence. `independent_validation.json` stores the standalone run.
The model projection normalizes only package-layout offsets and optional zero/null Next/ArrayInnerProp/StringTableAsset
from the UAssetAPI JSON bridge. Binary roundtrip equality has no such exceptions.

## Negative tests

Ten malformed variants of models freshly parsed from the generated binary assets are rejected. They are in-memory
fixtures, not installed packages and not modified accepted outputs:

- missing Border child slot: DETECTED.
- wrong parent: DETECTED.
- duplicate widget: DETECTED.
- invalid import: DETECTED.
- wrong DataTable row count: DETECTED.
- Arabic root visible: DETECTED.
- modified original bytecode: DETECTED.
- dangling package index: DETECTED.
- missing dependency: DETECTED.
- wrong BPGC type: DETECTED.

The bytecode fixture must specifically produce the original-bytecode-changed diagnostic; no exception alone counts
as its success. Other fixtures assert their intended invariant diagnostic. Exact schema comparison also detects
unrelated properties/flags/material/dependency mutations. No new native/editor/toolchain dependencies were installed.

## Determinism

`determinism/` is an independent second construction from source; `roundtrip/` is a new save after binary reread.
All ten binary files compare exactly across all three copies. Typed schema snapshots and row changes are reproducible;
review-only audit filenames do not enter a game package. Generator refuses existing output directories and restricts
writes to project builds/rtl_poc. Development runs stage1_run01..08 are labelled DEVELOPMENT_ONLY; the accepted
artifact is **stage1/**. Early runs exposed JSON-default/empty-FText/legacy optional-index normalization issues;
these were fixed rather than waived as unexpected asset changes.

## Stage-2 bytecode map

`WBP_STAGE2_BYTECODE_MAP.md` identifies actual exports/instructions/logical offsets, the post-profanity seam, existing
flow-stack continuations, planned helpers/state and exact ar/ar- language gate. It includes 81 current nested address/
context-skip operands; the machine-readable relocation inventory and full root-instruction spans are beside the assets.
This is a preparation artifact; no bytecode mutation is executed. It explicitly preserves English Proto/style/delegate/
speaker/censorship/skip/finish/pool operations and names unresolved timer/pause/segmentation edge fixtures.

## R8b package plan and rollback plan

`R8B_PACKAGE_PLAN.md` defines future Arabic tables, a future Stage-2 original-path WBP override, locres/culture metadata
and later images. No new shaders/material copies/EXE/DLLs. Future ownership/version checks and exact mod-only removal
are specified. No installable PAK/ZIP was built and no install/uninstall script was run against the game.

## Files changed

- tools/asset_inspector/Program.cs, ArabicStage1.cs, test_stage1.py, README.md; rebuilt existing .NET8 inspector binaries.
- scripts/verify_project.py: one additional mandatory Stage-1 integration check; existing checks unchanged.
- builds/rtl_poc/stage1/: five asset pairs, JSON/schema/evidence, repeat/roundtrip copies and explicit labels.
- reports/rtl_research/renderer_repair/: this result, Stage-2 map, package plan; status additions to architecture/patch/checklist.
- reports/CURRENT_STATUS.md, FINAL_VERIFICATION.json, rtl_research/RTL_RESEARCH.md; docs/RTL_IMPLEMENTATION.md,
  KNOWN_ISSUES.md and TESTING.md. Existing verification command refreshes its ordinary QA/font/static reports.
- backups/session_009/: relevant original project tools/docs before modification; no massive game assets copied.
- Desktop lastnews/supervisor_reply_008.md and the new sequential report_009.md (never overwrite).

## Commands executed and tests

```powershell
dotnet build tools/asset_inspector/asset_inspector.csproj -c Release --no-restore
dotnet tools/asset_inspector/bin/Release/net8.0/asset_inspector.dll --arabic-wbp-stage1 . builds/rtl_poc/stage1
dotnet tools/asset_inspector/bin/Release/net8.0/asset_inspector.dll --validate-arabic-wbp-stage1 . builds/rtl_poc/stage1
python -X utf8 tools/asset_inspector/test_stage1.py
dotnet tools/asset_inspector/bin/Release/net8.0/asset_inspector.dll --self-check
python -X utf8 scripts/verify_project.py
```

Build: 0 warnings/errors. Stage-1 integration and inspector selfcheck: PASS. Project verification: STATIC_PASS 25/25.
Development generators used new directories stage1_run01..08; first six failed strict schema comparisons, last two
passed preliminary checks. Final stage1 passed all strengthened checks. Other operations were bounded file inspection,
backups, reflection against the installed UAssetAPI assembly, and creation of review reports. Serena's C# server could
not start without .NET10; existing .NET8 tools were used under prior authorization, with no runtime installed.
`git status` reported this workspace is not a Git repository; source hashes/file backups are the preservation evidence.

## Hashes

| Asset | uasset / uexp bytes | uasset SHA256 | uexp SHA256 |
|---|---|---|---|
| DT_AR_Fill | 3,598 / 135,215 | 564FD5EC21BF6019BC9370C7014B198E3E270468F02B6C07F433139C0D81B613 | B9FEEEB5B211C50D02866380568C2D49FCBE3E44F5AC65B586AA6E5EA05DA2C7 |
| DT_AR_Fill_Large | 3,610 / 135,215 | 7CA693E2FEAC213CE646CF579F4FF839A44E8CD28E53E9F80E8431F60F4B96FD | E0615B35FAB7E37D6E206C32D701BD931A42AF6AEA85C25C040AC309BC6CBB1D |
| DT_AR_Outline | 3,604 / 135,215 | F70763C44A79955141D5BDB9B607C0A6F5247F3005BF901E58AB5903C0A78064 | 6E005FF57CF4D8FB16FE7E65B6FD8FD26D321C1FC13FC3AE3A9AA69630B87E87 |
| DT_AR_Outline_Large | 3,616 / 135,215 | 5BCD8F48843149DE519FD93731258033D0F131D7C54CAFB6D06E77E47E84A92E | BE845D56FA6E5F6089F81F8DB5128CDD74C35EB5DEE7F5A0570100F0CB949F84 |
| WBP_SubtitleBlock_AR_STAGE1 | 19,428 / 28,793 | A2E60FAF1F4F1416E2F90F5DC4B0B523CC522A22B648128E81B46BEB8D4B3A0B | 0DF24F1433BFC36F7D30A4D395FCE6760D0801C7D4DFE3712B52C7203715B22F |

All six source hashes and 21 raw script hashes are in the machine-readable evidence. Source WBP:
- uasset: 5B11CA427CC9BC990000E6C4FFA147E07D305E21C15132045FF18CB927D8D8A5
- uexp: 5CC987CF5190E3153A8B6B77E4444E3CB79FED419453175F22A80C2595FBA64F

## What remains unproven

Game loading/name binding, 4.27 outline tint propagation, Arabic runtime language routing, reveal/skip/finish timing,
pause semantics, pooled reuse, post-layout retained captures, ancestor HUD tint and per-speaker colour parity.
Parsing/structural validation and a deterministic roundtrip establish offline coherence, not game compatibility.
The existing UE5.8 evidence is not promoted to a UE4.27 or DISPATCH runtime result.

## Exact blockers and recommended next task

No remaining Stage-1 implementation blocker. The next smallest missing implementation is **the Arabic language-gated
Kismet CFG for Set Displayed Line (export11), after original instruction6**, with correctly scoped English flow-stack
pushes and recomputed labels. Continue with R8b WBP Stage-2 Kismet generator + validator using the prepared map;
do not redo architecture research or install Stage 1.

## Safety/runtime state

No command wrote into the game directory or ran Dispatch/Steam. Source extracted pairs are hash-unchanged; the
previous full game verification remains historical, with no new game writes. No EXE/debugger/hook/DLL/UE4SS work.
The required existing project package-audit check reads the local AES only in memory to detect leaks in the old
experimental archive; the new generator/validator/tests never read it, and no key value is printed or saved.

```text
GAME_NOT_RUN
STEAM_NOT_RUN
PACKAGE_NOT_INSTALLED
IN_GAME_RTL_NOT_PROVEN
DISPATCH_INTEGRATION_PROVEN=false
IN_GAME_RTL_PROVEN=false
tested_in_game=0
final=0
original game files unchanged
AES not exposed
ENGLISH_BYTECODE_UNCHANGED=true
```
