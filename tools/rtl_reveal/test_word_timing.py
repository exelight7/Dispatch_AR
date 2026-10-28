"""Self-checks for word_timing.py. Run: python -X utf8 tools/rtl_reveal/test_word_timing.py [--json out.json]
Passing proves the timing model only, not ProtoAnimatedText 1.02 or the game."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import reveal as R  # noqa: E402
import word_timing as W  # noqa: E402

FONTS = [R.Font(p) for p in R.DEFAULT_FONTS]
SPACE = 0.16  # corpus estimate, see word_timing.corpus_space_interval
POC = W.word_poc(SPACE)
SPEAKER = '<text style="Default" donthide="true">{}: </><text style="Default">{}</>'
ZWJ, ZWNJ = "‍", "‌"

CASES = {
    "salam": "السلام عليكم",
    "salam_marks": "السَّلَامُ عَلَيْكُمْ",
    "lam_alef": "لا إله إلا الله",
    "latin_digits": "أهلاً 123 ABC",
    "version": "الإصدار v1.02 متاح الآن",
    "parens_dash": "مرحبا (TEST-42) بالعالم",
    "newline": "سطر أول\nسطر ثانٍ",
    "zwj_zwnj": f"عبد{ZWNJ}الله ه{ZWJ} كلمة",
    "punctuation": "مرحبا، كيف حالك؟ جيد... شكراً!",
    "multi_space": "كلمة  كلمتان   ثلاث",
    "lam_alef_marks": "لَا لاَ لإِ",
    "dash_no_parens": "مرحبا TEST-42 بالعالم",
    "price_usd": "السعر 50 USD اليوم",
    "long_wrap": "لا تقلق، سنرسل وحدة الإطفاء إلى شارع 42 فورًا ثم نتابع البلاغ الثاني من مركز Z-Force قبل "
                 "أن ينتهي الوقت المتاح لنا في هذه المناوبة الطويلة جدًا يا روبرت",
}
WRAPPERS = {
    "bare": lambda t: f'<text style="Default">{t}</>',
    "speaker": lambda t: SPEAKER.format("روبرت", t),
    "rich": lambda t: f'<text style="Default">قال </><text style="Italic">{t}</><text style="Default"> نعم</>',
}


def lay(markup):
    return R.layout(markup, fonts=FONTS)


def main():
    out = {"space_interval": SPACE, "cases": []}
    stock_fail, tut_fail = [], []
    for cid, text in CASES.items():
        for wname, wrap in WRAPPERS.items():
            L = lay(wrap(text))
            units = R.reveal_units(L, "cluster")
            for donthide in ("skip", "count"):
                for wait in ("after", "before"):
                    due = W.due_times(L, POC, donthide, wait)
                    label = f"{cid}/{wname}/{donthide}/{wait}"
                    v = W.cluster_violations(L, due, units)
                    assert not v, ("WORD_REVEAL_REJECTED", label, "shaping cluster partly visible", v[:3])
                    sw = W.split_words(L, due)
                    assert not sw, (label, "word split across frames", sw)
                    # everything visible at the end; speaker label visible from the first frame
                    end = W.alpha_at(L, due, max(due.values()))
                    assert all(a or c == "\n" for a, c in zip(end, L["text"])), label
                    assert all(W.alpha_at(L, due, -1.0)[i] for i in L["donthide"]), label
            due = W.due_times(L, POC)
            s_ok, t_ok, rows = W.bidi_report(L, due)
            (stock_fail if not s_ok else []).append(f"{cid}/{wname}")
            (tut_fail if not t_ok else []).append(f"{cid}/{wname}")
            if wname == "bare":
                out["cases"].append(dict(id=cid, text=text, stock_ok=s_ok, tutorial_ok=t_ok, lines=len(L["lines"]),
                                         multi_codepoint_units=[L["text"][s:e] for s, e in units if e - s > 1],
                                         frames=len(W.frames(due)) - 1, words=rows))
    assert not stock_fail, ("stock layout BiDi check failed", stock_fail)

    # control 1: the shipped per-letter timing splits clusters (harness is not vacuous)
    ctl = {}
    for cid in ("lam_alef", "salam_marks", "lam_alef_marks"):
        L = lay(WRAPPERS["bare"](CASES[cid]))
        ctl[cid] = len(W.cluster_violations(L, W.due_times(L, W.ORIGINAL), R.reveal_units(L, "cluster")))
        assert ctl[cid] > 0, cid
    out["control_original_timing_violations"] = ctl

    # control 2: a 1-frame-late alef (letter interval > 0 inside a word) is caught
    L = lay(WRAPPERS["bare"]("لا"))
    bad = W.word_poc(SPACE) | {"letter": 1e-4}
    assert W.cluster_violations(L, W.due_times(L, bad), R.reveal_units(L, "cluster"))

    # newline: Slate has no printed '\n', so the last word of line 1 and first of line 2 share a frame
    L = lay(WRAPPERS["bare"](CASES["newline"]))
    due = W.due_times(L, POC)
    t = L["text"]
    assert due[t.index("أول")] == due[t.index("\n") + 1], "expected newline merge"

    # multiple spaces: each space waits once more
    L = lay(WRAPPERS["bare"](CASES["multi_space"]))
    due = W.due_times(L, POC)
    t = L["text"]
    assert abs(due[t.index("ثلاث")] - 5 * SPACE) < 1e-9 and abs(due[t.index("كلمتان")] - 2 * SPACE) < 1e-9

    # donthide: 'count' delays the content by the speaker's space; 'skip' does not
    L = lay(WRAPPERS["speaker"]("مرحبا"))
    first = L["text"].index("مرحبا")
    assert W.due_times(L, POC, "skip")[first] == 0.0
    assert abs(W.due_times(L, POC, "count")[first] - SPACE) < 1e-9

    # zero-sum exactness: all letters of a word get bit-identical due times (0.0 additions)
    L = lay(WRAPPERS["bare"](CASES["salam_marks"]))
    due = W.due_times(L, POC)
    assert len({due[i] for i in range(len("السَّلَامُ"))}) == 1

    # long text wraps; reveal never changes line assignment (alpha-only over one layout) and lines go in order
    L = lay(WRAPPERS["bare"](CASES["long_wrap"]))
    assert len(L["lines"]) > 1, "long_wrap must wrap at 1050"
    due = W.due_times(L, POC)
    line_due = [min(due[i] for i in range(m["start"], m["end"]) if i in due) for m in L["lines"]]
    assert line_due == sorted(line_due)

    # a word split across two style runs (<text>مر</><text Italic>حبا</>) still shows in one frame
    L = lay('<text style="Default">قال مر</><text style="Italic">حبا</>')
    due = W.due_times(L, POC)
    assert len({due[i] for i in range(L["text"].index("مر"), len(L["text"]))}) == 1
    assert not W.cluster_violations(L, due, R.reveal_units(L, "cluster"))

    # English: original DataTable timing, per-character, unchanged; Arabic plan never built for en
    assert R.plan("<text>Hello there.</>", culture="en") is None
    en = R.layout("<text>Hello there.</>", fonts=FONTS, justify="left", base_dir="L")
    en_due = W.due_times(en, W.ORIGINAL)
    assert len(set(en_due.values())) == len(en_due), "English stays one character per tick"

    out["stock_bidi_failures"] = stock_fail
    out["tutorial_bidi_failures"] = tut_fail
    if "--json" in sys.argv:
        Path(sys.argv[sys.argv.index("--json") + 1]).write_text(
            json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    n = len(CASES) * len(WRAPPERS)
    print(f"cluster safety: 0 violations over {n} texts x 2 donthide x 2 wait models (every due-time frame)")
    print(f"control (shipped per-letter timing) violations: {ctl}")
    print(f"stock-position BiDi: {n - len(stock_fail)}/{n} ok")
    print(f"tutorial-slicing BiDi: {n - len(tut_fail)}/{n} ok; failing: {len(tut_fail)}")
    print("word_timing self-check passed (model only)")


if __name__ == "__main__":
    main()
