# `Content/L10N/ar` and the AssetRegistry — static classification (round 006)

Result per asset type below. No asset was added, cooked or installed.

## Evidence

| # | Fact | Label |
|---|---|---|
| E1 | The game ships localized packages only at `/Game/L10N/en/FMOD/Events/Ep104/VO/...` (7 events, 14 files); no other culture uses asset localization — the 16 other languages rely on locres and composite-font fallback | CONFIRMED_FROM_ASSET (pak index) |
| E2 | The cooked `Dispatch/AssetRegistry.bin` (11.8 MB, pakchunk0) lists those `/Game/L10N/en/...` packages (15 `L10N` occurrences, the full package path twice) | CONFIRMED_FROM_ASSET (temporary copy, not kept) |
| E3 | The same registry has no `/Game/Tools/` entries, matching the 30 manifest-only OtherContent rows whose widgets were never cooked | CONFIRMED_FROM_ASSET |
| E4 | UE4.27's default package-localization cache discovers `L10N/<culture>` packages by querying the AssetRegistry for the localized root, then redirects package loads by prioritized culture | ENGINE_SOURCE_RECALL |
| E5 | The UE4.27 asset-localization documentation excludes bytecode assets (Blueprints) | Official doc (already in `rtl_research/SOURCES.md`) |
| E6 | Cooked packages are unversioned, LicenseeUE=0; event-driven loader | CONFIRMED_FROM_ASSET (round 004) |

Consequence: a package added by a mod under `/Game/L10N/ar/...` is **not** in the shipped AssetRegistry state, so the
localization cache would not know it exists. Mod-side options are (a) replacing `Dispatch/AssetRegistry.bin` through a
`_P` pak with a regenerated registry that contains every original entry plus the ar entries (needs an exact cook of the
registry; replaces an 11.8 MB original-path file used for all cultures), or (b) a content plugin whose own
AssetRegistry is appended on mount (NOT_PROVEN for this monolithic build; round 004 found plugin discovery is content-only).

## Questions asked by the supervisor

1. **DataTable localized override discovery** — through E4 only: L10N_OVERRIDE_REQUIRES_ASSETREGISTRY.
2. **Hard object imports** — redirection is applied when the package name is resolved for load, including imports
   (ENGINE_SOURCE_RECALL, NOT_PROVEN in this build). It still depends on the cache from (1).
3. **AssetRegistry dependency** — yes (E2, E4).
4. **Mod-added localized asset discovery** — not by default (E1–E4); needs option (a) or (b).
5. **Culture redirect behaviour** — prioritized cultures `ar` → `en`; with no ar package the original asset loads.
   An English `L10N/en` package would be chosen only for `en` (ENGINE_SOURCE_RECALL).

## Classification

| Asset type | Classification | Note |
|---|---|---|
| DataTable | L10N_OVERRIDE_REQUIRES_ASSETREGISTRY | Plain data; would allow an Arabic-only style table (e.g. DT_SubtitlesProtoRichText with an Arabic font) once discovery is solved |
| Font (FontFace / .ufont) | L10N_OVERRIDE_REQUIRES_ASSETREGISTRY | Same |
| CompositeFont (UFont) | L10N_OVERRIDE_REQUIRES_ASSETREGISTRY | Same; an Arabic sub-typeface could instead be added to the original Montserrat-Variable (affects all cultures only for U+0600–06FF ranges) — COOK_REQUIRED |
| Material / MaterialInstance | L10N_OVERRIDE_REQUIRES_ASSETREGISTRY | Plus shader delivery (gate G4) |
| Texture | L10N_OVERRIDE_REQUIRES_ASSETREGISTRY | Relevant to the 13 small runtime NEEDS_ARABIC images |
| Blueprint | L10N_OVERRIDE_UNSUPPORTED | E5; Arabic branch must be authored inside the original asset (renderer_repair) |
| WidgetBlueprint | L10N_OVERRIDE_UNSUPPORTED | E5; same |
| StringTable | L10N_OVERRIDE_UNSUPPORTED (not needed) | Entries are localized through locres namespaces (verified, `reports/coverage/NON_LOCRES_TEXT.md`) |

None of these is `L10N_OVERRIDE_SUPPORTED` for a mod without the registry change. All remain NOT_PROVEN at runtime.
