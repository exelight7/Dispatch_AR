# Automated translation QA (round 006)

Tool: `python -X utf8 tools/translation_qa/qa.py` → `translation_qa.json` (every finding with record id, check,
severity, detail). These are machine checks; they are not literary review.

Checks per record: structural validator (tags, placeholders, `|`, `^`, CR/LF/tab/backslash, URLs, e-mails, Unicode
corruption, presentation forms, directional controls), verbatim natural language (respecting VERBATIM_APPROVALS),
English source embedded in Arabic, Latin tokens absent from the source, English phrase leakage, no Arabic letters,
number multisets, Arabic-Indic digits, bracket/quote balance, Latin `? , ;` after Arabic, space before punctuation,
missing space after `،`, duplicated punctuation, double/edge spaces, repeated words, tatweel, English function words,
transliterated brand, leading Latin strong character, bidi/zero-width controls, reversed-word heuristic, glossary terms
(longest match first, clitic-tolerant).

## Result after this round's fixes

| Check | Count | Disposition |
|---|---:|---|
| ERROR (any) | **0** | — |
| leading_latin_base_direction | 178 | 171 engine VR/console key labels (brand first), 7 decorative strings; 20 game strings reworded |
| latin_token_not_in_source | 106 | `Z` of `Z-Team` → `فريق Z` (glossary), `A-Teams` → `فرق A`, key letters (X/Y axes), `URL`, `Ctrl`, `Esc`, `DDE` — all intended |
| tatweel | 99 | Intentional cut-off/stutter rendering (now in STYLE_GUIDE) |
| repeated_word | 27 | Mirror English repetitions (`Okay okay okay`, `Ding ding!`, `Here kitty, kitty`) |
| glossary_term_missing | 26 | Common-noun uses (Chase as verb, Security, Prime, Braindead state), possessive/plural Astral Pulse forms, a company name, and 5 documented glossary ambiguities (see `translation/review/GLOSSARY_AUDIT.md`) |
| number_mismatch | 19 | Spelled-out numbers vs digits with the same value (`eighty six` → `86`, `1 second` → `ثانية واحدة`) |
| english_phrase_leakage | 6 | Consent texts keep the e-mail subject `Delete My Personal Information` that support expects verbatim |
| space_before_punctuation | 3 | `Memory Test   :` terminal art and placeholders before `؟` |
| missing_space_after_comma | 2 | `،{Time}` dev log lines — follow English |
| possibly_reversed_word | 2 | Valid words (see Unicode report) |
| latin_punctuation_after_arabic | 1 | ICU plural argument syntax `one=…, other=…` |

Fixed by QA this round (logged in `translation/review/changes.json`): 37 glossary-name/speaker-label consistency fixes,
20 base-direction rewordings, 2 plural/ordinal format fixes (English `st/nd/rd/th` suffixes removed from Arabic; Arabic
CLDR plural categories added for minutes), and one Astral Pulse variant.
