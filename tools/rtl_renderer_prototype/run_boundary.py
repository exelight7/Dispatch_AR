"""Round 004: do rich-text run boundaries change final shaped geometry? Detached HarfBuzz/UBA model only.

Slate gives every rich-text run its own shaping call. This compares plain-line shaping against the same
text cut into style runs, with and without HarfBuzz pre/post context (Slate's choice is unverified).

python -X utf8 tools/rtl_renderer_prototype/run_boundary.py
"""
import json
import unicodedata
from contextlib import contextmanager

import renderer as M

R = M.R
OUT = M.ROOT / "reports/rtl_research/renderer_repair/run_boundary.json"

CASES = {
    "salam": "السلام عليكم",
    "salam_marks": "السَّلَامُ عَلَيْكُمْ",
    "lam_alef": "لا إله إلا الله",
    "mixed_test42": "مرحبا TEST-42 بالعالم",
    "version": "الإصدار v1.02 متاح الآن",
    "price": "السعر 50 USD اليوم",
    "multiline": "السطر الأول هنا\nوالسطر الثاني مع TEST-42 أيضًا",
    "speaker": "روبرت: مرحبا بالعالم، كيف حالك؟",
    "punctuation": "مرحبا، كيف حالك؟ (بخير!) «نعم» — حسنًا...",
    "long_wrap": " ".join(["هذه جملة طويلة جدًا تحتوي على كلمات عربية كثيرة مع SDN 250 XP وأرقام 1.02"] * 3),
}


def word_starts(t):
    return {i for i in range(1, len(t)) if t[i - 1].isspace() and not t[i].isspace()}


def word_ends(t):
    return {i for i in range(1, len(t)) if not t[i - 1].isspace() and t[i].isspace()}


def punct_cuts(t):
    p = lambda c: unicodedata.category(c).startswith("P")
    return word_starts(t) | {i for i in range(1, len(t)) if p(t[i - 1]) != p(t[i])
                             and not t[i - 1].isspace() and not t[i].isspace()}


def mid_word(t):
    """Negative control: cut inside every Arabic word of 2+ letters."""
    cuts, i = set(), 0
    for w in t.split(" "):
        if len(w) > 1 and any("؀" <= c <= "ۿ" for c in w):
            cuts.add(i + len(w) // 2)
        i += len(w) + 1
    return cuts


@contextmanager
def style_runs(cuts, context):
    """Make the oracle treat each cut as a run boundary, as Slate does for each rich-text run."""
    runs_of, shape_range = R.runs_of, R.shape_range

    def split_runs(lo, hi, levels, font_idx):
        out = []
        for s, e in runs_of(lo, hi, levels, font_idx):
            pts = [s, *sorted(c for c in cuts if s < c < e), e]
            out += zip(pts, pts[1:])
        return out

    def isolated(text, start, end, level, font, px):
        gs = shape_range(text[start:end], 0, end - start, level, font, px)
        for g in gs:
            g["cluster"] += start
            g["cluster_end"] += start
        return gs

    R.runs_of = split_runs
    if not context:
        R.shape_range = isolated
    try:
        yield
    finally:
        R.runs_of, R.shape_range = runs_of, shape_range


def geometry(lay):
    return [(g["line"], g["font"], g["gid"], g["cluster"], round(g["x"], 4), round(g["y"], 4), round(g["adv"], 4))
            for g in lay["glyphs"]], [(ln["start"], ln["end"]) for ln in lay["lines"]]


def diff(a, b):
    (ga, la), (gb, lb) = a, b
    return dict(lines_equal=la == lb, glyph_count=(len(ga), len(gb)),
                glyph_mismatches=sum(x != y for x, y in zip(ga, gb)) + abs(len(ga) - len(gb)))


def main():
    fonts = [R.Font(p) for p in R.DEFAULT_FONTS]
    cutters = {"word_start": word_starts, "word_end": word_ends, "word_and_punct": punct_cuts, "NEG_mid_word": mid_word}
    results = []
    for name, text in CASES.items():
        plain = geometry(R.layout(text, fonts=fonts))
        for cut_name, cutter in cutters.items():
            cuts = cutter(text)
            for context in (True, False):
                with style_runs(cuts, context):
                    split = geometry(R.layout(text, fonts=fonts))
                d = diff(plain, split)
                results.append(dict(case=name, cuts=cut_name, n_cuts=len(cuts), hb_context=context,
                                    identical=d["lines_equal"] and d["glyph_mismatches"] == 0, **d))

    pos = [r for r in results if not r["cuts"].startswith("NEG")]
    neg = [r for r in results if r["cuts"].startswith("NEG")]
    # Sensitivity: cutting inside Arabic words must be detectable, or the identity result means nothing.
    assert any(not r["identical"] for r in neg if not r["hb_context"]), "negative control did not detect a mid-word cut"
    assert any(not r["identical"] for r in neg if r["hb_context"]), "context mode hid every mid-word defect"
    summary = {
        "evidence_class": "DETACHED_MODEL_TESTED",
        "not_proven": "Slate 4.27 per-run shaping context, ICU line breaking, composite-font fallback parity",
        "cases": len(CASES),
        "positive_comparisons": len(pos),
        "positive_identical": sum(r["identical"] for r in pos),
        "positive_identical_with_context": sum(r["identical"] for r in pos if r["hb_context"]),
        "positive_identical_without_context": sum(r["identical"] for r in pos if not r["hb_context"]),
        "negative_detected_with_context": sum(not r["identical"] for r in neg if r["hb_context"]),
        "negative_detected_without_context": sum(not r["identical"] for r in neg if not r["hb_context"]),
        "negative_comparisons_per_mode": len(neg) // 2,
        "fonts": [p.name for p in R.DEFAULT_FONTS],
    }
    out = dict(summary=summary, results=results)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    for r in pos:
        if not r["identical"]:
            print("DIFF", r)


if __name__ == "__main__":
    main()
