# Text inventory

All 62,861 PAK entries were indexed. There are 159 locres files across packaged cultures, not one monolithic text file. This document inventories discovered sources; it does not prove every visible image/movie/native string is covered.

## Selected translation resources

Modification safety: edit generated copies only; original files remain read-only. All rows below require a new additive PAK, not an original archive overwrite. RTL rendering/reveal status is NOT_RUN/UNRESOLVED as applicable.

| Source file | Format | Original resource rows | Selected rows | Category | Encoding | Safe modification / pack | RTL |
|---|---|---:|---:|---|---|---|---|
| `Dispatch/Content/Localization/101/en/101.locres` | locres v3 | 797 | 797 | UI/Other (review context), Phone / Computer UI, Tutorials, Character Names, Notifications, Choices, Dialogue/Subtitles | Binary index; ASCII/UTF-16 FString | Copies only; new PAK | Not verified |
| `Dispatch/Content/Localization/102/en/102.locres` | locres v3 | 2192 | 2192 | UI/Other (review context), Phone / Computer UI, Character Names, Choices, Dialogue/Subtitles, Notifications | Binary index; ASCII/UTF-16 FString | Copies only; new PAK | Not verified |
| `Dispatch/Content/Localization/103/en/103.locres` | locres v3 | 1254 | 1254 | UI/Other (review context), Phone / Computer UI, Character Names, Notifications, Choices, Dialogue/Subtitles | Binary index; ASCII/UTF-16 FString | Copies only; new PAK | Not verified |
| `Dispatch/Content/Localization/104/en/104.locres` | locres v3 | 1722 | 1722 | UI/Other (review context), Phone / Computer UI, Character Names, Choices, Dialogue/Subtitles, Notifications | Binary index; ASCII/UTF-16 FString | Copies only; new PAK | Not verified |
| `Dispatch/Content/Localization/105/en/105.locres` | locres v3 | 1098 | 1098 | UI/Other (review context), Phone / Computer UI, Character Names, Choices, Dialogue/Subtitles, Notifications | Binary index; ASCII/UTF-16 FString | Copies only; new PAK | Not verified |
| `Dispatch/Content/Localization/106/en/106.locres` | locres v3 | 865 | 865 | UI/Other (review context), Phone / Computer UI, Character Names, Choices, Dialogue/Subtitles, Notifications | Binary index; ASCII/UTF-16 FString | Copies only; new PAK | Not verified |
| `Dispatch/Content/Localization/107/en/107.locres` | locres v3 | 684 | 684 | UI/Other (review context), Phone / Computer UI, Character Names, Choices, Dialogue/Subtitles, Notifications | Binary index; ASCII/UTF-16 FString | Copies only; new PAK | Not verified |
| `Dispatch/Content/Localization/108/en/108.locres` | locres v3 | 2116 | 2116 | UI/Other (review context), Phone / Computer UI, Character Names, Choices, Descriptions, Dialogue/Subtitles, Notifications | Binary index; ASCII/UTF-16 FString | Copies only; new PAK | Not verified |
| `Dispatch/Content/Localization/OtherContent/en/OtherContent.locres` | locres v3 | 50 | 50 | UI/Other (review context), Menus, Phone / Computer UI | Binary index; ASCII/UTF-16 FString | Copies only; new PAK | Not verified |
| `Dispatch/Content/Localization/Shared/en/Shared.locres` | locres v3 | 1685 | 1685 | UI/Other (review context), Phone / Computer UI, Descriptions, Dialogue/Subtitles, Notifications, Settings, Menus, Choices, Tutorials, Objectives, Credits, Character Names | Binary index; ASCII/UTF-16 FString | Copies only; new PAK | Not verified |
| `Engine/Content/Localization/Engine/en/Engine.locres` | locres v3 | 20282 | 460 | UI/Other (review context), Controls/Accessibility, System Messages | Binary index; ASCII/UTF-16 FString | Copies only; new PAK | Not verified |
| `Engine/Plugins/Online/OnlineSubsystem/Content/Localization/OnlineSubsystem/en/OnlineSubsystem.locres` | locres v1 | 24 | 24 | System Messages | Binary index; ASCII/UTF-16 FString | Copies only; new PAK | Not verified |
| `Engine/Plugins/Online/OnlineSubsystemSteam/Content/Localization/OnlineSubsystemSteam/en/OnlineSubsystemSteam.locres` | locres v1 | 2 | 2 | System Messages | Binary index; ASCII/UTF-16 FString | Copies only; new PAK | Not verified |
| `Engine/Plugins/Online/OnlineSubsystemUtils/Content/Localization/OnlineSubsystemUtils/en/OnlineSubsystemUtils.locres` | locres v1 | 20 | 20 | System Messages, UI/Other (review context) | Binary index; ASCII/UTF-16 FString | Copies only; new PAK | Not verified |

Selected total: **12969 records**, including **12483 changed Arabic authorings** and **486 preserved technical/brand/number/symbol values**. All selected records retain original English and identities.

## Other discovered sources

- Project `.manifest`, `.archive`, `.csv`, `.po` companions provide source text, context and alternate language authoring. JSON companions inspected use UTF-16 BOM. Their counts can differ from runtime locres.
- OtherContent has80 manifest/archive keys but50 installed English runtime entries. Episode108 has2,116 runtime entries but2,113 manifest identities. Three runtime keys therefore have unconfirmed manifest context.
- 30 manifest-only identities are retained in `reports/manifest_only_keys.json`; they are not silently counted as completed runtime translations.
- Engine.locres contains20,282 mixed editor/runtime records across2,195 namespaces. Explicitly selected460 system/input/accessibility entries are translated as a sparse ar resource.19,822 Engine entries remain outside that subset; their reachability is not proved.
- Three online plugin English resources contain24+2+20 entries (locres v1); all46 selected.
- Fonts:91 ufont face binaries and14 ttf files; composite Font, FontFace and rich-style DataTable assets. See FONT_ANALYSIS.md.
- Native AdHocStory/AdHocSubtitles and cooked Blueprint/line/choice assets: manifest context points to them, but nonlocalized hardcoded text can remain outside locres.
- FMOD banks contain audio/event data; voice and cinematic timing are unchanged.
- Images and3,435 packaged webm entries may include raster/video text. No complete OCR or replacement of embedded art/movie text has been performed.
- Credits, tutorial, menu/settings, names, choices, dialogue/subtitles, notifications, objectives and computer/hacking text are represented among project categories. Categories are heuristic hints from namespaces/paths; they are not a scene-level content audit.

Detailed machine inventories: reports/all_asset_paths.json, localization_paths.tsv, text_sources.json and engine_text_audit/.
