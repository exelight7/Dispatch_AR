"""Reference model (oracle) for cluster-safe Arabic progressive reveal over a fixed final layout.

Not game code. It shows what a native ProtoRichText run fix must compute and gives a test
oracle for it: shape and wrap the complete text once, then change only per-glyph visibility.
Text stays in logical Unicode order. Nothing is reversed or turned into presentation forms.
BiDi comes from python-bidi (unicode-bidi crate, full UBA). Shaping comes from HarfBuzz.

Usage:
  python -X utf8 tools/rtl_reveal/reveal.py "<markup text>" [--json out.json] [--svg out.svg]
"""
import argparse
import json
import re
import sys
from pathlib import Path

import regex
import uharfbuzz as hb
from bidi import get_display

ROOT = Path(__file__).resolve().parents[2]
# Fallback chain modeled on Slate composite-font fallback: Latin face first, then the engine's Arabic UI face.
DEFAULT_FONTS = [
    ROOT / "extracted/Dispatch/Content/Shared/UI/Fonts/Montserrat/static/Montserrat-Medium.ufont",
    ROOT / "extracted/Engine/Content/Slate/Fonts/NotoNaskhArabicUI-Regular.ttf",
]
# Values taken from WBP_SubtitleBlock / DT_SubtitlesProtoRichText (reports/rtl_research/ASSET_INSPECTION.md).
WRAP_AT = 1050.0
FONT_PT = 28
PRINT_INTERVAL = 0.025
PX_PER_PT = 96 / 72  # Slate renders font points at 96 DPI

TAG = re.compile(r'<(/?)([A-Za-z]*)((?:\s+\w+="[^"]*")*)\s*/?>')
ATTR = re.compile(r'(\w+)="([^"]*)"')


class Font:
    def __init__(self, path):
        self.path = Path(path)
        self.data = self.path.read_bytes()
        self.face = hb.Face(self.data)
        self.hb = hb.Font(self.face)
        self.upem = self.face.upem
        self.cmap = set(self.face.unicodes)
        ext = self.hb.get_font_extents("ltr")
        self.ascender, self.descender = ext.ascender, ext.descender


def parse_markup(s):
    """Proto markup -> (content, donthide index set). Supports <text ...>, <t ...>, </>."""
    out, exempt, stack, pos = [], set(), [], 0

    def emit(seg):
        start = sum(map(len, out))
        if stack and stack[-1].get("donthide") == "true":
            exempt.update(range(start, start + len(seg)))
        out.append(seg)

    for m in TAG.finditer(s):
        emit(s[pos:m.start()])
        if m.group(1):
            stack and stack.pop()
        else:
            stack.append(dict(ATTR.findall(m.group(3))))
        pos = m.end()
    emit(s[pos:])
    return "".join(out), exempt


def bidi_levels(text, base_dir):
    """Per-codepoint embedding levels from the full UBA (unicode-bidi via python-bidi)."""
    if not text:
        return []
    # ponytail: parses python-bidi's debug dump (levels per UTF-8 byte); swap for an ICU binding if one is ever installed.
    dump = get_display(text, base_dir=base_dir, debug=True)
    lv = [int(x) for x in re.findall(r"Level\(\s*(\d+),?\s*\)", dump.split("paragraphs:")[0])]
    out, b = [], 0
    for ch in text:
        out.append(lv[b])
        b += len(ch.encode("utf-8"))
    return out


def pick_fonts(text, fonts):
    """Per-codepoint font: first face covering it; marks/neutrals stay with the previous face if covered."""
    res, prev = [], None
    for ch in text:
        cp = ord(ch)
        neutral = not (ch.isalpha() or ch.isdigit())
        if prev is not None and neutral and cp in fonts[prev].cmap:
            res.append(prev)
            continue
        prev = next((i for i, f in enumerate(fonts) if cp in f.cmap), 0)
        res.append(prev)
    return res


def shape_range(text, start, end, level, font, px):
    """Shape text[start:end] with surrounding context; return glyphs in visual (left-to-right) order."""
    buf = hb.Buffer()
    buf.add_str(text, item_offset=start, item_length=end - start)
    buf.guess_segment_properties()
    buf.direction = "rtl" if level % 2 else "ltr"
    hb.shape(font.hb, buf)
    k = px / font.upem
    clusters = sorted({i.cluster for i in buf.glyph_infos})
    cl_end = {c: (clusters[n + 1] if n + 1 < len(clusters) else end) for n, c in enumerate(clusters)}
    return [
        dict(gid=i.codepoint, cluster=i.cluster, cluster_end=cl_end[i.cluster],
             adv=p.x_advance * k, dx=p.x_offset * k, dy=p.y_offset * k)
        for i, p in zip(buf.glyph_infos, buf.glyph_positions)
    ]


def runs_of(lo, hi, levels, font_idx):
    runs, s = [], lo
    for i in range(lo + 1, hi + 1):
        if i == hi or levels[i] != levels[s] or font_idx[i] != font_idx[s]:
            runs.append((s, i))
            s = i
    return runs


