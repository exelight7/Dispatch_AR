# Technical analysis

Observed locally on 2026-10-23. Game root: `D:\SteamLibrary\steamapps\common\Dispatch`. Workspace: `C:\Dispatch_AR`.

| Component | Evidence / finding |
|---|---|
| Engine | Shipped executable contains UTF-16 `++UE4+Release-4.27`; plugin descriptor targets 4.27.0. Exact engine patch level is not established. |
| Game version | `Dispatch/Config/DefaultGame.ini`: ProjectVersion=1.0.19512. Installed Steam manifest buildid=25637711, appid=2592160. |
| Packaging | 20 v11 PAKs; 62,861 indexed entries. No IoStore `.utoc`/`.ucas` packaging observed. |
| Encryption | All 20 indexes encrypted. Local executable key candidate verified using complete decrypted-index SHA1 for every PAK. Key is local tooling data and excluded from distribution. |
| Compression | repak detects Oodle and Zlib; DefaultGame.ini specifies Kraken, 1MB blocks. New text PAK is uncompressed, additive, and leaves original packages untouched. |
| Localization | Native Unreal FText resources: 10 project locres v3 resources; UTF-16-BOM JSON manifests/archives, CSV and PO companions. Three online plugin English resources use locres v1. |
| UI | UMG/Slate, CommonUI/CommonInput, cooked Widget Blueprints, native AdHoc modules. |
| Story | AdHocStory, per-episode line assets, localized `LocalizeableSlicedText`, speaker identities and choices. `|` marks subtitle slices; do not reorder slices or change timing. |
| Subtitles | AdHocSubtitlesWidgetBase -> pooled WBP_SubtitleBlock -> two ProtoRichTextBlock instances for foreground/shadow. |
| Progressive text | Blueprint sets the entire processed line, then PrintLetterByLetter or ShowText according to SubtitleTypewriterAnimationEnabled. Native ProtoAnimatedText handles reveal; no Blueprint substring-growth mechanism was observed here. |
| Fonts | 105 TTF-compatible face binaries inspected: 91 ufont + 14 ttf. Runtime composite font objects and fallback resources are packaged. |
| Audio | FMOD Studio runtime and `.bank` files. Voice/cinematic timing is not modified. |
| ICU | Full internationalization data packaged, including Arabic locale resources. This does not establish Arabic renderer/reveal success. |

No Unity/TextMeshPro, Ink or Yarn evidence was found in package paths or the inspected subtitle path. This is a scoped negative finding, not exhaustive native-code decompilation.

Sources of truth: `reports/investigation.json`, `reports/pak_inventory.json`, `reports/all_asset_paths.json`, `reports/extraction_manifest.json`, and `reports/rtl_research/ASSET_INSPECTION.md`.

The baseline launch was attempted before the user's prohibition. A transient game window was reported, then was no longer present; no Arabic test or screenshot was obtained. Do not infer a game crash from that observation. No further game launch is authorized or performed.

The optional Serena C# language server required an unavailable .NET 10 runtime. Existing .NET 8 built the small UAssetAPI inspector successfully; no system runtime was installed.
