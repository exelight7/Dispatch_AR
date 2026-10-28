"""Static Arabic font readiness: block coverage, corpus coverage, full-corpus shaping and metric clipping risk.

python -X utf8 tools/font_analysis/coverage.py
Writes reports/fonts/font_coverage.json. Uses installed fontTools + uharfbuzz on the extracted font copies.
Static only: Slate fallback selection, atlas rendering and real clipping need the game or a UE4.27 editor.
"""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import unicodedata

from fontTools.ttLib import TTFont
import uharfbuzz as hb

ROOT = Path(__file__).resolve().parents[2]
EX = ROOT / "extracted"
OUT = ROOT / "reports/fonts/font_coverage.json"

LATIN = "Dispatch/Content/Shared/UI/Fonts/Montserrat/static/Montserrat-Medium.ufont"
LATIN_ITALIC = "Dispatch/Content/Shared/UI/Fonts/Montserrat/static/Montserrat-MediumItalic.ufont"
NOTO_SANS = "Dispatch/Content/Shared/UI/Fonts/NotoSans/NotoSans-Medium.ufont"
NASKH = "Engine/Content/Slate/Fonts/NotoNaskhArabicUI-Regular.ttf"
CANDIDATES = [LATIN, LATIN_ITALIC, NOTO_SANS, NASKH,
              "Dispatch/Content/Shared/Shifts/Art/Fonts/Aktiv_Grotesk.ufont",
              "Engine/Content/Slate/Fonts/Roboto-Regular.ttf", "Engine/Content/Slate/Fonts/DroidSansFallback.ttf"]
# Proposed chain: the game's subtitle composite (Montserrat Medium default, NotoSans fallback typeface)
# followed by the engine's shipped Slate fallback face for Arabic.
CHAIN = [LATIN, NOTO_SANS, NASKH]
BLOCKS = {
    "Arabic Basic (U+0600-06FF)": (0x0600, 0x06FF),
    "Arabic Supplement (U+0750-077F)": (0x0750, 0x077F),
    "Arabic Extended-A (U+08A0-08FF)": (0x08A0, 0x08FF),
    "Arabic Presentation Forms-A (U+FB50-FDFF)": (0xFB50, 0xFDFF),
    "Arabic Presentation Forms-B (U+FE70-FEFF)": (0xFE70, 0xFEFF),
}
# Codepoints the localization actually needs from the Arabic block (letters, marks, punctuation, digits).
REQUIRED = {
    "arabic_letters": [c for c in range(0x0621, 0x064B) if unicodedata.category(chr(c)) == "Lo"],
    "arabic_combining_marks": list(range(0x064B, 0x0653)) + [0x0670],
    "arabic_punctuation": [0x060C, 0x061B, 0x061F, 0x066A, 0x066B, 0x066C, 0x06D4],
    "arabic_indic_digits": list(range(0x0660, 0x066A)),
    "latin_basic": list(range(0x20, 0x7F)),
    "western_digits": list(range(0x30, 0x3A)),
    "general_punctuation": [0x2013, 0x2014, 0x2018, 0x2019, 0x201C, 0x201D, 0x2022, 0x2026, 0x00AB, 0x00BB, 0x00B0],
}


def load(rel):
    font = TTFont(EX / rel, lazy=True)
    return font, set((font.getBestCmap() or {}).keys())


def corpus():
    texts = []
    for path in sorted((ROOT / "translation/arabic").glob("*.json")):
        texts.extend(json.loads(path.read_text(encoding="utf-8")).values())
    return texts


def runs(text):
    """Split into maximal Arabic / non-Arabic runs (Slate shapes per font face; Arabic goes to the Arabic face)."""
    out, cur, kind = [], "", None
    for ch in text:
        k = "ar" if 0x0600 <= ord(ch) <= 0x06FF or 0x0750 <= ord(ch) <= 0x077F else "other"
        if unicodedata.category(ch).startswith("M") and kind:
            k = kind  # marks stay with their base
        if k != kind and cur:
            out.append((kind, cur))
            cur = ""
        cur, kind = cur + ch, k
    if cur:
        out.append((kind, cur))
    return out


