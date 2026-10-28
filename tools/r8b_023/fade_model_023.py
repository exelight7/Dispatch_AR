"""Round 023: offline design proof for a smooth per-word fade in the R8b Arabic reveal. Design only; never runs or touches the game.

Proposed change (nothing emitted, nothing installed):
  - unchanged: Build Arabic Markup/Timing, units, rows (row B = 10.5^-i), K2_SetTimer -> Arabic Clock Fired -> Advance Budget,
    integer Set Threshold Arabic (it additionally records ArabicFadeBase and ArabicLastBlue).
  - new "Arabic Fade Tick", called from the existing Blueprint Tick after Arabic Paused Clock (architecture A):
        E     = Due[T+1] - ArabicClockRemainder + (Now - ArabicClockStamp)       time since unit T+1 started
        alpha = FClamp((E - 0.025) / (Due[T+1] - 0.025), 0, 1)                    0 at its first native letter, 1 at its last
        Blue  = ArabicFadeBase * (1 + 9.4 * alpha)                                 FadeBase = 10.5^T (1/10.5 for T = -1)
        if Blue != ArabicLastBlue: both Border tints (1,1,Blue,1) + RequestRender on both shadow retainers
    alpha = 0 gives exactly integer T; alpha = 1 gives sRGB code 254 (opacity 0.989), so the last 1% and full opacity
    arrive only with the timer (integer T+1) at the native last-letter frame. Units <= T stay full, units >= T+2 stay hidden.
Every Kismet op is float32. Vertex colour = FLinearColor.ToFColor(sRGB) (4.27), decoded exactly in the shipped VS
(round 008), then opacity = sat((B - 0.1) * 1.11). A linear-8-bit variant is replayed too, as a robustness check.

usage: python -X utf8 -I tools/r8b_023/fade_model_023.py <project> <out.json>
"""
import glob
import json
import random
import statistics
import sys
from collections import Counter
from pathlib import Path

import numpy as np

ROOT, OUT = Path(sys.argv[1]), Path(sys.argv[2])
sys.path.insert(0, str(ROOT / "tools/asset_inspector"))
import test_clock as tc   # binds clock_model_012 (cross-checked against the installed bytecode in round 022) and segment_units

model, ref = tc.model, tc.reference
f32 = np.float32
DT, LETTER, SLOPE = 1 / 60, f32(0.025), f32(9.4)
POW = [f32(10.5 ** i) for i in range(37)]            # Set Threshold Arabic constants: (float)Math.Pow(10.5, i)
ROW_B = np.array([f32(10.5 ** -i) for i in range(37)], dtype=np.float32)   # DT_AR u0..u36 colour B
FADE_BASE_NEG = f32(1 / 10.5)

recs = [r for p in sorted(glob.glob(str(ROOT / "translation/records/*.json"))) for r in json.load(open(p, encoding="utf-8"))]
subs = [s for s in (r["ar"].replace("<Italic>", "").replace("</>", "") for r in recs if r["category"] == "Dialogue/Subtitles")
        if ref.letters(s) > 0]


# ---- quantization: FLinearColor::ToFColor (4.27) -> exact decode in the VS -> M_SubtitlePrinting opacity ----
def to_code(lin, srgb=True):
    lin = np.clip(np.asarray(lin, dtype=np.float32), 0, 1)
    if srgb:
        lin = np.where(lin <= f32(0.0031308), lin * f32(12.92), np.power(lin, f32(1 / 2.4)) * f32(1.055) - f32(0.055))
    return np.floor(lin.astype(np.float32) * f32(255.999)).astype(np.int32)

_s = np.arange(256) / 255
DECODE = {True: np.where(_s <= 0.04045, _s / 12.92, ((_s + 0.055) / 1.055) ** 2.4), False: _s}
OPACITY = {k: np.clip((v - 0.1) * 1.11, 0, 1) for k, v in DECODE.items()}
FULL = {k: v[255] for k, v in OPACITY.items()}


def unit_opacity(blue, n, srgb=True):
    return OPACITY[srgb][to_code(ROW_B[:n] * f32(blue), srgb)]


