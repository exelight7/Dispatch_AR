# Primary-source register

Checked 2026-10-23. This register establishes engine capabilities and text rules, not Dispatch behavior. UE 4.27 is the research baseline pending the coordinator's exact build identification. Current Unicode/HarfBuzz manuals are conceptual references; their current versions must not be assumed to match libraries compiled into the game.

| ID | Source | Evidence used |
|---|---|---|
| UE-SHAPE | [TextShapingMethod, UE 4.27](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/TextShapingMethod.html?application_version=4.27) | FullShaping supports Arabic; KerningOnly does not; Auto chooses by text direction. |
| UE-FLOW | [TextFlowDirection, UE 4.27](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/TextFlowDirection?application_version=4.27) | Auto, LeftToRight, RightToLeft; this version documents no Culture member. |
| UE-OPTIONS | [ShapedTextOptions, UE 4.27](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/ShapedTextOptions.html?application_version=4.27) | Shaping and paragraph direction values have independent override switches. |
| UE-LAYOUT | [TextLayoutWidget, UE 4.27](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/TextLayoutWidget?application_version=4.27) | Justification, wrapping, margin, widget flow and shaped-text options are distinct properties. |
| UE-TEXT | [TextBlock, UE 4.27](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/TextBlock?application_version=4.27) | Simple text mode bypasses complex text layout. SetText removes the text binding. |
| UE-SLOT | [CanvasPanelSlot, UE 4.27](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/CanvasPanelSlot?application_version=4.27) | Anchors, alignment, offsets, size and auto-size govern the widget slot. |
| UE-FONT | [Font Asset and Editor, UE 4.27](https://dev.epicgames.com/documentation/unreal-engine/font-asset-and-editor?application_version=4.27) | Runtime composite fonts, FontFace data and range-based sub-fonts. |
| UE-I18N | [Localization Overview, UE 4.27](https://dev.epicgames.com/documentation/unreal-engine/localization-overview?application_version=4.27) | ICU handles culture/boundary/BiDi facilities; packaged internationalization data can be restricted. |
| UE-COOKED | [Working with Cooked Content, UE 4.27](https://dev.epicgames.com/documentation/en-us/unreal-engine/working-with-cooked-content-in-the-editor?application_version=4.27) | Cooked assets are read-only in the normal editor workflow; Blueprint limitations and split asset files apply. |
| UE-PYTHON | [Scripting the Editor using Python, UE 4.27](https://dev.epicgames.com/documentation/en-us/unreal-engine/scripting-the-editor-using-python?application_version=4.27) | Python scripting is editor-only, unavailable as gameplay scripting in cooked executables. |
| UAX9 | [Unicode Bidirectional Algorithm](https://www.unicode.org/reports/tr9/) | Logical storage order, mixed-direction resolution, contextual shaping and shaped-width line breaking. |
| UAX29 | [Unicode Text Segmentation](https://www.unicode.org/reports/tr29/) | Extended grapheme boundaries prevent splitting user-perceived characters; distinct from line breaking. |
| HB-SHAPE | [What is HarfBuzz?](https://harfbuzz.github.io/what-is-harfbuzz.html) | Glyph selection/position depends on text, font, script and language; OpenType shaping uses GSUB/GPOS features. |
| HB-CLUSTERS | [Clusters](https://harfbuzz.github.io/clusters.html) | Graphemes and shaping clusters are different; ligatures may merge several graphemes. |
| HB-MAPPING | [Working with HarfBuzz clusters](https://harfbuzz.github.io/working-with-harfbuzz-clusters.html) | Cluster values map source input to output glyph groups; RTL output reverses monotonic ordering. |

The .html aliases above successfully returned the pinned 4.27 pages when their extensionless counterparts intermittently failed. Newer Epic API pages were deliberately excluded as proof of 4.27 enum layout.
