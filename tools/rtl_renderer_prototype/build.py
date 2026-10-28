"""Validate and emit detached frozen-layout comparisons. Never reads the game EXE.

python -X utf8 tools/rtl_renderer_prototype/build.py
"""
import hashlib
import json
import re
from copy import deepcopy
from pathlib import Path

import renderer as M
import word_timing as W

OUT = M.ROOT / "reports/rtl_research/renderer_repair/prototype"


def expect_failure(fn, exception=AssertionError):
    try:
        fn()
    except exception:
        return
    raise AssertionError("negative control failed to detect the defect")


def check(scene, lay):
    fingerprint = scene.fingerprint()
    ctrl = M.RevealController(scene)
    due_times = sorted({0.0, scene.trace.finish, *(d for d in scene.due if d is not None)})
    samples = sorted({max(0, d - 1e-7) for d in due_times} | set(due_times))
    boundaries = M.utf16_boundaries(scene.text)
    for glyph in scene.glyphs:
        a, b = scene.units[glyph.unit]
        assert a <= glyph.start and glyph.end <= b, "shaping range crosses reveal unit"
    # The renderer cannot reach HarfBuzz again after the final layout exists.
    real_shape = M.R.hb.shape

    def no_reshape(*args, **kwargs):
        raise AssertionError("shape called during reveal")

    M.R.hb.shape = no_reshape
    try:
        for t in samples:
            ctrl.AdvanceRevealUnit(t)
            foreground, shadow = ctrl.draw_pass(), ctrl.draw_pass((2.0, 3.0))
            M.assert_safe_alphas(scene, foreground)
            for a, b, g in zip(foreground, shadow, scene.glyphs):
                assert (a[1], a[2]) == (g.x, g.y), "glyph moved during reveal"
                assert abs(b[1] - a[1] - 2.0) < 1e-9
                assert abs(b[2] - a[2] - 3.0) < 1e-9
                assert a[3] == b[3], "shadow mask drift"
            assert scene.fingerprint() == fingerprint, "layout changed during reveal"
        assert ctrl.done
        assert sum(e[0] == "OnRevealFinished" for e in ctrl.events) == 1
        ctrl.SkipToEnd()
        ctrl.CompleteReveal()
        assert sum(e[0] == "OnRevealFinished" for e in ctrl.events) == 1
    finally:
        M.R.hb.shape = real_shape
    for u, (a, b) in enumerate(scene.units):
        native_due = [d for d in scene.trace.ready[boundaries[a]:boundaries[b]] if d is not None]
        assert scene.due[u] == (max(native_due) if native_due else None)
    if scene.mode == "word":
        for word in re.finditer(r"\S+", scene.text):
            covering = [u for u, (a, b) in enumerate(scene.units) if a < word.end() and b > word.start()]
            assert len(covering) == 1, "word was split between reveal units"
    # Reuse the earlier corpus's placement checks, without its POC timing schedule.
    correct, _, _ = W.bidi_report(lay, {})
    assert correct, "final-layout model failed mixed-BiDi placement oracle"
    return len(samples)


def comparison_svg(scene, lay, proto_x):
    """Outlined glyphs, no browser font shaping. All panels are synthetic."""
    from fontTools.pens.svgPathPen import SVGPathPen
    fonts = lay["_fonts"]
    lh = lay["line_height"]
    asc = max(f.ascender * lay["px"] / f.upem for f in fonts)
    panel_h = 36 + max(1, len(scene.lines)) * lh
    width = lay["wrap_at"]
    fractions = (0.0, 0.33, 0.66, 1.0)
    paths, svg = {}, []
    for fi, fraction in enumerate(fractions):
        for model in range(2):
            x0 = model * (width + 20)
            y0 = fi * panel_h
            name = "CORRECT_FINAL_LAYOUT_MODEL" if model == 0 else "PROTO_LOGICAL_PEN_MODEL (abstraction)"
            svg.append(f'<text x="{x0+4}" y="{y0+16}" font-size="12">{name} | t={fraction * scene.trace.finish:.3f}s | SYNTHETIC</text>')
            ctrl = M.RevealController(scene)
            ctrl.AdvanceRevealUnit(fraction * scene.trace.finish)
            for i, g in enumerate(scene.glyphs):
                if not ctrl.mask[g.unit]:
                    continue
                key = (g.font, g.gid)
                if key not in paths:
                    pen = SVGPathPen(None)
                    fonts[g.font].hb.draw_glyph_with_pen(g.gid, pen)
                    paths[key] = pen.getCommands()
                if not paths[key]:
                    continue
                x = g.x if model == 0 else proto_x[i]
                y = y0 + 30 + g.line * lh + asc - g.y
                k = lay["px"] / fonts[g.font].upem
                color = "#663399" if "Italic" in g.style else "#151515"
                # Same mask, two passes. This models shared shadow alpha, not RetainerBox blur.
                for dx, dy, fill, alpha in [(2, 3, "#808080", 0.5), (0, 0, color, 1)]:
                    svg.append(f'<path fill="{fill}" opacity="{alpha}" transform="translate({x0+x+dx:.3f},{y+dy:.3f}) scale({k:.6f},{-k:.6f})" d="{paths[key]}"/>')
    w, h = 2 * width + 20, len(fractions) * panel_h
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><rect width="100%" height="100%" fill="white"/>' + "".join(svg) + "</svg>"


