# Arabic culture activation — static investigation (round 006)

Result: **ARABIC_SELECTION_STATIC_REQUIREMENTS_IDENTIFIED** — Arabic cannot be added to the in-game
language menu without an EXE change; a menu-independent route (launch culture + locmeta) is defined
but **RUNTIME_NOT_PROVEN**. Nothing was installed or run.

Evidence labels: CONFIRMED_FROM_ASSET (shipped data read from extracted copies), CONFIRMED_FROM_BINARY
(hash-locked EXE `365637a7…4923`, string/data presence only), ENGINE_SOURCE_RECALL (UE4.27 behaviour
from knowledge, not checked against 4.27 source), DESIGN_INFERENCE, NOT_PROVEN.

## 1. Facts

| # | Fact | Evidence | Label |
|---|---|---|---|
| F1 | The game ships **17 cultures**, not only `en`: `de, en, es, es-419, fr, it, ja, ko, LEET, pl, pt-BR, ru, th, tr, uk, zh-Hans, zh-Hant` for Shared and 101–108; OtherContent has `en, ru` | `CompiledCultures` in the extracted `*.locmeta`; locres culture folders in the 20 pak indexes | CONFIRMED_FROM_ASSET |
| F2 | `DefaultGame.ini` still says `-CulturesToStage=en` / `+CulturesToStage=en` | the shipped config; F1 shows the build overrode it | CONFIRMED_FROM_ASSET — the config line is **not** authoritative |
| F3 | `InternationalizationPreset=All`; ICU `icudt64l/ar.res` and 25+ `ar_*.res` are shipped | pak index | CONFIRMED_FROM_ASSET |
| F4 | The settings code holds a literal culture list `system, de, es, es-419, fr, it, ja, ko, pt-BR, ru, uk, th, tr, pl, zh-Hans, zh-Hant` (UTF-16, contiguous at 0x32e5090, followed by `ST_InputBindingPresets` and `SettingCategoryGeneral`); `en` is pooled elsewhere; **no `ar`**; `LEET` absent | EXE bytes | CONFIRMED_FROM_BINARY (data); that it is the Language option list is DESIGN_INFERENCE (strong: order, `system`, adjacency to settings literals, `LEET` excluded) |
| F5 | The Language setting is native: `Shared:DispatchSettings:Language` comes from `Source/Dispatch/Private/DispatchCloudSettings.cpp:326`; class `UDispatchLanguageSetting` with `OnLanguageSettingValueChanged` | manifest context; EXE names (round 004) | CONFIRMED_FROM_ASSET / BINARY |
| F6 | No culture display names exist in any locres (no "Deutsch", "日本語" …) | full source scan | CONFIRMED_FROM_ASSET — names come from ICU native names at runtime (DESIGN_INFERENCE) |
| F7 | Command-line culture switches are compiled in: `CULTURE=`, `LANGUAGE=`, `CULTUREFORCOOKING=` | EXE wide strings | CONFIRMED_FROM_BINARY |
| F8 | `%s.locmeta` is compiled in (the engine reads `<Target>.locmeta`) | EXE wide strings | CONFIRMED_FROM_BINARY |
| F9 | `[Internationalization] LocalizationPaths` lists the 10 game targets (+ NewTarget, PluginSourceCode which ship no files) | DefaultGame.ini | CONFIRMED_FROM_ASSET |
| F10 | RTL layout cvars are compiled in: `Slate.EnableLayoutLocalization`, `Slate.ShouldFollowCultureByDefault` | EXE wide strings | CONFIRMED_FROM_BINARY |
| F11 | No `EnabledCultures` / `DisabledCultures` / `CultureMappings` entries in the shipped game configs | grep of extracted ini | CONFIRMED_FROM_ASSET (the keys exist in the EXE) |
| F12 | Per-language profanity DataTables exist for 16 languages; none for Arabic | pak index | CONFIRMED_FROM_ASSET |
| F13 | The game ships localized packages only under `/Game/L10N/en/FMOD` (7 VO events) | pak index; AssetRegistry.bin | CONFIRMED_FROM_ASSET |

