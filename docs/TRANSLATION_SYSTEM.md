# Translation system

Canonical records come from the installed English **locres**, rather than assuming archive/manifest companions are current. OtherContent's archive has 80 keys but its runtime resource has 50; episode 108 has 2,116 runtime keys and 2,113 manifest keys. The three extra runtime keys remain included with unconfirmed context.

Each source record retains `id`, target, namespace, key, source CRC/hash, source file, context paths, inferred speaker, category and the exact runtime English text. An identity is `target:namespace:key`; dialogue records are never deduplicated by English wording.

`translation/arabic/<target>.json` maps stable numeric source indexes to Arabic. `scripts/validate_translation.py` merges these into `translation/records/` and generates MASTER_TRANSLATION.md with Arabic before English. It rejects missing/extra IDs, duplicate JSON keys, missing Arabic, changed placeholder/tag multisets, broken slice/caret/newline counts and Unicode corruption. It also reports untranslated natural-language candidates. Generic reverse-Arabic detection cannot be proved from codepoints alone; no such guarantee is claimed.

Status vocabulary: TODO -> TRANSLATED -> REVIEWED -> TESTED -> FINAL. Current authoring does not establish the latter three stages. Legitimate preserved technical identifiers/brands/numbers are documented, rather than silently used as English fallback for missing translations.

The 460-key EngineRuntime subset covers explicit native system/input/accessibility candidates; it does not claim all 20,282 Engine strings are translated or reachable. Exact selected identities are versioned in `translation/engine_scope.json`. The 68 deliberately preserved physical key legends, platform brands and chord formats are recorded by identity, original text and reason in VERBATIM_APPROVALS.json. These approvals only classify unchanged wording; they never bypass markup, placeholder or Unicode validation.

A post-merge name pass reconciled 61 records for Galen, Lightningstruck, Willem and the Vanderstenk/fan-club forms. Exact before/after values are in `reports/NAMING_RECONCILIATION.json`. These broaden the earlier bounded core-name audit; no comprehensive literary review is claimed. The specific 401(k) plan reference in106:427 was restored after numeric-content diagnostics.

Glossary: GLOSSARY.json; style: STYLE_GUIDE.md. Keep original `|` subtitle slicing, caret emphasis, formatting tags, parameters, URLs, email addresses, keyboard/controller identifiers and voice timing. Natural-language values inside Unreal plural/ordinal format modifiers may be localized while preserving their parameter identities and grammar keywords; actual native formatter behavior still requires runtime checking.

The five uppercase bracket occurrences in project resources were inspected: `[HIGH]`, two `[OVERRIDDEN]`, `[SCREEEEECH]`, `[SCREEEEEEECH]`. These are visible status/sound labels, not engine substitution variables; translating their contents is intentional. Unknown `[VAR]`-style tokens remain protected. See source contexts and validation selfchecks.

Full translation authoring continued after the user explicitly requested finishing localization while prohibiting game launches. This does not waive the original visual acceptance criteria or mark the RTL PoC passed.
