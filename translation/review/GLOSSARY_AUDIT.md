# Glossary consistency audit (round 006)

Method: every Capitalized glossary term was searched (longest match first) in every English source and the expected
Arabic in the same record; variant spellings were counted corpus-wide (`tools/translation_qa/qa.py`, check
`glossary_term_missing`). The glossary is authoritative; fixes were applied only where it is unambiguous.

## Fixed (glossary authoritative) — 37 records

| Term | Variant found → glossary form | Records |
|---|---|---:|
| Terrence | تيرينس → تيرنس | 9 |
| Charles Kingsley | كينغزلي → كينغسلي | 2 |
| Hunter / Brian / Kiera / Jordan | هنتر / براين / كييرا / جوردن → هانتر / برايان / كيرا / جوردان | 4 |
| Equilibrium (hero) | التوازن → إيكويليبريوم | 3 |
| Reporter A–E | مراسل A…E → المراسل أ/ب/ج/د/هـ | 5 |
| On Scene Reporter, Nurse, Officer, Waitress, News Anchor | article-less labels → glossary labels | 9 |
| Green/Orange/Red Ski | المقنع بالأخضر… → ذو قناع التزلج الأخضر… | 3 |
| Darts Guy / Other Darts Guy | لاعب سهام… → رجل السهام… | 2 |

Review also unified `Astral Pulse` (نبضة أسترال → النبضة النجمية, 6 records) and `avatar` in the hacking tutorial
(رمز → أفاتار, 6 records; رمز is the word for the node *code* in the same screens).

## Added to the glossary (formalizing existing consistent usage)

`Astral Pulse → النبضة النجمية`, `Proto Pulse → النبضة الأولية`, `avatar (hacking) → أفاتار`,
`The Sardine (bar) → حانة السردين`.

## Ambiguities documented, not changed

| Term | Glossary | Corpus | Why not changed |
|---|---|---|---|
| Soothing Goon / Soothing Voice | هادئ (calm) | مهدئ (soothing) in two speaker labels | The corpus form is the more accurate meaning; needs a glossary owner decision |
| Curator | القيّم | أمين المتحف in one label | Both acceptable; أمين المتحف is clearer — owner decision |
| Bouncer | حارس الباب | حارس الملهى in one label | Context-dependent |
| Chief | الرئيس | القائد مارشال (Chief Marshall) | Title compound, not the bare speaker label |
| Police Officer | (none) | شرطي (103) / ضابط شرطة (108) | Not in glossary; possibly different characters |
| Chase / Security / Prime | names | verbs/common nouns in other records | Same English word, different meaning |

No transliteration drift, character renaming or brand corruption remains for the other glossary names; `Dispatch`,
`SDN`, `XP`, `HP` stay Latin as specified.