# ---- the proposed Blueprint state + functions (float32, same op order as the planned bytecode) ----
class Block:
    def __init__(self, world, delays, awp=False):
        self.ar = model.Arabic(world, delays, awp)
        self.w, self.n, self.awp = world, len(delays), awp
        self.base, self.last, self.blue = f32(0), f32(-1), f32(0)
        self.effects = Counter(); self.fade_writes = 0

    def set_threshold(self, t):                  # existing Set Threshold Arabic + two recorded values
        blue = f32(0) if t < 0 else POW[min(t, 36)]
        self.base = FADE_BASE_NEG if t < 0 else blue
        self.write(blue)

    def write(self, blue):
        self.blue = self.last = blue
        self.effects["SetContentColorAndOpacity"] += 2; self.effects["RequestRender"] += 2

    def fade_tick(self):                         # new Arabic Fade Tick (Blueprint Tick, after Arabic Paused Clock)
        ar = self.ar
        if not (ar.active and ar.armed and not ar.finished) or not ar.rem >= 0 or not ar.cur + 1 < self.n:
            return None
        due = ar.d[ar.cur + 1]
        now = self.w.unpaused if self.awp else self.w.time
        e = f32(f32(due - ar.rem) + f32(now - ar.stamp))
        span = f32(due - LETTER)
        alpha = f32(min(max(f32(f32(e - LETTER) / span), f32(0)), f32(1))) if span >= f32(0.001) else f32(0)
        blue = f32(self.base * f32(f32(1) + f32(SLOPE * alpha)))
        if not (blue >= self.last and self.last >= blue):
            self.write(blue); self.fade_writes += 1
        return alpha


def drive(blk, frames_cb, dt_fn=lambda f: DT, events=None, max_frames=20000):
    """World tick (timer -> Clock Fired -> Advance -> Step -> Set Threshold) then Slate (Tick -> Fade Tick -> paint)."""
    ar, w, prev, f, events = blk.ar, blk.w, -2, 0, events or {}
    ar.frame = 0; blk.set_threshold(-1); ar.begin(0)
    if ar.cur != prev: blk.set_threshold(ar.cur) if ar.cur >= 0 else None; prev = ar.cur
    if ar.finished: blk.set_threshold(blk.n - 1)
    alpha = blk.fade_tick(); frames_cb(0, ar.cur, alpha)
    while f < max_frames:
        f += 1; ar.frame = f
        paused = events.get("paused", lambda f: False)(f)
        w.tick(dt_fn(f), paused, 1.0)
        if ar.cur != prev and ar.cur >= 0: blk.set_threshold(ar.cur); prev = ar.cur
        if f in events.get("skip", ()): ar.finish_(True); blk.set_threshold(blk.n - 1)
        if f in events.get("cancel", ()): ar.cancel(); blk.set_threshold(-1)
        if ar.awp: ar.slate_tick()
        if ar.cur != prev and ar.cur >= 0: blk.set_threshold(ar.cur); prev = ar.cur
        alpha = blk.fade_tick(); frames_cb(f, ar.cur, alpha)
        if (ar.finished or not ar.active) and f > max(ar.reveal.values(), default=0) + 2:
            return f


def native_frames(n_letters):
    w = model.World(); nat = model.NativeProto(w, [0.025] * n_letters + [0.025], False); nat.frame = 0; nat.start(0); f = 0
    while not nat.finish and f < 20000:
        f += 1; nat.frame = f; w.tick(DT, False, 1.0)
    return [nat.reveal[i] for i in range(n_letters)]


