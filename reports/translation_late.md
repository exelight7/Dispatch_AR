# Episode targets 107 and 108 — TRANSLATED, NOT TESTED

Completed 2026-10-23 from the canonical runtime records in `translation/source/107.json` and `108.json`, following STYLE_GUIDE.md and GLOSSARY.json. No game launch or external translation service. Outputs are UTF-8 JSON objects mapping numeric index strings directly to Arabic strings:

| Target | Records | Output SHA256 |
|---|---:|---|
| 107 | 684 / 684 | `417fcaf1cca21dd7102ee48e3228bfa4122510a36d3685a8fb747bc821a9f41d` |
| 108 | 2116 / 2116 | `af6cc37fc86c9f7227d4f7bed07cd6960d17bbc4a2d48420c1db8659222f61aa` |

All 2800 runtime indexes are present exactly once; no empty strings. Structural checks pass: placeholder/tag multisets, exact CRLF/LF sequences, subtitle `|` slice counts, caret counts and bullet counts. No replacement characters, Arabic presentation forms or added direction controls. Incremental batches were saved throughout. Terminal-corrupted bullet transcription was corrected against source Unicode, then revalidated.

Unchanged entries are intentional: 107 index12 is the technical `Disabled_Volta_Virtu` hacking token; 107 indexes13–30 are handles. In108, index0 and handle entries37–99 (excluding translated42) retain exact handles, while32–36 retain numerical age/height values. Hacking feedback108 indexes1 and42 was translated while retaining punctuation/underscore patterns. There is no natural-language English fallback or filler.

Consistent additional terms used: Red Ring = الحلقة الحمراء; Astral Pulse = النبضة النجمية; Proto Pulse = النبضة الأولية; Bone Zone = بون زون; Up-Chuck = أب تشاك; Thumbstick = ثمبستيك; Track Star = تراك ستار; Mindfucker = مايندفاكر; SmileMore = سمايل مور. The split objectives108:1907–1911 and1991–1995 were translated as components of “Give him/her everything you've got”; final assembled UI still needs review.

Source SHA256:107 `8c09d7d28fac1f93fdb1b08a78e25129898a4a7c529ae710c989de3c9f12d3d7`;108 `e727165b48d4342f076abdb99566caead335e1a67a69173f56d12c0bda47df82`.

Status is TRANSLATED. These checks do not establish literary review, subtitle timing fit, font/RTL behavior or runtime success. Shared subtitle renderer limitations remain documented in `reports/rtl_research/ASSET_INSPECTION.md`; the detached layout prototype is excluded from distributables.
