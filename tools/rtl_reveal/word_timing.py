"""Word-reveal hypothesis model for Proto style timing (not game code, not Unreal).

Hypothesis: PrintLetterInterval=0, PrintLetterAnimationTime=0, UseAdvancedPrintIntervals=true,
SpaceInterval>0. Timing follows the author's published PlayNextLetter loop: a timer callback prints
characters in a while-loop until the accumulated time no longer covers the next wait, so characters
whose waits are 0 are all printed inside one callback. That loop is PUBLIC_REFERENCE_ONLY; shipped 1.02
code was not seen.

Paint boundary: one Slate OnPaint per frame, after the world/timer tick of that frame. Every alpha
write made by timer callbacks that fired at or before frame time T is visible in that paint; none after.
Visibility is a step function of T that changes only at due times, so checking T at every distinct due
time covers every possible frame at any frame rate.

Two paint models are compared over the same per-index alpha:
  stock    glyphs at their final HarfBuzz + UBA positions (what a correct run would draw)
  tutorial one slice per UTF-16 index, pen moving left-to-right in logical order (published tutorial)

Usage: python -X utf8 tools/rtl_reveal/word_timing.py [--corpus]
"""
import glob
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import reveal as R  # noqa: E402

# DT_SubtitlesProtoRichText row "Default" as shipped (CONFIRMED_FROM_ASSET).
ORIGINAL = dict(letter=0.025, anim=0.0, advanced=False, space=0.0,
                comma=0.045, sentence=0.045, ellipsis=0.045, dash=0.05)


def word_poc(space):
    # Punctuation waits are 0: the shipped rows never apply them (advanced=false), and a mid-word
    # dash wait would split a word. Only SpaceInterval becomes active.
    return dict(letter=0.0, anim=0.0, advanced=True, space=space,
                comma=0.0, sentence=0.0, ellipsis=0.0, dash=0.0)


def special(text, i):
    """PRT_* class of text[i]. ponytail: ASCII rules inferred from EProtoRichTextSpecialCharacter names;
    1.02's classifier was not seen (Arabic ، and ؟ are assumed ordinary letters)."""
    c = text[i]
    if c == " ":
        return "space"
    if c == ",":
        return "comma"
    if c == ".":
        return "ellipsis" if "." in (text[i - 1:i], text[i + 1:i + 2]) else "sentence"
    if c in "!?":
        return "sentence"
    if c == "-" and 0 < i < len(text) - 1 and text[i - 1].isalnum() and text[i + 1].isalnum():
        return "dash"
    return None


def interval(text, i, cfg):
    k = special(text, i) if cfg["advanced"] else None
    return cfg[k] if k else cfg["letter"]


def counted_indices(lay, donthide):
    """Indices Proto counts. '\\n' ends a Slate line and is assumed not to be a printed character
    (INFERRED). donthide: 'skip' = not counted, 'count' = counted but visible from t=0 (NOT_PROVEN which)."""
    ex = set(lay["donthide"]) if donthide == "skip" else set()
    return [i for i, c in enumerate(lay["text"]) if c != "\n" and i not in ex]


def due_times(lay, cfg, donthide="skip", wait="after"):
    """index -> time its alpha becomes 1. wait='after': a character's interval is waited after it is
    printed (author's wording "wait after a space"); 'before': waited before it. With letter=0 both
    'replace' and 'add' readings of special intervals give the same result."""
    text, due, t, prev = lay["text"], {}, 0.0, None
    for i in counted_indices(lay, donthide):
        if prev is not None:
            t += interval(text, prev if wait == "after" else i, cfg)
        due[i], prev = t, i
    return due


def alpha_at(lay, due, T):
    """Per-index alpha at a paint whose frame time is T. donthide is always visible."""
    vis = {i for i, d in due.items() if d <= T} | set(lay["donthide"])
    return [i in vis for i in range(len(lay["text"]))]


def frames(due):
    return [-1.0] + sorted(set(due.values()))


def cluster_violations(lay, due, units):
    """(frame time, unit) pairs where a shaping cluster is partly visible. units = grapheme clusters
    closed under HarfBuzz clusters. Checked on source indices, so it holds for any glyph->index mapping
    (including UE's per-character SourceIndex)."""
    bad = []
    for T in frames(due):
        a = alpha_at(lay, due, T)
        for s, e in units:
            idx = [i for i in range(s, e) if lay["text"][i] != "\n"]
            if len({a[i] for i in idx}) > 1:
                bad.append((T, (s, e), lay["text"][s:e]))
    return bad


