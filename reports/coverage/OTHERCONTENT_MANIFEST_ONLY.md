# The 30 OtherContent manifest-only identities (round 006)

Tool: `python -X utf8 tools/coverage/othercontent_trace.py --asset-registry <temporary copy of Dispatch/AssetRegistry.bin>`.
Per-record table: `othercontent_manifest_only.json` (namespace, key, source, manifest location, expected locres,
package, pak/registry presence, reason, runtime relevance, action).

## Result

All 30 are **SOURCE_ONLY**.

- Every record's manifest context is a widget under `/Game/Tools/CensorWidgets/` (7 packages: WBP_CensorImport,
  WBP_CensorImporter, WBP_CensorTabButton, WBP_CensorTestingWidget, WBP_CensorTrackEditor, WBP_TrackEditorTreeItem,
  WBP_TrackListItem) — the developer's censor-track authoring tool ("Censor Track Editor", "Select Premiere XML file to
  import", "Save Censor Asset").
- None of the 7 packages is in any of the 20 pak indexes (0 entries under `Dispatch/Content/Tools/`), and the shipped
  `AssetRegistry.bin` has no `/Game/Tools/` entry.
- The manifest was gathered from the source project; the locres was compiled for cooked content, so these editor-utility
  texts never reached the shipped resource. The exact cook-time filter is not identified, but the absence of the owning
  packages makes the text unloadable at runtime.

Expected locres: `Dispatch/Content/Localization/OtherContent/en/OtherContent.locres` (absent there, as in `ru`).
Runtime relevance: none. Action: no translation; not counted as translated. No integration needed.
