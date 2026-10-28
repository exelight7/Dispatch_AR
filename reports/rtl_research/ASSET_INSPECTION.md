# Concrete Dispatch subtitle findings — TRANSLATION/RENDERING NOT TESTED

2026-10-23. Input game build 1.0.19512, UE4.27 as established by coordinator. Shipped plugin descriptor `extracted/Dispatch/Plugins/ProtoAnimatedText/ProtoAnimatedText.uplugin` independently declares VersionName 1.02 and EngineVersion 4.27.0. No game was launched or installed.

## Actual shared path

`/Game/Shared/Core/Widgets/WBP_SubtitlesWidget` uses `/Script/AdHocSubtitles:AdHocSubtitlesWidgetBase`; its add-subtitle path obtains pooled WBP_SubtitleBlock instances, adds them to SubtitleBlocksList and calls `Set Displayed Line`. This is a central subtitle path, not a per-line asset workaround.

`/Game/Shared/Core/Widgets/WBP_SubtitleBlock` decodes to 37 exports and 95 imports. Export 11 `Set Displayed Line` applies censorship filtering, `ProcessLocalizedTextWithCallback` and speaker-name formatting, then calls `SetText` with the complete processed text on both `SubtitleProtoText` (export 33) and `SubtitleShadowProtoText` (export 34). Both use `/Script/ProtoAnimatedText:ProtoRichTextBlock`.

That function then reads `DispatchCloudSettings.SubtitleTypewriterAnimationEnabled` through `DispatchBoolSetting.GetOptionValue`. Its true branch calls `PrintLetterByLetter()` on both text widgets; its other branch calls `ShowText()` on both. Thus Blueprint supplies complete text and delegates reveal to native Proto code. Prefix-string replacement is not the observed Blueprint mechanism.

`Get Text Tag Opener` (export 17) builds `<text` plus Default/Italic/Outline/Large style attributes, includes a ` donthide="true"` literal under its conditional logic, and closes with `>`. Export 13 `Format As Subtitle Text With Tags` uses `{Opener}{Content}{Closer}`, `</>` and `<Italic>` substitutions. Speaker formatting uses `{OpeningSpeakerTag}{SpeakerName}: </>{SubtitleContent}`. Removing tags from translated locres alone cannot guarantee bypass because this shared formatter adds tags.

`Setup Dynamic Material` creates a dynamic instance from `/Game/Shared/Core/Widgets/M_SubtitlePrinting` and assigns the foreground widget's `OverrideFontMaterial`. `OnPrintLetter` causes both shadow RetainerBoxes to request a render; completion is forwarded through the block's own finish delegate. Preserve the shadow and timing/event path in any future shared renderer change.

## Exact style and layout data

Both text exports: `ProtoTextStyleSet` -> `/Game/Shared/Core/Widgets/DT_SubtitlesProtoRichText`, `Justification=ETextJustify::Center`, `WrapTextAt=1050`, all margins=2. The CDO `Wrap Text Length=1050`; `PreConstruct` and `Set Wrap Text At` call `AdHocUtilsBlueprintLibrary.SetTextWrapAt` for both widgets. No serialized ShapedTextOptions override was found in this asset. Its relevant OverlaySlots are centered.

DT_SubtitlesProtoRichText has 8 `ProtoRichTextStyleRow` rows: Default, Italic, Default_Outline, Italic_Outline and their `_Large` variants. All point to `/Game/Shared/UI/Fonts/Montserrat-Variable`; typefaces are `Medium` or `Medium Italic`, sizes 28 or 36. PrintLetterInterval is approximately 0.025 seconds; PrintLetterAnimationTime=0; UseAdvancedPrintIntervals=false. Outline rows use `/Game/Shared/Core/Widgets/MI_SubtitlePrinting_Bold`; the font material is M_SubtitlePrinting. DT_SubtitlesProtoRichText_Large has 4 rows using sizes 32. `ChangeTextToLarge` assigns both Proto and ordinary RichText style tables, then invalidates both layouts.

Montserrat-Variable is a Runtime CompositeFont with many FontFace imports (Montserrat plus NotoSans, Bengali, CJK, Devanagari and Thai). Its asset name alone cannot establish Arabic coverage or mark support; the font specialist must inspect actual face cmap/GSUB/GPOS data and fallback ranges.

## Exposed Proto surface and hard boundary

Static reflected-name strings in the shipped executable include HideText, ShowText, PrintLetterByLetter, IsLetterByLetterPrintInProgress, Set/ClearPrintLetterIntervalOverride, SetProtoTextStyleSet; OverridePrintLetterInterval, OverridePrintLetterAnimationTime, EndHoldTime, AnimateWhilePaused, OverrideFontMaterial; and begin/print/finish/pause/resume/new-block delegates. The inspected neighborhood did not reveal a public current-character setter or shaping-cluster counter. This is static-name evidence, not an exhaustive reflection dump.

The [author's official Fab listing](https://www.fab.com/listings/ddb894cc-1686-4172-bfde-6d876e1f8af9) documents RTL/Arabic limitations and a markup opt-out to ordinary rich text. Current documentation does not by itself prove every detail of shipped 1.02. The [author's text-rendering tutorial](https://protowlf.com/unreal/printing-text-in-unreal/) explains the full-text/decorator/vertex-color design; it is conceptual source, not Dispatch source. Author docs and the legacy Google Doc URL embedded in the descriptor returned access failures to this research tool. No unsupported source dump was downloaded.

Native Arabic full shaping can help ordinary Slate runs, but the Proto decorator's per-character paint path may still break clusters. A material-only fix cannot restore joining if the native run has already split shaping incorrectly. No exposed method discovered here proves cluster-safe reveal. Disabling typewriter is a diagnostic/static fallback only and does not fulfill the requested animated RTL result.

## Detached experiment and validation

The new SDK8 CLI in `tools/asset_inspector` uses official UAssetAPI 1.1.0. Six source pairs exported and passed in-memory binary equality: WBP_SubtitleBlock, WBP_SubtitlesWidget, DT_SubtitlesProtoRichText, DT_SubtitlesProtoRichText_Large, M_SubtitlePrinting, Montserrat-Variable. All source hashes remained unchanged. JSON files are adjacent to this report; human-readable call summaries are subtitle_block_summary.txt and subtitles_widget_summary.txt. Build: zero errors/warnings; CLI selfcheck passed. See the CLI README for exact usage.

`tools/asset_inspector/prototype/Dispatch/Content/Shared/Core/Widgets/WBP_SubtitleBlock.{uasset,uexp}` is detached and **excluded from distribution**. Only exports 28/29/30 change horizontal slot alignment Center->Fill, and 33/34 change justification Center->Right plus FullShaping/RightToLeft shaped-text overrides with both override flags. The schema names are documented in [UE4.27 FShapedTextOptions](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/UMG/Components/FShapedTextOptions?application_version=4.27); enum/flag names are also present in the shipped executable. Reparse and binary roundtrip pass; the other 32 export payloads, including all Blueprint bytecode, are byte-identical. Adjacent verification JSON contains SHA256 values. These checks prove detached binary serialization only, not that the engine honors all fields or that the decorator renders Arabic correctly.

The [UE4.27 asset-localization documentation](https://dev.epicgames.com/documentation/unreal-engine/asset-localization?application_version=4.27) explicitly excludes bytecode assets such as Blueprints. Therefore do not place this WBP in L10N/ar and claim language-scoped replacement. An original-path WBP override would also alter English. Language-specific Font/DataTable assets remain a possible scoped route, but cannot alone establish right anchoring or cluster-safe reveal. Coordinator instructed that this prototype remain outside the distributable.
