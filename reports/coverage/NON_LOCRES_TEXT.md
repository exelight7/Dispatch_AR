# Text outside the translated locres resources (round 006)

Machine-readable: `non_locres_text.json` (built by `python -X utf8 tools/coverage/build_coverage_reports.py`).
Supporting scan: `cooked_text_scan.json` (`python -X utf8 tools/coverage/cooked_text_scan.py <extracted copies>`).

## Method

- Pak path indexes (62,861 entries) for asset classes; no blind full extraction.
- **Targeted** temporary extraction (outside the project, deleted after the round) of 1,642 cooked `WBP_/DA_/DT_/ST_/BP_`
  packages, 851 Engine packages, 2,087 texture files and `AssetRegistry.bin`, read-only from the game paks.
- A cooked-FText scanner that recognises the two exact UE4.27 FText layouts (Base history with namespace/key/source, and
  `ETextFlag::CultureInvariant` with no history), and checks every localizable triple against the translated identities.
- UAssetAPI exports of five string tables; config `NSLOCTEXT`/`LOCTABLE` parsing.

## Findings

| Class | Records | Source |
|---|---:|---|
| LOCALIZED_ALREADY | 40 tables | String tables — every entry is a locres identity (5 tables verified entry by entry) |
| LOCALIZED_ALREADY | 783 | Localizable FText in cooked UI/data packages (783 of 801 triples) |
| EDITOR_ONLY | 18 | Localizable FText with no locres identity: all in `DebugTools/` or `Sandbox/` widgets |
| EDITOR_ONLY | 69 | Culture-invariant FText in debug/sandbox widgets |
| TECHNICAL_NOT_USER_VISIBLE | 80 | Culture-invariant designer placeholders (`Sample ^Text^`, `Button Text`, `XX%`, `[Consent Text]` …) and symbols |
| **UNKNOWN** | **91** | Culture-invariant FText in shipping widgets with real-looking labels (`LEGAL NAME:`, `SUBSCRIBER REVIEW`, `CHOOSE ONE POWER TO LEARN`, `< Previous Audio Log >`, `CALLER:` …). **Cannot be localized through locres**; visible only if not overwritten at runtime; the same English shows in all 16 shipped cultures |
| LOCALIZED_ALREADY | 13 | `DefaultGame.ini` commentary-speaker `NSLOCTEXT` titles (package namespace `[/Script/Dispatch]` is stripped in locres) |
| RETAINED_PROPER_NAME | 35 | Real cast/crew names in the same section (no locres identity in any shipped culture); policy: keep Latin spelling |
| LOCALIZED_ALREADY | 35 | `LOCTABLE` config references (ST_CommentarySpeakerTitles, ST_InputBindingPresets) |
| LOCALIZED_ALREADY | 2 | `BaseEngine.ini [Core.System]` corrupt-data dialog (added to the Engine scope this round) |
| EDITOR_ONLY | 20 | LOD-group / buffer-visualization / Niagara quality names in engine ini |
| TECHNICAL_NOT_USER_VISIBLE | 16 | Profanity-filter DataTables (16 languages, **no Arabic list** — functional gap, see ARABIC_CULTURE R8) |
| TECHNICAL_NOT_USER_VISIBLE | 9 | Rich-text style DataTables (fonts/styles only) |
| EDITOR_ONLY | 63 | `.uplugin` descriptors |
| TECHNICAL_NOT_USER_VISIBLE | 47 | `.playstats` choice-statistics data (displayed sentences are translated ChoiceStat records) |
| TECHNICAL_NOT_USER_VISIBLE | 3,463 | ICU data (incl. `ar.res`) |
| LOCALIZED_ALREADY | 46 | Online plugin messages |
| UNKNOWN | 15 | Credits are videos — see `VIDEO_LOCALIZATION.md` |
| UNKNOWN | 2 | Licenses / Terms of Service body: placeholder text only; the real text is supplied at runtime |

`RETAINED_PROPER_NAME` extends the requested five classes; it is a policy decision, not a gap.

## Hard-coded C++ text

Native settings/UI strings of the Dispatch module that are `LOCTEXT` are in the Shared manifest (contexts such as
`Source/Dispatch/Private/DispatchCloudSettings.cpp:326`) and are translated. Culture names come from ICU. FString text
built in native code without FText cannot be enumerated statically beyond the EXE string inventory; none surfaced in the
reviewed UI.

## Conclusion

No runtime text that **can** be localized through resources is missing from the Arabic locres. The open items are the
91 culture-invariant labels (need in-game observation; a fix needs a WBP edit) and video/licence content.