def main():
    fonts = {rel: load(rel) for rel in CANDIDATES}
    texts = corpus()
    used = Counter(ord(c) for t in texts for c in t)
    arabic_used = sorted(c for c in used if 0x0600 <= c <= 0x06FF or 0x0750 <= c <= 0x08FF)
    report = {"corpus_records": len(texts), "corpus_distinct_codepoints": len(used),
              "corpus_arabic_codepoints": [f"U+{c:04X}" for c in arabic_used], "fonts": {}, "chain": CHAIN}
    for rel, (font, cmap) in fonts.items():
        head, hhea, os2 = font["head"], font["hhea"], font["OS/2"] if "OS/2" in font else None
        gsub = sorted({r.ScriptTag for r in font["GSUB"].table.ScriptList.ScriptRecord}) if "GSUB" in font else []
        gpos = sorted({r.ScriptTag for r in font["GPOS"].table.ScriptList.ScriptRecord}) if "GPOS" in font else []
        report["fonts"][rel] = {
            "family": font["name"].getDebugName(1), "style": font["name"].getDebugName(2),
            "units_per_em": head.unitsPerEm, "hhea_ascent": hhea.ascent, "hhea_descent": hhea.descent,
            "hhea_line_gap": hhea.lineGap,
            "win_ascent": getattr(os2, "usWinAscent", None), "win_descent": getattr(os2, "usWinDescent", None),
            "gsub_scripts": gsub, "gpos_scripts": gpos,
            "blocks": {name: sum(lo <= c <= hi for c in cmap) for name, (lo, hi) in BLOCKS.items()},
            "required": {k: {"covered": sum(c in cmap for c in v), "total": len(v),
                             "missing": [f"U+{c:04X}" for c in v if c not in cmap]} for k, v in REQUIRED.items()},
            "corpus_missing": [f"U+{c:04X}" for c in sorted(used) if c not in cmap and c >= 0x20],
        }
    chain_cmaps = [fonts[r][1] for r in CHAIN]
    missing_chain = [c for c in sorted(used) if c >= 0x20 and not any(c in m for m in chain_cmaps)]
    report["chain_missing_glyphs"] = [f"U+{c:04X} {unicodedata.name(chr(c), '?')}" for c in missing_chain]
    report["corpus_presentation_forms"] = sum(n for c, n in used.items() if 0xFB50 <= c <= 0xFDFF or 0xFE70 <= c <= 0xFEFF)

    # Shape every Arabic run of every record with the Arabic face; any .notdef (gid 0) is a failure.
    blob = hb.Blob.from_file_path(str(EX / NASKH))
    face = hb.Face(blob)
    hbfont = hb.Font(face)
    upem = face.upem
    naskh = fonts[NASKH][0]
    glyf = naskh["glyf"] if "glyf" in naskh else None
    order = naskh.getGlyphOrder()
    notdef, shaped_runs, lam_alef = 0, 0, Counter()
    ink_top, ink_bottom = 0, 0
    for text in texts:
        for kind, run in runs(text):
            if kind != "ar":
                continue
            buf = hb.Buffer()
            buf.add_str(run)
            buf.guess_segment_properties()
            hb.shape(hbfont, buf, {})
            shaped_runs += 1
            for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
                if info.codepoint == 0:
                    notdef += 1
                    continue
                if glyf is not None:
                    g = glyf[order[info.codepoint]]
                    if hasattr(g, "yMax") and g.numberOfContours:
                        ink_top = max(ink_top, g.yMax + pos.y_offset)
                        ink_bottom = min(ink_bottom, g.yMin + pos.y_offset)
            if "لا" in run or "لأ" in run or "لإ" in run or "لآ" in run:
                # lam-alef must shape to fewer glyphs than input characters (ligature).
                probe = hb.Buffer()
                probe.add_str("لا")
                probe.guess_segment_properties()
                hb.shape(hbfont, probe, {})
                lam_alef[len(probe.glyph_infos)] += 1
    latin = fonts[LATIN][0]
    l_upem, l_asc, l_desc = latin["head"].unitsPerEm, latin["hhea"].ascent, latin["hhea"].descent
    styles = {}
    for name, size, outline in [("Default", 28, 0), ("Default_Outline", 28, 2), ("Large table", 32, 0),
                                ("Large table outline", 32, 2), ("Default_Large", 36, 0), ("Default_Outline_Large", 36, 2)]:
        px = size * 96 / 72  # Slate font size is in points at 96 DPI
        line_top = l_asc / l_upem * px
        line_bottom = -l_desc / l_upem * px
        arab_top = ink_top / upem * px + outline
        arab_bottom = -ink_bottom / upem * px + outline
        naskh_line_top = naskh["hhea"].ascent / upem * px
        naskh_line_bottom = -naskh["hhea"].descent / upem * px
        over_top = round(arab_top - max(line_top, naskh_line_top), 2)
        over_bottom = round(arab_bottom - max(line_bottom, naskh_line_bottom), 2)
        styles[name] = {"size_pt": size, "px": round(px, 2), "outline_px": outline,
                        "montserrat_line_ascent_px": round(line_top, 2), "montserrat_line_descent_px": round(line_bottom, 2),
                        "naskh_line_ascent_px": round(naskh_line_top, 2), "naskh_line_descent_px": round(naskh_line_bottom, 2),
                        "arabic_ink_top_px": round(arab_top, 2), "arabic_ink_bottom_px": round(arab_bottom, 2),
                        "ink_over_line_box_top_px": over_top, "ink_over_line_box_bottom_px": over_bottom,
                        "classification": "STATIC_RISK_FOUND" if max(over_top, over_bottom) > 2 else "STATIC_LOW_RISK"}
    report["shaping"] = {"face": NASKH, "arabic_runs_shaped": shaped_runs, "notdef_glyphs": notdef,
                         "lam_alef_probe_glyph_count": dict(lam_alef),
                         "max_ink_top_units": ink_top, "max_ink_bottom_units": ink_bottom, "upem": upem}
    report["clipping"] = styles
    report["limits"] = ["Static font data only; Slate's composite fallback choice is not executed here.",
                        "Ink extents use shaped glyph outlines with mark offsets; Slate atlas padding and RetainerBox bounds are not modeled.",
                        "Italic subtitle rows have no Arabic italic face; Slate will not synthesize one."]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    assert report["corpus_presentation_forms"] == 0, "Presentation forms found in translated text"
    print(json.dumps({"chain_missing_glyphs": report["chain_missing_glyphs"], "shaping": report["shaping"],
                      "clipping": {k: v["classification"] for k, v in styles.items()}}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
