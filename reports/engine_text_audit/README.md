# Engine and online text inventory

This is a static resource inventory, not a proof that a string appears in Dispatch. The game was not launched. The supplemental 460-record translation output is described below; extracted Engine resources and game files were not written.

## Engine resource

- File: `extracted/Engine/Content/Localization/Engine/en/Engine.locres`
- Parsed with `scripts.localization.read_locres`; resource version 3.
- **20,282 records across 2,195 namespaces.**
- SHA256: `06cb30ea757da9e7edc0fa0ea1b500d0c7e311c322fac24e907f00c052ba7e76`.
- Complete distribution: `namespace_distribution.json`; English text, exact namespace/key, source hash and global index for bounded candidates: the three candidate JSON files.

The resource includes large editor/tooling collections. Examples are AssetTypeActions (456), UnrealEd (327), ContentBrowser (182), UICommands.ModelingToolsManagerCommands (162), NiagaraCompiler (114) and SEventGraph (112). It also contains tests such as STestSuite (214), and hardware-specific input labels. This supports treating it as a mixed engine localization catalog. It does **not** establish that all unselected records are editor-only, nor that any selected record is reachable in the shipping game.

The empty namespace has 631 records; samples include sky-dome demonstration instructions and asset/tooling labels. A keyword scan of it did not provide a persuasive additional native error-message cluster. This was a bounded inspection, not a reachability analysis.

## A: 67 bounded native system candidates

These texts directly describe engine state, network failure, installation/graphics problems or common native dialog actions. This is the first subset selected for the authorized supplemental SystemMessages coverage; building and integration belong to the parent. No whole-namespace selection was used for the mixed Core or Engine collections.

| Namespace | Selected | Whole namespace | Basis |
| --- | ---: | ---: | --- |
| Core | 16 | 71 | Dialog actions, generic loading/saving, URL-launch failure, ini warning and application fault |
| Engine | 16 | 47 | Network initialization/connection, invalid URL/link, map/startup and cooked shader-cache failures |
| MessageDialog | 12 | 15 | Crash/hang, missing game files, system error and graphics-driver dialogs; macOS-only and debug-title rows excluded |
| NetworkErrors | 6 | 6 | Connection failure, host departure, buffer overflow |
| GameViewportClient | 5 | 5 | CONNECTING, LOADING, PAUSED, PRECACHING, SAVING |
| WindowsDynamicRHI | 7 | 7 | GPU/API requirements and driver/capture warnings |
| D3D11RHI | 1 | 1 | Video-memory exhaustion |
| D3D12RHI | 1 | 1 | Video-memory exhaustion |
| Launch | 1 | 1 | Resolution too low to run the game |
| EngineInit | 1 | 1 | Loading |
| EngineLoop | 1 | 1 | Initializing |

For example, Engine/ConnectionFailed says `Your connection to the host has been lost.`; MessageDialog/MissingGlobalShaderLibraryFiles_Body asks the reader to check correct game installation; D3D11RHI/OutOfMemory asks the reader to lower resolution or close other applications. Their wording is user-directed. Their presence alone does not prove that Dispatch invokes those code paths, or loads this resource for an Arabic culture.

Some native candidates are legacy/developer-launch cases (for example command-line/project-file and ini diagnostics). They are included as a small explicit inventory, not a prediction that a typical player sees them. Network candidates likewise do not imply Dispatch has multiplayer gameplay.

## B: 393 optional input/common-text records

| Namespace | Records | Qualification |
| --- | ---: | --- |
| InputKeys | 351 | Includes keyboard/mouse/controller plus VR/mobile/other-platform labels; not a PC-only list |
| FInputChord | 6 | Modifier/key-chord labels and formatting; preserve key identifiers and placeholders |
| InputKeySelector | 2 | Empty/default selection labels |
| SlateAccessibility | 15 | Accessible control names; actual screen-reader integration unverified |
| EditableTextContextMenu | 1 | Modify Text heading |
| UICommands.GenericCommands | 18 | Shared editing commands/tooltips, also used by editor UI; reuse in this game unverified |

