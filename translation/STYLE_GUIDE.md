# Arabic style guide

- Natural modern standard Arabic, concise enough for timed subtitles; maintain each speaker's sarcasm, emotion and level of profanity. Do not sanitize adult dialogue or add explanations.
- Keep logical Unicode order. Never reverse text or preconvert to Arabic presentation forms. The renderer must handle shaping and BiDi.
- Use GLOSSARY.json as the shared naming reference. Character and asset identifiers are never renamed.
- Preserve every placeholder, rich-text tag, escape, line break, and `|` slice separator. Translate each subtitle slice independently and keep the original slice order and count; timing remains original.
- Preserve the count and paired purpose of caret `^` emphasis markers. Keep keyboard/controller identifiers, URLs, email addresses, format specifiers and engine commands intact.
- Keep Western digits and abbreviations XP, HP and SDN. Do not insert directional controls into data to imitate a renderer fix.
- Infer speaker from the manifest context where available. Avoid inventing scene context or speaker gender; concise neutral wording is preferable where ambiguity remains.
- Do not merge dialogue records merely because their English text is identical.
- Machine checks establish structural validity, not literary review or in-game quality. TRANSLATED does not mean REVIEWED, TESTED or FINAL.
- The user has prohibited launching the game. No runtime/visual acceptance test may be marked passed without real evidence.

## Round 006 additions (from QA and review)

- Real-person names (cast/crew in commentary, credits) keep their original Latin spelling, as in all 16 shipped cultures.
- Cut-off or stuttered words (`Wh-`, `the-`) may use U+0640 tatweel after the cut letter (`لـ...`, `ما الـ--`); it is logical text, not a shaping trick.
- Prefer starting a line with an Arabic word when it would otherwise begin with a Latin brand/acronym (`إن SDN ليست…`, `شبكة SDN:`, `مفتاح Shift الأيسر`), so automatic paragraph direction resolves RTL. Never add directional control characters.
- ICU plural/ordinal arguments: give Arabic its CLDR categories where the English uses `plural(...)` (`zero, one, two, few, many, other`); English ordinal suffixes (`st/nd/rd/th`) must not appear in Arabic (use empty values).
- Sound/description tags in brackets use noun forms consistently (`[تجشؤ]`, `[تنهد]`, `[مقاومة]`), never a gendered verb.
- Do not sanitize profanity in choices or nicknames; use the project's standard forms (`تبًا`, `اللعنة`, `اللعين`) rather than colloquial `طز`.
- Button labels use the imperative (`العب`, `اشترك`); status words use the progressive (`جارٍ تحميل…`).
- Use `أفاتار` for the hacking avatar; `الرمز` is reserved for codes.
- Self-reference agrees with the speaker's gender, including the accusative after `لست`/`كنت`/`سأكون` (`لست بارعة`, `سأكون جاهزة`, `أنا ذاهبة`). Address agrees with the listener: Blazer → Robert is masculine (`أتظن`, `تريد`). Confirmed genders: Granny, Sweetalker and Andrew are male; Beefcake and Bug Lady are female. `qa.py` `speaker_gender_agreement` catches first-person cases. Its remaining warnings are second-person false positives.
- Status chips (`X: Y`) whose value is a bare past passive get a damma on the first letter (`قُتل`, `أُنقذ`, `فُقد`) or are rephrased (`تعرض للضرب`, `تحت الحراسة`), so they cannot be read as active verbs.
- The nickname Coop is `كوب`. The hero name Coupe/Coupé stays `كوبيه`.
- Unvocalised you/I collisions get an explicit pronoun (`كنت محقًا، وأنا كنت مخطئًا`).

## User language preference — 2026-10-28

Settings menus, their option labels/tooltips, and input-binding key names stay in original English by user request. Preserve the explicit per-record approvals in VERBATIM_APPROVALS.json. Dialogue/subtitles remain Arabic; this does not change the game culture or actual option values.
