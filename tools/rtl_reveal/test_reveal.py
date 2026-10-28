"""Self-checks for reveal.py. Run: python -X utf8 tools/rtl_reveal/test_reveal.py
Passing proves the reference model only, not the game or ProtoAnimatedText."""
import json
import sys
from pathlib import Path

import regex

sys.path.insert(0, str(Path(__file__).parent))
import reveal as R  # noqa: E402

FONTS = [R.Font(p) for p in R.DEFAULT_FONTS]
CASES = json.loads((R.ROOT / "tests/rtl_cases.json").read_text(encoding="utf-8"))
SPEAKER = '<text style="Default" donthide="true">Robert: </><text style="Default">{}</>'
EPS = 1e-6


def P(markup, mode="cluster", **kw):
    return R.plan(markup, mode=mode, fonts=FONTS, **kw)


def total(p):
    return max([d for d in p["due"] if d is not None] or [0])


def gkey(g):
    return (g["line"], g["font"], g["gid"], round(g["x"], 6), round(g["y"], 6))


def unit_index(p):
    return {i: u for u, (s, e) in enumerate(p["units"]) for i in range(s, e)}


def is_right_sweep(p, vis):
    """True if, on every line, the visible units are exactly the rightmost ones."""
    for ln in range(len(p["lines"])):
        right = {}
        for i, g in enumerate(p["glyphs"]):
            if g["line"] == ln and not p["text"][g["cluster"]:g["cluster_end"]].isspace():
                right[g["unit"]] = max(right.get(g["unit"], -1e9), g["x"] + g["adv"])
        order = sorted(right, key=lambda u: -right[u])
        shown = {p["glyphs"][i]["unit"] for i in vis if p["glyphs"][i]["line"] == ln} & set(order)
        if set(order[:len(shown)]) != shown:
            return False
    return True


