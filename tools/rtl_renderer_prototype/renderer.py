"""Detached renderer contract: frozen visual layout + safe-unit mask, never game code.

Reuses the existing HarfBuzz/UBA layout transaction. Frame generation cannot shape,
wrap, truncate, sort glyphs by source index or advance a logical-order pen.
"""
import hashlib
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/rtl_reveal"))
import reveal as R


def arabic_language(language):
    return language.replace("_", "-").split("-")[0].lower() == "ar"


def utf16_boundaries(text):
    offsets = [0]
    for ch in text:
        offsets.append(offsets[-1] + len(ch.encode("utf-16-le")) // 2)
    return offsets


def markup_styles(markup):
    """Preserve style identifiers per logical codepoint; font metrics remain the old oracle's.

    This is not a complete Unreal markup parser. Unknown attributes remain outside
    this contract; native integration must retain its full parsed style/run data.
    """
    chars, styles, stack, pos = [], [], [], 0

    def emit(segment):
        style = next((s["style"] for s in reversed(stack) if "style" in s), "Default")
        chars.extend(segment)
        styles.extend([style] * len(segment))

    for match in R.TAG.finditer(markup):
        emit(markup[pos:match.start()])
        if match.group(1):
            if stack:
                stack.pop()
        else:
            stack.append(dict(R.ATTR.findall(match.group(3))))
        pos = match.end()
    emit(markup[pos:])
    return "".join(chars), styles


@dataclass(frozen=True)
class TimingTrace:
    """Adapter input: ready timestamp for each logical UTF-16 unit, None = exempt.

    Native classifier/donthide/EndHold semantics belong in the future adapter.
    The renderer must never guess those semantics from a glyph's visual order.
    """
    ready: tuple
    finish: float


def sample_trace(text, exempt=(), interval=0.025, end_hold=0.0):
    """Explicit fixture cadence, not a claim of exact shipped timing/event equivalence.

    Assumptions inherited from the previous model: newline and donthide do not
    consume time. First timed UTF-16 unit is due after interval, rather than t=0.
    """
    exempt, due, clock = set(exempt), [], 0.0
    for i, ch in enumerate(text):
        for _ in range(len(ch.encode("utf-16-le")) // 2):
            if i in exempt or ch in "\r\n":
                due.append(None)
            else:
                clock += interval
                due.append(round(clock, 9))
    return TimingTrace(tuple(due), round(clock + end_hold, 9))


@dataclass(frozen=True)
class Glyph:
    gid: int
    font: int
    start: int
    end: int
    utf16_start: int
    utf16_end: int
    line: int
    x: float
    y: float
    advance: float
    unit: int
    style: str


@dataclass(frozen=True)
class Scene:
    text: str
    glyphs: tuple
    lines: tuple
    units: tuple
    due: tuple
    trace: TimingTrace
    mode: str

    def geometry(self):
        return [(g.gid, g.font, g.start, g.end, g.line, g.x, g.y, g.advance, g.style)
                for g in self.glyphs]

    def fingerprint(self):
        payload = json.dumps([self.text, self.geometry(), self.lines], ensure_ascii=False,
                             separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def freeze_layout(lay, styles, mode="cluster", trace=None):
    """Consume an already-final layout. No shaping/layout operation occurs here."""
    if mode not in {"cluster", "word"}:
        raise ValueError("Unknown reveal mode")
    units = tuple(R.reveal_units(lay, mode))
    offsets = utf16_boundaries(lay["text"])
    trace = trace or sample_trace(lay["text"], lay["donthide"])
    trace = TimingTrace(tuple(trace.ready), trace.finish)
    if len(trace.ready) != offsets[-1]:
        raise ValueError("Timing trace must cover every UTF-16 source unit")
    valid = [t for t in trace.ready if t is not None]
    if any(not math.isfinite(t) or t < 0 for t in valid) or valid != sorted(valid):
        raise ValueError("Timing timestamps must be nonnegative and monotonic")
    if not math.isfinite(trace.finish) or trace.finish < max(valid, default=0):
        raise ValueError("Finish cannot precede the last native ready timestamp")
    owner = {i: u for u, (a, b) in enumerate(units) for i in range(a, b)}
    due = []
    for a, b in units:
        ts = [t for t in trace.ready[offsets[a]:offsets[b]] if t is not None]
        due.append(max(ts) if ts else None)
    glyphs = tuple(Glyph(g["gid"], g["font"], g["cluster"], g["cluster_end"],
                         offsets[g["cluster"]], offsets[g["cluster_end"]], g["line"],
                         g["x"], g["y"], g["adv"], owner[g["cluster"]], styles[g["cluster"]])
                   for g in lay["glyphs"])
    lines = tuple((l["start"], l["end"], l["width"]) for l in lay["lines"])
    return Scene(lay["text"], glyphs, lines, units, tuple(due), trace, mode)


def prepare(markup, language="ar", mode="cluster", **kw):
    if not arabic_language(language):
        return None  # Caller retains the original Proto objects and dispatch.
    lay = R.layout(markup, culture="ar", **kw)
    text, styles = markup_styles(markup)
    assert lay["text"] == text
    return freeze_layout(lay, styles, mode), lay


class RevealController:
    """One state/mask for foreground and shadow. Events are design-level equivalents."""
    def __init__(self, scene):
        self.scene = scene
        self.events = []
        self.StartReveal()

    def StartReveal(self):
        self.time = -1.0
        self.done = False
        self.mask = tuple(d is None for d in self.scene.due)
        self.events = [("start", 0.0)]

    def AdvanceRevealUnit(self, time):
        if not math.isfinite(time) or time < 0:
            raise ValueError("Reveal clock must be finite and nonnegative")
        if time < self.time:
            raise ValueError("Reveal clock moved backwards")
        self.time = time
        if self.done:
            return
        mask = tuple(d is None or d <= time for d in self.scene.due)
        if mask != self.mask:
            self.mask = mask
            self.events.append(("mask_changed", time))
        if all(mask) and time >= self.scene.trace.finish:
            self.CompleteReveal(time)

    def CompleteReveal(self, time=None):
        if self.done:
            return
        time = max(self.time, 0.0) if time is None else time
        if not all(self.mask):
            self.mask = (True,) * len(self.mask)
            self.events.append(("mask_changed", time))
        self.done = True
        self.events.append(("OnRevealFinished", time))

    def SkipToEnd(self):
        self.CompleteReveal()

    def draw_pass(self, offset=(0.0, 0.0)):
        """Same frozen glyph order/positions; the mask affects alpha only."""
        return [(i, g.x + offset[0], g.y + offset[1], float(self.mask[g.unit]), g.style)
                for i, g in enumerate(self.scene.glyphs)]


def proto_logical_pen_model(lay):
    """Comparison abstraction, NOT an emulator of shipped slicing/ligature failures.

    Generously retain all shaped glyphs, but assign cluster groups an ascending
    logical-source pen. Only this rejected comparator constructs logical-order x.
    """
    positions = [None] * len(lay["glyphs"])
    for line in range(len(lay["lines"])):
        ids = [i for i, g in enumerate(lay["glyphs"]) if g["line"] == line]
        pen = min((lay["glyphs"][i]["x"] - lay["glyphs"][i]["dx"] for i in ids), default=0)
        for source in sorted({lay["glyphs"][i]["cluster"] for i in ids}):
            group = [i for i in ids if lay["glyphs"][i]["cluster"] == source]
            origin = min(lay["glyphs"][i]["x"] - lay["glyphs"][i]["dx"] for i in group)
            for i in group:
                positions[i] = pen + lay["glyphs"][i]["x"] - origin
            pen += sum(lay["glyphs"][i]["adv"] for i in group)
    return positions


def assert_safe_alphas(scene, commands):
    by_cluster = {}
    for i, _, _, alpha, _ in commands:
        g = scene.glyphs[i]
        by_cluster.setdefault((g.start, g.end), set()).add(alpha)
    assert all(len(a) == 1 for a in by_cluster.values()), "partially visible shaping cluster"


def scene_json(scene):
    from dataclasses import asdict
    return asdict(scene)