## 2. What must change to make Arabic selectable

| Requirement | Category | Status |
|---|---|---|
| R1 Arabic entry in the in-game Language menu | **EXE change** (literal list in native code, F4) | BLOCKED — forbidden by project constraints; only the developer can add it |
| R2 Arabic text resources at `Localization/<target>/ar/<target>.locres` for every target | LOCALIZATION_RESOURCE_CHANGE | DONE (experimental PAK, 14 resources) — load at runtime NOT_PROVEN |
| R3 `ar` in the locmeta `CompiledCultures` of the game targets | LOCALIZATION_RESOURCE_CHANGE (original-path override of 10 small `.locmeta` files in a `_P` pak; only adds one list entry) | PROTOTYPE BUILT, not packed/installed (`prototype/`). Needed if the engine validates the requested culture against the available-culture list (ENGINE_SOURCE_RECALL: 4.2x falls back to the native/default culture when the requested culture has no localization data) |
| R4 Requesting the culture without the menu | CULTURE_CONFIG_CHANGE (user side) | Options: launch option `-culture=ar` (Steam launch options), or user `GameUserSettings.ini` `[Internationalization] Culture=ar` (ENGINE_SOURCE_RECALL). RUNTIME_NOT_PROVEN |
| R5 The game's own Language setting must not override R4 | RUNTIME_NOT_PROVEN | The saved value `system` presumably leaves the engine culture alone; a saved explicit language (e.g. `de`) probably re-applies that culture. Requires runtime observation |
| R6 RTL widget flow at window level | CULTURE_CONFIG_CHANGE (optional, user-side `[ConsoleVariables] Slate.ShouldFollowCultureByDefault=1`) | NOT_PROVEN; text paragraphs already resolve RTL from content (Auto flow), and 4.27 flips Left/Right justification for RTL lines (ENGINE_SOURCE_RECALL; `InvariantLeft` absent from the EXE confirms the 4.27 enum) |
| R7 Arabic subtitles in ProtoAnimatedText reveal | BLUEPRINT_CHANGE + COOK_REQUIRED | See renderer_repair (G1–G5); unchanged by this round |
| R8 Arabic profanity filter list | COOK_REQUIRED (new DataTable) + BLUEPRINT_CHANGE (routing) | Optional; not part of minimum activation |
| R9 Culture display name in any menu | none | ICU provides `العربية`; only relevant if R1 ever happens |

Minimum mod-side activation set: **R2 + R3 + R4**, with R5 observed at runtime.

## 3. Fallback behaviour (static)

- Prioritized cultures for `ar`: `ar` then the native culture `en` (ICU parent of `ar` is root). A key missing from the
  ar locres shows its English source. All game targets are fully covered; the Engine target is a sparse 464-row subset by
  design, so unselected engine text shows English (classified non-runtime in `reports/coverage/engine_classification.json`).
- `ar-SA` (an OS locale) would prioritize `ar-SA`, then `ar`, then `en`; our `ar` resources therefore also serve `ar-SA`
  (ENGINE_SOURCE_RECALL).

## 4. Detached prototype (not installed)

`reports/arabic_activation/prototype/Dispatch/Content/Localization/*/*.locmeta` — 10 files, generated by
`python -X utf8 tools/arabic_activation/locmeta.py prototype`. Self-test: byte round-trip of all 11 extracted locmeta
files; `ar` inserted once in case-insensitive order; native culture and native locres unchanged. Hashes in
`prototype/locmeta_prototype.json`. Not added to the experimental package (supervisor decision: it replaces original-path
files, although only the list grows).

## 5. Remaining runtime questions

Whether `-culture=ar` is honoured with/without R3; whether the saved Language setting overrides it; whether
`FText` lookups pick up the ar locres for every target; RTL paragraph/justification in actual widgets. All need the game.