def l2_order(runs, levels):
    """UAX#9 L2 applied to whole runs (each run has a single level)."""
    order = list(range(len(runs)))
    lv = [levels[r[0]] for r in runs]
    if not lv:
        return order
    lowest_odd = min(l for l in lv if l % 2) if any(l % 2 for l in lv) else max(lv) + 1
    for level in range(max(lv), lowest_odd - 1, -1):
        i = 0
        while i < len(order):
            if lv[order[i]] >= level:
                j = i
                while j < len(order) and lv[order[j]] >= level:
                    j += 1
                order[i:j] = order[i:j][::-1]
                i = j
            else:
                i += 1
    return order


def layout(markup, fonts=None, culture="ar", wrap_at=WRAP_AT, font_pt=FONT_PT,
           justify="right", base_dir="R"):
    """Build the final shaped, wrapped, BiDi-ordered layout once. Returns None for non-Arabic cultures
    so the caller keeps the original Proto path (English behaviour unchanged)."""
    if culture.split("-")[0] != "ar":
        return None
    fonts = fonts or [Font(p) for p in DEFAULT_FONTS]
    px = font_pt * PX_PER_PT
    text, donthide = parse_markup(markup)
    levels = [0] * len(text)
    font_idx = pick_fonts(text, fonts)
    lines = []  # (start, end) codepoint ranges
    p0 = 0
    for para in text.split("\n"):
        p1 = p0 + len(para)
        levels[p0:p1] = bidi_levels(para, base_dir)
        lines += wrap_paragraph(text, p0, p1, levels, font_idx, fonts, px, wrap_at)
        p0 = p1 + 1
    glyphs, line_meta = [], []
    for ln, (a, b) in enumerate(lines):
        lv = levels[:]
        t = b
        while t > a and text[t - 1].isspace():  # UAX#9 L1: trailing whitespace takes paragraph level
            t -= 1
        for i in range(t, b):
            lv[i] = 1 if base_dir == "R" else 0
        runs = runs_of(a, b, lv, font_idx) if b > a else []
        shaped = [shape_range(text, s, e, lv[s], fonts[font_idx[s]], px) for s, e in runs]
        for g_list, (s, e) in zip(shaped, runs):
            for g in g_list:
                g["font"] = font_idx[s]
                g["level"] = lv[s]
        visual = [g for r in l2_order(runs, lv) for g in shaped[r]]
        width = sum(g["adv"] for g in visual)
        ink = width - sum(g["adv"] for g in visual if g["cluster"] >= t)
        x = {"right": wrap_at - width, "center": (wrap_at - width) / 2}.get(justify, 0.0)
        for g in visual:
            g.update(line=ln, x=x + g["dx"], y=g["dy"])
            x += g["adv"]
            glyphs.append(g)
        line_meta.append(dict(start=a, end=b, width=width, ink_width=ink))
    line_h = max((f.ascender - f.descender) * px / f.upem for f in fonts)
    return dict(text=text, donthide=sorted(donthide), levels=levels, lines=line_meta,
                glyphs=glyphs, px=px, line_height=line_h, wrap_at=wrap_at, fonts=[str(f.path) for f in fonts],
                _fonts=fonts)


def wrap_paragraph(text, a, b, levels, font_idx, fonts, px, wrap_at):
    """Greedy wrap at whitespace using shaped advances of the whole paragraph."""
    # ponytail: break opportunities = after whitespace only (UE uses ICU UAX#14); add a UAX#14 iterator if hyphen/CJK breaks matter.
    if a == b:
        return [(a, b)]
    adv = [0.0] * (b - a)
    for s, e in runs_of(a, b, levels, font_idx):
        for g in shape_range(text, s, e, levels[s], fonts[font_idx[s]], px):
            adv[g["cluster"] - a] += g["adv"]
    words = [(m.start() + a, m.end() + a) for m in re.finditer(r"\S*\s*", text[a:b]) if m.group()]
    lines, ls, w = [], a, 0.0
    for ws, we in words:
        ink_end = ws + len(text[ws:we].rstrip())
        word_ink = sum(adv[ws - a:ink_end - a])
        if w + word_ink > wrap_at and ws > ls:
            lines.append((ls, ws))
            ls, w = ws, 0.0
        w += sum(adv[ws - a:we - a])
    lines.append((ls, b))
    return lines


def reveal_units(lay, mode="cluster"):
    """Logical-order reveal units. Each unit is a union of extended grapheme clusters closed under
    HarfBuzz shaping clusters (lam-alef and similar ligatures stay whole). mode='word' merges up to whitespace."""
    text = lay["text"]
    n = len(text)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union_range(s, e):
        for i in range(s + 1, e):
            parent[find(i)] = find(s)

    for m in regex.finditer(r"\X", text):
        union_range(m.start(), m.end())
    for g in lay["glyphs"]:
        union_range(g["cluster"], g["cluster_end"])
    if mode == "word":
        for m in re.finditer(r"\S+\s*", text):
            union_range(m.start(), m.end())
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    units = sorted((min(v), max(v) + 1) for v in groups.values())
    for s, e in units:
        assert all(find(i) == find(s) for i in range(s, e)), "unit is not contiguous"
    return units