def main():
    original_corpus = M.ROOT / "reports/rtl_research/word_reveal_model.json"
    cases = json.loads(original_corpus.read_text(encoding="utf-8-sig"))["cases"]
    assert len(cases) == 14
    wrappers = {
        "bare": lambda t: f'<text style="Default">{t}</>',
        "speaker": lambda t: f'<text style="Default" donthide="true">روبرت: </><text style="Default">{t}</>',
        "rich": lambda t: f'<text style="Default">قال </><text style="Italic">{t}</><text style="Default"> نعم</>',
    }
    fonts = [M.R.Font(p) for p in M.R.DEFAULT_FONTS]
    output, count, proto_bad, total_frames = [], 0, 0, 0
    OUT.mkdir(parents=True, exist_ok=True)
    for case in cases:
        for wrapper, wrap in wrappers.items():
            markup = wrap(case["text"])
            _, lay = M.prepare(markup, fonts=fonts)
            text, styles = M.markup_styles(markup)
            assert text == lay["text"]
            px = M.proto_logical_pen_model(lay)
            rejected = deepcopy({k: v for k, v in lay.items() if k != "_fonts"})
            for g, x in zip(rejected["glyphs"], px):
                g["x"] = x
            proto_ok, _, _ = W.bidi_report(rejected, {})
            proto_bad += not proto_ok
            count += 1
            for mode in ("cluster", "word"):
                scene = M.freeze_layout(lay, styles, mode)
                total_frames += check(scene, lay)
                record = {"id": case["id"] + "/" + wrapper + "/" + mode,
                          "CORRECT_FINAL_LAYOUT_MODEL": M.scene_json(scene),
                          "PROTO_LOGICAL_PEN_MODEL": {"glyph_x": px, "placement_check": proto_ok,
                                                       "exact_binary_emulator": False},
                          "geometry_sha256": scene.fingerprint(),
                          "sample_masks": []}
                for f in (0, 0.25, 0.5, 0.75, 1):
                    c = M.RevealController(scene)
                    c.AdvanceRevealUnit(f * scene.trace.finish)
                    record["sample_masks"].append({"t": f * scene.trace.finish, "visible_units": c.mask})
                output.append(record)
                if wrapper == "bare" and mode == "word" and case["id"] in {"lam_alef_marks", "latin_digits", "long_wrap", "punctuation"}:
                    (OUT / (case["id"] + ".svg")).write_text(comparison_svg(scene, lay, px), encoding="utf-8")

    assert proto_bad == count, "negative placement control no longer distinguishes models"
    # Culture gate cannot depend on Arabic letters in a line, or on punctuation/branding.
    for language in ("en", "en-US", "fr", "ara"):
        assert M.prepare("مرحبا Dispatch", language=language, fonts=fonts) is None
    assert M.prepare("Dispatch 250 XP", language="AR_sa", fonts=fonts) is not None
    # Non-BMP text validates UTF-16 mapping; the emoji is exempt from visual-fidelity assertions.
    scene, lay = M.prepare("<text>لا 𝟚 مُ</>", fonts=fonts)
    offsets = M.utf16_boundaries(scene.text)
    assert offsets[-1] == len(scene.text.encode("utf-16-le")) // 2
    assert offsets[-1] > len(scene.text)
    for g in scene.glyphs:
        assert g.utf16_start == offsets[g.start] and g.utf16_end == offsets[g.end]
    # Explicit timing trace: zero-delay batching plus a positive gap, no DataTable retuning.
    timed_scene, _ = M.prepare("<text>لا لا</>", fonts=fonts)
    trace = M.TimingTrace((0.0, 0.0, 0.1, 0.1, 0.1), 0.2)
    timed_scene = M.freeze_layout(M.R.layout("<text>لا لا</>", fonts=fonts), ["Default"] * 5, trace=trace)
    c = M.RevealController(timed_scene)
    c.AdvanceRevealUnit(0.0)
    assert sum(c.mask) == 1 and not c.done
    c.AdvanceRevealUnit(0.1)
    assert all(c.mask) and not c.done
    c.AdvanceRevealUnit(0.2)
    assert c.done and sum(e[0] == "OnRevealFinished" for e in c.events) == 1
    c.StartReveal()
    c.SkipToEnd()
    c.SkipToEnd()
    assert all(c.mask) and sum(e[0] == "OnRevealFinished" for e in c.events) == 1
    expect_failure(lambda: c.AdvanceRevealUnit(float("nan")), ValueError)
    expect_failure(lambda: M.freeze_layout(lay, ["Default"] * len(lay["text"]), trace=M.TimingTrace((), 0)), ValueError)
    expect_failure(lambda: M.freeze_layout(lay, ["Default"] * len(lay["text"]), mode="utf16"), ValueError)
    expect_failure(lambda: M.freeze_layout(lay, ["Default"] * len(lay["text"]),
                                          trace=M.TimingTrace((float("nan"),) * offsets[-1], 1)), ValueError)
    # A split-alpha mutation must be detected for a multi-glyph marked cluster.
    marked, _ = M.prepare("<text>مُهِمّ</>", fonts=fonts)
    c = M.RevealController(marked)
    c.SkipToEnd()
    commands = c.draw_pass()
    groups = {}
    for i, g in enumerate(marked.glyphs):
        groups.setdefault((g.start, g.end), []).append(i)
    multi = next(ids for ids in groups.values() if len(ids) > 1)
    i = multi[0]
    commands[i] = (*commands[i][:3], 0.0, commands[i][4])
    expect_failure(lambda: M.assert_safe_alphas(marked, commands))
    # Long wrapping and explicit newline are actually represented in the outputs.
    assert any(len(x["CORRECT_FINAL_LAYOUT_MODEL"]["lines"]) > 1 and x["id"].startswith("long_wrap/") for x in output)
    assert any("\n" in x["CORRECT_FINAL_LAYOUT_MODEL"]["text"] for x in output)
    summary = {
        "result": "RENDERER_REPAIR_PROTOTYPE_BUILT", "prototype_kind": "detached Python/SVG, NOT Unreal",
        "corpus_texts": len(cases), "wrappers": 3, "placement_cases": count,
        "cluster_and_word_plans": len(output), "reveal_frames_checked": total_frames,
        "correct_model_bidi_failures": 0, "proto_model_bidi_failures": proto_bad,
        "shaping_cluster_splits": 0, "position_or_wrap_drift": 0, "shadow_mask_drift": 0,
        "reshape_calls_during_reveal": 0, "negative_controls_passed": True,
        "source_corpus_sha256": hashlib.sha256(original_corpus.read_bytes()).hexdigest(),
        "native_build": "NOT_BUILT_NO_DISCOVERED_UE427_TOOLCHAIN",
        "arabic_branch": "ARABIC_BRANCH_REQUIRES_NATIVE_INTEGRATION",
        "arabic_isolation": "ARABIC_ISOLATION_NOT_PROVEN", "tested_in_game": 0, "final": 0,
        "limitations": ["Same prior simplified whitespace wrapping and per-codepoint font fallback",
                        "UBA via python-bidi/unicode-bidi; not ICU and not Slate parity",
                        "Style IDs retained; italic/outline/size metrics and font materials are not modeled",
                        "Sample timing trace has explicit donthide/newline assumptions; native timing adapter unbuilt",
                        "Proto comparator preserves clusters generously; not an exact executable emulator",
                        "No native atlas resource lifetime/material/retainer integration verified"],
    }
    for name, value in [("comparison.json", output), ("validation.json", summary)]:
        (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    import pymupdf
    for name in ("latin_digits", "lam_alef_marks", "long_wrap", "punctuation"):
        with pymupdf.open(OUT / (name + ".svg")) as doc:
            doc[0].get_pixmap(alpha=False).save(OUT / (name + ".png"))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