def replay_line(s, keep=False, srgb_both=True):
    _, n, _, d = ref.build_markup(s, "")
    lw = [round(x / 0.025) for x in d]
    blk = Block(model.World(), d)
    rows, op_prev, checks = [], None, Counter()
    lin_prev = None
    state = {"T": -2, "V": -2.0}

    def cb(f, t, alpha):
        op = unit_opacity(blk.blue, n)
        nonlocal op_prev, lin_prev
        v = t + (float(alpha) if alpha is not None else 0.0)
        checks["threshold_regress"] += t < state["T"] or v < state["V"] - 1e-9
        state["T"], state["V"] = t, max(v, state["V"])
        checks["revealed_not_full"] += int(np.any(op[:t + 1] < FULL[True]))
        checks["ghost_T2"] += int(np.any(op[t + 2:] > 0))
        if op_prev is not None:
            checks["opacity_regress"] += int(np.any(op < op_prev - 1e-12))
            checks["changed_frames"] += int(np.any(op != op_prev))
        if srgb_both:
            ol = unit_opacity(blk.blue, n, srgb=False)
            checks["lin8_ghost_T2"] += int(np.any(ol[t + 2:] > 0)); checks["lin8_revealed_not_full"] += int(np.any(ol[:t + 1] < FULL[False]))
            if lin_prev is not None:
                checks["lin8_opacity_regress"] += int(np.any(ol < lin_prev - 1e-12)); checks["lin8_changed_frames"] += int(np.any(ol != lin_prev))
            lin_prev = ol
        if checks["complete"] == 0 and np.all(op >= FULL[True]):
            checks["complete"] = f + 1   # stored +1 so frame 0 is truthy
        op_prev = op
        if keep:
            k = t + 1
            rows.append({"frame": f, "threshold_T": t, "fading_unit": k if k < n else None,
                         "alpha": None if alpha is None else round(float(alpha), 4), "tint_B": float(blk.blue),
                         "fading_unit_opacity": round(float(op[k]), 4) if k < n else None})

    drive(blk, cb)
    assert blk.effects.keys() <= {"SetContentColorAndOpacity", "RequestRender"}
    return n, d, lw, blk, rows, checks


def events(frames, weights=None):
    ev = Counter()
    for i, f in enumerate(frames):
        ev[f] += weights[i] if weights else 1
    return ev


# ---------------- 1) quantization proof over the whole threshold domain ----------------
alphas = np.linspace(0, 1, 20001, dtype=np.float32)
quant = {}
for srgb in (True, False):
    worst_ghost = worst_full = 0.0; levels = set(); mono = True
    for t in range(-1, 36):
        base = FADE_BASE_NEG if t < 0 else POW[t]
        blues = (base * (f32(1) + SLOPE * alphas)).astype(np.float32)
        nxt = OPACITY[srgb][to_code(ROW_B[t + 1] * blues, srgb)]
        mono &= bool(np.all(np.diff(nxt) >= 0))
        levels |= set(np.round(nxt, 6).tolist())
        if t + 2 < 37: worst_ghost = max(worst_ghost, float(OPACITY[srgb][to_code(ROW_B[t + 2] * blues, srgb)].max()))
        if t >= 0: worst_full = max(worst_full, float(FULL[srgb] - OPACITY[srgb][to_code(ROW_B[:t + 1, None] * blues, srgb)].min()))
        assert nxt[0] == 0 and 0.98 < nxt[-1] < FULL[srgb], (srgb, t, nxt[0], nxt[-1])
        top = float(nxt[-1])
    lv = sorted(levels)
    quant["srgb8" if srgb else "linear8"] = {"next_unit_monotone_all_T": mono, "distinct_opacity_levels": len(lv),
                                             "max_level_step": round(max(b - a for a, b in zip(lv, lv[1:])), 4),
                                             "unit_T2_max_opacity": worst_ghost, "revealed_units_max_deficit": worst_full,
                                             "alpha0_equals_integer_T": True, "alpha1_opacity_below_full": top}
    assert mono and worst_ghost == 0 and worst_full == 0
quant["opacity_at_alpha"] = {str(a): round(float(OPACITY[True][to_code(ROW_B[1] * f32(1 + 9.4 * a))]), 3) for a in (0, .1, .25, .5, .75, .9, 1)}
quant["float32_range"] = {"max_tint_B": float(POW[35] * f32(10.5)), "min_row_B": float(ROW_B[36]), "float32_max": float(np.finfo(np.float32).max),
                          "float32_min_normal": float(np.finfo(np.float32).tiny)}
# supervisor variant tint B = 10.5^(T+f) (needs MultiplyMultiply_FloatFloat): same endpoints, convex ramp
quant["pow_variant_opacity_at_f"] = {str(a): round(float(OPACITY[True][to_code(ROW_B[1] * f32(10.5 ** a))]), 3) for a in (0, .1, .25, .5, .75, .9, 1)}

