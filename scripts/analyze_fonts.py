"""Inspect bundled font cmap, shaping tables and metrics without changing fonts."""
import json
from pathlib import Path
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
cases = json.loads((ROOT / "tests/rtl_cases.json").read_text(encoding="utf-8"))
needed = {ord(c) for case in cases for c in case["text"] if 0x600 <= ord(c) <= 0x6ff}
results = []
for path in sorted((ROOT / "extracted").rglob("*")):
    if path.suffix.lower() not in (".ufont", ".ttf", ".otf"):
        continue
    record = {"file": path.relative_to(ROOT / "extracted").as_posix()}
    try:
        with TTFont(path) as font:
            cmap = font.getBestCmap() or {}
            record.update(arabic_cmap=sum(0x600 <= c <= 0x6ff for c in cmap),
                presentation_forms=sum(0xfb50 <= c <= 0xfdff or 0xfe70 <= c <= 0xfeff for c in cmap),
                latin_cmap=sum(0x20 <= c <= 0x7e for c in cmap),
                has_GSUB="GSUB" in font, has_GPOS="GPOS" in font,
                units_per_em=font["head"].unitsPerEm,
                ascender=font["hhea"].ascent, descender=font["hhea"].descent,
                missing_probe_arabic=[f"U+{c:04X}" for c in sorted(needed - cmap.keys())])
            record["shaping_scripts"] = {tag: [r.ScriptTag for r in font[tag].table.ScriptList.ScriptRecord]
                for tag in ("GSUB", "GPOS") if tag in font and font[tag].table.ScriptList}
            record["family"] = font["name"].getDebugName(1)
    except Exception as error:
        record["error"] = str(error)
    results.append(record)
assert results and needed, "No fonts or Arabic probe characters found"
(ROOT / "reports/font_coverage.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
print(f"Inspected {len(results)} fonts; {sum(r.get('arabic_cmap', 0) > 0 for r in results)} have Arabic cmap entries")
print("Static coverage is not proof of fallback selection, clipping, shaping or animation in-game")
