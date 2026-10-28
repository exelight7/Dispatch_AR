# Translation middle: targets 104, 105, 106

Status: **TRANSLATED**. Not REVIEWED, TESTED, or FINAL.

## Coverage

| Target | Source records | Arabic records |
| --- | ---: | ---: |
| 104 | 1722 | 1722 |
| 105 | 1098 | 1098 |
| 106 | 865 | 865 |
| Total | 3685 | 3685 |

All natural-language entries translated individually, including repeated dialogue records. Character names follow translation/GLOSSARY.json. Modern standard Arabic in logical Unicode order; no shaping, reversal or bidi controls introduced. No external translation service/API used.

## Legitimate unchanged KEEP entries

- 104 indexes 27–29: numeric age/height values (`24`, `6'4`, `6'4`).
- 104 indexes 30–64: exact social/account handles, including repeated `@SDN-T` handles.
- 105 index 28: `:DROWSSAP`, intentionally reversed source hacking/password interface token. Preserved as provided; no reversal was applied by translation.
- 105 indexes 29–59: exact social/account handles.
- 106 index 18 and indexes 21–39: exact social/account handles.
- Embedded `SDN`, `XP`, `HP`, `Z`, `UCT`, Western digits, account handles and source markup/placeholders retain their technical spelling wherever present. These are not English dialogue fallbacks.

## Adaptation notes

- 104 film/game titles are rendered consistently: `Standing Alive` → `صامد حي`; `Staying Alive` → `البقاء حيا`; `The Wolves Inside Us` → `الذئاب التي فينا`; `The Wolf Within Us` → `الذئب الذي فينا`; `The Wolves Have Eyes` → `للذئاب عيون`. Incorrect puzzle choices remain distinct.
- 104 `jizzed`/`jazzed` slip becomes a conspicuously inappropriate `مقذوف من الفرح`, corrected to `مبتهج`; retains embarrassment rather than adding an explanation.
- 106 `boobstraps`/`bootstraps` joke becomes `أربطة نهديك`/`أربطة حذائك`, with the later correction retained.
- Astral Pulse → `نبضة أسترال`; Proto Pulse → `النبضة الأولية`; Mole People → `أناس الخلد`; Red Ring → `الحلقة الحمراء` within these targets.
- Source typos and malformed natural wording were translated by intended meaning, while exact rich-text tags, placeholders, literal newlines, subtitle slice counts, and caret counts remain intact.

## Validation

Reproducible command: `python -X utf8 tools/translation_middle/validate.py`.

Checks: exact complete numeric index set; duplicate JSON-key rejection; nonempty string values; preserved rich-text tag and brace-placeholder multisets; identical counts of carets, pipe slice separators, CR and LF; no bidi-control or Arabic presentation-form code points.

No structural mismatches found in 3685 records. Only the owned Arabic JSONs, this report and helpers in tools/translation_middle were written. The game was not launched. Runtime/visual acceptance remains untested, as required by the user.