# ---------------- 2) all subtitles ----------------
tot = Counter(); total_frames = 0; end_diff = Counter(); end_diff_cur = Counter(); over = []; per_line_share = []
nat_changes = cur_changes = 0
for s in subs:
    n, d, lw, blk, _, ck = replay_line(s)
    nf = native_frames(sum(lw)); uf = [blk.ar.reveal[i] for i in range(n)]
    complete = ck["complete"] - 1
    frames = max(nf[-1], uf[-1], complete) + 1
    total_frames += frames
    tot.update({k: v for k, v in ck.items() if k != "complete"})
    nat_changes += len(events(nf)); cur_changes += len(events(uf))
    end_diff[complete - nf[-1]] += 1; end_diff_cur[uf[-1] - nf[-1]] += 1
    per_line_share.append(ck["changed_frames"] / frames)
    _, units = ref.units_of(s)
    if len(units) > 37:
        over.append({"text_chars": len(s), "raw_units": len(units), "tail_letters": lw[-1], "tail_fade_frames": round((lw[-1] - 1) * 1.5, 1),
                     "line_share_changed": round(ck["changed_frames"] / frames, 3), "complete_minus_native": complete - nf[-1]})

replay = {
    "lines": len(subs), "frames": total_frames,
    "visible_change_share": {"native_proto": round(nat_changes / total_frames, 4), "current_r8b": round(cur_changes / total_frames, 4),
                             "proposed_fade_srgb8": round(tot["changed_frames"] / total_frames, 4),
                             "proposed_fade_linear8": round(tot["lin8_changed_frames"] / total_frames, 4)},
    "visible_changes_per_second": {"native_proto": round(nat_changes / (total_frames * DT), 2), "current_r8b": round(cur_changes / (total_frames * DT), 2),
                                   "proposed_fade_srgb8": round(tot["changed_frames"] / (total_frames * DT), 2)},
    "line_share_p10": round(sorted(per_line_share)[len(per_line_share) // 10], 3),
    "completion_frame_minus_native": {"proposed": dict(sorted(end_diff.items())), "current_r8b": dict(sorted(end_diff_cur.items()))},
    "violations": {k: tot[k] for k in ("threshold_regress", "opacity_regress", "ghost_T2", "revealed_not_full",
                                         "lin8_opacity_regress", "lin8_ghost_T2", "lin8_revealed_not_full")},
    "overflow_lines": {"count": len(over), "lines": over},
}
assert all(v == 0 for v in replay["violations"].values()), replay["violations"]
assert set(end_diff) <= {-1, 0, 1}, end_diff

# ---------------- 3) lifecycle: variable fps, pause/resume, skip, cancel + pool reuse, animation off, AWP=true ----------------
rng = random.Random(23); life = Counter()
for i in range(3000):
    s = rng.choice(subs); _, n, _, d = ref.build_markup(s, "")
    awp = i % 5 == 0
    blk = Block(model.World(), d, awp)
    for _ in range(rng.randint(0, 50)): blk.w.tick(rng.uniform(1 / 144, 1 / 20), False, 1.0)
    pause_on, pause_len = rng.randint(1, 60), rng.randint(5, 90)
    skip = {rng.randint(1, 120)} if rng.random() < 0.3 else set()
    cancel = {rng.randint(1, 120)} if rng.random() < 0.2 else set()
    if rng.random() < 0.1: skip = {0}   # animation disabled == Arabic Finish(True) before the first frame
    seen = {"V": -9.0, "op": None, "dead": False, "writes_after_end": 0}
    def cb(f, t, alpha, blk=blk, seen=seen, skip=skip):
        op = unit_opacity(blk.blue, blk.n)
        if seen["dead"] and blk.fade_writes != seen["eff"]: seen["writes_after_end"] += 1
        if not blk.ar.active and not seen["dead"]: seen["dead"], seen["eff"] = True, blk.fade_writes
        if blk.ar.active:
            v = t + (float(alpha) if alpha is not None else 0)
            life["regress"] += v < seen["V"] - 1e-9; seen["V"] = max(seen["V"], v)
            life["ghost"] += int(np.any(op[t + 2:] > 0))
            if seen["op"] is not None: life["opacity_regress"] += int(np.any(op < seen["op"] - 1e-12))
        if blk.ar.finished and blk.ar.finish and blk.ar.finish[0][1]:
            life["skip_frames"] += 1; life["skip_not_full"] += int(np.any(op < FULL[True]))
        seen["op"] = op
    if 0 in skip:
        blk.set_threshold(-1); blk.ar.frame = 0; blk.ar.begin(0); blk.ar.finish_(True); blk.set_threshold(n - 1)
        life["anim_off_full_now"] += int(np.all(unit_opacity(blk.blue, n) >= FULL[True])); life["anim_off"] += 1
        life["anim_off_fade_writes"] += blk.fade_tick() is not None
        continue
    drive(blk, cb, dt_fn=lambda f: rng.uniform(1 / 144, 1 / 25),
          events={"paused": lambda f: pause_on <= f < pause_on + pause_len, "skip": skip, "cancel": cancel})
    life["fade_writes_after_cancel_or_finish"] += seen["writes_after_end"]
    life["lines"] += 1; life["cancelled"] += bool(cancel); life["skipped"] += bool(skip); life["awp"] += awp
    life["finish_broadcasts_gt1"] += len(blk.ar.finish) > 1
assert life["regress"] == life["ghost"] == life["opacity_regress"] == life["skip_not_full"] == 0
assert life["fade_writes_after_cancel_or_finish"] == life["finish_broadcasts_gt1"] == 0 and life["anim_off_full_now"] == life["anim_off"]
assert life["anim_off_fade_writes"] == 0

# pause freezes the fade: no tint write while paused (GetTimeSeconds stops with the timer manager)
_, n, _, d = ref.build_markup(max(subs[:200], key=ref.letters), ""); blk = Block(model.World(), d); writes = []
drive(blk, lambda f, t, a: writes.append((f, blk.effects["SetContentColorAndOpacity"])), events={"paused": lambda f: 10 <= f < 70})
pause_writes = writes[69][1] - writes[10][1]
assert pause_writes == 0

# ---------------- 4) representative examples ----------------
by_units = {}
for s in subs:
    by_units.setdefault(len(ref.units_of(s)[1]), []).append(s)
pick = {
    "two_word": sorted(by_units[2], key=len)[len(by_units[2]) // 2],
    "five_word": next((s for s in subs if s.strip() == "أيمكنك توصيلي يا ميكا مان؟"), sorted(by_units[5], key=len)[len(by_units[5]) // 2]),
    "long": max((s for s in subs if len(ref.units_of(s)[1]) <= 30), key=ref.letters),
    "wrapped_explicit_newline": next(s for s in subs if "\n" in s),
    "exactly_37_units": sorted(by_units[37], key=len)[0],
    "overflow_gt37": max(subs, key=lambda s: len(ref.units_of(s)[1])),
}
examples = {}
for k, s in pick.items():
    n, d, lw, blk, rows, ck = replay_line(s, keep=True)
    nf = native_frames(sum(lw)); ne = events(nf); uf = events([blk.ar.reveal[i] for i in range(n)], lw)
    for r in rows:
        r["native_letters_visible"] = sum(1 for x in nf if x <= r["frame"])
        r["current_r8b_threshold"] = max([i for i in range(n) if blk.ar.reveal[i] <= r["frame"]], default=-1)
    examples[k] = {"text": s, "units": n, "raw_units": len(ref.units_of(s)[1]), "unit_letters": lw,
                   "native_last_letter_frame": nf[-1], "current_r8b_last_unit_frame": max(blk.ar.reveal.values()),
                   "proposed_complete_frame": ck["complete"] - 1, "frames_changed": {"native": len(ne), "current_r8b": len(uf), "proposed": ck["changed_frames"]},
                   "frames": rows}

result = {
    "label": "OFFLINE DESIGN MODEL at fixed 60 fps (lifecycle: random 25-144 fps) - not Unreal execution, not in-game evidence",
    "design": {"architecture": "A: K2_SetTimer keeps integer word boundaries; Blueprint Tick computes the fade of unit T+1",
               "alpha": "FClamp((Due-Remainder+(Now-Stamp)-0.025)/(Due-0.025),0,1); 0 for single-letter units",
               "tint_B": "FadeBase(T)*(1+9.4*alpha), FadeBase = 10.5^T (1/10.5 at T=-1)",
               "new_natives": ["Divide_FloatFloat", "FClamp"], "exe_signatures": "KismetMathLibrary, OuterFunc 0x285ae80, (float,float)->float and (float,float,float)->float"},
    "quantization": quant, "replay": replay, "lifecycle": dict(life), "pause_tint_writes_during_60_paused_frames": pause_writes,
    "examples": examples,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print("R8B_FADE_MODEL_023", json.dumps({k: replay[k] for k in ("visible_change_share", "completion_frame_minus_native", "violations")}))
print("quant", json.dumps({k: quant[k] for k in ("srgb8", "linear8")}))
print("life", json.dumps(dict(life)), "overflow", len(over))
