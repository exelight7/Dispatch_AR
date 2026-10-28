# Round 003 primary references

Accessed 2026-10-23. Engine primitives, not proof of Dispatch integration. No engine
source archive or Proto source was downloaded.

| ID | Official reference, 4.27 selector | Capability used |
|---|---|---|
| RUN | [FSlateTextRun](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/Slate/Framework/Text/FSlateTextRun?application_version=4.27) | Run painting, style and layout blocks |
| LAYOUT | [FSlateTextLayout](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/Slate/Framework/Text/FSlateTextLayout?application_version=4.27) | Text layout and paint owner |
| LINES | [GetLineViews](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/Slate/Framework/Text/FTextLayout/GetLineViews?application_version=4.27), [FLineView](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/Slate/Framework/Text/FTextLayout/FLineView?application_version=4.27) | Final line blocks, offsets and ranges |
| BLOCK | [ILayoutBlock](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/Slate/Framework/Text/ILayoutBlock?application_version=4.27) | Block geometry, range and text context |
| SEQUENCE | [FShapedGlyphSequence](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/SlateCore/Fonts/FShapedGlyphSequence?application_version=4.27) | Shaped glyph data |
| GLYPH | [FShapedGlyphEntry](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/SlateCore/Fonts/FShapedGlyphEntry?application_version=4.27) | SourceIndex, coverage, advances and offsets |
| RICH | [UMG Rich Text Block](https://dev.epicgames.com/documentation/en-us/unreal-engine/umg-rich-text-block?application_version=4.27) | Style tables and native decorators |
| WRAPPER | [UWidget::RebuildWidget](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/UMG/Components/UWidget/RebuildWidget?application_version=4.27) | UMG-to-Slate construction |
| ATLAS | [GetShapedGlyphFontAtlasData](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/SlateCore/Fonts/FSlateFontCache/GetShapedGlyphFontAtlasData?application_version=4.27) | Atlas data for shaped glyphs |
| VERTS | [MakeCustomVerts](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/SlateCore/Rendering/FSlateDrawElement/MakeCustomVerts?application_version=4.27) | Custom geometry carrier candidate |
| LANGUAGE | [GetCurrentLanguage](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/Core/Internationalization/FInternationalization/GetCurrentLanguage?application_version=4.27) | Localization language |
| CULTURE | [GetCurrentCulture](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/Core/Internationalization/FInternationalization/GetCurrentCulture?application_version=4.27) | Legacy equivalent; prefer language API |
| L10N | [Asset localization](https://dev.epicgames.com/documentation/unreal-engine/asset-localization?application_version=4.27) | Blueprint bytecode exclusion already established locally |

Version caution: some official pages reached with the 4.27 selector contain newer
types/overload lists (notably UWidget and FSlateVertex). Primitive roles support
the design; exact signatures, ABI, shaders and compilation need actual UE4.27
headers. Do not copy current-engine snippets as a verified 4.27 implementation.

Local primary evidence: `../proto_binary/`, Desktop `report_002.md`, the two WBP
JSON exports and `../ASSET_INSPECTION.md`. Public Proto tutorial remains
PUBLIC_REFERENCE_ONLY; no conclusion here equates it with shipped code.
