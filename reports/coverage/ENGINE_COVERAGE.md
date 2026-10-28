# Engine.locres runtime-relevance audit (round 006)

Tool: `python -X utf8 tools/coverage/engine_audit.py --engine-assets <temporary copy of shipped Engine/** packages>`.
Outputs: `engine_classification.json` (one row per excluded record, with evidence flags) and
`engine_classification_summary.json` (per-namespace counts).

## Evidence model

UE4 `LOCTEXT`/`NSLOCTEXT` compile the source text, namespace and key as separate NUL-terminated UTF-16 literals. The
shipping EXE is monolithic, so a record whose key **and** source literals are absent from it is not produced by shipped
C++ code. The tool also checks `NSLOCTEXT`/`LOCTEXT` references in the shipped `.ini` files and searches the 851 shipped
`Engine/**` cooked packages for each key.

- "Distinctive" source: unique within Engine.locres and ≥24 characters or ≥3 words. A distinctive present source proves
  its namespace's code is compiled in; short/common sources only count inside such a namespace.
- Positive control: 445 of the 460 previously selected runtime records have key and source in the EXE (the 15 misses are
  platform-specific keys compiled out, e.g. 4 InputKeys and 2 GenericCommands tooltips).
- The 624 asset-gathered records (empty namespace, GUID keys: StandardMacros tooltips, sky-sphere sample text, material
  function descriptions) have **no** key in any shipped Engine package.

## Result for the 19,822 records outside the original scope

| Class | Records | Basis |
|---|---:|---|
| RUNTIME_CONFIRMED | 4 | `Audio:XAudio2Error`, `Audio:XAudio2Missing` (compiled, player-directed dialog); `SerializationOutOfBoundsErrorMessage(+Caption)` (BaseEngine.ini `[Core.System]` corrupt-data dialog). **Added** to `translation/engine_scope.json` and translated |
| RUNTIME_LIKELY | 21 | Compiled and player-addressed but trigger unverified: PluginManager failure dialogs (13), SlateD3DRenderer (2), CommonDateTimeTextBlock (2), CommonBoundActionButton (1, multi-player), Timespan formats (2), Internationalization memory format (1). **Not added** — documented |
| DEVELOPMENT_ONLY_CONFIRMED | 4,847 | 853 compiled but developer-facing (UnicodeBlock names for font tooling, Niagara/EQS/material documentation, Blueprint VM and Kismet-library warnings, descriptor validation, XR cvar help, console feedback); the rest not compiled and in developer/platform tooling namespaces |
| EDITOR_ONLY_CONFIRMED | 13,418 | Not compiled into the shipping EXE and owned by editor modules, or asset-gathered editor content text |
| UNUSED_OR_UNREACHABLE_CONFIRMED | 1,532 | Not compiled, not configured, not in shipped packages (platform plugins, unused features, crash reporter — no CrashReportClient ships) |
| UNKNOWN | 0 | |

"Confirmed" for the non-compiled classes rests on absence from the hash-locked shipping binary plus config/package
checks; for compiled developer text it rests on the text content and owning module. `RUNTIME_CONFIRMED` means compiled
into (or configured for) the shipping build and addressed to the player — actual display is still not runtime-tested.

## Scope change

`translation/engine_scope.json`: 460 → **464** identities. Existing 460 translations were remapped by identity (indexes
shift when rows are inserted); English, keys and source hashes are unchanged.

## Re-run after the scope change (end of round 006)

`python -X utf8 tools/coverage/engine_audit.py` was run again against the 464-identity scope (the temporary Engine package copies had been deleted, so this run used EXE plus ini evidence only):
19,818 records outside scope. DEVELOPMENT_ONLY_CONFIRMED 4,847, EDITOR_ONLY_CONFIRMED 13,418, RUNTIME_LIKELY 21, UNUSED_OR_UNREACHABLE_CONFIRMED 1,532, RUNTIME_CONFIRMED 0 (the 4 confirmed records are now inside the scope).
Positive control: 447 of 464. `reports/coverage/engine_classification*.json` now holds this re-run.