A+B is **460 records**, a bounded candidate inventory rather than a translation of the 20k catalog. Input display labels may be overridden by the game's own bindings or glyph UI; native rendering and resource-loading behavior still require actual implementation evidence. Technical keyboard/controller names should follow the project's preservation rule rather than indiscriminate transliteration.

## Supplemental EngineRuntime translation

The parent exported exactly A+B to `translation/source/EngineRuntime.json`. All **460 entries** are now covered in `translation/arabic/EngineRuntime.json`, status **TRANSLATED**. These are only the selected identities; the other 19,822 Engine rows are outside this translation target (including C). This does not assert that all Engine text is translated, or that any selected message is reachable at runtime.

**68 legitimate KEEP entries** retain physical key names, platform/device/framework brands, a punctuation-only label, or key-chord formatting. The exact indexes and reasons are listed in `runtime_keep.json`. Alt/Ctrl/Shift/Cmd, function keys, keyboard legends and controller button identifiers stay recognizable. Left/right qualifiers, controller actions, accessibility control labels, native messages and prose are Arabic. Embedded Windows/OpenGL/Vulkan/Steam/VR brands and technical tokens such as `GIsRunning`, `COOKED`, `UNCOOKED`, `RHI` and command-line flags remain intact.

All 460 entries passed structural checks for exact index coverage and duplicate-key rejection; nonempty values; exact tag/brace-placeholder multisets; counts of pipe/caret/CR/LF/backslash characters; and absence of directional-control or presentation-form code points. No English prose fallback or external translation service was used. This is not literary review, runtime testing, or FINAL acceptance.

Reproduce the supplemental validation with `python -X utf8 reports/engine_text_audit/validate_runtime.py`. Results are in `runtime_validation.json`. This agent did not build or install the supplemental resource, and did not launch the game.

## C: 54 deferred diagnostics/external surfaces

- CrashReportClient: 21. Crash-report UI may belong to a separate process/resource load path. An override in the game package alone is not evidence that the reporter would use it.
- PreLoadManager.BuildPatchServices: 10. Downloader/installer status vocabulary; feature use in this game is unproven.
- UnrealEngine: 23. Mostly development overlays/profiling/rebuild messages, with some memory warnings. Not ordinary dialogue/UI coverage.

The other **19,768** records are left unselected. They were not translated or asserted unreachable. No broad “all SystemMessages localized” claim follows from this audit.

## Online plugins: 46 records translated

| Target | Records | Status |
| --- | ---: | --- |
| OnlineSubsystem | 24 | TRANSLATED |
| OnlineSubsystemSteam | 2 | TRANSLATED |
| OnlineSubsystemUtils | 20 | TRANSLATED |

Outputs are `translation/arabic/OnlineSubsystem.json`, `OnlineSubsystemSteam.json` and `OnlineSubsystemUtils.json`. Original English remains in each unmodified `translation/source/<target>.json` and in the extracted resources. No external translation API was used.

`Steam` is unchanged as a brand (OnlineSubsystemSteam index 1). Embedded technical identifiers `ClientWorldPackageName` and `NetGUIDAck` are preserved in otherwise translated messages. OnlineSubsystemUtils also contains three K2Node/editor-style rows (10–12); all requested plugin records were translated, without claiming those three are player-facing.

Validation passed for all 46 plugin entries: exact index sets, nonempty strings, tag/brace-placeholder preservation, pipe/caret/CR/LF counts, and absence of bidi controls/presentation forms. These are structural checks. Status is **TRANSLATED**, not REVIEWED, TESTED or FINAL; plugin reachability and visual rendering are untested.

Reproduce inventory and plugin checks from the workspace root with:

`python -X utf8 -m reports.engine_text_audit.audit`
