# Early targets — TRANSLATED

Completed Arabic authoring for all 4,243 source records. Each index is stored separately; dialogue was not deduplicated. Outputs are UTF-8 JSON objects mapping source index strings to Arabic strings.

| Target | Output | Records | Arabic translations | Legitimate KEEP |
|---|---|---:|---:|---:|
| 101 | translation/arabic/101.json | 797 | 787 | 10 |
| 102 | translation/arabic/102.json | 2,192 | 2,177 | 15 |
| 103 | translation/arabic/103.json | 1,254 | 1,221 | 33 |
| Total | | 4,243 | 4,185 | 58 |

## KEEP decisions

- 101 indexes 4–12: exact @ account handles, identifying senders in the interface.
- 101 index 110: `Svg`, a technical speaker/asset label; parent explicitly confirmed this KEEP.
- 102 indexes 19–33: exact @ account handles.
- 103 indexes 27–31: numeric values 10, 10, 25, 50, 85.
- 103 indexes 32–59: exact @ account handles.
- Within translated sentences: preserve SDN, XP, HP, Z, VAND-CO, VAND-GO, CIA, UCT, 401K, source placeholders and ordinal-format syntax. These are identifiers, mandated abbreviations, brand labels or formatting expressions rather than untranslated natural-language fallback.
- Source 103:175 `N/A` was translated to `غير متاح` per parent validation guidance.

## Naming and wordplay decisions

- Canonical glossary names were followed; Bone Zone was aligned to بون زون after the glossary update.
- New encountered names: Granny → غراني (male bakery owner; distinct from generic grandmother); Willem Vanderstenk → ويلم فاندستنكر; Vanderstenker fan club → فاندستنكرز; Galen → غايلن; Lightningstruck → لايتنينغسترك; YouTopia → يوتوبيا; Victor Vazlav → فيكتور فازلاف.
- Nickname variants remain contextual: Coupé → كوبيه, casual Coop → كوب; Invisigal → إنفيزيغال, nickname Visi → فيزي; villain-era Invisibitch → إنفيزيوغدة.
- Phenomamal character mispronunciation/catchphrase adapted as فينومامذهل, joining the character name and “amazing.”
- Fight-Men → رجلا القتال; Duelist and Brawler → المبارز والملاكم; Saber and the Bruiser → سيف وكاسر; Fighterman/Manfighter → فايترمان/مانفايتر. The intentionally clumsy final pair remains transliterated to preserve the naming joke.
- Dr. Don’t Do Shit → الدكتور لا يفعل شيئا; Mr. Wet Ponytail → السيد ذيل الحصان المبلل; Sunglasses at Night Guy → رجل النظارة الشمسية ليلا. Dialogue and choice/result labels share these names.
- Thundercuck → ديوث الرعد; comic lightning/bangle insults translated contextually.
- “Rock/rock” advertisement adapted with صخرة / نجم روك; “wing it/fly” retains the bird/flight cue in the dialogue; punchline and subtitle slice order remain original.

## Structural checks

All source indexes are present exactly once in each JSON object. Local checks compared caret counts, pipe slice separator counts, literal newline sequences, rich-text tag multisets and brace placeholder multisets against source; no differences remained. Literal backslash counts and absence of inserted BiDi controls were also checked. Source 103:23's four backslashes were restored after the first escape-count check identified the mismatch. Parent independently validates and compiles the final locres.

Status is TRANSLATED only. No literary review or in-game acceptance is claimed. The game was never launched. No game files, original source records or other target shards were modified by this translation worker.