def split_words(lay, due):
    """Words (maximal non-space runs) whose counted characters do not all share one due time."""
    return [m.group() for m in re.finditer(r"\S+", lay["text"])
            if len({due[i] for i in range(m.start(), m.end()) if i in due}) > 1]


def tutorial_x(lay):
    """x per logical index under the published per-index slicing (pen left-to-right in logical order)."""
    xs = {}
    for ln, meta in enumerate(lay["lines"]):
        gs = [g for g in lay["glyphs"] if g["line"] == ln]
        pen = min((g["x"] - g["dx"] for g in gs), default=0.0)
        for i in range(meta["start"], meta["end"]):
            mine = [g for g in gs if g["cluster"] == i]
            if mine:
                xs[i] = pen
            pen += sum(g["adv"] for g in mine)
    return xs


def stock_x(lay):
    xs = {}
    for g in lay["glyphs"]:
        xs[g["cluster"]] = min(xs.get(g["cluster"], 1e9), g["x"])
    return xs


def word_rows(lay, due):
    """Per word in logical order: reveal time, line, x-range under both paint models."""
    sx, tx = stock_x(lay), tutorial_x(lay)
    line_of = {g["cluster"]: g["line"] for g in lay["glyphs"]}
    rows = []
    for m in re.finditer(r"\S+", lay["text"]):
        idx = [i for i in range(m.start(), m.end()) if i in sx]
        if not idx:
            continue
        rows.append(dict(word=m.group(), start=m.start(), line=line_of[idx[0]],
                         due=min((due[i] for i in idx if i in due), default=None),
                         chars="".join(lay["text"][i] for i in idx),
                         stock=[round(sx[i], 1) for i in idx], tutorial=[round(tx[i], 1) for i in idx]))
    return rows


def rtl_word(w):
    return any("؀" <= c <= "ۿ" for c in w)


def bidi_report(lay, due):
    """Checks on the final layout of each paint model plus the reveal sequence (logical order).
    Returns (stock_ok, tutorial_ok, rows)."""
    rows = word_rows(lay, due)
    dues = [r["due"] for r in rows if r["due"] is not None]
    assert dues == sorted(dues), "reveal must follow logical order"

    def ok(model):
        for r in rows:  # letters/digits only: brackets mirror, ZWJ/ZWNJ and marks have no own advance
            xs = [x for c, x in zip(r["chars"], r[model]) if c.isalnum()]
            if len(xs) < 2:
                continue
            ar = rtl_word(r["word"])
            if ar and not all(a > b for a, b in zip(xs, xs[1:])):
                return False
            if not ar and r["word"].isascii() and not all(a < b for a, b in zip(xs, xs[1:])):
                return False
        for a, b in zip(rows, rows[1:]):  # consecutive Arabic words on one line: right to left
            if a["line"] == b["line"] and rtl_word(a["word"]) and rtl_word(b["word"]) and \
                    not min(a[model]) > max(b[model]):
                return False
        return True

    return ok("stock"), ok("tutorial"), rows


def corpus_space_interval(letter=ORIGINAL["letter"]):
    """SpaceInterval that keeps the Arabic subtitle corpus' total reveal time: letter * sum(N) / sum(S),
    N = counted UTF-16 units per line, S = ASCII spaces per line. An estimate, not a tuned value."""
    n = s = lines = 0
    for f in glob.glob(str(R.ROOT / "translation/records/10*.json")):
        for r in json.loads(Path(f).read_text(encoding="utf-8")):
            if r["category"] != "Dialogue/Subtitles" or not r.get("ar"):
                continue
            t = re.sub(r"<[^>]*>", "", r["ar"]).replace("\r", "").replace("\n", "")
            n += len(t.encode("utf-16-le")) // 2
            s += t.count(" ")
            lines += 1
    return dict(lines=lines, utf16_units=n, spaces=s, units_per_space=n / s, space_interval=letter * n / s)


def main():
    c = corpus_space_interval()
    print(json.dumps(c, indent=1))
    if "--corpus" in sys.argv:
        return


if __name__ == "__main__":
    main()
