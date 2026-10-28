"""Automated QA over every Arabic record: structure, punctuation, tokens, numbers, glossary, Unicode safety.

python -X utf8 tools/translation_qa/qa.py
Writes reports/validation/translation_qa.json and reports/validation/unicode_safety.json.
Findings are machine checks, not literary review; severity ERROR blocks a build, WARN needs a human look.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path
import re
import sys
import unicodedata

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_translation import PLACEHOLDERS, TAGS, URLS, EMAILS, issues, is_technical  # noqa: E402

AR = "ء-يٮ-ۓ"
ARABIC_LETTER = re.compile(f"[{AR}]")
LATIN_WORD = re.compile(r"[A-Za-z][A-Za-z'’\-]*[A-Za-z]|[A-Za-z]")
BIDI = {"‪": "LRE", "‫": "RLE", "‬": "PDF", "‭": "LRO", "‮": "RLO",
        "⁦": "LRI", "⁧": "RLI", "⁨": "FSI", "⁩": "PDI", "‎": "LRM", "‏": "RLM",
        "؜": "ALM"}
APPROVED = json.loads((ROOT / "translation/VERBATIM_APPROVALS.json").read_text(encoding="utf-8"))
ZERO_WIDTH = {"​": "ZWSP", "‌": "ZWNJ", "‍": "ZWJ", "⁠": "WJ", "﻿": "BOM/ZWNBSP"}


FEMALE_SPEAKERS = {"Blonde Blazer", "Blazer", "Invisigal", "Prism", "Coupe", "Coupé", "Malevola", "Mandy", "Waitress",
                   "Nurse", "Rebecca", "Gena", "Tina", "Karen", "Brenda", "Ronda", "Sylvia", "Edna", "Lillian", "Helena", "Hannah"}
MALE_SPEAKERS = {"Robert", "Mecha Man", "Chase", "Flambae", "Sonar", "Golem", "Punch-Up", "Punch Up", "Phenomaman", "Waterboy",
                 "Shroud", "Royd", "Toxic", "Galen"}
SELF_ADJ = ["آسف", "متأكد", "سعيد", "واثق", "مستعد", "متعب", "ممتن", "مشغول", "خائف", "قلق", "غاضب", "فخور", "جاد", "مخطئ", "محق",
            "قادم", "قادر", "بارع", "نادم", "جاهز", "دقيق", "حزين", "مكتئب", "يائس", "متفاجئ", "مسيطر", "ذاهب", "مهتم", "مشغول", "منبهر", "مدين", "موافق", "محبط", "منسحب", "راحل", "مصدوم"]
SELF = r"(?:(?:أنا|إنني|أنني|لأني|لأنني|كنت|لست|سأكون|أكون|نفسي)\s+|(?:^|\|)\W*|(?:آه|أوه|تبا|حسنا|مهلا)[،.]?\s+)"


def load_records():
    rows = []
    for src in sorted((ROOT / "translation/source").glob("*.json")):
        ar = json.loads((ROOT / "translation/arabic" / src.name).read_text(encoding="utf-8"))
        for row in json.loads(src.read_text(encoding="utf-8")):
            rows.append({**row, "ar": ar[str(row["index"])]})
    return rows


def strip_markup(text):
    return PLACEHOLDERS.sub(" ", URLS.sub(" ", EMAILS.sub(" ", TAGS.sub(" ", text))))


def first_strong(text):
    for ch in strip_markup(text):
        bidi = unicodedata.bidirectional(ch)
        if bidi in ("L", "R", "AL"):
            return bidi
    return None


def glossary():
    data = json.loads((ROOT / "translation/GLOSSARY.json").read_text(encoding="utf-8"))
    pairs = data.items() if isinstance(data, dict) else [(d["en"], d["ar"]) for d in data]
    return {en: ar for en, ar in pairs if isinstance(ar, str)}


def check(row, word_freq, terms):
    en, ar, out = row["en"], row["ar"], []

    def add(code, severity, detail=""):
        out.append({"check": code, "severity": severity, "detail": detail})

    for problem in issues(en, ar):
        add("structural", "ERROR", problem)
    if ar == en:
        if not is_technical(en, row["namespace"]) and not APPROVED.get(row["id"], {}).get("reason"):
            add("verbatim_natural_language", "WARN", "Arabic equals English; must be an approved verbatim keep")
        return out
    plain_en, plain_ar = strip_markup(en), strip_markup(ar)
    punct_ar = PLACEHOLDERS.sub("", TAGS.sub("", ar))  # tags removed without spacing, for punctuation checks
    if en.strip() and len(en) > 20 and en in ar:
        add("source_duplicated_in_arabic", "ERROR", "Full English source embedded in Arabic")
    en_words = {re.sub(r"['’]s$", "", w).lower() for w in LATIN_WORD.findall(plain_en)}
    ar_latin = [re.sub(r"['’]s$", "", w) for w in LATIN_WORD.findall(plain_ar)]
    foreign = [w for w in ar_latin if w.lower() not in en_words]
    if foreign:
        add("latin_token_not_in_source", "WARN", " ".join(sorted(set(foreign))[:8]))
    leak = re.findall(r"(?:[A-Za-z]{2,}[ ,.'’]+){3,}[A-Za-z]{2,}", plain_ar)
    if leak and ARABIC_LETTER.search(plain_ar):
        add("english_phrase_leakage", "WARN", leak[0][:80])
    if not ARABIC_LETTER.search(plain_ar) and re.search(r"[A-Za-z]{3,}", plain_en) and not is_technical(ar, row["namespace"]):
        add("no_arabic_letters", "WARN", "Translated text has no Arabic letters")
    if Counter(re.findall(r"\d+", plain_en)) != Counter(re.findall(r"\d+", plain_ar)):
        add("number_mismatch", "WARN", f"en={re.findall(r'[0-9]+', plain_en)} ar={re.findall(r'[0-9]+', plain_ar)}")
    if re.search("[٠-٩۰-۹]", ar):
        add("arabic_indic_digits", "WARN", "Style guide keeps Western digits")
    for open_, close in ["()", "[]", "«»", "“”"]:
        if ar.count(open_) != ar.count(close) and en.count(open_ if open_ != "«" else '"') >= 0:
            if (ar.count(open_) - ar.count(close)) != (en.count(open_) - en.count(close)):
                add("unbalanced_brackets_or_quotes", "WARN", open_ + close)
    if ar.count('"') % 2 and not en.count('"') % 2:
        add("unbalanced_brackets_or_quotes", "WARN", '"')
    if re.search(f"[{AR}]\\s*[?;]", plain_ar) or re.search(f"[{AR}],", plain_ar):
        add("latin_punctuation_after_arabic", "WARN", "Use ؟ ، ؛ after Arabic words")
    if re.search(r" [،؛؟!:](?![.:])", punct_ar):
        add("space_before_punctuation", "WARN")
    if re.search(r"[،؛](?=[^\s\d\"'»”)\]<|^]|$)", punct_ar.rstrip()):
        add("missing_space_after_comma", "WARN")
    doubled = re.findall(r"([،؛؟!?,;])\1", ar)
    if doubled and not re.search(re.escape(doubled[0] * 2), en.replace("؟", "?")):
        add("duplicated_punctuation", "WARN", doubled[0] * 2)
    if re.search(r"  +", ar) and not re.search(r"  +", en):
        add("double_space", "WARN")
    if ar != ar.strip() and en == en.strip():
        add("edge_whitespace", "WARN")
    if re.search(rf"(?<![{AR}])([{AR}]{{2,}}) \1(?![{AR}])", plain_ar):
        add("repeated_word", "WARN", re.search(rf"([{AR}]{{2,}}) \1", plain_ar)[0])
    if "ـ" in ar:
        add("tatweel", "WARN", "Kashida in data; renderer-dependent stretch")
    if re.search(r"\b(?:the|and|of|to|you)\b", plain_ar):
        add("english_function_word", "WARN")
    if "ديسباتش" in ar or "ديسبتش" in ar:
        add("brand_transliterated", "WARN", "Glossary keeps 'Dispatch' in Latin")
    if first_strong(ar) == "L" and ARABIC_LETTER.search(plain_ar):
        add("leading_latin_base_direction", "WARN", "First strong character is Latin; auto paragraph direction may become LTR")
    if row["speaker"] in FEMALE_SPEAKERS and re.search("(?<![ء-ي])آسف(?![ةء-ي])", ar):
        add("speaker_gender_agreement", "WARN", "female speaker, masculine آسف")
    if row["speaker"] in MALE_SPEAKERS and re.search("(?<![ء-ي])آسفة(?![ء-ي])", ar):
        add("speaker_gender_agreement", "WARN", "male speaker, feminine آسفة")
    for a in SELF_ADJ:  # first-person adjective agreement with the speaker's gender
        # masculine bare form, or the masculine accusative -ًا/-ا (لست بارعًا) instead of -ة
        if row["speaker"] in FEMALE_SPEAKERS and re.search(SELF + a + "(?:ًا|ا)?(?![ةء-ي])", ar):
            add("speaker_gender_agreement", "WARN", f"female speaker, masculine {a}")
        if row["speaker"] in MALE_SPEAKERS and re.search(SELF + a + "ة(?![ء-ي])", ar):
            add("speaker_gender_agreement", "WARN", f"male speaker, feminine {a}ة")
    for ch, name in {**BIDI, **ZERO_WIDTH}.items():
        if ch in ar:
            add("bidi_or_zero_width_control", "ERROR", name)
    if any(0xFB50 <= ord(c) <= 0xFDFF or 0xFE70 <= ord(c) <= 0xFEFC for c in ar):
        add("presentation_forms", "ERROR")
    for word in set(re.findall(f"[{AR}]{{4,}}", ar)):
        rev = word[::-1]
        if rev != word and word_freq[word] <= 1 and word_freq[rev] >= 20:
            add("possibly_reversed_word", "WARN", f"{word} (reverse '{rev}' appears {word_freq[rev]}x)")
    remaining = plain_en
    for term, expected in terms:  # longest first; a matched compound hides its parts
        pattern = r"(?<![A-Za-z])" + re.escape(term) + r"(?![A-Za-z])"
        if re.search(pattern, remaining):
            remaining = re.sub(pattern, " ", remaining)
            bare = expected[2:] if expected.startswith("ال") else expected  # clitic forms (للحلقة الحمراء)
            if expected not in ar and bare not in ar:
                add("glossary_term_missing", "WARN", f"{term} -> {expected}")
    return out


def main():
    rows = load_records()
    word_freq = Counter(w for r in rows for w in re.findall(f"[{AR}]{{2,}}", r["ar"]))
    gloss = glossary()
    # Only proper-name style terms are checked literally; common nouns inflect too much for substring checks.
    terms = sorted(((en, ar) for en, ar in gloss.items() if en[:1].isupper() and en != ar and len(en) > 2),
                   key=lambda t: -len(t[0]))
    findings, by_check = [], Counter()
    for row in rows:
        for f in check(row, word_freq, terms):
            findings.append({"id": row["id"], "target": row["target"], "index": row["index"], **f})
            by_check[(f["check"], f["severity"])] += 1
    unicode_rows = [f for f in findings if f["check"] in ("bidi_or_zero_width_control", "presentation_forms", "possibly_reversed_word")]
    out = ROOT / "reports/validation"
    out.mkdir(parents=True, exist_ok=True)
    summary = {"records": len(rows), "arabic_changed": sum(r["ar"] != r["en"] for r in rows),
               "findings": len(findings), "errors": sum(f["severity"] == "ERROR" for f in findings),
               "by_check": {f"{c}:{s}": n for (c, s), n in sorted(by_check.items())},
               "records_with_findings": len({f["id"] for f in findings})}
    (out / "translation_qa.json").write_text(json.dumps({"summary": summary, "findings": findings}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    codepoints = Counter(c for r in rows for c in r["ar"])
    safety = {"records": len(rows),
              "presentation_form_codepoints": sum(n for c, n in codepoints.items() if 0xFB50 <= ord(c) <= 0xFDFF or 0xFE70 <= ord(c) <= 0xFEFC),
              "bidi_controls": {name: codepoints.get(ch, 0) for ch, name in BIDI.items()},
              "zero_width": {name: codepoints.get(ch, 0) for ch, name in ZERO_WIDTH.items()},
              "possibly_reversed_words": [f for f in unicode_rows if f["check"] == "possibly_reversed_word"],
              "records_starting_with_latin_strong_char": sum(f["check"] == "leading_latin_base_direction" for f in findings)}
    (out / "unicode_safety.json").write_text(json.dumps(safety, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps({k: v for k, v in safety.items() if k != "possibly_reversed_words"}, indent=2),
          "reversed candidates:", len(safety["possibly_reversed_words"]))


if __name__ == "__main__":
    main()
