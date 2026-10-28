# Arabic Unicode safety (round 006)

Tool: `python -X utf8 tools/translation_qa/qa.py` → `unicode_safety.json`. Scope: all 12,973 records (12,487 Arabic).

| Forbidden / suspicious item | Code points | Count | Status |
|---|---|---:|---|
| Arabic Presentation Forms-A/B in text | U+FB50–FDFF, U+FE70–FEFC | **0** | PASS |
| RLO / LRO | U+202E / U+202D | **0** | PASS |
| RLE / LRE / PDF | U+202B / U+202A / U+202C | **0** | PASS |
| RLI / LRI / FSI / PDI | U+2067 / U+2066 / U+2068 / U+2069 | **0** | PASS |
| RLM / LRM / ALM | U+200F / U+200E / U+061C | **0** | PASS |
| ZWSP / ZWNJ / ZWJ / WJ / BOM | U+200B–200D, U+2060, U+FEFF | **0** | PASS |
| Manually reversed / visual-order Arabic | heuristic: rare word whose reverse is ≥20× more frequent | 2 candidates | Both explained (الطب "medicine", لوقت "for a time" are valid logical words) |
| NUL / U+FFFD / lone surrogates / control chars | — | 0 | PASS (validator) |

Explained items, not violations:

- **U+0640 tatweel in 99 records** — used deliberately for cut-off/stuttered speech (`لـ... لماذا`, `ما الـ--`) where
  English has `Wh-`/`the-`. It is a logical character; the shaper joins it. Now documented in `STYLE_GUIDE.md`.
- **178 records whose first strong character is Latin** (171 are engine VR/console key labels such as
  `Valve Index (يسار) ضغط A`, plus 7 decorative/copyright strings). With automatic paragraph direction these lines resolve
  LTR. 20 game-text cases were reworded this round to start with Arabic (no control characters inserted); the remaining key
  labels are left as brand-first labels (not used by Dispatch's PC prompts).

Logical Unicode remains authoritative: the translated data contains no shaping or ordering workaround.

**Result: 0 unexplained violations.**
