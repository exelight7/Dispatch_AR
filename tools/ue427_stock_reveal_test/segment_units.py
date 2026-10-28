"""Reference implementation of the Arabic reveal-unit segmentation (round 008) and a check over the real subtitles.

The Blueprint builder must reproduce `build_markup` exactly. Rules:
  1. Input = final logical text: censorship and ProcessLocalizedTextWithCallback already applied, game italic markers
     (<Italic>, </>) removed. Speaker prefix = "<SpeakerName>:" when the game would show a speaker name.
  2. Split characters are exactly U+0020, U+0009, U+000A, U+000D. NBSP, U+202F, ZWSP, ZWJ, ZWNJ, harakat, tatweel and
     punctuation never split, so a run boundary is always next to one of those four characters.
  3. Token = maximal run of non-split characters. A token with no letter (digits, punctuation, symbols) joins the previous
     unit together with the gap between them, unless that gap contains a newline or there is no previous unit.
  4. Speaker units come first; reveal starts with all of them visible (English shows the speaker immediately).
  5. More than MAX_UNITS units: units MAX_UNITS-1.. merge into one last unit (coarser end, layout unchanged).
  6. Markup: leading gap, then "<u{k}>" + escaped unit + "</>" + gap. Gaps stay outside tags (Default row).
     Escape & < > " as &amp; &lt; &gt; &quot; (the stock rich-text parser unescapes these).
  7. Step delay of a unit = 0.025 s x its letters that are not combining marks (DISPATCH rows: PrintLetterInterval 0.025,
     UseAdvancedPrintIntervals false, SpaceInterval 0). Speaker units have delay 0.

usage: python -I segment_units.py [records_dir] [out.json]
"""
import glob
import html
import json
import re
import sys
import unicodedata

MAX_UNITS = 128
SPLIT = " \t\n\r"
LETTER_RANGES = ((0x41, 0x5A), (0x61, 0x7A), (0x620, 0x64A), (0x66E, 0x6D3), (0x750, 0x77F), (0xFB50, 0xFDFF), (0xFE70, 0xFEFC))


def is_letter(c):
    o = ord(c)
    return any(a <= o <= b for a, b in LETTER_RANGES)


def tokens(text):
    lead = re.match(r"[ \t\n\r]*", text).group(0)
    return lead, re.findall(r"([^ \t\n\r]+)([ \t\n\r]*)", text[len(lead):])


def units_of(text):
    """[[unit text, gap after]] for text (rule 3)."""
    lead, toks = tokens(text)
    out = []
    for word, gap in toks:
        if not any(is_letter(c) for c in word) and out and "\n" not in out[-1][1]:
            out[-1][0] += out[-1][1] + word
            out[-1][1] = gap
        else:
            out.append([word, gap])
    return lead, out


def letters(s):
    return sum(1 for c in s if c not in SPLIT and not unicodedata.combining(c))


def build_markup(content, speaker=""):
    s_lead, s_units = units_of(speaker + ":") if speaker else ("", [])
    if s_units:
        s_units[-1][1] = " "  # the game's format is "{SpeakerName}: {SubtitleContent}"
    c_lead, c_units = units_of(content)
    units = s_units + c_units
    n_speaker = len(s_units)
    if len(units) > MAX_UNITS:
        tail = units[MAX_UNITS - 1:]
        units = units[:MAX_UNITS - 1] + [["".join(w + g for w, g in tail[:-1]) + tail[-1][0], tail[-1][1]]]
    lead = s_lead if speaker else c_lead
    markup = lead + "".join(f"<u{k}>{html.escape(w, quote=True).replace('&#x27;', chr(39))}</>{g}" for k, (w, g) in enumerate(units))
    delays = [0.0 if k < n_speaker else 0.025 * letters(w) for k, (w, g) in enumerate(units)]
    return markup, len(units), n_speaker, delays


def plain_of(markup):
    return html.unescape(re.sub(r"<u\d+>|</>", "", markup))


def self_check():
    m, n, k, _ = build_markup("مرحبا (TEST-42) بالعالم", "المحقق")
    assert m == "<u0>المحقق:</> <u1>مرحبا</> <u2>(TEST-42)</> <u3>بالعالم</>" and (n, k) == (4, 1), m
    m, n, _, _ = build_markup("السعر 50 USD اليوم")
    assert m == "<u0>السعر 50</> <u1>USD</> <u2>اليوم</>" and n == 3, m
    m, n, _, _ = build_markup("أ\n50 ب")
    assert m == "<u0>أ</>\n<u1>50</> <u2>ب</>", m  # no merge across a newline
    m, _, _, _ = build_markup("a<b & \"c\"")
    assert plain_of(m) == "a<b & \"c\"" and "<b" not in m, m
    m, n, _, _ = build_markup(" ".join(["كلمة"] * 200))
    assert n == MAX_UNITS and plain_of(m) == " ".join(["كلمة"] * 200)
    _, _, _, d = build_markup("السَّلَامُ")
    assert abs(d[0] - 0.025 * 6) < 1e-9, d  # harakat do not lengthen the delay


def main():
    self_check()
    rec_dir = sys.argv[1] if len(sys.argv) > 1 else "translation/records"
    recs = [r for p in sorted(glob.glob(rec_dir + "/*.json")) for r in json.load(open(p, encoding="utf-8"))]
    names = {r["en"]: r["ar"] for r in recs if r["category"] == "Character Names"}
    subs = [r for r in recs if r["category"] == "Dialogue/Subtitles"]
    stats = {"subtitles": len(subs), "max_units": 0, "max_speaker_units": 0, "over_max_units": 0,
             "roundtrip_failures": 0, "speaker_name_missing_arabic": 0, "lines_with_markup_chars": 0}
    hist = {}
    longest = None
    for r in subs:
        text = r["ar"].replace("<Italic>", "").replace("</>", "")
        spk = names.get(r["speaker"], "") if r["speaker"] else ""
        if r["speaker"] and not spk:
            stats["speaker_name_missing_arabic"] += 1
        m, n, k, _ = build_markup(text, spk)
        stats["roundtrip_failures"] += plain_of(m) != ((spk + ": ") if spk else "") + text
        stats["lines_with_markup_chars"] += any(c in text for c in "<>&\"")
        stats["over_max_units"] += n >= MAX_UNITS
        stats["max_speaker_units"] = max(stats["max_speaker_units"], k)
        if n > stats["max_units"]:
            stats["max_units"], longest = n, r["id"]
        hist[n] = hist.get(n, 0) + 1
    ns = sorted(n for n, c in hist.items() for _ in range(c))
    stats.update({"longest_id": longest, "p50_units": ns[len(ns) // 2], "p99_units": ns[int(len(ns) * 0.99)],
                  "max_units_capacity": MAX_UNITS, "label": "OFFLINE - Arabic translation data, not in-game"})
    if len(sys.argv) > 2:
        with open(sys.argv[2], "w", encoding="utf-8") as fh:
            json.dump(stats, fh, ensure_ascii=False, indent=1)
    print(json.dumps(stats, ensure_ascii=False, indent=1))
    assert stats["roundtrip_failures"] == 0 and stats["over_max_units"] == 0


if __name__ == "__main__":
    main()