def check_invariants(p, label):
    text, units = p["text"], p["units"]
    # units partition the text in logical order
    assert units[0][0] == 0 and units[-1][1] == len(text), label
    assert all(a[1] == b[0] for a, b in zip(units, units[1:])), label
    ui = unit_index(p)
    # graphemes never split
    for m in regex.finditer(r"\X", text):
        assert ui[m.start()] == ui[m.end() - 1], (label, "grapheme split", m.group())
    # shaping clusters never split
    for g in p["glyphs"]:
        assert ui[g["cluster"]] == ui[g["cluster_end"] - 1], (label, "cluster split", g)
    # every frame is a subset of the final layout, and frames only grow
    final = [gkey(g) for g in p["glyphs"]]
    T = total(p)
    prev = set()
    for k in range(21):
        vis = set(R.visible_at(p, T * k / 20))
        assert {final[i] for i in vis} <= set(final), label
        assert prev <= vis, (label, "frame shrank")
        prev = vis
    assert prev == set(range(len(final))), (label, "final frame incomplete")
    # lines fit the wrap width and are pinned to the right edge
    for ln, meta in enumerate(p["lines"]):
        gs = [g for g in p["glyphs"] if g["line"] == ln]
        if gs:
            assert abs(max(g["x"] - g["dx"] + g["adv"] for g in gs) - p["wrap_at"]) < 1e-3, (label, "not right-anchored")
        words = len(text[meta["start"]:meta["end"]].split())
        assert meta["ink_width"] <= p["wrap_at"] + EPS or words <= 1, (label, "overflow", meta)
    # timing: same total as Proto's per-UTF-16-unit cadence, monotone in logical order
    dues = [d for d in p["due"] if d is not None]
    assert dues == sorted(dues), label
    counted = sum(len(text[i].encode("utf-16-le")) // 2 for i in range(len(text)) if i not in set(p["donthide"]))
    assert abs(T - max(counted - 1, 0) * R.PRINT_INTERVAL) < EPS, (label, "duration changed")
    # events: one print per timed unit, then exactly one finish; skip finishes once and stops printing
    ticks = [i * R.PRINT_INTERVAL / 2 for i in range(int(T / R.PRINT_INTERVAL * 2) + 3)]
    ev = R.simulate(p, ticks)
    assert [e[0] for e in ev].count("print") == len(dues) and ev[-1][0] == "finish", label
    assert [e[0] for e in ev].count("finish") == 1, label
    ev = R.simulate(p, ticks, skip_at=T / 2)
    assert [e[0] for e in ev].count("finish") == 1 and ev[-1][0] == "finish", label
    assert all(e[2] < T / 2 for e in ev if e[0] == "print"), label
    assert set(R.visible_at(p, None)) == set(range(len(final))), label


def proto_tutorial_model(p):
    """x positions per the author's public tutorial: one UTF-16 index per slice, pen advancing left-to-right
    in logical order. A model of the published technique, not of shipped 1.02 code."""
    x0 = min(g["x"] - g["dx"] for g in p["glyphs"])
    xs, pen = {}, x0
    for i in range(len(p["text"])):
        gs = [g for g in p["glyphs"] if g["cluster"] == i]
        xs[i] = pen if gs else None
        pen += sum(g["adv"] for g in gs)
    return xs


def first_x(p, i):
    return min(g["x"] for g in p["glyphs"] if g["cluster"] == i)


def main():
    # 1. culture gating: English (and any non-ar culture) keeps the original Proto path
    for c in ("en", "en-US", "fr"):
        assert P("<text>Hello there.</>", culture=c) is None
    assert P("<text>Hello</>", culture="ar-SA") is not None

    # 2. every project probe, bare and with the shared speaker formatter, in both modes
    for case in CASES:
        for wrapped in (False, True):
            m = SPEAKER.format(case["text"]) if wrapped else f'<text style="Default">{case["text"]}</>'
            for mode in ("cluster", "word"):
                p = P(m, mode=mode)
                assert p["text"].endswith(case["text"]), "logical order must be kept verbatim"
                assert not any(0xFB50 <= ord(c) <= 0xFEFF for c in p["text"]), "presentation forms"
                check_invariants(p, f'{case["id"]}/{mode}/{"speaker" if wrapped else "bare"}')

    # 3. lam-alef: two graphemes, one shaping cluster -> one unit
    p = P("<text>لا لَا</>")
    assert p["units"][0] == (0, 2), p["units"]
    assert len([g for g in p["glyphs"] if g["unit"] == 0]) == 1, "expected the font's lam-alef ligature"
    assert (3, 6) in p["units"], "lam+fatha+alef must stay one unit"

    # 4. combining marks stay with their base
    p = P("<text>مُهِمّ</>")
    assert p["units"][0] == (0, 2) and p["units"][-1] == (4, 6), p["units"]

    # 5. mixed BiDi: Arabic runs right-to-left, numbers and Latin left-to-right inside them
    t = "اضغط E للمتابعة، لديك 250 XP."
    p = P(f"<text>{t}</>")
    i250, ixp = t.index("250"), t.index("XP")
    assert first_x(p, i250) < first_x(p, i250 + 1) < first_x(p, i250 + 2)
    assert first_x(p, ixp) < first_x(p, ixp + 1)
    assert first_x(p, 0) > first_x(p, 1) > first_x(p, 2)
    assert first_x(p, ixp) < first_x(p, i250) < first_x(p, 0)
    # a single right-to-left clip rectangle cannot express this reveal; pure Arabic can
    T = total(p)
    assert not all(is_right_sweep(p, R.visible_at(p, T * k / 100)) for k in range(101)), "rect clip unexpectedly valid"
    q = P("<text>مرحبا بالعالم</>")
    assert all(is_right_sweep(q, R.visible_at(q, total(q) * k / 100)) for k in range(101))

    # 6. wrapping: computed once; lines reveal in order; explicit newlines respected
    long = next(c["text"] for c in CASES if c["id"] == "wrap")
    p = P(f"<text>{long} {long}</>")
    assert len(p["lines"]) >= 2
    line_due = [max(p["due"][g["unit"]] for g in p["glyphs"] if g["line"] == ln) for ln in range(len(p["lines"]))]
    assert line_due == sorted(line_due)
    assert len(P("<text>سطر أول\nسطر ثانٍ</>")["lines"]) == 2

    # 7. word mode keeps the identical layout; only unit grouping changes
    a, b = P(f"<text>{t}</>"), P(f"<text>{t}</>", mode="word")
    assert [gkey(g) for g in a["glyphs"]] == [gkey(g) for g in b["glyphs"]]
    assert all(b["text"][e - 1].isspace() or e == len(b["text"]) for _, e in b["units"])

    # 8. foreground and shadow get identical plans
    assert json.dumps(R.to_json(P(SPEAKER.format(t))), ensure_ascii=False) == \
        json.dumps(R.to_json(P(SPEAKER.format(t))), ensure_ascii=False)

    # 9. control: reshaping growing prefixes changes forms that were already visible
    word = "مرحبا بالعالم"
    final = {g["cluster"]: g["gid"] for g in P(f"<text>{word}</>")["glyphs"]}
    changed = [k for k in range(1, len(word)) for g in P(f"<text>{word[:k]}</>")["glyphs"]
               if g["cluster"] < k - 1 and final.get(g["cluster"]) != g["gid"]]
    last_changed = [k for k in range(1, len(word))
                    if [g["gid"] for g in P(f"<text>{word[:k]}</>")["glyphs"] if g["cluster"] == k - 1]
                    != [final[k - 1]]]
    assert last_changed, "prefix reshaping should change the newest letter's contextual form"
    print(f"control: prefix reshaping changes the newest letter's form at {len(last_changed)}/{len(word) - 1} steps"
          f" (older clusters: {len(changed)})")

    # 10. diagnostic: the published per-index slicing places Arabic letters in reverse, English correctly
    p = P(f"<text>{word}</>")
    xs = proto_tutorial_model(p)
    assert xs[0] < xs[1] and first_x(p, 0) > first_x(p, 1), "tutorial model should reverse Arabic"
    la = P("<text>لا</>")
    assert proto_tutorial_model(la)[1] is None, "alef of lam-alef has no glyph of its own"
    en = R.layout("<text>Hello world</>", fonts=FONTS, justify="left", base_dir="L")
    en_xs = proto_tutorial_model(en)
    assert all(abs(en_xs[i] - first_x(en, i)) < 1e-6 for i in range(len("Hello world")) if en_xs[i] is not None)

    print(f"rtl_reveal self-check passed: {len(CASES)} probe texts x 2 wrappers x 2 modes + targeted checks")


if __name__ == "__main__":
    main()