def schedule(lay, units, interval=PRINT_INTERVAL):
    """Due time per unit, keeping Proto's per-UTF-16-unit cadence: a unit appears when its last code
    unit would have appeared originally, so total duration is unchanged. donthide text is visible at t=0
    and not counted (assumption: unverified against shipped Proto 1.02)."""
    exempt = set(lay["donthide"])
    k, due = -1, []
    for s, e in units:
        for i in range(s, e):
            if i not in exempt:
                k += len(lay["text"][i].encode("utf-16-le")) // 2
        due.append(None if all(i in exempt for i in range(s, e)) else max(k, 0) * interval)
    return due


def plan(markup, culture="ar", mode="cluster", **kw):
    lay = layout(markup, culture=culture, **kw)
    if lay is None:
        return None
    units = reveal_units(lay, mode)
    due = schedule(lay, units)
    unit_of = {}
    for u, (s, e) in enumerate(units):
        for i in range(s, e):
            unit_of[i] = u
    for g in lay["glyphs"]:
        g["unit"] = unit_of[g["cluster"]]
    lay.update(units=units, due=due, mode=mode)
    return lay


def visible_at(p, t):
    """Indices into p['glyphs'] visible at time t (None = after skip/finish)."""
    ok = {u for u, d in enumerate(p["due"]) if d is None or t is None or d <= t}
    return [i for i, g in enumerate(p["glyphs"]) if g["unit"] in ok]


def simulate(p, ticks, skip_at=None):
    """Event stream as the Blueprint sees it: one 'print' per revealed unit (drives shadow RequestRender),
    one 'finish'. Skip reveals everything and finishes once."""
    events, shown, done = [], set(), False
    for t in ticks:
        if done:
            break
        if skip_at is not None and t >= skip_at:
            events.append(("finish", t))
            done = True
            break
        for u, d in enumerate(p["due"]):
            if d is not None and d <= t and u not in shown:
                shown.add(u)
                events.append(("print", u, t))
        if len(shown) == sum(d is not None for d in p["due"]):
            events.append(("finish", t))
            done = True
    return events


def to_json(p):
    return {k: v for k, v in p.items() if not k.startswith("_")}


def svg(p, fractions=(0.0, 0.25, 0.5, 0.75, 1.0)):
    """Synthetic frames (not game output): hidden glyphs grey, visible black; geometry identical per frame."""
    from fontTools.pens.svgPathPen import SVGPathPen

    fonts = p["_fonts"]
    total = max([d for d in p["due"] if d is not None] or [0])
    lh = p["line_height"]
    frame_h = lh * len(p["lines"]) + 20
    asc = max(f.ascender * p["px"] / f.upem for f in fonts)
    paths = {}
    rows = []
    for fi, fr in enumerate(fractions):
        vis = set(visible_at(p, total * fr))
        y0 = fi * frame_h
        rows.append(f'<text x="4" y="{y0 + 14:.1f}" font-size="12" fill="#888">t={total * fr:.3f}s'
                    ' | SYNTHETIC HarfBuzz model, not game output</text>')
        for i, g in enumerate(p["glyphs"]):
            key = (g["font"], g["gid"])
            if key not in paths:
                pen = SVGPathPen(None)
                fonts[g["font"]].hb.draw_glyph_with_pen(g["gid"], pen)
                paths[key] = pen.getCommands()
            if not paths[key]:
                continue
            k = p["px"] / fonts[g["font"]].upem
            by = y0 + 20 + g["line"] * lh + asc
            fill = "#111" if i in vis else "#ddd"
            rows.append(f'<path fill="{fill}" transform="translate({g["x"]:.2f},{by - g["y"]:.2f}) '
                        f'scale({k:.5f},{-k:.5f})" d="{paths[key]}"/>')
    h = frame_h * len(fractions)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {p["wrap_at"]:.0f} {h:.0f}" '
            f'width="{p["wrap_at"]:.0f}" height="{h:.0f}"><rect width="100%" height="100%" fill="#fff"/>'
            + "".join(rows) + "</svg>")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("markup")
    ap.add_argument("--culture", default="ar")
    ap.add_argument("--mode", choices=["cluster", "word"], default="cluster")
    ap.add_argument("--json")
    ap.add_argument("--svg")
    a = ap.parse_args()
    p = plan(a.markup, culture=a.culture, mode=a.mode)
    if p is None:
        print("non-Arabic culture: original Proto path, no plan")
        return
    if a.json:
        Path(a.json).write_text(json.dumps(to_json(p), ensure_ascii=False, indent=1), encoding="utf-8")
    if a.svg:
        Path(a.svg).write_text(svg(p), encoding="utf-8")
    print(f"lines={len(p['lines'])} glyphs={len(p['glyphs'])} units={len(p['units'])} "
          f"duration={max([d for d in p['due'] if d is not None] or [0]):.3f}s")


if __name__ == "__main__":
    sys.exit(main())
